"""Genera adoption.json y adoption_badge.json con señales públicas de adopción:
descargas PyPI (pypistats.org) y descargas de assets en GitHub Releases.

Restricción ética dura: la señal se lee exclusivamente desde APIs públicas de
plataforma, en CI. Este script NUNCA corre en la máquina del usuario ni se
empaqueta con la librería instalada — cero telemetría en el artefacto
distribuido.

Cada fuente degrada con gracia: si PyPI o GitHub fallan (red, rate-limit, 404
porque el paquete aún no tiene descargas), el script no aborta — usa None/0
para esa fuente y sigue. La señal es informativa, no un gate.

Uso:
  python scripts/fetch_adoption_stats.py                             # modo online
  python scripts/fetch_adoption_stats.py --offline PATH_A_FIXTURE.json  # modo offline
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ADOPTION_PATH = ROOT_DIR / "data" / "normalized" / "adoption.json"
BADGE_PATH = ROOT_DIR / "data" / "normalized" / "adoption_badge.json"

PYPI_STATS_URL = "https://pypistats.org/api/packages/chile-hub/recent"
GITHUB_RELEASES_URL = "https://api.github.com/repos/cortega26/chile-hub/releases"
REQUEST_TIMEOUT_SECONDS = 10


def _http_get_json(url: str, headers: dict | None = None) -> dict | list | None:
    """Hace GET a `url` y parsea el JSON de respuesta.

    Degrada con gracia: cualquier error de red, HTTP o de parseo devuelve
    `None` en vez de propagar la excepción (invariante de este script: una
    fuente caída no debe abortar la corrida).
    """
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"WARN: fallo al leer {url}: {exc}", file=sys.stderr)
        return None


def fetch_pypi_recent() -> dict | None:
    """Lee las estadísticas recientes de descargas PyPI (endpoint público, sin auth)."""
    return _http_get_json(PYPI_STATS_URL)


def fetch_github_releases() -> list | None:
    """Lee la lista de releases de GitHub (assets incluidos).

    Usa `GITHUB_TOKEN` del entorno si está presente, sólo para evitar
    rate-limit del endpoint público — no es requisito.
    """
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _http_get_json(GITHUB_RELEASES_URL, headers=headers)


def parse_pypi_stats(pypi_recent: dict | None) -> dict:
    """Extrae last_day/last_week/last_month desde la respuesta cruda de pypistats.org."""
    data = pypi_recent.get("data", {}) if isinstance(pypi_recent, dict) else {}
    return {
        "last_day": data.get("last_day"),
        "last_week": data.get("last_week"),
        "last_month": data.get("last_month"),
    }


def sum_github_downloads(releases: list | None) -> int:
    """Suma `download_count` de todos los assets de todos los releases.

    Degrada a 0 si `releases` es `None` o está vacío.
    """
    if not releases:
        return 0
    total = 0
    for release in releases:
        for asset in release.get("assets", []):
            total += asset.get("download_count", 0)
    return total


def build_payload(pypi_stats: dict, github_total: int) -> dict:
    """Construye el payload JSON completo de adopción (`adoption.json`)."""
    return {
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pypi": pypi_stats,
        "github_releases": {"total_downloads": github_total},
    }


def build_badge(pypi_last_month: int | None) -> dict:
    """Construye el payload JSON para el endpoint de shields.io."""
    return {
        "schemaVersion": 1,
        "label": "instalaciones/mes",
        "message": f"{pypi_last_month}" if pypi_last_month is not None else "n/d",
        "color": "blue",
        "namedLogo": "pypi",
        "cacheSeconds": 86400,
    }


def load_offline_fixture(path: Path) -> tuple[dict | None, list | None]:
    """Lee un fixture con la forma `{"pypi_recent": {...}, "github_releases": [...]}`."""
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return fixture.get("pypi_recent"), fixture.get("github_releases")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        metavar="PATH",
        help=(
            "Lee un fixture JSON en vez de golpear las APIs de PyPI/GitHub "
            "(modo reproducible, sin red, para tests y CI)."
        ),
    )
    args = parser.parse_args()

    if args.offline:
        pypi_recent, github_releases = load_offline_fixture(Path(args.offline))
    else:
        pypi_recent = fetch_pypi_recent()
        github_releases = fetch_github_releases()

    pypi_stats = parse_pypi_stats(pypi_recent)
    github_total = sum_github_downloads(github_releases)

    payload = build_payload(pypi_stats, github_total)
    badge = build_badge(pypi_stats["last_month"])

    ADOPTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    ADOPTION_PATH.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    BADGE_PATH.write_text(json.dumps(badge, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Señal de adopción generada: {ADOPTION_PATH} y {BADGE_PATH} "
        f"→ {badge['message']} instalaciones/mes"
    )


if __name__ == "__main__":
    main()
