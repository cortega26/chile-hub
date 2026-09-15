# Plan 095: Floor Python `>=3.11` + despineo pandas + matriz CI

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- pyproject.toml uv.lock .github/workflows/pipeline-check.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: migration
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Python 3.10 hits EOL 2026-10-31 (~6 weeks; security-only since 2023, no bugfix
releases). Worse than EOL itself: the repo silently tests TWO pandas majors —
`uv.lock` resolves pandas 2.3.3 for `<3.11` vs 3.0.3 otherwise — so the 3.10
CI leg masks pandas-3-only regressions while consuming a matrix slot. 3.11+ is
already the tested majority; consumers on 3.10 deserve a clean resolver error,
not a stale interpreter.

## Current state

- `pyproject.toml:10` — `requires-python = ">=3.10,<3.15"`; `:29-35`
  classifiers advertise 3.10–3.14; `:172` ruff `target-version = "py310"`;
  `:215` mypy `python_version = "3.10"`.
- `:49` — `"pandas==3.0.3; python_version >= '3.11'"` (conditional fork).
- `uv.lock:3` — `requires-python = ">=3.10, <3.15"`; pandas resolves to
  **2.3.3** (`python_full_version < '3.11'`) and **3.0.3** (`>= '3.11'`).
- `pipeline-check.yml:423` — package-quality matrix `["3.10", "3.11", "3.12",
  "3.13", "3.14"]`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Relock | `uv lock` (NOT `--locked`) | declared | exit 0, single pandas |
| Lock check | `uv lock --locked` / `uv lock --check` | declared | exit 0 |
| Suite | `./.venv/bin/pytest -n auto -q` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: `requires-python`, pandas marker removal, ruff/mypy floor,
CI matrix, `uv.lock` regen, classifier touch.

**Out of scope**: adopting 3.11+-only syntax in a cleanup sweep (only touch
what breaks); dropping `<3.15` upper cap; Polars 2.0 (Plan 100).

## Git workflow

- Branch: `advisor/095-python-311-floor`
- Commit por step; estilo conventional commits (this is a `feat!:`/breaking-adjacent change — confirm message style with maintainer; classifiers + requires-python are the public contract).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline (no changes)

Confirm the fork live: `grep -n -A3 'version = "2.3.3"\|version = "3.0.3"'`
scoped to pandas in `uv.lock`; record 3.10-leg CI status.

**Verify**: fork confirmed as in Current state (or STOP if already resolved).

### Step 1: Raise the floor

- `requires-python = ">=3.11,<3.15"` (`pyproject.toml:10` + `uv.lock:3` via relock).
- Unmark the pandas pin → `"pandas==3.0.3"` unconditional.
- ruff `target-version = "py311"`, mypy `python_version = "3.11"`.
- Drop `"3.10"` from the CI matrix (`pipeline-check.yml:423`); drop the 3.10 classifier.
- `uv lock` to regen; confirm exactly one pandas in the lock.

**Verify**: `grep -c 'name = "pandas"' uv.lock` → 1; `uv lock --locked` exits 0.

### Step 2: Suite + 3.10-only workarounds

Run the full suite on 3.11+; grep for 3.10-compat shims (`sys.version_info`
checks, `tomllib` backports, `except ImportError` fallbacks for 3.10) and
remove ONLY the ones that are pure 3.10 workarounds with test coverage.
Do not go hunting for new syntax adoption.

**Verify**: `./.venv/bin/pytest -n auto -q` green; `make doctor` green.

## Test plan

- No new tests required (deletion of a matrix leg). If a 3.10 workaround is
  removed, its covering test must still pass (or be removed with it — say so
  in the commit, per the repo's test-update policy in AGENTS.md §8).

## Done criteria

- [ ] `requires-python` floor is 3.11 everywhere (pyproject + lock)
- [ ] Single pandas major in `uv.lock`; `uv lock --locked` green
- [ ] CI matrix has no 3.10; ruff/mypy floors at 3.11
- [ ] Full suite + doctor green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- A runtime consumer constraint requires 3.10 (maintainer call — report, don't decide).
- Relock pulls unrelated upgrades (pin the diff to the floor change; if `uv lock` rewrites the world, use `uv lock --upgrade-package` scoping or report).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Next EOL on the horizon: 3.11 security until 2027-10-31 — no action now, noted for the calendar.
- Reviewer: the `feat!:`-style message + CHANGELOG entry (via PSR, automatic) — confirm release-note wording mentions the dropped interpreter.
- **Deferred:** upper-cap `<3.15` policy (revisit when 3.15 RCs appear).
