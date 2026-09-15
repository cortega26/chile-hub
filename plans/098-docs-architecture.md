# Plan 098: Arquitectura docs — SOURCE índice, CLAUDE delgado, anti-drift extendido

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 3315eb6..HEAD -- SOURCE_OF_TRUTH.md CLAUDE.md AGENTS.md CONTRIBUTING.md docs/dataset-inclusion-criteria.md scripts/check_agents_sync.py .github/workflows/pipeline-check.yml Makefile`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (habit break for agents using CLAUDE.md as cheatsheet)
- **Depends on**: 097 (same prose; avoid conflicts — rebase/sequence after it)
- **Category**: docs
- **Planned at**: commit `3315eb6`, 2026-09-15

## Why this matters

A new agent must read ~85 (CLAUDE) + ~134 (SOURCE) lines plus AGENTS sections
just to learn what to read next, and every duplicate is future drift surface
(the extract-command counts and line anchors already diverged). The anti-drift
system (§12) protects AGENTS/README/landing but leaves the two agent
entrypoints uncovered — exactly where drift hurts most. Rule after this plan:
"un hecho, un dueño".

## Current state

- Triplication: `SOURCE_OF_TRUTH.md:40-45` ownership table vs
  `CLAUDE.md:23-30` second nav table; `AGENTS.md §11` vs `CLAUDE.md:31-50`
  command lists; `SOURCE_OF_TRUTH.md:49-55` vs `CLAUDE.md:52-58` vs
  `AGENTS.md §4` — same 5 invariants in 3 wordings.
- Vocabulary gap: AGENTS §1/§3 `candidate`/`stable_publishable`,
  `maturity_status`, `confidence_tier`, `review_by` vs registry keys
  (`publication_track`, `maturity_status`, `live_extractor_status`,
  `public_bundle_eligible`, `cadencia`) vs criteria states
  (`accepted`/`under-review`/`needs-research`/`deferred`/`rejected`) — no
  state↔lane↔field map anywhere.
- `scripts/check_agents_sync.py:21` opens only `AGENTS.md`
  (`AGENTS_PATH = ... / "AGENTS.md"`); `grep -rn CLAUDE.md scripts/check_*.py`
  = zero gates. `SOURCE_OF_TRUTH.md:66-80` also cites line counts
  (base 76 vs 99 real, build_dev_db 927 vs 928).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Agents check | `./.venv/bin/python scripts/check_agents_sync.py` | declared | exit 0 (extended mode) |
| Docs check | `./.venv/bin/python scripts/sync_docs.py --check` | declared | exit 0 |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**: SOURCE-as-index, CLAUDE slimming with explicit redirects,
state↔lane↔field glossary in the criteria doc, `check_agents_sync --docs`
over the three files wired into `quality` + `doctor`.

**Out of scope**: changing registry JSON keys (needs ADR — prose aligns to
keys, never the reverse); rewriting AGENTS sections beyond pointer alignment;
deleting files (redirect, don't silently remove).

## Git workflow

- Branch: `advisor/098-docs-architecture`
- Commit por step; estilo conventional commits (`docs:`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline

Record current line counts of the three docs + confirm zero CLAUDE/SOURCE
coverage in the checker (commands in Current state).

**Verify**: facts confirmed live.

### Step 1: Glossary (source of truth for lanes)

In `docs/dataset-inclusion-criteria.md`, add "Mapa estado→carril→campos
registry" (states × `publication_track` × registry fields × example dataset).
Align AGENTS §1/§3 + CONTRIBUTING prose to those exact names (references, not
redefinitions). Prose renames only — no JSON key changes.

**Verify**: `grep` the three docs for the old divergent terms used as
non-comparable concepts → resolved to the glossary names.

### Step 2: Single reading route

Declare `SOURCE_OF_TRUTH.md` the sole index (~3 min). Slim `CLAUDE.md` to ~30
lines: redirect table + essential commands + read order (do NOT delete the
file; agents have it bookmarked — explicit redirects per section removed).
Invariants live only in AGENTS §4; commands canonical in `Makefile --help`;
SOURCE links, never restates. Keep every removed block reachable via one link.

**Verify**: CLAUDE.md ≤ ~40 lines; each removed block has a link target that exists.

### Step 3: Extend anti-drift

Parameterize `check_agents_sync.py` (`--docs AGENTS.md,CLAUDE.md,SOURCE_OF_TRUTH.md`;
tolerances/ranges for line counts, or forbid literal counts outside AGENTS —
either, documented). Wire into `quality` job + `make doctor`. Keep the error
message actionable (which doc, which fact, how to fix: `make sync-docs` or
manual edit).

**Verify**: introduce a scratch 1-line-count lie in CLAUDE.md → gate fails naming it; restore → green. `make doctor` green.

## Test plan

- No pytest changes (doc gates are the tests). The Step 3 scratch-proof is the
  regression demo (not committed).

## Done criteria

- [ ] "Un hecho, un dueño": invariants→AGENTS §4, nav→SOURCE, commands→Makefile; CLAUDE routes only
- [ ] Glossary exists; three docs use one vocabulary
- [ ] Anti-drift covers all three entrypoints in CI + doctor (scratch-proven)
- [ ] `make doctor` green
- [ ] `git diff --name-only 3315eb6...HEAD` lists only in-scope files
- [ ] `plans/README.md` + `ROADMAP.md` updated

## STOP conditions

- Maintainer rejects the aggressive slimming (fallback: keep structure, still ship glossary + anti-drift — report the split).
- Registry key rename seems required (STOP — needs ADR, explicitly out of scope).
- CI `quality` has no dependency budget for the extended gate (stdlib-only like the existing gates — if it needs deps, report instead).
- Verification fails twice; out-of-scope touch needed.

## Maintenance notes

- Reviewer: click every redirect left in CLAUDE.md.
- If a fourth agent doc appears, it must enter the `--docs` list in the same PR (rule, not goodwill).
- **Deferred:** README CLI-table introspection from `build_parser()` (needs `uv sync` in `quality`; noted in AGENTS §12 as recommended follow-up).
