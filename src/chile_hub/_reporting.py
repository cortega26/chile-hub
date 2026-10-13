"""Renderizado de tablas y textos del hub (plan 134b).

Composición pura: cada `render_*` recibe los datos ya calculados por
`ChileHub` (dicts/listas de sus métodos públicos) y devuelve el string.
El hub conserva los métodos públicos delegando acá — misma salida.
"""

from typing import Any

from ._render import render_table
from .pipeline_status_utils import format_top_issue_summary


def render_top_issue_table(top_issue: dict[str, Any] | None) -> str:
    """Renderiza `top_issue_table` (movido del hub, plan 134b)."""
    if not top_issue:
        return "chile-hub top issue\n\nSin top issue activo.\n"

    rows = [
        ["dataset", top_issue.get("dataset", "unknown")],
        ["attention_priority", str(top_issue.get("attention_priority", "unknown"))],
        ["build_freshness_status", top_issue.get("build_freshness_status", "unknown")],
        ["current_freshness_status", top_issue.get("current_freshness_status", "unknown")],
        ["drift_status", top_issue.get("drift_status", "unknown")],
        ["degradation_status", top_issue.get("degradation_status", "unknown")],
        ["warning_count", str(top_issue.get("warning_count", 0))],
        ["source_detail", top_issue.get("source_detail", "unknown")],
        ["diagnostic_summary", top_issue.get("diagnostic_summary", "unknown")],
        ["recommended_action", top_issue.get("recommended_action", "unknown")],
    ]
    return render_table("chile-hub top issue", ["key", "value"], rows)


def render_summary_table(rows: list[dict[str, Any]]) -> str:
    """Renderiza `summary_table` (movido del hub, plan 134b)."""
    table_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("source_mode", "unknown"),
            str(entry.get("record_count", "N/D")),
            entry.get("freshness_status", "unknown"),
            entry.get("coverage_status", "unknown"),
            entry.get("validation_status", "unknown"),
            entry.get("drift_status", "unknown"),
            str(entry.get("warning_count", 0)),
        ]
        for entry in rows
    ]
    return render_table(
        "chile-hub summary",
        [
            "dataset",
            "mode",
            "records",
            "freshness",
            "coverage",
            "validation",
            "drift",
            "warnings",
        ],
        table_rows,
    )


def render_snapshot_text(
    overview: dict[str, Any], freshness_audit: dict[str, Any], runtime_status: dict[str, Any]
) -> str:
    """Renderiza `snapshot_text` (movido del hub, plan 134b)."""
    freshness_by_dataset = {
        entry.get("dataset"): entry for entry in freshness_audit.get("datasets", [])
    }
    package = overview.get("primary_package") or {}
    top_issue = overview.get("top_issue")
    lines = [
        "chile-hub snapshot",
        f"generated_at_utc: {overview.get('generated_at_utc', 'unknown')}",
        (
            f"status_build: {overview.get('build_overall_status', overview.get('overall_status', 'unknown'))} | "
            f"status_current: {overview.get('current_overall_status', runtime_status.get('current_overall_status', 'unknown'))} | "
            f"datasets={overview.get('dataset_count', 0)} | "
            f"live={overview.get('live_count', 0)} | "
            f"stale={overview.get('stale_count', 0)} | "
            f"drifted={overview.get('drifted_count', 0)} | "
            f"warnings={overview.get('warning_count', 0)}"
        ),
        (
            f"current_freshness: fresh={freshness_audit.get('fresh_count', 0)} | "
            f"stale={freshness_audit.get('stale_count', 0)} | "
            f"unknown={freshness_audit.get('unknown_count', 0)} | "
            f"checked_at={freshness_audit.get('checked_at_utc', 'unknown')}"
        ),
    ]
    if top_issue:
        lines.append(
            f"top_issue: {top_issue.get('dataset')} | "
            f"build={top_issue.get('build_freshness_status', 'unknown')} | "
            f"current={top_issue.get('current_freshness_status', 'unknown')} | "
            f"drift={top_issue.get('drift_status', 'unknown')} | "
            f"warnings={top_issue.get('warning_count', 0)}"
        )
        lines.append(f"top_issue_reason: {top_issue.get('diagnostic_summary', 'unknown')}")
        lines.append(f"top_issue_action: {top_issue.get('recommended_action', 'unknown')}")

    if package:
        lines.append(
            f"package: {package.get('path', 'unknown')} | "
            f"{package.get('package_type', 'unknown')} | "
            f"checksum={package.get('checksum_algorithm', 'unknown')}"
        )
        lines.append(f"verify: {package.get('verification_command', 'unknown')}")

    lines.append("")
    for entry in overview.get("datasets", []):
        runtime_freshness = freshness_by_dataset.get(entry.get("dataset"), {})
        lines.append(
            f"- {entry.get('dataset', 'unknown')}: "
            f"mode={entry.get('source_mode', 'unknown')}, "
            f"validation={entry.get('validation_status', 'unknown')}, "
            f"freshness_build={entry.get('freshness_status', 'unknown')}, "
            f"freshness_now={runtime_freshness.get('current_freshness_status', 'unknown')}, "
            f"coverage={entry.get('coverage_status', 'unknown')}, "
            f"drift={entry.get('drift_status', 'unknown')}"
        )

    return "\n".join(lines) + "\n"


def render_snapshot_table(overview: dict[str, Any], freshness_audit: dict[str, Any]) -> str:
    """Renderiza `snapshot_table` (movido del hub, plan 134b)."""
    freshness_by_dataset = {
        entry.get("dataset"): entry for entry in freshness_audit.get("datasets", [])
    }
    rows = [
        ("generated_at_utc", overview.get("generated_at_utc", "unknown")),
        (
            "build_overall_status",
            overview.get("build_overall_status", overview.get("overall_status", "unknown")),
        ),
        (
            "current_overall_status",
            overview.get("current_overall_status", "unknown"),
        ),
        ("datasets", str(overview.get("dataset_count", 0))),
        ("live", str(overview.get("live_count", 0))),
        ("stale", str(overview.get("stale_count", 0))),
        ("drifted", str(overview.get("drifted_count", 0))),
        ("warnings", str(overview.get("warning_count", 0))),
        ("current_fresh", str(freshness_audit.get("fresh_count", 0))),
        ("current_stale", str(freshness_audit.get("stale_count", 0))),
        ("current_unknown", str(freshness_audit.get("unknown_count", 0))),
        ("audit_checked", freshness_audit.get("checked_at_utc", "unknown")),
    ]
    top_issue = overview.get("top_issue")
    if top_issue:
        rows.extend(
            [
                ("top_issue", top_issue.get("dataset", "unknown")),
                (
                    "top_issue_build",
                    top_issue.get("build_freshness_status", "unknown"),
                ),
                (
                    "top_issue_current",
                    top_issue.get("current_freshness_status", "unknown"),
                ),
                ("top_issue_drift", top_issue.get("drift_status", "unknown")),
                (
                    "top_issue_reason",
                    top_issue.get("diagnostic_summary", "unknown"),
                ),
                (
                    "top_issue_action",
                    top_issue.get("recommended_action", "unknown"),
                ),
                (
                    "top_issue_summary",
                    overview.get("top_issue_summary", format_top_issue_summary(top_issue)),
                ),
            ]
        )

    package = overview.get("primary_package") or {}
    if package:
        rows.extend(
            [
                ("package_path", package.get("path", "unknown")),
                ("package_type", package.get("package_type", "unknown")),
                ("checksum", package.get("checksum_algorithm", "unknown")),
                ("verify", package.get("verification_command", "unknown")),
            ]
        )

    label_width = max(len(label) for label, _ in rows)
    lines = ["chile-hub snapshot table", ""]
    lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)

    dataset_rows = []
    for entry in overview.get("datasets", []):
        runtime_freshness = freshness_by_dataset.get(entry.get("dataset"), {})
        dataset_rows.append(
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("validation_status", "unknown"),
                entry.get("freshness_status", "unknown"),
                runtime_freshness.get("current_freshness_status", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("drift_status", "unknown"),
            ]
        )

    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "mode", "validation", "build", "current", "coverage", "drift"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_shared_artifacts_table(artifacts: list[dict[str, Any]]) -> str:
    """Renderiza `shared_artifacts_table` (movido del hub, plan 134b)."""
    table_rows = []
    for entry in artifacts:
        size_bytes = entry.get("size_bytes")
        if isinstance(size_bytes, int):
            size_label = f"{size_bytes} B" if size_bytes < 1024 else f"{size_bytes / 1024:.1f} KB"
        else:
            size_label = "N/D"
        table_rows.append(
            [
                entry.get("shared_type", "unknown"),
                entry.get("format", "unknown"),
                size_label,
                entry.get("path", "unknown"),
            ]
        )
    return render_table(
        "chile-hub shared artifacts",
        ["shared_type", "format", "size", "path"],
        table_rows,
    )


def render_report_index_table(rows: list[dict[str, Any]]) -> str:
    """Renderiza `report_index_table` (movido del hub, plan 134b)."""
    table_rows = []
    for entry in rows:
        size_bytes = entry.get("size_bytes")
        if isinstance(size_bytes, int):
            size_label = f"{size_bytes} B" if size_bytes < 1024 else f"{size_bytes / 1024:.1f} KB"
        else:
            size_label = "N/D"
        table_rows.append(
            [
                entry.get("report_key", "unknown"),
                entry.get("shared_type", "unknown"),
                entry.get("format", "unknown"),
                size_label,
                entry.get("path", "unknown"),
            ]
        )
    return render_table(
        "chile-hub report index",
        ["report_key", "shared_type", "format", "size", "path"],
        table_rows,
    )


def render_overview_table(overview: dict[str, Any]) -> str:
    """Renderiza `overview_table` (movido del hub, plan 134b)."""
    rows = [
        ("generated_at_utc", overview.get("generated_at_utc", "unknown")),
        ("build_overall_status", overview.get("build_overall_status", "unknown")),
        (
            "current_overall_status",
            overview.get("current_overall_status", "unknown"),
        ),
        ("datasets", str(overview.get("dataset_count", 0))),
        ("live", str(overview.get("live_count", 0))),
        ("fallback", str(overview.get("fallback_count", 0))),
        ("build_stale", str(overview.get("stale_count", 0))),
        ("current_fresh", str(overview.get("current_fresh_count", 0))),
        ("current_stale", str(overview.get("current_stale_count", 0))),
        ("current_unknown", str(overview.get("current_unknown_count", 0))),
        ("drifted", str(overview.get("drifted_count", 0))),
        ("degraded", str(overview.get("degraded_count", 0))),
        ("partial_coverage", str(overview.get("partial_coverage_count", 0))),
        ("warnings", str(overview.get("warning_count", 0))),
        ("shared_artifacts", str(overview.get("shared_artifact_count", 0))),
        ("packages", str(overview.get("package_count", 0))),
        ("current_checked_at", overview.get("current_checked_at_utc", "unknown")),
    ]
    top_issue = overview.get("top_issue")
    if top_issue:
        rows.extend(
            [
                ("top_issue", top_issue.get("dataset", "unknown")),
                (
                    "top_issue_build",
                    top_issue.get("build_freshness_status", "unknown"),
                ),
                (
                    "top_issue_current",
                    top_issue.get("current_freshness_status", "unknown"),
                ),
                ("top_issue_drift", top_issue.get("drift_status", "unknown")),
                (
                    "top_issue_reason",
                    top_issue.get("diagnostic_summary", "unknown"),
                ),
                (
                    "top_issue_action",
                    top_issue.get("recommended_action", "unknown"),
                ),
                (
                    "top_issue_summary",
                    overview.get("top_issue_summary", format_top_issue_summary(top_issue)),
                ),
            ]
        )

    package = overview.get("primary_package") or {}
    if package:
        rows.extend(
            [
                ("package_path", package.get("path", "unknown")),
                ("package_type", package.get("package_type", "unknown")),
                ("checksum", package.get("checksum_algorithm", "unknown")),
            ]
        )

    label_width = max(len(label) for label, _ in rows)
    lines = ["chile-hub overview", ""]
    lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)

    dataset_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("source_mode", "unknown"),
            entry.get("validation_status", "unknown"),
            entry.get("freshness_status", "unknown"),
            entry.get("coverage_status", "unknown"),
            entry.get("drift_status", "unknown"),
        ]
        for entry in overview.get("datasets", [])
    ]

    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "mode", "validation", "build", "coverage", "drift"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_inventory_table(rows: list[dict[str, Any]]) -> str:
    """Renderiza `inventory_table` (movido del hub, plan 134b)."""
    table_rows = []
    for entry in rows:
        outputs = ",".join(entry.get("published_outputs", [])) or "N/D"
        size_bytes = entry.get("total_size_bytes")
        if isinstance(size_bytes, int):
            size_label = f"{size_bytes} B" if size_bytes < 1024 else f"{size_bytes / 1024:.1f} KB"
        else:
            size_label = "N/D"
        table_rows.append(
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                str(entry.get("record_count", "N/D")),
                outputs,
                size_label,
                entry.get("freshness_status", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("drift_status", "unknown"),
            ]
        )
    return render_table(
        "chile-hub inventory",
        ["dataset", "mode", "records", "outputs", "size", "freshness", "coverage", "drift"],
        table_rows,
    )


def render_check_sources_table(results: list[dict[str, Any]]) -> str:
    """Formatea el resultado de check_sources como una tabla amigable para terminal."""
    table_rows = []
    for entry in results:
        status = entry.get("status", "unknown")
        code = str(entry.get("status_code")) if entry.get("status_code") is not None else "N/A"
        latency = f"{entry.get('latency_ms')}ms" if entry.get("latency_ms") is not None else "N/A"
        url = entry.get("url", "N/A")
        if len(url) > 48:
            url = url[:45] + "..."
        table_rows.append(
            [
                entry.get("dataset", "unknown"),
                status,
                code,
                latency,
                entry.get("source_name", "unknown"),
                url,
            ]
        )
    return render_table(
        "chile-hub check-sources",
        ["dataset", "status", "code", "latency", "source name", "url"],
        table_rows,
    )


def render_status_table(status: dict[str, Any]) -> str:
    """Renderiza `status_table` (movido del hub, plan 134b)."""
    table_rows = [
        ["generated_at_utc", status.get("generated_at_utc", "unknown")],
        ["overall_status", status.get("overall_status", "unknown")],
        ["dataset_count", str(status.get("dataset_count", 0))],
        ["live_count", str(status.get("live_count", 0))],
        ["fallback_count", str(status.get("fallback_count", 0))],
        ["stale_count", str(status.get("stale_count", 0))],
        ["drifted_count", str(status.get("drifted_count", 0))],
        ["degraded_count", str(status.get("degraded_count", 0))],
        ["warning_count", str(status.get("warning_count", 0))],
    ]
    top_issue = status.get("top_issue")
    if top_issue:
        table_rows.extend(
            [
                ["top_issue", top_issue.get("dataset", "unknown")],
                ["top_issue_reason", top_issue.get("diagnostic_summary", "unknown")],
                ["top_issue_action", top_issue.get("recommended_action", "unknown")],
                [
                    "top_issue_summary",
                    status.get("top_issue_summary", format_top_issue_summary(top_issue)),
                ],
            ]
        )
    return render_table("chile-hub status", ["key", "value"], table_rows)


def render_health_table(health: dict[str, Any]) -> str:
    """Renderiza `health_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub health", ""]
    lines.append(
        "overall="
        f"{health.get('overall_status', 'unknown')} | "
        f"datasets={health.get('dataset_count', 0)} | "
        f"ok={health.get('ok_count', 0)} | "
        f"warn={health.get('warn_count', 0)} | "
        f"error={health.get('error_count', 0)} | "
        f"live={health.get('live_count', 0)} | "
        f"fallback={health.get('fallback_count', 0)} | "
        f"stale={health.get('stale_count', 0)} | "
        f"drifted={health.get('drifted_count', 0)}"
    )

    dataset_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("severity", "unknown"),
            entry.get("source_mode", "unknown"),
            entry.get("freshness_status", "unknown"),
            entry.get("validation_status", "unknown"),
            entry.get("publishability_status", "unknown"),
            entry.get("coverage_status", "unknown"),
            entry.get("drift_status", "unknown"),
            str(entry.get("warning_count", 0)),
        ]
        for entry in health.get("datasets", [])
    ]
    lines.append("")
    lines.append(
        render_table(
            "",
            [
                "dataset",
                "severity",
                "mode",
                "freshness",
                "validation",
                "reuse",
                "coverage",
                "drift",
                "warnings",
            ],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_runtime_status_table(runtime: dict[str, Any]) -> str:
    """Renderiza `runtime_status_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub runtime status", ""]
    lines.append(
        f"build={runtime.get('build_overall_status', 'unknown')} | "
        f"current={runtime.get('current_overall_status', 'unknown')} | "
        f"datasets={runtime.get('dataset_count', 0)} | "
        f"live={runtime.get('live_count', 0)} | "
        f"fresh={runtime.get('fresh_count', 0)} | "
        f"stale={runtime.get('stale_count', 0)} | "
        f"unknown={runtime.get('unknown_count', 0)} | "
        f"drifted={runtime.get('drifted_count', 0)} | "
        f"warnings={runtime.get('warning_count', 0)} | "
        f"checked_at={runtime.get('checked_at_utc', 'unknown')}"
    )
    if runtime.get("top_issue"):
        top_issue = runtime["top_issue"]
        lines.append(
            f"top_issue={top_issue.get('dataset', 'unknown')} | "
            f"build={top_issue.get('build_freshness_status', 'unknown')} | "
            f"current={top_issue.get('current_freshness_status', 'unknown')} | "
            f"drift={top_issue.get('drift_status', 'unknown')} | "
            f"warnings={top_issue.get('warning_count', 0)}"
        )
        lines.append(f"top_issue_reason={top_issue.get('diagnostic_summary', 'unknown')}")
        lines.append(f"top_issue_action={top_issue.get('recommended_action', 'unknown')}")
        lines.append(
            f"top_issue_summary={runtime.get('top_issue_summary', format_top_issue_summary(top_issue))}"
        )

    dataset_rows = []
    for entry in runtime.get("datasets", []):
        age = entry.get("current_age_hours")
        age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
        max_age = entry.get("max_age_hours")
        max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
        dataset_rows.append(
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("severity", "unknown"),
                entry.get("build_freshness_status", "unknown"),
                entry.get("current_freshness_status", "unknown"),
                age_label,
                max_age_label,
                entry.get("coverage_status", "unknown"),
                entry.get("drift_status", "unknown"),
                str(entry.get("warning_count", 0)),
            ]
        )
    lines.append("")
    lines.append(
        render_table(
            "",
            [
                "dataset",
                "mode",
                "severity",
                "build",
                "current",
                "age_h",
                "max_h",
                "coverage",
                "drift",
                "warnings",
            ],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_freshness_audit_table(audit: dict[str, Any]) -> str:
    """Renderiza `freshness_audit_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub freshness audit", ""]
    lines.append(
        f"checked_at_utc={audit.get('checked_at_utc')} | "
        f"datasets={audit.get('dataset_count', 0)} | "
        f"fresh={audit.get('fresh_count', 0)} | "
        f"stale={audit.get('stale_count', 0)} | "
        f"unknown={audit.get('unknown_count', 0)}"
    )

    dataset_rows = []
    for entry in audit.get("datasets", []):
        age = entry.get("current_age_hours")
        age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
        max_age = entry.get("max_age_hours")
        max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
        dataset_rows.append(
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("build_freshness_status", "unknown"),
                entry.get("current_freshness_status", "unknown"),
                age_label,
                max_age_label,
                entry.get("freshness_label", "N/D"),
            ]
        )
    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "mode", "build", "current", "age_h", "max_h", "label"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_packages_table(packages: list[dict[str, Any]]) -> str:
    """Renderiza `packages_table` (movido del hub, plan 134b)."""
    table_rows = []
    for package in packages:
        size_bytes = package.get("size_bytes")
        if isinstance(size_bytes, int):
            size_label = f"{size_bytes} B" if size_bytes < 1024 else f"{size_bytes / 1024:.1f} KB"
        else:
            size_label = "N/D"
        table_rows.append(
            [
                package.get("package_type", "unknown"),
                size_label,
                package.get("checksum_algorithm", "unknown"),
                package.get("path", "unknown"),
            ]
        )
    return render_table(
        "chile-hub packages",
        ["package_type", "size", "checksum", "path"],
        table_rows,
    )


def render_redistribution_table(report: dict[str, Any]) -> str:
    """Renderiza `redistribution_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub redistribution", ""]
    lines.append(
        f"ready={report.get('ready_count', 0)} | "
        f"review_terms={report.get('review_terms_count', 0)} | "
        f"unknown={report.get('unknown_count', 0)} | "
        f"datasets={report.get('dataset_count', 0)}"
    )

    dataset_rows = []
    for entry in report.get("datasets", []):
        attribution = "yes" if entry.get("attribution_required") else "no"
        dataset_rows.append(
            [
                entry.get("dataset", "unknown"),
                entry.get("publishability_status", "unknown"),
                entry.get("reuse_status", "unknown"),
                attribution,
                entry.get("license", "unknown"),
            ]
        )
    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "status", "reuse_status", "attribution", "license"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_provenance_table(report: dict[str, Any]) -> str:
    """Renderiza `provenance_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub provenance", ""]
    lines.append(
        f"datasets={report.get('dataset_count', 0)} | "
        f"live={report.get('live_count', 0)} | "
        f"fallback={report.get('fallback_count', 0)}"
    )

    dataset_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("source_mode", "unknown"),
            entry.get("source_detail", "unknown"),
            entry.get("freshness_status", "unknown"),
            str(entry.get("warning_count", 0)),
            entry.get("refreshed_at_utc", "unknown"),
        ]
        for entry in report.get("datasets", [])
    ]
    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "mode", "source", "freshness", "warnings", "refreshed_at_utc"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"


def render_drift_table(report: dict[str, Any]) -> str:
    """Renderiza `drift_table` (movido del hub, plan 134b)."""
    lines = ["chile-hub drift", ""]
    lines.append(
        f"datasets={report.get('dataset_count', 0)} | "
        f"drifted={report.get('drifted_count', 0)} | "
        f"healthy={report.get('healthy_count', 0)} | "
        f"fallback={report.get('fallback_count', 0)} | "
        f"partial_coverage={report.get('partial_coverage_count', 0)} | "
        f"degraded={report.get('degraded_count', 0)}"
    )

    dataset_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("drift_status", "unknown"),
            entry.get("source_mode", "unknown"),
            entry.get("coverage_status", "unknown"),
            entry.get("degradation_status", "unknown"),
            str(entry.get("warning_count", 0)),
        ]
        for entry in report.get("datasets", [])
    ]
    lines.append("")
    lines.append(
        render_table(
            "",
            ["dataset", "drift", "mode", "coverage", "degradation", "warnings"],
            dataset_rows,
        )
    )
    return "\n".join(lines) + "\n"
