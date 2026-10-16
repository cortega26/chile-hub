# Plan 142: Resolver parity across Python, CLI, and MCP (+ fuzzy spike)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- src/chile_hub/_query.py src/chile_hub/core.py src/chile_hub/cli.py src/chile_hub/mcp_tools.py src/chile_hub/mcp_server.py src/chile_hub/text.py docs/mcp.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (pure surface parity; no data change)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

Python has three resolvers, the CLI exposes two, and the MCP server exposes one. Agents consuming chile-hub over MCP — the audience plan 104 was built for — get `resolve_comunas` but not `resolve_regiones` or `resolve_by_coords`, so they hand-roll exactly the brittle name-matching the resolvers exist to kill. Parity is a small, safe surface close: the pure functions already exist in `_query.py`, the CLI pattern already exists for `resolve-regiones`, and the MCP cache already exists for parquet reads. The fuzzy-matching question (ADR-009 open) stays a spike with a measured recommendation, not a silent behavior change.

## Current state

Relevant files and roles:

- `src/chile_hub/_query.py:76` — `resolve_comunas(names, comunas)` pure function; `:94` — `resolve_regiones(names, regiones)` pure function; `:120` — `resolve_by_coords(...)` pure function. All deterministic, exact-match on normalized names.
- `src/chile_hub/core.py:264` — `ChileHub.resolve_comunas`; `:288` — `resolve_regiones` (added in archived plan 129); `:314` — `resolve_by_coords` (added in archived plan 065; extra `geo` with lazy import, `ImportError` message `pip install chile-hub[geo]`).
- `src/chile_hub/text.py` — `normalize_comuna_name()` pure helper reproducing the `subdere_extractor.py` chain (lowercase, strip accents, `ñ→n`); the anti-divergence guardrail test pins helper ↔ extractor parity.
- `src/chile_hub/cli.py:240` — `_add_resolve_parser(subparsers, name, help_text, argument_help)` helper; `:408-421` registers `resolve` (comunas) and `resolve-regiones`; `:711-719` `_cmd_resolve` / `_cmd_resolve_regiones`; `:804-805` dispatch table. **No `resolve-coords` subcommand exists** (verified by grep: only the two names match `resolve`).
- `src/chile_hub/mcp_tools.py:76` — `list_datasets()`; `:87` — `get_dataset()`; `:106` — `resolve_comunas(nombres, base_url)` (only resolver exposed); `:134` — `get_indicadores(...)`. Parquet reads go through `_read_parquet_cached` (`:50`, LazyFrame per-process cache from plan 119).
- `src/chile_hub/mcp_server.py:35-107` — `build_server()` registers exactly **four** tools: `list_datasets`, `get_dataset`, `resolve_comunas`, `get_indicadores` (verified by reading the file). Server instructions (`:52-58`) mention `resolve_comunas` by name.
- `docs/mcp.md` — MCP consumer doc + nav; documents the four tools.
- ADR-009 (resolver design): open questions include fuzzy matching (deferred — 0 collisions among the 346 comunas today), `resolve_regiones()` (since delivered by plan 129), Series/DataFrame inputs. Fuzzy stays deferred unless this spike measures a concrete user need.

Conventions that apply:

- Resolver contract (archived plans 050/065/129): deterministic exact-match on normalized names; non-matches return explicit `matched=False` rows, never raise; input order and duplicates preserved; `codigo_comuna`/`codigo_region` returned as `pl.String`; out-of-range lat/lon raises `ValueError` naming the input; ties broken deterministically (lowest CUT + warning).
- CLI pattern exemplar: `_add_resolve_parser` + `_cmd_resolve_regiones` in `src/chile_hub/cli.py:240,417,717` — copy it for coords (mindful that coords input is `lat,lon` pairs, not names; see `resolve_by_coords` signature first).
- MCP pattern exemplar: `_resolve_comunas` wrapper in `mcp_server.py:82-84` — thin delegation to `mcp_tools`, no logic in the server file. New tools follow the same shape; the `geo` extra must stay lazy (no `geopandas` import at server startup).
- Surface guardrail precedent: plan 134a added an API-surface guardrail; extend it rather than inventing a new test file.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Surface inventory | `grep -n "def resolve_\|resolve-regiones\|_resolve_comunas\|@server.tool" src/chile_hub/_query.py src/chile_hub/core.py src/chile_hub/cli.py src/chile_hub/mcp_tools.py src/chile_hub/mcp_server.py` | executed | Python 3 resolvers; CLI 2 subcommands; MCP 1 resolver tool (pre-change) |
| Focal tests | `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -q -k "esolve or MCP or Mcp"` | declared | all pass |
| MCP smoke | `./.venv/bin/pytest tests/test_chile_hub.py -q -k "Mcp"` (or the MCP smoke added by plan 122 — locate with `grep -rn "mcp" tests/ \| head`) | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `src/chile_hub/mcp_tools.py` (add `resolve_regiones` + `resolve_by_coords` pure wrappers reusing `_read_parquet_cached` / existing helpers)
- `src/chile_hub/mcp_server.py` (register the two new tools + update instructions string)
- `src/chile_hub/cli.py` (add `resolve-coords` subcommand only — `resolve`/`resolve-regiones` already exist)
- `docs/mcp.md` (document the new tools)
- `tests/test_chile_hub.py` and/or `tests/test_core.py` (parity + surface-guardrail tests)
- `plans/README.md` (status row only)

**Out of scope** (do NOT touch, even though they look related):

- `src/chile_hub/_query.py` matching logic — no fuzzy, no threshold, no behavior change in this plan.
- `src/chile_hub/text.py` normalization — pinned by guardrail; do not alter.
- `src/chile_hub/geo.py` download/cache contract (checksum, atomic replace) — reuse as-is.
- `resolve_by_coords` geometry artifact or refresh cadence (plan 139's territory).
- Any dataset, extractor, or validation change.

## Git workflow

- Branch: `advisor/142-resolver-parity`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `feat(mcp): expose resolve_regiones and resolve_by_coords tools`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run the surface-inventory grep; record the 3/2/1 counts. Run focal resolver + MCP tests and `make doctor`.

**Verify**: inventory matches Current state; tests + doctor green.

### Step 1: Expose resolve_regiones in MCP (exact-match, cached)

1. Add `resolve_regiones(nombres, base_url)` to `src/chile_hub/mcp_tools.py` mirroring `resolve_comunas(:106)`: fetch the `regiones` parquet via `_read_parquet_cached`, delegate matching to the existing pure `resolve_regiones` in `_query.py` (do not reimplement normalization).
2. Register it in `mcp_server.py` mirroring `_resolve_comunas(:82-84)`; extend the instructions string's resolver sentence to name both resolvers.
3. Update `docs/mcp.md` tool list + one example call.

**Verify**: MCP smoke tests pass; manual `python -c "from chile_hub.mcp_tools import resolve_regiones; print(resolve_regiones(['Valparaiso']))"` returns the CUT `05` row (accent-insensitive).

### Step 2: Expose resolve_by_coords in MCP (lazy geo, no startup import)

1. Add `resolve_by_coords(points, base_url)` wrapper in `mcp_tools.py` that lazy-imports the geo path (same `ImportError` message pattern as `core.py:314`: `pip install chile-hub[geo]`) and reuses the cached-geometry contract from `geo.py` (checksum-verified download, `platformdirs` cache, no redownload when cached).
2. Register the tool in `mcp_server.py` with a description stating input shape (`[[lat, lon], ...]`), `matched=False` outside Chile, and `ValueError` on out-of-range inputs.
3. Synthetic-geometry test only (mirror `tests/geo_fixtures.py` 3-square pattern from plan 065) — never hit the network in tests.

**Verify**: MCP tests pass with zero network (mock geometry); importing `mcp_server` without the `geo` extra does not import `geopandas` (assert via `sys.modules` check in test).

### Step 3: Add resolve-coords to the CLI

Add the `resolve-coords` subcommand via `_add_resolve_parser` (or a coords-specific parser if `lat,lon` pairs don't fit the names-shaped helper — read `:240` first and choose the smaller diff). Input format: repeatable `LAT,LON` strings (document with an example: `chile-hub resolve-coords --points "-33.45,-70.66"` — confirm the exact flag shape against `_cmd_resolve` conventions before finalizing). Delegate to `hub.resolve_by_coords`.

**Verify**: `chile-hub resolve-coords --help` exits 0; focal CLI tests pass.

### Step 4: Surface guardrail + fuzzy spike note

1. Extend the API-surface guardrail (plan 134a) to assert resolver parity: Python resolvers ⊆ CLI subcommands ⊆ MCP tools (or the explicitly documented exception list). One test, table-driven.
2. Fuzzy spike (write-only, no code): measure the concrete cost of staying exact-match — run the 346 `nombre_comuna` values through 3–5 realistic typo variants (missing accent, `n`/`ñ` swap, one-letter drop, extra space) against the current exact matcher; report match rate. Recommend: keep exact-only, add `suggest`/`did-you-mean` output, or adopt a threshold — with the 0-collision invariant and the `matched=False` contract as constraints. Cite ADR-009 open questions.

**Verify**: `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -q` → pass including the parity test; spike note exists with numbers.

## Test plan

- New tests: MCP `resolve_regiones` happy path + unmatched explicitness; MCP `resolve_by_coords` with synthetic geometry (matched/unmatched/out-of-range); CLI `resolve-coords --help` + one happy-path invocation (mocked hub method, no network); parity guardrail test (table of expected commands/tools).
- Patterns: MCP smoke from plan 122; resolver tests from plans 050/065/129 in `tests/test_core.py`; geo fixtures from `tests/geo_fixtures.py`.
- Verification: focal pytest → pass including new tests; `make test` → verde.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] MCP server registers `resolve_regiones` + `resolve_by_coords` alongside the existing four tools
- [ ] CLI offers `resolve-coords` with `--help` exit 0
- [ ] `resolve_regiones(['Valparaiso'])` returns CUT `05` via the MCP wrapper (accent-insensitive, exact-match preserved)
- [ ] No `geopandas` import at MCP server startup without the `geo` extra
- [ ] Parity guardrail test exists and passes
- [ ] Fuzzy spike note with typo-variant match rates + recommendation exists; no fuzzy behavior change shipped
- [ ] `docs/mcp.md` documents the new tools
- [ ] `make test` verde; `make doctor`, `make lint && make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `_query.py` resolver signatures differ from Current state (matching logic changed under you).
- The `geo` extra cannot stay lazy in the MCP path (startup import required) — report, do not vendor a new download path.
- CLI coords input shape conflicts with `_add_resolve_parser` assumptions and the fix requires touching `_main`/parser architecture (larger blast radius — report).
- Fuzzy measurement shows collisions under exact-match (the 0-collision invariant is void) — report before recommending anything.

## Maintenance notes

- If a new resolver is ever added to `_query.py`, the parity guardrail will fail until CLI + MCP are extended — that is the intended signal.
- Reviewer should scrutinize: thin-wrapper discipline (no matching logic duplicated in `mcp_tools.py` or `cli.py`), lazy-geo handling, and synthetic-only geometry in tests.
- **Deferred:** fuzzy/did-you-mean behavior — unblocked by the spike recommendation + maintainer approval, not by this plan.
- **Deferred:** Series/DataFrame resolver inputs (ADR-009 open) — same gate.
