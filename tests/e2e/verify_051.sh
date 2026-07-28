#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/051-static-http-access-and-dcat-catalog.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- ADR-010 con Decision/Consecuencias/Preguntas abiertas/follow-up --"
test -f docs/adr/ADR-010-acceso-http-estatico-y-dcat.md
test "$(grep -c "follow-up\|Follow-up\|Consecuencias" docs/adr/ADR-010-acceso-http-estatico-y-dcat.md)" -ge 1
test "$(grep -c "Preguntas abiertas" docs/adr/ADR-010-acceso-http-estatico-y-dcat.md)" -ge 1

echo "-- from_datapackage(url) ya no lanza FileNotFoundError; path local intacto --"
.venv/bin/pytest tests/test_core.py -v -k datapackage

echo "-- make build genera data.json con dataset[] y downloadURL absolutas --"
make build >/dev/null
.venv/bin/python -c "
import json
d = json.load(open('data/normalized/data.json'))
assert d.get('dataset'), 'sin datasets'
u = d['dataset'][0]['distribution'][0]['downloadURL']
assert u.startswith('https://'), u
print('datasets:', len(d['dataset']), 'ejemplo:', u)
"
# make build regenera timestamps/artefactos vivos fuera del scope de este plan
# (comparten repo con data/normalized/data.json, que SI es el deliverable). Revierte
# ese ruido para dejar el working tree igual a como estaba antes de este script.
git checkout -- data/normalized/ README.md index.html 2>/dev/null || true

echo "-- docs/http-access.md existe y mkdocs build pasa --"
test -f docs/http-access.md
.venv/bin/mkdocs build >/dev/null

echo "-- pytest tests/test_core.py tests/test_pipeline_logic.py tests/test_data_package.py --"
.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py tests/test_data_package.py -v

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- make doctor --"
make doctor

echo "Plan 051: OK"
