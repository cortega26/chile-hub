"""Verifica que las `official_url` de data/source_registry.json sigan vivas.

Detecta fuentes que se movieron o murieron silenciosamente (el protocolo de
§6 "fuente permanentemente caída" depende de que alguien se dé cuenta). Corre
semanalmente vía `.github/workflows/source-urls.yml` — nunca bloquea publish;
su señal es fallar el workflow semanal para que el mantenedor evalúe.

Clasificación por URL:
  OK    HTTP 2xx/3xx (redirects seguidos).
  WARN  HTTP 4xx — a menudo bloqueo anti-bot o URL movida; se reporta pero no
        falla el job (camara.cl, cead.cl, wikipedia rechazan bots simples).
  DEAD  Error de red/timout, o 5xx persistente tras reintentos — falla el job.

Reusa la convención de `src/extractors/http_utils.py` (requests + retry en
errores transitorios y 5xx; 4xx no se reintenta).
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extractors.http_utils import fetch_with_retry  # noqa: E402

SOURCE_REGISTRY_PATH = "data/source_registry.json"
TIMEOUT_SECONDS = 20
HEADERS = {"User-Agent": "chile-hub source-url-liveness-check (github-actions)"}


def load_urls() -> list[str]:
    import json

    with open(SOURCE_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)
    urls = sorted({str(entry.get("official_url", "")).strip() for entry in registry})
    return [u for u in urls if u and u.startswith("http")]


def check_url(url: str) -> str:
    """Retorna 'OK', 'WARN', o 'DEAD'. NO lanza para URLs muertas."""
    try:
        resp = fetch_with_retry(
            url,
            max_attempts=3,
            timeout=TIMEOUT_SECONDS,
            headers=HEADERS,
        )
        if resp.status_code < 400:
            return "OK"
        if resp.status_code < 500:
            return "WARN"
        return "DEAD"
    except Exception:
        return "DEAD"


def main() -> int:
    urls = load_urls()
    if not urls:
        print("check_source_urls: sin URLs en data/source_registry.json")
        return 1

    dead: list[str] = []
    warned: list[str] = []
    print(f"check_source_urls: {len(urls)} URLs — verificando...\n")
    for url in urls:
        status = check_url(url)
        if status == "DEAD":
            dead.append(url)
        elif status == "WARN":
            warned.append(url)
        print(f"  [{status:4s}] {url}")
        time.sleep(0.5)

    print(
        f"\nResumen: {len(urls) - len(dead) - len(warned)} OK, {len(warned)} WARN, {len(dead)} DEAD"
    )
    if warned:
        print("\nWARN (revisar manualmente — puede ser bloqueo anti-bot):")
        for url in warned:
            print(f"  - {url}")
    if dead:
        print("\nDEAD (evaluar protocolo §6 — fuente caída o movida):")
        for url in dead:
            print(f"  - {url}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
