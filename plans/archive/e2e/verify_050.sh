#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/050-resolve-comunas-name-to-cut.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- src/chile_hub/text.py existe --"
test -f src/chile_hub/text.py

echo "-- resolve_comunas devuelve DataFrame con 5 columnas, codigo_comuna pl.String --"
.venv/bin/python -c "
from src.chile_hub import ChileHub
import polars as pl
h = ChileHub()
r = h.resolve_comunas(['Ñuñoa', 'No Existe'])
assert set(r.columns) == {'input', 'codigo_comuna', 'nombre_comuna', 'codigo_region', 'matched'}
assert r.schema['codigo_comuna'] == pl.String
row_nunoa = r.to_dicts()[0]
assert row_nunoa['matched'] is True and len(row_nunoa['codigo_comuna']) == 5
row_no_existe = r.to_dicts()[1]
assert row_no_existe['matched'] is False and row_no_existe['codigo_comuna'] is None
print('resolve_comunas OK')
"

echo "-- CLI resolve --"
.venv/bin/python -m src.chile_hub resolve Ñuñoa

echo "-- pytest tests/test_core.py tests/test_pipeline_logic.py --"
.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py -v

echo "-- ADR-009 con seccion 'Preguntas abiertas' --"
test "$(grep -c "Preguntas abiertas" docs/adr/ADR-009-resolutor-nombres-comunales.md)" -ge 1

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- make doctor --"
make doctor

echo "Plan 050: OK"
