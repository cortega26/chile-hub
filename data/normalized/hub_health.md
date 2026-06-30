# chile-hub health summary

- `generated_at_utc`: `2026-06-30T20:33:50.919792+00:00`
- `overall_status`: `warn`
- `dataset_count`: `17`
- `ok_count`: `12`
- `warn_count`: `5`
- `error_count`: `0`
- `live_count`: `15`
- `fallback_count`: `2`
- `stale_count`: `1`
- `publishable_count`: `17`
- `review_terms_count`: `0`
- `unknown_reuse_count`: `0`
- `degraded_count`: `0`
- `degradation_warning_count`: `5`
- `partial_coverage_count`: `2`
- `unknown_coverage_count`: `0`
- `drifted_count`: `6`
- `warning_count`: `11`
- `top_issue`: `consumo_electrico_comunal` (freshness=fresh, drift=drifted, warnings=3)
- `top_issue_reason`: tipos de cliente: ['Comercial', 'Residencial']
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: consumo_electrico_comunal: tipos de cliente: ['Comercial', 'Residencial'] [source_detail=Consumo eléctrico anual por comuna y tipo de cliente; warnings=3; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| `censo_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `censo_hogares_viviendas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas_enriquecidas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `consumo_electrico_comunal` | `warn` | `fallback` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 3 |
| `distritos_electorales` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `empresas` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 3 |
| `establecimientos_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `establecimientos_salud` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `finanzas_municipales` | `ok` | `live` | `fresh` | `partial` | `drifted` | `ready` | `none` | `ok` | 0 |
| `indicadores` | `warn` | `live` | `stale` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `indicadores_urbanos_siedu` | `warn` | `live` | `fresh` | `partial` | `drifted` | `ready` | `warning` | `ok` | 1 |
| `perfil_territorial_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `pobreza_comunal` | `warn` | `fallback` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `provincias` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `regiones` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `resultados_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
