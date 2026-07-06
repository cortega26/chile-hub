"""Utilidades compartidas de normalización de texto y mapeo de regiones de Chile.

Extraído de `autoridades_locales_extractor.py` (Plan 023) para reutilizarse también en
`autoridades_electas_extractor.py` (región de senadores desde `senado.cl`).
"""

import re
import unicodedata


def norm_text(text: str) -> str:
    """Minúsculas sin acentos, para emparejar nombres (regiones, comunas, partidos)."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Nombre corto de región (como aparece en Wikipedia) -> código CUT de 2 dígitos.
REGION_A_CODIGO = {
    "arica y parinacota": "15",
    "tarapaca": "01",
    "antofagasta": "02",
    "atacama": "03",
    "coquimbo": "04",
    "valparaiso": "05",
    "metropolitana de santiago": "13",
    "metropolitana": "13",
    "libertador general bernardo o'higgins": "06",
    "o'higgins": "06",
    "maule": "07",
    "nuble": "16",
    "biobio": "08",
    "la araucania": "09",
    "araucania": "09",
    "los rios": "14",
    "los lagos": "10",
    "santiago": "13",
    "aysen del general carlos ibanez del campo": "11",
    "aysen": "11",
    "magallanes y de la antartica chilena": "12",
    "magallanes y la antartica chilena": "12",
    "magallanes": "12",
}

# Prefijo habitual antes del nombre de región ("Región de Antofagasta", "Región del
# Biobío", "Región Metropolitana"), a quitar antes del lookup en REGION_A_CODIGO.
_REGION_PREFIJO_RE = re.compile(r"^region\s+(?:metropolitana\s+)?(?:de\s+|del\s+)?", re.I)


def region_nombre_a_codigo(texto: str) -> str | None:
    """Mapea un nombre de región (con o sin prefijo "Región de/del") a su código CUT."""
    sin_prefijo = _REGION_PREFIJO_RE.sub("", norm_text(texto)).strip()
    return REGION_A_CODIGO.get(sin_prefijo)
