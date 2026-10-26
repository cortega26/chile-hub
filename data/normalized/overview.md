# chile-hub overview

- `generated_at_utc`: `2026-10-26T00:25:12.586077+00:00`
- `overall_status`: `warn`
- `dataset_count`: `23`
- `live_count`: `22`
- `fallback_count`: `0`
- `stale_count`: `1`
- `drifted_count`: `2`
- `degraded_count`: `0`
- `partial_coverage_count`: `1`
- `warning_count`: `8`
- `shared_artifact_count`: `25`
- `package_count`: `1`
- `top_issue`: `calidad_aire` (freshness=stale, drift=drifted, warnings=2)
- `top_issue_reason`: cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: calidad_aire: cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación [source_detail=Promedios diarios por estación y contaminante (MP2.5, MP10, SO2, NO2, CO, O3) desde el JSON del SINCA. Cobertura parcial por diseño (~65 comunas con estación). Serie incremental desde la primera cosecha.; warnings=2; freshness=stale; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `autoridades_electas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `calidad_aire` | `live` | `ok` | `stale` | `not_applicable` | `drifted` |
| `censo_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `censo_hogares_viviendas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas_enriquecidas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `consumo_electrico_comunal` | `fallback` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `distritos_electorales` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `empresas` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `establecimientos_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `establecimientos_salud` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `estadisticas_vitales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `finanzas_municipales` | `monthly` | `ok` | `fresh` | `full` | `healthy` |
| `indicadores` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `indicadores_urbanos_siedu` | `live` | `ok` | `fresh` | `partial` | `healthy` |
| `partidos_politicos` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `perfil_territorial_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `permisos_edificacion` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `pobreza_comunal` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `precipitaciones_dgac` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `resultados_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `31801139`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, dataset_changelog_json, dataset_quality_json, dataset_quality_markdown, dataset_status_json, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, source_readiness_json, source_readiness_markdown, status_json, status_markdown`
