"""Writer especializado para el artefacto GeoParquet de geometría comunal.

GeoParquet (spec 1.0, https://geoparquet.org) requiere la geometría codificada
en WKB más una clave `geo` en el metadata del footer del Parquet — distinto de
un Parquet plano con una columna de texto WKT, que ninguna herramienta GIS
reconoce como geometría. `geopandas.GeoDataFrame.to_parquet` produce ese
footer correctamente; por eso este writer no reutiliza
`write_parquet_atomic` (`io_utils.py`), que solo sabe escribir DataFrames de
Polars sin metadata geo.
"""

import os

import geopandas as gpd
import polars as pl
from shapely import wkt

# Tolerancia de simplificación en grados (~100 m en la latitud de Chile).
# La geometría BCN ya es "generalizada"; sin simplificar el artefacto pesa
# ~28 MB (345 comunas — Magallanes domina el peso por sus fiordos e islas).
# tol=0.001 baja a ~5 MB preservando la forma reconocible de cada comuna;
# decisión y comparativa de tolerancias documentadas en ADR-012.
GEOMETRIA_SIMPLIFY_TOLERANCE_DEG = 0.001


def write_geometria_comunal_parquet(
    df: pl.DataFrame,
    path: str,
    simplify_tolerance: float = GEOMETRIA_SIMPLIFY_TOLERANCE_DEG,
) -> None:
    """Escribe el artefacto GeoParquet de geometría comunal.

    ``df`` debe tener el esquema de staging de ``geometria_comunal``
    (``codigo_region``, ``codigo_comuna``, ``nombre_comuna``,
    ``nombre_comuna_clean``, ``nombre_region``, ``geometry_wkt``). Convierte
    WKT a geometría shapely, simplifica preservando topología (evita que un
    polígono colapse a vacío) y escribe con ``geopandas.to_parquet``: footer
    GeoParquet 1.0 estándar, CRS EPSG:4326 (WGS84 — el sistema de coordenadas
    universal para compartir fuera de chile-hub, ej. QGIS/deck.gl).
    """
    geometries = [wkt.loads(g) for g in df["geometry_wkt"].to_list()]
    if simplify_tolerance > 0:
        geometries = [g.simplify(simplify_tolerance, preserve_topology=True) for g in geometries]

    gdf = gpd.GeoDataFrame(
        {
            "codigo_region": df["codigo_region"].to_list(),
            "codigo_comuna": df["codigo_comuna"].to_list(),
            "nombre_comuna": df["nombre_comuna"].to_list(),
            "nombre_comuna_clean": df["nombre_comuna_clean"].to_list(),
            "nombre_region": df["nombre_region"].to_list(),
        },
        geometry=geometries,
        crs="EPSG:4326",
    )

    tmp_path = path + ".tmp"
    # geometry_encoding="WKB" + schema_version="1.0.0" explícitos: máxima
    # interoperabilidad (QGIS/deck.gl/lectores más viejos) en vez del default
    # "geoarrow" experimental de GeoParquet 1.1 que algunos lectores no soportan.
    gdf.to_parquet(
        tmp_path,
        compression="zstd",
        geometry_encoding="WKB",
        schema_version="1.0.0",
    )
    os.replace(tmp_path, path)
