# chile-hub drift report

- `generated_at_utc`: `2026-07-29T15:00:04.506057+00:00`
- `dataset_count`: `19`
- `drifted_count`: `3`
- `healthy_count`: `16`
- `fallback_count`: `1`
- `partial_coverage_count`: `2`
- `degraded_count`: `0`

| Dataset | Drift | Mode | Coverage | Degradation | Warnings | Action |
| :--- | :--- | :--- | :--- | :--- | ---: | :--- |
| `regiones` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `provincias` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `comunas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `comunas_enriquecidas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `indicadores` | `drifted` | `live` | `not_applicable` | `warning` | 2 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `censo_comunal` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `establecimientos_salud` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `establecimientos_educacionales` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `censo_hogares_viviendas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `distritos_electorales` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `finanzas_municipales` | `healthy` | `monthly` | `partial` | `none` | 0 | Ninguna. |
| `resultados_educacionales` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `indicadores_urbanos_siedu` | `healthy` | `live` | `partial` | `none` | 1 | Ninguna. |
| `perfil_territorial_comunal` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `empresas` | `drifted` | `live` | `not_applicable` | `warning` | 2 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `pobreza_comunal` | `healthy` | `live` | `not_applicable` | `none` | 1 | Ninguna. |
| `consumo_electrico_comunal` | `drifted` | `fallback` | `not_applicable` | `warning` | 3 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `partidos_politicos` | `healthy` | `live` | `full` | `none` | 1 | Ninguna. |
| `autoridades_electas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |

## regiones

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## provincias

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## comunas

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## comunas_enriquecidas

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## indicadores

- `drift_status`: `drifted`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: indicadores live refresh reused last published artifact for missing codes: ipc; indicadores freshness is stale: 229.36h since refresh, policy max is 72h
- `warning_count`: `2`
- `diagnostic_summary`: indicadores live refresh reused last published artifact for missing codes: ipc
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.

## censo_comunal

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## establecimientos_salud

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## establecimientos_educacionales

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## censo_hogares_viviendas

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## distritos_electorales

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## finanzas_municipales

- `drift_status`: `healthy`
- `source_mode`: `monthly`
- `coverage`: `Cobertura parcial: 345/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## resultados_educacionales

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## indicadores_urbanos_siedu

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Comunas urbanas incluidas por SIEDU, no las 346 comunas del país.`
- `degradation`: 1 observación(es) esperada(s): indicadores_urbanos_siedu has intentionally partial urban coverage
- `warning_count`: `1`
- `diagnostic_summary`: indicadores_urbanos_siedu has intentionally partial urban coverage
- `recommended_action`: Ninguna.

## perfil_territorial_comunal

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## empresas

- `drift_status`: `drifted`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: found 1 RUTs with invalid format
- `warning_count`: `2`
- `diagnostic_summary`: found 1 RUTs with invalid format
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.

## pobreza_comunal

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: 1 observación(es) esperada(s): cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación
- `warning_count`: `1`
- `diagnostic_summary`: cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación
- `recommended_action`: Ninguna.

## consumo_electrico_comunal

- `drift_status`: `drifted`
- `source_mode`: `fallback`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.
- `warning_count`: `3`
- `diagnostic_summary`: tipos de cliente: ['Comercial', 'Residencial']
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.

## partidos_politicos

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 36/36 filas respecto del baseline esperado.`
- `degradation`: 1 observación(es) esperada(s): estado_legal poblado (vía SERVEL) en 15/36 partidos
- `warning_count`: `1`
- `diagnostic_summary`: estado_legal poblado (vía SERVEL) en 15/36 partidos
- `recommended_action`: Ninguna.

## autoridades_electas

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 205/205 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.
