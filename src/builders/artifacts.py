"""Builders de artefactos publicables y bundles.

Generan el índice de artefactos, el manifiesto, el bundle JSON del hub y el
paquete ZIP publicable con su checksum SHA-256.
"""

import json
import os
import zipfile
from datetime import datetime

from src.builders._shared import (
    DATA_DIR,
    DATASET_CATALOG_CONFIG,
    NORMALIZED_DIR,
    PUBLISHABLE_ARTIFACT_SUFFIXES,
    PUBLISHABLE_BUNDLE_SHA256_NAME,
    PUBLISHABLE_BUNDLE_ZIP_NAME,
    UTC,
)
from src.builders.io_utils import compute_sha256, write_json_atomic
from src.builders.reports import load_source_registry


def build_publishable_artifact_index():
    artifact_index = {}
    # Load source registry to filter by public_bundle_eligible
    registry = load_source_registry()
    registry_by_dataset = {entry["dataset"]: entry for entry in registry}

    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        # Los datasets con alias_for son punteros de compatibilidad que comparten
        # los mismos archivos físicos que el dataset canónico. Saltarlos aquí evita
        # que sobrescriban el mapeo de artefactos y deja que el dataset canónico
        # sea el dueño de sus archivos.
        if config.get("alias_for"):
            continue

        reg_entry = registry_by_dataset.get(dataset_name, {})
        public_bundle_eligible = reg_entry.get("public_bundle_eligible", True)
        publication_track = reg_entry.get("publication_track", "stable_publishable")

        # Only include datasets eligible for the public bundle
        if not isinstance(public_bundle_eligible, bool) or not public_bundle_eligible:
            continue

        outputs = config.get("outputs", {})
        for output_type, path in outputs.items():
            if isinstance(path, str) and path.startswith("data/normalized/"):
                artifact_index[path] = {
                    "dataset": dataset_name,
                    "output_type": output_type,
                    "publication_track": publication_track,
                    "public_bundle_eligible": True,
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
        "data/normalized/dataset_status.json": {
            "shared_type": "dataset_status",
            "format": "json",
        },
        "data/normalized/dataset_changelog.json": {
            "shared_type": "dataset_changelog",
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
        "data/normalized/source_readiness.json": {
            "shared_type": "source_readiness",
            "format": "json",
        },
        "data/normalized/source_readiness.md": {
            "shared_type": "source_readiness",
            "format": "markdown",
        },
        "data/normalized/dataset_quality.json": {
            "shared_type": "dataset_quality",
            "format": "json",
        },
        "data/normalized/dataset_quality.md": {
            "shared_type": "dataset_quality",
            "format": "markdown",
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
        artifact_metadata = artifact_index.get(relative_path)
        # Only include artifacts that have metadata in the index.
        # Candidate dataset artifacts are excluded from the index and will be skipped.
        if artifact_metadata is None:
            continue
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
    write_json_atomic(manifest, output_path, ensure_ascii=False, indent=2)
    return output_path, manifest


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
        "source_readiness_json": ("source_readiness", "json"),
        "source_readiness_markdown": ("source_readiness", "markdown"),
        "dataset_quality_json": ("dataset_quality", "json"),
        "dataset_quality_markdown": ("dataset_quality", "markdown"),
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

    # Load registry to separate stable_publishable from candidate datasets
    registry = load_source_registry()
    registry_by_dataset = {entry["dataset"]: entry for entry in registry}

    stable_publicable_datasets = {
        entry["dataset"]
        for entry in registry
        if entry.get("publication_track") == "stable_publishable"
        and entry.get("public_bundle_eligible") is True
    }
    candidate_datasets = {
        entry["dataset"] for entry in registry if entry.get("publication_track") == "candidate"
    }

    full_catalog_count = dataset_catalog.get("dataset_count")
    public_dataset_count = len(stable_publicable_datasets)
    candidate_dataset_count = len(candidate_datasets)

    bundle = {
        "version": pipeline_metadata.get("version", "unknown"),
        "generated_at_utc": pipeline_metadata.get("generated_at_utc"),
        "overall_status": hub_health.get("overall_status"),
        "dataset_count": full_catalog_count,
        "public_dataset_count": public_dataset_count,
        "candidate_dataset_count": candidate_dataset_count,
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
        "candidate_datasets": [],
        "reports": reports,
        "shared_artifacts": shared_artifacts,
        "packages": artifact_manifest.get("packages", []),
    }

    health_by_dataset = {entry["dataset"]: entry for entry in hub_health.get("datasets", [])}

    for dataset in dataset_catalog.get("datasets", []):
        dataset_name = dataset["dataset"]
        dataset_health = health_by_dataset.get(dataset_name, {})

        # Si este dataset es un alias de otro, hereda los artefactos del canónico
        # para que ambos aparezcan en el bundle con los mismos archivos.
        canonical_name = dataset.get("alias_for") or dataset_name

        if dataset_name in stable_publicable_datasets:
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
                    "artifacts": artifacts_by_dataset.get(canonical_name, []),
                }
            )

        if dataset_name in candidate_datasets:
            reg_entry = registry_by_dataset.get(dataset_name, {})
            candidate_entry = {
                "dataset": dataset_name,
                "maturity_status": reg_entry.get("maturity_status", "unknown"),
                "publication_track": "candidate",
                "public_bundle_eligible": False,
                "source_mode": dataset.get("source_mode"),
                "source_detail": dataset.get("source_detail"),
                "freshness": dataset.get("freshness", {}),
                "next_action": reg_entry.get("next_action", ""),
            }
            if reg_entry.get("upstream_datasets"):
                candidate_entry["upstream_datasets"] = reg_entry["upstream_datasets"]
            bundle["candidate_datasets"].append(candidate_entry)

    output_path = os.path.join(NORMALIZED_DIR, "hub_bundle.json")
    write_json_atomic(bundle, output_path, ensure_ascii=False, indent=2)
    return output_path, bundle


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
    tmp_path = output_path + ".tmp"
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in artifacts:
            relative_path = artifact["path"]
            absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
            archive.write(absolute_path, arcname=relative_path)

    with zipfile.ZipFile(tmp_path, "r") as archive:
        bad_file = archive.testzip()
        if bad_file is not None:
            raise SystemExit(f"Error: ZIP corrupto; primer archivo fallido: {bad_file}")
        if len(archive.namelist()) != len(artifacts):
            raise SystemExit(
                f"Error: ZIP incompleto; esperados {len(artifacts)} archivos, "
                f"encontrados {len(archive.namelist())}"
            )
    os.replace(tmp_path, output_path)
    return output_path


def write_publishable_bundle_sha256(zip_path):
    output_path = os.path.join(NORMALIZED_DIR, PUBLISHABLE_BUNDLE_SHA256_NAME)
    relative_zip_path = f"data/normalized/{os.path.basename(zip_path)}"
    sha256 = compute_sha256(zip_path)
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(f"{sha256}  {relative_zip_path}\n")
    os.replace(tmp_path, output_path)
    return output_path


def attach_publishable_package_to_manifest(zip_path, sha256_path, manifest=None):
    manifest_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    if manifest is None:
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

    write_json_atomic(manifest, manifest_path, ensure_ascii=False, indent=2)
    return manifest_path, manifest
