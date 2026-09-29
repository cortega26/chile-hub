# Plan 128: Compatibilidad hacia adelante — Python 3.15 y DuckDB-Wasm vendorizado

> **Executor instructions**: Sigue los pasos en orden. El Step 1 depende de la
> fecha: Python 3.15 final sale el **2026-10-01**. Si hoy es anterior, sigue
> con el Step 2 y vuelve al Step 1 después (o déjalo en BLOCKED con la fecha).
> Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- pyproject.toml .github/workflows/pipeline-check.yml README.md vendor/duckdb/ scripts/run_lighthouse.sh`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1 (3.15) / P3 (DuckDB-Wasm)
- **Effort**: S (3.15) / M (wasm)
- **Risk**: LOW (3.15) / LOW-MED (wasm)
- **Depends on**: none
- **Category**: deps
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

1. **Python 3.15 final se publica el 2026-10-01** (PEP 790; RC2 el 2026-09-01).
   `pyproject.toml:10` declara `requires-python = ">=3.11,<3.15"` y la matriz
   de packaging prueba 3.11–3.14: desde octubre, `pip install chile-hub` en
   3.15 falla aunque las deps base son compatibles (polars publica wheels
   `cp310-abi3`, requests/platformdirs/rich son puras). El propio Plan 095 dejó
   anotado "revisitar cuando aparezcan los RC" — ese trigger ya se cumplió.
2. **DuckDB-Wasm vendorizado quedó 2 años atrás**: el playground del sitio usa
   la copia en `vendor/duckdb/` (DuckDB-Wasm ~1.29.0 ≈ DuckDB 1.1.1) mientras
   el pipeline escribe con `duckdb==1.5.5`. No hay detección de drift upstream:
   el showcase puede fallar con Parquet nuevos y se pierde dos años de fixes.

## Current state

- `pyproject.toml:10` — `requires-python = ">=3.11,<3.15"`; classifiers
  `:28-32` sin 3.15.
- `.github/workflows/pipeline-check.yml:464-498` — job `package-quality`,
  matriz `["3.11","3.12","3.13","3.14"]`; instala el wheel puro y smoke-testea
  CLI (no instala el extra `pipeline`, por lo que `duckdb` no participa).
- `vendor/duckdb/` — bundle DuckDB-Wasm usado por `playground.js`
  (carga perezosa de módulos desde `vendor/duckdb/`); el plan archivado
  `plans/archive/020-duckdb-wasm-playground.md:122-145` documenta el
  procedimiento de vendorizado original. `scripts/run_lighthouse.sh` y
  `make verify-landing` cubren el smoke del explorador.
- `plans/095-python-311-floor.md:119` — "Deferred: upper-cap `<3.15` policy
  (revisit when 3.15 RCs appear)".

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Build wheel | `make package` | declared | `dist/*.whl` |
| Smoke del wheel | `make package-smoke` | declared | exit 0 |
| Landing smoke | `make verify-landing` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `pyproject.toml` (`requires-python`, classifiers)
- `.github/workflows/pipeline-check.yml` (matriz de 3.15)
- `vendor/duckdb/*` (Step 2)
- `playground.js` / `scripts/verify_landing.py` solo si la API de la librería
  cambió (Step 2)

**Out of scope**:
- Subir `target-version` de ruff o `python_version` de mypy (siguen en 3.11,
  que es el floor).
- DuckDB 2.0 de Python (`duckdb==1.5.5` sigue pineado; GA ~2026-10-21 y su
  revisión consciente ya está documentada en `pyproject.toml:58-63`).
- Polars 2.0 (aún sin GA; el spike del Plan 100 ya está hecho).

## Git workflow

- Branch: `advisor/128-deps-forward-compat`
- Commits: `feat(deps): soporta Python 3.15` y
  `chore(vendor): actualiza DuckDB-Wasm del playground`
- No push/PR.

## Steps

### Step 0: Baseline

`make package-smoke` y (si Playwright está) `make verify-landing` verdes. Si
no, STOP.

### Step 1: Python 3.15 (ejecutar el 2026-10-01 o después)

1. Verifica disponibilidad: en un runner/entorno con `uv` o pyenv,
   `uv python install 3.15` (o `python3.15 --version`). Si 3.15 final no está
   disponible todavía, marca este step BLOCKED y sigue con el Step 2.
2. `pyproject.toml:10` → `requires-python = ">=3.11,<3.16"`.
3. `classifiers` → agrega `"Programming Language :: Python :: 3.15"`.
4. `pipeline-check.yml:472` → agrega `"3.15"` a la matriz.
5. Verifica local/CI que el wheel puro instala y corre:
   `uv build && uv pip install --system --force-reinstall dist/*.whl && python -c "from chile_hub import ChileHub; print(ChileHub)"`.
6. El badge de versiones del README se sincroniza desde `requirements-python`
   vía `scripts/sync_docs.py`; corre `make sync-docs` y revisa el diff.

**Verify**: la matriz del workflow incluye 3.15; `uv lock --locked` sigue
pasando (el cap no afecta el lock); `make sync-docs --check` (o
`python scripts/sync_docs.py --check`) → exit 0.

### Step 2: DuckDB-Wasm

1. Identifica la versión vendorizada actual: `grep -o 'version "[0-9.]*"' vendor/duckdb/*.mjs | head`
   y la dependencia `apache-arrow` embebida; lee
   `plans/archive/020-duckdb-wasm-playground.md:122-145` para saber de dónde
   salieron los archivos.
2. Descarga la release actual de `@duckdb/duckdb-wasm` que use DuckDB ≤1.6
   (misma línea mayor que el pipeline, `duckdb==1.5.5`). Reemplaza los archivos
   `.wasm`/`.mjs`/`.worker.js` en `vendor/duckdb/` conservando **los mismos
   nombres de archivo** que `playground.js` importa (no renombres).
3. Actualiza cualquier referencia de versión en `index.html`/`playground.js`
   (p. ej. comentarios, `?v=` cache-buster si aplica).
4. Ejecuta una query real contra un Parquet de `data/normalized/` en la
   landing local (el smoke de `make verify-landing` puede no cubrirlo; si no
   lo cubre, agrega al smoke una query mínima `SELECT count(*) FROM
   read_parquet('data/normalized/comunas.parquet')` y su assert).
5. Documenta la versión nueva en `vendor/duckdb/README.md` (créalo si no
   existe) con fecha y fuente.

**Verify**: `make verify-landing` → exit 0; query manual del paso 4 devuelve
filas (captura en el PR).

### Step 3: Cierre

`make lint`, `make format-check`, `make doctor`, índice.

## Test plan

- 3.15: la propia matriz de CI (4 versiones → 5) es el test; más
  `make package-smoke` local.
- DuckDB-Wasm: smoke de la landing + query real (agrega assert si falta).
- No se agrega test unitario de versión de wheel.

## Done criteria

- [ ] `grep -n "requires-python" pyproject.toml` → `>=3.11,<3.16`
- [ ] `grep -n "3.15" .github/workflows/pipeline-check.yml` → en la matriz
- [ ] `make package-smoke` → exit 0
- [ ] `make verify-landing` → exit 0
- [ ] `vendor/duckdb/` actualizado + README con versión/fecha
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si 3.15 no está disponible en el runner (final no publicada), deja el Step 1
  como BLOCKED con la fecha objetivo 2026-10-01; no agregues `allow-prereleases`
  ni `3.15-dev` a la matriz sin decisión.
- Si `polars`/`rich`/`requests` no resuelven en 3.15 sin cambios, reporta la
  dependencia y el error exacto (puede requerir un plan de bump separado).
- Si la API de DuckDB-Wasm cambió de forma que `playground.js` necesita
  reescritura (el plan archivado 020 lo advirtió), STOP y reporta el alcance
  real antes de tocar JS.
- Si el nuevo bundle no pasa `make verify-landing`, revierte el vendor y
  reporta.

## Maintenance notes

- La matriz de packaging es el contrato de compatibilidad; cualquier cap nuevo
  se decide ahí con fecha de revisión (como este plan).
- El vendor de DuckDB-Wasm debería tener un check de drift upstream periódico
  (p. ej. en `dependabot` no aplica a vendor); si se repite este trabajo,
  considerar script `scripts/check_vendor_versions.py` con la versión embebida.
- **Deferred:** DuckDB 2.0 (Python y Wasm) — GA esperada ~2026-10-21; revisar
  con el mismo procedimiento (spike + suite) cuando salga, reutilizando
  `plans/100` como plantilla.
