"""Acceso en tiempo de ejecución a activos de release de datos versionados de chile-hub."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from platformdirs import user_cache_dir

from .exceptions import ChileHubDataError

DEFAULT_REPOSITORY = "cortega26/chile-hub"
DEFAULT_BUNDLE_NAME = "chile-hub-publishable-bundle.zip"
DEFAULT_CHECKSUM_NAME = "chile-hub-publishable-bundle.zip.sha256"
ENV_CACHE_DIR = "CHILE_HUB_CACHE_DIR"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str


class ChileHubDataManager:
    def __init__(
        self,
        *,
        data_version: str = "latest",
        repository: str = DEFAULT_REPOSITORY,
        cache_dir: str | Path | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.data_version = data_version
        self.repository = repository
        self.cache_root = Path(
            cache_dir or os.environ.get(ENV_CACHE_DIR) or user_cache_dir("chile-hub", "chile-hub")
        )
        self.session = session or requests.Session()

    @property
    def version_cache_dir(self) -> Path:
        return self.cache_root / self.data_version

    @property
    def normalized_dir(self) -> Path:
        return self.version_cache_dir / "data" / "normalized"

    @property
    def marker_path(self) -> Path:
        return self.version_cache_dir / ".verified.json"

    def status(self) -> dict[str, Any]:
        """Estado del caché local de datos: versión, rutas y si está listo para usarse."""
        catalog_path = self.normalized_dir / "dataset_catalog.json"
        marker = self._read_json(self.marker_path)
        return {
            "cache_root": str(self.cache_root),
            "data_version": self.data_version,
            "normalized_dir": str(self.normalized_dir),
            "is_ready": catalog_path.exists() and self.marker_path.exists(),
            "dataset_catalog": str(catalog_path),
            "verified": bool(marker),
            "release": marker.get("release") if marker else None,
        }

    def ensure_data_dir(self, *, auto_update: bool = True) -> Path:
        """Garantiza que el directorio de datos normalizados existe, descargándolo si es necesario.

        Args:
            auto_update: Si es True, descarga automáticamente el bundle cuando no hay caché local.

        Returns:
            Path al directorio normalized/ con los datos listos para consumir.

        Raises:
            ChileHubDataError: Si auto_update es False y no existe caché local verificado.
        """
        if (self.normalized_dir / "dataset_catalog.json").exists() and self.marker_path.exists():
            return self.normalized_dir
        if not auto_update:
            raise ChileHubDataError(
                "No verified chile-hub data cache found. Run `chile-hub cache update` "
                "or pass ChileHub(data_dir='/path/to/data/normalized')."
            )
        self.update()
        return self.normalized_dir

    def update(self) -> Path:
        """Descarga y verifica el bundle de datos desde GitHub Releases.

        El proceso es: resolver release → descargar checksum → descargar bundle
        (hasheando en tránsito) → verificar SHA-256 → extraer → escribir marcador
        de verificación. Si el hash no coincide, el bundle se descarta sin tocar
        el directorio normalized/.

        Returns:
            Path al directorio normalized/ con los datos extraídos.

        Raises:
            ChileHubDataError: Si el checksum no coincide o el bundle no contiene el catálogo.
        """
        release = self._resolve_release()
        assets = self._assets_by_name(release)
        bundle = self._require_asset(assets, DEFAULT_BUNDLE_NAME)
        checksum = self._require_asset(assets, DEFAULT_CHECKSUM_NAME)

        self.version_cache_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = self.version_cache_dir / DEFAULT_BUNDLE_NAME
        checksum_path = self.version_cache_dir / DEFAULT_CHECKSUM_NAME

        # Descargar checksum primero
        self._download(checksum.url, checksum_path)
        expected_sha256 = self._read_checksum(checksum_path)

        # Descargar bundle hasheando en tránsito para eliminar ventana TOCTOU
        sha256_hash = hashlib.sha256()
        with self.session.get(bundle.url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(
                dir=str(self.version_cache_dir), delete=False, suffix=".tmp"
            ) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        sha256_hash.update(chunk)
                        tmp.write(chunk)
                tmp_path = Path(tmp.name)

        actual_sha256 = sha256_hash.hexdigest()
        if actual_sha256 != expected_sha256:
            tmp_path.unlink(missing_ok=True)
            raise ChileHubDataError(
                f"Checksum mismatch for {DEFAULT_BUNDLE_NAME}: "
                f"expected {expected_sha256}, got {actual_sha256}"
            )

        # Renombrar atómicamente al path final solo si el hash coincide
        tmp_path.replace(bundle_path)

        self._extract_bundle(bundle_path)
        if not (self.normalized_dir / "dataset_catalog.json").exists():
            raise ChileHubDataError(
                f"Downloaded bundle did not contain {self.normalized_dir / 'dataset_catalog.json'}"
            )

        self.marker_path.write_text(
            json.dumps(
                {
                    "release": {
                        "tag_name": release.get("tag_name"),
                        "html_url": release.get("html_url"),
                    },
                    "sha256": actual_sha256,
                    "bundle": DEFAULT_BUNDLE_NAME,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return self.normalized_dir

    def clear(self) -> None:
        """Elimina el caché local de datos, forzando una descarga fresca en el próximo uso.

        Por seguridad, solo opera dentro del directorio de caché esperado (platformdirs).
        Si el directorio configurado está fuera de ese árbol, levanta ChileHubDataError.

        Raises:
            ChileHubDataError: Si cache_root no está bajo el directorio de caché esperado.
        """
        # Validar que cache_root es un subdirectorio esperado
        expected_parent = user_cache_dir("chile-hub")
        cache_path = Path(self.cache_root).resolve()
        if not str(cache_path).startswith(str(Path(expected_parent).resolve())):
            raise ChileHubDataError(
                f"Por seguridad, 'cache clear' solo opera dentro del directorio de cache "
                f"esperado ({expected_parent}). El directorio configurado es {cache_path}. "
                f"Verifica la variable de entorno CHILE_HUB_CACHE_DIR."
            )
        if not cache_path.exists():
            return  # nothing to clear
        shutil.rmtree(str(cache_path))

    def _resolve_release(self) -> dict[str, Any]:
        suffix = (
            "releases/latest"
            if self.data_version == "latest"
            else f"releases/tags/{self.data_version}"
        )
        url = f"https://api.github.com/repos/{self.repository}/{suffix}"
        response = self.session.get(
            url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=30,
        )
        if response.status_code != 200:
            raise ChileHubDataError(
                f"Could not resolve chile-hub release '{self.data_version}' "
                f"from {url}: HTTP {response.status_code}"
            )
        return response.json()  # type: ignore[no-any-return]  # requests.Response.json → dict en runtime

    @staticmethod
    def _assets_by_name(release: dict[str, Any]) -> dict[str, ReleaseAsset]:
        return {
            asset["name"]: ReleaseAsset(
                name=asset["name"],
                url=asset["browser_download_url"],
            )
            for asset in release.get("assets", [])
            if asset.get("name") and asset.get("browser_download_url")
        }

    @staticmethod
    def _require_asset(assets: dict[str, ReleaseAsset], name: str) -> ReleaseAsset:
        if name not in assets:
            available = ", ".join(sorted(assets)) or "none"
            raise ChileHubDataError(f"Release asset '{name}' not found. Available: {available}")
        return assets[name]

    def _download(self, url: str, destination: Path) -> None:
        with self.session.get(url, stream=True, timeout=120) as response:
            if response.status_code != 200:
                raise ChileHubDataError(f"Could not download {url}: HTTP {response.status_code}")
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

    def _extract_bundle(self, bundle_path: Path) -> None:
        if self.normalized_dir.exists():
            shutil.rmtree(self.normalized_dir)
        with zipfile.ZipFile(bundle_path) as archive:
            archive.extractall(self.version_cache_dir)

    @staticmethod
    def _read_checksum(path: Path) -> str:
        line = path.read_text(encoding="utf-8").strip().splitlines()[0]
        return line.split()[0].lower()

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
