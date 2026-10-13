"""Validadores político-electorales (plan 135)."""

from typing import Any

import polars as pl

from ._constants import VALID_CARGOS_AUTORIDADES_ELECTAS, VALID_ESTADO_LEGAL
from ._helpers import (
    _add_expected_warning,
    _duplicate_count,
    _invalid_fixed_length_count,
    _missing_columns,
    _unknown_codes,
)


def validate_distritos_electorales(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    if df.height == 0:
        errors.append("distritos_electorales dataset is empty")
    if df.height != 346:
        errors.append(f"distritos_electorales expected 346 communes, found {df.height}")
    if df.height - df["codigo_comuna"].n_unique() > 0:
        errors.append("codigo_comuna must be unique in distritos_electorales")
    invalid = df.filter(pl.col("codigo_comuna").str.len_chars() != 5).height
    if invalid:
        errors.append(f"found {invalid} invalid codigo_comuna values")
    if valid_commune_codes is not None:
        unknown = set(df["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
        if unknown:
            errors.append(f"distritos_electorales references unknown communes: {sorted(unknown)}")
    return {
        "dataset": "distritos_electorales",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": [],
    }


def validate_partidos_politicos(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de partidos políticos (Cámara + SERVEL, Plan 023).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (id_partido)
    - Dominio de estado_legal (nullable: SERVEL no cubre el roster completo de la Cámara)
    - Sin columnas de datos personales (línea roja)
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    row_count = df.height

    required = ["id_partido", "nombre", "sigla", "fuente", "url_fuente", "fecha_consulta"]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "partidos_politicos",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    if row_count == 0:
        errors.append("dataset está vacío")
        return {
            "dataset": "partidos_politicos",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    dup_count = _duplicate_count(df, ["id_partido"])
    if dup_count > 0:
        errors.append(f"found {dup_count} duplicate rows by primary key (id_partido)")

    if "estado_legal" in df.columns:
        actual = set(df["estado_legal"].drop_nulls().unique().to_list())
        unexpected = actual - VALID_ESTADO_LEGAL
        if unexpected:
            errors.append(f"estado_legal con valores fuera de dominio: {sorted(unexpected)}")
        con_estado = df["estado_legal"].drop_nulls().len()
        _add_expected_warning(
            warnings,
            expected_warnings,
            f"estado_legal poblado (vía SERVEL) en {con_estado}/{row_count} partidos",
        )

    personales = {"rut", "run", "domicilio"}
    if personales & {c.lower() for c in df.columns}:
        errors.append("el dataset contiene columnas de datos personales (línea roja)")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("partidos_politicos source_mode is fallback; usando snapshot versionado.")

    return {
        "dataset": "partidos_politicos",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }


def validate_autoridades_electas(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de autoridades electas (diputados + senadores, Plan 023).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (id_autoridad)
    - Dominio de cargo (v1: diputado/senador — gobernador_regional/alcalde viven en el
      dataset segregado autoridades_locales, CC-BY-SA)
    - Formato de codigo_comuna/codigo_region cuando están poblados
    - Sin columnas de datos personales (línea roja)
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height

    required = [
        "id_autoridad",
        "nombre",
        "cargo",
        "institucion",
        "fuente",
        "url_fuente",
        "fecha_consulta",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "autoridades_electas",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    if row_count == 0:
        errors.append("dataset está vacío")
        return {
            "dataset": "autoridades_electas",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    dup_count = _duplicate_count(df, ["id_autoridad"])
    if dup_count > 0:
        errors.append(f"found {dup_count} duplicate rows by primary key (id_autoridad)")

    actual_cargos = set(df["cargo"].drop_nulls().unique().to_list())
    unexpected_cargos = actual_cargos - VALID_CARGOS_AUTORIDADES_ELECTAS
    if unexpected_cargos:
        errors.append(f"cargo con valores fuera de dominio v1: {sorted(unexpected_cargos)}")

    if "codigo_comuna" in df.columns:
        con_comuna = df.filter(pl.col("codigo_comuna").is_not_null())
        invalid_cut = _invalid_fixed_length_count(con_comuna, "codigo_comuna", 5)
        if invalid_cut > 0:
            errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")
        unknown = _unknown_codes(con_comuna, "codigo_comuna", valid_commune_codes)
        if unknown:
            warnings.append(f"autoridades_electas references unknown communes: {unknown}")

    if "codigo_region" in df.columns:
        con_region = df.filter(pl.col("codigo_region").is_not_null())
        invalid_region = _invalid_fixed_length_count(con_region, "codigo_region", 2)
        if invalid_region > 0:
            errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    personales = {"rut", "rutdv", "run", "domicilio", "fecha_nacimiento", "email", "fono"}
    if personales & {c.lower() for c in df.columns}:
        errors.append("el dataset contiene columnas de datos personales (línea roja)")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("autoridades_electas source_mode is fallback; usando snapshot versionado.")

    return {
        "dataset": "autoridades_electas",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }
