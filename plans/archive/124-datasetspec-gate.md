# Plan 124: Cerrar el hueco del cohort DatasetSpec (3 specs faltantes + gate catálogo↔spec)

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- data/dataset_specs/ data/dataset_catalog_config.json scripts/check_companion_paths.py tests/test_phase2_datasetspec.py src/registry/dataset_spec.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt / dirección (D1)
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

La migración DatasetSpec (ADR-018, Phases 2–3D) se declaró **completa** con 22
specs. Pero el catálogo tiene **25 claves**: `calidad_aire`,
`estadisticas_vitales` y `permisos_edificacion` (agregados 2026-09-14/15,
después de Phase 3D) no tienen spec, y **ningún gate lo detecta**:
`check_companion_paths.py registry` exige contrato y doc por clave, no spec; el
overlay `catalog_config_with_spec_overlay` conserva la entrada legacy en
silencio (`dataset_spec.py:631-642`); y `test_phase2_datasetspec.py:87` fija el
conteo literal `22`. Cada dataset nuevo en el hueco encarece la migración
futura (Phase 11) sin que nadie lo note. Además, tres documentos canónicos
siguen afirmando "22 specs: complete" (`AGENTS.md:151,652,928`,
`SOURCE_OF_TRUTH.md:87`).

## Current state

- `data/dataset_catalog_config.json` — 25 claves.
- `data/dataset_specs/` — 22 archivos; faltan los 3 citados.
- `data/dataset_specs/comunas.json` (modelo): `spec_version`, `dataset`,
  `kind`, `publication_track`, `public_bundle_eligible`, `maturity_status`,
  `confidence_tier`, `extraction_lane`, `extractor`, `contract_path`,
  `validator`, `alias_for`, `dependencies`, `source{...}`, `reuse_policy{...}`,
  `freshness_policy{...}`, `documentation{...}`, `outputs{...}`, `join_keys`.
- `src/registry/dataset_spec.py:631-642` (`catalog_config_with_spec_overlay`) —
  tolera datasets sin spec.
- `scripts/check_companion_paths.py:73-84` (`check_registry`) — exige contrato
  y doc, no spec.
- `tests/test_phase2_datasetspec.py:83-111` — `assert len(specs) == 22` + set
  literal de nombres.
- `docs/architecture-migration-roadmap.md:253-258` — "Every dataset has one
  DatasetSpec"/precondición de Phase 5.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests spec | `./.venv/bin/pytest tests/test_phase2_datasetspec.py -v` | declared | verde |
| Gate registry | `python scripts/check_companion_paths.py registry` | declared | exit 0 |
| Gates docs | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `data/dataset_specs/calidad_aire.json`, `data/dataset_specs/estadisticas_vitales.json`,
  `data/dataset_specs/permisos_edificacion.json` (nuevos)
- `scripts/check_companion_paths.py` (gate de spec)
- `tests/test_phase2_datasetspec.py` (conteo dinámico)
- `AGENTS.md`, `SOURCE_OF_TRUTH.md`, `docs/architecture-migration-phase-3d.md`,
  `docs/architecture-migration-roadmap.md` (afirmaciones "22 complete")

**Out of scope**:
- Phase 4–11 de la migración (no se toca `_shared.py`/`reports.py`).
- Cambiar el esquema de los specs.
- `data/source_registry.json` (los specs lo referencian; no lo modifican).

## Git workflow

- Branch: `advisor/124-datasetspec-gate`
- Commits: `feat(registry): cierra cohort DatasetSpec con 3 specs y gate`
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_phase2_datasetspec.py -v` verde y
`python scripts/check_companion_paths.py registry` exit 0. Si no, STOP.

### Step 1: Crear los 3 specs

El ejecutor debe derivar cada spec de las fuentes existentes, **sin inventar**:

- `data/dataset_catalog_config.json[<clave>]` → `outputs`, `extractor`,
  `reuse_policy`.
- `data/source_registry.json` → `publication_track`, `maturity_status`,
  `confidence_tier`, `extraction_lane`, `source.*`, `review_by`.
- `contracts/datasets/<clave>.schema.json` → `contract_path`.
- `src/validation.py` → `validator` (busca `validate_<clave>`).
- `docs/datasets/<clave>.md` → `documentation.path` + descripción.
- `kind`: `"direct"` para los tres (no son alias ni derivados).

Copia la forma exacta de un spec de un dataset comparable:
- `estadisticas_vitales` ← modelo `censo_comunal.json` (INE, anual, comunal).
- `permisos_edificacion` ← modelo `finanzas_municipales.json` (anual, comunal).
- `calidad_aire` ← modelo `indicadores_urbanos_siedu.json` (cobertura parcial).

Regla dura: **cero hechos nuevos**. Si un campo no se puede derivar, usa el
mismo valor que el registry/catálogo y anota en el PR qué campo quedó igual.

**Verify**: `python - <<'PY'` que cargue los 3 JSON y afirme que
`dataset`, `contract_path`, `validator`, `outputs.parquet` existen y que
`contract_path`/`outputs.parquet` apuntan a archivos reales (`Path.is_file()`).

### Step 2: Tests dinámicos

En `tests/test_phase2_datasetspec.py`:
- Reemplaza el literal `22` y el set de nombres por una comparación contra
  `data/dataset_catalog_config.json`:
  `assert {s.dataset for s in specs} == set(catalog.keys())`.
- Mantén el resto de los asserts de equivalencia (ya iteran `iter_specs()` y
  ahora cubrirán los 3 nuevos).
- Si algún test asume `len(specs) == 22` en otro archivo, actualízalo
  (`grep -rn "== 22" tests/`).

**Verify**: `./.venv/bin/pytest tests/test_phase2_datasetspec.py -v` → verde
(idealmente sube el conteo de tests por parametrización).

### Step 3: Gate en `check_companion_paths.py`

En `check_registry()` agrega el chequeo simétrico al de contrato/doc:

```python
SPECS_DIR = ROOT_DIR / "data" / "dataset_specs"
ALLOWED_MISSING_SPEC: set[str] = set()  # exención explícita, con razón

...
        if key not in ALLOWED_MISSING_SPEC:
            spec_path = SPECS_DIR / f"{key}.json"
            if not spec_path.is_file():
                errors.append(f"falta DatasetSpec para '{key}': {spec_path}")
```

Documenta en el comentario de `ALLOWED_MISSING_SPEC` que una exención solo
entra con razón escrita (p. ej. "dataset agregado durante un freeze de
migración decidido en <fecha>").

**Verify**: `python scripts/check_companion_paths.py registry` → exit 0;
test: en `tests/test_ci_config.py` o `test_phase2_datasetspec.py`, un caso que
borra temporalmente un spec de un tmpdir y afirma que `check_registry()`
reporta el error (patch de `SPECS_DIR`).

### Step 4: Corregir las afirmaciones "22 complete"

- `AGENTS.md:151` → `(22 specs: complete)` pasa a `(25 specs: complete — cubre
  todo el catálogo)`.
- `AGENTS.md:652` y `:928` → idem.
- `SOURCE_OF_TRUTH.md:87` → `25 specs`.
- `docs/architecture-migration-phase-3d.md:26` — es un documento histórico de
  fase: **no reescribir el hito**, agrega una línea al inicio: "Nota
  post-3D (2026-09-29): el catálogo creció a 25 datasets; los 3 posteriores
  (calidad_aire, estadisticas_vitales, permisos_edificacion) se sumaron al
  cohort en el Plan 124."
- `docs/architecture-migration-roadmap.md:253-258` → actualizar la
  precondición "Every dataset has one DatasetSpec" con "cubierto por gate
  `check_companion_paths.py registry` desde Plan 124".

**Verify**: `grep -rn "22 specs" AGENTS.md SOURCE_OF_TRUTH.md` → 0; `make
doctor` → exit 0 (los gates de docs no cuentan números de specs, pero
`check_agents_sync` valida otros hechos contables).

### Step 5: Cierre

`make lint`, `make format-check`, actualizar índice.

## Test plan

- `test_phase2_datasetspec.py`: conteo dinámico + equivalencia de los 3 specs
  nuevos (los tests existentes ya comparan spec↔catálogo/registry/contrato).
- Gate: test de `check_registry()` con un spec faltante → error.
- Verificación total: `./.venv/bin/pytest tests/test_phase2_datasetspec.py -v`
  + `make doctor`.

## Done criteria

- [ ] `ls data/dataset_specs/*.json | wc -l` → 25
- [ ] `python scripts/check_companion_paths.py registry` → exit 0
- [ ] `./.venv/bin/pytest tests/test_phase2_datasetspec.py -v` → verde
- [ ] `grep -rn "22 specs" AGENTS.md SOURCE_OF_TRUTH.md` → 0
- [ ] `make doctor` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si un campo de un spec nuevo no puede derivarse de registry/catálogo (p. ej.
  `confidence_tier` ausente), detente y reporta el campo; no inventes valores.
- Si la equivalencia spec↔legacy falla para alguno de los 3 (el test te lo
  dirá), NO ajustes el test: investiga si el legacy o el spec están mal y
  reporta.
- Si el gate nuevo encuentra otros huecos (más datasets sin spec), repórtalos.

## Maintenance notes

- Regla nueva: todo dataset que entre al catálogo necesita spec o exención
  escrita. Si se decide pausar la migración, la exención debe registrar la
  decisión (fecha + motivo) — un hueco silencioso ya no es posible.
- `COMPANION_RULES` ya exige que `data/dataset_specs/` se toque junto a docs y
  tests; el gate nuevo cierra el otro lado (catálogo → spec).
- **Deferred:** decidir el fin de la migración (cutover de `_shared.py` a
  specs como fuente runtime, Phase 11) — es una decisión de arquitectura mayor;
  este plan solo restaura la integridad del cohort.
