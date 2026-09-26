"""Verifica umbrales de Lighthouse (a11y, SEO, best practices) desde su JSON.

Pensado para CI y para `make lighthouse`: separa el "correr Lighthouse" (npx)
del "decidir si pasa" (stdlib puro), de modo que el umbral sea auditable y
testeable sin navegador.

Uso:
  python scripts/check_lighthouse.py /tmp/lighthouse.json
  python scripts/check_lighthouse.py /tmp/lighthouse.json --min-accessibility 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Umbrales por defecto: el proyecto mantiene 100 en accesibilidad/SEO/best
# practices; exigir 100 en los tres es realista (se verificó localmente) y
# cualquier regresión de contraste/etiquetado aborta el PR.
DEFAULT_MIN_SCORES = {
    "accessibility": 100,
    "seo": 100,
    "best-practices": 100,
}


def check(report_path: Path, min_scores: dict[str, int]) -> list[str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    categories = report.get("categories", {})
    errors = []
    for name, minimum in min_scores.items():
        category = categories.get(name)
        if category is None:
            errors.append(f"Lighthouse no reportó la categoría '{name}'")
            continue
        score = round((category.get("score") or 0) * 100)
        status = "ok" if score >= minimum else "FALLA"
        print(f"lighthouse {name}: {score}/100 (mínimo {minimum}) [{status}]")
        if score < minimum:
            failing = [
                audit_id
                for audit_id in category.get("auditRefs", [])
                if (report["audits"].get(audit_id.get("id"), {}).get("score") or 0) < 1
                and report["audits"][audit_id["id"]].get("scoreDisplayMode")
                not in {"notApplicable", "informative", "manual"}
            ]
            errors.append(
                f"{name} bajo el mínimo ({score} < {minimum}); audits: {', '.join(failing) or 'n/d'}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Ruta al JSON de Lighthouse")
    parser.add_argument(
        "--min-accessibility", type=int, default=DEFAULT_MIN_SCORES["accessibility"]
    )
    parser.add_argument("--min-seo", type=int, default=DEFAULT_MIN_SCORES["seo"])
    parser.add_argument(
        "--min-best-practices", type=int, default=DEFAULT_MIN_SCORES["best-practices"]
    )
    args = parser.parse_args(argv)

    errors = check(
        Path(args.report),
        {
            "accessibility": args.min_accessibility,
            "seo": args.min_seo,
            "best-practices": args.min_best_practices,
        },
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("check_lighthouse: umbrales OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
