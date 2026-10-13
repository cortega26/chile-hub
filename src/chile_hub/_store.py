"""Artifact store interno de la fachada ChileHub (plan 134a).

Contexto (auditoría 2026-10-13, hallazgo B019): los loaders de artefactos
JSON usaban `functools.lru_cache(maxsize=1)` sobre métodos de instancia, lo
que retiene cada `ChileHub` en una caché a nivel clase — fuga real para
consumidores que crean un hub por request. Este store mueve esa caché a un
dict por instancia: mismo contenido cacheado por hub, sin compartición entre
hubs y sin retención.

Semántica conservada a propósito (revisión del advisor):

- `load_*()` devuelve **el mismo objeto** cacheado (los consumidores mutan
  en-place, p. ej. `health()["top_issue_summary"]`), igual que `lru_cache`.
- La lectura del catálogo mantiene el mismo `ChileHubDataError` con mensaje
  de guía cuando falta.
- `load_catalog` no se cachea: `ChileHub.__init__` lo lee una sola vez.
"""

import json
from pathlib import Path
from typing import Any

from .exceptions import ChileHubDataError


class ArtifactStore:
    """Lectores y caché por instancia de los artefactos de `data/normalized/`."""

    def __init__(self, normalized_dir: Path) -> None:
        self._dir = normalized_dir
        self._cache: dict[str, Any] = {}

    def load_catalog(self, catalog_path: Path) -> dict[str, Any]:
        """Catálogo de datasets; mensaje de error con guía de recuperación."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]  # json.load → dict en runtime
        except FileNotFoundError as exc:
            raise ChileHubDataError(
                f"Catálogo de datasets no encontrado en {catalog_path}. "
                f"Usa ChileHub() sin argumentos para descargar el bundle automáticamente, "
                f"o asegúrate de que el directorio '{catalog_path.parent}' contiene "
                f"los datos normalizados (ejecuta 'make build' si estás en desarrollo)."
            ) from exc

    def load_json(self, filename: str) -> dict[str, Any]:
        """Lee (y cachea por hub) un artefacto JSON de `normalized_dir`."""
        cached: Any = self._cache.get(filename)
        if cached is None:
            with (self._dir / filename).open("r", encoding="utf-8") as f:
                cached = json.load(f)
            self._cache[filename] = cached
        return cached  # type: ignore[no-any-return]  # json.load → dict en runtime

    def load_artifact_manifest(self) -> dict[str, Any]:
        return self.load_json("artifact_manifest.json")

    def load_hub_health(self) -> dict[str, Any]:
        return self.load_json("hub_health.json")

    def load_hub_status(self) -> dict[str, Any]:
        return self.load_json("hub_status.json")

    def load_dataset_status(self) -> dict[str, Any]:
        return self.load_json("dataset_status.json")

    def load_dataset_changelog(self) -> dict[str, Any]:
        return self.load_json("dataset_changelog.json")

    def load_hub_bundle(self) -> dict[str, Any]:
        return self.load_json("hub_bundle.json")

    def load_redistribution_report(self) -> dict[str, Any]:
        return self.load_json("redistribution_report.json")

    def load_provenance_report(self) -> dict[str, Any]:
        return self.load_json("provenance_report.json")

    def load_drift_report(self) -> dict[str, Any]:
        return self.load_json("drift_report.json")

    def load_source_readiness(self) -> dict[str, Any]:
        return self.load_json("source_readiness.json")

    def load_dataset_quality(self) -> dict[str, Any]:
        return self.load_json("dataset_quality.json")
