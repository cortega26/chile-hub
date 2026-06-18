"""Python access layer for curated Chilean public datasets."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .core import ChileHub, main
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
    """Read the package version from the single source of truth: pyproject.toml.

    In development (source checkout), the version is parsed directly from
    ``pyproject.toml`` on disk.  When installed from a PyPI wheel — where
    ``pyproject.toml`` is not distributed — we fall back to the version
    embedded in the wheel's METADATA by the build backend.
    """
    # 1. Development checkout — read directly from pyproject.toml.
    _pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if _pyproject.is_file():
        try:
            _text = _pyproject.read_text(encoding="utf-8")
        except OSError:
            pass
        else:
            _match = re.search(r'^version\s*=\s*"([^"]+)"', _text, re.MULTILINE)
            if _match:
                return _match.group(1)

    # 2. Installed from PyPI wheel — version is in wheel METADATA.
    if sys.version_info >= (3, 8):  # pragma: no cover – always true on 3.10+
        try:
            from importlib.metadata import PackageNotFoundError, version

            return version("chile-hub")
        except PackageNotFoundError:
            pass

    # 3. Last resort — should never happen in practice.
    return "0.0.0"


__version__ = _get_version()
