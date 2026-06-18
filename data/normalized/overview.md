# chile-hub overview

- `generated_at_utc`: `2026-06-18T18:20:03.516188+00:00`
- `overall_status`: `warn`
- `dataset_count`: `15`
- `live_count`: `11`
- `fallback_count`: `4`
- `stale_count`: `0`
- `drifted_count`: `6`
- `degraded_count`: `0`
- `partial_coverage_count`: `1`
- `warning_count`: `9`
- `shared_artifact_count`: `23`
- `package_count`: `1`
- `top_issue`: `empresas` (freshness=fresh, drift=drifted, warnings=3)
- `top_issue_reason`: found 1 RUTs with non-standard format (not validated)
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: empresas: found 1 RUTs with non-standard format (not validated) [source_detail=datos_gob_cl_ckan_api; warnings=3; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `censo_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `censo_hogares_viviendas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas_enriquecidas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `distritos_electorales` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `empresas` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `establecimientos_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `establecimientos_salud` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `finanzas_municipales` | `fallback` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `indicadores` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `indicadores_urbanos_siedu` | `fallback` | `ok` | `fresh` | `partial` | `drifted` |
| `perfil_territorial_comunal` | `fallback` | `ok` | `fresh` | `full` | `drifted` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `resultados_educacionales` | `fallback` | `ok` | `fresh` | `not_applicable` | `drifted` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `29151937`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, dataset_changelog_json, dataset_quality_json, dataset_quality_markdown, dataset_status_json, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, source_readiness_json, source_readiness_markdown, status_json, status_markdown`
