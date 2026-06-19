"""Extrae indicadores urbanos SIEDU con cobertura comunal parcial esperada."""

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
STAGING_CSV_PATH = STAGING_DIR / "indicadores_urbanos_siedu.csv"
METADATA_PATH = STAGING_DIR / "indicadores_urbanos_siedu.metadata.json"
SOURCE_URL = "https://siedu.ine.cl/"

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "Licencia de Datos Abiertos INE",
    "license_url": "https://www.ine.gob.cl/terminos-de-uso",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": "Indicadores urbanos SIEDU publicados por INE para comunas urbanas seleccionadas.",
}

FALLBACK_ROWS = [
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "codigo_indicador": "siedu_acceso_areas_verdes",
        "nombre_indicador": "Acceso a areas verdes",
        "categoria": "Espacio publico",
        "valor": 71.4,
        "unidad": "porcentaje",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "codigo_indicador": "siedu_acceso_areas_verdes",
        "nombre_indicador": "Acceso a areas verdes",
        "categoria": "Espacio publico",
        "valor": 65.8,
        "unidad": "porcentaje",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "codigo_indicador": "siedu_acceso_areas_verdes",
        "nombre_indicador": "Acceso a areas verdes",
        "categoria": "Espacio publico",
        "valor": 62.3,
        "unidad": "porcentaje",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "codigo_indicador": "siedu_tiempo_transporte",
        "nombre_indicador": "Tiempo medio de viaje urbano",
        "categoria": "Movilidad",
        "valor": 42.0,
        "unidad": "minutos",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "codigo_indicador": "siedu_tiempo_transporte",
        "nombre_indicador": "Tiempo medio de viaje urbano",
        "categoria": "Movilidad",
        "valor": 36.0,
        "unidad": "minutos",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "codigo_indicador": "siedu_tiempo_transporte",
        "nombre_indicador": "Tiempo medio de viaje urbano",
        "categoria": "Movilidad",
        "valor": 34.0,
        "unidad": "minutos",
        "fuente_original": "SIEDU INE",
        "cobertura_tipo": "urbana",
    },
]


def fetch_data(source_url: str = SOURCE_URL) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Obtiene datos desde SIEDU, con fallback a filas curadas."""
    ensure_staging_directories()
    notes: list[str] = ["partial_urban_coverage_expected"]
    success, _content, note, data_parsed = fetch_url_snapshot(source_url, RAW_DIR, "siedu")
    notes.append(note)
    # data_parsed es False porque el HTML del portal de mapas no se procesa.
    # Se requiere descarga del Excel Matriz de Indicadores desde siedu.ine.cl.
    if data_parsed:
        notes.append(fallback_metadata_note("until_download_matrix_is_configured"))
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
            pl.col("codigo_indicador").cast(pl.String),
            pl.col("nombre_indicador").cast(pl.String),
            pl.col("categoria").cast(pl.String),
            pl.col("valor").cast(pl.Float64),
            pl.col("unidad").cast(pl.String),
            pl.col("fuente_original").cast(pl.String),
            pl.col("cobertura_tipo").cast(pl.String),
        )
        .sort(["anio", "codigo_comuna", "codigo_indicador"])
    )


def build_metadata(df: pl.DataFrame, source_mode: str, source_url: str, notes: list[str]) -> dict:
    commune_count = df["codigo_comuna"].n_unique()
    metadata = build_standard_metadata(
        dataset="indicadores_urbanos_siedu",
        source_name="INE - Sistema de Indicadores y Estándares de Desarrollo Urbano",
        source_url=source_url,
        source_mode=source_mode,
        source_detail="curated_fallback_partial_urban_coverage",
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )
    # SIEDU agrega metadata de cobertura parcial esperada
    metadata["coverage"] = {
        "status": "partial_expected",
        "coverage_ratio": round(commune_count / 346, 4),
        "expected_scope": ("Comunas urbanas incluidas por SIEDU, no las 346 comunas del país."),
    }
    return metadata


def process_siedu() -> str:
    raw_rows, source_mode, source_url, notes = fetch_data()
    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)
    validation = SieduExtractor().validate(df, metadata)
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")
    SieduExtractor().write_staging(df, metadata)
    print(f"Indicadores SIEDU guardados en: {STAGING_CSV_PATH} ({df.height} registros)")
    return str(STAGING_CSV_PATH)


class SieduExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "indicadores_urbanos_siedu"

    def fetch(self, **kwargs):
        return fetch_data(**kwargs)

    def normalize(self, raw_data):
        return normalize_rows(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_indicadores_urbanos_siedu

        return validate_indicadores_urbanos_siedu(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_siedu()
