# Plan 127: Correcciones de documentación canónica (7 desviaciones verificadas)

> **Executor instructions**: Sigue los pasos en orden; cada uno verifica solo.
> Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- AGENTS.md SOURCE_OF_TRUTH.md CLAUDE.md docs/installation.md docs/backlog/NEXT_STEPS.md docs/dataset-compatibility-policy.md docs/case-study-construccion-chile-hub.md docs/backlog/06-api-error-handling.md docs/datasets/partidos_politicos.md docs/datasets/autoridades_electas.md scripts/publish_hf_dataset.py tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (coordina con Plan 124 para las líneas "22 specs" de AGENTS.md: si 124 aterrizó, esas ya están corregidas; no dupliques)
- **Category**: docs
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Ocho hechos documentados son **activamente falsos** a HEAD, en documentos
canónicos (AGENTS.md es la guía obligatoria de agentes; installation.md es la
página de instalación del sitio de docs). Un agente o contribuyente que confíe
en ellos toma decisiones equivocadas o rehace trabajo ya hecho.

## Current state (verificado línea por línea)

1. `AGENTS.md:62` — `perfil_territorial_comunal` figura como "(carril
   `candidate`, `review_by` 2026-09-18)"; el registry dice
   `publication_track: stable_publishable`, `maturity_status: stable`,
   `review_by: 2026-12-31`, `public_bundle_eligible: true`.
2. `AGENTS.md:761` — "replica las **17** capas publicables"; el registry tiene
   **21** `stable_publishable` (README dice 21). El comentario
   `scripts/publish_hf_dataset.py:81` también dice "17 capas publicables
   reales".
3. `AGENTS.md:220-234` (§3) — lista 14 extractores y afirma "(los 17 que corre
   `make extract`)". Faltan `estadisticas_vitales_extractor.py`,
   `permisos_edificacion_extractor.py`, `calidad_aire_extractor.py`
   (`Makefile:120-140` corre 17).
4. `docs/installation.md:55,61` — `pip install chile-hub==1.15.0` y
   `cache update --data-version v1.15.0` con la versión actual en 1.43.1.
5. `docs/backlog/NEXT_STEPS.md:34-35` — "existe un plan
   (`plans/021-mkdocs-api-docs.md`) … Pendiente de priorización"; el plan 021
   está DONE/archivado (`plans/archive/021-...`) y el sitio se construye en
   `pages-deploy.yml:58`.
6. Links a planes movidos: `docs/dataset-compatibility-policy.md:131`
   (`plans/008-...`), `docs/case-study-construccion-chile-hub.md:254`
   (`plans/022-...`), `docs/backlog/06-api-error-handling.md:21`
   (`plans/011-...`), `docs/datasets/partidos_politicos.md:63` y
   `docs/datasets/autoridades_electas.md:88` (`plans/023-...`); todos viven en
   `plans/archive/`.
7. `AGENTS.md:197` (`codegraph search`) no existe en el CLI instalado
   (`codegraph --help` → subcomando `query`; `callers/callees/impact` sí
   existen); `SOURCE_OF_TRUTH.md:120-121` usa `codegraph find` (inexistente) y
   apunta a secciones de `CLAUDE.md` ("Comandos esenciales", "CodeGraph") que
   no existen (CLAUDE.md solo tiene "Orden de lectura" y "Arranque mínimo").

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Gates agentes | `python scripts/check_agents_sync.py --docs AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md` | declared | exit 0 |
| Gates docs | `make doctor` | declared | exit 0 |
| Tests CI | `./.venv/bin/pytest tests/test_ci_config.py -v` | declared | verde |
| Docs build | `make docs-build` | declared | exit 0 |

## Scope

**In scope**: los archivos citados en Current state + `tests/test_ci_config.py`
(guardrail de links) + `scripts/publish_hf_dataset.py` (solo comentario).

**Out of scope**: reescribir prosa más allá de lo citado; ADR-023; docs de
datasets (otro dueño); CHANGELOG.

## Git workflow

- Branch: `advisor/127-docs-corrections-batch`
- Commits por grupo: `docs(agents): ...`, `docs: ...`.
- No push/PR.

## Steps

### Step 0: Baseline

`make doctor` y `python scripts/check_agents_sync.py --docs
AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md` verdes. Si no, STOP.

### Step 1: AGENTS.md (3 correcciones)

- `:62` → quita la anotación de carril/fecha o corrígela:
  `(carril stable_publishable, review_by 2026-12-31)`.
- `:761` → "**21** capas publicables" o redacción sin número:
  "(las capas `stable_publishable` del registry — hoy 21)". Actualiza también
  el comentario de `scripts/publish_hf_dataset.py:81`.
- `:220-234` → agrega las 3 líneas faltantes al bloque de extractores (mantén
  el orden de `Makefile:120-140`) o reemplaza la lista por "17 extractores: ver
  `Makefile` target `extract`" + conteo. Preferible agregar las 3 líneas:
  conserva la utilidad del listado.
- **Verifica** que la línea "los 17 que corre `make extract`" siga siendo
  coherente con la lista (17 entradas). El conteo lo verifica
  `check_agents_sync.py`; corre el gate.

**Verify**: `python scripts/check_agents_sync.py --docs
AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md` → exit 0.

### Step 2: installation.md con versión sincronizada

Opción recomendada (robusta): agrega un bloque delimitado en
`docs/installation.md` y una función de sync mínima:

- Envuelve los dos ejemplos en:
  ```
  <!-- START_INSTALLATION_PIN -->
  ```bash
  pip install chile-hub==X.Y.Z
  ```
  ...
  <!-- END_INSTALLATION_PIN -->
  ```
- En `src/builders/doc_sync.py`, agrega
  `sync_installation_pins()` que lea `read_project_version()` y reemplace
  `chile-hub==<ver>` y `--data-version v<ver>` dentro del bloque (mismo patrón
  que los otros sync). Wiring en `sync_all_docs()`.
- Agrega el caso al test de `DocSyncTests` en `tests/test_pipeline_logic.py`
  (grep `class DocSyncTests`).

Si esto resulta más grande de lo previsto, opción mínima aceptable: cambiar
`1.15.0` por la versión actual y un comentario HTML "actualizar con
`make sync-docs`", pero deja constancia en el PR de que la deriva puede
repetirse.

**Verify**: `python scripts/sync_docs.py --check` → exit 0;
`grep -n "1.15.0" docs/installation.md` → 0.

### Step 3: NEXT_STEPS

- `docs/backlog/NEXT_STEPS.md:34-35` → reemplaza por:
  "Documentación de API con MkDocs — **completada** (Plan 021 archivado); el
  sitio se publica en `/reference/`."
- Nota: la corrección de Zenodo en `ROADMAP.md` **ya se hizo** al reescribir el
  ROADMAP (2026-09-29); no lo toques en este plan.

**Verify**: `grep -n "Pendiente de priorización" docs/backlog/NEXT_STEPS.md` →
0; `grep -n "pendiente operador" ROADMAP.md` → 0 (verificación de que la
reescritura del ROADMAP incorporó el DOI).

### Step 4: Links a planes archivados + guardrail

- Repunta los 6 links de Current state a `plans/archive/...` (los relativos
  `plans/NNN-...md` → `plans/archive/NNN-...md`; los URLs absolutos de GitHub
  también).
- Agrega en `tests/test_ci_config.py` un test que recorra `docs/**/*.md` y
  `plans/README.md`, encuentre referencias `plans/(\d{3}-[a-z0-9-]+\.md)` y
  afirme que el archivo existe en `plans/` **o** `plans/archive/`. (No falla
  por links a planes aún activos.)

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "archive or plan_link" -v`
→ verde; los 6 links apuntan a archivos existentes.

### Step 5: CodeGraph en AGENTS/SOURCE_OF_TRUTH

- `AGENTS.md:197` → `codegraph query "<query>"` (verifica el resto del bloque:
  `callers/callees/explore/impact` existen en `codegraph --help`).
- `SOURCE_OF_TRUTH.md:120-121` → `codegraph query <name>` y repuntar el "Ir a"
  a `AGENTS.md §2½` (y "Comandos esenciales" de CLAUDE.md no existe: repunta a
  `AGENTS.md §11` o al README).
- `SOURCE_OF_TRUTH.md:112` ("CLAUDE.md → Comandos esenciales") → apunta a
  `AGENTS.md §11` (referencia rápida de comandos).

**Verify**: `codegraph query --help` funciona; `grep -n "codegraph find\|codegraph search" SOURCE_OF_TRUTH.md AGENTS.md` → 0.

### Step 6: Cierre

`make doctor`, `make docs-build`, `make lint`, `make format-check`, índice.

## Test plan

- Guardrail de links de planes (Step 4) y caso de `DocSyncTests` (Step 2).
- El resto son ediciones de texto verificadas por grep en Done criteria.

## Done criteria

- [ ] `grep -n "candidate.*2026-09-18" AGENTS.md` → 0
- [ ] `grep -n "17 capas publicables" AGENTS.md scripts/publish_hf_dataset.py` → 0
- [ ] `grep -c "extractor.py" AGENTS.md` en §3 → 17 entradas
- [ ] `grep -n "1.15.0" docs/installation.md` → 0
- [ ] `grep -n "Pendiente de priorización" docs/backlog/NEXT_STEPS.md` → 0
- [ ] `grep -n "pendiente operador" ROADMAP.md` → 0
- [ ] `grep -rn "plans/0[0-9][0-9]-" docs/ | grep -v archive` → solo links a planes existentes
- [ ] `grep -n "codegraph find\|codegraph search" AGENTS.md SOURCE_OF_TRUTH.md` → 0
- [ ] `make doctor` → exit 0
- [ ] `./.venv/bin/pytest tests/test_ci_config.py tests/test_pipeline_logic.py -v` → verde
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `check_agents_sync.py` falla por una regla que cuenta entradas de §3 (p. ej.
  exige un número específico), detente y reporta: puede que el checker tenga
  hardcodeado el 14 — actualizarlo es parte del plan, pero verifica su
  docstring antes.
- Si `docs/installation.md` no está en el nav de `mkdocs.yml` o el bloque
  delimitado rompe el render, STOP.
- Si el guardrail de links encuentra decenas de referencias rotas (no solo las
  6), repórtalas; arreglar todas puede ser otro plan.

## Maintenance notes

- La versión en `installation.md` ahora se regenera con `make sync-docs`;
  incluirla en el flujo de release si `sync_docs.py --version-only` no la
  cubre.
- El guardrail de links solo valida existencia, no anclas; es suficiente para
  evitar el 404.
- **Deferred:** bloques de conteo de capas dinámicos en AGENTS §1/§9 (hoy
  prosa); el gate `check_agents_sync` ya protege algunos hechos contables.
