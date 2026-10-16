# Plan 144: Honest adoption funnel before the 2026-11-01 sustainability review

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- docs/sostenibilidad/README.md docs/sostenibilidad/auditoria-3-2026-09-29.md docs/adoption-review.md docs/launch-pack.md plans/107-activacion-lanzamiento-handoff.md plans/110-programa-de-patrocinios.md ROADMAP.md AGENTS.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S-M (operator-heavy; ≤15 h total per sustainability cap)
- **Risk**: LOW (no code, no external contact, no money ask)
- **Depends on**: none (reads 139–143 only for consistent numbers; no file overlap)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

The 2026-11-01 sustainability review is 17 days away and the standing verdict is D/HOLD: zero verified organizational users, PyPI downloads tracking release cadence (R² 0.94–0.97, ~80–100 per release), real activations ~27 bundle downloads/month, HF mirror at 274. Without an honest, telemetry-free funnel the review will re-derive the same D from the same vanity numbers, and the anti-patrón #10 gate ("no new datasets before validated adoption") stays frozen — blocking even the worthy depth work in plans 139–143 from being framed as demand. This plan builds the measurement the review needs: a documented funnel from public counters only, plus execution of the already-READY plan 107 discovery handoff inside its 15-hour, no-money-ask cap.

## Current state

Facts the executor needs (all read during recon; do not re-derive from memory):

- `docs/sostenibilidad/README.md:10-23` — **HOLD / sin búsqueda activa** (veredicto D aceptado 2026-09-30). Allowed: keep `FUNDING.yml` + CLI support note; run discovery experiment §E (max 15 h, no asking money); consult an accountant on vehicle (no external contact); serve inbound demand. Forbidden until gate §G: tiers/`SPONSORS.md`/landing sponsorship section; asking organizations/vendors/funders for money; executing `plans/110-programa-de-patrocinios.md` (HOLD); launching self-initiated service pilots without gate conditions 2, 3, 5; presenting PyPI downloads as installs/users/audience.
- `docs/sostenibilidad/auditoria-3-2026-09-29.md` §G (gate) + Annex M (refresh method for any cited figure) — the only honest way to quote numbers. Conclusions: (1) no identifiable buyer (0 dependents, 0 public importers, 0 third-party interactions, 0 sponsors); (2) PyPI measures cadence; (3) no vehicle to charge (no legal entity; Ley 21.440 blocks natural-person donations with tax benefit; public bodies buy via Compra Ágil, not sponsorships); (4) infra ≈ USD 0, scarce resource is maintainer time; (5–8) sponsorship-hours = cheap consulting, grants need institutional partner + usage evidence over 12–24 mo, CAF is for learning/network only after ≥3 verified orgs.
- `plans/107-activacion-lanzamiento-handoff.md` — READY (not DONE): external-agent handoff for GSC meta tag, sitemap, schedule, adoption tracking, with fallbacks + STOP. `plans/110-programa-de-patrocinios.md` — HOLD, do not execute.
- `ROADMAP.md §5/§7` — 107 READY; 110 HOLD with 2026-11-01 review; operator-only actions pending: register chile-hub in datos.gob.cl "Reutilización" (ClaveÚnica), request structured CEAD delincuencia via datos.gob.cl "Sugerencias" or Ley 20.285, report the dead 2015 bulk links via "Notifica un error", optionally present to SGD help desk re open-data technical norm. Zenodo DOI done (`10.5281/zenodo.22968698`).
- `AGENTS.md §10` antipattern — never present PyPI downloads as installs/users/audience; method lives in `docs/sostenibilidad/README.md` (Auditoría 3). `ROADMAP.md §8` rejected list — telemetry, premium API/paywall, English README, Kaggle/conda-forge (until HF effect measured), sigstore (until second publisher) stay rejected.
- Distribution baseline (all shipped): HF subsets + `hf://` (101), SEO/sitemap/`llms.txt` (102), citation/DOI (103), MCP server (104), comuna pages (105), HF metric 274 downloads (129), bundle activations ~27/mo (Auditoría 3 §G).

Conventions that apply:

- Agent rules (`docs/sostenibilidad/README.md:59-66`): no executing 110, no contacting sponsors/vendors/CAF/funders beyond the vigente state, never quote PyPI as audience (refresh via Annex M first), no publishing contact PII or commercial terms (tracker stays out of the repo, Ley 21.719), every new analysis registered in the chronology with date/document/result/status — and any contradiction of Auditoría 3 reconciled explicitly before changing state.
- Docs anti-drift (`AGENTS.md §12`): README numbers (test counts, ADR counts, contract counts, badge layers) are delimited-block generated via `doc_sync.py`; the funnel doc must not hardcode drifting counts — link to the live reports (`hub_health.md`, `dataset_quality.md`, `redistribution_report.md`) instead.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Baseline docs check | `make doctor` | declared | exit 0 (includes `sync_docs --check`, `check_agents_sync`) |
| Readiness | `./.venv/bin/python scripts/verify_pipeline.py --profile readiness --help 2>&1 \| head -20` | declared | help text (do not run full verify without a build) |
| Link hygiene | `grep -rn "2.2k\|2,218\|instalaciones\|usuarios" README.md docs/sostenibilidad/ docs/adoption-review.md 2>/dev/null \| head -20` | executed | locate any stale vanity phrasing to correct |
| Lint (docs only) | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `docs/adoption-funnel.md` (create — the honest funnel definition + refresh procedure; see Steps)
- `docs/sostenibilidad/README.md` (chronology entry only — date/document/result/status row for this experiment)
- `docs/adoption-review.md` (refresh numbers via Annex M method only, with dates; no narrative inflation)
- `plans/README.md` (status row only)

**Out of scope** (do NOT touch, even though they look related):

- `plans/110-programa-de-patrocinios.md` — HOLD; do not rewrite, retitle, or partially execute.
- `FUNDING.yml`, README sponsorship sections, landing sponsorship blocks — forbidden until gate §G.
- Any telemetry in the package, any paywall/premium API, any English README/docs.
- Contacting any organization, vendor, CAF, funder, or public body — operator-only; this plan prepares the one-pager they would receive, it does not send it.
- `AGENTS.md`, `ROADMAP.md` state tables (except the plans index row) — review outcomes are the maintainer's call on 2026-11-01.

## Git workflow

- Branch: `advisor/144-adoption-funnel`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `docs(adopcion): define honest adoption funnel for 2026-11-01 review`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run `make doctor` and the link-hygiene grep; record every vanity-phrased line found (file:line + quote). Do not fix yet.

**Verify**: doctor exit 0; vanity-line list recorded (possibly empty — record "none found" explicitly).

### Step 1: Define the honest funnel (document, no code)

Create `docs/adoption-funnel.md` with:

1. Funnel stages from **public counters only** (no telemetry): PyPI downloads (cadence-contaminated — always quoted with release-count normalization per Annex M), GitHub release-asset bundle downloads (primary activation signal), HF mirror downloads + per-config hits (discovery signal, plan 129 metric), comuna-pages/landing traffic (only if GSC/search-console access exists — otherwise "unmeasured, see 107"), downstream citations (DOI/Zenodo, scholarly mentions), verified organizational users (manual, out-of-repo tracker; definition of "verified" quoted from Auditoría 3).
2. For each stage: counter source, refresh command/URL, known confound (e.g. release cadence for PyPI), and the exact sentence allowed in external material (e.g. "≈27 bundle activations/month (2026-09, Auditoría 3 §G method)" — never "users").
3. Refresh procedure with dates: who runs it, how often (weekly until 2026-11-01, then per review cadence), and where the refreshed numbers land (`docs/adoption-review.md` dated entries — not README prose).
4. Explicit non-goals section restating the rejected list (telemetry, paywall, English docs, Kaggle/conda-forge until HF measured) with one-line rationale each, so the review does not re-litigate them.

**Verify**: `make doctor` → exit 0 (new doc does not break `check_agents_sync` — it checks only AGENTS/CLAUDE/SOURCE_OF_TRUTH facts, but confirm); new doc contains zero hardcoded drifting counts (grep for bare large numbers without dates fails clean).

### Step 2: Execute the 107 discovery remainder inside the cap

Read `plans/107-activacion-lanzamiento-handoff.md` fully, then execute only what fits ALL of: (a) inside the 15-hour §E cap, (b) no money ask, (c) no external contact, (d) reversible docs/config. Concretely: GSC meta-tag + sitemap verification steps, schedule sanity, and the adoption-tracking checklist — saltando anything requiring maintainer credentials (ClaveÚnica, Search Console ownership, HF_TOKEN) with a named "operator action" handoff list. Log hours spent per task in the plan report (cap accounting).

**Verify**: written hour log totaling ≤15 h; operator-action handoff list with exact URLs/steps for the credentialed items (datos.gob.cl reutilización registration, CEAD request, dead-link report, SGD desk) — prepared, not sent.

### Step 3: Refresh + chronology (no inflation)

1. Refresh `docs/adoption-review.md` numbers via the Annex M method with today's date; correct any vanity phrasing found in Step 0 to the allowed sentences from Step 1.
2. Append the chronology row in `docs/sostenibilidad/README.md` (date 2026-10-15, document `docs/adoption-funnel.md` + this plan, result "funnel defined; 107-remainder executed/logged; no state change", status "vigente — pending 2026-11-01 review").

**Verify**: `make doctor` → exit 0; `git diff` shows only the four in-scope paths.

## Test plan

- No code tests (docs + process plan). Verification is: `make doctor` green (anti-drift gates), grep checks for vanity phrasing returning empty post-fix, and the hour-log + handoff list existing.
- If any gate in `make doctor` touches the new doc unexpectedly, fix the doc (never the gate).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `docs/adoption-funnel.md` exists with stages, refresh procedure, allowed sentences, and non-goals
- [ ] `docs/adoption-review.md` numbers refreshed with dates via Annex M; Step-0 vanity lines corrected or confirmed absent
- [ ] Sustainability chronology row appended (no state change claimed)
- [ ] 107-remainder hour log ≤15 h + credentialed operator-action handoff list (prepared, not sent)
- [ ] Zero new telemetry, pricing, sponsorship, or English-doc surface
- [ ] `make doctor` exits 0; `make lint && make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Any step requires external contact, credentials, money ask, or PII in the repo (violates HOLD rules — stop, hand off to operator).
- Annex M refresh method is unreachable or its data sources changed (do not invent a new methodology — report).
- The 15-hour cap would be exceeded by the 107 remainder (stop, log, hand off — do not overrun).
- A finding contradicts Auditoría 3's verdict D (e.g. a verifiable org user appears) — reconcile explicitly per the sustainability rules before claiming any state change; default to reporting, not promoting.

## Maintenance notes

- The 2026-11-01 reviewer needs exactly three inputs from this plan: the funnel doc, the refreshed review numbers, and the hour log. Keep them linked and dated.
- Reviewer should scrutinize: every external-facing sentence for PyPI-vanity leakage, the hour-log total, and that no HOLD rule was bent (tiers, outreach, tracker-in-repo).
- **Deferred:** any sponsorship/grant/vehicle work — gated on §G + the 2026-11-01 decision, never on this plan.
- **Deferred:** Kaggle/conda-forge re-evaluation — unblocked only by a measured HF effect, per the rejected list.
