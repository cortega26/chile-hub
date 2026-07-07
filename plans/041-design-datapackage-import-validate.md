# Plan 041 (design/spike): Add a consumer‑facing `datapackage.json` load/validate path (Frictionless)

> **Executor instructions**: This is a **design/spike** plan. Deliverable: a small
> working prototype + a design decision, NOT a hardened feature. Keep `frictionless`
> optional and lazily imported. Update `plans/README.md` when done.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/builders/data_package.py src/chile_hub/core.py pyproject.toml`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`chile-hub` **publishes** a Frictionless `datapackage.json` (built by `src/builders/data_package.py`,
shipped inside `chile-hub-publishable-bundle.zip`) and already declares `frictionless>=5.18,<6` as a
dependency — but it's used only inside `scripts/verify_pipeline.py` (skipped if absent), and the
consumer‑facing `ChileHub.validate_user_data()` validates against chile‑hub's **own** internal
`contracts/datasets/*.schema.json`, not the published descriptor. This is a clean one‑directional
asymmetry: the hub exports an interoperability standard but gives consumers no first‑class way to
**consume or validate against it**. `docs/product-spec.md` lists a "catálogo de versiones / índice de
archivos" as a desired post‑MVP capability. A thin `from_datapackage(path_or_url)` loader and/or a
`frictionless_validate()` closes the loop for the "developers building Chilean software / BI teams"
audience the spec targets — at the marginal cost of a wrapper, since the descriptor and dependency exist.

## Design questions to resolve

1. **API shape**: pick one or both —
   - `ChileHub.from_datapackage(path_or_url) -> ChileHub` (open a downloaded/pinned bundle by its
     `datapackage.json`, resolving `resources[].path` to the local Parquet/CSV), and/or
   - `ChileHub.frictionless_validate(dataset_name=None) -> report` (validate the local bundle against the
     shipped descriptor using `frictionless.Package(...).validate()`).
2. **Dependency handling**: `frictionless` is heavy. Move it from dev‑only to an **optional extra**
   (`validation = ["frictionless>=5.18,<6"]`) and **lazy‑import** it inside the new methods with a clear
   "install chile-hub[validation]" error. Do NOT add it to base runtime deps.
3. **Layering (respect ADR‑005)**: the internal `contracts/datasets/*.schema.json` remains the source of truth.
   This new path is a **publication/consumer convenience** over the already‑emitted descriptor — it must not
   become a third schema representation. Confirm ADR‑005's intent by reading `docs/adr/`.

## Deliverable

- A working prototype of the chosen method(s) in `src/chile_hub/core.py` (lazy `frictionless` import).
- 2–3 tests in `tests/test_data_package.py` (validate the repo's own shipped `datapackage.json` passes;
  a corrupted descriptor/resource fails; a clear ImportError when the extra isn't installed).
- A short ADR note recording the API and the "descriptor is a projection of the internal contracts" decision.

## Steps

1. Read `src/builders/data_package.py` to see exactly what the emitted `datapackage.json` contains
   (`resources[].path`, schema fields) so the loader/validator matches it.
2. Add the optional extra in `pyproject.toml` and a lazy import helper.
3. Prototype the chosen method(s): for `frictionless_validate`, wrap `frictionless.Package(descriptor).validate()`
   and return a compact pass/fail + errors dict (mirror the shape of `validate_dataset`). For `from_datapackage`,
   resolve resource paths relative to the descriptor and construct a `ChileHub` pointed at that data dir.
4. Add tests using the repo's own `data/normalized/datapackage.json` as the happy‑path fixture.
5. Write the ADR note.

## Done criteria

- [ ] The chosen method(s) exist in `src/chile_hub/core.py` with a lazy `frictionless` import + helpful ImportError
- [ ] `frictionless` is an optional extra in `pyproject.toml`, not a base runtime dep
- [ ] `frictionless_validate()` on the repo's own shipped `datapackage.json` returns a passing report; a corrupted fixture fails
- [ ] Tests in `tests/test_data_package.py` pass; `make lint` and `make format-check` exit 0
- [ ] ADR note records the API + "descriptor projects the internal contracts (ADR‑005)" decision
- [ ] `plans/README.md` status row updated

## STOP conditions

- If `frictionless` 5.x's `Package.validate()` API differs from the wrapper sketch, adapt to the installed
  version's real API and note it.
- If ADR‑005 forbids exposing a Frictionless‑based validation surface at all, stop and report — the maintainer
  should decide before adding it.

## Maintenance notes

- Keep this a thin projection: when the internal contracts change, `data_package.py` already regenerates the
  descriptor; this consumer path should need no change.
- Reviewer should confirm the base `pip install chile-hub` does not pull `frictionless` (only `chile-hub[validation]` does).
