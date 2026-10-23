# Plan 148: Convertir el suministro en demanda vía canales oficiales (datos.gob.cl + SGD)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat dff71ef..HEAD -- ROADMAP.md docs/sostenibilidad/README.md docs/adoption-review.md plans/144-adoption-funnel-review.md plans/107-activacion-lanzamiento-handoff.md plans/110-programa-de-patrocinios.md AGENTS.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S-M (operator-heavy, no code, no money ask, no external contact beyond what the vigente sustainability state allows)
- **Risk**: LOW
- **Depends on**: none (reads plan 144 numbers and plan 107 READY handoff; no file overlap)
- **Category**: direction
- **Planned at**: commit `dff71ef`, 2026-10-22

## Why this matters

chile-hub's supply side is fully built (21 public layers, HF mirror, SEO/comuna pages, MCP server, DOI, SQL playground), but the demand side is unverified: plan 144 (Auditoría 3 lineage) found 0 dependents, 0 public importers, 0 third-party interactions, 0 sponsors, ~27 bundle activations/month, and PyPI downloads tracking release cadence (not adoption). Until the product is visible inside the official open-data ecosystem, the anti-patrón #10 gate ("no new datasets before validated adoption") stays frozen and even worthy depth work cannot be framed as demand. This plan executes the operator-only outreach actions already listed in `ROADMAP.md §7` — registering in datos.gob.cl "Reutilización", requesting structured CEAD delincuencia via official channels instead of scraping, reporting dead bulk links, and optionally presenting to the Secretaría de Gobierno Digital help desk — so the hub goes from "built but unknown" to "discoverable through the channels users already use."

## Current state

Facts the executor needs (all read during recon; inline, not "as discussed"):

- `ROADMAP.md:249-259` (§7 "Acciones de operador") — all four are unchecked:
  1. Registrar chile-hub en "Reutilización" de datos.gob.cl (ingreso con ClaveÚnica).
  2. Pedir la delincuencia comunal estructurada del CEAD por "Sugerencias" de datos.gob.cl o por la Ley 20.285, en vez de scrapearla.
  3. Reportar con "Notifica un error" el bulk 2015 de delincuencia en datos.gob.cl (enlaces muertos).
  4. Opcional: presentar el proyecto a la mesa de ayuda de la Secretaría de Gobierno Digital y preguntar por el estado de la norma técnica de datos abiertos.
  (Zenodo DOI `10.5281/zenodo.22968698` is already done — checked `[x]`.)
- `docs/sostenibilidad/README.md:10-23` — HOLD / sin búsqueda activa (veredicto D, aceptado 2026-09-30; revisión 2026-11-01). Allowed until gate §G: keep `FUNDING.yml` + CLI support note; run discovery experiment §E (max 15 h, no asking money); consult an accountant on the charging vehicle (no external contact); serve inbound demand. Forbidden: tiers/`SPONSORS.md`/landing sponsorship section; asking organizations/vendors/funders for money; executing `plans/110-programa-de-patrocinios.md` (HOLD); launching self-initiated service pilots without gate conditions 2, 3, 5; presenting PyPI downloads as installs/users/audience.
- `plans/144-adoption-funnel-review.md` — DONE (2026-10-15): honest, telemetry-free funnel defined; verdict D unchanged; numbers refreshed via Anexo M method only.
- `plans/107-activacion-lanzamiento-handoff.md` — READY (not DONE): external-agent handoff for GSC meta tag, sitemap, schedule verification, adoption tracking, with fallbacks + STOP conditions.
- `AGENTS.md §10` — never present PyPI downloads as "instalaciones", "usuarios" or "audiencia"; the honest method lives in `docs/sostenibilidad/README.md` (Auditoría 3).
- `ROADMAP.md §8` — telemetry, premium API/paywall, English README/docs, Kaggle/conda-forge (until HF effect measured), sigstore (until second publisher) stay rejected.

Conventions that apply:

- Sostenibilidad agent rules (`docs/sostenibilidad/README.md:59-66`): no executing plan 110; no contacting sponsors/vendors/CAF/funders beyond the vigente state; never quote PyPI as audience (refresh via Annex M first); no publishing contact PII or third-party commercial terms (tracker stays out of the repo, Ley 21.719); register every analysis/decision in the chronology with date/document/result/status; any contradiction of Auditoría 3 reconciled explicitly before changing state.
- Docs anti-drift (`AGENTS.md §12`): README counts are delimited-block generated via `doc_sync.py`; this plan's one-pager must not hardcode drifting counts — link to live reports (`hub_health.md`, `dataset_quality.md`, `redistribution_report.md`) instead.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Baseline health | `make doctor` | declared | exit 0 (includes `sync_docs --check`, `check_agents_sync`) |
| Lint + format | `make lint && make format-check` | declared | exit 0 |
| Confirm outreach doc has no vanity PyPI phrasing | `grep -inE "instalaciones|usuarios|audiencia|2\.2k|2,218" docs/adoption-outreach.md` | declared | no matches (exit 1 from grep is expected/OK) |
| Confirm ROADMAP §7 items are the 4 actions | `grep -n "Reutilización\|Sugerencias\|Notifica un error\|Secretaría de Gobierno Digital" ROADMAP.md` | declared | 4 lines, all under §7 |

## Scope

**In scope** (the only files you should modify):

- `docs/adoption-outreach.md` (create — one-pager: what chile-hub is, honest numbers via Annex M, the 4 ROADMAP §7 actions each with owner + method + evidence + expected outcome, and the "never say" list from AGENTS.md §10)
- `docs/sostenibilidad/README.md` (chronology entry only: date / document / result / status row for this outreach)
- `plans/README.md` (status row for plan 148 only)

**Out of scope** (do NOT touch, even though they look related):

- `plans/110-programa-de-patrocinios.md` — HOLD; do not rewrite, retitle, or partially execute.
- `FUNDING.yml`, README/landing sponsorship sections — forbidden until gate §G.
- Any telemetry in the package, any paywall/premium API, any English README/docs.
- Contacting any organization, vendor, CAF, funder, or public body — operator-only; this plan prepares the one-pager and records the actions, it does not send anything or ask money.
- `AGENTS.md`, `ROADMAP.md` state tables (except the plans index row) — outcomes are the maintainer's call.

## Git workflow

- Branch: `advisor/148-adopcion-datos-gob-cl-sgd-outreach`
- Commit per logical unit; conventional-commit style per repo (e.g. `docs(outreach): add one-pager y acciones de datos.gob.cl y SGD`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Before changing anything, confirm the repo is healthy and the preconditions hold:

- Run `make doctor` → exit 0. If it fails on the unmodified checkout, **STOP and report** the exact output (broken baseline, not yours to fix).
- Confirm `ROADMAP.md §7` still lists the 4 unchecked operator actions (grep in the command table). If any is already checked or removed, **STOP and report** (state changed since the plan was written).
- Confirm `docs/sostenibilidad/README.md` still states HOLD with review 2026-11-01. If state changed (e.g. gate §G passed), **STOP and report** — this plan's assumptions no longer hold.

### Step 1: Create the outreach one-pager `docs/adoption-outreach.md`

Write a self-contained one-pager (audience: datos.gob.cl / Secretaría de Gobierno Digital / interested reusers) containing:

1. What chile-hub is — one paragraph, emphasizing it is an independent reuser downstream of datos.gob.cl and the institutions, never "oficial" (product-spec § "Quién hace qué", ADR-023).
2. Honest numbers, refreshed via the sostenibilidad Annex M method and linked to live reports (`data/normalized/hub_health.md`, `dataset_quality.md`, `redistribution_report.md`) — never hardcoded counts, never PyPI-as-audience. Use: ~27 bundle activations/month, 21 public layers, HF mirror 274 downloads, 0 dependents/sponsors (veredicto D).
3. The 4 ROADMAP §7 actions, each as a mini-card: action, where (datos.gob.cl "Reutilización" / "Sugerencias" / Ley 20.285 / "Notifica un error" / SGD mesa de ayuda), method (ClaveÚnica login, form, email), evidence (which dataset/link), expected outcome, and owner (mantenedor, operator-only).
4. The "never say" list: do not present PyPI downloads as installs/users/audience; do not promise paywall/premium; do not scrape where an official channel exists (product-spec "buen vecino del ecosistema").

**Verify**: `grep -inE "instalaciones|usuarios|audiencia|2\.2k|2,218|premium|paywall|oficial" docs/adoption-outreach.md` → no matches for the vanity/commercial claims (the word "oficial" may appear only in the "never of chile-hub" sense, which is fine). `make lint && make format-check` → exit 0.

### Step 2: Register the outreach in the sostenibilidad chronology

Add one row to the `docs/sostenibilidad/README.md` chronology table: date `2026-10-22`, document `plans/148-adopcion-datos-gob-cl-sgd-outreach.md`, result `one-pager creado; 4 acciones de ROADMAP §7 documentadas; sin contacto externo ni pedido de dinero`, status `listo para ejecución por el operador`.

Reconcile explicitly: this does not contradict Auditoría 3 verdict D — it is measurement/visibility work within the allowed discovery cap, not sponsorship execution.

**Verify**: the chronology table gains exactly one new row with the 4 columns (date/document/result/status); `make doctor` → exit 0.

### Step 3: Update the plans index

Add a status row for plan 148 in `plans/README.md` (see "Planes activos" of this batch) set to `TODO`, then flip to `DONE` once Steps 1–2 verify.

**Verify**: `plans/README.md` contains a row `| 148 | ... | P2 | S-M | LOW | — | DONE |` after this plan completes; `git status` shows only the in-scope files modified.

## Test plan

- No code tests (operator/docs plan).
- Structural check: `docs/adoption-outreach.md` contains all 4 ROADMAP §7 actions (grep each action name → 1 match each).
- Verification command: `make doctor` exit 0 and `make lint && make format-check` exit 0.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `docs/adoption-outreach.md` exists and contains the 4 ROADMAP §7 actions with owner + method + evidence each.
- [ ] No vanity PyPI phrasing ("instalaciones", "usuarios", "audiencia", "2.2k", "2,218") and no premium/paywall claims in the one-pager (grep returns nothing).
- [ ] `docs/sostenibilidad/README.md` chronology has one new row for this outreach (4 columns present).
- [ ] `make doctor` → exit 0; `make lint && make format-check` → exit 0.
- [ ] `plans/README.md` status row for plan 148 added and set to `DONE`.
- [ ] `git diff --name-only dff71ef...HEAD` lists only `docs/adoption-outreach.md`, `docs/sostenibilidad/README.md`, `plans/README.md`.

## STOP conditions

Stop and report back (do not improvise) if:

- The code/docs at "Current state" locations don't match the excerpts (drift since `dff71ef`).
- `make doctor` or `make lint` fails on the unmodified checkout (broken baseline).
- Any step would require contacting an organization, vendor, CAF, funder, or public body, or asking money — that is operator-only and forbidden by the vigente sustainability state; mark the plan `BLOCKED` with reason and report.
- The mantenedor decides not to proceed with outreach — mark `REJECTED` with one-line rationale and do not create the one-pager.

## Maintenance notes

- **Deferred:** contacting datos.gob.cl / SGD / CEAD — operator-only, after the one-pager is reviewed; unblocked by mantenedor approval of this plan.
- **Deferred:** measuring the effect of outreach (bundle downloads, HF metric, datos.gob.cl listing) — feed plan 144's funnel refresh; unblocked by the 2026-11-01 sustainability review or a separate metrics pass.
- A reviewer should scrutinize: no money ask, no vanity PyPI numbers, no contact PII or third-party commercial terms in the one-pager.
- Follow-up: after datos.gob.cl "Reutilización" registration, expect a listing delay; the CEAD request under Ley 20.285 has legal response times — do not scrape in the meantime (anti-patrón #10 + product-spec remain in force).

---

## Nota del advisor (no formar parte del plan ejecutable)

Este plan es de dirección/operador, no de código: no toca `src/`, tests ni CI. Su valor es cerrar la asimetría "suministro listo, demanda no verificada" que dejó la Auditoría 3 (veredicto D). Ejecutarlo no cambia el veredicto D; lo prepara para la revisión del 2026-11-01.
