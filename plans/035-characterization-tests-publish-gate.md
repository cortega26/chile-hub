# Plan 035: Characterization‑test the publish gate `verify_pipeline.py` and make it visible to coverage

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- scripts/verify_pipeline.py pyproject.toml tests/`
> If `verify_pipeline.py` changed, re‑enumerate its `verify_*` functions before writing tests.

## Status

- **Priority**: P2
- **Effort**: L
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`scripts/verify_pipeline.py` is the last gate before public data is published: `main()` runs a
sequence of ~16 `verify_*` checks (schema contracts, staging‑not‑newer‑than‑normalized, pipeline
metadata, dataset catalog, artifact manifest, publishable zip, publication policy, readiness). Each
`fail()` / `raise SystemExit(1)` is what stops corrupt data from shipping. Yet `tests/test_pipeline_logic.py`
imports only **4** of these functions, and `pyproject.toml` sets `source = ["src"]` so
`scripts/verify_pipeline.py` is **excluded from coverage entirely** — its untested gates don't even
appear as a coverage hole. The honest ~52% headline hides the single most dangerous file. This plan
makes the gate visible to coverage and characterization‑tests the highest‑value checks (good fixture
passes; corrupted fixture raises `SystemExit`).

## Current state

- `scripts/verify_pipeline.py` (1626 lines). Header sets up `sys.path` and imports
  `DATASET_CATALOG_CONFIG`, `verify_dataset_contract`, `load_json` (lines 11‑20). Runs with a
  `--profile {dev,readiness,publication}` argument (and a deprecated `--require-live`).
- `main()` (lines 1594‑1622) calls, in order: `verify_staging_not_newer_than_normalized`,
  `verify_required_files`, `verify_pipeline_metadata`, `verify_hub_health`, `verify_hub_status`,
  `verify_hub_bundle`, `verify_redistribution_report`, `verify_provenance_report`, `verify_drift_report`,
  `verify_overview`, `verify_dataset_catalog`, `verify_schema_contracts`, `verify_source_registry`,
  `verify_artifact_manifest`, `verify_data_package`, `verify_publishable_zip`; then `verify_readiness`
  (readiness/publication) and `verify_publication_policy` (publication only).
- `tests/test_pipeline_logic.py:20` imports only `_verify_stagnation`, `verify_dataset_contract`,
  `verify_publication_policy`, `verify_source_registry`.
- `pyproject.toml:175` — `source = ["src"]` (scripts excluded); `[tool.coverage.run] omit` lists some
  `src/chile_hub/*` files.
- Also untested: `validate_puntos_interes` (`src/validation.py:688`) — a registered validator (per
  `scripts/check_validation_registration.py`) with **zero** test references. Folded here as a small add.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Enumerate gates | `grep -nE "^def verify_" scripts/verify_pipeline.py` | ~30 functions |
| Run new tests | `.venv/bin/python -m pytest tests/test_verify_pipeline.py tests/test_validation.py -q` | all pass |
| Coverage incl. scripts | `.venv/bin/python -m pytest --cov=src --cov=scripts --cov-report=term-missing -q` | verify_pipeline.py now measured |
| Lint / format | `make lint && make format-check` | exit 0 |

## Scope

**In scope**:
- `tests/test_verify_pipeline.py` (create)
- `tests/test_validation.py` (add `validate_puntos_interes` cases)
- `pyproject.toml` — add `scripts` to coverage `source` (and adjust `omit` if needed)

**Out of scope**:
- Changing `verify_pipeline.py` behavior — this plan only tests it. If a test reveals a real bug, STOP
  and report it (do not fix it inline; it becomes its own plan).
- The `.github/workflows` coverage step wording — leave as is.

## Git workflow

- Branch: `advisor/035-verify-pipeline-tests`
- Conventional commit, e.g. `test(verify): caracteriza el gate de publicación y lo hace visible a coverage`.

## Steps

### Step 1: Make the gate visible to coverage

In `pyproject.toml` `[tool.coverage.run]`, add `scripts` to `source`:
```toml
source = ["src", "scripts"]
```
Run `.venv/bin/python -m pytest --cov=src --cov=scripts --cov-report=term-missing -q` and confirm
`scripts/verify_pipeline.py` now appears in the report (likely near 0% before new tests).

### Step 2: Build a fixture harness

Create `tests/test_verify_pipeline.py`. Because the gates read `data/staging/`, `data/normalized/`,
`contracts/`, and `data/source_registry.json` off `ROOT_DIR`, the cleanest approach is a fixture that
copies a **minimal valid** set of these into a temp dir and monkeypatches the module‑level path constants
(`STAGING_DIR`, `NORMALIZED_DIR`, `CONTRACTS_DIR`, `SOURCE_REGISTRY_PATH`, `ROOT_DIR`). Two viable
strategies — pick whichever the repo already leans toward:
- **(a) Golden copy**: `shutil.copytree` the real (already built) `data/normalized/`, `data/staging/`,
  `contracts/` into a temp dir; monkeypatch the constants to point there; each "good" test asserts the
  gate returns without raising.
- **(b) Minimal synthetic**: hand‑build the smallest JSON/parquet a gate needs.

Prefer (a) for the manifest/zip/catalog gates (they need real cross‑file consistency), (b) for the
policy/registry gates.

### Step 3: Characterization tests — good passes, corrupted raises

For each prioritized gate, write two tests: the good fixture passes; one targeted corruption raises
`SystemExit` (use `pytest.raises(SystemExit)`). Prioritize (highest publish risk first):
1. `verify_publication_policy` — flip a dataset to `source_mode="fallback"` / stale and assert it rejects.
2. `verify_artifact_manifest` — delete/rename a listed artifact and assert it rejects.
3. `verify_publishable_zip` — corrupt or shrink the zip’s file list and assert it rejects.
4. `verify_staging_not_newer_than_normalized` — `touch` a staging file newer than normalized and assert it rejects.
5. `verify_dataset_catalog`, `verify_schema_contracts`, `verify_pipeline_metadata`, `verify_source_registry` — one corruption each.

Then add a happy‑path `main()` smoke test running `--profile dev` against the good fixture, asserting no raise.

### Step 4: Test `validate_puntos_interes`

In `tests/test_validation.py` (model after the existing `ValidatorTests` cases), add:
- a valid `puntos_interes` DataFrame → `status == "ok"`;
- missing required columns → `status == "error"` with a message mentioning the missing columns;
- an out‑of‑bounds coordinate and a non‑5‑char `codigo_comuna` → error/warning as the validator specifies.

**Verify**: `.venv/bin/python -m pytest tests/test_verify_pipeline.py tests/test_validation.py -q` → all pass.

## Test plan

- New file `tests/test_verify_pipeline.py`: ~10‑16 tests (good + corrupted per prioritized gate + a `main()` smoke).
- `tests/test_validation.py`: 3 new `validate_puntos_interes` cases.
- Pattern: existing `ValidatorTests`/`PipelineLogicTests` structure; the 4 `verify_*` functions already
  imported in `test_pipeline_logic.py` show the calling convention.
- Verification: the pytest command above; coverage of `scripts/verify_pipeline.py` rises from ~0%.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n '"scripts"' pyproject.toml` shows `scripts` in coverage `source`
- [ ] `tests/test_verify_pipeline.py` exists with ≥1 passing corrupted‑fixture `SystemExit` test per prioritized gate (≥5 gates)
- [ ] `validate_puntos_interes` has ≥3 tests in `tests/test_validation.py`
- [ ] `.venv/bin/python -m pytest tests/test_verify_pipeline.py tests/test_validation.py -q` exits 0
- [ ] `.venv/bin/python -m pytest --cov=src --cov=scripts -q` shows `verify_pipeline.py` measured (>0%)
- [ ] `make lint` and `make format-check` exit 0
- [ ] No `scripts/verify_pipeline.py` behavior changes (`git diff` shows it unchanged)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- A gate can't be exercised without a full real build and no built `data/normalized/` is available — do the
  gates you can (policy/registry via synthetic fixtures) and report which needed a build.
- A "good fixture passes" test unexpectedly raises — that means the current real artifacts don't satisfy the
  gate, i.e. a latent bug in the gate or the data. Report it; do not weaken the test to make it pass.

## Maintenance notes

- Adding `scripts` to coverage will drop the headline % (more code measured) — that's the honest direction;
  don't re‑narrow `source` to inflate it.
- This is the "verification baseline" the other test plans build on; land it before large `verify_pipeline`
  refactors.
