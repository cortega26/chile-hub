# Plan 145: Wire geometria_comunal into the build pipeline (spike + decision)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- src/build_dev_db.py src/builders/inputs.py src/builders/datasets.py src/builders/geo.py src/builders/artifacts.py scripts/build_geometria_comunal.py scripts/publish_hf_dataset.py .github/workflows/geometria-comunal.yml docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Origin**: Plan 139 (geometria stable promotion) BLOCKED 2026-10-15 after 2 executor rounds. The staged verification build proved config-only promotion yields an inconsistent bundle. This plan is the unblocker: spike first, maintainer decision second, implementation never in this plan.

## Status

- **Priority**: P1
- **Effort**: S (spike + decision package only — NO pipeline change in this plan)
- **Risk**: LOW (read-only spike + doc; the risky change is explicitly deferred)
- **Depends on**: 139 (reuses its verified evidence: 345 rows, 12202 absent, spec-first metadata half committed on `advisor/139-geometria-stable-promotion`)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

`geometria_comunal` is metadata-promoted (Plan 139 branch: spec + registry + catalog all say `stable_publishable`, guardrails green) but the pipeline never ingests it: `src/build_dev_db.py` has zero geometria references, and the parquet is produced out-of-band by `scripts/build_geometria_comunal.py` BY DESIGN (Plan 053 + ADR-012). A staged `make build` against the promoted config produced an internally inconsistent bundle — manifest/ZIP orphan parquet, catalog 21-of-claimed-22, publication-gate missing-metadata failure. Until the pipeline half lands, the 139 metadata half must not merge (it would break the daily publish). This spike measures the three possible pipeline shapes and puts a decision package in front of the maintainer; it changes no pipeline code.

## Current state

Verified facts (from the 139 rounds — re-confirm, do not re-derive from memory):

- `src/build_dev_db.py`: `grep geometria` → zero matches (executor-measured). The daily build neither fetches nor ingests geometria staging.
- `scripts/build_geometria_comunal.py` header: standalone, explicitly NOT part of `make build`/`build_dev_db.py`; geometria is `candidate` / `bajo_demanda` like `delincuencia_comunal` and `autoridades_locales`; extractor excluded from `make extract`; excluded from the generated `dataset_catalog.json`. Reasoning in `docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md`.
- `src/builders/geo.py:67` (`write_mapa_comunal_geojson` docstring): derived visual of the candidate lane — enters neither ZIP nor dataset catalog, deterministic output to avoid spurious diffs.
- Staged-build evidence (round 2, re-confirm the commands not the conclusions): post-build `dataset_catalog.json` 22 datasets without geometria; `hub_bundle` public=22 but 21 dataset entries; geometria parquet present in ZIP manifest as orphan; `pipeline_metadata.json` missing geometria entry (publication-gate failure); suite 20 failed (14 golden 22-vs-23 + 6 bundle-summary/status/top-issue).
- 139 branch state: 5 in-scope files committed (`8aded3f`+`5ea7391`), derived files uncommitted, worktree clean — the metadata half, waiting for this pipeline half.
- Constraints: ArcGIS region-by-region fetch is fragile/slow (HTTP 500 on bulk, region 12 fallback documented); the daily publish must never break because geometry refresh hiccups (fail-loud protects data, but a missing lane breaks count gates all the same).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Ingestion map | `grep -rn "geometria" src/build_dev_db.py src/builders/inputs.py src/builders/datasets.py src/builders/geo.py scripts/build_geometria_comunal.py \| head -30` | executed | confirms the out-of-band shape above |
| Focal tests | `./.venv/bin/pytest tests/test_phase1_characterization.py tests/test_pipeline_logic.py -q` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md` (decision appendix ONLY if the ADR's amendment process allows; otherwise put the decision package in the report NOTES and leave the ADR untouched — check the ADR's own status section first)
- `plans/README.md` (status row only — SKIP per dispatcher override; reviewer owns the index)

**Out of scope** (do NOT touch — this is a spike, the roles reverse after the decision):

- `src/build_dev_db.py`, `src/builders/*`, `scripts/build_geometria_comunal.py` — NO pipeline change in this plan.
- `data/*`, `contracts/*` — the 139 branch owns the metadata half; do not duplicate it.
- `.github/workflows/*` — cadence changes are maintainer decisions documented here, not implemented here.
- Any new dataset, any other lane.

## Git workflow

- Branch: `advisor/145-geometria-pipeline-spike`
- At most one commit (the decision package, if filed as a doc); a report-only outcome with zero commits is also a valid COMPLETE.
- Do NOT push.

## Steps

### Step 0: Establish a green baseline

Run the ingestion-map grep; confirm the out-of-band shape matches Current state. Run focal tests + `make doctor`.

**Verify**: grep shows no `build_dev_db.py` ingestion; tests + doctor green.

### Step 1: Measure the three pipeline shapes (read-only spike)

For each option, answer from code reading (no edits): exact files/functions that would change, estimated diff size, and which gates it satisfies or breaks.

- **(A) Full ingestion into `build_dev_db.py`**: geometria staging → normalized parquet inside the daily build (fetch stays manual/out-of-band; build ingests existing staging like every other lane). Questions: where in `_load_inputs` would it slot (mirror an existing lane); what happens when staging is absent (fail-loud vs skip-with-warning — the daily publish must survive a missing geometry refresh); build-time cost of the 76 MB staging CSV; does `verify_pipeline.py --profile publication` then go green with 345/346 + `coverage_policy: "partial"`.
- **(B) Out-of-band outputs wired into bundle generation only**: `build_geometria_comunal.py` keeps producing the parquet; `build_dev_db.py` (or the artifacts/manifest step) picks up the existing normalized parquet + staging metadata and includes it in catalog/manifest/ZIP/HF without re-fetching or re-validating geometry. Questions: which function owns the pickup (`artifacts.py` vs a new `inputs.py` branch); staleness semantics (what if the parquet predates the config); whether golden tests can distinguish "lane intentionally absent" from "lane missing".
- **(C) Keep candidate (revert the 139 metadata half)**: promotion premature; close with new `review_by` + explicit condition (e.g. pipeline ingestion funded, or bundle-size budget approved). Questions: exact revert scope (the 5 files on the 139 branch); what happens to `resolve_by_coords()` + landing map consumers (they read the Pages artifact — unaffected by lane status, confirm by reading `geo.py` cache + map fetch code).

Also record for each: effect on ZIP size (+~5 MB), on HF mirror (new config subset), on `make build` wall time (estimate, do not run a full build — staging is absent in a fresh worktree and extraction is out of scope).

**Verify**: written comparison (A)/(B)/(C) with file:line evidence for every claim; no source file modified (`git diff --name-only` empty, `git status` clean).

### Step 2: Decision package (write-only)

Write the decision package as the executor report NOTES (and, only if it fits naturally, a short appendix in the 139 plan file — NO, that file belongs to another plan; keep the package in NOTES): recommendation (A/B/C) with one-paragraph rationale tied to ADR-011/ADR-012 and the fail-loud invariant, exact file list the implementation would touch, new risks introduced (daily-publish fragility for A; staleness semantics for B; review-date slip for C), and the concrete maintainer question to answer (which option + any budget/schedule constraint).

**Verify**: NOTES contain recommendation + file list + risks + maintainer question; `git status` clean.

## Test plan

No code changes, no new tests. Verification is gates-green on the untouched tree plus the written comparison.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] (A)/(B)/(C) comparison exists with file:line evidence per claim
- [ ] Recommendation + implementation file list + risks + maintainer question in NOTES
- [ ] Focal tests + `make doctor` + `make lint && make format-check` green on the untouched tree
- [ ] `git status --short` clean (zero commits is acceptable)
- [ ] No pipeline, data, contract, or workflow file modified

## STOP conditions

Stop and report back (do not improvise) if:

- The out-of-band shape differs from Current state (e.g. `build_dev_db.py` now ingests geometria — someone already did this).
- Any option requires touching the extractor fetch logic or the ArcGIS endpoint handling (larger blast radius — report, do not redesign).
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- After the maintainer decides, the implementation is a new build plan (not a resume of this spike): (A) needs `_load_inputs` + validation + golden-test updates; (B) needs artifacts/manifest pickup + staleness policy; (C) needs a clean revert of the 139 branch.
- Reviewer should scrutinize: that no code changed, that every option's gate analysis names the exact gate (publication profile, golden suite, bundle manifest), and that the recommendation respects fail-loud (daily publish never held hostage by geometry refresh).
- **Deferred:** the implementation itself — unblocked by the maintainer decision, not by this spike.
