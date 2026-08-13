#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/063-historial-salud-hub.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- make build (x2) + hub_health_history.jsonl no duplica por timestamp --"
make build >/dev/null
make build >/dev/null
LINES_AFTER="$(wc -l < data/normalized/hub_health_history.jsonl)"
echo "lineas: $LINES_AFTER"
test "$LINES_AFTER" -ge 1

echo "-- el archivo aparece en artifact_manifest.json --"
.venv/bin/python -c "
import json
m = json.load(open('data/normalized/artifact_manifest.json'))
assert any(a['path'].endswith('hub_health_history.jsonl') for a in m['artifacts'])
print('en manifiesto')
"

echo "-- make verify --"
make verify >/dev/null
echo "make verify OK"

# NOTA: a diferencia de otros verify_NNN.sh de esta cola, este script NO hace
# `git checkout -- index.html` — index.html tiene cambios de codigo a mano
# (el markup/CSS del sparkline de Step 4), no solo ruido de build. Revertirlo
# a ciegas aqui borro esos cambios una vez durante el desarrollo (recuperados
# manualmente). Solo se revierte data/normalized/ (100% generado) y README.md
# (solo el badge/conteo mecanico de sync_docs), nunca index.html.
git checkout -- data/normalized/ README.md 2>/dev/null || true
make sync-docs >/dev/null

echo "-- pytest tests/test_pipeline_logic.py --"
.venv/bin/pytest tests/test_pipeline_logic.py -v -k "HubHealthHistory"

echo "-- make verify-landing (sin tocar scripts/verify_landing.py) --"
make verify-landing >/dev/null
echo "verify-landing OK"

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- make doctor --"
make doctor

echo "Plan 063: OK"
