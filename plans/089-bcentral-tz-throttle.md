# Plan 089: bcentral — fechas a UTC y throttle real en fetch concurrente

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/extractors/bcentral_extractor.py tests/test_extractors.py`
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

Two small defects in the highest-churn extractor: (1) year/today computed in
the runner's local TZ while everything else uses UTC — near midnight CLT vs
UTC the incremental slice (`years_to_fetch=[current_year]`) targets the wrong
year (needless re-fetch or a one-year hole + misattributed backfills); (2) the
courtesy `sleep` runs inside ThreadPoolExecutor workers, so N workers sleep in
parallel — it lengthens wall-time without spacing requests to mindicador.cl.

## Current state

- `src/extractors/bcentral_extractor.py:230` —
  `return df, datetime.date.today().year, published_backfills`
- `:247` — `current_year = datetime.date.today().year`
- `:434` — `today = datetime.date.today()` (confirm exact use at read time)
- Contrast: `:143` uses `datetime.datetime.now(UTC)`, as do
  `subdere_extractor.py:406` and `builders/metadata.py:634`.
- `:307-313`:
  ```python
  # Espera de cortesía idéntica a la serial, solapada entre hilos.
  time.sleep(REQUEST_DELAY_SECONDS)
  return outcome
  ...
  with concurrent.futures.ThreadPoolExecutor(max_workers=MINDICADOR_MAX_WORKERS) as pool:
  ```
  The comment itself admits the sleep overlaps across threads.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Focal tests | `./.venv/bin/pytest tests/test_extractors.py -q -k "bcentral or indicador or mindicador"` | declared | all pass |
| Full extractor suite | `./.venv/bin/pytest tests/test_extractors.py -q` | declared | all pass |
| Lint | `make lint` | declared | exit 0 |

## Scope

**In scope**: `src/extractors/bcentral_extractor.py` (3 date sites + throttle) and
`tests/test_extractors.py` (regression tests).

**Out of scope**: changing fetch semantics, retry policy (`http_utils.py`),
`MINDICADOR_MAX_WORKERS`/`REQUEST_DELAY_SECONDS` values, or other extractors'
date handling.

## Git workflow

- Branch: `advisor/089-bcentral-tz-throttle`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run focal tests unmodified.

**Verify**: exit 0 before any edit.

### Step 1: UTC dates

Replace the three `datetime.date.today()` uses with the UTC equivalent used
elsewhere (`datetime.datetime.now(UTC).date()` / `.year`). Check the file's
existing `UTC` import (if it imports `datetime` module vs names, match file
convention — `:143` already uses `datetime.datetime.now(UTC)`).

**Verify**: `grep -n "date.today()" src/extractors/bcentral_extractor.py` → no matches; focal tests pass.

### Step 2: Real throttle

Replace the in-worker `time.sleep(REQUEST_DELAY_SECONDS)` with spacing that
actually serializes submissions: e.g. a shared `threading.Semaphore(1)` +
sleep outside the pool, or pace `pool.submit` calls with the delay between
submits (keep `pool.map` order-preservation for the byte-identical fold noted
in `:271-276,311-313`). Do NOT change `max_workers` or the outcome-fold logic.
Add a test asserting inter-request spacing (mock `fetch_indicator_year` +
record call timestamps; assert min gap ≈ `REQUEST_DELAY_SECONDS` modulo
scheduling jitter — use a tolerant bound, not exact equality).

**Verify**: focal tests pass; new spacing test passes and fails if the sleep is moved back inside the worker (sanity-check by reverting in scratch).

## Test plan

- New: UTC-year boundary test (freeze time near midnight UTC±CLT offset if the suite has freeze tooling; otherwise assert `datetime.now(UTC)` is the source via mock), throttle-spacing test.
- Existing bcentral tests stay green; then full `test_extractors.py`.

## Done criteria

- [ ] No `date.today()` left in `bcentral_extractor.py`
- [ ] Courtesy delay spaces submissions (proven by the new test, tolerant bound)
- [ ] `./.venv/bin/pytest tests/test_extractors.py -q` exits 0, `make lint` exits 0
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- `:434`'s `today` feeds logic where local-TZ is load-bearing (then keep it, document why, and still fix `:230/:247`).
- Pacing submits breaks the order-preserving fold (`pool.map` semantics) — report instead of redesigning the fold.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: the spacing bound must be tolerant (CI runners are noisy); exact-timing asserts are flaky by construction.
- **Deferred:** sharing one throttle helper across extractors (`http_utils.py`) — needs a second extractor with the same pattern; don't generalize from one.
