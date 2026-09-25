"""Inyecta JSON-LD schema.org `Dataset` en las páginas de dataset de mkdocs.

El sitio estático tiene 86 páginas de documentación (mkdocs, `site_dir:
reference/`) pero las páginas `reference/datasets/{capa}/` sólo llevan
`canonical`: sin markup schema.org no pueden aparecer en Google Dataset
Search. Este script post-build inserta, antes de `</head>`, un bloque
`<script type="application/ld+json" id="chile-hub-dataset-json-ld">` por cada
capa del catálogo que tenga página, reutilizando
`src.builders.landing.build_dataset_json_ld()` (fuente única del shape).

Idempotente: re-ejecutarlo reemplaza el bloque existente, no lo duplica.
Corre en `.github/workflows/pages-deploy.yml` después de `mkdocs build`.

Uso:
  python scripts/inject_dataset_json_ld.py --site-dir reference
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.builders.landing import build_dataset_json_ld  # noqa: E402

JSON_LD_ID = "chile-hub-dataset-json-ld"
_MARKER = f'id="{JSON_LD_ID}"'
_BLOCK_PATTERN = re.compile(
    rf'<script type="application/ld\+json" id="{JSON_LD_ID}">.*?</script>\n?',
    re.DOTALL,
)


def inject_page(html: str, json_ld: dict) -> str:
    """Inserta (o reemplaza) el bloque JSON-LD del dataset en una página HTML."""
    body = json.dumps(json_ld, indent=2, ensure_ascii=False)
    block = f'<script type="application/ld+json" id="{JSON_LD_ID}">\n{body}\n</script>\n'
    if _MARKER in html:
        return _BLOCK_PATTERN.sub(lambda _: block, html, count=1)
    return html.replace("</head>", block + "</head>", 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir",
        default=str(ROOT_DIR / "reference"),
        help="Directorio generado por mkdocs (default: reference/).",
    )
    parser.add_argument(
        "--site-url",
        default="https://tooltician.com/chile-hub/",
        help="URL pública canónica del sitio.",
    )
    parser.add_argument(
        "--catalog",
        default=str(ROOT_DIR / "data" / "dataset_catalog_config.json"),
        help="Catálogo de datasets (JSON) a usar como fuente.",
    )
    args = parser.parse_args(argv)

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    datasets_root = Path(args.site_dir) / "datasets"
    pages = sorted(datasets_root.glob("*/index.html"))
    if not pages:
        raise SystemExit(
            f"ERROR: no hay páginas de dataset en {datasets_root}. "
            "Corre 'mkdocs build' antes de inyectar el JSON-LD."
        )

    injected = 0
    missing: list[str] = []
    for key in sorted(catalog):
        page = datasets_root / key / "index.html"
        if not page.is_file():
            missing.append(key)
            continue
        html = page.read_text(encoding="utf-8")
        new_html = inject_page(html, build_dataset_json_ld(key, args.site_url, catalog=catalog))
        if new_html != html:
            page.write_text(new_html, encoding="utf-8")
        injected += 1

    detail = f" ({len(missing)} sin página: {', '.join(missing)})" if missing else ""
    print(f"{injected} páginas con Dataset JSON-LD{detail}")
    if injected == 0:
        raise SystemExit(
            "ERROR: ninguna capa del catálogo tiene página en "
            f"{datasets_root}; revisa el layout de mkdocs."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
