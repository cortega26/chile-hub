"""Normalización de texto compartida para búsqueda de nombres sin acento.

La cadena de reemplazos debe mantenerse idéntica a la que produce
``nombre_comuna_clean`` en ``src/extractors/subdere_extractor.py`` (invariante #4,
AGENTS.md §4.5). Si esa cadena cambia, cambia también aquí (ver ADR-009).
"""

_ACCENT_MAP = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}


def normalize_comuna_name(name: str) -> str:
    """Normaliza un nombre de comuna a su forma ``nombre_comuna_clean``.

    Minúsculas, sin acentos, sin ``ñ``. Es la clave canónica de join de texto
    inexacto del proyecto. ``normalize_comuna_name("Ñuñoa") == "nunoa"``.
    """
    out = name.strip().lower()
    for src, dst in _ACCENT_MAP.items():
        out = out.replace(src, dst)
    return out
