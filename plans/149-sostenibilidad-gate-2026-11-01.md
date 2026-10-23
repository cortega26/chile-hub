# Plan 149: Revisar el gate de sostenibilidad el 2026-11-01 (Plan 110 sigue HOLD hasta entonces)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat dff71ef..HEAD -- docs/sostenibilidad/README.md docs/sostenibilidad/auditoria-3-2026-09-29.md docs/backlog/NEXT_STEPS.md plans/110-programa-de-patrocinios.md plans/144-adoption-funnel-review.md ROADMAP.md AGENTS.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M (decision work + bounded discovery experiment §E capped at 15 h, no money ask)
- **Risk**: LOW (no code, no external contact beyond the vigente state, no money ask)
- **Depends on**: plan 144 (adoption funnel numbers must be stable/consistent; 144 is DONE)
- **Category**: direction
- **Planned at**: commit `dff71ef`, 2026-10-22

## Why this matters

The sustainability question is the project's open strategic fork: keep HOLD (veredicto D of Auditoría 3, accepted 2026-09-30) or attempt a bounded discovery experiment (§E, max 15 h, no asking money) that could lead to sponsorship/services/pivot/stop. `docs/sostenibilidad/README.md` fixes the review date at **2026-11-01** and `plans/110-programa-de-patrocinios.md` sits at HOLD pending gate §G. Without a dated decision before that review, the project drifts: no sponsorship work, no discovery, and no clarity on whether the single-maintainer bus factor is acceptable. This plan forces a documented, evidence-based decision before 2026-11-01 within the constraints the mantenedor already set.

## Current state

Facts the executor needs (all read during recon; inline):

- `docs/sostenibilidad/README.md:10-23` — **HOLD / sin búsqueda activa** (veredicto D, 2026-09-30; revisión del tema 2026-11-01). Próxima acción registrada: revisar el tema el 2026-11-01. Experiment §E no iniciado; si se retoma: máximo 15 h y sin pedir dinero; decisión entre el día 30 y el 45.
- Auditoría 3 conclusions (`docs/sostenibilidad/auditoria-3-2026-09-29.md`, §G gate + Annex M): (1) no comprador identificado (0 dependents, 0 repos públicos que importen `chile_hub`, 0 interacciones de terceros, 0 sponsors); (2) PyPI mide cadencia de releases (R² 0.94–0.97, ~80–100 descargas/release), activaciones reales ~27 bundle descargas/mes; (3) no vehículo para cobrar (sin personalidad jurídica; Ley 21.440 bloquea donaciones con beneficio tributario a persona natural; organismos públicos compran vía Compra Ágil, no patrocinan); (4) infra ≈ USD 0, lo escaso es el tiempo del mantenedor, riesgo = continuidad; (5–8) sponsorship-horas = consultoría barata; grants solo vía socio institucional con evidencia de uso (12–24 mes); CAF solo para aprender/red tras §E y ≥3 organizaciones verificables; bus factor se reduce con plan de continuidad, no con dinero.
- `plans/110-programa-de-patrocinios.md` — HOLD (2026-09-30); do not execute; any rewrite must start from Auditoría 3 §F delta and only after gate §G.
- `docs/backlog/NEXT_STEPS.md` — largo plazo: estrategia de sostenibilidad en `docs/sostenibilidad/README.md`; Auditoría 3 veredicto D; plan 110 HOLD.
- `plans/144-adoption-funnel-review.md` — DONE: honest telemetry-free funnel defined; verdict D sin cambios; 1.6 h ≤ 15 h cap; no contacto externo ni dinero.
- `ROADMAP.md §5` — 110 HOLD with 2026-11-01 review; §7 operator actions pending (see plan 148).

Conventions that apply:

- Sostenibilidad agent rules (`docs/sostenibilidad/README.md:59-66`): no executing plan 110; no contacting sponsors/vendors/CAF/funders beyond vigente state; discovery does not ask money; no presenting PyPI downloads as installs/users/audience (refresh via Annex M first); no publishing contact PII or third-party commercial terms (tracker out of repo, Ley 21.719); register every analysis/decision in the chronology with date/document/result/status; any contradiction of Auditoría 3 reconciled explicitly before changing state.
- `AGENTS.md §10` — PyPI downloads are not installations/users/audience.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Baseline health | `make doctor` | declared | exit 0 (includes `sync_docs --check`, `check_agents_sync`) |
| Lint + format | `make lint && make format-check` | declared | exit 0 |
| Confirm sostenibilidad state still HOLD w/ review 2026-11-01 | `grep -n "HOLD\|2026-11-01\|veredicto D" docs/sostenibilidad/README.md` | declared | HOLD present, review date 2026-11-01 present, veredicto D present |
| Confirm plan 110 HOLD row | `grep -n "110" plans/README.md` | declared | row shows HOLD |

## Scope

**In scope** (the only files you should modify):

- `docs/sostenibilidad/README.md` — chronology entry + state row reflecting the pre-2026-11-01 decision (HOLD maintained, or §E executed with result). No narrative inflation.
- `plans/README.md` — status row for plan 149 only.

**Out of scope** (do NOT touch, even though they look related):

- `plans/110-programa-de-patrocinios.md` — HOLD; do not rewrite, retitle, or execute. Its content is untouched by this plan.
- `FUNDING.yml`, README/landing sponsorship sections — forbidden until gate §G.
- Contacting sponsors, vendors, CAF, funders, or public bodies — beyond vigente state unless §E finds ≥3 verified orgs (then a listening conversation with CAF is allowed, no money).
- Asking money, launching service pilots, tiers/`SPONSORS.md`, telemetry, paywall/premium API, English docs.
- `AGENTS.md`, `ROADMAP.md` state tables (except plans index row) — the mantenedor decides on 2026-11-01.

## Git workflow

- Branch: `advisor/149-sostenibilidad-gate-2026-11-01`
- Commit per logical unit; conventional-commit style per repo (e.g. `docs(sostenibilidad): decision previa al gate 2026-11-01, plan 110 sigue HOLD`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Before changing anything:

- Run `make doctor` → exit 0. On failure on the unmodified checkout, **STOP and report** exact output (broken baseline).
- Confirm `docs/sostenibilidad/README.md` still states HOLD with review 2026-11-01 and veredicto D (grep in command table). If the state already changed (e.g. gate §G passed, plan 110 un-HOLDed), **STOP and report** — assumptions no longer hold.
- Confirm `plans/144-adoption-funnel-review.md` is DONE and its numbers are the ones to cite (veredicto D unchanged, ~27 bundle activations/mo, 0 sponsors). If not, **STOP and report**.

### Step 1: Make the pre-review decision (on or before 2026-11-01)

Decide and document one of two paths, in this order of preference:

**Path A — Keep HOLD (default unless evidence appears).** Record in `docs/sostenibilidad/README.md` chronology + state: veredicto D maintained, plan 110 stays HOLD, no sponsorship search, next mandatory review April 2027 only if §E is ever run and ends in Stop. This is the compliant default.

**Path B — Run bounded discovery §E.** Only if the mantenedor explicitly opts in: execute §E within the 15 h cap, no money ask, listening-only (per `docs/sostenibilidad/README.md` rules). Outcome must be one of: Avanzar / Servicios / Pivotear / Stop. If §E finds fewer than 3 organizations with verifiable use, CAF conversation is NOT allowed (threshold not met) → effectively Stop. If §E ends in Stop, next mandatory review is April 2027.

Record whichever path is chosen as a chronology row: date (before 2026-11-01), document `plans/149-sostenibilidad-gate-2026-11-01.md`, result (Path A or B + outcome), status (HOLD maintained / §E ejecutado con resultado X).

Reconcile explicitly: the chosen path must not contradict Auditoría 3 without citing new evidence that changes a specific conclusion.

**Verify**: `docs/sostenibilidad/README.md` state/chronology shows a dated decision entry before 2026-11-01; `plans/110-programa-de-patrocinios.md` unmodified (still HOLD); `make doctor` → exit 0.

### Step 2: Update the plans index

Add a status row for plan 149 in `plans/README.md` set to `DONE`; if the decision changed plan 110's state, note it in the row rationale but do not edit plan 110's content.

**Verify**: `plans/README.md` contains a row `| 149 | ... | P2 | M | LOW | 144 | DONE |`; `git status` shows only `docs/sostenibilidad/README.md` and `plans/README.md`.

## Test plan

- No code tests (direction/decision plan).
- Verification: `make doctor` exit 0; `make lint && make format-check` exit 0; sostenibilidad README chronology gains exactly one dated decision row referencing this plan.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `docs/sostenibilidad/README.md` has a dated decision entry on/before 2026-11-01 (state: HOLD maintained, or §E executed with a named outcome Avanzar/Servicios/Pivotear/Stop).
- [ ] `plans/110-programa-de-patrocinios.md` content unmodified (still HOLD) — no tiers, no `SPONSORS.md`, no landing sponsorship section added.
- [ ] No money ask, no sponsor/vendor/CAF/funder contact beyond vigente state, no PyPI-as-audience phrasing in anything touched.
- [ ] `make doctor` → exit 0; `make lint && make format-check` → exit 0.
- [ ] `plans/README.md` status row for plan 149 set to `DONE`.
- [ ] `git diff --name-only dff71ef...HEAD` lists only `docs/sostenibilidad/README.md`, `plans/README.md`.

## STOP conditions

Stop and report back (do not improvise) if:

- The "Current state" excerpts don't match the live files (drift since `dff71ef`).
- `make doctor`/`make lint` fails on the unmodified checkout.
- Gate §G is not met but a step would advance sponsorship (contact orgs for money, tiers, `SPONSORS.md`, landing section) — keep HOLD, mark plan `BLOCKED` with reason, report.
- The mantenedor overrides to a different path — that is their decision; record it explicitly in the chronology and do not implement anything beyond recording.

## Maintenance notes

- **Deferred:** execution of `plans/110-programa-de-patrocinios.md` — gated on §G (requires §E evidence + a charging vehicle + a verified buyer); unblocked only by gate §G, not by this plan.
- **Deferred:** mandatory April 2027 review — only if §E is run and ends in Stop (per `docs/sostenibilidad/README.md:23`).
- **Deferred:** next sustainability reconsideration — the 2026-11-01 review itself, owned by the mantenedor.
- A reviewer should scrutinize: no money ask, no contact beyond vigente state, plan 110 untouched, decision dated before 2026-11-01.
- Follow-up: whatever path is chosen, feed the result into `ROADMAP.md §5` (110 state) and the 2026-11-01 review record.

---

## Nota del advisor (no formar parte del plan ejecutable)

Este plan es de dirección/decisión, no de código. Su único producto ejecutable es una entrada fechada y razonada en `docs/sostenibilidad/README.md` antes del 2026-11-01, dejando `plans/110` en HOLD hasta que el gate §G se cumpla. No ejecuta patrocinios, no contacta financiadores y no pide dinero.
