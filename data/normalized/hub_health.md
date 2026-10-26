# chile-hub health summary

- `generated_at_utc`: `2026-10-25T23:25:43.532012+00:00`
- `overall_status`: `warn`
- `dataset_count`: `23`
- `ok_count`: `20`
- `warn_count`: `2`
- `error_count`: `0`
- `live_count`: `22`
- `fallback_count`: `0`
- `held_count`: `3`
- `stale_count`: `1`
- `publishable_count`: `22`
- `review_terms_count`: `0`
- `unknown_reuse_count`: `0`
- `degraded_count`: `0`
- `degradation_warning_count`: `2`
- `partial_coverage_count`: `1`
- `unknown_coverage_count`: `0`
- `drifted_count`: `2`
- `warning_count`: `8`
- `top_issue`: `calidad_aire` (freshness=stale, drift=drifted, warnings=2)
- `top_issue_reason`: cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: calidad_aire: cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación [source_detail=Promedios diarios por estación y contaminante (MP2.5, MP10, SO2, NO2, CO, O3) desde el JSON del SINCA. Cobertura parcial por diseño (~65 comunas con estación). Serie incremental desde la primera cosecha.; warnings=2; freshness=stale; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]

| Dataset | Severity | Mode | Freshness | Coverage | Drift | Publishability | Degradation | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| `autoridades_electas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `calidad_aire` | `warn` | `live` | `stale` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 2 |
| `censo_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `censo_hogares_viviendas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `comunas_enriquecidas` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `consumo_electrico_comunal` | `warn` | `fallback` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 3 |
| `distritos_electorales` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `empresas` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 1 |
| `establecimientos_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `establecimientos_salud` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `estadisticas_vitales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `finanzas_municipales` | `ok` | `monthly` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `indicadores` | `warn` | `live` | `fresh` | `not_applicable` | `drifted` | `ready` | `warning` | `ok` | 1 |
| `indicadores_urbanos_siedu` | `ok` | `live` | `fresh` | `partial` | `healthy` | `ready` | `none` | `ok` | 1 |
| `partidos_politicos` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 1 |
| `perfil_territorial_comunal` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `permisos_edificacion` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
| `pobreza_comunal` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 1 |
| `precipitaciones_dgac` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 1 |
| `provincias` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `regiones` | `ok` | `live` | `fresh` | `full` | `healthy` | `ready` | `none` | `ok` | 0 |
| `resultados_educacionales` | `ok` | `live` | `fresh` | `not_applicable` | `healthy` | `ready` | `none` | `ok` | 0 |
