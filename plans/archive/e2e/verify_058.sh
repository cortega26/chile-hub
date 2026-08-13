#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/058-catalogo-campo-extractor-y-tabla-readme.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- 22/22 entradas con campo extractor --"
python3 -c "import json; d=json.load(open('data/dataset_catalog_config.json')); assert all('extractor' in v for v in d.values())"

echo "-- check_companion_paths.py registry --"
.venv/bin/python scripts/check_companion_paths.py registry

echo "-- make doctor --"
make doctor

echo "-- make sync-docs + sync_docs.py --check --"
make sync-docs
.venv/bin/python scripts/sync_docs.py --check

echo "-- START_EXTRACTOR_TABLE presente exactamente una vez --"
test "$(grep -c "START_EXTRACTOR_TABLE" README.md)" = "1"

echo "-- pytest tests/test_pipeline_logic.py --"
.venv/bin/pytest tests/test_pipeline_logic.py -v

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- AGENTS.md ya no lista la tabla de extractores como pendiente --"
! grep -q "automatizar la tabla de extractores" AGENTS.md

echo "Plan 058: OK"
