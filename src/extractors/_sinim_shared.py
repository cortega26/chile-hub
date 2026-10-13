"""Lógica compartida de finanzas_municipales (Plan 099, TECHDEBT-03).

`normalize_rows`/`build_metadata` vivían duplicados en
`sinim_finanzas_extractor.py` (stub de fallback) y
`sinim_finanzas_live_extractor.py` (scraper real): cada fix de normalización o
provenance había que aplicarlo dos veces y las copias ya habían divergido
(docstrings, `source_detail`, `REUSE_POLICY`). Ambos extractores son ahora
wrappers delgados de fetch; la normalización y la metadata son una sola
implementación.

Lo que NO se comparte (a propósito): `REUSE_POLICY` (divergió entre stub y
scraper; se pasa por parámetro) ni nada del lado fetch
(`VARIABLE_COLUMN_MAP`, `_parse_xml_spreadsheet`, scraping). La muestra
`FALLBACK_ROWS` sí se comparte desde el plan 133a (auditoría 2026-10-13):
era byte-idéntica en ambos y podía derivar en silencio.
"""

from typing import Any

import polars as pl

try:
    from src.extractors.source_adapter import build_standard_metadata
except ModuleNotFoundError:  # ejecución como script (python src/extractors/*.py)
    from source_adapter import build_standard_metadata


# Muestra de respaldo curada (3 comunas con datos verificados). Única fuente:
# antes estaba copiada byte a byte en `sinim_finanzas_extractor` (stub) y
# `sinim_finanzas_live_extractor` (`_get_fallback_rows`).
FALLBACK_ROWS: list[dict[str, Any]] = [
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "ingresos_totales": 245000000000.0,
        "gastos_totales": 231000000000.0,
        "ingresos_propios_permanentes": 162000000000.0,
        "fondo_comun_municipal": 39000000000.0,
        "gasto_personal": 70500000000.0,
        "gasto_inversion": 28500000000.0,
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "nombre_comuna": "Viña del Mar",
        "ingresos_totales": 155000000000.0,
        "gastos_totales": 149000000000.0,
        "ingresos_propios_permanentes": 98000000000.0,
        "fondo_comun_municipal": 21000000000.0,
        "gasto_personal": 52300000000.0,
        "gasto_inversion": 17400000000.0,
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "ingresos_totales": 132000000000.0,
        "gastos_totales": 126000000000.0,
        "ingresos_propios_permanentes": 76500000000.0,
        "fondo_comun_municipal": 24500000000.0,
        "gasto_personal": 41800000000.0,
        "gasto_inversion": 15200000000.0,
    },
]


def normalize_rows(rows: list[dict[str, Any]]) -> pl.DataFrame:
    """Normaliza filas al esquema canónico de finanzas_municipales."""
    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("anio").cast(pl.Int32),
            pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
            pl.col("nombre_comuna").cast(pl.String),
            pl.col("ingresos_totales").cast(pl.Float64),
            pl.col("gastos_totales").cast(pl.Float64),
            pl.col("ingresos_propios_permanentes").cast(pl.Float64),
            pl.col("fondo_comun_municipal").cast(pl.Float64),
            pl.col("gasto_personal").cast(pl.Float64),
            pl.col("gasto_inversion").cast(pl.Float64),
        )
        .sort(["anio", "codigo_comuna"])
    )


def build_metadata(
    df: pl.DataFrame,
    source_mode: str,
    source_url: str,
    notes: list[str],
    reuse_policy: dict[str, Any],
) -> dict:
    """Construye metadata.json para staging.

    `source_detail` ramifica por modo (heredado del scraper): el stub siempre
    llegaba con modo no-live, así que su salida es idéntica; si algún día
    reportara "live", ahora quedaría registrado como tal en vez de como
    fallback (comportamiento más correcto, ver commit).
    """
    return build_standard_metadata(
        dataset="finanzas_municipales",
        source_name="SINIM - SUBDERE",
        source_url=source_url,
        source_mode=source_mode,
        source_detail=(
            "live_scraping_sinim_portal"
            if source_mode == "live"
            else "curated_fallback_pending_direct_export"
        ),
        df=df,
        notes=notes,
        reuse_policy=reuse_policy,
    )
