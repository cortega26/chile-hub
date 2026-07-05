"""Extractor de autoridades electas de Chile (Plan 023 · Ola A).

v1 (carril `candidate`): cargo **diputados** — 155 diputados/as del período
legislativo vigente, con su partido actual y su **distrito electoral**.

Fuentes:
- Roster + partido: web service de datos abiertos de la Cámara
  (`WSDiputado.asmx/retornarDiputadosPeriodoActual`).
- Distrito electoral: listado web de la Cámara (`camara.cl/diputados/diputados.aspx`),
  que bloquea HTTP simple (403) — se obtiene con **Scrapling** (fetch con headers
  stealth). Se une al roster por `prmID`, que coincide con el Id del web service.

Cargos pendientes (documentados en la ficha y el plan): `senador` (50),
`gobernador_regional` (16), `alcalde` (345).

Solo datos institucionales públicos de cargos en ejercicio; **sin datos personales**
(línea roja Ley 19.628, ver `docs/legal/b2-2-electoral-research.md`). El RUT que expone
el web service se descarta explícitamente.
"""

import datetime
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import polars as pl

UTC = datetime.timezone.utc

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from http_utils import fetch_with_retry

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "autoridades_electas.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "autoridades_electas.metadata.json")

DIPUTADOS_URL = (
    "https://opendata.camara.cl/camaradiputados/WServices/WSDiputado.asmx/"
    "retornarDiputadosPeriodoActual"
)
DIPUTADOS_LISTADO_URL = "https://www.camara.cl/diputados/diputados.aspx"
CAMARA_NS = {"v": "http://opendata.camara.cl/camaradiputados/v1"}

# Período legislativo vigente de la Cámara (actualizar cada 4 años; ver review_by).
PERIODO_DIPUTADOS = {"inicio": "2026-03-11", "fin": "2030-03-10"}

# Columnas canónicas del dataset autoridades_electas.
SCHEMA: dict[str, type[pl.DataType]] = {
    "id_autoridad": pl.String,
    "nombre": pl.String,
    "cargo": pl.String,
    "institucion": pl.String,
    "partido": pl.String,
    "pacto": pl.String,
    "distrito_electoral": pl.String,
    "circunscripcion_senatorial": pl.String,
    "codigo_comuna": pl.String,
    "codigo_region": pl.String,
    "periodo_inicio": pl.String,
    "periodo_fin": pl.String,
    "estado_mandato": pl.String,
    "fuente": pl.String,
    "url_fuente": pl.String,
    "fecha_consulta": pl.String,
}

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Autoridades electas en ejercicio (cargos públicos) desde datos abiertos "
        "oficiales. Solo agregados institucionales; sin datos personales."
    ),
}

EXPECTED_DIPUTADOS = 155
_HEADERS = {"User-Agent": "chile-hub/data-pipeline (+https://github.com/cortega26/chile-hub)"}


def _text(node: ET.Element | None, tag: str) -> str:
    if node is None:
        return ""
    child = node.find(f"v:{tag}", CAMARA_NS)
    return (child.text or "").strip() if child is not None and child.text else ""


def _parse_date(value: str) -> datetime.date | None:
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value[:10])
    except ValueError:
        return None


def _partido_vigente(militancias: ET.Element | None) -> str:
    """Devuelve el nombre del partido de la militancia que cubre hoy (o la más reciente)."""
    if militancias is None:
        return ""
    today = datetime.datetime.now(UTC).date()
    candidatas: list[tuple[datetime.date, str]] = []
    vigente_hoy: str | None = None
    for mil in militancias.findall("v:Militancia", CAMARA_NS):
        inicio = _parse_date(_text(mil, "FechaInicio"))
        fin = _parse_date(_text(mil, "FechaTermino"))
        partido = _text(mil.find("v:Partido", CAMARA_NS), "Nombre")
        if not partido:
            continue
        if inicio is not None and (fin is None or inicio <= today <= fin):
            vigente_hoy = partido
        candidatas.append((inicio or datetime.date.min, partido))
    if vigente_hoy:
        return vigente_hoy
    return max(candidatas, key=lambda x: x[0])[1] if candidatas else ""


def fetch_diputados_xml() -> bytes:
    """Descarga el XML de diputados/as del período vigente (web service de la Cámara)."""
    response = fetch_with_retry(DIPUTADOS_URL, timeout=30, headers=_HEADERS)
    response.raise_for_status()
    content: bytes = response.content
    return content


def fetch_distritos_diputados() -> dict[str, str]:
    """Mapa ``id_diputado -> distrito`` desde el listado web de la Cámara vía Scrapling.

    ``camara.cl`` responde 403 a un GET normal; Scrapling lo obtiene con headers
    stealth. Cada card trae ``prmID=<id>`` (igual al Id del web service) y
    ``Distrito: Nº <n>``. Si la obtención falla, retorna ``{}`` (distrito nulo) para
    no romper el extractor — el distrito es un enriquecimiento, no la fuente primaria.
    """
    try:
        from scrapling.fetchers import Fetcher

        page = Fetcher.get(DIPUTADOS_LISTADO_URL, stealthy_headers=True)
        html = page.html_content
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener el distrito de diputados ({exc}). Queda nulo.")
        return {}
    mapa: dict[str, str] = {}
    for card in html.split("<article"):
        mid = re.search(r"prmID=(\d+)", card)
        dist = re.search(r"Distrito:\s*N[ºo°]\s*(\d+)", card)
        if mid and dist:
            mapa[mid.group(1)] = dist.group(1)
    return mapa


def _normalize_diputados(
    xml_bytes: bytes, distritos: dict[str, str], fecha_consulta: str
) -> list[dict[str, str | None]]:
    root = ET.fromstring(xml_bytes)
    rows: list[dict[str, str | None]] = []
    for dp in root.findall(".//v:DiputadoPeriodo", CAMARA_NS):
        dip = dp.find("v:Diputado", CAMARA_NS)
        if dip is None:
            continue
        dip_id = _text(dip, "Id")
        nombre = " ".join(
            p
            for p in (
                _text(dip, "Nombre"),
                _text(dip, "ApellidoPaterno"),
                _text(dip, "ApellidoMaterno"),
            )
            if p
        )
        if not dip_id or not nombre:
            continue
        partido = _partido_vigente(dip.find("v:Militancias", CAMARA_NS))
        rows.append(
            {
                "id_autoridad": f"diputado_{dip_id}",
                "nombre": nombre,
                "cargo": "diputado",
                "institucion": "Cámara de Diputadas y Diputados",
                "partido": partido or None,
                "pacto": None,
                "distrito_electoral": distritos.get(dip_id),
                "circunscripcion_senatorial": None,
                "codigo_comuna": None,
                "codigo_region": None,
                "periodo_inicio": PERIODO_DIPUTADOS["inicio"],
                "periodo_fin": PERIODO_DIPUTADOS["fin"],
                "estado_mandato": "vigente",
                "fuente": "Cámara de Diputadas y Diputados (datos abiertos)",
                "url_fuente": DIPUTADOS_URL,
                "fecha_consulta": fecha_consulta,
            }
        )
    return rows


def build_autoridades_df(xml_diputados: bytes, distritos: dict[str, str]) -> pl.DataFrame:
    """Construye el DataFrame canónico de autoridades electas (v1: solo diputados)."""
    fecha = datetime.datetime.now(UTC).date().isoformat()
    rows = _normalize_diputados(xml_diputados, distritos, fecha)
    df = pl.DataFrame(rows, schema=SCHEMA)
    return df.unique(subset=["id_autoridad"], keep="first").sort("id_autoridad")


class AutoridadesElectasExtractor(BaseExtractor):
    """Extractor de autoridades electas (v1: cargo diputados desde la Cámara)."""

    @property
    def dataset_name(self) -> str:
        return "autoridades_electas"

    def fetch(self, **kwargs) -> dict[str, object]:
        return {
            "diputados_xml": fetch_diputados_xml(),
            "distritos": fetch_distritos_diputados(),
        }

    def normalize(self, raw_data: dict[str, object]) -> pl.DataFrame:
        xml_bytes = raw_data["diputados_xml"]
        distritos = raw_data["distritos"]
        assert isinstance(xml_bytes, bytes)
        assert isinstance(distritos, dict)
        return build_autoridades_df(xml_bytes, distritos)

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        errors = []
        n_dip = df.filter(pl.col("cargo") == "diputado").height
        if n_dip != EXPECTED_DIPUTADOS:
            errors.append(f"Diputados esperados {EXPECTED_DIPUTADOS}, obtenidos {n_dip}.")
        if df["id_autoridad"].n_unique() != df.height:
            errors.append("id_autoridad no es único.")
        # Línea roja: sin columnas de datos personales.
        personales = {"rut", "rutdv", "run", "domicilio", "fecha_nacimiento"}
        if personales & {c.lower() for c in df.columns}:
            errors.append("El dataset contiene columnas de datos personales (línea roja).")
        return {"status": "error" if errors else "ok", "errors": errors, "record_count": df.height}

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


def process_autoridades_electas() -> str:
    """Ejecuta el extractor standalone."""
    ensure_staging_directories()
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = Path(RAW_DIR) / f"camara_diputados_{stamp}.xml"

    extractor = AutoridadesElectasExtractor()
    raw = extractor.fetch()
    with open(raw_path, "wb") as f:
        assert isinstance(raw["diputados_xml"], bytes)
        f.write(raw["diputados_xml"])

    df = extractor.normalize(raw)
    validation = extractor.validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    n_con_distrito = df.filter(pl.col("distrito_electoral").is_not_null()).height
    metadata = {
        "dataset": "autoridades_electas",
        "source_name": "Cámara de Diputadas y Diputados (datos abiertos + listado web)",
        "source_url": DIPUTADOS_URL,
        "source_mode": "live",
        "source_detail": "WSDiputado.asmx/retornarDiputadosPeriodoActual + camara.cl (Scrapling)",
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            "v1: solo cargo diputado (155). Senadores/gobernadores/alcaldes pendientes.",
            f"distrito_electoral vía Scrapling: {n_con_distrito}/{df.height} diputados.",
            "RUT del web service descartado (línea roja de datos personales).",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(
        f"Autoridades electas guardadas en: {STAGING_CSV_PATH} "
        f"({df.height} registros, {n_con_distrito} con distrito)"
    )
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process_autoridades_electas()
