"""Writer especializado para el artefacto GeoParquet de geometría comunal.

GeoParquet (spec 1.0, https://geoparquet.org) requiere la geometría codificada
en WKB más una clave `geo` en el metadata del footer del Parquet — distinto de
un Parquet plano con una columna de texto WKT, que ninguna herramienta GIS
reconoce como geometría. `geopandas.GeoDataFrame.to_parquet` produce ese
footer correctamente; por eso este writer no reutiliza
`write_parquet_atomic` (`io_utils.py`), que solo sabe escribir DataFrames de
Polars sin metadata geo.
"""

import json
import os

import geopandas as gpd
import polars as pl
from shapely import set_precision, wkt
from shapely.geometry import MultiPolygon, mapping

# Tolerancia de simplificación en grados (~100 m en la latitud de Chile).
# La geometría BCN ya es "generalizada"; sin simplificar el artefacto pesa
# ~28 MB (345 comunas — Magallanes domina el peso por sus fiordos e islas).
# tol=0.001 baja a ~5 MB preservando la forma reconocible de cada comuna;
# decisión y comparativa de tolerancias documentadas en ADR-012.
GEOMETRIA_SIMPLIFY_TOLERANCE_DEG = 0.001

# Asset visual del mapa coroplético del sitio (Leaflet): no es el dataset.
# El GeoParquet pesa ~5 MB porque conserva la forma reconocible de cada
# comuna; para un mapa nacional se simplifica más fuerte, se descartan islotes
# menores a ~1 km² y se hace snap a una grilla de 0.001° (~100 m). Resultado:
# ~390 KB (≈60 KB comprimido en la CDN) con las 345 comunas y sus islas
# principales. La regla y su porqué viven en ADR-012; el dataset en carril
# candidate sigue intacto.
MAPA_WEB_SIMPLIFY_TOLERANCE_DEG = 0.02
MAPA_WEB_MIN_PART_AREA_DEG2 = 1e-4
MAPA_WEB_PRECISION_DEG = 0.001


def _keep_main_parts(geometry, min_part_area: float):
    """Conserva el polígono mayor de cada comuna y sus islas sobre el umbral."""
    if not isinstance(geometry, MultiPolygon):
        return geometry
    parts = sorted(geometry.geoms, key=lambda part: part.area, reverse=True)
    keep = [parts[0]] + [part for part in parts[1:] if part.area >= min_part_area]
    return MultiPolygon(keep)


def _round_coords(value, digits: int = 3):
    if isinstance(value, (list, tuple)):
        return [_round_coords(item, digits) for item in value]
    if isinstance(value, float):
        return round(value, digits)
    return value


def write_mapa_comunal_geojson(
    df: pl.DataFrame,
    path: str,
    simplify_tolerance: float = MAPA_WEB_SIMPLIFY_TOLERANCE_DEG,
    min_part_area: float = MAPA_WEB_MIN_PART_AREA_DEG2,
    precision_deg: float = MAPA_WEB_PRECISION_DEG,
) -> None:
    """Escribe el GeoJSON simplificado que consume el mapa del sitio.

    Derivado **visual** de ``geometria_comunal`` (carril candidate): no entra
    al bundle ZIP ni al catálogo de datasets. Determinista: features ordenadas
    por CUT, coordenadas redondeadas y JSON compacto, para que el build
    programado no genere diffs espurios.
    """
    features = []
    for row in df.sort("codigo_comuna").iter_rows(named=True):
        geometry = wkt.loads(row["geometry_wkt"])
        geometry = _keep_main_parts(geometry, min_part_area)
        if simplify_tolerance > 0:
            geometry = geometry.simplify(simplify_tolerance, preserve_topology=True)
        geometry = set_precision(geometry, precision_deg)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "codigo_region": row["codigo_region"],
                    "codigo_comuna": row["codigo_comuna"],
                    "nombre_comuna": row["nombre_comuna"],
                    "nombre_comuna_clean": row["nombre_comuna_clean"],
                    "nombre_region": row["nombre_region"],
                },
                "geometry": _round_coords(mapping(geometry)),
            }
        )

    payload = {
        "type": "FeatureCollection",
        "atribucion": "Límites: BCN ArcGIS (geometría generalizada) — asset visual de chile-hub",
        "features": features,
    }
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
    os.replace(tmp_path, path)


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
