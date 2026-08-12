# Plan 078: Paralelizar CEAD y geometría (scrapes secuenciales)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/extractors/cead_delincuencia_live_extractor.py src/extractors/geometria_comunal_extractor.py tests/test_extractors.py`
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

Dos scrapes secuenciales con riesgo de timeout:
1. **CEAD** (`cead_delincuencia_live_extractor.py:388-404`): 346 POSTs
   secuenciales, uno por comuna, con rate-limit `sleep(max(elapsed*2, 0.5))`
   y `timeout=120` por request; el job `scrape-cead` tiene `timeout-minutes:
   45` (`monthly-scrape.yml:106`). Con degradación (~6-7s por comuna) el job
   muere y el mes queda sin dato.
2. **Geometría** (`geometria_comunal_extractor.py:166-192`): fallback
   por-comuna secuencial (timeout 90 por request) bajo `timeout-minutes: 20`
   del workflow bajo demanda.

El repo ya tiene precedente: `autoridades_locales_extractor.py:506-529`
(`ThreadPoolExecutor`). No hay dependencia entre comunas en ninguno.

## Current state

- `cead_delincuencia_live_extractor.py:388-404` — loop secuencial con
  `_fetch_comuna_data` (`:236-241`) y sleeps de rate-limit.
- `geometria_comunal_extractor.py:166-192` — `_fetch_region_comuna_codes` +
  un request por comuna (`_fetch_comuna`, `:129-144`).
- Precedente: `autoridades_locales_extractor.py:506-529`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_extractors.py -q -k "Cead\|Geometria"` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope**: ambos extractores + tests.
**Out of scope**: el rate-limit del endpoint (respetarlo), el formato de
salida (contrato intacto), el workflow.

## Steps

### Step 1: CEAD con workers acotados

Extrae el cuerpo del loop a una función por comuna y despacha con
`ThreadPoolExecutor(max_workers=4)`, acumulando el sleep de cortesía global
entre tandas (preservando el rate-limit agregado, no por comuna). Mantén
`continue-on-error` y el conteo de fallos.

**Verify**: test con `_fetch_comuna_data` mockeado → los 346 se invocan con
≤4 concurrentes; el tiempo total se reduce.

### Step 2: Geometría con workers acotados

Mismo patrón en el fallback por-comuna (`ThreadPoolExecutor(max_workers=4)`),
manteniendo el registro de fallos por comuna en las notas.

**Verify**: test con fetch mockeado → el fallback despacha en paralelo.

### Step 3: Tests

En `tests/test_extractors.py`, agrega tests que verifiquen el despacho
paralelo (workers ≤ N concurrentes, todos los códigos procesados, fallos
registrados). Modelar sobre los tests de `autoridades_locales_extractor`.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "Cead\|Geometria"` → all pass.

## Done criteria

- [ ] CEAD despacha ≤4 workers concurrentes
- [ ] Geometría (fallback) despacha ≤4 workers
- [ ] Rate-limit agregado preservado
- [ ] Tests nuevos pasan
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El endpoint rechaza con 403/429 el paralelismo moderado (probar con 2
  workers si 4 falla — el rate-limit es deliberado).
- El orden de escritura del consolidado cambia (si algún consumidor depende
  del orden de comunas).

## Maintenance notes

- Si CEAD sigue siendo lento con 4 workers, subir a 6 tras validación —
  documentar la decisión en el código.
- El riesgo de timeout del job mensual queda mitigado pero no eliminado;
  monitorizar la duración real en el próximo `monthly-scrape`.
