# Plan 082: Mostrar el carril candidate en la landing

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- index.html app.js src/builders/reports.py src/builders/landing.py tests/test_chile_hub.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: 070, 071 (que el catálogo distinga carriles limpiamente)
- **Category**: direction
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`hub_bundle.json` produce `candidate_datasets` con `maturity_status` y
`next_action` que ninguna UI consume; `app.js:844` renderiza solo las 17
estables. `perfil_territorial_comunal` — capa derivada con cobertura 346/346,
`validation_status: ok`, 9 datasets consolidados (la promesa literal de "una
línea de código") — es invisible en la superficie principal. El sistema de
carriles (un diferenciador real del producto) queda sin expresión visual y
los analistas no pueden evaluar datos candidate.

## Current state

- `app.js:844` — renderiza `bundle.datasets` (17 estables).
- `src/builders/reports.py` — produce `candidate_datasets` en el bundle.
- `index.html` — hero/Capacidades no mencionan el concepto de carril.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build | `make build` | exit 0 |
| Landing verify | `make verify-landing` | exit 0 |
| Tests | `./.venv/bin/pytest tests/test_chile_hub.py -q` | all pass |

## Scope

**In scope**: `index.html`, `app.js`, tests de landing.
**Out of scope**: la decisión de promover candidate (DIR-03), el conteo
público "17 capas" en el hero (no cambiar sin decisión de producto).

## Steps

### Step 1: Render de la sección candidate

En `app.js`, renderiza una sección "En evaluación (candidate)" después del
catálogo estable, leyendo `bundle.candidate_datasets`, con badge explícito
"candidate" + `maturity_status` + `next_action`. Sin contar en el total del
catálogo estable.

**Verify**: con el bundle real, la sección candidate aparece con perfil y
consumo; el catálogo estable sigue mostrando 17.

### Step 2: Estilos + verificación

Agrega estilos coherentes con la paleta existente (`.candidate-*`). Asegura
que `make verify-landing` siga pasando (los textos verificados del catálogo
estable intactos).

**Verify**: `make verify-landing` exit 0; Playwright muestra la sección.

### Step 3: Tests de guardrail

En `tests/test_ci_config.py` (o el patrón de landing guardrails), test que
`app.js` renderiza `candidate_datasets` y que el catálogo estable no se
contamina.

**Verify**: suite focal verde.

## Done criteria

- [ ] Sección candidate visible con badge y `next_action`
- [ ] Catálogo estable intacto (17, textos verificados)
- [ ] `make verify-landing` exit 0
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- La landing rompe `verify_landing.py` (textos byte-checked) — verificar con
  el smoke test real antes de tocar selectores existentes.
- El hero "17 capas" cambia de sentido sin decisión de producto.

## Maintenance notes

- Esta sección hace visible el sistema de carriles — el copy debe ser
  honesto: "evaluados, no en el bundle público" (AGENTS.md §1).
- Coordinar con DIR-03: si perfil se promueve, sale de esta sección.
