import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scripts import package_publishable_bundle
from scripts.verify_pipeline import verify_publication_policy
from src.build_dev_db import (
    build_coverage,
    build_degradation,
    build_drift,
    load_metadata,
    write_publishable_bundle_zip,
)
from src.build_dev_db import (
    main as build_main,
)
from src.extractors import bcentral_extractor
from src.pipeline_status_utils import build_hub_health, build_status_text
from src.validation import (
    EXPECTED_INDICATOR_CODES,
    EXPECTED_LIVE_COMUNAS_COUNT,
    FALLBACK_COMUNAS_COUNT,
    validate_comunas,
    validate_provincias,
    validate_regiones,
)


class PipelineLogicTests(unittest.TestCase):
    def test_build_main_fails_when_staging_inputs_are_missing(self):
        with (
            patch("src.build_dev_db.ensure_directories"),
            patch("src.build_dev_db.os.path.exists", return_value=False),
            self.assertRaisesRegex(SystemExit, "No se encuentran los archivos CSV"),
        ):
            build_main()

    def test_build_main_fails_when_metadata_inputs_are_missing(self):
        def mock_exists(path):
            if str(path).endswith(".csv"):
                return True
            return False

        with (
            patch("src.build_dev_db.ensure_directories"),
            patch("src.build_dev_db.os.path.exists", side_effect=mock_exists),
            self.assertRaisesRegex(SystemExit, "No se encuentra comunas.metadata.json"),
        ):
            build_main()

    def test_load_metadata_fails_on_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_json_file = Path(tmpdir) / "bad.json"
            bad_json_file.write_text("{invalid json", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "contiene un JSON malformado"):
                load_metadata(str(bad_json_file))

    def test_load_metadata_fails_on_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            incomplete_json_file = Path(tmpdir) / "incomplete.json"
            incomplete_metadata = {
                "dataset": "comunas",
                "source_name": "SUBDERE",
                # missing other fields
            }
            incomplete_json_file.write_text(json.dumps(incomplete_metadata), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "no cumple con el esquema obligatorio"):
                load_metadata(str(incomplete_json_file))

    def test_publication_policy_accepts_fresh_live_data(self):
        datasets = {
            name: {
                "source_mode": "live",
                "source_detail": "public_api",
                "freshness": {"status": "fresh"},
            }
            for name in [
                "regiones",
                "provincias",
                "comunas",
                "comunas_enriquecidas",
                "indicadores",
                "censo_comunal",
                "censo_hogares_viviendas",
                "establecimientos_salud",
                "establecimientos_educacionales",
                "distritos_electorales",
            ]
        }
        datasets["indicadores"]["indicator_delivery"] = {
            code: "live" for code in EXPECTED_INDICATOR_CODES
        }

        verify_publication_policy({"datasets": datasets})

    def test_publication_policy_accepts_clean_published_monthly_backfill(self):
        datasets = {
            name: {
                "source_mode": "live",
                "source_detail": "public_api",
                "freshness": {"status": "fresh"},
            }
            for name in [
                "regiones",
                "provincias",
                "comunas",
                "comunas_enriquecidas",
                "indicadores",
                "censo_comunal",
                "censo_hogares_viviendas",
                "establecimientos_salud",
                "establecimientos_educacionales",
                "distritos_electorales",
            ]
        }
        datasets["indicadores"].update(
            {
                "source_detail": "public_api_with_published_backfill",
                "indicator_delivery": {"ipc": "published_backfill", "uf": "live"},
                "published_backfills": ["ipc"],
                "fetch_failures": [],
                "raw_recoveries": [],
                "preserved_existing_pairs": [],
                "empty_live_pairs": [],
            }
        )

        verify_publication_policy({"datasets": datasets})

    def test_publication_policy_rejects_fallback_and_partial_delivery(self):
        datasets = {
            name: {
                "source_mode": "live",
                "source_detail": "public_api",
                "freshness": {"status": "fresh"},
            }
            for name in [
                "regiones",
                "provincias",
                "comunas",
                "comunas_enriquecidas",
                "indicadores",
            ]
        }
        datasets["comunas"]["source_mode"] = "fallback"
        datasets["indicadores"].update(
            {
                "source_detail": "public_api_partial",
                "indicator_delivery": {"uf": "preserved_existing"},
                "fetch_failures": ["uf/2026: timeout"],
                "preserved_existing_pairs": ["uf/2026"],
            }
        )

        with (
            patch("builtins.print") as print_mock,
            self.assertRaisesRegex(SystemExit, "1"),
        ):
            verify_publication_policy({"datasets": datasets})

        self.assertIn("Publication policy rejected", print_mock.call_args.args[0])

    def test_write_publishable_bundle_zip_fails_before_creating_partial_zip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            normalized_dir = data_dir / "normalized"
            normalized_dir.mkdir(parents=True)
            manifest = {"artifacts": [{"path": "data/normalized/no-existe.parquet"}]}
            (normalized_dir / "artifact_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            with (
                patch("src.build_dev_db.NORMALIZED_DIR", str(normalized_dir)),
                patch("src.build_dev_db.DATA_DIR", str(data_dir)),
                self.assertRaisesRegex(SystemExit, "no-existe.parquet"),
            ):
                write_publishable_bundle_zip()

            self.assertFalse((normalized_dir / "chile-hub-publishable-bundle.zip").exists())

    def test_clean_publishable_removes_only_manifest_declared_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_file = root / "data" / "normalized" / "artifact_manifest.json"
            artifact_one = root / "data" / "normalized" / "dataset_catalog.json"
            artifact_two = root / "data" / "normalized" / "hub_status.json"
            package_zip = root / "data" / "normalized" / "bundle.zip"
            checksum = root / "data" / "normalized" / "bundle.zip.sha256"
            unrelated = root / "data" / "normalized" / "keep.me"

            for path in [
                manifest_file,
                artifact_one,
                artifact_two,
                package_zip,
                checksum,
                unrelated,
            ]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x", encoding="utf-8")

            manifest = {
                "artifacts": [
                    {"path": "data/normalized/artifact_manifest.json"},
                    {"path": "data/normalized/dataset_catalog.json"},
                    {"path": "data/normalized/hub_status.json"},
                    {"path": "data/normalized/hub_status.json"},
                ],
                "packages": [
                    {
                        "path": "data/normalized/bundle.zip",
                        "checksum_path": "data/normalized/bundle.zip.sha256",
                    },
                ],
            }

            removed = package_publishable_bundle.clean_publishable(manifest, root)

            self.assertEqual(
                removed,
                [
                    "data/normalized/dataset_catalog.json",
                    "data/normalized/hub_status.json",
                    "data/normalized/bundle.zip",
                    "data/normalized/bundle.zip.sha256",
                    "data/normalized/artifact_manifest.json",
                ],
            )
            self.assertFalse(manifest_file.exists())
            self.assertFalse(artifact_one.exists())
            self.assertFalse(artifact_two.exists())
            self.assertFalse(package_zip.exists())
            self.assertFalse(checksum.exists())
            self.assertTrue(unrelated.exists())

    def test_clean_publishable_removes_manifest_last(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for relative_path in [
                "data/normalized/artifact_manifest.json",
                "data/normalized/hub_status.json",
                "data/normalized/dataset_catalog.json",
            ]:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x", encoding="utf-8")

            manifest = {
                "artifacts": [
                    {"path": "data/normalized/artifact_manifest.json"},
                    {"path": "data/normalized/hub_status.json"},
                    {"path": "data/normalized/dataset_catalog.json"},
                ],
                "packages": [],
            }

            removed = package_publishable_bundle.clean_publishable(
                manifest,
                root_dir=root,
            )

            self.assertEqual(removed[-1], "data/normalized/artifact_manifest.json")

    def test_clean_publishable_from_manifest_is_idempotent_when_manifest_is_missing(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = root / "data" / "normalized" / "artifact_manifest.json"

            self.assertEqual(
                package_publishable_bundle.clean_publishable_from_manifest(
                    manifest_path=manifest_path,
                    root_dir=root,
                ),
                [],
            )

    def test_load_existing_staging_returns_consistent_empty_tuple_without_staging_file(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            staging_path = str(Path(tmpdir) / "indicadores.csv")
            published_path = str(Path(tmpdir) / "indicadores.parquet")
            original_staging = bcentral_extractor.STAGING_CSV_PATH
            original_published = bcentral_extractor.PUBLISHED_INDICATORS_PATH
            try:
                bcentral_extractor.STAGING_CSV_PATH = staging_path
                bcentral_extractor.PUBLISHED_INDICATORS_PATH = published_path
                self.assertEqual(
                    bcentral_extractor.load_existing_staging(),
                    (None, None, []),
                )
            finally:
                bcentral_extractor.STAGING_CSV_PATH = original_staging
                bcentral_extractor.PUBLISHED_INDICATORS_PATH = original_published

    def test_build_coverage_full_for_expected_cardinality(self):
        coverage = build_coverage("comunas", {"record_count": 346})

        self.assertEqual(coverage["status"], "full")
        self.assertEqual(coverage["expected_record_count"], 346)
        self.assertEqual(coverage["actual_record_count"], 346)
        self.assertEqual(coverage["coverage_ratio"], 1.0)
        self.assertIn("Cobertura completa", coverage["summary"])

    def test_build_coverage_partial_when_below_baseline(self):
        coverage = build_coverage("provincias", {"record_count": 12})

        self.assertEqual(coverage["status"], "partial")
        self.assertEqual(coverage["expected_record_count"], 56)
        self.assertEqual(coverage["actual_record_count"], 12)
        self.assertEqual(coverage["coverage_ratio"], 0.2143)
        self.assertIn("Cobertura parcial", coverage["summary"])

    def test_build_coverage_not_applicable_without_baseline(self):
        coverage = build_coverage("indicadores", {"record_count": 5})

        self.assertEqual(coverage["status"], "not_applicable")
        self.assertIsNone(coverage["expected_record_count"])
        self.assertEqual(coverage["actual_record_count"], 5)
        self.assertIsNone(coverage["coverage_ratio"])

    def test_build_degradation_marks_fallback_comunas_as_degraded(self):
        degradation = build_degradation(
            "comunas",
            {"source_mode": "fallback", "record_count": 18},
            {"warnings": []},
        )

        self.assertEqual(degradation["status"], "degraded")
        self.assertIn("18 comunas", degradation["impact"])
        self.assertIn("fuente territorial primaria", degradation["recommended_action"])

    def test_build_degradation_uses_warning_status_when_validation_warns(self):
        degradation = build_degradation(
            "indicadores",
            {"source_mode": "live", "record_count": 5},
            {"warnings": ["schema changed", "freshness borderline"]},
        )

        self.assertEqual(degradation["status"], "warning")
        self.assertIn("schema changed", degradation["impact"])
        self.assertIn("freshness borderline", degradation["impact"])
        self.assertIn("warnings operativos", degradation["recommended_action"])

    def test_build_drift_is_healthy_for_live_full_non_degraded_dataset(self):
        drift = build_drift(
            {
                "source_mode": "live",
                "coverage": {"status": "full"},
                "degradation": {"status": "none"},
            }
        )

        self.assertEqual(drift["status"], "healthy")
        self.assertIn("Sin drift operativo", drift["summary"])
        self.assertEqual(drift["recommended_action"], "Ninguna.")

    def test_build_drift_is_drifted_for_fallback_partial_degraded_dataset(self):
        drift = build_drift(
            {
                "source_mode": "fallback",
                "coverage": {"status": "partial"},
                "degradation": {"status": "degraded"},
            }
        )

        self.assertEqual(drift["status"], "drifted")
        self.assertIn("mode=fallback", drift["summary"])
        self.assertIn("coverage=partial", drift["summary"])
        self.assertIn("degradation=degraded", drift["summary"])
        self.assertIn("Revisar fuente, cobertura y warnings", drift["recommended_action"])

    def test_build_hub_health_aggregates_severity_and_operational_counts(self):
        metadata = {
            "generated_at_utc": "2026-06-01T12:00:00+00:00",
            "datasets": {
                "alpha": {
                    "source_mode": "live",
                    "freshness": {"status": "fresh"},
                    "reuse_policy": {
                        "status": "open-attribution",
                        "redistribution_ok": True,
                    },
                    "degradation": {"status": "none"},
                    "coverage": {"status": "full", "coverage_ratio": 1.0},
                    "drift": {"status": "healthy"},
                },
                "beta": {
                    "source_mode": "fallback",
                    "freshness": {"status": "stale"},
                    "reuse_policy": {
                        "status": "public-api-review-terms",
                        "redistribution_ok": False,
                    },
                    "degradation": {"status": "degraded"},
                    "coverage": {"status": "partial", "coverage_ratio": 0.5},
                    "drift": {"status": "drifted"},
                },
                "gamma": {
                    "source_mode": "live",
                    "freshness": {"status": "unknown"},
                    "reuse_policy": {"status": "unknown", "redistribution_ok": None},
                    "degradation": {"status": "warning"},
                    "coverage": {"status": "unknown", "coverage_ratio": None},
                    "drift": {"status": "drifted"},
                },
            },
            "validations": {
                "alpha": {"status": "ok", "warnings": []},
                "beta": {"status": "ok", "warnings": ["fallback active"]},
                "gamma": {"status": "error", "warnings": ["missing baseline"]},
            },
        }

        health = build_hub_health(metadata)
        by_dataset = {entry["dataset"]: entry for entry in health["datasets"]}

        self.assertEqual(health["overall_status"], "error")
        self.assertEqual(health["dataset_count"], 3)
        self.assertEqual(health["ok_count"], 1)
        self.assertEqual(health["warn_count"], 1)
        self.assertEqual(health["error_count"], 1)
        self.assertEqual(health["live_count"], 2)
        self.assertEqual(health["fallback_count"], 1)
        self.assertEqual(health["stale_count"], 1)
        self.assertEqual(health["unknown_freshness_count"], 1)
        self.assertEqual(health["publishable_count"], 1)
        self.assertEqual(health["review_terms_count"], 1)
        self.assertEqual(health["unknown_reuse_count"], 1)
        self.assertEqual(health["degraded_count"], 1)
        self.assertEqual(health["degradation_warning_count"], 1)
        self.assertEqual(health["partial_coverage_count"], 1)
        self.assertEqual(health["unknown_coverage_count"], 1)
        self.assertEqual(health["drifted_count"], 2)
        self.assertEqual(health["warning_count"], 2)

        self.assertEqual(by_dataset["alpha"]["severity"], "ok")
        self.assertEqual(by_dataset["beta"]["severity"], "warn")
        self.assertEqual(by_dataset["gamma"]["severity"], "error")
        self.assertEqual(by_dataset["alpha"]["publishability_status"], "ready")
        self.assertEqual(by_dataset["beta"]["publishability_status"], "review_terms")
        self.assertEqual(by_dataset["gamma"]["publishability_status"], "unknown")

    def test_build_status_text_includes_top_issue_reason_and_action(self):
        metadata = {
            "generated_at_utc": "2026-06-01T12:00:00+00:00",
            "datasets": {
                "alpha": {
                    "source_name": "Alpha Source",
                    "source_mode": "live",
                    "source_detail": "alpha_live",
                    "record_count": 10,
                    "fields": ["id"],
                    "notes": [],
                    "freshness": {"status": "fresh", "summary": "fresh"},
                    "coverage": {"status": "full", "summary": "Cobertura completa"},
                    "reuse_policy": {
                        "status": "open-attribution",
                        "redistribution_ok": True,
                    },
                    "degradation": {
                        "status": "none",
                        "impact": "Sin impacto.",
                        "recommended_action": "Ninguna.",
                    },
                    "drift": {
                        "status": "healthy",
                        "summary": "Sin drift operativo.",
                        "recommended_action": "Ninguna.",
                    },
                },
                "beta": {
                    "source_name": "Beta Source",
                    "source_mode": "live",
                    "source_detail": "beta_partial",
                    "record_count": 5,
                    "fields": ["id", "value"],
                    "notes": ["empty_live_pairs: ipc/2026"],
                    "freshness": {"status": "fresh", "summary": "fresh"},
                    "coverage": {
                        "status": "not_applicable",
                        "summary": "Sin baseline esperado.",
                    },
                    "reuse_policy": {
                        "status": "open-attribution",
                        "redistribution_ok": True,
                    },
                    "degradation": {
                        "status": "warning",
                        "impact": "Serie vacia detectada.",
                        "recommended_action": "Revisar warnings operativos del dataset antes de consumirlo en producción.",
                    },
                    "drift": {
                        "status": "drifted",
                        "summary": "Drift operativo detectado: warnings activos.",
                        "recommended_action": "Revisar warnings operativos del dataset antes de consumirlo en producción.",
                    },
                },
            },
            "validations": {
                "alpha": {"status": "ok", "warnings": []},
                "beta": {
                    "status": "ok",
                    "warnings": [
                        "indicadores live refresh returned empty series for: ipc/2026",
                    ],
                },
            },
        }

        status_text = build_status_text(metadata)

        self.assertIn("top_issue: beta", status_text)
        self.assertIn(
            "top_issue_reason: indicadores live refresh returned empty series for: ipc/2026",
            status_text,
        )
        self.assertIn(
            "top_issue_action: Revisar warnings operativos del dataset antes de consumirlo en producción.",
            status_text,
        )
        self.assertIn(
            "top_issue_summary: beta: indicadores live refresh returned empty series for: ipc/2026",
            status_text,
        )
        self.assertIn(
            "hub_status_json: data/normalized/hub_status.json",
            status_text,
        )


class ValidatorTests(unittest.TestCase):
    def test_validate_regiones_accepts_valid_data(self):
        df = pl.DataFrame(
            {
                "codigo_region": ["01", "02"],
                "nombre_region": ["Tarapaca", "Antofagasta"],
            }
        )
        self.assertEqual(validate_regiones(df)["status"], "ok")

    def test_validate_regiones_rejects_empty_and_duplicate_data(self):
        empty = pl.DataFrame({"codigo_region": pl.Series([], dtype=pl.String)})
        duplicate = pl.DataFrame({"codigo_region": ["01", "01"]})
        self.assertEqual(validate_regiones(empty)["status"], "error")
        self.assertEqual(validate_regiones(duplicate)["status"], "error")

    def test_validate_provincias_accepts_valid_data(self):
        df = pl.DataFrame({"codigo_region": ["01", "01"], "codigo_provincia": ["011", "014"]})
        self.assertEqual(validate_provincias(df)["status"], "ok")

    def test_validate_provincias_rejects_empty_and_duplicate_keys(self):
        empty = pl.DataFrame(
            {
                "codigo_region": pl.Series([], dtype=pl.String),
                "codigo_provincia": pl.Series([], dtype=pl.String),
            }
        )
        duplicate = pl.DataFrame(
            {"codigo_region": ["01", "01"], "codigo_provincia": ["011", "011"]}
        )
        self.assertEqual(validate_provincias(empty)["status"], "error")
        self.assertEqual(validate_provincias(duplicate)["status"], "error")

    def test_validate_comunas_accepts_complete_live_data(self):
        codes = [str(i).zfill(5) for i in range(EXPECTED_LIVE_COMUNAS_COUNT)]
        result = validate_comunas(pl.DataFrame({"codigo_comuna": codes}), {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")

    def test_validate_comunas_rejects_incomplete_or_duplicate_live_data(self):
        incomplete = pl.DataFrame({"codigo_comuna": ["01101", "01102"]})
        duplicate = pl.DataFrame({"codigo_comuna": ["01101", "01101"]})
        self.assertEqual(validate_comunas(incomplete, {"source_mode": "live"})["status"], "error")
        self.assertEqual(validate_comunas(duplicate, {"source_mode": "live"})["status"], "error")

    def test_validate_comunas_warns_for_fallback(self):
        codes = [str(i).zfill(5) for i in range(FALLBACK_COMUNAS_COUNT)]
        result = validate_comunas(
            pl.DataFrame({"codigo_comuna": codes}), {"source_mode": "fallback"}
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("fallback" in warning for warning in result["warnings"]))


class CUTInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"

    def _load_parquet(self, name):
        path = self.normalized_dir / f"{name}.parquet"
        if not path.exists():
            self.skipTest(f"{name}.parquet no existe; correr make build primero")
        return pl.read_parquet(path)

    def test_comunas_cut_codes_are_fixed_width_strings(self):
        df = self._load_parquet("comunas")
        for column, width in (
            ("codigo_region", 2),
            ("codigo_provincia", 3),
            ("codigo_comuna", 5),
        ):
            self.assertEqual(df[column].dtype, pl.String)
            self.assertTrue((df[column].str.len_chars() == width).all())

    def test_comunas_leading_zeros_are_preserved(self):
        df = self._load_parquet("comunas")
        self.assertTrue(df["codigo_region"].str.starts_with("0").any())

    def test_region_and_province_codes_are_strings_with_fixed_width(self):
        regiones = self._load_parquet("regiones")
        provincias = self._load_parquet("provincias")
        self.assertEqual(regiones["codigo_region"].dtype, pl.String)
        self.assertTrue((regiones["codigo_region"].str.len_chars() == 2).all())
        self.assertEqual(provincias["codigo_provincia"].dtype, pl.String)
        self.assertTrue((provincias["codigo_provincia"].str.len_chars() == 3).all())


class IndicatorFallbackTests(unittest.TestCase):
    def _make_minimal_df(self):
        today = datetime.date.today()
        return pl.DataFrame(
            [
                {"fecha": today, "codigo_indicador": code, "valor": 1.0}
                for code in sorted(EXPECTED_INDICATOR_CODES)
            ]
        ).with_columns(pl.col("fecha").cast(pl.Date))

    def _run_process(self, tmpdir, df, diagnostics):
        staging_path = Path(tmpdir) / "indicadores.csv"
        metadata_path = Path(tmpdir) / "indicadores.metadata.json"
        with (
            patch.object(bcentral_extractor, "STAGING_CSV_PATH", str(staging_path)),
            patch.object(bcentral_extractor, "METADATA_PATH", str(metadata_path)),
            patch.object(bcentral_extractor, "fetch_all_history", return_value=(df, diagnostics)),
        ):
            bcentral_extractor.process_indicators()
        return pl.read_csv(staging_path), json.loads(metadata_path.read_text(encoding="utf-8"))

    def test_generate_fallback_returns_all_expected_codes(self):
        df = bcentral_extractor.generate_fallback_indicators()
        self.assertGreater(df.height, 0)
        self.assertTrue(EXPECTED_INDICATOR_CODES.issubset(set(df["codigo_indicador"].unique())))

    def test_process_indicators_uses_fallback_when_fetch_fails(self):
        diagnostics = {
            "fetch_failures": ["uf/2026: timeout"],
            "raw_recoveries": [],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            written, metadata = self._run_process(tmpdir, None, diagnostics)
        self.assertGreater(written.height, 0)
        self.assertEqual(metadata["source_mode"], "fallback")
        self.assertIn("fallback_due_to_live_fetch_failure", metadata["notes"])

    def test_process_indicators_records_raw_recovery(self):
        diagnostics = {
            "fetch_failures": ["uf/2026: timeout"],
            "raw_recoveries": ["uf/2026"],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            _, metadata = self._run_process(tmpdir, self._make_minimal_df(), diagnostics)
        self.assertEqual(metadata["source_detail"], "public_api_with_raw_recovery")
        self.assertEqual(metadata["indicator_delivery"]["uf"], "raw_recovery")

    def test_process_indicators_records_published_backfill(self):
        diagnostics = {
            "fetch_failures": [],
            "raw_recoveries": [],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": ["ipc"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            _, metadata = self._run_process(tmpdir, self._make_minimal_df(), diagnostics)
        self.assertEqual(metadata["source_detail"], "public_api_with_published_backfill")
        self.assertEqual(metadata["indicator_delivery"]["ipc"], "published_backfill")

    def test_empty_live_series_reuses_published_pair(self):
        today = datetime.date.today()
        published = self._make_minimal_df()
        live_records = [
            {
                "fecha": today.strftime("%Y-%m-%d"),
                "codigo_indicador": code,
                "valor": 2.0,
            }
            for code in sorted(EXPECTED_INDICATOR_CODES - {"ipc"})
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            published_path = Path(tmpdir) / "indicadores.parquet"
            published.write_parquet(published_path)
            with (
                patch.object(
                    bcentral_extractor,
                    "STAGING_CSV_PATH",
                    str(Path(tmpdir) / "missing.csv"),
                ),
                patch.object(
                    bcentral_extractor,
                    "PUBLISHED_INDICATORS_PATH",
                    str(published_path),
                ),
                patch.object(
                    bcentral_extractor,
                    "INDICATOR_CODES",
                    sorted(EXPECTED_INDICATOR_CODES),
                ),
                patch.object(
                    bcentral_extractor,
                    "fetch_indicator_year",
                    side_effect=lambda code, year: (
                        []
                        if code == "ipc"
                        else [
                            record for record in live_records if record["codigo_indicador"] == code
                        ]
                    ),
                ),
                patch.object(bcentral_extractor.time, "sleep"),
            ):
                df, diagnostics = bcentral_extractor.fetch_all_history()

        self.assertEqual(set(df["codigo_indicador"].unique()), EXPECTED_INDICATOR_CODES)
        # ipc es un indicador mensual: una serie vacía en el año en curso es esperada,
        # por lo que NO debe aparecer en empty_live_pairs (no es un error operativo).
        self.assertEqual(diagnostics["empty_live_pairs"], [])
        self.assertEqual(diagnostics["published_backfills"], ["ipc"])


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
