# chile-hub overview

- `generated_at_utc`: `2026-06-16T19:40:24.888324+00:00`
- `overall_status`: `warn`
- `dataset_count`: `10`
- `live_count`: `10`
- `fallback_count`: `0`
- `stale_count`: `0`
- `drifted_count`: `1`
- `degraded_count`: `0`
- `partial_coverage_count`: `0`
- `warning_count`: `1`
- `shared_artifact_count`: `17`
- `package_count`: `1`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=1)
- `top_issue_reason`: indicadores live refresh reused last published artifact for missing codes: ipc
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh reused last published artifact for missing codes: ipc [source_detail=public_api_with_published_backfill; warnings=1; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `censo_comunal` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `censo_hogares_viviendas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `comunas_enriquecidas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `distritos_electorales` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `establecimientos_educacionales` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `establecimientos_salud` | `live` | `ok` | `fresh` | `not_applicable` | `healthy` |
| `indicadores` | `live` | `ok` | `fresh` | `not_applicable` | `drifted` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `1280000`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, status_json, status_markdown`
