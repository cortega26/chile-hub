# chile-hub pipeline status

- `generated_at_utc`: `2026-06-12T15:58:17.707652+00:00`
- `overall_status`: `warn`
- `warning_count`: `2`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=2)
- `top_issue_reason`: indicadores live refresh returned empty series for: ipc/2026
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh returned empty series for: ipc/2026 [source_detail=public_api_with_published_backfill; warnings=2; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]
- `hub_status_json`: `data/normalized/hub_status.json`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (263.97h / 2160h)` | `full` | 346 | `ok` | none |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `fresh (12.73h / 72h)` | `not_applicable` | 424 | `ok` | indicadores live refresh returned empty series for: ipc/2026; indicadores live refresh reused last published artifact for missing codes: ipc |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (263.97h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (263.97h / 2160h)` | `full` | 16 | `ok` | none |

## comunas

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (263.97h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## indicadores

- `refreshed_at_utc`: `2026-06-12T03:14:30.733498+00:00`
- `freshness`: `fresh (12.73h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `notes`: empty_live_pairs: ipc/2026; published_backfills_used_for_codes: ipc
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: indicadores live refresh returned empty series for: ipc/2026; indicadores live refresh reused last published artifact for missing codes: ipc

## provincias

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (263.97h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (263.97h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none
