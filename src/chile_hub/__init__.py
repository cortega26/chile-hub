"""Capa de acceso en Python para datasets públicos chilenos curados."""

from __future__ import annotations

import re
import sys

from .cli import main
from .core import ChileHub
from .exceptions import (
    ChileHubDataError,
    ChileHubDatasetError,
    ChileHubError,
    ChileHubExampleError,
    ChileHubOutputError,
)

__all__ = [
    "ChileHub",
    "ChileHubDataError",
    "ChileHubDatasetError",
    "ChileHubError",
    "ChileHubExampleError",
    "ChileHubOutputError",
    "__version__",
    "main",
]


def _get_version() -> str:
    """Lee la versión del paquete desde la fuente única de verdad: pyproject.toml.

    En desarrollo (checkout del código fuente), la versión se parsea directamente
    desde ``pyproject.toml`` en disco. Cuando se instala desde una rueda PyPI
    (donde ``pyproject.toml`` no se distribuye), se recurre a la versión
    incrustada en los metadatos de la rueda por el build backend.
    """
    # 1. Development checkout — lectura directa de pyproject.toml.
    from ._paths import find_root

    _pyproject = find_root() / "pyproject.toml"
    if _pyproject.is_file():
        try:
            _text = _pyproject.read_text(encoding="utf-8")
        except OSError:
            pass
        else:
            _match = re.search(r'^version\s*=\s*"([^"]+)"', _text, re.MULTILINE)
            if _match:
                return _match.group(1)

    # 2. Instalado desde rueda PyPI — la versión está en los metadatos de la rueda.
    if sys.version_info >= (3, 8):  # pragma: no cover – always true on 3.10+
        try:
            from importlib.metadata import PackageNotFoundError, version

            return version("chile-hub")
        except PackageNotFoundError:
            pass

    # 3. Último recurso — nunca debería ocurrir en la práctica.
    return "0.0.0"


__version__ = _get_version()
