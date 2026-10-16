# Plan 143: Fix finanzas_municipales credibility gap (stale docs + monthly lane)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- data/dataset_catalog_config.json data/source_registry.json data/dataset_specs/finanzas_municipales.json contracts/datasets/finanzas_municipales.schema.json data/staging/finanzas_municipales.metadata.json src/extractors/sinim_finanzas_live_extractor.py src/extractors/_sinim_shared.py src/builders/datasets.py src/registry/dataset_spec.py src/builders/_shared.py docs/datasets/finanzas_municipales.md .github/workflows/monthly-scrape.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **History (2026-10-15)**: first execution (`advisor/143-finanzas-credibility`, clean worktree, no commits) reached a documented STOP: editing the legacy JSONs alone does not change rendered output because the DatasetSpec overlay shadows them (see "Current state — overlay mechanism"). Verdict on the data stands: **(B) 345 live rows real but aging** (last monthly success 2026-09-01; missing comuna = Antártica `12202`). This re-scoped revision adds the spec + contract files to Scope and Step 2. Re-execution starts at Step 0.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: LOW-MED
- **Depends on**: none (docs-first; extractor work only if the spike finds rot)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

The catalog tells users `finanzas_municipales` covers "3 de 346 comunas (0.9%) — usar con precaución; no representa cobertura nacional", while the actual normalized parquet holds **345 rows** from a live SINIM scrape (`source_mode: monthly`, `record_count: 345`). One of the two is stale, and a flagship derived layer (`perfil_territorial_comunal`) left-joins these finances into every comuna row. Either users distrust good data or they trust bad data — both corrode the fail-loud promise. The fix is mostly editorial (sync the description, declare the coverage honestly) plus pinning the monthly lane that the registry says is still pending (workflow 3.3 + cadence metadata 3.4).

## Current state

Relevant files and roles:

- `data/dataset_catalog_config.json:343-356` — finanzas entry: `description: "Indicadores financieros municipales anuales desde SINIM/SUBDERE. CAPA PARCIAL/CANDIDATO: 3 de 346 comunas (0.9%). Usar con precaución; no representa cobertura nacional."`, `coverage_note: parcial_candidato_3_de_346_comunas`, `coverage_pct: 0.9`, `expected_record_count: null`. This text is also rendered into the README layers table via `doc_sync.py`.
- `data/source_registry.json:217-238` — finanzas entry: `live_extractor_status: implemented`, `publication_track: stable_publishable`, `public_bundle_eligible: true`, `source_mode: mensual`, `next_action: "Fase 3.2 PoC exitoso: extractor live implementado (sinim_finanzas_live_extractor.py). Cobertura 345/346 municipios (2024). Pendiente: workflow mensual (3.3) y metadata de cadencia (3.4)."`
- `data/staging/finanzas_municipales.metadata.json` — `source_mode: monthly`, `record_count: 345`, notes: `live: Playwright configurando filtros SINIM / descargando XML Spreadsheet / parseando XML Spreadsheet / 345 municipios extraídos (snapshot: sinim_finanzas_municipales_20260901T030218Z.xlsx)`.
- Verified (2026-10-15): `pl.read_parquet('data/normalized/finanzas_municipales.parquet').height == 345` with 345 distinct `codigo_comuna`; staging CSV dated 2026-07-08, metadata 2026-09-01 (over a month old at planning — check freshness policy `max_age_hours: 8760` = annual, so not stale by policy, but confirm).
- `src/extractors/sinim_finanzas_live_extractor.py` + `src/extractors/_sinim_shared.py` (Plan 099) — live scraper + shared normalization/metadata; stub `sinim_finanzas_extractor.py` is dev-fallback only and must never run in scheduled jobs (`SinimDailyJobGuardrailTests`).
- `src/builders/datasets.py:115-129` — perfil takes `latest_finanzas` (latest `anio` per comuna); a 3-row upstream would null out 343 comunas silently, a 345-row upstream fills them. The join works either way — the lie is in the docs, not the code.
- `.github/workflows/monthly-scrape.yml` — monthly lane for the live extractor (verify existence + schedule in Step 1; `AGENTS.md §3` says the stub never runs in scheduled jobs). Spike 2026-10-15 verified: cron `0 3 1 * *`, line 62 runs the LIVE extractor (`uv run python src/extractors/sinim_finanzas_live_extractor.py`), stub absent from all scheduled paths, `SinimDailyJobGuardrailTests` present. Last success 2026-09-01; the 2026-10-01 run failed at "Rebuild normalized artifacts" while extract + validate succeeded → extractor healthy, snapshot retained (verdict **B**).
- **Overlay mechanism (read this — it determines where the fix goes).** `src/builders/_shared.py::_load_catalog_config()` loads the legacy catalog JSON and then applies `catalog_config_with_spec_overlay()` (`src/registry/dataset_spec.py:671-682`): every dataset WITH a spec file gets its catalog entry REPLACED by `spec.to_catalog_entry()`. That projection takes `description` from the spec's `documentation.description` and `expected_record_count` mechanically from the referenced contract (`dataset_spec.py:243-254`), not from the legacy JSON. A parallel `source_registry_with_spec_overlay()` does the same for the registry. Consequence: for `finanzas_municipales` (spec exists at `data/dataset_specs/finanzas_municipales.json`, verified stale: `coverage_note: parcial_candidato_3_de_346_comunas`, `coverage_pct: 0.9`, same stale `next_action`), editing ONLY the legacy JSONs changes nothing rendered — `make sync-docs` reports "sin cambios" and the Phase-2 equivalence tests (`test_all_specs_catalog_entries_equal_legacy`, `test_all_specs_source_registry_entries_equal_legacy`, `test_overlay_is_semantically_identical_to_legacy`) fail. The spec file and the legacy JSONs must be edited TOGETHER so the equivalence tests stay green. The contract already carries `coverage_policy: partial_expected`, so no other contract change is expected beyond `expected_record_count`.

Conventions that apply:

- Single-source rule (`AGENTS.md §12`): catalog JSON is the truth for what exists; README/doc text derived via `doc_sync.py` delimited blocks. Fix the JSON, regenerate (`make sync-docs` or the `build_dev_db.py` auto-sync), verify with `scripts/sync_docs.py --check` in `make doctor`.
- Freshness labels: catalog `freshness_policy: {max_age_hours: 8760, label: anual}` for finanzas. Monthly-scrape cadence vs annual freshness must read coherently after the fix.
- Legal: SINIM page carries CC BY 2.0 CL + "sin fines comerciales"; chile-hub is non-commercial MIT. Keep the `reuse_policy` attribution wording; this plan does not relitigate the license.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Coverage truth | `./.venv/bin/python -c "import polars as pl; df=pl.read_parquet('data/normalized/finanzas_municipales.parquet'); print(df.height, df.select('codigo_comuna').n_unique(), sorted(df.select('anio').unique().to_series().to_list()))"` | executed | `345 345 [latest-year-list]` (pre-change) |
| Catalog text | `./.venv/bin/python -c "import json; c=json.load(open('data/dataset_catalog_config.json')); print(c['finanzas_municipales']['description']); print(c['finanzas_municipales'].get('coverage_note'), c['finanzas_municipales'].get('coverage_pct'))"` | executed | the stale 3-comuna text (pre-change) |
| Staging meta | `cat data/staging/finanzas_municipales.metadata.json` | executed | `record_count: 345`, `source_mode: monthly` (pre-change) |
| Monthly lane | `ls .github/workflows/monthly-scrape.yml && grep -n -i "sinim\|finanzas" .github/workflows/monthly-scrape.yml \| head` | declared | file exists; sinim lines present (to confirm) |
| Focal tests | `./.venv/bin/pytest tests/test_extractors.py -q -k "Sinim" tests/test_ci_config.py -q` | declared | all pass |
| Doctor + sync check | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `data/dataset_specs/finanzas_municipales.json` (description, coverage fields, `source.next_action` — the render-effective copy)
- `data/dataset_catalog_config.json` (finanzas `description`, `coverage_note`, `coverage_pct`, `expected_record_count` — keep identical to the spec projection; the Phase-2 equivalence tests enforce this)
- `data/source_registry.json` (finanzas `next_action` — close or re-state the pending 3.3/3.4 items only; keep identical to the spec projection)
- `contracts/datasets/finanzas_municipales.schema.json` (`expected_record_count: 345` — the spec projects this field from the contract; plus a minimal SIEDU-style `coverage_policy` only if the 345/346 gap needs one beyond the existing `partial_expected`)
- `docs/datasets/finanzas_municipales.md` (coverage + cadence section)
- `tests/test_ci_config.py` (1 guardrail: catalog coverage text matches built row counts)
- `plans/README.md` (status row only — SKIP per dispatcher override; reviewer owns the index)

**Out of scope** (do NOT touch, even though they look related):

- `src/extractors/sinim_finanzas_live_extractor.py` and `_sinim_shared.py` — no scraper change unless Step 1 proves rot (then STOP and file a follow-up; do not expand scope).
- `.github/workflows/monthly-scrape.yml` schedule itself — verify only; rescheduling is a maintainer decision.
- `src/builders/datasets.py` perfil join — works regardless of coverage; no change.
- `reuse_policy`/license text — settled; do not relitigate.
- Any other dataset's catalog entry.

## Git workflow

- Branch: `advisor/143-finanzas-credibility`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `docs(finanzas): sync catalog coverage with 345-row live build`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run the three truth commands; record heights, description text, and staging metadata. Run focal Sinim tests + `make doctor`.

**Verify**: parquet 345/345; catalog still says 3 comunas (the drift this plan fixes); doctor green.

### Step 1: Spike the monthly lane (verify, don't change)

1. Confirm `.github/workflows/monthly-scrape.yml` exists, runs the **live** extractor (not the stub), and on what schedule (`grep -n "sinim\|schedule\|cron"`). Record the last successful run date (GH UI or `gh run list` if available; otherwise note "operator to confirm" — do not guess).
2. Confirm `SinimDailyJobGuardrailTests` still pins the stub out of scheduled jobs (`grep -n "SinimDailyJob" tests/test_ci_config.py`).
3. Decide which of three truths holds and write it down: (A) 345-row live coverage is real and current → docs fix only; (B) 345 rows are real but aging (last live fetch > freshness window or last monthly run failed) → docs fix + freshness/`next_action` update; (C) live extractor rotted and the build silently fell back → STOP, do not fix docs to match rotten data; file the extractor-rot finding instead.

**Verify**: written (A)/(B)/(C) verdict with command outputs; proceed to Step 2 only on (A) or (B).

### Step 2: Sync spec + legacy JSONs + contract + doc (all four together)

1. Rewrite the description to the measured truth in BOTH `data/dataset_specs/finanzas_municipales.json` (`documentation.description`) AND `data/dataset_catalog_config.json` (draft verified 2026-10-15: `Indicadores financieros municipales anuales desde SINIM/SUBDERE. Cobertura 345/346 comunas (año 2024; falta Antártica 12202, hueco conocido de la fuente). Extracción mensual vía monthly-scrape.` — mirrors the geometria_comunal 12202 wording; adjust only if Step-0 output differs). Remove or correct `coverage_note`/`coverage_pct: 0.9` in both files.
2. Set `expected_record_count: 345` in `contracts/datasets/finanzas_municipales.schema.json` (this is the field the spec projection actually reads; setting it only in the catalog JSON is a no-op). Prefer the number; keep `null` only with a written reason.
3. Update `next_action` in BOTH the spec (`source.next_action`) and `data/source_registry.json`: close 3.3/3.4 as done only with run-date evidence (monthly lane verified live 2026-09-01), otherwise restate with owner + date. Do not leave the 2026-06-30-era "Pendiente" text if it is done.
4. Update `docs/datasets/finanzas_municipales.md` coverage + cadence section to match; regenerate README blocks (`make sync-docs` or the documented sync command) so the layers table stops saying 0.9%. NOTE: if the sync command modifies README.md (not in scope), leave that hunk uncommitted and report it in NOTES.
5. If the 345/346 gap needs more than the existing `coverage_policy: partial_expected`, add the minimal SIEDU-style allowance; otherwise leave the rest of the contract untouched.

**Verify**: catalog truth command prints the new text; `./.venv/bin/pytest tests/test_phase2_datasetspec.py -q` → all pass (equivalence holds); `make doctor` (includes `sync_docs --check`) → exit 0; `git diff --stat` shows only spec + legacy JSONs + contract + doc files.

### Step 3: Guardrail against re-drift

Add one test in `tests/test_ci_config.py` asserting catalog coverage text and built row counts agree (e.g. parse `coverage_pct`/`expected_record_count` vs a recorded-build fixture or a documented threshold — do not read the 17 KB parquet in a text-guardrail test if the file's slow-path precedent says otherwise; prefer asserting that the stale `3 de 346` / `0.9` literals are gone and `expected_record_count` is non-null). Docstring cites this plan + the stale-text incident.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -q` → pass including the new test.

## Test plan

- New guardrail test as above, modeled on existing `test_ci_config.py` text-guardrail style (small, targeted, with incident docstring).
- No extractor/builder unit change expected; existing Sinim + pipeline tests must stay green.
- Verification: focal pytest → pass; `make test` → verde.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] Catalog AND spec finanzas `description` no longer claim 3 comunas / 0.9%; state measured coverage + year (both copies identical)
- [ ] Contract `expected_record_count == 345` (or a written reason exists in the executor report)
- [ ] `tests/test_phase2_datasetspec.py` verde (legacy ≡ spec equivalence holds after the edit)
- [ ] Registry `next_action` (both copies) reflects the verified monthly-lane state (closed or dated, not stale "Pendiente")
- [ ] `make doctor` exits 0 (README/doc blocks re-synced)
- [ ] New anti-drift guardrail test exists and passes
- [ ] `make test` verde; `make lint && make format-check` exit 0
- [ ] Step-1 verdict was (A) or (B) with evidence (on (C), this plan correctly STOPped instead)
- [ ] `git diff --name-only bd77d34...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Verdict is (C) — live extractor rotted or build is on fallback rows (do not paper over rotten data with new docs).
- Monthly workflow does not run the live extractor or the stub appears in any scheduled path (guardrail breach — report, do not rewire CI here).
- Fixing the description requires changing `reuse_policy`/license semantics (legal scope — report).
- Any step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- The next SINIM schema change will break the scraper before it breaks these docs; the guardrail catches text drift, not source drift — source health stays on `hub_health` + the monthly job.
- Reviewer should scrutinize: the exact coverage sentence (year + missing-comuna honesty), that `coverage_pct` was removed-or-corrected (not left at 0.9), and that no extractor file changed.
- **Deferred:** rescheduling or hardening the monthly scrape itself — unblocked by the maintainer + Step-1 run-date evidence.
- **Deferred:** backfilling the 346th comuna if the missing row is systematic (spike 2026-10-15 identified it as Antártica `12202`, no municipal admin in SINIM — consistent with the geometria hole; do not invent data).
- **Deferred (incidental finding, spike 2026-10-15, untouched per scope):** `.github/workflows/monthly-scrape.yml:83` runs bare `python src/build_dev_db.py` while the extract step uses `uv run` — the 2026-10-01 run failed exactly at that rebuild step after a successful scrape. Maintainer should confirm the runner's `python` resolves to the pipeline venv; if not, that one-line fix (`uv run python`) belongs in a CI hygiene commit, not in this docs plan.
