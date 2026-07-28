# Plan 064: Publish the candidate GeoParquet through a CI-owned workflow

> **Executor instructions**: Follow each step in order and run every verification
> gate. Do not weaken a repository guard or substitute another storage mechanism.
> On any STOP condition, report it rather than improvising. When all done criteria
> pass, update this plan's row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 63cc106..HEAD -- scripts/build_geometria_comunal.py src/extractors/geometria_comunal_extractor.py src/builders/geo.py .github/workflows/monthly-scrape.yml .github/workflows/pages-deploy.yml .pre-commit-config.yaml tests/test_ci_config.py docs/datasets/geometria_comunal.md`
> If in-scope code no longer matches the Current state, STOP.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: direction / distribution
- **Planned at**: commit `63cc106`, 2026-07-26

## Why this matters

The geometry extractor, validator, and GeoParquet writer are complete, but no
artifact is available to users: the roughly 5 MB output is absent from the repo
because the local 500 KB large-file guard blocks a manual commit. The existing
monthly candidate workflows establish the correct mechanism—CI validates and
commits ignored data with explicit repository write permission. This plan applies
that mechanism without weakening the guard for normal source commits.

The result is a Pages-served, directly consumable GIS file plus a SHA-256 companion
file. It remains candidate data: it must not join the daily build, stable catalog,
publishable ZIP, or PyPI runtime bundle.

## Current state

- `scripts/build_geometria_comunal.py:1-13` is intentionally standalone: extract
  → fail-loud validation → GeoParquet write, never `make build`.
- `src/extractors/geometria_comunal_extractor.py:13-17` fetches per region and
  falls back to per-comuna requests; it writes raw snapshots and staging data.
- `src/builders/geo.py:18-23` uses `0.001` degrees simplification; ADR-012
  records a valid ~4.98 MB GeoParquet.
- `.pre-commit-config.yaml:10-11` has `check-added-large-files --maxkb=500`.
- `.github/workflows/monthly-scrape.yml:14-16,71-90` is the workflow exemplar:
  `contents: write`, `git add -f`, no-change handling, and a `[skip ci]` commit.
- `.github/workflows/pages-deploy.yml:57-59` deploys the repository root, so a
  committed normalized artifact is served by the existing static site.
- The stable bundle already uses `.sha256` companion files; geometry needs the
  same small, independently fetchable integrity artifact without entering that bundle.
- ADR-012 requires geometry to remain outside `build_dev_db.py`, `make extract`,
  and the generated stable catalog.

## Commands you will need

| Purpose | Command | Expected result |
|---|---|---|
| CI-equivalent dependencies | `uv sync --extra pipeline --extra dev --locked` | exit 0 |
| Build geometry | `uv run python scripts/build_geometria_comunal.py` | exit 0; ≥340 records |
| Inspect artifact | `uv run python -c "import geopandas as gpd; d=gpd.read_parquet('data/normalized/geometria_comunal.parquet'); assert len(d)>=340; assert d.crs.to_epsg()==4326; print(len(d))"` | prints ≥340 |
| Geometry tests | `uv run pytest tests/test_extractors.py tests/test_validation.py -v -k Geometria` | selected tests pass |
| CI tests | `uv run pytest tests/test_ci_config.py -v` | all pass |
| Quality | `make lint && make format-check && make doctor` | exit 0 |

## Scope

**In scope**:

- `.github/workflows/geometria-comunal.yml` (create)
- `tests/test_ci_config.py`
- `docs/datasets/geometria_comunal.md`
- `plans/README.md` status

**Out of scope**:

- `.pre-commit-config.yaml`, `Makefile`, `src/build_dev_db.py`, the dataset
  config, `Dataset` enum, package/release workflows, and public bundle scripts.
- `src/chile_hub/core.py` and any coordinate resolver (Plan 065).
- Scheduled refreshes: begin with manual dispatch only.

## Git workflow

- Branch: `advisor/064-publish-geometry-artifact`
- Commit: `feat(ci): publica GeoParquet comunal bajo demanda`
- Do not push, dispatch, or alter Pages settings without explicit operator approval.

## Steps

### Step 1: Create an isolated, manually dispatched workflow

Create `.github/workflows/geometria-comunal.yml`, structurally modeled on the
SINIM job in `monthly-scrape.yml`.

1. Trigger only on `workflow_dispatch`; no `schedule`.
2. Use top-level `permissions: contents: write`, a dedicated concurrency group,
   Ubuntu, Python 3.13, uv cache, and a 20-minute timeout.
3. Run `uv lock --locked`, then `uv sync --extra pipeline --extra dev --locked`.
4. Run exactly `uv run python scripts/build_geometria_comunal.py`; do not use
   `--skip-fetch`, `make build`, or `make extract`.
5. Before any commit, read the result with geopandas and assert: file exists,
   ≥340 records, CRS EPSG:4326, no null geometry, and five-character CUT values.
   Also run focused geometry extractor/validation tests.

**Verify**: `rg -n "workflow_dispatch|contents: write|build_geometria_comunal.py|make build|schedule" .github/workflows/geometria-comunal.yml` → the first three appear; the latter two do not.

### Step 2: Stage only successfully validated candidate artifacts

Add a commit step after validation, following `monthly-scrape.yml:71-90`.

Before staging, generate the checksum:

```bash
sha256sum data/normalized/geometria_comunal.parquet \
  > data/normalized/geometria_comunal.parquet.sha256
```

The companion must contain the conventional digest plus the artifact path. It is
the integrity contract consumed by Plan 065.

- Configure `github-actions[bot]` identity.
- Use `git add -f` only for:
  `data/normalized/geometria_comunal.parquet`,
  `data/staging/geometria_comunal.csv`,
  `data/staging/geometria_comunal.metadata.json`,
  `data/normalized/geometria_comunal.parquet.sha256`, and
  `data/raw/bcn_geometria_comunal_*.json`.
- If no staged diff exists, print `No changes to commit` and exit 0.
- Otherwise commit `chore(data): refresh candidate comunal geometry [skip ci]`
  and push.
- Add a summary with record count, byte size, metadata source mode, and the
  candidate/outside-bundle boundary. Never print raw payload data or secrets.

**Verify**: `sha256sum -c data/normalized/geometria_comunal.parquet.sha256` →
`data/normalized/geometria_comunal.parquet: OK`; and
`rg -n "git add -f|geometria_comunal.parquet.sha256|\[skip ci\]" .github/workflows/geometria-comunal.yml` → all patterns appear.

### Step 3: Add CI configuration regression tests

Add `GeometriaCandidateWorkflowGuardrailTests` to `tests/test_ci_config.py`, using
the repository's existing text-based workflow-test style. Assert that the workflow:

- is manual only and unscheduled;
- uses locked pipeline/dev dependencies;
- calls the standalone builder and validates before its commit step;
- stages only the five allowed geometry path families, including the checksum;
- has `contents: write` and `[skip ci]`; and
- does not call the daily build or publishable bundle scripts.

**Verify**: `uv run pytest tests/test_ci_config.py -v` → all pass.

### Step 4: Document the distribution boundary

Add a “Publication” section to `docs/datasets/geometria_comunal.md`. State that
the manually dispatched workflow generates the file, Pages serves it at
`https://tooltician.com/chile-hub/data/normalized/geometria_comunal.parquet` and
its adjacent `.sha256` file after deployment, and GIS users read it directly.
State explicitly that it is candidate data and excluded from `ChileHub()`'s stable
bundle and normal build. Include CRS/record-count and `sha256sum -c` verification;
do not promise a refresh cadence.

**Verify**: `make doctor` → exit 0; `rg -n "candidate|workflow_dispatch|geometria_comunal.parquet" docs/datasets/geometria_comunal.md` → all terms appear.

## Test plan

- New CI guardrail tests in `tests/test_ci_config.py`.
- Local integration: build, then inspect the GeoParquet's records, CRS, and geometry.
- Regression: focused extractor/validator tests plus `make doctor` and quality checks.
- Manual post-dispatch acceptance: inspect the bot commit and workflow summary,
  wait for Pages, and execute `gpd.read_parquet(<Pages URL>)` with the same
  record-count/CRS assertions. This changes remote state and requires operator approval.

## Done criteria

- [ ] Workflow is manual-only and passes its guardrail tests.
- [ ] It validates before committing, writes a valid `.sha256` companion, and stages only the allowed artifacts.
- [ ] The 500 KB pre-commit guard is unchanged.
- [ ] Geometry stays absent from the stable catalog, daily build, and ZIP.
- [ ] Focused tests, `make doctor`, lint, and format checks exit 0.
- [ ] Documentation accurately describes direct Pages access and candidate status.
- [ ] Plan 064 is marked DONE only after successful workflow dispatch and Pages readback.

## STOP conditions

- Fewer than 340 valid geometries, non-EPSG:4326 CRS, or invalid CUT widths.
- The only solution changes the large-file limit or bypasses a hook.
- The workflow needs the daily build, stable catalog, or publishable bundle.
- Branch protections prevent the Actions bot from pushing; report the required
  maintainer configuration rather than inventing credentials or deploy keys.

## Maintenance notes

Keep the workflow manual until demand justifies a cadence. Any future schedule
must keep the same validation and candidate-only boundaries. Plan 065 can consume
the artifact and its checksum only after this plan's Pages readback succeeds.
