"""Extractor de geometría comunal (límites poligonales) desde BCN ArcGIS.

Fuente: capa `tematico/Comunas_Generalizadas` (BCN, `arcgiswebad.bcn.cl`), la misma
familia de servicios que ya usa `subdere_extractor.py` para atributos DPA. Licencia
confirmada vía la declaración de condiciones de uso de `bcn.cl/siit/mapas_vectoriales`
("uso libre con atribución"; ver `docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md`
para el detalle completo del gate de licencia del Plan 053 Step 1).

La geometría es "generalizada" (simplificada para cartografía a escala nacional, no
apta para trabajo de precisión geodésica ni catastral) — se documenta el disclaimer
en `docs/datasets/geometria_comunal.md`.

Estrategia de fetch: el endpoint rechaza una consulta única con las 346+ comunas y
geometría (HTTP 500 — payload demasiado grande), pero responde con normalidad cuando
se filtra por región (`codregion`, 16 valores oficiales 1-16; `codregion=0` es un
registro placeholder "Zona sin demarcar" sin comuna real, se descarta). Por eso el
fetch itera región por región y concatena.

Carril CANDIDATE — dataset nuevo, geometría separada de `comunas` (nunca una columna).
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

import polars as pl
import requests
from shapely.geometry import shape

UTC = datetime.timezone.utc

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
    from src.extractors.http_utils import fetch_with_retry
    from src.extractors.source_adapter import build_standard_metadata
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from http_utils import fetch_with_retry
    from source_adapter import build_standard_metadata

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
STAGING_CSV_PATH = STAGING_DIR / "geometria_comunal.csv"
METADATA_PATH = STAGING_DIR / "geometria_comunal.metadata.json"

BCN_GEOMETRIA_SERVICE_URL = "https://arcgiswebad.bcn.cl/arcgis/rest/services/tematico/Comunas_Generalizadas/MapServer/0/query"

# Códigos de región oficiales de Chile (1-16). `codregion=0` existe en el servicio
# como placeholder "Zona sin demarcar" (cod_comuna=0) y se excluye a propósito.
REGION_CODES = list(range(1, 17))

REUSE_POLICY = {
    "status": "open-attribution",
    "license": (
        "Uso libre con atribución a la Biblioteca del Congreso Nacional de Chile "
        '("Los mapas vectoriales son puestos a disposición en virtud del principio '
        "de transparencia de la función pública. Las personas o instituciones pueden "
        "usar libremente esta información, señalando como fuente a la Biblioteca del "
        'Congreso Nacional de Chile."). Geometría "generalizada": material de '
        "referencia, no apto para trabajo de precisión geodésica."
    ),
    "license_url": "https://www.bcn.cl/siit/mapas_vectoriales/index_html",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Límites comunales (geometría generalizada) desde BCN ArcGIS "
        "(tematico/Comunas_Generalizadas). Ver ADR-012 para el gate de licencia."
    ),
}


def _fetch_region(codregion: int) -> list[dict[str, Any]]:
    """Obtiene las features GeoJSON de una región desde el servicio BCN ArcGIS.

    Retorna la lista de features (`type: Feature`) tal como las entrega el
    servicio; una consulta con todas las regiones a la vez falla con HTTP 500
    (payload demasiado grande), por eso se filtra por `codregion`.
    """
    params = {
        "where": f"codregion={codregion}",
        "outFields": "cod_comuna,nom_com,nom_reg,codregion",
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }
    response = fetch_with_retry(
        BCN_GEOMETRIA_SERVICE_URL, get_fn=requests.get, params=params, timeout=90
    )
    response.raise_for_status()
    payload = response.json()
    features: list[dict[str, Any]] = payload.get("features", [])
    return features


def _fetch_region_comuna_codes(codregion: int) -> list[int]:
    """Lista los `cod_comuna` de una región sin geometría (query liviana)."""
    params = {
        "where": f"codregion={codregion}",
        "outFields": "cod_comuna",
        "returnGeometry": "false",
        "f": "json",
    }
    response = fetch_with_retry(
        BCN_GEOMETRIA_SERVICE_URL, get_fn=requests.get, params=params, timeout=60
    )
    response.raise_for_status()
    payload = response.json()
    return [
        int(f["attributes"]["cod_comuna"])
        for f in payload.get("features", [])
        if f.get("attributes", {}).get("cod_comuna")
    ]


def _fetch_comuna(cod_comuna: int) -> dict[str, Any] | None:
    """Obtiene la feature GeoJSON de una única comuna por `cod_comuna`."""
    params = {
        "where": f"cod_comuna={cod_comuna}",
        "outFields": "cod_comuna,nom_com,nom_reg,codregion",
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }
    response = fetch_with_retry(
        BCN_GEOMETRIA_SERVICE_URL, get_fn=requests.get, params=params, timeout=90
    )
    response.raise_for_status()
    payload = response.json()
    features = payload.get("features", [])
    return features[0] if features else None


def fetch_geometria_comunal() -> tuple[list[dict[str, Any]], list[str]]:
    """Obtiene la geometría de las 346 comunas iterando por región.

    Algunas regiones (ej. Magallanes, region 12: fiordos e islas generan un
    payload combinado enorme) devuelven HTTP 500 al pedir la región completa
    de una vez aunque cada comuna individual responde bien por separado — el
    servicio parece tener un límite de tamaño de respuesta combinada, no por
    comuna. Ante ese fallo se reintenta comuna por comuna dentro de la región.

    Returns:
        Tupla (features, notes) con todas las features GeoJSON acumuladas y una
        lista de notas operativas (una por región con su conteo, o el detalle
        del fallback si una región falló).
    """
    ensure_staging_directories()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_features: list[dict[str, Any]] = []
    notes: list[str] = []

    for codregion in REGION_CODES:
        try:
            features = _fetch_region(codregion)
            all_features.extend(features)
            notes.append(f"región {codregion}: {len(features)} comunas")
            continue
        except Exception as e:
            notes.append(
                f"región {codregion}: fetch por región falló ({e}); reintentando comuna por comuna"
            )

        try:
            codes = _fetch_region_comuna_codes(codregion)
        except Exception as e:
            notes.append(f"región {codregion}: fallback por-comuna también falló — {e}")
            continue

        ok = 0
        for code in codes:
            try:
                feature = _fetch_comuna(code)
                if feature:
                    all_features.append(feature)
                    ok += 1
            except Exception as e2:
                notes.append(f"  comuna {code} (región {codregion}): error — {e2}")
        notes.append(f"región {codregion}: {ok}/{len(codes)} comunas vía fallback por-comuna")

    timestamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DIR / f"bcn_geometria_comunal_{timestamp}.json"
    raw_path.write_text(
        json.dumps({"features": all_features}, ensure_ascii=False), encoding="utf-8"
    )
    notes.append(f"snapshot crudo: {raw_path.name}")

    return all_features, notes


def normalize_features(features: list[dict[str, Any]]) -> pl.DataFrame:
    """Normaliza features GeoJSON al esquema canónico de `geometria_comunal`.

    Descarta features sin `cod_comuna` válido (incluye el placeholder
    "Zona sin demarcar" de `codregion=0`, `cod_comuna=0`, que no representa una
    comuna real) y deduplica por `codigo_comuna` (las regiones son disjuntas por
    diseño, pero se protege contra respuestas repetidas del servicio).
    """
    if not features:
        return pl.DataFrame(
            schema={
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "nombre_comuna_clean": pl.String,
                "nombre_region": pl.String,
                "geometry_wkt": pl.String,
            }
        )

    records: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties", {})
        cod_comuna = props.get("cod_comuna")
        codregion = props.get("codregion")
        geom = feature.get("geometry")
        if not cod_comuna or not geom:
            continue  # descarta el placeholder cod_comuna=0 y features sin geometría

        codigo_comuna = str(int(cod_comuna)).rjust(5, "0")
        codigo_region = str(int(codregion)).rjust(2, "0") if codregion is not None else ""
        wkt = shape(geom).wkt

        records.append(
            {
                "codigo_region": codigo_region,
                "codigo_comuna": codigo_comuna,
                "nombre_comuna": props.get("nom_com", ""),
                "nombre_region": props.get("nom_reg", ""),
                "geometry_wkt": wkt,
            }
        )

    df = pl.DataFrame(records)
    df = df.unique(subset=["codigo_comuna"], keep="first")
    df = df.with_columns(
        pl.col("nombre_comuna")
        .str.to_lowercase()
        .str.replace_all("á", "a")
        .str.replace_all("é", "e")
        .str.replace_all("í", "i")
        .str.replace_all("ó", "o")
        .str.replace_all("ú", "u")
        .str.replace_all("ü", "u")
        .str.replace_all("ñ", "n")
        .alias("nombre_comuna_clean")
    )
    df = df.select(
        [
            "codigo_region",
            "codigo_comuna",
            "nombre_comuna",
            "nombre_comuna_clean",
            "nombre_region",
            "geometry_wkt",
        ]
    ).sort("codigo_comuna")
    return df


def build_metadata(df: pl.DataFrame, source_mode: str, notes: list[str]) -> dict[str, Any]:
    """Construye metadata.json para staging."""
    return build_standard_metadata(
        dataset="geometria_comunal",
        source_name="BCN ArcGIS — tematico/Comunas_Generalizadas",
        source_url=BCN_GEOMETRIA_SERVICE_URL,
        source_mode=source_mode,
        source_detail="bcn_arcgis_geometria_generalizada",
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )


def process_geometria_comunal() -> str:
    """Ejecuta el ciclo completo de extracción para `geometria_comunal`."""
    features, notes = fetch_geometria_comunal()
    df = normalize_features(features)

    if df.height == 0:
        print(
            "⚠️  geometria_comunal: fetch no devolvió features. "
            "Se mantiene el último snapshot bueno (si existe)."
        )
        return ""

    source_mode = "live" if df.height >= 300 else "fallback"
    metadata = build_metadata(df, source_mode, notes)

    validation = GeometriaComunalExtractor().validate(df, metadata)
    if validation["status"] == "error":
        print(
            f"⚠️  Validación geometria_comunal fallida (no bloqueante — carril candidate): "
            f"{validation['errors']}"
        )

    GeometriaComunalExtractor().write_staging(df, metadata)
    print(
        f"Geometría comunal guardada en: {STAGING_CSV_PATH} "
        f"({df.height} comunas, source_mode={source_mode})"
    )
    return str(STAGING_CSV_PATH)


class GeometriaComunalExtractor(BaseExtractor):
    """Extractor de geometría comunal (límites poligonales) desde BCN ArcGIS.

    Itera por región (`codregion` 1-16) porque el servicio rechaza una consulta
    única con las ~346 comunas y geometría (HTTP 500).

    Carril: CANDIDATE — geometría separada del dataset `comunas`, nunca una columna.
    """

    @property
    def dataset_name(self) -> str:
        return "geometria_comunal"

    def fetch(self, **kwargs: Any) -> tuple[list[dict[str, Any]], list[str]]:
        return fetch_geometria_comunal()

    def normalize(self, raw_data: tuple) -> pl.DataFrame:
        return normalize_features(raw_data[0])

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        """Validación ligera para dataset candidate.

        Los datasets en carril candidate no tienen contrato fail-loud: la
        validación es informativa, no bloqueante. La validación fuerte
        (`validate_geometria_comunal`, integridad referencial con DPA) vive en
        `src/validation.py` y corre en el build (Step 3).
        """
        errors: list[str] = []
        warnings: list[str] = []

        if df.height == 0:
            warnings.append("dataset vacío — fetch posiblemente fallido")
        else:
            duplicate_count = df.height - df["codigo_comuna"].n_unique()
            if duplicate_count > 0:
                errors.append(f"codigo_comuna debe ser único, {duplicate_count} duplicados")

            bad_length = df.filter(pl.col("codigo_comuna").str.len_chars() != 5).height
            if bad_length > 0:
                errors.append(f"{bad_length} filas con codigo_comuna distinto de 5 caracteres")

            if df.height < 300:
                warnings.append(f"solo {df.height}/346 comunas presentes — cobertura parcial")

        return {
            "status": "error" if errors else "ok",
            "errors": errors,
            "warnings": warnings,
        }

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_geometria_comunal()
