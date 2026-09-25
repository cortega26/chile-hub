# Plan 101: Subsets reales en el visor de Hugging Face + acceso `hf://`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 039fc03..HEAD -- docs/hf/dataset-card.md scripts/publish_hf_dataset.py docs/http-access.md tests/test_pipeline_logic.py tests/test_ci_config.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: distribution
- **Planned at**: commit `039fc03`, 2026-09-25

## Why this matters

El mirror de Hugging Face (Plan 059/070) es un canal de descubrimiento con
~135 descargas/mes, pero el Dataset Viewer muestra **un único subset `default`
de 1.62M filas** cuyas primeras columnas son de `autoridades_electas`: la card
no declara `configs:`, así que HF fusiona las capas publicables (21 al
2026-09-25) en una sola
tabla confusa. Un visitante (humano o agente) no puede distinguir `comunas` de
`empresas`. Declarar un subset por capa arregla el visor, el SQL Console y
`load_dataset`, sin cambiar ni un dato. Además, el acceso **cero-instalación**
vía `hf://` de DuckDB no está documentado en ninguna parte del repo, pese a que
DuckDB 1.5 (dependencia del extra `query`) lo soporta de forma nativa.

## Current state

- `docs/hf/dataset-card.md` — front-matter `license: other` sin `configs:`;
  placeholders `{{DATASET_COUNT}}` / `{{DATASET_TABLE}}`; ejemplo
  `load_dataset("cortega26/chile-hub", data_files="data/comunas.parquet")`.
- `scripts/publish_hf_dataset.py:144-164` — `build_staging_dir()` copia
  `data/{name}.parquet` y sustituye ambos placeholders en la card.
- Verificado en vivo (2026-09-25): `https://huggingface.co/datasets/cortega26/chile-hub`
  muestra `Subset (1) default · 1.62M rows` con columnas `id_autoridad`,
  `nombre`, `cargo`… (fusionó todo).
- Sintaxis confirmada contra la documentación oficial:
  - HF: bloque `configs:` en el front-matter; `config_name` obligatorio;
    `default: true` elige el subset inicial.
  - DuckDB: `SELECT * FROM 'hf://datasets/cortega26/chile-hub/data/comunas.parquet';`

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Dry-run del publisher | `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` | executed | lista staging + README con `configs:` |
| Tests de lógica | `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "hf or hugging"` | declared | all pass |
| Test CI guardrails | `./.venv/bin/pytest tests/test_ci_config.py -q -k "HfPublish"` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope** (only files you should modify):
- `docs/hf/dataset-card.md` (placeholder + ejemplo + metadata de licencia)
- `scripts/publish_hf_dataset.py` (generar el bloque `configs:`)
- `docs/http-access.md` (sección de acceso vía HF/`hf://`)
- `tests/test_pipeline_logic.py` (test de `build_staging_dir` → README con configs)
- `tests/test_ci_config.py` (guardrail de que la card conserva el placeholder)

**Out of scope** (do NOT touch):
- Selección de carriles `publication_track` (Plan 070) y job `hf-publish` (Plan 059).
- Subir nada a HF: el publish real sigue disparándose solo en release con
  `HF_TOKEN`; este plan es verificable con `--dry-run`.
- Kaggle u otro mirror: deferido en la auditoría 2026-07-18; no reabrir aquí.

## Git workflow

- Branch: `advisor/distribution-wave-1` (wave de los planes 101–105).
- Commit por step; estilo conventional commits (ej. `feat(hf): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Generar el bloque `configs:` desde la selección publicable

Agregar a `scripts/publish_hf_dataset.py` una función pura
`_build_dataset_configs(parquet_entries)` que devuelva el YAML de `configs:`
(un `config_name` por capa, `data_files` con `split: train` y
`path: data/{name}.parquet`, `default: true` sólo en `comunas`). Insertar un
placeholder `{{DATASET_CONFIGS}}` en el front-matter de la card (columna 0) y
sustituirlo en `build_staging_dir()`. El bloque debe ser YAML válido y contener
todas las capas seleccionadas por `select_publishable_files()` (21 archivos
hoy; el conteo sale del registry, nunca hardcodeado).

**Verify**: `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` seguido
de `grep -c "config_name:" <staging>/README.md` → igual al número de
parquet publicables (21 al 2026-09-25).

### Step 2: Corregir el ejemplo de uso y la metadata de la card

En `docs/hf/dataset-card.md`: reemplazar el ejemplo `data_files=` por
`load_dataset("cortega26/chile-hub", "comunas", split="train")`; agregar
`license_name: chile-hub-data-licenses` (HF exige el patrón
`/^[a-z0-9-.]+$/`; un valor con espacios/mayúsculas rechaza el upload) +
`license_link` apuntando a `DATA_LICENSES.md`; corregir
`size_categories` a `1M<n<10M` (el visor reporta 1.62M filas). No tocar
`{{DATASET_TABLE}}` / `{{DATASET_COUNT}}`.

**Verify**: dry-run y `grep -n "load_dataset" <staging>/README.md` muestra el
nombre de configuración; el front-matter parsea como YAML.

### Step 3: Documentar el acceso `hf://` (cero instalación)

Agregar una sección "Hugging Face Hub" a `docs/http-access.md` con: el one-liner
DuckDB sobre `hf://datasets/cortega26/chile-hub/data/comunas.parquet`, la
variante `@~parquet` (revisión auto-convertida) y el ejemplo `load_dataset` por
configuración. Indicar el caveat de que el mirror publica sólo el carril
`stable_publishable`.

**Verify**: `grep -n "hf://datasets/cortega26/chile-hub" docs/http-access.md`
muestra el ejemplo; `make docs-build` exit 0.

### Step 4: Tests

En `tests/test_pipeline_logic.py`, clase `HfDatasetCardTests`:
- `_build_dataset_configs()` devuelve un bloque con un `config_name` por
  entrada y `default: true` sólo en `comunas`.
- `build_staging_dir()` con parquet sintéticos en `tmp_path` escribe un README
  cuyo front-matter parsea con `yaml.safe_load` y cuyas `configs` son N.
En `tests/test_ci_config.py`, guardrail de texto: la card conserva
`{{DATASET_CONFIGS}}`, `{{DATASET_COUNT}}` y `{{DATASET_TABLE}}` (el generador no
debe “absorber” los placeholders).

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q -k "hf or hugging or HfPublish"` → all pass.

## Test plan

- Nuevos: `HfDatasetCardTests` (2 tests) + 1 guardrail en `test_ci_config.py`.
- Patrón existente: `HfPublishJobGuardrailTests` (texto) y tests que importan
  `scripts.publish_hf_dataset` desde `tests/test_pipeline_logic.py`.
- Regresión: dry-run real del script (sin red) en done criteria.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` exit 0 e imprime el staging.
- [ ] `grep -c "config_name:" <staging>/README.md` == número de parquet publicables (21 al 2026-09-25) y el ejemplo de la card ya no usa `data_files=`.
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q` exits 0.
- [ ] `make doctor` exits 0 (incluye `sync_docs --check` y `check_landing_sync`).
- [ ] `git diff --name-only 039fc03...HEAD` lista sólo archivos in-scope.
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog actualizados.

## STOP conditions

Stop and report back (do not improvise) if:

- El placeholder `{{DATASET_CONFIGS}}` no puede quedar en columna 0 del
  front-matter sin romper el YAML generado.
- `build_staging_dir()` cambió de firma respecto a `scripts/publish_hf_dataset.py:144-164`.
- El dry-run intenta red (debe ser 100% offline).
- Una verificación falla dos veces tras un intento razonable de fix.

## Maintenance notes

- Si el set publicable cambia de tamaño, el `configs:` se regenera solo: no
  hardcodear el conteo en la card.
- Reviewer: verificar que `default: true` siga en `comunas` (es el subset que un
  visitante nuevo necesita ver primero).
- Deferido: evaluar Kaggle cuando el fix del visor de HF muestre efecto medible
  (descargas HF del mes siguiente).
