"""Genera freshness_badge.json para el badge de shields.io desde hub_health.json.

El archivo generado se sirve vía GitHub Pages y alimenta un badge dinámico
de frescura de datos en el README.

Uso: python scripts/generate_freshness_badge.py
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
HEALTH_PATH = ROOT_DIR / "data" / "normalized" / "hub_health.json"
BADGE_PATH = ROOT_DIR / "data" / "normalized" / "freshness_badge.json"


def build_badge(health: dict) -> dict:
    """Construye el payload JSON para el endpoint de shields.io."""
    overall = health.get("overall_status", "unknown")
    stale = health.get("stale_count", 0)
    warn = health.get("warn_count", 0)
    error = health.get("error_count", 0)

    if overall == "ok" and stale == 0 and error == 0:
        message = "fresh"
        color = "green"
    elif error > 0:
        message = "error"
        color = "red"
    elif stale > 0 or warn > 0:
        message = f"{stale} stale" if stale else "stale"
        color = "orange"
    else:
        message = overall
        color = "lightgrey"

    return {
        "schemaVersion": 1,
        "label": "data",
        "message": message,
        "color": color,
        "isError": overall == "error",
        "namedLogo": "github",
        "cacheSeconds": 3600,
    }


def main() -> None:
    if not HEALTH_PATH.exists():
        print(f"ERROR: {HEALTH_PATH} no encontrado. Ejecuta 'make build' primero.")
        sys.exit(1)

    health = json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    badge = build_badge(health)
    BADGE_PATH.write_text(json.dumps(badge, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Badge de frescura generado: {BADGE_PATH} → {badge['message']} ({badge['color']})")


if __name__ == "__main__":
    main()
