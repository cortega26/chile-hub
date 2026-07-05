"""Extractor de autoridades locales de Chile (Plan 023 · Ola A, dataset separado).

Dataset **`autoridades_locales`**, aislado de `autoridades_electas` porque su fuente es
**Wikipedia (CC-BY-SA)** — no debe contaminar la licencia CC-BY de los cargos oficiales.

v1 (carril `candidate`): cargo **gobernador_regional** (16), desde la tabla de la página
de Wikipedia "Gobernador regional de Chile", obtenida con **Scrapling**.

Cargo pendiente: `alcalde` (345) — sin fuente de tabla única redistribuible (Wikidata da
conteos inconsistentes; el anexo de Wikipedia son ~345 subpáginas). Follow-up.

Solo cargos públicos; **sin datos personales**. Mismo esquema que `autoridades_electas`.
"""

import datetime
import os
import re
import sys
import unicodedata
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
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "autoridades_locales.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "autoridades_locales.metadata.json")

GOBERNADORES_URL = "https://es.wikipedia.org/wiki/Gobernador_regional_de_Chile"

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
    "license": "CC-BY-SA",
    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    "attribution_required": True,
    "redistribution_ok": True,
    "share_alike": True,
    "summary": (
        "Autoridades locales (gobernadores regionales) compiladas desde Wikipedia "
        "(CC-BY-SA). Dataset segregado para no propagar share-alike al resto del bundle."
    ),
}

EXPECTED_GOBERNADORES = 16

# El título del enlace de región es "Gobernador(a) regional [Metropolitano] de|del <región>".
_REGION_TITLE_RE = re.compile(
    r"^gobernador[a]?\s+regional\s+(?:metropolitan[oa]\s+)?del?\s+(.+)$", re.I
)


def _region_from_title(title: str) -> str | None:
    match = _REGION_TITLE_RE.match(title.strip())
    return match.group(1).strip() if match else None


def _norm(text: str) -> str:
    """Minúsculas sin acentos, para emparejar nombres de región."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Nombre corto de región (como aparece en Wikipedia) -> código CUT de 2 dígitos.
_REGION_A_CODIGO = {
    "arica y parinacota": "15",
    "tarapaca": "01",
    "antofagasta": "02",
    "atacama": "03",
    "coquimbo": "04",
    "valparaiso": "05",
    "metropolitana de santiago": "13",
    "metropolitana": "13",
    "libertador general bernardo o'higgins": "06",
    "o'higgins": "06",
    "maule": "07",
    "nuble": "16",
    "biobio": "08",
    "la araucania": "09",
    "araucania": "09",
    "los rios": "14",
    "los lagos": "10",
    "santiago": "13",
    "aysen del general carlos ibanez del campo": "11",
    "aysen": "11",
    "magallanes y de la antartica chilena": "12",
    "magallanes": "12",
}


def fetch_gobernadores() -> list[dict[str, str]]:
    """Extrae (region, nombre, partido, pacto) de la tabla de Wikipedia vía Scrapling.

    Cada fila de datos trae, como enlaces: región, titular, partido y coalición. Si la
    obtención falla, retorna ``[]`` (el extractor no rompe).
    """
    try:
        from scrapling.fetchers import Fetcher

        page = Fetcher.get(GOBERNADORES_URL, stealthy_headers=True)
        tables = page.css("table.wikitable")
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener gobernadores ({exc}). Se omiten.")
        return []
    if not tables:
        print("Advertencia: Wikipedia no expuso la tabla de gobernadores.")
        return []
    filas = []
    for row in tables[0].css("tr"):
        if not row.css("td"):
            continue
        links = [
            (a.attrib.get("title", "").strip(), a.text.strip())
            for a in row.css("a")
            if a.attrib.get("title")
        ]

        # links: región (título "Gobernador(a) regional|metropolitano de X"), luego
        # titular, partido y coalición. La región se toma del *título* (completo), no del
        # texto del enlace (que puede venir truncado).
        region = ""
        resto = []
        for title, text in links:
            reg = _region_from_title(title)
            if reg and not region:
                region = reg
            else:
                resto.append((title, text))
        if not region or not resto:
            continue
        nombre = resto[0][1]
        partido = resto[1][0] if len(resto) > 1 else ""
        pacto = resto[2][1] if len(resto) > 2 else ""
        filas.append({"region": region, "nombre": nombre, "partido": partido, "pacto": pacto})
    return filas


def _normalize_gobernadores(
    gobernadores: list[dict[str, str]], fecha_consulta: str
) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    for g in gobernadores:
        region = g["region"].strip()
        codigo_region = _REGION_A_CODIGO.get(_norm(region))
        rows.append(
            {
                "id_autoridad": f"gobernador_{codigo_region or _norm(region).replace(' ', '_')}",
                "nombre": g["nombre"].strip(),
                "cargo": "gobernador_regional",
                "institucion": f"Gobierno Regional de {region}",
                "partido": g.get("partido") or None,
                "pacto": g.get("pacto") or None,
                "distrito_electoral": None,
                "circunscripcion_senatorial": None,
                "codigo_comuna": None,
                "codigo_region": codigo_region,
                "periodo_inicio": None,
                "periodo_fin": None,
                "estado_mandato": "vigente",
                "fuente": "Wikipedia (CC-BY-SA)",
                "url_fuente": GOBERNADORES_URL,
                "fecha_consulta": fecha_consulta,
            }
        )
    return rows


def build_autoridades_locales_df(gobernadores: list[dict[str, str]]) -> pl.DataFrame:
    """Construye el DataFrame canónico de autoridades locales (v1: gobernadores)."""
    fecha = datetime.datetime.now(UTC).date().isoformat()
    rows = _normalize_gobernadores(gobernadores, fecha)
    df = pl.DataFrame(rows, schema=SCHEMA)
    return df.unique(subset=["id_autoridad"], keep="first").sort("id_autoridad")


class AutoridadesLocalesExtractor(BaseExtractor):
    """Extractor de autoridades locales (v1: gobernadores regionales, CC-BY-SA)."""

    @property
    def dataset_name(self) -> str:
        return "autoridades_locales"

    def fetch(self, **kwargs) -> dict[str, object]:
        return {"gobernadores": fetch_gobernadores()}

    def normalize(self, raw_data: dict[str, object]) -> pl.DataFrame:
        gobernadores = raw_data.get("gobernadores") or []
        assert isinstance(gobernadores, list)
        return build_autoridades_locales_df(gobernadores)

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        errors = []
        n_gob = df.filter(pl.col("cargo") == "gobernador_regional").height
        if n_gob and n_gob != EXPECTED_GOBERNADORES:
            errors.append(f"Gobernadores esperados {EXPECTED_GOBERNADORES}, obtenidos {n_gob}.")
        if df["id_autoridad"].n_unique() != df.height:
            errors.append("id_autoridad no es único.")
        personales = {"rut", "run", "domicilio", "fecha_nacimiento"}
        if personales & {c.lower() for c in df.columns}:
            errors.append("El dataset contiene columnas de datos personales (línea roja).")
        return {"status": "error" if errors else "ok", "errors": errors, "record_count": df.height}

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


def process_autoridades_locales() -> str:
    """Ejecuta el extractor standalone."""
    ensure_staging_directories()
    extractor = AutoridadesLocalesExtractor()
    raw = extractor.fetch()
    df = extractor.normalize(raw)
    validation = extractor.validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    n_gob = df.filter(pl.col("cargo") == "gobernador_regional").height
    metadata = {
        "dataset": "autoridades_locales",
        "source_name": "Wikipedia (CC-BY-SA)",
        "source_url": GOBERNADORES_URL,
        "source_mode": "live",
        "source_detail": "Wikipedia 'Gobernador regional de Chile' (Scrapling)",
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            f"v1: gobernador_regional ({n_gob}). Cargo alcalde (345) pendiente.",
            "Fuente Wikipedia CC-BY-SA: dataset segregado para no propagar share-alike.",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(f"Autoridades locales guardadas en: {STAGING_CSV_PATH} ({df.height} registros)")
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process_autoridades_locales()
