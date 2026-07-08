# chile-hub overview

- `generated_at_utc`: `2026-07-08T22:02:42.124535+00:00`
- `overall_status`: `warn`
- `dataset_count`: `19`
- `live_count`: `16`
- `fallback_count`: `3`
- `stale_count`: `0`
- `drifted_count`: `8`
- `degraded_count`: `0`
- `partial_coverage_count`: `2`
- `warning_count`: `11`
- `shared_artifact_count`: `24`
- `package_count`: `1`
- `top_issue`: `empresas` (freshness=fresh, drift=drifted, warnings=3)
- `top_issue_reason`: found 1 RUTs with invalid format
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: empresas: found 1 RUTs with invalid format [source_detail=datos_gob_cl_ckan_api; warnings=3; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `autoridades_electas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `censo_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `censo_hogares_viviendas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas_enriquecidas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `consumo_electrico_comunal` | `fallback` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `distritos_electorales` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `empresas` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `establecimientos_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `establecimientos_salud` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `finanzas_municipales` | `monthly` | `ok` | `fresh` | `partial` | `drifted` |
| `indicadores` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `indicadores_urbanos_siedu` | `live` | `ok` | `fresh` | `partial` | `drifted` |
| `partidos_politicos` | `live` | `ok` | `fresh` | `full` | `drifted` |
| `perfil_territorial_comunal` | `fallback` | `ok` | `fresh` | `full` | `drifted` |
| `pobreza_comunal` | `fallback` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `resultados_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `29300576`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, dataset_changelog_json, dataset_quality_json, dataset_quality_markdown, dataset_status_json, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, source_readiness_json, source_readiness_markdown, status_json, status_markdown`
