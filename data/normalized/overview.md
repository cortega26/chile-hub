# chile-hub overview

- `generated_at_utc`: `2026-06-11T23:01:16.584873+00:00`
- `overall_status`: `warn`
- `dataset_count`: `4`
- `live_count`: `4`
- `fallback_count`: `0`
- `stale_count`: `1`
- `drifted_count`: `1`
- `degraded_count`: `0`
- `partial_coverage_count`: `0`
- `warning_count`: `1`
- `shared_artifact_count`: `16`
- `package_count`: `1`
- `top_issue`: `indicadores` (freshness=stale, drift=drifted, warnings=1)

| Dataset | Mode | Validation | Freshness | Coverage | Drift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comunas` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `indicadores` | `live` | `ok` | `stale` | `not_applicable` | `drifted` |
| `provincias` | `live` | `ok` | `fresh` | `full` | `healthy` |
| `regiones` | `live` | `ok` | `fresh` | `full` | `healthy` |

## Primary Package

- `path`: `data/normalized/chile-hub-publishable-bundle.zip`
- `package_type`: `zip`
- `size_bytes`: `54012`
- `checksum`: `sha256` via `data/normalized/chile-hub-publishable-bundle.zip.sha256`
- `verification_command`: `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256`

- `report_keys`: `bundle_json, catalog_json, catalog_markdown, drift_json, drift_markdown, health_json, health_markdown, manifest_json, overview_json, overview_markdown, provenance_json, provenance_markdown, redistribution_json, redistribution_markdown, status_markdown`
