# Plan 090: Una sola conversión `to_pandas()` + descarte pre-conversión

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/builders/formats.py src/build_dev_db.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

`build_sqlite` and `build_excel` each reconvert the 7 base tables with
`to_pandas()` (2× CPU/RAM peak), while `extra_tables_pd` is already converted
once in `build_dev_db.py:744` and shared. Worse, the massive-table skip
(`empresas` ~1.57M rows) is decided by `len(df_extra)` AFTER paying the
conversion — `empresas` gets converted to pandas just to be discarded by
SQLite/Excel. This feeds the `build-and-test` job's OOM/timeout risk.

## Current state

- `src/builders/formats.py:100-108` (`build_sqlite`) and `:194-202`
  (`build_excel`): 7× `df_*.to_pandas()` each, unconditionally.
- `:107-108` / `:201-202`: `if extra_tables_pd is None: extra_tables_pd =
  {name: df.to_pandas() ...}` — the sharing pattern already exists for extras.
- `src/build_dev_db.py:742-744`: converts extras once with the comment
  "Empresas tiene ~1.57M filas: la conversión es costosa y no debe duplicarse"
  — then passes them to both builders. Base tables get no such treatment.
- Skip thresholds AFTER conversion: `:128-138` (SQLite 500k) and `:221-229`
  (Excel 500k). Note flat-files already check `df_extra.height` (Polars, no
  conversion) at `:370-371` — that is the pattern to copy.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Build smoke | `make build` | declared | exit 0 |
| Verify dev | `make verify` | declared | exit 0 |
| Focal tests | `./.venv/bin/pytest tests/test_builders_artifacts.py tests/test_builders_formats.py -q` | declared | all pass |

## Scope

**In scope**: `src/builders/formats.py` (share base frames, pre-conversion size
filter), `src/build_dev_db.py` (build `base_tables_pd` once, pass it down).

**Out of scope**: parallelizing formats (Plan 092), changing skip thresholds,
changing the Excel sheet-splitting logic, touching DuckDB/Parquet paths.

## Git workflow

- Branch: `advisor/090-single-pandas-conversion`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

`make build` + `make verify` unmodified take a while; if a full build is
impractical in this environment, run the focal tests + record artifact hashes
(`sha256sum data/normalized/chile_data.db data/normalized/chile_data_latest.xlsx`)
as the equivalence baseline instead.

**Verify**: chosen baseline is green/recorded before edits.

### Step 1: Size filter before conversion (extras)

In both builders, decide skip/include from `extra_tables` (Polars `.height`,
no conversion) BEFORE building `extra_tables_pd`; only convert included
tables. Keep thresholds and messages byte-identical.

**Verify**: focal tests pass.

### Step 2: Share base-table pandas frames

Build the 7 base pandas frames once in `_write_data_artifacts`
(`build_dev_db.py`, next to `:744`), pass as `base_tables_pd` to
`build_sqlite`/`build_excel` (same optional-param pattern as
`extra_tables_pd=None` default so direct callers/tests keep working), and
delete the duplicate conversions inside both builders.

**Verify**: focal tests pass; `grep -n "to_pandas()" src/builders/formats.py`
shows conversions only behind the `is None` fallback + the single shared path.

### Step 3: Byte-equivalence

Re-run the Step 0 baseline: same `make verify`, and `sha256sum` of
`chile_data.db`/`chile_data_latest.xlsx` matches (timestamps inside SQLite may
differ — if hashes differ, compare dumps: table list, row counts, and spot
`SELECT` checksums instead; document which comparison was used).

**Verify**: equivalence demonstrated by the recorded method.

## Test plan

- Existing: `test_builders_artifacts.py`, `test_builders_formats.py` (golden round-trips).
- New (only if cheap): a test that `build_sqlite`/`build_excel` skip a >500k synthetic extra WITHOUT converting it (e.g. assert via mock on `to_pandas` or timing-independent call count). If the builders' signatures make this awkward, skip the new test and rely on Step 3 equivalence — say so in the commit.

## Done criteria

- [ ] No unconditional double conversion of the 7 base tables (one shared build)
- [ ] Skip decisions precede conversion (no converting a table that gets skipped)
- [ ] Equivalence with baseline demonstrated (hashes or dump comparison, documented)
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Hash/dump comparison shows data differences (not just timestamps) — report, don't "fix" by adjusting thresholds.
- A direct caller of `build_sqlite`/`build_excel` (test or script) breaks on the new param — keep backward-compatible default (`None` → convert inside) rather than refactoring callers.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: confirm thresholds/messages unchanged (behavioral no-op except memory/time).
- Future format additions must take frames from the shared dict, not convert again — note it in the commit message.
- **Deferred:** process-level parallelization of formats (Plan 092).
