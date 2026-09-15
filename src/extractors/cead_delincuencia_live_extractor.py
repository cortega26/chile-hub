"""Extractor de delincuencia comunal (CEAD) — NO OPERATIVO (deprecated).

Degradado a rechazado el 2026-09-15 al cumplirse su `review_by` (2026-09-21
anticipado por revisión): en 90+ días no apareció ninguna fuente estructurada
oficial (datos.gob.cl solo tiene bulk 2015 con links muertos; el portal CEAD
tiene protección anti-bots y solo publica PDF/presentaciones) y el dataset
nunca fue redistribuible (`redistribution_ok: false`), por lo que jamás
podía entrar al bundle público.

Veredicto registrado en `docs/dataset-ideas/delincuencia-cead.md` (rejected)
y `docs/datasets/delincuencia_comunal.md` (aviso de deprecación).

Este módulo se mantiene como no operativo durante 2 versiones para no romper
imports (AGENTS.md §5, paso 4 de deprecación); luego se elimina junto con su
validación y tests. Cualquier invocación levanta NotImplementedError.
"""

import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import BaseExtractor
except ModuleNotFoundError:
    from base import BaseExtractor

_MSG = (
    "delincuencia_comunal está degradado (rejected 2026-09-15): el CEAD no "
    "expone descarga estructurada (solo scraping HTML frágil tras "
    "protección anti-bots) y los datos no son redistribuibles. Ver "
    "docs/dataset-ideas/delincuencia-cead.md. Reevaluar solo si aparece "
    "una descarga oficial."
)


def fetch_data(*args: Any, **kwargs: Any) -> Any:
    """No operativo: ver docstring del módulo."""
    raise NotImplementedError(_MSG)


def normalize_rows(*args: Any, **kwargs: Any) -> Any:
    """No operativo: ver docstring del módulo."""
    raise NotImplementedError(_MSG)


def build_metadata(*args: Any, **kwargs: Any) -> Any:
    """No operativo: ver docstring del módulo."""
    raise NotImplementedError(_MSG)


def process_cead_delincuencia(*args: Any, **kwargs: Any) -> Any:
    """No operativo: ver docstring del módulo."""
    raise NotImplementedError(_MSG)


class CeaddelincuenciaLiveExtractor(BaseExtractor):
    """Stub no operativo (deprecated 2026-09-15)."""

    @property
    def dataset_name(self) -> str:
        return "delincuencia_comunal"

    def fetch(self, **kwargs: Any) -> Any:
        raise NotImplementedError(_MSG)

    def normalize(self, raw_data: Any) -> Any:
        raise NotImplementedError(_MSG)

    def validate(self, df: Any, metadata: dict) -> dict:
        raise NotImplementedError(_MSG)

    def write_staging(self, df: Any, metadata: dict) -> Path:
        raise NotImplementedError(_MSG)


if __name__ == "__main__":
    raise NotImplementedError(_MSG)
