# chile-hub health summary

- `generated_at_utc`: `2026-07-29T14:55:39.488634+00:00`
- `overall_status`: `warn`
- `dataset_count`: `19`
- `ok_count`: `16`
- `warn_count`: `2`
- `error_count`: `0`
- `live_count`: `18`
- `fallback_count`: `0`
- `stale_count`: `1`
- `publishable_count`: `18`
- `review_terms_count`: `0`
- `unknown_reuse_count`: `0`
- `degraded_count`: `0`
- `degradation_warning_count`: `2`
- `partial_coverage_count`: `2`
- `unknown_coverage_count`: `0`
- `drifted_count`: `2`
- `warning_count`: `7`
- `top_issue`: `empresas` (freshness=fresh, drift=drifted, warnings=2)
- `top_issue_reason`: found 1 RUTs with invalid format
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: empresas: found 1 RUTs with invalid format [source_detail=datos_gob_cl_ckan_api; warnings=2; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| `autoridades_electas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `censo_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `censo_hogares_viviendas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas_enriquecidas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `consumo_electrico_comunal` | `warn` | `fallback` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 3 |
| `distritos_electorales` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `empresas` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `establecimientos_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `establecimientos_salud` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `finanzas_municipales` | `ok` | `monthly` | `fresh` | `partial` | `healthy` | `ready` | `none` | `ok` | 0 |
| `indicadores` | `warn` | `live` | `stale` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `indicadores_urbanos_siedu` | `ok` | `live` | `fresh` | `partial` | `healthy` | `ready` | `none` | `ok` | 1 |
| `partidos_politicos` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 1 |
| `perfil_territorial_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `pobreza_comunal` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 1 |
| `provincias` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `regiones` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `resultados_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
