#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/054-temporal-anomaly-validation-numeric-series.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- detect_series_anomalies detecta un salto 10x inyectado --"
.venv/bin/python -c "
import polars as pl
from src.validation import detect_series_anomalies
df = pl.DataFrame({
    'codigo_indicador': ['uf'] * 6,
    'fecha': ['2026-01-0' + str(i) for i in range(1, 7)],
    'valor': [100.0, 100.1, 100.2, 100.1, 100.3, 1000.0],
})
a = detect_series_anomalies(df, z_threshold=4.0, min_history=4)
assert len(a) == 1 and a[0]['codigo_indicador'] == 'uf', a
print('anomalia detectada:', a[0]['motivo'])
"

echo "-- validate_indicadores: anomalia va a warnings, nunca a errors --"
.venv/bin/python -c "
import polars as pl
from src.validation import validate_indicadores
rows = []
for code in ['dolar', 'euro', 'utm', 'ipc']:
    for i in range(1, 7):
        rows.append({'codigo_indicador': code, 'fecha': f'2026-01-0{i}', 'valor': 100.0})
for i, v in enumerate([100.0, 100.1, 100.2, 100.1, 100.3, 1000.0], start=1):
    rows.append({'codigo_indicador': 'uf', 'fecha': f'2026-01-0{i}', 'valor': v})
r = validate_indicadores(pl.DataFrame(rows), None)
assert r['status'] != 'error', r
assert any('anomal' in w.lower() for w in r['warnings']), r['warnings']
print('status:', r['status'], '| warnings con anomalia OK')
"

echo "-- frontera dura: ninguna anomalia llega a errors.append --"
test "$(grep -c 'errors.append.*anomal' src/validation.py)" = "0"

echo "-- ADR-013 existe --"
test -f docs/adr/ADR-013-validacion-de-anomalias-temporales.md

echo "-- check_validation_registration.py --"
.venv/bin/python scripts/check_validation_registration.py

echo "-- pytest tests/test_validation.py tests/test_verify_pipeline.py --"
.venv/bin/pytest tests/test_validation.py tests/test_verify_pipeline.py -v

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- make build && make doctor (gate en modo dev, no aborta el build) --"
make build >/dev/null
.venv/bin/python scripts/verify_pipeline.py
git checkout -- data/normalized/ README.md index.html 2>/dev/null || true
make sync-docs >/dev/null
make doctor

echo "Plan 054: OK"
