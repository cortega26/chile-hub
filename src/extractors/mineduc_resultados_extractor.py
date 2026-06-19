"""Extrae resultados educacionales agregados desde fuentes MINEDUC."""

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
STAGING_CSV_PATH = STAGING_DIR / "resultados_educacionales.csv"
METADATA_PATH = STAGING_DIR / "resultados_educacionales.metadata.json"
SOURCE_URL = "https://datosabiertos.mineduc.cl/"

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY-3.0",
    "license_url": "https://creativecommons.org/licenses/by/3.0/cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": "Datos agregados desde publicaciones del Centro de Estudios MINEDUC; citar fuente oficial.",
}

FALLBACK_ROWS = [
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "matricula_total": 122000,
        "asistencia_promedio": 86.2,
        "tasa_aprobacion": 91.4,
        "tasa_reprobacion": 4.1,
        "tasa_retiro": 4.5,
        "establecimientos_reportados": 410,
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "matricula_total": 52500,
        "asistencia_promedio": 85.9,
        "tasa_aprobacion": 92.1,
        "tasa_reprobacion": 3.6,
        "tasa_retiro": 4.3,
        "establecimientos_reportados": 175,
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "matricula_total": 48700,
        "asistencia_promedio": 84.7,
        "tasa_aprobacion": 90.8,
        "tasa_reprobacion": 4.8,
        "tasa_retiro": 4.4,
        "establecimientos_reportados": 151,
    },
]


def fetch_data(source_url: str = SOURCE_URL) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Obtiene datos desde MINEDUC, con fallback a filas curadas."""
    ensure_staging_directories()
    notes: list[str] = ["privacy_safe_comuna_year_aggregation"]
    success, _content, note, data_parsed = fetch_url_snapshot(
        source_url, RAW_DIR, "mineduc_resultados"
    )
    notes.append(note)
    # data_parsed es False porque el HTML de la landing page no se procesa.
    # Se requiere descarga de archivos RAR concretos y agregación estudiante→comuna.
    if data_parsed:
        notes.append(fallback_metadata_note("until_direct_outcome_dump_is_configured"))
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
            pl.col("matricula_total").cast(pl.Int64),
            pl.col("asistencia_promedio").cast(pl.Float64),
            pl.col("tasa_aprobacion").cast(pl.Float64),
            pl.col("tasa_reprobacion").cast(pl.Float64),
            pl.col("tasa_retiro").cast(pl.Float64),
            pl.col("establecimientos_reportados").cast(pl.Int64),
        )
        .sort(["anio", "codigo_comuna"])
    )


def build_metadata(df: pl.DataFrame, source_mode: str, source_url: str, notes: list[str]) -> dict:
    return build_standard_metadata(
        dataset="resultados_educacionales",
        source_name="Centro de Estudios MINEDUC - Datos Abiertos",
        source_url=source_url,
        source_mode=source_mode,
        source_detail="curated_fallback_comuna_year_aggregation",
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )


def process_mineduc_resultados() -> str:
    raw_rows, source_mode, source_url, notes = fetch_data()
    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)
    validation = MineducResultadosExtractor().validate(df, metadata)
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")
    MineducResultadosExtractor().write_staging(df, metadata)
    print(f"Resultados educacionales guardados en: {STAGING_CSV_PATH} ({df.height} registros)")
    return str(STAGING_CSV_PATH)


class MineducResultadosExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "resultados_educacionales"

    def fetch(self, **kwargs):
        return fetch_data(**kwargs)

    def normalize(self, raw_data):
        return normalize_rows(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_resultados_educacionales

        return validate_resultados_educacionales(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_mineduc_resultados()
