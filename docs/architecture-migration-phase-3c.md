# Architecture migration — Phase 3C cohort record

**Status:** executed — Phase 3C alias and derived cohort (2 datasets), compatibility
backed by `DatasetSpec`, per the frozen [migration roadmap](architecture-migration-roadmap.md)
and ratified decisions [ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** aliases and derived only. No Phase 3D.

## Cohort (Phase 3C)

Aliases and datasets with upstream dependencies; requires direct cohort proven
(`3A`/`3B`) for track inheritance and dependency ordering.

| Dataset | Kind | Upstream / Alias | Validator |
|---|---|---|---|
| `comunas_enriquecidas` | `alias` | `alias_for: comunas`, upstream `[comunas, censo_comunal]` (enrichment) | `validate_comunas` (shared) |
| `perfil_territorial_comunal` | `derived` | `dependencies: 9` (`comunas`, `censo_comunal`, `censo_hogares_viviendas`, `establecimientos_salud`, `establecimientos_educacionales`, `distritos_electorales`, `finanzas_municipales`, `resultados_educacionales`, `indicadores_urbanos_siedu`) | `validate_perfil_territorial_comunal` |

Total specs after 3C: 15 (pilot + 9 direct `3A` + 3 shared `3B` + 2 alias/derived `3C`).

## What was added

| Component | Path | Purpose |
|---|---|---|
| 2 specs | `data/dataset_specs/{comunas_enriquecidas,perfil_territorial_comunal}.json` | Versioned `spec_version:1.0` alias/derived |
| Model | `src/registry/dataset_spec.py` | Added `upstream_datasets` projection and `catalog_notes` (`_notes`) handling; `expected_record_count` now includes `null` verbatim |

Shadow wiring unchanged: overlays all specs present; legacy remains authoritative
for non-migrated (candidate/monthly/ad-hoc/scraper/multi-source → 3D).

## Equivalence proof

- `alias` projects `alias_for` and shared physical parquet (`comunas.parquet`)
  but distinct `duckdb_table`/`sqlite_table`; 1/1 alias catalog/registry equal legacy.
- `derived` projects `extractor:null`, 9 upstream dependencies, and
  `publication_track` inheritance; 1/1 derived catalog/registry equal legacy
  (including `source.upstream_datasets`).
- Full overlay identity for 15 specs: `catalog_config_with_spec_overlay` and
  `source_registry_with_spec_overlay` remain semantically identical to legacy.
- `tests/test_phase2_datasetspec.py` now asserts per-dataset equivalence for
  all 15 and overlay identity.

## What did not change

Public paths, schemas, IDs, aliases, CLI, tracks, lanes, and derived-track
inheritance unchanged. `comunas_enriquecidas` still resolves via alias to
canonical physical artifact; `perfil_territorial_comunal` still built from
validated upstream layers.

## Validation for this record

- `pytest tests/test_phase2_datasetspec.py` — 24 passed (15 specs)
- `make build` / `make verify` — pass with 15-spec overlay
- `check_companion_paths.py registry`, `check_validation_registration.py`,
  `check_agents_sync.py`, `sync_docs.py --check`, `check_landing_sync.py`,
  `make lint`/`make format-check` — pass
