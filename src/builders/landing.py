"""Sincronización de metadatos JSON-LD y enlaces en la landing page.

El bloque JSON-LD de `index.html` y el `PUBLIC_DATA_BASE` de `app.js` son
artefactos **derivados**: se generan desde `data/dataset_catalog_config.json`
y `pyproject.toml`, no se editan a mano. `render_catalog_json_ld_block()` es
la única fuente de verdad de ese bloque; la usan tanto el pipeline
(`sync_landing_metadata`, vía `build_dev_db.py`) como el gate
`scripts/check_landing_sync.py`, para que no existan dos representaciones
que puedan divergir.
"""

import json
import os
import re

from src.builders._shared import DATASET_CATALOG_CONFIG, ROOT_DIR

CATALOG_JSON_LD_START_MARKER = "<!-- START_DATA_CATALOG_JSON_LD -->"
CATALOG_JSON_LD_END_MARKER = "<!-- END_DATA_CATALOG_JSON_LD -->"

DEFAULT_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

DISPLAY_NAMES = {
    "regiones": "Regiones de Chile",
    "provincias": "Provincias de Chile",
    "comunas": "División Político-Administrativa (DPA) de Chile",
    "comunas_enriquecidas": "Comunas Enriquecidas de Chile",
    "indicadores": "Indicadores Económicos de Chile",
    "censo_comunal": "Censo Comunal de Chile 2024",
    "censo_hogares_viviendas": "Censo Hogares y Viviendas de Chile 2024",
    "establecimientos_salud": "Establecimientos de Salud de Chile",
    "distritos_electorales": "Distritos Electorales de Chile",
    "establecimientos_educacionales": "Establecimientos Educacionales de Chile",
    "finanzas_municipales": "Finanzas Municipales de Chile",
    "resultados_educacionales": "Resultados Educacionales de Chile",
    "indicadores_urbanos_siedu": "Indicadores Urbanos SIEDU de Chile",
    "perfil_territorial_comunal": "Perfil Territorial Comunal de Chile",
    "empresas": "Registro de Empresas y Sociedades de Chile (RES)",
}

CREATORS = {
    "regiones": "Biblioteca del Congreso Nacional de Chile (BCN)",
    "provincias": "Biblioteca del Congreso Nacional de Chile (BCN)",
    "comunas": "Biblioteca del Congreso Nacional de Chile (BCN)",
    "comunas_enriquecidas": "Biblioteca del Congreso Nacional de Chile (BCN) e Instituto Nacional de Estadísticas (INE)",
    "indicadores": "Banco Central de Chile e Instituto Nacional de Estadísticas (INE)",
    "censo_comunal": "Instituto Nacional de Estadísticas (INE)",
    "censo_hogares_viviendas": "Instituto Nacional de Estadísticas (INE)",
    "establecimientos_salud": "Ministerio de Salud de Chile (MINSAL)",
    "distritos_electorales": "Biblioteca del Congreso Nacional de Chile (BCN) y Servicio Electoral de Chile (SERVEL)",
    "establecimientos_educacionales": "Ministerio de Educación de Chile (MINEDUC)",
    "finanzas_municipales": "Sistema Nacional de Información Municipal (SINIM) y SUBDERE",
    "resultados_educacionales": "Ministerio de Educación de Chile (MINEDUC)",
    "indicadores_urbanos_siedu": "Instituto Nacional de Estadísticas (INE) y SIEDU",
    "perfil_territorial_comunal": "chile-hub (Capa derivada a partir de datasets validados de chile-hub)",
    "empresas": "Registro de Empresas y Sociedades (RES) - Ministerio de Economía de Chile",
}


def normalize_site_url(public_site_url):
    """Normaliza la URL pública a la forma canónica con slash final."""
    return public_site_url.rstrip("/") + "/"


def build_catalog_json_ld(public_site_url):
    """Construye el DataCatalog schema.org a partir del catálogo de datasets.

    Función pura: no lee ni escribe archivos. Cada entrada de
    DATASET_CATALOG_CONFIG produce exactamente un Dataset, en el mismo orden.
    """
    public_site_url = normalize_site_url(public_site_url)

    datasets_json_ld = []
    for key, config in DATASET_CATALOG_CONFIG.items():
        reuse_policy = config.get("reuse_policy", {})
        datasets_json_ld.append(
            {
                "@type": "Dataset",
                "name": DISPLAY_NAMES.get(key, key),
                "description": config.get("description", ""),
                "url": f"{public_site_url}#dataset-{key}",
                "license": reuse_policy.get("license_url", DEFAULT_LICENSE_URL),
                "creator": {
                    "@type": "Organization",
                    "name": CREATORS.get(key, "chile-hub"),
                },
            }
        )

    return {
        "@context": "https://schema.org",
        "@type": "DataCatalog",
        "name": "chile-hub",
        "url": public_site_url,
        "description": "Capa de datos oficial, curada y reproducible sobre Chile. Datasets limpios en Parquet, JSON, DuckDB y Excel.",
        "publisher": {"@type": "Organization", "name": "chile-hub"},
        "dataset": datasets_json_ld,
    }


def render_catalog_json_ld_block(public_site_url):
    """Renderiza el bloque HTML completo (marcadores incluidos) del JSON-LD.

    Fuente única de verdad del bloque que vive en index.html: `sync_landing_metadata`
    lo escribe y `scripts/check_landing_sync.py` lo compara byte a byte.
    """
    catalog_json_ld = build_catalog_json_ld(public_site_url)
    json_ld_string = json.dumps(catalog_json_ld, indent=2, ensure_ascii=False)
    indented_json_ld = "\n".join(
        "    " + line if line.strip() else "" for line in json_ld_string.splitlines()
    )
    return (
        f"{CATALOG_JSON_LD_START_MARKER}\n"
        f'    <script type="application/ld+json">\n'
        f"{indented_json_ld}\n"
        f"    </script>\n"
        f"    {CATALOG_JSON_LD_END_MARKER}"
    )


def extract_catalog_json_ld_block(index_html):
    """Extrae el bloque JSON-LD delimitado por marcadores, o None si falta."""
    match = re.search(
        re.escape(CATALOG_JSON_LD_START_MARKER) + r".*?" + re.escape(CATALOG_JSON_LD_END_MARKER),
        index_html,
        flags=re.DOTALL,
    )
    return match.group(0) if match else None


def sync_landing_metadata(public_site_url, version=None):
    index_path = os.path.join(ROOT_DIR, "index.html")
    app_path = os.path.join(ROOT_DIR, "app.js")
    public_site_url = normalize_site_url(public_site_url)
    public_data_base = public_site_url + "data/normalized"

    try:
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_script = render_catalog_json_ld_block(public_site_url)

            pattern_marker = (
                re.escape(CATALOG_JSON_LD_START_MARKER)
                + r".*?"
                + re.escape(CATALOG_JSON_LD_END_MARKER)
            )
            if CATALOG_JSON_LD_START_MARKER in content:
                new_content = re.sub(pattern_marker, lambda _: new_script, content, flags=re.DOTALL)
            else:
                pattern_catalog = r'<script type="application/ld\+json">\s*\{\s*"@context":\s*"https://schema\.org",\s*"@type":\s*"DataCatalog".*?</script>'
                new_content = re.sub(
                    pattern_catalog, lambda _: new_script, content, flags=re.DOTALL
                )

            replacements = [
                (
                    r"https://cortega26\.github\.io/chile-hub/",
                    public_site_url,
                ),
            ]
            for pattern, replacement in replacements:
                new_content = re.sub(pattern, replacement, new_content)
            if version:
                new_content = re.sub(
                    r'<script src="app\.js(?:\?v=[^"]*)?" defer></script>',
                    f'<script src="app.js?v={version}" defer></script>',
                    new_content,
                )

            if new_content != content:
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(
                    f"Sincronización Landing: index.html actualizado a {public_site_url} con JSON-LD sincronizado."
                )
        if os.path.exists(app_path):
            with open(app_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                r'const PUBLIC_DATA_BASE = "[^"]+";',
                f'const PUBLIC_DATA_BASE = "{public_data_base}";',
                content,
            )
            if new_content != content:
                with open(app_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Sincronización Landing: app.js actualizado a {public_data_base}")
    except Exception as e:
        print(f"Advertencia: No se pudo actualizar la landing: {e}")
