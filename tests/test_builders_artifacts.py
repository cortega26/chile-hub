"""Tests de integridad para los builders de artefactos publicables (artifacts.py).

Cubre: bundle ZIP, SHA-256, consistencia manifiesto↔ZIP y guardia de artefacto
faltante.
"""

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.builders.artifacts import (
    attach_publishable_package_to_manifest,
    write_publishable_bundle_sha256,
    write_publishable_bundle_zip,
)
from src.builders.io_utils import write_json_atomic, write_parquet_atomic

# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------


def _create_sample_artifact(normalized_dir: str, name: str, suffix: str = ".parquet") -> str:
    """Crea un archivo de artefacto de muestra en NORMALIZED_DIR y retorna su ruta."""
    path = os.path.join(normalized_dir, f"{name}{suffix}")
    if suffix == ".parquet":
        df = pl.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})
        write_parquet_atomic(df, path)
    elif suffix == ".json":
        data = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
        write_json_atomic(data, path, ensure_ascii=False, indent=2)
    else:
        with open(path, "w") as f:
            f.write("test content")
    return path


def _make_artifact_entry(
    relative_path: str, dataset: str = "test_dataset", output_type: str = "parquet"
) -> dict:
    """Crea una entrada de manifiesto para un artefacto."""
    return {
        "path": relative_path,
        "dataset": dataset,
        "output_type": output_type,
        "publication_track": "stable_publishable",
        "public_bundle_eligible": True,
    }


def _create_test_manifest(normalized_dir: str) -> str:
    """Crea un artifact_manifest.json con entradas de prueba y retorna su ruta."""
    artifacts = []

    # Parquet: debe coincidir con PUBLISHABLE_ARTIFACT_SUFFIXES
    _create_sample_artifact(normalized_dir, "test_data", ".parquet")
    artifacts.append(
        _make_artifact_entry("data/normalized/test_data.parquet", "test_dataset", "parquet")
    )

    # JSON
    _create_sample_artifact(normalized_dir, "test_metadata", ".json")
    artifacts.append(
        _make_artifact_entry("data/normalized/test_metadata.json", "test_dataset", "json")
    )

    manifest = {
        "generated_at_utc": "2026-07-09T00:00:00+00:00",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "packages": [],
    }
    manifest_path = os.path.join(normalized_dir, "artifact_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBundleZip:
    """write_publishable_bundle_zip: creacion y validacion del ZIP."""

    def test_bundle_zip_created(self):
        """El ZIP se crea con los artefactos listados en el manifiesto."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)

            # DATA_DIR debe ser el padre de normalized para que la resolucion
            # de rutas relativa funcione (DATA_DIR / relpath("data/...", "data"))
            data_dir = tmpdir

            _create_test_manifest(normalized)

            patches = [
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ]
            for p in patches:
                p.start()

            try:
                zip_path = write_publishable_bundle_zip()
                assert os.path.exists(zip_path), f"ZIP no creado: {zip_path}"
                assert zip_path.endswith(".zip"), f"Extension incorrecta: {zip_path}"
            finally:
                for p in patches:
                    p.stop()

    def test_bundle_zip_namelist_matches_manifest(self):
        """Cada ruta del manifiesto existe dentro del ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            _create_test_manifest(normalized)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()

            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()

            with open(os.path.join(normalized, "artifact_manifest.json"), "r") as f:
                manifest = json.load(f)

            for artifact in manifest["artifacts"]:
                assert artifact["path"] in namelist, (
                    f"Ruta '{artifact['path']}' del manifiesto no encontrada en ZIP: {namelist}"
                )

    def test_bundle_zip_missing_artifact_raises_system_exit(self):
        """SystemExit si falta un artefacto declarado en el manifiesto."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            # Crear manifiesto que referencia un archivo inexistente
            manifest = {
                "generated_at_utc": "2026-07-09T00:00:00+00:00",
                "artifact_count": 1,
                "artifacts": [
                    {
                        "path": "data/normalized/missing_file.parquet",
                        "dataset": "ghost",
                        "output_type": "parquet",
                    }
                ],
                "packages": [],
            }
            manifest_path = os.path.join(normalized, "artifact_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                import pytest

                with pytest.raises(SystemExit, match="missing_file"):
                    write_publishable_bundle_zip()


class TestBundleSha256:
    """write_publishable_bundle_sha256: generacion y verificacion del checksum."""

    def test_sha256_file_matches_independent_computation(self):
        """El digest en el .sha256 coincide con hashlib.sha256 del ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            _create_test_manifest(normalized)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()
                sha256_path = write_publishable_bundle_sha256(zip_path)

            # Calcular SHA-256 del ZIP de forma independiente
            with open(zip_path, "rb") as f:
                expected_digest = hashlib.sha256(f.read()).hexdigest()

            # Leer el digest del archivo .sha256
            with open(sha256_path, "r") as f:
                line = f.read().strip()

            # Formato: "<sha256>  data/normalized/<zip>"
            written_digest = line.split("  ")[0]
            assert written_digest == expected_digest, (
                f"Digest en .sha256 ({written_digest}) no coincide con "
                f"computo directo ({expected_digest})"
            )

    def test_sha256_path_format(self):
        """El archivo .sha256 contiene la ruta relativa esperada."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            _create_test_manifest(normalized)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()
                sha256_path = write_publishable_bundle_sha256(zip_path)

            with open(sha256_path, "r") as f:
                line = f.read().strip()

            parts = line.split("  ")
            assert len(parts) == 2, (
                f"Formato incorrecto en .sha256: se esperaban 2 partes "
                f"separadas por doble espacio, obtenido: {line!r}"
            )
            # La segunda parte debe ser la ruta relativa del ZIP
            assert "chile-hub-publishable-bundle.zip" in parts[1], (
                f"Ruta en .sha256 no contiene el nombre del ZIP: {parts[1]}"
            )


class TestManifestPackage:
    """attach_publishable_package_to_manifest: registro del paquete en el manifiesto."""

    def test_package_entry_has_correct_fields(self):
        """El manifiesto actualizado contiene path, size_bytes, sha256 correctos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            _create_test_manifest(normalized)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()
                sha256_path = write_publishable_bundle_sha256(zip_path)
                manifest_path, manifest = attach_publishable_package_to_manifest(
                    zip_path, sha256_path
                )

            assert os.path.exists(manifest_path)

            # Verificar el contenido del paquete
            packages = manifest.get("packages", [])
            assert len(packages) >= 1, "No hay paquetes en el manifiesto"
            pkg = packages[0]

            assert pkg["path"].endswith("chile-hub-publishable-bundle.zip"), (
                f"path inesperado: {pkg['path']}"
            )
            assert pkg["package_type"] == "zip"
            assert pkg["size_bytes"] == os.path.getsize(zip_path), (
                f"size_bytes {pkg['size_bytes']} != {os.path.getsize(zip_path)}"
            )
            assert len(pkg["sha256"]) == 64, (
                f"sha256 deberia tener 64 caracteres hex, tiene {len(pkg['sha256'])}"
            )
            assert pkg["checksum_algorithm"] == "sha256"
            assert pkg["checksum_path"].endswith(".sha256")
            assert "shasum" in pkg["verification_command"]

    def test_package_entry_sha256_matches(self):
        """El sha256 en el manifiesto coincide con el del archivo .sha256."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            _create_test_manifest(normalized)

            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()
                sha256_path = write_publishable_bundle_sha256(zip_path)
                _, manifest = attach_publishable_package_to_manifest(zip_path, sha256_path)

            pkg_sha256 = manifest["packages"][0]["sha256"]

            # Leer del .sha256
            with open(sha256_path, "r") as f:
                sha256_digest = f.read().strip().split("  ")[0]

            assert pkg_sha256 == sha256_digest, (
                f"SHA-256 en manifiesto ({pkg_sha256}) no coincide con "
                f"archivo .sha256 ({sha256_digest})"
            )


class TestFromNormalFlow:
    """Prueba de integracion que sigue el flujo normal: flat files → manifest → bundle."""

    def test_full_round_trip(self):
        """Flujo completo: escribir artefactos → manifest → zip → sha256 → paquete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized = os.path.join(tmpdir, "normalized")
            os.makedirs(normalized, exist_ok=True)
            data_dir = tmpdir

            # 1. Crear archivos de artefacto (simula build_flat_files)
            _create_sample_artifact(normalized, "regiones", ".parquet")
            _create_sample_artifact(normalized, "regiones", ".json")
            _create_sample_artifact(normalized, "comunas", ".parquet")
            _create_sample_artifact(normalized, "indicadores", ".parquet")
            _create_sample_artifact(normalized, "pipeline_metadata", ".json")
            _create_sample_artifact(normalized, "pipeline_status", ".md")
            _create_sample_artifact(normalized, "hub_health", ".json")
            _create_sample_artifact(normalized, "hub_health", ".md")
            _create_sample_artifact(normalized, "hub_status", ".json")

            # 2. Escribir manifiesto
            # Nota: write_artifact_manifest depende de DATASET_CATALOG_CONFIG
            # y load_source_registry.  Para un test aislado, construimos
            # un manifiesto minimo que los builders de artefactos consumen.
            artifacts = [
                {
                    "path": "data/normalized/regiones.parquet",
                    "dataset": "regiones",
                    "output_type": "parquet",
                    "format": "parquet",
                },
                {
                    "path": "data/normalized/comunas.parquet",
                    "dataset": "comunas",
                    "output_type": "parquet",
                    "format": "parquet",
                },
                {
                    "path": "data/normalized/indicadores.parquet",
                    "dataset": "indicadores",
                    "output_type": "parquet",
                    "format": "parquet",
                },
            ]
            manifest = {
                "generated_at_utc": "2026-07-09T00:00:00+00:00",
                "artifact_count": len(artifacts),
                "artifacts": artifacts,
                "packages": [],
            }
            manifest_path = os.path.join(normalized, "artifact_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            # 3. Bundle ZIP
            with (
                patch("src.builders.artifacts.NORMALIZED_DIR", normalized),
                patch("src.builders.artifacts.DATA_DIR", data_dir),
            ):
                zip_path = write_publishable_bundle_zip()
                assert os.path.exists(zip_path)

                # 4. SHA-256
                sha256_path = write_publishable_bundle_sha256(zip_path)
                assert os.path.exists(sha256_path)

                # 5. Anadir paquete al manifiesto
                mpath, updated_manifest = attach_publishable_package_to_manifest(
                    zip_path, sha256_path
                )
                assert len(updated_manifest["packages"]) == 1

                # 6. Verificar que todas las rutas del manifiesto esten en el ZIP
                with zipfile.ZipFile(zip_path, "r") as zf:
                    namelist = zf.namelist()

                for artifact in updated_manifest["artifacts"]:
                    assert artifact["path"] in namelist

                # 7. Verificar que el archivo .sha256 existe en disco
                assert os.path.exists(sha256_path), f"Archivo .sha256 no encontrado: {sha256_path}"
                assert sha256_path.endswith(".sha256")
