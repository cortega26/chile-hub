# Plan 094: Toolchain única — ruff/mypy una versión + targets locales

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- pyproject.toml Makefile .pre-commit-config.yaml .github/workflows/pipeline-check.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Lint/typecheck give different answers depending on where they run: local ruff
0.16.7 vs CI/pre-commit 0.15.17 (spurious red CI on format-rule drift), hook
mypy v2.1.0 + floating deps vs CI `mypy==2.3.1` locked (errors appear/disappear
by location), and mypy/bandit/pip-audit have no local `make` target — the
strictest gates fail only after push. Slowest possible feedback loop.

## Current state

- `pyproject.toml:78` dev pins `ruff==0.16.7` (what `make lint` uses via
  `.venv`); `pipeline-check.yml:88,91` runs `uvx ruff@0.15.17`;
  `.pre-commit-config.yaml:19-24` hook `astral-sh/ruff-pre-commit v0.15.17`.
- `.pre-commit-config.yaml:26-31` hook `mirrors-mypy v2.1.0` with
  `additional_dependencies: [polars>=1.41.2, requests>=2.34.2,
  tenacity>=9.1.4]` (unpinned); CI (`pipeline-check.yml:68-69`) runs
  `uv run mypy` = `mypy==2.3.1` (`pyproject.toml:82`).
- `Makefile:163-173` — `lint`/`format-check` cover ruff only; zero targets for
  mypy/bandit/pip-audit; `make doctor` (`:82-90`) doesn't run them either.
  CI runs all three (`pipeline-check.yml:68-79`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Lint local | `make lint && make format-check` | declared | exit 0 |
| Typecheck (new target) | `make typecheck` | declared (new) | exit 0, same as CI `uv run mypy` |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: version pins (CI + pre-commit → locked versions), three thin
Makefile targets wired into `check` (and `doctor` if cheap), nothing else.

**Out of scope**: fixing newly-surfaced lint/type findings beyond what the
version alignment itself produces (if alignment surfaces errors, fix the
trivial ones, report the non-trivial — do not expand into a typecheck
remediation plan); changing ruff rule selection; touching 095's Python floor.

## Git workflow

- Branch: `advisor/094-dx-single-toolchain`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline (no changes)

Record current versions: `.venv` ruff/mypy, CI pins, hook revs (all in
Current state — confirm still true live).

**Verify**: `make lint` green unmodified (or record red as broken baseline → STOP).

### Step 1: Single ruff version

Bump `.pre-commit-config.yaml` rev and `pipeline-check.yml` `uvx ruff@...` pin
to `0.16.7` (match the lock). Run `ruff format` once repo-wide if rules
drifted between 0.15→0.16; keep that diff isolated in its own commit.

**Verify**: `make lint && make format-check` green; CI command lines now name the same version (grep).

### Step 2: Single mypy version

Pin the pre-commit mypy rev to match `2.3.1` and pin its
`additional_dependencies` to the `uv.lock` versions (or drop the hook's mypy
and rely on CI + the new local target — either is acceptable; document the
choice in the commit). No floating deps in the hook afterwards.

**Verify**: hook config contains no unpinned mypy deps; `uv run mypy` green.

### Step 3: Local targets

Add `make typecheck` (`uv run mypy`, exact CI invocation), `make audit`
(`uv run pip-audit` exact CI invocation incl. the 096-owned ignore flag —
reference, don't duplicate the flag's rationale), `make sec` (`uv run bandit
-c pyproject.toml -r src/`). Wire into `make check` (keep `refresh` ordering
sane: typecheck/audit alongside lint). Update `make help` text.

**Verify**: all three targets run green locally; `make help` lists them.

## Test plan

- No pytest changes expected. Verification is the gates themselves + a
  `test_ci_config.py`-adjacent assertion ONLY if that file already asserts
  Makefile/CI targets (check first; don't invent a new test home for config).

## Done criteria

- [ ] One ruff version everywhere (lock, CI, pre-commit) — grep-proven
- [ ] One mypy version + pinned hook deps (or documented hook removal)
- [ ] `make typecheck/audit/sec` exist, mirror CI invocations, wired into `check`
- [ ] `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Version alignment surfaces non-trivial new errors (fix trivial, report the rest — don't balloon scope).
- `COMPANION_RULES` flags `Makefile` without `AGENTS.md`/`README.md` in the same diff (rule at `check_companion_paths.py:39`): companions mode runs only on PRs, but pre-empt it — if your Makefile help-text change alters the documented contract, include the doc touch; report if unclear.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Dependabot bumps ruff/mypy: the rule is "bump all three pins in one PR" — say it in the commit message so the next bump follows suit.
- **Deferred:** pip-audit ignore expiry + bandit scope (Plan 096); Python floor (095).
