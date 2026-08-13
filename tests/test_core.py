"""Tests unitarios para los métodos públicos de ChileHub (core.py).

Estos tests se enfocan en la lógica de negocio de la librería: consulta
de metadatos, reportes operativos y métodos de inspección.  Usan los
artefactos existentes en data/normalized/.

No cubren el CLI (argparse + _main) — eso corresponde a tests de integración.
"""

import datetime
import unittest
from pathlib import Path
from unittest import mock

import polars as pl

from chile_hub import ChileHub
from chile_hub.exceptions import ChileHubDataError, ChileHubDatasetError

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"


def _hub():
    """Factory reutilizable: ChileHub apuntando a data/normalized/ local."""
    # Staleness guard (Plan 080): antes, test_core.py (73 tests) corría
    # contra artefactos stale — el guard solo se llamaba en 3 de 9 clases
    # de test_chile_hub.py. Se reutiliza la función compartida.
    from test_chile_hub import _assert_normalized_not_stale

    _assert_normalized_not_stale()
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

    def test_load_polars_cache(self):
        """Verifica que la segunda llamada a load_polars no relea Parquet."""
        hub = _hub()
        df1 = hub.load_polars("comunas")
        self.assertGreater(df1.height, 0)

        with mock.patch("chile_hub.core.pl.read_parquet") as mock_read:
            df2 = hub.load_polars("comunas")
            mock_read.assert_not_called()

        self.assertIs(df1, df2)

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
        # Sin red real (Plan 080): la señal de liveness la cubre
        # source-urls.yml semanalmente — aquí solo se prueba el formato.
        fake_resp = mock.MagicMock(status_code=200, elapsed=datetime.timedelta(milliseconds=5))
        fake_resp.close = lambda: None
        with mock.patch("chile_hub.core.requests.head", return_value=fake_resp):
            results = hub.check_sources(timeout=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("dataset", r)
            self.assertIn("status", r)
            self.assertEqual(r["status"], "online")


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


class ChileHubApiDocstringTests(unittest.TestCase):
    """Los docstrings de los métodos públicos de la API no deben ser None."""

    def test_public_api_methods_have_docstrings(self):
        methods = [
            ChileHub.load_polars,
            ChileHub.validate_dataset,
            ChileHub.validate_user_data,
        ]
        for method in methods:
            self.assertIsNotNone(
                method.__doc__,
                f"{method.__name__}.__doc__ is None — "
                f"documentation will not render in mkdocstrings",
            )


class ChileHubSQLTests(unittest.TestCase):
    """Tests para el mÃ©todo ChileHub.sql()."""

    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_sql_single_table_select(self):
        """Una consulta simple contra una sola tabla retorna un DataFrame."""
        result = self.hub.sql("SELECT codigo_comuna, nombre_comuna_clean FROM comunas LIMIT 5")
        self.assertIsInstance(result, pl.DataFrame)
        self.assertEqual(result.height, 5)
        self.assertGreater(result.width, 0)

    def test_sql_two_dataset_join(self):
        """Un JOIN entre dos datasets por codigo_comuna produce resultados."""
        result = self.hub.sql(
            "SELECT c.codigo_comuna, c.nombre_comuna_clean, cen.poblacion_censada "
            "FROM comunas c "
            "JOIN censo_comunal cen ON c.codigo_comuna = cen.codigo_comuna "
            "LIMIT 10"
        )
        self.assertIsInstance(result, pl.DataFrame)
        self.assertGreater(result.height, 0)
        self.assertIn("codigo_comuna", result.columns)
        self.assertIn("nombre_comuna_clean", result.columns)
        self.assertIn("poblacion_censada", result.columns)

    def test_sql_missing_duckdb_raises_import_error(self):
        """Si duckdb no estÃ¡ instalado, sql() lanza ImportError con mensaje Ãºtil."""
        import sys

        # Remover duckdb de sys.modules para forzar re-import
        for key in list(sys.modules.keys()):
            if key == "duckdb" or key.startswith("duckdb."):
                sys.modules.pop(key)

        def mock_import(name, *args, **kwargs):
            if name == "duckdb":
                raise ImportError("No module named 'duckdb'")
            return __import__(name, *args, **kwargs)

        hub = _hub()
        with mock.patch("builtins.__import__", side_effect=mock_import):
            with self.assertRaises(ImportError) as ctx:
                hub.sql("SELECT 1")
            self.assertIn("chile-hub[query]", str(ctx.exception))


class ChileHubResolveComunasTests(unittest.TestCase):
    """Tests para ChileHub.resolve_comunas() (Plan 050, ADR-009)."""

    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    def test_resolve_comunas_happy_path(self):
        """Un nombre conocido resuelve a su codigo CUT de 5 caracteres."""
        result = self.hub.resolve_comunas(["Ñuñoa"])
        row = result.to_dicts()[0]
        self.assertTrue(row["matched"])
        self.assertEqual(len(row["codigo_comuna"]), 5)
        self.assertEqual(row["nombre_comuna"], "Ñuñoa")

    def test_resolve_comunas_no_match_returns_null_without_raising(self):
        """Un nombre inexistente devuelve matched=False y codigos null, sin excepcion."""
        result = self.hub.resolve_comunas(["No Existe Como Comuna"])
        row = result.to_dicts()[0]
        self.assertFalse(row["matched"])
        self.assertIsNone(row["codigo_comuna"])
        self.assertIsNone(row["nombre_comuna"])
        self.assertIsNone(row["codigo_region"])

    def test_resolve_comunas_preserves_order_and_duplicates(self):
        """El orden y los duplicados del input se preservan fila a fila."""
        result = self.hub.resolve_comunas(["Ñuñoa", "Ñuñoa", "Concón"])
        self.assertEqual(result.height, 3)
        rows = result.to_dicts()
        self.assertEqual(rows[0]["input"], "Ñuñoa")
        self.assertEqual(rows[1]["input"], "Ñuñoa")
        self.assertEqual(rows[2]["input"], "Concón")
        self.assertEqual(rows[0]["codigo_comuna"], rows[1]["codigo_comuna"])

    def test_resolve_comunas_codigo_comuna_is_pl_string(self):
        """Invariante CUT: codigo_comuna nunca es int, siempre pl.String."""
        result = self.hub.resolve_comunas(["Ñuñoa"])
        self.assertEqual(result.schema["codigo_comuna"], pl.String)

    def test_normalize_matches_published_nombre_comuna_clean(self):
        """Guardrail anti-divergencia: normalize_comuna_name debe reproducir
        exactamente nombre_comuna_clean para las 346 comunas publicadas. Si
        diverge, resolve_comunas normalizaria el input del usuario distinto
        a como se construyo nombre_comuna_clean, produciendo no-matches
        silenciosos contra datos publicados."""
        from chile_hub.text import normalize_comuna_name

        comunas = self.hub.load_polars("comunas")
        for row in comunas.iter_rows(named=True):
            self.assertEqual(
                normalize_comuna_name(row["nombre_comuna"]),
                row["nombre_comuna_clean"],
                msg=(
                    f"divergencia en {row['codigo_comuna']}: "
                    f"{normalize_comuna_name(row['nombre_comuna'])!r} != "
                    f"{row['nombre_comuna_clean']!r}"
                ),
            )


class FromDatapackageUrlTests(unittest.TestCase):
    """Tests para from_datapackage(url) (Plan 051, ADR-010).

    No dependen de red: mockean frictionless.Package para evitar resolver una
    URL real. Modelados sobre DataPackageConsumerTests de test_data_package.py.
    """

    URL = "https://tooltician.com/chile-hub/data/normalized/datapackage.json"

    def test_url_skips_local_path_check(self):
        """Una URL no debe intentar Path(...).exists() ni lanzar FileNotFoundError."""
        with mock.patch("frictionless.Package") as mock_package:
            with self.assertRaises(ChileHubDataError):
                ChileHub.from_datapackage(self.URL)
            mock_package.assert_called_once_with(self.URL)

    def test_url_validates_descriptor_before_raising(self):
        """Si frictionless no puede resolver el descriptor remoto, ese error propaga
        (no se enmascara con el ChileHubDataError de la limitación conocida)."""
        with mock.patch("frictionless.Package", side_effect=RuntimeError("no accesible")):
            with self.assertRaises(RuntimeError):
                ChileHub.from_datapackage(self.URL)

    def test_local_path_behavior_unchanged(self):
        """El path local sigue funcionando exactamente igual (regresión)."""
        descriptor = NORMALIZED_DIR / "datapackage.json"
        hub = ChileHub.from_datapackage(str(descriptor))
        self.assertIsInstance(hub, ChileHub)
        self.assertGreater(len(hub.summary()), 0)


class ChileHubResolveByCoordsTests(unittest.TestCase):
    """Tests para ChileHub.resolve_by_coords() (Plan 065, ADR-012).

    Usan un fixture sintético de 3 comunas cuadradas (tests/geo_fixtures.py),
    nunca el artefacto real de 5 MB. El umbral de >= 340 geometrías se parchea
    en los tests de happy-path; el test estructural con < 340 lo ejercita sin
    parche (en tests/test_chile_hub.py).
    """

    @classmethod
    def setUpClass(cls):
        cls.hub = _hub()

    @staticmethod
    def _fixture_path(comunas=None):
        import tempfile

        from geo_fixtures import write_synthetic_parquet

        tmpdir = Path(tempfile.mkdtemp())
        return write_synthetic_parquet(tmpdir / "geometria_comunal.parquet", comunas)

    def test_known_point_matches_five_char_cut(self):
        """Un punto dentro de la comuna A resuelve a su CUT de 5 caracteres."""
        with mock.patch("chile_hub.geo.MIN_NON_EMPTY_GEOMETRIES", 3):
            result = self.hub.resolve_by_coords(
                [(-19.5, -70.0)], geometry_path=self._fixture_path()
            )
        row = result.to_dicts()[0]
        self.assertTrue(row["matched"])
        self.assertEqual(row["codigo_comuna"], "01101")
        self.assertEqual(len(row["codigo_comuna"]), 5)
        self.assertEqual(row["nombre_comuna"], "Arica")
        self.assertEqual(result.schema["codigo_comuna"], pl.String)

    def test_point_outside_chile_is_unmatched(self):
        """Un punto fuera de todo polígono devuelve matched=False y nulos."""
        with mock.patch("chile_hub.geo.MIN_NON_EMPTY_GEOMETRIES", 3):
            result = self.hub.resolve_by_coords(
                [(-21.0, -71.0)], geometry_path=self._fixture_path()
            )
        row = result.to_dicts()[0]
        self.assertFalse(row["matched"])
        self.assertIsNone(row["codigo_comuna"])
        self.assertIsNone(row["nombre_comuna"])

    def test_order_and_duplicates_preserved(self):
        """El orden y los duplicados del input se preservan fila a fila."""
        points = [(-19.5, -70.0), (-19.5, -70.0), (-21.0, -71.0)]
        with mock.patch("chile_hub.geo.MIN_NON_EMPTY_GEOMETRIES", 3):
            result = self.hub.resolve_by_coords(points, geometry_path=self._fixture_path())
        rows = result.to_dicts()
        self.assertEqual([r["matched"] for r in rows], [True, True, False])
        self.assertEqual(rows[0]["codigo_comuna"], rows[1]["codigo_comuna"])
        self.assertEqual(rows[0]["input_lat"], -19.5)
        self.assertEqual(rows[0]["input_lon"], -70.0)

    def test_invalid_coordinates_raise_value_error_naming_input(self):
        """Latitud/longitud fuera de rango levantan ValueError nombrando el input."""
        with self.assertRaises(ValueError) as ctx:
            self.hub.resolve_by_coords([(-33.4, -70.6), (95.0, 0.0)])
        self.assertIn("input 1", str(ctx.exception))
        with self.assertRaises(ValueError):
            self.hub.resolve_by_coords([(0.0, 181.0)])

    def test_boundary_point_matches_via_covers(self):
        """Un punto exactamente en el borde matchea (covers, no contains)."""
        edge_point = (-19.0, -70.0)  # borde superior de A, fuera de B/C
        with mock.patch("chile_hub.geo.MIN_NON_EMPTY_GEOMETRIES", 3):
            result = self.hub.resolve_by_coords([edge_point], geometry_path=self._fixture_path())
        self.assertTrue(result.to_dicts()[0]["matched"])
        self.assertEqual(result.to_dicts()[0]["codigo_comuna"], "01101")

    def test_overlap_tie_break_is_deterministic_and_warns(self):
        """Punto cubierto por dos comunas: gana el CUT menor y se emite warning."""
        with mock.patch("chile_hub.geo.MIN_NON_EMPTY_GEOMETRIES", 3):
            with self.assertLogs("chile_hub.geo", level="WARNING") as logs:
                result = self.hub.resolve_by_coords(
                    [(-18.75, -69.2)], geometry_path=self._fixture_path()
                )
        row = result.to_dicts()[0]
        self.assertTrue(row["matched"])
        self.assertEqual(row["codigo_comuna"], "01102")  # min("01102", "01103")
        self.assertTrue(any("tie-break" in msg for msg in logs.output))

    def test_lazy_geo_extra_raises_import_error_with_hint(self):
        """Sin geopandas/shapely: ChileHub() construye bien, resolve_by_coords
        levanta ImportError con la instrucción exacta (patrón ChileHubSQLTests)."""

        def mock_import(name, *args, **kwargs):
            if name.startswith(("geopandas", "shapely")):
                raise ImportError(f"No module named '{name}'")
            return __import__(name, *args, **kwargs)

        fixture = self._fixture_path()
        with mock.patch("builtins.__import__", side_effect=mock_import):
            hub = ChileHub(data_dir=NORMALIZED_DIR)  # construcción sin importar geo
            with self.assertRaises(ImportError) as ctx:
                hub.resolve_by_coords([(-19.5, -70.0)], geometry_path=fixture)
            self.assertIn("pip install chile-hub[geo]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
