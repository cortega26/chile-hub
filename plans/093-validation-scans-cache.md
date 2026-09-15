# Plan 093: Scans O(K·N)→`partition_by` + allowlist única + cache acotado

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/validation.py src/build_dev_db.py src/builders/datasets.py src/chile_hub/core.py tests/test_validation.py tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Three local inefficiencies compound on every build/run: anomaly detection
scans the full frame once per indicator key O(K·N); `_compute_validations`
copies the comunas code column via `to_list()` ~15 times; long-lived API
processes cache every loaded frame forever (`empresas` + `cross_view` →
unbounded growth toward OOM).

## Current state

- `src/validation.py:352-353`:
  ```python
  for key in df[key_col].unique().sort().to_list():
      series = df.filter(pl.col(key_col) == key).sort(date_col)
  ```
  One full scan per `codigo_indicador`.
- `src/build_dev_db.py:567-679` — `df_comunas["codigo_comuna"].to_list()`
  repeated at ~every validator call site (salud, censo_hogares, electoral,
  educacionales, finanzas, resultados, siedu, empresas, pobreza, consumo,
  autoridades, vitales, permisos, calidad).
- `src/builders/datasets.py:76-79` — `_latest_calidad_summary` derives `anio`
  via `str.slice(0,4).cast(Int64)` over full calidad history each build.
- `src/chile_hub/core.py:88,268-279,315-324` — `self._df_cache: dict[str,
  pl.DataFrame]`, unbounded; `load_polars` caches forever, `cross_view`
  compounds via repeated `load_polars`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Focal tests | `./.venv/bin/pytest tests/test_validation.py tests/test_pipeline_logic.py -q` | declared | all pass |
| Core tests | `./.venv/bin/pytest tests/test_core.py -q` | declared | all pass (needs `make build` first) |
| Lint | `make lint` | declared | exit 0 |

## Scope

**In scope**: `detect_series_anomalies` iteration, single `frozenset`
allowlist, persisted `anio` column, bounded `_df_cache`.

**Out of scope**: changing anomaly math/thresholds (Plan 074 territory);
changing cache *semantics* (still cache, just bounded); `cross_view` API shape.

## Git workflow

- Branch: `advisor/093-validation-scans-cache`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline (no changes)

Focal tests green unmodified. Optionally time `detect_series_anomalies` on the
real `indicadores` frame for the commit message (nice-to-have, not required).

**Verify**: focal tests exit 0.

### Step 1: `partition_by` in anomaly detection

Replace the unique+filter loop with `df.partition_by(key_col,
maintain_order=True)` (or `group_by` + per-group sort), preserving the exact
per-series order the math assumes (sorted by `date_col`) and identical output
(anomaly list equality on a fixture with ≥2 keys, incl. constant series and
the Plan 074 non-positive-tail path at `validation.py:405+`).

**Verify**: existing anomaly tests pass unmodified (they encode the math);
add a multi-key equivalence test if none covers ≥2 series.

### Step 2: One allowlist

Compute `valid_codes = frozenset(df_comunas["codigo_comuna"].to_list())` once
in `_compute_validations` and pass it to every `validate_*` call. Validator
signatures take `list[str] | None` — a frozenset is NOT a list; either keep
passing a list built once, or widen the annotation honestly and check each
validator's use (`in` checks are fine; indexing is not — grep before widening).

**Verify**: `grep -c 'df_comunas\["codigo_comuna"\].to_list()' src/build_dev_db.py` → 1; focal tests pass.

### Step 3: Persist `anio` + bound the cache

- Calidad/vitales staging: persist an `anio` Int column at build/extraction so
  `_latest_calidad_summary` stops deriving it per build (backfill for existing
  staging: derive once if absent — never break on old staging files).
- `core.py`: bound `_df_cache` (`functools.lru_cache`-style `maxsize` or
  explicit invalidation method; smallest diff that caps growth; document the
  eviction policy in the `load_polars` docstring).

**Verify**: core tests + focal tests pass; a test loads N>maxsize datasets and
asserts cache size stays capped while last-loaded data stays correct.

## Test plan

- Equivalence tests (Step 1 multi-key; Step 2 unchanged validator outputs).
- New: cache-cap test (Step 3); `anio` backfill test (old staging without column still builds).
- Pattern: `tests/test_validation.py` edge cases + `tests/test_pipeline_logic.py`.

## Done criteria

- [ ] No per-key full-frame scans in `detect_series_anomalies`
- [ ] Single allowlist construction in `_compute_validations`
- [ ] `_df_cache` bounded with documented policy + test
- [ ] Focal + core tests and `make lint` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- `partition_by` changes anomaly output on any existing fixture (math must be byte-identical in behavior — report, don't "adjust" thresholds).
- Widening the allowlist type breaks a validator's internal use (keep `list`, built once).
- Eviction policy breaks `cross_view` chaining in tests (then choose invalidation-over-eviction and report).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: confirm per-series date ordering is still guaranteed after Step 1 (the z-math is order-sensitive).
- Future validators must take the shared allowlist param — note in commit message.
- **Deferred:** general frame-lifecycle policy for the API (bigger than a cache cap).
