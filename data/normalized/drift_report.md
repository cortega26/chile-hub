# chile-hub drift report

- `generated_at_utc`: `2026-06-30T11:06:52.581611+00:00`
- `dataset_count`: `15`
- `drifted_count`: `5`
- `healthy_count`: `10`
- `fallback_count`: `2`
- `partial_coverage_count`: `1`
- `degraded_count`: `0`

| Dataset | Drift | Mode | Coverage | Degradation | Warnings | Action |
| :--- | :--- | :--- | :--- | :--- | ---: | :--- |
| `regiones` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `provincias` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `comunas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `comunas_enriquecidas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `indicadores` | `drifted` | `live` | `not_applicable` | `warning` | 1 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `censo_comunal` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `establecimientos_salud` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `establecimientos_educacionales` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `censo_hogares_viviendas` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `distritos_electorales` | `healthy` | `live` | `full` | `none` | 0 | Ninguna. |
| `finanzas_municipales` | `drifted` | `fallback` | `not_applicable` | `warning` | 1 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `resultados_educacionales` | `healthy` | `live` | `not_applicable` | `none` | 0 | Ninguna. |
| `indicadores_urbanos_siedu` | `drifted` | `live` | `partial` | `warning` | 1 | Revisar warnings operativos del dataset antes de consumirlo en producción. |
| `perfil_territorial_comunal` | `drifted` | `fallback` | `full` | `none` | 0 | Ninguna. |
| `empresas` | `drifted` | `live` | `not_applicable` | `warning` | 3 | Revisar warnings operativos del dataset antes de consumirlo en producción. |

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
- `degradation`: indicadores live refresh reused last published artifact for missing codes: ipc
- `warning_count`: `1`
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

- `drift_status`: `drifted`
- `source_mode`: `fallback`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: finanzas_municipales source_mode is fallback; review before publication
- `warning_count`: `1`
- `diagnostic_summary`: finanzas_municipales source_mode is fallback; review before publication
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.

## resultados_educacionales

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## indicadores_urbanos_siedu

- `drift_status`: `drifted`
- `source_mode`: `live`
- `coverage`: `Comunas urbanas incluidas por SIEDU, no las 346 comunas del país.`
- `degradation`: indicadores_urbanos_siedu has intentionally partial urban coverage
- `warning_count`: `1`
- `diagnostic_summary`: indicadores_urbanos_siedu has intentionally partial urban coverage
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.

## perfil_territorial_comunal

- `drift_status`: `drifted`
- `source_mode`: `fallback`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `warning_count`: `0`
- `diagnostic_summary`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## empresas

- `drift_status`: `drifted`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: found 1 RUTs with invalid format; unknown sociedad codes (new types?): ['SpA']; RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.
- `warning_count`: `3`
- `diagnostic_summary`: found 1 RUTs with invalid format
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
