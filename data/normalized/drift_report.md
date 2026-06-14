# chile-hub drift report

- `generated_at_utc`: `2026-06-14T18:08:08.213189+00:00`
- `dataset_count`: `7`
- `drifted_count`: `1`
- `healthy_count`: `6`
- `fallback_count`: `0`
- `partial_coverage_count`: `0`
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
