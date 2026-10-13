"""Validadores de la división político-administrativa (plan 135)."""

from typing import Any

import polars as pl

from ._constants import EXPECTED_LIVE_COMUNAS_COUNT, FALLBACK_COMUNAS_COUNT


def validate_comunas(df_comunas: pl.DataFrame, metadata: dict[str, Any] | None) -> dict[str, Any]:
    errors = []
    warnings = []
    row_count = df_comunas.height
    duplicate_count = row_count - df_comunas["codigo_comuna"].n_unique()

    if duplicate_count > 0:
        errors.append(f"codigo_comuna must be unique, found {duplicate_count} duplicate rows")

    if (
        metadata
        and metadata.get("source_mode") == "live"
        and row_count < EXPECTED_LIVE_COMUNAS_COUNT
    ):
        errors.append(
            f"live comunas dataset looks incomplete: {row_count} rows, expected at least {EXPECTED_LIVE_COMUNAS_COUNT}"
        )

    if metadata and metadata.get("source_mode") == "fallback":
        if row_count != FALLBACK_COMUNAS_COUNT:
            warnings.append(
                f"fallback comunas expected about {FALLBACK_COMUNAS_COUNT} rows, found {row_count}"
            )
        warnings.append("comunas source_mode is fallback; coverage is limited by design")

    return {
        "dataset": "comunas",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }


def validate_regiones(df_regiones: pl.DataFrame) -> dict[str, Any]:
    errors = []
    if df_regiones.height == 0:
        errors.append("regiones dataset is empty")
    duplicate_count = df_regiones.height - df_regiones["codigo_region"].n_unique()
    if duplicate_count > 0:
        errors.append(f"codigo_region must be unique, found {duplicate_count} duplicate rows")
    return {
        "dataset": "regiones",
        "status": "error" if errors else "ok",
        "record_count": df_regiones.height,
        "errors": errors,
        "warnings": [],
    }


def validate_provincias(df_provincias: pl.DataFrame) -> dict[str, Any]:
    errors = []
    if df_provincias.height == 0:
        errors.append("provincias dataset is empty")
    keys = (df_provincias["codigo_region"] + "-" + df_provincias["codigo_provincia"]).n_unique()
    if keys != df_provincias.height:
        errors.append("codigo_region + codigo_provincia must be unique")
    return {
        "dataset": "provincias",
        "status": "error" if errors else "ok",
        "record_count": df_provincias.height,
        "errors": errors,
        "warnings": [],
    }
