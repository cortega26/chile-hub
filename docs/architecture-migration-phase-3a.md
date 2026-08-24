# Architecture migration — Phase 3A cohort record

**Status:** executed — Phase 3A direct stable cohort (9 datasets + pilot), compatibility
backed by `DatasetSpec`, per the frozen [migration roadmap](architecture-migration-roadmap.md)
and ratified decisions [ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** direct stable cohort only. No Phase 3B/3C/3D, no DAG, no extractor changes.

## Eligible cohort (Phase 3A)

Stable, public, direct, single-source datasets with dedicated extractor, no alias,
no derived, no shared-extractor fan-out, no monthly/ad-hoc special lane, and no
multi-source recovery chain. Pilot `partidos_politicos` (Phase 2) is member 1.

| Dataset | Validator | Extractor |
|---|---|---|
| `censo_comunal` | `validate_censo_comunal` | `censo_extractor.py` |
| `censo_hogares_viviendas` | `validate_censo_hogares_viviendas` | `censo_hogares_viviendas_extractor.py` |
| `distritos_electorales` | `validate_distritos_electorales` | `electoral_extractor.py` |
| `empresas` | `validate_empresas` | `res_extractor.py` |
| `establecimientos_educacionales` | `validate_establecimientos_educacionales` | `mineduc_establecimientos_extractor.py` |
| `establecimientos_salud` | `validate_establecimientos_salud` | `salud_extractor.py` |
| `indicadores_urbanos_siedu` | `validate_indicadores_urbanos_siedu` | `siedu_extractor.py` |
| `pobreza_comunal` | `validate_pobreza_comunal` | `pobreza_extractor.py` |
| `resultados_educacionales` | `validate_resultados_educacionales` | `mineduc_resultados_extractor.py` |
| `partidos_politicos` (pilot) | `validate_partidos_politicos` | `partidos_politicos_extractor.py` |

Excluded from 3A (deferred):
- `indicadores` — multi-source recovery (mindicador + INE IPC override → backfill) remains on legacy adapters per Phase 3 guard; first permitted in 3D.
- Shared extractor: `regiones`, `provincias`, `comunas` (+ alias `comunas_enriquecidas`) → 3B.
- Derived `perfil_territorial_comunal` → 3C; alias `comunas_enriquecidas` → 3C.
- Multi-extractor `finanzas_municipales` → 3B; monthly/ad-hoc candidate `consumo_electrico_comunal`, `delincuencia_comunal`, `geometria_comunal`, `autoridades_locales` and scrapling `autoridades_electas` → 3D.

## What was added

| Component | Path | Purpose |
|---|---|---|
| 9 new specs | `data/dataset_specs/{dataset}.json` | Versioned `spec_version:1.0` operational declarations |
| Catalog alignment | `data/dataset_catalog_config.json` | Added explicit `expected_record_count:null` for 5 datasets where contract `null` was missing (single-authority fix) |
| Model extension | `src/registry/dataset_spec.py` | `expected_record_count` now includes `null` verbatim; added `catalog_notes` (`_notes`) and `source_notes` projections |
| Tests | `tests/test_phase2_datasetspec.py` | Now 24 tests: per-dataset catalog/registry equivalence for all 10 specs, contract reference, overlay identity, public inventory, fail-closed, spec-backed build |

Shadow wiring unchanged: `src/builders/_shared.py` and `src/builders/reports.py` overlay all specs present in `data/dataset_specs/`; legacy remains authoritative for every non-migrated dataset.

## Equivalence proof

- `to_catalog_entry()` projects `expected_record_count` mechanically from contract (including `null`); 10/10 specs' catalog projections equal legacy entries (after catalog null fix).
- `to_source_registry_entry()` includes `source_notes` where present; 10/10 registry projections equal legacy.
- `catalog_config_with_spec_overlay` and `source_registry_with_spec_overlay` are semantically identical to legacy payloads — no public artifact can observe a difference.
- `tests/test_phase2_datasetspec.py` now asserts per-dataset equivalence via `iter_specs()`, public inventory for all, and overlay identity for the full catalog/registry.

## What did not change

Public paths, schemas, IDs, aliases, CLI, tracks, lanes, and runtime client behavior unchanged. No DAG, no extractor invocation, no cache/release, no workflow changes.

## Validation for this record

- `pytest tests/test_phase2_datasetspec.py` — 24 passed (10 specs equivalence included)
- `pytest tests/test_phase1_characterization.py` — 11 passed
- `make build` / `make verify` — pass with 10-spec overlay active
- `check_companion_paths.py registry`, `check_validation_registration.py`, `check_agents_sync.py`, `sync_docs.py --check`, `check_landing_sync.py` — pass
- `make lint` / `make format-check` — pass
