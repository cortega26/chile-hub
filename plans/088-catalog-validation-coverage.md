# Plan 088: Cobertura catálogo→validación — gate + exenciones explícitas

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- scripts/check_validation_registration.py src/build_dev_db.py src/validation.py data/dataset_catalog_config.json tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests / tech-debt
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

The registration checker enforces `validate_*` ↔ `validations = {...}`
consistency, but NOT catalog → validation coverage. Result: 25 catalog keys vs
22 validation keys, and the 3 unvalidated datasets are invisible to CI.
`autoridades_locales` (candidate, extractor + doc exist, 362 expected records)
has no validator, no build path (`grep autoridades_locales src/build_dev_db.py`
= zero hits), and no staging/normalized artifacts — yet nothing fails. The next
dataset added the same way will also publish-or-vanish silently. (AGENTS §10:
no publicar sin pasar por `validate_*()`.)

## Current state

- `scripts/check_validation_registration.py:8-22` — exemptions exist for
  functions (`ALLOWED_UNREGISTERED_VALIDATORS = {"puntos_interes",
  "geometria_comunal"}`, with documented reasons) and alias keys
  (`ALLOWED_WITHOUT_DEDICATED_VALIDATOR = {"comunas_enriquecidas"}`).
  Missing rule: catalog keys with no validation entry at all.
- Verified 2026-09-15: catalog = 25 keys; `validations` = 22 keys; checker
  passes (`22 validation keys, 23 validate_* functions`). The 3 uncovered:
  - `geometria_comunal` — has `validate_geometria_comunal`, separate build
    script (`scripts/build_geometria_comunal.py`, ADR-012). Legit, needs an
    explicit exemption of the *catalog-coverage* kind.
  - `delincuencia_comunal` — deprecated/rejected 2026-09-15, extractor
    neutralized. Legit, needs an explicit exemption.
  - `autoridades_locales` — candidate (`publication_track: candidate`,
    `public_bundle_eligible: False`, `cadencia: bajo_demanda`), no validator,
    no build path, no artifacts. Needs an explicit exemption with that reason
    (wiring a real validator is a follow-up: there is no staging data today).
- `validate_puntos_interes` (`src/validation.py:904`): NOT in catalog —
  correctly exempted already. Do NOT touch it.
- `validate_autoridades_electas` (`src/validation.py:1338-1352`) covers only
  diputado/senador; `autoridades_locales` (gobernador/alcalde) is explicitly
  out of its domain per its own docstring. Do NOT stretch it.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Checker (baseline) | `./.venv/bin/python scripts/check_validation_registration.py` | executed | `validation registration ok: ...` |
| Companion registry | `./.venv/bin/python scripts/check_companion_paths.py registry` | declared | `check_companion_paths ok (modo: registry)` |
| Focal tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**:
- `scripts/check_validation_registration.py` (new catalog-coverage rule + `ALLOWED_UNVALIDATED_DATASETS`-style set with lane reasons)
- `tests/test_pipeline_logic.py` (tests for the new rule: covered key passes, uncovered-unexempted key fails, exempted key passes)
- `AGENTS.md` one-line pointer if §5/§12 names the checker behavior (only if it already does; do not expand docs here)

**Out of scope**:
- Writing `validate_autoridades_locales` or wiring it into the build (no staging data exists; that is a follow-up dataset plan, not this gate).
- Touching `validate_puntos_interes` or its exemption.
- Changing `DATASET_CATALOG_CONFIG` keys or lanes.

## Git workflow

- Branch: `advisor/088-catalog-validation-coverage`
- Commit por step; estilo conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline + confirm the uncovered set

Run the checker unmodified; then compute the uncovered set yourself:
catalog keys minus validation keys (parse both with `ast`/json, same technique
as the script). Confirm it equals `{geometria_comunal, delincuencia_comunal,
autoridades_locales}`.

**Verify**: checker exits 0; your computed set matches. If it doesn't match,
STOP (catalog changed — re-derive exemptions from the live registry lanes).

### Step 1: Add the catalog-coverage rule

In `check_validation_registration.py`, load catalog keys from
`data/dataset_catalog_config.json`, compute `unvalidated = catalog -
registered`, and fail unless each is in a new explicit set, e.g.
`ALLOWED_UNVALIDATED_DATASETS = {"geometria_comunal": "<reason: separate
script ADR-012>", "delincuencia_comunal": "<reason: rejected/deprecated>",
"autoridades_locales": "<reason: candidate bajo_demanda, no build path>"}`
— reasons as data, printed in the error. Keep the existing two exemption sets
untouched.

**Verify**: checker still exits 0 on the unmodified tree.

### Step 2: Tests for the rule

Add tests (model after existing checker-adjacent tests; if none exist as
pytest, test the pure functions by importing the script as a module or extract
the set-computation into a testable function without changing behavior):
uncovered-unexempted key → SystemExit; exempted key → ok; fully-covered
catalog → ok.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -q` → all pass.

### Step 3: Prove the gate bites

Temporarily (in a scratch, NOT committed) remove one exemption and confirm the
checker fails with the dataset named; restore. Then `make doctor`.

**Verify**: `make doctor` → exit 0; scratch test showed failure without exemption.

## Test plan

- New: rule tests (Step 2) + manual bite-proof (Step 3, not committed).
- Existing: `test_pipeline_logic.py` suite stays green.

## Done criteria

- [ ] Checker fails on a catalog key that is neither validated nor exempted (proven in Step 3)
- [ ] `./.venv/bin/python scripts/check_validation_registration.py` exits 0 on the final tree
- [ ] `make doctor` exits 0
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- The uncovered set in Step 0 differs (catalog evolved) — re-derive, don't force the three names.
- You discover `autoridades_locales` IS validated/built via a path outside `build_dev_db.py` (separate script like geometria) — then its exemption reason changes to that path; still complete the gate.
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- When `autoridades_locales` gains a build path, its entry moves from the exemption set to a real registration — the gate forces that edit (that is the point).
- Reviewer: each exemption must cite lane + reason; a bare name is a reject.
- **Deferred:** `validate_autoridades_locales` + build wiring (needs staging data + lane decision; separate dataset plan).
