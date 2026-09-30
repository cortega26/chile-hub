# Plan 117: Alinear el protocolo de fuente caída con el código (`source_mode: archived`)

> **Executor instructions**: Este plan tiene una decisión embebida. Ejecuta el
> Step 0 (decisión) y sigue solo la rama elegida. Si no puedes decidir con la
> evidencia del repo, detente y reporta. Actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- AGENTS.md src/builders/_shared.py scripts/verify_pipeline.py docs/adr/ADR-015-fuentes-retiradas-fuera-de-la-senal-de-salud.md`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: LOW-MED
- **Depends on**: none
- **Category**: docs / decisión
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

AGENTS.md §6 ("Protocolo ante fuente permanentemente caída", `:526-537`) instruye
marcar el metadata con `source_mode: "archived"` para congelar un dataset
histórico. Pero `VALID_SOURCE_MODES = {"live", "fallback", "monthly"}`
(`src/builders/_shared.py:52`) y `verify_pipeline.py:915` rechaza cualquier
modo fuera de ese set: **seguir el protocolo documentado aborta el build/verify**.
La práctica real del repo para fuentes muertas es otra: `maturity_status:
"deprecated"` en `data/source_registry.json` + conjunto `retired` (ADR-015,
Plan 068) + extractor neutralizado. La documentación canónica y el state machine
del código deben decir lo mismo; hoy, un agente que siga §6 rompe CI.

## Current state

- `AGENTS.md:526-537`:
  ```
  3. **Marcar** el metadata con `source_mode: "archived"` y `notes: ["Fuente original
     dejó de existir el YYYY-MM-DD. Dataset congelado en su última actualización."]`.
  ```
- `src/builders/_shared.py:50-56`:
  ```python
  VALID_SOURCE_MODES = {"live", "fallback", "monthly"}
  ...
  NON_FALLBACK_SOURCE_MODES = {"live", "monthly"}
  ```
- `scripts/verify_pipeline.py:915` — `if dataset_metadata.get("source_mode") not
  in VALID_SOURCE_MODES: fail(...)`; `:594` y `:1322` usan los mismos sets.
- Mecanismo real vigente: `data/source_registry.json` con
  `maturity_status: "deprecated"` (ver `consumo_electrico_comunal` y
  `delincuencia_comunal`), `_load_retired_datasets()` en `src/builders/reports.py`
  (ADR-015), `extractor` neutralizado (Plan §5 de AGENTS, pasos de deprecación).
- `grep -rn '"archived"' src/ scripts/ app.js` → 0 matches.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Gates docs | `python scripts/check_agents_sync.py --docs AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md` | declared | exit 0 |
| Tests invariantes | `./.venv/bin/pytest tests/test_pipeline_logic.py -k "source_mode or retired or health" -v` | declared | verde |
| Tests verify | `./.venv/bin/pytest tests/test_verify_pipeline.py -v` | declared | verde |
| Build | `make build` | declared | exit 0 |

## Scope

**In scope**:
- `AGENTS.md` (§6, pasos 3-5) **o** `src/builders/_shared.py` +
  `scripts/verify_pipeline.py` + tests, según la decisión
- `tests/` (según rama elegida)

**Out of scope**:
- Cambiar `maturity_status` de datasets existentes.
- `data/source_registry.json` (no hay dataset que congelar en este plan).
- La lógica de salud/`retired` (ADR-015) — se reutiliza, no se rediseña.

## Git workflow

- Branch: `advisor/117-archived-mode-alignment`
- Commit: `docs(agents): alinea el protocolo de fuente caída con el código` o
  `feat(pipeline): soporta source_mode archived` según rama.
- No push/PR.

## Steps

### Step 0: Decisión (obligatoria)

Revisa `docs/adr/ADR-015-fuentes-retiradas-fuera-de-la-senal-de-salud.md` y
`docs/dataset-inclusion-criteria.md`. Elige:

- **Rama A (recomendada, default):** el congelamiento se expresa con
  `maturity_status: "deprecated"` + conjunto `retired` (mecanismo ya
  implementado y probado). El `source_mode` sigue siendo el modo del último
  fetch (`live`/`fallback`/`monthly`). Es un cambio de documentación.
- **Rama B:** implementar `archived` como modo válido con semántica definida
  (¿publicable? ¿exento de freshness? ¿cómo lo trata `hub_health`?). Requiere
  decisión explícita del mantenedor y toca gates.

Si el mantenedor no está disponible y no hay instrucción previa, ejecuta
**Rama A** (es la que refleja el código y ADR-015) y déjalo escrito en el PR.

---

## Rama A (docs) — ejecutar si Step 0 = A

### Step A1: Corregir §6

En `AGENTS.md:526-537` (y cualquier otra mención; `grep -n "archived" AGENTS.md`):

- Paso 3 pasa a: "**Marcar** el dataset como retirado en
  `data/source_registry.json` (`maturity_status: "deprecated"`, ver ADR-015) y
  agregar la nota de congelamiento en `notes` del metadata. `source_mode`
  conserva el modo del último fetch exitoso; **no existe un modo `archived`**
  (el state machine válido es `live|fallback|monthly`)."
- Paso 4/5: referenciar el procedimiento de deprecación de §5 y `retired`.

### Step A2: Guardrail de no-recaída

En `tests/test_ci_config.py` agrega un test (o extiende
`AgentsSyncGateGuardrailTests`) que afirme que `AGENTS.md` no contiene
`source_mode: "archived"` y que `VALID_SOURCE_MODES` en
`src/builders/_shared.py` es exactamente `{"live", "fallback", "monthly"}`
(importa la constante o lee el archivo; el test ya tiene `ROOT_DIR`).

**Verify**: `python scripts/check_agents_sync.py --docs
AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md` → exit 0;
`./.venv/bin/pytest tests/test_ci_config.py -k "Agents" -v` → verde.

---

## Rama B (código) — solo con aprobación explícita

### Step B1: Definir semántica por escrito

Antes de tocar código, agrega la definición al ADR existente (nuevo ADR si
corresponde): `archived` = dataset congelado, no se re-extrae, sigue
publicable si `public_bundle_eligible`, exento de gates de frescura live, y
`build_hub_health` lo trata como `retired`-like. Sin esta definición escrita,
STOP.

### Step B2: Implementar

- `VALID_SOURCE_MODES` incluye `"archived"`.
- `NON_FALLBACK_SOURCE_MODES`: decidir si `archived` es "no fallback" para el
  gate de publicación; documentarlo en un comentario.
- `verify_pipeline.py`: comportamiento explícito (no accidental) para
  `archived` en `:594`, `:915`, `:1322`.
- `src/builders/metadata.py`/`reports.py`: freshness exenta para `archived`.
- Tests: un caso por gate en `tests/test_verify_pipeline.py` y
  `tests/test_pipeline_logic.py`.

**Verify**: `make build && ./.venv/bin/pytest tests/test_verify_pipeline.py
tests/test_pipeline_logic.py -v` → verde.

---

## Test plan

- Rama A: guardrail de texto/constante (2 asserts) + gates de docs.
- Rama B: un test por gate tocado (publicación, frescura, salud) + test de
  metadata válida.

## Done criteria

- [ ] Step 0 ejecutado y rama declarada en el PR/commit
- [ ] Rama elegida implementada con sus verifies en verde (`make build`, gates de docs, pytest focal)
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope de la rama elegida
- [ ] Fila del índice actualizada

## STOP conditions

- Si Step 0 no produce decisión y no puedes inferir que Rama A es la correcta,
  STOP (documentar la duda y cerrar como Rama A solo si el mantenedor lo pidió).
- Rama B: si aparece una tercera interpretación (p. ej. `archived` debe
  desaparecer del bundle), STOP.
- Si `check_agents_sync.py` tiene reglas que cuentan menciones/estructura de §6
  y el cambio las rompe, reporta el conflicto antes de "arreglar" el checker.

## Maintenance notes

- La frase clave a preservar: **un hecho, un dueño** — el modo de extracción
  lo define `VALID_SOURCE_MODES`; el estado de retiro, `source_registry.json`
  (ADR-015). No volver a introducir estados de retiro dentro de `source_mode`.
- Si en el futuro se implementa Rama B, este plan queda superseded y debe
  actualizar AGENTS §6 en el mismo PR.
- **Deferred:** unificar el enum de `source_mode` con el de `maturity_status`
  en un solo campo derivado — cambio de contrato mayor; reabrir con un ADR.
