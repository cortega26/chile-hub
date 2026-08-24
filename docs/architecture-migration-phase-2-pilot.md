# Architecture migration — Phase 2 pilot record

**Status:** executed — Phase 2 pilot for `partidos_politicos`, compatibility
backed by `DatasetSpec`, per the frozen
[migration roadmap](architecture-migration-roadmap.md) and ratified decisions
[ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** one dataset only. No Phase 3+ work is started by this record.

## What was added

| Component | Path | Purpose |
| --- | --- | --- |
| Typed model + loader | `src/registry/dataset_spec.py` | `DatasetSpec` frozen dataclass, fail-closed `parse_dataset_spec`/`load_dataset_spec`, mechanical compatibility projections, shadow overlay adapters |
| Package init | `src/registry/__init__.py` | Public surface of the registry module |
| Pilot spec | `data/dataset_specs/partidos_politicos.json` | Versioned (`spec_version: "1.0"`) operational declaration of the pilot |
| Equivalence tests | `tests/test_phase2_datasetspec.py` | 22 tests: model typing, projection equality vs legacy, overlay identity, fail-closed cases, spec-backed offline build |
| Shadow wiring | `src/builders/_shared.py` `_load_catalog_config()` | The pilot's catalog entry is read through its spec projection; every other dataset keeps its legacy entry verbatim |
| Shadow wiring | `src/builders/reports.py` `load_source_registry()` | The pilot's source-policy entry is read through its spec projection; the rest is legacy |
| Companion guard | `scripts/check_companion_paths.py` | New co-change rule: `data/dataset_specs/` requires docs/tests/AGENTS companions |

## Authority boundary applied (P0-D1, P0-D2)

`DatasetSpec` owns the pilot's **operational facts**: identity, lifecycle kind,
publication track and public eligibility, maturity/confidence, source/reuse/
fallback/freshness policy, extraction lane and extractor reference, contract
reference, semantic-validator reference, aliases/dependencies, declared
outputs, and documentation metadata.

The separately authored contract
(`contracts/datasets/partidos_politicos.schema.json`) remains the authority for
**structural schema facts**. This is enforced mechanically, not by convention:

- `parse_dataset_spec` rejects any spec that authors contract-owned keys
  (`columns`, `column_types`, `nullable_columns`, `required_columns`,
  `primary_key`, `expected_record_count`, `coverage_policy`,
  `publish_outputs`) with a `DatasetSpecError` naming the violated boundary.
- The catalog projection reads `expected_record_count` **from the referenced
  contract** rather than from the spec — a direct demonstration that the
  projection is mechanical and the contract remains the schema authority.
- The loader fails closed when the referenced contract path does not exist.

No fact is independently authored in both the spec and the contract. No legacy
catalog/registry/contract path changed; all non-pilot datasets keep reading
legacy JSON verbatim.

## Shadow adapters and equivalence

The build's two configuration readers (`_load_catalog_config`,
`load_source_registry`) overlay the pilot's spec projection when a spec file
exists and leave every other entry byte-identical. The strongest equivalence
assertion is `test_overlay_is_semantically_identical_to_legacy`: the overlaid
catalog and registry are **equal to the legacy payloads as whole objects**,
so no build consumer can observe a difference.

A full offline build with synthetic pilot staging
(`test_pilot_build_reads_through_spec_backed_path`) proves the pilot flows
through the spec-backed path end to end: `reuse_policy` and freshness policy
reach `pipeline_metadata.json`; description/join keys/confidence/outputs/
usage examples reach the public `dataset_catalog.json`; source policy reaches
`source_readiness.json`; declared outputs are emitted and enter the manifest;
and the validator referenced by the spec runs and passes. Artifact content is
unchanged by construction because the projections are equal to the legacy
inputs.

## Enum/public inventory policy (documented and tested)

`DatasetSpec.public_inventory()` declares public eligibility from track +
bundle eligibility. Policy for this phase: a `stable_publishable` and
`public_bundle_eligible` dataset is a member of the public `Dataset` enum;
candidates may or may not be (the current surface is unchanged). The tests
assert `Dataset.PARTIDOS_POLITICOS` membership and that the enum value list is
byte-identical to the pre-pilot surface. Enum generation from the registry is
deliberately not implemented (roadmap "Changes that must not be implemented
independently").

## What did not change

- No dataset other than `partidos_politicos` was migrated.
- Public artifact paths, schemas, dataset IDs, aliases, CLI behavior,
  publication tracks, extraction lanes, and runtime client behavior are
  unchanged (verified by the full existing suite and artifact gates).
- No DAG, no extractor invocation change, no cache/release architecture
  change, no CI workflow change; anti-drift guards remain and one co-change
  rule was added.
- Fail-closed validation and stable/candidate policy are preserved exactly.

## Validation run for this record

Executed locally with the working tree of 2026-08-23 (Phase 0/1 docs and
Phase 1 tests present; `data/normalized/` artifacts regenerated by the Phase 1
build gates):

- `pytest tests/test_phase2_datasetspec.py` — 22 passed.
- Phase 1 focused gate (characterization + pipeline logic + verifier +
  builders/artifacts + public API) — passed.
- `check_companion_paths.py registry`, `check_validation_registration.py`,
  `check_agents_sync.py`, `sync_docs.py --check`, `check_landing_sync.py` —
  passed.
- `make build`, `make verify`, `make lint`, `make format-check` — passed with
  the spec-backed readers active.

## Next gate (Phase 3A — not started here)

Before Phase 3A begins: merge of this pilot, explicit maintainer acceptance of
the Phase 2 record, and re-run of the focused Phase 2 gate on the merged tree.
Phase 3A then repeats the same pattern on the direct stable pilot cohort with
per-dataset projection equivalence and fixed-input build/verify/package
equivalence gates.
