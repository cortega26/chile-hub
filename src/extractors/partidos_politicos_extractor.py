"""Extractor de partidos políticos desde el web service de datos abiertos de la Cámara.

Fuente: `WSComun.asmx/retornarPartidosPoliticos` (Cámara de Diputadas y Diputados).
Devuelve el roster de partidos conocidos por la Cámara (Id/Nombre/Alias), que incluye
partidos vigentes e históricos asociados a las militancias de los diputados/as. No es el
registro legal de SERVEL.

`estado_legal`/`fecha_constitucion` se completan uniendo por nombre normalizado contra
dos páginas HTML estáticas y reales de SERVEL (`partidos-constituidos`/
`partidos-en-formacion`; verificadas en vivo, 2026-07-06). `ambito` (nacional/regional)
queda nullable: no se encontró esa señal en ninguna página del sitio de SERVEL.

Plan 023 · Ola B. Solo datos institucionales públicos; sin datos personales.
"""

import datetime
import html
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
    from src.extractors.region_utils import norm_text
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from http_utils import fetch_with_retry
    from region_utils import norm_text

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "partidos_politicos.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "partidos_politicos.metadata.json")

SOURCE_URL = (
    "https://opendata.camara.cl/camaradiputados/WServices/WSComun.asmx/retornarPartidosPoliticos"
)
CAMARA_NS = {"v": "http://opendata.camara.cl/camaradiputados/v1"}

SERVEL_CONSTITUIDOS_URL = "https://www.servel.cl/partidos-politicos/partidos-constituidos/"
SERVEL_EN_FORMACION_URL = "https://www.servel.cl/partidos-politicos/partidos-en-formacion/"

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Roster de partidos políticos publicado por la Cámara de Diputadas y Diputados "
        "en su portal de datos abiertos (datos institucionales públicos), enriquecido con "
        "estado_legal/fecha_constitucion desde las páginas públicas de SERVEL."
    ),
}

# Sufijos/valores esperados para reconciliación (orden de magnitud, no rígido).
MIN_EXPECTED_PARTIES = 15


def _text(node: ET.Element, tag: str) -> str:
    child = node.find(f"v:{tag}", CAMARA_NS)
    return (child.text or "").strip() if child is not None and child.text else ""


_MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
_FECHA_ES_RE = re.compile(r"(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+de\s+(\d{4})", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)

# Filas de las tablas de SERVEL que no representan un partido real: encabezados y un
# artefacto de la tabla "constituidos" (fila con el mismo texto que la cabecera de
# fecha, en vez de un nombre de partido) — confirmados en vivo, 2026-07-06.
_FILAS_NO_PARTIDO = {
    norm_text("Partidos Políticos"),
    norm_text("Fecha Constitución Partidos Políticos"),
    norm_text("Partidos en trámites y caducidades"),
}


def _celda_a_texto(raw_html: str) -> str:
    return html.unescape(_TAG_RE.sub("", raw_html)).strip()


_DE_CHILE_RE = re.compile(r"\s+de\s+chile$")


def _norm_partido(nombre: str) -> str:
    """Normaliza un nombre de partido para el join Cámara↔SERVEL.

    Además de `norm_text` (minúsculas sin acentos), quita el sufijo "de Chile": la
    Cámara suele omitirlo ("Partido Comunista") mientras SERVEL lo incluye ("Partido
    Comunista de Chile") para el mismo partido.
    """
    return _DE_CHILE_RE.sub("", norm_text(nombre)).strip()


def _parse_fecha_espanol(texto: str) -> str | None:
    """Convierte una fecha en español ("2 de mayo de 1988") a ISO ("1988-05-02")."""
    match = _FECHA_ES_RE.search(texto)
    if not match:
        return None
    day, mes_nombre, year = match.groups()
    mes = _MESES_ES.get(norm_text(mes_nombre))
    if mes is None:
        return None
    try:
        return datetime.date(int(year), mes, int(day)).isoformat()
    except ValueError:
        return None


def _parse_servel_tabla(html_content: str, con_fecha: bool) -> list[tuple[str, str | None]]:
    """Extrae ``(nombre, fecha_texto)`` de la primera tabla HTML de una página de SERVEL."""
    tabla_match = re.search(r"<table.*?</table>", html_content, re.S | re.I)
    if not tabla_match:
        return []
    filas = []
    for row_html in _ROW_RE.findall(tabla_match.group(0)):
        celdas = [_celda_a_texto(c) for c in _CELL_RE.findall(row_html)]
        if not celdas or not celdas[0] or norm_text(celdas[0]) in _FILAS_NO_PARTIDO:
            continue
        fecha_texto = celdas[1] if con_fecha and len(celdas) > 1 else None
        filas.append((celdas[0], fecha_texto))
    return filas


def fetch_servel_estado_legal() -> dict[str, tuple[str, str | None]]:
    """Consulta SERVEL y arma ``nombre_normalizado -> (estado_legal, fecha_constitucion)``.

    No expone `ambito` (nacional/regional): no se encontró esa señal en ninguna de las
    dos páginas (verificado en vivo). Ante cualquier falla de red o cambio de estructura,
    degrada omitiendo la fuente que falle — SERVEL es secundaria en este extractor, no
    debe bloquear el roster autoritativo de la Cámara.
    """
    lookup: dict[str, tuple[str, str | None]] = {}
    try:
        constituidos_html = fetch_with_retry(SERVEL_CONSTITUIDOS_URL, timeout=30).text
        for nombre, fecha_texto in _parse_servel_tabla(constituidos_html, con_fecha=True):
            fecha_iso = _parse_fecha_espanol(fecha_texto) if fecha_texto else None
            lookup[_norm_partido(nombre)] = ("constituido", fecha_iso)
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener SERVEL (constituidos): {exc}")
    try:
        en_formacion_html = fetch_with_retry(SERVEL_EN_FORMACION_URL, timeout=30).text
        for nombre, _fecha in _parse_servel_tabla(en_formacion_html, con_fecha=False):
            lookup.setdefault(_norm_partido(nombre), ("en_formacion", None))
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener SERVEL (en_formación): {exc}")
    return lookup


def fetch_partidos_xml() -> bytes:
    """Descarga el XML de partidos desde el web service de la Cámara."""
    headers = {"User-Agent": "chile-hub/data-pipeline (+https://github.com/cortega26/chile-hub)"}
    response = fetch_with_retry(SOURCE_URL, timeout=30, headers=headers)
    response.raise_for_status()
    content: bytes = response.content
    return content


def parse_partidos(
    xml_bytes: bytes, servel_lookup: dict[str, tuple[str, str | None]] | None = None
) -> pl.DataFrame:
    """Parsea el XML de la Cámara al esquema canónico de `partidos_politicos`.

    ``servel_lookup`` (``nombre_normalizado -> (estado_legal, fecha_constitucion)``,
    ver `fetch_servel_estado_legal`) completa esos dos campos por join de nombre; sin
    match, quedan `None` (no se inventa). `ambito` siempre queda `None`: SERVEL no
    expone esa señal en ninguna de sus dos páginas de partidos.
    """
    servel_lookup = servel_lookup or {}
    root = ET.fromstring(xml_bytes)
    fecha_consulta = datetime.datetime.now(UTC).date().isoformat()
    rows = []
    for partido in root.findall(".//v:PartidoPolitico", CAMARA_NS):
        id_partido = _text(partido, "Id")
        nombre = _text(partido, "Nombre")
        sigla = _text(partido, "Alias") or id_partido
        if not id_partido or not nombre:
            continue
        estado_legal, fecha_constitucion = servel_lookup.get(_norm_partido(nombre), (None, None))
        rows.append(
            {
                "id_partido": id_partido,
                "nombre": nombre,
                "sigla": sigla,
                "estado_legal": estado_legal,
                "fecha_constitucion": fecha_constitucion,
                # No se encontró esta señal en SERVEL (ni en ninguna otra fuente
                # institucional) → nullable, documentado en la ficha.
                "ambito": None,
                "fuente": "Cámara de Diputadas y Diputados (datos abiertos)",
                "url_fuente": SOURCE_URL,
                "fecha_consulta": fecha_consulta,
            }
        )
    df = pl.DataFrame(
        rows,
        schema={
            "id_partido": pl.String,
            "nombre": pl.String,
            "sigla": pl.String,
            "estado_legal": pl.String,
            "fecha_constitucion": pl.String,
            "ambito": pl.String,
            "fuente": pl.String,
            "url_fuente": pl.String,
            "fecha_consulta": pl.String,
        },
    )
    return df.unique(subset=["id_partido"], keep="first").sort("id_partido")


class PartidosPoliticosExtractor(BaseExtractor):
    """Extractor del roster de partidos políticos de la Cámara."""

    @property
    def dataset_name(self) -> str:
        return "partidos_politicos"

    def fetch(self, **kwargs) -> dict[str, object]:
        return {
            "xml": fetch_partidos_xml(),
            "servel": fetch_servel_estado_legal(),
        }

    def normalize(self, raw_data: dict[str, object]) -> pl.DataFrame:
        xml_bytes = raw_data["xml"]
        servel_lookup = raw_data.get("servel") or {}
        assert isinstance(xml_bytes, bytes)
        assert isinstance(servel_lookup, dict)
        return parse_partidos(xml_bytes, servel_lookup)

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        errors = []
        if df.height < MIN_EXPECTED_PARTIES:
            errors.append(
                f"Conteo de partidos ({df.height}) por debajo del mínimo esperado "
                f"({MIN_EXPECTED_PARTIES})."
            )
        if df.filter(pl.col("id_partido").is_null() | (pl.col("id_partido") == "")).height:
            errors.append("Hay partidos sin id_partido.")
        if df["id_partido"].n_unique() != df.height:
            errors.append("id_partido no es único.")
        # Línea roja: sin columnas de datos personales.
        personales = {"rut", "run", "domicilio"}
        if personales & {c.lower() for c in df.columns}:
            errors.append("El dataset contiene columnas de datos personales (línea roja).")
        return {"status": "error" if errors else "ok", "errors": errors, "record_count": df.height}

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


def process_partidos_politicos() -> str:
    """Ejecuta el extractor standalone (invocado desde el Makefile)."""
    ensure_staging_directories()
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = Path(RAW_DIR) / f"camara_partidos_{stamp}.xml"

    extractor = PartidosPoliticosExtractor()
    raw = extractor.fetch()
    with open(raw_path, "wb") as f:
        assert isinstance(raw["xml"], bytes)
        f.write(raw["xml"])

    df = extractor.normalize(raw)
    validation = extractor.validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    n_con_estado_legal = df.filter(pl.col("estado_legal").is_not_null()).height
    metadata = {
        "dataset": "partidos_politicos",
        "source_name": "Cámara de Diputadas y Diputados (datos abiertos) + SERVEL",
        "source_url": SOURCE_URL,
        "source_mode": "live",
        "source_detail": (
            "WSComun.asmx/retornarPartidosPoliticos + servel.cl/partidos-politicos (estado legal)"
        ),
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            "Roster de partidos de la Cámara (incluye vigentes e históricos).",
            f"estado_legal/fecha_constitucion vía SERVEL: {n_con_estado_legal}/{df.height} matcheados por nombre.",
            "ambito (nacional/regional) no provisto por ninguna fuente encontrada (nullable).",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(f"Partidos políticos guardados en: {STAGING_CSV_PATH} ({df.height} registros)")
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process_partidos_politicos()
