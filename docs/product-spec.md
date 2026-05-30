# chile-hub product spec

## One-liner

`chile-hub` is a curated, versioned, and easy-to-consume access layer for Chilean data from open or legally reusable sources.

## Principle

The product's value is not "having all Chilean data."

The value is reducing the time, ambiguity, and failure rate involved in finding, cleaning, understanding, joining, versioning, and consuming reliable Chilean datasets.

## Viability

The project is viable if it stays narrow in operating model and broad only in long-term vision.

It is not viable as:

- a promise to cover every relevant dataset in Chile
- a scraping-heavy portal with unclear licenses
- a dashboard-first product with weak data foundations

It is viable as:

- a repository of high-value data layers
- a repeatable ingestion and normalization framework
- a trust-oriented catalog with provenance, caveats, and examples

## Core trade-offs

- Breadth vs maintainability: more topics increase appeal but also multiply brittle pipelines.
- Freshness vs reliability: daily automation is useful only when the source is stable enough to justify it.
- Convenience vs legal clarity: republishing improves usability but should never outrun source permissions.
- API surface vs operating cost: versioned files are cheaper to maintain than an always-on API.
- Uniformity vs truthfulness: not every source can meet the same quality bar, so confidence levels must be explicit.

## Automation policy

Not every dataset belongs in the same automation tier.

### Tier A: fully automatable

Use for:

- stable APIs
- machine-readable CSV/JSON/Parquet
- predictable schemas
- clear legal reuse

Expected behavior:

- scheduled refresh
- schema checks
- deterministic outputs

### Tier B: semi-automatable

Use for:

- Excel files with periodic manual drift
- stable files with occasional schema changes
- datasets that need normalization rules maintained by hand

Expected behavior:

- mostly automated ingestion
- manual review on schema drift
- stronger tests and fallback behavior

### Tier C: research or manual

Use for:

- PDFs
- brittle HTML scraping
- unclear rights
- unstable publication patterns

Expected behavior:

- do not include in MVP
- document as future research

## Dataset admission criteria

A dataset should enter `chile-hub` only if it scores well on most of the following:

1. Solves a recurring user pain.
2. Has strong cross-dataset join value.
3. Comes from a stable and inspectable source.
4. Has clear or manageable reuse conditions.
5. Can be refreshed at reasonable cost.
6. Produces outputs that are useful without custom tooling.
7. Helps prove the product's differentiation.

## Initial user priority

### Primary

- developers building Chilean software
- analysts or BI teams who repeatedly prepare Chilean reference data

### Secondary

- journalists, researchers, and civic-tech teams

Non-technical spreadsheet users matter, but they should be served through exports and templates rather than being the primary design center of the MVP.

## MVP recommendation

The MVP should prove that `chile-hub` can turn messy Chilean public data into dependable building blocks.

### Included in MVP

- territorial base layer: region, province, comuna, standardized codes, search-safe names
- daily economic indicators: UF, USD, EUR, UTM, and similar high-reuse indicators
- one additional transversal layer chosen by admission criteria, not intuition alone

Good candidates for the third layer:

- establishments or institutional directories with strong join potential
- election results with stable official identifiers
- municipal finance or budget summaries if access and licensing are clean

### Explicitly excluded from MVP

- universal "all Chilean data" coverage
- complex dashboards
- a public API that must stay online 24/7
- fragile scraping as the product's core promise
- sources with unclear redistribution conditions

## Consumption modes

### Must-have

- versioned flat files: CSV, JSON, Parquet
- local analytical database: DuckDB
- SQLite export
- documentation with copy-paste examples

### Nice-to-have after MVP

- Python helper package
- richer search UI
- hosted file index or release catalog

### Usually overkill for MVP

- REST API
- auth
- interactive dashboard suite

## Trust model

Every data layer should publish:

- source
- access method
- update frequency
- legal notes
- schema
- normalization rules
- known caveats
- freshness timestamp
- confidence tier

## Definition of success

The MVP succeeds if a technical user can:

1. discover a dataset quickly
2. understand whether it is trustworthy
3. load it in one line
4. join it with their own data without cleanup work

## Immediate next step

Build the repo around a visible catalog of data layers and a strict admission rubric before expanding source coverage.
