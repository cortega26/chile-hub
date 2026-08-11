"""Fixtures sintéticos de geometría comunal para tests de resolve_by_coords.

Nunca se usa el artefacto real de 5 MB (contrato Plan 065 Step 5): cuadrados
de prueba en EPSG:4326 con comunas de 5 caracteres. geopandas/shapely se
importan de forma perezosa — este módulo NO debe importarlos en el top-level
para no contaminar los tests de "instalación base sin geo".
"""

from pathlib import Path
from typing import Any


def build_synthetic_gdf(comunas: list[dict[str, Any]] | None = None):
    """GeoDataFrame de comunas cuadradas (lat/lon grados decimales, EPSG:4326).

    Cada comuna: ``codigo_comuna`` (5 chars), ``nombre_comuna``, y bounds
    ``(lat_min, lat_max, lon_min, lon_max)``. Default: 3 comunas que no se
    tocan + un overlap intencional para probar el tie-break.
    """
    if comunas is None:
        comunas = [
            {
                "codigo_comuna": "01101",
                "nombre_comuna": "Arica",
                "lat_min": -20.0,
                "lat_max": -19.0,
                "lon_min": -70.5,
                "lon_max": -69.5,
            },
            {
                "codigo_comuna": "01102",
                "nombre_comuna": "Camarones",
                "lat_min": -19.5,
                "lat_max": -18.5,
                "lon_min": -69.5,
                "lon_max": -68.5,
            },
            {
                "codigo_comuna": "01103",
                "nombre_comuna": "Putre",
                "lat_min": -19.0,
                "lat_max": -18.0,
                "lon_min": -69.8,
                "lon_max": -68.8,
            },
        ]
    import geopandas as gpd
    from shapely.geometry import box

    gdf = gpd.GeoDataFrame(
        {
            "codigo_comuna": [c["codigo_comuna"] for c in comunas],
            "nombre_comuna": [c["nombre_comuna"] for c in comunas],
            "geometry": [
                box(c["lon_min"], c["lat_min"], c["lon_max"], c["lat_max"]) for c in comunas
            ],
        },
        crs="EPSG:4326",
    )
    return gdf


def write_synthetic_parquet(path: Path, comunas: list[dict[str, Any]] | None = None) -> Path:
    """Escribe el fixture como GeoParquet 1.0/WKB, igual que el builder real."""
    gdf = build_synthetic_gdf(comunas)
    gdf.to_parquet(path, geometry_encoding="WKB", schema_version="1.0.0")
    return path


def payload_and_digest(payload: bytes) -> tuple[bytes, str]:
    """Retorna (payload, sha256) para fabricar compañeros .sha256 en tests."""
    import hashlib

    return payload, hashlib.sha256(payload).hexdigest()


def fake_sha_body(digest: str, basename: str = "geometria_comunal.parquet") -> str:
    """Cuerpo de un compañero .sha256 bien formado (dos espacios, sha256sum)."""
    return f"{digest}  {basename}"
