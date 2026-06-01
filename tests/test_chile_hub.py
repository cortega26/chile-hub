import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chile_hub import ChileHub  # noqa: E402


class ChileHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = ChileHub()
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"
        cls.catalog = cls.hub.catalog
        cls.catalog_by_dataset = {
            entry["dataset"]: entry for entry in cls.catalog.get("datasets", [])
        }
        cls.health = cls.hub.health()
        cls.bundle = cls.hub.bundle()

    def test_list_datasets(self):
        self.assertEqual(self.hub.list_datasets(), ["regiones", "provincias", "comunas", "indicadores"])

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

    def test_summary_statuses(self):
        summary = self.hub.summary()
        statuses = {item["dataset"]: item["validation_status"] for item in summary}
        self.assertEqual(
            statuses,
            {"regiones": "ok", "provincias": "ok", "comunas": "ok", "indicadores": "ok"},
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
                next(item for item in summary if item["dataset"] == dataset_name)["coverage_status"],
                {"full", "partial", "unknown", "not_applicable"},
            )
            self.assertIn(
                next(item for item in summary if item["dataset"] == dataset_name)["drift_status"],
                {"healthy", "drifted"},
            )
            self.assertIn(
                next(item for item in summary if item["dataset"] == dataset_name)["degradation_status"],
                {"none", "warning", "degraded"},
            )

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

    def test_get_report(self):
        report = self.hub.get_report("drift_report", "markdown")
        self.assertEqual(report["shared_type"], "drift_report")
        self.assertEqual(report["format"], "markdown")
        self.assertEqual(report["path"], "data/normalized/drift_report.md")
        overview_report = self.hub.get_report("overview", "json")
        self.assertEqual(overview_report["shared_type"], "overview")
        self.assertEqual(overview_report["format"], "json")
        self.assertEqual(overview_report["path"], "data/normalized/overview.json")

    def test_overview(self):
        overview = self.hub.overview()
        self.assertIn(overview["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(overview["dataset_count"], 4)
        self.assertGreaterEqual(overview["shared_artifact_count"], 1)
        self.assertGreaterEqual(overview["package_count"], 1)
        self.assertIn("health_json", overview["report_keys"])
        self.assertIn("drift_json", overview["report_keys"])
        self.assertEqual(len(overview["datasets"]), 4)

    def test_inventory_contains_artifact_types(self):
        inventory = self.hub.inventory()
        comunas = next(item for item in inventory if item["dataset"] == "comunas")
        self.assertEqual(comunas["published_outputs"], ["json", "parquet"])
        self.assertEqual(comunas["artifact_count"], 2)
        self.assertGreater(comunas["total_size_bytes"], 0)
        self.assertIn(comunas["freshness_status"], {"fresh", "stale", "unknown"})
        self.assertIsInstance(comunas["freshness_age_hours"], float)
        self.assertEqual(comunas["warning_count"], len(self.catalog_by_dataset["comunas"].get("warnings", [])))
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

    def test_unknown_dataset_raises(self):
        with self.assertRaises(KeyError):
            self.hub.get_dataset("no-existe")

    def test_health_summary(self):
        health = self.health
        self.assertIn(health["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(health["dataset_count"], 4)
        self.assertEqual(health["ok_count"] + health["warn_count"] + health["error_count"], 4)
        self.assertEqual(
            health["publishable_count"] + health["review_terms_count"] + health["unknown_reuse_count"],
            4,
        )
        self.assertEqual(
            health["degraded_count"] + health["degradation_warning_count"] + sum(
                1 for entry in health["datasets"] if entry["degradation_status"] == "none"
            ),
            4,
        )
        self.assertEqual(
            health["partial_coverage_count"] + health["unknown_coverage_count"] + sum(
                1 for entry in health["datasets"] if entry["coverage_status"] in {"full", "not_applicable"}
            ),
            4,
        )
        self.assertEqual(
            health["drifted_count"] + sum(1 for entry in health["datasets"] if entry["drift_status"] == "healthy"),
            4,
        )

    def test_bundle_summary(self):
        bundle = self.bundle
        self.assertEqual(bundle["overall_status"], self.health["overall_status"])
        self.assertEqual(bundle["dataset_count"], 4)
        self.assertEqual(len(bundle["datasets"]), 4)
        self.assertEqual(bundle["reports"]["health_json"]["path"], "data/normalized/hub_health.json")
        self.assertEqual(bundle["reports"]["provenance_json"]["path"], "data/normalized/provenance_report.json")
        self.assertEqual(bundle["reports"]["overview_json"]["path"], "data/normalized/overview.json")
        self.assertEqual(bundle["reports"]["overview_markdown"]["path"], "data/normalized/overview.md")
        self.assertEqual(bundle["health"]["publishable_count"], self.health["publishable_count"])
        self.assertEqual(bundle["health"]["review_terms_count"], self.health["review_terms_count"])
        self.assertEqual(bundle["health"]["partial_coverage_count"], self.health["partial_coverage_count"])
        self.assertEqual(bundle["health"]["drifted_count"], self.health["drifted_count"])
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
        self.assertEqual(comunas["reuse_policy"]["status"], self.catalog_by_dataset["comunas"]["reuse_policy"]["status"])
        self.assertIn(comunas["publishability_status"], {"ready", "review_terms", "unknown"})
        self.assertIn(comunas["coverage"]["status"], {"full", "partial", "unknown", "not_applicable"})
        self.assertIn(comunas["drift"]["status"], {"healthy", "drifted"})
        self.assertIn(comunas["degradation"]["status"], {"none", "warning", "degraded"})
        indicadores = next(entry for entry in bundle["datasets"] if entry["dataset"] == "indicadores")
        self.assertEqual(indicadores["reuse_policy"]["status"], self.catalog_by_dataset["indicadores"]["reuse_policy"]["status"])
        self.assertIn(indicadores["publishability_status"], {"ready", "review_terms", "unknown"})

    def test_redistribution_report(self):
        report = self.hub.redistribution()
        self.assertEqual(report["dataset_count"], 4)
        self.assertEqual(report["ready_count"] + report["review_terms_count"] + report["unknown_count"], 4)
        indicadores = next(entry for entry in report["datasets"] if entry["dataset"] == "indicadores")
        self.assertIn(indicadores["publishability_status"], {"ready", "review_terms", "unknown"})
        self.assertTrue(indicadores["recommended_action"])

    def test_provenance_report(self):
        report = self.hub.provenance()
        self.assertEqual(report["dataset_count"], 4)
        self.assertEqual(report["live_count"] + report["fallback_count"], 4)
        comunas = next(entry for entry in report["datasets"] if entry["dataset"] == "comunas")
        self.assertTrue(comunas["source_name"])
        self.assertTrue(comunas["source_detail"])
        self.assertIn(comunas["freshness_status"], {"fresh", "stale", "unknown"})

    def test_drift_report(self):
        report = self.hub.drift()
        self.assertEqual(report["dataset_count"], 4)
        self.assertEqual(report["drifted_count"] + report["healthy_count"], 4)
        comunas = next(entry for entry in report["datasets"] if entry["dataset"] == "comunas")
        self.assertIn(comunas["drift_status"], {"healthy", "drifted"})
        self.assertIn(comunas["coverage_status"], {"full", "partial", "unknown", "not_applicable"})
        self.assertIn(comunas["degradation_status"], {"none", "warning", "degraded"})
        self.assertTrue(comunas["recommended_action"])


class ArtifactContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"
        cls.catalog = json.loads((cls.normalized_dir / "dataset_catalog.json").read_text())
        cls.manifest = json.loads((cls.normalized_dir / "artifact_manifest.json").read_text())

    def test_catalog_dataset_count(self):
        self.assertEqual(self.catalog["dataset_count"], 4)

    def test_manifest_contains_expected_publishable_files(self):
        artifact_paths = {entry["path"] for entry in self.manifest["artifacts"]}
        self.assertIn("data/normalized/dataset_catalog.json", artifact_paths)
        self.assertIn("data/normalized/pipeline_status.md", artifact_paths)
        self.assertIn("data/normalized/hub_health.json", artifact_paths)
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
            self.assertIn(dataset.get("freshness", {}).get("status"), {"fresh", "stale", "unknown"})
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
        self.assertIn("data/normalized/hub_bundle.json", names)
        self.assertIn("data/normalized/artifact_manifest.json", names)
        self.assertIn("data/normalized/overview.json", names)


class ChileHubCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "src.chile_hub", *args],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_cli_list(self):
        result = self.run_cli("list")
        self.assertEqual(
            result.stdout.strip().splitlines(),
            ["regiones", "provincias", "comunas", "indicadores"],
        )

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
        result = self.run_cli("shared-artifacts", "--shared-type", "hub_health", "--format", "json")
        self.assertIn('"shared_type": "hub_health"', result.stdout)
        self.assertIn('"path": "data/normalized/hub_health.json"', result.stdout)

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

    def test_cli_overview(self):
        result = self.run_cli("overview")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"shared_artifact_count":', result.stdout)
        self.assertIn('"report_keys":', result.stdout)

    def test_cli_health(self):
        result = self.run_cli("health")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"dataset_count": 4', result.stdout)
        self.assertIn('"review_terms_count":', result.stdout)
        self.assertIn('"partial_coverage_count":', result.stdout)
        self.assertIn('"drifted_count":', result.stdout)

    def test_cli_bundle(self):
        result = self.run_cli("bundle")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn('"shared_artifacts"', result.stdout)
        self.assertIn('"reports"', result.stdout)

    def test_cli_packages(self):
        result = self.run_cli("packages")
        self.assertIn('"package_type": "zip"', result.stdout)
        self.assertIn('"path": "data/normalized/chile-hub-publishable-bundle.zip"', result.stdout)

    def test_cli_redistribution(self):
        result = self.run_cli("redistribution")
        self.assertIn('"review_terms_count":', result.stdout)
        self.assertIn('"dataset": "indicadores"', result.stdout)

    def test_cli_provenance(self):
        result = self.run_cli("provenance")
        self.assertIn('"live_count":', result.stdout)
        self.assertIn('"source_name":', result.stdout)

    def test_cli_drift(self):
        result = self.run_cli("drift")
        self.assertIn('"drifted_count":', result.stdout)
        self.assertIn('"coverage_status":', result.stdout)


if __name__ == "__main__":
    unittest.main()
