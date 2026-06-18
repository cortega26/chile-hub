# chile-hub pipeline status

- `generated_at_utc`: `2026-06-18T18:20:03.516188+00:00`
- `overall_status`: `warn`
- `warning_count`: `9`
- `top_issue`: `empresas` (freshness=fresh, drift=drifted, warnings=3)
- `top_issue_reason`: found 1 RUTs with non-standard format (not validated)
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: empresas: found 1 RUTs with non-standard format (not validated) [source_detail=datos_gob_cl_ckan_api; warnings=3; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]
- `hub_status_json`: `data/normalized/hub_status.json`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (25.48h / 87600h)` | `full` | 346 | `ok` | none |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (25.48h / 87600h)` | `full` | 346 | `ok` | none |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (25.49h / 2160h)` | `full` | 346 | `ok` | none |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (25.49h / 2160h)` | `full` | 346 | `ok` | none |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `fresh (25.48h / 87600h)` | `full` | 346 | `ok` | none |
| `empresas` | Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES) | `live` | `datos_gob_cl_ckan_api` | `fresh (3.13h / 1080h)` | `not_applicable` | 1572116 | `ok` | found 1 RUTs with non-standard format (not validated); unknown sociedad codes (new types?): ['SpA']; RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013. |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `fresh (25.48h / 8760h)` | `not_applicable` | 12898 | `ok` | none |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `fresh (25.48h / 1080h)` | `not_applicable` | 5643 | `ok` | none |
| `finanzas_municipales` | SINIM - SUBDERE | `fallback` | `curated_fallback_pending_direct_export` | `fresh (25.48h / 8760h)` | `not_applicable` | 3 | `ok` | finanzas_municipales source_mode is fallback; review before publication |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `fresh (25.48h / 72h)` | `not_applicable` | 430 | `ok` | indicadores live refresh reused raw snapshots for: uf/2026; indicadores live refresh reused last published artifact for missing codes: ipc |
| `indicadores_urbanos_siedu` | INE - Sistema de Indicadores y Estándares de Desarrollo Urbano | `fallback` | `curated_fallback_partial_urban_coverage` | `fresh (25.48h / 8760h)` | `partial` | 6 | `ok` | indicadores_urbanos_siedu has intentionally partial urban coverage; indicadores_urbanos_siedu source_mode is fallback; review before publication |
| `perfil_territorial_comunal` | chile-hub | `fallback` | `derived_from_validated_chile_hub_layers` | `fresh (0.0h / 1080h)` | `full` | 346 | `ok` | none |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (25.49h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (25.49h / 2160h)` | `full` | 16 | `ok` | none |
| `resultados_educacionales` | Centro de Estudios MINEDUC - Datos Abiertos | `fallback` | `curated_fallback_comuna_year_aggregation` | `fresh (25.48h / 8760h)` | `not_applicable` | 3 | `ok` | resultados_educacionales source_mode is fallback; review before publication |

## censo_comunal

- `refreshed_at_utc`: `2026-06-17T16:51:19.142622+00:00`
- `freshness`: `fresh (25.48h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, poblacion_censada, hombres, mujeres, razon_hombre_mujer, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas`
- `notes`: age_bands_derived_from_quinquennial_groups
- `warnings`: none

## censo_hogares_viviendas

- `refreshed_at_utc`: `2026-06-17T16:51:19.609225+00:00`
- `freshness`: `fresh (25.48h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, viviendas_censadas, viviendas_particulares_ocupadas, viviendas_particulares_desocupadas, viviendas_colectivas, hogares_censados, promedio_personas_hogar`
- `warnings`: none

## comunas

- `refreshed_at_utc`: `2026-06-17T16:50:40.866524+00:00`
- `freshness`: `fresh (25.49h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## comunas_enriquecidas

- `refreshed_at_utc`: `2026-06-17T16:50:40.866524+00:00`
- `freshness`: `fresh (25.49h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## distritos_electorales

- `refreshed_at_utc`: `2026-06-17T16:51:24.727935+00:00`
- `freshness`: `fresh (25.48h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_comuna, nombre_comuna, distrito_electoral, circunscripcion_senatorial`
- `warnings`: none

## empresas

- `refreshed_at_utc`: `2026-06-18T15:12:32.375088+00:00`
- `freshness`: `fresh (3.13h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rut, razon_social, codigo_sociedad, tipo_actuacion, capital, fecha_actuacion, fecha_registro, fecha_aprobacion_sii, anio, mes, comuna_tributaria, region_tributaria, comuna_social, region_social`
- `notes`: Solo incluye empresas constituidas bajo el Regimen Simplificado (Ley 20.659) desde mayo 2013.; No contiene direccion postal (solo comuna y region).; No contiene actividad economica (giro).; No refleja cese de actividades ni modificaciones posteriores.; Los codigos de region usan el formato numerico del SII (1-15), distinto del codigo CUT (01-16). Verificar antes de cruzar con DPA.
- `warnings`: found 1 RUTs with non-standard format (not validated); unknown sociedad codes (new types?): ['SpA']; RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.

## establecimientos_educacionales

- `refreshed_at_utc`: `2026-06-17T16:51:25.318310+00:00`
- `freshness`: `fresh (25.48h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rbd, dv_rbd, nombre_establecimiento, codigo_region, codigo_comuna, dependencia_administrativa, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## establecimientos_salud

- `refreshed_at_utc`: `2026-06-17T16:51:24.593612+00:00`
- `freshness`: `fresh (25.48h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_establecimiento, nombre_establecimiento, tipo_establecimiento, dependencia_administrativa, nivel_atencion, codigo_region, nombre_region, codigo_comuna, nombre_comuna, tiene_servicio_urgencia, tipo_urgencia, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## finanzas_municipales

- `refreshed_at_utc`: `2026-06-17T16:51:25.710419+00:00`
- `freshness`: `fresh (25.48h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, nombre_comuna, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion`
- `notes`: official_landing_snapshot_saved; fallback_curated_rows_used_until_stable_direct_export_is_configured
- `warnings`: finanzas_municipales source_mode is fallback; review before publication

## indicadores

- `refreshed_at_utc`: `2026-06-17T16:51:18.423894+00:00`
- `freshness`: `fresh (25.48h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `notes`: raw_recovery_used_for_pairs: uf/2026; published_backfills_used_for_codes: ipc
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: indicadores live refresh reused raw snapshots for: uf/2026; indicadores live refresh reused last published artifact for missing codes: ipc

## indicadores_urbanos_siedu

- `refreshed_at_utc`: `2026-06-17T16:51:29.383250+00:00`
- `freshness`: `fresh (25.48h / 8760h)`
- `coverage`: `Comunas urbanas incluidas por SIEDU, no las 346 comunas del país.`
- `fields`: `anio, codigo_comuna, codigo_indicador, nombre_indicador, categoria, valor, unidad, fuente_original, cobertura_tipo`
- `notes`: partial_urban_coverage_expected; official_landing_snapshot_saved; fallback_curated_rows_used_until_download_matrix_is_configured
- `warnings`: indicadores_urbanos_siedu has intentionally partial urban coverage; indicadores_urbanos_siedu source_mode is fallback; review before publication

## perfil_territorial_comunal

- `refreshed_at_utc`: `2026-06-18T18:20:03.515006+00:00`
- `freshness`: `fresh (0.0h / 1080h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada, poblacion_censada, poblacion_hombres, poblacion_mujeres, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas, viviendas_censadas, hogares_censados, promedio_personas_por_hogar, establecimientos_salud_total, establecimientos_educacionales_total, distrito_electoral, circunscripcion_senatorial, anio_finanzas, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion, anio_resultados_educacionales, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados, indicadores_siedu_total, valor_promedio_siedu`
- `notes`: derived_dataset; upstreams: comunas,censo_comunal,censo_hogares_viviendas,establecimientos_salud,establecimientos_educacionales,distritos_electorales,finanzas_municipales,resultados_educacionales,indicadores_urbanos_siedu
- `warnings`: none

## provincias

- `refreshed_at_utc`: `2026-06-17T16:50:40.866524+00:00`
- `freshness`: `fresh (25.49h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-06-17T16:50:40.866524+00:00`
- `freshness`: `fresh (25.49h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## resultados_educacionales

- `refreshed_at_utc`: `2026-06-17T16:51:28.239977+00:00`
- `freshness`: `fresh (25.48h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados`
- `notes`: privacy_safe_comuna_year_aggregation; official_landing_snapshot_saved; fallback_curated_rows_used_until_direct_outcome_dump_is_configured
- `warnings`: resultados_educacionales source_mode is fallback; review before publication
