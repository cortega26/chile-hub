"""Resolución de nombres de región de Chile a códigos CUT de 2 dígitos.

Fuente única de la tabla de alias que antes vivía en
``src/extractors/region_utils.py`` (Plan 023). El paquete no puede importar
extractores: la dependencia va en un solo sentido — el extractor delega aquí
(mismo patrón que ``chile_hub.text.normalize_comuna_name``).

Las claves de ``REGION_ALIASES`` están en la forma normalizada que produce
``normalize_region_name`` (minúsculas, sin acentos) para que el lookup sea una
igualdad de strings. La tabla incluye los alias históricos de los extractores
más las variantes oficiales publicadas en el dataset ``regiones`` (p. ej.
"Bío-Bío" con guion, "Gral.Ibañez") y "rm", de uso masivo en Chile.
"""

from __future__ import annotations

import re

from .text import norm_text

# Nombre de región (normalizado) -> código CUT de 2 dígitos.
REGION_ALIASES: dict[str, str] = {
    "arica y parinacota": "15",
    "tarapaca": "01",
    "antofagasta": "02",
    "atacama": "03",
    "coquimbo": "04",
    "valparaiso": "05",
    "metropolitana de santiago": "13",
    "metropolitana": "13",
    "santiago": "13",
    "rm": "13",
    "libertador general bernardo o'higgins": "06",
    # Variante oficial del dataset regiones ("Región del Libertador Bernardo O'Higgins").
    "libertador bernardo o'higgins": "06",
    "o'higgins": "06",
    "maule": "07",
    "nuble": "16",
    "biobio": "08",
    # Variante oficial del dataset regiones ("Región del Bío-Bío").
    "bio-bio": "08",
    "la araucania": "09",
    "araucania": "09",
    "los rios": "14",
    "los lagos": "10",
    "aysen del general carlos ibanez del campo": "11",
    # Variante oficial del dataset regiones ("Región de Aysén del Gral.Ibañez del Campo").
    "aysen del gral.ibanez del campo": "11",
    "aysen": "11",
    "magallanes y de la antartica chilena": "12",
    "magallanes y la antartica chilena": "12",
    # Variante oficial del dataset regiones ("Región de Magallanes y Antártica Chilena").
    "magallanes y antartica chilena": "12",
    "magallanes y antartica": "12",
    "magallanes": "12",
}

# Prefijo habitual antes del nombre de región ("Región de Antofagasta", "Región del
# Biobío", "Región Metropolitana"), a quitar antes del lookup en REGION_ALIASES.
_REGION_PREFIJO_RE = re.compile(r"^region\s+(?:metropolitana\s+)?(?:de\s+|del\s+)?", re.I)


def normalize_region_name(texto: str) -> str:
    """Normaliza un nombre de región a la forma de las claves de ``REGION_ALIASES``.

    Minúsculas, sin acentos y sin el prefijo "Región (Metropolitana) de/del".
    ``normalize_region_name("Región del Bío-Bío") == "bio-bio"``.
    """
    return _REGION_PREFIJO_RE.sub("", norm_text(texto)).strip()


def region_name_to_code(texto: str) -> str | None:
    """Mapea un nombre de región (con o sin prefijo "Región de/del") a su código CUT."""
    return REGION_ALIASES.get(normalize_region_name(texto))
