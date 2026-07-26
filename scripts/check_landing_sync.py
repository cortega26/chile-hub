"""Gate anti-drift: index.html y app.js deben estar sincronizados con el catálogo.

`sync_landing_metadata()` regenera, en cada `make build`, tres cosas derivadas:

1. el bloque JSON-LD `DataCatalog` de `index.html`, desde `data/dataset_catalog_config.json`;
2. el `PUBLIC_DATA_BASE` de `app.js`, desde `[tool.chile_hub] public_site_url`;
3. el cache-buster `app.js?v={version}` de `index.html`, desde `[project] version`.

Si el catálogo (o la URL, o la versión) cambia y no se vuelve a correr el build,
esos archivos quedan desfasados. El gate de CI que lo detecta
("Check build-synced files") solo corre en la vía `schedule`/`workflow_dispatch`,
es decir una vez al día y después de un pipeline completo de ~2 minutos, así que
la deriva queda latente durante días y aborta el publish diario.

Ya ocurrió dos veces: `autoridades_locales` (Pipeline Check #270) y
`geometria_comunal` (agregado al catálogo en 56cd9d5 el 2026-07-23, detectado el
2026-07-24/25/26). Los tests de `SyncLandingMetadataTests` no lo atrapan porque
ejercitan la función contra un fixture temporal, no contra el archivo commiteado.

Este script cierra ese hueco de forma determinista y sin correr el pipeline, para
poder ejecutarse en cada push y PR.

NO cubre la tabla de capas del README — de eso se encarga `scripts/sync_docs.py --check`.
"""

import re
import sys
from pathlib import Path

import tomllib

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.builders.landing import (  # noqa: E402
    CATALOG_JSON_LD_START_MARKER,
    extract_catalog_json_ld_block,
    normalize_site_url,
    render_catalog_json_ld_block,
)

INDEX_PATH = ROOT_DIR / "index.html"
APP_PATH = ROOT_DIR / "app.js"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"

REMEDIATION = "Corre `python src/build_dev_db.py` (o `make build`) y commitea index.html/app.js."


def load_project_settings():
    """Lee la versión y la URL pública canónica desde pyproject.toml."""
    with open(PYPROJECT_PATH, "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data.get("project", {}).get("version", "unknown")
    public_site_url = (
        pyproject_data.get("tool", {})
        .get("chile_hub", {})
        .get("public_site_url", "https://tooltician.com/chile-hub/")
    )
    return version, normalize_site_url(public_site_url)


def check_json_ld_block(index_html, public_site_url):
    """El bloque JSON-LD commiteado debe ser byte a byte el que genera el build."""
    if CATALOG_JSON_LD_START_MARKER not in index_html:
        return [
            "index.html no contiene el marcador "
            f"{CATALOG_JSON_LD_START_MARKER} — sync_landing_metadata() no puede "
            "regenerar el bloque JSON-LD y fallaría en silencio"
        ]

    actual = extract_catalog_json_ld_block(index_html)
    if actual is None:
        return [
            "index.html tiene el marcador de apertura del JSON-LD pero no el de "
            "cierre — el bloque está malformado"
        ]

    expected = render_catalog_json_ld_block(public_site_url)
    if actual != expected:
        return [describe_json_ld_drift(actual, expected)]
    return []


def describe_json_ld_drift(actual, expected):
    """Mensaje accionable: qué datasets sobran/faltan, o la primera línea que difiere."""
    dataset_pattern = r'"url": "[^"]*#dataset-([^"]+)"'
    actual_keys = re.findall(dataset_pattern, actual)
    expected_keys = re.findall(dataset_pattern, expected)

    missing = [k for k in expected_keys if k not in actual_keys]
    extra = [k for k in actual_keys if k not in expected_keys]
    if missing or extra:
        details = []
        if missing:
            details.append("faltan en index.html: " + ", ".join(missing))
        if extra:
            details.append("sobran en index.html: " + ", ".join(extra))
        return "el JSON-LD está desfasado del catálogo (" + "; ".join(details) + ")"

    for line_no, (actual_line, expected_line) in enumerate(
        zip(actual.splitlines(), expected.splitlines(), strict=False), start=1
    ):
        if actual_line != expected_line:
            return (
                f"el JSON-LD difiere del generado en la línea {line_no} del bloque\n"
                f"    commiteado: {actual_line.strip()[:160]}\n"
                f"    esperado:   {expected_line.strip()[:160]}"
            )
    return "el JSON-LD difiere del generado (largo distinto)"


def check_app_data_base(app_js, public_site_url):
    """app.js debe apuntar al mismo host publicado que index.html."""
    expected = f'const PUBLIC_DATA_BASE = "{public_site_url}data/normalized";'
    if expected in app_js:
        return []
    match = re.search(r'const PUBLIC_DATA_BASE = "[^"]+";', app_js)
    actual = match.group(0) if match else "(no encontrado)"
    return [f"app.js tiene {actual} pero se esperaba {expected}"]


def check_app_cache_buster(index_html, version):
    """El cache-buster de app.js debe seguir a [project] version."""
    if version == "unknown":
        return []
    match = re.search(r'<script src="app\.js(?:\?v=([^"]*))?" defer></script>', index_html)
    if not match:
        return ["index.html no referencia app.js con el patrón esperado"]
    actual_version = match.group(1)
    if actual_version != version:
        return [
            f"index.html carga app.js?v={actual_version} pero pyproject.toml "
            f"declara la versión {version}"
        ]
    return []


def main():
    version, public_site_url = load_project_settings()

    for path in (INDEX_PATH, APP_PATH):
        if not path.exists():
            raise SystemExit(f"ERROR: no existe {path.relative_to(ROOT_DIR)}")

    index_html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_PATH.read_text(encoding="utf-8")

    problems = [
        *check_json_ld_block(index_html, public_site_url),
        *check_app_data_base(app_js, public_site_url),
        *check_app_cache_buster(index_html, version),
    ]

    if problems:
        raise SystemExit(
            "ERROR: la landing está desfasada de sus fuentes:\n"
            + "\n".join(f"  - {problem}" for problem in problems)
            + f"\n{REMEDIATION}"
        )

    dataset_count = len(re.findall(r'"@type": "Dataset"', index_html))
    print(
        f"landing sync ok: {dataset_count} datasets en el JSON-LD, "
        f"app.js?v={version}, base pública {public_site_url}"
    )


if __name__ == "__main__":
    main()
