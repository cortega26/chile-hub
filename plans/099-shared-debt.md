# Plan 099: Deuda media — sinim-shared + salud canónica + `_paths` único

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- src/extractors/sinim_finanzas_extractor.py src/extractors/sinim_finanzas_live_extractor.py src/builders/metadata.py src/builders/reports.py src/chile_hub/pipeline_status_utils.py src/pipeline_status_utils.py src/chile_hub/_paths.py src/chile_hub.py src/extractors/cead_delincuencia_live_extractor.py tests/test_extractors.py tests/test_verify_pipeline.py tests/test_ci_config.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: 091 (health-computation touches `hub_health.json` goldens — sequence after it)
- **Category**: tech-debt
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

Three admitted-but-open debts (TECHDEBT-03/05 + health duality): every
normalization/provenance fix must be applied twice to divergent sinim copies
(Plan 027 already touched only one); health is computed on two layers that can
diverge (the `retired_count/drifted_count` incident already forced one
re-expression); every new extractor copies the `sys.path` hack and root
resolution depends on import context. Each is small; together they are the
"same change in N files" tax. Characterization (077) should land first for the
health part — golden tests are the safety net.

## Current state

- `sinim_finanzas_extractor.py:109-137` vs
  `sinim_finanzas_live_extractor.py:416-450`: `normalize_rows` + `build_metadata`
  byte-near-identical (live copy adds `source_detail` live-branch). Tests exist:
  `tests/test_extractors.py` Sinim classes. `plans/README.md` records TECHDEBT-03 deferred.
- `build_freshness` ALREADY delegates to `compute_freshness`
  (`src/builders/metadata.py:88-89`, imports `from src.pipeline_status_utils`
  at `:21`) — do NOT "unify" what is unified. Remaining duality to close:
  `build_freshness_warnings` templates (`metadata.py:92-106`) vs any
  equivalent in `pipeline_status_utils.py` (grep showed none — confirm live),
  and `build_hub_status` (`reports.py:76`) vs `build_hub_health`
  (`pipeline_status_utils.py:276`). Import paths: `src.pipeline_status_utils`
  shim (lazy `__getattr__`, `src/pipeline_status_utils.py:12-21`) used by
  build/metadata/reports/scripts vs relative `.pipeline_status_utils` in
  `core.py:22` — same file, two resolutions.
- `src/chile_hub/_paths.py:1-59` — canonical root (`find_root()`, sentinel
  `name = "chile-hub"`, `parents[2]` fallback documented). Survivors:
  `src/chile_hub.py:11-13` (`sys.path.insert`), `src/pipeline_status_utils.py`
  shim (keep — documented purpose, PYTHONPATH=src), and
  `cead_delincuencia_live_extractor.py:27-31` (`ROOT_DIR not in sys.path:
  insert` + `try: from src... except: from base...`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Focal tests | `./.venv/bin/pytest tests/test_extractors.py tests/test_verify_pipeline.py -q` | declared | all pass |
| Goldens | `make verify` | declared | exit 0 |
| Import probe | `./.venv/bin/python -c "import chile_hub; print(chile_hub.__version__)"` (wheel-style path TBD by executor) | declared | version prints |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: `_sinim_shared` extraction + thin wrappers + equivalence test;
freshness/health delegation remainder; extractor `sys.path` prohibition +
guardrail test.

**Out of scope**: god-object splits (Wave 6); DatasetSpec promotion (spike in
ROADMAP Wave 5 — separate decision); removing the `pipeline_status_utils` shim
(it serves PYTHONPATH=src scripts by design).

## Git workflow

- Branch: `advisor/099-shared-debt`
- One commit per item (3); conventional commits.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline + 077 status

Confirm 077 state (if characterization landed, cite it as the safety net for
the health item; if not, be extra conservative on item 2 — wrappers only, no
logic moves). Focal tests green unmodified.

**Verify**: green baseline recorded.

### Step 1: `_sinim_shared`

Extract `normalize_rows`/`build_metadata` into a shared module (name it
`src/extractors/_sinim_shared.py` unless the codebase has a better convention
— check first), keeping the live copy's `source_detail` branch as a parameter.
Both extractors become thin fetch wrappers + re-export for backward compat.
Diff the two copies FIRST and reconcile any semantic divergence explicitly in
the commit (don't silently pick one). Add a stub-vs-live equivalence test on a
fixed fixture.

**Verify**: equivalence test passes; focal extractor tests pass; staging CSV
output for finanzas unchanged on fixture (compare bytes).

### Step 2: Canonical health remainder

Map precisely (read both): which of `build_freshness_warnings`,
`build_hub_status`, and any warning-template code in `reports.py` duplicates
`pipeline_status_utils` logic. Convert the `builders/` side to thin wrappers
over the canonical functions WITHOUT changing `hub_health.json` bytes
(golden-compare before/after on a real or synthetic build). If any output byte
differs, STOP and report (behavior change disguised as refactor).

**Verify**: `hub_health.json` byte-identical pre/post; `make verify` green.

### Step 3: `sys.path` → `_paths` + guardrail

Standardize extractors on absolute `src.*` imports + `_paths.find_root()`;
remove the `sys.path.insert` + try/except-import fallback pattern (cead-style).
Add a `test_ci_config.py` guardrail failing if any `src/extractors/*.py`
contains `sys.path` (mirrors the existing guardrail style). Keep
`src/chile_hub.py` + `src/pipeline_status_utils.py` shims (documented purpose;
the guardrail must exempt exactly these two by path, not by pattern).

**Verify**: guardrail passes; `PYTHONPATH=src` and wheel-style imports both resolve (probe command).

## Test plan

- New: sinim equivalence, health byte-identity (via build artifacts), sys.path guardrail.
- Existing suites stay green; goldens (`test_verify_pipeline.py:57`-adjacent) unchanged.

## Done criteria

- [ ] One sinim normalization implementation; wrappers thin; equivalence proven
- [ ] No behavior change in health outputs (byte-identity demonstrated)
- [ ] No `sys.path` in extractors (guardrail-enforced, 2 shims explicitly exempted)
- [ ] Focal tests + `make verify` + `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Sinim copies diverged semantically in a way tests can't reconcile (report both semantics, ask which wins).
- Health wrapper changes any output byte (report the diff, don't "fix" goldens).
- An extractor genuinely needs its import hack in some supported context (then exempt-by-path with reason, like the shims).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: the sinim divergence diff is the core of the review — read it line by line.
- New extractors must import via `src.*` + `_paths` (guardrail enforces); put it in the extractor playbook if one exists.
- **Deferred:** DatasetSpec inversion spike (catálogo generated from specs, one pilot dataset) — needs 077 + maintainer decision; tracked in ROADMAP Wave 5.
