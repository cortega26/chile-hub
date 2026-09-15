"""Contrato comun para extractores de chile-hub.

Convención `sys.path` (Plan 099, congela TECHDEBT-05): cada extractor corre en
dos modos — como script (`PYTHONPATH=src python src/extractors/x.py`, vía
Makefile/CI) y como paquete (`src.extractors.x`, vía tests/build). Los imports
absolutos `src.*` solo resuelven en modo paquete, y los relativos (`from base
import …`) solo en modo script; por eso cada módulo trae el idiom canónico ::

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

seguido del `try: from src... except ModuleNotFoundError: from ... import ...`.
El idiom es load-bearing (quitarlo rompe `make extract`) y no se reemplaza por
`_paths.find_root()` (dependencia circular: `_paths` vive bajo `src/` y aún no
es importable en ese punto). Nuevos extractores deben copiarlo tal cual; el
test `SysPathIdiomTests` en `tests/test_ci_config.py` lo exige y falla ante
cualquier otra manipulación de `sys.path` en `src/extractors/`.
"""

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
        # Newline final: sin él, el hook end-of-file-fixer reescribe el archivo
        # en cada corrida de pre-commit y el arbol nunca queda limpio.
        f.write("\n")
    os.replace(tmp_path, path)


def write_raw_snapshot_atomic(path: str | Path, payload: Any) -> None:
    """Persiste un snapshot crudo en data/raw/ de forma atómica.

    Escribe a un hermano temporal y lo mueve con ``os.replace`` (mismo
    patrón que :func:`write_staging_metadata`): un crash a mitad de
    escritura nunca deja un archivo parcial que un lector (p. ej.
    ``load_latest_raw_snapshot``) pueda confundir con un snapshot válido.
    Acepta dict/list (se serializan a JSON), ``str`` o ``bytes``.
    """
    path_str = os.fspath(path)
    tmp_path = path_str + ".tmp"
    if isinstance(payload, (dict, list)):
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    elif isinstance(payload, bytes):
        with open(tmp_path, "wb") as f:
            f.write(payload)
    else:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(payload)
    os.replace(tmp_path, path_str)


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
