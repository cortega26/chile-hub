# Plan 038: Deduplicate the two byte‑identical `pipeline_status_utils.py` copies

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/pipeline_status_utils.py src/chile_hub/pipeline_status_utils.py src/chile_hub/__init__.py`
> Also run `diff src/pipeline_status_utils.py src/chile_hub/pipeline_status_utils.py` — it must be empty
> (byte‑identical). If it isn't, the copies have already drifted; STOP and report the diff.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: none (but if Plan 024 edited both copies, ensure they are still identical before starting)
- **Category**: tech-debt
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`src/pipeline_status_utils.py` and `src/chile_hub/pipeline_status_utils.py` are **886 lines each and
byte‑identical**. They are kept in sync only by a docstring instructing a human to hand‑copy edits
("Si editas este archivo, copia el resultado idéntico a la otra ubicación"). A prior audit claimed this
was "unified," but two physical copies remain — 886 lines of logic maintained twice, guaranteed to drift
the first time someone edits one under time pressure. The wheel ships only `src/chile_hub`, so the
package copy must remain real, self‑contained code; the top‑level copy exists only for pipeline/script
imports (run with `PYTHONPATH=src`).

## Current state

- `src/chile_hub/pipeline_status_utils.py` — the **shipped** copy (in the wheel). Self‑contained; uses
  `_find_root()` (searches for `pyproject.toml`) so the same code works from `src/` and `src/chile_hub/`.
  This must stay the canonical real module.
- `src/pipeline_status_utils.py` — identical copy, **not** shipped. Imported (via `PYTHONPATH=src`) by:
  - `src/build_dev_db.py:109`
  - `src/builders/metadata.py:13`
  - `scripts/verify_pipeline.py:20` (`from src.pipeline_status_utils import load_json`)
  - `scripts/pipeline_status.py:8`
  - `tests/test_pipeline_logic.py`
- The package copy is imported by `src/chile_hub/core.py:24` via `from .pipeline_status_utils import …`.
- **Important coupling risk**: `src/chile_hub/__init__.py:9` does `from .core import ChileHub, main`. So
  importing `chile_hub.pipeline_status_utils` runs the package `__init__`, which imports `core.py`
  (2302 lines). A re‑export shim (below) therefore makes the pipeline transitively import the library's
  `core.py`. `core.py` imports the package copy via a **relative** import (`from .pipeline_status_utils`),
  so there is no import cycle back to the top‑level shim — but confirm this in Step 2.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Confirm identical (before) | `diff src/pipeline_status_utils.py src/chile_hub/pipeline_status_utils.py` | empty |
| Import smoke (pipeline context) | `PYTHONPATH=src .venv/bin/python -c "import pipeline_status_utils as m; print(m.load_json)"` | prints a function, no error |
| Pipeline‑logic tests | `.venv/bin/python -m pytest tests/test_pipeline_logic.py -q` | all pass |
| Full build | `make build` | exit 0 |
| Library tests | `make build && .venv/bin/python -m pytest tests/test_chile_hub.py -q` | all pass |

## Scope

**In scope**:
- `src/pipeline_status_utils.py` (becomes a thin re‑export shim)
- Possibly `src/chile_hub/pipeline_status_utils.py` (only to drop the "copy me by hand" docstring)

**Out of scope**:
- Changing any of the 886 lines of logic — this is a pure dedup; behavior must be identical.
- The import sites listed above — they should keep working unchanged (`from pipeline_status_utils import X`
  and `from src.pipeline_status_utils import X` both still resolve to the shim).
- Making `chile_hub/__init__.py` lazy — tempting to avoid the core import, but that's a separate change; do not
  do it here.

## Git workflow

- Branch: `advisor/038-dedup-pipeline-status-utils`
- Conventional commit, e.g. `refactor: deduplica pipeline_status_utils via re‑export shim`.

## Steps

### Step 1: Replace the top‑level copy with a re‑export shim

Replace the entire body of `src/pipeline_status_utils.py` with a shim that re‑exports everything (including
underscore‑prefixed names some callers may use) from the canonical package module:

```python
"""Shim de compatibilidad: re‑exporta la fuente canónica del paquete.

La implementación real vive en ``chile_hub/pipeline_status_utils.py`` (la copia
empaquetada en el wheel). Este módulo existe para imports del pipeline que corren
con ``PYTHONPATH=src`` (``from pipeline_status_utils import …``). No dupliques
lógica aquí.
"""

from chile_hub.pipeline_status_utils import *  # noqa: F401,F403
import chile_hub.pipeline_status_utils as _canonical

# Re‑exporta también los nombres con guion bajo que algunos callers usan.
globals().update({k: getattr(_canonical, k) for k in dir(_canonical) if not k.startswith("__")})
```

### Step 2: Verify no import cycle and the pipeline context works

**Verify**:
```bash
PYTHONPATH=src .venv/bin/python -c "import pipeline_status_utils as m; print(m.load_json, m.compute_freshness)"
PYTHONPATH=src .venv/bin/python -c "from src.pipeline_status_utils import load_json; print(load_json)"
```
Both must print functions with no `ImportError`/`RecursionError`. If either raises a circular‑import or
`RecursionError`, STOP — the shim approach is blocked by the `__init__ → core` coupling; fall back to the
guard‑test approach in the Maintenance notes.

### Step 3: Drop the manual‑sync docstring from the canonical copy

In `src/chile_hub/pipeline_status_utils.py`, remove the "CANONICAL SOURCE … deben ser IDÉNTICOS … copia el
resultado idéntico" instructions from the module docstring (they no longer apply). Keep the rest of the
docstring describing what the module does.

### Step 4: Run the pipeline and both guarding test suites

**Verify**:
```bash
make build
.venv/bin/python -m pytest tests/test_pipeline_logic.py tests/test_chile_hub.py -q
```
Both must pass (these two suites are the existing drift guards; they now guard the shim instead of a hand copy).

## Test plan

- No new logic tests. The existing `test_pipeline_logic.py` (imports the top‑level module) and
  `test_chile_hub.py` (exercises the package copy via `core.py`) together prove the shim re‑exports correctly
  and the package copy still works.
- Optionally add a tiny test asserting `pipeline_status_utils.load_json is chile_hub.pipeline_status_utils.load_json`
  (same object) to lock in that there's one implementation.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `wc -l src/pipeline_status_utils.py` shows a small number (< 30 lines — it's now a shim)
- [ ] `PYTHONPATH=src .venv/bin/python -c "import pipeline_status_utils as m; m.load_json; m.compute_freshness; m.build_hub_health"` exits 0
- [ ] `make build` exits 0
- [ ] `.venv/bin/python -m pytest tests/test_pipeline_logic.py tests/test_chile_hub.py -q` exits 0
- [ ] `grep -n "deben ser IDÉNTICOS" src/chile_hub/pipeline_status_utils.py` → no matches
- [ ] `make lint` and `make format-check` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- Step 2 raises a circular import / `RecursionError` (the `__init__ → core` coupling blocks the shim).
- Any import site relies on a name the `import *` + `globals().update` shim does not re‑export (a test/import fails).
- `make build` fails after the change with an import‑related error.

## Maintenance notes

- **Fallback if the shim is blocked** (Step 2 fails): keep both files but (a) add a test/pre‑commit check that
  asserts `diff` of the two files is empty, so drift fails CI, and (b) reduce the finding to "guarded, not merged."
  Record this outcome in `plans/README.md` if you take it.
- A cleaner long‑term fix is making `chile_hub/__init__.py` lazy (PEP 562 `__getattr__`) so importing a submodule
  doesn't pull in `core.py`; that would also speed up `import chile_hub`. Deferred — note it as a follow‑up.
- Reviewer should confirm the wheel still contains a real `pipeline_status_utils.py` (the package copy), not the shim.
