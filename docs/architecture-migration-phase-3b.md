# Architecture migration — Phase 3B cohort record

**Status:** executed — Phase 3B shared-source cohort (3 datasets), compatibility
backed by `DatasetSpec`, per the frozen [migration roadmap](architecture-migration-roadmap.md)
and ratified decisions [ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** shared-extractor direct stable cohort only. No Phase 3C/3D, no DAG.

## Cohort (Phase 3B)

Stable, public, direct datasets that share the `subdere_extractor.py` fan-out
(BCN ArcGIS DPA). Establishes one source policy and one shared-extractor
mapping without mixing in derived or candidate exceptions.

| Dataset | Validator | Extractor | Expected |
|---|---|---|---|
| `regiones` | `validate_regiones` | `subdere_extractor.py` | 16 |
| `provincias` | `validate_provincias` | `subdere_extractor.py` | 56 |
| `comunas` | `validate_comunas` | `subdere_extractor.py` | 346 |

Excluded from 3B: alias `comunas_enriquecidas` → 3C; derived `perfil_territorial_comunal` → 3C;
`finanzas_municipales` (dual extractor `sinim_*`, monthly lane) and conventional
multi-source `indicadores` remain legacy through 3B — first permitted in 3D per
multi-source guard.

Total specs after 3B: 13 (pilot + 9 direct stable from 3A + 3 shared from 3B).

## What was added

| Component | Path | Purpose |
|---|---|---|
| 3 specs | `data/dataset_specs/{regiones,provincias,comunas}.json` | Versioned `spec_version:1.0` direct stable |
| Model | `src/registry/dataset_spec.py` | No new fields; shared extractor handled per-dataset (legacy duplication preserved, proven equivalent) |

Shadow wiring unchanged: `src/builders/_shared.py` and `src/builders/reports.py`
overlay all specs present; legacy remains authoritative for non-migrated.

## Equivalence proof

- `to_catalog_entry()` projects `expected_record_count` from contract (16/56/346);
  3/3 projections equal legacy entries.
- `to_source_registry_entry()` 3/3 equal legacy (distinct `source_id` per dataset,
  same `official_url`).
- `catalog_config_with_spec_overlay` and `source_registry_with_spec_overlay`
  remain semantically identical to legacy payloads for the full 13-spec cohort.
- `tests/test_phase2_datasetspec.py` now asserts per-dataset equivalence for
  all 13 specs, overlay identity, and spec-backed build.

## What did not change

Public paths, schemas, IDs, aliases, CLI, tracks, lanes, and runtime client
unchanged. `derive_geography_layers` still derives `regiones`/`provincias`
from `df_comunas` at build time; catalog `extractor` duplication is preserved
and proven equivalent, not refactored to a DAG.

## Validation for this record

- `pytest tests/test_phase2_datasetspec.py` — 24 passed (13 specs)
- `make build` / `make verify` — pass with 13-spec overlay
- `check_companion_paths.py registry`, `check_validation_registration.py`,
  `check_agents_sync.py`, `sync_docs.py --check`, `check_landing_sync.py`,
  `make lint`/`make format-check` — pass
