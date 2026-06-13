"""Contrato comun para extractores de chile-hub."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

_BASE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
_RAW_DIR = os.path.join(_BASE_DATA_DIR, "raw")
_STAGING_DIR = os.path.join(_BASE_DATA_DIR, "staging")


def ensure_staging_directories() -> None:
    """Crea data/raw/ y data/staging/ si no existen."""
    os.makedirs(_RAW_DIR, exist_ok=True)
    os.makedirs(_STAGING_DIR, exist_ok=True)


class BaseExtractor(ABC):
    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nombre canonico registrado en el catalogo de datasets."""

    @abstractmethod
    def fetch(self, **kwargs):
        """Obtiene datos desde la fuente o su estrategia de fallback."""

    @abstractmethod
    def normalize(self, raw_data):
        """Convierte los datos obtenidos al schema canonico."""

    @abstractmethod
    def validate(self, df, metadata: dict) -> dict:
        """Retorna el resultado de validacion del dataset."""

    @abstractmethod
    def write_staging(self, df, metadata: dict) -> Path:
        """Persiste el dataset normalizado y sus metadatos en staging."""

    def run(self, dry_run: bool = False, **kwargs) -> dict:
        raw_data = self.fetch(**kwargs)
        df = self.normalize(raw_data)
        metadata = {"dataset": self.dataset_name, "dry_run": dry_run}
        validation = self.validate(df, metadata)
        if not dry_run:
            self.write_staging(df, metadata)
        return validation
