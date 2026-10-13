# Plan 132: Auditoría — descomposición del pipeline de build (+ CLI) y trinquete de complejidad

> **Executor instructions**: Sigue los pasos en orden. Este plan toca el
> corazón del build: cada step debe terminar con `make test` verde antes de
> seguir. Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu
> fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- src/build_dev_db.py src/builders/metadata.py src/chile_hub/pipeline_status_utils.py src/chile_hub/cli.py src/registry/dataset_spec.py scripts/check_validation_registration.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: M (dividir en 2–3 PRs si el ejecutor lo prefiere)
- **Risk**: MED (pipeline diario)
- **Depends on**: 131 (ruff select ampliado; evita conflictos de config)
- **Category**: refactor / KISS (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

Cuatro god functions y una fuente de datos implícita concentran el riesgo del
build: `_load_inputs` (E34, 364 L) repite ~4 veces la misma lista de datasets
(rutas, required, metadata, loads); `build_dataset_metadata` tiene 443 L;
`_compute_validations` 181 L; `build_hub_health` F53/152 L; y la CLI tiene
`build_parser` 344 L + `_main` 308 L (F79) que hoy solo se cubren con smoke
tests. Descomponer habilita el trinquete de complejidad y el ratchet de tipado
(137). La duplicación `dfs[...]` es el hallazgo D2 del reporte.

## Current state

- `build_dev_db.py:158-521` — `_load_inputs`: rutas individuales (18), tuplas
  `required_staging`, `metadata_checks`, `metadata_files`, `load_metadata`
  individuales y extracción de `dfs`; triplica la misma lista de datasets.
- `build_dev_db.py:524` — `_compute_validations` (181 L) con unpacking de 20
  variables + bloque `validations = {…}` (contrato de
  `scripts/check_validation_registration.py` y §5 de AGENTS.md).
- `builders/metadata.py:400` — `build_dataset_metadata` (443 L).
- `chile_hub/pipeline_status_utils.py:276` — `build_hub_health` (F53, 152 L).
- `chile_hub/cli.py:72` `build_parser` (344 L); `:418` `_main` (F79, 308 L,
  `# pragma: no cover`).
- `registry/dataset_spec.py:446` — `parse_dataset_spec` (E39).
- radon actual: máximos E/F = `_main` 79, `_parse_comuna_sheet` 61 (va en 133),
  `build_hub_health` 53, `fetch_data` 40 (133), `parse_dataset_spec` 39,
  `_load_inputs` 34.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Tests pipeline | `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_phase1_characterization.py -q` | verde |
| Suite | `make test` | verde |
| Build real | `make build && make verify` | verde (usa staging local) |
| Complejidad | `uvx radon@6.0.1 cc -s --min C src/build_dev_db.py src/builders/metadata.py src/chile_hub/pipeline_status_utils.py src/chile_hub/cli.py src/registry/dataset_spec.py` | lista decreciente |
| Lint | `make lint` | exit 0 |

## Scope

**In scope**: `build_dev_db.py`, `builders/metadata.py`,
`chile_hub/pipeline_status_utils.py`, `chile_hub/cli.py`,
`registry/dataset_spec.py`, config ruff (`C901`), tests que los cubren.

**Out of scope**: `validation.py` (135), `core.py` (134), `scripts/*` (136),
comportamiento externo (mismos artefactos, mismos mensajes de error).

## Steps

### Step 0 — Baseline

`make test` + `make build && make verify` verdes. radon registrado.

### Step 1 — `src/builders/inputs.py`: tabla declarativa + contenedor

- Crear `InputSpec(name, csv, metadata, extractor, required)` como **única**
  tabla de datasets de entrada (reemplaza rutas, `required_staging`,
  `metadata_checks`, `metadata_files`).
- `load_staging_inputs() -> BuildInputs` con `frames: dict[str, pl.DataFrame]`,
  `metadata: dict[str, dict | None]` y `previous_pipeline_metadata`; conservar
  exactamente los mensajes `SystemExit` actuales (tests los ejercitan).
- `_load_inputs()` en build_dev_db pasa a ser fachada de 1 línea (o se elimina
  junto con sus callers).
- Criterio: `build_dev_db.py` pierde ≥250 líneas y la lista de datasets queda
  en un solo lugar.

### Step 2 — `build_dataset_metadata` por dataset

- Extraer `_metadata_<dataset>(frames, meta, …)` por dataset, con un loop sobre
  la tabla de 131/Step 1; los campos que dependen de varios datasets
  (p. ej. `perfil_territorial`) quedan explícitos y documentados.
- No cambiar el JSON de salida (verificar con `git diff` de
  `data/normalized/*.json` tras `make build`).

### Step 3 — `_compute_validations` y el contrato del registro

- Reducir el unpacking usando `BuildInputs` (D2).
- **Conservar el bloque `validations = {…}`** (es el contrato textual del
  checker §5). Si se decide reemplazarlo por tabla declarativa, actualizar en
  el mismo commit `scripts/check_validation_registration.py` + su test + el
  texto de AGENTS.md §5 que lo describe.
- `detect_series_anomalies` (D24) puede quedar como está (vive en 135).

### Step 4 — `build_hub_health` (C53)

- Extraer `_dataset_health_entry(dataset_name, dataset, validation)` y
  `_severity(...)`; el loop principal queda <40 líneas. Salida byte-idéntica
  (test de caracterización existente).

### Step 5 — CLI: parser por comando + dispatch

- `build_parser` → builders por grupo (`_add_cache_parser`, `_add_export…`) o
  tabla; `_main` → `HANDLERS: dict[str, Callable]` con una función por comando
  (las actuales ramas `if args.command == …`).
- Quitar el `# pragma: no cover` ya que los handlers se vuelven testeables;
  añadir 2–3 tests de dispatch en `tests/test_chile_hub.py` (sin invocar red).

### Step 6 — `parse_dataset_spec` (E39)

- Tabla de parsing por sección (`_parse_source`, `_parse_outputs`,
  `_parse_contract` ya existen parcialmente); sin cambios de semántica
  (tests de `test_phase2_datasetspec.py` son el contrato).

### Step 7 — Trinquete de complejidad

- `[tool.ruff.lint] select` += `"C90"`; `[tool.ruff.lint.mccabe]`
  `max-complexity = 35` (o el mínimo que deje el árbol verde tras los Steps
  1–6). Para las funciones pendientes (p. ej. `_parse_comuna_sheet`,
  `fetch_data` → 133), `# noqa: C901  # 133` con referencia al plan; cada plan
  posterior remueve sus noqas.
- Guardrail en `tests/test_ci_config.py`: el select incluye `C90` (docstring:
  god functions del audit; el umbral baja con cada plan de descomposición).

### Step 8 — Cierre

`make test`, `make build && make verify`, `make lint`, `make doctor`;
`plans/README.md` actualizado. Si el diff de artefactos en `make build` es
distinto de cero (fuera de timestamps), STOP.

## Test plan

- `test_pipeline_logic.py`, `test_phase1_characterization.py`,
  `test_phase2_datasetspec.py`, `test_chile_hub.py` (CLI dispatch nuevo).
- `make build && make verify` es el gate de no-regresión de artefactos.

## Done criteria

- [ ] `build_dev_db.py` ≤ ~700 L y lista de datasets en una sola tabla
- [ ] radon: ningún F/E en los archivos tocados; C901 habilitado
- [ ] `make build` sin diff de artefactos + suite/doctor verdes
- [ ] Fila del índice actualizada

## STOP conditions

- Si `make build` produce artefactos distintos (más allá de timestamps),
  detente: la descomposición cambió semántica.
- Si `check_validation_registration.py` no puede adaptarse sin debilitar el
  contrato §5, deja el bloque `validations` intacto y limita el step al
  unpacking.
