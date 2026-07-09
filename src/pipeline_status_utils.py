"""Shim de compatibilidad: re-exporta la fuente canónica del paquete.

La implementación real vive en ``chile_hub/pipeline_status_utils.py`` (la copia
empaquetada en el wheel). Este módulo existe para imports del pipeline que corren
con ``PYTHONPATH=src`` (``from pipeline_status_utils import …``). No dupliques
lógica aquí.
"""

from typing import Any


def __getattr__(name: str) -> Any:
    import chile_hub.pipeline_status_utils as _canonical  # noqa: F401

    return getattr(_canonical, name)


def __dir__() -> list[str]:
    import chile_hub.pipeline_status_utils as _canonical  # noqa: F401

    return [k for k in dir(_canonical) if not k.startswith("__")]
