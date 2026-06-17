# chile-hub drift report

- `generated_at_utc`: `2026-06-17T00:26:13.614202+00:00`
- `dataset_count`: `10`
- `drifted_count`: `1`
- `healthy_count`: `9`
- `fallback_count`: `0`
- `partial_coverage_count`: `0`
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
- `degradation`: indicadores live refresh reused raw snapshots for: uf/2026, dolar/2026, euro/2026, utm/2026; indicadores live refresh preserved previous staging rows for: ipc/2026
- `warning_count`: `2`
- `diagnostic_summary`: indicadores live refresh reused raw snapshots for: uf/2026, dolar/2026, euro/2026, utm/2026
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
