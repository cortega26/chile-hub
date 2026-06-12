# chile-hub health summary

- `generated_at_utc`: `2026-06-12T15:58:17.707652+00:00`
- `overall_status`: `warn`
- `dataset_count`: `4`
- `ok_count`: `3`
- `warn_count`: `1`
- `error_count`: `0`
- `live_count`: `4`
- `fallback_count`: `0`
- `stale_count`: `0`
- `publishable_count`: `4`
- `review_terms_count`: `0`
- `unknown_reuse_count`: `0`
- `degraded_count`: `0`
- `degradation_warning_count`: `1`
- `partial_coverage_count`: `0`
- `unknown_coverage_count`: `0`
- `drifted_count`: `1`
- `warning_count`: `2`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=2)
- `top_issue_reason`: indicadores live refresh returned empty series for: ipc/2026
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh returned empty series for: ipc/2026 [source_detail=public_api_with_published_backfill; warnings=2; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| `comunas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `indicadores` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `provincias` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `regiones` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
