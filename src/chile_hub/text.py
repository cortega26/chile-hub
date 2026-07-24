"""Normalización de texto compartida para búsqueda de nombres sin acento.

La cadena de minúsculas + reemplazo de acentos/``ñ`` debe mantenerse idéntica a
la que produce ``nombre_comuna_clean`` en ``src/extractors/subdere_extractor.py``
(invariante #4, AGENTS.md §4.5) — mismo orden, mismos reemplazos. Si esa cadena
cambia, cambia también aquí (ver ADR-009).

**Única divergencia intencional**: esta función además recorta espacios al borde
(``.strip()``) antes de normalizar; la cadena Polars del extractor no lo hace
porque ``nombre_comuna`` ya llega sin espacios sobrantes desde la fuente BCN. El
recorte es seguro (no puede producir un match falso: ninguna comuna publicada
tiene espacios al borde en su forma limpia), y existe para tolerar input de
usuario tipeado a mano (el caso de uso real de ``resolve_comunas``), que sí puede
traer espacios extra. El test de paridad anti-divergencia en
``tests/test_core.py`` verifica el resto de la cadena contra las 346 comunas
reales; ``tests/test_pipeline_logic.py`` cubre el ``.strip()`` por separado.
"""

_ACCENT_MAP = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}


def normalize_comuna_name(name: str) -> str:
    """Normaliza un nombre de comuna a su forma ``nombre_comuna_clean``.

    Minúsculas, sin acentos, sin ``ñ``, sin espacios al borde. Es la clave
    canónica de join de texto inexacto del proyecto.
    ``normalize_comuna_name("Ñuñoa") == "nunoa"``.
    """
    out = name.strip().lower()
    for src, dst in _ACCENT_MAP.items():
        out = out.replace(src, dst)
    return out
