import hashlib
import json
import os
import sqlite3
import sys
import zipfile
from datetime import UTC, datetime

import duckdb
import polars as pl

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.pipeline_status_utils import (
    build_hub_health,
    compute_freshness,
    write_dataset_catalog_markdown_file,
    write_drift_report_markdown_file,
    write_hub_health_markdown_file,
    write_overview_markdown_file,
    write_provenance_report_markdown_file,
    write_redistribution_report_markdown_file,
    write_status_markdown_file,
)
from src.validation import (
    validate_censo_comunal,
    validate_censo_hogares_viviendas,
    validate_comunas,
    validate_distritos_electorales,
    validate_establecimientos_educacionales,
    validate_establecimientos_salud,
    validate_indicadores,
    validate_provincias,
    validate_regiones,
)

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
COMUNAS_METADATA_PATH = os.path.join(STAGING_DIR, "comunas.metadata.json")
INDICADORES_METADATA_PATH = os.path.join(STAGING_DIR, "indicadores.metadata.json")
CENSO_METADATA_PATH = os.path.join(STAGING_DIR, "censo_comunal.metadata.json")
SALUD_METADATA_PATH = os.path.join(STAGING_DIR, "establecimientos_salud.metadata.json")
CENSO_HOGARES_METADATA_PATH = os.path.join(STAGING_DIR, "censo_hogares_viviendas.metadata.json")
ELECTORAL_METADATA_PATH = os.path.join(STAGING_DIR, "distritos_electorales.metadata.json")
PUBLISHABLE_ARTIFACT_SUFFIXES = (".json", ".md", ".parquet")
PUBLISHABLE_BUNDLE_ZIP_NAME = "chile-hub-publishable-bundle.zip"
PUBLISHABLE_BUNDLE_SHA256_NAME = "chile-hub-publishable-bundle.zip.sha256"

DATASET_CATALOG_CONFIG = {
    "regiones": {
        "description": "Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel.",
        "join_keys": ["codigo_region"],
        "confidence_tier": "Tier B",
        "expected_record_count": 16,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY",
            "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Derivada de datos abiertos BCN reutilizables con atribucion.",
        },
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('regiones')",
            "duckdb": "SELECT *\nFROM 'data/normalized/regiones.parquet'\nORDER BY codigo_region;",
            "cli": "python -m src.chile_hub show regiones",
        },
        "outputs": {
            "parquet": "data/normalized/regiones.parquet",
            "json": "data/normalized/regiones.json",
            "duckdb_table": "regiones",
            "sqlite_table": "regiones",
            "excel_sheet": "Regiones",
        },
        "documentation": "docs/datasets/regiones.md",
    },
    "provincias": {
        "description": "Capa derivada de provincias para cruces intermedios entre region y comuna.",
        "join_keys": ["codigo_provincia", "codigo_region"],
        "confidence_tier": "Tier B",
        "expected_record_count": 56,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY",
            "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Derivada de datos abiertos BCN reutilizables con atribucion.",
        },
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('provincias')",
            "duckdb": "SELECT *\nFROM 'data/normalized/provincias.parquet'\nWHERE codigo_region = '13';",
            "cli": "python -m src.chile_hub show provincias",
        },
        "outputs": {
            "parquet": "data/normalized/provincias.parquet",
            "json": "data/normalized/provincias.json",
            "duckdb_table": "provincias",
            "sqlite_table": "provincias",
            "excel_sheet": "Provincias",
        },
        "documentation": "docs/datasets/provincias.md",
    },
    "comunas": {
        "description": "Base territorial normalizada para cruces por region, provincia y comuna.",
        "join_keys": ["codigo_comuna", "codigo_region"],
        "confidence_tier": "Tier B",
        "expected_record_count": 346,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY",
            "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Fuente operativa BCN dentro de su superficie de datos abiertos; atribucion requerida.",
        },
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('comunas')",
            "duckdb": "SELECT codigo_comuna, nombre_comuna, nombre_region\nFROM 'data/normalized/comunas.parquet'\nLIMIT 10;",
            "cli": "python -m src.chile_hub path comunas --output parquet",
        },
        "outputs": {
            "parquet": "data/normalized/comunas.parquet",
            "json": "data/normalized/comunas.json",
            "duckdb_table": "comunas",
            "sqlite_table": "comunas",
            "excel_sheet": "Comunas y Regiones",
        },
        "documentation": "docs/datasets/comunas.md",
    },
    "comunas_enriquecidas": {
        "description": (
            "Comunas con coordenadas de cabecera y poblacion estimada INE, listas para "
            "analisis territorial sin joins adicionales."
        ),
        "join_keys": ["codigo_comuna"],
        "confidence_tier": "Tier B",
        "expected_record_count": 346,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY",
            "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Derivada de datos abiertos BCN con coordenadas e informacion INE.",
        },
        "freshness_policy": {"max_age_hours": 24 * 90, "label": "estable"},
        "usage_examples": {
            "python": (
                "from src.chile_hub import ChileHub\n\nhub = ChileHub()\n"
                "df = hub.load_polars('comunas_enriquecidas')"
            ),
            "duckdb": (
                "SELECT codigo_comuna, nombre_comuna, latitud_cabecera, "
                "longitud_cabecera, poblacion_estimada\n"
                "FROM 'data/normalized/comunas_enriquecidas.parquet'\n"
                "ORDER BY poblacion_estimada DESC LIMIT 10;"
            ),
            "cli": "python -m src.chile_hub show comunas_enriquecidas",
        },
        "outputs": {
            "parquet": "data/normalized/comunas_enriquecidas.parquet",
            "json": "data/normalized/comunas_enriquecidas.json",
            "duckdb_table": "comunas_enriquecidas",
            "sqlite_table": "comunas_enriquecidas",
            "excel_sheet": "ComunasEnriquecidas",
        },
        "documentation": "docs/datasets/comunas_enriquecidas.md",
    },
    "indicadores": {
        "description": "Serie de indicadores economicos diarios de referencia para analisis y software.",
        "join_keys": ["fecha", "codigo_indicador"],
        "confidence_tier": "Tier A/B",
        "reuse_policy": {
            "status": "open-attribution",
            "license": "Reproducción libre con citación (BCCh / INE)",
            "license_url": "https://www.bcentral.cl/web/banco-central/terminos-y-condiciones",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Datos del Banco Central de Chile (BCCh) e INE. Libre reproducción con citación. Acceso vía mindicador.cl (API pública de la comunidad).",
        },
        "freshness_policy": {
            "max_age_hours": 72,
            "label": "diaria",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('indicadores')",
            "duckdb": "SELECT *\nFROM 'data/normalized/indicadores.parquet'\nORDER BY fecha DESC, codigo_indicador;",
            "cli": "python -m src.chile_hub show indicadores",
        },
        "outputs": {
            "parquet": "data/normalized/indicadores.parquet",
            "json": "data/normalized/indicadores_hoy.json",
            "duckdb_table": "indicadores",
            "sqlite_table": "indicadores",
            "excel_sheet": "Indicadores Diarios",
        },
        "documentation": "docs/datasets/indicadores.md",
    },
    "censo_comunal": {
        "description": "Perfil demografico comunal del Censo 2024 con sexo y grandes grupos de edad.",
        "join_keys": ["codigo_comuna", "codigo_region"],
        "confidence_tier": "Tier A",
        "expected_record_count": 346,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY 4.0",
            "license_url": "https://www.ine.gob.cl/terminos-de-uso",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Resultados oficiales del Censo 2024 publicados por el INE.",
        },
        "freshness_policy": {"max_age_hours": 24 * 365 * 10, "label": "decenal"},
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('censo_comunal')",
            "duckdb": "SELECT * FROM 'data/normalized/censo_comunal.parquet' ORDER BY poblacion_censada DESC;",
            "cli": "python -m src.chile_hub show censo_comunal",
        },
        "outputs": {
            "parquet": "data/normalized/censo_comunal.parquet",
            "json": "data/normalized/censo_comunal.json",
            "duckdb_table": "censo_comunal",
            "sqlite_table": "censo_comunal",
            "excel_sheet": "Censo Comunal",
        },
        "documentation": "docs/datasets/censo_comunal.md",
    },
    "censo_hogares_viviendas": {
        "description": "Viviendas y hogares censados por comuna, ocupacion y tamano medio del hogar.",
        "join_keys": ["codigo_comuna", "codigo_region"],
        "confidence_tier": "Tier A",
        "expected_record_count": 346,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY 4.0",
            "license_url": "https://www.ine.gob.cl/terminos-de-uso",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Resultados oficiales del Censo 2024 publicados por el INE.",
        },
        "freshness_policy": {"max_age_hours": 87600, "label": "decenal"},
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('censo_hogares_viviendas')",
            "duckdb": "SELECT * FROM 'data/normalized/censo_hogares_viviendas.parquet';",
            "cli": "python -m src.chile_hub show censo_hogares_viviendas",
        },
        "outputs": {
            "parquet": "data/normalized/censo_hogares_viviendas.parquet",
            "json": "data/normalized/censo_hogares_viviendas.json",
        },
        "documentation": "docs/datasets/censo_hogares_viviendas.md",
    },
    "establecimientos_salud": {
        "description": "Directorio vigente de establecimientos de salud con tipo, dependencia, urgencia y ubicacion.",
        "join_keys": ["codigo_establecimiento", "codigo_comuna"],
        "confidence_tier": "Tier A",
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC0",
            "license_url": "http://www.opendefinition.org/licenses/cc-zero",
            "attribution_required": False,
            "redistribution_ok": True,
            "summary": "Directorio oficial MINSAL publicado en datos.gob.cl bajo CC0.",
        },
        "freshness_policy": {"max_age_hours": 24 * 45, "label": "mensual"},
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('establecimientos_salud')",
            "duckdb": "SELECT codigo_comuna, count(*) FROM 'data/normalized/establecimientos_salud.parquet' GROUP BY 1;",
            "cli": "python -m src.chile_hub show establecimientos_salud",
        },
        "outputs": {
            "parquet": "data/normalized/establecimientos_salud.parquet",
            "json": "data/normalized/establecimientos_salud.json",
            "duckdb_table": "establecimientos_salud",
            "sqlite_table": "establecimientos_salud",
            "excel_sheet": "Establecimientos Salud",
        },
        "documentation": "docs/datasets/establecimientos_salud.md",
    },
    "distritos_electorales": {
        "description": "Asociación de comunas a distritos electorales (diputados) y circunscripciones senatoriales.",
        "join_keys": ["codigo_comuna"],
        "confidence_tier": "Tier A",
        "expected_record_count": 346,
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC0",
            "license_url": "http://www.opendefinition.org/licenses/cc-zero",
            "attribution_required": False,
            "redistribution_ok": True,
            "summary": "Asociación comunal a distritos y circunscripciones electorales basada en Ley N° 20.840.",
        },
        "freshness_policy": {"max_age_hours": 87600, "label": "estable"},
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('distritos_electorales')",
            "duckdb": "SELECT * FROM 'data/normalized/distritos_electorales.parquet';",
            "cli": "python -m src.chile_hub show distritos_electorales",
        },
        "outputs": {
            "parquet": "data/normalized/distritos_electorales.parquet",
            "json": "data/normalized/distritos_electorales.json",
        },
        "documentation": "docs/datasets/distritos_electorales.md",
    },
    "establecimientos_educacionales": {
        "description": "Directorio oficial del Ministerio de Educación (MINEDUC) con Rol Base de Datos (RBD), ubicación y dependencia administrativa.",
        "join_keys": ["codigo_comuna"],
        "confidence_tier": "Tier A",
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC-BY-3.0",
            "license_url": "https://creativecommons.org/licenses/by/3.0/cl/",
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Directorio oficial MINEDUC publicado por el Centro de Estudios del Ministerio de Educación de Chile bajo licencia CC BY.",
        },
        "freshness_policy": {"max_age_hours": 24 * 365, "label": "anual"},
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('establecimientos_educacionales')",
            "duckdb": "SELECT nombre_establecimiento, dependencia_administrativa FROM 'data/normalized/establecimientos_educacionales.parquet' LIMIT 10;",
            "cli": "python -m src.chile_hub show establecimientos_educacionales",
        },
        "outputs": {
            "parquet": "data/normalized/establecimientos_educacionales.parquet",
            "json": "data/normalized/establecimientos_educacionales.json",
            "duckdb_table": "establecimientos_educacionales",
            "sqlite_table": "establecimientos_educacionales",
            "excel_sheet": "Establecimientos Educacionales",
        },
        "documentation": "docs/datasets/establecimientos_educacionales.md",
    },
}


def build_freshness(refreshed_at_utc, max_age_hours):
    return compute_freshness(refreshed_at_utc, max_age_hours)


def build_freshness_warnings(dataset_name, freshness):
    status = freshness.get("status")
    age_hours = freshness.get("age_hours")
    max_age_hours = freshness.get("max_age_hours")

    if status == "stale":
        return [
            (
                f"{dataset_name} freshness is stale: "
                f"{age_hours}h since refresh, policy max is {max_age_hours}h"
            )
        ]
    if status == "unknown":
        return [f"{dataset_name} freshness is unknown: missing or invalid refreshed_at_utc"]
    return []


def build_indicator_delivery(metadata):
    indicator_codes = metadata.get("indicator_codes", [])
    delivery = metadata.get("indicator_delivery")
    if isinstance(delivery, dict) and delivery:
        return delivery

    delivery = {code: "live" for code in indicator_codes}
    for pair in metadata.get("raw_recoveries", []):
        delivery[pair.split("/", 1)[0]] = "raw_recovery"
    for pair in metadata.get("preserved_existing_pairs", []):
        delivery[pair.split("/", 1)[0]] = "preserved_existing"
    for code in metadata.get("published_backfills", []):
        delivery[code] = "published_backfill"
    return delivery


def build_degradation(dataset_name, dataset_metadata, validation):
    source_mode = dataset_metadata.get("source_mode")
    record_count = dataset_metadata.get("record_count")
    warnings = validation.get("warnings", [])

    if source_mode == "fallback":
        if dataset_name == "comunas":
            return {
                "status": "degraded",
                "impact": (
                    f"Cobertura territorial parcial: {record_count} comunas disponibles "
                    "desde fallback embebido."
                ),
                "recommended_action": "Reintentar extractores o restaurar la fuente territorial primaria.",
            }
        if dataset_name in {"regiones", "provincias"}:
            return {
                "status": "degraded",
                "impact": (
                    f"Capa derivada desde comunas en fallback; cardinalidad reducida a {record_count} filas."
                ),
                "recommended_action": "Recuperar comunas live para restaurar cobertura derivada completa.",
            }
        if dataset_name == "indicadores":
            return {
                "status": "degraded",
                "impact": "Valores provenientes de fallback local; no representan el último snapshot live.",
                "recommended_action": "Reintentar la API pública antes de redistribuir o usar en reporting.",
            }

    if warnings:
        return {
            "status": "warning",
            "impact": "; ".join(warnings),
            "recommended_action": "Revisar warnings operativos del dataset antes de consumirlo en producción.",
        }

    return {
        "status": "none",
        "impact": "Sin degradación operativa detectada en este build.",
        "recommended_action": "Ninguna.",
    }


def build_coverage(dataset_name, dataset_metadata):
    expected_record_count = DATASET_CATALOG_CONFIG.get(dataset_name, {}).get(
        "expected_record_count"
    )
    actual_record_count = dataset_metadata.get("record_count")

    if expected_record_count is None:
        return {
            "status": "not_applicable",
            "expected_record_count": None,
            "actual_record_count": actual_record_count,
            "coverage_ratio": None,
            "summary": "Sin baseline de cobertura por cardinalidad para esta capa.",
        }

    if actual_record_count is None or expected_record_count <= 0:
        return {
            "status": "unknown",
            "expected_record_count": expected_record_count,
            "actual_record_count": actual_record_count,
            "coverage_ratio": None,
            "summary": "No fue posible calcular cobertura contra el baseline esperado.",
        }

    coverage_ratio = round(actual_record_count / expected_record_count, 4)
    if actual_record_count >= expected_record_count:
        status = "full"
        summary = (
            f"Cobertura completa: {actual_record_count}/{expected_record_count} filas "
            "respecto del baseline esperado."
        )
    else:
        status = "partial"
        summary = (
            f"Cobertura parcial: {actual_record_count}/{expected_record_count} filas "
            "respecto del baseline esperado."
        )

    return {
        "status": status,
        "expected_record_count": expected_record_count,
        "actual_record_count": actual_record_count,
        "coverage_ratio": coverage_ratio,
        "summary": summary,
    }


def build_drift(dataset_metadata):
    source_mode = dataset_metadata.get("source_mode")
    coverage = dataset_metadata.get("coverage", {})
    degradation = dataset_metadata.get("degradation", {})
    coverage_status = coverage.get("status", "unknown")
    degradation_status = degradation.get("status", "none")

    drift_status = "healthy"
    if (
        source_mode == "fallback"
        or coverage_status in {"partial", "unknown"}
        or degradation_status in {"warning", "degraded"}
    ):
        drift_status = "drifted"

    if drift_status == "healthy":
        summary = "Sin drift operativo detectado en este build."
        recommended_action = "Ninguna."
    else:
        summary = (
            f"Drift detectado: mode={source_mode}, coverage={coverage_status}, "
            f"degradation={degradation_status}."
        )
        recommended_action = degradation.get(
            "recommended_action",
            "Revisar fuente, cobertura y warnings antes de consumir esta capa.",
        )

    return {
        "status": drift_status,
        "summary": summary,
        "recommended_action": recommended_action,
    }


def enrich_dataset_metadata(dataset_metadata, validations):
    enriched = {}
    for dataset_name, metadata in dataset_metadata.items():
        validation = validations.get(dataset_name, {})
        degradation = build_degradation(dataset_name, metadata, validation)
        coverage = build_coverage(dataset_name, metadata)
        enriched[dataset_name] = {
            **metadata,
            "degradation": degradation,
            "coverage": coverage,
        }
        enriched[dataset_name]["drift"] = build_drift(enriched[dataset_name])
    return enriched


def ensure_directories():
    os.makedirs(NORMALIZED_DIR, exist_ok=True)


def load_metadata(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_pipeline_metadata(dataset_metadata, validations):
    pipeline_metadata = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "datasets": dataset_metadata,
        "validations": validations,
    }
    output_path = os.path.join(NORMALIZED_DIR, "pipeline_metadata.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_metadata, f, ensure_ascii=False, indent=2)
    return output_path


def write_dataset_catalog(pipeline_metadata):
    datasets = []
    for dataset_name, dataset_metadata in pipeline_metadata["datasets"].items():
        validation = pipeline_metadata["validations"].get(dataset_name, {})
        config = DATASET_CATALOG_CONFIG.get(dataset_name, {})
        freshness_policy = config.get("freshness_policy", {})
        datasets.append(
            {
                "dataset": dataset_name,
                "description": config.get("description", ""),
                "source_name": dataset_metadata.get("source_name"),
                "source_url": dataset_metadata.get("source_url"),
                "source_mode": dataset_metadata.get("source_mode"),
                "source_detail": dataset_metadata.get("source_detail"),
                "refreshed_at_utc": dataset_metadata.get("refreshed_at_utc"),
                "record_count": dataset_metadata.get("record_count"),
                "fields": dataset_metadata.get("fields", []),
                "indicator_codes": dataset_metadata.get("indicator_codes", []),
                "indicator_delivery": dataset_metadata.get("indicator_delivery", {}),
                "join_keys": config.get("join_keys", []),
                "confidence_tier": config.get("confidence_tier"),
                "reuse_policy": config.get("reuse_policy", {}),
                "freshness": dataset_metadata.get("freshness", {}),
                "freshness_policy": freshness_policy,
                "coverage": dataset_metadata.get("coverage", {}),
                "drift": dataset_metadata.get("drift", {}),
                "usage_examples": config.get("usage_examples", {}),
                "outputs": config.get("outputs", {}),
                "documentation": config.get("documentation"),
                "validation_status": validation.get("status"),
                "warnings": validation.get("warnings", []),
                "degradation": dataset_metadata.get("degradation", {}),
                "notes": dataset_metadata.get("notes", []),
            }
        )

    catalog = {
        "generated_at_utc": pipeline_metadata["generated_at_utc"],
        "dataset_count": len(datasets),
        "datasets": datasets,
    }
    output_path = os.path.join(NORMALIZED_DIR, "dataset_catalog.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    return output_path


def compute_sha256(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_publishable_artifact_index():
    artifact_index = {}
    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        outputs = config.get("outputs", {})
        for output_type, path in outputs.items():
            if isinstance(path, str) and path.startswith("data/normalized/"):
                artifact_index[path] = {
                    "dataset": dataset_name,
                    "output_type": output_type,
                }
    shared_artifacts = {
        "data/normalized/pipeline_metadata.json": {
            "shared_type": "pipeline_metadata",
            "format": "json",
        },
        "data/normalized/pipeline_status.md": {
            "shared_type": "pipeline_status",
            "format": "markdown",
        },
        "data/normalized/hub_health.json": {
            "shared_type": "hub_health",
            "format": "json",
        },
        "data/normalized/hub_health.md": {
            "shared_type": "hub_health",
            "format": "markdown",
        },
        "data/normalized/hub_status.json": {
            "shared_type": "hub_status",
            "format": "json",
        },
        "data/normalized/hub_bundle.json": {
            "shared_type": "hub_bundle",
            "format": "json",
        },
        "data/normalized/redistribution_report.json": {
            "shared_type": "redistribution_report",
            "format": "json",
        },
        "data/normalized/redistribution_report.md": {
            "shared_type": "redistribution_report",
            "format": "markdown",
        },
        "data/normalized/provenance_report.json": {
            "shared_type": "provenance_report",
            "format": "json",
        },
        "data/normalized/provenance_report.md": {
            "shared_type": "provenance_report",
            "format": "markdown",
        },
        "data/normalized/drift_report.json": {
            "shared_type": "drift_report",
            "format": "json",
        },
        "data/normalized/drift_report.md": {
            "shared_type": "drift_report",
            "format": "markdown",
        },
        "data/normalized/overview.json": {
            "shared_type": "overview",
            "format": "json",
        },
        "data/normalized/overview.md": {
            "shared_type": "overview",
            "format": "markdown",
        },
        "data/normalized/dataset_catalog.json": {
            "shared_type": "dataset_catalog",
            "format": "json",
        },
        "data/normalized/dataset_catalog.md": {
            "shared_type": "dataset_catalog",
            "format": "markdown",
        },
        "data/normalized/artifact_manifest.json": {
            "shared_type": "artifact_manifest",
            "format": "json",
        },
    }
    artifact_index.update(shared_artifacts)
    return artifact_index


def write_artifact_manifest():
    artifact_index = build_publishable_artifact_index()
    artifacts = []
    for filename in sorted(os.listdir(NORMALIZED_DIR)):
        if not filename.endswith(PUBLISHABLE_ARTIFACT_SUFFIXES):
            continue
        path = os.path.join(NORMALIZED_DIR, filename)
        if not os.path.isfile(path):
            continue
        relative_path = f"data/normalized/{filename}"
        artifact_metadata = artifact_index.get(relative_path, {})
        artifacts.append(
            {
                "path": relative_path,
                "dataset": artifact_metadata.get("dataset"),
                "output_type": artifact_metadata.get("output_type"),
                "shared_type": artifact_metadata.get("shared_type"),
                "format": artifact_metadata.get("format"),
                "size_bytes": os.path.getsize(path),
                "sha256": compute_sha256(path),
            }
        )

    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "packages": [],
    }
    output_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return output_path


def write_hub_health_json(health):
    output_path = os.path.join(NORMALIZED_DIR, "hub_health.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)
    return output_path


def build_hub_status(hub_health):
    return {
        "generated_at_utc": hub_health.get("generated_at_utc"),
        "overall_status": hub_health.get("overall_status"),
        "dataset_count": hub_health.get("dataset_count"),
        "live_count": hub_health.get("live_count"),
        "fallback_count": hub_health.get("fallback_count"),
        "stale_count": hub_health.get("stale_count"),
        "drifted_count": hub_health.get("drifted_count"),
        "degraded_count": hub_health.get("degraded_count"),
        "warning_count": hub_health.get("warning_count"),
        "top_issue": hub_health.get("top_issue"),
        "top_issue_summary": hub_health.get("top_issue_summary"),
    }


def write_hub_status_json(hub_status):
    output_path = os.path.join(NORMALIZED_DIR, "hub_status.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(hub_status, f, ensure_ascii=False, indent=2)
    return output_path


def build_redistribution_report(dataset_catalog):
    datasets = []
    for entry in dataset_catalog.get("datasets", []):
        reuse_policy = entry.get("reuse_policy", {})
        redistribution_ok = reuse_policy.get("redistribution_ok")
        publishability_status = (
            "ready"
            if redistribution_ok is True
            else "review_terms"
            if redistribution_ok is False
            else "unknown"
        )
        if publishability_status == "ready":
            recommended_action = "Publicable con atribucion y referencia de fuente."
        elif publishability_status == "review_terms":
            recommended_action = "Revisar terminos vigentes antes de redistribuir fuera del repo."
        else:
            recommended_action = "Aclarar licencia o terminos antes de redistribuir."

        datasets.append(
            {
                "dataset": entry.get("dataset"),
                "publishability_status": publishability_status,
                "license": reuse_policy.get("license"),
                "license_url": reuse_policy.get("license_url"),
                "reuse_status": reuse_policy.get("status"),
                "attribution_required": reuse_policy.get("attribution_required"),
                "redistribution_ok": redistribution_ok,
                "summary": reuse_policy.get("summary"),
                "recommended_action": recommended_action,
                "documentation": entry.get("documentation"),
            }
        )

    report = {
        "generated_at_utc": dataset_catalog.get("generated_at_utc"),
        "dataset_count": len(datasets),
        "ready_count": sum(1 for entry in datasets if entry["publishability_status"] == "ready"),
        "review_terms_count": sum(
            1 for entry in datasets if entry["publishability_status"] == "review_terms"
        ),
        "unknown_count": sum(
            1 for entry in datasets if entry["publishability_status"] == "unknown"
        ),
        "datasets": datasets,
    }
    return report


def write_redistribution_report_json(report):
    output_path = os.path.join(NORMALIZED_DIR, "redistribution_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path


def build_provenance_report(dataset_catalog):
    datasets = []
    for entry in dataset_catalog.get("datasets", []):
        freshness = entry.get("freshness", {})
        freshness_status = freshness.get("status", "unknown")
        age_hours = freshness.get("age_hours")
        max_age_hours = freshness.get("max_age_hours")
        if age_hours is None or max_age_hours is None:
            freshness_label = freshness_status
        else:
            freshness_label = f"{freshness_status} ({age_hours}h / {max_age_hours}h)"
        warnings = entry.get("warnings", [])
        notes = entry.get("notes", [])
        diagnostic_summary = "Sin observaciones operativas."
        if warnings:
            diagnostic_summary = warnings[0]
        elif notes:
            diagnostic_summary = notes[0]

        datasets.append(
            {
                "dataset": entry.get("dataset"),
                "source_name": entry.get("source_name"),
                "source_url": entry.get("source_url"),
                "source_mode": entry.get("source_mode"),
                "source_detail": entry.get("source_detail"),
                "refreshed_at_utc": entry.get("refreshed_at_utc"),
                "freshness_status": freshness_status,
                "freshness_label": freshness_label,
                "reuse_status": entry.get("reuse_policy", {}).get("status"),
                "warning_count": len(warnings),
                "diagnostic_summary": diagnostic_summary,
                "documentation": entry.get("documentation"),
            }
        )

    return {
        "generated_at_utc": dataset_catalog.get("generated_at_utc"),
        "dataset_count": len(datasets),
        "live_count": sum(1 for entry in datasets if entry.get("source_mode") == "live"),
        "fallback_count": sum(1 for entry in datasets if entry.get("source_mode") == "fallback"),
        "datasets": datasets,
    }


def write_provenance_report_json(report):
    output_path = os.path.join(NORMALIZED_DIR, "provenance_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path


def build_drift_report(dataset_catalog):
    datasets = []
    for entry in dataset_catalog.get("datasets", []):
        source_mode = entry.get("source_mode")
        coverage = entry.get("coverage", {})
        degradation = entry.get("degradation", {})
        drift = entry.get("drift", {})
        coverage_status = coverage.get("status", "unknown")
        degradation_status = degradation.get("status", "none")
        drift_status = drift.get("status", "healthy")
        warnings = entry.get("warnings", [])
        diagnostic_summary = "Sin observaciones operativas."
        if warnings:
            diagnostic_summary = warnings[0]
        elif degradation.get("impact"):
            diagnostic_summary = degradation.get("impact")

        datasets.append(
            {
                "dataset": entry.get("dataset"),
                "drift_status": drift_status,
                "source_mode": source_mode,
                "coverage_status": coverage_status,
                "coverage_ratio": coverage.get("coverage_ratio"),
                "coverage_summary": coverage.get("summary"),
                "degradation_status": degradation_status,
                "degradation_impact": degradation.get("impact"),
                "drift_summary": drift.get("summary"),
                "warning_count": len(warnings),
                "diagnostic_summary": diagnostic_summary,
                "recommended_action": drift.get("recommended_action"),
                "documentation": entry.get("documentation"),
            }
        )

    return {
        "generated_at_utc": dataset_catalog.get("generated_at_utc"),
        "dataset_count": len(datasets),
        "drifted_count": sum(1 for entry in datasets if entry["drift_status"] == "drifted"),
        "healthy_count": sum(1 for entry in datasets if entry["drift_status"] == "healthy"),
        "fallback_count": sum(1 for entry in datasets if entry["source_mode"] == "fallback"),
        "partial_coverage_count": sum(
            1 for entry in datasets if entry["coverage_status"] == "partial"
        ),
        "degraded_count": sum(1 for entry in datasets if entry["degradation_status"] == "degraded"),
        "datasets": datasets,
    }


def write_drift_report_json(report):
    output_path = os.path.join(NORMALIZED_DIR, "drift_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path


def build_overview(hub_health, hub_bundle, artifact_manifest):
    primary_package = next(
        (
            package
            for package in artifact_manifest.get("packages", [])
            if package.get("package_type") == "zip"
        ),
        None,
    )
    return {
        "generated_at_utc": hub_health.get("generated_at_utc"),
        "overall_status": hub_health.get("overall_status"),
        "dataset_count": hub_health.get("dataset_count"),
        "live_count": hub_health.get("live_count"),
        "fallback_count": hub_health.get("fallback_count"),
        "stale_count": hub_health.get("stale_count"),
        "drifted_count": hub_health.get("drifted_count"),
        "degraded_count": hub_health.get("degraded_count"),
        "partial_coverage_count": hub_health.get("partial_coverage_count"),
        "warning_count": hub_health.get("warning_count"),
        "top_issue": hub_health.get("top_issue"),
        "top_issue_summary": hub_health.get("top_issue_summary"),
        "shared_artifact_count": len(
            [entry for entry in artifact_manifest.get("artifacts", []) if entry.get("shared_type")]
        ),
        "package_count": len(artifact_manifest.get("packages", [])),
        "primary_package": (
            {
                "path": primary_package.get("path"),
                "package_type": primary_package.get("package_type"),
                "size_bytes": primary_package.get("size_bytes"),
                "checksum_algorithm": primary_package.get("checksum_algorithm"),
                "checksum_path": primary_package.get("checksum_path"),
                "verification_command": primary_package.get("verification_command"),
            }
            if primary_package
            else None
        ),
        "report_keys": sorted(hub_bundle.get("reports", {}).keys()),
        "datasets": [
            {
                "dataset": entry.get("dataset"),
                "source_mode": entry.get("source_mode"),
                "validation_status": entry.get("validation_status"),
                "freshness_status": entry.get("freshness_status"),
                "coverage_status": entry.get("coverage_status"),
                "drift_status": entry.get("drift_status"),
            }
            for entry in hub_health.get("datasets", [])
        ],
    }


def write_overview_json(overview):
    output_path = os.path.join(NORMALIZED_DIR, "overview.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(overview, f, ensure_ascii=False, indent=2)
    return output_path


def write_hub_bundle_json(pipeline_metadata, hub_health, dataset_catalog, artifact_manifest):
    artifacts_by_dataset = {}
    shared_artifacts = []

    for artifact in artifact_manifest.get("artifacts", []):
        dataset_name = artifact.get("dataset")
        if dataset_name:
            artifacts_by_dataset.setdefault(dataset_name, []).append(artifact)
        else:
            shared_artifacts.append(artifact)

    shared_artifacts_by_semantic_key = {}
    for artifact in shared_artifacts:
        shared_type = artifact.get("shared_type")
        artifact_format = artifact.get("format")
        if shared_type and artifact_format:
            shared_artifacts_by_semantic_key[f"{shared_type}:{artifact_format}"] = artifact

    report_specs = {
        "status_markdown": ("pipeline_status", "markdown"),
        "health_json": ("hub_health", "json"),
        "health_markdown": ("hub_health", "markdown"),
        "status_json": ("hub_status", "json"),
        "bundle_json": ("hub_bundle", "json"),
        "redistribution_json": ("redistribution_report", "json"),
        "redistribution_markdown": ("redistribution_report", "markdown"),
        "provenance_json": ("provenance_report", "json"),
        "provenance_markdown": ("provenance_report", "markdown"),
        "drift_json": ("drift_report", "json"),
        "drift_markdown": ("drift_report", "markdown"),
        "overview_json": ("overview", "json"),
        "overview_markdown": ("overview", "markdown"),
        "catalog_json": ("dataset_catalog", "json"),
        "catalog_markdown": ("dataset_catalog", "markdown"),
        "manifest_json": ("artifact_manifest", "json"),
    }
    reports = {}
    for report_name, (shared_type, artifact_format) in report_specs.items():
        reports[report_name] = shared_artifacts_by_semantic_key.get(
            f"{shared_type}:{artifact_format}",
            {
                "path": None,
                "shared_type": shared_type,
                "format": artifact_format,
            },
        )

    bundle = {
        "generated_at_utc": pipeline_metadata.get("generated_at_utc"),
        "overall_status": hub_health.get("overall_status"),
        "dataset_count": dataset_catalog.get("dataset_count"),
        "health": {
            "ok_count": hub_health.get("ok_count"),
            "warn_count": hub_health.get("warn_count"),
            "error_count": hub_health.get("error_count"),
            "live_count": hub_health.get("live_count"),
            "fallback_count": hub_health.get("fallback_count"),
            "stale_count": hub_health.get("stale_count"),
            "publishable_count": hub_health.get("publishable_count"),
            "review_terms_count": hub_health.get("review_terms_count"),
            "unknown_reuse_count": hub_health.get("unknown_reuse_count"),
            "degraded_count": hub_health.get("degraded_count"),
            "degradation_warning_count": hub_health.get("degradation_warning_count"),
            "partial_coverage_count": hub_health.get("partial_coverage_count"),
            "unknown_coverage_count": hub_health.get("unknown_coverage_count"),
            "drifted_count": hub_health.get("drifted_count"),
            "warning_count": hub_health.get("warning_count"),
            "top_issue": hub_health.get("top_issue"),
            "top_issue_summary": hub_health.get("top_issue_summary"),
        },
        "top_issue": hub_health.get("top_issue"),
        "top_issue_summary": hub_health.get("top_issue_summary"),
        "datasets": [],
        "reports": reports,
        "shared_artifacts": shared_artifacts,
        "packages": artifact_manifest.get("packages", []),
    }

    health_by_dataset = {entry["dataset"]: entry for entry in hub_health.get("datasets", [])}

    for dataset in dataset_catalog.get("datasets", []):
        dataset_name = dataset["dataset"]
        dataset_health = health_by_dataset.get(dataset_name, {})
        bundle["datasets"].append(
            {
                "dataset": dataset_name,
                "description": dataset.get("description"),
                "source_name": dataset.get("source_name"),
                "source_url": dataset.get("source_url"),
                "source_mode": dataset.get("source_mode"),
                "source_detail": dataset.get("source_detail"),
                "refreshed_at_utc": dataset.get("refreshed_at_utc"),
                "record_count": dataset.get("record_count"),
                "indicator_codes": dataset.get("indicator_codes", []),
                "indicator_delivery": dataset.get("indicator_delivery", {}),
                "join_keys": dataset.get("join_keys", []),
                "confidence_tier": dataset.get("confidence_tier"),
                "reuse_policy": dataset.get("reuse_policy", {}),
                "validation_status": dataset.get("validation_status"),
                "freshness": dataset.get("freshness", {}),
                "coverage": dataset.get("coverage", {}),
                "warning_count": len(dataset.get("warnings", [])),
                "severity": dataset_health.get("severity"),
                "publishability_status": dataset_health.get("publishability_status"),
                "degradation": dataset.get("degradation", {}),
                "drift": dataset.get("drift", {}),
                "documentation": dataset.get("documentation"),
                "outputs": dataset.get("outputs", {}),
                "usage_examples": dataset.get("usage_examples", {}),
                "artifacts": artifacts_by_dataset.get(dataset_name, []),
            }
        )

    output_path = os.path.join(NORMALIZED_DIR, "hub_bundle.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    return output_path


def write_publishable_bundle_zip():
    manifest_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    artifacts = manifest.get("artifacts", [])
    missing = []
    for artifact in artifacts:
        relative_path = artifact["path"]
        absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
        if not os.path.exists(absolute_path):
            missing.append(relative_path)
    if missing:
        summary = ", ".join(missing[:5])
        suffix = " (y mas)" if len(missing) > 5 else ""
        raise SystemExit(
            f"Error: no se puede crear el ZIP; faltan {len(missing)} artefactos: {summary}{suffix}"
        )

    output_path = os.path.join(NORMALIZED_DIR, PUBLISHABLE_BUNDLE_ZIP_NAME)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in artifacts:
            relative_path = artifact["path"]
            absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
            archive.write(absolute_path, arcname=relative_path)

    with zipfile.ZipFile(output_path, "r") as archive:
        bad_file = archive.testzip()
        if bad_file is not None:
            raise SystemExit(f"Error: ZIP corrupto; primer archivo fallido: {bad_file}")
        if len(archive.namelist()) != len(artifacts):
            raise SystemExit(
                f"Error: ZIP incompleto; esperados {len(artifacts)} archivos, "
                f"encontrados {len(archive.namelist())}"
            )
    return output_path


def write_publishable_bundle_sha256(zip_path):
    output_path = os.path.join(NORMALIZED_DIR, PUBLISHABLE_BUNDLE_SHA256_NAME)
    relative_zip_path = f"data/normalized/{os.path.basename(zip_path)}"
    sha256 = compute_sha256(zip_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"{sha256}  {relative_zip_path}\n")
    return output_path


def attach_publishable_package_to_manifest(zip_path, sha256_path):
    manifest_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    relative_path = f"data/normalized/{os.path.basename(zip_path)}"
    checksum_path = f"data/normalized/{os.path.basename(sha256_path)}"
    manifest["packages"] = [
        {
            "path": relative_path,
            "package_type": "zip",
            "size_bytes": os.path.getsize(zip_path),
            "sha256": compute_sha256(zip_path),
            "checksum_algorithm": "sha256",
            "checksum_path": checksum_path,
            "verification_command": f"shasum -a 256 -c {checksum_path}",
        }
    ]

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest_path


def derive_geography_layers(df_comunas):
    df_regiones = (
        df_comunas.select(["codigo_region", "nombre_region"]).unique().sort("codigo_region")
    )
    df_provincias = (
        df_comunas.select(
            ["codigo_region", "nombre_region", "codigo_provincia", "nombre_provincia"]
        )
        .unique()
        .sort(["codigo_region", "codigo_provincia"])
    )
    return df_regiones, df_provincias


def build_duckdb(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    output_path,
):
    print(f"Compilando base de datos DuckDB en: {output_path}")
    # Si la base de datos ya existe, la eliminamos para reconstruirla limpia
    if os.path.exists(output_path):
        os.remove(output_path)

    con = duckdb.connect(output_path)
    try:
        # Registrar los DataFrames de Polars como vistas temporales en DuckDB
        con.register("df_regiones_view", df_regiones)
        con.register("df_provincias_view", df_provincias)
        con.register("df_comunas_view", df_comunas)
        con.register("df_indicadores_view", df_indicadores)
        con.register("df_censo_view", df_censo)
        con.register("df_salud_view", df_salud)
        con.register("df_educacionales_view", df_educacionales)

        # Crear tablas físicas en DuckDB
        con.execute("CREATE TABLE regiones AS SELECT * FROM df_regiones_view")
        con.execute("CREATE TABLE provincias AS SELECT * FROM df_provincias_view")
        con.execute("CREATE TABLE comunas AS SELECT * FROM df_comunas_view")
        con.execute("CREATE TABLE comunas_enriquecidas AS SELECT * FROM df_comunas_view")
        con.execute("CREATE TABLE indicadores AS SELECT * FROM df_indicadores_view")
        con.execute("CREATE TABLE censo_comunal AS SELECT * FROM df_censo_view")
        con.execute("CREATE TABLE establecimientos_salud AS SELECT * FROM df_salud_view")
        con.execute(
            "CREATE TABLE establecimientos_educacionales AS SELECT * FROM df_educacionales_view"
        )

        # Agregar índices básicos para mejorar rendimiento en queries
        con.execute("CREATE UNIQUE INDEX idx_region_code ON regiones (codigo_region)")
        con.execute("CREATE UNIQUE INDEX idx_provincia_code ON provincias (codigo_provincia)")
        con.execute("CREATE UNIQUE INDEX idx_comuna_code ON comunas (codigo_comuna)")
        con.execute("CREATE INDEX idx_indicador_date ON indicadores (fecha, codigo_indicador)")
        con.execute("CREATE UNIQUE INDEX idx_censo_comuna ON censo_comunal (codigo_comuna)")
        con.execute("CREATE INDEX idx_salud_comuna ON establecimientos_salud (codigo_comuna)")
        con.execute("CREATE UNIQUE INDEX idx_educ_rbd ON establecimientos_educacionales (rbd)")
        con.execute(
            "CREATE INDEX idx_educ_comuna ON establecimientos_educacionales (codigo_comuna)"
        )

        print("Tablas e índices creados con éxito en DuckDB.")
    finally:
        con.close()


def build_sqlite(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    output_path,
):
    print(f"Compilando base de datos SQLite en: {output_path}")
    if os.path.exists(output_path):
        os.remove(output_path)

    # Convertimos a Pandas para inserción rápida con to_sql de pandas
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    df_censo_pd = df_censo.to_pandas()
    df_salud_pd = df_salud.to_pandas()
    df_educacionales_pd = df_educacionales.to_pandas()

    # SQLite no maneja Date de forma nativa como tipo fecha real (los guarda como string ISO)
    # Por lo tanto, convertimos las fechas a string ISO antes de guardar
    df_indicadores_pd["fecha"] = df_indicadores_pd["fecha"].astype(str)

    conn = sqlite3.connect(output_path)
    try:
        df_regiones_pd.to_sql("regiones", conn, index=False, if_exists="replace")
        df_provincias_pd.to_sql("provincias", conn, index=False, if_exists="replace")
        df_comunas_pd.to_sql("comunas", conn, index=False, if_exists="replace")
        df_comunas_pd.to_sql("comunas_enriquecidas", conn, index=False, if_exists="replace")
        df_indicadores_pd.to_sql("indicadores", conn, index=False, if_exists="replace")
        df_censo_pd.to_sql("censo_comunal", conn, index=False, if_exists="replace")
        df_salud_pd.to_sql("establecimientos_salud", conn, index=False, if_exists="replace")
        df_educacionales_pd.to_sql(
            "establecimientos_educacionales", conn, index=False, if_exists="replace"
        )

        # Crear índices en SQLite
        cursor = conn.cursor()
        cursor.execute("CREATE UNIQUE INDEX idx_lite_region ON regiones (codigo_region)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_provincia ON provincias (codigo_provincia)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_comuna ON comunas (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_indicador ON indicadores (fecha, codigo_indicador)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_censo ON censo_comunal (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_salud ON establecimientos_salud (codigo_comuna)")
        cursor.execute(
            "CREATE UNIQUE INDEX idx_lite_educ_rbd ON establecimientos_educacionales (rbd)"
        )
        cursor.execute(
            "CREATE INDEX idx_lite_educ_comuna ON establecimientos_educacionales (codigo_comuna)"
        )
        conn.commit()
        print("Tablas e índices creados con éxito en SQLite.")
    finally:
        conn.close()


def build_excel(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    output_path,
):
    print(f"Generando archivo Excel consolidado para no técnicos en: {output_path}")
    # Convertir a Pandas para exportar de forma robusta con XlsxWriter
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    df_censo_pd = df_censo.to_pandas()
    df_salud_pd = df_salud.to_pandas()
    df_educacionales_pd = df_educacionales.to_pandas()

    # Limpieza visual y formateo para Excel
    # En Excel, queremos que el Código Comuna siga siendo un string para que no se pierdan los ceros iniciales
    # XlsxWriter nos permite definir formatos específicos por columna
    with pd_excel_writer(output_path) as writer:
        df_regiones_pd.to_excel(writer, sheet_name="Regiones", index=False)
        df_provincias_pd.to_excel(writer, sheet_name="Provincias", index=False)
        df_comunas_pd.to_excel(writer, sheet_name="Comunas y Regiones", index=False)
        df_comunas_pd.to_excel(writer, sheet_name="ComunasEnriquecidas", index=False)
        df_indicadores_pd.to_excel(writer, sheet_name="Indicadores Diarios", index=False)
        df_censo_pd.to_excel(writer, sheet_name="Censo Comunal", index=False)
        df_salud_pd.to_excel(writer, sheet_name="Establecimientos Salud", index=False)
        df_educacionales_pd.to_excel(
            writer, sheet_name="Establecimientos Educacionales", index=False
        )

        # Acceder a los objetos workbook y worksheet para aplicar formato estético
        worksheet_regiones = writer.sheets["Regiones"]
        worksheet_provincias = writer.sheets["Provincias"]
        workbook = writer.book
        worksheet_comunas = writer.sheets["Comunas y Regiones"]
        worksheet_indicadores = writer.sheets["Indicadores Diarios"]
        worksheet_censo = writer.sheets["Censo Comunal"]
        worksheet_salud = writer.sheets["Establecimientos Salud"]
        worksheet_educacionales = writer.sheets["Establecimientos Educacionales"]

        # Formato de texto para el código comunal para prevenir pérdida de ceros
        text_format = workbook.add_format({"num_format": "@"})
        worksheet_regiones.set_column("A:A", 12, text_format)
        worksheet_provincias.set_column("A:A", 12, text_format)
        worksheet_provincias.set_column("C:C", 15, text_format)
        worksheet_comunas.set_column("A:A", 12, text_format)  # Código Comuna
        worksheet_comunas.set_column("D:D", 15, text_format)  # Código Provincia
        worksheet_comunas.set_column("F:F", 12, text_format)  # Código Región

        # Ajustar anchos de columnas comunes para que sea estético
        worksheet_comunas.set_column("B:B", 22)  # Nombre Comuna
        worksheet_comunas.set_column("G:G", 25)  # Nombre Región
        worksheet_indicadores.set_column("A:A", 15)  # Fecha
        worksheet_indicadores.set_column("B:B", 18)  # Código Indicador
        worksheet_indicadores.set_column("C:C", 15)  # Valor
        worksheet_censo.set_column("A:A", 12, text_format)
        worksheet_censo.set_column("C:C", 15, text_format)
        worksheet_censo.set_column("E:E", 15, text_format)
        worksheet_salud.set_column("A:A", 20, text_format)
        worksheet_salud.set_column("F:F", 12, text_format)
        worksheet_salud.set_column("H:H", 15, text_format)
        worksheet_educacionales.set_column("A:A", 12, text_format)  # rbd
        worksheet_educacionales.set_column("B:B", 10, text_format)  # dv_rbd
        worksheet_educacionales.set_column("D:D", 12, text_format)  # codigo_region
        worksheet_educacionales.set_column("E:E", 12, text_format)  # codigo_comuna

    print("Archivo Excel multi-pestaña generado con éxito.")


def pd_excel_writer(path):
    import pandas as pd

    return pd.ExcelWriter(path, engine="xlsxwriter")


def build_flat_files(
    df_regiones, df_provincias, df_comunas, df_indicadores, df_censo, df_salud, df_educacionales
):
    import json

    # Generamos archivos Parquet
    regiones_parquet = os.path.join(NORMALIZED_DIR, "regiones.parquet")
    provincias_parquet = os.path.join(NORMALIZED_DIR, "provincias.parquet")
    comunas_parquet = os.path.join(NORMALIZED_DIR, "comunas.parquet")
    comunas_enriquecidas_parquet = os.path.join(NORMALIZED_DIR, "comunas_enriquecidas.parquet")
    indicadores_parquet = os.path.join(NORMALIZED_DIR, "indicadores.parquet")

    df_regiones.write_parquet(regiones_parquet)
    df_provincias.write_parquet(provincias_parquet)
    df_comunas.write_parquet(comunas_parquet)
    df_comunas.write_parquet(comunas_enriquecidas_parquet)
    df_indicadores.write_parquet(indicadores_parquet)
    df_censo.write_parquet(os.path.join(NORMALIZED_DIR, "censo_comunal.parquet"))
    df_salud.write_parquet(os.path.join(NORMALIZED_DIR, "establecimientos_salud.parquet"))
    df_educacionales.write_parquet(
        os.path.join(NORMALIZED_DIR, "establecimientos_educacionales.parquet")
    )
    print(f"Archivos Parquet exportados a: {NORMALIZED_DIR}")

    # Generamos los endpoints JSON simulados
    regiones_json = os.path.join(NORMALIZED_DIR, "regiones.json")
    provincias_json = os.path.join(NORMALIZED_DIR, "provincias.json")
    comunas_json = os.path.join(NORMALIZED_DIR, "comunas.json")
    comunas_enriquecidas_json = os.path.join(NORMALIZED_DIR, "comunas_enriquecidas.json")
    indicadores_json = os.path.join(NORMALIZED_DIR, "indicadores_hoy.json")

    # Para JSON estáticos orientados a frontend, exportamos como lista de diccionarios
    # SQLite/DuckDB maneja fechas como objetos datetime.date, por lo que convertimos a str para serialización JSON
    df_indicadores_serializable = df_indicadores.with_columns(pl.col("fecha").cast(pl.String))

    with open(regiones_json, "w", encoding="utf-8") as f:
        json.dump(df_regiones.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(provincias_json, "w", encoding="utf-8") as f:
        json.dump(df_provincias.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(comunas_json, "w", encoding="utf-8") as f:
        json.dump(df_comunas.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(comunas_enriquecidas_json, "w", encoding="utf-8") as f:
        json.dump(df_comunas.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(indicadores_json, "w", encoding="utf-8") as f:
        json.dump(df_indicadores_serializable.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(os.path.join(NORMALIZED_DIR, "censo_comunal.json"), "w", encoding="utf-8") as f:
        json.dump(df_censo.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(
        os.path.join(NORMALIZED_DIR, "establecimientos_salud.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(df_salud.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(
        os.path.join(NORMALIZED_DIR, "establecimientos_educacionales.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(df_educacionales.to_dicts(), f, ensure_ascii=False, indent=2)

    print(f"Endpoints JSON de prueba exportados a: {NORMALIZED_DIR}")


def main():
    ensure_directories()

    # Rutas de origen (Staging)
    comunas_csv = os.path.join(STAGING_DIR, "comunas.csv")
    indicadores_csv = os.path.join(STAGING_DIR, "indicadores.csv")
    censo_csv = os.path.join(STAGING_DIR, "censo_comunal.csv")
    salud_csv = os.path.join(STAGING_DIR, "establecimientos_salud.csv")
    censo_hogares_csv = os.path.join(STAGING_DIR, "censo_hogares_viviendas.csv")
    electoral_csv = os.path.join(STAGING_DIR, "distritos_electorales.csv")
    educacionales_csv = os.path.join(STAGING_DIR, "establecimientos_educacionales.csv")

    required_staging = (
        comunas_csv,
        indicadores_csv,
        censo_csv,
        salud_csv,
        censo_hogares_csv,
        electoral_csv,
        educacionales_csv,
    )
    if any(not os.path.exists(path) for path in required_staging):
        raise SystemExit(
            "Error: No se encuentran los archivos CSV en staging. Corre los extractores primero."
        )

    comunas_metadata = load_metadata(COMUNAS_METADATA_PATH)
    indicadores_metadata = load_metadata(INDICADORES_METADATA_PATH)
    censo_metadata = load_metadata(CENSO_METADATA_PATH)
    salud_metadata = load_metadata(SALUD_METADATA_PATH)
    censo_hogares_metadata = load_metadata(CENSO_HOGARES_METADATA_PATH)
    electoral_metadata = load_metadata(ELECTORAL_METADATA_PATH)
    educacionales_metadata = load_metadata(
        os.path.join(STAGING_DIR, "establecimientos_educacionales.metadata.json")
    )
    indicadores_metadata["indicator_codes"] = sorted(
        df_code for df_code in indicadores_metadata.get("indicator_codes", [])
    )
    indicadores_metadata["indicator_delivery"] = build_indicator_delivery(indicadores_metadata)

    # Cargar datos desde staging
    # Especificamos explícitamente el tipo de dato de los códigos a String para no perder ceros
    df_comunas = pl.read_csv(
        comunas_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )

    df_indicadores = pl.read_csv(
        indicadores_csv,
        schema_overrides={"codigo_indicador": pl.String, "valor": pl.Float64},
    ).with_columns(pl.col("fecha").str.to_date("%Y-%m-%d"))
    df_censo = pl.read_csv(
        censo_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_salud = pl.read_csv(
        salud_csv,
        schema_overrides={
            "codigo_establecimiento": pl.String,
            "codigo_region": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_censo_hogares = pl.read_csv(
        censo_hogares_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_electoral = pl.read_csv(
        electoral_csv,
        schema_overrides={
            "codigo_comuna": pl.String,
            "distrito_electoral": pl.String,
            "circunscripcion_senatorial": pl.String,
        },
    )
    df_educacionales = pl.read_csv(
        educacionales_csv,
        schema_overrides={
            "rbd": pl.String,
            "dv_rbd": pl.String,
            "codigo_region": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_regiones, df_provincias = derive_geography_layers(df_comunas)

    validations = {
        "regiones": validate_regiones(df_regiones),
        "provincias": validate_provincias(df_provincias),
        "comunas": validate_comunas(df_comunas, comunas_metadata),
        "comunas_enriquecidas": {
            **validate_comunas(df_comunas, comunas_metadata),
            "dataset": "comunas_enriquecidas",
        },
        "indicadores": validate_indicadores(df_indicadores, indicadores_metadata),
        "censo_comunal": validate_censo_comunal(df_censo, censo_metadata),
        "establecimientos_salud": validate_establecimientos_salud(
            df_salud, salud_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "censo_hogares_viviendas": validate_censo_hogares_viviendas(
            df_censo_hogares, censo_hogares_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "distritos_electorales": validate_distritos_electorales(
            df_electoral, electoral_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "establecimientos_educacionales": validate_establecimientos_educacionales(
            df_educacionales, educacionales_metadata, df_comunas["codigo_comuna"].to_list()
        ),
    }

    failed_validations = [
        result["dataset"] for result in validations.values() if result["status"] == "error"
    ]
    if failed_validations:
        messages = [f"Validaciones fallidas para {', '.join(failed_validations)}."]
        for result in validations.values():
            for error in result["errors"]:
                messages.append(f" - {result['dataset']}: {error}")
        raise SystemExit("\n".join(messages))

    # Compilar entregables
    build_duckdb(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        os.path.join(NORMALIZED_DIR, "chile_data.duckdb"),
    )
    build_sqlite(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        os.path.join(NORMALIZED_DIR, "chile_data.db"),
    )
    build_excel(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        os.path.join(NORMALIZED_DIR, "chile_data_latest.xlsx"),
    )
    build_flat_files(
        df_regiones, df_provincias, df_comunas, df_indicadores, df_censo, df_salud, df_educacionales
    )
    df_censo_hogares.write_parquet(os.path.join(NORMALIZED_DIR, "censo_hogares_viviendas.parquet"))
    with open(
        os.path.join(NORMALIZED_DIR, "censo_hogares_viviendas.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(df_censo_hogares.to_dicts(), f, ensure_ascii=False, indent=2)

    df_electoral.write_parquet(os.path.join(NORMALIZED_DIR, "distritos_electorales.parquet"))
    with open(
        os.path.join(NORMALIZED_DIR, "distritos_electorales.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(df_electoral.to_dicts(), f, ensure_ascii=False, indent=2)

    dataset_metadata = {
        "regiones": {
            **comunas_metadata,
            "dataset": "regiones",
            "record_count": df_regiones.height,
            "fields": df_regiones.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["regiones"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["regiones"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "provincias": {
            **comunas_metadata,
            "dataset": "provincias",
            "record_count": df_provincias.height,
            "fields": df_provincias.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["provincias"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["provincias"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "comunas": {
            **comunas_metadata,
            "dataset": "comunas",
            "record_count": df_comunas.height,
            "fields": df_comunas.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["comunas"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["comunas"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "comunas_enriquecidas": {
            **comunas_metadata,
            "dataset": "comunas_enriquecidas",
            "record_count": df_comunas.height,
            "fields": df_comunas.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "indicadores": {
            **indicadores_metadata,
            "dataset": "indicadores",
            "record_count": df_indicadores.height,
            "fields": df_indicadores.columns,
            "indicator_codes": sorted(df_indicadores["codigo_indicador"].unique().to_list()),
            "indicator_delivery": build_indicator_delivery(
                {
                    **indicadores_metadata,
                    "indicator_codes": sorted(
                        df_indicadores["codigo_indicador"].unique().to_list()
                    ),
                }
            ),
            "reuse_policy": DATASET_CATALOG_CONFIG["indicadores"]["reuse_policy"],
            "freshness": build_freshness(
                indicadores_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["indicadores"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "censo_comunal": {
            **censo_metadata,
            "dataset": "censo_comunal",
            "record_count": df_censo.height,
            "fields": df_censo.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["censo_comunal"]["reuse_policy"],
            "freshness": build_freshness(
                censo_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["censo_comunal"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "establecimientos_salud": {
            **salud_metadata,
            "dataset": "establecimientos_salud",
            "record_count": df_salud.height,
            "fields": df_salud.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["establecimientos_salud"]["reuse_policy"],
            "freshness": build_freshness(
                salud_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["establecimientos_salud"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "establecimientos_educacionales": {
            **educacionales_metadata,
            "dataset": "establecimientos_educacionales",
            "record_count": df_educacionales.height,
            "fields": df_educacionales.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["establecimientos_educacionales"][
                "reuse_policy"
            ],
            "freshness": build_freshness(
                educacionales_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["establecimientos_educacionales"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "censo_hogares_viviendas": {
            **censo_hogares_metadata,
            "record_count": df_censo_hogares.height,
            "fields": df_censo_hogares.columns,
            "freshness": build_freshness(
                censo_hogares_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["censo_hogares_viviendas"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "distritos_electorales": {
            **electoral_metadata,
            "record_count": df_electoral.height,
            "fields": df_electoral.columns,
            "freshness": build_freshness(
                electoral_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["distritos_electorales"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
    }
    validations_with_freshness = {
        dataset_name: {
            **validation,
            "warnings": validation.get("warnings", [])
            + build_freshness_warnings(dataset_name, dataset_metadata[dataset_name]["freshness"]),
            "freshness_status": dataset_metadata[dataset_name]["freshness"]["status"],
            "freshness_age_hours": dataset_metadata[dataset_name]["freshness"]["age_hours"],
        }
        for dataset_name, validation in validations.items()
    }
    dataset_metadata = enrich_dataset_metadata(dataset_metadata, validations_with_freshness)
    metadata_output = write_pipeline_metadata(
        dataset_metadata,
        validations_with_freshness,
    )
    with open(metadata_output, encoding="utf-8") as f:
        pipeline_metadata = json.load(f)
    write_status_markdown_file(pipeline_metadata)
    hub_health = build_hub_health(pipeline_metadata)
    hub_health_output = write_hub_health_json(hub_health)
    hub_status = build_hub_status(hub_health)
    hub_status_output = write_hub_status_json(hub_status)
    write_hub_health_markdown_file(hub_health)
    catalog_output = write_dataset_catalog(pipeline_metadata)
    with open(catalog_output, encoding="utf-8") as f:
        dataset_catalog = json.load(f)
    write_dataset_catalog_markdown_file(dataset_catalog)
    redistribution_report = build_redistribution_report(dataset_catalog)
    redistribution_report_output = write_redistribution_report_json(redistribution_report)
    write_redistribution_report_markdown_file(redistribution_report)
    provenance_report = build_provenance_report(dataset_catalog)
    provenance_report_output = write_provenance_report_json(provenance_report)
    write_provenance_report_markdown_file(provenance_report)
    drift_report = build_drift_report(dataset_catalog)
    drift_report_output = write_drift_report_json(drift_report)
    write_drift_report_markdown_file(drift_report)
    artifact_manifest_output = write_artifact_manifest()
    with open(artifact_manifest_output, encoding="utf-8") as f:
        artifact_manifest = json.load(f)
    hub_bundle_output = write_hub_bundle_json(
        pipeline_metadata,
        hub_health,
        dataset_catalog,
        artifact_manifest,
    )
    with open(hub_bundle_output, encoding="utf-8") as f:
        hub_bundle = json.load(f)
    overview = build_overview(hub_health, hub_bundle, artifact_manifest)
    overview_output = write_overview_json(overview)
    write_overview_markdown_file(overview)
    artifact_manifest_output = write_artifact_manifest()
    zip_output = write_publishable_bundle_zip()
    sha256_output = write_publishable_bundle_sha256(zip_output)
    artifact_manifest_output = attach_publishable_package_to_manifest(zip_output, sha256_output)
    with open(artifact_manifest_output, encoding="utf-8") as f:
        artifact_manifest = json.load(f)
    hub_bundle_output = write_hub_bundle_json(
        pipeline_metadata,
        hub_health,
        dataset_catalog,
        artifact_manifest,
    )
    with open(hub_bundle_output, encoding="utf-8") as f:
        hub_bundle = json.load(f)
    overview = build_overview(hub_health, hub_bundle, artifact_manifest)
    overview_output = write_overview_json(overview)
    write_overview_markdown_file(overview)
    print(f"Metadata y validaciones exportadas a: {metadata_output}")
    print(f"Resumen de salud exportado a: {hub_health_output}")
    print(f"Status compacto exportado a: {hub_status_output}")
    print(f"Catalogo de datasets exportado a: {catalog_output}")
    print(f"Reporte de redistribucion exportado a: {redistribution_report_output}")
    print(f"Reporte de procedencia exportado a: {provenance_report_output}")
    print(f"Reporte de drift exportado a: {drift_report_output}")
    print(f"Overview exportado a: {overview_output}")
    print(f"Manifest de artefactos exportado a: {artifact_manifest_output}")
    print(f"Bundle publicable exportado a: {hub_bundle_output}")
    print(f"ZIP publicable exportado a: {zip_output}")
    print(f"SHA256 publicable exportado a: {sha256_output}")

    print("\n--- Compilación del Sprint 0 completada con éxito ---")


if __name__ == "__main__":
    main()
