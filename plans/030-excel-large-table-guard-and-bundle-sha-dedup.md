# Plan 030: Guard the Excel builder against oversized tables (and dedup the bundle SHA‑256)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/builders/formats.py src/builders/artifacts.py src/build_dev_db.py`
> If any in-scope file changed since this plan was written, compare the "Current
> state" excerpts against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`build_excel` writes **every** extra table via pure‑Python XlsxWriter, splitting tables
larger than Excel's per‑sheet limit (1,048,576 rows) across multiple sheets. The `empresas`
dataset is ~1.57M rows, so each build spends minutes of CPU and large peak RAM serializing it
across two sheets — into a consolidated `chile_data_latest.xlsx` that (a) no one can practically
open at that size and (b) isn't even a published artifact (the bundle only ships
`.json/.md/.parquet`). The SQLite builder already skips tables over 500k rows, and the JSON
builder skips over 100k — Excel is the only serializer with **no skip guard**. This is the
single cheapest build‑time win.

Step 3 (optional) also removes a redundant second SHA‑256 hash of the whole publishable bundle.

## Current state

`src/builders/formats.py`:

- SQLite already guards large tables (lines 126‑138):
  ```python
  _SQLITE_MAX_ROWS = 500_000
  _SQLITE_MAX_VARS = 999
  for table_name, df_extra in extra_tables_pd.items():
      num_rows = len(df_extra)
      if num_rows > _SQLITE_MAX_ROWS:
          print(f"  Omite SQLite para {table_name} ({num_rows:,} filas > {_SQLITE_MAX_ROWS:,}) — usa DuckDB o Parquet.", flush=True)
          continue
  ```
- `build_excel` has **no** such guard — it only splits (lines 218‑244):
  ```python
  for table_name, df_extra in extra_tables_pd.items():
      base_sheet = DATASET_CATALOG_CONFIG[table_name]["outputs"].get("excel_sheet", table_name[:31])[:31]
      num_rows = len(df_extra)
      if num_rows <= EXCEL_MAX_ROWS:
          df_extra.to_excel(writer, sheet_name=base_sheet, index=False)
          ...
      else:
          # split into ceil(num_rows / EXCEL_MAX_ROWS) sheets
          ...
  ```
- `EXCEL_MAX_ROWS = 1_048_576` is imported from `src/builders/_shared.py:38`.

`src/builders/artifacts.py` + `src/build_dev_db.py` (Step 3 only):

- `write_publishable_bundle_sha256(zip_path)` computes `compute_sha256(zip_path)` (artifacts.py:412) and returns the sha256 file path.
- `attach_publishable_package_to_manifest(zip_path, sha256_path, manifest=None)` computes `compute_sha256(zip_path)` **again** (artifacts.py:433).
- Both are called back‑to‑back on the same zip (`build_dev_db.py:804‑808`):
  ```python
  zip_output = write_publishable_bundle_zip()
  sha256_output = write_publishable_bundle_sha256(zip_output)
  artifact_manifest_output, artifact_manifest = attach_publishable_package_to_manifest(
      zip_output, sha256_output, artifact_manifest
  )
  ```

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Builder tests | `.venv/bin/python -m pytest tests/test_pipeline_logic.py -q` | all pass |
| Full build (requires staging inputs) | `make build` | exit 0; prints the "Omite Excel" notice for `empresas` |

## Scope

**In scope**:
- `src/builders/formats.py`
- `src/builders/artifacts.py` (Step 3 only)
- `src/build_dev_db.py` (Step 3 only)
- `tests/test_pipeline_logic.py` (add a guard test)

**Out of scope**:
- Switching ZIP compression to `ZIP_STORED` — that changes published bundle bytes and every
  downstream consumer's checksum; not in this plan.
- The SQLite/JSON guards — they already work; do not change their thresholds.

## Git workflow

- Branch: `advisor/030-excel-guard`
- Conventional commit, e.g. `perf(build): omite Excel para tablas masivas y evita doble hash del bundle`.

## Steps

### Step 1: Add a large‑table skip to `build_excel`

At the top of the `for table_name, df_extra in extra_tables_pd.items():` loop in `build_excel`,
add a skip that mirrors the SQLite guard (choose 500k to match SQLite):

```python
        _EXCEL_MAX_ROWS_SKIP = 500_000
        num_rows = len(df_extra)
        if num_rows > _EXCEL_MAX_ROWS_SKIP:
            print(
                f"  Omite Excel para {table_name} ({num_rows:,} filas > "
                f"{_EXCEL_MAX_ROWS_SKIP:,}) — usa DuckDB o Parquet.",
                flush=True,
            )
            continue
```

Place it before the `base_sheet = ...` lookup so skipped tables never touch XlsxWriter. Keep the
existing `<= EXCEL_MAX_ROWS` split logic for mid‑sized tables (it's now only reachable for tables
between the skip threshold and the physical limit — harmless).

**Verify**: `make lint` → exit 0.

### Step 2: Add a guard test

In `tests/test_pipeline_logic.py`, add a test that builds two small pandas DataFrames (one with
2 rows, one you monkeypatch/construct to report >500k rows without allocating 500k — e.g. patch
`len()` via a thin wrapper, or pass a real 3‑row frame and lower the threshold is not possible since
it's a local constant; instead assert on the printed notice or on which sheets exist). The robust
approach: call `build_excel` with a tiny `extra_tables_pd` where one entry is a DataFrame you wrap so
`len()` returns a large number, write to a temp `.xlsx`, then reopen with `openpyxl` and assert the
oversized table's sheet is **absent** while a small table's sheet is present.

If wrapping `len()` is awkward in this codebase, instead add a focused unit test on the decision by
extracting the threshold check is not required — a simpler acceptance is the `make build` notice
(Step 4). Prefer a real assertion if feasible; otherwise document why.

**Verify**: `.venv/bin/python -m pytest tests/test_pipeline_logic.py -q` → all pass.

### Step 3 (optional, do only if Step‑1 done and time allows): compute the bundle SHA‑256 once

Make `attach_publishable_package_to_manifest` accept an already‑computed digest, and pass it from
`build_dev_db` so the bundle is hashed once instead of twice.

1. `grep -rn "write_publishable_bundle_sha256\|attach_publishable_package_to_manifest" src/ scripts/ tests/`
   to enumerate all callers. If either is called from more than the one `build_dev_db` site + tests,
   keep the change backward‑compatible (default parameter).
2. In `artifacts.py`, change the signature to
   `def attach_publishable_package_to_manifest(zip_path, sha256_path, manifest=None, sha256=None):`
   and use `sha256 = sha256 or compute_sha256(zip_path)` instead of the unconditional recompute.
3. In `build_dev_db.py`, compute once and pass it:
   ```python
   from src.builders.artifacts import compute_sha256  # if not already imported
   zip_output = write_publishable_bundle_zip()
   bundle_sha256 = compute_sha256(zip_output)
   sha256_output = write_publishable_bundle_sha256(zip_output)  # unchanged
   artifact_manifest_output, artifact_manifest = attach_publishable_package_to_manifest(
       zip_output, sha256_output, artifact_manifest, sha256=bundle_sha256
   )
   ```
   (Optionally also give `write_publishable_bundle_sha256` an optional `sha256=None` param and pass
   `bundle_sha256` to it too, so the zip is hashed exactly once total.)

**Verify**: `make build` still produces an identical `chile-hub-publishable-bundle.zip.sha256`
content vs before (the digest value must not change — only how many times it's computed).

### Step 4: Confirm the build

**Verify**: `make build` → exit 0 and the log shows `Omite Excel para empresas (... filas > 500,000)`.
(If staging inputs aren't present, run the extractors first per the repo's `make extract`, or STOP and
report that a build environment is required.)

## Test plan

- New guard test (Step 2): oversized table is skipped from the Excel workbook; small table is present.
- Pattern: the SQLite guard's behavior and any existing `build_*` tests in `tests/test_pipeline_logic.py`.
- Verification: pytest + `make build` notice.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "Omite Excel" src/builders/formats.py` shows the new skip
- [ ] `.venv/bin/python -m pytest tests/test_pipeline_logic.py -q` exits 0 (incl. new test)
- [ ] `make build` exits 0 and logs the Excel skip for `empresas` (if a build env is available)
- [ ] If Step 3 done: the `.zip.sha256` file content is byte‑identical to a pre‑change build
- [ ] `make lint` and `make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- A consumer/test asserts that `empresas` (or any >500k table) has an Excel sheet — surfacing that
  means someone relies on the behavior; report before changing.
- Step 3: `write_publishable_bundle_sha256`/`attach_...` are called in ways that make a
  backward‑compatible change impossible.
- No build environment is available to run `make build` — do Steps 1‑2 and note that Step 4 could
  not be exercised.

## Maintenance notes

- If Excel of large tables is ever genuinely wanted, use XlsxWriter's `constant_memory` mode rather than
  removing the guard.
- The `ZIP_STORED`/`compresslevel` optimization (avoid re‑deflating already‑compressed Parquet) was
  deliberately left out because it changes published bytes; consider it only alongside a checksum‑rotation
  communication to consumers.
