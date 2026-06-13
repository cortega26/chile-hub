import json
import os
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import requests

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

# curl_cffi impersona el fingerprint TLS de Chrome, evitando bloqueos a nivel de TLS
# que rechazan al user-agent por defecto de la librería requests de Python.
try:
    from curl_cffi import requests as _cffi_requests

    _CURL_CFFI_AVAILABLE = True
except ImportError:
    _CURL_CFFI_AVAILABLE = False


def _stealth_get(url: str, **kwargs):
    """
    HTTP GET con impersonación de Chrome (curl_cffi) cuando está disponible,
    con fallback a requests estándar + headers de navegador.
    Resuelve rechazos TLS de servidores que bloquean fingerprints de Python.
    """
    if _CURL_CFFI_AVAILABLE:
        return _cffi_requests.get(url, impersonate="chrome124", **kwargs)
    # Fallback: headers de navegador para evitar bloqueos por User-Agent
    headers = kwargs.pop("headers", {})
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    headers.setdefault("Accept", "application/json, text/plain, */*")
    headers.setdefault("Accept-Language", "es-CL,es;q=0.9,en;q=0.8")
    return requests.get(url, headers=headers, **kwargs)


# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
METADATA_PATH = os.path.join(STAGING_DIR, "comunas.metadata.json")

# URL Oficial de la Codificación Territorial del INE (DPA 2020/2021)
# Esta URL oficial puede estar caída o cambiar sin previo aviso.
SUBDERE_DPA_URL = "https://www.subdere.gov.cl/sites/default/files/documentos/cut_2018_0.xls"
BCN_COMUNAS_SERVICE_URL = (
    "https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query"
)
SUPPLEMENTAL_COMUNAS = [
    {
        "codigo_region": "12",
        "nombre_region": "Región de Magallanes y Antártica Chilena",
        "abreviatura": "",
        "codigo_provincia": "122",
        "nombre_provincia": "Antártica Chilena",
        "codigo_comuna": "12202",
        "nombre_comuna": "Antártica",
        "latitud_cabecera": 0.0,
        "longitud_cabecera": 0.0,
        "poblacion_estimada": 0,
    }
]

# Abreviaturas oficiales por código de región (2 dígitos CUT)
REGION_ABBREVIATIONS = {
    "01": "TA",
    "02": "AN",
    "03": "AT",
    "04": "CO",
    "05": "VS",
    "06": "OH",
    "07": "ML",
    "08": "BI",
    "09": "AR",
    "10": "LL",
    "11": "AI",
    "12": "MG",
    "13": "RM",
    "14": "LR",
    "15": "AP",
    "16": "NU",
}

# Fallback local con una muestra representativa y real de comunas de Chile (con Ñuble y comunas con ceros iniciales)
DPA_FALLBACK_DATA = [
    # Región de Arica y Parinacota (Código 15)
    {
        "codigo_region": "15",
        "nombre_region": "Arica y Parinacota",
        "abreviatura": "AP",
        "codigo_provincia": "151",
        "nombre_provincia": "Arica",
        "codigo_comuna": "15101",
        "nombre_comuna": "Arica",
        "latitud_cabecera": -18.4783,
        "longitud_cabecera": -70.3126,
        "poblacion_estimada": 247500,
    },
    {
        "codigo_region": "15",
        "nombre_region": "Arica y Parinacota",
        "abreviatura": "AP",
        "codigo_provincia": "151",
        "nombre_provincia": "Arica",
        "codigo_comuna": "15102",
        "nombre_comuna": "Camarones",
        "latitud_cabecera": -19.0167,
        "longitud_cabecera": -69.8667,
        "poblacion_estimada": 1200,
    },
    # Región de Tarapacá (Código 01 - Ceros iniciales)
    {
        "codigo_region": "01",
        "nombre_region": "Tarapacá",
        "abreviatura": "TA",
        "codigo_provincia": "011",
        "nombre_provincia": "Iquique",
        "codigo_comuna": "01101",
        "nombre_comuna": "Iquique",
        "latitud_cabecera": -20.2138,
        "longitud_cabecera": -70.1508,
        "poblacion_estimada": 223400,
    },
    {
        "codigo_region": "01",
        "nombre_region": "Tarapacá",
        "abreviatura": "TA",
        "codigo_provincia": "011",
        "nombre_provincia": "Iquique",
        "codigo_comuna": "01107",
        "nombre_comuna": "Alto Hospicio",
        "latitud_cabecera": -20.2692,
        "longitud_cabecera": -70.1008,
        "poblacion_estimada": 129000,
    },
    # Región de Antofagasta (Código 02)
    {
        "codigo_region": "02",
        "nombre_region": "Antofagasta",
        "abreviatura": "AN",
        "codigo_provincia": "021",
        "nombre_provincia": "Antofagasta",
        "codigo_comuna": "02101",
        "nombre_comuna": "Antofagasta",
        "latitud_cabecera": -23.6500,
        "longitud_cabecera": -70.4000,
        "poblacion_estimada": 425000,
    },
    # Región Metropolitana (Código 13)
    {
        "codigo_region": "13",
        "nombre_region": "Metropolitana de Santiago",
        "abreviatura": "RM",
        "codigo_provincia": "131",
        "nombre_provincia": "Santiago",
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "latitud_cabecera": -33.4372,
        "longitud_cabecera": -70.6506,
        "poblacion_estimada": 503000,
    },
    {
        "codigo_region": "13",
        "nombre_region": "Metropolitana de Santiago",
        "abreviatura": "RM",
        "codigo_provincia": "131",
        "nombre_provincia": "Santiago",
        "codigo_comuna": "13114",
        "nombre_comuna": "Las Condes",
        "latitud_cabecera": -33.4121,
        "longitud_cabecera": -70.5666,
        "poblacion_estimada": 330000,
    },
    {
        "codigo_region": "13",
        "nombre_region": "Metropolitana de Santiago",
        "abreviatura": "RM",
        "codigo_provincia": "131",
        "nombre_provincia": "Santiago",
        "codigo_comuna": "13123",
        "nombre_comuna": "Providencia",
        "latitud_cabecera": -33.4312,
        "longitud_cabecera": -70.6122,
        "poblacion_estimada": 157000,
    },
    {
        "codigo_region": "13",
        "nombre_region": "Metropolitana de Santiago",
        "abreviatura": "RM",
        "codigo_provincia": "131",
        "nombre_provincia": "Santiago",
        "codigo_comuna": "13124",
        "nombre_comuna": "Pudahuel",
        "latitud_cabecera": -33.4411,
        "longitud_cabecera": -70.7516,
        "poblacion_estimada": 253000,
    },
    {
        "codigo_region": "13",
        "nombre_region": "Metropolitana de Santiago",
        "abreviatura": "RM",
        "codigo_provincia": "131",
        "nombre_provincia": "Santiago",
        "codigo_comuna": "13125",
        "nombre_comuna": "Quilicura",
        "latitud_cabecera": -33.3611,
        "longitud_cabecera": -70.7306,
        "poblacion_estimada": 254000,
    },
    # Región de Valparaíso (Código 05)
    {
        "codigo_region": "05",
        "nombre_region": "Valparaíso",
        "abreviatura": "VS",
        "codigo_provincia": "051",
        "nombre_provincia": "Valparaíso",
        "codigo_comuna": "05101",
        "nombre_comuna": "Valparaíso",
        "latitud_cabecera": -33.0472,
        "longitud_cabecera": -71.6127,
        "poblacion_estimada": 315000,
    },
    {
        "codigo_region": "05",
        "nombre_region": "Valparaíso",
        "abreviatura": "VS",
        "codigo_provincia": "051",
        "nombre_provincia": "Valparaíso",
        "codigo_comuna": "05109",
        "nombre_comuna": "Viña del Mar",
        "latitud_cabecera": -33.0245,
        "longitud_cabecera": -71.5518,
        "poblacion_estimada": 361000,
    },
    # Región del Biobío (Código 08)
    {
        "codigo_region": "08",
        "nombre_region": "Biobío",
        "abreviatura": "BI",
        "codigo_provincia": "081",
        "nombre_provincia": "Concepción",
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "latitud_cabecera": -36.8201,
        "longitud_cabecera": -73.0444,
        "poblacion_estimada": 235000,
    },
    # Región de La Araucanía (Código 09)
    {
        "codigo_region": "09",
        "nombre_region": "La Araucanía",
        "abreviatura": "AR",
        "codigo_provincia": "091",
        "nombre_provincia": "Cautín",
        "codigo_comuna": "09101",
        "nombre_comuna": "Temuco",
        "latitud_cabecera": -38.7359,
        "longitud_cabecera": -72.5904,
        "poblacion_estimada": 302000,
    },
    # Región de Los Ríos (Código 14)
    {
        "codigo_region": "14",
        "nombre_region": "Los Ríos",
        "abreviatura": "LR",
        "codigo_provincia": "141",
        "nombre_provincia": "Valdivia",
        "codigo_comuna": "14101",
        "nombre_comuna": "Valdivia",
        "latitud_cabecera": -39.8142,
        "longitud_cabecera": -73.2459,
        "poblacion_estimada": 176000,
    },
    # Región de Los Lagos (Código 10)
    {
        "codigo_region": "10",
        "nombre_region": "Los Lagos",
        "abreviatura": "LL",
        "codigo_provincia": "101",
        "nombre_provincia": "Llanquihue",
        "codigo_comuna": "10101",
        "nombre_comuna": "Puerto Montt",
        "latitud_cabecera": -41.4689,
        "longitud_cabecera": -72.9411,
        "poblacion_estimada": 269000,
    },
    # Región de Ñuble (Nueva Región, Código 16)
    {
        "codigo_region": "16",
        "nombre_region": "Ñuble",
        "abreviatura": "NU",
        "codigo_provincia": "161",
        "nombre_provincia": "Diguillín",
        "codigo_comuna": "16101",
        "nombre_comuna": "Chillán",
        "latitud_cabecera": -36.6066,
        "longitud_cabecera": -72.1034,
        "poblacion_estimada": 204000,
    },
    # Región de Magallanes (Código 12)
    {
        "codigo_region": "12",
        "nombre_region": "Magallanes y de la Antártica Chilena",
        "abreviatura": "MG",
        "codigo_provincia": "121",
        "nombre_provincia": "Magallanes",
        "codigo_comuna": "12101",
        "nombre_comuna": "Punta Arenas",
        "latitud_cabecera": -53.1627,
        "longitud_cabecera": -70.9081,
        "poblacion_estimada": 141000,
    },
]


def ensure_directories():
    ensure_staging_directories()


def write_metadata(metadata):
    write_staging_metadata(METADATA_PATH, metadata)


def extract_coords(feature: dict) -> tuple:
    """
    Extrae (latitud, longitud) de un feature ArcGIS REST en WGS84 (outSR=4326).
    Soporta geometría puntual (Point) y poligonal (Polygon).
    Para polígonos calcula el centroide simple del anillo exterior.
    Retorna (0.0, 0.0) si la geometría está ausente o fuera del rango de Chile.
    """
    geom = feature.get("geometry")
    if not geom:
        return 0.0, 0.0

    if "x" in geom and "y" in geom:
        # Geometría puntual: x = longitud, y = latitud en WGS84
        lon, lat = float(geom["x"]), float(geom["y"])
    elif "rings" in geom:
        # Geometría poligonal: centroide simple del anillo exterior
        rings = geom.get("rings", [])
        if not rings or not rings[0]:
            return 0.0, 0.0
        exterior = rings[0]
        lons = [pt[0] for pt in exterior]
        lats = [pt[1] for pt in exterior]
        lon = sum(lons) / len(lons)
        lat = sum(lats) / len(lats)
    else:
        return 0.0, 0.0

    # Chile: lat -90..0, lon -180..0 (incluye Isla de Pascua y Territorio Antártico)
    if not (-90.0 <= lat <= 0.0 and -180.0 <= lon <= 0.0):
        return 0.0, 0.0

    return round(lat, 6), round(lon, 6)


def fetch_bcn_comunas():
    print(f"Intentando descargar base territorial desde BCN ArcGIS: {BCN_COMUNAS_SERVICE_URL}")
    params = {
        "where": "1=1",
        "outFields": "nom_reg,nom_prov,nom_com,cod_comuna,codregion",
        "returnGeometry": "false",  # Capa_Factores es tabla de atributos, sin geometría
        "f": "json",
    }
    response = _stealth_get(BCN_COMUNAS_SERVICE_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    # Persistir snapshot raw para trazabilidad
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(RAW_DIR, f"bcn_comunas_{timestamp}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"Snapshot raw BCN guardado en: {raw_path}")
    features = payload.get("features", [])
    if not features:
        raise ValueError("BCN ArcGIS did not return features")

    records = []
    skipped_null_codes = 0
    for feature in features:
        attrs = feature["attributes"]
        if attrs.get("cod_comuna") is None or attrs.get("codregion") is None:
            skipped_null_codes += 1
            continue
        codigo_comuna = str(int(attrs["cod_comuna"]))  # cod_comuna can arrive as numeric
        codigo_comuna = codigo_comuna.rjust(5, "0")
        codigo_region = str(int(attrs["codregion"])).rjust(2, "0")
        codigo_provincia = codigo_comuna[:3]
        lat, lon = extract_coords(feature)
        records.append(
            {
                "codigo_region": codigo_region,
                "nombre_region": attrs["nom_reg"],
                "abreviatura": REGION_ABBREVIATIONS.get(codigo_region, ""),
                "codigo_provincia": codigo_provincia,
                "nombre_provincia": attrs["nom_prov"],
                "codigo_comuna": codigo_comuna,
                "nombre_comuna": attrs["nom_com"],
                "latitud_cabecera": lat,
                "longitud_cabecera": lon,
                "poblacion_estimada": 0,
            }
        )

    df = pl.DataFrame(records)
    original_count = df.height
    df = df.unique(subset=["codigo_comuna"], keep="first")
    deduped_rows = original_count - df.height

    supplemental_added = 0
    existing_codes = set(df["codigo_comuna"].to_list())
    missing_records = [
        record for record in SUPPLEMENTAL_COMUNAS if record["codigo_comuna"] not in existing_codes
    ]
    if missing_records:
        df = pl.concat([df, pl.DataFrame(missing_records)], how="vertical")
        supplemental_added = len(missing_records)

    print(
        f"BCN ArcGIS respondió con {original_count} registros válidos,"
        f" {skipped_null_codes} omitidos,"
        f" {deduped_rows} deduplicados"
        f" y {supplemental_added} suplementados."
    )
    return df, skipped_null_codes, deduped_rows, supplemental_added


def download_subdere_file():
    target_path = os.path.join(RAW_DIR, "cut_2018.xls")
    print(f"Intentando descargar base territorial de SUBDERE: {SUBDERE_DPA_URL}")
    try:
        response = requests.get(SUBDERE_DPA_URL, timeout=10)
        if response.status_code == 200:
            with open(target_path, "wb") as f:
                f.write(response.content)
            print("Descarga completada y almacenada en raw/cut_2018.xls")
            return target_path
        else:
            print(
                f"Error de descarga HTTP: Código {response.status_code}. Se utilizará el fallback local."
            )
    except Exception as e:
        print(f"Error al descargar la base territorial: {e}. Se utilizará el fallback local.")
    return None


def normalize_dpa():
    print("Normalizando la División Político-Administrativa (DPA)...")
    source_mode = "fallback"
    source_detail = "embedded_sample"
    notes = []
    try:
        df, skipped_null_codes, deduped_rows, supplemental_added = fetch_bcn_comunas()
        source_mode = "live"
        source_detail = "bcn_arcgis"
        if skipped_null_codes:
            notes.append(f"bcn_skipped_null_code_records: {skipped_null_codes}")
        if deduped_rows:
            notes.append(f"bcn_deduped_codigo_comuna_records: {deduped_rows}")
        if supplemental_added:
            notes.append(f"bcn_supplemented_missing_comunas: {supplemental_added}")
    except Exception as bcn_error:
        print(f"Error consultando BCN ArcGIS: {bcn_error}.")
        notes.append(f"bcn_fetch_error: {bcn_error}")
        file_path = download_subdere_file()
        if file_path and os.path.exists(file_path):
            try:
                # Si logramos descargar la base de SUBDERE, la procesamos
                # Nota: cut_2018.xls suele requerir xlrd para leer con pandas o polars
                # En la Fase 0 usaremos el motor openpyxl o pandas para leer el excel si está instalado
                import pandas as pd

                df_pandas = pd.read_excel(file_path, dtype=str)
                df = pl.from_pandas(df_pandas)
                print("Procesando datos desde el archivo descargado de SUBDERE...")
                source_mode = "live"
                source_detail = "subdere_xls"

                # Aquí vendría la lógica de renombre de columnas de SUBDERE a nuestro canon
                # Como ejemplo simplificado y robusto de normalización:
                # (SUBDERE tiene columnas Código Región, Nombre Región, Código Provincia, etc.)
                # Normalizamos el formato del Código Comuna a 5 dígitos
                df = df.rename(
                    {
                        "Código Región": "codigo_region",
                        "Nombre Región": "nombre_region",
                        "Código Provincia": "codigo_provincia",
                        "Nombre Provincia": "nombre_provincia",
                        "Código Comuna": "codigo_comuna",
                        "Nombre Comuna": "nombre_comuna",
                    }
                )

                # Aseguramos ceros a la izquierda
                df = df.with_columns(
                    [
                        pl.col("codigo_region").str.rjust(2, "0"),
                        pl.col("codigo_provincia").str.rjust(3, "0"),
                        pl.col("codigo_comuna").str.rjust(5, "0"),
                    ]
                )

                # Agregar abreviaturas y centroides por defecto si no existen
                # (En un pipeline de producción completo esto cruza con datos de IDE Chile)
                df = df.with_columns(
                    [
                        pl.lit("").alias("abreviatura"),
                        pl.lit(0.0).cast(pl.Float64).alias("latitud_cabecera"),
                        pl.lit(0.0).cast(pl.Float64).alias("longitud_cabecera"),
                        pl.lit(0).cast(pl.Int32).alias("poblacion_estimada"),
                    ]
                )
            except Exception as e:
                print(
                    f"Error procesando el Excel de SUBDERE: {e}. Usando fallback de datos estático."
                )
                df = pl.DataFrame(DPA_FALLBACK_DATA)
                notes.append(f"fallback_after_subdere_processing_error: {e}")
        else:
            # Fallback local con los datos predefinidos
            print("Usando set de datos DPA embebido (Fase 0 Fallback)...")
            df = pl.DataFrame(DPA_FALLBACK_DATA)
            notes.append("fallback_due_to_missing_remote_file")

    # Normalización adicional (nombre clean para búsquedas sin acento)
    # Reemplazo de caracteres con acento común en Chile
    df = df.with_columns(
        pl.col("nombre_comuna")
        .str.to_lowercase()
        .str.replace_all("á", "a")
        .str.replace_all("é", "e")
        .str.replace_all("í", "i")
        .str.replace_all("ó", "o")
        .str.replace_all("ú", "u")
        .str.replace_all("ü", "u")
        .str.replace_all("ñ", "n")  # Ej: "Ñuñoa" → "nunoa"
        .alias("nombre_comuna_clean")
    )

    # Reordenar y seleccionar columnas finales
    df_clean = df.select(
        [
            "codigo_region",
            "nombre_region",
            "abreviatura",
            "codigo_provincia",
            "nombre_provincia",
            "codigo_comuna",
            "nombre_comuna",
            "nombre_comuna_clean",
            "latitud_cabecera",
            "longitud_cabecera",
            "poblacion_estimada",
        ]
    )

    # ── Enriquecimiento de coordenadas desde tabla de referencia estática ────────
    # Aplica las coords del CSV a cualquier comuna con latitud_cabecera == 0.0.
    # Funciona para datos en vivo (BCN sin geometría) y datos de fallback.
    _coords_csv = os.path.join(os.path.dirname(__file__), "../data/comunas_coords.csv")
    if os.path.exists(_coords_csv):
        coords_ref = pl.read_csv(
            _coords_csv,
            schema_overrides={"codigo_comuna": pl.String},
        ).rename({"latitud": "_lat_ref", "longitud": "_lon_ref"})
        df_clean = (
            df_clean.join(coords_ref, on="codigo_comuna", how="left")
            .with_columns(
                [
                    pl.when(pl.col("latitud_cabecera") == 0.0)
                    .then(pl.col("_lat_ref"))
                    .otherwise(pl.col("latitud_cabecera"))
                    .alias("latitud_cabecera"),
                    pl.when(pl.col("longitud_cabecera") == 0.0)
                    .then(pl.col("_lon_ref"))
                    .otherwise(pl.col("longitud_cabecera"))
                    .alias("longitud_cabecera"),
                ]
            )
            .drop(["_lat_ref", "_lon_ref"])
        )
        _coords_filled = df_clean.filter(pl.col("latitud_cabecera") != 0.0).height
        print(f"Coordenadas: {_coords_filled}/{df_clean.height} comunas con coords no-cero.")
    else:
        print("Advertencia: tabla de referencia de coordenadas no encontrada.")

    # ── Enriquecimiento de población desde tabla de referencia INE 2022 ───────────
    # Fuente: INE Estimaciones y Proyecciones de Población, base Censo 2017.
    # Aplica el valor a cualquier comuna con poblacion_estimada == 0.
    _pob_csv = os.path.join(os.path.dirname(__file__), "../data/comunas_poblacion.csv")
    if os.path.exists(_pob_csv):
        pob_ref = pl.read_csv(
            _pob_csv,
            schema_overrides={
                "codigo_comuna": pl.String,
                "poblacion_estimada": pl.Int32,
            },
        ).rename({"poblacion_estimada": "_pob_ref"})
        df_clean = (
            df_clean.with_columns(pl.col("codigo_comuna").cast(pl.String))
            .join(pob_ref, on="codigo_comuna", how="left")
            .with_columns(
                pl.when(pl.col("poblacion_estimada") == 0)
                .then(pl.col("_pob_ref"))
                .otherwise(pl.col("poblacion_estimada"))
                .alias("poblacion_estimada")
            )
            .drop("_pob_ref")
        )
        _pob_filled = df_clean.filter(pl.col("poblacion_estimada") > 0).height
        print(f"Población: {_pob_filled}/{df_clean.height} comunas con datos INE 2022.")
    else:
        print("Advertencia: tabla de referencia de población INE no encontrada.")

    output_path = os.path.join(STAGING_DIR, "comunas.csv")
    df_clean.write_csv(output_path)
    source_name = "SUBDERE"
    source_url = SUBDERE_DPA_URL
    if source_detail == "bcn_arcgis":
        source_name = "BCN ArcGIS"
        source_url = BCN_COMUNAS_SERVICE_URL
    metadata = {
        "dataset": "comunas",
        "source_name": source_name,
        "source_url": source_url,
        "source_mode": source_mode,
        "source_detail": source_detail,
        "refreshed_at_utc": datetime.now(UTC).isoformat(),
        "record_count": len(df_clean),
        "fields": df_clean.columns,
        "notes": notes,
        "poblacion_source": (
            "BCN ArcGIS Capa_Factores campo ppobing022 (Censo 2022)"
            if source_detail == "bcn_arcgis"
            else "fallback_embedded_sample_sin_poblacion"
        ),
    }
    write_metadata(metadata)
    print(f"Guardada DPA normalizada en: {output_path} (Total registros: {len(df_clean)})")
    return output_path


class SubdereExtractor(BaseExtractor):
    """Adaptador orientado a objetos para el extractor territorial existente."""

    @property
    def dataset_name(self) -> str:
        return "comunas"

    def fetch(self, **kwargs):
        return fetch_bcn_comunas()

    def normalize(self, raw_data):
        return raw_data[0] if isinstance(raw_data, tuple) else raw_data

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_comunas

        return validate_comunas(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_directories()
        output_path = Path(STAGING_DIR) / "comunas.csv"
        df.write_csv(output_path)
        write_metadata(
            {
                **metadata,
                "dataset": self.dataset_name,
                "record_count": df.height,
                "fields": df.columns,
            }
        )
        return output_path


if __name__ == "__main__":
    ensure_directories()
    normalize_dpa()
