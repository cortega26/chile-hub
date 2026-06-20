"""Builders de datasets derivados a partir de capas ya validadas.

Construyen capas geográficas y el perfil territorial comunal combinando
DataFrames de Polars de otros datasets del hub.
"""

import polars as pl


def derive_geography_layers(df_comunas):
    df_regiones = (
        df_comunas.select(["codigo_region", "nombre_region"]).unique().sort("codigo_region")
    )
    df_provincias = (
        df_comunas.select(
            ["codigo_region", "nombre_region", "codigo_provincia", "nombre_provincia"]
        )
        .unique()
        .sort(["codigo_region", "codigo_provincia"])
    )
    return df_regiones, df_provincias


def build_perfil_territorial_comunal(
    df_comunas,
    df_censo,
    df_censo_hogares,
    df_salud,
    df_educacionales,
    df_electoral,
    df_finanzas,
    df_resultados,
    df_siedu,
):
    salud_counts = (
        df_salud.group_by("codigo_comuna")
        .agg(pl.len().alias("establecimientos_salud_total"))
        .with_columns(pl.col("codigo_comuna").cast(pl.String))
    )
    educ_counts = (
        df_educacionales.group_by("codigo_comuna")
        .agg(pl.len().alias("establecimientos_educacionales_total"))
        .with_columns(pl.col("codigo_comuna").cast(pl.String))
    )
    latest_finanzas = (
        df_finanzas.sort(["codigo_comuna", "anio"])
        .group_by("codigo_comuna")
        .tail(1)
        .select(
            "codigo_comuna",
            pl.col("anio").alias("anio_finanzas"),
            "ingresos_totales",
            "gastos_totales",
            "ingresos_propios_permanentes",
            "fondo_comun_municipal",
            "gasto_personal",
            "gasto_inversion",
        )
    )
    latest_resultados = (
        df_resultados.sort(["codigo_comuna", "anio"])
        .group_by("codigo_comuna")
        .tail(1)
        .select(
            "codigo_comuna",
            pl.col("anio").alias("anio_resultados_educacionales"),
            "matricula_total",
            "asistencia_promedio",
            "tasa_aprobacion",
            "tasa_reprobacion",
            "tasa_retiro",
            "establecimientos_reportados",
        )
    )
    siedu_summary = (
        df_siedu.group_by("codigo_comuna")
        .agg(
            pl.col("codigo_indicador").n_unique().alias("indicadores_siedu_total"),
            pl.col("valor").mean().alias("valor_promedio_siedu"),
        )
        .with_columns(pl.col("codigo_comuna").cast(pl.String))
    )

    return (
        df_comunas.join(
            df_censo.select(
                "codigo_comuna",
                "poblacion_censada",
                pl.col("hombres").alias("poblacion_hombres"),
                pl.col("mujeres").alias("poblacion_mujeres"),
                "poblacion_0_14",
                "poblacion_15_29",
                "poblacion_30_44",
                "poblacion_45_64",
                "poblacion_65_mas",
            ),
            on="codigo_comuna",
            how="left",
        )
        .join(
            df_censo_hogares.select(
                "codigo_comuna",
                "viviendas_censadas",
                "hogares_censados",
                pl.col("promedio_personas_hogar").alias("promedio_personas_por_hogar"),
            ),
            on="codigo_comuna",
            how="left",
        )
        .join(salud_counts, on="codigo_comuna", how="left")
        .join(educ_counts, on="codigo_comuna", how="left")
        .join(
            df_electoral.select(
                "codigo_comuna", "distrito_electoral", "circunscripcion_senatorial"
            ),
            on="codigo_comuna",
            how="left",
        )
        .join(latest_finanzas, on="codigo_comuna", how="left")
        .join(latest_resultados, on="codigo_comuna", how="left")
        .join(siedu_summary, on="codigo_comuna", how="left")
        .with_columns(
            pl.col("establecimientos_salud_total").fill_null(0).cast(pl.Int64),
            pl.col("establecimientos_educacionales_total").fill_null(0).cast(pl.Int64),
            pl.col("indicadores_siedu_total").fill_null(0).cast(pl.Int64),
        )
        .sort("codigo_comuna")
    )
