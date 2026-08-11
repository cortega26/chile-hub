"""Tests unitarios de ChileHubDataManager y del contrato de caché de geometría.

TC-07: extraídos de ``test_chile_hub.py`` — no requieren el directorio de
artefactos normalizados del build (usan temp dirs, Mocks y fixtures
sintéticos), así que corren sin build previo.
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import warnings
import zipfile
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

UTC = timezone.utc

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chile_hub import ChileHubDataError
from chile_hub.cli import _main
from chile_hub.data_manager import (
    ChileHubDataManager,
    ChileHubUpdateWarning,
    ReleaseAsset,
)
from chile_hub.geo import acquire_geometry, load_geometry, validate_geometry


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

    def test_ready_latest_cache_notifies_once_when_new_release_is_available(self):
        """La caché latest consulta una vez por semana y avisa en español por defecto."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"tag_name": "v9.9.9"}
        session = Mock()
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir, session=session)
            manager.normalized_dir.mkdir(parents=True)
            (manager.normalized_dir / "dataset_catalog.json").write_text("{}", encoding="utf-8")
            manager.marker_path.write_text(
                json.dumps({"release": {"tag_name": "v1.0.0"}}), encoding="utf-8"
            )

            with (
                patch.dict(os.environ, {"CHILE_HUB_LANG": "es"}, clear=False),
                warnings.catch_warnings(record=True) as caught,
            ):
                warnings.simplefilter("always", ChileHubUpdateWarning)
                self.assertEqual(manager.ensure_data_dir(), manager.normalized_dir)

            self.assertEqual(len(caught), 1)
            message = str(caught[0].message)
            self.assertIn("Hay una nueva versión", message)
            self.assertIn("apoyar económicamente", message)
            self.assertIn("https://github.com/sponsors/cortega26", message)
            self.assertIn("https://www.buymeacoffee.com/cortega26", message)
            self.assertEqual(session.get.call_args.kwargs["timeout"], 3)
            self.assertEqual(
                json.loads(manager.update_check_path.read_text(encoding="utf-8"))["latest_tag"],
                "v9.9.9",
            )

    def test_ready_cache_skips_update_check_before_week_has_elapsed(self):
        """El estado local evita una consulta de red en cada inicialización."""
        session = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir, session=session)
            manager.normalized_dir.mkdir(parents=True)
            (manager.normalized_dir / "dataset_catalog.json").write_text("{}", encoding="utf-8")
            manager.marker_path.write_text("{}", encoding="utf-8")
            manager.update_check_path.write_text(
                json.dumps({"checked_at_utc": datetime.now(UTC).isoformat()}), encoding="utf-8"
            )

            self.assertEqual(manager.ensure_data_dir(), manager.normalized_dir)

        session.get.assert_not_called()

    def test_update_check_opt_out_prevents_network_request(self):
        """CHILE_HUB_NO_UPDATE_CHECK desactiva por completo la comprobación opcional."""
        session = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir, session=session)
            manager.normalized_dir.mkdir(parents=True)
            (manager.normalized_dir / "dataset_catalog.json").write_text("{}", encoding="utf-8")
            manager.marker_path.write_text("{}", encoding="utf-8")

            with patch.dict(os.environ, {"CHILE_HUB_NO_UPDATE_CHECK": "1"}, clear=False):
                self.assertEqual(manager.ensure_data_dir(), manager.normalized_dir)

        session.get.assert_not_called()

    def test_update_notice_uses_english_for_english_locale(self):
        """La variable de idioma explícita traduce el mensaje para usuarios en inglés."""
        with patch.dict(os.environ, {"CHILE_HUB_LANG": "en_US"}, clear=False):
            message = ChileHubDataManager._format_update_notice(
                current_tag="v1.0.0", latest_tag="v9.9.9"
            )

        self.assertIn("A new chile-hub data release is available", message)
        self.assertIn("supporting its development", message)

    def test_cache_update_cli_forces_bundle_download(self):
        """cache update debe descargar aun cuando ya exista una caché verificada."""
        with patch("chile_hub.cli.ChileHubDataManager") as manager_class:
            manager_class.return_value.update.return_value = Path("/tmp/chile-hub-data")
            output = io.StringIO()
            with redirect_stdout(output):
                _main(["cache", "update"])

        manager_class.return_value.update.assert_called_once_with()
        manager_class.return_value.ensure_data_dir.assert_not_called()
        self.assertIn("/tmp/chile-hub-data", output.getvalue())

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


class GeoCacheIntegrityTests(unittest.TestCase):
    """Contrato de distribución/caché de la geometría (Plan 065, ADR-012).

    Modelado sobre ChileHubDataManagerUnitTests: sin red real — requests.get
    se reemplaza con Mocks y los archivos son sintéticos (geo_fixtures).
    """

    # --- helpers para fabricar respuestas HTTP falsas ---------------------

    @staticmethod
    def _fake_artifact_response(payload: bytes):
        class FakeArtifact:
            def __init__(self, payload):
                self._chunks = [payload[i : i + 1024] for i in range(0, len(payload), 1024)] or [
                    b""
                ]

            def raise_for_status(self):
                pass

            def iter_content(self, chunk_size=1024):
                return iter(self._chunks)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return FakeArtifact(payload)

    @staticmethod
    def _fake_sha_response(body: str):
        class FakeSha:
            def __init__(self, body):
                self._body = body

            def raise_for_status(self):
                pass

            @property
            def text(self):
                return self._body

        return FakeSha(body)

    @staticmethod
    def _sha_body(digest: str, basename: str = "geometria_comunal.parquet") -> str:
        return f"{digest}  {basename}"

    # --- descarga y verificación ------------------------------------------

    def test_download_success_replaces_cache(self):
        """Descarga + digest correcto reemplazan el caché con el payload."""
        from geo_fixtures import payload_and_digest

        payload, digest = payload_and_digest(b"geom-data-v2")

        def fake_get(url, **kwargs):
            if url.endswith(".sha256"):
                return self._fake_sha_response(self._sha_body(digest))
            return self._fake_artifact_response(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "geometria_comunal.parquet"
            with patch("chile_hub.geo.requests.get", side_effect=fake_get):
                result = acquire_geometry(
                    refresh_geometry=True,
                    cache_file=cache,
                    artifact_url="https://x/geometria_comunal.parquet",
                    sha_url="https://x/geometria_comunal.parquet.sha256",
                )
            self.assertEqual(result, cache)
            self.assertEqual(cache.read_bytes(), payload)

    def test_checksum_mismatch_preserves_existing_cache(self):
        """Digest distinto al compañero: se preserva el caché anterior y se
        levanta ChileHubDataError (nunca se reemplaza con datos malos)."""
        from geo_fixtures import payload_and_digest

        old_payload = b"verified-cache-from-earlier"
        # El compañero declara la digest de X, pero el artefacto entrega Y:
        # el SHA-256 del payload descargado NO coincide con el declarado.
        _declared, declared_digest = payload_and_digest(b"declared-content")
        actual_payload = b"actual-content-different"

        def fake_get(url, **kwargs):
            if url.endswith(".sha256"):
                return self._fake_sha_response(self._sha_body(declared_digest))
            return self._fake_artifact_response(actual_payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "geometria_comunal.parquet"
            cache.write_bytes(old_payload)
            with patch("chile_hub.geo.requests.get", side_effect=fake_get):
                with self.assertRaises(ChileHubDataError):
                    acquire_geometry(
                        refresh_geometry=True,
                        cache_file=cache,
                        artifact_url="https://x/geometria_comunal.parquet",
                        sha_url="https://x/geometria_comunal.parquet.sha256",
                    )
            self.assertEqual(cache.read_bytes(), old_payload)

    def test_offline_reuses_verified_cache_without_network(self):
        """Con caché verificado existente no hay ninguna llamada de red."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "geometria_comunal.parquet"
            cache.write_bytes(b"cached")

            def fake_get(*args, **kwargs):
                raise AssertionError("no debería haber red con caché verificado")

            with patch("chile_hub.geo.requests.get", side_effect=fake_get):
                result = acquire_geometry(cache_file=cache)
            self.assertEqual(result, cache)

    def test_offline_without_cache_raises_with_hints(self):
        """Sin caché y sin red: ChileHubDataError con las alternativas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "geometria_comunal.parquet"
            with patch("chile_hub.geo.requests.get", side_effect=ConnectionError("sin red")):
                with self.assertRaises(ChileHubDataError) as ctx:
                    acquire_geometry(cache_file=cache)
            message = str(ctx.exception)
            self.assertIn("refresh_geometry", message)
            self.assertIn("geometry_path", message)

    def test_malformed_sha_companion_raises(self):
        """Compañero .sha256 malformado o con basename equivocado = error de contrato."""
        from geo_fixtures import payload_and_digest

        _payload, digest = payload_and_digest(b"x")
        bad_bodies = [
            "garbage",
            "abc123  geometria_comunal.parquet",
            f"{digest}  otro.parquet",
            f"{digest}",
        ]
        for body in bad_bodies:
            with self.subTest(body=body):
                with tempfile.TemporaryDirectory() as tmpdir:
                    cache = Path(tmpdir) / "geometria_comunal.parquet"
                    with patch(
                        "chile_hub.geo.requests.get",
                        return_value=self._fake_sha_response(body),
                    ):
                        with self.assertRaises(ChileHubDataError):
                            acquire_geometry(
                                refresh_geometry=True,
                                cache_file=cache,
                                sha_url="https://x/geometria_comunal.parquet.sha256",
                            )

    # --- validación estructural del GeoParquet ----------------------------

    def test_too_few_geometries_fails_structural_validation(self):
        """Menos de 340 geometrías (umbral de contrato) es error estructural."""
        from geo_fixtures import write_synthetic_parquet

        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_synthetic_parquet(Path(tmpdir) / "fixture.parquet")  # 3 comunas
            with self.assertRaises(ChileHubDataError) as ctx:
                load_geometry(path)
            self.assertIn("340", str(ctx.exception))

    def test_structural_validation_missing_geometry_and_crs(self):
        """Sin columna geometry o CRS distinto de EPSG:4326 = error estructural."""
        import geopandas as gpd
        from geo_fixtures import build_synthetic_gdf

        no_geometry = gpd.GeoDataFrame({"codigo_comuna": ["01101"], "nombre_comuna": ["A"]})
        with self.assertRaises(ChileHubDataError) as ctx:
            validate_geometry(no_geometry)
        self.assertIn("geometry", str(ctx.exception))

        wrong_crs = build_synthetic_gdf().to_crs("EPSG:3857")
        with self.assertRaises(ChileHubDataError) as ctx:
            validate_geometry(wrong_crs)
        self.assertIn("4326", str(ctx.exception))

    def test_structural_validation_bad_cut_width_and_duplicates(self):
        """CUT sin 5 caracteres o duplicado = error estructural."""
        from geo_fixtures import build_synthetic_gdf

        bad_width = build_synthetic_gdf(
            [
                {
                    "codigo_comuna": "123",
                    "nombre_comuna": "A",
                    "lat_min": -20.0,
                    "lat_max": -19.0,
                    "lon_min": -70.5,
                    "lon_max": -69.5,
                },
                {
                    "codigo_comuna": "01102",
                    "nombre_comuna": "B",
                    "lat_min": -19.0,
                    "lat_max": -18.0,
                    "lon_min": -69.5,
                    "lon_max": -68.5,
                },
            ]
        )
        with self.assertRaises(ChileHubDataError) as ctx:
            validate_geometry(bad_width)
        self.assertIn("5 caracteres", str(ctx.exception))

        duplicated = build_synthetic_gdf(
            [
                {
                    "codigo_comuna": "01101",
                    "nombre_comuna": "A",
                    "lat_min": -20.0,
                    "lat_max": -19.0,
                    "lon_min": -70.5,
                    "lon_max": -69.5,
                },
                {
                    "codigo_comuna": "01101",
                    "nombre_comuna": "A2",
                    "lat_min": -19.0,
                    "lat_max": -18.0,
                    "lon_min": -69.5,
                    "lon_max": -68.5,
                },
            ]
        )
        with self.assertRaises(ChileHubDataError) as ctx:
            validate_geometry(duplicated)
        self.assertIn("duplicados", str(ctx.exception))
