"""Extrae y normaliza finanzas municipales desde SINIM/SUBDERE."""

import datetime
import os
import sys
from pathlib import Path
from typing import Any

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
    from src.extractors.source_adapter import (
        build_standard_metadata,
        fallback_metadata_note,
        fetch_url_snapshot,
        source_mode_from_live_success,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from source_adapter import (
        build_standard_metadata,
        fallback_metadata_note,
        fetch_url_snapshot,
        source_mode_from_live_success,
    )

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
STAGING_CSV_PATH = STAGING_DIR / "finanzas_municipales.csv"
METADATA_PATH = STAGING_DIR / "finanzas_municipales.metadata.json"
SOURCE_URL = "https://datos.sinim.gov.cl/datos_municipales.php"

REUSE_POLICY = {
    "status": "public-api-review-terms",
    "license": "Datos públicos municipales; términos de reutilización sujetos a revisión",
    "license_url": "https://datos.sinim.gov.cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": "Información municipal pública publicada por SINIM/SUBDERE; citar fuente oficial.",
}

FALLBACK_ROWS = [
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "ingresos_totales": 245000000000.0,
        "gastos_totales": 231000000000.0,
        "ingresos_propios_permanentes": 162000000000.0,
        "fondo_comun_municipal": 39000000000.0,
        "gasto_personal": 70500000000.0,
        "gasto_inversion": 28500000000.0,
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "nombre_comuna": "Viña del Mar",
        "ingresos_totales": 155000000000.0,
        "gastos_totales": 149000000000.0,
        "ingresos_propios_permanentes": 98000000000.0,
        "fondo_comun_municipal": 21000000000.0,
        "gasto_personal": 52300000000.0,
        "gasto_inversion": 17400000000.0,
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "ingresos_totales": 132000000000.0,
        "gastos_totales": 126000000000.0,
        "ingresos_propios_permanentes": 76500000000.0,
        "fondo_comun_municipal": 24500000000.0,
        "gasto_personal": 41800000000.0,
        "gasto_inversion": 15200000000.0,
    },
]


def fetch_data(source_url: str = SOURCE_URL) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Obtiene datos desde SINIM, con fallback a filas curadas."""
    ensure_staging_directories()
    notes: list[str] = []
    success, _content, note, data_parsed = fetch_url_snapshot(
        source_url, RAW_DIR, "sinim_finanzas_municipales"
    )
    notes.append(note)
    # data_parsed es False porque el contenido HTML no se procesa como datos tabulares.
    # El portal SINIM requiere simulación de formulario JS/POST; no es scrapeable vía GET.
    if data_parsed:
        notes.append(fallback_metadata_note("until_stable_direct_export_is_configured"))
    else:
        notes.append(fallback_metadata_note("official_landing_fetch_failed"))
    source_mode = source_mode_from_live_success(success, data_parsed)
    return FALLBACK_ROWS, source_mode, source_url, notes


def normalize_rows(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("anio").cast(pl.Int32),
            pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
            pl.col("nombre_comuna").cast(pl.String),
            pl.col("ingresos_totales").cast(pl.Float64),
            pl.col("gastos_totales").cast(pl.Float64),
            pl.col("ingresos_propios_permanentes").cast(pl.Float64),
            pl.col("fondo_comun_municipal").cast(pl.Float64),
            pl.col("gasto_personal").cast(pl.Float64),
            pl.col("gasto_inversion").cast(pl.Float64),
        )
        .sort(["anio", "codigo_comuna"])
    )


def build_metadata(df: pl.DataFrame, source_mode: str, source_url: str, notes: list[str]) -> dict:
    return build_standard_metadata(
        dataset="finanzas_municipales",
        source_name="SINIM - SUBDERE",
        source_url=source_url,
        source_mode=source_mode,
        source_detail="curated_fallback_pending_direct_export",
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )


def process_sinim_finanzas() -> str:
    raw_rows, source_mode, source_url, notes = fetch_data()
    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)
    validation = SinimFinanzasExtractor().validate(df, metadata)
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")
    SinimFinanzasExtractor().write_staging(df, metadata)
    print(f"Finanzas municipales guardadas en: {STAGING_CSV_PATH} ({df.height} registros)")
    return str(STAGING_CSV_PATH)


class SinimFinanzasExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "finanzas_municipales"

    def fetch(self, **kwargs):
        return fetch_data(**kwargs)

    def normalize(self, raw_data):
        return normalize_rows(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_finanzas_municipales

        return validate_finanzas_municipales(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_sinim_finanzas()
