# chile-hub pipeline status

- `generated_at_utc`: `2026-06-15T23:39:29.359352+00:00`
- `overall_status`: `warn`
- `warning_count`: `1`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=1)
- `top_issue_reason`: indicadores live refresh reused last published artifact for missing codes: ipc
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh reused last published artifact for missing codes: ipc [source_detail=public_api_with_published_backfill; warnings=1; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]
- `hub_status_json`: `data/normalized/hub_status.json`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (29.52h / 87600h)` | `full` | 346 | `ok` | none |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (29.0h / 87600h)` | `full` | 346 | `ok` | none |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (49.61h / 2160h)` | `full` | 346 | `ok` | none |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (49.61h / 2160h)` | `full` | 346 | `ok` | none |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `fresh (0.19h / 87600h)` | `full` | 346 | `ok` | none |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `fresh (0.06h / 8760h)` | `not_applicable` | 12898 | `ok` | none |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `fresh (29.54h / 1080h)` | `not_applicable` | 5643 | `ok` | none |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `fresh (49.61h / 72h)` | `not_applicable` | 426 | `ok` | indicadores live refresh reused last published artifact for missing codes: ipc |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (49.61h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (49.61h / 2160h)` | `full` | 16 | `ok` | none |

## censo_comunal

- `refreshed_at_utc`: `2026-06-14T18:08:06.406574+00:00`
- `freshness`: `fresh (29.52h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, poblacion_censada, hombres, mujeres, razon_hombre_mujer, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas`
- `notes`: age_bands_derived_from_quinquennial_groups
- `warnings`: none

## censo_hogares_viviendas

- `refreshed_at_utc`: `2026-06-14T18:39:22.957446+00:00`
- `freshness`: `fresh (29.0h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, viviendas_censadas, viviendas_particulares_ocupadas, viviendas_particulares_desocupadas, viviendas_colectivas, hogares_censados, promedio_personas_hogar`
- `warnings`: none

## comunas

- `refreshed_at_utc`: `2026-06-13T22:02:44.348995+00:00`
- `freshness`: `fresh (49.61h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## comunas_enriquecidas

- `refreshed_at_utc`: `2026-06-13T22:02:44.348995+00:00`
- `freshness`: `fresh (49.61h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## distritos_electorales

- `refreshed_at_utc`: `2026-06-15T23:28:09.928013+00:00`
- `freshness`: `fresh (0.19h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_comuna, nombre_comuna, distrito_electoral, circunscripcion_senatorial`
- `warnings`: none

## establecimientos_educacionales

- `refreshed_at_utc`: `2026-06-15T23:35:37.946512+00:00`
- `freshness`: `fresh (0.06h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rbd, dv_rbd, nombre_establecimiento, codigo_region, codigo_comuna, dependencia_administrativa, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## establecimientos_salud

- `refreshed_at_utc`: `2026-06-14T18:06:51.839082+00:00`
- `freshness`: `fresh (29.54h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_establecimiento, nombre_establecimiento, tipo_establecimiento, dependencia_administrativa, nivel_atencion, codigo_region, nombre_region, codigo_comuna, nombre_comuna, tiene_servicio_urgencia, tipo_urgencia, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## indicadores

- `refreshed_at_utc`: `2026-06-13T22:02:50.757821+00:00`
- `freshness`: `fresh (49.61h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `notes`: published_backfills_used_for_codes: ipc
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: indicadores live refresh reused last published artifact for missing codes: ipc

## provincias

- `refreshed_at_utc`: `2026-06-13T22:02:44.348995+00:00`
- `freshness`: `fresh (49.61h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-06-13T22:02:44.348995+00:00`
- `freshness`: `fresh (49.61h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none
