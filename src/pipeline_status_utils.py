import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
PIPELINE_METADATA_PATH = NORMALIZED_DIR / "pipeline_metadata.json"
STATUS_MARKDOWN_PATH = NORMALIZED_DIR / "pipeline_status.md"
DATASET_CATALOG_MARKDOWN_PATH = NORMALIZED_DIR / "dataset_catalog.md"
HUB_HEALTH_MARKDOWN_PATH = NORMALIZED_DIR / "hub_health.md"
REDISTRIBUTION_REPORT_MARKDOWN_PATH = NORMALIZED_DIR / "redistribution_report.md"
PROVENANCE_REPORT_MARKDOWN_PATH = NORMALIZED_DIR / "provenance_report.md"
DRIFT_REPORT_MARKDOWN_PATH = NORMALIZED_DIR / "drift_report.md"
OVERVIEW_MARKDOWN_PATH = NORMALIZED_DIR / "overview.md"


def load_metadata(path=PIPELINE_METADATA_PATH):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def format_warnings(warnings):
    if not warnings:
        return "none"
    return "; ".join(warnings)


def format_freshness(freshness):
    if not freshness:
        return "unknown"
    status = freshness.get("status", "unknown")
    age_hours = freshness.get("age_hours")
    max_age_hours = freshness.get("max_age_hours")
    if age_hours is None or max_age_hours is None:
        return status
    return f"{status} ({age_hours}h / {max_age_hours}h)"


def format_reuse_policy(reuse_policy):
    if not reuse_policy:
        return "unknown"
    status = reuse_policy.get("status", "unknown")
    license_name = reuse_policy.get("license")
    if license_name:
        return f"{status} ({license_name})"
    return status


def compute_top_issue(entries):
    if not entries:
        return None

    def attention_priority(entry):
        warning_count = entry.get("warning_count", 0) or 0
        freshness_status = entry.get("freshness_status")
        drift_status = entry.get("drift_status")
        degradation_status = entry.get("degradation_status")
        if warning_count > 0 or freshness_status in {"stale", "unknown"}:
            return 0
        if drift_status == "drifted" or degradation_status in {"warning", "degraded"}:
            return 1
        return 2

    ordered = sorted(entries, key=lambda entry: (attention_priority(entry), entry.get("dataset", "")))
    top_entry = ordered[0]
    priority = attention_priority(top_entry)
    if priority >= 2:
        return None
    return {
        "dataset": top_entry.get("dataset"),
        "attention_priority": priority,
        "warning_count": top_entry.get("warning_count", 0),
        "build_freshness_status": top_entry.get("freshness_status"),
        "drift_status": top_entry.get("drift_status"),
        "degradation_status": top_entry.get("degradation_status"),
    }


def build_hub_health(metadata):
    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})
    entries = []

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})
        warning_count = len(validation.get("warnings", []))
        freshness_status = dataset.get("freshness", {}).get("status", "unknown")
        source_mode = dataset.get("source_mode", "unknown")
        validation_status = validation.get("status", "unknown")
        reuse_policy = dataset.get("reuse_policy", {})
        redistribution_ok = reuse_policy.get("redistribution_ok")
        reuse_status = reuse_policy.get("status", "unknown")
        degradation_status = dataset.get("degradation", {}).get("status", "none")
        coverage = dataset.get("coverage", {})
        coverage_status = coverage.get("status", "unknown")
        coverage_ratio = coverage.get("coverage_ratio")
        drift_status = dataset.get("drift", {}).get("status", "healthy")

        severity = "ok"
        if validation_status != "ok":
            severity = "error"
        elif freshness_status in {"stale", "unknown"}:
            severity = "warn"
        elif source_mode == "fallback" or warning_count > 0:
            severity = "warn"

        publishability_status = "ready"
        if redistribution_ok is False:
            publishability_status = "review_terms"
        elif reuse_status == "unknown":
            publishability_status = "unknown"

        entries.append(
            {
                "dataset": dataset_name,
                "severity": severity,
                "source_mode": source_mode,
                "freshness_status": freshness_status,
                "validation_status": validation_status,
                "warning_count": warning_count,
                "reuse_status": reuse_status,
                "redistribution_ok": redistribution_ok,
                "publishability_status": publishability_status,
                "degradation_status": degradation_status,
                "coverage_status": coverage_status,
                "coverage_ratio": coverage_ratio,
                "drift_status": drift_status,
            }
        )

    error_count = sum(1 for entry in entries if entry["severity"] == "error")
    warn_count = sum(1 for entry in entries if entry["severity"] == "warn")
    ok_count = sum(1 for entry in entries if entry["severity"] == "ok")
    overall_status = "error" if error_count else "warn" if warn_count else "ok"

    return {
        "generated_at_utc": metadata.get("generated_at_utc"),
        "overall_status": overall_status,
        "dataset_count": len(entries),
        "ok_count": ok_count,
        "warn_count": warn_count,
        "error_count": error_count,
        "live_count": sum(1 for entry in entries if entry["source_mode"] == "live"),
        "fallback_count": sum(1 for entry in entries if entry["source_mode"] == "fallback"),
        "stale_count": sum(1 for entry in entries if entry["freshness_status"] == "stale"),
        "unknown_freshness_count": sum(
            1 for entry in entries if entry["freshness_status"] == "unknown"
        ),
        "publishable_count": sum(1 for entry in entries if entry["publishability_status"] == "ready"),
        "review_terms_count": sum(
            1 for entry in entries if entry["publishability_status"] == "review_terms"
        ),
        "unknown_reuse_count": sum(
            1 for entry in entries if entry["publishability_status"] == "unknown"
        ),
        "degraded_count": sum(1 for entry in entries if entry["degradation_status"] == "degraded"),
        "degradation_warning_count": sum(
            1 for entry in entries if entry["degradation_status"] == "warning"
        ),
        "partial_coverage_count": sum(1 for entry in entries if entry["coverage_status"] == "partial"),
        "unknown_coverage_count": sum(1 for entry in entries if entry["coverage_status"] == "unknown"),
        "drifted_count": sum(1 for entry in entries if entry["drift_status"] == "drifted"),
        "warning_count": sum(entry["warning_count"] for entry in entries),
        "top_issue": compute_top_issue(entries),
        "datasets": entries,
    }


def build_status_text(metadata):
    health = build_hub_health(metadata)
    lines = []
    generated_at = metadata.get("generated_at_utc", "unknown")
    lines.append("chile-hub pipeline status")
    lines.append(f"generated_at_utc: {generated_at}")
    lines.append(f"overall_status: {health.get('overall_status', 'unknown')}")
    lines.append(f"warning_count: {health.get('warning_count', 0)}")
    if health.get("top_issue"):
        top_issue = health["top_issue"]
        lines.append(
            "top_issue: "
            f"{top_issue.get('dataset')} "
            f"(freshness={top_issue.get('build_freshness_status')}, "
            f"drift={top_issue.get('drift_status')}, "
            f"warnings={top_issue.get('warning_count', 0)})"
        )
    else:
        lines.append("top_issue: none")
    lines.append("")

    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})

        lines.append(f"[{dataset_name}]")
        lines.append(f"source: {dataset.get('source_name', 'unknown')}")
        lines.append(f"mode: {dataset.get('source_mode', 'unknown')}")
        lines.append(f"detail: {dataset.get('source_detail', 'unknown')}")
        lines.append(f"refreshed_at_utc: {dataset.get('refreshed_at_utc', 'unknown')}")
        lines.append(f"freshness: {format_freshness(dataset.get('freshness'))}")
        lines.append(f"records: {dataset.get('record_count', 'unknown')}")
        lines.append(f"coverage: {dataset.get('coverage', {}).get('summary', 'unknown')}")
        lines.append(f"validation_status: {validation.get('status', 'unknown')}")
        lines.append(f"warnings: {format_warnings(validation.get('warnings', []))}")

        notes = dataset.get("notes", [])
        if notes:
            lines.append(f"notes: {'; '.join(notes)}")

        indicator_codes = dataset.get("indicator_codes")
        if indicator_codes:
            lines.append(f"indicator_codes: {', '.join(indicator_codes)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_status_markdown(metadata):
    health = build_hub_health(metadata)
    generated_at = metadata.get("generated_at_utc", "unknown")
    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})

    lines = [
        "# chile-hub pipeline status",
        "",
        f"- `generated_at_utc`: `{generated_at}`",
        f"- `overall_status`: `{health.get('overall_status', 'unknown')}`",
        f"- `warning_count`: `{health.get('warning_count', 0)}`",
    ]
    if health.get("top_issue"):
        top_issue = health["top_issue"]
        lines.append(
            f"- `top_issue`: `{top_issue.get('dataset')}` "
            f"(freshness={top_issue.get('build_freshness_status')}, "
            f"drift={top_issue.get('drift_status')}, "
            f"warnings={top_issue.get('warning_count', 0)})"
        )
    else:
        lines.append("- `top_issue`: `none`")
    lines.extend(
        [
        "",
        "| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |",
        ]
    )

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})
        warnings = format_warnings(validation.get("warnings", []))
        lines.append(
            "| "
            f"`{dataset_name}` | "
            f"{dataset.get('source_name', 'unknown')} | "
            f"`{dataset.get('source_mode', 'unknown')}` | "
            f"`{dataset.get('source_detail', 'unknown')}` | "
            f"`{format_freshness(dataset.get('freshness'))}` | "
            f"`{dataset.get('coverage', {}).get('status', 'unknown')}` | "
            f"{dataset.get('record_count', 'unknown')} | "
            f"`{validation.get('status', 'unknown')}` | "
            f"{warnings} |"
        )

    lines.append("")

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})
        lines.append(f"## {dataset_name}")
        lines.append("")
        lines.append(f"- `refreshed_at_utc`: `{dataset.get('refreshed_at_utc', 'unknown')}`")
        lines.append(f"- `freshness`: `{format_freshness(dataset.get('freshness'))}`")
        lines.append(f"- `coverage`: `{dataset.get('coverage', {}).get('summary', 'unknown')}`")
        lines.append(f"- `fields`: `{', '.join(dataset.get('fields', []))}`")

        notes = dataset.get("notes", [])
        if notes:
            lines.append(f"- `notes`: {'; '.join(notes)}")

        indicator_codes = dataset.get("indicator_codes")
        if indicator_codes:
            lines.append(f"- `indicator_codes`: `{', '.join(indicator_codes)}`")

        warnings = validation.get("warnings", [])
        if warnings:
            lines.append(f"- `warnings`: {'; '.join(warnings)}")
        else:
            lines.append("- `warnings`: none")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_status_markdown_file(metadata, path=STATUS_MARKDOWN_PATH):
    Path(path).write_text(build_status_markdown(metadata), encoding="utf-8")


def build_hub_health_markdown(health):
    lines = [
        "# chile-hub health summary",
        "",
        f"- `generated_at_utc`: `{health.get('generated_at_utc', 'unknown')}`",
        f"- `overall_status`: `{health.get('overall_status', 'unknown')}`",
        f"- `dataset_count`: `{health.get('dataset_count', 0)}`",
        f"- `ok_count`: `{health.get('ok_count', 0)}`",
        f"- `warn_count`: `{health.get('warn_count', 0)}`",
        f"- `error_count`: `{health.get('error_count', 0)}`",
        f"- `live_count`: `{health.get('live_count', 0)}`",
        f"- `fallback_count`: `{health.get('fallback_count', 0)}`",
        f"- `stale_count`: `{health.get('stale_count', 0)}`",
        f"- `publishable_count`: `{health.get('publishable_count', 0)}`",
        f"- `review_terms_count`: `{health.get('review_terms_count', 0)}`",
        f"- `unknown_reuse_count`: `{health.get('unknown_reuse_count', 0)}`",
        f"- `degraded_count`: `{health.get('degraded_count', 0)}`",
        f"- `degradation_warning_count`: `{health.get('degradation_warning_count', 0)}`",
        f"- `partial_coverage_count`: `{health.get('partial_coverage_count', 0)}`",
        f"- `unknown_coverage_count`: `{health.get('unknown_coverage_count', 0)}`",
        f"- `drifted_count`: `{health.get('drifted_count', 0)}`",
        f"- `warning_count`: `{health.get('warning_count', 0)}`",
    ]
    if health.get("top_issue"):
        top_issue = health["top_issue"]
        lines.append(
            f"- `top_issue`: `{top_issue.get('dataset')}` "
            f"(freshness={top_issue.get('build_freshness_status')}, "
            f"drift={top_issue.get('drift_status')}, "
            f"warnings={top_issue.get('warning_count', 0)})"
        )
    else:
        lines.append("- `top_issue`: `none`")
    lines.extend(
        [
            "",
            "| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |",
        ]
    )

    for entry in health.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"`{entry.get('severity', 'unknown')}` | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"`{entry.get('freshness_status', 'unknown')}` | "
            f"`{entry.get('coverage_status', 'unknown')}` | "
            f"`{entry.get('drift_status', 'unknown')}` | "
            f"`{entry.get('publishability_status', 'unknown')}` | "
            f"`{entry.get('degradation_status', 'unknown')}` | "
            f"`{entry.get('validation_status', 'unknown')}` | "
            f"{entry.get('warning_count', 0)} |"
        )

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_hub_health_markdown_file(health, path=HUB_HEALTH_MARKDOWN_PATH):
    Path(path).write_text(build_hub_health_markdown(health), encoding="utf-8")


def build_redistribution_report_markdown(report):
    lines = [
        "# chile-hub redistribution report",
        "",
        f"- `generated_at_utc`: `{report.get('generated_at_utc', 'unknown')}`",
        f"- `dataset_count`: `{report.get('dataset_count', 0)}`",
        f"- `ready_count`: `{report.get('ready_count', 0)}`",
        f"- `review_terms_count`: `{report.get('review_terms_count', 0)}`",
        f"- `unknown_count`: `{report.get('unknown_count', 0)}`",
        "",
        "| Dataset | Publishability | License | Attribution | Redistribution | Action |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for entry in report.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"`{entry.get('publishability_status', 'unknown')}` | "
            f"{entry.get('license', 'unknown')} | "
            f"`{'yes' if entry.get('attribution_required') else 'no'}` | "
            f"`{'ok' if entry.get('redistribution_ok') else 'review' if entry.get('redistribution_ok') is False else 'unknown'}` | "
            f"{entry.get('recommended_action', 'unknown')} |"
        )

    lines.append("")
    for entry in report.get("datasets", []):
        lines.append(f"## {entry.get('dataset', 'unknown')}")
        lines.append("")
        lines.append(f"- `publishability_status`: `{entry.get('publishability_status', 'unknown')}`")
        lines.append(f"- `license`: `{entry.get('license', 'unknown')}`")
        lines.append(f"- `license_url`: {entry.get('license_url', 'unknown')}")
        lines.append(f"- `attribution_required`: `{entry.get('attribution_required')}`")
        lines.append(f"- `redistribution_ok`: `{entry.get('redistribution_ok')}`")
        lines.append(f"- `recommended_action`: {entry.get('recommended_action', 'unknown')}")
        lines.append(f"- `summary`: {entry.get('summary', 'unknown')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_redistribution_report_markdown_file(report, path=REDISTRIBUTION_REPORT_MARKDOWN_PATH):
    Path(path).write_text(build_redistribution_report_markdown(report), encoding="utf-8")


def build_provenance_report_markdown(report):
    lines = [
        "# chile-hub provenance report",
        "",
        f"- `generated_at_utc`: `{report.get('generated_at_utc', 'unknown')}`",
        f"- `dataset_count`: `{report.get('dataset_count', 0)}`",
        f"- `live_count`: `{report.get('live_count', 0)}`",
        f"- `fallback_count`: `{report.get('fallback_count', 0)}`",
        "",
        "| Dataset | Source | Mode | Detail | Refreshed | Freshness | Reuse |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for entry in report.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"{entry.get('source_name', 'unknown')} | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"`{entry.get('source_detail', 'unknown')}` | "
            f"`{entry.get('refreshed_at_utc', 'unknown')}` | "
            f"`{entry.get('freshness_label', 'unknown')}` | "
            f"`{entry.get('reuse_status', 'unknown')}` |"
        )

    lines.append("")
    for entry in report.get("datasets", []):
        lines.append(f"## {entry.get('dataset', 'unknown')}")
        lines.append("")
        lines.append(f"- `source_name`: {entry.get('source_name', 'unknown')}")
        lines.append(f"- `source_url`: {entry.get('source_url', 'unknown')}")
        lines.append(f"- `source_mode`: `{entry.get('source_mode', 'unknown')}`")
        lines.append(f"- `source_detail`: `{entry.get('source_detail', 'unknown')}`")
        lines.append(f"- `refreshed_at_utc`: `{entry.get('refreshed_at_utc', 'unknown')}`")
        lines.append(f"- `freshness`: `{entry.get('freshness_label', 'unknown')}`")
        lines.append(f"- `reuse_status`: `{entry.get('reuse_status', 'unknown')}`")
        lines.append(f"- `documentation`: `{entry.get('documentation', 'unknown')}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_provenance_report_markdown_file(report, path=PROVENANCE_REPORT_MARKDOWN_PATH):
    Path(path).write_text(build_provenance_report_markdown(report), encoding="utf-8")


def build_drift_report_markdown(report):
    lines = [
        "# chile-hub drift report",
        "",
        f"- `generated_at_utc`: `{report.get('generated_at_utc', 'unknown')}`",
        f"- `dataset_count`: `{report.get('dataset_count', 0)}`",
        f"- `drifted_count`: `{report.get('drifted_count', 0)}`",
        f"- `healthy_count`: `{report.get('healthy_count', 0)}`",
        f"- `fallback_count`: `{report.get('fallback_count', 0)}`",
        f"- `partial_coverage_count`: `{report.get('partial_coverage_count', 0)}`",
        f"- `degraded_count`: `{report.get('degraded_count', 0)}`",
        "",
        "| Dataset | Drift | Mode | Coverage | Degradation | Action |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for entry in report.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"`{entry.get('drift_status', 'unknown')}` | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"`{entry.get('coverage_status', 'unknown')}` | "
            f"`{entry.get('degradation_status', 'unknown')}` | "
            f"{entry.get('recommended_action', 'unknown')} |"
        )

    lines.append("")
    for entry in report.get("datasets", []):
        lines.append(f"## {entry.get('dataset', 'unknown')}")
        lines.append("")
        lines.append(f"- `drift_status`: `{entry.get('drift_status', 'unknown')}`")
        lines.append(f"- `source_mode`: `{entry.get('source_mode', 'unknown')}`")
        lines.append(f"- `coverage`: `{entry.get('coverage_summary', 'unknown')}`")
        lines.append(f"- `degradation`: {entry.get('degradation_impact', 'unknown')}")
        lines.append(f"- `recommended_action`: {entry.get('recommended_action', 'unknown')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_drift_report_markdown_file(report, path=DRIFT_REPORT_MARKDOWN_PATH):
    Path(path).write_text(build_drift_report_markdown(report), encoding="utf-8")


def build_overview_markdown(overview):
    lines = [
        "# chile-hub overview",
        "",
        f"- `generated_at_utc`: `{overview.get('generated_at_utc', 'unknown')}`",
        f"- `overall_status`: `{overview.get('overall_status', 'unknown')}`",
        f"- `dataset_count`: `{overview.get('dataset_count', 0)}`",
        f"- `live_count`: `{overview.get('live_count', 0)}`",
        f"- `fallback_count`: `{overview.get('fallback_count', 0)}`",
        f"- `stale_count`: `{overview.get('stale_count', 0)}`",
        f"- `drifted_count`: `{overview.get('drifted_count', 0)}`",
        f"- `degraded_count`: `{overview.get('degraded_count', 0)}`",
        f"- `partial_coverage_count`: `{overview.get('partial_coverage_count', 0)}`",
        f"- `warning_count`: `{overview.get('warning_count', 0)}`",
        f"- `shared_artifact_count`: `{overview.get('shared_artifact_count', 0)}`",
        f"- `package_count`: `{overview.get('package_count', 0)}`",
    ]
    if overview.get("top_issue"):
        top_issue = overview["top_issue"]
        lines.append(
            f"- `top_issue`: `{top_issue.get('dataset')}` "
            f"(freshness={top_issue.get('build_freshness_status')}, "
            f"drift={top_issue.get('drift_status')}, "
            f"warnings={top_issue.get('warning_count', 0)})"
        )
    else:
        lines.append("- `top_issue`: `none`")
    lines.extend(
        [
            "",
            "| Dataset | Mode | Validation | Freshness | Coverage | Drift |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for entry in overview.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"`{entry.get('validation_status', 'unknown')}` | "
            f"`{entry.get('freshness_status', 'unknown')}` | "
            f"`{entry.get('coverage_status', 'unknown')}` | "
            f"`{entry.get('drift_status', 'unknown')}` |"
        )

    lines.append("")
    primary_package = overview.get("primary_package")
    if primary_package:
        lines.append("## Primary Package")
        lines.append("")
        lines.append(f"- `path`: `{primary_package.get('path', 'unknown')}`")
        lines.append(f"- `package_type`: `{primary_package.get('package_type', 'unknown')}`")
        lines.append(f"- `size_bytes`: `{primary_package.get('size_bytes', 0)}`")
        lines.append(
            f"- `checksum`: `{primary_package.get('checksum_algorithm', 'unknown')}` "
            f"via `{primary_package.get('checksum_path', 'unknown')}`"
        )
        lines.append(
            f"- `verification_command`: `{primary_package.get('verification_command', 'unknown')}`"
        )
        lines.append("")

    report_keys = overview.get("report_keys", [])
    if report_keys:
        lines.append(f"- `report_keys`: `{', '.join(report_keys)}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_overview_markdown_file(overview, path=OVERVIEW_MARKDOWN_PATH):
    Path(path).write_text(build_overview_markdown(overview), encoding="utf-8")


def build_dataset_catalog_markdown(catalog):
    lines = [
        "# chile-hub dataset catalog",
        "",
        f"- `generated_at_utc`: `{catalog.get('generated_at_utc', 'unknown')}`",
        f"- `dataset_count`: `{catalog.get('dataset_count', 0)}`",
        "",
        "| Dataset | Source | Mode | Freshness | Reuse | Records | Confidence | Join Keys | Validation |",
        "| :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |",
    ]

    for entry in catalog.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"{entry.get('source_name', 'unknown')} | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"`{format_freshness(entry.get('freshness'))}` | "
            f"`{format_reuse_policy(entry.get('reuse_policy'))}` | "
            f"{entry.get('record_count', 'unknown')} | "
            f"`{entry.get('confidence_tier', 'unknown')}` | "
            f"`{', '.join(entry.get('join_keys', []))}` | "
            f"`{entry.get('validation_status', 'unknown')}` |"
        )

    lines.append("")

    for entry in catalog.get("datasets", []):
        lines.append(f"## {entry.get('dataset', 'unknown')}")
        lines.append("")
        lines.append(entry.get("description", ""))
        lines.append("")
        lines.append(f"- `source_url`: {entry.get('source_url', 'unknown')}")
        lines.append(f"- `documentation`: `{entry.get('documentation', 'unknown')}`")
        lines.append(f"- `freshness`: `{format_freshness(entry.get('freshness'))}`")
        lines.append(
            f"- `reuse_policy`: `{json.dumps(entry.get('reuse_policy', {}), ensure_ascii=False)}`"
        )
        lines.append(f"- `fields`: `{', '.join(entry.get('fields', []))}`")
        lines.append(f"- `join_keys`: `{', '.join(entry.get('join_keys', []))}`")
        lines.append(f"- `outputs`: `{json.dumps(entry.get('outputs', {}), ensure_ascii=False)}`")
        usage_examples = entry.get("usage_examples", {})
        if usage_examples:
            lines.append(f"- `usage_examples`: `{json.dumps(usage_examples, ensure_ascii=False)}`")

        warnings = entry.get("warnings", [])
        if warnings:
            lines.append(f"- `warnings`: {'; '.join(warnings)}")
        else:
            lines.append("- `warnings`: none")

        notes = entry.get("notes", [])
        if notes:
            lines.append(f"- `notes`: {'; '.join(notes)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_dataset_catalog_markdown_file(catalog, path=DATASET_CATALOG_MARKDOWN_PATH):
    Path(path).write_text(build_dataset_catalog_markdown(catalog), encoding="utf-8")
