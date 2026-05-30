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


if __name__ == "__main__":
    unittest.main()
