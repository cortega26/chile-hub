"""Validadores educacionales (plan 135)."""

from typing import Any

import polars as pl

from ._helpers import (
    _duplicate_count,
    _invalid_fixed_length_count,
    _missing_columns,
    _negative_numeric_count,
    _percentage_out_of_bounds_count,
    _unknown_codes,
)


def validate_establecimientos_educacionales(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    if df.height == 0:
        errors.append("establecimientos_educacionales dataset is empty")
    if df.height - df["rbd"].n_unique() > 0:
        errors.append("rbd must be unique")
    invalid = df.filter(pl.col("codigo_comuna").str.len_chars() != 5).height
    if invalid:
        errors.append(f"found {invalid} invalid codigo_comuna values")
    if valid_commune_codes is not None:
        unknown = set(df["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
        if unknown:
            errors.append(f"education facilities reference unknown communes: {sorted(unknown)}")
    return {
        "dataset": "establecimientos_educacionales",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": [],
    }


def validate_resultados_educacionales(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    warnings = []
    required = [
        "anio",
        "codigo_comuna",
        "matricula_total",
        "asistencia_promedio",
        "tasa_aprobacion",
        "tasa_reprobacion",
        "tasa_retiro",
        "establecimientos_reportados",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"resultados_educacionales missing columns: {', '.join(missing)}")
    if df.height == 0:
        errors.append("resultados_educacionales dataset is empty")
    if not missing:
        duplicates = _duplicate_count(df, ["anio", "codigo_comuna"])
        if duplicates:
            errors.append(f"anio + codigo_comuna must be unique, found {duplicates} duplicates")
        invalid = _invalid_fixed_length_count(df, "codigo_comuna", 5)
        if invalid:
            errors.append(f"found {invalid} invalid codigo_comuna values")
        unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
        if unknown:
            errors.append(f"resultados_educacionales references unknown communes: {unknown}")
        negative = _negative_numeric_count(df, ["matricula_total", "establecimientos_reportados"])
        if negative:
            errors.append(f"found {negative} negative education outcome counts")
        out_of_bounds = _percentage_out_of_bounds_count(
            df, ["asistencia_promedio", "tasa_aprobacion", "tasa_reprobacion", "tasa_retiro"]
        )
        if out_of_bounds:
            errors.append(f"found {out_of_bounds} percentage values outside 0-100")
    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "resultados_educacionales source_mode is fallback; review before publication"
        )
    return {
        "dataset": "resultados_educacionales",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": warnings,
    }
