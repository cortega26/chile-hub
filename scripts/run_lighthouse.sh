#!/usr/bin/env bash
# Corre Lighthouse contra la landing local y verifica umbrales (a11y/SEO/best
# practices). Lo usan `make lighthouse` y el job `landing` de pipeline-check.
#
# Resuelve CHROME_PATH priorizando el Chromium de Playwright (lo que instala
# `make bootstrap`); si no existe, deja que Lighthouse busque Chrome del sistema.
set -euo pipefail

PORT="${LIGHTHOUSE_PORT:-8765}"
REPORT="${LIGHTHOUSE_REPORT:-/tmp/chile-hub-lighthouse.json}"
PYTHON_BIN="${PYTHON:-python3}"

chrome_path="$(ls "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1 || true)"
if [ -n "$chrome_path" ]; then
  export CHROME_PATH="$chrome_path"
elif command -v google-chrome >/dev/null 2>&1; then
  export CHROME_PATH="$(command -v google-chrome)"
fi

"$PYTHON_BIN" -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 1

npx --yes lighthouse@12.8.2 "http://127.0.0.1:$PORT/" --quiet \
  --chrome-flags="--headless=new --no-sandbox --disable-gpu" \
  --output=json --output-path="$REPORT" \
  --only-categories=accessibility,seo,best-practices

"$PYTHON_BIN" scripts/check_lighthouse.py "$REPORT"
