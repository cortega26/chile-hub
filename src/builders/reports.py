"""Builders de reportes y estados del hub (JSON).

Generan las estructuras de datos de los reportes operativos (estado del hub,
changelog, redistribución, procedencia, drift, overview, readiness de fuentes y
calidad de datasets) y las escriben a `data/normalized/` de forma atómica.
"""

import json
import os
import re
from datetime import datetime

from src.builders._shared import (
    DATA_DIR,
    DATASET_CATALOG_CONFIG,
    NORMALIZED_DIR,
    ROOT_DIR,
    UTC,
)
from src.builders.io_utils import write_json_atomic


def write_hub_health_json(health):
    output_path = os.path.join(NORMALIZED_DIR, "hub_health.json")
    write_json_atomic(health, output_path, ensure_ascii=False, indent=2)
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
    write_json_atomic(hub_status, output_path, ensure_ascii=False, indent=2)
    return output_path


def build_dataset_status(pipeline_metadata):
    datasets = []
    for dataset_name, dataset in sorted(pipeline_metadata.get("datasets", {}).items()):
        validation = pipeline_metadata.get("validations", {}).get(dataset_name, {})
        config = DATASET_CATALOG_CONFIG.get(dataset_name, {})
        datasets.append(
            {
                "dataset": dataset_name,
                "validation_status": validation.get("status"),
                "source_mode": dataset.get("source_mode"),
                "freshness": dataset.get("freshness", {}),
                "record_count": dataset.get("record_count"),
                "expected_record_count": config.get("expected_record_count"),
                "coverage_status": dataset.get("coverage", {}).get("status"),
                "coverage_ratio": dataset.get("coverage", {}).get("coverage_ratio"),
                "redistribution_status": config.get("reuse_policy", {}).get("status"),
                "redistribution_ok": config.get("reuse_policy", {}).get("redistribution_ok"),
                "refreshed_at_utc": dataset.get("refreshed_at_utc"),
                "warnings": validation.get("warnings", []),
                "recommended_action": dataset.get("drift", {}).get(
                    "recommended_action", "Ninguna."
                ),
            }
        )
    return {
        "generated_at_utc": pipeline_metadata.get("generated_at_utc"),
        "dataset_count": len(datasets),
        "datasets": datasets,
    }


def write_dataset_status_json(dataset_status):
    output_path = os.path.join(NORMALIZED_DIR, "dataset_status.json")
    write_json_atomic(dataset_status, output_path, ensure_ascii=False, indent=2)
    return output_path


def _is_compatible_type_change(old_type, new_type):
    """Determina si un cambio de tipo de columna es compatible hacia atrás.

    El mismo tipo siempre es compatible.
    Widening integer → float es compatible.
    Cualquier otro cambio de tipo es incompatible.
    """
    if old_type == new_type:
        return True
    if old_type == "integer" and new_type == "float":
        return True
    return False


def _compute_dataset_change_severity(current, previous, entry, is_new_dataset):
    """Calcula los campos de severidad para un dataset comparando contratos.

    Usa los campos contract_* incrustados en pipeline_metadata por
    enrich_dataset_metadata(). Maneja el caso de migración donde previous
    no tiene campos de contrato.
    """
    breaking_changes = []
    new_columns = []
    removed_columns = []
    primary_key_changed = False
    contract_changed = False

    prev_has_contract = previous.get("contract_exists", False)
    curr_has_contract = current.get("contract_exists", False)

    if prev_has_contract and curr_has_contract:
        prev_pk = previous.get("contract_primary_key", [])
        curr_pk = current.get("contract_primary_key", [])
        prev_required = set(previous.get("contract_required_columns", []))
        curr_required = set(current.get("contract_required_columns", []))
        prev_types = previous.get("contract_column_types", {})
        curr_types = current.get("contract_column_types", {})
        prev_nullable = set(previous.get("contract_nullable_columns", []))
        curr_nullable = set(current.get("contract_nullable_columns", []))

        # 1. Clave primaria cambiada → major
        if prev_pk != curr_pk:
            primary_key_changed = True
            contract_changed = True
            breaking_changes.append(f"Primary key changed from {prev_pk} to {curr_pk}")

        # 2. Columnas requeridas eliminadas → major
        removed_required = prev_required - curr_required
        for col in sorted(removed_required):
            breaking_changes.append(f"Required column removed: {col}")
            contract_changed = True

        # 3. Cambios de tipo incompatibles → major
        for col, prev_type in prev_types.items():
            curr_type = curr_types.get(col)
            if curr_type and prev_type != curr_type:
                if not _is_compatible_type_change(prev_type, curr_type):
                    breaking_changes.append(
                        f"Column type changed incompatibly: {col} from {prev_type} to {curr_type}"
                    )
                    contract_changed = True

        # 4. Columnas agregadas o eliminadas del contrato
        prev_contract_cols = set(prev_types.keys()) | prev_required | prev_nullable
        curr_contract_cols = set(curr_types.keys()) | curr_required | curr_nullable
        added_cols = curr_contract_cols - prev_contract_cols
        removed_cols = prev_contract_cols - curr_contract_cols

        for col in sorted(added_cols):
            if col in curr_nullable:
                new_columns.append(col)
            else:
                breaking_changes.append(f"New non-nullable column added: {col}")
                contract_changed = True
        if any(col in curr_nullable for col in added_cols):
            contract_changed = True

        for col in sorted(removed_cols):
            removed_columns.append(col)
            breaking_changes.append(f"Column removed from contract: {col}")
            contract_changed = True

    # Determinar severidad global
    if breaking_changes:
        change_severity = "major"
    elif contract_changed:
        change_severity = "minor"
    elif is_new_dataset:
        change_severity = "minor"
    elif (
        entry.get("added_fields")
        or entry.get("removed_fields")
        or entry.get("record_count_delta", 0) != 0
    ):
        change_severity = "patch"
    else:
        change_severity = "none"

    return {
        "change_severity": change_severity,
        "breaking_changes": breaking_changes,
        "new_columns": new_columns,
        "removed_columns": removed_columns,
        "primary_key_changed": primary_key_changed,
        "contract_changed": contract_changed,
    }


def build_dataset_changelog(current_metadata, previous_metadata=None):
    previous_datasets = (previous_metadata or {}).get("datasets", {})
    current_datasets = current_metadata.get("datasets", {})
    changes = []
    for dataset_name in sorted(current_datasets):
        current = current_datasets[dataset_name]
        previous = previous_datasets.get(dataset_name, {})
        current_fields = set(current.get("fields", []))
        previous_fields = set(previous.get("fields", []))

        entry = {
            "dataset": dataset_name,
            "previous_record_count": previous.get("record_count"),
            "current_record_count": current.get("record_count"),
            "record_count_delta": (
                current.get("record_count") - previous.get("record_count")
                if isinstance(current.get("record_count"), int)
                and isinstance(previous.get("record_count"), int)
                else None
            ),
            "added_fields": sorted(current_fields - previous_fields),
            "removed_fields": sorted(previous_fields - current_fields),
            "previous_source_mode": previous.get("source_mode"),
            "current_source_mode": current.get("source_mode"),
            "previous_freshness_status": previous.get("freshness", {}).get("status"),
            "current_freshness_status": current.get("freshness", {}).get("status"),
            "previous_validation_status": (previous_metadata or {})
            .get("validations", {})
            .get(dataset_name, {})
            .get("status"),
            "current_validation_status": current_metadata.get("validations", {})
            .get(dataset_name, {})
            .get("status"),
        }

        # Calcular severidad comparando contratos actual y anterior
        is_new_dataset = dataset_name not in previous_datasets
        severity_info = _compute_dataset_change_severity(current, previous, entry, is_new_dataset)
        entry.update(severity_info)

        changes.append(entry)

    return {
        "generated_at_utc": current_metadata.get("generated_at_utc"),
        "previous_generated_at_utc": (previous_metadata or {}).get("generated_at_utc"),
        "dataset_count": len(changes),
        "datasets": changes,
    }


def write_dataset_changelog_json(dataset_changelog):
    output_path = os.path.join(NORMALIZED_DIR, "dataset_changelog.json")
    write_json_atomic(dataset_changelog, output_path, ensure_ascii=False, indent=2)
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
    write_json_atomic(report, output_path, ensure_ascii=False, indent=2)
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
    write_json_atomic(report, output_path, ensure_ascii=False, indent=2)
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
    write_json_atomic(report, output_path, ensure_ascii=False, indent=2)
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
    write_json_atomic(overview, output_path, ensure_ascii=False, indent=2)
    return output_path, overview


def load_source_registry():
    """Carga el registry de fuentes desde data/source_registry.json."""
    registry_path = os.path.join(DATA_DIR, "source_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_source_readiness(pipeline_metadata):
    """Construye el reporte de madurez de fuente combinando registry y metadatos."""
    registry = load_source_registry()
    datasets_metadata = pipeline_metadata.get("datasets", {})

    entries = []
    for src in registry:
        dataset_name = src["dataset"]
        ds_meta = datasets_metadata.get(dataset_name, {})

        # Derivar URL del contrato de esquema
        contract_path = f"contracts/datasets/{dataset_name}.schema.json"
        contract_abs = os.path.join(ROOT_DIR, contract_path)
        source_contract_url = (
            f"github:chile-hub/chile-hub/{contract_path}" if os.path.exists(contract_abs) else None
        )

        # Determinar estancamiento
        review_by = src.get("review_by")
        stalled_after_days = src.get("stalled_after_days", 90)
        stalled = False
        if review_by:
            try:
                review_date = datetime.fromisoformat(review_by).replace(tzinfo=UTC)
                stalled = datetime.now(UTC) > review_date
            except (ValueError, TypeError):
                pass

        # Acción recomendada
        recommended_action = src.get("next_action", "—")
        if stalled:
            recommended_action = f"⚠ ESTANCADO (revisión vencida {review_by}). {recommended_action}"

        entries.append(
            {
                "dataset": dataset_name,
                "maturity_status": src.get("maturity_status", "unknown"),
                "source_id": src.get("source_id", ""),
                "source_name": src.get("source_name", ""),
                "official_url": src.get("official_url", ""),
                "access_method": src.get("access_method", ""),
                "license_status": src.get("license_status", ""),
                "source_mode": ds_meta.get("source_mode", "not_built"),
                "source_detail": ds_meta.get("source_detail", ""),
                "live_ready": src.get("live_ready", False),
                "fallback_allowed": src.get("fallback_allowed", False),
                "publish_blocking": src.get("publish_blocking", False),
                "live_extractor_status": src.get("live_extractor_status", "unknown"),
                "fallback_policy": src.get("fallback_policy", "none"),
                "source_contract_url": source_contract_url,
                "stalled_after_days": stalled_after_days,
                "review_by": review_by,
                "stalled": stalled,
                "owner": src.get("owner", "core"),
                "next_action": src.get("next_action", "—"),
                "recommended_action": recommended_action,
            }
        )

    maturity_counts = {
        s: sum(1 for e in entries if e["maturity_status"] == s)
        for s in ("stable", "candidate", "experimental", "deprecated")
    }

    return {
        "generated_at_utc": pipeline_metadata.get(
            "generated_at_utc", datetime.now(UTC).isoformat()
        ),
        "dataset_count": len(entries),
        **{f"{k}_count": v for k, v in maturity_counts.items()},
        "live_ready_count": sum(1 for e in entries if e["live_ready"]),
        "fallback_only_count": sum(
            1 for e in entries if e["live_extractor_status"] == "fallback_only"
        ),
        "publish_blocking_count": sum(1 for e in entries if e["publish_blocking"]),
        "datasets": entries,
    }


def write_source_readiness_json(readiness):
    output_path = os.path.join(NORMALIZED_DIR, "source_readiness.json")
    write_json_atomic(readiness, output_path, ensure_ascii=False, indent=2)
    return output_path, readiness


def build_dataset_quality(pipeline_metadata, hub_health, source_readiness):
    """Construye tarjeta de puntuación de calidad multidimensional por dataset."""
    health_by_dataset = {entry["dataset"]: entry for entry in hub_health.get("datasets", [])}
    readiness_by_dataset = {
        entry["dataset"]: entry for entry in source_readiness.get("datasets", [])
    }

    # Ponderaciones
    WEIGHTS = {
        "validation": 25,
        "schema_contract": 20,
        "source_readiness": 20,
        "freshness": 15,
        "coverage": 10,
        "reuse_policy": 10,
    }

    def _grade(score):
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    def _score_validation(health):
        return 100 if health.get("validation_status") == "ok" else 0

    def _score_schema_contract(dataset_name):
        contract_path = os.path.join(
            ROOT_DIR, "contracts", "datasets", f"{dataset_name}.schema.json"
        )
        return 100 if os.path.exists(contract_path) else 0

    def _score_source_readiness(readiness):
        if readiness.get("live_ready") and readiness.get("live_extractor_status") == "implemented":
            return 100
        if readiness.get("fallback_allowed"):
            return 50
        return 0

    def _score_freshness(health):
        status = health.get("freshness_status", "unknown")
        if status == "fresh":
            return 100
        if status == "stale":
            return 50
        return 0

    def _score_coverage(health):
        status = health.get("coverage_status", "unknown")
        if status == "full":
            return 100
        if status == "partial":
            return 70
        return 0

    def _score_reuse(health):
        status = health.get("reuse_status", "unknown")
        if status == "open-attribution":
            return 100
        if status == "public-api-review-terms":
            return 50
        return 0

    entries = []

    # Solo puntuar datasets que están en el catálogo con outputs (los que el build produce)
    eligible = {name for name, cfg in DATASET_CATALOG_CONFIG.items() if cfg.get("outputs")}
    for dataset_name in sorted(eligible & (set(health_by_dataset) | set(readiness_by_dataset))):
        health = health_by_dataset.get(dataset_name, {})
        readiness = readiness_by_dataset.get(dataset_name, {})

        dims = {
            "validation": _score_validation(health),
            "schema_contract": _score_schema_contract(dataset_name),
            "source_readiness": _score_source_readiness(readiness),
            "freshness": _score_freshness(health),
            "coverage": _score_coverage(health),
            "reuse_policy": _score_reuse(health),
        }

        overall = sum(dims[k] * WEIGHTS[k] for k in WEIGHTS) / 100

        blocking_reasons = []
        if dims["validation"] < 100:
            blocking_reasons.append(f"Validación: {health.get('validation_status', 'error')}")
        if dims["schema_contract"] < 100:
            blocking_reasons.append("Contrato de esquema ausente")
        if dims["source_readiness"] < 100:
            rd = readiness
            if rd.get("live_extractor_status") == "fallback_only":
                blocking_reasons.append(
                    f"Fuente en fallback_only — {rd.get('next_action', 'sin acción definida')}"
                )
            elif not rd.get("live_ready"):
                blocking_reasons.append("Fuente no lista para live")
            else:
                blocking_reasons.append("Madurez de fuente incompleta")
        if dims["freshness"] < 100:
            blocking_reasons.append(f"Datos {health.get('freshness_status', 'desconocidos')}")
        if dims["coverage"] < 100:
            blocking_reasons.append(f"Cobertura {health.get('coverage_status', 'desconocida')}")
        if dims["reuse_policy"] < 100:
            blocking_reasons.append(f"Reutilización: {health.get('reuse_status', 'desconocida')}")

        # Bloqueo por upstreams candidatos en datasets derivados
        maturity = readiness.get("maturity_status", "unknown")
        if maturity == "candidate" and readiness.get("access_method") == "derived":
            blocking_reasons.append("Capa derivada — depende de datasets upstream no publicables")

        recommended_action = readiness.get(
            "next_action",
            health.get("recommended_action", "—"),
        )
        if not blocking_reasons:
            recommended_action = "Mantener monitoreo operativo y actualizaciones periódicas."

        entries.append(
            {
                "dataset": dataset_name,
                "maturity_status": maturity,
                "overall_score": round(overall, 1),
                "grade": _grade(overall),
                "dimensions": dims,
                "weights": WEIGHTS,
                "blocking_reasons": blocking_reasons,
                "recommended_action": recommended_action,
            }
        )

    # Aggregate stats
    grades: dict[str, int] = {}
    for e in entries:
        g = e["grade"]
        grades[g] = grades.get(g, 0) + 1

    return {
        "generated_at_utc": pipeline_metadata.get(
            "generated_at_utc", datetime.now(UTC).isoformat()
        ),
        "dataset_count": len(entries),
        "grade_distribution": {
            "A": grades.get("A", 0),
            "B": grades.get("B", 0),
            "C": grades.get("C", 0),
            "D": grades.get("D", 0),
            "F": grades.get("F", 0),
        },
        "average_score": round(sum(e["overall_score"] for e in entries) / len(entries), 1)
        if entries
        else 0,
        "weights": WEIGHTS,
        "datasets": entries,
    }


def write_dataset_quality_json(quality):
    output_path = os.path.join(NORMALIZED_DIR, "dataset_quality.json")
    write_json_atomic(quality, output_path, ensure_ascii=False, indent=2)
    return output_path, quality


# ── Mappings para sync_readme_layers_table ──────────────────────────────

_DISPLAY_NAMES = {
    "regiones": "Regiones",
    "provincias": "Provincias",
    "comunas": "Comunas",
    "comunas_enriquecidas": "Comunas Enriquecidas",
    "indicadores": "Indicadores Económicos",
    "censo_comunal": "Censo Comunal 2024",
    "censo_hogares_viviendas": "Censo Hogares y Viviendas",
    "establecimientos_salud": "Establecimientos de Salud",
    "distritos_electorales": "Distritos Electorales",
    "establecimientos_educacionales": "Establecimientos Educacionales",
    "finanzas_municipales": "Finanzas Municipales",
    "resultados_educacionales": "Resultados Educacionales",
    "indicadores_urbanos_siedu": "Indicadores Urbanos SIEDU",
    "perfil_territorial_comunal": "Perfil Territorial Comunal",
    "empresas": "Empresas (RES)",
    "pobreza_comunal": "Pobreza Comunal (SAE)",
    "consumo_electrico_comunal": "Consumo Eléctrico Comunal",
    "delincuencia_comunal": "Delincuencia Comunal",
    "partidos_politicos": "Partidos Políticos",
    "autoridades_electas": "Autoridades Electas",
}

_SOURCE_NAMES = {
    "regiones": "BCN ArcGIS",
    "provincias": "BCN ArcGIS",
    "comunas": "BCN ArcGIS",
    "comunas_enriquecidas": "BCN + INE",
    "indicadores": "BCCh / mindicador.cl",
    "censo_comunal": "INE",
    "censo_hogares_viviendas": "INE",
    "establecimientos_salud": "MINSAL / datos.gob.cl",
    "distritos_electorales": "BCN / Ley 20.840",
    "establecimientos_educacionales": "MINEDUC",
    "finanzas_municipales": "SINIM / SUBDERE",
    "resultados_educacionales": "MINEDUC",
    "indicadores_urbanos_siedu": "INE / SIEDU",
    "perfil_territorial_comunal": "chile-hub derivado",
    "empresas": "Min. Economía / datos.gob.cl",
    "pobreza_comunal": "MDS / Observatorio Social",
    "consumo_electrico_comunal": "CNE / Energía Abierta",
    "delincuencia_comunal": "CEAD / SPD",
    "partidos_politicos": "Cámara de Diputados",
    "autoridades_electas": "Cámara de Diputados + Senado",
}

_LICENSE_LABELS = {
    "regiones": "CC BY",
    "provincias": "CC BY",
    "comunas": "CC BY",
    "comunas_enriquecidas": "CC BY",
    "indicadores": "Libre c/cita",
    "censo_comunal": "CC BY 4.0",
    "censo_hogares_viviendas": "CC BY 4.0",
    "establecimientos_salud": "CC0",
    "distritos_electorales": "CC0",
    "establecimientos_educacionales": "CC BY 3.0 CL",
    "finanzas_municipales": "Revisión términos",
    "resultados_educacionales": "CC BY 3.0 CL",
    "indicadores_urbanos_siedu": "Datos abiertos INE",
    "perfil_territorial_comunal": "Fuentes abiertas",
    "empresas": "CC-BY 3.0 CL",
    "pobreza_comunal": "Datos abiertos MDS",
    "consumo_electrico_comunal": "CC BY",
    "delincuencia_comunal": "Revisión términos",
    "partidos_politicos": "CC BY",
    "autoridades_electas": "CC BY",
}

# Dataset cuyos registros varían entre builds (directorios vivos).
# Se marcan con ~ para indicar que el número es aproximado al momento del build.
_VARIABLE_COUNT_DATASETS = {
    "establecimientos_salud",
    "establecimientos_educacionales",
    "empresas",
    "autoridades_electas",
    "partidos_politicos",
}

# Datasets con formato especial de registros (no numérico).
_SPECIAL_RECORD_COUNTS = {
    "indicadores": "Serie histórica",
}


def _format_record_count(record_count, expected_count, coverage_note):
    """Formatea el conteo de registros para la tabla del README."""
    if coverage_note and coverage_note.startswith("parcial"):
        if record_count is not None and expected_count is not None:
            return f"{record_count} (parcial, {record_count}/{expected_count})"
        if record_count is not None:
            return f"{record_count} (parcial)"
        return "parcial"

    if record_count is None:
        return "—"

    if record_count >= 10_000:
        # Formato con separador de miles y ~ para directorios variables
        s = f"{record_count:,}".replace(",", " ")
        return f"~{s}"
    return str(record_count)


def sync_readme_layers_table():
    """Regenera la tabla de capas del README desde los reportes máquina.

    Lee ``hub_health.json`` (modo, cobertura) y ``dataset_status.json``
    (conteo de registros) y escribe el bloque delimitado por
    ``<!-- START_DATASET_TABLE -->`` / ``<!-- END_DATASET_TABLE -->``
    en ``README.md``.

    Si los reportes no existen (p. ej. build no ejecutado), no modifica nada.
    """
    health_path = os.path.join(NORMALIZED_DIR, "hub_health.json")
    status_path = os.path.join(NORMALIZED_DIR, "dataset_status.json")

    if not os.path.exists(health_path) or not os.path.exists(status_path):
        print("README sync: omitido (reportes no encontrados)")
        return

    with open(health_path, "r", encoding="utf-8") as f:
        health = json.load(f)
    with open(status_path, "r", encoding="utf-8") as f:
        status = json.load(f)

    health_by_ds = {e["dataset"]: e for e in health.get("datasets", [])}
    status_by_ds = {e["dataset"]: e for e in status.get("datasets", [])}

    # Ordenar: primero datasets con outputs (consumibles), luego placeholders (próximamente)
    all_names = list(DATASET_CATALOG_CONFIG.keys())
    built = [n for n in all_names if DATASET_CATALOG_CONFIG[n].get("outputs")]
    upcoming = [n for n in all_names if not DATASET_CATALOG_CONFIG[n].get("outputs")]
    ordered_names = built + upcoming

    rows = []
    for i, ds_name in enumerate(ordered_names, 1):
        h = health_by_ds.get(ds_name, {})
        s = status_by_ds.get(ds_name, {})
        cfg = DATASET_CATALOG_CONFIG.get(ds_name, {})

        display_name = _DISPLAY_NAMES.get(ds_name, ds_name)
        source_name = _SOURCE_NAMES.get(ds_name, "—")
        license_label = _LICENSE_LABELS.get(ds_name, "—")

        has_outputs = bool(cfg.get("outputs"))

        source_mode = h.get("source_mode", "unknown")
        coverage_note = cfg.get("coverage_note", "")
        coverage_status = h.get("coverage_status", "unknown")

        # Indicador de modo
        if not has_outputs:
            mode_emoji = "🔜 próximamente"
            registros = "—"
        elif coverage_note.startswith("parcial"):
            mode_emoji = "🔶 parcial"
        elif source_mode == "live":
            mode_emoji = "🟢 live"
        elif source_mode == "fallback":
            mode_emoji = "🟡 fallback"
        else:
            mode_emoji = f"⚪ {source_mode}"

        # Conteo de registros (solo para capas con outputs)
        if has_outputs:
            if ds_name in _SPECIAL_RECORD_COUNTS:
                registros = _SPECIAL_RECORD_COUNTS[ds_name]
            elif coverage_note.startswith("parcial"):
                rc = s.get("record_count")
                ec = cfg.get("expected_record_count")
                if rc is not None and ec is not None:
                    rc_fmt = f"{rc:,}".replace(",", " ")
                    registros = f"{rc_fmt} (parcial, {rc}/{ec})"
                elif rc is not None:
                    rc_fmt = f"{rc:,}".replace(",", " ")
                    registros = f"{rc_fmt} (parcial)"
                else:
                    registros = "parcial"
            elif ds_name in _VARIABLE_COUNT_DATASETS:
                rc = s.get("record_count")
                registros = _format_record_count(
                    rc, cfg.get("expected_record_count"), coverage_note
                )
            elif source_mode == "fallback":
                rc = s.get("record_count")
                if rc is not None and rc > 0:
                    registros = f"{rc:,}".replace(",", " ")
                else:
                    registros = "fallback curado"
            elif coverage_status == "partial":
                rc = s.get("record_count")
                ec = cfg.get("expected_record_count")
                if rc is not None and ec is not None:
                    pct = int(round(rc / ec * 100)) if ec > 0 else 0
                    registros = f"{rc:,} (parcial, {pct}%)".replace(",", " ")
                elif rc is not None:
                    registros = f"{rc:,} (parcial)".replace(",", " ")
                else:
                    registros = "cobertura parcial"
            else:
                rc = s.get("record_count")
                registros = f"{rc:,}".replace(",", " ") if rc is not None else "—"

        # Advertencia para capas parciales
        name_display = f"**{display_name}**"
        if not has_outputs:
            name_display += " 🆕"
        elif coverage_note.startswith("parcial"):
            name_display += " ⚠️"

        # Etiqueta de actualización
        if not has_outputs:
            actualizacion = "—"
        else:
            freshness_label = cfg.get("freshness_policy", {}).get("label", "")
            if freshness_label in ("estable", ""):
                actualizacion = "—"
            else:
                actualizacion = freshness_label.capitalize()

        rows.append(
            f"| {i} | {name_display} | {registros} | {mode_emoji} | {source_name} | {license_label} | {actualizacion} |"
        )

    header = (
        "| # | Capa | Registros | Modo | Fuente | Licencia | Actualización |\n"
        "|:--:|:---|:---|:--:|:---|:---|:--:|"
    )
    table_lines = [header] + rows

    legend = (
        "> **🟢 live**: datos extraídos directamente desde la fuente oficial"
        " en cada ejecución del pipeline.\n"
        "> **🟡 fallback**: datos servidos desde un respaldo curado mientras"
        " se completa la extracción en vivo.\n"
        "> **🔶 parcial**: cobertura inferior al 50% del universo esperado."
        " Capa candidata, no completa.\n"
        "> **🔜 próximamente**: capa en carril candidate — extractor implementado,"
        " datos no incluidos en el bundle público.\n"
        "> Para auditar el estado exacto de cada capa:"
        " `chile-hub provenance` y `chile-hub health`."
    )

    table_block = "\n".join(table_lines) + "\n\n" + legend

    readme_path = os.path.join(ROOT_DIR, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- START_DATASET_TABLE -->.*?<!-- END_DATASET_TABLE -->"
    replacement = f"<!-- START_DATASET_TABLE -->\n\n{table_block}\n\n<!-- END_DATASET_TABLE -->"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README sync: tabla de capas regenerada desde hub_health.json + dataset_status.json")
    else:
        print("README sync: tabla de capas sin cambios")
