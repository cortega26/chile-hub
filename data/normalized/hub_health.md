# chile-hub health summary

- `generated_at_utc`: `2026-06-25T11:01:38.705135+00:00`
- `overall_status`: `warn`
- `dataset_count`: `15`
- `ok_count`: `10`
- `warn_count`: `5`
- `error_count`: `0`
- `live_count`: `13`
- `fallback_count`: `2`
- `stale_count`: `0`
- `publishable_count`: `15`
- `review_terms_count`: `0`
- `unknown_reuse_count`: `0`
- `degraded_count`: `0`
- `degradation_warning_count`: `4`
- `partial_coverage_count`: `1`
- `unknown_coverage_count`: `0`
- `drifted_count`: `5`
- `warning_count`: `6`
- `top_issue`: `empresas` (freshness=fresh, drift=drifted, warnings=3)
- `top_issue_reason`: found 1 RUTs with invalid format
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: empresas: found 1 RUTs with invalid format [source_detail=datos_gob_cl_ckan_api; warnings=3; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| `censo_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `censo_hogares_viviendas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas_enriquecidas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `distritos_electorales` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `empresas` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 3 |
| `establecimientos_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `establecimientos_salud` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `finanzas_municipales` | `warn` | `fallback` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 1 |
| `indicadores` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 1 |
| `indicadores_urbanos_siedu` | `warn` | `live` | `fresh` | `partial` | `drifted` | `ready` | `warning` | `ok` | 1 |
| `perfil_territorial_comunal` | `warn` | `fallback` | `fresh` | `full` | `drifted` | `ready` | `none` | `ok` | 0 |
| `provincias` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `regiones` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `resultados_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
