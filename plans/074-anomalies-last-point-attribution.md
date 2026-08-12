# Plan 074: Anomalías temporales sobre el punto más reciente (IPC negativo)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/validation.py tests/test_validation.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`detect_series_anomalies` construye log-retornos saltando pares donde
`prev_value <= 0 or curr_value <= 0`, pero `last_return = log_returns[-1]`
es el último par **admitido**, no necesariamente el más reciente; luego
`prev_value = values[-2]` y `dates[-1]` sí son los últimos. Para el IPC
mensual chileno los valores negativos son frecuentes (el propio staging tiene
`2025-12-01 = -0.2`): cuando el mes más reciente es negativo, la señal se
calcula sobre un par viejo pero se reporta con la fecha y el rango del mes
nuevo — la anomalía queda mal atribuida. Es justamente el guard del valor
scrapeado del INE (Plan 069), que queda debilitado.

## Current state

- `src/validation.py:356-380` — construcción de log-retornos con filtro
  `prev_value <= 0 or curr_value <= 0` y `last_return = log_returns[-1]`.
- Tests: `tests/test_validation.py` — casos de `detect_series_anomalies`
  (ruido estable, serie corta, tendencia gradual) del Plan 054.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_validation.py -q -k "anomal"` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope**: `src/validation.py`, `tests/test_validation.py`
**Out of scope**: el override INE (069), el umbral `z_threshold` (calibrado).

## Steps

### Step 1: Corrige la atribución del último punto

En `detect_series_anomalies`, evalúa explícitamente el **último punto
cronológico**: si el par más reciente no entró en los log-retornos (por valor
≤ 0), usa un detector de nivel alternativo (p. ej. z-score sobre los últimos
N valores, o comparación del último cambio absoluto contra la desviación
histórica) en vez de reportar con fecha del último punto un par viejo.
Asegura que `dates`/`esperado_rango` correspondan al punto evaluado.

**Verify**: test nuevo con serie terminando en valor negativo (p. ej.
`[0.3, 0.5, -0.2]`) reporta la anomalía —si la hay— con la fecha correcta.

### Step 2: Tests de regresión

En `tests/test_validation.py`, agrega:
- `test_anomaly_last_point_negative_value` — serie con último valor negativo;
  la anomalía (si la hay) se atribuye a la fecha correcta.
- `test_anomaly_negative_values_no_crash` — serie con varios negativos; no
  crashea y no reporta falsos positivos.

**Verify**: `./.venv/bin/pytest tests/test_validation.py -q -k "anomal"` → all pass.

## Done criteria

- [ ] El último punto negativo se evalúa con la fecha correcta
- [ ] 2 tests nuevos pasan
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El detector de nivel alternativo cambia el set de anomalías reportadas en
  los 506 registros reales de calibración (verificar contra el fixture).

## Maintenance notes

- Si el umbral cambia en el futuro, re-calibrar con el fixture de 506
  registros reales (patrón del Plan 054).
