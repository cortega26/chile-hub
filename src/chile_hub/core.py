import argparse
import importlib.metadata
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .data_manager import ChileHubDataManager
from .pipeline_status_utils import (
    compute_freshness,
    compute_top_issue,
    format_top_issue_summary,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DATASET_CATALOG_PATH = NORMALIZED_DIR / "dataset_catalog.json"


class ChileHub:
    def __init__(
        self,
        catalog_path: str | Path | None = None,
        *,
        data_dir: str | Path | None = None,
        data_version: str = "latest",
        auto_update: bool = True,
    ) -> None:
        if catalog_path is not None and data_dir is not None:
            raise ValueError("Use catalog_path or data_dir, not both.")

        if catalog_path is not None:
            self.catalog_path = Path(catalog_path)
        elif data_dir is not None:
            self.catalog_path = Path(data_dir) / "dataset_catalog.json"
        elif DATASET_CATALOG_PATH.exists():
            self.catalog_path = DATASET_CATALOG_PATH
        else:
            manager = ChileHubDataManager(data_version=data_version)
            self.catalog_path = (
                manager.ensure_data_dir(auto_update=auto_update) / "dataset_catalog.json"
            )

        self.normalized_dir = self.catalog_path.resolve().parent
        self.root_dir = self.normalized_dir.parents[1]
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> dict[str, Any]:
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_artifact_manifest(self) -> dict[str, Any]:
        with (self.normalized_dir / "artifact_manifest.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_hub_health(self) -> dict[str, Any]:
        with (self.normalized_dir / "hub_health.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_hub_status(self) -> dict[str, Any]:
        with (self.normalized_dir / "hub_status.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_hub_bundle(self) -> dict[str, Any]:
        with (self.normalized_dir / "hub_bundle.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_redistribution_report(self) -> dict[str, Any]:
        with (self.normalized_dir / "redistribution_report.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_provenance_report(self) -> dict[str, Any]:
        with (self.normalized_dir / "provenance_report.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_drift_report(self) -> dict[str, Any]:
        with (self.normalized_dir / "drift_report.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _status_rank(status: str) -> int:
        return {"ok": 0, "warn": 1, "error": 2}.get(status, 1)

    @classmethod
    def _max_status(cls, *statuses: str) -> str:
        filtered = [status for status in statuses if status]
        if not filtered:
            return "unknown"
        return max(filtered, key=cls._status_rank)

    def top_issue(self) -> dict[str, Any] | None:
        provenance_by_dataset = {
            entry.get("dataset"): entry for entry in self.provenance().get("datasets", [])
        }
        drift_by_dataset = {
            entry.get("dataset"): entry for entry in self.drift().get("datasets", [])
        }
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in self.freshness_audit().get("datasets", [])
        }
        entries = []
        for entry in self.summary():
            dataset_name = entry.get("dataset")
            freshness_entry = freshness_by_dataset.get(dataset_name, {})
            provenance = provenance_by_dataset.get(dataset_name, {})
            drift = drift_by_dataset.get(dataset_name, {})
            current_freshness_status = freshness_entry.get("current_freshness_status", "unknown")
            entries.append(
                {
                    "dataset": dataset_name,
                    "warning_count": entry.get("warning_count", 0),
                    "freshness_status": current_freshness_status,
                    "build_freshness_status": entry.get("freshness_status"),
                    "current_freshness_status": current_freshness_status,
                    "drift_status": entry.get("drift_status"),
                    "degradation_status": entry.get("degradation_status"),
                    "source_detail": provenance.get("source_detail", "unknown"),
                    "diagnostic_summary": drift.get(
                        "diagnostic_summary",
                        provenance.get("diagnostic_summary", "Sin observaciones operativas."),
                    ),
                    "recommended_action": drift.get("recommended_action", "Ninguna."),
                }
            )

        return compute_top_issue(entries)

    def top_issue_table(self) -> str:
        top_issue = self.top_issue()
        lines = ["chile-hub top issue", ""]
        if not top_issue:
            lines.append("Sin top issue activo.")
            return "\n".join(lines) + "\n"

        rows = [
            ("dataset", top_issue.get("dataset", "unknown")),
            ("attention_priority", str(top_issue.get("attention_priority", "unknown"))),
            (
                "build_freshness_status",
                top_issue.get("build_freshness_status", "unknown"),
            ),
            (
                "current_freshness_status",
                top_issue.get("current_freshness_status", "unknown"),
            ),
            ("drift_status", top_issue.get("drift_status", "unknown")),
            ("degradation_status", top_issue.get("degradation_status", "unknown")),
            ("warning_count", str(top_issue.get("warning_count", 0))),
            ("source_detail", top_issue.get("source_detail", "unknown")),
            ("diagnostic_summary", top_issue.get("diagnostic_summary", "unknown")),
            ("recommended_action", top_issue.get("recommended_action", "unknown")),
        ]
        label_width = max(len(label) for label, _ in rows)
        lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)
        return "\n".join(lines) + "\n"

    def list_datasets(self) -> list[str]:
        return [entry["dataset"] for entry in self.catalog.get("datasets", [])]

    def get_dataset(self, dataset_name: str) -> dict[str, Any]:
        for entry in self.catalog.get("datasets", []):
            if entry["dataset"] == dataset_name:
                return entry
        available = ", ".join(self.list_datasets())
        raise KeyError(f"Dataset '{dataset_name}' no existe. Disponibles: {available}")

    def get_output_path(self, dataset_name: str, output_type: str = "parquet") -> Path:
        dataset = self.get_dataset(dataset_name)
        outputs = dataset.get("outputs", {})
        if output_type not in outputs:
            available = ", ".join(sorted(outputs.keys()))
            raise KeyError(
                f"Output '{output_type}' no existe para '{dataset_name}'. Disponibles: {available}"
            )
        return self.root_dir / outputs[output_type]

    def load_polars(self, dataset_name: str) -> pl.DataFrame:
        path = self.get_output_path(dataset_name, "parquet")
        return pl.read_parquet(path)

    def example_usage(self, dataset_name: str, kind: str = "python") -> str:
        dataset = self.get_dataset(dataset_name)
        examples = dataset.get("usage_examples", {})
        if kind not in examples:
            available = ", ".join(sorted(examples.keys()))
            raise KeyError(
                f"Example '{kind}' no existe para '{dataset_name}'. Disponibles: {available}"
            )
        return examples[kind]

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "dataset": entry["dataset"],
                "source_mode": entry["source_mode"],
                "record_count": entry["record_count"],
                "join_keys": entry.get("join_keys", []),
                "confidence_tier": entry.get("confidence_tier"),
                "reuse_status": entry.get("reuse_policy", {}).get("status"),
                "reuse_license": entry.get("reuse_policy", {}).get("license"),
                "attribution_required": entry.get("reuse_policy", {}).get("attribution_required"),
                "freshness_status": entry.get("freshness", {}).get("status"),
                "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                "coverage_status": entry.get("coverage", {}).get("status"),
                "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                "validation_status": entry.get("validation_status"),
                "warning_count": len(entry.get("warnings", [])),
                "drift_status": entry.get("drift", {}).get("status"),
                "drift_summary": entry.get("drift", {}).get("summary"),
                "degradation_status": entry.get("degradation", {}).get("status"),
                "degradation_impact": entry.get("degradation", {}).get("impact"),
            }
            for entry in self.catalog.get("datasets", [])
        ]

    def summary_table(self):
        rows = self.summary()
        lines = ["chile-hub summary", ""]
        lines.append(
            "dataset      mode      records  freshness  coverage        validation  drift     warnings"
        )
        lines.append(
            "-----------  --------  -------  ---------  --------------  ----------  --------  --------"
        )
        for entry in rows:
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{str(entry.get('record_count', 'N/D')):<7}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('validation_status', 'unknown'):<10}  "
                f"{entry.get('drift_status', 'unknown'):<8}  "
                f"{str(entry.get('warning_count', 0)):<8}"
            )
        return "\n".join(lines) + "\n"

    def snapshot_text(self):
        overview = self.overview()
        freshness_audit = self.freshness_audit()
        runtime_status = self.runtime_status_audit()
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

    def snapshot_table(self):
        overview = self.overview()
        freshness_audit = self.freshness_audit()
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
        lines.append("")
        lines.append(
            "dataset      mode      validation  build      current    coverage        drift"
        )
        lines.append(
            "-----------  --------  ----------  ---------  ---------  --------------  --------"
        )

        for entry in overview.get("datasets", []):
            runtime_freshness = freshness_by_dataset.get(entry.get("dataset"), {})
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('validation_status', 'unknown'):<10}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{runtime_freshness.get('current_freshness_status', 'unknown'):<9}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('drift_status', 'unknown'):<8}"
            )

        return "\n".join(lines) + "\n"

    def artifacts(self, dataset_name=None):
        manifest = self._load_artifact_manifest()
        artifacts = manifest.get("artifacts", [])
        if dataset_name is None:
            return artifacts

        self.get_dataset(dataset_name)
        return [entry for entry in artifacts if entry.get("dataset") == dataset_name]

    def shared_artifacts(self, shared_type=None, format=None):
        artifacts = [entry for entry in self.artifacts() if entry.get("shared_type")]
        if shared_type is not None:
            artifacts = [entry for entry in artifacts if entry.get("shared_type") == shared_type]
        if format is not None:
            artifacts = [entry for entry in artifacts if entry.get("format") == format]
        return artifacts

    def shared_artifacts_table(self, shared_type=None, format=None):
        artifacts = self.shared_artifacts(shared_type, format)
        lines = ["chile-hub shared artifacts", ""]
        lines.append("shared_type             format    size      path")
        lines.append(
            "----------------------  --------  --------  -----------------------------------------------"
        )
        for entry in artifacts:
            size_bytes = entry.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            lines.append(
                f"{entry.get('shared_type', 'unknown'):<22}  "
                f"{entry.get('format', 'unknown'):<8}  "
                f"{size_label:<8}  "
                f"{entry.get('path', 'unknown')}"
            )
        return "\n".join(lines) + "\n"

    def reports(self):
        return self.bundle().get("reports", {})

    def report_index(self):
        rows = []
        for report_key, entry in sorted(self.reports().items()):
            rows.append(
                {
                    "report_key": report_key,
                    "shared_type": entry.get("shared_type"),
                    "format": entry.get("format"),
                    "path": entry.get("path"),
                    "size_bytes": entry.get("size_bytes"),
                    "sha256": entry.get("sha256"),
                }
            )
        return rows

    def report_index_table(self):
        rows = self.report_index()
        lines = ["chile-hub report index", ""]
        lines.append("report_key              shared_type            format    size      path")
        lines.append(
            "----------------------  ---------------------  --------  --------  -----------------------------------------------"
        )
        for entry in rows:
            size_bytes = entry.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            lines.append(
                f"{entry.get('report_key', 'unknown'):<22}  "
                f"{entry.get('shared_type', 'unknown'):<21}  "
                f"{entry.get('format', 'unknown'):<8}  "
                f"{size_label:<8}  "
                f"{entry.get('path', 'unknown')}"
            )
        return "\n".join(lines) + "\n"

    def get_report(self, shared_type, format):
        for entry in self.reports().values():
            if entry.get("shared_type") == shared_type and entry.get("format") == format:
                return entry
        raise KeyError(f"Reporte '{shared_type}' con formato '{format}' no existe en el bundle.")

    def overview(self):
        health = self.health()
        bundle = self.bundle()
        packages = self.packages()
        runtime_status = self.runtime_status_audit()
        primary_package = None
        try:
            primary_package = self.primary_package()
        except KeyError:
            primary_package = None
        top_issue = self.top_issue()
        shared_artifacts = self.shared_artifacts()
        return {
            "generated_at_utc": health.get("generated_at_utc"),
            "overall_status": health.get("overall_status"),
            "build_overall_status": health.get("overall_status"),
            "current_overall_status": runtime_status.get("current_overall_status"),
            "dataset_count": health.get("dataset_count"),
            "live_count": health.get("live_count"),
            "fallback_count": health.get("fallback_count"),
            "stale_count": health.get("stale_count"),
            "drifted_count": health.get("drifted_count"),
            "degraded_count": health.get("degraded_count"),
            "partial_coverage_count": health.get("partial_coverage_count"),
            "warning_count": health.get("warning_count"),
            "current_fresh_count": runtime_status.get("fresh_count"),
            "current_stale_count": runtime_status.get("stale_count"),
            "current_unknown_count": runtime_status.get("unknown_count"),
            "current_checked_at_utc": runtime_status.get("checked_at_utc"),
            "top_issue": top_issue,
            "top_issue_summary": format_top_issue_summary(top_issue),
            "shared_artifact_count": len(shared_artifacts),
            "package_count": len(packages),
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
            "report_keys": sorted(bundle.get("reports", {}).keys()),
            "datasets": [
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "validation_status": entry.get("validation_status"),
                    "freshness_status": entry.get("freshness_status"),
                    "coverage_status": entry.get("coverage_status"),
                    "drift_status": entry.get("drift_status"),
                }
                for entry in health.get("datasets", [])
            ],
        }

    def overview_table(self):
        overview = self.overview()
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
        lines.append("")
        lines.append("dataset      mode      validation  build      coverage        drift")
        lines.append("-----------  --------  ----------  ---------  --------------  --------")
        for entry in overview.get("datasets", []):
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('validation_status', 'unknown'):<10}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('drift_status', 'unknown'):<8}"
            )
        return "\n".join(lines) + "\n"

    def inventory(self):
        inventory = []
        manifest_artifacts = self.artifacts()
        by_dataset = {}
        for artifact in manifest_artifacts:
            dataset = artifact.get("dataset")
            if not dataset:
                continue
            by_dataset.setdefault(dataset, []).append(artifact)

        for entry in self.catalog.get("datasets", []):
            dataset_name = entry["dataset"]
            artifacts = sorted(
                by_dataset.get(dataset_name, []),
                key=lambda item: (
                    item.get("output_type") or "",
                    item.get("path") or "",
                ),
            )
            published_outputs = [
                artifact["output_type"] for artifact in artifacts if artifact.get("output_type")
            ]
            inventory.append(
                {
                    "dataset": dataset_name,
                    "source_mode": entry.get("source_mode"),
                    "record_count": entry.get("record_count"),
                    "validation_status": entry.get("validation_status"),
                    "confidence_tier": entry.get("confidence_tier"),
                    "reuse_status": entry.get("reuse_policy", {}).get("status"),
                    "reuse_license": entry.get("reuse_policy", {}).get("license"),
                    "attribution_required": entry.get("reuse_policy", {}).get(
                        "attribution_required"
                    ),
                    "freshness_status": entry.get("freshness", {}).get("status"),
                    "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                    "coverage_status": entry.get("coverage", {}).get("status"),
                    "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                    "warning_count": len(entry.get("warnings", [])),
                    "drift_status": entry.get("drift", {}).get("status"),
                    "drift_summary": entry.get("drift", {}).get("summary"),
                    "degradation_status": entry.get("degradation", {}).get("status"),
                    "degradation_impact": entry.get("degradation", {}).get("impact"),
                    "published_outputs": published_outputs,
                    "artifact_count": len(artifacts),
                    "total_size_bytes": sum(
                        artifact.get("size_bytes", 0) for artifact in artifacts
                    ),
                    "artifacts": [
                        {
                            "path": artifact.get("path"),
                            "output_type": artifact.get("output_type"),
                            "size_bytes": artifact.get("size_bytes"),
                        }
                        for artifact in artifacts
                    ],
                }
            )
        return inventory

    def inventory_table(self):
        rows = self.inventory()
        lines = ["chile-hub inventory", ""]
        lines.append(
            "dataset      mode      records  outputs        size      freshness  coverage        drift"
        )
        lines.append(
            "-----------  --------  -------  -------------  --------  ---------  --------------  --------"
        )
        for entry in rows:
            outputs = ",".join(entry.get("published_outputs", [])) or "N/D"
            size_bytes = entry.get("total_size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{str(entry.get('record_count', 'N/D')):<7}  "
                f"{outputs:<13}  "
                f"{size_label:<8}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('drift_status', 'unknown'):<8}"
            )
        return "\n".join(lines) + "\n"

    def health(self):
        health = self._load_hub_health()
        if "top_issue_summary" not in health:
            health["top_issue_summary"] = format_top_issue_summary(health.get("top_issue"))
        return health

    def status(self):
        status = self._load_hub_status()
        if "top_issue_summary" not in status:
            status["top_issue_summary"] = format_top_issue_summary(status.get("top_issue"))
        return status

    def status_table(self):
        status = self.status()
        rows = [
            ("generated_at_utc", status.get("generated_at_utc", "unknown")),
            ("overall_status", status.get("overall_status", "unknown")),
            ("dataset_count", str(status.get("dataset_count", 0))),
            ("live_count", str(status.get("live_count", 0))),
            ("fallback_count", str(status.get("fallback_count", 0))),
            ("stale_count", str(status.get("stale_count", 0))),
            ("drifted_count", str(status.get("drifted_count", 0))),
            ("degraded_count", str(status.get("degraded_count", 0))),
            ("warning_count", str(status.get("warning_count", 0))),
        ]
        top_issue = status.get("top_issue")
        if top_issue:
            rows.extend(
                [
                    ("top_issue", top_issue.get("dataset", "unknown")),
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
                        status.get("top_issue_summary", format_top_issue_summary(top_issue)),
                    ),
                ]
            )
        label_width = max(len(label) for label, _ in rows)
        lines = ["chile-hub status", ""]
        lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)
        return "\n".join(lines) + "\n"

    def health_table(self):
        health = self.health()
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
        lines.append("")
        lines.append(
            "dataset      severity  mode      freshness  validation  reuse    coverage        drift     warnings"
        )
        lines.append(
            "-----------  --------  --------  ---------  ----------  -------  --------------  --------  --------"
        )
        for entry in health.get("datasets", []):
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('severity', 'unknown'):<8}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{entry.get('validation_status', 'unknown'):<10}  "
                f"{entry.get('publishability_status', 'unknown'):<7}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('drift_status', 'unknown'):<8}  "
                f"{str(entry.get('warning_count', 0)):<8}"
            )
        return "\n".join(lines) + "\n"

    def freshness_audit(self):
        checked_at = datetime.now(UTC)
        datasets = []
        fresh_count = 0
        stale_count = 0
        unknown_count = 0

        for entry in self.catalog.get("datasets", []):
            max_age_hours = entry.get("freshness_policy", {}).get("max_age_hours")
            freshness = compute_freshness(entry.get("refreshed_at_utc"), max_age_hours, checked_at)
            current_status = freshness["status"]

            if current_status == "fresh":
                fresh_count += 1
            elif current_status == "stale":
                stale_count += 1
            else:
                unknown_count += 1

            datasets.append(
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "refreshed_at_utc": entry.get("refreshed_at_utc"),
                    "build_freshness_status": entry.get("freshness", {}).get("status"),
                    "current_freshness_status": current_status,
                    "current_age_hours": freshness["age_hours"],
                    "max_age_hours": freshness["max_age_hours"],
                    "freshness_label": entry.get("freshness_policy", {}).get("label"),
                }
            )

        return {
            "checked_at_utc": checked_at.isoformat(),
            "dataset_count": len(datasets),
            "fresh_count": fresh_count,
            "stale_count": stale_count,
            "unknown_count": unknown_count,
            "datasets": datasets,
        }

    def runtime_status_audit(self):
        health = self.health()
        freshness_audit = self.freshness_audit()
        build_overall_status = health.get("overall_status", "unknown")
        runtime_freshness_status = "ok"
        if freshness_audit.get("unknown_count", 0) > 0 or freshness_audit.get("stale_count", 0) > 0:
            runtime_freshness_status = "warn"
        current_overall_status = self._max_status(build_overall_status, runtime_freshness_status)
        return {
            "build_overall_status": build_overall_status,
            "current_overall_status": current_overall_status,
            "fresh_count": freshness_audit.get("fresh_count", 0),
            "stale_count": freshness_audit.get("stale_count", 0),
            "unknown_count": freshness_audit.get("unknown_count", 0),
            "checked_at_utc": freshness_audit.get("checked_at_utc"),
        }

    def runtime_status(self):
        health = self.health()
        runtime_audit = self.runtime_status_audit()
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in self.freshness_audit().get("datasets", [])
        }
        datasets = []
        for entry in health.get("datasets", []):
            freshness_entry = freshness_by_dataset.get(entry.get("dataset"), {})
            datasets.append(
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "severity": entry.get("severity"),
                    "validation_status": entry.get("validation_status"),
                    "build_freshness_status": entry.get("freshness_status"),
                    "current_freshness_status": freshness_entry.get(
                        "current_freshness_status", "unknown"
                    ),
                    "current_age_hours": freshness_entry.get("current_age_hours"),
                    "max_age_hours": freshness_entry.get("max_age_hours"),
                    "coverage_status": entry.get("coverage_status"),
                    "drift_status": entry.get("drift_status"),
                    "warning_count": entry.get("warning_count", 0),
                }
            )
        top_issue = self.top_issue()
        return {
            "generated_at_utc": health.get("generated_at_utc"),
            "build_overall_status": runtime_audit.get("build_overall_status"),
            "current_overall_status": runtime_audit.get("current_overall_status"),
            "dataset_count": health.get("dataset_count"),
            "live_count": health.get("live_count"),
            "fallback_count": health.get("fallback_count"),
            "fresh_count": runtime_audit.get("fresh_count"),
            "stale_count": runtime_audit.get("stale_count"),
            "unknown_count": runtime_audit.get("unknown_count"),
            "drifted_count": health.get("drifted_count"),
            "warning_count": health.get("warning_count"),
            "checked_at_utc": runtime_audit.get("checked_at_utc"),
            "top_issue": top_issue,
            "top_issue_summary": format_top_issue_summary(top_issue),
            "datasets": datasets,
        }

    def runtime_status_table(self):
        runtime = self.runtime_status()
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
        lines.append("")
        lines.append(
            "dataset      mode      severity  build      current    age_h   max_h   coverage        drift     warnings"
        )
        lines.append(
            "-----------  --------  --------  ---------  ---------  ------  ------  --------------  --------  --------"
        )
        for entry in runtime.get("datasets", []):
            age = entry.get("current_age_hours")
            age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
            max_age = entry.get("max_age_hours")
            max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('severity', 'unknown'):<8}  "
                f"{entry.get('build_freshness_status', 'unknown'):<9}  "
                f"{entry.get('current_freshness_status', 'unknown'):<9}  "
                f"{age_label:<6}  "
                f"{max_age_label:<6}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('drift_status', 'unknown'):<8}  "
                f"{str(entry.get('warning_count', 0)):<8}"
            )
        return "\n".join(lines) + "\n"

    def freshness_audit_table(self):
        audit = self.freshness_audit()
        lines = ["chile-hub freshness audit", ""]
        lines.append(
            f"checked_at_utc={audit.get('checked_at_utc')} | "
            f"datasets={audit.get('dataset_count', 0)} | "
            f"fresh={audit.get('fresh_count', 0)} | "
            f"stale={audit.get('stale_count', 0)} | "
            f"unknown={audit.get('unknown_count', 0)}"
        )
        lines.append("")
        lines.append("dataset      mode      build      current    age_h   max_h   label")
        lines.append("-----------  --------  ---------  ---------  ------  ------  --------")
        for entry in audit.get("datasets", []):
            age = entry.get("current_age_hours")
            age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
            max_age = entry.get("max_age_hours")
            max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('build_freshness_status', 'unknown'):<9}  "
                f"{entry.get('current_freshness_status', 'unknown'):<9}  "
                f"{age_label:<6}  "
                f"{max_age_label:<6}  "
                f"{entry.get('freshness_label', 'N/D')}"
            )
        return "\n".join(lines) + "\n"

    def bundle(self):
        return self._load_hub_bundle()

    def packages(self):
        bundle_packages = self.bundle().get("packages", [])
        if bundle_packages:
            return bundle_packages
        manifest = self._load_artifact_manifest()
        return manifest.get("packages", [])

    def packages_table(self):
        packages = self.packages()
        lines = ["chile-hub packages", ""]
        lines.append("package_type  size      checksum  path")
        lines.append(
            "------------  --------  --------  -----------------------------------------------"
        )
        for package in packages:
            size_bytes = package.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            lines.append(
                f"{package.get('package_type', 'unknown'):<12}  "
                f"{size_label:<8}  "
                f"{package.get('checksum_algorithm', 'unknown'):<8}  "
                f"{package.get('path', 'unknown')}"
            )
        return "\n".join(lines) + "\n"

    def primary_package(self, package_type="zip"):
        for package in self.packages():
            if package.get("package_type") == package_type:
                return package
        raise KeyError(f"No existe package_type '{package_type}' en el hub.")

    def package_verification(self, package_type="zip"):
        package = self.primary_package(package_type)
        return {
            "path": package.get("path"),
            "package_type": package.get("package_type"),
            "checksum_algorithm": package.get("checksum_algorithm"),
            "checksum_path": package.get("checksum_path"),
            "verification_command": package.get("verification_command"),
            "sha256": package.get("sha256"),
            "size_bytes": package.get("size_bytes"),
        }

    def redistribution(self):
        return self._load_redistribution_report()

    def redistribution_table(self):
        report = self.redistribution()
        lines = ["chile-hub redistribution", ""]
        lines.append(
            f"ready={report.get('ready_count', 0)} | "
            f"review_terms={report.get('review_terms_count', 0)} | "
            f"unknown={report.get('unknown_count', 0)} | "
            f"datasets={report.get('dataset_count', 0)}"
        )
        lines.append("")
        lines.append("dataset      status         reuse_status       attribution  license")
        lines.append(
            "-----------  -------------  -----------------  -----------  ----------------------------------------"
        )
        for entry in report.get("datasets", []):
            attribution = "yes" if entry.get("attribution_required") else "no"
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('publishability_status', 'unknown'):<13}  "
                f"{entry.get('reuse_status', 'unknown'):<17}  "
                f"{attribution:<11}  "
                f"{entry.get('license', 'unknown')}"
            )
        return "\n".join(lines) + "\n"

    def provenance(self):
        return self._load_provenance_report()

    def provenance_table(self):
        report = self.provenance()
        lines = ["chile-hub provenance", ""]
        lines.append(
            f"datasets={report.get('dataset_count', 0)} | "
            f"live={report.get('live_count', 0)} | "
            f"fallback={report.get('fallback_count', 0)}"
        )
        lines.append("")
        lines.append(
            "dataset      mode      source                        freshness  warnings  refreshed_at_utc"
        )
        lines.append(
            "-----------  --------  ----------------------------  ---------  --------  --------------------------------"
        )
        for entry in report.get("datasets", []):
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('source_detail', 'unknown'):<28}  "
                f"{entry.get('freshness_status', 'unknown'):<9}  "
                f"{entry.get('warning_count', 0):<8}  "
                f"{entry.get('refreshed_at_utc', 'unknown')}"
            )
        return "\n".join(lines) + "\n"

    def drift(self):
        return self._load_drift_report()

    def drift_table(self):
        report = self.drift()
        lines = ["chile-hub drift", ""]
        lines.append(
            f"datasets={report.get('dataset_count', 0)} | "
            f"drifted={report.get('drifted_count', 0)} | "
            f"healthy={report.get('healthy_count', 0)} | "
            f"fallback={report.get('fallback_count', 0)} | "
            f"partial_coverage={report.get('partial_coverage_count', 0)} | "
            f"degraded={report.get('degraded_count', 0)}"
        )
        lines.append("")
        lines.append("dataset      drift      mode      coverage        degradation  warnings")
        lines.append("-----------  ---------  --------  --------------  -----------  --------")
        for entry in report.get("datasets", []):
            lines.append(
                f"{entry.get('dataset', 'unknown'):<11}  "
                f"{entry.get('drift_status', 'unknown'):<9}  "
                f"{entry.get('source_mode', 'unknown'):<8}  "
                f"{entry.get('coverage_status', 'unknown'):<14}  "
                f"{entry.get('degradation_status', 'unknown'):<11}  "
                f"{entry.get('warning_count', 0)}"
            )
        return "\n".join(lines) + "\n"


def build_parser():
    parser = argparse.ArgumentParser(description="CLI minima para inspeccionar chile-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Mostrar version instalada de chile-hub")

    cache_parser = subparsers.add_parser("cache", help="Administrar cache local de datos")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)
    cache_subparsers.add_parser("status", help="Mostrar estado del cache local")
    cache_update_parser = cache_subparsers.add_parser(
        "update", help="Descargar o actualizar artefactos normalizados"
    )
    cache_update_parser.add_argument(
        "--data-version",
        default="latest",
        help="Version de datos o tag de GitHub Release a descargar",
    )
    cache_subparsers.add_parser("clear", help="Eliminar cache local de chile-hub")

    subparsers.add_parser("list", help="Listar datasets disponibles")

    show_parser = subparsers.add_parser("show", help="Mostrar metadata de un dataset")
    show_parser.add_argument("dataset", help="Nombre del dataset")

    path_parser = subparsers.add_parser("path", help="Resolver path de salida de un dataset")
    path_parser.add_argument("dataset", help="Nombre del dataset")
    path_parser.add_argument(
        "--output",
        default="parquet",
        help="Tipo de output a resolver, por ejemplo parquet, json o sqlite_table",
    )

    example_parser = subparsers.add_parser("example", help="Mostrar ejemplo de uso de un dataset")
    example_parser.add_argument("dataset", help="Nombre del dataset")
    example_parser.add_argument(
        "--kind",
        default="python",
        help="Tipo de ejemplo a mostrar, por ejemplo python, duckdb o cli",
    )

    artifacts_parser = subparsers.add_parser("artifacts", help="Mostrar artefactos publicables")
    artifacts_parser.add_argument(
        "dataset",
        nargs="?",
        help="Nombre opcional de dataset para filtrar artefactos",
    )

    shared_artifacts_parser = subparsers.add_parser(
        "shared-artifacts", help="Mostrar artefactos compartidos del hub"
    )
    shared_artifacts_parser.add_argument("--shared-type", help="Filtrar por shared_type")
    shared_artifacts_parser.add_argument(
        "--artifact-format",
        help="Filtrar por formato de artifact, por ejemplo json o markdown",
    )
    shared_artifacts_parser.add_argument(
        "--output",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de shared-artifacts",
    )

    reports_parser = subparsers.add_parser("reports", help="Listar reportes compartidos del hub")
    reports_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del indice de reportes",
    )

    report_parser = subparsers.add_parser(
        "report", help="Resolver metadata de un reporte compartido"
    )
    report_parser.add_argument(
        "shared_type", help="shared_type del reporte, por ejemplo hub_health"
    )
    report_parser.add_argument(
        "--format",
        default="json",
        help="Formato del reporte, por ejemplo json o markdown",
    )

    inventory_parser = subparsers.add_parser(
        "inventory", help="Mostrar inventario compacto de datasets y artefactos"
    )
    inventory_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del inventario",
    )
    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Mostrar snapshot humano y compacto del hub"
    )
    snapshot_parser.add_argument(
        "--format",
        choices=["text", "table"],
        default="text",
        help="Formato de salida del snapshot",
    )
    overview_parser = subparsers.add_parser(
        "overview", help="Mostrar vista agregada compacta del hub"
    )
    overview_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de overview",
    )
    status_parser = subparsers.add_parser(
        "status", help="Mostrar status operativo compacto del hub"
    )
    status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de status",
    )
    health_parser = subparsers.add_parser("health", help="Mostrar salud agregada del hub")
    health_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de health",
    )
    subparsers.add_parser("bundle", help="Mostrar bundle consolidado del hub")
    freshness_audit_parser = subparsers.add_parser(
        "freshness-audit",
        help="Recalcular frescura contra el reloj actual sin reconstruir el hub",
    )
    freshness_audit_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de freshness-audit",
    )
    runtime_status_parser = subparsers.add_parser(
        "runtime-status",
        help="Combinar estado build y estado actual recalculado del hub",
    )
    runtime_status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de runtime-status",
    )
    top_issue_parser = subparsers.add_parser(
        "top-issue",
        help="Mostrar la capa prioritaria que requiere atención operativa",
    )
    top_issue_parser.add_argument(
        "--format",
        choices=["json", "text", "table"],
        default="json",
        help="Formato de salida de top-issue",
    )
    packages_parser = subparsers.add_parser("packages", help="Mostrar paquetes publicables del hub")
    packages_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de packages",
    )
    package_parser = subparsers.add_parser("package", help="Mostrar package principal del hub")
    package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    verify_package_parser = subparsers.add_parser(
        "verify-package",
        help="Mostrar metadata de verificación del package principal",
    )
    verify_package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    redistribution_parser = subparsers.add_parser(
        "redistribution", help="Mostrar inventario de redistribucion del hub"
    )
    redistribution_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de redistribution",
    )
    provenance_parser = subparsers.add_parser(
        "provenance", help="Mostrar inventario de procedencia del hub"
    )
    provenance_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de provenance",
    )
    drift_parser = subparsers.add_parser(
        "drift", help="Mostrar inventario de drift operativo del hub"
    )
    drift_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de drift",
    )

    summary_parser = subparsers.add_parser("summary", help="Mostrar resumen breve de datasets")
    summary_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del summary",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "version":
        try:
            version = importlib.metadata.version("chile-hub")
        except importlib.metadata.PackageNotFoundError:
            version = "0.1.0"
        print(version)
        return

    if args.command == "cache":
        manager = ChileHubDataManager(
            data_version=getattr(args, "data_version", "latest"),
        )
        if args.cache_command == "status":
            print(json.dumps(manager.status(), ensure_ascii=False, indent=2))
            return
        if args.cache_command == "update":
            data_dir = manager.ensure_data_dir(auto_update=True)
            print(data_dir)
            return
        if args.cache_command == "clear":
            manager.clear()
            print(manager.cache_root)
            return

    hub = ChileHub()

    if args.command == "list":
        for dataset in hub.list_datasets():
            print(dataset)
        return

    if args.command == "show":
        print(json.dumps(hub.get_dataset(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "path":
        print(hub.get_output_path(args.dataset, args.output))
        return

    if args.command == "example":
        print(hub.example_usage(args.dataset, args.kind))
        return

    if args.command == "artifacts":
        print(json.dumps(hub.artifacts(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "shared-artifacts":
        if args.output == "table":
            print(
                hub.shared_artifacts_table(args.shared_type, args.artifact_format),
                end="",
            )
        else:
            print(
                json.dumps(
                    hub.shared_artifacts(args.shared_type, args.artifact_format),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    if args.command == "reports":
        if args.format == "table":
            print(hub.report_index_table(), end="")
        else:
            print(json.dumps(hub.report_index(), ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        print(
            json.dumps(
                hub.get_report(args.shared_type, args.format),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "inventory":
        if args.format == "table":
            print(hub.inventory_table(), end="")
        else:
            print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))
        return

    if args.command == "snapshot":
        if args.format == "table":
            print(hub.snapshot_table(), end="")
        else:
            print(hub.snapshot_text(), end="")
        return

    if args.command == "overview":
        if args.format == "table":
            print(hub.overview_table(), end="")
        else:
            print(json.dumps(hub.overview(), ensure_ascii=False, indent=2))
        return

    if args.command == "status":
        if args.format == "table":
            print(hub.status_table(), end="")
        else:
            print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
        return

    if args.command == "health":
        if args.format == "table":
            print(hub.health_table(), end="")
        else:
            print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
        return

    if args.command == "bundle":
        print(json.dumps(hub.bundle(), ensure_ascii=False, indent=2))
        return

    if args.command == "freshness-audit":
        if args.format == "table":
            print(hub.freshness_audit_table(), end="")
        else:
            print(json.dumps(hub.freshness_audit(), ensure_ascii=False, indent=2))
        return

    if args.command == "runtime-status":
        if args.format == "table":
            print(hub.runtime_status_table(), end="")
        else:
            print(json.dumps(hub.runtime_status(), ensure_ascii=False, indent=2))
        return

    if args.command == "top-issue":
        top_issue = hub.top_issue()
        if args.format == "table":
            print(hub.top_issue_table(), end="")
        elif args.format == "text":
            if not top_issue:
                print("chile-hub top issue\n\nSin top issue activo.\n", end="")
            else:
                print(
                    "chile-hub top issue\n\n"
                    f"dataset={top_issue.get('dataset')} | "
                    f"build={top_issue.get('build_freshness_status', 'unknown')} | "
                    f"current={top_issue.get('current_freshness_status', 'unknown')} | "
                    f"drift={top_issue.get('drift_status', 'unknown')} | "
                    f"warnings={top_issue.get('warning_count', 0)} | "
                    f"source_detail={top_issue.get('source_detail', 'unknown')} | "
                    f"reason={top_issue.get('diagnostic_summary', 'unknown')} | "
                    f"action={top_issue.get('recommended_action', 'unknown')}\n",
                    end="",
                )
        else:
            print(json.dumps(top_issue, ensure_ascii=False, indent=2))
        return

    if args.command == "packages":
        if args.format == "table":
            print(hub.packages_table(), end="")
        else:
            print(json.dumps(hub.packages(), ensure_ascii=False, indent=2))
        return

    if args.command == "package":
        print(json.dumps(hub.primary_package(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "verify-package":
        print(json.dumps(hub.package_verification(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "redistribution":
        if args.format == "table":
            print(hub.redistribution_table(), end="")
        else:
            print(json.dumps(hub.redistribution(), ensure_ascii=False, indent=2))
        return

    if args.command == "provenance":
        if args.format == "table":
            print(hub.provenance_table(), end="")
        else:
            print(json.dumps(hub.provenance(), ensure_ascii=False, indent=2))
        return

    if args.command == "drift":
        if args.format == "table":
            print(hub.drift_table(), end="")
        else:
            print(json.dumps(hub.drift(), ensure_ascii=False, indent=2))
        return

    if args.command == "summary":
        if args.format == "table":
            print(hub.summary_table(), end="")
        else:
            print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
