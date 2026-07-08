import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import polars as pl

UTC = timezone.utc

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chile_hub import (
    ChileHub,
    ChileHubDataError,
    ChileHubDatasetError,
    ChileHubExampleError,
    ChileHubOutputError,
)
from chile_hub.data_manager import ChileHubDataManager, ReleaseAsset
from src.validation import validate_indicadores

# ── Staleness guard ───────────────────────────────────────────────────────────
_STAGING_DIR = ROOT_DIR / "data" / "staging"
_NORMALIZED_SENTINEL = ROOT_DIR / "data" / "normalized" / "pipeline_metadata.json"
INDICADORES_RECOVERY_SOURCE_DETAILS = {
    "public_api_with_published_backfill",
    "public_api_with_raw_recovery",
    "public_api_with_raw_recovery_partial",
    "public_api_partial",
}
INDICADORES_NON_SYNTHETIC_DELIVERY = {
    "live",
    "published_backfill",
    "raw_recovery",
    "preserved_existing",
}
EXPECTED_DATASET_COUNT = 19
EXPECTED_TOP_ISSUE = "consumo_electrico_comunal"


def _assert_summary_has_recovery_source_detail(test_case, summary):
    test_case.assertTrue(
        any(source_detail in summary for source_detail in INDICADORES_RECOVERY_SOURCE_DETAILS),
        summary,
    )


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
                "finanzas_municipales",
                "resultados_educacionales",
                "indicadores_urbanos_siedu",
                "perfil_territorial_comunal",
                "empresas",
                "pobreza_comunal",
                "consumo_electrico_comunal",
                "partidos_politicos",
                "autoridades_electas",
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
        finanzas = self.hub.load_polars("finanzas_municipales")
        resultados = self.hub.load_polars("resultados_educacionales")
        siedu = self.hub.load_polars("indicadores_urbanos_siedu")
        perfil = self.hub.load_polars("perfil_territorial_comunal")
        self.assertEqual(censo.height, 346)
        self.assertGreater(salud.height, 5000)
        self.assertGreater(finanzas.height, 0)
        self.assertGreater(resultados.height, 0)
        self.assertGreater(siedu.height, 0)
        self.assertEqual(perfil.height, 346)
        self.assertEqual(censo["codigo_comuna"].str.len_chars().min(), 5)
        self.assertEqual(salud["codigo_comuna"].str.len_chars().min(), 5)

    def test_load_polars_empresas(self):
        """Carga condicional del dataset empresas (puede no estar presente)."""
        if "empresas" not in self.catalog_by_dataset:
            self.skipTest("Dataset empresas no esta en el catalogo — extractor no ejecutado aun.")
        df = self.hub.load_polars("empresas")
        self.assertGreater(df.height, 0)
        self.assertIn("rut", df.columns)
        self.assertIn("razon_social", df.columns)
        self.assertIn("codigo_sociedad", df.columns)
        # Verificar que los RUT son strings con formato esperado
        self.assertEqual(df["rut"].dtype, pl.String)

    def test_load_polars_missing_dataset(self):
        """load_polars con dataset inexistente lanza ChileHubDatasetError."""
        with self.assertRaises(ChileHubDatasetError) as ctx:
            self.hub.load_polars("dataset_inexistente")
        self.assertIn("dataset_inexistente", str(ctx.exception))

    def test_load_polars_corrupt_parquet(self):
        """load_polars con Parquet corrupto lanza ChileHubDatasetError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear un catálogo mínimo y un Parquet inválido
            catalog = {
                "datasets": [
                    {
                        "dataset": "corrupto",
                        "outputs": {"parquet": "corrupto.parquet"},
                    }
                ],
                "dataset_count": 1,
            }
            catalog_path = Path(tmpdir) / "dataset_catalog.json"
            catalog_path.write_text(json.dumps(catalog))
            (Path(tmpdir) / "corrupto.parquet").write_text("esto no es parquet")

            hub = ChileHub(data_dir=tmpdir)
            with self.assertRaises(ChileHubDatasetError) as ctx:
                hub.load_polars("corrupto")
            self.assertIn("corrupto", str(ctx.exception))

    def test_init_missing_catalog(self):
        """Constructor con data_dir inexistente lanza ChileHubDataError."""
        with self.assertRaises(ChileHubDataError) as ctx:
            ChileHub(data_dir="/tmp/no_existe_chile_hub_test")
        self.assertIn("Catálogo de datasets no encontrado", str(ctx.exception))

    def test_cache_clear_safety(self):
        """clear() con ruta fuera del cache esperado lanza ChileHubDataError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["CHILE_HUB_CACHE_DIR"] = tmpdir
            try:
                # Si la ruta no está bajo user_cache_dir, debe lanzar error
                from platformdirs import user_cache_dir

                expected = user_cache_dir("chile-hub")
                if not str(Path(tmpdir).resolve()).startswith(str(Path(expected).resolve())):
                    with self.assertRaises(ChileHubDataError) as ctx:
                        ChileHubDataManager().clear()
                    self.assertIn("Por seguridad", str(ctx.exception))
                else:
                    # Si por alguna razón está dentro, clear debería funcionar
                    manager = ChileHubDataManager()
                    manager.clear()
            finally:
                del os.environ["CHILE_HUB_CACHE_DIR"]

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
                "finanzas_municipales": "ok",
                "resultados_educacionales": "ok",
                "indicadores_urbanos_siedu": "ok",
                "perfil_territorial_comunal": "ok",
                "empresas": "ok",
                "pobreza_comunal": "ok",
                "consumo_electrico_comunal": "ok",
                "partidos_politicos": "ok",
                "autoridades_electas": "ok",
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
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("records", table)
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
        self.assertEqual(overview["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertGreaterEqual(overview["shared_artifact_count"], 1)
        self.assertGreaterEqual(overview["package_count"], 1)
        self.assertEqual(
            overview["current_fresh_count"]
            + overview["current_stale_count"]
            + overview["current_unknown_count"],
            EXPECTED_DATASET_COUNT,
        )
        self.assertTrue(overview["current_checked_at_utc"])
        self.assertIsNotNone(overview["top_issue"])
        self.assertEqual(overview["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, overview["top_issue_summary"])
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
        self.assertEqual(len(overview["datasets"]), EXPECTED_DATASET_COUNT)

    def test_status(self):
        status = self.hub.status()
        self.assertIn(status["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(status["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertIsNotNone(status["top_issue"])
        self.assertEqual(status["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, status["top_issue_summary"])

    def test_dataset_status_and_changelog(self):
        status = self.hub.dataset_status()
        changelog = self.hub.dataset_changelog()
        self.assertEqual(status["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(changelog["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(
            {entry["dataset"] for entry in status["datasets"]},
            set(self.catalog_by_dataset),
        )
        self.assertIn("record_count_delta", changelog["datasets"][0])

    def test_status_table(self):
        table = self.hub.status_table()
        self.assertIn("chile-hub status", table)
        self.assertIn("overall_status", table)
        self.assertIn("top_issue", table)
        self.assertIn("top_issue_summary", table)
        self.assertIn(EXPECTED_TOP_ISSUE, table)

    def test_overview_table(self):
        table = self.hub.overview_table()
        self.assertIn("chile-hub overview", table)
        self.assertIn("build_overall_status", table)
        self.assertIn("current_overall_status", table)
        self.assertIn("top_issue", table)
        self.assertIn("top_issue_reason", table)
        self.assertIn("top_issue_action", table)
        self.assertIn("top_issue_summary", table)
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("validation", table)
        self.assertIn("indicadores", table)

    def test_runtime_status_audit(self):
        audit = self.hub.runtime_status_audit()
        self.assertIn(audit["build_overall_status"], {"ok", "warn", "error"})
        self.assertIn(audit["current_overall_status"], {"ok", "warn", "error"})
        self.assertEqual(
            audit["fresh_count"] + audit["stale_count"] + audit["unknown_count"],
            EXPECTED_DATASET_COUNT,
        )
        self.assertTrue(audit["checked_at_utc"])

    def test_runtime_status(self):
        runtime = self.hub.runtime_status()
        self.assertIn(runtime["build_overall_status"], {"ok", "warn", "error"})
        self.assertIn(runtime["current_overall_status"], {"ok", "warn", "error"})
        self.assertEqual(
            runtime["fresh_count"] + runtime["stale_count"] + runtime["unknown_count"],
            EXPECTED_DATASET_COUNT,
        )
        self.assertEqual(runtime["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(len(runtime["datasets"]), EXPECTED_DATASET_COUNT)
        self.assertIsNotNone(runtime["top_issue"])
        self.assertEqual(runtime["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, runtime["top_issue_summary"])
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
        self.assertIn(f"top_issue={EXPECTED_TOP_ISSUE}", table)
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("severity", table)
        self.assertIn("indicadores", table)

    def test_top_issue(self):
        top_issue = self.hub.top_issue()
        self.assertIsNotNone(top_issue)
        self.assertEqual(top_issue["dataset"], EXPECTED_TOP_ISSUE)
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
        self.assertIn(EXPECTED_TOP_ISSUE, table)

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
        self.assertIn(f"top_issue: {EXPECTED_TOP_ISSUE}", snapshot)
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
        self.assertIn("dataset", snapshot)
        self.assertIn("mode", snapshot)
        self.assertIn("validation", snapshot)
        self.assertIn("build", snapshot)
        self.assertIn("current", snapshot)
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
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("records", table)
        self.assertIn("comunas", table)
        self.assertIn("indicadores", table)

    def test_unknown_dataset_raises(self):
        with self.assertRaises(KeyError):
            self.hub.get_dataset("no-existe")

    def test_typed_errors_keep_key_error_compatibility(self):
        with self.assertRaises(ChileHubDatasetError) as dataset_error:
            self.hub.get_dataset("comuna")
        self.assertIsInstance(dataset_error.exception, KeyError)
        self.assertIn("Quizás quisiste decir 'comunas'", str(dataset_error.exception))

        with self.assertRaises(ChileHubOutputError) as output_error:
            self.hub.get_output_path("comunas", "csv")
        self.assertIsInstance(output_error.exception, KeyError)
        self.assertIn("Output 'csv' no existe", str(output_error.exception))

        with self.assertRaises(ChileHubExampleError) as example_error:
            self.hub.example_usage("comunas", "sql")
        self.assertIsInstance(example_error.exception, KeyError)
        self.assertIn("Example 'sql' no existe", str(example_error.exception))

    def test_health_summary(self):
        health = self.health
        self.assertIn(health["overall_status"], {"ok", "warn", "error"})
        self.assertEqual(health["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(
            health["ok_count"] + health["warn_count"] + health["error_count"],
            EXPECTED_DATASET_COUNT,
        )
        self.assertEqual(
            health["publishable_count"]
            + health["review_terms_count"]
            + health["unknown_reuse_count"],
            EXPECTED_DATASET_COUNT,
        )
        self.assertEqual(
            health["degraded_count"]
            + health["degradation_warning_count"]
            + sum(1 for entry in health["datasets"] if entry["degradation_status"] == "none"),
            EXPECTED_DATASET_COUNT,
        )
        self.assertEqual(
            health["partial_coverage_count"]
            + health["unknown_coverage_count"]
            + sum(
                1
                for entry in health["datasets"]
                if entry["coverage_status"] in {"full", "not_applicable"}
            ),
            EXPECTED_DATASET_COUNT,
        )
        self.assertEqual(
            health["drifted_count"]
            + sum(1 for entry in health["datasets"] if entry["drift_status"] == "healthy"),
            EXPECTED_DATASET_COUNT,
        )

    def test_health_table(self):
        table = self.hub.health_table()
        self.assertIn("chile-hub health", table)
        self.assertIn(f"overall={self.health['overall_status']}", table)
        self.assertIn("dataset", table)
        self.assertIn("severity", table)
        self.assertIn("mode", table)
        self.assertIn("comunas", table)

    def test_freshness_audit(self):
        audit = self.hub.freshness_audit()
        self.assertEqual(audit["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(
            audit["fresh_count"] + audit["stale_count"] + audit["unknown_count"],
            EXPECTED_DATASET_COUNT,
        )
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
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("build", table)
        self.assertIn("indicadores", table)

    def test_bundle_summary(self):
        bundle = self.bundle
        self.assertEqual(bundle["overall_status"], self.health["overall_status"])
        self.assertEqual(bundle["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(bundle["public_dataset_count"], 17)
        self.assertEqual(bundle["candidate_dataset_count"], 2)
        self.assertEqual(len(bundle["datasets"]), bundle["public_dataset_count"])
        self.assertEqual(len(bundle["candidate_datasets"]), bundle["candidate_dataset_count"])
        # Verify candidate names (only candidates with real catalog outputs;
        # delincuencia_comunal/autoridades_locales are "próximamente" with no
        # outputs yet, so they never appear in dataset_catalog.json)
        candidate_names = {e["dataset"] for e in bundle["candidate_datasets"]}
        self.assertEqual(
            candidate_names,
            {
                "perfil_territorial_comunal",
                "consumo_electrico_comunal",
            },
        )
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
        self.assertEqual(bundle["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertEqual(bundle["health"]["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
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
        self.assertEqual(report["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(
            report["ready_count"] + report["review_terms_count"] + report["unknown_count"],
            EXPECTED_DATASET_COUNT,
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
        self.assertIn("dataset", table)
        self.assertIn("status", table)
        self.assertIn("indicadores", table)

    def test_provenance_report(self):
        report = self.hub.provenance()
        self.assertEqual(report["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(report["live_count"] + report["fallback_count"], EXPECTED_DATASET_COUNT)
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
        self.assertIn("dataset", table)
        self.assertIn("mode", table)
        self.assertIn("source", table)
        self.assertIn("warnings", table)
        self.assertIn("comunas", table)

    def test_drift_report(self):
        report = self.hub.drift()
        self.assertEqual(report["dataset_count"], EXPECTED_DATASET_COUNT)
        self.assertEqual(report["drifted_count"] + report["healthy_count"], EXPECTED_DATASET_COUNT)
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
        self.assertIn("dataset", table)
        self.assertIn("drift", table)
        self.assertIn("mode", table)
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

    # ── cross_view tests ────────────────────────────────────────────────────────

    def test_cross_view_basic(self):
        df = self.hub.cross_view(["comunas", "censo_comunal"])
        self.assertEqual(df.height, 346)
        self.assertIn("comunas_nombre_comuna", df.columns)
        self.assertIn("censo_comunal_poblacion_censada", df.columns)

    def test_cross_view_single_dataset_error(self):
        with self.assertRaises(ChileHubDatasetError):
            self.hub.cross_view(["comunas"])

    def test_cross_view_three_datasets(self):
        df = self.hub.cross_view(["comunas", "censo_comunal", "censo_hogares_viviendas"])
        self.assertEqual(df.height, 346)
        self.assertIn("comunas_nombre_comuna", df.columns)
        self.assertIn("censo_comunal_poblacion_censada", df.columns)
        self.assertIn("censo_hogares_viviendas_viviendas_censadas", df.columns)

    # ── validate_user_data tests ────────────────────────────────────────────────

    def test_validate_user_data_ok(self):
        import polars as pl

        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "01107"],
                "nombre_comuna": ["Iquique", "Alto Hospicio"],
                "codigo_provincia": ["011", "011"],
                "codigo_region": ["01", "01"],
                "nombre_comuna_clean": ["iquique", "alto hospicio"],
            }
        )
        result = self.hub.validate_user_data(df, "comunas")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_validate_user_data_missing_column(self):
        import polars as pl

        df = pl.DataFrame({"codigo_comuna": ["01101"]})
        result = self.hub.validate_user_data(df, "comunas")
        self.assertEqual(result["status"], "error")
        self.assertGreater(len(result["errors"]), 0)

    def test_validate_user_data_unknown_dataset(self):
        import polars as pl

        df = pl.DataFrame({"codigo_comuna": ["01101"]})
        with self.assertRaises(ChileHubDatasetError):
            self.hub.validate_user_data(df, "no_existe")

    def test_validate_user_data_duplicate_pk(self):
        import polars as pl

        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "01101"],
                "nombre_comuna": ["Iquique", "Iquique"],
                "codigo_provincia": ["011", "011"],
                "codigo_region": ["01", "01"],
                "nombre_comuna_clean": ["iquique", "iquique"],
            }
        )
        result = self.hub.validate_user_data(df, "comunas")
        self.assertEqual(result["status"], "error")
        self.assertTrue(
            any("duplicados" in e for e in result["errors"]),
            f"Esperaba error de duplicados, obtuve: {result['errors']}",
        )

    # ── validate_dataset tests ─────────────────────────────────────────────────

    def test_validate_dataset_ok(self):
        """Valida que un dataset del hub pase su propio contrato."""
        result = self.hub.validate_dataset("comunas")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_validate_dataset_unknown(self):
        """Valida que pedir un dataset inexistente lance error."""
        with self.assertRaises(ChileHubDatasetError):
            self.hub.validate_dataset("no_existe")

    def test_load_polars_validate_ok(self):
        """Valida que load_polars(validate=True) funcione con datos correctos."""
        df = self.hub.load_polars("comunas", validate=True)
        self.assertGreater(df.height, 0)
        self.assertIn("codigo_comuna", df.columns)

    def test_load_polars_validate_default(self):
        """Valida que load_polars() sin validate=True no lance validación."""
        df = self.hub.load_polars("comunas")
        self.assertGreater(df.height, 0)

    # ── search_datasets tests ───────────────────────────────────────────────────

    def test_search_datasets_query(self):
        results = self.hub.search_datasets(query="salud")
        self.assertGreaterEqual(len(results), 1)
        names = [r["name"] for r in results]
        self.assertIn("establecimientos_salud", names)

    def test_search_datasets_source(self):
        results = self.hub.search_datasets(source_name="INE")
        self.assertGreaterEqual(len(results), 1)

    def test_search_datasets_maturity(self):
        results = self.hub.search_datasets(maturity="stable")
        self.assertGreaterEqual(len(results), 1)

    def test_search_datasets_no_results(self):
        results = self.hub.search_datasets(query="zzz_no_existe")
        self.assertEqual(len(results), 0)


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
        self.assertEqual(self.catalog["dataset_count"], EXPECTED_DATASET_COUNT)

    def test_manifest_contains_expected_publishable_files(self):
        artifact_paths = {entry["path"] for entry in self.manifest["artifacts"]}
        self.assertIn("data/normalized/dataset_catalog.json", artifact_paths)
        self.assertIn("data/normalized/pipeline_status.md", artifact_paths)
        self.assertIn("data/normalized/hub_health.json", artifact_paths)
        self.assertIn("data/normalized/hub_status.json", artifact_paths)
        self.assertIn("data/normalized/dataset_status.json", artifact_paths)
        self.assertIn("data/normalized/dataset_changelog.json", artifact_paths)
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
        self.assertEqual(
            by_path["data/normalized/dataset_status.json"]["shared_type"], "dataset_status"
        )
        self.assertEqual(by_path["data/normalized/dataset_status.json"]["format"], "json")
        self.assertEqual(
            by_path["data/normalized/dataset_changelog.json"]["shared_type"],
            "dataset_changelog",
        )
        self.assertEqual(by_path["data/normalized/dataset_changelog.json"]["format"], "json")
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
        self.assertEqual(self.health["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, self.health["top_issue_summary"])
        self.assertTrue(self.health["top_issue"]["diagnostic_summary"])
        self.assertTrue(self.health["top_issue"]["source_detail"])
        self.assertIsNotNone(self.bundle["top_issue"])
        self.assertEqual(self.bundle["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, self.bundle["top_issue_summary"])
        self.assertTrue(self.bundle["top_issue"]["diagnostic_summary"])
        self.assertEqual(self.bundle["health"]["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, self.bundle["health"]["top_issue_summary"])
        self.assertTrue(self.bundle["health"]["top_issue"]["diagnostic_summary"])
        self.assertIsNotNone(self.overview["top_issue"])
        self.assertEqual(self.overview["top_issue"]["dataset"], EXPECTED_TOP_ISSUE)
        self.assertIn(EXPECTED_TOP_ISSUE, self.overview["top_issue_summary"])
        self.assertTrue(self.overview["top_issue"]["diagnostic_summary"])

    def test_top_issue_is_exposed_in_markdown_reports(self):
        self.assertIn(f"- `top_issue`: `{EXPECTED_TOP_ISSUE}`", self.overview_markdown)
        self.assertIn(f"- `top_issue`: `{EXPECTED_TOP_ISSUE}`", self.pipeline_status_markdown)
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
        self.assertIn(indicadores_catalog["source_detail"], INDICADORES_RECOVERY_SOURCE_DETAILS)
        self.assertEqual(
            indicadores_catalog["indicator_codes"],
            ["dolar", "euro", "ipc", "uf", "utm"],
        )
        for delivery in indicadores_catalog["indicator_delivery"].values():
            self.assertIn(delivery, INDICADORES_NON_SYNTHETIC_DELIVERY)
        self.assertTrue(indicadores_catalog["notes"])
        self.assertTrue(indicadores_catalog["warnings"])
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

    def run_cli_raw(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        return subprocess.run(
            [sys.executable, "-m", "chile_hub", *args],
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=False,
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
                "finanzas_municipales",
                "resultados_educacionales",
                "indicadores_urbanos_siedu",
                "perfil_territorial_comunal",
                "empresas",
                "pobreza_comunal",
                "consumo_electrico_comunal",
                "partidos_politicos",
                "autoridades_electas",
            ],
        )

    def test_cli_summary_table(self):
        result = self.run_cli("summary", "--format", "table")
        self.assertIn("chile-hub summary", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("records", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_path(self):
        result = self.run_cli("path", "comunas", "--output", "parquet")
        self.assertTrue(result.stdout.strip().endswith("data/normalized/comunas.parquet"))

    def test_cli_unknown_dataset_prints_clean_error(self):
        result = self.run_cli_raw("show", "comuna")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Error: Dataset 'comuna' no es válido", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

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
        self.assertIn('"report_key": "dataset_status_json"', result.stdout)
        self.assertIn('"report_key": "dataset_changelog_json"', result.stdout)
        self.assertIn('"report_key": "overview_markdown"', result.stdout)

    def test_cli_reports_table(self):
        result = self.run_cli("reports", "--format", "table")
        self.assertIn("chile-hub report index", result.stdout)
        self.assertIn("health_json", result.stdout)
        self.assertIn("status_json", result.stdout)
        self.assertIn("dataset_status_json", result.stdout)
        self.assertIn("overview_markdown", result.stdout)

    def test_cli_dataset_status_and_changelog(self):
        status = self.run_cli("dataset-status")
        changelog = self.run_cli("dataset-changelog")
        self.assertIn(f'"dataset_count": {EXPECTED_DATASET_COUNT}', status.stdout)
        self.assertIn('"dataset": "perfil_territorial_comunal"', status.stdout)
        self.assertIn(f'"dataset_count": {EXPECTED_DATASET_COUNT}', changelog.stdout)
        self.assertIn('"record_count_delta"', changelog.stdout)

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
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("records", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_snapshot(self):
        result = self.run_cli("snapshot")
        self.assertIn("chile-hub snapshot", result.stdout)
        self.assertIn(f"status_build: {self.health['overall_status']}", result.stdout)
        self.assertIn("status_current:", result.stdout)
        self.assertIn("current_freshness:", result.stdout)
        self.assertIn(f"top_issue: {EXPECTED_TOP_ISSUE}", result.stdout)
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
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("validation", result.stdout)
        self.assertIn("build", result.stdout)
        self.assertIn("current", result.stdout)
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
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("validation", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_health(self):
        result = self.run_cli("health")
        self.assertIn('"overall_status":', result.stdout)
        self.assertIn(f'"dataset_count": {EXPECTED_DATASET_COUNT}', result.stdout)
        self.assertIn('"review_terms_count":', result.stdout)
        self.assertIn('"partial_coverage_count":', result.stdout)
        self.assertIn('"drifted_count":', result.stdout)

    def test_cli_health_table(self):
        result = self.run_cli("health", "--format", "table")
        self.assertIn("chile-hub health", result.stdout)
        self.assertIn(f"overall={self.health['overall_status']}", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("severity", result.stdout)
        self.assertIn("mode", result.stdout)

    def test_pipeline_status_script_text(self):
        result = self.run_script("scripts/pipeline_status.py")
        self.assertIn("chile-hub pipeline status", result.stdout)
        self.assertIn(f"top_issue: {EXPECTED_TOP_ISSUE}", result.stdout)
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
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("build", result.stdout)
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
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("severity", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_top_issue(self):
        result = self.run_cli("top-issue")
        self.assertIn(f'"dataset": "{EXPECTED_TOP_ISSUE}"', result.stdout)
        self.assertIn('"drift_status": "drifted"', result.stdout)

    def test_cli_top_issue_text(self):
        result = self.run_cli("top-issue", "--format", "text")
        self.assertIn("chile-hub top issue", result.stdout)
        self.assertIn(f"dataset={EXPECTED_TOP_ISSUE}", result.stdout)
        self.assertIn(EXPECTED_TOP_ISSUE, result.stdout)
        self.assertIn("reason=", result.stdout)
        self.assertIn("action=", result.stdout)

    def test_cli_top_issue_table(self):
        result = self.run_cli("top-issue", "--format", "table")
        self.assertIn("chile-hub top issue", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn(EXPECTED_TOP_ISSUE, result.stdout)

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
        self.assertIn("dataset", result.stdout)
        self.assertIn("status", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_provenance(self):
        result = self.run_cli("provenance")
        self.assertIn('"live_count":', result.stdout)
        self.assertIn('"source_name":', result.stdout)

    def test_cli_provenance_table(self):
        result = self.run_cli("provenance", "--format", "table")
        self.assertIn("chile-hub provenance", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("source", result.stdout)
        self.assertIn("comunas", result.stdout)

    def test_cli_drift(self):
        result = self.run_cli("drift")
        self.assertIn('"drifted_count":', result.stdout)
        self.assertIn('"coverage_status":', result.stdout)

    def test_cli_drift_table(self):
        result = self.run_cli("drift", "--format", "table")
        self.assertIn("chile-hub drift", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("drift", result.stdout)
        self.assertIn("mode", result.stdout)
        self.assertIn("indicadores", result.stdout)

    def test_cli_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "regiones_export.csv")
            result = self.run_cli("export", "regiones", "--format", "csv", "--output", out_file)
            self.assertIn("exportado exitosamente", result.stdout)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("codigo_region", content)

    def test_cli_check_sources(self):
        result = self.run_cli("check-sources", "--timeout", "2", "--format", "table")
        self.assertIn("chile-hub check-sources", result.stdout)
        self.assertIn("dataset", result.stdout)
        self.assertIn("status", result.stdout)

    def test_cli_cross(self):
        result = self.run_cli("cross", "comunas", "censo_comunal", "--format", "json")
        self.assertIn("comunas_nombre_comuna", result.stdout)
        self.assertIn("censo_comunal_poblacion_censada", result.stdout)

    def test_cli_search(self):
        result = self.run_cli("search", "salud")
        self.assertIn("establecimientos_salud", result.stdout)

    def test_cli_search_source(self):
        result = self.run_cli("search", "--source", "INE")
        self.assertGreater(len(result.stdout.strip()), 0)

    def test_cli_search_maturity(self):
        result = self.run_cli("search", "--maturity", "stable")
        self.assertGreater(len(result.stdout.strip()), 0)

    def test_cli_validate_dataset_ok(self):
        """Valida que chile-hub validate comunas (sin path) funcione."""
        result = self.run_cli("validate", "comunas")
        self.assertIn('"status": "ok"', result.stdout)

    def test_cli_validate_dataset_error(self):
        """Valida que chile-hub validate no_existe muestre error."""
        result = self.run_cli_raw("validate", "no_existe")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no es válido", result.stderr)

    def test_cli_validate_ok(self):
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            csv_path = f.name
            pl.DataFrame(
                {
                    "codigo_comuna": ["01101"],
                    "nombre_comuna": ["Iquique"],
                    "codigo_provincia": ["011"],
                    "codigo_region": ["01"],
                    "nombre_comuna_clean": ["iquique"],
                }
            ).write_csv(csv_path)
        try:
            result = self.run_cli("validate", csv_path, "--dataset", "comunas")
            self.assertIn('"status": "ok"', result.stdout)
        finally:
            os.unlink(csv_path)

    def test_cli_validate_error(self):
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            csv_path = f.name
            pl.DataFrame(
                {
                    "codigo_comuna": ["01101"],
                }
            ).write_csv(csv_path)
        try:
            result = self.run_cli_raw("validate", csv_path, "--dataset", "comunas")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Columnas requeridas faltantes", result.stdout)
        finally:
            os.unlink(csv_path)

    def test_cli_health_exit_code(self):
        # Solo verifica que no crashea (exit code depende del estado real)
        result = self.run_cli_raw("health", "--exit-code", "--format", "json")
        self.assertIn("overall_status", result.stdout)


class WorkflowContractTests(unittest.TestCase):
    CRITICAL_STEP_NAMES_IN_ORDER: ClassVar[list[str]] = [
        "Extract source data (conditional)",
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
        cls.release_workflow_text = (
            ROOT_DIR / ".github" / "workflows" / "pypi-release.yml"
        ).read_text()
        cls.codeql_workflow_text = (ROOT_DIR / ".github" / "workflows" / "codeql.yml").read_text()
        cls.lgtm_text = (ROOT_DIR / "lgtm.yml").read_text()
        cls.monthly_workflow_text = (
            ROOT_DIR / ".github" / "workflows" / "monthly-scrape.yml"
        ).read_text()
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
        self.assertIn("profile=publication", self.workflow_text)
        self.assertIn("profile=readiness", self.workflow_text)
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
        self.assertIn("uv build", self.workflow_text)
        self.assertIn("uvx twine check dist/*", self.workflow_text)
        self.assertIn(
            'python -c "from chile_hub import ChileHub; print(ChileHub)"', self.workflow_text
        )
        self.assertIn("chile-hub cache status", self.workflow_text)

    def test_pypi_release_workflow_uses_trusted_publishing_and_release_assets(self):
        self.assertIn("id-token: write", self.release_workflow_text)
        self.assertIn("python -m semantic_release version --skip-build", self.release_workflow_text)
        self.assertIn(
            "steps.semantic-release.outputs.released == 'true'", self.release_workflow_text
        )
        self.assertIn("pypa/gh-action-pypi-publish", self.release_workflow_text)
        self.assertIn(
            "data/normalized/chile-hub-publishable-bundle.zip", self.release_workflow_text
        )
        self.assertIn("data/normalized/dataset_catalog.json", self.release_workflow_text)
        self.assertNotIn(
            'gh release create "$tag" --notes "Release $tag" || true', self.release_workflow_text
        )
        self.assertIn('gh release view "$tag"', self.release_workflow_text)

    def test_pipeline_artifact_records_publication_provenance(self):
        self.assertIn("pipeline_artifact_provenance.json", self.workflow_text)
        self.assertIn('"verification_profile": profile', self.workflow_text)
        self.assertIn('"require_live": profile == "publication"', self.workflow_text)
        self.assertIn('"source_run_event": "${{ github.event_name }}"', self.workflow_text)
        self.assertIn(
            "Readiness profile: this run may pass with fallback or sample data.", self.workflow_text
        )
        self.assertIn("Publication profile: live-source gates are enforced", self.workflow_text)

    def test_pypi_release_requires_publication_grade_data_assets(self):
        self.assertIn("pipeline_artifact_provenance.json", self.release_workflow_text)
        self.assertIn(
            "python scripts/verify_pipeline.py --require-live", self.release_workflow_text
        )
        self.assertIn("steps.pipeline-assets.outputs.ready == 'true'", self.release_workflow_text)
        self.assertIn("release data assets will not be attached", self.release_workflow_text)

    def test_pypi_release_keeps_uv_lock_in_release_commit(self):
        self.assertIn("--no-commit --no-tag --no-push --no-vcs-release", self.release_workflow_text)
        self.assertIn("uv lock", self.release_workflow_text)
        self.assertIn("uv lock --locked", self.release_workflow_text)
        self.assertIn("git add CHANGELOG.md pyproject.toml uv.lock", self.release_workflow_text)

    def test_monthly_scrape_uses_project_extras_not_dependency_groups(self):
        self.assertNotIn("uv sync --group dev", self.monthly_workflow_text)
        self.assertEqual(
            self.monthly_workflow_text.count("uv sync --extra pipeline --extra dev"), 2
        )
        self.assertEqual(self.monthly_workflow_text.count("uv lock --locked"), 2)
        self.assertIn("Validate SINIM staging output", self.monthly_workflow_text)
        self.assertNotIn("uv run make build", self.monthly_workflow_text)
        self.assertNotIn("git add --ignore-missing", self.monthly_workflow_text)
        self.assertEqual(
            self.monthly_workflow_text.count('[ -e "$path" ] && git add -f "$path"'), 2
        )

    def test_codeql_python_analysis_uses_no_build_mode(self):
        self.assertIn("languages: python", self.codeql_workflow_text)
        self.assertIn("build-mode: none", self.codeql_workflow_text)
        self.assertIn(
            "CODEQL_EXTRACTOR_PYTHON_OPTION_PYTHON_EXECUTABLE_NAME: python3",
            self.codeql_workflow_text,
        )
        self.assertIn("Provide Python 2 legacy probe shim", self.codeql_workflow_text)
        self.assertIn("python_setup:", self.lgtm_text)
        self.assertIn("version: 3", self.lgtm_text)

    def test_testpypi_workflow_smoke_tests_installed_console_script(self):
        testpypi_text = (ROOT_DIR / ".github" / "workflows" / "testpypi.yml").read_text()
        self.assertIn("repository-url: https://test.pypi.org/legacy/", testpypi_text)
        self.assertIn("uv build", testpypi_text)
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


# ── Dataset enum tests ─────────────────────────────────────────────────────


class DatasetEnumTests(unittest.TestCase):
    """Tests para el enum Dataset en src/chile_hub/datasets.py."""

    def test_members_are_strings(self):
        from src.chile_hub.datasets import Dataset

        for member in Dataset:
            self.assertIsInstance(member.value, str)
            self.assertIsInstance(member, str)

    def test_from_string_exact(self):
        from src.chile_hub.datasets import Dataset

        self.assertIs(Dataset.from_string("comunas"), Dataset.COMUNAS)
        self.assertIs(Dataset.from_string("regiones"), Dataset.REGIONES)
        self.assertIs(Dataset.from_string("empresas"), Dataset.EMPRESAS)

    def test_from_string_with_typo_suggests(self):
        from src.chile_hub.datasets import Dataset

        with self.assertRaises(ValueError) as ctx:
            Dataset.from_string("comuna")
        self.assertIn("Quizás quisiste decir 'comunas'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Dataset.from_string("indicadore")
        self.assertIn("Quizás quisiste decir 'indicadores'", str(ctx.exception))

    def test_from_string_unknown_raises(self):
        from src.chile_hub.datasets import Dataset

        with self.assertRaises(ValueError):
            Dataset.from_string("no_existe")

    def test_values_match_catalog(self):
        import json
        from pathlib import Path

        from src.chile_hub.datasets import Dataset

        catalog_path = Path("data/normalized/dataset_catalog.json")
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog_ids = {entry["dataset"] for entry in catalog["datasets"]}

        vals = Dataset.values()
        self.assertEqual(set(vals), catalog_ids)
        self.assertIn("comunas", vals)
        self.assertIn("regiones", vals)
        self.assertIn("empresas", vals)

    def test_all_datasets_have_corresponding_contract(self):
        from pathlib import Path

        from src.chile_hub.datasets import Dataset

        contracts_dir = Path(__file__).resolve().parents[1] / "contracts" / "datasets"
        for member in Dataset:
            contract_path = contracts_dir / f"{member.value}.schema.json"
            self.assertTrue(
                contract_path.exists(),
                f"Dataset '{member.value}' no tiene contrato en {contract_path}",
            )

    def test_load_polars_with_enum(self):
        from src.chile_hub.datasets import Dataset

        hub = self._get_hub()
        df = hub.load_polars(Dataset.COMUNAS)
        self.assertGreater(df.height, 0)
        self.assertIn("codigo_comuna", df.columns)

    def test_load_polars_with_enum_validate(self):
        from src.chile_hub.datasets import Dataset

        hub = self._get_hub()
        df = hub.load_polars(Dataset.COMUNAS, validate=True)
        self.assertGreater(df.height, 0)

    def test_get_dataset_with_enum(self):
        from src.chile_hub.datasets import Dataset

        hub = self._get_hub()
        meta = hub.get_dataset(Dataset.COMUNAS)
        self.assertEqual(meta["dataset"], "comunas")

    def test_cross_view_with_enum(self):
        from src.chile_hub.datasets import Dataset

        hub = self._get_hub()
        df = hub.cross_view([Dataset.COMUNAS, Dataset.CENSO_COMUNAL])
        self.assertGreater(df.height, 0)

    def _get_hub(self):
        from src.chile_hub import ChileHub

        return ChileHub()


class EntryPointTests(unittest.TestCase):
    """Smoke tests para puntos de entrada y código de inicialización."""

    def test_module_main_executable(self):
        """python -m chile_hub --help ejecuta sin errores."""
        result = subprocess.run(
            [sys.executable, "-m", "chile_hub", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("chile-hub", result.stdout)

    def test_get_version_fallback_to_hardcoded(self):
        """_get_version retorna '0.0.0' cuando pyproject.toml no existe
        e importlib.metadata.version lanza PackageNotFoundError."""
        from importlib.metadata import PackageNotFoundError
        from pathlib import Path as _Path

        from src.chile_hub.__init__ import _get_version

        with (
            patch.object(_Path, "is_file", return_value=False),
            patch(
                "importlib.metadata.version",
                side_effect=PackageNotFoundError("package not found"),
            ),
        ):
            version = _get_version()
            self.assertEqual(version, "0.0.0")

    def test_chile_hub_key_error_empty_args(self):
        """_ChileHubKeyError sin args produce string vacío."""
        from src.chile_hub.exceptions import _ChileHubKeyError

        error = _ChileHubKeyError()
        self.assertEqual(str(error), "")

    def test_chile_hub_key_error_with_message(self):
        """_ChileHubKeyError con mensaje produce el mensaje."""
        from src.chile_hub.exceptions import _ChileHubKeyError

        error = _ChileHubKeyError("dataset no encontrado")
        self.assertEqual(str(error), "dataset no encontrado")


class ChileHubConstructorTests(unittest.TestCase):
    """Edge cases del constructor ChileHub."""

    def test_rejects_both_catalog_path_and_data_dir(self):
        """catalog_path + data_dir simultáneos lanza ValueError."""
        from chile_hub import ChileHub

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                ChileHub(catalog_path=Path(tmp) / "catalog.json", data_dir=tmp)

    def test_falls_back_to_data_manager_when_no_catalog(self):
        """Usa el catálogo empaquetado cuando no hay data_dir ni catalog_path explícito."""
        from chile_hub import ChileHub

        hub = ChileHub()
        self.assertIsNotNone(hub.catalog)
        self.assertIn("dataset_count", hub.catalog)

    def test_constructor_with_explicit_catalog_path(self):
        """Constructor acepta catalog_path directo a un JSON de catálogo."""
        from chile_hub import ChileHub

        with tempfile.TemporaryDirectory() as tmp:
            import json

            cat = {"datasets": [], "dataset_count": 0}
            cat_path = Path(tmp) / "catalog.json"
            cat_path.write_text(json.dumps(cat))
            hub = ChileHub(catalog_path=str(cat_path))
            self.assertEqual(hub.catalog, cat)

    def test_format_available_with_values(self):
        """_format_available sugiere datasets disponibles."""
        from src.chile_hub.core import _format_available

        result = _format_available(["comunas", "regiones", "provincias"], "comunas")
        self.assertIn("Disponibles", result)

    def test_format_available_exact_match(self):
        """_format_available sin match sugiere valores cercanos."""
        from src.chile_hub.core import _format_available

        result = _format_available(["comuna", "comunas_enriquecidas"], "comunas")
        self.assertIn("Quizas", result)

    def test_format_available_empty_values(self):
        """_format_available con lista vacía."""
        from src.chile_hub.core import _format_available

        result = _format_available([], "x")
        self.assertIn("Disponibles", result)


class ChileHubReportTablesTests(unittest.TestCase):
    """Tests de smoke para métodos de tabla de reportes."""

    @classmethod
    def setUpClass(cls):
        _assert_normalized_not_stale()
        cls.hub = ChileHub()

    def test_freshness_audit_table_output(self):
        table = self.hub.freshness_audit_table()
        self.assertIn("chile-hub freshness audit", table)
        self.assertIn("dataset", table)

    def test_redistribution_table_output(self):
        table = self.hub.redistribution_table()
        self.assertIn("chile-hub", table)

    def test_provenance_table_output(self):
        table = self.hub.provenance_table()
        self.assertIn("chile-hub", table)

    def test_drift_table_output(self):
        table = self.hub.drift_table()
        self.assertIn("chile-hub", table)

    def test_overview_table_output(self):
        table = self.hub.overview_table()
        self.assertIn("chile-hub", table)


class ChileHubDataManagerUnitTests(unittest.TestCase):
    """Tests unitarios para métodos internos de ChileHubDataManager."""

    def test_sha256_static_method(self):
        """_sha256() retorna el hash SHA-256 correcto para un archivo."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"contenido de prueba")
            temp_path = Path(f.name)
        try:
            digest = ChileHubDataManager._sha256(temp_path)
            expected = hashlib.sha256(b"contenido de prueba").hexdigest()
            self.assertEqual(digest, expected)
        finally:
            temp_path.unlink()

    def test_require_asset_missing_raises_error(self):
        """_require_asset() con nombre ausente lanza ChileHubDataError."""
        assets = {"bundle.zip": ReleaseAsset(name="bundle.zip", url="http://example.com")}
        with self.assertRaises(ChileHubDataError) as ctx:
            ChileHubDataManager._require_asset(assets, "inexistente.zip")
        self.assertIn("inexistente.zip", str(ctx.exception))
        self.assertIn("bundle.zip", str(ctx.exception))

    def test_read_json_missing_file_returns_empty_dict(self):
        """_read_json() con archivo inexistente retorna {}."""
        result = ChileHubDataManager._read_json(Path("/tmp/no_existe_xyz_123.json"))
        self.assertEqual(result, {})

    def test_cache_clear_when_not_exists_returns_early(self):
        """clear() cuando el caché no existe retorna sin error."""
        from platformdirs import user_cache_dir

        expected_parent = user_cache_dir("chile-hub")
        # Usar un subdirectorio que no existe dentro del árbol esperado
        cache_dir = Path(expected_parent) / "_test_clear_nonexistent_xyz"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Crear manager con ese cache_dir
            manager = ChileHubDataManager(cache_dir=cache_dir)
            # Borrar el directorio para que no exista
            shutil.rmtree(str(cache_dir))
            # clear() no debe lanzar error
            manager.clear()
        finally:
            if cache_dir.exists():
                shutil.rmtree(str(cache_dir))

    def test_cache_clear_when_exists_removes_directory(self):
        """clear() cuando el caché existe elimina el directorio."""
        from platformdirs import user_cache_dir

        expected_parent = user_cache_dir("chile-hub")
        cache_dir = Path(expected_parent) / "_test_clear_exists_xyz"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / "test_file.txt").write_text("data")
            self.assertTrue(cache_dir.exists())
            manager = ChileHubDataManager(cache_dir=cache_dir)
            manager.clear()
            self.assertFalse(cache_dir.exists())
        finally:
            if cache_dir.exists():
                shutil.rmtree(str(cache_dir))

    def test_extract_bundle_cleans_existing_normalized_dir(self):
        """_extract_bundle() elimina normalized_dir existente antes de extraer."""
        from platformdirs import user_cache_dir

        expected_parent = user_cache_dir("chile-hub")
        cache_root = Path(expected_parent) / "_test_extract_xyz"
        try:
            cache_root.mkdir(parents=True, exist_ok=True)
            manager = ChileHubDataManager(cache_dir=cache_root, data_version="v0.0.0-test")
            manager.version_cache_dir.mkdir(parents=True, exist_ok=True)
            # Crear un normalized_dir falso con un archivo marcador
            manager.normalized_dir.mkdir(parents=True, exist_ok=True)
            marker = manager.normalized_dir / "test_sentinel.txt"
            marker.write_text("old")
            self.assertTrue(marker.exists())

            # Crear un ZIP mínimo para extraer
            bundle_path = manager.version_cache_dir / "test_bundle.zip"
            with zipfile.ZipFile(bundle_path, "w") as zf:
                zf.writestr("data/normalized/new_file.txt", "new content")

            manager._extract_bundle(bundle_path)
            # El marcador antiguo debe haber desaparecido
            self.assertFalse(marker.exists())
            # El nuevo archivo debe existir
            new_file = manager.normalized_dir / "new_file.txt"
            self.assertTrue(new_file.exists())
        finally:
            if cache_root.exists():
                shutil.rmtree(str(cache_root))


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
