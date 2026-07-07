# Plan 036: Golden‑output tests for the artifact writers (`builders/formats.py` + `builders/artifacts.py`)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/builders/formats.py src/builders/artifacts.py`
> If either changed, re‑read the target functions' signatures before writing tests.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none (pairs well after 030, which adds the Excel guard these tests can assert)
- **Category**: tests
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`src/builders/formats.py` (line 4.7% coverage, 0% branch) and `src/builders/artifacts.py` (~20%)
are the code that produces **every published artifact**: Parquet, DuckDB, SQLite, Excel, the flat
JSON files, the downloadable zip, its SHA‑256 integrity file, and the manifest that lists what's
published. A regression here (wrong column, wrong dtype, truncated table, mismatched/missing SHA‑256,
a manifest referencing a file not in the zip) ships corrupt data with **no test to catch it**. These
are pure functions over DataFrames writing to disk, so golden round‑trip tests (write → reopen →
assert) are cheap and high‑value.

## Current state

`src/builders/formats.py` — writers (all near‑0% covered):
- `build_duckdb(...)` (line 17) — registers Polars frames and `CREATE TABLE AS SELECT`.
- `build_sqlite(...)` (line ~82) — `.to_pandas().to_sql(...)`, skips tables > 500k rows.
- `build_excel(...)` (line ~180) — XlsxWriter; (after Plan 030) skips tables > 500k rows.
- `build_flat_files(...)` (line ~296) — writes each published `*.parquet` and JSON via
  `write_parquet_atomic` / `write_json_atomic` (from `src/builders/io_utils.py`).

`src/builders/artifacts.py` — bundle/manifest (near‑0% covered):
- `write_publishable_bundle_zip()` (line 369) — builds the zip; runs `testzip()` and a namelist count check.
- `write_publishable_bundle_sha256(zip_path)` (line 409) — writes `<sha256>  data/normalized/<zip>` file.
- `attach_publishable_package_to_manifest(zip_path, sha256_path, manifest=None)` (line 420) — records
  size/sha256/checksum_path in `manifest["packages"]`.
- `compute_sha256(...)` helper (used by both).

Existing tests: `tests/test_pipeline_logic.py` and `tests/test_data_package.py` cover adjacent logic;
`tests/test_data_package.py` is the closest structural pattern for a build‑artifact round‑trip.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Inspect signatures | `grep -nE "^def build_|^def write_|^def compute_" src/builders/formats.py src/builders/artifacts.py` | exact params |
| Run new tests | `.venv/bin/python -m pytest tests/test_builders_formats.py tests/test_builders_artifacts.py -q` | all pass |
| Coverage of writers | `.venv/bin/python -m pytest --cov=src.builders.formats --cov=src.builders.artifacts -q` | both rise substantially |
| Lint / format | `make lint && make format-check` | exit 0 |

## Scope

**In scope**:
- `tests/test_builders_formats.py` (create)
- `tests/test_builders_artifacts.py` (create)

**Out of scope**:
- Changing `formats.py` / `artifacts.py` behavior. If a test reveals a bug, STOP and report it.
- Excel large‑table skip logic — that's Plan 030 (assert it here only if 030 has landed).

## Git workflow

- Branch: `advisor/036-artifact-writer-tests`
- Conventional commit, e.g. `test(builders): golden round‑trip para writers de formatos y bundle`.

## Steps

### Step 1: Confirm the writer signatures

Run the `grep` above and read each target function's parameter list so the fixtures pass exactly what
each writer expects (the `build_*` functions take specific base DataFrames plus an `extra_tables`/
`extra_tables_pd` mapping and an output path). Build a tiny fixture: 2–3 row Polars DataFrames for
`regiones`, `provincias`, `comunas`, `indicadores`, `censo`, `salud`, `educacionales`, plus one small
"extra" table, all with the canonical columns/dtypes.

### Step 2: `formats.py` round‑trip tests (`tests/test_builders_formats.py`)

- `build_flat_files` → reopen each written `*.parquet` with `pl.read_parquet` and assert columns, dtypes
  (CUT codes are `String`!), and row counts match the fixture; assert no `*.tmp` files remain (atomic writes cleaned up).
- `build_duckdb` → open the `.duckdb` with `duckdb.connect` and `SELECT * FROM comunas`; assert row count
  and that `codigo_comuna` is a string type (VARCHAR).
- `build_sqlite` → open with `sqlite3`, `SELECT` a table, assert row count; add a table reporting >500k rows
  (wrap `len`) and assert it is **skipped** (table absent).
- `build_excel` → open with `openpyxl` and assert the expected sheet names exist; if Plan 030 landed, assert
  an oversized extra table's sheet is absent.

### Step 3: `artifacts.py` integrity tests (`tests/test_builders_artifacts.py`)

- Round‑trip the bundle in a temp `NORMALIZED_DIR` (monkeypatch the module constant): call
  `write_publishable_bundle_zip()` → `write_publishable_bundle_sha256(zip)` → independently
  `hashlib.sha256(open(zip,'rb').read())` and assert it equals the digest written in the `.sha256` file.
- `attach_publishable_package_to_manifest` → assert `manifest["packages"][0]` has matching
  `path`/`size_bytes`/`sha256`, and that every path listed in the manifest exists **inside** the zip
  (`zipfile.ZipFile(zip).namelist()`).
- Assert `write_publishable_bundle_zip` raises `SystemExit` when an artifact it expects is missing (delete one
  from the fixture) — covers the guard at artifacts.py:381‑386.

**Verify**: `.venv/bin/python -m pytest tests/test_builders_formats.py tests/test_builders_artifacts.py -q` → all pass.

## Test plan

- Two new test files, ~8‑12 tests total, each a write→reopen→assert round trip.
- Pattern: `tests/test_data_package.py` for build‑artifact fixtures and temp‑dir handling.
- Verification: the pytest command; coverage of both modules rises from ~5%/20% toward the writers being exercised.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `tests/test_builders_formats.py` and `tests/test_builders_artifacts.py` exist and pass
- [ ] A Parquet round‑trip asserts `codigo_comuna` stays a String/VARCHAR
- [ ] An artifacts test independently recomputes the bundle SHA‑256 and asserts equality with the `.sha256` file
- [ ] A manifest⇄zip consistency test asserts every manifest package path exists in the zip
- [ ] `.venv/bin/python -m pytest tests/test_builders_formats.py tests/test_builders_artifacts.py -q` exits 0
- [ ] `make lint` and `make format-check` exit 0
- [ ] No `src/builders/*` behavior changes (`git diff` shows those files unchanged)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- A round‑trip test fails on correct fixtures — that indicates a real writer bug (e.g. dtype loss); report it.
- A writer's signature is materially different from "base frames + extra_tables + output_path" — capture the
  real signature and adapt the fixture rather than guessing.

## Maintenance notes

- These golden tests are the safety net for any future change to the serializers or the bundle format;
  a reviewer changing `formats.py`/`artifacts.py` should expect to update them deliberately.
- Pairs with Plan 035 (gate tests) to give end‑to‑end confidence that what's built is also verified.
