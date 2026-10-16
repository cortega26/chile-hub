# Plan 139: Promote geometria_comunal candidate to stable bundle

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- data/source_registry.json data/dataset_catalog_config.json data/dataset_specs/geometria_comunal.json contracts/datasets/geometria_comunal.schema.json src/extractors/geometria_comunal_extractor.py src/builders/datasets.py src/builders/artifacts.py .github/workflows/geometria-comunal.yml docs/datasets/geometria_comunal.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Amendment 2026-10-15 (lesson from Plan 143 execution)**: `data/dataset_specs/geometria_comunal.json` exists and, via `catalog_config_with_spec_overlay()` (`src/registry/dataset_spec.py:671-682`, applied in `src/builders/_shared.py`), SHADOWS the legacy catalog/registry entries at render time. Editing only the legacy JSONs is a no-op (proven in 143: `make sync-docs` reported "sin cambios" and Phase-2 equivalence tests failed). The spec file is therefore in Scope and Step 2 edits spec + legacy together. The contract already carries `expected_record_count: 345` and `coverage_policy: "partial"` (verified 2026-10-15) — Step 1-Q4 only needs to confirm the publication gate accepts it, not to add it.
>
> **Outcome 2026-10-15: BLOCKED after 2 executor rounds (revision budget exhausted).** Steps 0–3 verified as far as locally possible (spike Q1–Q5 answered, spec-first promotion + legacy mirror committed, guardrails green, doctor/lint/format green). The staged verification build (round 2, staging copied read-only from the user tree) proved the plan's core premise false: `src/build_dev_db.py` never ingests `data/staging/geometria_comunal.csv` — the parquet is produced out-of-band by `scripts/build_geometria_comunal.py` BY DESIGN (Plan 053 + ADR-012). Config promotion alone yields an inconsistent bundle (manifest ZIP-orphan, catalog 21-of-22, publication-gate missing-metadata failure; post-build suite 20 failed vs 14 pre-build, all traced). Unblocked by Plan 145 (pipeline-ingestion spike + maintainer decision). Worktree `advisor/139-geometria-stable-promotion` left config-only and clean; nothing to revert.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none (coordinate with 143 on `coverage_policy` wording; no file overlap)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

`geometria_comunal` is the only candidate lane with a live extractor, a published artifact, and two shipped consumers (`resolve_by_coords()` and the landing map). Its `review_by` is 2026-10-21 — six days from planning. Either it graduates to `stable_publishable` with an explicit Antártica exception, or the review date slips again and the candidate lane rots. Promotion is a distribution decision, not a code rewrite: the parquet already builds at 345/346 rows and reads end-to-end from Pages (verified in archived plan 064).

## Current state

Relevant files and roles:

- `data/source_registry.json:383-401` — geometria entry: `maturity_status: candidate`, `publication_track: candidate`, `public_bundle_eligible: false`, `review_by: 2026-10-21`, `expected 345/346, missing 12202/Antártica (known BCN hole, see ADR-012)`.
- `data/dataset_catalog_config.json:585-611` — geometria entry has `expected_record_count: 345` and **no `outputs` key** (verified: the only three catalog keys without `outputs` are `geometria_comunal`, `delincuencia_comunal`, `autoridades_locales`). That is why it is absent from the ZIP/bundle.
- `src/extractors/geometria_comunal_extractor.py:148` — `Obtiene la geometría de las 346 comunas iterando por región.` Region-by-region fetch because a single query for ~346 comunas returns HTTP 500 (`:321`). Line `:359`: `warnings.append(f"solo {df.height}/346 comunas presentes — cobertura parcial")`.
- `.github/workflows/geometria-comunal.yml` — manual/out-of-band refresh lane (ADR-012). It commits parquet + `.sha256` + staging CSV/metadata + raw snapshot without touching the 500 KB guard.
- `docs/datasets/geometria_comunal.md` — user doc; states generalized geometry, EPSG:4326, not for geodetic precision.
- `contracts/datasets/geometria_comunal.schema.json` — JSON Schema contract (PK `codigo_comuna`).
- Verified live counts during recon (2026-10-15): `data/normalized/geometria_comunal.parquet` reads **345 rows** via Polars; `finanzas` reads 345 for comparison. Antártica `12202` is the documented missing row.

Conventions that apply:

- Lane vocabulary is normative: `publication_track` (`stable_publishable` vs `candidate`), `maturity_status`, `confidence_tier`, `review_by` live in `data/source_registry.json`; inclusion criteria live in `docs/dataset-inclusion-criteria.md` (states `under-review` → `candidate`, never in public bundle; needs `review_by` + exit rule). Match them exactly — see `docs/datasets/perfil_territorial_comunal.md` for a promoted-layer doc example.
- CUT invariant (`AGENTS.md §4.1`): `codigo_comuna` is `pl.String` length 5, preserved as `"01101"`. The geometry join key must stay string-typed.
- Bundle membership is derived from the registry (`public_bundle_eligible` + `publication_track`), filtered in `src/builders/artifacts.py` and `scripts/publish_hf_dataset.py` (see archived plans 070/071). Do not hand-edit the ZIP.

Design constraints from intent docs (executor has not read them):

- `docs/product-spec.md` principle "Profundidad antes que amplitud" + ADR-011: growth is depth on validated BCN sources, not breadth on fragile ones. Geometry qualifies (BCN ArcGIS, same source as DPA).
- ADR-012 (geometría comunal): generalized geometry, EPSG:4326, `resolve_by_coords()` cache contract with `.sha256` verification, Antártica hole acknowledged. Any promotion must keep the generalization disclaimer and the checksum contract.
- ADR-023: chile-hub is downstream of official sources, never "official". Keep attribution to BCN (`bcn.cl/siit/mapas_vectoriales`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Drift Baseline | `git diff --stat bd77d34..HEAD -- data/source_registry.json data/dataset_catalog_config.json` | executed | exit 0; empty means no drift |
| Geometry count | `./.venv/bin/python -c "import polars as pl; print(pl.read_parquet('data/normalized/geometria_comunal.parquet').height)"` | executed | `345` (warnings about `geoarrow.wkb` extension are benign) |
| Catalog outputs check | `./.venv/bin/python -c "import json; c=json.load(open('data/dataset_catalog_config.json')); print([k for k,v in c.items() if 'outputs' not in v])"` | executed | lists the three keys without outputs (pre-change) |
| Focal tests | `./.venv/bin/pytest tests/test_phase2_datasetspec.py tests/test_builders_artifacts.py -q` | declared | all pass |
| Full suite | `make test` | declared | verde (reads `data/normalized/`, does not run pipeline) |
| Lint/format | `make lint && make format-check` | declared | exit 0 |
| Doctor + gates | `make doctor` | declared | exit 0 (runs `check_companion_paths.py registry`, `sync_docs.py --check`, `check_agents_sync.py`) |
| Contract check | `./.venv/bin/python scripts/check_companion_paths.py registry` | declared | exit 0 |

## Suggested executor toolkit

- Read `docs/adr/ADR-012-*.md` (exact filename via `ls docs/adr/ | grep 012`) before Step 1; quote its Antártica + generalization language verbatim in docs changes.

## Scope

**In scope** (the only files you should modify):

- `data/dataset_specs/geometria_comunal.json` (`publication_track`, `maturity_status`, `public_bundle_eligible`, `outputs`, `source.next_action`, `source.review_by` — the render-effective copy via the spec overlay)
- `data/source_registry.json` (geometria entry: track/eligibility/review outcome — keep identical to the spec projection; Phase-2 equivalence tests enforce this)
- `data/dataset_catalog_config.json` (geometria entry: add `outputs`, fix description if needed — keep identical to the spec projection)
- `docs/datasets/geometria_comunal.md` (promotion note, Antártica exception, bundle inclusion)
- `contracts/datasets/geometria_comunal.schema.json` (already has `expected_record_count: 345` + `coverage_policy: "partial"` — touch ONLY if Step 1-Q4 proves the publication gate rejects it)
- `tests/test_ci_config.py` or `tests/test_phase2_datasetspec.py` (1–3 guardrails for the new invariant)
- `plans/README.md` (status row only — SKIP per dispatcher override; reviewer owns the index)

**Out of scope** (do NOT touch, even though they look related):

- `src/extractors/geometria_comunal_extractor.py` — fetch logic is settled; no endpoint change in this plan.
- `src/chile_hub/geo.py` / `resolve_by_coords()` — consumer stays as-is.
- `index.html` / `app.js` / landing map — no visual change; the map already reads the Pages artifact.
- `.github/workflows/geometria-comunal.yml` — cadence change (manual → scheduled) is a separate decision; document as deferred.
- Any new dataset, any change to `delincuencia_comunal` or `autoridades_locales` lanes.
- The public ZIP itself — it is generated by `make build` / release assets, never hand-edited.

## Git workflow

- Branch: `advisor/139-geometria-stable-promotion`
- One commit per step below; message style follows repo (`tipo(scope): mensaje`, e.g. `feat(geometria): promote candidate to stable_publishable with Antartica exception` — see `git log --oneline -10` for examples).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

On the unmodified checkout, run: focal geometry count (expect 345), catalog outputs check (expect the 3-key list), `./.venv/bin/pytest tests/test_phase2_datasetspec.py -q`, `make doctor`. Record results.

- If a `declared` command does not exist or fails on the unmodified checkout: STOP and report (broken baseline, not your regression).
- If the geometry count is not 345: STOP and report (source changed; the promotion premise is void).

**Verify**: all baseline commands match Expected above.

### Step 1: Spike the promotion cost (measure, don't change)

Answer these five questions with commands, and write the answers into the plan's working notes (do not edit source yet):

1. Byte size of `data/normalized/geometria_comunal.parquet` + `.sha256` (`ls -lh`). Impact on ZIP/bundle and on the 500 KB guard (which the geometria workflow bypasses by allowlist — confirm the allowlist entry).
2. Does `src/builders/artifacts.py` include geometry in the ZIP once `outputs` + `public_bundle_eligible: true` are set, or does it need an explicit suffix/allowlist change (`.parquet` vs GeoParquet)? Read the filter function; do not change it.
3. Does the HF publish script (`scripts/publish_hf_dataset.py`) pick up geometry automatically via `publication_track`, and does the HF dataset viewer render GeoParquet usefully or confusingly?
4. Does `contracts/datasets/geometria_comunal.schema.json` already carry a `coverage_policy` that tolerates 345/346, or would `verify_pipeline.py --profile publication` fail on the missing Antártica row? (Compare with how SIEDU's partial coverage is declared — `coverage.expected: true` pattern from archived plan 066.)
5. Confirm Antártica `12202` is absent in the live parquet (`filter codigo_comuna == "12202"` → 0 rows) and present in `comunas` (→ 1 row). This is the exception to document.

**Verify**: five written answers with command outputs; if Q4 shows the publication gate would fail, the plan's Step 2 must include the contract carve-out — otherwise STOP and report the gate text.

### Step 2: Promote the lane in spec + registry + catalog (all three together)

1. In `data/dataset_specs/geometria_comunal.json` FIRST (render-effective copy): set `publication_track: stable_publishable`, `public_bundle_eligible: true`, `maturity_status: stable` (only if the Step-1 gate analysis supports it; otherwise keep `candidate` + new `source.review_by` and STOP for a maintainer decision — do not half-promote). Update `source.review_by` to the decision date + 12 months, rewrite `source.next_action` to the post-promotion monitor (endpoint stability + Antártica watch), and add the `outputs` block if absent (mirror the real artifact paths: `parquet: data/normalized/geometria_comunal.parquet`, plus `json` only if that artifact is actually generated — check first).
2. Mirror the SAME values into `data/source_registry.json` and `data/dataset_catalog_config.json` (track/eligibility/maturity/review_by/next_action/description/outputs). The Phase-2 equivalence tests (`test_all_specs_catalog_entries_equal_legacy`, `test_all_specs_source_registry_entries_equal_legacy`, `test_overlay_is_semantically_identical_to_legacy`) require legacy ≡ spec; keep them byte-consistent in meaning.
3. Keep the description's generalization + attribution sentences; append one sentence: stable since <date>, 345/346 comunas (Antártica `12202` absent upstream, see ADR-012). Same text in spec `documentation.description` and legacy catalog.

**Verify**: `./.venv/bin/python scripts/check_companion_paths.py registry` → exit 0; `./.venv/bin/pytest tests/test_phase2_datasetspec.py -q` → all pass (equivalence holds); `make doctor` → exit 0; `git diff --stat` lists only spec + the two legacy JSONs.

### Step 3: Docs + contract carve-out + guardrails

1. `docs/datasets/geometria_comunal.md`: add promotion note (date, bundle inclusion, 345/346 with Antártica exception, EPSG:4326 + generalization disclaimer verbatim from ADR-012, `resolve_by_coords()` pointer).
2. If Step 1-Q4 requires it: add the minimal `coverage_policy`/`expected` allowance to the schema contract following the SIEDU precedent (boolean `expected` + `expected_reason`, no enum change). Otherwise leave the contract untouched.
3. Add 1–3 tests: (a) geometry is `stable_publishable` + eligible in registry; (b) catalog entry has `outputs.parquet` pointing at an existing file; (c) Antártica exception is explicit (registry `next_action` or contract reason mentions `12202`). Model after `tests/test_ci_config.py` guardrail style (text/structure checks with incident docstrings).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py tests/test_phase2_datasetspec.py -q` → all pass; `make lint && make format-check` → exit 0.

### Step 4: Full verification (no data rebuild required)

Run `make test` and `make doctor`. Do NOT run `make build`/`make extract` (geometry refresh is manual/out-of-band; a full rebuild is unnecessary to validate metadata promotion and risks touching 21 other lanes).

**Verify**: `make test` verde; `make doctor` exit 0; `git diff --name-only bd77d34...HEAD` (three dots) lists only in-scope files.

## Test plan

- New tests (in `tests/test_ci_config.py` or `tests/test_phase2_datasetspec.py`, following existing guardrail patterns): registry track/eligibility assertion; catalog `outputs` existence assertion; Antártica-exception explicitness assertion.
- Existing pattern: `AutoridadesElectasScraplingGuardrailTests`-style docstring citing the incident/decision (here: review_by 2026-10-21 + ADR-012).
- Verification: focal pytest → all pass, including the new tests; `make test` → verde.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `pl.read_parquet('data/normalized/geometria_comunal.parquet').height == 345` and `12202` absent (exception documented, not silently dropped)
- [ ] Registry AND spec geometria entries have `publication_track == stable_publishable` and `public_bundle_eligible is True`, identical in both copies (or an explicit maintainer-signed decision to keep candidate with a new `review_by`)
- [ ] Catalog AND spec geometria entries have `outputs.parquet` pointing at a file that exists
- [ ] `tests/test_phase2_datasetspec.py` verde (legacy ≡ spec equivalence holds after the edit)
- [ ] `scripts/check_companion_paths.py registry` exits 0 and `make doctor` exits 0
- [ ] `make test` verde including the new guardrail tests
- [ ] `make lint && make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The parquet count is not 345 or `12202` is present/absent opposite to Current state (source changed).
- `verify_pipeline.py --profile publication` logic (read, do not run destructive) would reject 345/346 and the SIEDU-style carve-out does not cleanly apply.
- Promotion requires changing `src/builders/artifacts.py` filter logic or the ZIP allowlist beyond adding `outputs` (larger blast radius than this plan).
- HF viewer renders the GeoParquet in a way that misleads (e.g. failed preview presented as data error) — report, do not hack the card.
- Any step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If a scheduled refresh cadence for geometry is later adopted, revisit `.github/workflows/geometria-comunal.yml` wiring and the `review_by` monitor text.
- Reviewer should scrutinize: the exact registry/catalog diff (no other lane touched), the Antártica wording (must match ADR-012, not invent a new explanation), and that no extractor/consumer code changed.
- **Deferred:** automatic scheduled refresh of geometry (needs maintainer decision; manual lane stays until then) — unblocked by nothing except that decision.
- **Deferred:** Antártica `12202` backfill if BCN ever publishes it — the exception test will start failing, which is the intended signal.
