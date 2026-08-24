# Architecture migration — Phase 3D cohort record

**Status:** executed — Phase 3D exceptional lifecycle cohort (7 datasets), compatibility
backed by `DatasetSpec`, per the frozen [migration roadmap](architecture-migration-roadmap.md)
and ratified decisions [ADR-018](adr/ADR-018-datasetspec-boundary-and-contract-authority.md) /
[ADR-019](adr/ADR-019-equivalence-gates-and-durable-release-eligibility.md).
**Scope:** candidate, deprecated, monthly/ad-hoc, scraper, multi-source. Completes the
full 22-spec migration (pilot `3A` `3B` `3C` `3D`).

## Cohort (Phase 3D)

Fragile or intentionally non-default behavior, isolated so it cannot destabilize
the public stable path. First batch permitted to represent multi-source recovery
and monthly/ad-hoc lanes in `DatasetSpec`.

| Dataset | Track | Lane | Extractor | Validator | Notes |
|---|---|---|---|---|---|
| `consumo_electrico_comunal` | `candidate` `deprecated` | `bajo_demanda` | `consumo_electrico_extractor.py` | `validate_consumo_electrico_comunal` | `FALLBACK_ROWS` only, never public |
| `delincuencia_comunal` | `candidate` | `monthly` | `cead_delincuencia_live_extractor.py` | — (candidate, no main validation) | No public outputs (`outputs:{}`) |
| `geometria_comunal` | `candidate` | `bajo_demanda` | `geometria_comunal_extractor.py` | `validate_geometria_comunal` | 345/346 (Antártica missing) |
| `autoridades_locales` | `candidate` | `bajo_demanda` | `autoridades_locales_extractor.py` | — | No public outputs |
| `autoridades_electas` | `stable_publishable` | `bajo_demanda` | `autoridades_electas_extractor.py` | `validate_autoridades_electas` | Scrapling (special lane) |
| `indicadores` | `stable_publishable` | `diaria` | `bcentral_extractor.py` | `validate_indicadores` | Multi-source `mindicador` + `ine_ipc` override + backfill (preserved via legacy adapters through `3A–3C`, now represented) |
| `finanzas_municipales` | `stable_publishable` | `mensual` | `sinim_finanzas_extractor.py` + `sinim_finanzas_live_extractor.py` (list) | `validate_finanzas_municipales` | `coverage_note`/`coverage_pct`, `source_mode:mensual`, `degradation_reason`, `legal_note` |

Total specs after 3D: 22/22 (complete).

## What was added

| Component | Path | Purpose |
|---|---|---|
| 7 specs | `data/dataset_specs/{consumo,delincuencia,geometria,autoridades_locales,autoridades_electas,indicadores,finanzas_municipales}.json` | Versioned `spec_version:1.0` exceptional |
| Model | `src/registry/dataset_spec.py` | Added `extractor: list` (finanzas), `validator: null` (candidate without main validation), `coverage_note`/`coverage_pct`, `source_mode`/`degradation_reason`/`legal_note`, `outputs:{}` omission for candidate without public outputs, `expected_record_count:null` verbatim from contract |
| Catalog alignment | `data/dataset_catalog_config.json` | Added `documentation` for 2 candidate datasets missing it, fixed `expected_record_count` drift (`indicadores` missing → `null`, `finanzas` `346` → `null` to match contract authority) |

Shadow wiring unchanged: overlays all 22 specs present; no DAG, no extractor
invocation change, no candidate leakage into public bundle.

## Equivalence proof

- `to_catalog_entry()` now handles `extractor:list`, `validator:null`,
  `outputs:{}` omission, `coverage_*`, and `expected_record_count:null` verbatim;
  7/7 new projections equal legacy entries after catalog drift fixes.
- `to_source_registry_entry()` handles `source_mode`, `degradation_reason`,
  `legal_note` and candidate `publish_blocking`/`live_ready`; 7/7 equal legacy.
- Full overlay identity for 22 specs: `catalog_config_with_spec_overlay` and
  `source_registry_with_spec_overlay` remain semantically identical to legacy.
- `tests/test_phase2_datasetspec.py` now asserts per-dataset equivalence for
  all 22.

## What did not change

Public paths, schemas, IDs, aliases, CLI, tracks, lanes, candidate exclusion,
and monthly/ad-hoc workflow ownership unchanged. `indicadores` multi-source
chain and `finanzas` monthly lane remain on legacy extractor adapters through
`3A–3C`; `3D` is the first batch permitted to represent them and proves
`expected_record_count`/`coverage`/`source_mode` equivalence before migration.

## Validation for this record

- `pytest tests/test_phase2_datasetspec.py` — 24 passed (22 specs)
- `make build` / `make verify` — pass with 22-spec overlay
- `check_companion_paths.py registry`, `check_validation_registration.py`,
  `check_agents_sync.py`, `sync_docs.py --check`, `check_landing_sync.py`,
  `make lint`/`make format-check` — pass
