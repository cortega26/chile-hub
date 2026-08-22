"""Registro central de tipos de columnas para las lecturas de staging.

Cada entrada de ``STAGING_SCHEMAS`` preserva exactamente los tipos que
``build_dev_db.py`` y los extractores ya asumían de forma implícita, dispersos
antes en `schema_overrides` ad hoc repetidos en cada `pl.read_csv`. No
reconcilia inconsistencias entre datasets (p. ej. `anio` es `Int32` en unos y
`Int64` en otros) — armonizar tipos cambia el schema Parquet publicado y es
una decisión aparte, no un refactor.

`STAGING_DATE_COLUMNS` cubre las columnas de fecha que Polars no puede tipar
de forma confiable vía `schema_overrides` en un CSV (formato no-ISO): se leen
como string y se castean con `apply_date_casts()` después de la lectura.
"""

import polars as pl

STAGING_SCHEMAS: dict[str, dict[str, type[pl.DataType] | pl.DataType]] = {
    "comunas": {
        "codigo_region": pl.String,
        "codigo_provincia": pl.String,
        "codigo_comuna": pl.String,
    },
    "indicadores": {
        "codigo_indicador": pl.String,
        "valor": pl.Float64,
    },
    "censo_comunal": {
        "codigo_region": pl.String,
        "codigo_provincia": pl.String,
        "codigo_comuna": pl.String,
    },
    "establecimientos_salud": {
        "codigo_establecimiento": pl.String,
        "codigo_region": pl.String,
        "codigo_comuna": pl.String,
    },
    "censo_hogares_viviendas": {
        "codigo_region": pl.String,
        "codigo_provincia": pl.String,
        "codigo_comuna": pl.String,
    },
    "distritos_electorales": {
        "codigo_comuna": pl.String,
        "distrito_electoral": pl.String,
        "circunscripcion_senatorial": pl.String,
    },
    "establecimientos_educacionales": {
        "rbd": pl.String,
        "dv_rbd": pl.String,
        "codigo_region": pl.String,
        "codigo_comuna": pl.String,
    },
    "finanzas_municipales": {
        "anio": pl.Int32,
        "codigo_comuna": pl.String,
    },
    "resultados_educacionales": {
        "anio": pl.Int32,
        "codigo_comuna": pl.String,
    },
    "indicadores_urbanos_siedu": {
        "anio": pl.Int32,
        "codigo_comuna": pl.String,
        "codigo_indicador": pl.String,
        "valor": pl.Float64,
    },
    "empresas": {
        "rut": pl.String,
        "razon_social": pl.String,
        "codigo_sociedad": pl.String,
        "capital": pl.Int64,
        "anio": pl.Int32,
        "comuna_tributaria": pl.String,
        "region_tributaria": pl.String,
        "comuna_social": pl.String,
        "region_social": pl.String,
    },
    "pobreza_comunal": {
        "codigo_region": pl.String,
        "codigo_comuna": pl.String,
        "anio": pl.Int64,
        "tasa": pl.Float64,
        "limite_inferior": pl.Float64,
        "limite_superior": pl.Float64,
    },
    "consumo_electrico_comunal": {
        "codigo_region": pl.String,
        "codigo_comuna": pl.String,
        "anio": pl.Int64,
        "consumo_kwh": pl.Float64,
        "numero_clientes": pl.Int64,
    },
    "autoridades_electas": {
        "distrito_electoral": pl.String,
        "circunscripcion_senatorial": pl.String,
        "codigo_comuna": pl.String,
        "codigo_region": pl.String,
    },
}

STAGING_DATE_COLUMNS: dict[str, dict[str, str]] = {
    "empresas": {
        "fecha_actuacion": "%Y-%m-%d",
        "fecha_registro": "%Y-%m-%d",
        "fecha_aprobacion_sii": "%Y-%m-%d",
    },
}


def apply_date_casts(df: pl.DataFrame, dataset: str) -> pl.DataFrame:
    for col, fmt in STAGING_DATE_COLUMNS.get(dataset, {}).items():
        if col in df.columns:
            df = df.with_columns(pl.col(col).str.to_date(fmt, strict=False))
    return df
