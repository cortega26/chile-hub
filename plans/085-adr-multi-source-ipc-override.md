# Plan 085: ADR multi-fuente para el override de IPC (estrategia revisable)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- docs/adr/ docs/extraction-lanes.md src/extractors/ine_ipc.py src/extractors/bcentral_extractor.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 069 (delivery visible), 075 (regex robusto)
- **Category**: direction
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

El publish diario de `indicadores` depende de un parseo HTML anclado al
`<h1>` y clases CSS de `ine.gob.cl` (`ine_ipc.py`). La doc del dataset
promete "una estrategia histórica más clara para IPC y UTM frente a snapshots
parciales del agregador" (`docs/datasets/indicadores.md:128`) — no entregada.
AGENTS.md §10 prohíbe scraping HTML frágil como fuente principal; el override
es la excepción de último recurso, validado en producción, pero sin ADR
propio: la cadena multi-fuente (INE HTML → series IPC → backfill) y su escape
hatch no están decididos ni documentados. Un rediseño de `ine.gob.cl` rompe
silenciosamente el carril diario.

## Current state

- `src/extractors/ine_ipc.py:1-13` — docstring con la justificación y el
  patrón validado (citando el proyecto Monedario); sin ADR.
- ADR-016 cubre backfill; no hay ADR de overrides multi-fuente.
- `docs/datasets/indicadores.md:128` — promesa declarada y no entregada.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| ADR count | `grep -c "adr/" README.md` | refleja el nuevo ADR tras `make sync-docs` |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**: `docs/adr/ADR-017-*.md` (nuevo), `docs/extraction-lanes.md`,
`docs/datasets/indicadores.md`.
**Out of scope**: cambiar el código del override (planes 069/075); elegir
fuentes alternativas no disponibles (el ADR documenta el estado y el
escape hatch, no inventa fuentes).

## Steps

### Step 1: Escribe ADR-017

Usa `docs/adr/ADR-016-*.md` como plantilla de formato. Contenido:
- **Contexto**: mindicador.cl no publica IPC desde 2025-12; el INE es la
  fuente autoritativa; el agregador es el punto de falla.
- **Decisión**: cadena multi-fuente con override de último recurso — serie
  histórica del agregador + variación mensual del INE (HTML anclado, patrón
  validado desde 2026-05-16); el override es delivery visible (Plan 069).
- **Estado**: `proposed` — requiere ratificación del mantenedor.
- **Preguntas abiertas**: ¿API de series del INE cuando exista? ¿UTM tiene
  un override análogo (SII)? ¿backfill congelado vs retirar la serie?

**Verify**: `test -f docs/adr/ADR-017-*.md` y contiene "override" + "INE".

### Step 2: Documenta en carriles y dataset

Agrega a `docs/extraction-lanes.md` (regla del carril diario) que
`indicadores` depende del override INE; actualiza
`docs/datasets/indicadores.md:128` para que la promesa referencie el ADR.

**Verify**: `grep -n "ADR-017" docs/extraction-lanes.md docs/datasets/indicadores.md` → referencias presentes.

### Step 3: Sync

**Verify**: `make sync-docs` (el conteo de ADRs del README sube a 17);
`make doctor` exit 0.

## Done criteria

- [ ] ADR-017 existe con contexto/decisión/estado/preguntas abiertas
- [ ] `docs/extraction-lanes.md` menciona el override INE
- [ ] `docs/datasets/indicadores.md:128` referencia el ADR
- [ ] `make doctor` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

- El mantenedor rechaza el enfoque de override (el ADR documenta la
  alternativa de retirar la serie en vez de insistir).

## Maintenance notes

- El ADR hace visible la dependencia frágil y decide el escape hatch
  (degradar al backfill publicado si el INE rediseña y el regex falla).
- Si el INE publica una API de series estable, el ADR es el lugar para
  registrar la migración.
