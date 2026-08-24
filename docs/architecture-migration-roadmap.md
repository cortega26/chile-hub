# Incremental migration roadmap for the clean-sheet architecture review

> **Roadmap status: frozen for implementation (2026-08-23).** This is the
> approved sequencing baseline after final review. New recommendations or scope
> changes belong in a separate follow-up decision. Phase 0 was documentation-only
> and is closed: its accepted decision package and compatibility inventory are
> recorded in [architecture-migration-phase-0-decisions.md](architecture-migration-phase-0-decisions.md)
> and [architecture-migration-compatibility-inventory.md](architecture-migration-compatibility-inventory.md),
> ratified by ADR-018 and ADR-019. Decisions assigned to later phases remain
> deferred.

## Purpose and compatibility envelope

This roadmap covers only recommendations classified A — Worth changing now. It is
an incremental strangler migration, not a rewrite. Each phase is independently
releasable and leaves existing code working until its replacement has been proven
with behavioral/equivalence tests. Behavioral and artifact equivalence—not line
coverage percentage—is the primary safety criterion throughout. Coverage remains
a diagnostic for locating unexercised code, never a promotion gate by itself.

The following behavior is non-negotiable throughout:

- extract → build → verify → test → publish stays fail-closed;
- stable_publishable and candidate tracks, including derived-dataset inheritance,
  keep the same publication behavior;
- CUT string encoding, existing schemas, dataset IDs, aliases, artifact names,
  current static latest URLs, and release bundle contents remain compatible;
- the current client constructor forms, local bundle cache, checksum verification,
  public methods, CLI commands, and error behavior remain supported;
- contracts remain the internal schema contract; Frictionless and DCAT remain
  generated interoperability projections;
- daily data updates do not require a package SemVer release, and the existing
  dataset-compatibility/deprecation policy remains in force.

No phase introduces partial publishing, automatic quarantine, a dynamic API,
or a workflow-engine dependency.

## Phase 0 — Decide only the target boundaries needed before the pilot

### Review findings addressed

- One authoritative typed DatasetSpec.
- The minimum compatibility and promotion-gate policy required to migrate a
  DatasetSpec pilot safely.

### Dependencies

Phase 0 has two gates: decision-package review plus the compatibility inventory
permit Phase 1 characterization; explicit acceptance of P0-D1–D4 is required
only before Phase 2. Decisions deliberately deferred here are prerequisites
only for their owning implementation phase.

### Architectural decisions required

Accept proposed decisions that decide:

1. The DatasetSpec boundary: canonical fields, fields that stay in
   source-specific extractor code, and generated compatibility projections.
2. The contract relationship: a spec references the existing separately authored
   contract file. Existing contract paths and contract authority remain intact.
3. Lifecycle semantics: direct, alias, derived, candidate, stable, deprecated,
   upstream inheritance, and daily/monthly/ad-hoc/stub extraction lanes.
4. The behavioral/equivalence baseline and objective promotion-gate policy used
   to make a migrated path the default.

The following decisions are safely deferred; deciding them now would manufacture
detail before their boundary exists:

| Deferred decision | Decide before | Reason for deferral |
| --- | --- | --- |
| Final `ExtractionResult` provenance/time field semantics and extensions | Phase 4 | Phase 4 owns the extractor boundary and can test the model against real source lanes. |
| Snapshot provider, retention, legal/access policy, credentials, and archive-failure publication policy | Phase 7 | They do not affect a registry pilot or graph compatibility adapter. |
| Release ID, manifest version, signing, retention, rollback, and static `latest` mapping | Phase 8 | They are meaningful only once durable snapshots and manifest materialization exist. |
| Client release pinning, offline/refresh behavior, cache layout, and remote datapackage scope | Phase 10 | The client should target a proven release contract, not a provisional one. |
| New public-module names and facade deprecation duration | Phase 10 | This concerns a later API split and must not constrain the registry migration. |

### Existing repository constraints to retain

- ADR-001: a critical validation failure blocks publication.
- ADR-004: publication tracks are product policy, not a packaging detail.
- ADR-005: complex semantic validation remains Python; it is not all expressible
  as schema configuration.
- ADR-008: Frictionless is optional and lazy, never the canonical internal model.
- ADR-010: distribution remains static; current Pages URLs are a mutable latest
  contract until a compatibility view replaces them.
- ADR-016: content age differs from retrieval time; stale backfill remains a
  publication gate, not a build failure.
- The four extraction lanes in docs/extraction-lanes.md remain distinct.

### Affected components conceptually

The proposed-decision package, the architecture review, compatibility
documentation, and DatasetSpec design documentation only.

### Existing behavior that remains unchanged

Everything. This phase makes decisions and documents them; it changes no code.

### Risks

A vague specification would simply recreate current duplication. A decision that
tries to encode semantic validation or source-specific recovery entirely as data
would produce an unusable framework.

### Completion record

- P0-D1 through P0-D4 are accepted by the repository maintainer and ratified by
  ADR-018 and ADR-019.
- A compatibility inventory covers all public methods, CLI commands, artifact
  paths, latest URLs, cache behavior, and schemas.
- A pilot dataset is selected: stable/public, direct, one physical output, known
  source lane, and no alias/derived or special scraping behavior.

The completed inventory selects `partidos_politicos` as the Phase 2 pilot. No
`DatasetSpec` draft or production configuration was created in Phase 0.

### Validation before proceeding

Decision-package review and a written compatibility matrix are required before
Phase 1. Explicit maintainer acceptance of P0-D1–D4 is required before Phase 2.
There is no implementation validation in this phase.

## Phase 1 — Characterize current behavior and build a safe refactoring harness

### Review findings addressed

This is an enabling phase for every A recommendation. It protects the current
manual build, validation, artifact, release, extractor, and public-client
behavior before they are changed.

### Dependencies

Phase 0 compatibility inventory.

### Desired end-state

The complete pipeline can run from synthetic staging fixtures with no network
access. Tests characterize the existing four build phases and main orchestration
against accepted contracts and known-good artifacts.

### Affected components conceptually

The build orchestrator, builder modules, artifact/report verification, synthetic
staging fixtures, and pipeline/public API test suites. This is the scope of the
existing Plan 077 direction.

### Existing behavior that remains unchanged

All artifact content and paths, required/optional staging rules, error behavior,
publication policy, and client behavior. This phase adds tests only.

### Compatibility and regression risks

Characterization tests can institutionalize a bug. Assertions must target
published contracts and accepted policy, rather than incidental ordering or
timestamps from the current implementation.

### Prerequisite decisions versus mechanical work

- Decision: classify each observed output as a compatibility guarantee or an
  implementation detail.
- Mechanical work: construct synthetic staging, patch paths, run each phase and
  main, and assert output structure.

### Objective completion criteria

- Synthetic staging runs load, validation, artifact writing, reporting, and main
  without extractors or network.
- A reviewed behavioral matrix covers the four phases and `main`: successful
  direct and derived builds, candidate exclusion, missing/optional staging,
  validation failure, fallback/publication rejection, and published artifact /
  report behavior.
- Deterministic rebuild comparisons prove equivalent public artifacts,
  validation outcomes, manifests, and reports for fixed inputs, with an explicit
  allowlist only for volatile metadata.
- Line coverage is reported to identify unexercised paths, but is not a phase
  completion or promotion criterion.
- Full test suite, build, verify, lint, and formatting checks pass.

### Required validation before Phase 2

Focused pipeline/artifact/verifier behavioral tests, a deterministic rebuild
comparison, and the standard build/verify/test/lint/format gates. Reported line
coverage may guide additional tests but cannot replace those checks.

## Phase 2 — Add a DatasetSpec pilot behind compatibility adapters

### Review findings addressed

- A single typed DatasetSpec as authoritative configuration.
- Generated or explicitly scoped public Dataset enumeration.
- Reduction of duplicated catalog, registry, contract, and documentation facts.

### Dependencies

Phases 0 and 1.

### Desired end-state

One pilot dataset has a typed spec. The spec produces in-memory compatibility
views equivalent to its current catalog entry, source policy, contract reference,
documentation metadata, and enum behavior. Legacy JSON remains the runtime input
for every non-pilot dataset.

### Affected components conceptually

A new registry/spec module and versioned spec file; catalog/source-registry/
contract readers; builder shared configuration; public Dataset enum; documentation
generation; companion-path checks; and registry tests.

### Existing behavior that remains unchanged

Current config files and paths, contract files, documentation locations, enum
values, CLI names, artifact names, source policy, tracks, lanes, and outputs.
Candidate datasets continue to be excluded exactly as today.

### Compatibility and regression risks

A generated compatibility view can drop a field used by a verifier. Enum
generation can expose candidate datasets or remove a current enum value. A spec
can incorrectly mark a derived dataset as extractable.

### Prerequisite decisions versus mechanical work

- Decision: canonical field ownership and public enum policy.
- Mechanical work: parse/type-check the spec, create legacy-compatible adapters,
  add the pilot, and run semantic equivalence tests.

### Objective completion criteria

- Pilot spec round-trips to equivalent catalog/source-policy/contract metadata.
- A build, verify, and package run using the spec-backed view yields identical
  artifact hashes except explicitly volatile metadata.
- Enum policy is documented and tested.
- Legacy config remains authoritative for all non-pilot datasets.

### Required validation before Phase 3

Registry, companion-path, validation-registration, landing-sync, and agent-sync
checks; contract verification and changelog compatibility checks; focused public
API and packaging tests.

## Phase 3 — Migrate all dataset definitions to the canonical registry

### Review findings addressed

- One authoritative DatasetSpec.
- Consistent enum policy.
- Removal of manual cross-file dataset drift.

### Dependencies

Successful Phase 2 pilot. This phase must complete before the build graph and
artifact policy are made registry-driven.

### Desired end-state

Every dataset has one DatasetSpec that defines identity, source/reuse/fallback/
freshness policy, track, public eligibility, lane, contract reference, semantic
validator registration, outputs, aliases, dependencies, and documentation
metadata.

Existing catalog, source registry, and documentation remain at their present
paths and may become compatibility projections as their ownership is proven.
Existing contracts remain separately authored authoritative artifacts referenced
by DatasetSpec; they are not generated by this migration absent a later approved
ADR.

### Independently mergeable migration batches

Each batch is a complete vertical slice: it adds only the eligible specs, keeps
legacy inputs authoritative for every un-migrated dataset, and proves the same
compatibility projections and fixed-input behavior before merge. A later batch
must not require a temporary alternate registry model.

| Batch | Eligible datasets | Why this order | Merge gate |
| --- | --- | --- | --- |
| 3A — direct stable pilot cohort | Stable, public, direct, single-source datasets with no alias, derived dependency, special scraper, or shared-extractor fan-out | Repeats the Phase 2 pattern on a bounded cohort and exposes projection defects without lifecycle edge cases. | Per-dataset spec/projection equivalence; fixed-input build/verify/package equivalence; public inventory unchanged. |
| 3B — stable shared-source and multi-artifact cohort | Stable direct datasets that share an extractor, emit multiple related outputs, or have conventional multi-source policy | Establishes one source policy and one shared-extractor mapping without mixing in derived/publication exceptions. | 3A gates plus shared-extractor coverage, source-policy equivalence, and no cross-dataset output change. |
| 3C — aliases and derived cohort | Aliases and datasets with one or more upstream dataset dependencies | Makes dependency and track-inheritance semantics executable only after direct definitions are proven. | 3B gates plus alias resolution, dependency ordering, derived-track inheritance, and derived-output equivalence. |
| 3D — exceptional lifecycle cohort | Candidate, deprecated, monthly/ad-hoc, fallback-heavy, scraper, and multi-source exception datasets | Contains fragile or intentionally non-default behavior so it cannot destabilize the public stable path. | 3C gates plus lane ownership, candidate/deprecated exclusion, fallback/reuse behavior, and CI-guard equivalence. |

**Multi-source recovery preservation guard:** Current override, published
backfill, and delivery-label behavior remains on legacy extractor adapters
through 3A–3C, including its existing publication/freshness gates. Phase 3D is
the first batch permitted to represent that behavior in DatasetSpec and must
prove delivery-label, override-precedence, backfill, and failure-path
equivalence with recorded fixtures before migration.

### Affected components conceptually

All dataset configuration, source registry, contracts, documentation, registry
readers in builders/scripts/client, enum generation, and anti-drift checks.

### Existing behavior that remains unchanged

Dataset IDs, schemas, aliases, expected files, workflows, data contents,
publication filtering, and source policy. Daily data refresh remains independent
of software SemVer.

### Compatibility and regression risks

Bulk migration can change candidate/public filtering, aliases, lane assignment,
or generated documentation. One projection defect can affect many datasets.

### Prerequisite decisions versus mechanical work

- Decision: the 3A–3D eligibility rules, generated-document diff policy, and
  the objective gate that permits the next batch.
- Mechanical work: author specs, generate/prove projections, migrate readers,
  and compare outputs one batch at a time.

### Objective completion criteria

- Each completed batch meets its merge gate and leaves all remaining datasets on
  their legacy-compatible path.
- After 3D, every dataset has exactly one spec and one-to-one coverage is
  asserted among specs, contracts, source policy, and public inventory.
- Existing anti-drift gates pass against generated projections.
- Fixed inputs retain the same dataset change-severity result.
- No public artifact path, schema, or client API changes.

### Required validation before Phase 4

Run each batch's merge gate, then focused tests for that batch, build/verify/
package smoke tests, schema/change-severity comparisons, and the full suite.
Advance only when the prior batch has no unresolved behavioral or projection
discrepancy; line coverage changes do not qualify a batch on their own.

## Phase 4 — Standardize extractor results while retaining script entry points

### Review findings addressed

- Make the extractor abstraction real instead of parallel to production flow.
- Establish the source-snapshot/provenance boundary needed by later phases.
- Prepare registry-driven orchestration.

### Dependencies

Phase 3, because lane/source policies must be canonical. It precedes the build
graph migration.

### Desired end-state

Every extractor can return a common internal ExtractionResult: normalized data,
staging metadata, source snapshot identity (`snapshot_hash`) and immutable
reference, source mode,
`retrieved_at`, `source_published_at` when known, a documented nullable
`observed_period` when the source describes a time range, and declared
incremental/reuse policy. This is the final extractor-facing provenance/time
model; later phases may normalize, validate, and project it, but must not add a
second structural model.

Existing process functions and command-line script entry points remain adapters.
Makefile and workflows continue to call the same scripts initially.

### Affected components conceptually

Base extractor, individual extractors, shared source/HTTP utilities, staging
metadata writing, Makefile/workflow guardrails, and extractor tests.

### Existing behavior that remains unchanged

Script commands, function names, staging output paths, fallback behavior, raw
snapshot behavior, schedule ownership, isolated scrapling environment, and the
unscheduled SINIM stub.

### Compatibility and regression risks

The existing generic run path does not have production-complete metadata.
Switching callers prematurely could silently degrade provenance. Incremental
extractors may depend on existing staging/raw state. A common model must retain
source-specific fallback reasons.

### Prerequisite decisions versus mechanical work

- Decision: final mandatory/nullable ExtractionResult fields, definitions of
  `source_published_at` and `observed_period`, and source-specific extension
  policy.
- Mechanical work: adapters around existing scripts, result conversion, tests,
  then phased extractor conversion.

### Objective completion criteria

- A pilot extractor produces staging data and metadata equivalent to its legacy
  script on recorded input.
- The migration demonstrates one ordinary extractor, one incremental/fallback
  extractor, and one multi-source or scraper extractor.
- Each demonstrated result includes every mandatory provenance/time field; each
  unavailable optional field is represented according to its accepted nullable
  policy, not inferred from retrieval time.
- Each migrated extractor has script-adapter and in-process result tests.
- Make extract and workflow lane ownership are unchanged.
- No production caller directly replaces a script with bare BaseExtractor.run.

### Required validation before Phase 5

Extractor and CI-config tests; source-mode/fallback/reuse tests; daily, monthly,
and candidate synthetic workflow tests; build/verify over every migrated output.

## Phase 5 — Move build execution from manual maps to a registry-driven graph

### Review findings addressed

- Declarative build DAG/registry.
- Elimination of hard-wired input, validation, metadata, and artifact maps.
- Preservation of the semantic-validator boundary.

### Dependencies

Phases 1 through 4. All datasets need canonical definitions and extractors need
a common result boundary before graph execution becomes safe.

### Desired end-state

The build engine resolves dependencies from specs and invokes registered load,
transform, semantic-validation, and artifact nodes. Structural rules may be
compiled from the spec, but semantic validators remain ordinary Python callables.
A legacy-build compatibility mode remains until graph output is proven equivalent.

Start with a leaf dataset, then an alias/derived path, then a multi-input
derived dataset, and only then default to the graph.

### Affected components conceptually

Build orchestrator, staging schema logic, metadata/formats/artifacts/reports
builders, validator registration, verifier scripts, and pipeline tests.

### Existing behavior that remains unchanged

The fail-closed sequence; required/optional semantics; validation outcomes;
artifact paths and formats; report schemas; publication gates; and derived
track inheritance.

### Compatibility and regression risks

Topological ordering can alter materialization/error timing. Optional-input
semantics can be weakened. A generic registry can omit a validator or
accidentally change hash ordering.

### Prerequisite decisions versus mechanical work

- Decision: node types, dependency semantics, optionality, and output-equivalence
  criteria.
- Mechanical work: graph resolver, registered nodes, one-by-one migration, and
  retirement of manual maps only after successful default use.

### Objective completion criteria

- Synthetic staging runs legacy and graph paths with equivalent datasets,
  validations, artifacts, manifests, and reports.
- Graph tests cover direct, alias, derived, candidate, and multi-source paths.
- Validation-registration checking remains effective or is replaced with a
  stronger spec-to-callable completeness assertion.
- The graph becomes default only after all datasets pass equivalence; legacy
  retirement has a documented release target.

### Required validation before Phase 6

Full pipeline characterization, validation, builder/artifact/report, verifier,
and workflow suites; repeated deterministic builds; and publication-profile
checks using representative live/fallback fixtures.

## Phase 6 — Normalize, validate, and project provenance/time metadata

### Review findings addressed

- Normalize and project the final extractor provenance/time model.
- Compile structural validation from the canonical model without removing
  semantic Python validation.

### Dependencies

Phase 3 for canonical fields and Phase 4 for extractor results. It must precede
release manifests, which need precise snapshot linkage.

### Desired end-state

The final `ExtractionResult` fields introduced in Phase 4 are consistently
normalized into staging metadata, runtime contracts, reports, and verifier
inputs. This phase does not introduce new provenance/time concepts. It retains
legacy-compatible `refreshed_at_utc` as a projection while exposing
`retrieved_at`, nullable `source_published_at`, nullable `observed_period`,
`snapshot_hash`, and immutable snapshot reference according to the Phase 4
definitions.

Keys, required columns, fixed widths, and suitable coverage/output rules are
compiled from specs/contracts. Referential, range, cohort, anomaly, and other
semantic validation stays in Python.

### Affected components conceptually

Specs/contracts, extractors/staging metadata, validation module, runtime
contracts, metadata/report builders, verifier, and freshness/status consumers.

### Existing behavior that remains unchanged

refreshed_at_utc remains present. ADR-016 behavior is preserved exactly:
content age is based on delivered data, cadence-specific stale backfill remains
an overrideable publication gate, and it does not become a build validation
failure.

### Compatibility and regression risks

Missing source publication times must be valid where sources cannot provide
them. Replacing freshness terminology can mislabel data. Over-generalizing
validation can weaken real semantic checks.

### Prerequisite decisions versus mechanical work

- Decision: structural-versus-semantic rule boundary. Field meaning and
  nullability are already decided for `ExtractionResult` in Phase 4.
- Mechanical work: normalize and project the established fields, compile
  structural rules, update reports, and add compatibility/equivalence tests.

### Objective completion criteria

- Every metadata record has retrieved_at and snapshot_hash; optional time fields
  follow documented nullable policy.
- Recorded inputs retain identical validation pass/fail outcomes.
- Structural compiler coverage is complete for declared structural rules.
- Existing freshness and publication tests, including stale backfill, pass
  without behavioral change.

### Required validation before Phase 7

Runtime/contract and semantic validation suites, metadata/report suites,
publication-policy verification, and a data rebuild/migration rehearsal.

## Phase 7 — Establish durable content-addressed source snapshots

### Review findings addressed

- Durable content-addressed raw source storage.
- True reproducibility and provenance linkage before immutable releases become a
  production publication boundary.

### Dependencies

Phases 4 and 6. The final `ExtractionResult` and its normalized provenance
projection supply the snapshot identity. This deliberately precedes shadow
release manifests and production promotion: a release cannot honestly claim
reproducibility until its included source material is durably resolvable.

### Desired end-state

Extractors register immutable source snapshots through a storage abstraction.
Every eligible build result has a verified durable snapshot reference before it
can enter a shadow release. Local raw files may remain development caches; durable
archival storage is the audit source.

### Affected components conceptually

Extractor/storage utilities, metadata, CI credentials, retention jobs, local
developer tooling, reproducibility docs, and integration tests.

### Existing behavior that remains unchanged

Existing raw naming may remain as a local cache. Fallback/source modes,
append-only semantics, fail-closed behavior, and consumer independence from
archive credentials remain unchanged. The current normalized output remains the
only public publication boundary.

### Compatibility and regression risks

Archive upload failure could produce unreproducible claims; licensing may prohibit
archival/redistribution; large binaries affect CI cost/time; binary hashes must be
streaming/exact.

### Prerequisite decisions versus mechanical work

- Decision: provider, retention, legal/access policy, credentials, and whether
  archive success blocks a *shadow-release-eligible* build.
- Mechanical work: hash/upload/register, replay tools, local cache, and active
  snapshot migration.

### Objective completion criteria

- Every dataset selected for the release-path pilot has a resolvable immutable
  snapshot reference and verified hash.
- One direct and one derived dataset rebuild from archived snapshots without
  network and match their accepted artifacts and validation results.
- Missing/failed archival follows accepted policy, blocks release eligibility,
  and never produces a falsely reproducible claim.
- Retention/license policies are documented and automated.

### Required validation before Phase 8

Fake object-storage integration tests, corruption/retry/idempotency/retention
tests, and a complete fixed-input rebuild/verification from archived source
material.

## Phase 8 — Produce immutable release manifests in shadow mode

### Review findings addressed

- Versioned atomic release architecture.
- Release identity tied to verified durable snapshot provenance.
- Foundation for safe publisher/cache/client evolution.

### Dependencies

Phases 3, 6, and 7. A manifest is not release-eligible until dataset policy,
normalized provenance, and durable snapshot resolution are all available.

### Desired end-state

Each eligible build produces a shadow immutable release directory and manifest in
addition to the current flat normalized output. The manifest names included
artifacts, contract/spec versions, durable snapshot references and hashes,
checksums, tracks, and verification state. Legacy normalized outputs remain
canonical to consumers.

### Affected components conceptually

Artifact/manifest/package builders, pipeline metadata, verifier, CI uploads,
static catalog generation, and artifact/package tests.

### Existing behavior that remains unchanged

Current normalized paths, ZIP contents, checksum behavior, Pages latest URLs,
data-manager behavior, candidate exclusion, and alias handling. No client reads
the shadow release by default.

### Compatibility and regression risks

The manifest can misrepresent an artifact, include a candidate, reference an
unavailable snapshot, consume excess storage, or use non-deterministic release
identity.

### Prerequisite decisions versus mechanical work

- Decision: release-ID semantics, manifest version, retention, signing/checksum,
  and the required archival state for manifest eligibility.
- Mechanical work: shadow materialization, manifest validation, artifact
  comparison, and CI upload.

### Objective completion criteria

- Manifest verification checks every artifact checksum, eligibility rule, and
  durable snapshot reference.
- Identical inputs yield identical release membership and payload checksums,
  excluding explicit volatile fields.
- Legacy ZIP and shadow release expose the same public datasets/artifacts.
- CI uploads shadow releases without changing consumer behavior.

### Required promotion gates before Phase 9

All of the following must pass; elapsed time alone does not qualify:

1. Ten successful production-equivalent shadow builds, including at least two
   scheduled daily runs and one representative run for each non-daily lane that
   may contribute a release.
2. For every run, manifest/artifact/public-inventory equivalence passes and every
   included snapshot is durably resolvable with a matching hash.
3. Fault tests prove that a missing artifact, checksum mismatch, candidate leak,
   or missing snapshot prevents shadow-release eligibility.
4. No unresolved release-correctness or backwards-compatibility defect remains.

## Phase 9 — Switch publication to atomic releases while retaining latest paths

### Review findings addressed

- Atomic publish boundary.
- Elimination of mixed mutable normalized output as the public publication
  boundary.

### Dependencies

The Phase 8 objective promotion gates. Durable snapshots therefore precede
production promotion rather than following it.

### Desired end-state

CI publishes a complete immutable release only after all existing gates pass,
then atomically updates a static latest view that preserves existing
`data/normalized` URLs and ZIP naming. A failed run leaves the prior latest
release untouched.

### Affected components conceptually

Publishing workflow, artifact/package scripts, Pages deployment, verifier, static
latest index/pointer, release retention, HTTP-access docs, and cache tests.

### Existing behavior that remains unchanged

Pages latest URLs, direct HTTP use, release bundle behavior, public contents,
failure policy, and static-only hosting. No dynamic service is added.

### Compatibility and regression risks

Static hosting may require an atomic generated index rather than a filesystem
pointer. Publishing order can expose a manifest before files. Retention can
remove a release cached by users.

### Prerequisite decisions versus mechanical work

- Decision: static atomicity mechanism, rollback, retention, and pinned release
  URL contract.
- Mechanical work: stage/promote/rollback, latest compatibility view, CI changes,
  and smoke tests.

### Objective completion criteria

- Fault injection proves failed publication leaves latest unchanged.
- Latest and pinned releases both pass checksum/manifest/snapshot verification.
- Existing ChileHub default behavior and direct URLs work without client changes.
- A rollback promotes a known prior immutable release without rewriting it.

### Required validation before Phase 10

End-to-end publishing against a static server; cache/download/checksum/rollback
smoke tests; existing public API, packaging, verifier, artifact, and landing
suites.

## Phase 10 — Split consumer client from operational reporting with a facade

### Review findings addressed

- Separate the consumer API from operational/reporting functions.
- Reduce the overloaded ChileHub public object without breaking users.

### Dependencies

Stable structured manifests and reporting projections from Phases 8–9. Splitting
earlier would move unstable behavior twice.

### Desired end-state

A small client owns discovery, describe/path resolution, load/scan, SQL, cache/
release operations, and entity resolution. An inspector/operational module owns
health, reports, provenance, drift, inventory, packages, and table rendering.
The CLI composes those modules.

ChileHub remains a forwarding facade for a published deprecation window.

### Affected components conceptually

Core client, data manager, CLI, rendering, status utilities, exports, typing,
API docs, and public/cache/report/CLI tests.

### Existing behavior that remains unchanged

Constructor forms, load_polars, SQL, aliases, validation methods, exceptions,
cache behavior, documented CLI commands, table output, optional lazy dependencies,
and local datapackage/Frictionless behavior.

### Compatibility and regression risks

Users may import or monkey-patch ChileHub; moving renderers can alter tables;
loader caching can alter freshness visibility.

### Prerequisite decisions versus mechanical work

- Decision: module names, permanent core API, and facade/deprecation duration.
- Mechanical work: extract modules, forwarding methods, CLI migration,
  warnings/documentation, and import/package tests.

### Objective completion criteria

- New client and inspector APIs are documented and independently tested.
- Every prior public ChileHub method works through the facade with equivalent
  results/output where promised.
- CLI output snapshots and clean-environment packaging smoke tests pass.
- A future-major removal list and migration guide are published; no forwarding
  method is removed in this roadmap.

### Required validation before Phase 11

Core, public API, renderer, data-manager, packaging-runtime, CLI smoke, docs
build, and clean-install optional-dependency tests.

## Phase 11 — Retire legacy duplication and CI documentation auto-healing

### Review findings addressed

- Complete the single-source DatasetSpec migration.
- Remove drift mechanisms made redundant by generation.
- Remove CI commits to main after release/docs ownership is deterministic.

### Dependencies

All previous phases plus the completed Phase 8 promotion gates, successful Phase
9 fault-injection/rollback tests, and a full compatibility matrix for the new
default paths. Elapsed time is not a substitute for this evidence.

### Desired end-state

DatasetSpec is the sole authored dataset model for the dataset facts it owns.
Legacy catalog/source-registry/docs are generated compatibility outputs or
intentionally public projections where that ownership is proven. Contracts remain
separately authored authoritative schema artifacts referenced by DatasetSpec
unless a later ADR explicitly changes that boundary.
Manual build maps are removed. CI validates specs and projections rather than
reconciling independent hand-authored files. Release automation generates docs
inside the verified release transaction; CI no longer commits documentation fixes
to main.

### Affected components conceptually

Legacy config readers, builder maps, companion/validation-registration checks,
doc-sync scripts, docs-autosync workflow, Makefile/workflows, and developer docs.

### Existing behavior that remains unchanged

Published paths, data policy, client facade methods, and fail-closed releases
remain until their explicit deprecation terms end.

### Compatibility and regression risks

Removing a guardrail too soon recreates silent drift. Generated docs can lose
curated prose. Changing release/docs ordering can reintroduce the race that the
auto-heal currently absorbs.

### Prerequisite decisions versus mechanical work

- Decision: generated-file ownership, committed/public outputs, release
  transaction ownership, and the objective removal gate for each legacy reader
  or guard.
- Mechanical work: retire each legacy reader/guard only after an equivalent
  generated invariant exists; simplify CI and delete dead tests/code.

### Objective completion criteria

- Traceability tests show every projected dataset fact has one authored source,
  while contract schema fields resolve to their separately authored contract.
- Default build paths no longer import legacy hand-authored dataset maps.
- No CI job repairs documentation by committing to main.
- Code version, generated docs, manifest, and static artifacts are produced in
  one verified release transaction.
- Full suite, every verify profile, packaging/Pages smoke tests, rollback, and
  reproducibility exercises pass.

## Changes that must not be implemented independently

| Change | Why it must wait |
| --- | --- |
| Generic DAG/workflow engine | Before a canonical registry it duplicates the existing manual maps in a second system. |
| Registry-generated enum | It needs an explicit stable-public/candidate policy first. |
| Direct Makefile/CI switch to BaseExtractor.run | The generic path does not yet preserve production metadata and fallback behavior. |
| Replacement of all Python validators with spec rules | It conflicts with the accepted semantic-validation boundary. |
| Immutable release directories alone | A release directory without manifest and dual-read compatibility changes storage without a safe contract. |
| Raw object storage after release promotion | Durable snapshot resolution must be proven before a release is promoted as immutable/reproducible. |
| Raw object storage without release eligibility | Without a manifest-eligibility rule and later references it is a second archive, not reproducibility. |
| Cache/client redesign | It must follow stable release identity and atomic publishing. |
| CI auto-heal removal | Its replacement is deterministic docs/release ownership in Phase 11. |
| Legacy config/guardrail deletion after the pilot | Non-pilot datasets still depend on them until full migration is proven. |

## Recommended implementation order

1. Phase 0: accept architectural decisions and compatibility envelope.
2. Phase 1: characterize the build and artifact behavior.
3. Phase 2: add one compatibility-backed DatasetSpec pilot.
4. Phase 3: migrate definitions in risk-ordered dataset batches.
5. Phase 4: standardize extraction results behind existing scripts.
6. Phase 5: make the registry-driven graph default after equivalence evidence.
7. Phase 6: normalize/project the Phase 4 provenance/time model and compile structural rules.
8. Phase 7: establish durable content-addressed snapshots before release promotion.
9. Phase 8: create shadow immutable releases bound to durable snapshots.
10. Phase 9: atomically publish immutable releases with a latest compatibility view.
11. Phase 10: split the public client and operational reporting behind a facade.
12. Phase 11: retire duplicate sources and CI auto-healing.

This sequence minimizes rework: it establishes the data model before changing
orchestration; proves legacy behavior before refactoring it; proves durable
source provenance before treating a release as immutable; and keeps each
replacement in adapter/shadow mode until objective behavioral equivalence gates
are demonstrated.
