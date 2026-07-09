# Plan 033: Enforce mypy, bandit, pip‑audit, and interrogate in CI (not just local pre‑commit)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- .github/workflows/pipeline-check.yml .pre-commit-config.yaml pyproject.toml Makefile`
> If any changed, re‑read them before editing.

## Status

- **Priority**: P2
- **Effort**: S–M
- **Risk**: MED
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

Four configured quality/security gates run **only** as local pre‑commit hooks and are never
enforced server‑side: `mypy`, `bandit`, `pip‑audit`, `interrogate`. The CI `quality` job runs
only `ruff check` + `ruff format --check`. So a contributor who hasn't run `pre-commit install`,
or who commits with `--no-verify`, can land type regressions, bandit‑class issues, and vulnerable
dependencies on `main` with zero server‑side detection. The two security gates (bandit, pip‑audit)
have no CI enforcement at all. Additionally, the strict docstring gate is unreachable: interrogate
runs with `fail-under = 0`, and the `make docs-coverage` target its comment points at does not exist.

## Current state

- `.github/workflows/pipeline-check.yml` `quality` job (lines 30‑55): only `uvx ruff@0.15.17 check` and
  `uvx ruff@0.15.17 format --check`. No mypy/bandit/pip‑audit/interrogate step anywhere in the file.
- `.pre-commit-config.yaml` defines the four locally:
  - mypy (`mirrors-mypy` v2.1.0, `pass_filenames: false`, `additional_dependencies: [polars, requests, tenacity]`)
  - pip‑audit: `entry: uv run pip-audit`
  - interrogate: `entry: uv run interrogate`
  - bandit: `entry: uv run bandit -c pyproject.toml -r src/`
- `pyproject.toml`: `[tool.mypy]` (files = chile_hub, extractors, validation.py, build_dev_db.py, builders),
  `[tool.bandit]`, `[tool.interrogate] fail-under = 0` with a comment referencing a non‑existent
  `make docs-coverage`.
- `Makefile`: has `docs-build`/`docs-serve` but **no** `docs-coverage` target.
- Verified clean baselines by the audit: `pip-audit` reports **no** known vulnerabilities; `bandit -ll`
  reports **no** medium+ issues. mypy and interrogate baselines are unknown — establish them in Step 1.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Sync dev env | `uv sync --extra pipeline --extra dev` | exit 0 |
| mypy | `uv run mypy` | establish baseline (Step 1) |
| bandit | `uv run bandit -c pyproject.toml -r src/` | no medium+ (known clean) |
| pip‑audit | `uv run pip-audit` | no vulns (known clean) |
| interrogate (strict) | `uv run interrogate --fail-under=80 src/chile_hub` | establish baseline (Step 1) |

## Scope

**In scope**:
- `.github/workflows/pipeline-check.yml` (add gate steps to the `quality` job)
- `Makefile` (add a `docs-coverage` target)
- `pyproject.toml` (only if Step 1 requires a mypy/interrogate baseline tweak — keep minimal)

**Out of scope**:
- Fixing a large backlog of mypy errors in one go — if Step 1 reveals many, see STOP conditions; do not
  paper over them with blanket `# type: ignore`.
- Changing `[tool.bandit]`/`[tool.mypy]` scope — mirror what pre‑commit already runs.

## Git workflow

- Branch: `advisor/033-ci-quality-gates`
- Conventional commit, e.g. `ci(quality): ejecuta mypy/bandit/pip-audit/interrogate en CI`.

## Steps

### Step 1: Establish current baselines locally (decide blocking vs staged)

```bash
uv sync --extra pipeline --extra dev
uv run mypy                                   # record pass/fail + error count
uv run bandit -c pyproject.toml -r src/       # expect clean
uv run pip-audit                              # expect clean
uv run interrogate --fail-under=80 src/chile_hub  # record pass/fail + %
```

Decision:
- If `mypy` and `interrogate` pass (or fail by a handful easily fixed) → wire all four as **blocking** CI steps (Step 2) and fix the few issues.
- If either has a **large** backlog (dozens of errors / far below 80%) → STOP and report the counts; wiring
  it as blocking would red‑wall the repo. The likely path is: wire bandit + pip‑audit + mypy as blocking now
  (bandit/pip‑audit are known clean; mypy is the project's declared type surface), and add interrogate as a
  **non‑blocking** informational step until docstring coverage is raised (a separate effort).

### Step 2: Add gate steps to the `quality` job

Add to `.github/workflows/pipeline-check.yml` `quality` job. Because these tools need the project's deps
(mypy needs polars stubs etc.), add a sync first (the job currently uses `uvx ruff` without syncing):

```yaml
      - name: Install dev dependencies
        run: uv sync --extra pipeline --extra dev

      - name: Type check (mypy)
        run: uv run mypy

      - name: Security scan (bandit)
        run: uv run bandit -c pyproject.toml -r src/

      - name: Dependency audit (pip-audit)
        run: uv run pip-audit
```

Keep the existing ruff steps. If Step 1 decided interrogate is non‑blocking, add it as:
```yaml
      - name: Docstring coverage (informational)
        run: uv run interrogate --fail-under=80 src/chile_hub || true
```
Otherwise make it blocking (drop the `|| true`).

Alternatively (cleaner parity, if you prefer): replace the individual steps with a single
`uv run pre-commit run --all-files` step after the sync, so CI runs exactly the local hook set. Choose one
approach and be consistent.

### Step 3: Add the missing `make docs-coverage` target

In `Makefile`, add (and register in `.PHONY`):

```make
docs-coverage:
	$(PYTHON) -m interrogate --fail-under=80 src/chile_hub
```

Update the `[tool.interrogate]` comment in `pyproject.toml` so it references the now‑real target.

**Verify**: `make docs-coverage` runs (passes or reports the % — matching Step 1's baseline).

### Step 4 (optional): decide pytest‑xdist

`pytest-xdist` is a declared dev dep but never used (no `-n auto`). Either add `-n auto` to the CI pytest
step and `Makefile` `test`/`coverage` targets (faster CI), or remove the dependency. If enabling, run the
suite once with `-n auto` locally to surface any order/shared‑state dependence before committing.

## Test plan

- No new unit tests. The gates ARE the verification. Optionally extend `WorkflowContractTests` in
  `tests/test_chile_hub.py` to assert the `quality` job contains the mypy/bandit/pip‑audit steps so they
  can't be silently removed.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -nE "mypy|bandit|pip-audit" .github/workflows/pipeline-check.yml` shows the new steps
- [ ] `make docs-coverage` exists and runs
- [ ] Locally: `uv run mypy`, `uv run bandit -c pyproject.toml -r src/`, `uv run pip-audit` all exit 0 (or the interrogate/mypy exception is documented per Step 1)
- [ ] `make lint` and `make format-check` still exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `uv run mypy` reports a large backlog (report the count and the top error categories) — do not mass‑ignore.
- `uv run pip-audit` reports a real CRITICAL/HIGH (unexpected — the last audit was clean) — surface it; it
  becomes its own fix.
- Interrogate is far below 80% — report the number so the maintainer can decide blocking vs informational.

## Maintenance notes

- Once green, any new type/security regression fails CI — the intended safety net. This is the highest‑value
  DX change because it closes the local‑only enforcement gap.
- Reviewer should confirm the `quality` job's added sync doesn't blow the 10‑minute timeout (it shouldn't).
