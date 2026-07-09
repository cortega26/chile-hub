# Plan 031: Make the `load_polars` Parquet cache actually cache on the default path

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/chile_hub/core.py`
> If the file changed since this plan was written, locate the guard by content
> (the string `if not validate or dataset_name not in self._df_cache:`) rather
> than by line number, and compare against the excerpt below; on a real mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (coordinate line numbers with Plan 029 if both touch `load_polars`)
- **Category**: perf
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`ChileHub._df_cache` exists to avoid re‑reading Parquet on repeated `load_polars` /
`cross_view` calls, but its guard is inverted so the cache is **dead on the default path**.
The guard is `if not validate or dataset_name not in self._df_cache:` — when `validate=False`
(the default), `not validate` is always `True`, so the branch always runs, always re‑reads the
Parquet from disk, and overwrites the cache. The cache only ever short‑circuits when
`validate=True` **and** the dataset is already cached. So every ordinary `load_polars("comunas")`
and every `cross_view` join re‑reads from disk — the memoization the prior audit added never helps
the hot path. Output is correct; this is pure wasted I/O.

## Current state

`src/chile_hub/core.py`, `load_polars` (guard at line 316):

```python
    def load_polars(self, dataset_name: str | Dataset, validate: bool = False) -> pl.DataFrame:
        dataset_name = _resolve_dataset_name(dataset_name)
        """... docstring ..."""
        if not validate or dataset_name not in self._df_cache:
            path = self.get_output_path(dataset_name, "parquet")
            try:
                df = pl.read_parquet(path)
            except FileNotFoundError:
                raise ChileHubDatasetError(...)
            except Exception as exc:
                raise ChileHubDatasetError(...)
            self._df_cache[dataset_name] = df

        if validate:
            result = self.validate_dataset(dataset_name)
            if result["status"] == "error":
                raise ChileHubDataError(...)

        return self._df_cache[dataset_name]
```

`self._df_cache` is an instance dict initialized in `__init__` (a plain `dict[str, pl.DataFrame]`).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| API tests (need built data) | `make build && .venv/bin/python -m pytest tests/test_chile_hub.py tests/test_core.py -q` | all pass |
| Cache behavior test | (added in Step 2) | pass |

## Scope

**In scope**:
- `src/chile_hub/core.py` (the `load_polars` read guard only)
- `tests/test_core.py` or `tests/test_chile_hub.py` (add a cache test)

**Out of scope**:
- The `validate=True` validation block — keep it exactly as is (validation must still run every time
  the caller asks for it).
- Converting `_df_cache` to `functools.cached_property` or adding invalidation — not needed; a plain
  read‑once dict is correct for the read‑only, single‑process CLI/library lifetime.
- The misplaced docstring in this same method — that is Plan 029. If Plan 029 already landed, the
  docstring is above the `_resolve_dataset_name` line; either order is fine for this change.

## Git workflow

- Branch: `advisor/031-load-polars-cache`
- Conventional commit, e.g. `perf(api): cachea Parquet en load_polars también en la ruta por defecto`.

## Steps

### Step 1: Fix the read guard

Change the read condition so it caches on **both** paths (read once, then reuse), while leaving the
`if validate:` block untouched:

```python
        if dataset_name not in self._df_cache:
            path = self.get_output_path(dataset_name, "parquet")
            try:
                df = pl.read_parquet(path)
            except FileNotFoundError:
                raise ChileHubDatasetError(
                    f"Archivo Parquet no encontrado para '{dataset_name}': {path}"
                )
            except Exception as exc:
                raise ChileHubDatasetError(f"Error al leer Parquet para '{dataset_name}': {exc}")
            self._df_cache[dataset_name] = df

        if validate:
            result = self.validate_dataset(dataset_name)
            if result["status"] == "error":
                raise ChileHubDataError(
                    f"Validación fallida para '{dataset_name}': {'; '.join(result['errors'])}"
                )

        return self._df_cache[dataset_name]
```

**Verify**: `grep -n "if not validate or dataset_name not in self._df_cache" src/chile_hub/core.py` → no matches.

### Step 2: Add a test proving the cache serves the default path

In `tests/test_core.py` (or wherever `ChileHub` load tests live), add a test that:
- constructs a `ChileHub`, calls `load_polars("comunas")` once,
- patches `polars.read_parquet` (or `pl.read_parquet` as imported in `core.py`) with a
  `unittest.mock.patch` that raises if called,
- calls `load_polars("comunas")` again and asserts it returns the cached frame **without** calling
  `read_parquet` again.

Also assert that the returned frames are the same object (`is`) across two default calls.

**Verify**: `.venv/bin/python -m pytest tests/test_core.py -q -k "cache or load_polars"` → passes.

### Step 3: Confirm the full suite

**Verify**: `make build && .venv/bin/python -m pytest tests/test_chile_hub.py tests/test_core.py -q` → all pass.
(`test_chile_hub.py` requires `data/normalized/`, hence `make build` first. If no build env, run at least
`tests/test_core.py` and note the limitation.)

## Test plan

- New test (Step 2): second `load_polars` on the default path does not re‑read Parquet; returns the same object.
- Pattern: existing `ChileHub` construction in `tests/test_core.py`.
- Verification: pytest commands above.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "if not validate or" src/chile_hub/core.py` → no matches
- [ ] The Step‑2 cache test exists and passes (proves no second `read_parquet` on default path)
- [ ] `.venv/bin/python -m pytest tests/test_core.py -q` exits 0
- [ ] `make lint` and `make format-check` exit 0
- [ ] Only `src/chile_hub/core.py` (+ the test file) modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- Any existing test asserts that `load_polars` returns a **fresh** read each call (i.e. relies on the
  current no‑op behavior) — that would be a deliberate contract; report before changing.
- `_df_cache` is not an instance‑level dict (e.g. it's class‑level or an lru_cache) — the fix differs; report.

## Maintenance notes

- The cache is never invalidated, which is correct for the process‑lifetime, read‑only usage. If a future
  feature mutates artifacts in‑process (unlikely), revisit.
- Reviewer should confirm `cross_view` (which calls `load_polars`) benefits — repeated joins over the same
  datasets no longer re‑read Parquet.
