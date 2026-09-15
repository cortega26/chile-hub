# Plan 091: Datasets opcionales ruidosos + fallback sintético strict

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/build_dev_db.py src/validation.py scripts/verify_pipeline.py tests/test_pipeline_logic.py tests/test_validation.py tests/test_chile_hub.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: correctness
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Two silent paths violate "fail loudly before publishing bad data" (§4.2):
(1) 8 datasets (`empresas`, `pobreza_comunal`, `consumo_electrico_comunal`,
`partidos_politicos`, `autoridades_electas`, `estadisticas_vitales`,
`permisos_edificacion`, `calidad_aire`) validate only `if df_X is not None
else {}` — a broken extractor or deleted CSV drops the layer from the bundle
without aborting; consumers see `hub.load_polars("empresas")` fail as
"unknown dataset". (2) Synthetic fallback data (`generate_fallback_indicators`,
18-row comunas fallback) and statistical anomalies surface only as warnings
with `status: "ok"`, publishable if the publication gate doesn't cover them.

## Current state

- `src/build_dev_db.py:185-200` — `required_staging` = 10 CSVs only; the 8
  above load as `df_X = None` when CSV/metadata missing (`:347-440` pattern,
  e.g. `:347-348` `df_empresas = None` + exists-check).
- `:589-672` — each optional validates `if df_X is not None else {}` (8 sites).
- `src/validation.py:475-478` — `indicadores` fallback → warning only,
  `status` stays `"ok"`; `:500-502` anomalies → warnings; `:150-155` comunas
  fallback (18 vs 346 rows) → warning + `"ok"`; `:340-343` documents
  "nunca esta función aborta nada" (by design for the detector — keep it; the
  strictness belongs in the caller/profile, not the detector).
- `scripts/verify_pipeline.py --profile publication` is the last gate — map
  exactly which of these cases it already rejects before adding strictness
  (no double-gating surprises).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Focal tests | `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_validation.py -q` | declared | all pass |
| Contract tests | `./.venv/bin/pytest tests/test_chile_hub.py -q` | declared | all pass (needs `make build` first) |
| Publication gate | `./.venv/bin/python scripts/verify_pipeline.py --profile publication` | declared | behavior per Step 1 mapping |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: optional-missing policy in `build_dev_db.py`, `strict`/`profile`
plumbing in the affected `validate_*`, publication-profile enforcement in
`verify_pipeline.py`, tests.

**Out of scope**: changing what `detect_series_anomalies` detects (Plan 074
territory); adding new datasets; touching candidate-lane build paths (088).

## Git workflow

- Branch: `advisor/091-optional-datasets-strict`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Map the publication gate (no code changes)

Run `verify_pipeline.py --profile publication` paths by reading (and a dry
run if cheap): for each of (a) missing optional staging, (b) `source_mode:
fallback` synthetic, (c) anomaly warnings — record REJECT vs PASS today.
This table goes in the commit message; it prevents double-gating.

**Verify**: table written down; focal tests green unmodified.

### Step 1: Unexpected absence becomes loud

Distinguish expected absence (lane `candidate` per registry
`publication_track`, e.g. docs) from unexpected: if the catalog declares the
dataset publishable AND staging/metadata is missing, `raise SystemExit` with
the extractor command (same message style as `:197-200`). Only allow `None`
for datasets whose registry lane says so. Centralize the lane check (don't
hardcode 8 names twice — read `DATASET_CATALOG_CONFIG`/registry like the rest
of the pipeline does).

**Verify**: focal tests pass; scratch-test (uncommitted): temporarily rename one
optional CSV → build aborts with the loud message; restore.

### Step 2: `strict`/`profile` for synthetic + anomalies

Add a `strict=False` (or `profile="dev"`) parameter to `validate_indicadores`
and `validate_comunas` (and any other validator emitting fallback-synthetic
warnings found in Step 0): default keeps current warning behavior (dev green);
`strict=True` promotes synthetic-fallback and high-z anomalies to errors.
`_compute_validations` passes strictness from the run profile; publication
profile sets strict. Per-dataset thresholds, not a global flip (SIEDU/calidad
partial coverage stays warning-legit).

**Verify**: `tests/test_pipeline_logic.py tests/test_validation.py` pass,
including new strict/loose cases.

### Step 3: Contract tests + doctor

Update/extend `ArtifactContractTests`-adjacent expectations if `summary()` /
`validation_status` surface the new errors; run `make doctor`.

**Verify**: contract tests + doctor green.

## Test plan

- New: missing-publishable-aborts (scratch-proven + a unit test on the lane check), strict-promotes-fallback, strict-promotes-anomaly, loose-keeps-warning.
- Pattern: `tests/test_pipeline_logic.py::ValidatorTests` (empty + dup-key cases per §5).

## Done criteria

- [ ] Missing staging for a publishable dataset aborts with extractor hint
- [ ] `strict` promotes synthetic fallback + anomalies to error; default unchanged
- [ ] Step 0 gate-mapping table in the commit message (no silent double-gating)
- [ ] Focal + contract tests and `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Step 0 shows publication already rejects all three cases → shrink to Step 1 only and report.
- Promoting to error blocks a legitimate lane (partial-coverage-expected dataset) — then that dataset stays warning with a named reason, don't force global strict.
- Daily-build breakage risk materializes (MED risk): keep the change additive + profile-gated, never unconditional.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: every new `raise` must name the extractor command (copy `:197-200` style).
- If a dataset changes lanes, its absence policy follows the registry automatically — verify that linkage in review.
- **Deferred:** unifying the mode vocabulary across extractors (see 086).
