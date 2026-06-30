#!/usr/bin/env python3
"""Registra semanalmente las descargas del bundle desde GitHub Releases API.

Señal pasiva de uso real — sin telemetría en la librería, sin PII, sin cookies.
Cero código en ``ChileHub``.

Limitación documentada:
  El contador de GitHub cuenta descargas por asset, no por usuario único.
  El bundle se cachea localmente tras la primera descarga y ``data_dir=``
  local lo evita por completo, por lo que esta métrica **subcuenta** usuarios
  recurrentes. Es una cota inferior del uso real.

Uso:
  python scripts/usage_snapshot.py          # Registra un snapshot hoy
  python scripts/usage_snapshot.py --json   # Ídem, salida JSON a stdout

Los snapshots se acumulan en ``data/normalized/usage_snapshots.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

REPO_OWNER = "cortega26"
REPO_NAME = "chile-hub"
BUNDLE_ASSET_NAME = "chile-hub-publishable-bundle.zip"
RELEASES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases?per_page=100"

# ── Rutas relativas a __file__ ───────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "normalized"
SNAPSHOTS_PATH = DATA_DIR / "usage_snapshots.json"


def _http_get(url: str) -> Any:
    """GET contra una URL HTTP/S. Sin dependencias externas (solo stdlib)."""
    import urllib.request

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        print(f"Error HTTP {exc.code} al consultar {url}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"Error de conexión al consultar {url}: {exc.reason}", file=sys.stderr)
        return None


def fetch_release_stats() -> dict[str, Any]:
    """Consulta la API de GitHub Releases y extrae conteos de descarga.

    Returns:
        Dict con ``total_downloads``, ``release_count``, y ``releases``
        (cada release con ``tag_name``, ``published_at``, ``assets``).
    """
    releases_data = _http_get(RELEASES_URL)
    if releases_data is None:
        raise SystemExit("No se pudo consultar GitHub Releases API. Abortando.")

    total_downloads = 0
    releases = []

    for release in releases_data:
        tag = release.get("tag_name", "unknown")
        published = release.get("published_at", "")
        release_total = 0
        assets_out = []

        for asset in release.get("assets", []):
            asset_name = asset.get("name", "")
            downloads = asset.get("download_count", 0)
            assets_out.append(
                {
                    "name": asset_name,
                    "download_count": downloads,
                }
            )
            if asset_name == BUNDLE_ASSET_NAME:
                release_total += downloads

        total_downloads += release_total
        releases.append(
            {
                "tag_name": tag,
                "published_at": published,
                "release_total_downloads": release_total,
                "assets": assets_out,
            }
        )

    return {
        "total_downloads": total_downloads,
        "release_count": len(releases),
        "releases": releases,
    }


def load_existing_snapshots() -> list[dict[str, Any]]:
    """Carga la serie histórica existente, o retorna lista vacía."""
    if not SNAPSHOTS_PATH.exists():
        return []
    try:
        with open(SNAPSHOTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("snapshots", [])
    except (json.JSONDecodeError, OSError) as exc:
        print(
            f"Advertencia: no se pudo leer {SNAPSHOTS_PATH}: {exc}. Se iniciará una serie nueva.",
            file=sys.stderr,
        )
        return []


def save_snapshots(snapshots: list[dict[str, Any]]) -> None:
    """Persiste la serie histórica de forma atómica."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "description": (
            "Serie histórica semanal de descargas del bundle "
            f"'{BUNDLE_ASSET_NAME}' desde GitHub Releases API. "
            "Señal pasiva — subcuenta usuarios recurrentes (cache local). "
            "Cero telemetría en la librería."
        ),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "asset_name": BUNDLE_ASSET_NAME,
        "snapshots": snapshots,
    }
    tmp_path = SNAPSHOTS_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, SNAPSHOTS_PATH)


def take_snapshot() -> dict[str, Any]:
    """Toma un snapshot hoy y lo agrega a la serie histórica.

    Si ya existe un snapshot para el día actual, lo reemplaza (idempotente).
    """
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    fetched_at = datetime.now(UTC).isoformat()

    stats = fetch_release_stats()

    snapshot = {
        "date": today,
        "fetched_at_utc": fetched_at,
        "total_downloads": stats["total_downloads"],
        "release_count": stats["release_count"],
        "releases": stats["releases"],
    }

    snapshots = load_existing_snapshots()

    # Reemplazar snapshot del mismo día si existe (idempotencia)
    replaced = False
    for i, existing in enumerate(snapshots):
        if existing.get("date") == today:
            snapshots[i] = snapshot
            replaced = True
            break

    if not replaced:
        snapshots.append(snapshot)

    # Mantener orden cronológico
    snapshots.sort(key=lambda s: s["date"])

    save_snapshots(snapshots)

    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Registra descargas del bundle desde GitHub Releases API"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emitir solo el snapshot actual como JSON a stdout",
    )
    args = parser.parse_args()

    snapshot = take_snapshot()

    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    else:
        print(
            f"usage_snapshot {snapshot['date']}: "
            f"{snapshot['total_downloads']} descargas totales del bundle "
            f"({snapshot['release_count']} releases). "
            f"Guardado en {SNAPSHOTS_PATH}"
        )


if __name__ == "__main__":
    main()
