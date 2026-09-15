# chile-hub overview

- `generated_at_utc`: `2026-09-15T17:36:48.057196+00:00`
- `overall_status`: `warn`
- `dataset_count`: `22`
- `live_count`: `21`
- `fallback_count`: `0`
- `stale_count`: `0`
- `drifted_count`: `1`
- `degraded_count`: `0`
- `partial_coverage_count`: `1`
- `warning_count`: `6`
- `shared_artifact_count`: `25`
- `package_count`: `1`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=1)
- `top_issue_reason`: indicadores live refresh reused last published artifact for missing codes: ipc
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh reused last published artifact for missing codes: ipc [source_detail=public_api_with_published_backfill; warnings=1; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `autoridades_electas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `calidad_aire` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
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
| `finanzas_municipales` | `monthly` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `indicadores` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `indicadores_urbanos_siedu` | `live` | `ok` | `fresh` | `partial` | `healthy` |
| `partidos_politicos` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `perfil_territorial_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `permisos_edificacion` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `pobreza_comunal` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `resultados_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `30234309`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, dataset_changelog_json, dataset_quality_json, dataset_quality_markdown, dataset_status_json, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, source_readiness_json, source_readiness_markdown, status_json, status_markdown`
