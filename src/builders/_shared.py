"""Rutas, constantes y configuración de catálogo compartidas por los builders.

Este módulo no importa código específico del proyecto (extractores,
validación), por lo que puede ser importado libremente por cualquier builder
y por `build_dev_db.py` sin riesgo de imports circulares.
"""

import json
import os
from datetime import timezone

UTC = timezone.utc

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
COMUNAS_METADATA_PATH = os.path.join(STAGING_DIR, "comunas.metadata.json")
INDICADORES_METADATA_PATH = os.path.join(STAGING_DIR, "indicadores.metadata.json")
CENSO_METADATA_PATH = os.path.join(STAGING_DIR, "censo_comunal.metadata.json")
SALUD_METADATA_PATH = os.path.join(STAGING_DIR, "establecimientos_salud.metadata.json")
CENSO_HOGARES_METADATA_PATH = os.path.join(STAGING_DIR, "censo_hogares_viviendas.metadata.json")
ELECTORAL_METADATA_PATH = os.path.join(STAGING_DIR, "distritos_electorales.metadata.json")
FINANZAS_METADATA_PATH = os.path.join(STAGING_DIR, "finanzas_municipales.metadata.json")
RESULTADOS_EDUCACIONALES_METADATA_PATH = os.path.join(
    STAGING_DIR, "resultados_educacionales.metadata.json"
)
SIEDU_METADATA_PATH = os.path.join(STAGING_DIR, "indicadores_urbanos_siedu.metadata.json")
EMPRESAS_METADATA_PATH = os.path.join(STAGING_DIR, "empresas.metadata.json")
POBREZA_COMUNAL_METADATA_PATH = os.path.join(STAGING_DIR, "pobreza_comunal.metadata.json")
CONSUMO_ELECTRICO_COMUNAL_METADATA_PATH = os.path.join(
    STAGING_DIR, "consumo_electrico_comunal.metadata.json"
)
EXCEL_MAX_ROWS = 1_048_576  # Límite físico de Excel por hoja
PUBLISHABLE_ARTIFACT_SUFFIXES = (".json", ".md", ".parquet")
PUBLISHABLE_BUNDLE_ZIP_NAME = "chile-hub-publishable-bundle.zip"
PUBLISHABLE_BUNDLE_SHA256_NAME = "chile-hub-publishable-bundle.zip.sha256"


def _load_catalog_config() -> dict:
    path = os.path.join(ROOT_DIR, "data", "dataset_catalog_config.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Archivo de configuración de catálogo no encontrado: {path}\n"
            "Este archivo es la fuente de verdad para los metadatos de datasets.\n"
            "Asegúrate de que existe en el repositorio (debe estar tracked en git).\n"
            "Si acabas de clonar, verifica que el archivo no esté en .gitignore."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]  # json.load → dict en runtime


DATASET_CATALOG_CONFIG = _load_catalog_config()
