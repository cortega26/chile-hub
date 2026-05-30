import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STAGING_DIR = ROOT_DIR / "data" / "staging"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"

REQUIRED_FILES = [
    STAGING_DIR / "comunas.csv",
    STAGING_DIR / "indicadores.csv",
    STAGING_DIR / "comunas.metadata.json",
    STAGING_DIR / "indicadores.metadata.json",
    NORMALIZED_DIR / "chile_data.duckdb",
    NORMALIZED_DIR / "chile_data.db",
    NORMALIZED_DIR / "chile_data_latest.xlsx",
    NORMALIZED_DIR / "regiones.parquet",
    NORMALIZED_DIR / "provincias.parquet",
    NORMALIZED_DIR / "comunas.parquet",
    NORMALIZED_DIR / "indicadores.parquet",
    NORMALIZED_DIR / "regiones.json",
    NORMALIZED_DIR / "provincias.json",
    NORMALIZED_DIR / "comunas.json",
    NORMALIZED_DIR / "indicadores_hoy.json",
    NORMALIZED_DIR / "pipeline_metadata.json",
    NORMALIZED_DIR / "pipeline_status.md",
    NORMALIZED_DIR / "dataset_catalog.json",
    NORMALIZED_DIR / "dataset_catalog.md",
    NORMALIZED_DIR / "artifact_manifest.json",
]

REQUIRED_DATASETS = {"regiones", "provincias", "comunas", "indicadores"}


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_required_files():
    missing = [str(path.relative_to(ROOT_DIR)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"Missing required files: {', '.join(missing)}")


def verify_pipeline_metadata():
    metadata_path = NORMALIZED_DIR / "pipeline_metadata.json"
    metadata = load_json(metadata_path)

    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})
    missing_datasets = sorted(REQUIRED_DATASETS - set(datasets.keys()))
    missing_validations = sorted(REQUIRED_DATASETS - set(validations.keys()))

    if missing_datasets:
        fail(f"pipeline_metadata.json is missing dataset entries: {', '.join(missing_datasets)}")

    if missing_validations:
        fail(f"pipeline_metadata.json is missing validation entries: {', '.join(missing_validations)}")

    if not metadata.get("generated_at_utc"):
        fail("pipeline_metadata.json is missing generated_at_utc")

    warning_count = 0
    for dataset_name in sorted(REQUIRED_DATASETS):
        dataset_metadata = datasets[dataset_name]
        validation = validations[dataset_name]

        if dataset_metadata.get("dataset") != dataset_name:
            fail(f"Dataset metadata mismatch for {dataset_name}")

        if validation.get("dataset") != dataset_name:
            fail(f"Validation metadata mismatch for {dataset_name}")

        if not dataset_metadata.get("refreshed_at_utc"):
            fail(f"{dataset_name} metadata is missing refreshed_at_utc")

        if not dataset_metadata.get("fields"):
            fail(f"{dataset_name} metadata is missing fields")

        if dataset_metadata.get("source_mode") not in {"live", "fallback"}:
            fail(f"{dataset_name} metadata has invalid source_mode: {dataset_metadata.get('source_mode')}")

        freshness = dataset_metadata.get("freshness", {})
        if freshness.get("status") not in {"fresh", "stale", "unknown"}:
            fail(f"{dataset_name} metadata has invalid freshness status: {freshness.get('status')}")
        if freshness.get("max_age_hours") is None:
            fail(f"{dataset_name} metadata is missing freshness.max_age_hours")
        if not freshness.get("checked_at_utc"):
            fail(f"{dataset_name} metadata is missing freshness.checked_at_utc")

        if validation.get("status") != "ok":
            fail(f"{dataset_name} validation status is not ok: {validation.get('status')}")

        errors = validation.get("errors", [])
        if errors:
            fail(f"{dataset_name} validation contains errors: {errors}")

        if dataset_metadata.get("record_count") != validation.get("record_count"):
            fail(
                f"{dataset_name} record_count mismatch between datasets and validations: "
                f"{dataset_metadata.get('record_count')} vs {validation.get('record_count')}"
            )

        if validation.get("freshness_status") != freshness.get("status"):
            fail(
                f"{dataset_name} freshness mismatch between datasets and validations: "
                f"{freshness.get('status')} vs {validation.get('freshness_status')}"
            )

        warnings = validation.get("warnings", [])
        if warnings:
            warning_count += len(warnings)
            for warning in warnings:
                print(f"WARNING [{dataset_name}]: {warning}")

        if dataset_name == "indicadores":
            expected_codes = ["dolar", "euro", "ipc", "uf", "utm"]
            if dataset_metadata.get("indicator_codes") != expected_codes:
                fail(
                    "indicadores metadata has unexpected indicator_codes: "
                    f"{dataset_metadata.get('indicator_codes')}"
                )
            if validation.get("indicator_codes") != expected_codes:
                fail(
                    "indicadores validation has unexpected indicator_codes: "
                    f"{validation.get('indicator_codes')}"
                )
        if dataset_name == "regiones" and validation.get("record_count") < 16:
            fail("regiones validation record_count looks too small")
        if dataset_name == "provincias" and validation.get("record_count") < 50:
            fail("provincias validation record_count looks too small")

    print(
        "Verification passed:"
        f" {len(REQUIRED_FILES)} required files found,"
        f" {len(REQUIRED_DATASETS)} datasets validated,"
        f" {warning_count} warnings."
    )


def verify_dataset_catalog():
    catalog_path = NORMALIZED_DIR / "dataset_catalog.json"
    catalog = load_json(catalog_path)

    if catalog.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(
            "dataset_catalog.json has unexpected dataset_count: "
            f"{catalog.get('dataset_count')}"
        )

    datasets = catalog.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"dataset_catalog.json has unexpected datasets: {sorted(dataset_names)}")

    for entry in datasets:
        if not entry.get("outputs"):
            fail(f"{entry.get('dataset')} catalog entry is missing outputs")
        if not entry.get("join_keys"):
            fail(f"{entry.get('dataset')} catalog entry is missing join_keys")
        freshness = entry.get("freshness", {})
        if freshness.get("status") not in {"fresh", "stale", "unknown"}:
            fail(
                f"{entry.get('dataset')} catalog entry has invalid freshness.status: "
                f"{freshness.get('status')}"
            )
        if not entry.get("freshness_policy", {}).get("max_age_hours"):
            fail(f"{entry.get('dataset')} catalog entry is missing freshness_policy.max_age_hours")
        usage_examples = entry.get("usage_examples", {})
        for required_example in ("python", "duckdb", "cli"):
            if not usage_examples.get(required_example):
                fail(
                    f"{entry.get('dataset')} catalog entry is missing usage_examples.{required_example}"
                )
        if entry.get("validation_status") != "ok":
            fail(
                f"{entry.get('dataset')} catalog entry has invalid validation_status: "
                f"{entry.get('validation_status')}"
            )


def verify_artifact_manifest():
    manifest_path = NORMALIZED_DIR / "artifact_manifest.json"
    manifest = load_json(manifest_path)

    artifacts = manifest.get("artifacts", [])
    if manifest.get("artifact_count") != len(artifacts):
        fail(
            "artifact_manifest.json has inconsistent artifact_count: "
            f"{manifest.get('artifact_count')} vs {len(artifacts)}"
        )

    expected_paths = {
        "data/normalized/regiones.parquet",
        "data/normalized/provincias.parquet",
        "data/normalized/comunas.parquet",
        "data/normalized/indicadores.parquet",
        "data/normalized/regiones.json",
        "data/normalized/provincias.json",
        "data/normalized/comunas.json",
        "data/normalized/indicadores_hoy.json",
        "data/normalized/pipeline_metadata.json",
        "data/normalized/pipeline_status.md",
        "data/normalized/dataset_catalog.json",
        "data/normalized/dataset_catalog.md",
    }
    actual_paths = {entry.get("path") for entry in artifacts}
    if expected_paths - actual_paths:
        fail(
            "artifact_manifest.json is missing expected publishable files: "
            f"{sorted(expected_paths - actual_paths)}"
        )

    for entry in artifacts:
        path = entry.get("path")
        if path in expected_paths:
            if path.endswith((".parquet", ".json")) and path not in {
                "data/normalized/pipeline_metadata.json",
                "data/normalized/dataset_catalog.json",
                "data/normalized/artifact_manifest.json",
            }:
                if not entry.get("dataset"):
                    fail(f"artifact manifest entry is missing dataset: {entry}")
            if path.endswith((".parquet", ".json")) and path not in {
                "data/normalized/pipeline_metadata.json",
                "data/normalized/dataset_catalog.json",
                "data/normalized/artifact_manifest.json",
            }:
                if path.endswith(".parquet") and not entry.get("output_type") == "parquet":
                    fail(f"artifact manifest entry has invalid output_type for parquet: {entry}")
        if path in {
            "data/normalized/regiones.json",
            "data/normalized/provincias.json",
            "data/normalized/comunas.json",
            "data/normalized/indicadores_hoy.json",
        } and not entry.get("output_type") == "json":
            fail(f"artifact manifest entry has invalid output_type for json: {entry}")
        if not entry.get("sha256"):
            fail(f"artifact manifest entry is missing sha256: {entry}")
        if entry.get("size_bytes", 0) <= 0:
            fail(f"artifact manifest entry has invalid size_bytes: {entry}")


def main():
    verify_required_files()
    verify_pipeline_metadata()
    verify_dataset_catalog()
    verify_artifact_manifest()


if __name__ == "__main__":
    main()
