"""Herramientas puras del servidor MCP de chile-hub.

Se mantienen separadas del wrapper `mcp_server.py` para poder testearlas sin el
paquete `mcp` (extra opcional) y sin red: `base_url` es inyectable (URL HTTP
pública o ruta local). Este módulo nunca importa `mcp`.

Origen de datos: la capa HTTP estática (`data/normalized/{capa}.parquet`), el
mismo contrato que documenta `docs/http-access.md`; no descarga el bundle.
"""

from __future__ import annotations

import datetime
import io
from functools import lru_cache

import polars as pl
import requests

from .datasets import Dataset
from .text import normalize_comuna_name

PUBLIC_DATA_BASE = "https://tooltician.com/chile-hub/data/normalized"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def _parquet_url(base_url: str, name: str) -> str:
    return f"{base_url.rstrip('/')}/{name}.parquet"


def _dataset_url(name: str, base_url: str) -> str:
    dataset = Dataset.from_string(name)  # ValueError con sugerencia si no existe
    return _parquet_url(base_url, dataset.value)


def _scan_parquet(url: str) -> pl.LazyFrame:
    """Plan de lectura perezoso para una URL HTTP o una ruta local."""
    if url.startswith(("http://", "https://")):
        # GitHub Pages no envía `Content-Length` y el reader HTTP de polars lo
        # exige ("Content-Length Header missing from response"). Descargar con
        # requests y parsear los bytes funciona con cualquier servidor.
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return pl.scan_parquet(io.BytesIO(response.content))
    return pl.scan_parquet(url)


@lru_cache(maxsize=16)
def _read_parquet_cached(url: str) -> pl.LazyFrame:
    """Plan de lectura de un Parquet, cacheado por proceso.

    El servidor MCP vive toda la sesión del cliente y los Parquet publicados
    son inmutables dentro de ella (el sitio se regenera a diario): sin caché,
    cada tool call vuelve a descargar y parsear el archivo. `maxsize=16` acota
    las entradas; cada una retiene sólo los bytes comprimidos del Parquet (la
    capa más grande, `empresas`, pesa 29 MB), así que el tope de memoria queda
    en decenas de MB y no hace falta un tope de bytes explícito.

    Se cachea el plan perezoso (`LazyFrame`), no el DataFrame: `get_dataset`
    resuelve el total desde los metadatos y lee sólo la porción pedida, sin
    materializar 1.6 M filas para devolver 10.

    `lru_cache` no cachea excepciones: si la descarga o el parseo falla, el
    siguiente llamado lo reintenta. `_read_parquet_cached.cache_clear()` está
    disponible para los tests.
    """
    return _scan_parquet(url)


def _read_dataset(name: str, base_url: str) -> pl.DataFrame:
    """DataFrame completo de una capa, pasando por la caché por proceso."""
    return _read_parquet_cached(_dataset_url(name, base_url)).collect()


def list_datasets() -> list[dict]:
    """Lista las capas disponibles con la URL de su Parquet público."""
    return [
        {
            "nombre": dataset.value,
            "parquet": _parquet_url(PUBLIC_DATA_BASE, dataset.value),
        }
        for dataset in Dataset
    ]


def get_dataset(name: str, limite: int = DEFAULT_LIMIT, base_url: str = PUBLIC_DATA_BASE) -> dict:
    """Devuelve las primeras `limite` filas de una capa (máximo duro 1000)."""
    if limite < 1:
        raise ValueError("'limite' debe ser >= 1")
    lazy = _read_parquet_cached(_dataset_url(name, base_url))
    # `pl.len()` se resuelve desde los metadatos del Parquet y `head()` lee sólo
    # las filas necesarias: no se materializa la capa completa (empresas:
    # 1.6 M filas / 183 MB en memoria) para devolver `limite` filas.
    total = lazy.select(pl.len()).collect().item()
    head = lazy.head(min(limite, MAX_LIMIT)).collect()
    return {
        "dataset": name,
        "filas_totales": total,
        "filas_devueltas": head.height,
        "columnas": head.columns,
        "registros": head.to_dicts(),
    }


def resolve_comunas(nombres: list[str], base_url: str = PUBLIC_DATA_BASE) -> list[dict]:
    """Resuelve nombres de comuna (con tildes/ñ/mayúsculas) a su código CUT."""
    df = _read_dataset("comunas", base_url)
    lookup = {
        row["nombre_comuna_clean"]: (row["codigo_comuna"], row["nombre_comuna"])
        for row in df.iter_rows(named=True)
    }
    results = []
    for nombre in nombres:
        match = lookup.get(normalize_comuna_name(nombre))
        results.append(
            {
                "entrada": nombre,
                "codigo_comuna": match[0] if match else None,
                "nombre_comuna": match[1] if match else None,
                "matched": match is not None,
            }
        )
    return results


def _parse_date(value: str, field: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"'{field}' debe ser ISO YYYY-MM-DD, recibido {value!r}") from exc


def get_indicadores(
    codigo: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    limite: int = DEFAULT_LIMIT,
    base_url: str = PUBLIC_DATA_BASE,
) -> dict:
    """Serie de indicadores económicos (uf, dolar, euro, utm, ipc).

    Sin argumentos devuelve las últimas `limite` filas de todas las series.
    `desde`/`hasta` son fechas ISO (YYYY-MM-DD), inclusivas.
    """
    if limite < 1:
        raise ValueError("'limite' debe ser >= 1")
    df = _read_dataset("indicadores", base_url)
    codigos_disponibles = sorted(df["codigo_indicador"].unique().to_list())
    if codigo:
        df = df.filter(pl.col("codigo_indicador") == codigo)
    if desde:
        df = df.filter(pl.col("fecha") >= _parse_date(desde, "desde"))
    if hasta:
        df = df.filter(pl.col("fecha") <= _parse_date(hasta, "hasta"))
    tail = df.tail(min(limite, MAX_LIMIT)).with_columns(pl.col("fecha").cast(pl.String))
    return {
        "codigos": codigos_disponibles,
        "filas_devueltas": tail.height,
        "registros": tail.to_dicts(),
    }
