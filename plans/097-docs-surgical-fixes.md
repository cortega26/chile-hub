# Plan 097: Docs quirúrgicos — CLAUDE counts, badge capas, §5 como puntero

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- CLAUDE.md README.md AGENTS.md CONTRIBUTING.md docs/dataset-inclusion-criteria.md scripts/check_agents_sync.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

`CLAUDE.md` is the first file a new agent reads and it is actively wrong
(counts, extractor number), so agents start with broken read-anchors and learn
to distrust docs. Separately, three docs answer "how many datasets?" three
ways, and AGENTS §5 contradicts the normative inclusion criteria on what
blocks a dataset (scraping/format) — so contributors/agents get inconsistent
reviews depending on which doc they followed.

## Current state

- `CLAUDE.md:42` — `make extract # 14 extractores`; reality: `Makefile:118-135`
  invokes 17, `src/extractors/*extractor*.py` = 22 files (17 daily + candidate/
  stub/live variants). `:64-67` cites base 73 / validation 1194 /
  build_dev_db 867 / core 2302; reality: 99 / 1956 / 928 / 1995.
- `README.md:26` badge `22 capas`; `:197` `25 contratos`; catalog = 25 keys;
  `contracts/datasets/*.json` = 25 files; `docs/datasets/*.md` = 28 files
  (incl. archived); `AGENTS.md §1` = 25-row table mixing deprecated/candidate.
  Convention to set: `N publicables (bundle) / M registradas (catálogo) /
  K docs (con archivados)` — verify N against `publication_track`/registry
  before writing the badge (don't hardcode 22 blindly).
- `AGENTS.md:349-360` — 3 blockers (licencia, formato JSON/dump, estabilidad;
  scraping = no-MVP) + 2 orientativas. `docs/dataset-inclusion-criteria.md`
  — 5 blockers (+no-personal, validación posible), `under-review` tolerates
  fragile/scraping sources in `candidate`. `CONTRIBUTING.md:60-64` — new
  datasets enter via `candidate`, contradicting the §5 MVP rejection.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Counts | `ls src/extractors/*extractor*.py \| wc -l; wc -l src/extractors/base.py src/validation.py src/build_dev_db.py src/chile_hub/core.py` | executed | 22; 99/1956/928/1995 |
| Docs check | `./.venv/bin/python scripts/sync_docs.py --check` | declared | exit 0 |
| Agents check | `./.venv/bin/python scripts/check_agents_sync.py` | declared | exit 0 |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: numbers in `CLAUDE.md`, badge/count convention in `README.md` +
`AGENTS.md §1`, AGENTS §5 Paso 1 → 2-line summary + normative pointer,
CONTRIBUTING checklist alignment.

**Out of scope**: structural consolidation (Plan 098); changing inclusion
criteria semantics (docs point at the norm, don't rewrite it); regenerating
`sync_docs.py` blocks beyond what the edits require.

## Git workflow

- Branch: `advisor/097-docs-surgical-fixes`
- Commit por fix; estilo conventional commits (`docs:`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Re-measure (no edits)

Re-run the counts command; confirm the mismatches still hold live.

**Verify**: numbers match Current state (or STOP if code moved — then correct to live values).

### Step 1: CLAUDE.md numbers

Fix `14 extractores` → daily-lane truth (17 via `make extract`, 22 files;
one line + lanes note pointing at `docs/extraction-lanes.md`), and the 4 line
counts to live values (or replace counts with a pointer to the verified doc —
either is fine; document the choice). No other CLAUDE restructuring (098).

**Verify**: every number in CLAUDE.md reproducible by the Step 0 commands.

### Step 2: Count convention

Apply `N publicables / M registradas / K docs` to the README badge area
(`:26`), the `:145` layers section title if it encodes a number, and
`AGENTS.md §1` intro. Derive N from the registry (`publication_track`/bundle
eligibility — read, don't assume 22). Keep `sync_docs.py` blocks regenerable
(`--check` must stay green; if the badge is inside a delimited block, edit via
the generator, not by hand).

**Verify**: `scripts/sync_docs.py --check` green; badge formula documented next to the block.

### Step 3: §5 → pointer + CONTRIBUTING

Rewrite AGENTS §5 Paso 1 as a 2-line summary declaring
`docs/dataset-inclusion-criteria.md` the sole normative gate/state source;
AGENTS + CONTRIBUTING link, never redefine. Align the CONTRIBUTING checklist
(`:60-64` + "3 preguntas bloqueantes" line) to the same pointer.

**Verify**: `check_agents_sync.py` + `make doctor` green; `grep` for duplicated gate matrices in AGENTS/CONTRIBUTING → gone.

## Test plan

- No pytest changes. Gates are the doc-sync scripts + doctor.

## Done criteria

- [ ] Every number in CLAUDE.md reproducible live
- [ ] Badge/count convention applied + formula documented; `sync_docs --check` green
- [ ] Single normative criteria source; no duplicated gate matrix
- [ ] `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- The badge/count lives inside a generator you can't safely extend (then do counts-only by hand + report the generator gap to 098).
- Inclusion-criteria semantics are disputed (don't resolve product disputes in a docs fix — pointer only).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Counts will drift again — that's why 098 extends anti-drift to these files. This plan buys correctness; 098 buys durability.
- **Deferred:** glossary/consolidation (098).
