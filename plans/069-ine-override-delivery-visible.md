# Plan 069: Que el override INE sea un delivery visible (no enmascarado como backfill)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/extractors/bcentral_extractor.py src/validation.py scripts/verify_pipeline.py tests/test_extractors.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

El override INE (issue #43, serie IPC muerta en mindicador.cl) scrapea la
variación mensual del IPC desde `ine.gob.cl`. El valor es **nuevo** (p. ej.
2026-07-01 = 0.1), pero el build lo etiqueta como `published_backfill`
("reutilización del último artefacto publicado", que es falso) porque el
bucle de `published_backfills` corre **después** del bucle de
`ine_override_pairs` y lo sobrescribe. El gate de publicación ADR-016
(`verify_publication_policy`) —el único mecanismo pensado para frenar datos
scrapeados sin revisión— queda inerte. Confirmado en `data/normalized/pipeline_metadata.json`
del build publicado: `indicator_delivery.ipc == "published_backfill"` y
`ine_override_pairs == ['ipc/2026']` simultáneamente.

## Current state

- `src/extractors/bcentral_extractor.py:459-463` — orden de los bucles que
  construyen `indicator_delivery`:
  ```python
  for pair in diagnostics.get("ine_override_pairs", []):
      indicator_delivery[pair.split("/", 1)[0]] = "ine_override"
  for code in diagnostics.get("published_backfills", []):
      indicator_delivery[code] = "published_backfill"
  ```
  El segundo sobrescribe al primero cuando co-ocurren (el caso real: el
  extractor no pudo obtener ipc de mindicador y lo tomó del INE).
- `scripts/verify_pipeline.py:541-547` — `verify_publication_policy` rechaza
  deliveries fuera de un allowlist:
  ```python
  if dataset.get("source_mode") not in NON_FALLBACK_SOURCE_MODES:
      violations.append(...)
  ```
  El delivery `ine_override` no está en el allowlist de `verify_dataset_catalog`
  (`verify_pipeline.py:904-918`), así que si el enmascaramiento se quitara sin
  tocar verify, el build fallaría — comportamiento deseado pero requiere el
  allowlist con revisión explícita.
- Tests: `tests/test_extractors.py:634-679`
  (`test_process_indicators_records_ine_override_in_metadata`) cubre solo el
  caso `load_existing_staging → (None, None, [])`; el caso co-ocurrente
  (production) no está testeado y hoy contradice el test.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_extractors.py -q -k "IneIpc"` | all pass |
| Build | `make build` | exit 0 |
| Verify | `./.venv/bin/python scripts/verify_pipeline.py --profile publication` | exit 0 |
| Lint | `make lint && make format-check` | exit 0 |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**:
- `src/extractors/bcentral_extractor.py`
- `scripts/verify_pipeline.py`
- `src/validation.py` (solo si se necesita una validación de delivery)
- `tests/test_extractors.py`, `tests/test_pipeline_logic.py`, `tests/test_verify_pipeline.py`

**Out of scope**:
- `src/extractors/ine_ipc.py` (regex/fetch — plan separado)
- Cambios en el gate de ADR-016 para otras series (UF/dólar/euro/UTM)
- El bundle ZIP / catálogo (plan separado 071)

## Git workflow

- Branch: `advisor/069-ine-override-delivery`
- Conventional commits, uno por paso lógico (ej. `fix(extractors): ...`).
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Reproduce el bug con un test que falle

Agrega en `tests/test_extractors.py` (en `IneIpcOverrideIntegrationTests`) un
test `test_override_coexists_with_published_backfill_delivery_visible` que
simule el caso de producción: `load_existing_staging` devuelve
`(existing, current_year, ["ipc"])` (el staging previo tiene ipc de 2025-12),
`fetch_indicator_year("ipc", current_year)` devuelve `[]`, y
`fetch_ine_ipc` devuelve el reading de julio. Luego `process_indicators()` y
assert que `metadata["indicator_delivery"]["ipc"] == "ine_override"` y que
`"ipc" not in metadata["published_backfills"]` o que el delivery gana.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "override_coexists"` → FALLA (bug reproducido).

### Step 2: Corrige el orden de los bucles

En `src/extractors/bcentral_extractor.py:459-463`, aplica el bucle de
`published_backfills` ANTES del de `ine_override_pairs` (o excluye los códigos
de override del bucle de backfill), de modo que `ine_override` gane cuando
ambos co-ocurran.

**Verify**: el test del Step 1 pasa; `./.venv/bin/pytest tests/test_extractors.py -q -k "IneIpc"` → all pass.

### Step 3: Registra `ine_override` en el allowlist de verify con revisión explícita

En `scripts/verify_pipeline.py`, agrega `ine_override` a los deliveries
permitidos por `verify_dataset_catalog` (líneas 904-918) SOLO cuando el
override viene de una fuente autoritativa documentada (INE). Modela el
patrón de `--allow-known-anomalies` (ADR-013) si se quiere revisión explícita;
mínimo, el delivery debe ser visible en `pipeline_metadata.json`.

**Verify**: `./.venv/bin/python scripts/verify_pipeline.py --profile publication` → exit 0 con el metadata real (que ahora dice `ine_override`).

### Step 4: Actualiza el test existente y la doc

Actualiza `test_process_indicators_records_ine_override_in_metadata` si
necesita el caso co-ocurrente, y `docs/datasets/indicadores.md` para que el
estado del delivery `ine_override` sea el documentado.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py tests/test_pipeline_logic.py tests/test_verify_pipeline.py -q` → all pass.

## Test plan

- `test_override_coexists_with_published_backfill_delivery_visible` (nuevo,
  en `IneIpcOverrideIntegrationTests`) — el caso de producción.
- Modelar sobre `test_process_indicators_records_ine_override_in_metadata`
  existente.
- Verificación: suite focal + `make build` + `verify --profile publication`.

## Done criteria

- [ ] `metadata["indicator_delivery"]["ipc"] == "ine_override"` en el build real
- [ ] `verify_pipeline.py --profile publication` exit 0 con el metadata real
- [ ] Test del caso co-ocurrente existe y pasa
- [ ] `make lint && make format-check` exit 0
- [ ] `make doctor` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

- El código en las ubicaciones citadas no coincide con los excerpts (drift).
- El metadata real ya dice `ine_override` sin el fix (el bug se corrigió por otra vía).
- El gate de publicación empieza a rechazar el build diario por otra serie.

## Maintenance notes

- El delivery `ine_override` debe ser visible en `pipeline_metadata.json` —
  es la provenance honesta que el Plan 066 construyó; no reintroducir el
  enmascaramiento.
- Revisar en el PR: que el allowlist de verify no acepte `ine_override` sin
  la fuente autoritativa documentada.
- Follow-up fuera de scope: hacer que `detect_series_anomalies` (Plan 072)
  cubra el valor INE.
