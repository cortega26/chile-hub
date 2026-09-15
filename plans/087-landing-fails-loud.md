# Plan 087: `sync_landing_metadata` falla ruidoso en vez de `print`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/builders/landing.py src/builders/catalog.py src/build_dev_db.py scripts/check_landing_sync.py tests/test_ci_config.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: correctness
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

`sync_landing_metadata()` escribe `index.html` y luego `app.js`; si el segundo
falla, el `except` solo imprime y el build queda verde con la landing a medio
sincronizar. La deriva se detecta 24h después en el gate `schedule` ("Check
build-synced files") y aborta el publish diario. Ya ocurrió dos veces
(`autoridades_locales`, Pipeline Check #270; `geometria_comunal`, publish roto
2026-07-24 al 26 — ver `scripts/check_landing_sync.py:15`). AGENTS.md §4.2
exige fallar ruidosamente.

## Current state

- `src/builders/landing.py:172-191`: escribe `index.html` (`:172-177`), luego
  `app.js` (`:186-189`), y ante cualquier excepción:
  ```python
  except Exception as e:
      print(f"Advertencia: No se pudo actualizar la landing: {e}")
  ```
- `src/builders/catalog.py:14-31`: `write_pipeline_metadata()` llama a
  `sync_landing_metadata(public_site_url, version)` (`:31`) solo si la versión
  se leyó bien; ante fallo de lectura de `pyproject.toml` (`:27-28`) otro
  `print` de advertencia y `version = "unknown"` (ese path es benigno: no hay
  nada que sincronizar — no tocar).
- `scripts/check_landing_sync.py` reconstruye el bloque con la misma función
  del pipeline y compara byte a byte (no duplicar lógica de render).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Landing gate | `./.venv/bin/python scripts/check_landing_sync.py` | declared | exit 0 |
| Focal tests | `./.venv/bin/pytest tests/test_ci_config.py -q` | declared | all pass |
| Build smoke | `make build` | declared | exit 0, `index.html`/`app.js` synced |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**:
- `src/builders/landing.py` (propagar error en vez de solo `print`)
- `src/build_dev_db.py` solo si el call path necesita manejar el error (ver Step 1)
- `tests/test_ci_config.py` o `tests/test_pipeline_logic.py` (guardrail del nuevo comportamiento)

**Out of scope**:
- `render_catalog_json_ld_block()` — fuente única de render, no tocar.
- `catalog.py:27-28` (versión ilegible → skip benigno, no es el bug).
- Reescribir `check_landing_sync.py`.

## Git workflow

- Branch: `advisor/087-landing-fails-loud`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run landing gate + focal tests unmodified. If red unmodified, STOP and report.

**Verify**: both exit 0 before any edit.

### Step 1: Make the failure loud

Change `landing.py:190-191` so a sync failure raises (keep the `print` as a log
line before the raise). Trace the caller: `catalog.py:31` ← `build_dev_db.py`
`_generate_reports` — confirm the exception aborts the build (fail-ruidoso)
rather than being swallowed upstream. If an upstream `except` swallows it,
narrow the fix to re-raise (do not refactor the whole report phase).

**Verify**: `./.venv/bin/python scripts/check_landing_sync.py` → exit 0; unit-run `sync_landing_metadata()` against a read-only path raises instead of printing.

### Step 2: Guardrail test

Add a test (model after `AutoridadesElectasScraplingGuardrailTests`-style
text/regression tests in `tests/test_ci_config.py`): `sync_landing_metadata`
with an unwritable target (or mocked `open` raising) must raise, not return
normally. If `test_ci_config.py` is the wrong home (it guards CI/Makefile
regressions), put it in `tests/test_pipeline_logic.py` and say why in the
commit message.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py tests/test_pipeline_logic.py -q` → all pass.

### Step 3: End-to-end smoke

Run `make build` (or at minimum the report phase) and confirm green + synced
landing; then `make doctor`.

**Verify**: `make doctor` → exit 0.

## Test plan

- New: raise-on-failure test (Step 2).
- Existing: landing sync gate + CI config tests.
- Verification: commands in the table.

## Done criteria

- [ ] `grep -n "Advertencia: No se pudo actualizar la landing" src/builders/landing.py` is followed (within ~3 lines) by a `raise`
- [ ] Landing gate + focal tests + `make doctor` all exit 0
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Excerpts at `landing.py:172-191` / `catalog.py:14-31` don't match.
- The raise breaks `make build` in a path that used to succeed for a benign reason (e.g. missing markers on a fresh checkout) — then scope to raise only when a partial write occurred, and report the nuance.
- Verification fails twice after reasonable fixes; out-of-scope touch needed.

## Maintenance notes

- Reviewer: confirm no new `except Exception: print(...)` swallow was added elsewhere in the touched path.
- **Deferred:** unifying the two `print`-warnings in `catalog.py`/`landing.py` into structured `_logging` — cosmetic, not worth a plan alone.
