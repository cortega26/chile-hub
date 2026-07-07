# Plan 040 (design/spike): Add a `hub.sql(...)` query surface over the published Parquet

> **Executor instructions**: This is a **design/spike** plan. Deliverable: a small,
> working prototype of the API + a written design decision on scope and dependency
> handling — NOT a fully hardened feature. Follow the steps, keep the prototype behind
> a clear boundary, and update `plans/README.md` when done.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/chile_hub/core.py pyproject.toml README.md`

## Status

- **Priority**: P2
- **Effort**: S–M
- **Risk**: LOW
- **Depends on**: coordinate with 032 (which moves `duckdb` out of runtime deps — see "Dependency decision")
- **Category**: direction
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

The repo already treats "SQL against the published Parquet" as a first‑class consumption mode: `duckdb`
is a dependency, `build_duckdb` ships `chile_data.duckdb`, `README.md` has a "Consultas SQL con DuckDB"
section, every dataset in `dataset_catalog.json` ships a copy‑paste `"duckdb"` recipe, and
`chile-hub example <capa> --kind duckdb` advertises it. Yet the Python API exposes only `load_polars()`
and a hand‑rolled `cross_view()` — there is **no** `sql`/`query` method across the 2,302‑line `core.py`.
A `hub.sql("SELECT … FROM comunas JOIN censo_comunal USING(codigo_comuna)")` that registers each published
dataset as a named DuckDB view turns those recipes into a real method and makes `cross_view` a trivial
special case. This is the un‑gated sibling of the blocked landing playground (Plan 020, NO‑GO on demand):
it serves the audience that demonstrably exists (people already downloading the bundle and following the
DuckDB recipes) without depending on landing traffic.

## Design questions to resolve (the point of this spike)

1. **API shape**: `hub.sql(query: str) -> pl.DataFrame`. Which datasets are registered as views, and under
   what names? (Proposal: every `Dataset` value → a view of the same name, backed by
   `read_parquet('<path>')` resolved via `get_output_path(name, "parquet")`.) Lazy‑register on first use.
2. **Backing store**: query the **Parquet views**, not the shipped `.duckdb` file (the 70 MB `.duckdb` is not
   in the pip bundle — only Parquet is). Confirm by checking what the release/packaging ships.
3. **Dependency decision (must reconcile with Plan 032)**: Plan 032 moves `duckdb` OUT of runtime deps
   because the library doesn't import it today. `hub.sql()` WOULD import it. Decide one of:
   - (a) add an optional extra `query = ["duckdb>=1.5.4"]` and lazy‑import duckdb inside `sql()` with a clear
     "install chile-hub[query]" error if absent (keeps the base install slim — **recommended**); or
   - (b) return `duckdb` to runtime deps (heavier base install).
   Record the choice and update Plan 032 / `pyproject.toml` consistently.
4. **Relationship to `cross_view`**: keep both, or reimplement `cross_view` as sugar over `sql`? (Proposal:
   keep `cross_view` as‑is for now; note the overlap.)
5. **CLI**: a `chile-hub query "SELECT …"` subcommand — in scope for the prototype or deferred?

## Deliverable

- A working `ChileHub.sql(query)` prototype in `src/chile_hub/core.py` (lazy duckdb import, view registration,
  returns a Polars DataFrame) behind the dependency decision from Q3.
- 2–3 tests in `tests/test_core.py` (single‑table select; a two‑dataset join on `codigo_comuna`; a clear error
  when `duckdb` is not installed, if using the optional‑extra approach).
- A short note in the ADR/docs recording the design decisions above.

## Steps

1. Confirm what the pip release ships (Parquet vs `.duckdb`) — read `.github/workflows/pypi-release.yml` and the
   bundle contents. Decide to back views with Parquet.
2. Prototype `sql()`: open an in‑memory duckdb connection, `CREATE VIEW <name> AS SELECT * FROM read_parquet('<path>')`
   for each published dataset (resolve paths via existing helpers), `con.execute(query).pl()`, return it. Lazy‑import
   `duckdb` with a helpful ImportError if the chosen extra isn't installed.
3. Implement the Q3 dependency decision in `pyproject.toml` (recommended: `[project.optional-dependencies] query`),
   and reconcile with Plan 032.
4. Add the tests. Add a README example if the prototype is solid.
5. Write the design decisions into a short ADR (`docs/adr/`).

## Done criteria

- [ ] `ChileHub.sql("SELECT codigo_comuna FROM comunas LIMIT 5")` returns a Polars DataFrame with rows
- [ ] A join query across two datasets on `codigo_comuna` returns expected rows
- [ ] The dependency decision is implemented and consistent with Plan 032 (base install stays slim, or duckdb is deliberately in runtime)
- [ ] Tests in `tests/test_core.py` pass; `make lint` and `make format-check` exit 0
- [ ] Design decisions recorded in an ADR
- [ ] `plans/README.md` status row updated

## STOP conditions

- If registering all datasets as views is slow or memory‑heavy at import (it should be lazy and cheap since
  duckdb reads Parquet on demand), reassess — register on first `sql()` call, not in `__init__`.
- If the packaging ships only the `.duckdb` (not Parquet), revisit Q2 before prototyping.

## Maintenance notes

- New datasets automatically get a view if registration derives from `Dataset`/the catalog — but that couples this
  to Plan 025 (enum↔catalog sync); prefer deriving view names from the catalog, not the enum, so it stays complete.
- A hosted/browser version (Plan 020) remains gated on landing demand; this Python/CLI surface is independent of it.
