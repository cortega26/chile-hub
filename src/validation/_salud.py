"""Validadores de salud (plan 135)."""

from typing import Any

import polars as pl


def validate_establecimientos_salud(
    df_salud: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    row_count = df_salud.height
    if row_count == 0:
        errors.append("establecimientos_salud dataset is empty")
    if row_count - df_salud["codigo_establecimiento"].n_unique() > 0:
        errors.append("codigo_establecimiento must be unique")
    invalid_codes = df_salud.filter(pl.col("codigo_comuna").str.len_chars() != 5).height
    if invalid_codes:
        errors.append(f"found {invalid_codes} invalid codigo_comuna values")
    if valid_commune_codes is not None:
        unknown = set(df_salud["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
        if unknown:
            errors.append(
                f"health facilities reference unknown communes: {', '.join(sorted(unknown))}"
            )
    return {
        "dataset": "establecimientos_salud",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": [],
    }
