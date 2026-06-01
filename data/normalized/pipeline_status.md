# chile-hub pipeline status

- `generated_at_utc`: `2026-06-01T17:37:55.601608+00:00`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (1.63h / 2160h)` | `full` | 346 | `ok` | none |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api` | `fresh (1.99h / 72h)` | `not_applicable` | 375 | `ok` | none |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (1.63h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (1.63h / 2160h)` | `full` | 16 | `ok` | none |

## comunas

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (1.63h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## indicadores

- `refreshed_at_utc`: `2026-06-01T15:38:37.668778+00:00`
- `freshness`: `fresh (1.99h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: none

## provincias

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (1.63h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (1.63h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none
