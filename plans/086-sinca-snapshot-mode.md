# Plan 086: Snapshot SINCA viejo deja de etiquetarse `live`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/extractors/calidad_aire_extractor.py src/builders/metadata.py scripts/verify_pipeline.py tests/test_extractors.py`
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

Si el listado SINCA cae, `fetch_data()` carga el último snapshot de disco pero
retorna `source_mode="live"` con `refreshed_at_utc=now` cuando el payload viejo
parsea filas. Los gates de freshness/staleness no disparan y el reporte de salud
muestra `calidad_aire` como fresco con datos de días/semanas atrás. Es la clase
exacta de corrupción silenciosa que AGENTS.md §4.2 prohíbe. El CSV resultante no
cambia — solo su etiqueta — así que el fix es de bajo riesgo.

## Current state

- `src/extractors/calidad_aire_extractor.py:297-341` — `fetch_data()`:
  - `:319-325` ante `RequestException/OSError/ValueError` carga
    `snapshots[-1]`, agrega nota, sigue parseando;
  - `:337-339` sin filas → `"fallback"`; `:341` con filas → `"live"` aunque el
    payload venga de disco (`target = snapshots[-1]`).
  ```python
  target = snapshots[-1]
  notes.append(f"listado SINCA inaccesible, usando snapshot {target.name} ({exc})")
  ...
  notes.append(f"{len(rows)} filas diarias nuevas desde '{target.name}'")
  return rows, "live", LISTADO_URL, notes
  ```
- `src/builders/metadata.py:88-89` — `build_freshness` delega en
  `compute_freshness(refreshed_at_utc, max_age_hours)` (ya canónico, no tocar).
- Convención de modos: `live | fallback` (ver otros extractores y
  `src/builders/_shared.py::NON_FALLBACK_SOURCE_MODES`). Revisa qué valores
  acepta el gate de publication en `scripts/verify_pipeline.py` antes de
  inventar un modo nuevo: preferir reutilizar `"fallback"` con nota que
  identifique el snapshot, salvo que el gate ya distinga `stale_snapshot`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline checker | `./.venv/bin/python scripts/check_validation_registration.py` | executed | `validation registration ok: ...` |
| Extractor tests | `./.venv/bin/pytest tests/test_extractors.py -q -k "calidad or sinca or aire"` | declared | all pass |
| Registry gate | `./.venv/bin/python scripts/check_companion_paths.py registry` | declared | `check_companion_paths ok (modo: registry)` |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope** (only files you should modify):
- `src/extractors/calidad_aire_extractor.py` (modo retornado en el path de snapshot)
- `tests/test_extractors.py` (nuevo test del path de snapshot)
- `scripts/verify_pipeline.py` solo si el modo elegido requiere tratarlo como no-fresco (ver Step 1)

**Out of scope** (do NOT touch):
- `src/builders/metadata.py::build_freshness` — ya delega, no duplicar.
- Cambios al CSV/schema de `calidad_aire` — las filas no cambian.
- Otros extractores con recuperación raw (bcentral registra `raw_recoveries` como warning; no unificar aquí).

## Git workflow

- Branch: `advisor/086-sinca-snapshot-mode`
- Commit por step; estilo conventional commits (ej. `fix(calidad-aire): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run baseline checker + extractor tests on the unmodified checkout. If they fail
unmodified, STOP and report (broken baseline, not your regression).

**Verify**: both commands exit 0 before any edit.

### Step 1: Decide the mode value against the publication gate

Grep `scripts/verify_pipeline.py` and `src/builders/_shared.py` for how
`source_mode` values are treated (`NON_FALLBACK_SOURCE_MODES`, publication
profile). Decide: (a) return `"fallback"` + nota con `target.name`, or
(b) introduce `"stale_snapshot"` tratado como no-fresco en freshness/verify.
Prefer (a) unless the gate needs the distinction. Record the decision in the
commit message.

**Verify**: `grep -rn "stale_snapshot\|NON_FALLBACK_SOURCE_MODES" src/ scripts/ | head` → shows the values your change relies on actually exist.

### Step 2: Return the honest mode from the snapshot path

In `fetch_data()`, when `payload` comes from `snapshots[-1]` (disk), return the
mode decided in Step 1 instead of `"live"`. Keep the note with `target.name`
and the exception. The `FALLBACK_ROWS` paths stay `"fallback"`.

**Verify**: extractor tests pass (Step 0 command).

### Step 3: Add a regression test

In `tests/test_extractors.py`, model after the existing calidad_aire test class:
mock `fetch_with_retry` to raise `requests.RequestException` with one snapshot
present in `RAW_DIR`, assert returned mode != `"live"` and note mentions the
snapshot filename; plus the no-snapshot case asserts `"fallback"`.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "calidad or sinca or aire"` → all pass, including the new test.

## Test plan

- New tests (Step 3): snapshot-recovery mode, no-snapshot fallback.
- Existing pattern: calidad_aire test class in `tests/test_extractors.py`.
- Verification: full `tests/test_extractors.py -q` green.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n 'return rows, "live"' src/extractors/calidad_aire_extractor.py` shows `"live"` only on the fresh-fetch path (not after snapshot load)
- [ ] `./.venv/bin/pytest tests/test_extractors.py -q` exits 0
- [ ] `./.venv/bin/python scripts/check_companion_paths.py registry` exits 0
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog updated

## STOP conditions

Stop and report back (do not improvise) if:

- The code at `calidad_aire_extractor.py:297-341` doesn't match the excerpts.
- `verify_pipeline.py` rejects the chosen mode in a way that breaks the daily build (then prefer `"fallback"` + note).
- A step's verification fails twice after a reasonable fix attempt.
- The fix appears to require touching an out-of-scope file.

## Maintenance notes

- If SINCA gains history endpoints, the snapshot path becomes rare; keep the test (it guards the mode contract, not the frequency).
- Reviewer: check the note still carries `target.name` (auditability of which snapshot fed the build).
- **Deferred:** unifying raw-recovery modes across extractors (bcentral `raw_recoveries`, RES) — needs a design decision on the mode vocabulary; nothing blocks it.
