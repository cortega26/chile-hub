import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.build_dev_db import build_coverage, build_degradation, build_drift  # noqa: E402
from src.pipeline_status_utils import build_hub_health  # noqa: E402


class PipelineLogicTests(unittest.TestCase):
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
                    "reuse_policy": {"status": "open-attribution", "redistribution_ok": True},
                    "degradation": {"status": "none"},
                    "coverage": {"status": "full", "coverage_ratio": 1.0},
                    "drift": {"status": "healthy"},
                },
                "beta": {
                    "source_mode": "fallback",
                    "freshness": {"status": "stale"},
                    "reuse_policy": {"status": "public-api-review-terms", "redistribution_ok": False},
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


if __name__ == "__main__":
    unittest.main()
