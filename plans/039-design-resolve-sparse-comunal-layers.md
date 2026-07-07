# Plan 039 (design/spike): Resolve the three comunal layers shipping at 3/346 rows in the public bundle

> **Executor instructions**: This is a **design/spike** plan. Its deliverable is a
> written decision + a small amount of enabling code/config, NOT a full feature build.
> Do not promote or delete data on your own judgment — produce the analysis and the
> recommended action, run the reversible config change only if the "Decision" step
> reaches a clear conclusion, and update `plans/README.md` when done.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- data/source_registry.json data/normalized/dataset_catalog.json`
> and re‑confirm the live row counts (Step 1) before deciding.

## Status

- **Priority**: P2
- **Effort**: M (per dataset; spike itself is S)
- **Risk**: MED
- **Depends on**: 024 (fixes the CUT bug that blocks `consumo_electrico` live data), 034 (fixes the SINIM refresh that blocks `finanzas_municipales`)
- **Category**: direction
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

Three comunal layers are in the **public bundle** at **3 of 346** communes:
`pobreza_comunal`, `consumo_electrico_comunal`, and `finanzas_municipales`. The project's stated
identity is "menos datasets, más limpios y confiables" and its trust story is that bundled data is
clean and join‑ready on `codigo_comuna`. Three near‑empty layers directly contradict that and quietly
poison any cross‑dataset join. `docs/backlog/08-evaluacion-producto-comercial.md` already flags these as
a blocker. Two of the three are stuck for reasons other plans fix (the `consumo_electrico` CUT bug in
Plan 024; the broken SINIM monthly refresh in Plan 034), so this spike decides, per dataset, whether to
**fill coverage** or **re‑carril to `candidate`** (out of the public bundle) so the bundle honors the promise.

## Background the executor needs

- Datasets have a maturity "carril": `stable_publishable` (in the public bundle) vs `candidate`
  (excluded). This is recorded in `data/source_registry.json` (fields like `maturity_status`,
  `public_bundle_eligible`) and enforced by the bundle builder + `verify_pipeline.py`. Re‑carriling a
  dataset to `candidate` is the reversible mechanism to remove it from the public bundle without deleting it.
- The three extractors exist: `src/extractors/pobreza_extractor.py`,
  `src/extractors/consumo_electrico_extractor.py`, and (live) `src/extractors/sinim_finanzas_live_extractor.py`.
- `docs/dataset-ideas/README.md` marks pobreza/consumo as `accepted` ("fuente XLSX comunal verificada");
  `docs/backlog/scorecard.md` records SINIM as effectively blocked (JS/POST portal, no API).

## Deliverable

A short decision doc `docs/adr/NNN-comunal-coverage-decision.md` (follow the existing `docs/adr/` format)
that, **for each of the three datasets**, records: current coverage, root cause of the gap, whether the
source can realistically reach ~346 communes, and the chosen action — **FILL** or **RE‑CARRIL to candidate** —
with the evidence. Plus the reversible config change implementing any RE‑CARRIL decision.

## Steps (spike)

### Step 1: Measure and attribute the gap

For each dataset, record the live row count (`.venv/bin/python -c "import polars as pl; print(pl.read_parquet('data/normalized/<name>.parquet').height)"`) and read its extractor's `fetch_data`/fallback path
to determine WHY it's at 3 rows (live fetch failing? enrichment dropping rows? source genuinely partial?).
Cross‑reference Plan 024 (consumo CUT bug → validation abort → stuck on fallback) and Plan 034 (SINIM
`--group dev` install bug → monthly refresh never runs).

### Step 2: Assess tractability per source

- `consumo_electrico_comunal` (CNE Energía Abierta XLSX): with Plan 024's CUT fix, does a live fetch produce
  ~all communes? Run the extractor (or inspect a raw snapshot in `data/raw/`) and record the achievable coverage.
- `pobreza_comunal` (MDS Observatorio Social / CASEN SAE): is the comunal XLSX complete for 346 communes?
- `finanzas_municipales` (SINIM): with Plan 034 fixing the monthly scrape, does it reach ~345 municipalities?
  (The audit found the live path yields ~345 rows when it runs.)

### Step 3: Decide per dataset (FILL vs RE‑CARRIL)

- **FILL** if the source is reachable and the coverage gap is a fixable extractor bug (likely `consumo_electrico`
  after 024, likely `finanzas_municipales` after 034). Scope the extractor work as a follow‑up implementation
  plan (one per dataset) — do NOT build it in this spike.
- **RE‑CARRIL to `candidate`** if the source cannot realistically reach full coverage (record the evidence).
  Implement by setting the dataset's `maturity_status`/`public_bundle_eligible` in `data/source_registry.json`
  so it drops from the public bundle, then `make build` and confirm the bundle no longer contains it.

### Step 4: Implement only the reversible RE‑CARRIL changes; write the ADR

Apply any RE‑CARRIL config change, rebuild, and confirm `verify_pipeline.py --profile readiness` still passes
and the 3‑row layer is gone from `chile-hub-publishable-bundle.zip`. Record all three decisions in the ADR.

## Done criteria

- [ ] `docs/adr/NNN-comunal-coverage-decision.md` exists with a FILL/RE‑CARRIL decision + evidence for each of the 3 datasets
- [ ] Any RE‑CARRIL decision is implemented in `data/source_registry.json`, `make build` passes, and the dataset is absent from the public bundle (`unzip -l data/normalized/chile-hub-publishable-bundle.zip | grep <name>` → empty)
- [ ] FILL decisions are written up as follow‑up plan stubs (title + scope) appended to `plans/README.md` backlog
- [ ] No public bundle still contains a <50%‑coverage layer that the ADR marked RE‑CARRIL
- [ ] `plans/README.md` status row updated

## STOP conditions

- If measuring coverage requires running network extractors and no network/build env is available, produce the
  decision framework from the raw snapshots + source docs and mark the coverage numbers as "to confirm."
- If a RE‑CARRIL would break a contract test that hardcodes the dataset as publishable, report it — the test must
  be updated deliberately as part of the decision.

## Maintenance notes

- This spike depends on 024 and 034 landing first; running it before them would mis‑attribute the gaps as
  source problems rather than the known bugs.
- Re‑carriling is reversible: once an extractor reaches full coverage it can be promoted back to `stable_publishable`
  (the Plan 009 carril mechanism). The ADR should say what coverage threshold justifies promotion.
