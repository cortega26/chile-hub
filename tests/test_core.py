"""Tests unitarios para los métodos públicos de ChileHub (core.py).

Estos tests se enfocan en la lógica de negocio de la librería: consulta
de metadatos, reportes operativos y métodos de inspección.  Usan los
artefactos existentes en data/normalized/.

No cubren el CLI (argparse + _main) — eso corresponde a tests de integración.
"""

import unittest
from pathlib import Path

import polars as pl

from chile_hub import ChileHub
from chile_hub.exceptions import ChileHubDatasetError

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"


def _hub():
    """Factory reutilizable: ChileHub apuntando a data/normalized/ local."""
    return ChileHub(data_dir=NORMALIZED_DIR)


class ChileHubSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_summary_returns_list_of_dicts(self):
        entries = self.hub.summary()
        self.assertIsInstance(entries, list)
        self.assertGreater(len(entries), 0)
        for entry in entries:
            self.assertIn("dataset", entry)
            self.assertIn("source_mode", entry)

    def test_summary_table_returns_string(self):
        table = self.hub.summary_table()
        self.assertIsInstance(table, str)
        self.assertIn("chile-hub summary", table)
        self.assertIn("dataset", table.lower())


class ChileHubHealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_health_returns_dict_with_expected_keys(self):
        health = self.hub.health()
        self.assertIsInstance(health, dict)
        self.assertIn("overall_status", health)
        self.assertIn("dataset_count", health)
        self.assertIn("datasets", health)

    def test_health_table_returns_string(self):
        table = self.hub.health_table()
        self.assertIn("chile-hub health", table)


class ChileHubStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_status_returns_dict(self):
        status = self.hub.status()
        self.assertIsInstance(status, dict)
        self.assertIn("overall_status", status)

    def test_status_table_returns_string(self):
        table = self.hub.status_table()
        self.assertIn("chile-hub status", table)


class ChileHubProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_provenance_returns_dict_with_datasets(self):
        prov = self.hub.provenance()
        self.assertIsInstance(prov, dict)
        self.assertIn("datasets", prov)

    def test_provenance_table_returns_string(self):
        table = self.hub.provenance_table()
        self.assertIn("chile-hub provenance", table)


class ChileHubRedistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_redistribution_returns_dict(self):
        report = self.hub.redistribution()
        self.assertIsInstance(report, dict)
        self.assertIn("datasets", report)

    def test_redistribution_table_returns_string(self):
        table = self.hub.redistribution_table()
        self.assertIn("chile-hub redistribution", table)


class ChileHubFreshnessAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_freshness_audit_returns_dict_with_counts(self):
        audit = self.hub.freshness_audit()
        self.assertIsInstance(audit, dict)
        self.assertIn("checked_at_utc", audit)
        self.assertIn("fresh_count", audit)
        self.assertIn("stale_count", audit)
        self.assertIn("datasets", audit)

    def test_freshness_audit_table_returns_string(self):
        table = self.hub.freshness_audit_table()
        self.assertIn("chile-hub freshness audit", table)


class ChileHubDriftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_drift_returns_dict(self):
        drift = self.hub.drift()
        self.assertIsInstance(drift, dict)
        self.assertIn("datasets", drift)

    def test_drift_table_returns_string(self):
        table = self.hub.drift_table()
        self.assertIn("chile-hub drift", table)


class ChileHubTopIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_top_issue_returns_dict_or_none(self):
        result = self.hub.top_issue()
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertIn("dataset", result)

    def test_top_issue_table_returns_string(self):
        table = self.hub.top_issue_table()
        self.assertIn("chile-hub top issue", table)


class ChileHubInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_inventory_returns_list_of_dicts(self):
        inv = self.hub.inventory()
        self.assertIsInstance(inv, list)
        self.assertGreater(len(inv), 0)
        for entry in inv:
            self.assertIn("dataset", entry)

    def test_inventory_table_returns_string(self):
        table = self.hub.inventory_table()
        self.assertIn("chile-hub inventory", table)


class ChileHubOverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_overview_returns_dict(self):
        overview = self.hub.overview()
        self.assertIsInstance(overview, dict)
        self.assertIn("dataset_count", overview)

    def test_overview_table_returns_string(self):
        table = self.hub.overview_table()
        self.assertIn("chile-hub overview", table)


class ChileHubRuntimeStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_runtime_status_returns_dict(self):
        runtime = self.hub.runtime_status()
        self.assertIsInstance(runtime, dict)
        self.assertIn("datasets", runtime)

    def test_runtime_status_table_returns_string(self):
        table = self.hub.runtime_status_table()
        self.assertIn("chile-hub runtime status", table)


class ChileHubSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_snapshot_text_returns_string(self):
        text = self.hub.snapshot_text()
        self.assertIn("chile-hub snapshot", text)

    def test_snapshot_table_returns_string(self):
        table = self.hub.snapshot_table()
        self.assertIn("chile-hub snapshot table", table)


class ChileHubDatasetStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_dataset_status_returns_dict(self):
        ds_status = self.hub.dataset_status()
        self.assertIsInstance(ds_status, dict)

    def test_dataset_changelog_returns_dict(self):
        changelog = self.hub.dataset_changelog()
        self.assertIsInstance(changelog, dict)


class ChileHubSourceReadinessAndQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_source_readiness_returns_dict(self):
        readiness = self.hub.source_readiness()
        self.assertIsInstance(readiness, dict)

    def test_dataset_quality_returns_dict(self):
        quality = self.hub.dataset_quality()
        self.assertIsInstance(quality, dict)


class ChileHubArtifactsAndPackagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_artifacts_without_dataset_returns_all(self):
        artifacts = self.hub.artifacts()
        self.assertIsInstance(artifacts, list)
        self.assertGreater(len(artifacts), 0)

    def test_artifacts_with_dataset_filters_correctly(self):
        artifacts = self.hub.artifacts("comunas")
        self.assertIsInstance(artifacts, list)
        if artifacts:
            for a in artifacts:
                self.assertEqual(a.get("dataset"), "comunas")

    def test_artifacts_invalid_dataset_raises_error(self):
        with self.assertRaises(ChileHubDatasetError):
            self.hub.artifacts("dataset_inexistente")

    def test_shared_artifacts_returns_list(self):
        shared = self.hub.shared_artifacts()
        self.assertIsInstance(shared, list)

    def test_shared_artifacts_with_filter(self):
        shared = self.hub.shared_artifacts(shared_type="hub_health", format="json")
        self.assertIsInstance(shared, list)
        for s in shared:
            self.assertEqual(s.get("shared_type"), "hub_health")
            self.assertEqual(s.get("format"), "json")

    def test_packages_returns_list(self):
        packages = self.hub.packages()
        self.assertIsInstance(packages, list)


class ChileHubBundleAndReportsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_bundle_returns_dict(self):
        bundle = self.hub.bundle()
        self.assertIsInstance(bundle, dict)

    def test_reports_index_returns_list(self):
        index = self.hub.report_index()
        self.assertIsInstance(index, list)

    def test_report_index_table_returns_string(self):
        table = self.hub.report_index_table()
        self.assertIn("chile-hub report index", table)

    def test_primary_package_returns_dict(self):
        pkg = self.hub.primary_package("zip")
        self.assertIsInstance(pkg, dict)


class ChileHubCatalogQueriesTests(unittest.TestCase):
    """Tests que cubren get_dataset, get_output_path, list_datasets."""

    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_list_datasets_returns_expected_count(self):
        datasets = self.hub.list_datasets()
        self.assertEqual(len(datasets), 19)

    def test_get_dataset_returns_dict_with_expected_fields(self):
        entry = self.hub.get_dataset("comunas")
        self.assertEqual(entry["dataset"], "comunas")
        self.assertIn("source_name", entry)

    def test_get_dataset_invalid_name_raises_error(self):
        with self.assertRaises(ChileHubDatasetError):
            self.hub.get_dataset("no_existe")

    def test_get_output_path_returns_existing_path(self):
        path = self.hub.get_output_path("comunas", "parquet")
        self.assertTrue(path.exists())

    def test_load_polars_returns_dataframe(self):
        df = self.hub.load_polars("regiones")
        self.assertIsInstance(df, pl.DataFrame)
        self.assertGreater(df.height, 0)

    def test_example_usage_returns_string(self):
        example = self.hub.example_usage("comunas", "python")
        self.assertIsInstance(example, str)
        self.assertGreater(len(example), 0)


class ChileHubEdgeCaseTests(unittest.TestCase):
    """Tests de borde: constructor, errores, modos de inicialización."""

    def test_constructor_rejects_both_catalog_path_and_data_dir(self):
        with self.assertRaises(ValueError):
            ChileHub(catalog_path="/tmp/foo", data_dir="/tmp/bar")

    def test_constructor_with_explicit_catalog_path(self):
        catalog = NORMALIZED_DIR / "dataset_catalog.json"
        hub = ChileHub(catalog_path=catalog)
        self.assertGreater(len(hub.list_datasets()), 0)

    def test_check_sources_returns_list(self):
        hub = _hub()
        results = hub.check_sources(timeout=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("dataset", r)
            self.assertIn("status", r)


class ChileHubInternalHelpersTests(unittest.TestCase):
    """Tests para funciones internas de core.py no cubiertas por tests existentes."""

    def test_format_available_without_requested(self):
        """_format_available() sin 'requested' retorna solo la lista de disponibles."""
        from chile_hub.core import _format_available

        result = _format_available(["comunas", "regiones"])
        self.assertIn("Disponibles", result)
        self.assertIn("comunas", result)
        self.assertIn("regiones", result)
        self.assertNotIn("Quizás", result)

    def test_max_status_all_unknown(self):
        """_max_status() sin argumentos retorna 'unknown'."""
        from chile_hub.core import ChileHub

        result = ChileHub._max_status()
        self.assertEqual(result, "unknown")

        result_none = ChileHub._max_status(None, "", None)
        self.assertEqual(result_none, "unknown")

    def test_get_report_missing_raises_keyerror(self):
        """get_report() con reporte inexistente lanza KeyError."""
        hub = _hub()
        with self.assertRaises(KeyError):
            hub.get_report("no_existe_reporte_xyz", "json")

    def test_primary_package_missing_raises_keyerror(self):
        """primary_package() con tipo inexistente lanza KeyError."""
        hub = _hub()
        with self.assertRaises(KeyError):
            hub.primary_package("formato_inexistente_xyz")

    def test_validate_user_data_type_mismatch(self):
        """validate_user_data() con tipo incorrecto reporta error."""
        hub = _hub()
        # comunas.codigo_comuna debe ser string; pasar enteros
        df = pl.DataFrame(
            {
                "codigo_comuna": [1, 2, 3],
                "codigo_region": ["01", "02", "03"],
                "codigo_provincia": ["011", "021", "031"],
                "nombre_comuna": ["A", "B", "C"],
                "nombre_comuna_clean": ["a", "b", "c"],
                "abreviatura": ["TA", "AN", "AT"],
            }
        )
        result = hub.validate_user_data(df, "comunas")
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("codigo_comuna" in e for e in result["errors"]))

    def test_validate_user_data_null_pk(self):
        """validate_user_data() con valores nulos en clave primaria reporta error."""
        hub = _hub()
        df = pl.DataFrame(
            {
                "codigo_comuna": [None, "13102", "13103"],
                "codigo_region": ["13", "13", "13"],
                "codigo_provincia": ["131", "131", "131"],
                "nombre_comuna": [None, "B", "C"],
                "nombre_comuna_clean": [None, "b", "c"],
                "abreviatura": ["RM", "RM", "RM"],
            }
        )
        result = hub.validate_user_data(df, "comunas")
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("valores nulos" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
