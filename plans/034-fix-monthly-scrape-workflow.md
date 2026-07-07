# Plan 034: Fix the monthly‑scrape workflow so the SINIM/CEAD refresh actually installs and runs

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- .github/workflows/monthly-scrape.yml pyproject.toml`
> If either changed, re‑read `monthly-scrape.yml` before editing.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (complements 027, which fixes the provenance label the live scrape writes)
- **Category**: dx
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`monthly-scrape.yml` is the **only** automation that refreshes `finanzas_municipales` (SINIM) and
the candidate `delincuencia_comunal` (CEAD). Both jobs install dependencies with
`uv sync --group dev`, but the project defines no `[dependency-groups]` table — only
`[project.optional-dependencies]` extras. `uv sync --group dev` therefore targets an undefined group
and fails (or installs nothing useful), while every other workflow and the Makefile correctly use
`uv sync --extra dev`. On top of that, the SINIM job's "Rebuild" step runs `make build`, which needs
the `pipeline` extra (pandas/duckdb/xlsxwriter) that `--group dev` never installs. Net effect: the
monthly refresh cannot run as written — `finanzas_municipales` stays frozen on its 3‑row curated
fallback with no working path to update it.

## Current state

`.github/workflows/monthly-scrape.yml`:

- `scrape-sinim` job — install (lines 43‑46):
  ```yaml
      - name: Install dependencies
        run: |
          uv sync --group dev
          uv run playwright install chromium
  ```
  Extract (line 52) runs `sinim_finanzas_live_extractor.py`; "Rebuild" (lines 64‑72) runs
  `process_sinim_finanzas()` then `uv run make build`.
- `scrape-cead` job — install (lines 119‑121):
  ```yaml
      - name: Install dependencies
        run: |
          uv sync --group dev
  ```
- Both extract steps are `continue-on-error: true` with a non‑blocking "Report scrape failure" step and
  a summary (intentional for the candidate lane — keep this design).
- Reference: `pipeline-check.yml:78` uses `uv sync --extra pipeline --extra dev`; `Makefile:74` uses
  `uv sync --extra pipeline --extra dev`.
- Neither `sinim_finanzas_live_extractor.py` nor `cead_delincuencia_live_extractor.py` imports `scrapling`
  (that's the `autoridades_*` extractors), so the `scraping` extra is **not** needed here. SINIM does use
  Playwright (already installed in that job).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| YAML lint (local) | `uv run python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/monthly-scrape.yml'))"` | exit 0 |
| Sync sanity (mirrors the fix) | `uv sync --extra pipeline --extra dev --locked` | exit 0 |

(You cannot fully run a GitHub workflow locally; verification is the correct sync command + YAML validity
+ a contract test.)

## Scope

**In scope**:
- `.github/workflows/monthly-scrape.yml`
- Optionally `tests/test_chile_hub.py` (`WorkflowContractTests`) to guard the sync command

**Out of scope**:
- The `continue-on-error` / non‑blocking design — it is intentional for the candidate lane; keep it.
- The extractors themselves — Plan 027 fixes SINIM's provenance label separately.

## Git workflow

- Branch: `advisor/034-fix-monthly-scrape`
- Conventional commit, e.g. `ci(monthly-scrape): usa --extra pipeline/dev en vez de --group dev inexistente`.

## Steps

### Step 1: Fix the SINIM job's install

Replace `uv sync --group dev` in `scrape-sinim` with the same extras the pipeline needs (the job later
runs `make build`):

```yaml
      - name: Install dependencies
        run: |
          uv sync --extra pipeline --extra dev
          uv run playwright install chromium
```

### Step 2: Fix the CEAD job's install

Replace `uv sync --group dev` in `scrape-cead` with:

```yaml
      - name: Install dependencies
        run: |
          uv sync --extra pipeline --extra dev
```

(CEAD only extracts + commits staging; `--extra pipeline` covers whatever the extractor imports for
normalization. If a run reveals it needs Playwright too, add `uv run playwright install chromium`.)

**Verify**: `grep -n "uv sync --group dev" .github/workflows/monthly-scrape.yml` → no matches;
`grep -n "uv sync --extra pipeline --extra dev" .github/workflows/monthly-scrape.yml` → two matches.

### Step 3: Add a guard so this can't regress

If `tests/test_chile_hub.py` has a `WorkflowContractTests` class, add an assertion that no workflow under
`.github/workflows/` uses `uv sync --group ` (since no dependency‑groups exist). Model it after the existing
workflow‑structure assertions in that class. If the class doesn't lend itself to this, skip and note it.

**Verify**: `.venv/bin/python -m pytest tests/test_chile_hub.py -q -k "Workflow"` → passes.

## Test plan

- The verification is: YAML validity, the grep checks, and (optionally) the workflow‑contract test.
- No data test — the workflow only runs in GitHub Actions.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "uv sync --group dev" .github/workflows/monthly-scrape.yml` → no matches
- [ ] Both jobs use `uv sync --extra pipeline --extra dev`
- [ ] YAML parses (the python `yaml.safe_load` command exits 0)
- [ ] `uv sync --extra pipeline --extra dev --locked` exits 0
- [ ] If added, the `WorkflowContractTests` guard passes
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- A `[dependency-groups]` table has since been added to `pyproject.toml` (then `--group dev` may be valid —
  reconcile intentionally rather than blindly switching).
- The CEAD extractor imports something not covered by `pipeline`/`dev` (surface it after a first run).

## Maintenance notes

- After this lands, the next monthly run (or a manual `workflow_dispatch`) is the real integration test —
  confirm the SINIM job produces `finanzas_municipales` with `source_mode="monthly"` and (with Plan 027)
  `source_detail="live_scraping_sinim_portal"`.
- The non‑blocking failure design means a broken scrape stays green; the job summary already surfaces it.
  If stronger alerting is wanted later, add a step that opens/updates a tracking issue on failure — out of
  scope here.
