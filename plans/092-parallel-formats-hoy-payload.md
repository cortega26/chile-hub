# Plan 092: Paralelizar formatos + `indicadores_hoy` = última fecha

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/build_dev_db.py src/builders/formats.py tests/test_builders_artifacts.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: 090 (same `formats.py` + shared-frames work; do not conflict)
- **Category**: perf
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Build wall-time is the sum of 4 sequential formats (SQLite multi-insert +
Excel XlsxWriter dominate), and `indicadores_hoy.json` ships the FULL history
since 2010 (`to_dicts()` of everything) under a name promising "today" — MBs
to a frontend needing one date, plus RAM spikes from duplicated Polars →
list-of-dicts → JSON-string materializations.

## Current state

- `src/build_dev_db.py:746-796` — `build_duckdb` → `build_sqlite` →
  `build_excel` → `build_flat_files` sequential with `1/4..4/4` logs; after
  090, base/extras pandas frames are shared dicts (read-only downstream).
- `src/builders/formats.py:343-348`:
  ```python
  df_indicadores_serializable = df_indicadores.with_columns(pl.col("fecha").cast(pl.String))
  ...
  write_json_atomic(df_indicadores_serializable.to_dicts(), indicadores_json, ...)
  ```
  Full history despite the `indicadores_hoy` name.
- `:370-382` — each extra JSON materializes `df_extra.to_dicts()` fully before
  writing (already skipped when >100k rows at `:369-377`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline timing | `time make build` (or report-phase subset) | declared | record wall-time BEFORE changes |
| Verify dev | `make verify` | declared | exit 0 |
| Focal tests | `./.venv/bin/pytest tests/test_builders_artifacts.py -q` | declared | all pass |

## Scope

**In scope**: `build_flat_files` hoy-payload + streaming/chunked JSON writes;
process-based parallelization of the format stage in `build_dev_db.py`.

**Out of scope**: changing skip thresholds (090 territory); consumer contract
changes beyond the hoy-payload fix (coordinate: anything reading
`indicadores_hoy.json` — landing/`app.js` — must be checked); GIL-thread
parallelism (will not help `to_pandas`/XlsxWriter — processes or nothing).

## Git workflow

- Branch: `advisor/092-parallel-formats-hoy-payload`
- Commit por step (payload fix separate from parallelization); conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline timing + consumer map (no code changes)

Time the build (or at least the 4 format calls) unmodified; grep consumers of
`indicadores_hoy.json` (`app.js`, `index.html`, docs, notebooks). Record both
in the commit message.

**Verify**: numbers + consumer list written down; focal tests green.

### Step 1: `indicadores_hoy` = max(fecha) (+ chunked writes)

Filter `df_indicadores` to `fecha == max(fecha)` before serializing (keep the
`.cast(pl.String)`); write large JSONs via `iter_batches`/`sink_ndjson`-style
chunking instead of one giant `to_dicts()` where the writer helper allows it
without changing output bytes (if bytes would change, keep `to_dicts()` and
only do the filter — say so in the commit). Update any consumer found in
Step 0 that depended on full history (if one exists and needs history, STOP —
that changes scope).

**Verify**: `indicadores_hoy.json` row count == distinct codes × 1 date; `make verify` green.

### Step 2: Parallelize formats by process (measure first)

Only after Step 1: launch DuckDB+Parquet and SQLite+Excel in two separate
process workers reading the same immutable shared frames
(`multiprocessing`/`concurrent.futures.ProcessPoolExecutor`; NOT threads —
GIL). Keep `1/4..4/4` logging coherent (log from parent on completion).
Compare wall-time vs Step 0 on the same machine. If speedup < ~20% or memory
doubles unacceptably (frames get pickled per worker — measure peak RSS), STOP
and keep the serial version: report numbers, close the plan as
"measured, not worth it".

**Verify**: wall-time improvement recorded; `make verify` green; artifact
equivalence per 090's method (hashes or dump comparison).

## Test plan

- Existing: `test_builders_artifacts.py` (manifest↔ZIP consistency), `make verify`.
- New: hoy-payload test (max-date only) in the builders-artifacts-adjacent test file.
- Equivalence: same method as Plan 090 Step 3.

## Done criteria

- [ ] `indicadores_hoy.json` contains only the latest `fecha` (proven by row-count/date query)
- [ ] Parallelization decision backed by measured numbers (shipped or explicitly rejected with data)
- [ ] `make verify` + focal tests green; artifacts equivalent
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- A consumer needs full history from `indicadores_hoy.json` (scope change — report).
- Parallel speedup insufficient or RSS unacceptable (revert to serial, report numbers — still a DONE with evidence).
- Atomic-write helpers (`write_*_atomic`, `.tmp` + `os.replace` in `:95-97,177`) don't compose with workers — don't redesign them; report.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: check no format writes to the same path from two workers; tmp+replace must stay per-format.
- If DuckDB 2.0 (Oct 2026) changes write behavior, re-measure Step 2.
- **Deferred:** incremental builds (rejected 2026-08-12 for lack of telemetry; Step 0 timings are the telemetry that could reopen it).
