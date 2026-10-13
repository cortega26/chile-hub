"""Validadores de población: censo, hogares y estadísticas vitales (plan 135)."""

import datetime
from typing import Any

import polars as pl

from ._helpers import (
    _duplicate_count,
    _invalid_fixed_length_count,
    _missing_columns,
    _unknown_codes,
)


def validate_censo_comunal(
    df_censo: pl.DataFrame, metadata: dict[str, Any] | None
) -> dict[str, Any]:
    errors = []
    row_count = df_censo.height
    if row_count == 0:
        errors.append("censo_comunal dataset is empty")
    if row_count != 346:
        errors.append(f"censo_comunal expected 346 communes, found {row_count}")
    if row_count - df_censo["codigo_comuna"].n_unique() > 0:
        errors.append("codigo_comuna must be unique in censo_comunal")
    age_total = sum(
        df_censo[column]
        for column in (
            "poblacion_0_14",
            "poblacion_15_29",
            "poblacion_30_44",
            "poblacion_45_64",
            "poblacion_65_mas",
        )
    )
    if df_censo.filter(age_total != df_censo["poblacion_censada"]).height > 0:
        errors.append("age bands must sum to poblacion_censada")
    return {
        "dataset": "censo_comunal",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": [],
    }


def validate_censo_hogares_viviendas(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    errors = []
    if df.height != 346:
        errors.append(f"censo_hogares_viviendas expected 346 communes, found {df.height}")
    if df.height - df["codigo_comuna"].n_unique() > 0:
        errors.append("codigo_comuna must be unique in censo_hogares_viviendas")
    if valid_commune_codes is not None:
        unknown = set(df["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
        if unknown:
            errors.append(f"censo_hogares_viviendas references unknown communes: {sorted(unknown)}")
    inconsistent = df.filter(
        pl.col("viviendas_particulares_ocupadas")
        + pl.col("viviendas_particulares_desocupadas")
        + pl.col("viviendas_colectivas")
        != pl.col("viviendas_censadas")
    ).height
    if inconsistent:
        errors.append(f"housing totals are inconsistent for {inconsistent} communes")
    return {
        "dataset": "censo_hogares_viviendas",
        "status": "error" if errors else "ok",
        "record_count": df.height,
        "errors": errors,
        "warnings": [],
    }


def validate_estadisticas_vitales(
    df: pl.DataFrame,
    metadata: dict[str, Any] | None = None,
    valid_commune_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Valida el dataset de estadísticas vitales comunales (INE).

    Chequeos:
    - Columnas requeridas
    - Duplicados de clave primaria (anio, codigo_comuna, evento, sexo)
    - Dominios cerrados: evento, sexo, estado_dato
    - cantidad entera no negativa y sin nulos
    - Formato de códigos CUT
    - Integridad referencial con la DPA (error: cobertura total esperada)
    - Cobertura: cada (anio, evento) debe traer las 346 comunas (solo en
      modo live; en fallback la cobertura parcial es esperada por diseño).
    - Continuidad: sin años faltantes en la serie y ambos eventos por año
      (un año o evento ausente por completo no genera grupo incompleto y
      debe fallar igual).
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height
    is_live = not metadata or metadata.get("source_mode") != "fallback"

    required = [
        "anio",
        "codigo_region",
        "codigo_comuna",
        "nombre_comuna",
        "evento",
        "sexo",
        "cantidad",
        "estado_dato",
        "fuente",
        "url_fuente",
        "fecha_fuente",
    ]
    missing = _missing_columns(df, required)
    if missing:
        errors.append(f"missing required columns: {missing}")
        return {
            "dataset": "estadisticas_vitales",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    if row_count == 0:
        errors.append("estadisticas_vitales dataset is empty")
        return {
            "dataset": "estadisticas_vitales",
            "status": "error",
            "record_count": row_count,
            "errors": errors,
            "warnings": warnings,
        }

    # Duplicados de clave primaria
    dup_count = _duplicate_count(df, ["anio", "codigo_comuna", "evento", "sexo"])
    if dup_count > 0:
        errors.append(
            f"found {dup_count} duplicate rows by primary key (anio, codigo_comuna, evento, sexo)"
        )

    # Formato de códigos CUT
    invalid_region = _invalid_fixed_length_count(df, "codigo_region", 2)
    if invalid_region > 0:
        errors.append(f"found {invalid_region} codigo_region with invalid length (expected 2)")

    invalid_cut = _invalid_fixed_length_count(df, "codigo_comuna", 5)
    if invalid_cut > 0:
        errors.append(f"found {invalid_cut} codigo_comuna with invalid length (expected 5)")

    # Dominios cerrados
    valid_eventos = {"nacimiento", "defuncion"}
    unexpected_eventos = set(df["evento"].drop_nulls().unique().to_list()) - valid_eventos
    if unexpected_eventos:
        errors.append(f"unexpected evento values: {sorted(unexpected_eventos)}")

    valid_sexos = {"hombre", "mujer", "indeterminado", "total"}
    unexpected_sexos = set(df["sexo"].drop_nulls().unique().to_list()) - valid_sexos
    if unexpected_sexos:
        errors.append(f"unexpected sexo values: {sorted(unexpected_sexos)}")

    valid_estados = {"definitivo", "provisional"}
    unexpected_estados = set(df["estado_dato"].drop_nulls().unique().to_list()) - valid_estados
    if unexpected_estados:
        errors.append(f"unexpected estado_dato values: {sorted(unexpected_estados)}")

    # cantidad: entera, sin nulos, no negativa
    null_cantidad = df.filter(pl.col("cantidad").is_null()).height
    if null_cantidad > 0:
        errors.append(f"found {null_cantidad} rows with null cantidad")
    negative_cantidad = df.filter(pl.col("cantidad") < 0).height
    if negative_cantidad > 0:
        errors.append(f"found {negative_cantidad} rows with negative cantidad")

    # Integridad referencial con la DPA
    unknown = _unknown_codes(df, "codigo_comuna", valid_commune_codes)
    if unknown:
        errors.append(f"estadisticas_vitales references unknown communes: {unknown}")

    # Cobertura total por (anio, evento): 346 comunas, sin excepción.
    # Solo en modo live: en fallback la muestra mínima (2 comunas) es
    # esperada por diseño y el publish la rechaza por otra vía.
    if valid_commune_codes and is_live:
        expected = len(valid_commune_codes)
        coverage = df.group_by(["anio", "evento"]).agg(
            pl.col("codigo_comuna").n_unique().alias("comunas")
        )
        incomplete = coverage.filter(pl.col("comunas") != expected)
        for row in incomplete.iter_rows(named=True):
            errors.append(
                f"cobertura incompleta: anio={row['anio']} evento={row['evento']} "
                f"trae {row['comunas']}/{expected} comunas"
            )

    # Continuidad de la serie: un año o evento ausente por completo no
    # genera grupo incompleto, así que se verifica explícitamente. Un hueco
    # significa que un anuario no se parseó y la serie quedaría parcial.
    if is_live:
        years = sorted(df["anio"].drop_nulls().unique().to_list())
        if years and years != list(range(min(years), max(years) + 1)):
            errors.append(f"serie con años faltantes: {years}")
        eventos_por_anio = df.group_by(["anio"]).agg(pl.col("evento").unique().alias("eventos"))
        for row in eventos_por_anio.iter_rows(named=True):
            faltantes = valid_eventos - set(row["eventos"])
            if faltantes:
                errors.append(f"anio={row['anio']} sin eventos: {sorted(faltantes)}")

    if not is_live:
        warnings.append("estadisticas_vitales source_mode no es live; cobertura parcial esperada.")

    # Años razonables (serie de anuarios definitivos 2010 en adelante)
    current_year = datetime.datetime.now(datetime.UTC).year
    years = df["anio"].drop_nulls().unique().to_list()
    odd_years = sorted(y for y in years if y < 2010 or y > current_year)
    if odd_years:
        warnings.append(f"años fuera del rango esperado [2010, {current_year}]: {odd_years}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append(
            "estadisticas_vitales source_mode is fallback; usando datos de muestra mínima."
        )

    return {
        "dataset": "estadisticas_vitales",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }
