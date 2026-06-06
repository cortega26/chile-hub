# chile-hub drift report

- `generated_at_utc`: `2026-06-06T23:11:44.833453+00:00`
- `dataset_count`: `4`
- `drifted_count`: `1`
- `healthy_count`: `3`
- `fallback_count`: `0`
- `partial_coverage_count`: `0`
- `degraded_count`: `0`

| Dataset | Drift | Mode | Coverage | Degradation | Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `regiones` | `healthy` | `live` | `full` | `none` | Ninguna. |
| `provincias` | `healthy` | `live` | `full` | `none` | Ninguna. |
| `comunas` | `healthy` | `live` | `full` | `none` | Ninguna. |
| `indicadores` | `drifted` | `live` | `not_applicable` | `warning` | Revisar warnings operativos del dataset antes de consumirlo en producción. |

## regiones

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## provincias

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## comunas

- `drift_status`: `healthy`
- `source_mode`: `live`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `degradation`: Sin degradación operativa detectada en este build.
- `recommended_action`: Ninguna.

## indicadores

- `drift_status`: `drifted`
- `source_mode`: `live`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `degradation`: indicadores freshness is stale: 127.55h since refresh, policy max is 72h
- `recommended_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
