"""Validación de observaciones DGAC: clave temporal por estación, sin CUT."""

from __future__ import annotations

from typing import Any

import polars as pl


def validate_precipitaciones_dgac(
    df: pl.DataFrame, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    required = [
        "fecha",
        "id_estacion",
        "nombre_estacion",
        "latitud_dms",
        "altitud_m",
        "precipitacion_mm",
        "url_fuente",
        "licencia_fuente",
    ]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        errors.append(f"missing required columns: {missing}")
    elif df.is_empty():
        errors.append("dataset DGAC vacío")
    else:
        if df.select(["fecha", "id_estacion"]).n_unique() != df.height:
            errors.append("clave duplicada: (fecha, id_estacion)")
        if df.filter(
            pl.col("id_estacion").is_null()
            | (pl.col("id_estacion").str.len_chars() != 6)
            | (~pl.col("id_estacion").str.contains(r"^\d{6}$"))
        ).height:
            errors.append("código de estación inválido")
        if df.filter(pl.col("precipitacion_mm") < 0).height:
            errors.append("precipitación negativa")
        if df.filter(pl.col("altitud_m").is_null()).height:
            errors.append("altitud desconocida")
        if df.filter(
            (~pl.col("licencia_fuente").is_in(["cc-by", "cc-zero"]))
            | pl.col("licencia_fuente").is_null()
        ).height:
            errors.append("licencias no redistribuibles detectadas")
        if df.filter(pl.col("url_fuente").is_null()).height:
            errors.append("fuente original ausente")
        try:
            dates = df.select(pl.col("fecha").str.to_date("%Y-%m-%d", strict=True))
            if dates.height != df.height:
                errors.append("fecha no interpretable")
        except (pl.exceptions.ComputeError, ValueError):
            errors.append("fecha no ISO")
        if df.height < 120_000:
            errors.append("cobertura histórica por debajo de 120.000 observaciones")
        if df["id_estacion"].n_unique() < 20:
            errors.append("menos de 20 estaciones")
    if metadata:
        if metadata.get("source_mode") not in {"live", "monthly"}:
            errors.append("fuente DGAC no verificada")
        if metadata.get("months") != 143:
            errors.append("histórico mensual no validado (esperados 143 meses)")
        if not metadata.get("source_files"):
            errors.append("faltan hashes y proveniencia de archivos origen")
        if not metadata.get("quarantined_source_months", {}).get("2017-01"):
            errors.append("no se documentó el archivo mal clasificado de 2017-01")

    coverage_note = (
        "DGAC: cobertura parcial por diseño; 2014 y 2015-I se excluyen por CC-NC; "
        "enero 2017 en cuarentena por contener temperaturas; 2026 solo primer semestre."
    )
    warnings.append(coverage_note)
    expected_warnings.append(coverage_note)
    return {
        "dataset": "precipitaciones_dgac",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }
