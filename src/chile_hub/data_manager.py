"""Acceso en tiempo de ejecución a activos de release de datos versionados de chile-hub."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import warnings
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from platformdirs import user_cache_dir

from .exceptions import ChileHubDataError

DEFAULT_REPOSITORY = "cortega26/chile-hub"
DEFAULT_BUNDLE_NAME = "chile-hub-publishable-bundle.zip"
DEFAULT_CHECKSUM_NAME = "chile-hub-publishable-bundle.zip.sha256"
ENV_CACHE_DIR = "CHILE_HUB_CACHE_DIR"
ENV_DISABLE_UPDATE_CHECK = "CHILE_HUB_NO_UPDATE_CHECK"
ENV_LANGUAGE = "CHILE_HUB_LANG"
UPDATE_CHECK_INTERVAL = timedelta(days=7)
UPDATE_CHECK_TIMEOUT = 3
UTC = timezone.utc
SUPPORT_URL = f"https://github.com/sponsors/{DEFAULT_REPOSITORY.split('/')[0]}"
BUY_ME_A_COFFEE_URL = f"https://www.buymeacoffee.com/{DEFAULT_REPOSITORY.split('/')[0]}"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str


class ChileHubUpdateWarning(UserWarning):
    """Avisa que existe una nueva versión de los datos publicados."""


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

    @property
    def update_check_path(self) -> Path:
        """Ruta del estado local del chequeo periódico de actualizaciones."""
        return self.version_cache_dir / ".update_check.json"

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
            self._check_for_update_if_due()
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
        expected_parent = Path(user_cache_dir("chile-hub")).resolve()
        cache_path = Path(self.cache_root).resolve()
        if not cache_path.is_relative_to(expected_parent):
            raise ChileHubDataError(
                f"Por seguridad, 'cache clear' solo opera dentro del directorio de cache "
                f"esperado ({expected_parent}). El directorio configurado es {cache_path}. "
                f"Verifica la variable de entorno CHILE_HUB_CACHE_DIR."
            )
        if not cache_path.exists():
            return  # nothing to clear
        shutil.rmtree(str(cache_path))

    def _check_for_update_if_due(self) -> None:
        """Avisa semanalmente si el bundle ``latest`` quedó desactualizado.

        Es una comprobación de mejor esfuerzo: no envía telemetría ni interrumpe
        el consumo de datos si GitHub, la red o el estado local no están disponibles.
        """
        if self.data_version != "latest" or self._update_checks_disabled():
            return

        state = self._read_json(self.update_check_path)
        if not self._is_update_check_due(state):
            return

        checked_at = datetime.now(UTC)
        try:
            release = self._resolve_release(timeout=UPDATE_CHECK_TIMEOUT)
            latest_tag = release.get("tag_name")
            if not isinstance(latest_tag, str) or not latest_tag:
                raise ValueError("GitHub release response does not include tag_name")

            marker = self._read_json(self.marker_path)
            current_tag = marker.get("release", {}).get("tag_name")
            self._write_json(
                self.update_check_path,
                {
                    "checked_at_utc": checked_at.isoformat(),
                    "latest_tag": latest_tag,
                    "status": "ok",
                },
            )
        except Exception:
            # Esta consulta es opcional: recordar el intento evita reintentos en
            # cada inicialización si el usuario está sin conectividad.
            try:
                self._write_json(
                    self.update_check_path,
                    {
                        "checked_at_utc": checked_at.isoformat(),
                        "status": "unavailable",
                    },
                )
            except OSError:
                pass
            return

        if isinstance(current_tag, str) and current_tag and current_tag != latest_tag:
            warnings.warn(
                self._format_update_notice(current_tag=current_tag, latest_tag=latest_tag),
                ChileHubUpdateWarning,
                stacklevel=3,
            )

    @staticmethod
    def _update_checks_disabled() -> bool:
        value = os.environ.get(ENV_DISABLE_UPDATE_CHECK, "")
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _is_update_check_due(state: dict[str, Any]) -> bool:
        checked_at = state.get("checked_at_utc")
        if not isinstance(checked_at, str):
            return True
        try:
            parsed = datetime.fromisoformat(checked_at)
        except ValueError:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        return parsed > now or now - parsed >= UPDATE_CHECK_INTERVAL

    @staticmethod
    def _preferred_language() -> str:
        """Retorna ``en`` solo para una preferencia inglesa explícita; español es el fallback."""
        language = os.environ.get(ENV_LANGUAGE)
        if not language:
            language = (
                os.environ.get("LC_ALL")
                or os.environ.get("LC_MESSAGES")
                or os.environ.get("LANG")
                or ""
            )
        return "en" if language.lower().startswith("en") else "es"

    @classmethod
    def _format_update_notice(cls, *, current_tag: str, latest_tag: str) -> str:
        if cls._preferred_language() == "en":
            return (
                f"A new chile-hub data release is available: {latest_tag}\n"
                f"Cached version: {current_tag}\n\n"
                "Update it with:\n"
                "    chile-hub cache update\n\n"
                "chile-hub is an independent project developed and maintained by one person, "
                "without institutional sponsors or affiliations. This independence lets it "
                "prioritize verifiable data and deliver an objective, impartial, useful, "
                "high-quality tool.\n\n"
                "If chile-hub is useful to you, consider supporting its development and "
                f"maintenance financially:\n{SUPPORT_URL}\n{BUY_ME_A_COFFEE_URL}"
            )
        return (
            f"Hay una nueva versión de los datos de chile-hub: {latest_tag}\n"
            f"Versión almacenada localmente: {current_tag}\n\n"
            "Actualízala ejecutando:\n"
            "    chile-hub cache update\n\n"
            "chile-hub es un proyecto independiente, desarrollado y mantenido por una sola "
            "persona, sin patrocinadores institucionales ni afiliaciones. Esta independencia "
            "permite priorizar datos verificables y ofrecer una herramienta objetiva, "
            "imparcial, útil y de calidad.\n\n"
            "Si chile-hub te resulta útil, puedes apoyar económicamente su desarrollo y "
            f"mantenimiento:\n{SUPPORT_URL}\n{BUY_ME_A_COFFEE_URL}"
        )

    def _resolve_release(self, *, timeout: float = 30) -> dict[str, Any]:
        suffix = (
            "releases/latest"
            if self.data_version == "latest"
            else f"releases/tags/{self.data_version}"
        )
        url = f"https://api.github.com/repos/{self.repository}/{suffix}"
        response = self.session.get(
            url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=timeout,
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
            # Zip-slip guard (Plan 072): el checksum SHA-256 verifica el bundle
            # contra un .sha256 de la MISMA release de GitHub — no añade un
            # dominio de confianza distinto. Un miembro con `../` o un symlink
            # permitiría escritura arbitraria fuera del directorio de caché si
            # la release se viera comprometida. Se validan TODOS los miembros
            # antes de extraer: solo se aceptan rutas bajo `data/normalized/`.
            for member in archive.infolist():
                filename = member.filename
                if not filename or filename == ".":
                    raise ChileHubDataError("Bundle ZIP inválido: miembro con nombre vacío o '.'.")
                if filename.startswith("/") or "\\" in filename or ".." in filename:
                    raise ChileHubDataError(
                        f"Bundle ZIP inválido: miembro con path traversal: {filename!r}"
                    )
                if not filename.startswith("data/normalized/"):
                    raise ChileHubDataError(
                        f"Bundle ZIP inválido: miembro fuera de data/normalized/: {filename!r}"
                    )
                # Detección de symlink: el modo unix (S_IFLNK = 0o120000) se
                # codifica en los bits altos de external_attr de ZipInfo.
                if member.external_attr >> 16 & 0o170000 == 0o120000:
                    raise ChileHubDataError(
                        f"Bundle ZIP inválido: miembro symlink no permitido: {filename!r}"
                    )
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

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
