"""Utilidades compartidas de normalización de texto y mapeo de regiones de Chile.

Extraído de `autoridades_locales_extractor.py` (Plan 023) para reutilizarse también en
`autoridades_electas_extractor.py` (región de senadores desde `senado.cl`).

Desde Plan 129 este módulo **delega en el paquete** `chile_hub` (fuente única):
`chile_hub.regions` para la tabla y el mapeo, `chile_hub.text.norm_text` para la
normalización. El import usa la forma `src.chile_hub.*` (el patrón establecido
de los extractores) para que mypy no resuelva el mismo archivo dos veces, como
`src.chile_hub.regions` y `chile_hub.regions`. Conserva su API pública
(`norm_text`, `REGION_A_CODIGO`, `region_nombre_a_codigo`) para no tocar a los
extractores que la importan.

Fallback: `autoridades_electas_extractor` corre en CI dentro de un entorno efímero
de `uv` (`uv run --no-project --with "scrapling[fetchers]"`, ver
`pipeline-check.yml`) que no instala las dependencias del paquete `chile_hub`
(rich, platformdirs, ...). Si el import del paquete falla, la copia local de
abajo —idéntica a la tabla original— mantiene el extractor funcionando. El test
`RegionAliasParityTests` carga esta rama a propósito y congela la equivalencia
con el paquete (16 regiones + alias).
"""

import re
import unicodedata

try:
    from src.chile_hub.regions import REGION_ALIASES as REGION_A_CODIGO
    from src.chile_hub.regions import region_name_to_code
    from src.chile_hub.text import norm_text
except ModuleNotFoundError:
    REGION_A_CODIGO = {
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
        "libertador bernardo o'higgins": "06",
        "o'higgins": "06",
        "maule": "07",
        "nuble": "16",
        "biobio": "08",
        "bio-bio": "08",
        "la araucania": "09",
        "araucania": "09",
        "los rios": "14",
        "los lagos": "10",
        "aysen del general carlos ibanez del campo": "11",
        "aysen del gral.ibanez del campo": "11",
        "aysen": "11",
        "magallanes y de la antartica chilena": "12",
        "magallanes y la antartica chilena": "12",
        "magallanes y antartica chilena": "12",
        "magallanes y antartica": "12",
        "magallanes": "12",
    }

    def norm_text(text: str) -> str:
        nfkd = unicodedata.normalize("NFKD", text.lower().strip())
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    _REGION_PREFIJO_RE = re.compile(r"^region\s+(?:metropolitana\s+)?(?:de\s+|del\s+)?", re.I)

    def region_name_to_code(texto: str) -> str | None:
        return REGION_A_CODIGO.get(_REGION_PREFIJO_RE.sub("", norm_text(texto)).strip())


region_nombre_a_codigo = region_name_to_code
