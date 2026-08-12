# Plan 076: RES incremental — descargar solo el año en curso

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/extractors/res_extractor.py tests/test_extractors.py .github/workflows/pipeline-check.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`res_extractor.py` re-descarga y re-parsea el histórico completo (2013→actual,
~14 archivos, consolidado 228 MB / ~1.57M filas) **cada día**, incluso con
cache-hit de CI (el workflow lo corre siempre en schedule). El dato que
cambia es solo el año en curso. bcentral ya tiene el patrón incremental
(descarga solo el año en curso cuando existe staging); RES no — cada corrida
diaria gasta ~2-5 min del job (timeout 30 min) y ~200-350 MB de tráfico.

## Current state

- `src/extractors/res_extractor.py:134-141` — descarga todos los CSVs
  anuales; `:156-185` re-parsea todo con `df.unique()` y `sort` sobre ~1.57M
  filas.
- `bcentral_extractor.py:241-246` — el patrón incremental a replicar:
  `years_to_fetch = [current_year] if existing_df is not None else range(HISTORY_START_YEAR, current_year+1)`.
- `src/extractors/res_extractor.py` — la dedup `unique(keep="last")` protege
  contra solapamiento entre archivos anuales (salvaguarda a conservar).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_extractors.py -q -k "Res"` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope**: `src/extractors/res_extractor.py`, `tests/test_extractors.py`
**Out of scope**: el workflow (no cambia la cadencia), el formato del
consolidado (contrato intacto).

## Steps

### Step 1: Detecta el rango ya presente

Replica el patrón de `load_existing_staging` de bcentral: si
`data/staging/empresas.csv` existe, deriva el rango de años presentes (o
guarda el rango en `empresas.metadata.json`); si no, descarga el histórico
completo. Descarga solo `current_year` (+1 año de solapamiento si el archivo
anual del año anterior se publica con retraso).

**Verify**: test con staging sintético (años 2013-2025) → el fetch solo pide el año actual.

### Step 2: Merge incremental conservando la dedup

Concatena el staging previo con el nuevo año y aplica
`unique(subset=..., keep="last")` — la misma dedup de hoy, ahora solo sobre
el merge, no sobre la re-descarga completa. Preserva el `sort` final.

**Verify**: con staging sintético de años previos + fetch del año actual, el
resultado tiene las filas previas + las nuevas, sin duplicados.

### Step 3: Tests de regresión

En `tests/test_extractors.py` (clase `ResExtractorTests`), agrega:
- `test_incremental_only_fetches_current_year` — staging previo presente.
- `test_incremental_preserves_history` — filas de años previos intactas.
- `test_incremental_dedup_overlap` — solapamiento anual deduplicado.
- `test_full_fetch_when_no_staging` — sin staging, descarga completa.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "Res"` → all pass.

## Done criteria

- [ ] Con staging previo, solo se descarga el año en curso
- [ ] Historial previo preservado y deduplicado
- [ ] 4 tests nuevos pasan
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El merge incremental pierde filas de años previos (comparar contra el
  consolidado actual antes del cambio).
- La fuente cambia el formato de los archivos anuales (drift).

## Maintenance notes

- Si la fuente publica el año anterior con retraso (revisar), el +1 de
  solapamiento lo cubre — documentar el hallazgo en el código.
- El ahorro diario esperado: ~2-5 min del job de CI y ~250 MB de tráfico.
