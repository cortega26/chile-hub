# Plan 084: Promover perfil_territorial_comunal al bundle estable

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- data/source_registry.json data/dataset_catalog_config.json docs/datasets/perfil_territorial_comunal.md contracts/datasets/perfil_territorial_comunal.schema.json src/build_dev_db.py tests/test_chile_hub.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3 (decisión de producto del mantenedor)
- **Effort**: S-M
- **Risk**: MED
- **Depends on**: 070/071 (coherencia del catálogo al promover)
- **Category**: direction
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`perfil_territorial_comunal` es la capa derivada que consolida 9 datasets por
`codigo_comuna` — "Chile en una tabla", la promesa literal de AGENTS.md §1.
Hoy es candidate invisible (cobertura 346/346, `validation_status: ok` en el
catálogo), con `review_by 2026-09-18` que fuerza la decisión pronto. El
mecanismo de derivación (`build_dev_db.py:495-536`) hace barato mantenerla.
Promoverla ataca la adopción — la señal que §10 exige antes de agregar
datasets — sin agregar fuentes nuevas.

## Current state

- `data/source_registry.json` — `perfil_territorial_comunal`:
  `publication_track: candidate`, `review_by: 2026-09-18`.
- `src/build_dev_db.py:465,637` — construye y valida la capa (346/346, ok).
- `docs/datasets/perfil_territorial_comunal.md` — documenta el uso como tabla
  única; no tiene header "Carril:" (ver Plan 081).
- `freshness_policy: derivada` — ya presente (mitiga el riesgo de bugs de
  agregación como datos "oficiales").

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build | `make build` | exit 0 |
| Tests | `./.venv/bin/pytest tests/test_chile_hub.py tests/test_pipeline_logic.py -q` | all pass |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**: `data/source_registry.json`, `data/dataset_catalog_config.json`
(si el catálogo distingue carriles), docs, tests de contrato.
**Out of scope**: agregar datasets nuevos; promover otras candidate.

## Steps

### Step 1: Flip de carril

Cambia `publication_track` a `stable_publishable` en el registry y verifica
que el build lo incluye en el bundle (parquet en el ZIP, catálogo consistente
— el Plan 071 debe estar antes o coordinarse).

**Verify**: `make build` → `perfil_territorial_comunal.parquet` en el bundle;
`verify_pipeline.py --profile publication` exit 0.

### Step 2: Docs y contrato

Actualiza `docs/datasets/perfil_territorial_comunal.md` (header Carril:
stable, nota de derivación), el badge de capas (17→18) y cualquier test que
fije el conteo (`EXPECTED_DATASET_COUNT` o similar).

**Verify**: `make sync-docs` regenera los bloques; suite verde.

### Step 3: Contrato de artefactos

Actualiza `ArtifactContractTests` y `EXPECTED_DATASET_COUNT` si existen; el
nuevo parquet debe pasar todos los contratos (ya validado en el build hoy).

**Verify**: `./.venv/bin/pytest tests/test_chile_hub.py -q` → all pass.

## Done criteria

- [ ] `perfil_territorial_comunal` en el bundle estable (18 capas)
- [ ] Parquet en el ZIP y catálogo consistente
- [ ] Docs y conteos actualizados
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El build rechaza la capa al promover (algún gate espera candidate).
- El conteo público "17 capas" del hero/landing requiere decisión de copy
  (el plan no cambia el hero sin instrucción).

## Maintenance notes

- Decisión de producto: el mantenedor la ratifica (es la que agenda el
  review_by 2026-09-18 de todos modos).
- Si se promueve, la sección candidate de la landing (Plan 082) pierde una
  entrada — coordinar.
