# Clean-sheet architecture review — chile-hub

## Purpose

This is a repository-grounded, opinionated architecture review. It asks how
`chile-hub` should be built today if starting from a blank repository while
preserving the current product goals, target users, dataset scope, and general
functionality.

The conclusion is not that the existing project is poorly designed. Its product
instincts are substantially better than its implementation shape. The project
should preserve its curated, reproducible, source-aware public-data philosophy,
while redesigning the internals around one declarative dataset model and one
execution model.

## What to keep essentially unchanged

- The narrow, curated scope rather than attempting to cover all Chilean open
  data.
- CUT codes as canonical string keys, loud data-quality failures, and immutable
  raw snapshots.
- Parquet as the primary distribution format; DuckDB as a valuable convenience
  artifact.
- Dataset contracts, provenance, freshness, licensing, and publication
  eligibility as first-class concepts.
- Candidate versus publishable tracks. This prevents a tempting-but-fragile
  dataset from silently becoming a public promise.
- A Python client that caches a release bundle locally and verifies checksums.
- Strong automated checks around generated artifacts and publication.

These are the hard lessons worth preserving.

## Clean-sheet design

```text
chile-hub/
  packages/
    client/                 # installable consumer library + CLI
    pipeline/               # extraction, normalization, validation, publishing
  datasets/
    <dataset-id>/
      spec.yaml             # one authoritative DatasetSpec
      contract.json
      transform.py          # only when declarative transforms are insufficient
      fixtures/
  platform/
    catalog.py              # typed DatasetSpec and registry
    storage.py              # content-addressed snapshots + release manifests
    validation.py           # reusable rule engine + domain rules
  releases/
    <release-id>/manifest.json
```

A `DatasetSpec` would be the authoritative declaration of:

- identity, lifecycle, owner, license, freshness, and source policy;
- source adapter and dependency graph;
- primary and foreign keys, fields, schema-evolution policy, and quality
  thresholds;
- generated artifacts and public availability;
- documentation metadata and usage examples.

The build would execute a DAG:

```text
source snapshot → normalized dataset → validations → derived datasets
                → immutable release manifest → public artifacts
```

Each run would be identified by immutable snapshot hashes and publish one
atomic release manifest. “Current release” would be a pointer, never a
directory gradually overwritten during a build.

## Significant changes and trade-offs

| Proposal | Why | Trade-off | Classification |
| --- | --- | --- | --- |
| Make one typed `DatasetSpec` the source of truth; generate catalog, contracts, docs, registry views, and enum from it. | Dataset facts are currently represented across the catalog, source registry, JSON schemas, `Dataset`, builder maps, docs, and CI guards. The guards catch drift, but do not eliminate its cause. | A richer schema and migration work; not every source-specific detail should become configuration. | **A. Worth changing now** |
| Replace the hand-wired central build registry with a declarative DAG/registry. | `src/build_dev_db.py` manually names inputs, optional datasets, derived datasets, validations, and output paths. `metadata.py` repeats that dataset-by-dataset. Adding a dataset is consequently cross-cutting by construction. | A generic framework can obscure unusual transforms. Preserve escape hatches for custom transforms. | **A. Worth changing now** |
| Make `BaseExtractor` the real execution interface, or remove it. | The generic `run()` is explicitly not used by the Makefile; the Makefile invokes bespoke `process_*` scripts. The abstraction and production path diverge. | Standardizing extractors needs incremental adapter work. | **A. Worth changing now** |
| Move raw snapshots to content-addressed object storage, or to a local cache plus durable archive, keyed by SHA-256 and referenced in release manifests. | Raw data is correctly append-only, but local `data/raw/` is large and mostly ignored by Git; CI also relies on cache restoration. That is not a durable shared reproducibility boundary. | Storage operations, retention policy, and possibly cost. Keep small legal fixtures in Git. | **A. Worth changing now** |
| Publish atomically to a versioned release directory/manifest. | Individual writes may be atomic, but the normalized directory is a mutable working location with many artifacts. A failed mid-build can leave a mixed release even if every individual write is safe. | Extra disk during builds and release-retention management. | **A. Worth changing now** |
| Separate the small consumer API from pipeline observability and reporting APIs. | `ChileHub` contains loading/querying, cache behavior, validation, reporting, tables, health, drift, provenance, packaging, and source checks. It is an “everything hub.” | More modules and imports; existing convenience methods need deprecation aliases. | **A. Worth changing now** |
| Make version selection explicit in the client: `release=`, `offline=True`, `refresh()`. | Local caching and checksum verification are good. Implicit update checks during normal use introduce network, latency, and reproducibility surprises. | Less “always current” convenience by default. | **B. Worth considering as the project grows** |
| Make Parquet plus a manifest the universal distribution baseline. Keep DuckDB as an optional convenience; generate Excel and JSON selectively or on demand. | Output combinations vary materially among datasets. Maintaining SQLite, Excel, JSON, DuckDB, ZIP, manifests, reports, and landing data multiplies failure surface. | Excel and JSON are real user conveniences; do not remove them where they serve a known audience. | **B. Worth considering as the project grows** |
| Replace `refreshed_at_utc` as the principal time concept with `source_published_at`, `retrieved_at`, `observed_period`, and `snapshot_hash`. | Freshness of retrieval, currency of source content, and the time data describes are different. This matters for historical, monthly, and derived datasets. | More metadata and more careful extractor implementations. | **A. Worth changing now** |
| Generate public `Dataset` values from the registry, or make it deliberately a stable-public-only enum. | The enum does not cover every catalog/contract dataset. That may be intentional, but it is encoded through manual omission rather than an explicit API policy. | Generated enums can make versioning more visible; a stable-only API needs clear documentation. | **A. Worth changing now** |
| Keep contract tests, but shift some large internal tests to behavior, golden, and replay tests. | The project has extensive test coverage effort, but parts of it risk coupling to orchestration internals rather than stable observable behavior. | Refactoring tests can reduce diagnostic specificity if overdone. | **B. Worth considering as the project grows** |
| Stop CI from auto-committing documentation fixes to `main`; make release/docs generation one atomic, reviewable change. | The auto-heal fixes a real race, but makes CI a writer to `main` and treats drift as operationally normal. | A release workflow needs clearer sequencing and may need a follow-up PR. | **A. Worth changing now** |
| Remove compatibility shims after a published deprecation window. | Compatibility modules preserve old paths and add namespace/tooling exceptions. | Breaking imports for old consumers. | **C. Better in a greenfield implementation, but not worth migrating immediately** |
| Use a workflow engine such as Dagster or Prefect. | The project has enough cadence and dependency complexity for this to be plausible. | Considerable operational weight; a compact internal DAG runner may be better. | **D. Merely an alternative design, with no clear advantage** |

## Blind spots and accumulated complexity

The project compensates for duplicated truth with an impressive number of
anti-drift scripts. This is useful protection, but also a signal. If adding a
dataset requires catalog edits, source-registry edits, contracts, staging schema,
validation registration, builder maps, artifact maps, docs, tests, Makefile,
workflow, and landing synchronization, then the architecture is asking humans to
maintain a distributed schema.

The central build is the clearest example. The builder modules are a reasonable
extraction from a monolith, but orchestration remains a manually maintained set
of parallel dictionaries and branches. “Optional because new” is especially
revealing: a dataset’s lifecycle is encoded partly as missing files and partly
in conditionals, rather than as an explicit state in the registry.

`BaseExtractor` is a missing-or-unnecessary abstraction in its current form. It
promises one lifecycle, but production uses another. Either make every extractor
return a common `ExtractionResult`—snapshot, normalized table, metadata, and
quality observations—or remove the base class and acknowledge independent
scripts. The former is preferable.

The public API has accumulated operator-facing reporting convenience methods
into the same object consumers use to load data. Methods such as
`summary_table`, `overview_table`, `inventory_table`, `runtime_status_table`,
and `redistribution_table` are CLI presentation concerns, not core client
responsibilities. Keep structured inspection data available, but move rendering
and operational reporting outside `ChileHub`.

The formats strategy is also evolution-driven. DuckDB, SQLite, Excel, Parquet,
and JSON were sensible experiments while discovering users, but each
materialization creates versioning, schema, verification, and support
obligations. Parquet plus a signed release manifest should be the invariant.
Everything else should justify itself with actual consumer demand.

The extractor for electoral mapping highlights a provenance concern: it
constructs assignments from application-maintained lists and labels the output
`live`. That may be reliable and carefully curated, but “live” should mean that
this run retrieved a source artifact, not merely that the result is current. A
curated reference mapping should have its own versioned source artifact and
review policy.

## Decisions that made sense historically

- Manual builders and a linear Makefile were the right way to ship a working
  MVP quickly.
- JSON, SQLite, DuckDB, Excel, and a ZIP were sensible experiments for learning
  which consumption modes users preferred.
- Compatibility shims were reasonable while moving from scripts to an
  installable package.
- Extensive CI checks were appropriate after real regressions in fragile public
  sources.
- Caching staging data in CI was practical when upstream sources were
  unreliable.

None of these were bad decisions. The problem is allowing them to become
permanent architecture after their original uncertainty has been resolved.

## What to remove

Remove structural forms, not necessarily their capabilities:

- Hand-maintained per-dataset wiring in load, validation, metadata, and artifact
  construction.
- The split `process_*` / `BaseExtractor.run()` lifecycle.
- Presentation/table-formatting methods from the public library object.
- Generated-data drift checks whose only job is reconciling multiple
  hand-authored sources of truth.
- Default production maintenance of every output format for every dataset.
- CI auto-commits as the normal way to recover documentation consistency.

## If everything were known before the first line of code

Start with a typed, versioned dataset registry; immutable source snapshots; an
explicit dependency graph; and atomic release manifests. Ship Parquet, a
release manifest, and a small Python client first. Add DuckDB, Excel, JSON
endpoints, health reports, candidate tracks, spatial resolution, and the landing
page only as independently justified layers.

Most importantly, distinguish three concepts from day one:

1. **A dataset’s logical contract** — schema, keys, semantics, and quality rules.
2. **A source snapshot** — what was received, when, from where, and with what hash.
3. **A release** — the exact validated set of dataset versions made public together.

The existing project already believes in all three. Its next architectural step
is to make that belief the organizing structure of the code, rather than
enforcing it through increasingly careful coordination across many files.
