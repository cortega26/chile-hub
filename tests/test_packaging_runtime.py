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
            "tag_name": "v0.1.0",
            "html_url": "https://github.com/cortega26/chile-hub/releases/tag/v0.1.0",
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
        session = _FakeSession(
            [
                _FakeResponse(payload=release),
                _FakeResponse(body=bundle),
                _FakeResponse(
                    body=f"{sha256}  data/normalized/chile-hub-publishable-bundle.zip\n".encode()
                ),
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
        session = _FakeSession(
            [
                _FakeResponse(payload=release),
                _FakeResponse(body=bundle),
                _FakeResponse(body=b"0  data/normalized/chile-hub-publishable-bundle.zip\n"),
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
