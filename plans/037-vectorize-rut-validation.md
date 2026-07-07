# Plan 037: Vectorize the RUT check‑digit validation and drop the `rutificador` dependency

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/validation.py pyproject.toml`
> If `src/validation.py` changed, re‑read `_validate_ruts_column` before editing.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none (coordinate with 032, which relocates `rutificador`; this plan removes it entirely)
- **Category**: perf
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`_validate_ruts_column` computes the expected check digit with a **per‑row Python UDF**:
`bases.map_elements(calcular_digito_verificador, return_dtype=pl.String)`. `map_elements` calls the
Python function once per row, so validating the `empresas` dataset (~1.5M RUTs) makes ~1.5M interpreter
round‑trips into `rutificador` every build — the CPU hot loop of `empresas` validation. The Chilean
check digit is a fixed weighted‑sum‑mod‑11 that Polars can compute vectorized. Doing so removes the hot
loop **and** the niche single‑maintainer `rutificador` dependency (of which only this one ~10‑line
function is used) from the critical publish‑gate path.

## Current state

`src/validation.py`:

- Import (line 4): `from rutificador import calcular_digito_verificador` (only use is the DV calc).
- `_validate_ruts_column` (lines 47‑81):
  ```python
  bases = valid_ruts.str.replace(r"-[\dkK]$", "")
  declared_dvs = valid_ruts.str.replace(r"^\d{7,8}-", "").str.to_lowercase()
  expected_dvs = bases.map_elements(
      calcular_digito_verificador,
      return_dtype=pl.String,
  )
  dv_bad = declared_dvs != expected_dvs
  dv_bad_count = int(dv_bad.sum())
  ```
  `valid_ruts` has already passed the format regex `^\d{7,8}-[\dkK]$` (line 60), so `bases` are 7–8 digit
  numeric strings and `declared_dvs` are single chars in `{0‑9, k}` (lowercased).
- `rutificador` is declared in both `[project.dependencies]` and the `pipeline` extra of `pyproject.toml`.

### The algorithm (Módulo 11) `calcular_digito_verificador` implements

For a numeric base, from the **rightmost** digit, multiply digits by the cycling weights
`2,3,4,5,6,7,2,3,…`; sum; `r = sum % 11`; `dv = 11 - r`; then `11 → "0"`, `10 → "k"`, else `str(dv)`.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Cross‑check vs rutificador (while installed) | `.venv/bin/python -m pytest tests/test_validation.py -q -k "rut or Rut or dv"` | all pass |
| Full validation tests | `.venv/bin/python -m pytest tests/test_validation.py -q` | all pass |
| Import no longer references rutificador | `grep -rn "rutificador" src/` | no matches after Step 3 |
| Lint / format | `make lint && make format-check` | exit 0 |

## Scope

**In scope**:
- `src/validation.py` (replace the UDF; remove the import)
- `tests/test_validation.py` (add the equivalence + known‑pair tests)
- `pyproject.toml` (remove `rutificador` from runtime deps and the `pipeline` extra)

**Out of scope**:
- The format‑check phase (`has_valid_format`, line 60) — already vectorized; keep it.
- Any other validator.

## Git workflow

- Branch: `advisor/037-vectorize-rut`
- Conventional commit, e.g. `perf(validation): vectoriza DV de RUT y elimina dependencia rutificador`.

## Steps

### Step 1: Add a characterization test FIRST (while `rutificador` is still installed)

In `tests/test_validation.py`, add:
- A **known‑pairs** test with hardcoded valid `(base, dv)` examples (use publicly known valid RUTs, e.g.
  `"6350612" -> "0"`, and a `k` case like `"11111111" -> "1"` — verify each pair against
  `rutificador.calcular_digito_verificador` when writing the test, then hardcode the expected values so the
  test survives the dependency's removal).
- An **equivalence** test guarded by `pytest.importorskip("rutificador")`: generate/enumerate a large sample
  of bases (e.g. `hypothesis` integers 1..99_999_999 as zero‑padded strings, or a fixed range) and assert the
  new vectorized function's output equals `calcular_digito_verificador` for every one. `hypothesis` is already
  a dev dependency.

Run these against the CURRENT code first to confirm they pass (baseline), then proceed.

### Step 2: Replace the UDF with a vectorized expression

Add a module‑private helper computing the DV vectorized, then call it instead of `map_elements`. Reference
implementation (right‑aligned fixed‑width so weights are positional; leading zeros contribute 0):

```python
def _expected_dv_vectorized(bases: pl.Series) -> pl.Series:
    # bases are 7-8 digit numeric strings (already format-validated).
    padded = bases.str.zfill(8)
    # weights from the RIGHT are 2,3,4,5,6,7,2,3; for an 8-wide right-aligned
    # string the per-offset (0=leftmost) weights are:
    weights = [3, 2, 7, 6, 5, 4, 3, 2]
    total = pl.Series([0] * padded.len())
    frame = padded.to_frame("b")
    weighted = pl.lit(0)
    for offset, w in enumerate(weights):
        digit = pl.col("b").str.slice(offset, 1).cast(pl.Int64)
        weighted = weighted + digit * w
    r = weighted % 11
    dv = 11 - r
    expr = (
        pl.when(dv == 11).then(pl.lit("0"))
        .when(dv == 10).then(pl.lit("k"))
        .otherwise(dv.cast(pl.String))
    )
    return frame.select(expr.alias("dv"))["dv"]
```

Then in `_validate_ruts_column`:
```python
    expected_dvs = _expected_dv_vectorized(bases)
```
Keep `declared_dvs` lowercased so the `k`/`K` comparison matches.

(Adapt the exact Polars idioms to the repo's style — the key invariant is: the result must equal
`calcular_digito_verificador` for every base, proven by Step 1's equivalence test.)

**Verify**: `.venv/bin/python -m pytest tests/test_validation.py -q -k "rut or Rut or dv"` → all pass (equivalence holds).

### Step 3: Remove the `rutificador` dependency

- Delete `from rutificador import calcular_digito_verificador` from `src/validation.py`.
- Remove `rutificador` from `[project.dependencies]` and the `pipeline` extra in `pyproject.toml`.
- `uv lock` → `uv lock --locked` (exit 0).

**Verify**: `grep -rn "rutificador" src/ pyproject.toml` → no matches.

### Step 4: Full suite + a scale sanity check

**Verify**: `.venv/bin/python -m pytest tests/test_validation.py -q` → all pass. Optionally time
`validate_empresas` on the real staging CSV before/after to confirm the speedup (report the numbers).

## Test plan

- Known‑pairs test (survives dependency removal) + `importorskip`‑guarded equivalence test over a large sample.
- Existing `ValidatorTests` for `validate_empresas` must still pass (it exercises `_validate_ruts_column`).
- Verification: pytest commands above; `rutificador` gone from source and manifest; lock in sync.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -rn "map_elements" src/validation.py` → no matches (the RUT UDF is gone)
- [ ] `grep -rn "rutificador" src/ pyproject.toml` → no matches
- [ ] The equivalence test (vs `rutificador`) passed at least once during development; the known‑pairs test passes now
- [ ] `.venv/bin/python -m pytest tests/test_validation.py -q` exits 0
- [ ] `uv lock --locked` exits 0
- [ ] `make lint` and `make format-check` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The vectorized function does NOT match `rutificador` for some base in the equivalence test — do not remove
  the dependency; report the mismatching input (there may be an edge case in base length or the weight cycle).
- `validate_empresas` or its tests break in a way that suggests the format‑validation pre‑filter lets through
  bases outside 7–8 digits (the `zfill(8)` assumption would then be wrong).

## Maintenance notes

- The check‑digit algorithm is fixed by Chilean law (Módulo 11); it will not change. The known‑pairs test is the
  permanent guard; the equivalence test can be deleted once `rutificador` is fully gone (it self‑skips).
- Reviewer should scrutinize the weight vector and the `11→0 / 10→k` mapping — those are the two easy places to
  get the DV wrong.
