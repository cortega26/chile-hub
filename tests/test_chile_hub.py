import json
import os
import subprocess
import sys
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chile_hub import ChileHub
from src.validation import validate_indicadores

# ── Staleness guard ───────────────────────────────────────────────────────────
_STAGING_DIR = ROOT_DIR / "data" / "staging"
_NORMALIZED_SENTINEL = ROOT_DIR / "data" / "normalized" / "pipeline_metadata.json"


def _assert_normalized_not_stale():
    """
    Fail fast if any staging metadata file is newer than the normalized
    pipeline_metadata.json sentinel.  This catches the common mistake of
    running an extractor and then running tests without rebuilding first.

    The check is intentionally lenient (1-second grace) to tolerate
    sub-second filesystem timestamp rounding on some platforms.
    """
    if not _NORMALIZED_SENTINEL.exists():
        raise AssertionError(
            "data/normalized/pipeline_metadata.json not found. "
            "Run 'make build' (or 'python src/build_dev_db.py') before pytest."
        )
    sentinel_mtime = _NORMALIZED_SENTINEL.stat().st_mtime
    stale_files = [
        p
        for p in _STAGING_DIR.glob("*.metadata.json")
        if p.stat().st_mtime > sentinel_mtime + 1  # 1-second grace
    ]
    if stale_files:
        names = ", ".join(sorted(p.name for p in stale_files))
        raise AssertionError(
            f"Normalized artifacts are older than staging metadata: [{names}]. "
            "Run 'make build' (or 'python src/build_dev_db.py') to rebuild, "
            "then re-run pytest."
        )


class ChileHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _assert_normalized_not_stale()
        cls.hub = ChileHub()
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"
        cls.catalog = cls.hub.catalog
        cls.catalog_by_dataset = {
            entry["dataset"]: entry for entry in cls.catalog.get("datasets", [])
        }
        cls.health = cls.hub.health()
        cls.bundle = cls.hub.bundle()

    def test_list_datasets(self):
        self.assertEqual(
            self.hub.list_datasets(),
            [
                "regiones",
                "provincias",
                "comunas",
                "comunas_enriquecidas",
                "indicadores",
                "censo_comunal",
                "establecimientos_salud",
                "establecimientos_educacionales",
                "censo_hogares_viviendas",
                "distritos_electorales",
            ],
        )

    def test_get_output_path(self):
        path = self.hub.get_output_path("comunas", "parquet")
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "comunas.parquet")

    def test_load_polars(self):
        df = self.hub.load_polars("comunas")
        self.assertEqual(df.height, self.catalog_by_dataset["comunas"]["record_count"])
        self.assertGreater(df.height, 0)
        self.assertIn("codigo_comuna", df.columns)

    def test_load_polars_regiones(self):
        df = self.hub.load_polars("regiones")
        self.assertEqual(df.height, self.catalog_by_dataset["regiones"]["record_count"])
        self.assertGreater(df.height, 0)
        self.assertIn("codigo_region", df.columns)

    def test_load_polars_comunas_enriquecidas(self):
        df = self.hub.load_polars("comunas_enriquecidas")
        self.assertEqual(df.height, self.catalog_by_dataset["comunas_enriquecidas"]["record_count"])
        self.assertGreater(df.filter(pl.col("latitud_cabecera") != 0.0).height, 300)
        self.assertGreater(df.filter(pl.col("poblacion_estimada") > 0).height, 300)

    def test_load_polars_new_layers(self):
        censo = self.hub.load_polars("censo_comunal")
        salud = self.hub.load_polars("establecimientos_salud")
        self.assertEqual(censo.height, 346)
        self.assertGreater(salud.height, 5000)
        self.assertEqual(censo["codigo_comuna"].str.len_chars().min(), 5)
        self.assertEqual(salud["codigo_comuna"].str.len_chars().min(), 5)

    def test_summary_statuses(self):
        summary = self.hub.summary()
        statuses = {item["dataset"]: item["validation_status"] for item in summary}
        self.assertEqual(
            statuses,
            {
                "regiones": "ok",
                "provincias": "ok",
                "comunas": "ok",
                "comunas_enriquecidas": "ok",
                "indicadores": "ok",
                "censo_comunal": "ok",
                "establecimientos_salud": "ok",
                "establecimientos_educacionales": "ok",
                "censo_hogares_viviendas": "ok",
                "distritos_electorales": "ok",
            },
        )
        warning_counts = {item["dataset"]: item["warning_count"] for item in summary}
        freshness_statuses = {item["dataset"]: item["freshness_status"] for item in summary}
        reuse_statuses = {item["dataset"]: item["reuse_status"] for item in summary}
        for dataset_name, entry in self.catalog_by_dataset.items():
            self.assertIn(freshness_statuses[dataset_name], {"fresh", "stale", "unknown"})
            self.assertEqual(warning_counts[dataset_name], len(entry.get("warnings", [])))
            self.assertEqual(
                reuse_statuses[dataset_name],
                entry.get("reuse_policy", {}).get("status"),
            )
            self.assertIn(
                next(item for item in summary if item["dataset"] == dataset_name)[
                    "coverage_status"
                ],
                {"full", "partial", "unknown", "not_applicable"},
            )
            self.assertIn(
                next(item for item in summary if item["dataset"] == dataset_name)["drift_status"],
                {"healthy", "drifted"},
            )
            self.assertIn(
                next(item for item in summary if item["dataset"] == dataset_name)[
                    "degradation_status"
                ],
                {"none", "warning", "degraded"},
            )

    def test_summary_table(self):
        table = self.hub.summary_table()
        self.assertIn("chile-hub summary", table)
        self.assertIn("dataset      mode      records", table)
        self.assertIn("comunas", table)
        self.assertIn("indicadores", table)

    def test_example_usage(self):
        example = self.hub.example_usage("comunas", "python")
        self.assertIn("ChileHub", example)
        self.assertIn("load_polars('comunas')", example)

    def test_artifacts_filtered_for_dataset(self):
        artifacts = self.hub.artifacts("comunas")
        paths = {artifact["path"] for artifact in artifacts}
        self.assertIn("data/normalized/comunas.parquet", paths)
        self.assertIn("data/normalized/comunas.json", paths)
        self.assertNotIn("data/normalized/indicadores.parquet", paths)

    def test_shared_artifacts_semantic_filtering(self):
        artifacts = self.hub.shared_artifacts("hub_health", "json")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["path"], "data/normalized/hub_health.json")
        status_artifacts = self.hub.shared_artifacts("hub_status", "json")
        self.assertEqual(len(status_artifacts), 1)
        self.assertEqual(status_artifacts[0]["path"], "data/normalized/hub_status.json")

    def test_get_report(self):
        report = self.hub.get_report("drift_report", "markdown")
        self.assertEqual(report["shared_type"], "drift_report")
        self.assertEqual(report["format"], "markdown")
        self.assertEqual(report["path"], "data/normalized/drift_report.md")
        overview_report = self.hub.get_report("overview", "json")
        self.assertEqual(overview_report["shared_type"], "overview")
        self.assertEqual(overview_report["format"], "json")
        self.assertEqual(overview_report["path"], "data/normalized/overview.json")
        status_report = self.hub.get_report("hub_status", "json")
        self.assertEqual(status_report["shared_type"], "hub_status")
        self.assertEqual(status_report["format"], "json")
        self.assertEqual(status_report["path"], "data/normalized/hub_status.json")

    def test_report_index(self):
        report_index = self.hub.report_index()
        report_keys = {entry["report_key"] for entry in report_index}
        self.assertIn("health_json", report_keys)
        self.assertIn("status_json", report_keys)
        self.assertIn("overview_markdown", report_keys)
        self.assertTrue(all(entry["shared_type"] for entry in report_index))
        self.assertTrue(all(entry["path"] for entry in report_index))

    def test_report_index_table(self):
        table = self.hub.report_index_table()
        self.assertIn("chile-hub report index", table)
        self.assertIn("report_key", table)
        self.assertIn("health_json", table)
        self.assertIn("status_json", table)
        self.assertIn("overview_markdown", table)

    def test_shared_artifacts_table(self):
        table = self.hub.shared_artifacts_table("hub_health", "json")
        self.assertIn("chile-hub shared artifacts", table)
        self.assertIn("hub_health", table)
        self.assertIn("data/normalized/hub_health.json", table)
        status_table = self.hub.shared_artifacts_table("hub_status", "json")
        self.assertIn("hub_status", status_table)
        self.assertIn("data/normalized/hub_status.json", status_table)

    def test_overview(self):
        overview = self.hub.overview()
        self.assertIn(overview["overall_status"], {"ok", "warn", "error"})
        self.assertIn(overview["build_overall_status"], {"ok", "warn", "error"})
        self.assertIn(overview["current_overall_status"], {"ok", "warn", "error"})
        self.assertEqual(overview["dataset_count"], 10)
        self.assertGreaterEqual(overview["shared_artifact_count"], 1)
        self.assertGreaterEqual(overview["package_count"], 1)
        self.assertEqual(
            overview["current_fresh_count"]
            + overview["current_stale_count"]
            + overview["current_unknown_count"],
            10,
        )
        self.assertTrue(overview["current_checked_at_utc"])
        self.assertIsNotNone(overview["top_issue"])
        self.assertEqual(overview["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", overview["top_issue_summary"])
        self.assertTrue(overview["top_issue"]["diagnostic_summary"])
        self.assertEqual(overview["primary_package"]["package_type"], "zip")
        self.assertEqual(
            overview["primary_package"]["checksum_path"],
            "data/normalized/chile-hub-publishable-bundle.zip.sha256",
        )
        self.assertEqual(
            overview["primary_package"]["verification_command"],
            "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
        )
        self.assertIn("health_json", overview["report_keys"])
        self.assertIn("status_json", overview["report_keys"])
        self.assertIn("drift_json", overview["report_keys"])
        self.assertEqual(len(overview["datasets"]), 10)

    def test_status(self):
        status = self.hub.status()
        self.assertIn(status["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(status["dataset_count"], 10)
        self.assertIsNotNone(status["top_issue"])
        self.assertEqual(status["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", status["top_issue_summary"])

    def test_status_table(self):
        table = self.hub.status_table()
        self.assertIn("chile-hub status", table)
        self.assertIn("overall_status", table)
        self.assertIn("top_issue", table)
        self.assertIn("top_issue_summary", table)
        self.assertIn("indicadores", table)

    def test_overview_table(self):
        table = self.hub.overview_table()
        self.assertIn("chile-hub overview", table)
        self.assertIn("build_overall_status", table)
        self.assertIn("current_overall_status", table)
        self.assertIn("top_issue", table)
        self.assertIn("top_issue_reason", table)
        self.assertIn("top_issue_action", table)
        self.assertIn("top_issue_summary", table)
        self.assertIn("dataset      mode      validation", table)
        self.assertIn("indicadores", table)

    def test_runtime_status_audit(self):
        audit = self.hub.runtime_status_audit()
        self.assertIn(audit["build_overall_status"], {"ok", "warn", "error"})
        self.assertIn(audit["current_overall_status"], {"ok", "warn", "error"})
        self.assertEqual(audit["fresh_count"] + audit["stale_count"] + audit["unknown_count"], 10)
        self.assertTrue(audit["checked_at_utc"])

    def test_runtime_status(self):
        runtime = self.hub.runtime_status()
        self.assertIn(runtime["build_overall_status"], {"ok", "warn", "error"})
        self.assertIn(runtime["current_overall_status"], {"ok", "warn", "error"})
        self.assertEqual(
            runtime["fresh_count"] + runtime["stale_count"] + runtime["unknown_count"],
            10,
        )
        self.assertEqual(runtime["dataset_count"], 10)
        self.assertEqual(len(runtime["datasets"]), 10)
        self.assertIsNotNone(runtime["top_issue"])
        self.assertEqual(runtime["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", runtime["top_issue_summary"])
        self.assertTrue(runtime["top_issue"]["diagnostic_summary"])
        indicadores = next(
            entry for entry in runtime["datasets"] if entry["dataset"] == "indicadores"
        )
        self.assertIn(indicadores["build_freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIn(indicadores["current_freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIn(
            indicadores["coverage_status"],
            {"full", "partial", "unknown", "not_applicable"},
        )
        self.assertIn(indicadores["drift_status"], {"healthy", "drifted"})

    def test_runtime_status_table(self):
        table = self.hub.runtime_status_table()
        self.assertIn("chile-hub runtime status", table)
        self.assertIn("build=", table)
        self.assertIn("current=", table)
        self.assertIn("top_issue_reason=", table)
        self.assertIn("top_issue_action=", table)
        self.assertIn("top_issue_summary=", table)
        self.assertIn("top_issue=indicadores", table)
        self.assertIn("dataset      mode      severity", table)
        self.assertIn("indicadores", table)

    def test_top_issue(self):
        top_issue = self.hub.top_issue()
        self.assertIsNotNone(top_issue)
        self.assertEqual(top_issue["dataset"], "indicadores")
        self.assertIn(top_issue["build_freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIn(top_issue["current_freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIn(top_issue["drift_status"], {"healthy", "drifted"})
        self.assertTrue(top_issue["diagnostic_summary"])

    def test_top_issue_table(self):
        table = self.hub.top_issue_table()
        self.assertIn("chile-hub top issue", table)
        self.assertIn("dataset", table)
        self.assertIn("source_detail", table)
        self.assertIn("diagnostic_summary", table)
        self.assertIn("recommended_action", table)
        self.assertIn("indicadores", table)

    def test_primary_package_and_verification(self):
        package = self.hub.primary_package()
        verification = self.hub.package_verification()
        self.assertEqual(package["package_type"], "zip")
        self.assertEqual(package["path"], "data/normalized/chile-hub-publishable-bundle.zip")
        self.assertEqual(verification["checksum_algorithm"], "sha256")
        self.assertEqual(
            verification["verification_command"],
            "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
        )
        self.assertEqual(verification["path"], package["path"])

    def test_packages_table(self):
        table = self.hub.packages_table()
        self.assertIn("chile-hub packages", table)
        self.assertIn("package_type", table)
        self.assertIn("zip", table)
        self.assertIn("data/normalized/chile-hub-publishable-bundle.zip", table)

    def test_snapshot_text(self):
        snapshot = self.hub.snapshot_text()
        self.assertIn("chile-hub snapshot", snapshot)
        self.assertIn(f"status_build: {self.health['overall_status']}", snapshot)
        self.assertIn("status_current:", snapshot)
        self.assertIn("current_freshness:", snapshot)
        self.assertIn("top_issue: indicadores", snapshot)
        self.assertIn("top_issue_reason:", snapshot)
        self.assertIn("top_issue_action:", snapshot)
        self.assertIn("package: data/normalized/chile-hub-publishable-bundle.zip", snapshot)
        self.assertIn(
            "verify: shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
            snapshot,
        )
        self.assertIn("- comunas:", snapshot)
        self.assertIn("freshness_build=", snapshot)
        self.assertIn("freshness_now=", snapshot)

    def test_snapshot_table(self):
        snapshot = self.hub.snapshot_table()
        self.assertIn("chile-hub snapshot table", snapshot)
        self.assertIn("build_overall_status", snapshot)
        self.assertIn("current_overall_status", snapshot)
        self.assertIn("current_fresh", snapshot)
        self.assertIn("current_stale", snapshot)
        self.assertIn("current_unknown", snapshot)
        self.assertIn("top_issue", snapshot)
        self.assertIn("top_issue_reason", snapshot)
        self.assertIn("top_issue_action", snapshot)
        self.assertIn("package_path", snapshot)
        self.assertIn("dataset      mode      validation  build      current", snapshot)
        self.assertIn("comunas", snapshot)

    def test_inventory_contains_artifact_types(self):
        inventory = self.hub.inventory()
        comunas = next(item for item in inventory if item["dataset"] == "comunas")
        self.assertEqual(comunas["published_outputs"], ["json", "parquet"])
        self.assertEqual(comunas["artifact_count"], 2)
        self.assertGreater(comunas["total_size_bytes"], 0)
        self.assertIn(comunas["freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIsInstance(comunas["freshness_age_hours"], float)
        self.assertEqual(
            comunas["warning_count"],
            len(self.catalog_by_dataset["comunas"].get("warnings", [])),
        )
        self.assertEqual(
            comunas["reuse_status"],
            self.catalog_by_dataset["comunas"].get("reuse_policy", {}).get("status"),
        )
        self.assertEqual(
            comunas["reuse_license"],
            self.catalog_by_dataset["comunas"].get("reuse_policy", {}).get("license"),
        )
        self.assertEqual(
            comunas["attribution_required"],
            self.catalog_by_dataset["comunas"].get("reuse_policy", {}).get("attribution_required"),
        )
        self.assertIn(comunas["coverage_status"], {"full", "partial", "unknown", "not_applicable"})
        self.assertIn(comunas["drift_status"], {"healthy", "drifted"})
        self.assertIn(comunas["degradation_status"], {"none", "warning", "degraded"})

    def test_inventory_table(self):
        table = self.hub.inventory_table()
        self.assertIn("chile-hub inventory", table)
        self.assertIn("dataset      mode      records", table)
        self.assertIn("comunas", table)
        self.assertIn("indicadores", table)

    def test_unknown_dataset_raises(self):
        with self.assertRaises(KeyError):
            self.hub.get_dataset("no-existe")

    def test_health_summary(self):
        health = self.health
        self.assertIn(health["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(health["dataset_count"], 10)
        self.assertEqual(health["ok_count"] + health["warn_count"] + health["error_count"], 10)
        self.assertEqual(
            health["publishable_count"]
            + health["review_terms_count"]
            + health["unknown_reuse_count"],
            10,
        )
        self.assertEqual(
            health["degraded_count"]
            + health["degradation_warning_count"]
            + sum(1 for entry in health["datasets"] if entry["degradation_status"] == "none"),
            10,
        )
        self.assertEqual(
            health["partial_coverage_count"]
            + health["unknown_coverage_count"]
            + sum(
                1
                for entry in health["datasets"]
                if entry["coverage_status"] in {"full", "not_applicable"}
            ),
            10,
        )
        self.assertEqual(
            health["drifted_count"]
            + sum(1 for entry in health["datasets"] if entry["drift_status"] == "healthy"),
            10,
        )

    def test_health_table(self):
        table = self.hub.health_table()
        self.assertIn("chile-hub health", table)
        self.assertIn(f"overall={self.health['overall_status']}", table)
        self.assertIn("dataset      severity  mode", table)
        self.assertIn("comunas", table)

    def test_freshness_audit(self):
        audit = self.hub.freshness_audit()
        self.assertEqual(audit["dataset_count"], 10)
        self.assertEqual(audit["fresh_count"] + audit["stale_count"] + audit["unknown_count"], 10)
        indicadores = next(
            entry for entry in audit["datasets"] if entry["dataset"] == "indicadores"
        )
        refreshed_at = datetime.fromisoformat(indicadores["refreshed_at_utc"]).astimezone(UTC)
        age_hours = max((datetime.now(UTC) - refreshed_at).total_seconds() / 3600, 0)
        expected_status = "fresh" if age_hours <= indicadores["max_age_hours"] else "stale"
        self.assertEqual(indicadores["current_freshness_status"], expected_status)

    def test_freshness_audit_table(self):
        table = self.hub.freshness_audit_table()
        self.assertIn("chile-hub freshness audit", table)
        self.assertIn("dataset      mode      build", table)
        self.assertIn("indicadores", table)

    def test_bundle_summary(self):
        bundle = self.bundle
        self.assertEqual(bundle["overall_status"], self.health["overall_status"])
        self.assertEqual(bundle["dataset_count"], 10)
        self.assertEqual(len(bundle["datasets"]), 10)
        self.assertEqual(
            bundle["reports"]["health_json"]["path"], "data/normalized/hub_health.json"
        )
        self.assertEqual(
            bundle["reports"]["provenance_json"]["path"],
            "data/normalized/provenance_report.json",
        )
        self.assertEqual(
            bundle["reports"]["overview_json"]["path"], "data/normalized/overview.json"
        )
        self.assertEqual(
            bundle["reports"]["overview_markdown"]["path"],
            "data/normalized/overview.md",
        )
        self.assertEqual(bundle["health"]["publishable_count"], self.health["publishable_count"])
        self.assertEqual(bundle["health"]["review_terms_count"], self.health["review_terms_count"])
        self.assertEqual(
            bundle["health"]["partial_coverage_count"],
            self.health["partial_coverage_count"],
        )
        self.assertEqual(bundle["health"]["drifted_count"], self.health["drifted_count"])
        self.assertIsNotNone(bundle["top_issue"])
        self.assertEqual(bundle["top_issue"]["dataset"], "indicadores")
        self.assertEqual(bundle["health"]["top_issue"]["dataset"], "indicadores")
        self.assertEqual(bundle["packages"][0]["package_type"], "zip")
        self.assertEqual(bundle["packages"][0]["checksum_algorithm"], "sha256")
        self.assertTrue(bundle["packages"][0]["checksum_path"].endswith(".sha256"))
        self.assertEqual(
            bundle["packages"][0]["verification_command"],
            "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
        )
        comunas = next(entry for entry in bundle["datasets"] if entry["dataset"] == "comunas")
        self.assertIn(comunas["severity"], {"ok", "warn", "error"})
        self.assertTrue(comunas["artifacts"])
        self.assertTrue(comunas["source_detail"])
        self.assertTrue(comunas["refreshed_at_utc"])
        self.assertEqual(
            comunas["reuse_policy"]["status"],
            self.catalog_by_dataset["comunas"]["reuse_policy"]["status"],
        )
        self.assertIn(comunas["publishability_status"], {"ready", "review_terms", "unknown"})
        self.assertIn(
            comunas["coverage"]["status"],
            {"full", "partial", "unknown", "not_applicable"},
        )
        self.assertIn(comunas["drift"]["status"], {"healthy", "drifted"})
        self.assertIn(comunas["degradation"]["status"], {"none", "warning", "degraded"})
        indicadores = next(
            entry for entry in bundle["datasets"] if entry["dataset"] == "indicadores"
        )
        self.assertTrue(indicadores["source_detail"])
        self.assertTrue(indicadores["refreshed_at_utc"])
        self.assertEqual(
            indicadores["reuse_policy"]["status"],
            self.catalog_by_dataset["indicadores"]["reuse_policy"]["status"],
        )
        self.assertIn(indicadores["publishability_status"], {"ready", "review_terms", "unknown"})

    def test_redistribution_report(self):
        report = self.hub.redistribution()
        self.assertEqual(report["dataset_count"], 10)
        self.assertEqual(
            report["ready_count"] + report["review_terms_count"] + report["unknown_count"],
            10,
        )
        indicadores = next(
            entry for entry in report["datasets"] if entry["dataset"] == "indicadores"
        )
        self.assertIn(indicadores["publishability_status"], {"ready", "review_terms", "unknown"})
        self.assertTrue(indicadores["recommended_action"])

    def test_redistribution_table(self):
        table = self.hub.redistribution_table()
        self.assertIn("chile-hub redistribution", table)
        self.assertIn("ready=", table)
        self.assertIn("dataset      status", table)
        self.assertIn("indicadores", table)

    def test_provenance_report(self):
        report = self.hub.provenance()
        self.assertEqual(report["dataset_count"], 10)
        self.assertEqual(report["live_count"] + report["fallback_count"], 10)
        comunas = next(entry for entry in report["datasets"] if entry["dataset"] == "comunas")
        self.assertTrue(comunas["source_name"])
        self.assertTrue(comunas["source_detail"])
        self.assertIn(comunas["freshness_status"], {"fresh", "stale", "unknown"})
        indicadores = next(
            entry for entry in report["datasets"] if entry["dataset"] == "indicadores"
        )
        self.assertGreaterEqual(indicadores["warning_count"], 1)
        self.assertTrue(indicadores["diagnostic_summary"])

    def test_provenance_table(self):
        table = self.hub.provenance_table()
        self.assertIn("chile-hub provenance", table)
        self.assertIn("dataset      mode      source", table)
        self.assertIn("warnings", table)
        self.assertIn("comunas", table)

    def test_drift_report(self):
        report = self.hub.drift()
        self.assertEqual(report["dataset_count"], 10)
        self.assertEqual(report["drifted_count"] + report["healthy_count"], 10)
        comunas = next(entry for entry in report["datasets"] if entry["dataset"] == "comunas")
        self.assertIn(comunas["drift_status"], {"healthy", "drifted"})
        self.assertIn(comunas["coverage_status"], {"full", "partial", "unknown", "not_applicable"})
        self.assertIn(comunas["degradation_status"], {"none", "warning", "degraded"})
        self.assertTrue(comunas["recommended_action"])
        indicadores = next(
            entry for entry in report["datasets"] if entry["dataset"] == "indicadores"
        )
        self.assertGreaterEqual(indicadores["warning_count"], 1)
        self.assertTrue(indicadores["diagnostic_summary"])

    def test_drift_table(self):
        table = self.hub.drift_table()
        self.assertIn("chile-hub drift", table)
        self.assertIn("dataset      drift      mode", table)
        self.assertIn("warnings", table)
        self.assertIn("indicadores", table)

    def test_validate_indicadores_warns_on_partial_live_refresh_recovery(self):
        df = self.hub.load_polars("indicadores")
        result = validate_indicadores(
            df,
            {
                "source_mode": "live",
                "empty_live_pairs": ["ipc/2026"],
                "published_backfills": ["ipc"],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn(
            "indicadores live refresh returned empty series for: ipc/2026",
            result["warnings"],
        )
        self.assertIn(
            "indicadores live refresh reused last published artifact for missing codes: ipc",
            result["warnings"],
        )


class ArtifactContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _assert_normalized_not_stale()
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"
        cls.catalog = json.loads((cls.normalized_dir / "dataset_catalog.json").read_text())
        cls.manifest = json.loads((cls.normalized_dir / "artifact_manifest.json").read_text())
        cls.health = json.loads((cls.normalized_dir / "hub_health.json").read_text())
        cls.bundle = json.loads((cls.normalized_dir / "hub_bundle.json").read_text())
        cls.overview = json.loads((cls.normalized_dir / "overview.json").read_text())
        cls.health_markdown = (cls.normalized_dir / "hub_health.md").read_text()
        cls.overview_markdown = (cls.normalized_dir / "overview.md").read_text()
        cls.pipeline_status_markdown = (cls.normalized_dir / "pipeline_status.md").read_text()

    def test_catalog_dataset_count(self):
        self.assertEqual(self.catalog["dataset_count"], 10)

    def test_manifest_contains_expected_publishable_files(self):
        artifact_paths = {entry["path"] for entry in self.manifest["artifacts"]}
        self.assertIn("data/normalized/dataset_catalog.json", artifact_paths)
        self.assertIn("data/normalized/pipeline_status.md", artifact_paths)
        self.assertIn("data/normalized/hub_health.json", artifact_paths)
        self.assertIn("data/normalized/hub_status.json", artifact_paths)
        self.assertIn("data/normalized/hub_health.md", artifact_paths)
        self.assertIn("data/normalized/hub_bundle.json", artifact_paths)
        self.assertIn("data/normalized/redistribution_report.json", artifact_paths)
        self.assertIn("data/normalized/redistribution_report.md", artifact_paths)
        self.assertIn("data/normalized/provenance_report.json", artifact_paths)
        self.assertIn("data/normalized/provenance_report.md", artifact_paths)
        self.assertIn("data/normalized/drift_report.json", artifact_paths)
        self.assertIn("data/normalized/drift_report.md", artifact_paths)
        self.assertIn("data/normalized/overview.json", artifact_paths)
        self.assertIn("data/normalized/overview.md", artifact_paths)
        self.assertIn("data/normalized/regiones.parquet", artifact_paths)
        self.assertIn("data/normalized/provincias.parquet", artifact_paths)
        self.assertIn("data/normalized/comunas.parquet", artifact_paths)

    def test_manifest_dataset_metadata_present_for_dataset_outputs(self):
        by_path = {entry["path"]: entry for entry in self.manifest["artifacts"]}
        self.assertEqual(by_path["data/normalized/comunas.parquet"]["dataset"], "comunas")
        self.assertEqual(by_path["data/normalized/comunas.parquet"]["output_type"], "parquet")
        self.assertEqual(by_path["data/normalized/indicadores_hoy.json"]["dataset"], "indicadores")
        self.assertEqual(by_path["data/normalized/indicadores_hoy.json"]["output_type"], "json")
        self.assertEqual(by_path["data/normalized/hub_health.json"]["shared_type"], "hub_health")
        self.assertEqual(by_path["data/normalized/hub_health.json"]["format"], "json")
        self.assertEqual(by_path["data/normalized/hub_status.json"]["shared_type"], "hub_status")
        self.assertEqual(by_path["data/normalized/hub_status.json"]["format"], "json")
        self.assertEqual(by_path["data/normalized/drift_report.md"]["shared_type"], "drift_report")
        self.assertEqual(by_path["data/normalized/drift_report.md"]["format"], "markdown")
        self.assertEqual(by_path["data/normalized/overview.json"]["shared_type"], "overview")
        self.assertEqual(by_path["data/normalized/overview.json"]["format"], "json")

    def test_catalog_usage_examples_present(self):
        for dataset in self.catalog["datasets"]:
            examples = dataset.get("usage_examples", {})
            self.assertIn("python", examples)
            self.assertIn("duckdb", examples)
            self.assertIn("cli", examples)

    def test_catalog_reuse_policy_present(self):
        for dataset in self.catalog["datasets"]:
            reuse_policy = dataset.get("reuse_policy", {})
            self.assertIn(
                reuse_policy.get("status"),
                {"open-attribution", "public-api-review-terms"},
            )
            self.assertTrue(reuse_policy.get("license"))
            self.assertTrue(reuse_policy.get("summary"))

    def test_catalog_freshness_present(self):
        for dataset in self.catalog["datasets"]:
            self.assertIn(
                dataset.get("freshness", {}).get("status"),
                {"fresh", "stale", "unknown"},
            )
            self.assertTrue(dataset.get("freshness_policy", {}).get("max_age_hours"))
            if dataset.get("freshness", {}).get("status") in {"stale", "unknown"}:
                self.assertGreater(len(dataset.get("warnings", [])), 0)

    def test_catalog_coverage_present(self):
        for dataset in self.catalog["datasets"]:
            coverage = dataset.get("coverage", {})
            self.assertIn(coverage.get("status"), {"full", "partial", "unknown", "not_applicable"})
            self.assertTrue(coverage.get("summary"))

    def test_catalog_drift_present(self):
        for dataset in self.catalog["datasets"]:
            drift = dataset.get("drift", {})
            self.assertIn(drift.get("status"), {"healthy", "drifted"})
            self.assertTrue(drift.get("summary"))

    def test_manifest_hashes_present(self):
        for artifact in self.manifest["artifacts"]:
            self.assertTrue(artifact["sha256"])
            self.assertGreater(artifact["size_bytes"], 0)
        self.assertEqual(self.manifest["packages"][0]["package_type"], "zip")
        self.assertEqual(self.manifest["packages"][0]["checksum_algorithm"], "sha256")
        self.assertTrue(self.manifest["packages"][0]["checksum_path"].endswith(".sha256"))
        self.assertEqual(
            self.manifest["packages"][0]["verification_command"],
            "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
        )

    def test_publishable_zip_exists_and_contains_bundle(self):
        zip_path = self.normalized_dir / "chile-hub-publishable-bundle.zip"
        checksum_path = self.normalized_dir / "chile-hub-publishable-bundle.zip.sha256"
        self.assertTrue(zip_path.exists())
        self.assertTrue(checksum_path.exists())
        with zipfile.ZipFile(zip_path) as archive:
            names = set(archive.namelist())
        self.assertIn("data/normalized/hub_status.json", names)
        self.assertIn("data/normalized/hub_bundle.json", names)
        self.assertIn("data/normalized/artifact_manifest.json", names)
        self.assertIn("data/normalized/overview.json", names)

    def test_top_issue_is_persisted_in_shared_artifacts(self):
        self.assertIsNotNone(self.health["top_issue"])
        self.assertEqual(self.health["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", self.health["top_issue_summary"])
        self.assertTrue(self.health["top_issue"]["diagnostic_summary"])
        self.assertEqual(
            self.health["top_issue"]["source_detail"],
            "public_api_with_published_backfill",
        )
        self.assertIsNotNone(self.bundle["top_issue"])
        self.assertEqual(self.bundle["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", self.bundle["top_issue_summary"])
        self.assertTrue(self.bundle["top_issue"]["diagnostic_summary"])
        self.assertEqual(self.bundle["health"]["top_issue"]["dataset"], "indicadores")
        self.assertIn(
            "public_api_with_published_backfill",
            self.bundle["health"]["top_issue_summary"],
        )
        self.assertTrue(self.bundle["health"]["top_issue"]["diagnostic_summary"])
        self.assertIsNotNone(self.overview["top_issue"])
        self.assertEqual(self.overview["top_issue"]["dataset"], "indicadores")
        self.assertIn("public_api_with_published_backfill", self.overview["top_issue_summary"])
        self.assertTrue(self.overview["top_issue"]["diagnostic_summary"])

    def test_top_issue_is_exposed_in_markdown_reports(self):
        self.assertIn("- `top_issue`: `indicadores`", self.overview_markdown)
        self.assertIn("- `top_issue`: `indicadores`", self.pipeline_status_markdown)
        self.assertIn("- `top_issue_reason`:", self.overview_markdown)
        self.assertIn("- `top_issue_reason`:", self.health_markdown)
        self.assertIn("- `top_issue_reason`:", self.pipeline_status_markdown)
        self.assertIn("- `top_issue_action`:", self.overview_markdown)
        self.assertIn("- `top_issue_action`:", self.health_markdown)
        self.assertIn("- `top_issue_action`:", self.pipeline_status_markdown)
        self.assertIn("- `top_issue_summary`:", self.overview_markdown)
        self.assertIn("- `top_issue_summary`:", self.health_markdown)
        self.assertIn("- `top_issue_summary`:", self.pipeline_status_markdown)
        self.assertIn(
            "- `hub_status_json`: `data/normalized/hub_status.json`",
            self.pipeline_status_markdown,
        )
        self.assertIn("- `warning_count`:", self.pipeline_status_markdown or "")

    def test_indicadores_partial_refresh_contract_is_published(self):
        indicadores_catalog = next(
            dataset for dataset in self.catalog["datasets"] if dataset["dataset"] == "indicadores"
        )
        self.assertEqual(indicadores_catalog["source_detail"], "public_api_with_published_backfill")
        self.assertEqual(
            indicadores_catalog["indicator_codes"],
            ["dolar", "euro", "ipc", "uf", "utm"],
        )
        self.assertEqual(indicadores_catalog["indicator_delivery"]["ipc"], "published_backfill")
        # "uf" must not be synthetic fallback data; "preserved_existing" is acceptable
        # when the live fetch had a transient failure for that indicator-year pair.
        self.assertIn(
            indicadores_catalog["indicator_delivery"]["uf"],
            {"live", "raw_recovery", "preserved_existing"},
        )
        self.assertIn("published_backfills_used_for_codes: ipc", indicadores_catalog["notes"])
        self.assertIn(
            "indicadores live refresh reused last published artifact for missing codes: ipc",
            indicadores_catalog["warnings"],
        )
        provenance = self.bundle["reports"]["provenance_json"]["path"]
        drift = self.bundle["reports"]["drift_json"]["path"]
        self.assertEqual(provenance, "data/normalized/provenance_report.json")
        self.assertEqual(drift, "data/normalized/drift_report.json")


class ChileHubCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.health = ChileHub().health()

    def run_cli(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        return subprocess.run(
            [sys.executable, "-m", "chile_hub", *args],
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_script(self, script_path):
        return subprocess.run(
            [sys.executable, script_path],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_cli_list(self):
        result = self.run_cli("list")
        self.assertEqual(
            result.stdout.strip().splitlines(),
            [
                "regiones",
                "provincias",
                "comunas",
                "comunas_enriquecidas",
                "indicadores",
                "censo_comunal",
                "establecimientos_salud",
                "establecimientos_educacionales",
                "censo_hogares_viviendas",
                "distritos_electorales",
            ],
        )

    def test_cli_summary_table(self):
        result = self.run_cli("summary", "--format", "table")
        self.assertIn("chile-hub summary", result.stdout)
        self.assertIn("dataset      mode      records", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_path(self):
        result = self.run_cli("path", "comunas", "--output", "parquet")
        self.assertTrue(result.stdout.strip().endswith("data/normalized/comunas.parquet"))

    def test_cli_example(self):
        result = self.run_cli("example", "indicadores", "--kind", "duckdb")
        self.assertIn("data/normalized/indicadores.parquet", result.stdout)

    def test_cli_artifacts(self):
        result = self.run_cli("artifacts", "regiones")
        self.assertIn("data/normalized/regiones.parquet", result.stdout)
        self.assertIn("data/normalized/regiones.json", result.stdout)

    def test_cli_shared_artifacts(self):
        result = self.run_cli(
            "shared-artifacts",
            "--shared-type",
            "hub_health",
            "--artifact-format",
            "json",
        )
        self.assertIn('"shared_type": "hub_health"', result.stdout)
        self.assertIn('"path": "data/normalized/hub_health.json"', result.stdout)

    def test_cli_shared_artifacts_table(self):
        result = self.run_cli(
            "shared-artifacts",
            "--shared-type",
            "hub_health",
            "--artifact-format",
            "json",
            "--output",
            "table",
        )
        self.assertIn("chile-hub shared artifacts", result.stdout)
        self.assertIn("hub_health", result.stdout)
        self.assertIn("data/normalized/hub_health.json", result.stdout)

    def test_cli_reports(self):
        result = self.run_cli("reports")
        self.assertIn('"report_key": "health_json"', result.stdout)
        self.assertIn('"report_key": "status_json"', result.stdout)
        self.assertIn('"report_key": "overview_markdown"', result.stdout)

    def test_cli_reports_table(self):
        result = self.run_cli("reports", "--format", "table")
        self.assertIn("chile-hub report index", result.stdout)
        self.assertIn("health_json", result.stdout)
        self.assertIn("status_json", result.stdout)
        self.assertIn("overview_markdown", result.stdout)

    def test_cli_report(self):
        result = self.run_cli("report", "drift_report", "--format", "markdown")
        self.assertIn('"shared_type": "drift_report"', result.stdout)
        self.assertIn('"path": "data/normalized/drift_report.md"', result.stdout)
        overview_result = self.run_cli("report", "overview", "--format", "json")
        self.assertIn('"shared_type": "overview"', overview_result.stdout)
        self.assertIn('"path": "data/normalized/overview.json"', overview_result.stdout)

    def test_cli_inventory(self):
        result = self.run_cli("inventory")
        self.assertIn('"dataset": "comunas"', result.stdout)
        self.assertIn('"published_outputs": [', result.stdout)
        self.assertIn('"artifact_count": 2', result.stdout)
        self.assertIn('"freshness_status":', result.stdout)
        self.assertIn('"coverage_status":', result.stdout)
        self.assertIn('"warning_count":', result.stdout)
        self.assertIn('"drift_status":', result.stdout)
        self.assertIn('"reuse_status":', result.stdout)
        self.assertIn('"degradation_status":', result.stdout)

    def test_cli_inventory_table(self):
        result = self.run_cli("inventory", "--format", "table")
        self.assertIn("chile-hub inventory", result.stdout)
        self.assertIn("dataset      mode      records", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_snapshot(self):
        result = self.run_cli("snapshot")
        self.assertIn("chile-hub snapshot", result.stdout)
        self.assertIn(f"status_build: {self.health['overall_status']}", result.stdout)
        self.assertIn("status_current:", result.stdout)
        self.assertIn("current_freshness:", result.stdout)
        self.assertIn("top_issue: indicadores", result.stdout)
        self.assertIn("top_issue_reason:", result.stdout)
        self.assertIn("top_issue_action:", result.stdout)
        self.assertIn("package: data/normalized/chile-hub-publishable-bundle.zip", result.stdout)
        self.assertIn(
            "verify: shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256",
            result.stdout,
        )

    def test_cli_status(self):
        result = self.run_cli("status")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"top_issue": {', result.stdout)
        self.assertIn('"top_issue_summary":', result.stdout)

    def test_cli_status_table(self):
        result = self.run_cli("status", "--format", "table")
        self.assertIn("chile-hub status", result.stdout)
        self.assertIn("overall_status", result.stdout)
        self.assertIn("top_issue", result.stdout)
        self.assertIn("top_issue_summary", result.stdout)

    def test_cli_snapshot_table(self):
        result = self.run_cli("snapshot", "--format", "table")
        self.assertIn("chile-hub snapshot table", result.stdout)
        self.assertIn("build_overall_status", result.stdout)
        self.assertIn("current_overall_status", result.stdout)
        self.assertIn("top_issue", result.stdout)
        self.assertIn("current_fresh", result.stdout)
        self.assertIn("dataset      mode      validation  build      current", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_overview(self):
        result = self.run_cli("overview")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"top_issue": {', result.stdout)
        self.assertIn('"shared_artifact_count":', result.stdout)
        self.assertIn('"primary_package": {', result.stdout)
        self.assertIn(
            '"verification_command": "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"',
            result.stdout,
        )
        self.assertIn('"report_keys":', result.stdout)

    def test_cli_overview_table(self):
        result = self.run_cli("overview", "--format", "table")
        self.assertIn("chile-hub overview", result.stdout)
        self.assertIn("build_overall_status", result.stdout)
        self.assertIn("current_overall_status", result.stdout)
        self.assertIn("top_issue", result.stdout)
        self.assertIn("top_issue_reason", result.stdout)
        self.assertIn("top_issue_action", result.stdout)
        self.assertIn("top_issue_summary", result.stdout)
        self.assertIn("dataset      mode      validation", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_health(self):
        result = self.run_cli("health")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"dataset_count": 10', result.stdout)
        self.assertIn('"review_terms_count":', result.stdout)
        self.assertIn('"partial_coverage_count":', result.stdout)
        self.assertIn('"drifted_count":', result.stdout)

    def test_cli_health_table(self):
        result = self.run_cli("health", "--format", "table")
        self.assertIn("chile-hub health", result.stdout)
        self.assertIn(f"overall={self.health['overall_status']}", result.stdout)
        self.assertIn("dataset      severity  mode", result.stdout)

    def test_pipeline_status_script_text(self):
        result = self.run_script("scripts/pipeline_status.py")
        self.assertIn("chile-hub pipeline status", result.stdout)
        self.assertIn("top_issue: indicadores", result.stdout)
        self.assertIn("top_issue_reason:", result.stdout)
        self.assertIn("top_issue_action:", result.stdout)
        self.assertIn("hub_status_json: data/normalized/hub_status.json", result.stdout)

    def test_cli_bundle(self):
        result = self.run_cli("bundle")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"shared_artifacts"', result.stdout)
        self.assertIn('"reports"', result.stdout)

    def test_cli_freshness_audit_table(self):
        result = self.run_cli("freshness-audit", "--format", "table")
        self.assertIn("chile-hub freshness audit", result.stdout)
        self.assertIn("dataset      mode      build", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_runtime_status(self):
        result = self.run_cli("runtime-status")
        self.assertIn('"build_overall_status":', result.stdout)
        self.assertIn('"current_overall_status":', result.stdout)
        self.assertIn('"top_issue": {', result.stdout)
        self.assertIn('"checked_at_utc":', result.stdout)
        self.assertIn('"dataset": "indicadores"', result.stdout)

    def test_cli_runtime_status_table(self):
        result = self.run_cli("runtime-status", "--format", "table")
        self.assertIn("chile-hub runtime status", result.stdout)
        self.assertIn("build=", result.stdout)
        self.assertIn("current=", result.stdout)
        self.assertIn("top_issue_reason=", result.stdout)
        self.assertIn("top_issue_action=", result.stdout)
        self.assertIn("top_issue_summary=", result.stdout)
        self.assertIn("dataset      mode      severity", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_top_issue(self):
        result = self.run_cli("top-issue")
        self.assertIn('"dataset": "indicadores"', result.stdout)
        self.assertIn('"drift_status": "drifted"', result.stdout)

    def test_cli_top_issue_text(self):
        result = self.run_cli("top-issue", "--format", "text")
        self.assertIn("chile-hub top issue", result.stdout)
        self.assertIn("dataset=indicadores", result.stdout)
        self.assertIn("source_detail=public_api_with_published_backfill", result.stdout)
        self.assertIn("reason=", result.stdout)
        self.assertIn("action=", result.stdout)

    def test_cli_top_issue_table(self):
        result = self.run_cli("top-issue", "--format", "table")
        self.assertIn("chile-hub top issue", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_packages(self):
        result = self.run_cli("packages")
        self.assertIn('"package_type": "zip"', result.stdout)
        self.assertIn('"path": "data/normalized/chile-hub-publishable-bundle.zip"', result.stdout)
        self.assertIn('"checksum_algorithm": "sha256"', result.stdout)
        self.assertIn(
            '"verification_command": "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"',
            result.stdout,
        )

    def test_cli_packages_table(self):
        result = self.run_cli("packages", "--format", "table")
        self.assertIn("chile-hub packages", result.stdout)
        self.assertIn("package_type", result.stdout)
        self.assertIn("data/normalized/chile-hub-publishable-bundle.zip", result.stdout)

    def test_cli_package(self):
        result = self.run_cli("package")
        self.assertIn('"package_type": "zip"', result.stdout)

    def test_cli_verify_package(self):
        result = self.run_cli("verify-package")
        self.assertIn('"checksum_algorithm": "sha256"', result.stdout)
        self.assertIn(
            '"checksum_path": "data/normalized/chile-hub-publishable-bundle.zip.sha256"',
            result.stdout,
        )
        self.assertIn(
            '"verification_command": "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"',
            result.stdout,
        )

    def test_cli_redistribution(self):
        result = self.run_cli("redistribution")
        self.assertIn('"review_terms_count":', result.stdout)
        self.assertIn('"dataset": "indicadores"', result.stdout)

    def test_cli_redistribution_table(self):
        result = self.run_cli("redistribution", "--format", "table")
        self.assertIn("chile-hub redistribution", result.stdout)
        self.assertIn("dataset      status", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_provenance(self):
        result = self.run_cli("provenance")
        self.assertIn('"live_count":', result.stdout)
        self.assertIn('"source_name":', result.stdout)

    def test_cli_provenance_table(self):
        result = self.run_cli("provenance", "--format", "table")
        self.assertIn("chile-hub provenance", result.stdout)
        self.assertIn("dataset      mode      source", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_drift(self):
        result = self.run_cli("drift")
        self.assertIn('"drifted_count":', result.stdout)
        self.assertIn('"coverage_status":', result.stdout)

    def test_cli_drift_table(self):
        result = self.run_cli("drift", "--format", "table")
        self.assertIn("chile-hub drift", result.stdout)
        self.assertIn("dataset      drift      mode", result.stdout)
        self.assertIn("indicadores", result.stdout)


class WorkflowContractTests(unittest.TestCase):
    CRITICAL_STEP_NAMES_IN_ORDER: ClassVar[list[str]] = [
        "Extract source data",
        "Build outputs",
        "Verify pipeline artifacts",
        "Run unit and contract tests",
        "Generate pipeline status",
        "Publish job summary",
        "Upload generated pipeline output",
        "Download generated pipeline output",
        "Verify landing page",
        "Download verified pipeline output",
        "Commit refreshed artifacts",
    ]

    @classmethod
    def setUpClass(cls):
        cls.workflow_text = (ROOT_DIR / ".github" / "workflows" / "pipeline-check.yml").read_text()
        cls.workflow_lines = cls.workflow_text.splitlines()
        cls.step_names = []

        for line in cls.workflow_lines:
            stripped = line.strip()
            if stripped.startswith("- name: "):
                cls.step_names.append(stripped.removeprefix("- name: "))

    def assertSequenceContainsOrderedSubsequence(self, actual, expected):
        positions = []
        for item in expected:
            self.assertIn(item, actual)
            positions.append(actual.index(item))
        self.assertEqual(
            positions,
            sorted(positions),
            msg=f"Expected ordered subsequence {expected}, got positions {positions} in {actual}",
        )

    def test_pipeline_check_workflow_uses_split_bounded_jobs(self):
        for job in ("quality:", "build-and-test:", "package-quality:", "landing:", "publish:"):
            self.assertIn(job, self.workflow_text)
        self.assertEqual(self.workflow_text.count("timeout-minutes:"), 5)
        self.assertIn("concurrency:", self.workflow_text)

    def test_pipeline_check_workflow_uses_one_generated_output_artifact(self):
        self.assertIn("PIPELINE_ARTIFACT: pipeline-output-${{ github.run_id }}", self.workflow_text)
        self.assertIn("path: data/normalized/", self.workflow_text)
        self.assertEqual(self.workflow_text.count("name: ${{ env.PIPELINE_ARTIFACT }}"), 3)
        self.assertNotIn("data/normalized/hub_status.json\n", self.workflow_text)

    def test_pipeline_check_workflow_has_guarded_least_privilege_publication(self):
        self.assertIn("permissions:\n  contents: read", self.workflow_text)
        self.assertIn("contents: write", self.workflow_text)
        self.assertIn("python scripts/verify_pipeline.py", self.workflow_text)
        self.assertIn("args+=(--require-live)", self.workflow_text)
        self.assertIn(
            "github.event_name == 'schedule' || inputs.publish == true", self.workflow_text
        )
        self.assertIn("chore(data): daily refresh [skip ci]", self.workflow_text)

    def test_pipeline_check_workflow_pins_third_party_actions(self):
        for line in self.workflow_lines:
            stripped = line.strip()
            if stripped.startswith("uses: actions/"):
                revision = stripped.split("@", 1)[1].split()[0]
                self.assertRegex(revision, r"^[0-9a-f]{40}$")

    def test_pipeline_check_workflow_orders_critical_steps_consistently(self):
        self.assertSequenceContainsOrderedSubsequence(
            self.step_names,
            self.CRITICAL_STEP_NAMES_IN_ORDER,
        )

    def test_pipeline_check_workflow_builds_installable_package_matrix(self):
        self.assertIn(
            'python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]', self.workflow_text
        )
        self.assertIn("python -m build", self.workflow_text)
        self.assertIn("python -m twine check dist/*", self.workflow_text)
        self.assertIn(
            'python -c "from chile_hub import ChileHub; print(ChileHub)"', self.workflow_text
        )
        self.assertIn("chile-hub cache status", self.workflow_text)

    def test_pypi_release_workflow_uses_trusted_publishing_and_release_assets(self):
        release_text = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text()
        self.assertIn("id-token: write", release_text)
        self.assertIn("python-semantic-release/python-semantic-release@v10.5.2", release_text)
        self.assertIn("pypa/gh-action-pypi-publish", release_text)
        self.assertIn("data/normalized/chile-hub-publishable-bundle.zip", release_text)
        self.assertIn("data/normalized/dataset_catalog.json", release_text)

    def test_testpypi_workflow_smoke_tests_installed_console_script(self):
        testpypi_text = (ROOT_DIR / ".github" / "workflows" / "testpypi.yml").read_text()
        self.assertIn("repository-url: https://test.pypi.org/legacy/", testpypi_text)
        self.assertIn("python -m build", testpypi_text)
        self.assertIn("from chile_hub import ChileHub", testpypi_text)
        self.assertIn("chile-hub --help", testpypi_text)


class MakefileContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.makefile_text = (ROOT_DIR / "Makefile").read_text()

    def test_clean_publishable_uses_manifest_driven_cleanup(self):
        self.assertIn("clean-publishable:", self.makefile_text)
        self.assertIn("scripts/package_publishable_bundle.py --clean", self.makefile_text)
        self.assertNotIn("rm -f data/normalized/*.json", self.makefile_text)
        self.assertNotIn("rm -f data/normalized/*.parquet", self.makefile_text)


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
