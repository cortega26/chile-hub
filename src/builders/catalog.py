"""Escritura del metadata del pipeline y del catálogo de datasets."""

import os
from datetime import datetime

import tomllib

from src.builders._shared import DATASET_CATALOG_CONFIG, NORMALIZED_DIR, ROOT_DIR, UTC
from src.builders.io_utils import write_json_atomic
from src.builders.landing import sync_landing_metadata


def write_pipeline_metadata(dataset_metadata, validations):
    version = "unknown"
    public_site_url = "https://tooltician.com/chile-hub/"
    try:
        pyproject_path = os.path.join(ROOT_DIR, "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        version = pyproject_data.get("project", {}).get("version", "unknown")
        public_site_url = (
            pyproject_data.get("tool", {})
            .get("chile_hub", {})
            .get("public_site_url", public_site_url)
        )
    except Exception as e:
        print(f"Advertencia: No se pudo obtener la versión de pyproject.toml: {e}")

    if version != "unknown":
        sync_landing_metadata(public_site_url)

    pipeline_metadata = {
        "version": version,
        "public_site_url": public_site_url,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "datasets": dataset_metadata,
        "validations": validations,
    }
    output_path = os.path.join(NORMALIZED_DIR, "pipeline_metadata.json")
    write_json_atomic(pipeline_metadata, output_path, ensure_ascii=False, indent=2)
    return output_path, pipeline_metadata


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
                "alias_for": config.get("alias_for"),
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
    write_json_atomic(catalog, output_path, ensure_ascii=False, indent=2)
    return output_path, catalog
