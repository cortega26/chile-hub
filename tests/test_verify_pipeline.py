"""
Characterization tests for ``scripts/verify_pipeline.py`` — the last
publish gate before public data is shipped.

Strategy
--------
*Golden-copy fixture* — real build artifacts (data/normalized/, contracts/,
data/staging/ metadata, pyproject.toml, source_registry.json) are copied
into a temp dir once per class (setUpClass).  Module-level path constants
are patched to point there.  This exercises the large file-based gates with
real cross-file consistency.

*Corruption tests* — each test creates its own isolated temp dir, copies a
single file from the golden copy, corrupts it, and asserts SystemExit.

*Synthetic tests* — for parameterized gates (publication policy, source
registry) that already accept dict inputs, we hand-build small fixtures
without the golden-copy machinery.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scripts import verify_pipeline as vp

# ── helpers ────────────────────────────────────────────────────────────────


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
#  Golden-copy tests
# ═══════════════════════════════════════════════════════════════════════════


class VerifyGoldenCopyTests(unittest.TestCase):
    """Tests that run against a read-only copy of the last successful build.

    Because the golden copy represents a *known-good* build, every happy-path
    test MUST pass.  If one raises, either the real data has drifted or the
    gate has a latent regression — report it, do not weaken the test.
    """

    _golden_dir: Path | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._golden_dir = Path(tempfile.mkdtemp())
        golden = cls._golden_dir

        # data/normalized/ — bulk of the files the gates inspect
        shutil.copytree(ROOT_DIR / "data" / "normalized", golden / "data" / "normalized")

        # contracts/ — needed by verify_schema_contracts
        shutil.copytree(ROOT_DIR / "contracts" / "datasets", golden / "contracts" / "datasets")

        # data/staging/ — only the metadata files are inspected by the
        # staging-not-newer-than-normalized gate
        staging_src = ROOT_DIR / "data" / "staging"
        staging_dst = golden / "data" / "staging"
        staging_dst.mkdir(parents=True, exist_ok=True)
        for p in staging_src.glob("*.metadata.json"):
            shutil.copy2(p, staging_dst)

        # data/source_registry.json — needed by verify_source_registry
        src_reg = ROOT_DIR / "data" / "source_registry.json"
        if src_reg.exists():
            shutil.copy2(src_reg, golden / "data" / "source_registry.json")

        # pyproject.toml — needed by load_project_version() inside
        # verify_pipeline_metadata, verify_hub_bundle, etc.
        shutil.copy2(ROOT_DIR / "pyproject.toml", golden / "pyproject.toml")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._golden_dir is not None:
            shutil.rmtree(cls._golden_dir)

    def setUp(self) -> None:
        assert self._golden_dir is not None
        self._patch_paths(self._golden_dir)

    def _patch_paths(self, base: Path) -> None:
        """Patch module-level path constants to point at *base*."""
        patchers = [
            patch.object(vp, "NORMALIZED_DIR", base / "data" / "normalized"),
            patch.object(vp, "STAGING_DIR", base / "data" / "staging"),
            patch.object(vp, "CONTRACTS_DIR", base / "contracts" / "datasets"),
            patch.object(vp, "ROOT_DIR", base),
            patch.object(vp, "SOURCE_REGISTRY_PATH", base / "data" / "source_registry.json"),
        ]
        for p in patchers:
            p.start()
        self._path_patchers = patchers

    def tearDown(self) -> None:
        for p in self._path_patchers:
            p.stop()

    # -- happy path (golden copy must pass) --------------------------------

    def test_artifact_manifest_passes(self) -> None:
        vp.verify_artifact_manifest()

    def test_publishable_zip_passes(self) -> None:
        vp.verify_publishable_zip()

    def test_dataset_catalog_passes(self) -> None:
        vp.verify_dataset_catalog()

    def test_pipeline_metadata_passes(self) -> None:
        vp.verify_pipeline_metadata()

    def test_schema_contracts_passes(self) -> None:
        vp.verify_schema_contracts()

    def test_hub_health_passes(self) -> None:
        vp.verify_hub_health()

    def test_hub_status_passes(self) -> None:
        vp.verify_hub_status()

    def test_hub_bundle_passes(self) -> None:
        vp.verify_hub_bundle()

    def test_source_registry_passes(self) -> None:
        vp.verify_source_registry()

    def test_data_package_passes(self) -> None:
        vp.verify_data_package()

    def test_redistribution_report_passes(self) -> None:
        vp.verify_redistribution_report()

    def test_provenance_report_passes(self) -> None:
        vp.verify_provenance_report()

    def test_drift_report_passes(self) -> None:
        vp.verify_drift_report()

    def test_overview_passes(self) -> None:
        vp.verify_overview()

    def test_readiness_report_passes(self) -> None:
        vp.verify_source_readiness_report()
        vp.verify_dataset_quality_report()

    def test_main_dev_profile_passes(self) -> None:
        """Smoke-test ``main()`` with ``--profile dev``.

        ``verify_required_files`` is stubbed because the golden copy does
        not include the full staging CSV set.
        """
        test_args = ["verify_pipeline.py", "--profile", "dev"]
        with (
            patch.object(sys, "argv", test_args),
            patch("builtins.print"),
            patch.object(vp, "verify_required_files"),
        ):
            vp.main()

    # -- corruption tests (isolated temp-dir per test) ---------------------

    def test_artifact_manifest_rejects_missing_expected_path(self) -> None:
        """Remove one required artifact path -> SystemExit."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            norm.mkdir(parents=True)
            src = self._golden_dir / "data" / "normalized" / "artifact_manifest.json"
            dst = norm / "artifact_manifest.json"
            shutil.copy2(src, dst)

            manifest = _read_json(dst)
            # Drop one expected path
            manifest["artifacts"] = [
                a
                for a in manifest["artifacts"]
                if a.get("path") != "data/normalized/regiones.parquet"
            ]
            manifest["artifact_count"] = len(manifest["artifacts"])
            _write_json(dst, manifest)

            self._patch_paths(base)
            self.addCleanup(self.tearDown)
            with self.assertRaises(SystemExit):
                vp.verify_artifact_manifest()

    def test_publishable_zip_rejects_empty_zip(self) -> None:
        """Truncate the zip to zero bytes -> SystemExit."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            norm.mkdir(parents=True)
            for name in (
                "chile-hub-publishable-bundle.zip",
                "chile-hub-publishable-bundle.zip.sha256",
            ):
                shutil.copy2(
                    self._golden_dir / "data" / "normalized" / name,
                    norm / name,
                )
            # Truncate
            (norm / "chile-hub-publishable-bundle.zip").write_bytes(b"")

            self._patch_paths(base)
            self.addCleanup(self.tearDown)
            with self.assertRaises(SystemExit):
                vp.verify_publishable_zip()

    def test_dataset_catalog_rejects_wrong_count(self) -> None:
        """Bump dataset_count -> SystemExit."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            norm.mkdir(parents=True)
            src = self._golden_dir / "data" / "normalized" / "dataset_catalog.json"
            dst = norm / "dataset_catalog.json"
            shutil.copy2(src, dst)

            catalog = _read_json(dst)
            catalog["dataset_count"] = 999
            _write_json(dst, catalog)

            self._patch_paths(base)
            self.addCleanup(self.tearDown)
            with self.assertRaises(SystemExit):
                vp.verify_dataset_catalog()

    def test_pipeline_metadata_rejects_wrong_version(self) -> None:
        """Change version in metadata -> SystemExit (version mismatch)."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            norm.mkdir(parents=True)
            shutil.copy2(
                self._golden_dir / "data" / "normalized" / "pipeline_metadata.json",
                norm / "pipeline_metadata.json",
            )
            # Also need pyproject.toml so load_project_version() works
            shutil.copy2(ROOT_DIR / "pyproject.toml", base / "pyproject.toml")

            meta = _read_json(norm / "pipeline_metadata.json")
            meta["version"] = "0.0.0-fake"
            _write_json(norm / "pipeline_metadata.json", meta)

            self._patch_paths(base)
            self.addCleanup(self.tearDown)
            with self.assertRaises(SystemExit):
                vp.verify_pipeline_metadata()


# ═══════════════════════════════════════════════════════════════════════════
#  Synthetic-fixture tests  (parameterized gates)
# ═══════════════════════════════════════════════════════════════════════════


class VerifySyntheticTests(unittest.TestCase):
    """Tests that inject hand-built dicts without filesystem fixtures."""

    # -- publication policy ------------------------------------------------

    @staticmethod
    def _stable_registry_entry(dataset_name: str) -> dict:
        return {
            "dataset": dataset_name,
            "access_method": "landing_snapshot",
            "live_extractor_status": "implemented",
            "fallback_policy": "none",
            "maturity_status": "stable",
            "live_ready": True,
            "publish_blocking": False,
            "publication_track": "stable_publishable",
            "public_bundle_eligible": True,
        }

    def test_publication_policy_accepts_fresh_live(self) -> None:
        datasets = {
            "comunas": {
                "source_mode": "live",
                "source_detail": "public_api",
                "freshness": {"status": "fresh"},
            }
        }
        registry = [self._stable_registry_entry("comunas")]
        vp.verify_publication_policy({"datasets": datasets}, registry=registry)

    def test_publication_policy_rejects_unknown_source_mode(self) -> None:
        datasets = {
            "comunas": {
                "source_mode": "weekly",
                "source_detail": "public_api",
                "freshness": {"status": "fresh"},
            }
        }
        registry = [self._stable_registry_entry("comunas")]
        with (
            patch("builtins.print"),
            self.assertRaises(SystemExit),
        ):
            vp.verify_publication_policy({"datasets": datasets}, registry=registry)

    # -- staging-not-newer-than-normalized (synthetic timestamps) ----------

    def test_staging_not_newer_passes(self) -> None:
        """Staging metadata older than sentinel -> passes."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            staging = base / "data" / "staging"
            norm.mkdir(parents=True)
            staging.mkdir(parents=True)

            # Sentinel — pipeline_metadata.json (old)
            sentinel = norm / "pipeline_metadata.json"
            _write_json(sentinel, {"dummy": True})
            old_mtime = 1_000_000_000  # 2001-09-09
            os.utime(sentinel, (old_mtime, old_mtime))

            # Staging metadata (older than sentinel) — should pass
            meta = staging / "finanzas_municipales.metadata.json"
            _write_json(meta, {"dummy": True})
            staging_mtime = old_mtime - 1000
            os.utime(meta, (staging_mtime, staging_mtime))

            self._start_patches(base)
            self.addCleanup(self._stop_patches)
            vp.verify_staging_not_newer_than_normalized()

    def test_staging_not_newer_rejects_newer_staging(self) -> None:
        """Staging metadata newer than sentinel -> SystemExit."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            norm = base / "data" / "normalized"
            staging = base / "data" / "staging"
            norm.mkdir(parents=True)
            staging.mkdir(parents=True)

            sentinel = norm / "pipeline_metadata.json"
            _write_json(sentinel, {"dummy": True})
            old_mtime = 1_000_000_000
            os.utime(sentinel, (old_mtime, old_mtime))

            # Staging metadata (NEWER than sentinel) — should fail
            meta = staging / "finanzas_municipales.metadata.json"
            _write_json(meta, {"dummy": True})
            new_mtime = old_mtime + 1000
            os.utime(meta, (new_mtime, new_mtime))

            self._start_patches(base)
            self.addCleanup(self._stop_patches)
            with self.assertRaises(SystemExit):
                vp.verify_staging_not_newer_than_normalized()

    # -- source registry (synthetic) ---------------------------------------

    def test_source_registry_accepts_matching_catalog(self) -> None:
        registry = [
            {
                "dataset": "comunas",
                "access_method": "landing_snapshot",
                "live_extractor_status": "implemented",
                "fallback_policy": "none",
                "maturity_status": "stable",
                "publication_track": "stable_publishable",
                "public_bundle_eligible": True,
                "license_status": "open-attribution",
                "live_ready": True,
                "publish_blocking": False,
            }
        ]
        catalog = {
            "datasets": [
                {
                    "dataset": "comunas",
                    "outputs": {"parquet": "data/normalized/comunas.parquet"},
                }
            ]
        }
        vp.verify_source_registry(registry, catalog)

    def test_source_registry_rejects_duplicate(self) -> None:
        registry = [
            {
                "dataset": "comunas",
                "access_method": "landing_snapshot",
                "live_extractor_status": "implemented",
                "fallback_policy": "none",
                "maturity_status": "stable",
                "publication_track": "stable_publishable",
                "public_bundle_eligible": True,
                "license_status": "open-attribution",
                "live_ready": True,
                "publish_blocking": False,
            },
            {
                "dataset": "comunas",
                "access_method": "api",
                "live_extractor_status": "fallback_only",
                "fallback_policy": "allowed_for_dev_blocked_for_publication",
                "maturity_status": "candidate",
                "publication_track": "candidate",
                "public_bundle_eligible": False,
                "license_status": "open-attribution",
                "live_ready": False,
                "publish_blocking": True,
            },
        ]
        catalog = {
            "datasets": [
                {
                    "dataset": "comunas",
                    "outputs": {"parquet": "data/normalized/comunas.parquet"},
                }
            ]
        }
        with (
            patch("builtins.print"),
            self.assertRaises(SystemExit),
        ):
            vp.verify_source_registry(registry, catalog)

    # -- internal helpers for path patching ---------------------------------

    def _start_patches(self, base: Path) -> None:
        patchers = [
            patch.object(vp, "NORMALIZED_DIR", base / "data" / "normalized"),
            patch.object(vp, "STAGING_DIR", base / "data" / "staging"),
            patch.object(vp, "CONTRACTS_DIR", base / "contracts" / "datasets"),
            patch.object(vp, "ROOT_DIR", base),
        ]
        for p in patchers:
            p.start()
        self._synthetic_patchers = patchers

    def _stop_patches(self) -> None:
        for p in self._synthetic_patchers:
            p.stop()
