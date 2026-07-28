#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/057-loading-skeletons-and-interaction-polish.md
#
# NOTA: el plan se escribio contra un app.js/index.html hipotetico (spinner
# inyectado por JS, filteredCount, tarjetas con atributo data-dataset). El
# codigo real usa placeholders ESTATICOS en index.html (mas simple, sin
# carrera con el fetch) y ya tenia el handler de Escape implementado. Los
# criterios de abajo se adaptaron para verificar la implementacion real
# (ver plans/README.md fila de Plan 057 para el detalle de la desviacion).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- skeleton-pulse / skeleton-shimmer en index.html --"
test "$(grep -c "skeleton-pulse" index.html)" -ge 1
test "$(grep -c "skeleton-shimmer" index.html)" -ge 1

echo "-- skeleton-card (placeholder estatico en index.html) --"
test "$(grep -c "skeleton-card" index.html)" -ge 2

echo "-- no-results-message en app.js --"
test "$(grep -c "no-results-message" app.js)" -ge 1

echo "-- tarjeta clickeable (delegado sobre .dataset-card) en app.js --"
test "$(grep -c 'closest(".dataset-card")' app.js)" -ge 1

echo "-- Escape en app.js (ya existia antes de este plan) --"
test "$(grep -c "Escape" app.js)" -ge 1

echo "-- cursor: pointer en index.html --"
test "$(grep -c "cursor: pointer" index.html)" -ge 1

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- make doctor --"
make doctor

echo "-- make verify-landing --"
make verify-landing >/dev/null

echo "Plan 057: OK"
