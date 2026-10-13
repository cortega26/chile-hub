"""Validadores económicos (plan 135)."""

from typing import Any

import polars as pl

from ._anomalias import detect_series_anomalies
from ._constants import EXPECTED_INDICATOR_CODES
from ._helpers import (
    _add_expected_warning,
    _duplicate_count,
    _invalid_fixed_length_count,
    _missing_columns,
    _negative_numeric_count,
    _percentage_out_of_bounds_count,
    _unknown_codes,
    _validate_ruts_column,
)


def validate_indicadores(
    df_indicadores: pl.DataFrame, metadata: dict[str, Any] | None
) -> dict[str, Any]:
    errors = []
    warnings = []
    row_count = df_indicadores.height
    codes = set(df_indicadores["codigo_indicador"].unique().to_list())
    missing_codes = sorted(EXPECTED_INDICATOR_CODES - codes)

    if row_count == 0:
        errors.append("indicadores dataset is empty")

    if missing_codes:
        errors.append(f"missing expected indicator codes: {', '.join(missing_codes)}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "indicadores source_mode is fallback; values are synthetic development data"
        )
    if metadata and metadata.get("raw_recoveries"):
        warnings.append(
            "indicadores live refresh reused raw snapshots for: "
            + ", ".join(metadata["raw_recoveries"])
        )
    if metadata and metadata.get("preserved_existing_pairs"):
        warnings.append(
            "indicadores live refresh preserved previous staging rows for: "
            + ", ".join(metadata["preserved_existing_pairs"])
        )
    if metadata and metadata.get("empty_live_pairs"):
        warnings.append(
            "indicadores live refresh returned empty series for: "
            + ", ".join(metadata["empty_live_pairs"])
        )
    if metadata and metadata.get("published_backfills"):
        warnings.append(
            "indicadores live refresh reused last published artifact for missing codes: "
            + ", ".join(metadata["published_backfills"])
        )

    anomalies = detect_series_anomalies(df_indicadores) if row_count > 0 else []
    for anomaly in anomalies:
        warnings.append(f"indicadores anomaly: {anomaly['motivo']}")

    return {
        "dataset": "indicadores",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "indicator_codes": sorted(codes),
        "anomalies": anomalies,
    }


def validate_finanzas_municipales(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    warnings = []
    required = [
        "anio",
        "codigo_comuna",
        "nombre_comuna",
        "ingresos_totales",
        "gastos_totales",
        "ingresos_propios_permanentes",
        "fondo_comun_municipal",
        "gasto_personal",
        "gasto_inversion",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"finanzas_municipales missing columns: {', '.join(missing)}")
    if df.height == 0:
        errors.append("finanzas_municipales dataset is empty")
    if not missing:
        duplicates = _duplicate_count(df, ["anio", "codigo_comuna"])
        if duplicates:
            errors.append(f"anio + codigo_comuna must be unique, found {duplicates} duplicates")
        invalid = _invalid_fixed_length_count(df, "codigo_comuna", 5)
        if invalid:
            errors.append(f"found {invalid} invalid codigo_comuna values")
        unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
        if unknown:
            errors.append(f"finanzas_municipales references unknown communes: {unknown}")
        negative = _negative_numeric_count(
            df,
            [
                "ingresos_totales",
                "gastos_totales",
                "ingresos_propios_permanentes",
                "fondo_comun_municipal",
                "gasto_personal",
                "gasto_inversion",
            ],
        )
        if negative:
            errors.append(f"found {negative} negative municipal finance values")
    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("finanzas_municipales source_mode is fallback; review before publication")
    return {
        "dataset": "finanzas_municipales",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": warnings,
    }


def validate_empresas(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de empresas (Registro de Empresas y Sociedades).

    Verifica:
    - DataFrame no vacío
    - RUT presente y sin duplicados (una misma razón social + RUT puede
      aparecer más de una vez si tiene múltiples constituciones)
    - Columnas requeridas presentes
    - Tipos de sociedad válidos
    - Fechas dentro de rangos esperados (2013+)
    - Capital no negativo
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    row_count = df.height

    required = [
        "rut",
        "razon_social",
        "codigo_sociedad",
        "fecha_registro",
        "anio",
        "comuna_tributaria",
        "region_tributaria",
    ]
    if row_count == 0:
        errors.append("empresas dataset is empty")
        return {
            "dataset": "empresas",
            "status": "error",
            "record_count": 0,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"empresas missing columns: {', '.join(missing)}")
        return {
            "dataset": "empresas",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    # RUT: no nulos, formato esperado (con guion)
    null_ruts = df["rut"].is_null().sum()
    if null_ruts:
        errors.append(f"found {null_ruts} null RUT values")

    # RUT: validación de formato y dígito verificador (vectorizada)
    format_bad, dv_bad = _validate_ruts_column(df["rut"])
    if format_bad > 0:
        warnings.append(f"found {format_bad} RUTs with invalid format")
    if dv_bad > 0:
        warnings.append(f"found {dv_bad} RUTs with invalid check digit")

    # Duplicados exactos (mismo RUT + misma razon social + misma fecha)
    dup_keys = df.select(["rut", "razon_social", "fecha_registro"])
    dup_count = _duplicate_count(dup_keys, ["rut", "razon_social", "fecha_registro"])
    if dup_count > 0:
        warnings.append(f"found {dup_count} duplicate (rut, razon_social, fecha_registro) rows")

    # Tipo de sociedad: códigos conocidos
    known_sociedad = {
        "SRL",
        "SPA",
        "EIRL",
        "SA",
        "SC",
        "SCPA",
        "SCA",
        "COOP",
        "EE",
        "FNDC",
        "AGR",
        "COPROP",
    }
    if "codigo_sociedad" in df.columns:
        # La fuente alterna el casing del mismo código ("SpA" vs "SPA"), así que
        # se compara normalizado. NO se reescribe el valor almacenado: el dato
        # publicado conserva lo que dice la fuente (issue #42).
        unknown_soc = {
            value
            for value in df["codigo_sociedad"].drop_nulls().unique().to_list()
            if value.upper() not in known_sociedad
        }
        if unknown_soc:
            warnings.append(f"unknown sociedad codes (new types?): {sorted(unknown_soc)}")

    # Fechas: anio >= 2013 (RES comenzo en mayo 2013)
    if "anio" in df.columns:
        invalid_anio = df.filter(pl.col("anio").is_null() | (pl.col("anio") < 2013)).height
        if invalid_anio:
            errors.append(f"found {invalid_anio} rows with anio < 2013 or null")

    # Capital: no negativo
    if "capital" in df.columns:
        negative_capital = df.filter(
            pl.col("capital").is_not_null() & (pl.col("capital") < 0)
        ).height
        if negative_capital:
            errors.append(f"found {negative_capital} rows with negative capital")

    # Códigos de región tributaria: deben ser 2 dígitos
    if "region_tributaria" in df.columns:
        invalid_region = df.filter(
            pl.col("region_tributaria").is_not_null()
            & (pl.col("region_tributaria").str.len_chars() != 2)
        ).height
        if invalid_region:
            errors.append(f"found {invalid_region} invalid region_tributaria values")

    # Cobertura acotada al regimen simplificado: es el alcance de la fuente por
    # diseño (la RES no registra el regimen tradicional), no una degradación.
    # Declarado como esperado en el emisor, según ADR-014.
    _add_expected_warning(
        warnings,
        expected_warnings,
        "RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). "
        "No incluye empresas del regimen tradicional (Diario Oficial) ni "
        "empresas anteriores a mayo 2013.",
    )

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("empresas source_mode is fallback; dataset may be incomplete or stale")

    return {
        "dataset": "empresas",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }


def validate_consumo_electrico_comunal(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de consumo eléctrico comunal (CNE / Energía Abierta).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (codigo_comuna, anio, tipo_cliente)
    - consumo_kwh >= 0
    - Formato de códigos CUT
    - Comunas desconocidas (warning)
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height

    required = [
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        "anio",
        "tipo_cliente",
        "consumo_kwh",
        "fuente",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "consumo_electrico_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    if row_count == 0:
        errors.append("dataset está vacío")
        return {
            "dataset": "consumo_electrico_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    # Duplicados de clave primaria
    dup_count = _duplicate_count(df, ["codigo_comuna", "anio", "tipo_cliente"])
    if dup_count > 0:
        errors.append(
            f"found {dup_count} duplicate rows by primary key (codigo_comuna, anio, tipo_cliente)"
        )

    # Formato de códigos CUT
    invalid_region = _invalid_fixed_length_count(df, "codigo_region", 2)
    if invalid_region > 0:
        errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    # Consumo no negativo
    neg_consumo = _negative_numeric_count(df, ["consumo_kwh"])
    if neg_consumo > 0:
        errors.append(f"found {neg_consumo} rows with negative consumo_kwh")

    # Número de clientes no negativo (si existe)
    if "numero_clientes" in df.columns:
        neg_clientes = df.filter(
            pl.col("numero_clientes").is_not_null() & (pl.col("numero_clientes") < 0)
        ).height
        if neg_clientes > 0:
            warnings.append(f"found {neg_clientes} rows with negative numero_clientes")

    # Comunas desconocidas (warning — puede haber municipios nuevos)
    if valid_commune_codes is not None:
        unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
        if unknown:
            warnings.append(
                f"consumo_electrico_comunal references {len(unknown)} communes not in DPA: {unknown}"
            )

    # Verificar que hay tipos de cliente razonables
    tipos = df["tipo_cliente"].drop_nulls().unique().to_list()
    if not tipos:
        warnings.append("no se encontraron tipos de cliente")
    else:
        warnings.append(f"tipos de cliente: {sorted(tipos)}")

    # Años razonables
    years = df["anio"].drop_nulls().unique().to_list()
    if years:
        warnings.append(f"años disponibles: {sorted(years)}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima."
        )

    return {
        "dataset": "consumo_electrico_comunal",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }


def validate_pobreza_comunal(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de pobreza comunal (CASEN / SAE).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (codigo_comuna, anio, dimension)
    - Rangos de tasa (0-100)
    - Formato de códigos CUT
    - Comunas desconocidas (warning, no error — la cobertura es parcial por diseño)
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    row_count = df.height

    required = [
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        "anio",
        "dimension",
        "tasa",
        "limite_inferior",
        "limite_superior",
        "metodologia",
        "fuente",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "pobreza_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    if row_count == 0:
        errors.append("dataset está vacío")
        return {
            "dataset": "pobreza_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    # Duplicados de clave primaria
    dup_count = _duplicate_count(df, ["codigo_comuna", "anio", "dimension"])
    if dup_count > 0:
        errors.append(
            f"found {dup_count} duplicate rows by primary key (codigo_comuna, anio, dimension)"
        )

    # Formato de códigos CUT
    invalid_region = _invalid_fixed_length_count(df, "codigo_region", 2)
    if invalid_region > 0:
        errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    # Rangos de tasa (0-100%)
    out_of_bounds = _percentage_out_of_bounds_count(
        df, ["tasa", "limite_inferior", "limite_superior"]
    )
    if out_of_bounds > 0:
        errors.append(f"found {out_of_bounds} values outside 0-100 range in tasa/intervalos")

    # Comunas desconocidas (warning — cobertura parcial por diseño SAE)
    if valid_commune_codes is not None:
        unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
        if unknown:
            warnings.append(
                f"pobreza_comunal references {len(unknown)} communes not in DPA: {unknown}"
            )

    # Dimensiones esperadas
    valid_dims = {"ingresos", "multidimensional"}
    actual_dims = set(df["dimension"].drop_nulls().unique().to_list())
    unexpected_dims = actual_dims - valid_dims
    if unexpected_dims:
        warnings.append(f"dimensiones inesperadas: {unexpected_dims}")

    # Advertencia de cobertura parcial (por diseño SAE)
    comunas_con_dato = df["codigo_comuna"].n_unique()
    if valid_commune_codes is not None and len(valid_commune_codes) > 0:
        coverage_pct = round(comunas_con_dato / len(valid_commune_codes) * 100, 1)
        _add_expected_warning(
            warnings,
            expected_warnings,
            f"cobertura SAE: {comunas_con_dato}/{len(valid_commune_codes)} comunas "
            f"({coverage_pct}%) — parcial por diseño; comunas sin muestra no tienen estimación",
        )

    # Verificar que el año es razonable
    years = df["anio"].drop_nulls().unique().to_list()
    future_years = [y for y in years if y > 2026]
    if future_years:
        warnings.append(f"años futuros detectados: {future_years}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("pobreza_comunal source_mode is fallback; usando datos de muestra mínima.")

    return {
        "dataset": "pobreza_comunal",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }
