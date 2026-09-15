# Plan 096: `duckdb` acotado + pip-audit expiry + bandit a extractors

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
- **Effort**: S-M
- **Risk**: LOW-MED (LOW for deps, MED for bandit noise)
- **Depends on**: none (coordinate with 094's `make audit`/`make sec` targets — reference them, don't re-do them)
- **Category**: security / deps
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Three small suppurating items: (1) a consumer installing only
`chile-hub[query]` floats on unbounded `duckdb>=1.5.4` while the pipeline that
WROTE the artifacts it reads is frozen at 1.5.5 — reader/writer drift, with
DuckDB 2.0 landing Oct 2026; (2) the pip-audit ignore for a real
command-injection advisory has no expiry trigger — when the upstream fix ships,
nobody is nudged; (3) the only SAST gate never inspects `src/extractors`,
precisely where HTTP/subprocess/filesystem risk lives.

## Current state

- `pyproject.toml:47` pipeline `duckdb==1.5.5`; `:59` query `duckdb>=1.5.4`;
  lock resolves both to 1.5.5 today (verified 2026-09-15).
- `pipeline-check.yml:74-79` — `uv run pip-audit --ignore-vuln
  PYSEC-2026-2132` with inline comment (click.edit() injection via
  click==8.1.8 pinned by python-semantic-release 10.6.2; repo doesn't call
  `click.edit()`; "revisar cuando PSR relaje el pin" — no version check, date,
  or issue).
- `pyproject.toml:254-260` — `[tool.bandit] exclude_dirs =
  ["src/extractors", "tests", "scripts", "data"]`, Medium/Medium thresholds.
  Pattern grep found no active shell-injection/pickle/eval in `src/` — this is
  a visibility gap, not a live vuln.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Relock | `uv lock` then `uv lock --locked` | declared | exit 0 |
| Bandit | `uv run bandit -c pyproject.toml -r src/` | declared | exit 0 after triage |
| Audit | `uv run pip-audit --ignore-vuln PYSEC-2026-2132` | declared | exit 0 |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: one-line duckdb bound, ignore-expiry mechanism, bandit
`exclude_dirs` narrowing + `nosec` triage for extractors.

**Out of scope**: upgrading duckdb past 1.5.x (watch 1.5.6/2.0 separately);
removing the ignore early (the advisory is real); bandit threshold changes.

## Git workflow

- Branch: `advisor/096-deps-alignment-bandit`
- Commit per item (3 commits); conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline

`uv run bandit -c pyproject.toml -r src/` green (excluded tree) unmodified;
record `pip show python-semantic-release click` versions for the commit.

**Verify**: baseline green.

### Step 1: Bound the query extra

`query`: `duckdb>=1.5.5,<1.6` (same floor as pipeline, major cap). Relock;
confirm resolution unchanged today (still 1.5.5) — a no-op lock diff except
the bound is the ideal outcome.

**Verify**: `uv lock --locked` green; query-only install resolves 1.5.x.

### Step 2: Expiry trigger for the ignore

Convert the inline note into a tracked mechanism: open/identify the tracking
issue for "drop ignore when PSR relaxes click pin", reference it in the
comment, and add a dated review marker the repo will actually see (e.g. extend
the comment with `Review: <issue-url> + re-evaluate on every PSR bump via the
weekly python-dev dependabot group`). If PSR already relaxed the pin upstream,
drop the flag and this step becomes the removal (verify audit still green).

**Verify**: `uv run pip-audit` (without ignore, in scratch) shows ONLY the known advisory; with ignore, green.

### Step 3: Bandit sees extractors

Narrow `exclude_dirs` to non-source dirs (keep `tests`/`scripts`/`data` only if
triage says so — default: re-include `src/extractors`), run bandit, triage
each hit: fix real issues; annotate intentional patterns with `# nosec` +
one-line justification citing the review. No blanket `# nosec` file-skips.

**Verify**: bandit green over full `src/`; every `nosec` carries a reason (grep-proven).

## Test plan

- No pytest changes (config-only). If Step 3 fixes a real pattern, add the
  regression test next to the extractor's test class (then it escapes S scope
  — report and split).

## Done criteria

- [ ] `query` duckdb bound `>=1.5.5,<1.6`; lock green
- [ ] Ignore has issue link + review trigger (or is removed with evidence)
- [ ] Bandit covers `src/extractors`; all `nosec` justified
- [ ] `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Step 3 surfaces a REAL vulnerability (don't just `nosec` it — report immediately, split a fix plan).
- Bandit triage explodes (>~10 hits needing judgment) — timebox, report, split.
- PSR-bump/relock rewrites unrelated pins (scope the lock diff or report).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: scrutinize every `nosec` — that list is the audit trail.
- DuckDB 2.0 (Oct 2026) will force revisiting the `<1.6` cap — calendar note, not this plan.
- **Deferred:** nothing; this plan closes its three items.
