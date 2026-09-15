# Plan 100: Spike Polars `2.0rc1` en rama — golden-diff, sin prod

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- pyproject.toml uv.lock src/ tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (branch-only; production stays on 1.x regardless)
- **Depends on**: 092 (needs the payload/perf baseline stable first)
- **Category**: migration (spike — design evidence, NOT a bump)
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Polars 2.0 RC1 (2026-09-02, GA "in the following weeks") makes the streaming
engine the LazyFrame default: row order no longer guaranteed for
join/group_by/unpivot. That is silent-corruption shaped — exactly what §4.2
exists to prevent — and dependabot will propose the major bump with no
baseline unless this spike creates one. Production MUST stay on 1.x until GA +
green diff; this plan only produces the diff evidence + the fix list.

## Current state

- `pyproject.toml:38` — `polars>=1.41.2,<2`; lock at **1.41.2**; latest 1.x is
  1.44.1 (2026-08-26). Migration guide: `docs.pola.rs/releases/upgrade/2`;
  announcement: `pola.rs/posts/announcing-polars-2`.
- Production LazyFrame usage is narrow (verified 2026-09-15):
  - `mineduc_resultados_extractor.py:144` — aggregation + `.sort(["anio",
    "codigo_comuna"])` + `.collect()` (sort-then-collect: order-safe).
  - `res_extractor.py:137` — `pl.scan_csv(...).select("anio").unique().collect()`
    (single-column unique scan for year discovery).
  - No `melt(`/`with_row_count`/`LazyFrame.profile(`/`streaming=`/`join_nulls`
    in `src/` (only `def fetch` extractor-contract methods matched).
- Exposure is therefore behavioral (engine defaults, `read_csv`→scan dispatch,
  stricter `is_in`/concat/`str`-to-temporal rules), not removed-API usage —
  but eager `join`/`group_by`/`unpivot` order-dependence across
  `builders/`+`build_dev_db.py` (30 + 11 + 25 + … hits) still needs the
  golden-diff to prove safety.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| RC env | `pip install polars==2.0rc1` in a SCRATCH venv/branch env (never `.venv`) | declared | RC importable in scratch |
| Patch bump (prod, separate) | 1.41.2→1.44.1 inside `<2` | declared | suite green (pre-step) |
| Golden build | `make build` twice (1.44.1 vs 2.0rc1) + artifact diff | declared | diff recorded |
| Suite on RC | `./.venv-scratch/bin/pytest -q` (scratch env) | declared | result recorded whatever it is |

## Scope

**In scope**: scratch RC environment, double build + golden-diff of
`data/normalized/`, ordered fix-list (`maintain_order`/`.sort()` where diffs
are order-only), spike report committed as the plan's outcome (or a short
`docs/` note if the maintainer prefers — ask, don't invent a docs home).

**Out of scope**: changing `pyproject.toml`/`uv.lock` polars bounds; merging
any 2.x code to prod; fixing non-order RC breakages beyond listing them.

## Git workflow

- Branch: `advisor/100-polars2-spike` (NEVER merge to main; evidence only).
- Commits: pre-step (patch bump verification) + diff evidence + fix-list.
- Do NOT push or open a PR unless the operator instructed it. Do NOT touch prod bounds.

## Steps

### Step 0: Prod patch baseline (on the branch, still 1.x-safe)

Bump polars 1.41.2→1.44.1 within the `<2` cap in scratch, run full suite +
`make build` + record `data/normalized/` hashes. This is the control.
(If the maintainer wants the patch bump shipped separately, say so in the
report — the bump itself is trivially shippable, the RC is not.)

**Verify**: suite + `make verify` green on 1.44.1; hashes recorded.

### Step 1: RC double-build + golden-diff

In the scratch env with `polars==2.0rc1` (isolated from `.venv` — never
`uv sync` the RC into the project lockfile), run `make build`, diff every
artifact in `data/normalized/` against Step 0 (hashes first, then
value-level diff for mismatches: row counts, sort orders, dtypes — note the
RC's known dtype changes like exact-int division and renamed temporal outputs
per the migration guide). Classify each diff: order-only / dtype / values /
error.

**Verify**: classified diff table exists (empty table = strongest result).

### Step 2: Fix-list (no prod application)

For order-only diffs, record the precise `maintain_order=True` / explicit
`.sort()` insertion points (file:line). For dtype/value diffs, record
expected-behavior verdicts per the migration guide (accept vs adapt). For
errors (removed APIs), record replacements. Do NOT apply to prod files…
unless a fix is a pure no-op under 1.x AND covered by tests (e.g. adding an
explicit `.sort()` that 1.x already guaranteed) — those may ship as a
separate hardening commit at maintainer discretion; default is list-only.

**Verify**: every diff row has a disposition (accept/adapt/harden); hardening
candidates (if any) pass the suite on 1.44.1.

## Test plan

- No prod test changes by default. Hardening candidates (Step 2 exception)
  must come with order-assertion tests.
- The spike's deliverable is evidence, verified by the diff table's existence
  + reproducibility (commands recorded).

## Done criteria

- [ ] Control build (1.44.1) hashes recorded; suite green
- [ ] RC double-build diff table exists with every row dispositioned
- [ ] Fix-list with file:line insertion points (applied: none by default)
- [ ] Prod bounds (`pyproject`/`uv.lock`) untouched (grep-proven, no polars diff)
- [ ] Report recorded (plan file outcome section + `plans/README.md`/`ROADMAP.md` status)
- [ ] Branch never merged (stays evidence-only until GA)

## STOP conditions

- RC breaks the scratch environment itself (packaging issue, not our code) — record + stop, retry at GA.
- Value-level (non-order, non-guide-documented) diffs appear in published data — escalate to the maintainer immediately, do not "adapt" silently.
- Any temptation to bump prod bounds in this plan — STOP, that's a different decision owned by the maintainer at GA.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Re-run this spike at 2.0 GA (the RC is a preview; GA may differ).
- DuckDB 2.0 (Oct 2026) deserves the same spike treatment — separate plan when its RC lands.
- If dependabot opens the 2.x bump before GA review, link this spike report in that PR.
