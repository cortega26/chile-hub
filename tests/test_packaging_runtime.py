import contextlib
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chile_hub import ChileHub
from chile_hub.data_manager import ChileHubDataError, ChileHubDataManager


class _FakeResponse:
    def __init__(self, *, status_code=200, payload=None, body=b""):
        self.status_code = status_code
        self._payload = payload or {}
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload

    def iter_content(self, chunk_size):
        yield self._body


class _FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)

    def get(self, *args, **kwargs):
        return self.responses.pop(0)


def _bundle_bytes() -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = Path(tmpdir) / "bundle.zip"
        with zipfile.ZipFile(bundle_path, "w") as archive:
            archive.writestr(
                "data/normalized/dataset_catalog.json",
                json.dumps({"datasets": [{"dataset": "regiones", "outputs": {}}]}),
            )
        return bundle_path.read_bytes()


class PackagingRuntimeTests(unittest.TestCase):
    def test_public_import_exposes_chile_hub(self):
        self.assertEqual(ChileHub.__name__, "ChileHub")

    def test_contract_path_falls_back_to_installed_wheel(self):
        """El contrato se resuelve desde el wheel cuando el checkout no lo tiene.

        Plan 073: los contratos viajan en el paquete instalado
        (src/chile_hub/contracts/datasets/). Si el root_dir del hub no tiene
        la carpeta contracts (consumidor de PyPI), _contract_path cae al
        wheel vía importlib.resources en vez de fallar con "No existe
        contrato de schema".
        """
        from unittest.mock import patch

        import polars as pl

        # Simular el wheel instalado: los contratos viven en un directorio
        # externo (site-packages), no en el checkout de desarrollo. El código
        # resuelve <raiz>/contracts/datasets, así que el fake es la raíz.
        fake_root = Path(tempfile.mkdtemp())
        fake_contracts = fake_root / "contracts" / "datasets"
        fake_contracts.mkdir(parents=True, exist_ok=True)
        contract_src = ROOT_DIR / "contracts" / "datasets" / "comunas.schema.json"
        (fake_contracts / "comunas.schema.json").write_text(
            contract_src.read_text(encoding="utf-8"), encoding="utf-8"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            normalized_dir = Path(tmpdir)
            (normalized_dir / "dataset_catalog.json").write_text(
                json.dumps({"datasets": [{"dataset": "comunas", "outputs": {"parquet": "x"}}]}),
                encoding="utf-8",
            )
            hub = ChileHub(data_dir=normalized_dir)
            # root_dir deriva de data_dir; no tiene contracts/ → fallback al wheel.
            with (
                patch("chile_hub.core.importlib.resources.files", return_value=fake_root),
                patch(
                    "chile_hub.core.importlib.resources.as_file",
                    side_effect=lambda p: contextlib.nullcontext(p),
                ),
            ):
                contract_path = hub._contract_path("comunas")
                self.assertIsNotNone(contract_path)
                self.assertTrue(contract_path.is_file())

                df = pl.DataFrame(
                    {
                        "codigo_comuna": ["01101"],
                        "nombre_comuna": ["Iquique"],
                        "codigo_provincia": ["011"],
                        "codigo_region": ["01"],
                        "nombre_comuna_clean": ["iquique"],
                    }
                )
                result = hub.validate_user_data(df, "comunas")
                self.assertEqual(result["status"], "ok")
                self.assertIn("schema_used", result)

    def test_contract_path_survives_ephemeral_as_file(self):
        """El contrato debe sobrevivir a un as_file() efímero (P2 del 073).

        Con un resource loader basado en zip (zipimport), as_file() materializa
        el recurso en un temporal que se ELIMINA al salir del with. El Path
        retornado no debe apuntar a un archivo borrado: _contract_path copia a
        un temporal persistente.
        """
        # Simular as_file efímero: materializa, devuelve el path, y BORRA el
        # archivo al salir del with (como zipimport).
        from unittest.mock import patch

        ephemeral = {}

        class _EphemeralContext:
            def __enter__(self):
                materialized = Path(tempfile.mkdtemp()) / "comunas.schema.json"
                materialized.write_text(
                    (ROOT_DIR / "contracts" / "datasets" / "comunas.schema.json").read_text(
                        encoding="utf-8"
                    ),
                    encoding="utf-8",
                )
                ephemeral["path"] = materialized
                return materialized

            def __exit__(self, *exc):
                ephemeral["path"].unlink(missing_ok=True)
                return False

        fake_root = Path(tempfile.mkdtemp())
        fake_contracts = fake_root / "contracts" / "datasets"
        fake_contracts.mkdir(parents=True, exist_ok=True)
        (fake_contracts / "comunas.schema.json").write_text("{}", encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            normalized_dir = Path(tmpdir)
            (normalized_dir / "dataset_catalog.json").write_text(
                json.dumps({"datasets": [{"dataset": "comunas", "outputs": {}}]}),
                encoding="utf-8",
            )
            hub = ChileHub(data_dir=normalized_dir)
            with (
                patch("chile_hub.core.importlib.resources.files", return_value=fake_root),
                patch(
                    "chile_hub.core.importlib.resources.as_file",
                    side_effect=lambda p: _EphemeralContext(),
                ),
            ):
                contract_path = hub._contract_path("comunas")
                self.assertIsNotNone(contract_path)
                # El path del as_file efímero ya no existe; el retornado debe ser
                # una copia persistente válida.
                self.assertFalse(ephemeral["path"].exists())
                self.assertTrue(contract_path.is_file())
                self.assertEqual(
                    contract_path.read_text(encoding="utf-8"),
                    (ROOT_DIR / "contracts" / "datasets" / "comunas.schema.json").read_text(
                        encoding="utf-8"
                    ),
                )

    def test_local_data_dir_mode_uses_explicit_normalized_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            normalized_dir = Path(tmpdir)
            (normalized_dir / "dataset_catalog.json").write_text(
                json.dumps({"datasets": [{"dataset": "regiones", "outputs": {}}]}),
                encoding="utf-8",
            )
            hub = ChileHub(data_dir=normalized_dir)

        self.assertEqual(hub.list_datasets(), ["regiones"])

    def test_cache_update_downloads_verifies_and_extracts_bundle(self):
        bundle = _bundle_bytes()
        sha256 = hashlib.sha256(bundle).hexdigest()
        release = {
            "tag_name": "v1.0.1",
            "html_url": "https://github.com/cortega26/chile-hub/releases/tag/v1.0.1",
            "assets": [
                {
                    "name": "chile-hub-publishable-bundle.zip",
                    "browser_download_url": "https://example.test/bundle.zip",
                },
                {
                    "name": "chile-hub-publishable-bundle.zip.sha256",
                    "browser_download_url": "https://example.test/bundle.zip.sha256",
                },
            ],
        }
        # update() descarga el checksum primero y luego el bundle
        session = _FakeSession(
            [
                _FakeResponse(payload=release),
                _FakeResponse(
                    body=f"{sha256}  data/normalized/chile-hub-publishable-bundle.zip\n".encode()
                ),
                _FakeResponse(body=bundle),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir, session=session)
            normalized_dir = manager.ensure_data_dir()

            self.assertTrue((normalized_dir / "dataset_catalog.json").exists())
            self.assertTrue(manager.status()["is_ready"])

    def test_cache_update_fails_on_sha_mismatch(self):
        bundle = _bundle_bytes()
        release = {
            "assets": [
                {
                    "name": "chile-hub-publishable-bundle.zip",
                    "browser_download_url": "https://example.test/bundle.zip",
                },
                {
                    "name": "chile-hub-publishable-bundle.zip.sha256",
                    "browser_download_url": "https://example.test/bundle.zip.sha256",
                },
            ],
        }
        # update() descarga el checksum primero y luego el bundle
        session = _FakeSession(
            [
                _FakeResponse(payload=release),
                _FakeResponse(body=b"0  data/normalized/chile-hub-publishable-bundle.zip\n"),
                _FakeResponse(body=bundle),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir, session=session)
            with self.assertRaisesRegex(ChileHubDataError, "Checksum mismatch"):
                manager.ensure_data_dir()

    def test_missing_offline_cache_fails_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChileHubDataManager(cache_dir=tmpdir)
            with self.assertRaisesRegex(ChileHubDataError, "chile-hub cache update"):
                manager.ensure_data_dir(auto_update=False)


if __name__ == "__main__":
    unittest.main()
