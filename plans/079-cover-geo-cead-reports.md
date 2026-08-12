# Plan 079: Cobertura de writers y extractores sin test (geo, CEAD, reports)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/builders/geo.py src/builders/reports.py src/extractors/cead_delincuencia_live_extractor.py tests/test_extractors.py tests/test_pipeline_logic.py tests/geo_fixtures.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none (077 cubre build_dev_db; este cubre los módulos)
- **Category**: tests
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

Tres módulos críticos sin cobertura:
1. **`src/builders/geo.py` 0%** — el writer del GeoParquet (ADR-012) no tiene
   ningún test; un bug en `simplify(preserve_topology=True)` o en el footer
   geo pasaría directo al workflow manual.
2. **`src/extractors/cead_delincuencia_live_extractor.py` 0%** — el único
   extractor sin tests; si el portal CEAD cambia el HTML/shape, falla
   silenciosamente y se descubre solo en la revisión mensual manual.
3. **`src/builders/reports.py` 35%** — los reportes que alimentan
   README/landing/health (badges, `hub_health.json`) sin cubrir; esta zona ya
   rompió publish dos veces (drift real).

## Current state

- `src/builders/geo.py` — `write_geometria_comunal_parquet` (WKB, schema
  1.0.0); `tests/geo_fixtures.py:63-67` ya tiene `write_synthetic_parquet`
  con el mismo encoding.
- `cead_delincuencia_live_extractor.py` — 209 stmts, 0 cubiertos; corre en
  `monthly-scrape.yml:103-130` con "Revisar manualmente" si falla.
- `src/builders/reports.py` — missing 300-345, 532-594, 617-755, 874-888,
  903-1045 (build_hub_health, pipeline_status, freshness, quality).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Cobertura | `./.venv/bin/pytest tests/test_extractors.py tests/test_pipeline_logic.py --cov=src.builders.geo --cov=src.builders.reports --cov=src.extractors.cead_delincuencia_live_extractor --cov-report=term-missing` | ≥60% en los 3 |
| Tests | `./.venv/bin/pytest tests/test_extractors.py tests/test_pipeline_logic.py -q` | all pass |

## Scope

**In scope**: tests (nuevos archivos o extensiones), fixtures sintéticos.
**Out of scope**: el código de los 3 módulos (solo lectura salvo bugs
encontrados por los tests — reportar, no arreglar en este plan).

## Steps

### Step 1: Writer GeoParquet (geo.py)

Test round-trip: `write_geometria_comunal_parquet` con el schema de staging
(WKT) → `gpd.read_parquet` → assert CRS EPSG:4326, columnas esperadas,
`simplify_tolerance=0` preserva todos los polígonos. Reusa
`tests/geo_fixtures.py`.

**Verify**: cobertura de `src.builders.geo.py` ≥ 60%; test pasa.

### Step 2: CEAD

Guarda un snapshot real del portal CEAD como fixture (o construye HTML/JSON
sintético si el portal no es accesible), testea parse + normalización +
metadata. Al menos los helpers puros. Modelar sobre `IneIpcExtractorTests`
(`test_extractors.py:424-499`).

**Verify**: cobertura de CEAD ≥ 60%; tests pasan.

### Step 3: reports.py

Con el staging sintético del Plan 077 (o un builder mínimo), ejercita
`build_hub_health`/`build_pipeline_status`/`build_freshness` y asserta
invariantes (dataset_count, drifted/warn/retired, severidad) — no texto
exacto. Modelar sobre `HubHealthHistoryTests` (`test_pipeline_logic.py:2537`).

**Verify**: cobertura de `src.builders.reports.py` ≥ 60%; tests pasan.

## Done criteria

- [ ] geo.py ≥ 60% de cobertura
- [ ] CEAD ≥ 60% de cobertura
- [ ] reports.py ≥ 60% de cobertura
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El fixture CEAD real no puede obtenerse (portal caído) — usar HTML
  sintético fiel al shape documentado y anotarlo.
- Un test encuentra un bug real en el writer/reportes — reportar con el
  repro, no arreglar en este plan (plan separado).

## Maintenance notes

- Si CEAD cambia el layout, el test del fixture es la primera alerta.
- reports.py quedará cubierto con el staging sintético compartido del 077 —
  mantener ese helper en un archivo común.
