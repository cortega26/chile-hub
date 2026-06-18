import argparse
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

UTC = timezone.utc

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.build_dev_db import DATASET_CATALOG_CONFIG
from src.pipeline_status_utils import load_json

STAGING_DIR = ROOT_DIR / "data" / "staging"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CONTRACTS_DIR = ROOT_DIR / "contracts" / "datasets"
SOURCE_REGISTRY_PATH = ROOT_DIR / "data" / "source_registry.json"


def _derive_dataset_artifact_paths():
    paths = []
    for config in DATASET_CATALOG_CONFIG.values():
        for output_type, relative_path in config.get("outputs", {}).items():
            if output_type in {"parquet", "json"}:
                paths.append(ROOT_DIR / relative_path)
    return paths


_SHARED_FILES = [
    STAGING_DIR / "comunas.csv",
    STAGING_DIR / "indicadores.csv",
    STAGING_DIR / "censo_comunal.csv",
    STAGING_DIR / "establecimientos_salud.csv",
    STAGING_DIR / "establecimientos_educacionales.csv",
    STAGING_DIR / "censo_hogares_viviendas.csv",
    STAGING_DIR / "distritos_electorales.csv",
    STAGING_DIR / "finanzas_municipales.csv",
    STAGING_DIR / "resultados_educacionales.csv",
    STAGING_DIR / "indicadores_urbanos_siedu.csv",
    STAGING_DIR / "comunas.metadata.json",
    STAGING_DIR / "indicadores.metadata.json",
    STAGING_DIR / "censo_comunal.metadata.json",
    STAGING_DIR / "establecimientos_salud.metadata.json",
    STAGING_DIR / "establecimientos_educacionales.metadata.json",
    STAGING_DIR / "censo_hogares_viviendas.metadata.json",
    STAGING_DIR / "distritos_electorales.metadata.json",
    STAGING_DIR / "finanzas_municipales.metadata.json",
    STAGING_DIR / "resultados_educacionales.metadata.json",
    STAGING_DIR / "indicadores_urbanos_siedu.metadata.json",
    NORMALIZED_DIR / "chile_data.duckdb",
    NORMALIZED_DIR / "chile_data.db",
    NORMALIZED_DIR / "chile_data_latest.xlsx",
    NORMALIZED_DIR / "pipeline_metadata.json",
    NORMALIZED_DIR / "pipeline_status.md",
    NORMALIZED_DIR / "hub_health.json",
    NORMALIZED_DIR / "hub_health.md",
    NORMALIZED_DIR / "hub_status.json",
    NORMALIZED_DIR / "dataset_status.json",
    NORMALIZED_DIR / "dataset_changelog.json",
    NORMALIZED_DIR / "hub_bundle.json",
    NORMALIZED_DIR / "redistribution_report.json",
    NORMALIZED_DIR / "redistribution_report.md",
    NORMALIZED_DIR / "provenance_report.json",
    NORMALIZED_DIR / "provenance_report.md",
    NORMALIZED_DIR / "drift_report.json",
    NORMALIZED_DIR / "drift_report.md",
    NORMALIZED_DIR / "overview.json",
    NORMALIZED_DIR / "overview.md",
    NORMALIZED_DIR / "dataset_catalog.json",
    NORMALIZED_DIR / "dataset_catalog.md",
    NORMALIZED_DIR / "artifact_manifest.json",
    NORMALIZED_DIR / "source_readiness.json",
    NORMALIZED_DIR / "source_readiness.md",
    NORMALIZED_DIR / "dataset_quality.json",
    NORMALIZED_DIR / "dataset_quality.md",
    NORMALIZED_DIR / "chile-hub-publishable-bundle.zip",
    NORMALIZED_DIR / "chile-hub-publishable-bundle.zip.sha256",
]

REQUIRED_FILES = _SHARED_FILES + _derive_dataset_artifact_paths()
REQUIRED_DATASETS = set(DATASET_CATALOG_CONFIG)


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


def _contract_type(dtype) -> str:
    dtype_name = str(dtype)
    if dtype_name == "String":
        return "string"
    if dtype_name in {"Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"}:
        return "integer"
    if dtype_name in {"Float32", "Float64"}:
        return "float"
    if dtype_name == "Date":
        return "date"
    if dtype_name == "Boolean":
        return "boolean"
    return dtype_name.lower()


def verify_dataset_contract(dataset_name, contract, df, outputs, root_dir=ROOT_DIR):
    if contract.get("dataset") != dataset_name:
        fail(f"{dataset_name} contract has mismatched dataset: {contract.get('dataset')}")

    required_columns = contract.get("required_columns", [])
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        fail(f"{dataset_name} is missing required columns: {', '.join(missing_columns)}")

    for column, expected_type in contract.get("column_types", {}).items():
        if column not in df.schema:
            fail(f"{dataset_name} contract type column is missing from data: {column}")
        actual_type = _contract_type(df.schema[column])
        if actual_type != expected_type:
            fail(f"{dataset_name}.{column} has type {actual_type}; expected {expected_type}")

    primary_key = contract.get("primary_key", [])
    if primary_key:
        missing_key_columns = [column for column in primary_key if column not in df.columns]
        if missing_key_columns:
            fail(
                f"{dataset_name} primary key columns are missing: {', '.join(missing_key_columns)}"
            )
        if df.select(primary_key).n_unique() != df.height:
            fail(f"{dataset_name} primary key is not unique: {', '.join(primary_key)}")

    for column, width in contract.get("fixed_width_columns", {}).items():
        if column not in df.schema:
            fail(f"{dataset_name} fixed-width column is missing: {column}")
        if _contract_type(df.schema[column]) != "string":
            fail(f"{dataset_name}.{column} must be string for fixed-width validation")
        invalid_count = df.filter(
            pl.col(column).is_null() | (pl.col(column).str.len_chars() != width)
        ).height
        if invalid_count:
            fail(f"{dataset_name}.{column} has {invalid_count} values outside width {width}")

    coverage_policy = contract.get("coverage_policy")
    expected_record_count = contract.get("expected_record_count")
    if coverage_policy == "full" and expected_record_count is not None:
        if df.height != expected_record_count:
            fail(f"{dataset_name} has {df.height} records; expected {expected_record_count}")

    for output_type in contract.get("publish_outputs", []):
        relative_path = outputs.get(output_type)
        if not relative_path:
            fail(f"{dataset_name} contract expects missing catalog output: {output_type}")
        output_path = root_dir / relative_path
        if not output_path.exists():
            fail(f"{dataset_name} contract output does not exist: {relative_path}")


def verify_schema_contracts():
    catalog = load_json(NORMALIZED_DIR / "dataset_catalog.json")
    for entry in catalog.get("datasets", []):
        dataset_name = entry.get("dataset")
        contract_path = CONTRACTS_DIR / f"{dataset_name}.schema.json"
        if not contract_path.exists():
            fail(f"Missing schema contract for dataset: {dataset_name}")
        contract = load_json(contract_path)
        parquet_output = entry.get("outputs", {}).get("parquet")
        if not parquet_output:
            fail(f"{dataset_name} catalog entry is missing parquet output")
        df = pl.read_parquet(ROOT_DIR / parquet_output)
        verify_dataset_contract(dataset_name, contract, df, entry.get("outputs", {}), ROOT_DIR)


def verify_source_registry(registry=None, catalog=None):
    if registry is None:
        registry = load_json(SOURCE_REGISTRY_PATH)
    if catalog is None:
        catalog = load_json(NORMALIZED_DIR / "dataset_catalog.json")

    if not isinstance(registry, list):
        fail("source_registry.json must be a list")

    catalog_names = {entry.get("dataset") for entry in catalog.get("datasets", [])}
    registry_names = [entry.get("dataset") for entry in registry]
    duplicate_names = sorted({name for name in registry_names if registry_names.count(name) > 1})
    if duplicate_names:
        fail(f"source_registry.json has duplicate datasets: {', '.join(duplicate_names)}")

    missing_registry = sorted(catalog_names - set(registry_names))
    if missing_registry:
        fail(f"source_registry.json is missing catalog datasets: {', '.join(missing_registry)}")

    valid_access_methods = {"api", "direct_file", "landing_snapshot", "derived"}
    valid_license_statuses = {"open-attribution", "public-api-review-terms", "restricted"}
    valid_live_statuses = {"implemented", "fallback_only", "derived"}
    valid_fallback_policies = {
        "none",
        "allowed_for_dev",
        "allowed_for_dev_blocked_for_publication",
    }
    valid_maturity_statuses = {"stable", "candidate", "experimental", "deprecated"}

    for entry in registry:
        dataset_name = entry.get("dataset")
        if dataset_name not in DATASET_CATALOG_CONFIG:
            fail(f"source_registry.json references unknown dataset: {dataset_name}")
        config = DATASET_CATALOG_CONFIG[dataset_name]
        expected_license = config.get("reuse_policy", {}).get("status")
        if entry.get("license_status") != expected_license:
            fail(
                f"{dataset_name} registry license_status={entry.get('license_status')} "
                f"does not match catalog config {expected_license}"
            )
        if entry.get("access_method") not in valid_access_methods:
            fail(f"{dataset_name} has invalid access_method: {entry.get('access_method')}")
        if entry.get("license_status") not in valid_license_statuses:
            fail(f"{dataset_name} has invalid license_status: {entry.get('license_status')}")
        if entry.get("live_extractor_status") not in valid_live_statuses:
            fail(
                f"{dataset_name} has invalid live_extractor_status: "
                f"{entry.get('live_extractor_status')}"
            )
        if entry.get("fallback_policy") not in valid_fallback_policies:
            fail(f"{dataset_name} has invalid fallback_policy: {entry.get('fallback_policy')}")
        if entry.get("maturity_status") not in valid_maturity_statuses:
            fail(f"{dataset_name} has invalid maturity_status: {entry.get('maturity_status')}")
        if entry.get("live_extractor_status") == "fallback_only":
            if entry.get("live_ready") is not False:
                fail(f"{dataset_name} fallback_only registry entry must set live_ready=false")
            if entry.get("publish_blocking") is not True:
                fail(f"{dataset_name} fallback_only registry entry must set publish_blocking=true")
        if (
            entry.get("live_extractor_status") == "derived"
            and entry.get("access_method") != "derived"
        ):
            fail(f"{dataset_name} derived registry entry must set access_method=derived")
        review_by = entry.get("review_by")
        if review_by is not None:
            try:
                datetime.fromisoformat(str(review_by))
            except (ValueError, TypeError):
                fail(f"{dataset_name} has invalid review_by date: {review_by}")
        stalled_after = entry.get("stalled_after_days")
        if stalled_after is not None and (not isinstance(stalled_after, int) or stalled_after < 1):
            fail(f"{dataset_name} has invalid stalled_after_days: {stalled_after}")


def _verify_stagnation(report=None, reference_date=None):
    """Verifica reglas de estancamiento según maturity_status.

    Reglas:
    - experimental: estancamiento emite warning (no falla)
    - candidate: estancamiento hace fallar verify-readiness
    - stable: regresión en madurez de fuente hace fallar verify-readiness
    - derivados: pueden marcarse estancados solo por bloqueadores upstream
    """
    if report is None:
        report = load_json(NORMALIZED_DIR / "source_readiness.json")
    if reference_date is None:
        reference_date = datetime.now(UTC)

    warnings = []
    failures = []

    for entry in report.get("datasets", []):
        dataset = entry["dataset"]
        maturity = entry.get("maturity_status", "unknown")
        access_method = entry.get("access_method", "")
        review_by = entry.get("review_by")
        stalled_after_days = entry.get("stalled_after_days", 90)

        # Determinar estancamiento contra la fecha de referencia
        stalled = False
        if review_by:
            try:
                review_date = datetime.fromisoformat(str(review_by))
                if review_date.tzinfo is None:
                    review_date = review_date.replace(tzinfo=UTC)
                stalled = reference_date > review_date
            except (ValueError, TypeError):
                pass

        if not stalled:
            continue

        # Datasets derivados: advertir en lugar de fallar (dependen de upstream)
        if access_method == "derived" and maturity != "deprecated":
            warnings.append(
                f"{dataset}: estancado (derivado) — revisar fuentes upstream. "
                f"Revisión vencida: {review_by}"
            )
            continue

        if maturity == "experimental":
            warnings.append(
                f"{dataset}: estancado (experimental, {stalled_after_days}d) — "
                f"revisión vencida {review_by}"
            )
        elif maturity == "candidate":
            failures.append(
                f"{dataset}: estancado (candidate, {stalled_after_days}d) — "
                f"revisión vencida {review_by}. Requiere acción."
            )
        elif maturity == "stable":
            failures.append(
                f"{dataset}: regresión en madurez estable — "
                f"revisión vencida {review_by}. Investigar degradación de fuente."
            )
        elif maturity == "deprecated":
            warnings.append(
                f"{dataset}: estancado y deprecado — considerar eliminación del registry"
            )

    for w in warnings:
        print(f"WARNING [stagnation]: {w}")

    if failures:
        fail("Stagnation policy rejected this build: " + "; ".join(failures))


def verify_staging_not_newer_than_normalized():
    """
    Detect the common mistake of running an extractor (which updates
    data/staging/*.metadata.json) without re-running build_dev_db.py
    (which would update data/normalized/pipeline_metadata.json).

    If any staging metadata is newer than the normalized sentinel, the
    tests will fail with cryptic assertion errors instead of the real
    cause.  Fail loudly here so the fix is obvious.
    """
    sentinel = NORMALIZED_DIR / "pipeline_metadata.json"
    if not sentinel.exists():
        fail(
            "data/normalized/pipeline_metadata.json not found. "
            "Run 'python src/build_dev_db.py' (or 'make build') before verifying."
        )
    sentinel_mtime = sentinel.stat().st_mtime
    stale = [
        p
        for p in STAGING_DIR.glob("*.metadata.json")
        if p.stat().st_mtime > sentinel_mtime + 1  # 1-second grace
    ]
    if stale:
        names = ", ".join(sorted(p.name for p in stale))
        fail(
            f"Staging metadata is newer than normalized artifacts: [{names}]. "
            "Run 'python src/build_dev_db.py' (or 'make build') to rebuild before verifying."
        )


def verify_publication_policy(metadata=None):
    if metadata is None:
        metadata = load_json(NORMALIZED_DIR / "pipeline_metadata.json")

    violations = []
    for dataset_name in sorted(REQUIRED_DATASETS):
        dataset = metadata.get("datasets", {}).get(dataset_name, {})
        freshness = dataset.get("freshness", {})
        if dataset.get("source_mode") != "live":
            violations.append(f"{dataset_name}: source_mode={dataset.get('source_mode')}")
        if freshness.get("status") != "fresh":
            violations.append(f"{dataset_name}: freshness={freshness.get('status')}")

    indicadores = metadata.get("datasets", {}).get("indicadores", {})
    allowed_indicator_source_details = {
        "public_api",
        "public_api_with_published_backfill",
    }
    if indicadores.get("source_detail") not in allowed_indicator_source_details:
        violations.append(f"indicadores: source_detail={indicadores.get('source_detail')}")
    failed_diagnostics = {
        field: indicadores.get(field, [])
        for field in (
            "fetch_failures",
            "raw_recoveries",
            "preserved_existing_pairs",
            "empty_live_pairs",
        )
        if indicadores.get(field)
    }
    if failed_diagnostics:
        violations.append(f"indicadores: recovery diagnostics={failed_diagnostics}")
    unsafe_delivery = {
        code: status
        for code, status in indicadores.get("indicator_delivery", {}).items()
        if status not in {"live", "published_backfill"}
    }
    if unsafe_delivery:
        violations.append(f"indicadores: unsafe delivery={unsafe_delivery}")

    if violations:
        fail("Publication policy rejected this build: " + "; ".join(violations))

    print("Publication policy passed: all datasets are fresh and publication-safe.")


def verify_indicadores_diagnostics(dataset_metadata, validation, origin):
    source_detail = dataset_metadata.get("source_detail")
    allowed_source_details = {
        "public_api",
        "public_api_with_raw_recovery",
        "public_api_with_raw_recovery_partial",
        "public_api_partial",
        "public_api_with_published_backfill",
        "generated_fallback",
    }
    if source_detail not in allowed_source_details:
        fail(f"{origin} has invalid indicadores source_detail: {source_detail}")

    notes = dataset_metadata.get("notes", [])
    warnings = validation.get("warnings", [])
    fetch_failures = dataset_metadata.get("fetch_failures", [])
    raw_recoveries = dataset_metadata.get("raw_recoveries", [])
    preserved_existing_pairs = dataset_metadata.get("preserved_existing_pairs", [])
    empty_live_pairs = dataset_metadata.get("empty_live_pairs", [])
    published_backfills = dataset_metadata.get("published_backfills", [])

    if source_detail == "generated_fallback":
        if dataset_metadata.get("source_mode") != "fallback":
            fail(f"{origin} fallback source_detail must use source_mode=fallback")
        return

    if dataset_metadata.get("source_mode") != "live":
        fail(f"{origin} live indicadores diagnostics require source_mode=live")

    if raw_recoveries:
        if source_detail not in {
            "public_api_with_raw_recovery",
            "public_api_with_raw_recovery_partial",
            "public_api_with_published_backfill",
        }:
            fail(f"{origin} raw_recoveries require a recovery-aware source_detail")
        expected_note = "raw_recovery_used_for_pairs: " + ", ".join(raw_recoveries)
        if expected_note not in notes:
            fail(f"{origin} is missing raw recovery note: {expected_note}")
        expected_warning = "indicadores live refresh reused raw snapshots for: " + ", ".join(
            raw_recoveries
        )
        if expected_warning not in warnings:
            fail(f"{origin} is missing raw recovery warning: {expected_warning}")

    if preserved_existing_pairs:
        if source_detail not in {
            "public_api_partial",
            "public_api_with_raw_recovery_partial",
            "public_api_with_published_backfill",
        }:
            fail(f"{origin} preserved_existing_pairs require a partial-aware source_detail")
        expected_note = "preserved_existing_pairs_due_to_fetch_failure: " + ", ".join(
            preserved_existing_pairs
        )
        if expected_note not in notes:
            fail(f"{origin} is missing preserved-existing note: {expected_note}")
        expected_warning = (
            "indicadores live refresh preserved previous staging rows for: "
            + ", ".join(preserved_existing_pairs)
        )
        if expected_warning not in warnings:
            fail(f"{origin} is missing preserved-existing warning: {expected_warning}")

    if empty_live_pairs:
        expected_note = "empty_live_pairs: " + ", ".join(empty_live_pairs)
        if expected_note not in notes:
            fail(f"{origin} is missing empty-live note: {expected_note}")
        expected_warning = "indicadores live refresh returned empty series for: " + ", ".join(
            empty_live_pairs
        )
        if expected_warning not in warnings:
            fail(f"{origin} is missing empty-live warning: {expected_warning}")

    if published_backfills:
        if source_detail != "public_api_with_published_backfill":
            fail(
                f"{origin} published_backfills require source_detail=public_api_with_published_backfill"
            )
        expected_note = "published_backfills_used_for_codes: " + ", ".join(published_backfills)
        if expected_note not in notes:
            fail(f"{origin} is missing published-backfill note: {expected_note}")
        expected_warning = (
            "indicadores live refresh reused last published artifact for missing codes: "
            + ", ".join(published_backfills)
        )
        if expected_warning not in warnings:
            fail(f"{origin} is missing published-backfill warning: {expected_warning}")

    if (
        fetch_failures
        and not raw_recoveries
        and not preserved_existing_pairs
        and dataset_metadata.get("source_mode") != "fallback"
    ):
        fail(f"{origin} recorded fetch_failures without any recovery path")


def verify_top_issue(top_issue, origin):
    if not isinstance(top_issue, dict):
        fail(f"{origin} has invalid top_issue payload: {top_issue}")
    if top_issue.get("dataset") not in REQUIRED_DATASETS:
        fail(f"{origin} has invalid top_issue.dataset: {top_issue}")
    if top_issue.get("build_freshness_status") not in {"fresh", "stale", "unknown"}:
        fail(f"{origin} has invalid top_issue.build_freshness_status: {top_issue}")
    if top_issue.get("drift_status") not in {"healthy", "drifted"}:
        fail(f"{origin} has invalid top_issue.drift_status: {top_issue}")
    if top_issue.get("degradation_status") not in {"none", "warning", "degraded"}:
        fail(f"{origin} has invalid top_issue.degradation_status: {top_issue}")
    warning_count = top_issue.get("warning_count")
    if not isinstance(warning_count, int) or warning_count < 0:
        fail(f"{origin} has invalid top_issue.warning_count: {top_issue}")
    if not top_issue.get("source_detail"):
        fail(f"{origin} is missing top_issue.source_detail: {top_issue}")
    if not top_issue.get("diagnostic_summary"):
        fail(f"{origin} is missing top_issue.diagnostic_summary: {top_issue}")
    if not top_issue.get("recommended_action"):
        fail(f"{origin} is missing top_issue.recommended_action: {top_issue}")


def verify_top_issue_summary(summary, top_issue, origin):
    if not isinstance(summary, str) or not summary.strip():
        fail(f"{origin} is missing top_issue_summary")
    dataset = top_issue.get("dataset") if isinstance(top_issue, dict) else None
    if dataset and dataset not in summary:
        fail(f"{origin} top_issue_summary does not mention dataset '{dataset}': {summary}")


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
        fail(
            f"pipeline_metadata.json is missing validation entries: {', '.join(missing_validations)}"
        )

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
            fail(
                f"{dataset_name} metadata has invalid source_mode: {dataset_metadata.get('source_mode')}"
            )

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
        if freshness.get("status") in {"stale", "unknown"} and not warnings:
            fail(
                f"{dataset_name} should expose freshness warning when status is {freshness.get('status')}"
            )
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
            verify_indicadores_diagnostics(dataset_metadata, validation, "pipeline_metadata.json")
        if dataset_name == "regiones":
            if (
                dataset_metadata.get("source_mode") == "live"
                and validation.get("record_count") < 16
            ):
                fail("regiones validation record_count looks too small for live mode")
            if (
                dataset_metadata.get("source_mode") == "fallback"
                and validation.get("record_count") <= 0
            ):
                fail("regiones validation record_count looks empty in fallback mode")
        if dataset_name == "provincias":
            if (
                dataset_metadata.get("source_mode") == "live"
                and validation.get("record_count") < 50
            ):
                fail("provincias validation record_count looks too small for live mode")
            if (
                dataset_metadata.get("source_mode") == "fallback"
                and validation.get("record_count") <= 0
            ):
                fail("provincias validation record_count looks empty in fallback mode")

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
        fail(f"dataset_catalog.json has unexpected dataset_count: {catalog.get('dataset_count')}")

    datasets = catalog.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"dataset_catalog.json has unexpected datasets: {sorted(dataset_names)}")

    for entry in datasets:
        if not entry.get("outputs"):
            fail(f"{entry.get('dataset')} catalog entry is missing outputs")
        if entry.get("dataset") == "indicadores":
            expected_codes = ["dolar", "euro", "ipc", "uf", "utm"]
            if entry.get("indicator_codes") != expected_codes:
                fail(
                    f"indicadores catalog entry has unexpected indicator_codes: {entry.get('indicator_codes')}"
                )
            indicator_delivery = entry.get("indicator_delivery", {})
            if sorted(indicator_delivery.keys()) != expected_codes:
                fail(
                    "indicadores catalog entry has unexpected indicator_delivery keys: "
                    f"{sorted(indicator_delivery.keys())}"
                )
            allowed_delivery_statuses = {
                "live",
                "raw_recovery",
                "preserved_existing",
                "published_backfill",
            }
            invalid_statuses = {
                code: status
                for code, status in indicator_delivery.items()
                if status not in allowed_delivery_statuses
            }
            if invalid_statuses:
                fail(
                    f"indicadores catalog entry has invalid indicator_delivery statuses: {invalid_statuses}"
                )
        if not entry.get("join_keys"):
            fail(f"{entry.get('dataset')} catalog entry is missing join_keys")
        reuse_policy = entry.get("reuse_policy", {})
        if reuse_policy.get("status") not in {
            "open-attribution",
            "public-api-review-terms",
        }:
            fail(
                f"{entry.get('dataset')} catalog entry has invalid reuse_policy.status: "
                f"{reuse_policy.get('status')}"
            )
        if not reuse_policy.get("license"):
            fail(f"{entry.get('dataset')} catalog entry is missing reuse_policy.license")
        if not reuse_policy.get("summary"):
            fail(f"{entry.get('dataset')} catalog entry is missing reuse_policy.summary")
        if reuse_policy.get("attribution_required") not in {True, False}:
            fail(
                f"{entry.get('dataset')} catalog entry has invalid reuse_policy.attribution_required"
            )
        if reuse_policy.get("redistribution_ok") not in {True, False}:
            fail(f"{entry.get('dataset')} catalog entry has invalid reuse_policy.redistribution_ok")
        freshness = entry.get("freshness", {})
        if freshness.get("status") not in {"fresh", "stale", "unknown"}:
            fail(
                f"{entry.get('dataset')} catalog entry has invalid freshness.status: "
                f"{freshness.get('status')}"
            )
        coverage = entry.get("coverage", {})
        if coverage.get("status") not in {
            "full",
            "partial",
            "unknown",
            "not_applicable",
        }:
            fail(f"{entry.get('dataset')} catalog entry has invalid coverage.status")
        if not coverage.get("summary"):
            fail(f"{entry.get('dataset')} catalog entry is missing coverage.summary")
        drift = entry.get("drift", {})
        if drift.get("status") not in {"healthy", "drifted"}:
            fail(f"{entry.get('dataset')} catalog entry has invalid drift.status")
        if not drift.get("summary"):
            fail(f"{entry.get('dataset')} catalog entry is missing drift.summary")
        if not entry.get("freshness_policy", {}).get("max_age_hours"):
            fail(f"{entry.get('dataset')} catalog entry is missing freshness_policy.max_age_hours")
        usage_examples = entry.get("usage_examples", {})
        for required_example in ("python", "duckdb", "cli"):
            if not usage_examples.get(required_example):
                fail(
                    f"{entry.get('dataset')} catalog entry is missing usage_examples.{required_example}"
                )
        degradation = entry.get("degradation", {})
        if degradation.get("status") not in {"none", "warning", "degraded"}:
            fail(f"{entry.get('dataset')} catalog entry has invalid degradation.status")
        if not degradation.get("impact"):
            fail(f"{entry.get('dataset')} catalog entry is missing degradation.impact")
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
        "data/normalized/hub_health.json",
        "data/normalized/hub_health.md",
        "data/normalized/hub_status.json",
        "data/normalized/dataset_status.json",
        "data/normalized/dataset_changelog.json",
        "data/normalized/hub_bundle.json",
        "data/normalized/redistribution_report.json",
        "data/normalized/redistribution_report.md",
        "data/normalized/provenance_report.json",
        "data/normalized/provenance_report.md",
        "data/normalized/drift_report.json",
        "data/normalized/drift_report.md",
        "data/normalized/overview.json",
        "data/normalized/overview.md",
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
                "data/normalized/hub_health.json",
                "data/normalized/hub_status.json",
                "data/normalized/dataset_status.json",
                "data/normalized/dataset_changelog.json",
                "data/normalized/hub_bundle.json",
                "data/normalized/redistribution_report.json",
                "data/normalized/provenance_report.json",
                "data/normalized/drift_report.json",
                "data/normalized/overview.json",
                "data/normalized/dataset_catalog.json",
                "data/normalized/artifact_manifest.json",
            }:
                if not entry.get("dataset"):
                    fail(f"artifact manifest entry is missing dataset: {entry}")
            if path.endswith((".parquet", ".json")) and path not in {
                "data/normalized/pipeline_metadata.json",
                "data/normalized/hub_health.json",
                "data/normalized/hub_status.json",
                "data/normalized/dataset_status.json",
                "data/normalized/dataset_changelog.json",
                "data/normalized/hub_bundle.json",
                "data/normalized/redistribution_report.json",
                "data/normalized/provenance_report.json",
                "data/normalized/drift_report.json",
                "data/normalized/dataset_catalog.json",
                "data/normalized/artifact_manifest.json",
            }:
                if path.endswith(".parquet") and not entry.get("output_type") == "parquet":
                    fail(f"artifact manifest entry has invalid output_type for parquet: {entry}")
        if path in {
            "data/normalized/pipeline_metadata.json",
            "data/normalized/hub_health.json",
            "data/normalized/hub_status.json",
            "data/normalized/dataset_status.json",
            "data/normalized/dataset_changelog.json",
            "data/normalized/hub_bundle.json",
            "data/normalized/redistribution_report.json",
            "data/normalized/provenance_report.json",
            "data/normalized/drift_report.json",
            "data/normalized/overview.json",
            "data/normalized/dataset_catalog.json",
            "data/normalized/artifact_manifest.json",
        }:
            if not entry.get("shared_type"):
                fail(f"artifact manifest shared JSON entry is missing shared_type: {entry}")
            if entry.get("format") != "json":
                fail(f"artifact manifest shared JSON entry has invalid format: {entry}")
        if path in {
            "data/normalized/pipeline_status.md",
            "data/normalized/hub_health.md",
            "data/normalized/redistribution_report.md",
            "data/normalized/provenance_report.md",
            "data/normalized/drift_report.md",
            "data/normalized/overview.md",
            "data/normalized/dataset_catalog.md",
        }:
            if not entry.get("shared_type"):
                fail(f"artifact manifest shared Markdown entry is missing shared_type: {entry}")
            if entry.get("format") != "markdown":
                fail(f"artifact manifest shared Markdown entry has invalid format: {entry}")
        if (
            path
            in {
                "data/normalized/regiones.json",
                "data/normalized/provincias.json",
                "data/normalized/comunas.json",
                "data/normalized/indicadores_hoy.json",
            }
            and not entry.get("output_type") == "json"
        ):
            fail(f"artifact manifest entry has invalid output_type for json: {entry}")
        if not entry.get("sha256"):
            fail(f"artifact manifest entry is missing sha256: {entry}")
        if entry.get("size_bytes", 0) <= 0:
            fail(f"artifact manifest entry has invalid size_bytes: {entry}")

    packages = manifest.get("packages", [])
    if len(packages) != 1:
        fail(f"artifact_manifest.json has unexpected packages count: {len(packages)}")
    package = packages[0]
    if package.get("path") != "data/normalized/chile-hub-publishable-bundle.zip":
        fail(f"artifact_manifest.json has unexpected package path: {package}")
    if package.get("package_type") != "zip":
        fail(f"artifact_manifest.json has invalid package_type: {package}")
    if package.get("checksum_path") != "data/normalized/chile-hub-publishable-bundle.zip.sha256":
        fail(f"artifact_manifest.json has invalid checksum_path: {package}")
    if package.get("checksum_algorithm") != "sha256":
        fail(f"artifact_manifest.json has invalid checksum_algorithm: {package}")
    if (
        package.get("verification_command")
        != "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"
    ):
        fail(f"artifact_manifest.json has invalid verification_command: {package}")
    if not package.get("sha256") or package.get("size_bytes", 0) <= 0:
        fail(f"artifact_manifest.json has invalid package metadata: {package}")


def verify_hub_health():
    health_path = NORMALIZED_DIR / "hub_health.json"
    health = load_json(health_path)

    if health.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"hub_health.json has unexpected dataset_count: {health.get('dataset_count')}")

    if health.get("overall_status") not in {"ok", "warn", "error"}:
        fail(f"hub_health.json has invalid overall_status: {health.get('overall_status')}")
    for key in (
        "publishable_count",
        "review_terms_count",
        "unknown_reuse_count",
        "degraded_count",
        "degradation_warning_count",
        "partial_coverage_count",
        "unknown_coverage_count",
        "drifted_count",
    ):
        if health.get(key) is None:
            fail(f"hub_health.json is missing {key}")

    datasets = health.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"hub_health.json has unexpected datasets: {sorted(dataset_names)}")

    for entry in datasets:
        if entry.get("severity") not in {"ok", "warn", "error"}:
            fail(f"hub_health.json entry has invalid severity: {entry}")
        if entry.get("source_mode") not in {"live", "fallback"}:
            fail(f"hub_health.json entry has invalid source_mode: {entry}")
        if entry.get("freshness_status") not in {"fresh", "stale", "unknown"}:
            fail(f"hub_health.json entry has invalid freshness_status: {entry}")
        if entry.get("validation_status") != "ok":
            fail(f"hub_health.json entry has unexpected validation_status: {entry}")
        if entry.get("publishability_status") not in {
            "ready",
            "review_terms",
            "unknown",
        }:
            fail(f"hub_health.json entry has invalid publishability_status: {entry}")
        if entry.get("degradation_status") not in {"none", "warning", "degraded"}:
            fail(f"hub_health.json entry has invalid degradation_status: {entry}")
        if entry.get("coverage_status") not in {
            "full",
            "partial",
            "unknown",
            "not_applicable",
        }:
            fail(f"hub_health.json entry has invalid coverage_status: {entry}")
        if entry.get("drift_status") not in {"healthy", "drifted"}:
            fail(f"hub_health.json entry has invalid drift_status: {entry}")

    if health.get("warning_count", 0) > 0:
        verify_top_issue(health.get("top_issue"), "hub_health.json")
        verify_top_issue_summary(
            health.get("top_issue_summary"),
            health.get("top_issue"),
            "hub_health.json",
        )
    elif health.get("top_issue") is not None:
        verify_top_issue(health.get("top_issue"), "hub_health.json")
        verify_top_issue_summary(
            health.get("top_issue_summary"),
            health.get("top_issue"),
            "hub_health.json",
        )


def verify_hub_status():
    status_path = NORMALIZED_DIR / "hub_status.json"
    status = load_json(status_path)

    if status.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"hub_status.json has unexpected dataset_count: {status.get('dataset_count')}")
    if status.get("overall_status") not in {"ok", "warn", "error"}:
        fail(f"hub_status.json has invalid overall_status: {status.get('overall_status')}")
    for key in (
        "live_count",
        "fallback_count",
        "stale_count",
        "drifted_count",
        "degraded_count",
        "warning_count",
    ):
        if status.get(key) is None:
            fail(f"hub_status.json is missing {key}")
    if status.get("warning_count", 0) > 0:
        verify_top_issue(status.get("top_issue"), "hub_status.json")
        verify_top_issue_summary(
            status.get("top_issue_summary"),
            status.get("top_issue"),
            "hub_status.json",
        )
    elif status.get("top_issue") is not None:
        verify_top_issue(status.get("top_issue"), "hub_status.json")
        verify_top_issue_summary(
            status.get("top_issue_summary"),
            status.get("top_issue"),
            "hub_status.json",
        )


def verify_hub_bundle():
    bundle_path = NORMALIZED_DIR / "hub_bundle.json"
    bundle = load_json(bundle_path)

    if bundle.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"hub_bundle.json has unexpected dataset_count: {bundle.get('dataset_count')}")
    if bundle.get("overall_status") not in {"ok", "warn", "error"}:
        fail(f"hub_bundle.json has invalid overall_status: {bundle.get('overall_status')}")
    health = bundle.get("health", {})
    if health.get("warning_count") is None:
        fail("hub_bundle.json is missing health.warning_count")
    if health.get("warning_count", 0) > 0:
        verify_top_issue(bundle.get("top_issue"), "hub_bundle.json")
        verify_top_issue(health.get("top_issue"), "hub_bundle.json health")
        verify_top_issue_summary(
            bundle.get("top_issue_summary"),
            bundle.get("top_issue"),
            "hub_bundle.json",
        )
        verify_top_issue_summary(
            health.get("top_issue_summary"),
            health.get("top_issue"),
            "hub_bundle.json health",
        )
    elif bundle.get("top_issue") is not None:
        verify_top_issue(bundle.get("top_issue"), "hub_bundle.json")
        verify_top_issue_summary(
            bundle.get("top_issue_summary"),
            bundle.get("top_issue"),
            "hub_bundle.json",
        )
    elif health.get("top_issue") is not None:
        verify_top_issue(health.get("top_issue"), "hub_bundle.json health")
        verify_top_issue_summary(
            health.get("top_issue_summary"),
            health.get("top_issue"),
            "hub_bundle.json health",
        )

    datasets = bundle.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"hub_bundle.json has unexpected datasets: {sorted(dataset_names)}")
    reports = bundle.get("reports", {})
    expected_reports = {
        "status_markdown": ("pipeline_status", "markdown"),
        "health_json": ("hub_health", "json"),
        "health_markdown": ("hub_health", "markdown"),
        "status_json": ("hub_status", "json"),
        "dataset_status_json": ("dataset_status", "json"),
        "dataset_changelog_json": ("dataset_changelog", "json"),
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
    for report_name, (shared_type, artifact_format) in expected_reports.items():
        report_entry = reports.get(report_name, {})
        if (
            report_entry.get("shared_type") != shared_type
            or report_entry.get("format") != artifact_format
        ):
            fail(f"hub_bundle.json has invalid reports.{report_name}: {report_entry}")
        if not report_entry.get("path"):
            fail(f"hub_bundle.json is missing reports.{report_name}.path: {report_entry}")

    for entry in datasets:
        if not entry.get("artifacts"):
            fail(f"hub_bundle.json dataset entry is missing artifacts: {entry.get('dataset')}")
        if entry.get("severity") not in {"ok", "warn", "error"}:
            fail(f"hub_bundle.json dataset entry has invalid severity: {entry}")
        if entry.get("validation_status") != "ok":
            fail(f"hub_bundle.json dataset entry has unexpected validation_status: {entry}")
        reuse_policy = entry.get("reuse_policy", {})
        if reuse_policy.get("status") not in {
            "open-attribution",
            "public-api-review-terms",
        }:
            fail(f"hub_bundle.json dataset entry has invalid reuse_policy: {entry}")
        if entry.get("publishability_status") not in {
            "ready",
            "review_terms",
            "unknown",
        }:
            fail(f"hub_bundle.json dataset entry has invalid publishability_status: {entry}")
        if entry.get("degradation", {}).get("status") not in {
            "none",
            "warning",
            "degraded",
        }:
            fail(f"hub_bundle.json dataset entry has invalid degradation: {entry}")
        if entry.get("coverage", {}).get("status") not in {
            "full",
            "partial",
            "unknown",
            "not_applicable",
        }:
            fail(f"hub_bundle.json dataset entry has invalid coverage: {entry}")
        if entry.get("drift", {}).get("status") not in {"healthy", "drifted"}:
            fail(f"hub_bundle.json dataset entry has invalid drift: {entry}")
        if not entry.get("source_detail"):
            fail(f"hub_bundle.json dataset entry is missing source_detail: {entry}")
        if not entry.get("refreshed_at_utc"):
            fail(f"hub_bundle.json dataset entry is missing refreshed_at_utc: {entry}")
    packages = bundle.get("packages", [])
    if len(packages) != 1 or packages[0].get("package_type") != "zip":
        fail(f"hub_bundle.json has invalid packages metadata: {packages}")
    if packages[0].get("checksum_algorithm") != "sha256":
        fail(f"hub_bundle.json has invalid package checksum_algorithm: {packages[0]}")
    if (
        packages[0].get("verification_command")
        != "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"
    ):
        fail(f"hub_bundle.json has invalid package verification_command: {packages[0]}")


def verify_redistribution_report():
    report_path = NORMALIZED_DIR / "redistribution_report.json"
    report = load_json(report_path)

    if report.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(
            "redistribution_report.json has unexpected dataset_count: "
            f"{report.get('dataset_count')}"
        )
    datasets = report.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"redistribution_report.json has unexpected datasets: {sorted(dataset_names)}")
    for entry in datasets:
        if entry.get("publishability_status") not in {
            "ready",
            "review_terms",
            "unknown",
        }:
            fail(f"redistribution_report.json has invalid publishability_status: {entry}")
        if not entry.get("license"):
            fail(f"redistribution_report.json is missing license: {entry}")
        if not entry.get("recommended_action"):
            fail(f"redistribution_report.json is missing recommended_action: {entry}")
    if report.get("ready_count") is None or report.get("review_terms_count") is None:
        fail("redistribution_report.json is missing aggregated counts")


def verify_provenance_report():
    report_path = NORMALIZED_DIR / "provenance_report.json"
    report = load_json(report_path)

    if report.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"provenance_report.json has unexpected dataset_count: {report.get('dataset_count')}")
    datasets = report.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"provenance_report.json has unexpected datasets: {sorted(dataset_names)}")
    for entry in datasets:
        if entry.get("source_mode") not in {"live", "fallback"}:
            fail(f"provenance_report.json has invalid source_mode: {entry}")
        if not entry.get("source_name"):
            fail(f"provenance_report.json is missing source_name: {entry}")
        if not entry.get("source_url"):
            fail(f"provenance_report.json is missing source_url: {entry}")
        if not entry.get("refreshed_at_utc"):
            fail(f"provenance_report.json is missing refreshed_at_utc: {entry}")
        if entry.get("freshness_status") not in {"fresh", "stale", "unknown"}:
            fail(f"provenance_report.json has invalid freshness_status: {entry}")
        if not isinstance(entry.get("warning_count"), int) or entry.get("warning_count") < 0:
            fail(f"provenance_report.json has invalid warning_count: {entry}")
        if not entry.get("diagnostic_summary"):
            fail(f"provenance_report.json is missing diagnostic_summary: {entry}")


def verify_drift_report():
    report_path = NORMALIZED_DIR / "drift_report.json"
    report = load_json(report_path)

    if report.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"drift_report.json has unexpected dataset_count: {report.get('dataset_count')}")
    for key in (
        "drifted_count",
        "healthy_count",
        "fallback_count",
        "partial_coverage_count",
        "degraded_count",
    ):
        if report.get(key) is None:
            fail(f"drift_report.json is missing {key}")

    datasets = report.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"drift_report.json has unexpected datasets: {sorted(dataset_names)}")

    for entry in datasets:
        if entry.get("drift_status") not in {"healthy", "drifted"}:
            fail(f"drift_report.json has invalid drift_status: {entry}")
        if entry.get("source_mode") not in {"live", "fallback"}:
            fail(f"drift_report.json has invalid source_mode: {entry}")
        if entry.get("coverage_status") not in {
            "full",
            "partial",
            "unknown",
            "not_applicable",
        }:
            fail(f"drift_report.json has invalid coverage_status: {entry}")
        if entry.get("degradation_status") not in {"none", "warning", "degraded"}:
            fail(f"drift_report.json has invalid degradation_status: {entry}")
        if not entry.get("coverage_summary"):
            fail(f"drift_report.json is missing coverage_summary: {entry}")
        if not isinstance(entry.get("warning_count"), int) or entry.get("warning_count") < 0:
            fail(f"drift_report.json has invalid warning_count: {entry}")
        if not entry.get("diagnostic_summary"):
            fail(f"drift_report.json is missing diagnostic_summary: {entry}")
        if not entry.get("recommended_action"):
            fail(f"drift_report.json is missing recommended_action: {entry}")


def verify_overview():
    overview_path = NORMALIZED_DIR / "overview.json"
    overview = load_json(overview_path)

    if overview.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(f"overview.json has unexpected dataset_count: {overview.get('dataset_count')}")
    if overview.get("overall_status") not in {"ok", "warn", "error"}:
        fail(f"overview.json has invalid overall_status: {overview.get('overall_status')}")
    if overview.get("shared_artifact_count", 0) <= 0:
        fail(
            f"overview.json has invalid shared_artifact_count: {overview.get('shared_artifact_count')}"
        )
    if overview.get("package_count", 0) <= 0:
        fail(f"overview.json has invalid package_count: {overview.get('package_count')}")
    if overview.get("warning_count", 0) > 0:
        verify_top_issue(overview.get("top_issue"), "overview.json")
        verify_top_issue_summary(
            overview.get("top_issue_summary"),
            overview.get("top_issue"),
            "overview.json",
        )
    elif overview.get("top_issue") is not None:
        verify_top_issue(overview.get("top_issue"), "overview.json")
        verify_top_issue_summary(
            overview.get("top_issue_summary"),
            overview.get("top_issue"),
            "overview.json",
        )

    primary_package = overview.get("primary_package")
    if not primary_package:
        fail("overview.json is missing primary_package")
    if primary_package.get("path") != "data/normalized/chile-hub-publishable-bundle.zip":
        fail(f"overview.json has invalid primary_package.path: {primary_package}")
    if primary_package.get("package_type") != "zip":
        fail(f"overview.json has invalid primary_package.package_type: {primary_package}")
    if primary_package.get("checksum_algorithm") != "sha256":
        fail(f"overview.json has invalid primary_package.checksum_algorithm: {primary_package}")
    if (
        primary_package.get("checksum_path")
        != "data/normalized/chile-hub-publishable-bundle.zip.sha256"
    ):
        fail(f"overview.json has invalid primary_package.checksum_path: {primary_package}")
    if (
        primary_package.get("verification_command")
        != "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"
    ):
        fail(f"overview.json has invalid primary_package.verification_command: {primary_package}")

    report_keys = overview.get("report_keys", [])
    if (
        "overview_json" not in report_keys
        or "health_json" not in report_keys
        or "drift_json" not in report_keys
        or "status_json" not in report_keys
    ):
        fail(f"overview.json has incomplete report_keys: {report_keys}")

    datasets = overview.get("datasets", [])
    dataset_names = {entry.get("dataset") for entry in datasets}
    if dataset_names != REQUIRED_DATASETS:
        fail(f"overview.json has unexpected datasets: {sorted(dataset_names)}")
    for entry in datasets:
        if entry.get("source_mode") not in {"live", "fallback"}:
            fail(f"overview.json has invalid source_mode: {entry}")
        if entry.get("validation_status") != "ok":
            fail(f"overview.json has unexpected validation_status: {entry}")
        if entry.get("freshness_status") not in {"fresh", "stale", "unknown"}:
            fail(f"overview.json has invalid freshness_status: {entry}")
        if entry.get("coverage_status") not in {
            "full",
            "partial",
            "unknown",
            "not_applicable",
        }:
            fail(f"overview.json has invalid coverage_status: {entry}")
        if entry.get("drift_status") not in {"healthy", "drifted"}:
            fail(f"overview.json has invalid drift_status: {entry}")


def verify_source_readiness_report():
    """Verifica que el reporte source_readiness.json existe y cubre todos los datasets."""
    path = NORMALIZED_DIR / "source_readiness.json"
    if not path.exists():
        fail("source_readiness.json not found — run 'make build' first")
    report = load_json(path)
    if report.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(
            f"source_readiness.json has unexpected dataset_count: "
            f"{report.get('dataset_count')} vs {len(REQUIRED_DATASETS)}"
        )
    readiness_names = {entry.get("dataset") for entry in report.get("datasets", [])}
    if readiness_names != REQUIRED_DATASETS:
        fail(f"source_readiness.json has unexpected datasets: {sorted(readiness_names)}")
    for entry in report.get("datasets", []):
        if entry.get("maturity_status") not in {
            "stable",
            "candidate",
            "experimental",
            "deprecated",
        }:
            fail(
                f"source_readiness.json has invalid maturity_status for "
                f"{entry.get('dataset')}: {entry.get('maturity_status')}"
            )
        if not entry.get("source_id"):
            fail(f"source_readiness.json missing source_id for {entry.get('dataset')}")
        if not entry.get("next_action"):
            fail(f"source_readiness.json missing next_action for {entry.get('dataset')}")


def verify_dataset_quality_report():
    """Verifica que el reporte dataset_quality.json existe y cubre todos los datasets."""
    path = NORMALIZED_DIR / "dataset_quality.json"
    if not path.exists():
        fail("dataset_quality.json not found — run 'make build' first")
    report = load_json(path)
    if report.get("dataset_count") != len(REQUIRED_DATASETS):
        fail(
            f"dataset_quality.json has unexpected dataset_count: "
            f"{report.get('dataset_count')} vs {len(REQUIRED_DATASETS)}"
        )
    quality_names = {entry.get("dataset") for entry in report.get("datasets", [])}
    if quality_names != REQUIRED_DATASETS:
        fail(f"dataset_quality.json has unexpected datasets: {sorted(quality_names)}")
    for entry in report.get("datasets", []):
        if entry.get("grade") not in {"A", "B", "C", "D", "F"}:
            fail(
                f"dataset_quality.json has invalid grade for "
                f"{entry.get('dataset')}: {entry.get('grade')}"
            )
        if entry.get("overall_score", -1) < 0:
            fail(f"dataset_quality.json missing overall_score for {entry.get('dataset')}")
        if not entry.get("blocking_reasons") and entry.get("overall_score", 0) < 100:
            # Permitir puntuación < 100 sin bloqueadores si es por cobertura not_applicable
            dims = entry.get("dimensions", {})
            if dims.get("validation", 0) < 100 or dims.get("source_readiness", 0) < 50:
                fail(
                    f"dataset_quality.json {entry.get('dataset')} score={entry.get('overall_score')} "
                    f"but has no blocking_reasons"
                )


def verify_readiness():
    """Perfil readiness: valida reportes source_readiness, dataset_quality y estancamiento."""
    verify_source_readiness_report()
    verify_dataset_quality_report()
    _verify_stagnation()
    print("Readiness verification passed: all datasets have source readiness and quality entries.")


def verify_publishable_zip():
    zip_path = NORMALIZED_DIR / "chile-hub-publishable-bundle.zip"
    if zip_path.stat().st_size <= 0:
        fail("publishable bundle zip is empty")
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    required_zip_entries = {
        "data/normalized/hub_status.json",
        "data/normalized/hub_bundle.json",
        "data/normalized/artifact_manifest.json",
        "data/normalized/overview.json",
    }
    missing_entries = sorted(required_zip_entries - names)
    if missing_entries:
        fail(f"publishable bundle zip is missing required entries: {missing_entries}")
    checksum_path = NORMALIZED_DIR / "chile-hub-publishable-bundle.zip.sha256"
    checksum_line = checksum_path.read_text(encoding="utf-8").strip()
    if "data/normalized/chile-hub-publishable-bundle.zip" not in checksum_line:
        fail("publishable bundle checksum file has unexpected contents")


def build_parser():
    parser = argparse.ArgumentParser(description="Verify generated chile-hub pipeline artifacts.")
    parser.add_argument(
        "--profile",
        choices=["dev", "readiness", "publication"],
        default="dev",
        help="Perfil de verificación: dev (default), readiness, o publication",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="[deprecated] Reject fallback, failed recovery, or stale data. "
        "Use --profile publication instead.",
    )
    return parser


def main():
    args = build_parser().parse_args()

    # Compatibilidad hacia atrás: --require-live fuerza perfil publication
    profile = "publication" if args.require_live else args.profile

    # Verificaciones comunes a todos los perfiles
    verify_staging_not_newer_than_normalized()
    verify_required_files()
    verify_pipeline_metadata()
    verify_hub_health()
    verify_hub_status()
    verify_hub_bundle()
    verify_redistribution_report()
    verify_provenance_report()
    verify_drift_report()
    verify_overview()
    verify_dataset_catalog()
    verify_schema_contracts()
    verify_source_registry()
    verify_artifact_manifest()
    verify_publishable_zip()

    if profile in ("readiness", "publication"):
        verify_readiness()

    if profile == "publication":
        verify_publication_policy()


if __name__ == "__main__":
    main()
