"""Resolución de coordenadas → comuna (reverse geocoding) vía el GeoParquet candidate.

Consume el artefacto publicado por Plan 064 y documentado en ADR-012 ("Plan 065
Step 1 — contrato de distribución y caché"): GeoParquet 1.0 servido desde
Pages con un compañero ``.sha256`` adyacente. La descarga solo reemplaza el
caché cuando la digest coincide; un caché verificado se reutiliza sin red.

geopandas/shapely se importan SOLO dentro de funciones (extra opcional ``geo``);
sin ese extra, ``resolve_by_coords()`` levanta ImportError con la instrucción
``pip install chile-hub[geo]``. Este módulo a nivel superior solo usa stdlib y
dependencias base (requests, platformdirs).
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import requests
from platformdirs import user_cache_dir

from .exceptions import ChileHubDataError

if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from shapely.geometry import Point

logger = logging.getLogger(__name__)

GEOMETRY_BASENAME = "geometria_comunal.parquet"
GEOMETRY_URL = "https://tooltician.com/chile-hub/data/normalized/geometria_comunal.parquet"
GEOMETRY_SHA256_URL = GEOMETRY_URL + ".sha256"
CACHE_FILE = Path(user_cache_dir("chile-hub")) / GEOMETRY_BASENAME

# Contrato ADR-012 / Plan 064: 345 comunas reales, tolerancia de simplificación
# 0.001° (~100 m); nunca debería bajar de 340 geometrías no vacías.
MIN_NON_EMPTY_GEOMETRIES = 340
DOWNLOAD_TIMEOUT = 60
GEO_INSTALL_HINT = "pip install chile-hub[geo]"


def _require_geo() -> None:
    """Valida que el extra ``geo`` esté instalado; falla con la instrucción exacta."""
    try:
        import geopandas  # noqa: F401
        import shapely  # noqa: F401
    except ImportError:
        raise ImportError(
            f"Para resolver coordenadas necesitas instalar el extra opcional: {GEO_INSTALL_HINT}"
        ) from None


def fetch_expected_digest(
    sha_url: str = GEOMETRY_SHA256_URL,
    *,
    get_fn: Callable[..., requests.Response] | None = None,
) -> str:
    """Descarga y parsea el compañero ``.sha256`` (contrato ADR-012).

    Formato `sha256sum` modo binario: ``<64 hex SHA-256>  <basename>`` (dos
    espacios). La digest es el primer token; el segundo debe ser el basename
    exacto del artefacto — cualquier discrepancia es error de contrato.

    ``get_fn`` se resuelve en la llamada (no en la definición) para que los
    tests puedan parchear ``geo.requests.get``.
    """
    if get_fn is None:
        get_fn = requests.get
    response = get_fn(sha_url, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    tokens = response.text.strip().split()
    if len(tokens) != 2 or len(tokens[0]) != 64:
        raise ChileHubDataError(
            f"Compañero de integridad inválido ({sha_url}): se esperaba "
            f"'<64 hex>  {GEOMETRY_BASENAME}' y se obtuvo {response.text.strip()!r}"
        )
    digest, name = tokens
    if name != GEOMETRY_BASENAME:
        raise ChileHubDataError(
            f"Contrato de integridad roto: el compañero .sha256 nombra "
            f"'{name}', se esperaba '{GEOMETRY_BASENAME}'"
        )
    return digest


def _sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_to_temp(
    url: str,
    dest_dir: Path,
    *,
    get_fn: Callable[..., requests.Response] | None = None,
) -> Path:
    """Descarga en streaming a un archivo temporal hermano del destino final.

    Nunca escribe sobre el caché: el reemplazo ocurre en
    ``verify_and_install_artifact`` solo tras validar la digest.
    """
    if get_fn is None:
        get_fn = requests.get
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=dest_dir, prefix=".geom-", suffix=".tmp", delete=False
    ) as tmp:
        temp_path = Path(tmp.name)
    try:
        with get_fn(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            with open(temp_path, "wb") as out:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    if chunk:
                        out.write(chunk)
        return temp_path
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def verify_and_install_artifact(
    temp_path: Path,
    dest_path: Path,
    expected_digest: str,
) -> None:
    """Reemplaza el caché solo si la digest SHA-256 del temporal coincide.

    En cualquier otro caso borra el temporal y deja ``dest_path`` (caché
    verificado previo) intacto.
    """
    try:
        actual = _sha256sum(temp_path)
        if actual != expected_digest:
            raise ChileHubDataError(
                f"SHA-256 no coincide: se esperaba {expected_digest}, "
                f"se obtuvo {actual}. Se preserva el caché verificado anterior "
                f"({dest_path}) si existía."
            )
        os.replace(temp_path, dest_path)
    finally:
        temp_path.unlink(missing_ok=True)


def acquire_geometry(
    *,
    refresh_geometry: bool = False,
    cache_file: Path = CACHE_FILE,
    artifact_url: str = GEOMETRY_URL,
    sha_url: str = GEOMETRY_SHA256_URL,
) -> Path:
    """Retorna un camino local al GeoParquet verificado (descarga si hace falta).

    - Caché verificado existente (y ``refresh_geometry=False``) → se reutiliza
      sin tocar la red.
    - ``refresh_geometry=True`` → re-descarga y re-verifica; el caché se
      reemplaza solo si la digest coincide con el compañero.
    - Fallo de red/checksum sin caché → ``ChileHubDataError``.
    - Fallo de red/checksum con caché → se preserva el caché y se levanta
      ``ChileHubDataError`` (fail-loud, sin silenciar la causa).
    """
    if not refresh_geometry and cache_file.is_file():
        return cache_file

    try:
        expected = fetch_expected_digest(sha_url)
        temp_path = _download_to_temp(artifact_url, cache_file.parent)
        verify_and_install_artifact(temp_path, cache_file, expected)
        return cache_file
    except ChileHubDataError:
        raise
    except Exception as exc:
        preserved = " Se preserva el caché verificado anterior." if cache_file.is_file() else ""
        raise ChileHubDataError(
            f"No se pudo obtener la geometría comunal ({exc}){preserved} "
            f"Reintenta con red, refresh_geometry=True, o pasa geometry_path=... "
            f"con el archivo local."
        ) from exc


def validate_geometry(gdf: "GeoDataFrame") -> None:
    """Validación estructural del GeoParquet (contrato ADR-012, Plan 065 Step 3).

    Fallos: sin columna geometry, CRS distinto de EPSG:4326, codigo_comuna no
    string de 5 caracteres, CUT duplicados, o menos de
    ``MIN_NON_EMPTY_GEOMETRIES`` geometrías no vacías.
    """
    if "geometry" not in gdf.columns:
        raise ChileHubDataError("GeoParquet inválido: falta la columna 'geometry'")
    crs = gdf.crs
    epsg = crs.to_epsg() if crs is not None else None
    if epsg != 4326:
        raise ChileHubDataError(f"GeoParquet inválido: se esperaba CRS EPSG:4326, se obtuvo {epsg}")
    if "codigo_comuna" not in gdf.columns:
        raise ChileHubDataError("GeoParquet inválido: falta la columna 'codigo_comuna'")
    codes = gdf["codigo_comuna"].astype(str)
    bad_width = [c for c in codes if len(c) != 5]
    if bad_width:
        raise ChileHubDataError(
            f"GeoParquet inválido: {len(bad_width)} codigo_comuna sin 5 caracteres "
            f"(ej. {bad_width[0]!r})"
        )
    if codes.duplicated().any():
        raise ChileHubDataError("GeoParquet inválido: codigo_comuna duplicados")
    non_empty = int((~gdf.geometry.is_empty).sum())
    if non_empty < MIN_NON_EMPTY_GEOMETRIES:
        raise ChileHubDataError(
            f"GeoParquet inválido: solo {non_empty} geometrías no vacías "
            f"(mínimo {MIN_NON_EMPTY_GEOMETRIES})"
        )


def load_geometry(path: Path) -> "GeoDataFrame":
    """Carga un GeoParquet local como GeoDataFrame, con validación estructural."""
    _require_geo()
    import geopandas as gpd

    gdf = gpd.read_parquet(path)
    validate_geometry(gdf)
    return gdf


def resolve_points(
    gdf: "GeoDataFrame",
    points: list[tuple[float, float]],
) -> list[tuple[str | None, str | None, bool]]:
    """Función pura: resuelve puntos ``(latitud, longitud)`` contra un GeoDataFrame cargado.

    Preserva el orden de entrada y los duplicados. Usa ``covers`` (no
    ``contains``) para que los puntos de borde matcheen. Si varias geometrías
    cubren un punto, gana el ``codigo_comuna`` lexicográficamente menor y se
    emite un warning del módulo (tie-break determinístico documentado).

    Returns:
        Lista de ``(codigo_comuna, nombre_comuna, matched)``; sin match los dos
        primeros van en None y ``matched=False``.
    """
    _require_geo()
    from shapely.geometry import Point

    points_geom: list[Point] = [Point(lon, lat) for lat, lon in points]
    codes = gdf["codigo_comuna"].astype(str).tolist()
    names = gdf["nombre_comuna"].astype(str).tolist() if "nombre_comuna" in gdf.columns else None

    results: list[tuple[str | None, str | None, bool]] = []
    index = gdf.sindex
    for pt in points_geom:
        candidate_idx = list(index.query(pt))
        covering = [i for i in candidate_idx if gdf.geometry.iloc[i].covers(pt)]
        if not covering:
            results.append((None, None, False))
            continue
        best = min(covering, key=lambda i: codes[i])
        if len(covering) > 1:
            logger.warning(
                "resolve_by_coords: punto %s cubierto por %d comunas (%s); "
                "se usa %s (tie-break lexicográfico)",
                (pt.x, pt.y),
                len(covering),
                ", ".join(sorted(codes[i] for i in covering)),
                codes[best],
            )
        results.append((codes[best], names[best] if names is not None else None, True))
    return results
