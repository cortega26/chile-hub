# Plan 077: Caracterizar build_dev_db.py (cobertura 21% → ≥60%)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/build_dev_db.py tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: L
- **Risk**: MED
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`build_dev_db.py` (883 líneas, 59 commits de churn desde 2026-05) tiene 21%
de cobertura: todo `main()` y las fases
`_load_inputs`/`_compute_validations`/`_write_data_artifacts`/`_generate_reports`
están sin test (missing 227-514, 519-656, 661-765, 775-831). El corazón del
pipeline —la feature por la que existe el repo— puede romperse en la ruta
feliz sin que la suite lo detecte; cualquier refactor de `main()` es a ciegas.

## Current state

- `src/build_dev_db.py` — `main()` + 4 fases; los únicos paths cubiertos son
  los de error temprano (`tests/test_pipeline_logic.py:87-124`).
- Patrón a reutilizar: `tests/test_verify_pipeline.py:88-121` (staging
  sintético en tmpdir + parcheo de rutas); `tests/geo_fixtures.py`
  (fixtures sintéticos).
- `pyproject.toml:182-185` — TC-02 documentado como follow-up pendiente.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Cobertura | `./.venv/bin/pytest tests/test_pipeline_logic.py --cov=src.build_dev_db --cov-report=term-missing` | ≥60% tras el plan |
| Tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q` | all pass |

## Scope

**In scope**: `tests/test_pipeline_logic.py` (o archivo nuevo
`tests/test_build_dev_db.py` — decidir según tamaño), fixtures sintéticos.
**Out of scope**: refactor de `build_dev_db.py` (solo lectura), los
extractores, los builders (planes separados).

## Steps

### Step 1: Baseline de cobertura

Mide la cobertura actual por fase y documenta el baseline en el commit.

**Verify**: `--cov=src.build_dev_db` reporta ~21%.

### Step 2: Staging sintético mínimo

Construye un helper (en el archivo de test) que cree en un tmpdir: los
CSVs + metadata.json necesarios para `_load_inputs` (patrón de
`test_verify_pipeline.py`), parcheando `STAGING_DIR`/`NORMALIZED_DIR`/rutas
de `build_dev_db`.

**Verify**: el helper crea el staging y `_load_inputs` lo lee sin red ni
extractores (assert de la estructura cargada).

### Step 3: Caracteriza las fases puras primero

Cubre `_compute_validations` (pura — dados los inputs, assert del dict de
validaciones y el resultado de los validadores registrados). Luego
`_write_data_artifacts` (assert de artefactos de salida en tmpdir).

**Verify**: cobertura de las 2 fases > 60% individual.

### Step 4: Caracteriza `main()` y `_generate_reports`

Con el staging sintético, corre `main()` completo (sin ZIP si se puede
parchear, o con ZIP en tmpdir) y asserta los reportes de salida
(`hub_health.json`, `pipeline_status.md`, etc.).

**Verify**: cobertura de `build_dev_db` ≥ 60% en total.

## Test plan

- Tests de caracterización por fase; modelar sobre
  `tests/test_verify_pipeline.py::VerifySyntheticTests`.
- Assertar invariantes (existencia + estructura), no contenido exacto.
- Verificación: `--cov=src.build_dev_db` ≥ 60%; suite completa verde.

## Done criteria

- [ ] Cobertura de `build_dev_db.py` ≥ 60% (era 21%)
- [ ] Tests de las 4 fases + `main()` existen
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- La caracterización congela un bug real (validar contra el artefacto golden
  publicado antes de escribir asserts).
- `main()` requiere red o extractores para correr (diseñar el staging para
  que no — si es imposible, cubrir las fases por separado y reportar).

## Maintenance notes

- Estos tests son la red de seguridad para el TECHDEBT-02 heredado y para
  cualquier refactor futuro de `build_dev_db.py`.
- El patrón de staging sintético puede reutilizarse en TEST-COV-09
  (reports.py).
