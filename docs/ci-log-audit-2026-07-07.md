# CI Log Audit Report

Date audited: 2026-07-07 / 2026-07-08 UTC

Repository: `cortega26/chile-hub`

Local repository path used during audit:
`/home/carlos/VS_Code_Projects/ecosystems/chile-data/chile-hub`

Downloaded logs directory:
`/tmp/chile-hub-ci-logs`

## Scope

The audit downloaded and reviewed the latest run logs for all active GitHub Actions workflows:

- CodeQL
- Dependency Review
- Monthly Scrape (SINIM + CEAD)
- Pages Deploy
- Pipeline Check
- PyPI Release
- TestPyPI Package Smoke
- Copilot
- Dependabot Updates
- Dependency Graph
- pages-build-deployment

`TestPyPI Package Smoke` is active but had no recorded runs at audit time, so there were no logs
to inspect for that workflow.

## Executive Summary

All required recent CI checks passed after `Pipeline Check #260`, but the logs reveal several
issues worth fixing.

The two highest-risk findings are:

1. `origin/main` is already `uv.lock`-drifted again after the automatic PyPI release bumped
   `pyproject.toml` to `1.19.3` without updating `uv.lock`.
2. The PyPI Release workflow attached data artifacts produced by a normal push/readiness
   Pipeline run, not a publication-gated/live-data run. Those artifacts include fallback/minimal
   datasets.

There is also a clear broken workflow:

3. `Monthly Scrape (SINIM + CEAD)` fails because it uses `uv sync --group dev`, but this project
   uses extras (`--extra dev`), not dependency groups.

## Finding 1: Release Workflow Leaves `uv.lock` Stale

Severity: High

Category: CI correctness / release automation

Workflow: `PyPI Release`

Latest relevant run: `PyPI Release #149`

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28906955703`

### Evidence

After `Pipeline Check #260` passed for commit:

```text
0a95440 chore(deps): sync uv lock after release bump
```

the `PyPI Release` workflow ran and created:

```text
8cdeaf5 chore(release): 1.19.3 [skip ci]
```

That release commit changed:

- `CHANGELOG.md`
- `pyproject.toml`

but did not update `uv.lock`.

Confirmed remote state:

```text
origin/main:pyproject.toml
version = "1.19.3"

origin/main:uv.lock
[[package]]
name = "chile-hub"
version = "1.19.2"
source = { editable = "." }
```

Running on `origin/main`:

```bash
uv lock --locked
```

fails with:

```text
The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.
To update the lockfile, run `uv lock`.
```

### Impact

The next `Pipeline Check` will fail at:

```text
Python quality -> Verify uv.lock is in sync with pyproject.toml
```

This is the same failure that happened in `Pipeline Check #259`.

Because the release commit includes `[skip ci]`, the lock drift is not caught immediately by CI.

### Likely Cause

`python -m semantic_release version --skip-build` updates `pyproject.toml` and commits the release,
but the workflow does not regenerate or include `uv.lock` after the version bump.

Relevant workflow file:

`/.github/workflows/pypi-release.yml`

Relevant step:

```yaml
- name: Python semantic release
  id: semantic-release
  run: |
    before="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")"
    python -m semantic_release version --skip-build
    after="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")"
```

### Recommended Fix

Update `PyPI Release` so release version bumps cannot leave `uv.lock` stale.

Potential approaches:

- Preferred: configure semantic-release to include `uv.lock` in the release commit by running
  `uv lock` after the version bump but before commit/push, if supported by python-semantic-release
  hooks.
- Alternative: add an explicit post-version step that runs `uv lock`, commits `uv.lock` if changed,
  and pushes it before publishing.
- Also add a guard inside `PyPI Release` after semantic-release:

```bash
uv lock --locked
```

so the workflow fails before publishing if lock drift remains.

### Verification

After the fix:

```bash
git fetch origin main
git checkout main
git pull --ff-only origin main
uv lock --locked
```

should exit `0`.

A release commit that bumps `pyproject.toml` should either:

- include matching `uv.lock`, or
- not touch `pyproject.toml` without a lock update.

## Finding 2: PyPI Release Attaches Readiness/Fallback Data Artifacts

Severity: High

Category: Release/data integrity

Workflow: `PyPI Release` consuming `Pipeline Check` artifacts

Relevant Pipeline run: `Pipeline Check #260`

Pipeline URL: `https://github.com/cortega26/chile-hub/actions/runs/28906842562`

PyPI Release URL: `https://github.com/cortega26/chile-hub/actions/runs/28906955703`

### Evidence

`Pipeline Check #260` was triggered by a normal push to `main`:

```text
event: push
displayTitle: chore(deps): sync uv lock after release bump
```

In `/.github/workflows/pipeline-check.yml`, extract/build steps only run on `schedule` or
`workflow_dispatch`:

```yaml
- name: Extract source data (conditional)
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'

- name: Build outputs
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
```

For normal push runs, `verify_pipeline.py` uses readiness profile:

```bash
if [[ "${{ github.event_name }}" == "schedule" || "${{ inputs.publish }}" == "true" ]]; then
  profile=publication
else
  profile=readiness
fi
python scripts/verify_pipeline.py --profile "$profile"
```

Despite that, `PyPI Release #149` downloaded `Pipeline Check #260` artifacts:

```bash
run_id="28906842562"

gh run download "$run_id" \
  --name "pipeline-output-$run_id" \
  --dir data/normalized
```

Then it uploaded release assets:

```bash
gh release upload "$tag" \
  data/normalized/chile-hub-publishable-bundle.zip \
  data/normalized/chile-hub-publishable-bundle.zip.sha256 \
  data/normalized/artifact_manifest.json \
  data/normalized/dataset_catalog.json \
  data/normalized/hub_bundle.json \
  --clobber
```

The data status for the artifact includes fallback/minimal datasets:

```text
finanzas_municipales
source_mode=fallback
records=3

pobreza_comunal
source_mode=fallback
records=3

consumo_electrico_comunal
source_mode=fallback
records=3
```

Pipeline status from #260:

```text
overall_status: warn
warning_count: 12
top_issue: consumo_electrico_comunal (freshness=fresh, drift=drifted, warnings=3)
freshness badge: 8 warn (yellow)
```

### Impact

A successful PyPI release can publish and attach data assets that did not pass
publication-profile/live-data gates.

This risks distributing fallback sample datasets as release assets, even though the normal
publication path is supposed to reject fallback/stale/unready data.

### Recommended Fix

Make PyPI Release refuse to attach data assets unless the upstream Pipeline Check run is a
publication-grade run.

Options:

1. Only attach assets when the upstream Pipeline Check was:
   - `schedule`, or
   - `workflow_dispatch` with `publish=true`, or
   - otherwise explicitly marked as publication-profile.
2. Have Pipeline Check write a small manifest in the artifact, for example:

```json
{
  "verification_profile": "publication",
  "require_live": true,
  "source_run_event": "schedule"
}
```

Then PyPI Release should validate that before uploading release assets.

3. In PyPI Release, run an explicit final guard before upload:

```bash
python scripts/verify_pipeline.py --require-live
```

or equivalent publication-profile validation against downloaded assets.

4. If PyPI package release should happen on every semantic release but data asset release should
   not, split the behavior:
   - publish wheel/sdist normally
   - attach data assets only when publication-grade artifact exists
   - otherwise skip data asset upload loudly with a neutral notice

### Verification

A normal push Pipeline run should no longer be sufficient to attach data assets.

A publication-grade run should attach assets only after:

```bash
python scripts/verify_pipeline.py --require-live
```

or equivalent passes.

## Finding 3: Monthly Scrape Workflow Is Broken

Severity: Medium-High

Category: CI workflow correctness

Workflow: `Monthly Scrape (SINIM + CEAD)`

Latest run: #1

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28493523344`

### Evidence

Both jobs failed at `Install dependencies`:

- `SINIM Finanzas Municipales`
- `CEAD Delincuencia Comunal`

Direct job logs show:

```text
Run uv sync --group dev
uv sync --group dev
uv run playwright install chromium

error: Group `dev` is not defined in the project's `dependency-groups` table
Process completed with exit code 2.
```

Same failure appears in both monthly scrape jobs.

Relevant file:

`/.github/workflows/monthly-scrape.yml`

Current commands:

```yaml
uv sync --group dev
```

The rest of the repo uses extras:

```text
Makefile: uv sync --extra pipeline --extra dev
pages-deploy.yml: uv sync --extra dev
pypi-release.yml: uv sync --extra dev
pipeline-check.yml: uv sync --extra pipeline --extra dev
```

### Impact

The monthly scrape never reaches extraction. SINIM and CEAD monthly refresh automation is currently
non-functional.

This also explains why `finanzas_municipales` remains fallback/minimal in the published artifacts.

### Recommended Fix

Replace both instances in `/.github/workflows/monthly-scrape.yml`:

```bash
uv sync --group dev
```

with:

```bash
uv sync --extra dev
```

If the scrape needs pipeline dependencies too, use:

```bash
uv sync --extra pipeline --extra dev
```

Also consider adding `uv lock --locked` at the start of the monthly workflow so dependency drift
fails with a clearer message.

### Verification

Run locally or in workflow:

```bash
uv sync --extra dev
```

Then manually dispatch:

```text
Monthly Scrape (SINIM + CEAD)
```

Expected:

- dependency install succeeds
- extraction steps actually run
- no install-time failure

## Finding 4: Pages Deploy Has MkDocs Warnings

Severity: Medium

Category: Documentation quality

Workflow: `Pages Deploy`

Latest run: #91

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28906842609`

### Evidence

`Pages Deploy` succeeds, but MkDocs emits warnings.

Broken doc links:

```text
WARNING - Doc file 'case-study-construccion-chile-hub.md' contains a link '../README.md', but the target is not found among documentation files.

WARNING - Doc file 'case-study-construccion-chile-hub.md' contains a link '../plans/022-plan-avance-narrativa-confiabilidad.md', but the target is not found among documentation files.

WARNING - Doc file 'dataset-compatibility-policy.md' contains a link '../plans/008-hardening-source-readiness-schema-contracts-quality.md', but the target is not found among documentation files.

WARNING - Doc file 'dataset-compatibility-policy.md' contains a link '../data/source_registry.json', but the target is not found among documentation files.

WARNING - Doc file 'backlog/06-api-error-handling.md' contains a link '../../plans/011-harden-api-error-handling.md', but the target '../plans/011-harden-api-error-handling.md' is not found among documentation files.
```

Unrecognized relative link:

```text
INFO - Doc file 'dataset-compatibility-policy.md' contains an unrecognized relative link '../contracts/datasets/', it was left as is.
```

Absolute local path links:

```text
INFO - Doc file 'datasets/comunas.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/extractors/subdere_extractor.py:1', it was left as is.

INFO - Doc file 'datasets/indicadores.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/extractors/bcentral_extractor.py:1', it was left as is.

INFO - Doc file 'datasets/provincias.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/build_dev_db.py:1', it was left as is.

INFO - Doc file 'datasets/provincias.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/extractors/subdere_extractor.py:1', it was left as is.

INFO - Doc file 'datasets/regiones.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/build_dev_db.py:1', it was left as is.

INFO - Doc file 'datasets/regiones.md' contains an absolute link '/home/carlos/VS_Code_Projects/chile-hub/src/extractors/subdere_extractor.py:1', it was left as is.
```

Griffe warning:

```text
WARNING - griffe: src/chile_hub/contracts.py:79:
Confusing indentation for continuation line 19 in docstring, should be 4 * 2 = 8 spaces, not 6
```

Material for MkDocs also prints an upstream warning about MkDocs 2.0. This one is external and
informational.

### Impact

Docs deploy succeeds but shipped documentation contains broken links and machine-local paths.
This is user-visible quality debt.

The griffe warning could affect API docs rendering.

### Recommended Fix

1. Replace links to repo-root files with valid published-doc links, GitHub links, or exclude those
   docs from MkDocs if they are internal-only.
2. Replace local absolute paths with relative repo paths or GitHub source links.
3. Fix indentation in the docstring around `src/chile_hub/contracts.py:79`.
4. After cleanup, consider making docs stricter:

```bash
mkdocs build --strict
```

or add a CI step that fails on MkDocs warnings.

### Verification

Run:

```bash
uv sync --extra dev
mkdocs build --strict
```

Expected: no warnings from broken links or griffe.

## Finding 5: Pipeline Check Is Green But Hub Status Is `warn`

Severity: Medium

Category: Data quality / operational visibility

Workflow: `Pipeline Check`

Latest successful run: #260

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28906842562`

### Evidence

Pipeline status output:

```text
overall_status: warn
warning_count: 12
top_issue: consumo_electrico_comunal (freshness=fresh, drift=drifted, warnings=3)
top_issue_reason: tipos de cliente: ['Comercial', 'Residencial']
freshness badge: 8 warn (yellow)
```

Dataset warnings include:

```text
consumo_electrico_comunal
mode: fallback
records: 3
warnings:
- tipos de cliente: ['Comercial', 'Residencial']
- años disponibles: [2023]
- consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.
notes:
- fallback: usando datos de muestra
- Failed to resolve 'datos.energiaabierta.cl'
```

```text
pobreza_comunal
mode: fallback
records: 3
warnings:
- cobertura SAE: 2/346 comunas (0.6%) - parcial por diseño
- pobreza_comunal source_mode is fallback; usando datos de muestra mínima.
notes:
- ingresos: 0 comunas con estimación desde URL oficial
- multidimensional: 0 comunas con estimación desde URL oficial
```

```text
finanzas_municipales
mode: fallback
records: 3
coverage: 3/346
warnings:
- finanzas_municipales source_mode is fallback; review before publication
```

Other warnings:

```text
indicadores
warnings:
- indicadores live refresh reused last published artifact for missing codes: ipc
```

```text
empresas
warnings:
- found 1 RUTs with invalid format
- unknown sociedad codes (new types?): ['SpA']
- RES solo cubre constituciones bajo Ley 20.659...
```

```text
partidos_politicos
warnings:
- estado_legal poblado (vía SERVEL) en 15/36 partidos
```

Local network check also failed for the Energia Abierta data host:

```bash
curl -I -L --max-time 15 http://datos.energiaabierta.cl/dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/
```

Result:

```text
curl: (6) Could not resolve host: datos.energiaabierta.cl
```

### Impact

CI passing may hide that several datasets are partial/minimal/fallback. This is acceptable for
readiness tests but risky if those assets are attached to public releases or presented as
publishable.

### Recommended Fix

1. Separate "readiness CI passed" from "publication-quality data passed" in release automation.
2. Make fallback/minimal datasets visually explicit in release artifacts and docs.
3. Repair or replace source URLs for:
   - `consumo_electrico_comunal`
   - `pobreza_comunal`
   - `finanzas_municipales`
4. Consider making publication release fail if stable publishable datasets are fallback with only
   sample rows.

## Finding 6: PyPI Release Logs a 422 While Still Succeeding

Severity: Low-Medium

Category: Release workflow polish

Workflow: `PyPI Release`

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28906955703`

### Evidence

During `Attach verified data assets to release`:

```bash
gh release create "$tag" --notes "Release $tag" || true
```

The log contains:

```text
HTTP 422: Validation Failed
Release.tag_name already exists
```

The workflow continues and succeeds because of `|| true`, and `gh release upload --clobber`
follows.

### Impact

Not currently breaking, but it creates alarming red/error-looking logs in a successful release.
It also makes it harder to spot real release failures.

### Recommended Fix

Check for the release before creating it:

```bash
if ! gh release view "$tag" >/dev/null 2>&1; then
  gh release create "$tag" --notes "Release $tag"
fi
```

Then upload assets.

### Verification

Re-run release workflow on an existing tag path should not print HTTP 422.

## Finding 7: CodeQL Has Noisy Python Version Guessing

Severity: Low

Category: CI noise / static analysis configuration

Workflow: `CodeQL`

Run URL: `https://github.com/cortega26/chile-hub/actions/runs/28906842547`

### Evidence

Logs include:

```text
/bin/sh: 1: python2: not found
Will try to guess Python version, as it was not specified in `lgtm.yml`
Wanted to run Python 2, but it is not available. Using Python 3 instead
Could not guess Python version, will use default: Python 3
```

Then CodeQL succeeds.

### Impact

Benign, but noisy. It can obscure real extraction problems.

### Recommended Fix

Configure CodeQL more explicitly for Python 3 / no-build mode if appropriate.

Current workflow:

```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@...
  with:
    languages: python
```

Consider:

```yaml
with:
  languages: python
  build-mode: none
```

Only do this if CodeQL supports it for the pinned action version and it preserves desired analysis
quality.

## Finding 8: Benign External/Platform Warnings

Severity: Low

Category: CI noise

Workflows: Dependency Graph, Pages Deploy, Pipeline Check

### Evidence

Dependency Graph:

```text
Failed to parse GITHUB_REGISTRIES_PROXY environment variable
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
fetch_files command is no longer used directly
```

Pages Deploy:

```text
(node:2391) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
```

Pipeline Check artifact download:

```text
(node:3152) [DEP0005] DeprecationWarning: Buffer() is deprecated.
```

Several workflows also log Git's default-branch hint during `git init`:

```text
hint: Using 'master' as the name for the initial branch...
```

### Impact

These are platform/action-level warnings, not project failures. No immediate action required unless
log hygiene becomes important.

### Recommended Fix

Track only if they start failing or GitHub/action maintainers publish a migration path. For Git
default branch hints, this is emitted by action internals and generally not worth chasing.

## Suggested Fix Order

1. Prevent release-created lock drift.
   - Fix `PyPI Release` to update/check `uv.lock` after semantic-release version bumps.
   - Immediately sync `uv.lock` for current `origin/main` (`1.19.3`) if not already fixed.
2. Protect release data assets.
   - Ensure PyPI Release only attaches publication-grade artifacts.
   - Add manifest/profile validation before asset upload.
3. Fix Monthly Scrape.
   - Replace `uv sync --group dev` with `uv sync --extra dev` or
     `uv sync --extra pipeline --extra dev`.
4. Clean docs warnings.
   - Fix broken links, absolute local paths, and griffe docstring indentation.
   - Consider `mkdocs build --strict`.
5. Investigate fallback datasets.
   - `consumo_electrico_comunal`: source host `datos.energiaabierta.cl` no longer resolves.
   - `pobreza_comunal`: official URL extraction currently yields zero live rows.
   - `finanzas_municipales`: monthly scrape is broken and normal artifacts remain fallback.

## Useful Reproduction Commands

Download latest workflow logs:

```bash
mkdir -p /tmp/chile-hub-ci-logs
gh workflow list --repo cortega26/chile-hub --all
gh run list --repo cortega26/chile-hub --limit 20 \
  --json databaseId,number,workflowName,displayTitle,status,conclusion,event,headBranch,headSha,createdAt,url
```

Inspect latest Pipeline Check:

```bash
gh run view 28906842562 --repo cortega26/chile-hub --log
gh run view 28906842562 --repo cortega26/chile-hub \
  --json name,workflowName,conclusion,status,url,event,headBranch,headSha,jobs
```

Inspect Monthly Scrape job logs directly:

```bash
gh api /repos/cortega26/chile-hub/actions/jobs/84454939541/logs
gh api /repos/cortega26/chile-hub/actions/jobs/84454939548/logs
```

Check lock drift on remote main:

```bash
git fetch origin main --tags
git checkout --detach origin/main
uv lock --locked
git checkout main
```

Check current remote version mismatch:

```bash
git show origin/main:pyproject.toml | rg -n '^version = '
git show origin/main:uv.lock | rg -n 'name = "chile-hub"|version = "1\\.19' -C 2
```

Check fallback datasets in local artifact catalog:

```bash
python - <<'PY'
import json
from pathlib import Path

cat = json.loads(Path("data/normalized/dataset_catalog.json").read_text())
for d in cat["datasets"]:
    if d.get("source_mode") == "fallback" or d.get("warnings"):
        print(d["dataset"], "mode=", d.get("source_mode"), "records=", d.get("record_count"))
        print("warnings=", d.get("warnings"))
PY
```
