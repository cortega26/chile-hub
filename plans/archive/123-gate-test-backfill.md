# Plan 123: Backfill de tests en gates críticos sin cobertura de fallo

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/extractors/calidad_aire_extractor.py scripts/verify_pipeline.py scripts/check_companion_paths.py scripts/sync_release_artifact_version.py scripts/check_source_urls.py tests/`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW-MED
- **Depends on**: soft de Plan 122 (para ver el efecto en cobertura); no bloquea
- **Category**: tests
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Cinco rutas críticas tienen solo cobertura de camino feliz (o ninguna), y sus
fallos son silenciosos o abortan el publish:

1. `process_calidad_aire()` (`calidad_aire_extractor.py:448-500`) — el merge
   incremental de la serie diaria de SINCA (staging o seed desde Parquet,
   `keep="last"`, casts post-concat, sort) no tiene ningún test. Un bug puede
   truncar/duplicar la serie publicada; el único guard aguas abajo es el gate
   de caída de `record_count` >20% de `verify_pipeline`.
2. `verify_indicadores_diagnostics()` (`verify_pipeline.py:699-794`) — solo se
   ejecuta contra el estado committeado; sus ~8 ramas de fallo nunca corren.
3. `check_companions()` (`check_companion_paths.py:113-134`) — el único test
   (`test_ci_config.py:184-193`) pasa paths que no disparan ninguna regla;
   una regresión apagaría el gate anti-drift de AGENTS §12 en silencio.
4. `sync_release_artifact_version.py` (`:31-78`) — reescribe versión en 3 JSON,
   reconstruye ZIP + sha, re-adjunta manifiesto y sincroniza la landing, sin
   un solo test que lo importe; ya causó una falla de release real
   (`pypi-release.yml:82-88`).
5. `check_source_urls.py` (`:31-55` clasificación OK/WARN/DEAD + códigos de
   salida en `:58-88`) — solo hay guardrails de texto; si la clasificación se
   rompe, las fuentes muertas dejan de avisar.

## Current state

- `calidad_aire_extractor.py:448-500` (merge), `:525-537` (`write_staging`).
  Tests de la clase `CalidadAire*` en `tests/test_extractors.py:3914-3990`
  cubren `fetch_data`, `normalize_rows`, parsers y `run(dry_run=True)`.
  `grep -rn "process_calidad_aire" tests/` → 0.
- `verify_pipeline.py:699-794` (`verify_indicadores_diagnostics`) y
  `:797-824` (`verify_top_issue*`); los tests viven en
  `tests/test_verify_pipeline.py` (golden copy + `SystemExit`).
- `check_companion_paths.py` — `COMPANION_RULES` en `:37-65`,
  `check_companions(changed)` en `:113-134`; test único en
  `tests/test_ci_config.py:184-193`.
- `sync_release_artifact_version.py` — funciones `update_json_version` (`:42-47`),
  `main()` (`:50-78`); writers en `src/builders/artifacts.py`.
- `check_source_urls.py` — `load_urls()` (`:31-37`), `check_url()` (`:40-55`),
  `main()` (`:58-88`).
- `tests/test_ci_config.py:14-24` agrega `scripts/` a `sys.path` (los módulos
  de scripts son importables desde tests).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests focal | `./.venv/bin/pytest tests/test_extractors.py tests/test_verify_pipeline.py tests/test_ci_config.py -v -k "calidad or diagnostics or companion or release_artifact or source_urls"` | declared | verde |
| Suite de extractores | `./.venv/bin/pytest tests/test_extractors.py -v` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `tests/test_extractors.py` (calidad_aire)
- `tests/test_verify_pipeline.py` (diagnostics/top_issue)
- `tests/test_ci_config.py` (companions, source_urls)
- `tests/test_builders_artifacts.py` o `tests/test_packaging_runtime.py`
  (sync_release_artifact_version — elige el que ya use fixtures de
  `data/normalized`; ver Step 4)
- `src/` solo si hace falta extraer una función pura para testear (evítalo si
  se puede testear lo existente)

**Out of scope**:
- Cambiar lógica de los gates (este plan solo prueba lo que hay).
- `src/validation.py` (ya tiene `test_validation.py`).

## Git workflow

- Branch: `advisor/123-gate-test-backfill`
- Un commit por módulo: `test(calidad-aire): ...`, `test(verify): ...`, etc.
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_extractors.py tests/test_verify_pipeline.py tests/test_ci_config.py -q` verde (los que requieren `data/normalized/` deben correr tras `make build`). Si no, STOP.

### Step 1: `process_calidad_aire` (4 casos)

Usa `tempfile.TemporaryDirectory` y `patch.object` de `STAGING_CSV_PATH`,
`METADATA_PATH` y `_seed_history_from_parquet`/`fetch_data`:
1. **sin staging** → siembra desde `_seed_history_from_parquet` y agrega lo
   nuevo.
2. **con staging** → merge y nota "historial: fusionado con staging existente".
3. **staging corrupto** → parte de lo nuevo y agrega la nota de ilegible.
4. **misma clave re-cosechada** → `keep="last"` deja la fila nueva (verifica
   valor, no solo conteo).

Afirma también tipos finales (fecha String, `valor_promedio_diario` Float64) y
orden por `[fecha, id_estacion, codigo_contaminante]`.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -v -k "calidad and process"` → 4 nuevos verdes.

### Step 2: `verify_indicadores_diagnostics`

En `tests/test_verify_pipeline.py`, tests sintéticos (el módulo acepta dicts):
1. `source_detail` inválido → `SystemExit`.
2. `published_backfill` sin la nota/warning correspondiente → `SystemExit`
   (lee las ramas exactas en `verify_pipeline.py:720-794` y arma un caso por
   cada acoplamiento: `raw_recoveries`, `preserved_existing_pairs`,
   `empty_live_pairs`, `published_backfills`, `fetch_failures`).
3. Caso feliz con el set completo → no lanza.
4. `verify_top_issue*` con payload inválido → `SystemExit` (un caso).

**Verify**: `./.venv/bin/pytest tests/test_verify_pipeline.py -v -k "diagnostics or top_issue"` → verde.

### Step 3: `check_companions` por regla

En `tests/test_ci_config.py`, tabla de casos (parametriza con
`subTest`):
1. Trigger sin compañero → error que nombra la regla.
2. Trigger + cada prefijo compañero → sin error.
3. `src/extractors/base.py` solo → sin error (exclusión documentada en
   `EXTRACTOR_RULE_EXCLUDED_PATHS`).
4. `data/dataset_catalog_config.json` + `AGENTS.md` → sin error.
5. Path sin regla → sin error.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -v -k companions` → verde.

### Step 4: `sync_release_artifact_version`

Elige el archivo de test que ya construye un `data/normalized/` sintético
(`tests/test_packaging_runtime.py` o `tests/test_builders_artifacts.py`;
grep `pipeline_metadata.json` en tests para ubicarlo). Agrega un test que:
1. Copie/construya un normalized mínimo (`pipeline_metadata.json`,
   `hub_bundle.json`, `datapackage.json`, un parquet mínimo, catálogo).
2. Corra `main()` con un `pyproject.toml`/versión controlada (patch de
   `ROOT_DIR`/`NORMALIZED_DIR`).
3. Afirme: los 3 JSON tienen `version` nueva; el ZIP contiene el manifiesto;
   el `.sha256` coincide con `sha256sum` del ZIP; segunda corrida idempotente
   (mismo digest).

Si montar el fixture es demasiado grande para el patrón existente, reduce el
alcance a `update_json_version()` (función pura, test trivial) y documenta la
parte de `main()` como Deferred — pero intenta el test completo primero.

**Verify**: test nuevo pasa.

### Step 5: `check_source_urls`

Tests con `fetch_with_retry` parcheado (importa el módulo desde `scripts/`):
1. `load_urls()` con registry sintético → solo URLs http, sin duplicados.
2. `check_url`: 200→OK, 404→WARN, 500→DEAD, excepción→DEAD.
3. `main()`: registry vacío → 1; con un DEAD → 1; solo WARN → 0.
Usa `patch.object` de `load_urls`/`check_url` para `main()` (evita red).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -v -k source_urls` → verde.

## Test plan

- ~15 tests nuevos entre 4 archivos. Cada paso tiene su filtro `-k`.
- Patrones: `tests/test_verify_pipeline.py` (golden + synthetic),
  `tests/test_ci_config.py:184` (companions), clase `CalidadAire*` en
  `tests/test_extractors.py`.

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_extractors.py tests/test_verify_pipeline.py tests/test_ci_config.py -v` → verde
- [ ] `grep -c "process_calidad_aire" tests/test_extractors.py` → ≥1
- [ ] `grep -c "check_companions" tests/test_ci_config.py` → ≥5 (casos)
- [ ] `grep -c "sync_release_artifact_version" tests/` → ≥1 import real (no solo texto)
- [ ] `grep -c "check_url" tests/test_ci_config.py` → ≥4
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `data/normalized/` no existe en tu checkout y los tests que lo requieren
  fallan, corre `make build` primero; si el build falla por red (extractores),
  reporta y testea solo los módulos sintéticos.
- Si `sync_release_artifact_version.main()` requiere red o writers pesados que
  no se pueden montar en test, reduce al caso `update_json_version` y deja el
  resto como Deferred explícito.
- Si descubres que una rama de `verify_indicadores_diagnostics` es
  inalcanzable (código muerto), NO la testees: repórtalo como hallazgo.

## Maintenance notes

- Estos tests son de caracterización: si los gates cambian de contrato
  deliberadamente, actualizar los asserts con la referencia al ADR/plan que lo
  motiva (regla de AGENTS §8).
- La cobertura de `scripts/` depende del Plan 122; sin él, el efecto no se ve
  en el badge.
- **Deferred:** tests de property/fuzz para el merge de series temporales
  (calidad_aire) — el caso incremental tiene invariantes claras; reabrir si
  aparece un bug de merge real.
