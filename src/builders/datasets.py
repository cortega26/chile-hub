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


def _latest_vitales_summary(df_vitales):
    """Crecimiento natural (nacimientos − defunciones) del último año con datos.

    Retorna None si el upstream no está disponible; el llamador agrega las
    columnas como nulas para mantener el esquema estable.
    """
    if df_vitales is None or df_vitales.height == 0:
        return None
    ultimo = df_vitales["anio"].max()
    return (
        df_vitales.filter(pl.col("anio") == ultimo)
        .group_by("codigo_comuna")
        .agg(
            pl.col("cantidad").filter(pl.col("evento") == "nacimiento").sum().alias("nacimientos"),
            pl.col("cantidad").filter(pl.col("evento") == "defuncion").sum().alias("defunciones"),
        )
        .with_columns(
            (pl.col("nacimientos").fill_null(0) - pl.col("defunciones").fill_null(0)).alias(
                "crecimiento_natural_ultimo_anio"
            ),
            pl.lit(ultimo).cast(pl.Int64).alias("anio_estadisticas_vitales"),
        )
        .select("codigo_comuna", "crecimiento_natural_ultimo_anio", "anio_estadisticas_vitales")
        .with_columns(pl.col("codigo_comuna").cast(pl.String))
    )


def _latest_permisos_summary(df_permisos):
    """Viviendas y superficie autorizadas del último año con datos."""
    if df_permisos is None or df_permisos.height == 0:
        return None
    ultimo = df_permisos["anio"].max()
    return (
        df_permisos.filter(pl.col("anio") == ultimo)
        .select(
            "codigo_comuna",
            pl.col("unidades_total").alias("viviendas_autorizadas_ultimo_anio"),
            pl.col("superficie_m2_total").alias("superficie_autorizada_m2_ultimo_anio"),
            pl.lit(ultimo).cast(pl.Int64).alias("anio_permisos_edificacion"),
        )
        .with_columns(pl.col("codigo_comuna").cast(pl.String))
    )


def _latest_calidad_summary(df_calidad):
    """MP2.5 promedio del último año con datos (media de medias diarias).

    Solo comunas con estación traen valor; el resto queda nulo (igual que
    valor_promedio_siedu para comunas fuera de la cobertura SIEDU).
    """
    if df_calidad is None or df_calidad.height == 0:
        return None
    with_anio = df_calidad.with_columns(
        pl.col("fecha").str.slice(0, 4).cast(pl.Int64).alias("anio")
    )
    ultimo = with_anio["anio"].max()
    return (
        with_anio.filter((pl.col("anio") == ultimo) & (pl.col("codigo_contaminante") == "mp25"))
        .group_by("codigo_comuna")
        .agg(pl.col("valor_promedio_diario").mean().alias("mp25_promedio_ultimo_anio"))
        .with_columns(
            pl.col("codigo_comuna").cast(pl.String),
            pl.lit(ultimo).cast(pl.Int64).alias("anio_calidad_aire"),
        )
    )


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
    df_vitales=None,
    df_permisos=None,
    df_calidad=None,
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
    vitales_summary = _latest_vitales_summary(df_vitales)
    permisos_summary = _latest_permisos_summary(df_permisos)
    calidad_summary = _latest_calidad_summary(df_calidad)

    perfil = (
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
    )
    if vitales_summary is not None:
        perfil = perfil.join(vitales_summary, on="codigo_comuna", how="left")
    else:
        perfil = perfil.with_columns(
            pl.lit(None, dtype=pl.Int64).alias("crecimiento_natural_ultimo_anio"),
            pl.lit(None, dtype=pl.Int64).alias("anio_estadisticas_vitales"),
        )
    if permisos_summary is not None:
        perfil = perfil.join(permisos_summary, on="codigo_comuna", how="left")
    else:
        perfil = perfil.with_columns(
            pl.lit(None, dtype=pl.Int64).alias("viviendas_autorizadas_ultimo_anio"),
            pl.lit(None, dtype=pl.Int64).alias("superficie_autorizada_m2_ultimo_anio"),
            pl.lit(None, dtype=pl.Int64).alias("anio_permisos_edificacion"),
        )
    if calidad_summary is not None:
        perfil = perfil.join(calidad_summary, on="codigo_comuna", how="left")
    else:
        perfil = perfil.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("mp25_promedio_ultimo_anio"),
            pl.lit(None, dtype=pl.Int64).alias("anio_calidad_aire"),
        )
    return perfil.with_columns(
        pl.col("establecimientos_salud_total").fill_null(0).cast(pl.Int64),
        pl.col("establecimientos_educacionales_total").fill_null(0).cast(pl.Int64),
        pl.col("indicadores_siedu_total").fill_null(0).cast(pl.Int64),
    ).sort("codigo_comuna")
