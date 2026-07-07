# Plan 024: Fix CUT leading-zero loss and non-ISO timestamps in the comunal extractors

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/extractors/consumo_electrico_extractor.py src/extractors/pobreza_extractor.py src/chile_hub/pipeline_status_utils.py src/pipeline_status_utils.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`consumo_electrico_comunal` enriches its rows with CUT codes by reading
`data/staging/comunas.csv`, but it reads that CSV **without forcing the code
columns to string**. Polars infers `codigo_region`/`codigo_comuna` as integers,
so the leading zero of every commune in regions `01`–`09` is dropped
(`"08101"` → `8101`). `normalize_rows` then casts back to string **without
`zfill`**, producing 4‑char codes. This violates non‑negotiable invariant #1
(CUT codes are fixed‑length strings) and makes `validate_consumo_electrico_comunal`
raise `SystemExit`, which **aborts the whole build**. The net effect is that
`consumo_electrico_comunal` can never publish real live data — it is stuck on
its 3‑row curated fallback.

Separately, `consumo_electrico_comunal` and `pobreza_comunal` write
`refreshed_at_utc` with a trailing `Z` (`strftime("...Z")`). Every other dataset
uses `datetime.now(UTC).isoformat()` (which emits `+00:00`). On Python 3.10 — a
**supported** runtime (`requires-python = ">=3.10,<3.15"`) — `datetime.fromisoformat("...Z")`
raises `ValueError`, so `parse_iso_datetime` returns `None` and `compute_freshness`
reports these two datasets as freshness `"unknown"` forever, inflating
`unknown_count` and potentially making them a false `top_issue`.

Both are one‑file‑family fixes that follow patterns already used elsewhere in the
repo.

## Current state

- `src/extractors/consumo_electrico_extractor.py` — extractor for `consumo_electrico_comunal`.
  - `_enrich_with_cut` reads `comunas.csv` with no `schema_overrides` (lines 201‑203):
    ```python
    comunas_df = pl.read_csv(
        comunas_csv, columns=["codigo_region", "codigo_comuna", "nombre_comuna"]
    )
    ```
  - `normalize_rows` casts the code columns to `String` but never `zfill`s them (lines 271‑274, 285):
    ```python
    df = df.with_columns(
        pl.col("codigo_region").cast(pl.String),
        pl.col("codigo_comuna").cast(pl.String),
        ...
    )
    ...
    df = df.filter(pl.col("codigo_comuna") != "")
    ```
  - `build_metadata` emits a `Z` timestamp (line 297):
    ```python
    "refreshed_at_utc": datetime.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    ```
- `src/extractors/pobreza_extractor.py` — extractor for `pobreza_comunal`. Emits the
  same `Z` timestamp in **two** places: `build_metadata` (line 295) and
  `PobrezaComunalExtractor.write_staging` (line 347).
- The established correct patterns already in the repo:
  - `.str.zfill(5)` on `codigo_comuna` — see `src/extractors/sinim_finanzas_live_extractor.py:422`
    and `src/extractors/mineduc_resultados_extractor.py:162`.
  - Forcing string dtype on read — see `src/extractors/electoral_extractor.py:232` and
    `src/extractors/subdere_extractor.py:596` (both pass `schema_overrides`/`dtypes` for code columns).
  - `datetime.now(UTC).isoformat()` for `refreshed_at_utc` — the norm across extractors.
- `parse_iso_datetime` lives in **two byte‑identical copies**
  (`src/chile_hub/pipeline_status_utils.py:69` and `src/pipeline_status_utils.py:69` — same line).
  It does **not** normalize a trailing `Z`:
  ```python
  def parse_iso_datetime(value):
      if not value:
          return None
      try:
          parsed = datetime.fromisoformat(value)
      except ValueError:
          return None
      ...
  ```

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Extractor + logic tests (no built data needed) | `.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -q` | all pass |

(If `.venv/bin/python` fails, use `uv run python` instead — the repo pins its
interpreter via `uv`. Do not create a new venv.)

## Scope

**In scope** (the only files you should modify):
- `src/extractors/consumo_electrico_extractor.py`
- `src/extractors/pobreza_extractor.py`
- `src/chile_hub/pipeline_status_utils.py` (Step 3 only)
- `src/pipeline_status_utils.py` (Step 3 only — the byte‑identical twin)
- `tests/test_extractors.py` (add tests)
- `tests/test_pipeline_logic.py` (add a `parse_iso_datetime` test)

**Out of scope** (do NOT touch, even though they look related):
- Any other extractor's timestamp format — this plan is scoped to the two broken ones.
- The `validate_*` functions in `src/validation.py` — they are correct; the bug is upstream.
- Deduplicating the two `pipeline_status_utils.py` copies — that is Plan 038. Here you
  edit both copies identically to keep them in sync.

## Git workflow

- Branch: `advisor/024-extractor-cut-timestamp`
- Conventional commits, matching `git log` (e.g. `fix(extractors): preserva ceros CUT y usa isoformat en consumo/pobreza`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Force string CUT codes in `consumo_electrico`'s commune enrichment

In `src/extractors/consumo_electrico_extractor.py`, make `_enrich_with_cut` read the
code columns as strings by adding `schema_overrides`:

```python
comunas_df = pl.read_csv(
    comunas_csv,
    columns=["codigo_region", "codigo_comuna", "nombre_comuna"],
    schema_overrides={"codigo_region": pl.String, "codigo_comuna": pl.String},
)
```

Then, in `normalize_rows`, add defensive zero‑padding after the string casts (so any
future upstream path is also protected). Change the two code casts to:

```python
pl.col("codigo_region").cast(pl.String).str.zfill(2),
pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
```

Leave the `.filter(pl.col("codigo_comuna") != "")` line as‑is (empty codes still filtered).

**Verify**: `make lint` → exit 0. (Behavioral verification is in Step 4.)

### Step 2: Emit ISO‑8601 timestamps in both extractors

Replace every `strftime("%Y-%m-%dT%H:%M:%SZ")` call with `isoformat()`:

- `consumo_electrico_extractor.py:297` → `"refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),`
- `pobreza_extractor.py:295` → same replacement.
- `pobreza_extractor.py:347` → `"refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),`

**Verify**: `grep -rn '%H:%M:%SZ' src/extractors/` → no matches.

### Step 3: Harden `parse_iso_datetime` against a trailing `Z` (defense‑in‑depth, both copies)

So any upstream `Z`-suffixed timestamp (from a source or a hand‑edited metadata file)
still parses on Python 3.10, normalize `Z` before `fromisoformat` in **both** copies
(`src/chile_hub/pipeline_status_utils.py` and `src/pipeline_status_utils.py` — apply the
identical edit to keep them byte‑identical):

```python
def parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, str) and value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    ...
```

**Verify**: `diff src/pipeline_status_utils.py src/chile_hub/pipeline_status_utils.py` → no output (still identical).

### Step 4: Add tests

In `tests/test_extractors.py` (model the class after an existing extractor test class —
`grep -n "class .*ExtractorTests" tests/test_extractors.py` to pick one, e.g. the SINIM one):
- A test that calls `consumo_electrico_extractor.normalize_rows([...])` with a row whose
  `codigo_comuna` came in as an int/short string for a region‑08 commune (e.g. `"8101"` or `8101`)
  and asserts the output `codigo_comuna` is exactly `"08101"` (5 chars) and `codigo_region` is `"08"`.
- A test that feeds `_enrich_with_cut` a temp `comunas.csv` (write it to a temp staging dir,
  monkeypatch `STAGING_DIR`) containing a region‑08 commune and asserts the enriched row's
  `codigo_comuna` keeps its leading zero.

In `tests/test_pipeline_logic.py`, add a `parse_iso_datetime` test asserting that both
`"2026-07-07T12:00:00Z"` and `"2026-07-07T12:00:00+00:00"` parse to the same aware UTC datetime
(not `None`).

**Verify**: `.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -q` → all pass, including the new tests.

## Test plan

- New tests (listed in Step 4): CUT leading‑zero preservation in `normalize_rows` and
  `_enrich_with_cut`; `parse_iso_datetime` accepts both `Z` and `+00:00`.
- Pattern to follow: an existing `*ExtractorTests` class in `tests/test_extractors.py` for
  structure and fixture style; existing `parse_iso_datetime`/freshness tests in
  `tests/test_pipeline_logic.py` if present.
- Verification: the pytest command above → all pass, ≥3 new tests.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -rn '%H:%M:%SZ' src/extractors/` returns no matches
- [ ] `grep -n 'schema_overrides' src/extractors/consumo_electrico_extractor.py` shows the code‑column override
- [ ] `grep -n 'str.zfill' src/extractors/consumo_electrico_extractor.py` shows `zfill(5)` and `zfill(2)`
- [ ] `diff src/pipeline_status_utils.py src/chile_hub/pipeline_status_utils.py` → no output
- [ ] `.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -q` exits 0, new tests present and passing
- [ ] `make lint` and `make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The "Current state" excerpts don't match the live code (drift since `c486e7c`).
- `validate_consumo_electrico_comunal` in `src/validation.py` does NOT check fixed‑length
  codes the way this plan assumes (open it and confirm `_invalid_fixed_length_count` is used) —
  if the assumption is false, report what you found instead of guessing.
- Adding `.str.zfill` breaks an existing consumo/pobreza test in a way that suggests the
  canonical code length differs from 5/2.

## Maintenance notes

- Any new extractor that reads `comunas.csv` must pass `schema_overrides` for code columns —
  this is a recurring footgun (see `src/extractors/cead_delincuencia_live_extractor.py:142`,
  which reads `comunas.csv` on its CSV‑fallback path and has the same latent risk; out of scope
  here but worth a follow‑up).
- Step 3 edits a duplicated file; once Plan 038 deduplicates `pipeline_status_utils.py`, this
  belt‑and‑suspenders lives in one place.
- Reviewer should confirm the freshness report for `consumo_electrico_comunal`/`pobreza_comunal`
  is no longer `"unknown"` after a build on Python 3.10.
