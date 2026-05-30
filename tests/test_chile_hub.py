import json
import subprocess
import sys
import unittest
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

    def test_list_datasets(self):
        self.assertEqual(self.hub.list_datasets(), ["regiones", "provincias", "comunas", "indicadores"])

    def test_get_output_path(self):
        path = self.hub.get_output_path("comunas", "parquet")
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "comunas.parquet")

    def test_load_polars(self):
        df = self.hub.load_polars("comunas")
        self.assertEqual(df.height, 346)
        self.assertIn("codigo_comuna", df.columns)

    def test_load_polars_regiones(self):
        df = self.hub.load_polars("regiones")
        self.assertGreaterEqual(df.height, 16)
        self.assertIn("codigo_region", df.columns)

    def test_summary_statuses(self):
        summary = self.hub.summary()
        statuses = {item["dataset"]: item["validation_status"] for item in summary}
        self.assertEqual(
            statuses,
            {"regiones": "ok", "provincias": "ok", "comunas": "ok", "indicadores": "ok"},
        )
        freshness_statuses = {item["dataset"]: item["freshness_status"] for item in summary}
        self.assertEqual(
            freshness_statuses,
            {"regiones": "fresh", "provincias": "fresh", "comunas": "fresh", "indicadores": "fresh"},
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

    def test_inventory_contains_artifact_types(self):
        inventory = self.hub.inventory()
        comunas = next(item for item in inventory if item["dataset"] == "comunas")
        self.assertEqual(comunas["published_outputs"], ["json", "parquet"])
        self.assertEqual(comunas["artifact_count"], 2)
        self.assertGreater(comunas["total_size_bytes"], 0)
        self.assertEqual(comunas["freshness_status"], "fresh")
        self.assertIsInstance(comunas["freshness_age_hours"], float)

    def test_unknown_dataset_raises(self):
        with self.assertRaises(KeyError):
            self.hub.get_dataset("no-existe")


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
        self.assertIn("data/normalized/regiones.parquet", artifact_paths)
        self.assertIn("data/normalized/provincias.parquet", artifact_paths)
        self.assertIn("data/normalized/comunas.parquet", artifact_paths)

    def test_manifest_dataset_metadata_present_for_dataset_outputs(self):
        by_path = {entry["path"]: entry for entry in self.manifest["artifacts"]}
        self.assertEqual(by_path["data/normalized/comunas.parquet"]["dataset"], "comunas")
        self.assertEqual(by_path["data/normalized/comunas.parquet"]["output_type"], "parquet")
        self.assertEqual(by_path["data/normalized/indicadores_hoy.json"]["dataset"], "indicadores")
        self.assertEqual(by_path["data/normalized/indicadores_hoy.json"]["output_type"], "json")

    def test_catalog_usage_examples_present(self):
        for dataset in self.catalog["datasets"]:
            examples = dataset.get("usage_examples", {})
            self.assertIn("python", examples)
            self.assertIn("duckdb", examples)
            self.assertIn("cli", examples)

    def test_catalog_freshness_present(self):
        for dataset in self.catalog["datasets"]:
            self.assertIn(dataset.get("freshness", {}).get("status"), {"fresh", "stale", "unknown"})
            self.assertTrue(dataset.get("freshness_policy", {}).get("max_age_hours"))

    def test_manifest_hashes_present(self):
        for artifact in self.manifest["artifacts"]:
            self.assertTrue(artifact["sha256"])
            self.assertGreater(artifact["size_bytes"], 0)


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

    def test_cli_inventory(self):
        result = self.run_cli("inventory")
        self.assertIn('"dataset": "comunas"', result.stdout)
        self.assertIn('"published_outputs": [', result.stdout)
        self.assertIn('"artifact_count": 2', result.stdout)
        self.assertIn('"freshness_status": "fresh"', result.stdout)


if __name__ == "__main__":
    unittest.main()
