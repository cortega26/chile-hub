# Phase 1 behavioral and equivalence matrix

**Status:** characterization contract for Phase 1. This document defines what
the Phase 1 harness must prove about the existing implementation; it does not
change the production architecture or make a future implementation choice.

## Purpose and evidence boundary

The migration roadmap makes behavioral and artifact equivalence the promotion
criterion, not line or branch coverage. This matrix translates that rule into
reviewable scenarios. An assertion is a **compatibility guarantee** only when
it is supported by a public contract, an accepted ADR, a verifier, a workflow
guardrail, or a consumer-facing test. Internal operation is deliberately not
promoted to a contract merely because it is observable in today's code.

The harness must exercise the current build boundary: `_load_inputs`,
`_compute_validations`, `_write_data_artifacts`, metadata generation,
`_generate_reports`, and `main` in `src/build_dev_db.py`. It must not call live
extractors or the network. Existing complementary evidence is retained:

- `tests/test_verify_pipeline.py` has golden-copy, corruption, and synthetic
  verifier coverage;
- `tests/test_builders_artifacts.py` covers manifest/ZIP/checksum behavior;
- `tests/test_chile_hub.py` covers public client, artifact, and CLI contracts;
- `tests/test_ci_config.py` preserves extraction-lane and workflow guardrails;
- ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-010, ADR-016, and ADR-017
  establish the relevant fail-closed, CUT, SemVer, track, contract, static
  distribution, freshness, and multi-source rules.

## Fixture model

The Phase 1 fixture is a complete, intentionally small staging tree in a
temporary directory. `tests.pipeline_characterization.write_legacy_build_staging_fixture`
generates it exclusively from committed static test literals; it never copies
mutable `data/staging/` inputs. Several legacy validators require 346 national
CUT rows, so the fixture's reviewable formulas generate those fixed-width
codes and validator-relevant values rather than committing hundreds of
mechanically identical CSV lines. It contains every CSV and `.metadata.json`
currently required by `_load_inputs`, plus a present valid candidate input. It
uses fixed source metadata, fixed CUT values (including a leading-zero value),
and no network. Module path constants are patched to the fixture staging and
an empty normalized directory; repository catalog, source-registry, and
contracts stay read-only inputs unless a scenario explicitly supplies a copied
corruption.

The fixture has two forms:

1. **baseline:** all required inputs, a valid present candidate, aliases, and
   the derived profile;
2. **variants:** the same static baseline with precisely one controlled
   omission or corruption.

This is a characterization harness, not an alternative extractor framework.
Small synthetic tables may use the repository's accepted fallback cardinality
where a validator requires it; they must never weaken a validator or mock the
phase under test merely to avoid supplying a valid input.

## Behavioral matrix

| ID | Scenario and assertion | Classification | Existing evidence / required harness assertion |
| --- | --- | --- | --- |
| B01 | A complete offline staging tree builds a direct public dataset and emits its declared physical outputs. | Compatibility guarantee | Catalog outputs, contracts, `ArtifactContractTests`; assert files, schemas, and rows for a direct layer. |
| B02 | Geography and territorial-profile layers are derived from their declared upstream staging inputs; their CUT keys remain strings with fixed width. | Compatibility guarantee | ADR-002; `derive_geography_layers`, `build_perfil_territorial_comunal`, validator tests. |
| B03 | `comunas_enriquecidas` remains an alias/compatibility view of `comunas`, not an independently written physical source. | Compatibility guarantee | `alias_for` catalog semantics and artifact-index skip rule; assert canonical artifact ownership, `ChileHub.get_output_path()` resolution, and equivalent `load_polars()` result. |
| B04 | A `stable_publishable` and `public_bundle_eligible` dataset is included in manifest, filtered bundle catalog, ZIP, and public inventory. | Compatibility guarantee | ADR-004, artifact builder, public artifact tests. |
| B05 | A present, valid candidate or otherwise public-ineligible dataset is absent from manifest and ZIP, while its candidate status remains visible in public inventory/bundle metadata where currently documented. | Compatibility guarantee | ADR-004, `verify_publication_policy`, bundle filtering tests. |
| B06 | A derived stable entry can qualify only through declared upstreams; candidate inheritance or missing upstream declarations is rejected by the registry/publication gates. | Compatibility guarantee | `VerifySyntheticTests` derived-entry cases. |
| B07 | Removing any current required staging CSV fails closed before data artifacts are written. | Compatibility guarantee | ADR-001 and `PipelineLogicTests.test_build_main_fails_when_staging_inputs_are_missing`. |
| B08 | Removing any required staging metadata file, or making it malformed/incomplete, fails closed with an actionable `SystemExit`. | Compatibility guarantee | metadata loader and `PipelineLogicTests` metadata tests. Exact prose is not asserted. |
| B09 | Removing an optional staging dataset and its metadata skips only that optional dataset under today's compatibility behavior; required core and derived outputs still build if their own required inputs exist. | Compatibility guarantee | `_load_inputs` optional branches. Assert the output/pipeline catalog reflects absence rather than asserting logs or branch order. |
| B10 | Invalid rows or structural/semantic validation rejection aborts the build before `_write_data_artifacts` and report/package creation. | Compatibility guarantee | ADR-001 and `_compute_validations`; inject a duplicate or invalid CUT and assert no new artifacts. |
| B11 | Contract verification rejects a physical output that violates required columns, types, primary key, fixed width, coverage, or declared outputs. | Compatibility guarantee | ADR-005 and `verify_schema_contracts` tests. |
| B12 | Fixed source fallback/reuse metadata is preserved into generated provenance/health, and a stable publication with blocked fallback is rejected by the publication profile. | Compatibility guarantee | source registry, `verify_publication_policy`, ADR-016/017. Exercise build metadata separately from publication rejection. |
| B13 | Fresh live inputs that meet policy are publication-eligible; stale, invalid-mode, unsafe fallback, unreviewed anomaly, or disallowed stale backfill is rejected. | Compatibility guarantee | publication verifier synthetic tests; no live fetch is involved. |
| B14 | Every manifest entry references an existing included artifact with its actual SHA-256/size; ZIP membership equals manifest membership; the external checksum verifies the ZIP. | Compatibility guarantee | artifact builder and verifier tests. |
| B15 | Generated catalog, metadata, health/status, provenance, redistribution, drift, data-package/DCAT, overview, and Markdown reports retain their documented structural fields and agree on dataset/artifact inventory. | Compatibility guarantee | verifier golden-copy tests and artifact/public API tests. Compare structured fields, not prose layout. |
| B16 | The current `dev`, `readiness`, `publication`, and `release` verifier profile boundaries remain: notably release does not require staging CSVs, while publication applies policy gates. | Compatibility guarantee | `VerifyGoldenCopyTests.test_release_profile_skips_staging_and_runs_publication_policy`. |
| B17 | Rebuilding from the same fixture and frozen clock produces equivalent datasets, validation results, public artifact paths, schemas, structured reports, and publication decision. | Compatibility guarantee | Phase 0 P0-D4 and roadmap Phase 1. See the comparator below. |
| B18 | The public Python constructor forms, documented methods, dataset IDs, aliases, CLI commands, typed/compatible exceptions, cache checksum behavior, and static latest URLs are unchanged by Phase 1. | Compatibility guarantee | docs/API, client/packaging tests, ADR-003/010. This phase need only re-run existing tests unless its harness touches the boundary. |
| I01 | Order in which `_load_inputs` reads files, map/dictionary insertion order, helper names, logger event text, and progress counters. | Implementation detail | No public contract; do not snapshot. |
| I02 | Exact `SystemExit` wording, traceback shape, temporary-file names, and internal exception nesting. | Implementation detail | Assert failure class and stable actionable category only. |
| I03 | Formatting/line wrapping of generated Markdown and JSON indentation where a structural consumer does not rely on it. | Implementation detail | Parse JSON and assert required fields; use Markdown assertions only for documented semantic content. |
| I04 | Number or order of internal builder calls and whether intermediary pandas conversions occur. | Implementation detail | Production performance work belongs outside Phase 1. |
| I05 | Current manually duplicated catalog/registry/builder maps and anti-drift implementation mechanism. | Implementation detail | Their externally visible results are guarantees; the mechanism is explicitly a future migration target. |

## Executable Phase 1 focused gate and traceability

The focused gate is deliberately a behavior suite, not a coverage target. Run
it before accepting a migration shadow result:

```bash
.venv/bin/pytest -q \
  tests/test_phase1_characterization.py \
  tests/test_pipeline_logic.py::PipelineLogicTests \
  tests/test_pipeline_logic.py::IndicatorFallbackTests \
  tests/test_pipeline_logic.py::ValidatorTests \
  tests/test_verify_pipeline.py::VerifyGoldenCopyTests \
  tests/test_verify_pipeline.py::VerifySyntheticTests \
  tests/test_builders_artifacts.py \
  tests/test_chile_hub.py
```

Every B-row has executable evidence in that command. The references below are
test node IDs (or a focused module/class where all its tests are required), so
the relationship is reviewable and does not depend on line coverage.

| Matrix rows | Focused-gate evidence |
| --- | --- |
| B01, B04, B14, B15, B17 | `tests/test_phase1_characterization.py::test_current_main_builds_isolated_offline_artifacts`; `::test_fixed_input_rebuild_is_semantically_equivalent_and_filters_candidates`; `tests/test_builders_artifacts.py` |
| B02, B10 | `tests/test_phase1_characterization.py::test_offline_staging_loads_direct_and_derived_datasets_without_extractors`; `::test_offline_staging_invalid_data_fails_closed_before_artifact_writing`; `tests/test_pipeline_logic.py::ValidatorTests` |
| B03 | `tests/test_phase1_characterization.py::test_alias_resolves_to_canonical_physical_artifact`; `tests/test_chile_hub.py` |
| B05, B06 | `tests/test_phase1_characterization.py::test_fixed_input_rebuild_is_semantically_equivalent_and_filters_candidates`; `tests/test_pipeline_logic.py::PipelineLogicTests::test_publication_policy_candidate_fallback_passes_when_excluded_from_manifest`; `tests/test_verify_pipeline.py::VerifySyntheticTests::test_publication_policy_rejects_derived_stable_without_upstreams` |
| B07, B08 | `tests/test_phase1_characterization.py::test_missing_required_csv_and_metadata_fail_closed`; `tests/test_pipeline_logic.py::PipelineLogicTests::test_load_metadata_fails_on_malformed_json`; `::test_load_metadata_fails_on_missing_required_fields` |
| B09 | `tests/test_phase1_characterization.py::test_optional_candidate_omission_keeps_required_build_path_available` |
| B11 | `tests/test_pipeline_logic.py::PipelineLogicTests::test_dataset_contract_rejects_missing_required_column`; `::test_dataset_contract_rejects_duplicate_primary_key`; `::test_dataset_contract_rejects_invalid_cut_width`; `tests/test_verify_pipeline.py::VerifyGoldenCopyTests::test_schema_contracts_passes` |
| B12 | `tests/test_pipeline_logic.py::IndicatorFallbackTests::test_process_indicators_records_raw_recovery`; `tests/test_pipeline_logic.py::PipelineLogicTests::test_publication_policy_stable_publishable_in_fallback_still_fails`; `::test_publication_policy_indicadores_raw_recovery_still_fails` |
| B13, B16 | `tests/test_verify_pipeline.py::VerifySyntheticTests`; `tests/test_verify_pipeline.py::VerifyGoldenCopyTests::test_release_profile_skips_staging_and_runs_publication_policy`; `::test_main_dev_profile_passes` |
| B18 | `tests/test_chile_hub.py` |

The injected emitted-artifact failure check is
`tests/test_phase1_characterization.py::test_declared_artifact_checksum_rejects_tampered_output`.
It complements—not replaces—the production verifier and artifact-builder test
coverage above.

## Deterministic comparator

The harness must run the baseline twice into separate normalized directories,
using identical staging bytes, contract/catalog/registry inputs, project
version, and a frozen UTC clock. It records a machine-readable comparison
report in the test output on failure.

The comparator operates at the strongest meaningful level for each artifact:

1. **Datasets:** compare Polars schema, row count, primary-key uniqueness, and
   canonical row values ordered by contract primary key. For fixed-format
   columns, assert the serialized string values as well as logical values.
2. **Validation and policy:** compare status, dataset IDs, errors/warnings by
   stable semantic content, freshness/policy decision, and exception class.
3. **Public artifact surface:** compare exact manifest artifact paths, dataset
   ownership, output/shared types, public eligibility, schema contracts, and
   package metadata. Recompute every declared SHA-256 and size from the
   produced bytes in each run.
4. **Structured reports:** parse JSON and compare all fields except the narrow
   allowlist below; compare Markdown only for its semantic headings/values and
   its file path in the manifest. JSON object-key serialization is canonicalized
   only after every emitted manifest checksum/size has been independently
   verified against its own bytes.
5. **Archives:** compare ZIP member names and each member's uncompressed bytes
   (with the JSON normalization rules below); independently verify the emitted
   `.sha256`. Do not require ZIP container bytes to match until archive timestamps
   are explicitly controlled. Excel is compared as public sheet/cell content and
   DuckDB as public table schemas/rows, not nondeterministic container/page bytes.

### Explicit volatile allowlist

The preferred approach is to freeze the clock. The following fields remain
excluded only where the existing build necessarily derives them from that clock
or appends historical state:

| Artifact / field | Reason | Comparator rule |
| --- | --- | --- |
| Root `generated_at_utc` in generated JSON/report structures, including `pipeline_metadata.json` and `artifact_manifest.json` | Build-time timestamp, not source data. | Remove exactly this JSON pointer before structured comparison; require valid UTC text. |
| `previous_generated_at_utc` in `dataset_changelog.json` | Depends on the prior normalized baseline intentionally supplied to the run. | Compare as `null`/present and valid UTC text; do not compare its value across clean directories. |
| `hub_health_history.jsonl` appended event timestamp and prior retained history | It is expressly append-only historical state, not a pure build result. | Compare the new event semantically after removing its `generated_at_utc`; assert prior history is preserved and no duplicate is added for an identical timestamp. |
| ZIP container member timestamps and resulting ZIP byte SHA-256/size | ZIP metadata is not presently controlled by the build. | Verify each declared hash/size against its emitted file, then compare a deterministic hash and byte total of member semantics; never simply discard the fields. |

`refreshed_at_utc`, source mode/detail, freshness result, indicator delivery,
dataset rows, contract contents, paths, membership, and declared hashes are not
general-purpose volatile fields. If their equality cannot be established from
the frozen fixture, the difference is a failure to investigate, not a field to
add to this allowlist.

## Current architecture limits to represent, not hide

- A full `main()` baseline needs the ten currently required staging datasets;
  optional datasets are independently skippable only for the five optional
  branches in `_load_inputs`. The fixture cannot pretend that a required
  dataset is optional.
- `perfil_territorial_comunal` currently takes several direct inputs regardless
  of later publication policy. A small direct-only fixture therefore proves a
  focused phase, but does not replace the full derived-path baseline.
- Publication rejection is a verifier/profile behavior after build metadata is
  available. A fallback fixture may build in development and still be required
  to fail publication; conflating those outcomes would erase the accepted
  fallback policy.
- The existing `hub_health_history.jsonl` is stateful. Its append semantics are
  characterized separately rather than excluded wholesale from equivalence.

## Completion rule

Phase 1 is ready only when each B-row has an executable test or an explicitly
named existing test that is run in the Phase 1 gate, all unexplained comparator
differences fail, and the relevant existing verifier/public API/CI guardrails
still pass. Coverage may be collected around `build_dev_db.py` to identify
unexercised branches, but no percentage is a completion criterion.
