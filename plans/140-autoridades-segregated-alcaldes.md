# Plan 140: Segregate autoridades_locales for stable alcaldes publication

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- data/source_registry.json data/dataset_catalog_config.json src/extractors/autoridades_locales_extractor.py src/validation/_politica.py docs/datasets/autoridades_locales.md contracts/datasets/autoridades_locales.schema.json`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: LOW-MED
- **Depends on**: none (design/spike; implementation would follow maintainer license decision)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

`autoridades_locales` is the only lane where the blocker is fully diagnosed: 346/346 alcaldes come from BCN SIIT (government public data) while 16 gobernadores come from Wikipedia (CC-BY-SA share-alike). The single `redistribution_ok: false` flag blocks all 362 rows from the public bundle. Segregating the publishable alcaldes from the share-alike gobernadores unlocks a complete national authority layer without violating the license — exactly the "depth over breadth" growth ADR-011 allows. Today the lane has no staging or normalized artifacts at all (verified by missing files), so the first deliverable is a decision + spike, not a bundle flip.

## Current state

Relevant files and roles:

- `data/source_registry.json:466-485` — `autoridades_locales` entry: `source_name: Wikipedia (CC-BY-SA)`, `maturity_status: candidate`, `publication_track: candidate`, `public_bundle_eligible: false`, `review_by: 2026-12-31`, `next_action: "la brecha de alcaldes quedó resuelta al migrar la fuente primaria a BCN SIIT (346/346 comunas). El único bloqueo para promover a stable_publishable es la licencia CC-BY-SA de los gobernadores obtenidos desde Wikipedia; buscar fuente institucional no-share-alike o definir publicación segregada compatible."`
- `data/dataset_catalog_config.json:703-729` — `autoridades_locales` entry: `expected_record_count: 362`, `reuse_policy: {status: open-attribution, license: "CC BY / CC BY-SA", redistribution_ok: false}`, summary ends with `"Carril CANDIDATE — NO redistribuible en el bundle público mientras los gobernadores dependan de fuente share-alike."` No `outputs` key (one of three keys without it).
- `src/extractors/autoridades_locales_extractor.py` — extractor exists (listed in `AGENTS.md §2` as ad-hoc, no daily cadence, candidate lane). It mixes two provenances in one CSV: alcaldes (BCN SIIT) + gobernadores (Wikipedia).
- `src/validation/_politica.py` — `validate_autoridades_*` functions live here (domain submodule; imported by `build_dev_db.py` per `AGENTS.md §5 Paso 4`).
- Verified during recon: `ls data/staging/autoridades_locales* data/normalized/autoridades_locales*` → both missing (no files). Contrast `autoridades_electas` (205 rows, stable, separate lane for diputados/senadores). The segregation premise (alcaldes vs gobernadores) matches the existing split between `autoridades_electas` (national) and `autoridades_locales` (subnational).

Conventions that apply:

- Legal semaphore (`AGENTS.md §6`): 🟢 `open-attribution` ships in bundle; 🔴 `restricted`/non-redistributable never ships. CC-BY-SA share-alike on a subset must not contaminate the clean subset — precedent is the existing `autoridades_electas` vs `autoridades_locales` split itself.
- New-dataset flow (`AGENTS.md §5`): extractor → catalog JSON (not code literal) → `validate_*()` in `src/validation/` + registration in `build_dev_db.py` `validations = {...}` → tests → CI → docs. A segregated `alcaldes` output follows the same steps; this plan only designs it.
- `check_companion_paths.py registry` requires every catalog key to have a contract + doc. Any new key (e.g. `alcaldes`) needs both.

Design constraints from intent docs:

- `docs/dataset-inclusion-criteria.md`: `under-review` tolerates source fragility but never personal-data or impossible-validation failures; share-alike is a redistribution (not validity) blocker → candidate lane, exactly where this sits.
- `docs/product-spec.md` + ADR-023: "La fuente oficial manda", "Lo abierto sigue abierto", never present chile-hub as official. Alcaldes must attribute BCN SIIT; gobernadores must attribute Wikipedia + share-alike terms.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Confirm missing artifacts | `ls data/staging/autoridades_locales* data/normalized/autoridades_locales*` | executed | both report "No existe" (pre-change baseline) |
| Read extractor head | `sed -n '1,80p' src/extractors/autoridades_locales_extractor.py` | declared | shows BCN SIIT + Wikipedia provenance |
| Focal validation tests | `./.venv/bin/pytest tests/test_validation.py -q -k "utoridad or olitica"` | declared | all pass |
| Doctor + registry gate | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `docs/datasets/autoridades_locales.md` (spike findings appendix — decision record, not a rewrite)
- `plans/140-*` working notes inside this plan file's Steps (no new source files)
- `tests/test_ci_config.py` (at most 1 guardrail pinning the segregation invariant, if the decision is taken; otherwise no test change)
- `plans/README.md` (status row only)

**Out of scope** (do NOT touch, even though they look related):

- `src/extractors/autoridades_locales_extractor.py` — no refactor in this design plan; implementation follows separately after the license decision.
- `data/source_registry.json` / `data/dataset_catalog_config.json` — do NOT flip any flag in this plan; write the exact diff as a proposal inside the doc appendix for maintainer approval.
- `autoridades_electas` lane, `partidos_politicos` lane, or any merge of national + local authorities.
- Contacting Wikipedia, BCN, SUBDERE, or any official body — operator-only actions.
- Any new `alcaldes` catalog key, contract, or doc file — deferred to the implementation plan.

## Git workflow

- Branch: `advisor/140-autoridades-segregation-spike`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `docs(autoridades): spike segregated alcaldes publication options`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Confirm the missing-artifact baseline (`ls` shows no files), run the focal validation tests and `make doctor`. Record outputs.

**Verify**: `ls` missing as above; pytest green; `make doctor` exit 0.

### Step 1: Provenance audit (read-only spike)

1. Read the full extractor (`src/extractors/autoridades_locales_extractor.py`) and list every outbound field populated from Wikipedia vs BCN SIIT (column-level provenance table: column → source → license implication).
2. Read `src/validation/_politica.py` for the autoridades validators; note whether validation distinguishes the two provenances or treats the lane as one blob.
3. Check whether any existing normalized consumer (perfil, comuna pages, landing) references `autoridades_locales` — `grep -rn "autoridades_locales" src/ index.html app.js | head -20`. Record hits.
4. Draft the two candidate segregation shapes and their trade-offs: (A) two catalog keys (`alcaldes` stable + `gobernadores_regionales` candidate) with separate contracts/docs/outputs; (B) one lane with row-level `redistribution_ok` filtering at bundle-build time (bundle includes only BCN-sourced rows). For (B), state precisely where the filter would live (`artifacts.py` vs extractor) and why (A) is preferred under the current "lane = bundle unit" architecture (cite plans 070/071).

**Verify**: a provenance table + (A)/(B) comparison written into the doc appendix draft; no source file modified (`git diff --name-only` shows only docs/working notes).

### Step 2: License decision package

Write the decision package as an appendix to `docs/datasets/autoridades_locales.md` (or a clearly-marked spike note if the maintainer prefers no doc churn — ask in the report, default to appendix):

1. Exact proposed registry/catalog diffs (unified-diff style, copy-pasteable) for option (A): new `alcaldes` entry (`publication_track: stable_publishable`, `public_bundle_eligible: true`, BCN SIIT attribution, `expected_record_count: 346`) + narrowed `autoridades_locales` or `gobernadores_regionales` candidate entry (CC-BY-SA, `redistribution_ok: false`). **Lesson from Plans 143/139 (mandatory):** every proposed diff MUST cover THREE copies — `data/dataset_specs/<dataset>.json` (render-effective via the spec overlay), the legacy `data/dataset_catalog_config.json` + `data/source_registry.json` (kept identical, Phase-2 equivalence tests enforce it), and `expected_record_count` via the contract (the spec projects it from there, not from the catalog JSON). A proposal covering only legacy JSONs is a no-op — the 143 executor proved it.
2. Three institutional-source leads for gobernadores that would remove the share-alike blocker entirely (e.g. Gobierno Regional / SUBDERE / SERVEL pages — verify each URL returns 200 with `curl -I`, record status codes; do not scrape).
3. Explicit recommendation (A vs B vs "keep candidate until institutional source found") with one-paragraph rationale tied to ADR-011 and the CC-BY-SA contamination risk.

**Verify**: `make doctor` still exit 0 (doc-only change passes `sync_docs --check` and `check_agents_sync`); the proposed diffs apply cleanly by inspection (paths + JSON keys exist).

### Step 3: Guardrail (only if decision is taken)

If the maintainer approves (A) in review: add one guardrail test asserting the segregation invariant (e.g. no Wikipedia-sourced row in the stable output path, or catalog `alcaldes` has `redistribution_ok: true` while `gobernadores*` has `false`). If no decision yet: skip code, leave the test as a named **Deferred** item.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -q` → all pass (or unchanged green if skipped).

## Test plan

- No new runtime tests in the spike path (decision precedes implementation).
- If decision taken: one guardrail in `tests/test_ci_config.py` modeled on existing lane guardrails, with a docstring citing this plan + the CC-BY-SA contamination risk.
- Verification: focal pytest green; `make doctor` green.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] Provenance table (column → source → license) exists in the spike output
- [ ] Options (A)/(B) documented with trade-offs and a named recommendation
- [ ] Proposed registry/catalog diffs are copy-pasteable and reference real keys/paths
- [ ] Three institutional-source leads listed with HTTP status evidence
- [ ] `make doctor` exits 0; `make lint && make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only docs/test-allowed + plan index files (no extractor/registry/catalog mutation unless maintainer approved)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The extractor's provenance split differs from Current state (e.g. gobernadores no longer Wikipedia-sourced) — the blocker premise changed.
- BCN SIIT alcaldes coverage is not 346/346 in the extractor's current logic (re-read; the registry claim may have drifted).
- Segregation would require changing the ZIP/bundle filter architecture (larger blast radius — report, do not redesign `artifacts.py` here).
- Any institutional source lead returns personal data or ambiguous redistribution terms — record as restricted, do not pursue scraping.

## Maintenance notes

- If an institutional gobernadores source is later found, the candidate entry can graduate without touching alcaldes; the guardrail will catch contamination regressions.
- Reviewer should scrutinize: the license reasoning (share-alike must not leak into the stable output), the exact JSON diffs (keys match `check_companion_paths.py` expectations), and that no lane flag was flipped without approval.
- **Deferred:** implementation of the approved segregation (new catalog key + contract + doc + extractor split + validation registration per `AGENTS.md §5`) — needs its own build plan after this spike.
- **Deferred:** scheduled refresh cadence for alcaldes (currently ad-hoc) — unblocked by the segregation decision.
