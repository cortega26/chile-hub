"""Motor de consulta y resolución del hub (plan 134c).

Funciones puras o casi-puras movidas de `ChileHub` (SRP): resolución de
nombres/comunas/regiones, reverse geocoding por coordenadas y composición de
cruces. `ChileHub` conserva los métodos públicos y les inyecta los datos
cargados (`load_polars`) o los parámetros.

`sql()` NO se movió a propósito (revisión del advisor): tiene estado lazy de
instancia (`_sql_connection`/`_sql_views_registered`) y un test que parchea
`ChileHub.get_output_path` a nivel clase *después* de crear el hub — el STOP
del plan 134 aplica y se queda en la fachada, documentado.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import polars as pl

from .exceptions import ChileHubDataError
from .geo import acquire_geometry, load_geometry, resolve_points
from .regions import REGION_ALIASES, normalize_region_name
from .text import normalize_comuna_name

JoinHow = Literal["inner", "left", "right", "full", "semi", "anti", "cross", "outer"]


def _resolve_names_to_frame(
    names: list[str],
    lookup: dict[str, dict[str, str]],
    normalizer: Callable[[str], str],
    value_columns: tuple[str, ...],
) -> pl.DataFrame:
    """Fila por input (orden y duplicados preservados) con ``matched`` explícito.

    Helper común de ``resolve_comunas`` y ``resolve_regiones``: normaliza cada
    input con ``normalizer``, busca en ``lookup`` y devuelve códigos nulos (sin
    excepción) para los no encontrados.
    """
    rows: list[dict[str, Any]] = []
    for original in names:
        hit = lookup.get(normalizer(str(original)))
        row: dict[str, Any] = {"input": original}
        for column in value_columns:
            row[column] = hit[column] if hit else None
        row["matched"] = hit is not None
        rows.append(row)
    schema = {
        "input": pl.String,
        **dict.fromkeys(value_columns, pl.String),
        "matched": pl.Boolean,
    }
    return pl.DataFrame(rows, schema=schema)


def cross_view(frames: list[tuple[str, pl.DataFrame]], on: str, how: JoinHow) -> pl.DataFrame:
    """Cruza `frames` (nombre, DataFrame) por `on`, prefijando columnas no-clave.

    El llamador (`ChileHub.cross_view`) valida el mínimo de datasets y carga
    cada frame vía `load_polars`; acá solo vive la composición del cruce
    (plan 134c).
    """
    dfs = []
    for name, df in frames:
        cols_to_prefix = [c for c in df.columns if c != on]
        dfs.append(
            df.select([pl.col(on)] + [pl.col(c).alias(f"{name}_{c}") for c in cols_to_prefix])
        )

    result = dfs[0]
    for df in dfs[1:]:
        result = result.join(df, on=on, how=how)
    return result


def resolve_comunas(names: list[str], comunas: pl.DataFrame) -> pl.DataFrame:
    """Resuelve nombres de comuna a códigos CUT (helper de ChileHub)."""
    lookup = {
        row["nombre_comuna_clean"]: {
            "codigo_comuna": row["codigo_comuna"],
            "nombre_comuna": row["nombre_comuna"],
            "codigo_region": row["codigo_region"],
        }
        for row in comunas.iter_rows(named=True)
    }
    return _resolve_names_to_frame(
        names,
        lookup,
        normalize_comuna_name,
        ("codigo_comuna", "nombre_comuna", "codigo_region"),
    )


def resolve_regiones(names: list[str], regiones: pl.DataFrame) -> pl.DataFrame:
    """Resuelve nombres de región a códigos CUT (helper de ChileHub)."""
    nombre_por_codigo = {
        row["codigo_region"]: row["nombre_region"] for row in regiones.iter_rows(named=True)
    }
    lookup: dict[str, dict[str, str]] = {}
    for row in regiones.iter_rows(named=True):
        lookup[normalize_region_name(row["nombre_region"])] = {
            "codigo_region": row["codigo_region"],
            "nombre_region": row["nombre_region"],
        }
    for alias, codigo in REGION_ALIASES.items():
        nombre_oficial = nombre_por_codigo.get(codigo)
        if nombre_oficial is not None:
            lookup.setdefault(
                alias,
                {"codigo_region": codigo, "nombre_region": nombre_oficial},
            )
    return _resolve_names_to_frame(
        names,
        lookup,
        normalize_region_name,
        ("codigo_region", "nombre_region"),
    )


def resolve_by_coords(
    points: list[tuple[float, float]],
    *,
    refresh_geometry: bool = False,
    geometry_path: Path | None = None,
) -> pl.DataFrame:
    """Reverse geocoding (lat, lon) → comuna (misma semántica que el hub)."""
    for i, point in enumerate(points):
        lat, lon = point
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            raise ValueError(
                f"Coordenada inválida en el input {i}: ({lat}, {lon}). "
                "Se espera (latitud en [-90, 90], longitud en [-180, 180])."
            )

    try:
        if geometry_path is not None:
            path = geometry_path
        else:
            path = acquire_geometry(refresh_geometry=refresh_geometry)
        gdf = load_geometry(path)
    except ImportError:
        raise
    except ChileHubDataError:
        raise
    except Exception as exc:
        raise ChileHubDataError(f"No se pudo cargar la geometría comunal: {exc}") from exc

    results = resolve_points(gdf, points)
    return pl.DataFrame(
        [
            {
                "input_lat": lat,
                "input_lon": lon,
                "codigo_comuna": code,
                "nombre_comuna": name,
                "matched": matched,
            }
            for (lat, lon), (code, name, matched) in zip(points, results, strict=False)
        ],
        schema={
            "input_lat": pl.Float64,
            "input_lon": pl.Float64,
            "codigo_comuna": pl.String,
            "nombre_comuna": pl.String,
            "matched": pl.Boolean,
        },
    )
