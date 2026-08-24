# Architecture migration — Phase 0 decision package

**Date:** 2026-08-23
**Status:** closed — P0-D1 through P0-D4 accepted by Carlos Ortega, repository
maintainer, on 2026-08-23
**Decision owner / acceptance authority:** Carlos Ortega, repository maintainer

## Purpose

This package contains only the decisions that must be accepted before the
DatasetSpec pilot in Phase 2 of
[the frozen migration roadmap](architecture-migration-roadmap.md). It is not a
replacement for an ADR. The accepted decisions are ratified in
[ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) and
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).

Decisions about extractor-result field semantics, durable-storage provider and
policy, release identity/publishing, and public-client decomposition are
intentionally deferred to Phases 4, 7, 8, and 10 respectively. They do not
block a safe registry pilot.

## P0-D1 — Canonical DatasetSpec boundary

**Status:** accepted — 2026-08-23, Carlos Ortega

**Recommended option:** Author one versioned, per-dataset declarative spec and
validate it with a typed `DatasetSpec` model. The spec owns dataset identity,
lifecycle, track, source/reuse/fallback/freshness policy, lane, public
eligibility, contract reference, validator reference, outputs, aliases,
dependencies, and documentation metadata. Source-specific extraction and
semantic-validation implementation remain Python code. Existing catalog, source
registry, and documentation paths may become compatibility projections during
migration, not new competing authored sources. Existing contracts remain
separately authored authoritative artifacts and are referenced by the spec.

**Single-authority invariant:** no dataset fact may be independently authored
in both `DatasetSpec` and a JSON Schema contract. Where a legacy catalog, source
registry, documentation page, public inventory, interoperability metadata, or
compatibility view needs information held by another authority, that
representation is mechanically projected; it is not a second manually
maintained source.

**Acceptance test:** The accepted boundary is sufficient to express the selected
direct, stable pilot without a special field or a second authoritative registry.

**Evidence:**

- [Clean-sheet architecture review](architecture-review-clean-sheet-2026.md)
  identifies duplicated dataset facts as the central maintainability risk.
- `data/dataset_catalog_config.json`, `data/source_registry.json`, contracts,
  documentation, and builder maps currently divide the same ownership facts.
- [ADR-005](adr/ADR-005-contratos-esquema-json-schema.md) requires semantic
  validation to remain outside a purely declarative schema.

## P0-D2 — Contract relationship

**Status:** accepted — 2026-08-23, Carlos Ortega

**Recommended option:** A DatasetSpec references the existing separately
authored, versioned JSON Schema contract by stable path and version. It neither
embeds nor generates the schema. The spec may declare contract-facing metadata
needed for projections, but the contract remains the internal schema authority
unless a later ADR explicitly approves a different boundary.

**Authority boundary:** JSON Schema contracts own fields/columns, types,
required and nullability rules, structural constraints, and schema-level
compatibility requirements. `DatasetSpec` owns identity, kind/lifecycle,
publication track and eligibility, source/reuse/fallback/freshness policy,
extraction lane, contract reference, semantic-validator reference, aliases,
dependencies, generated outputs/artifact declarations, documentation metadata,
and other dataset-level operational policy. This decision does not silently
move schema authority into `DatasetSpec`.

**Acceptance test:** The pilot resolves its unchanged contract path through the
spec and contract validation has identical pass/fail behavior for fixed input.

**Evidence:**

- [ADR-005](adr/ADR-005-contratos-esquema-json-schema.md) establishes JSON
  Schema contracts as the existing internal schema boundary.
- The roadmap’s compatibility envelope preserves schemas and contract paths.
- Embedding contracts immediately would duplicate a second large declarative
  model before the registry adapter has been proven.

## P0-D3 — Lifecycle and dependency semantics

**Status:** accepted — 2026-08-23, Carlos Ortega

**Recommended option:** Model lifecycle explicitly: `direct`, `alias`, and
`derived` are mutually exclusive dataset kinds; publication track, maturity,
public eligibility, extraction lane, dependencies, and derived-track inheritance
are separate declared fields. An alias does not create a physical dataset;
derived datasets declare upstream IDs; candidate, deprecated, monthly, ad-hoc,
and stub behavior remain policy attributes rather than implicit omissions or
build conditionals.

**Acceptance test:** The pilot is demonstrably `direct`; the model can represent
all existing lifecycle categories without changing their current publication or
schedule behavior. Exceptional categories are exercised later in Phase 3D, not
reimplemented prematurely.

**Evidence:**

- [ADR-004](adr/ADR-004-carriles-de-publicacion.md) makes publication tracks a
  product policy rather than a packaging detail.
- [Extraction lanes](extraction-lanes.md) distinguishes daily, monthly, ad-hoc,
  and stub execution ownership.
- The roadmap’s Phase 3 batch order isolates aliases, derived datasets, and
  exceptional lanes after direct stable definitions are proven.

## P0-D4 — Behavioral equivalence and promotion gates

**Status:** accepted — 2026-08-23, Carlos Ortega

**Recommended option:** A replacement is promoted only by an explicit behavioral
matrix and objective gates: fixed inputs must preserve validation outcomes,
public artifact membership/paths/schemas/checksums except allowlisted volatile
metadata, report and publication eligibility behavior, public API/CLI behavior,
and relevant failure modes. Line coverage is reported as a diagnostic, never as
the substitute or threshold for promotion. Each phase defines any additional
fault or end-to-end gate needed for its own boundary.

**Acceptance test:** Phase 1 can publish a reviewed matrix that classifies each
assertion as a public compatibility guarantee or an implementation detail; Phase
2 can run it for the pilot with no unexplained difference.

**Durable-snapshot release eligibility:** before a shadow release can satisfy
promotion gates to become the production publication model, every
dataset/artifact included in that public release must resolve to the required
durable source-snapshot provenance under the accepted archival policy. A release
must never claim reproducibility if its required source material is not durably
resolvable. A source that legally or technically cannot be archived requires an
explicit, documented exception policy and release-eligibility rule; it cannot
silently weaken this invariant. Provider, retention, legal/access, credential,
and exception mechanics remain deferred to Phase 7.

**Evidence:**

- [ADR-001](adr/ADR-001-pipeline-lineal-determinista.md) makes fail-closed
  validation and publication behavior a compatibility-critical guarantee.
- [ADR-016](adr/ADR-016-backfill-consciente-de-la-edad.md) shows that freshness
  and publication behavior include policy outcomes, not merely executed lines.
- Plan 077’s characterization direction is a useful test harness, but its
  coverage percentage alone cannot establish release equivalence.

## Deliberately deferred decisions

The following have not been accepted or pre-decided by Phase 0 and remain owned
by their roadmap phases:

- final `ExtractionResult` field semantics and extensions — Phase 4;
- durable-storage provider, retention, legal/access and credential policy — Phase 7;
- release ID, manifest, signing, retention, rollback, and publishing mechanics — Phases 8–9;
- client/cache redesign and public-module decomposition — Phase 10.

Phase 0 changed no production code, configuration, workflow, or publication
behavior. Its decision work is complete; Phase 1 may characterize current
behavior and Phase 2 may begin only when separately authorized.
