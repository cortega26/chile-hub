#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/066-taxonomia-drift-esperado-vs-real.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- build + verify (la taxonomia debe pasar los gates) --"
make build >/dev/null
make verify >/dev/null

echo "-- drifted_count 8 -> 2, warn_count 7 -> 2, overall sigue warn --"
# Nota: el Plan 066 dejo esto en 3/3. Bajo a 2/2 con el Plan 068 (ADR-015),
# que excluyo consumo_electrico_comunal de la contabilidad por fuente muerta
# — mecanismo distinto al de los warnings esperados de ADR-014.
.venv/bin/python -c "
import json
health = json.load(open('data/normalized/hub_health.json'))
assert health['drifted_count'] == 2, health['drifted_count']
assert health['warn_count'] == 2, health['warn_count']
assert health['retired_count'] == 1, health['retired_count']
assert health['dataset_count'] == 19, health['dataset_count']
assert health['overall_status'] == 'warn', health['overall_status']
report = json.load(open('data/normalized/drift_report.json'))
drifted = sorted(e['dataset'] for e in report['datasets'] if e['drift_status'] == 'drifted')
assert drifted == ['consumo_electrico_comunal', 'empresas', 'indicadores'], drifted
retired = sorted(e['dataset'] for e in health['datasets'] if e['retired'])
assert retired == ['consumo_electrico_comunal'], retired
print('drifted:', drifted, '| retired:', retired)
"

echo "-- warnings conserva TODOS los mensajes (nada se filtra) --"
.venv/bin/python -c "
import json
status = json.load(open('data/normalized/dataset_status.json'))
entries = status['datasets'] if isinstance(status, dict) else status
for name, needle in [
    ('pobreza_comunal', 'parcial por diseño'),
    ('partidos_politicos', 'estado_legal poblado'),
    ('indicadores_urbanos_siedu', 'intentionally partial urban coverage'),
]:
    entry = next(e for e in entries if e['dataset'] == name)
    assert any(needle in w for w in entry.get('warnings', [])), (name, entry.get('warnings'))
print('los 3 warnings esperados siguen listados')
"

echo "-- actionable_warning_count <= warning_count en cada entrada --"
.venv/bin/python -c "
import json
health = json.load(open('data/normalized/hub_health.json'))
for entry in health['datasets']:
    assert isinstance(entry['actionable_warning_count'], int), entry
    assert entry['actionable_warning_count'] <= entry['warning_count'], entry
print('contadores coherentes en', len(health['datasets']), 'datasets')
"

echo "-- coverage.expected siempre presente y booleano --"
.venv/bin/python -c "
import json
catalog = json.load(open('data/normalized/dataset_catalog.json'))
for entry in catalog['datasets']:
    coverage = entry['coverage']
    assert isinstance(coverage.get('expected'), bool), entry['dataset']
    if coverage['expected']:
        assert coverage['status'] == 'partial', entry['dataset']
print('coverage.expected OK en', len(catalog['datasets']), 'datasets')
"

echo "-- ningun enum gano valores --"
test "$(grep -c '\"healthy\", \"drifted\"' scripts/verify_pipeline.py)" -ge 4
.venv/bin/python -c "
from src.builders._shared import VALID_SOURCE_MODES
assert VALID_SOURCE_MODES == {'live', 'fallback', 'monthly'}, VALID_SOURCE_MODES
print('source_mode enum intacto')
"

echo "-- fuente unica de NON_FALLBACK_SOURCE_MODES --"
.venv/bin/python -c "
from src.builders._shared import NON_FALLBACK_SOURCE_MODES
from scripts.verify_pipeline import NON_FALLBACK_SOURCE_MODES as gate
assert NON_FALLBACK_SOURCE_MODES is gate
print('build y gate comparten la definicion')
"

echo "-- ADR-014 existe --"
test -f docs/adr/ADR-014-taxonomia-drift-esperado-vs-real.md

echo "-- pytest focal --"
.venv/bin/pytest tests/test_pipeline_logic.py tests/test_verify_pipeline.py tests/test_validation.py -q

echo "-- landing --"
.venv/bin/python scripts/check_landing_sync.py
make verify-landing >/dev/null

# Deja el arbol limpio: el build de arriba reescribe artefactos derivados.
# No se revierte app.js: en este plan contiene cambios escritos a mano
# (badge de atencion y pildora de cobertura esperada), no ruido de build.
git checkout -- data/normalized/ README.md index.html 2>/dev/null || true

echo "-- lint, format-check, doctor --"
make lint
make format-check
make sync-docs >/dev/null
make doctor

echo "Plan 066: OK"
