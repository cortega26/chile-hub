# CI Log Audit Rerun — 2026-07-08

## Purpose

This report reruns the CI log audit requested after the previous findings were expected to be fixed. It is self-contained so a fresh session can use it directly to request remaining follow-up work.

The audit reviewed the latest GitHub Actions runs visible for `cortega26/chile-hub` after commit `4ebca99768d2f99415f221a41fda226fcebfbfa0` (`fix(ci): harden release artifact gates`) and after the subsequent release commit `4e3b61c32a9eb7603bac5f0c8e6cf4e876f33994` (`chore(release): 1.19.4 [skip ci]`).

Raw logs were downloaded locally to:

```text
/tmp/chile-hub-ci-logs-rerun-2026-07-08
```

## Executive Summary

Most critical CI/release issues from the previous audit are fixed.

The important improvements confirmed in current logs are:

- `Pipeline Check #261` passed on `main`.
- `PyPI Release #150` passed.
- The release workflow no longer attaches readiness/push pipeline data assets to GitHub releases.
- The release workflow now updates `uv.lock` when semantic-release bumps `pyproject.toml`; `origin/main` has `pyproject.toml` and `uv.lock` both at `1.19.4`.
- The previous Pages broken-link warnings are no longer present in the latest Pages Deploy log.
- The previous `HTTP 422 / Release.tag_name already exists` message did not appear in `PyPI Release #150`.

Remaining issues or caveats:

- `Pipeline Check #261` still reports `overall_status: warn`, `warning_count: 12`, and `freshness_badge.json -> 8 warn`.
- Fallback/sample data warnings remain for `consumo_electrico_comunal`, `finanzas_municipales`, and `pobreza_comunal`.
- `Monthly Scrape (SINIM + CEAD)` has not been rerun since its old failing July 1 run, so the workflow fix is present in code but not validated by a fresh Actions run.
- `CodeQL #147` still prints `/bin/sh: 1: python2: not found` and Python-version guessing messages.
- `Pages Deploy #92` still includes third-party/dependency warnings from Material for MkDocs and GitHub Pages Node actions.
- `Dependency Graph #78` still prints Dependabot platform noise about `GITHUB_REGISTRIES_PROXY`.

## Latest Run Inventory

| Workflow | Latest run audited | Result | Head SHA | Notes |
|---|---:|---|---|---|
| Pipeline Check | `#261` / `28910376543` | Success | `4ebca99` | Current main push before release commit |
| PyPI Release | `#150` / `28910473615` | Success | `4ebca99` | Published `chile-hub 1.19.4`; release commit is `4e3b61c` |
| Pages Deploy | `#92` / `28910376533` | Success | `4ebca99` | Broken-link warnings from prior audit are gone |
| CodeQL | `#147` / `28910376538` | Success | `4ebca99` | Still has Python autobuild noise |
| Dependency Graph | `#78` / `28910377859` | Success | `4ebca99` | Still has Dependabot proxy warning |
| Dependabot Updates | `#14` / `28806268296` | Success | `b80e728` | Older dynamic run, not from current head |
| Dependency Review | `#21` | Success | `98d7447` | Older PR-related run |
| Copilot | `#4` | Success | `34b95a7` | Older PR-related run |
| Monthly Scrape (SINIM + CEAD) | `#1` / `28493523344` | Failure | `2c39890` | Old run from 2026-07-01; not rerun after fix |
| TestPyPI Package Smoke | none | N/A | N/A | No runs found |
| pages-build-deployment | `#130` | Success | `836a162` | Older Pages backend run from 2026-06-18 |

## Verification Commands Used

```bash
gh run watch 28910376543 --repo cortega26/chile-hub --exit-status
gh run watch 28910473615 --repo cortega26/chile-hub --exit-status
gh run list --repo cortega26/chile-hub --limit 80 --json databaseId,number,workflowName,displayTitle,status,conclusion,event,headBranch,headSha,createdAt,updatedAt,url
gh workflow list --repo cortega26/chile-hub --all
uv lock --locked
```

The lockfile check was run from a detached worktree of `origin/main`; it passed.

## Prior Findings Rechecked

### 1. `uv.lock` drift after release bump

Status: **Fixed**

Evidence:

- `origin/main` now points to `4e3b61c` (`chore(release): 1.19.4 [skip ci]`).
- `pyproject.toml` contains `version = "1.19.4"`.
- `uv.lock` contains the editable project package `chile-hub` with `version = "1.19.4"`.
- `uv lock --locked` passes on a detached `origin/main` worktree.

This confirms the previous `pyproject.toml`/`uv.lock` version mismatch has been fixed.

### 2. PyPI Release attaching readiness data assets

Status: **Fixed**

Evidence from `PyPI Release #150`:

```text
Pipeline artifact is not publication-grade (profile='readiness', require_live=False, event='push'); release data assets will not be attached.
```

The `Attach verified data assets to release` step was skipped. This is the desired behavior for a push/readiness pipeline run.

Relevant workflow behavior in `.github/workflows/pypi-release.yml`:

- Downloads the pipeline artifact from the triggering Pipeline Check run.
- Requires `pipeline_artifact_provenance.json`.
- Requires `verification_profile == "publication"` and `require_live is True`.
- Runs `scripts/verify_pipeline.py --require-live` only for publication-grade artifacts.
- Attaches release data assets only when `steps.pipeline-assets.outputs.ready == 'true'`.

This closes the previous risk where fallback/readiness data could be attached to a GitHub release.

### 3. PyPI Release `HTTP 422 / Release.tag_name already exists`

Status: **Fixed in latest evidence**

The latest `PyPI Release #150` log does not show the previous `HTTP 422: Validation Failed` or `Release.tag_name already exists` message.

One small code smell remains: the workflow still uses:

```bash
gh release create "v${after}" --notes "Release v${after}" || true
```

and later:

```bash
gh release create "$tag" --notes "Release $tag" || true
```

In `#150`, this did not produce the old warning. It is no longer an observed CI-log issue, but the workflow still relies on `|| true` instead of explicitly checking whether the release exists.

### 4. Monthly Scrape install failure (`uv sync --group dev`)

Status: **Fixed in code, not validated by a fresh run**

The latest workflow definition on `origin/main` now uses:

```bash
uv lock --locked
uv sync --extra pipeline --extra dev
```

for both SINIM and CEAD jobs.

However, the latest actual `Monthly Scrape (SINIM + CEAD)` run is still old:

- Run: `#1` / `28493523344`
- Date: 2026-07-01
- Result: failure
- Head SHA: `2c39890`

Because no new monthly or manual run exists after the fix, this cannot be marked fully validated. A manual `workflow_dispatch` run should be triggered to confirm the workflow now installs and proceeds to scraper execution.

### 5. Pages Deploy MkDocs broken links

Status: **Mostly fixed**

The latest `Pages Deploy #92` log no longer shows the previous broken-link warnings for:

- `../README.md`
- `../plans/...`
- `../data/source_registry.json`
- backlog plan links
- absolute local dataset links
- `src/chile_hub/contracts.py` griffe indentation warning

Remaining Pages log noise:

```text
Warning from the Material for MkDocs team
MkDocs 2.0 ... will introduce backward-incompatible changes
```

and GitHub Pages action/node warnings:

```text
(node:2439) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
```

The Pages action also prints:

```text
error_count: 10
```

This appears as an input/default printed by `actions/deploy-pages`, not as 10 observed deployment errors. The job still succeeds and deployment proceeds.

### 6. Pipeline health warnings and fallback data

Status: **Still present**

`Pipeline Check #261` passes, but the pipeline status remains warning-level:

```text
overall_status: warn
warning_count: 12
top_issue: consumo_electrico_comunal (freshness=fresh, drift=drifted, warnings=3)
Badge de frescura generado: ... freshness_badge.json -> 8 warn (yellow)
```

Important warning lines:

```text
WARNING [consumo_electrico_comunal]: tipos de cliente: ['Comercial', 'Residencial']
WARNING [consumo_electrico_comunal]: años disponibles: [2023]
WARNING [consumo_electrico_comunal]: consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.
WARNING [finanzas_municipales]: finanzas_municipales source_mode is fallback; review before publication
WARNING [pobreza_comunal]: cobertura SAE: 2/346 comunas (0.6%) — parcial por diseño; comunas sin muestra no tienen estimación
WARNING [pobreza_comunal]: pobreza_comunal source_mode is fallback; usando datos de muestra mínima.
```

The Pipeline Check was a push/readiness run, so fallback data is allowed there. The release gate now correctly prevents those readiness artifacts from being attached as publication data assets.

This is no longer a release-contamination issue, but it remains a data/source quality warning visible in CI.

### 7. `consumo_electrico_comunal` upstream DNS failure

Status: **Still present in pipeline status**

`Pipeline Check #261` generated this note:

```text
fallback: usando datos de muestra (HTTPConnectionPool(host='datos.energiaabierta.cl', port=80): Max retries exceeded with url: /dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/ (Caused by NameResolutionError("HTTPConnection(host='datos.energiaabierta.cl', port=80): Failed to resolve 'datos.energiaabierta.cl' ([Errno -2] Name or service not known)")))
```

This indicates the source is still unresolved from CI at build/status generation time. Since release asset attachment is now gated, the immediate publication risk is controlled, but the upstream source issue still needs investigation.

### 8. CodeQL Python autobuild noise

Status: **Still present**

`CodeQL #147` still prints:

```text
/bin/sh: 1: python2: not found
Will try to guess Python version, as it was not specified in `lgtm.yml`
Trying to guess Python version based on Trove classifiers in setup.py
Trying to guess Python version based on travis file
Trying to guess Python version based on installed versions
Could not guess Python version, will use default: Python 3
```

The job succeeds, but the old warning/noise remains. A likely cleanup is to configure CodeQL Python with explicit build mode, probably `build-mode: none`, in `.github/workflows/codeql.yml`.

### 9. Dependency Graph / Dependabot platform noise

Status: **Still present, low severity**

`Dependency Graph #78` still includes:

```text
Failed to parse GITHUB_REGISTRIES_PROXY environment variable
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
```

This appears to be GitHub/Dependabot platform noise. The job succeeds and no repository-level action is obviously required unless the project wants cleaner logs.

### 10. TestPyPI Package Smoke

Status: **No evidence**

The workflow is active, but `gh run list --workflow "TestPyPI Package Smoke"` returned no runs. Nothing can be audited for this workflow yet.

## Current Residual Findings

### Finding A — Data readiness warnings remain in successful Pipeline Check

Severity: **Medium**

The Pipeline Check is green, but it still reports warning-level data health:

- `overall_status: warn`
- `warning_count: 12`
- `freshness_badge.json -> 8 warn`
- fallback/sample data for multiple datasets

Recommended follow-up:

- Decide which warnings are acceptable in readiness CI and which should be moved to publication-only checks.
- Investigate live source failures for `consumo_electrico_comunal`, `finanzas_municipales`, and `pobreza_comunal`.
- Consider clearer summary wording in CI so green readiness runs do not look publication-ready when fallback data exists.

### Finding B — Monthly Scrape fix has not been validated by a new run

Severity: **Medium**

The workflow file is fixed, but the latest run is still the old failed July 1 run.

Recommended follow-up:

- Trigger `Monthly Scrape (SINIM + CEAD)` manually with `workflow_dispatch`.
- Confirm both install steps pass with `uv sync --extra pipeline --extra dev`.
- If scraper execution fails after install, capture that separately as a source/scraper issue.

### Finding C — CodeQL still emits Python autobuild/version guessing noise

Severity: **Low**

The job succeeds, but the logs remain confusing.

Recommended follow-up:

- Update CodeQL workflow to explicitly configure Python build mode, likely `build-mode: none`.
- Confirm the next CodeQL run no longer prints `python2: not found` or Python-version guessing messages.

### Finding D — Pages Deploy still contains third-party deprecation warnings

Severity: **Low**

The previous broken-link warnings are gone. Remaining messages are from dependencies/actions:

- Material for MkDocs warning about MkDocs 2.0.
- GitHub Pages action Node `punycode` deprecation.
- `actions/download-artifact` Node `Buffer()` deprecation appears in Pipeline landing smoke test.

Recommended follow-up:

- Track upstream action updates.
- Keep MkDocs and Material pinned until there is a clear migration path.
- No immediate project breakage observed.

### Finding E — PyPI release creation still relies on `|| true`

Severity: **Low**

The old `HTTP 422` message is absent in the latest run, but the workflow still suppresses release-create errors.

Recommended follow-up:

- Replace `gh release create ... || true` with an explicit existence check:

```bash
if gh release view "$tag" >/dev/null 2>&1; then
  echo "Release $tag already exists"
else
  gh release create "$tag" --notes "Release $tag"
fi
```

This is mostly log hygiene and observability now, not a current failing issue.

## Conclusion

The prior high-risk release and lockfile issues are fixed. The repository now correctly avoids attaching readiness/fallback data assets to releases, and `uv.lock` stays synchronized through the release bump to `1.19.4`.

The remaining work is mostly validation and cleanup:

1. Manually rerun Monthly Scrape to validate its workflow fix.
2. Investigate the still-present fallback/source warnings in Pipeline Check.
3. Clean up CodeQL and third-party action warning noise if log clarity is a priority.
