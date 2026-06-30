"""Contrato comun para extractores de chile-hub."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import polars as pl

_BASE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
_RAW_DIR = os.path.join(_BASE_DATA_DIR, "raw")
_STAGING_DIR = os.path.join(_BASE_DATA_DIR, "staging")


def ensure_staging_directories() -> None:
    """Crea data/raw/ y data/staging/ si no existen."""
    os.makedirs(_RAW_DIR, exist_ok=True)
    os.makedirs(_STAGING_DIR, exist_ok=True)


def write_staging_metadata(path: str, metadata: dict[str, Any]) -> None:
    """Persiste el metadata.json de un dataset en staging."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


class BaseExtractor(ABC):
    """Contrato común para extractores de chile-hub.

    Los extractores se ejecutan como scripts standalone a través de funciones
    ``process_*()`` invocadas desde el bloque ``if __name__ == "__main__"``
    de cada módulo.  El método ``run()`` es el entry point canónico para uso
    programático (tests, automatizaciones), no para el Makefile.
    """

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nombre canónico registrado en el catálogo de datasets."""

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Any:
        """Obtiene datos desde la fuente o su estrategia de fallback."""

    @abstractmethod
    def normalize(self, raw_data: Any) -> pl.DataFrame:
        """Convierte los datos obtenidos al esquema canónico."""

    @abstractmethod
    def validate(self, df: pl.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
        """Retorna el resultado de validación del dataset."""

    @abstractmethod
    def write_staging(self, df: pl.DataFrame, metadata: dict[str, Any]) -> Path:
        """Persiste el dataset normalizado y sus metadatos en staging."""

    def run(self, dry_run: bool = False, **kwargs: Any) -> dict[str, Any]:
        """Ejecuta el pipeline completo del extractor.

        Entry point canónico para uso programático (tests, automatizaciones).
        Los extractores invocados desde el Makefile usan ``process_*()``
        standalone en vez de este método.
        """
        raw_data = self.fetch(**kwargs)
        df = self.normalize(raw_data)
        metadata = {"dataset": self.dataset_name, "dry_run": dry_run}
        validation = self.validate(df, metadata)
        if not dry_run:
            self.write_staging(df, metadata)
        return validation
