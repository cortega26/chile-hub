"""Validadores territoriales y urbanos (plan 135)."""

import datetime
from typing import Any

import polars as pl

from ._constants import (
    _CATEGORIAS_VALIDAS,
    _CHILE_LAT_MAX,
    _CHILE_LAT_MIN,
    _CHILE_LON_MAX,
    _CHILE_LON_MIN,
)
from ._helpers import (
    _add_expected_warning,
    _duplicate_count,
    _invalid_fixed_length_count,
    _missing_columns,
    _unknown_codes,
)


def validate_indicadores_urbanos_siedu(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    required = [
        "anio",
        "codigo_comuna",
        "codigo_indicador",
        "nombre_indicador",
        "categoria",
        "valor",
        "unidad",
        "fuente_original",
        "cobertura_tipo",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"indicadores_urbanos_siedu missing columns: {', '.join(missing)}")
    if df.height == 0:
        errors.append("indicadores_urbanos_siedu dataset is empty")
    if not missing:
        duplicates = _duplicate_count(df, ["anio", "codigo_comuna", "codigo_indicador"])
        if duplicates:
            errors.append(
                "anio + codigo_comuna + codigo_indicador must be unique, "
                f"found {duplicates} duplicates"
            )
        invalid = _invalid_fixed_length_count(df, "codigo_comuna", 5)
        if invalid:
            errors.append(f"found {invalid} invalid codigo_comuna values")
        unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
        if unknown:
            errors.append(f"indicadores_urbanos_siedu references unknown communes: {unknown}")
        all_null = (
            df.group_by("codigo_indicador")
            .agg(pl.col("valor").is_not_null().sum().alias("non_null_values"))
            .filter(pl.col("non_null_values") == 0)
            .height
        )
        if all_null:
            errors.append(f"found {all_null} SIEDU indicators with all-null values")
    if metadata and metadata.get("coverage", {}).get("status") in {"partial_expected", "partial"}:
        _add_expected_warning(
            warnings,
            expected_warnings,
            "indicadores_urbanos_siedu has intentionally partial urban coverage",
        )
    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "indicadores_urbanos_siedu source_mode is fallback; review before publication"
        )
    return {
        "dataset": "indicadores_urbanos_siedu",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }


def validate_perfil_territorial_comunal(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if df.height != 346:
        errors.append(f"perfil_territorial_comunal expected 346 communes, found {df.height}")
    if df.height and df.height - df["codigo_comuna"].n_unique() > 0:
        errors.append("codigo_comuna must be unique in perfil_territorial_comunal")
    if df.height and _invalid_fixed_length_count(df, "codigo_comuna", 5):
        errors.append("perfil_territorial_comunal contains invalid codigo_comuna values")
    unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
    if unknown:
        errors.append(f"perfil_territorial_comunal references unknown communes: {unknown}")
    duplicated_columns = sorted({column for column in df.columns if df.columns.count(column) > 1})
    if duplicated_columns:
        errors.append(f"perfil_territorial_comunal has duplicate columns: {duplicated_columns}")
    for rate_col in (
        "tasa_pobreza_ingresos_ultimo_anio",
        "tasa_pobreza_multidimensional_ultimo_anio",
    ):
        if rate_col in df.columns and df.height:
            out_of_range = df.filter(
                pl.col(rate_col).is_not_null() & ((pl.col(rate_col) < 0) | (pl.col(rate_col) > 100))
            ).height
            if out_of_range:
                errors.append(
                    f"perfil_territorial_comunal {rate_col} out of 0-100 range "
                    f"in {out_of_range} rows"
                )
    if metadata and metadata.get("notes"):
        warnings.extend(
            note for note in metadata.get("notes", []) if "metric_unavailable" in str(note)
        )
    return {
        "dataset": "perfil_territorial_comunal",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": warnings,
    }


def validate_puntos_interes(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de puntos de interes (OpenStreetMap).

    Verifica:
    - DataFrame no vacío
    - osm_id único
    - Coordenadas dentro del bounding box de Chile
    - categoría en el conjunto conocido
    - direccion presente (warning si muchas nulas)
    - codigo_comuna con formato CUT (5 caracteres) si está presente
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height

    required = [
        "osm_id",
        "nombre",
        "categoria",
        "tipo",
        "latitud",
        "longitud",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"puntos_interes missing columns: {', '.join(missing)}")

    if row_count == 0:
        errors.append("puntos_interes dataset is empty")
        return {
            "dataset": "puntos_interes",
            "status": "error",
            "record_count": 0,
            "errors": errors,
            "warnings": warnings,
        }

    # Unicidad de osm_id
    dup_ids = _duplicate_count(df, ["osm_id"])
    if dup_ids > 0:
        errors.append(f"osm_id must be unique, found {dup_ids} duplicates")

    # Coordenadas dentro de Chile
    out_of_bounds = df.filter(
        (pl.col("latitud") < _CHILE_LAT_MIN)
        | (pl.col("latitud") > _CHILE_LAT_MAX)
        | (pl.col("longitud") < _CHILE_LON_MIN)
        | (pl.col("longitud") > _CHILE_LON_MAX)
    ).height
    if out_of_bounds > 0:
        errors.append(f"found {out_of_bounds} POIs with coordinates outside Chile bounds")

    # Categoria válida
    if "categoria" in df.columns:
        invalid_cats = set(df["categoria"].drop_nulls().unique().to_list()) - _CATEGORIAS_VALIDAS
        if invalid_cats:
            errors.append(f"unknown categoria values: {sorted(invalid_cats)}")

    # Direccion: warning si mas del 50% estan vacias
    if "direccion" in df.columns:
        null_dir = df["direccion"].is_null().sum() + df.filter(pl.col("direccion") == "").height
        if null_dir > row_count * 0.5:
            errors.append(f"more than 50% POIs missing address ({null_dir}/{row_count})")
        elif null_dir > 0:
            warnings.append(f"{null_dir}/{row_count} POIs without street address")

    # codigo_comuna: warning si mas del 90% son nulos
    if "codigo_comuna" in df.columns:
        null_comuna = df["codigo_comuna"].is_null().sum()
        if null_comuna > row_count * 0.9:
            warnings.append(
                f"DPA cross-reference resolved <10% of communes "
                f"({row_count - null_comuna}/{row_count}). "
                "Verify that comunas.csv is in staging before running this extractor."
            )
        elif null_comuna > 0:
            warnings.append(
                f"{null_comuna}/{row_count} POIs without codigo_comuna (commune not matched in DPA)"
            )

        # Validar formato CUT para los que SI tienen codigo
        if null_comuna < row_count:
            invalid_cut = df.filter(
                pl.col("codigo_comuna").is_not_null()
                & (pl.col("codigo_comuna").cast(pl.String).str.len_chars() != 5)
            ).height
            if invalid_cut:
                errors.append(
                    f"found {invalid_cut} invalid codigo_comuna values (must be 5-char string)"
                )

        # Integridad referencial con DPA
        if valid_commune_codes is not None:
            unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
            if unknown:
                warnings.append(f"puntos_interes references unknown communes: {unknown}")

    # Cobertura: siempre parcial por diseno
    warnings.append(
        "OSM coverage is partial by design: higher density in urban areas, "
        "limited in rural areas. Not a census."
    )

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "puntos_interes source_mode is fallback; embedded sample with no statistical value."
        )

    return {
        "dataset": "puntos_interes",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }


def validate_geometria_comunal(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de geometría comunal (límites poligonales, BCN ArcGIS).

    Carril CANDIDATE — cobertura parcial es esperada por diseño (un warning, no
    un error): la fuente BCN no expone geometría para `codigo_comuna=12202`
    (Antártica), el mismo hueco que `subdere_extractor.py` ya suplementa a mano
    para el dataset `comunas`. La integridad referencial (todo código presente
    aquí debe existir en el DPA) sí es un error — ver ADR-012.
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height

    required = [
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        "nombre_comuna_clean",
        "nombre_region",
        "geometry_wkt",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "geometria_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    if row_count == 0:
        errors.append("geometria_comunal dataset is empty")
        return {
            "dataset": "geometria_comunal",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    dup_count = _duplicate_count(df, ["codigo_comuna"])
    if dup_count > 0:
        errors.append(f"codigo_comuna must be unique, found {dup_count} duplicate rows")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    empty_geom = df.filter(
        pl.col("geometry_wkt").is_null() | (pl.col("geometry_wkt").str.len_chars() == 0)
    ).height
    if empty_geom > 0:
        errors.append(f"found {empty_geom} rows with empty geometry_wkt")

    unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
    if unknown:
        errors.append(f"geometria_comunal references unknown communes: {unknown}")

    if row_count < 340:
        warnings.append(
            f"solo {row_count}/346 comunas con geometría — cobertura parcial "
            "(candidate; la fuente BCN no cubre codigo_comuna=12202/Antártica)"
        )

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("geometria_comunal source_mode is fallback; usando snapshot versionado.")

    return {
        "dataset": "geometria_comunal",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }


def validate_permisos_edificacion(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de permisos de edificación por comuna (MINVU CEDOC).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (anio, codigo_comuna)
    - Métricas enteras no negativas y sin nulos
    - Consistencia interna: total == casas + departamentos (unidades y m2).
      La fuente publica el total como suma exacta de ambas tipologías.
    - Formato de códigos CUT
    - Integridad referencial con la DPA (error: cobertura total esperada)
    - Cobertura: cada anio debe traer las 346 comunas (solo en modo
      live; en fallback la muestra mínima es esperada por diseño).
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height
    is_live = not metadata or metadata.get("source_mode") != "fallback"

    metric_columns = [
        "unidades_total",
        "superficie_m2_total",
        "unidades_casas",
        "superficie_m2_casas",
        "unidades_departamentos",
        "superficie_m2_departamentos",
    ]
    required = [
        "anio",
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        *metric_columns,
        "estado_dato",
        "fuente",
        "url_fuente",
        "fecha_fuente",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "permisos_edificacion",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    if row_count == 0:
        errors.append("permisos_edificacion dataset is empty")
        return {
            "dataset": "permisos_edificacion",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    # Duplicados de clave primaria
    dup_count = _duplicate_count(df, ["anio", "codigo_comuna"])
    if dup_count > 0:
        errors.append(f"found {dup_count} duplicate rows by primary key (anio, codigo_comuna)")

    # Formato de códigos CUT
    invalid_region = _invalid_fixed_length_count(df, "codigo_region", 2)
    if invalid_region > 0:
        errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    # Métricas: sin nulos ni negativos
    for col in metric_columns:
        null_count = df.filter(pl.col(col).is_null()).height
        if null_count > 0:
            errors.append(f"found {null_count} rows with null {col}")
        negative_count = df.filter(pl.col(col) < 0).height
        if negative_count > 0:
            errors.append(f"found {negative_count} rows with negative {col}")

    # Consistencia interna total == casas + departamentos
    bad_unidades = df.filter(
        pl.col("unidades_total") != pl.col("unidades_casas") + pl.col("unidades_departamentos")
    ).height
    if bad_unidades > 0:
        errors.append(f"found {bad_unidades} rows where unidades_total != casas + departamentos")
    bad_m2 = df.filter(
        pl.col("superficie_m2_total")
        != pl.col("superficie_m2_casas") + pl.col("superficie_m2_departamentos")
    ).height
    if bad_m2 > 0:
        errors.append(f"found {bad_m2} rows where superficie_m2_total != casas + departamentos")

    # Dominio de estado_dato
    valid_estados = {"definitivo", "provisional"}
    unexpected_estados = set(df["estado_dato"].drop_nulls().unique().to_list()) - valid_estados
    if unexpected_estados:
        errors.append(f"unexpected estado_dato values: {sorted(unexpected_estados)}")

    # Integridad referencial con la DPA
    unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
    if unknown:
        errors.append(f"permisos_edificacion references unknown communes: {unknown}")

    # Cobertura total por año: 346 comunas, sin excepción (solo en live:
    # en fallback la muestra mínima es esperada por diseño).
    if valid_commune_codes and is_live:
        expected = len(valid_commune_codes)
        coverage = df.group_by(["anio"]).agg(pl.col("codigo_comuna").n_unique().alias("comunas"))
        incomplete = coverage.filter(pl.col("comunas") != expected)
        for row in incomplete.iter_rows(named=True):
            errors.append(
                f"cobertura incompleta: anio={row['anio']} trae {row['comunas']}/{expected} comunas"
            )

    if not is_live:
        warnings.append("permisos_edificacion source_mode no es live; cobertura parcial esperada.")

    # Años razonables (serie desde 2002)
    current_year = datetime.datetime.now(datetime.UTC).year
    years = df["anio"].drop_nulls().unique().to_list()
    odd_years = sorted(y for y in years if y < 2002 or y > current_year + 1)
    if odd_years:
        warnings.append(f"años fuera del rango esperado [2002, {current_year + 1}]: {odd_years}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "permisos_edificacion source_mode is fallback; usando datos de muestra mínima."
        )

    return {
        "dataset": "permisos_edificacion",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }


def validate_calidad_aire(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de calidad del aire por estación (SINCA / MMA).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (fecha, id_estacion, codigo_contaminante)
    - Dominios cerrados: codigo_contaminante, estado_dato
    - Métricas no negativas y sin nulos; horas_validas >= 1
    - Formato de fecha ISO y de códigos CUT
    - Integridad referencial con la DPA (error: toda comuna presente debe
      existir; la cobertura parcial es esperada por diseño y va como warning
      declarado, no como error — mismo patrón que SIEDU).
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected_warnings: list[str] = []
    row_count = df.height

    required = [
        "fecha",
        "id_estacion",
        "nombre_estacion",
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        "codigo_contaminante",
        "nombre_contaminante",
        "unidad",
        "valor_promedio_diario",
        "valor_max_horario",
        "horas_validas",
        "estado_dato",
        "fuente",
        "url_fuente",
        "fecha_fuente",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "calidad_aire",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    if row_count == 0:
        errors.append("calidad_aire dataset is empty")
        return {
            "dataset": "calidad_aire",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
            "expected_warnings": expected_warnings,
        }

    # Duplicados de clave primaria
    dup_count = _duplicate_count(df, ["fecha", "id_estacion", "codigo_contaminante"])
    if dup_count > 0:
        errors.append(
            f"found {dup_count} duplicate rows by primary key "
            "(fecha, id_estacion, codigo_contaminante)"
        )

    # Formato de códigos CUT
    invalid_region = _invalid_fixed_length_count(df, "codigo_region", 2)
    if invalid_region > 0:
        errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    # Dominios cerrados
    valid_contaminantes = {"mp25", "mp10", "so2", "no2", "co", "o3"}
    unexpected = set(df["codigo_contaminante"].drop_nulls().unique().to_list())
    unexpected -= valid_contaminantes
    if unexpected:
        errors.append(f"unexpected codigo_contaminante values: {sorted(unexpected)}")

    valid_estados = {"definitivo", "provisional"}
    unexpected_estados = set(df["estado_dato"].drop_nulls().unique().to_list()) - valid_estados
    if unexpected_estados:
        errors.append(f"unexpected estado_dato values: {sorted(unexpected_estados)}")

    # Métricas: sin nulos, no negativas, al menos 1 hora válida
    for col in ("valor_promedio_diario", "valor_max_horario"):
        null_count = df.filter(pl.col(col).is_null()).height
        if null_count > 0:
            errors.append(f"found {null_count} rows with null {col}")
        negative_count = df.filter(pl.col(col) < 0).height
        if negative_count > 0:
            errors.append(f"found {negative_count} rows with negative {col}")
    zero_hours = df.filter(pl.col("horas_validas") < 1).height
    if zero_hours > 0:
        errors.append(f"found {zero_hours} rows with horas_validas < 1")

    # Formato de fecha ISO
    bad_dates = df.filter(~pl.col("fecha").str.contains(r"^\d{4}-\d{2}-\d{2}$")).height
    if bad_dates > 0:
        errors.append(f"found {bad_dates} rows with non-ISO fecha")

    # Integridad referencial con la DPA
    unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
    if unknown:
        errors.append(f"calidad_aire references unknown communes: {unknown}")

    # Cobertura parcial por diseño (solo comunas con estación): warning
    # declarado como esperado, igual que SIEDU.
    if valid_commune_codes is not None and len(valid_commune_codes) > 0:
        comunas_con_dato = df["codigo_comuna"].n_unique()
        coverage_pct = round(comunas_con_dato / len(valid_commune_codes) * 100, 1)
        _add_expected_warning(
            warnings,
            expected_warnings,
            f"cobertura SINCA: {comunas_con_dato}/{len(valid_commune_codes)} comunas "
            f"({coverage_pct}%) — parcial por diseño; solo comunas con estación",
        )

    # Volumen de estaciones: caída brusca del inventario indica fuente rota.
    n_estaciones = df["id_estacion"].n_unique()
    if n_estaciones < 100:
        warnings.append(
            f"solo {n_estaciones} estaciones con datos (esperado ~125); "
            "posible caída parcial del SINCA"
        )

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("calidad_aire source_mode is fallback; usando datos de muestra mínima.")

    return {
        "dataset": "calidad_aire",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "expected_warnings": expected_warnings,
    }
