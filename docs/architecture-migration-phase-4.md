# Architecture migration — Phase 4 record

**Status:** executed — Phase 4 extractor standardization, per the frozen
[migration roadmap](architecture-migration-roadmap.md) and ratified decisions
[ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** standardize `ExtractionResult` while retaining `process_*` adapters.
No DAG, no workflow changes.

## Final ExtractionResult model

```python
@dataclass(frozen=True)
class ExtractionResult:
    # Identity
    dataset: str
    # Normalized data
    dataframe: pl.DataFrame
    # Source-snapshot provenance
    raw_snapshot_path: Path | None
    # SHA-256 of the raw snapshot, when one exists
    snapshot_hash: str | None
    # Immutable relative reference
    snapshot_reference: str | None
    # Mode and times
    source_mode: str  # live | fallback | monthly
    retrieved_at: datetime  # UTC, when fetched
    # When the source says it was published
    source_published_at: datetime | None
    # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} or None
    observed_period: dict | None
    # Policy and detail
    reuse_policy: dict
    source_detail: str | None
    notes: tuple[str, ...]
    # Legacy staging compatibility
    record_count: int | None
    fields: tuple[str, ...] | None
```

- **Mandatory** in every result: `dataset`, `dataframe`, `source_mode`,
  `retrieved_at`, `reuse_policy` (plus `snapshot_hash`/`reference` when a
  snapshot exists). Optional fields are `None` when the source does not
  provide them, never inferred from `retrieved_at`.

- **Source snapshot identity:** `snapshot_hash` is streaming SHA-256 of the
  raw file (`data/raw/...`), `snapshot_reference` is the immutable relative
  path. For multi-file sources (poverty two XLSX, indicadores many JSON +
  INE override), the hash is of the normalized DataFrame as proxy, or of the
  latest snapshot file.

## Demonstrated extractors

| Type | Dataset | Extractor | `extract_*` | `observed_period` | `source_published_at` |
|---|---|---|---|---|---|
| Ordinary | `censo_comunal` | `censo_extractor.py` | `extract_censo` | `2024-01-01` → `2024-12-31` | `None` |
| Fallback | `pobreza_comunal` | `pobreza_extractor.py` | `extract_pobreza_comunal` | `2022-01-01` → `2022-12-31` | `None` |
| Multi-source/scraper | `indicadores` | `bcentral_extractor.py` | `extract_indicadores` | `2010-01-01` → today (from DataFrame) | `None` |

Each has a `process_*` adapter that calls `extract_*` and writes staging via
`result.to_staging_metadata()` plus legacy-specific fields, preserving
byte-for-byte legacy behavior for `Makefile` and workflows.

## What did not change

- `process_*` function names, CLI entry points, staging output paths
  (`data/staging/*.csv`, `data/raw/*`), fallback behavior, raw snapshot
  append-only, schedule ownership, isolated `scrapling` env, and the
  unscheduled `sinim_finanzas_extractor.py` stub.
- No production caller uses `BaseExtractor.run` directly; `extract_*` is for
  programmatic use and tests.

## Validation for this record

- `pytest tests/test_phase4_extraction.py` — 11 passed (mandatory/optional
  fields, hash, observed_period, adapter equivalence)
- `pytest tests/test_extractors.py` — 149 passed (including `process_*`
  adapters)
- `make build` / `make verify` — pass with `22`-spec overlay and new
  extraction results
- `make lint` / `make format-check` / `check_agents_sync` / `sync_docs --check`
  / `check_landing_sync` — pass
