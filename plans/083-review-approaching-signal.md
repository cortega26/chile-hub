# Plan 083: Señal proactiva de review_by inminente (cadencia gestionada)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/builders/reports.py scripts/verify_pipeline.py tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S-M
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

Cuatro `review_by` vencen en 5-10 semanas (hoy 2026-08-12):
`perfil_territorial_comunal` 2026-09-18, `delincuencia_comunal` 2026-09-21,
`autoridades_locales` 2026-10-05, `geometria_comunal` 2026-10-21. El sistema
solo marca "⚠ ESTANCADO (revisión vencida)" cuando la fecha ya pasó
(`reports.py:548-561`) — no hay señal de aproximación. Un estado
`review_approaching` (< 30 días) en `source_readiness.json`/reporte de salud
convierte el sistema de carriles documentado en una cadencia gestionada en
vez de deuda silenciosa.

## Current state

- `data/source_registry.json` — 4 fechas `review_by` inminentes.
- `src/builders/reports.py:548-561` — solo marca vencidas, no próximas.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build | `make build` | exit 0 |
| Tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q` | all pass |

## Scope

**In scope**: `src/builders/reports.py`, `scripts/verify_pipeline.py` (si el
gate lo consume), tests.
**Out of scope**: las decisiones de carril por dataset (juicio del
mantenedor) — la señal solo las agenda.

## Steps

### Step 1: Estado review_approaching

En el builder de readiness/salud, computa `days_until_review_by` y emite
`review_status: upcoming` (< 30 días), `due` (< 0), `ok` (else) — sin tocar
el enum de severidad existente (agregar campo, no ampliar enums).

**Verify**: test con registry sintético (fechas a 10/40 días) → estado
correcto.

### Step 2: Superficie en el reporte de salud

Expón `review_approaching_count` en `hub_health.json` y el detalle por
dataset en `source_readiness.md`. Sin cambiar el `overall_status`.

**Verify**: `make build` → `hub_health.json` tiene el campo nuevo con el
conteo real (4 hoy).

### Step 3: Tests + gates

Agrega gate `review_approaching_count` entero `>= 0` en `verify_pipeline.py`
(si hay patrón de gates para hub_health) y tests.

**Verify**: suite focal verde; `make doctor` exit 0.

## Done criteria

- [ ] `review_status` por dataset en readiness (upcoming/due/ok)
- [ ] `review_approaching_count` en hub_health.json
- [ ] Tests nuevos pasan
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- Un cambio en `overall_status` altera el badge de la landing (no debe —
  el campo es aditivo).
- El registry no tiene `review_by` para algún candidate (drift de schema).

## Maintenance notes

- Esta señal agenda las 4 decisiones de carril; el mantenedor decide cada
  una (promover/deprecar), no el código.
- Cuando venzan, la señal pasa a `due` y el estado "ESTANCADO" existente
  sigue funcionando como hoy.
