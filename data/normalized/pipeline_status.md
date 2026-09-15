# chile-hub pipeline status

- `generated_at_utc`: `2026-09-15T00:04:41.910173+00:00`
- `overall_status`: `warn`
- `warning_count`: `6`
- `top_issue`: `empresas` (freshness=fresh, drift=healthy, warnings=1)
- `top_issue_reason`: RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.
- `top_issue_action`: Ninguna.
- `top_issue_summary`: empresas: RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013. [source_detail=datos_gob_cl_ckan_api; warnings=1; freshness=fresh; drift=healthy; action=Ninguna.]
- `hub_status_json`: `data/normalized/hub_status.json`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `autoridades_electas` | Cámara de Diputadas y Diputados + Senado de Chile | `live` | `WSDiputado.asmx/retornarDiputadosPeriodoActual + camara.cl + senado.cl (Scrapling)` | `fresh (820.24h / 87600h)` | `full` | 205 | `ok` | none |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (820.37h / 87600h)` | `full` | 346 | `ok` | none |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (566.6h / 87600h)` | `full` | 346 | `ok` | none |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (820.37h / 2160h)` | `full` | 346 | `ok` | none |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (820.37h / 2160h)` | `full` | 346 | `ok` | none |
| `consumo_electrico_comunal` | CNE — Energía Abierta | `fallback` | `Consumo eléctrico anual por comuna y tipo de cliente` | `fresh (820.26h / 17520h)` | `not_applicable` | 3 | `ok` | tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima. |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `fresh (820.37h / 87600h)` | `full` | 346 | `ok` | none |
| `empresas` | Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES) | `live` | `datos_gob_cl_ckan_api` | `fresh (820.26h / 1080h)` | `not_applicable` | 1590979 | `ok` | RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013. |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `fresh (820.37h / 8760h)` | `not_applicable` | 12898 | `ok` | none |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `fresh (820.37h / 1080h)` | `not_applicable` | 5717 | `ok` | none |
| `estadisticas_vitales` | Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales | `live` | `Anuarios de Estadísticas Vitales (tabulados XLSX, tabla 1.2.2-04 por comuna de residencia). Solo definitivos: los boletines provisionales del INE no publican desglose comunal.` | `fresh (0.59h / 8760h)` | `not_applicable` | 13840 | `ok` | none |
| `finanzas_municipales` | SINIM - SUBDERE | `monthly` | `curated_fallback_pending_direct_export` | `fresh (333.0h / 8760h)` | `not_applicable` | 345 | `ok` | none |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `stale (775.71h / 72h)` | `not_applicable` | 573 | `ok` | indicadores live refresh reused last published artifact for missing codes: ipc; indicadores freshness is stale: 775.71h since refresh, policy max is 72h |
| `indicadores_urbanos_siedu` | INE - Sistema de Indicadores y Estándares de Desarrollo Urbano | `live` | `ine_siedu_xlsm_cinco_mediciones_2018_2022` | `fresh (820.37h / 8760h)` | `partial` | 6701 | `ok` | indicadores_urbanos_siedu has intentionally partial urban coverage |
| `partidos_politicos` | Cámara de Diputadas y Diputados (datos abiertos) + SERVEL | `live` | `WSComun.asmx/retornarPartidosPoliticos + servel.cl/partidos-politicos (estado legal)` | `fresh (820.26h / 87600h)` | `full` | 36 | `ok` | estado_legal poblado (vía SERVEL) en 15/36 partidos |
| `perfil_territorial_comunal` | chile-hub | `live` | `derived_from_validated_chile_hub_layers` | `fresh (0.0h / 1080h)` | `full` | 346 | `ok` | none |
| `permisos_edificacion` | MINVU — Centro de Estudios de Ciudad y Territorio (CEDOC) | `live` | `Viviendas en unidades y superficie (m2) por comuna y año, serie desde 2002 (MINVU CEDOC, en base a permisos otorgados por las Direcciones de Obras Municipales e INE).` | `fresh (0.06h / 1080h)` | `not_applicable` | 8650 | `ok` | none |
| `pobreza_comunal` | Observatorio Social — Ministerio de Desarrollo Social y Familia | `live` | `Estimaciones de Pobreza Comunal vía SAE desde encuesta CASEN` | `fresh (820.26h / 175200h)` | `not_applicable` | 690 | `ok` | cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (820.37h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (820.37h / 2160h)` | `full` | 16 | `ok` | none |
| `resultados_educacionales` | Centro de Estudios MINEDUC - Rendimiento 2024 | `live` | `mineduc_rendimiento_2024_rar_agregado_por_comuna` | `fresh (820.37h / 8760h)` | `not_applicable` | 345 | `ok` | none |

## autoridades_electas

- `refreshed_at_utc`: `2026-08-11T19:50:16.685023+00:00`
- `freshness`: `fresh (820.24h / 87600h)`
- `coverage`: `Cobertura completa: 205/205 filas respecto del baseline esperado.`
- `fields`: `id_autoridad, nombre, cargo, institucion, partido, pacto, distrito_electoral, circunscripcion_senatorial, codigo_comuna, codigo_region, periodo_inicio, periodo_fin, estado_mandato, fuente, url_fuente, fecha_consulta`
- `notes`: v1: diputados (155) + senadores (50). Gobernador_regional/alcalde viven en el dataset segregado autoridades_locales (licencia CC-BY-SA).; distrito_electoral vía Scrapling: 154/155 diputados.; codigo_region/periodo de senadores: 50/50 poblados desde senado.cl (REGION/PERIODOS).; RUT (Cámara) y email/teléfono (Senado) descartados (línea roja de datos personales).
- `warnings`: none

## censo_comunal

- `refreshed_at_utc`: `2026-08-11T19:42:36.653758+00:00`
- `freshness`: `fresh (820.37h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, poblacion_censada, hombres, mujeres, razon_hombre_mujer, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas`
- `notes`: age_bands_derived_from_quinquennial_groups
- `warnings`: none

## censo_hogares_viviendas

- `refreshed_at_utc`: `2026-08-22T09:28:35.974071+00:00`
- `freshness`: `fresh (566.6h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, viviendas_censadas, viviendas_particulares_ocupadas, viviendas_particulares_desocupadas, viviendas_colectivas, hogares_censados, promedio_personas_hogar`
- `warnings`: none

## comunas

- `refreshed_at_utc`: `2026-08-11T19:42:23.780877+00:00`
- `freshness`: `fresh (820.37h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## comunas_enriquecidas

- `refreshed_at_utc`: `2026-08-11T19:42:23.780877+00:00`
- `freshness`: `fresh (820.37h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## consumo_electrico_comunal

- `refreshed_at_utc`: `2026-08-11T19:49:06.413089+00:00`
- `freshness`: `fresh (820.26h / 17520h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, tipo_cliente, consumo_kwh, numero_clientes, fuente, url_fuente, fecha_fuente`
- `notes`: fallback: usando datos de muestra (HTTPConnectionPool(host='datos.energiaabierta.cl', port=80): Max retries exceeded with url: /dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/ (Caused by NameResolutionError("HTTPConnection(host='datos.energiaabierta.cl', port=80): Failed to resolve 'datos.energiaabierta.cl' ([Errno -2] Name or service not known)"))). fuente confirmada caída de forma permanente (2026-07-07): CNE migró energiaabierta.cl a WordPress y decomisionó el catálogo Junar; no existe archivo ni endpoint de reemplazo. Ver AGENTS.md §6.
- `warnings`: tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.

## distritos_electorales

- `refreshed_at_utc`: `2026-08-11T19:42:40.945699+00:00`
- `freshness`: `fresh (820.37h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_comuna, nombre_comuna, distrito_electoral, circunscripcion_senatorial`
- `warnings`: none

## empresas

- `refreshed_at_utc`: `2026-08-11T19:49:00.139637+00:00`
- `freshness`: `fresh (820.26h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rut, razon_social, codigo_sociedad, tipo_actuacion, capital, fecha_actuacion, fecha_registro, fecha_aprobacion_sii, anio, mes, comuna_tributaria, region_tributaria, comuna_social, region_social`
- `notes`: filas descartadas por RUT centinela ['0']: 1; Solo incluye empresas constituidas bajo el Regimen Simplificado (Ley 20.659) desde mayo 2013.; No contiene dirección postal (solo comuna y región).; No contiene actividad económica (giro).; No refleja cese de actividades ni modificaciones posteriores.; Los codigos de region usan el formato numerico del SII (1-15), distinto del codigo CUT (01-16). Verificar antes de cruzar con DPA.
- `warnings`: RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.

## establecimientos_educacionales

- `refreshed_at_utc`: `2026-08-11T19:42:41.413175+00:00`
- `freshness`: `fresh (820.37h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rbd, dv_rbd, nombre_establecimiento, codigo_region, codigo_comuna, dependencia_administrativa, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## establecimientos_salud

- `refreshed_at_utc`: `2026-08-11T19:42:40.802326+00:00`
- `freshness`: `fresh (820.37h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_establecimiento, nombre_establecimiento, tipo_establecimiento, dependencia_administrativa, nivel_atencion, codigo_region, nombre_region, codigo_comuna, nombre_comuna, tiene_servicio_urgencia, tipo_urgencia, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## estadisticas_vitales

- `refreshed_at_utc`: `2026-09-14T23:29:24.975832+00:00`
- `freshness`: `fresh (0.59h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_region, codigo_comuna, nombre_comuna, evento, sexo, cantidad, estado_dato, fuente, url_fuente, fecha_fuente`
- `notes`: 2010: 692 filas desde 'Anuario de estadísticas vitales 2010' (hoja 122-04; TOTAL país: 250643 nacimientos, 97930 defunciones); 2011: 692 filas desde 'Anuario de estadísticas vitales 2011' (hoja 122-04; TOTAL país: 247358 nacimientos, 94985 defunciones); 2012: 692 filas desde 'Anuario de estadísticas vitales 2012' (hoja 122-04; TOTAL país: 243635 nacimientos, 98711 defunciones); 2013: 692 filas desde 'Anuario de estadísticas vitales 2013' (hoja 1.2.2-04; TOTAL país: 242005 nacimientos, 99770 defunciones); 2014: 692 filas desde 'Anuario de estadísticas vitales 2014' (hoja 1.2.2-04; TOTAL país: 250997 nacimientos, 101960 defunciones); 2015: 692 filas desde 'Anuario de estadísticas vitales 2015' (hoja 1.2.2-04; TOTAL país: 244670 nacimientos, 103327 defunciones); 2016: 692 filas desde 'Anuario de estadísticas vitales nacimientos 2016' (hoja 1.2.2-04; TOTAL país: 231749 nacimientos, 104026 defunciones); 2017: 692 filas desde 'Anuario de estadísticas vitales 2017' (hoja 1.2.2-04; TOTAL país: 219186 nacimientos, 106388 defunciones); 2018: convención de indentado invertida (comuna indentada); 2018: 692 filas desde 'Anuario de estadísticas vitales 2018' (hoja 122-04; TOTAL país: 221731 nacimientos, 106796 defunciones); 2019: convención de indentado invertida (comuna indentada); 2019: 692 filas desde 'Anuario de estadísticas vitales 2019' (hoja 122-04; TOTAL país: 210188 nacimientos, 109658 defunciones); 2020: convención de indentado invertida (comuna indentada); 2020: 692 filas desde 'Anuario de estadísticas vitales 2020' (hoja 122-04; TOTAL país: 194978 nacimientos, 126169 defunciones); 2021: 2076 filas desde 'Anuario de estadísticas vitales 2021' (hoja 122-04; TOTAL país: 177273 nacimientos, 137629 defunciones); 2022: 2076 filas desde 'Anuario de estadísticas vitales 2022, nacimientos y defunciones' (hoja 122-04; TOTAL país: 189303 nacimientos, 136972 defunciones); 2023: 2076 filas desde 'Anuario de estadísticas vitales 2023, nacimientos y defunciones' (hoja 122-04; TOTAL país: 174057 nacimientos, 122218 defunciones)
- `warnings`: none

## finanzas_municipales

- `refreshed_at_utc`: `2026-09-01T03:04:24.987281+00:00`
- `freshness`: `fresh (333.0h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, nombre_comuna, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion`
- `notes`: live: Playwright configurando filtros SINIM; live: descargando XML Spreadsheet; live: parseando XML Spreadsheet; live: 345 municipios extraídos (snapshot: sinim_finanzas_municipales_20260901T030218Z.xlsx)
- `warnings`: none

## indicadores

- `refreshed_at_utc`: `2026-08-13T16:22:04.519950+00:00`
- `freshness`: `stale (775.71h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `notes`: published_backfills_used_for_codes: ipc; ine_override_used_for_pairs: ipc/2026
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: indicadores live refresh reused last published artifact for missing codes: ipc; indicadores freshness is stale: 775.71h since refresh, policy max is 72h

## indicadores_urbanos_siedu

- `refreshed_at_utc`: `2026-08-11T19:42:46.514973+00:00`
- `freshness`: `fresh (820.37h / 8760h)`
- `coverage`: `Comunas urbanas incluidas por SIEDU, no las 346 comunas del país.`
- `fields`: `anio, codigo_comuna, codigo_indicador, nombre_indicador, categoria, valor, unidad, fuente_original, cobertura_tipo`
- `notes`: partial_urban_coverage_expected; deduplicado_anno_mas_reciente_por_indicador_comuna; 5_mediciones_2018_2022_consolidadas; live_data: xlsm parseado, 6701 registros, 117 comunas, 68 indicadores
- `warnings`: indicadores_urbanos_siedu has intentionally partial urban coverage

## partidos_politicos

- `refreshed_at_utc`: `2026-08-11T19:49:08.719490+00:00`
- `freshness`: `fresh (820.26h / 87600h)`
- `coverage`: `Cobertura completa: 36/36 filas respecto del baseline esperado.`
- `fields`: `id_partido, nombre, sigla, estado_legal, fecha_constitucion, ambito, fuente, url_fuente, fecha_consulta`
- `notes`: Roster de partidos de la Cámara (incluye vigentes e históricos).; estado_legal/fecha_constitucion vía SERVEL: 15/36 matcheados por nombre.; ambito (nacional/regional) no provisto por ninguna fuente encontrada (nullable).
- `warnings`: estado_legal poblado (vía SERVEL) en 15/36 partidos

## perfil_territorial_comunal

- `refreshed_at_utc`: `2026-09-15T00:04:41.904987+00:00`
- `freshness`: `fresh (0.0h / 1080h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada, poblacion_censada, poblacion_hombres, poblacion_mujeres, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas, viviendas_censadas, hogares_censados, promedio_personas_por_hogar, establecimientos_salud_total, establecimientos_educacionales_total, distrito_electoral, circunscripcion_senatorial, anio_finanzas, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion, anio_resultados_educacionales, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados, indicadores_siedu_total, valor_promedio_siedu`
- `notes`: derived_dataset; upstreams: comunas,censo_comunal,censo_hogares_viviendas,establecimientos_salud,establecimientos_educacionales,distritos_electorales,finanzas_municipales,resultados_educacionales,indicadores_urbanos_siedu
- `warnings`: none

## permisos_edificacion

- `refreshed_at_utc`: `2026-09-15T00:00:56.170127+00:00`
- `freshness`: `fresh (0.06h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_region, codigo_comuna, nombre_comuna, unidades_total, superficie_m2_total, unidades_casas, superficie_m2_casas, unidades_departamentos, superficie_m2_departamentos, estado_dato, fuente, url_fuente, fecha_fuente`
- `notes`: descubrimiento: repositorio-biblionumber; 8650 filas desde 'minvu_permisos_edificacion_anual_20260915T000055Z.xlsx' (hojas: número_total, m2_total, número_departamentos, m2_departamentos, número_casas, m2_casas; años provisionales: [2024, 2025, 2026])
- `warnings`: none

## pobreza_comunal

- `refreshed_at_utc`: `2026-08-11T19:49:01.701838+00:00`
- `freshness`: `fresh (820.26h / 175200h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, dimension, tasa, limite_inferior, limite_superior, metodologia, fuente, url_fuente, fecha_fuente`
- `notes`: ingresos: 345 comunas con estimación desde URL oficial; multidimensional: 345 comunas con estimación desde URL oficial
- `warnings`: cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación

## provincias

- `refreshed_at_utc`: `2026-08-11T19:42:23.780877+00:00`
- `freshness`: `fresh (820.37h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-08-11T19:42:23.780877+00:00`
- `freshness`: `fresh (820.37h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## resultados_educacionales

- `refreshed_at_utc`: `2026-08-11T19:42:44.201011+00:00`
- `freshness`: `fresh (820.37h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados`
- `notes`: privacy_safe_comuna_year_aggregation; sit_fin_r_Y=retirado T=trasladado asistencia_only_for_P_R_students; source_file: mineduc_rendimiento_2024.rar, comunas_agregadas: 345
- `warnings`: none
