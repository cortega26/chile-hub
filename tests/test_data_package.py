"""Tests para el builder de Frictionless Data Package."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.builders.data_package import build_data_package


class DataPackageBuilderTests(unittest.TestCase):
    """Tests para build_data_package con catalogo sintetico y load_schema_contract mockeado."""

    def _make_catalog(self, dataset_entries):
        return {
            "dataset_count": len(dataset_entries),
            "datasets": dataset_entries,
        }

    def _make_entry(
        self,
        name="test_dataset",
        fields=None,
        parquet_path="data/normalized/test_dataset.parquet",
        description="Test dataset",
        source_name="Test Source",
        source_url="https://example.com",
        license_name="CC BY",
        license_url="https://example.com/license",
    ):
        if fields is None:
            fields = ["id", "value"]
        entry = {
            "dataset": name,
            "description": description,
            "source_name": source_name,
            "source_url": source_url,
            "fields": fields,
            "outputs": {"parquet": parquet_path},
            "reuse_policy": {
                "status": "open-attribution",
                "license": license_name,
                "license_url": license_url,
            },
        }
        return entry

    def _make_contract(self, column_types=None, required_columns=None, primary_key=None):
        contract = {}
        if column_types is not None:
            contract["column_types"] = column_types
        if required_columns is not None:
            contract["required_columns"] = required_columns
        if primary_key is not None:
            contract["primary_key"] = primary_key
        return contract

    def test_build_data_package_has_name_and_version(self):
        """build_data_package produce name == 'chile-hub', version y resources no vacio."""
        catalog = self._make_catalog([self._make_entry()])
        with patch("src.builders.data_package.load_schema_contract", return_value=None):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        self.assertEqual(package["name"], "chile-hub")
        self.assertEqual(package["version"], "1.0.0")
        self.assertEqual(package["homepage"], "https://example.com/")
        self.assertGreater(len(package["resources"]), 0)

    def test_column_types_map_correctly(self):
        """Un dataset con column_types mapea tipos correctamente."""
        entry = self._make_entry(
            name="typed_dataset",
            fields=["int_col", "str_col", "untyped_col"],
        )
        contract = self._make_contract(
            column_types={"int_col": "integer", "str_col": "string"},
        )
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=contract):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        resource = package["resources"][0]
        fields_by_name = {f["name"]: f for f in resource["schema"]["fields"]}

        self.assertEqual(fields_by_name["int_col"]["type"], "integer")
        self.assertEqual(fields_by_name["str_col"]["type"], "string")
        # Columnas fuera de column_types caen a "string"
        self.assertEqual(fields_by_name["untyped_col"]["type"], "string")

    def test_primary_key_appears_in_schema(self):
        """primary_key del contrato aparece en schema.primaryKey."""
        entry = self._make_entry(name="pk_dataset", fields=["id", "name"])
        contract = self._make_contract(primary_key=["id"])
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=contract):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        resource = package["resources"][0]
        self.assertEqual(resource["schema"]["primaryKey"], ["id"])

    def test_required_columns_have_constraint(self):
        """required_columns produce constraints.required == True."""
        entry = self._make_entry(
            name="req_dataset",
            fields=["id", "name", "optional_tag"],
        )
        contract = self._make_contract(
            required_columns=["id", "name"],
        )
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=contract):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        resource = package["resources"][0]
        fields_by_name = {f["name"]: f for f in resource["schema"]["fields"]}

        self.assertEqual(fields_by_name["id"]["constraints"]["required"], True)
        self.assertEqual(fields_by_name["name"]["constraints"]["required"], True)
        self.assertNotIn("constraints", fields_by_name["optional_tag"])

    def test_dataset_without_parquet_is_omitted(self):
        """Un dataset sin outputs.parquet se omite de resources."""
        entry_no_parquet = {
            "dataset": "no_parquet_dataset",
            "description": "No parquet",
            "fields": ["id"],
            "outputs": {"json": "data/normalized/no_parquet.json"},
        }
        entry_with_parquet = self._make_entry(name="has_parquet")
        catalog = self._make_catalog([entry_no_parquet, entry_with_parquet])

        with patch("src.builders.data_package.load_schema_contract", return_value=None):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        resource_names = [r["name"] for r in package["resources"]]
        self.assertNotIn("no_parquet_dataset", resource_names)
        self.assertIn("has_parquet", resource_names)

    def test_sources_and_licenses_in_resource(self):
        """sources y licenses se incluyen desde el catalogo."""
        entry = self._make_entry()
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=None):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        resource = package["resources"][0]
        self.assertEqual(len(resource["sources"]), 1)
        self.assertEqual(resource["sources"][0]["title"], "Test Source")
        self.assertEqual(resource["sources"][0]["path"], "https://example.com")
        self.assertEqual(len(resource["licenses"]), 1)
        self.assertEqual(resource["licenses"][0]["title"], "CC BY")

    def test_resource_parquet_path_is_basename(self):
        """path del resource es solo el basename del parquet."""
        entry = self._make_entry(parquet_path="data/normalized/mydata.parquet")
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=None):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        self.assertEqual(package["resources"][0]["path"], "mydata.parquet")

    def test_missing_values_default_is_empty_string(self):
        """schema.missingValues es [""]."""
        entry = self._make_entry()
        catalog = self._make_catalog([entry])

        with patch("src.builders.data_package.load_schema_contract", return_value=None):
            package = build_data_package(catalog, "1.0.0", "https://example.com/")

        self.assertEqual(package["resources"][0]["schema"]["missingValues"], [""])


class DataPackageConsumerTests(unittest.TestCase):
    """Tests para los metodos consumer de datapackage.json en ChileHub."""

    @classmethod
    def setUpClass(cls):
        from chile_hub import ChileHub

        cls.hub = ChileHub(data_dir=ROOT_DIR / "data" / "normalized")

    def test_frictionless_validate_full_descriptor_passes(self):
        """El descriptor del repositorio es valido segun frictionless."""
        result = self.hub.frictionless_validate()
        self.assertTrue(result["valid"], f"Errores: {result['errors']}")
        self.assertEqual(result["errors"], [])

    def test_frictionless_validate_specific_dataset_exists(self):
        """Validar un dataset que existe en el descriptor retorna valid=True."""
        result = self.hub.frictionless_validate(dataset_name="comunas")
        self.assertTrue(result["valid"])
        self.assertIn("checked", result["stats"])

    def test_frictionless_validate_nonexistent_dataset_fails(self):
        """Validar un dataset que no existe en el descriptor retorna valid=False."""
        result = self.hub.frictionless_validate(dataset_name="no_existe_xyz")
        self.assertFalse(result["valid"])
        self.assertIn("no_existe_xyz", result["errors"][0])

    def test_from_datapackage_returns_chilehub(self):
        """from_datapackage con el descriptor local retorna un ChileHub funcional."""
        from chile_hub import ChileHub

        descriptor = ROOT_DIR / "data" / "normalized" / "datapackage.json"
        hub = ChileHub.from_datapackage(str(descriptor))
        self.assertIsInstance(hub, ChileHub)
        # Deberia poder listar datasets
        summary = hub.summary()
        self.assertIsInstance(summary, list)
        self.assertGreater(len(summary), 0)


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
