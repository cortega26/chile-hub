# chile-hub pipeline status

- `generated_at_utc`: `2026-10-02T16:05:00.198588+00:00`
- `overall_status`: `warn`
- `warning_count`: `6`
- `top_issue`: `indicadores` (freshness=fresh, drift=drifted, warnings=1)
- `top_issue_reason`: indicadores live refresh reused last published artifact for missing codes: ipc
- `top_issue_action`: Revisar warnings operativos del dataset antes de consumirlo en producción.
- `top_issue_summary`: indicadores: indicadores live refresh reused last published artifact for missing codes: ipc [source_detail=public_api_with_published_backfill; warnings=1; freshness=fresh; drift=drifted; action=Revisar warnings operativos del dataset antes de consumirlo en producción.]
- `hub_status_json`: `data/normalized/hub_status.json`

| Dataset | Source | Mode | Detail | Freshness | Coverage | Records | Validation | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| `autoridades_electas` | Cámara de Diputadas y Diputados + Senado de Chile | `live` | `WSDiputado.asmx/retornarDiputadosPeriodoActual + camara.cl + senado.cl (Scrapling)` | `fresh (0.0h / 87600h)` | `full` | 205 | `ok` | none |
| `calidad_aire` | SINCA — Ministerio del Medio Ambiente | `live` | `Promedios diarios por estación y contaminante (MP2.5, MP10, SO2, NO2, CO, O3) desde el JSON del SINCA. Cobertura parcial por diseño (~65 comunas con estación). Serie incremental desde la primera cosecha.` | `fresh (0.01h / 72h)` | `not_applicable` | 4134 | `ok` | cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (0.03h / 87600h)` | `full` | 346 | `ok` | none |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `fresh (0.03h / 87600h)` | `full` | 346 | `ok` | none |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (0.03h / 2160h)` | `full` | 346 | `ok` | none |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (0.03h / 2160h)` | `full` | 346 | `ok` | none |
| `consumo_electrico_comunal` | CNE — Energía Abierta | `fallback` | `Consumo eléctrico anual por comuna y tipo de cliente` | `fresh (0.02h / 17520h)` | `not_applicable` | 3 | `ok` | tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima. |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `fresh (0.03h / 87600h)` | `full` | 346 | `ok` | none |
| `empresas` | Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES) | `live` | `datos_gob_cl_ckan_api` | `fresh (0.02h / 1080h)` | `not_applicable` | 1628433 | `ok` | RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013. |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `fresh (0.02h / 8760h)` | `not_applicable` | 12898 | `ok` | none |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `fresh (0.03h / 1080h)` | `not_applicable` | 5743 | `ok` | none |
| `estadisticas_vitales` | Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales | `live` | `Anuarios de Estadísticas Vitales (tabulados XLSX, tabla 1.2.2-04 por comuna de residencia). Solo definitivos: los boletines provisionales del INE no publican desglose comunal.` | `fresh (0.01h / 8760h)` | `not_applicable` | 13840 | `ok` | none |
| `finanzas_municipales` | SINIM - SUBDERE | `monthly` | `curated_fallback_pending_direct_export` | `fresh (757.01h / 8760h)` | `not_applicable` | 345 | `ok` | none |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `fresh (0.03h / 72h)` | `not_applicable` | 675 | `ok` | indicadores live refresh reused last published artifact for missing codes: ipc |
| `indicadores_urbanos_siedu` | INE - Sistema de Indicadores y Estándares de Desarrollo Urbano | `live` | `ine_siedu_xlsm_cinco_mediciones_2018_2022` | `fresh (0.02h / 8760h)` | `partial` | 6701 | `ok` | indicadores_urbanos_siedu has intentionally partial urban coverage |
| `partidos_politicos` | Cámara de Diputadas y Diputados (datos abiertos) + SERVEL | `live` | `WSComun.asmx/retornarPartidosPoliticos + servel.cl/partidos-politicos (estado legal)` | `fresh (0.02h / 87600h)` | `full` | 37 | `ok` | estado_legal poblado (vía SERVEL) en 16/37 partidos |
| `perfil_territorial_comunal` | chile-hub | `live` | `derived_from_validated_chile_hub_layers` | `fresh (0.0h / 1080h)` | `full` | 346 | `ok` | none |
| `permisos_edificacion` | MINVU — Centro de Estudios de Ciudad y Territorio (CEDOC) | `monthly` | `Viviendas en unidades y superficie (m2) por comuna y año, serie desde 2002 (MINVU CEDOC, en base a permisos otorgados por las Direcciones de Obras Municipales e INE).` | `fresh (164.94h / 1080h)` | `not_applicable` | 8650 | `ok` | none |
| `pobreza_comunal` | Observatorio Social — Ministerio de Desarrollo Social y Familia | `live` | `Estimaciones de Pobreza Comunal vía SAE desde encuesta CASEN` | `fresh (0.02h / 175200h)` | `not_applicable` | 690 | `ok` | cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (0.03h / 2160h)` | `full` | 56 | `ok` | none |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `fresh (0.03h / 2160h)` | `full` | 16 | `ok` | none |
| `resultados_educacionales` | Centro de Estudios MINEDUC - Rendimiento 2024 | `live` | `mineduc_rendimiento_2024_rar_agregado_por_comuna` | `fresh (0.02h / 8760h)` | `not_applicable` | 345 | `ok` | none |

## autoridades_electas

- `refreshed_at_utc`: `2026-10-02T16:04:45.845704+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `coverage`: `Cobertura completa: 205/205 filas respecto del baseline esperado.`
- `fields`: `id_autoridad, nombre, cargo, institucion, partido, pacto, distrito_electoral, circunscripcion_senatorial, codigo_comuna, codigo_region, periodo_inicio, periodo_fin, estado_mandato, fuente, url_fuente, fecha_consulta`
- `notes`: v1: diputados (155) + senadores (50). Gobernador_regional/alcalde viven en el dataset segregado autoridades_locales (licencia CC-BY-SA).; distrito_electoral vía Scrapling: 0/155 diputados.; codigo_region/periodo de senadores: 50/50 poblados desde senado.cl (REGION/PERIODOS).; RUT (Cámara) y email/teléfono (Senado) descartados (línea roja de datos personales).
- `warnings`: none

## calidad_aire

- `refreshed_at_utc`: `2026-10-02T16:04:38.996690+00:00`
- `freshness`: `fresh (0.01h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, id_estacion, nombre_estacion, codigo_region, codigo_comuna, nombre_comuna, latitud, longitud, codigo_contaminante, nombre_contaminante, unidad, valor_promedio_diario, valor_max_horario, horas_validas, estado_dato, fuente, url_fuente, fecha_fuente`
- `notes`: inventario: 122 estaciones en el listado; 122 con filas emitidas; 714 filas diarias nuevas desde 'sinca_listadomapa_20261002T160438Z.json'; historial: fusionado con staging existente
- `warnings`: cobertura SINCA: 66/346 comunas (19.1%) — parcial por diseño; solo comunas con estación

## censo_comunal

- `refreshed_at_utc`: `2026-10-02T16:03:21.083119+00:00`
- `freshness`: `fresh (0.03h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, poblacion_censada, hombres, mujeres, razon_hombre_mujer, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas`
- `notes`: age_bands_derived_from_quinquennial_groups
- `warnings`: none

## censo_hogares_viviendas

- `refreshed_at_utc`: `2026-10-02T16:03:27.845293+00:00`
- `freshness`: `fresh (0.03h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, viviendas_censadas, viviendas_particulares_ocupadas, viviendas_particulares_desocupadas, viviendas_colectivas, hogares_censados, promedio_personas_hogar`
- `warnings`: none

## comunas

- `refreshed_at_utc`: `2026-10-02T16:03:12.617795+00:00`
- `freshness`: `fresh (0.03h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## comunas_enriquecidas

- `refreshed_at_utc`: `2026-10-02T16:03:12.617795+00:00`
- `freshness`: `fresh (0.03h / 2160h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## consumo_electrico_comunal

- `refreshed_at_utc`: `2026-10-02T16:04:02.897030+00:00`
- `freshness`: `fresh (0.02h / 17520h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, tipo_cliente, consumo_kwh, numero_clientes, fuente, url_fuente, fecha_fuente`
- `notes`: fallback: usando datos de muestra (HTTPConnectionPool(host='datos.energiaabierta.cl', port=80): Max retries exceeded with url: /dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/ (Caused by NameResolutionError("HTTPConnection(host='datos.energiaabierta.cl', port=80): Failed to resolve 'datos.energiaabierta.cl' ([Errno -2] Name or service not known)"))). fuente confirmada caída de forma permanente (2026-07-07): CNE migró energiaabierta.cl a WordPress y decomisionó el catálogo Junar; no existe archivo ni endpoint de reemplazo. Ver AGENTS.md §6.
- `warnings`: tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.

## distritos_electorales

- `refreshed_at_utc`: `2026-10-02T16:03:29.664262+00:00`
- `freshness`: `fresh (0.03h / 87600h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_comuna, nombre_comuna, distrito_electoral, circunscripcion_senatorial`
- `warnings`: none

## empresas

- `refreshed_at_utc`: `2026-10-02T16:03:54.524104+00:00`
- `freshness`: `fresh (0.02h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rut, razon_social, codigo_sociedad, tipo_actuacion, capital, fecha_actuacion, fecha_registro, fecha_aprobacion_sii, anio, mes, comuna_tributaria, region_tributaria, comuna_social, region_social`
- `notes`: filas descartadas por RUT centinela ['0']: 0; Solo incluye empresas constituidas bajo el Regimen Simplificado (Ley 20.659) desde mayo 2013.; No contiene dirección postal (solo comuna y región).; No contiene actividad económica (giro).; No refleja cese de actividades ni modificaciones posteriores.; Los codigos de region usan el formato numerico del SII (1-15), distinto del codigo CUT (01-16). Verificar antes de cruzar con DPA.
- `warnings`: RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.

## establecimientos_educacionales

- `refreshed_at_utc`: `2026-10-02T16:03:36.622414+00:00`
- `freshness`: `fresh (0.02h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `rbd, dv_rbd, nombre_establecimiento, codigo_region, codigo_comuna, dependencia_administrativa, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## establecimientos_salud

- `refreshed_at_utc`: `2026-10-02T16:03:29.496938+00:00`
- `freshness`: `fresh (0.03h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_establecimiento, nombre_establecimiento, tipo_establecimiento, dependencia_administrativa, nivel_atencion, codigo_region, nombre_region, codigo_comuna, nombre_comuna, tiene_servicio_urgencia, tipo_urgencia, latitud, longitud, estado_funcionamiento`
- `warnings`: none

## estadisticas_vitales

- `refreshed_at_utc`: `2026-10-02T16:04:27.547950+00:00`
- `freshness`: `fresh (0.01h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_region, codigo_comuna, nombre_comuna, evento, sexo, cantidad, estado_dato, fuente, url_fuente, fecha_fuente`
- `notes`: fetch incremental: 1 de 15 anuarios (faltantes + año más reciente 2023); 2023: 2076 filas desde 'Anuario de estadísticas vitales 2023, nacimientos y defunciones' (hoja 122-04; TOTAL país: 174057 nacimientos, 122218 defunciones)
- `warnings`: none

## finanzas_municipales

- `refreshed_at_utc`: `2026-09-01T03:04:24.987281+00:00`
- `freshness`: `fresh (757.01h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, nombre_comuna, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion`
- `notes`: live: Playwright configurando filtros SINIM; live: descargando XML Spreadsheet; live: parseando XML Spreadsheet; live: 345 municipios extraídos (snapshot: sinim_finanzas_municipales_20260901T030218Z.xlsx)
- `warnings`: none

## indicadores

- `refreshed_at_utc`: `2026-10-02T16:03:20.413412+00:00`
- `freshness`: `fresh (0.03h / 72h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `fecha, codigo_indicador, valor`
- `notes`: published_backfills_used_for_codes: ipc; ine_override_used_for_pairs: ipc/2026
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `warnings`: indicadores live refresh reused last published artifact for missing codes: ipc

## indicadores_urbanos_siedu

- `refreshed_at_utc`: `2026-10-02T16:03:49.430283+00:00`
- `freshness`: `fresh (0.02h / 8760h)`
- `coverage`: `Comunas urbanas incluidas por SIEDU, no las 346 comunas del país.`
- `fields`: `anio, codigo_comuna, codigo_indicador, nombre_indicador, categoria, valor, unidad, fuente_original, cobertura_tipo`
- `notes`: partial_urban_coverage_expected; deduplicado_anno_mas_reciente_por_indicador_comuna; 5_mediciones_2018_2022_consolidadas; live_data: xlsm parseado, 6701 registros, 117 comunas, 68 indicadores
- `warnings`: indicadores_urbanos_siedu has intentionally partial urban coverage

## partidos_politicos

- `refreshed_at_utc`: `2026-10-02T16:04:05.049135+00:00`
- `freshness`: `fresh (0.02h / 87600h)`
- `coverage`: `Cobertura completa: 37/36 filas respecto del baseline esperado.`
- `fields`: `id_partido, nombre, sigla, estado_legal, fecha_constitucion, ambito, fuente, url_fuente, fecha_consulta`
- `notes`: Roster de partidos de la Cámara (incluye vigentes e históricos).; estado_legal/fecha_constitucion vía SERVEL: 16/37 matcheados por nombre.; ambito (nacional/regional) no provisto por ninguna fuente encontrada (nullable).
- `warnings`: estado_legal poblado (vía SERVEL) en 16/37 partidos

## perfil_territorial_comunal

- `refreshed_at_utc`: `2026-10-02T16:05:00.194746+00:00`
- `freshness`: `fresh (0.0h / 1080h)`
- `coverage`: `Cobertura completa: 346/346 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada, poblacion_censada, poblacion_hombres, poblacion_mujeres, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas, viviendas_censadas, hogares_censados, promedio_personas_por_hogar, establecimientos_salud_total, establecimientos_educacionales_total, distrito_electoral, circunscripcion_senatorial, anio_finanzas, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion, anio_resultados_educacionales, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados, indicadores_siedu_total, valor_promedio_siedu, crecimiento_natural_ultimo_anio, anio_estadisticas_vitales, viviendas_autorizadas_ultimo_anio, superficie_autorizada_m2_ultimo_anio, anio_permisos_edificacion, mp25_promedio_ultimo_anio, anio_calidad_aire`
- `notes`: derived_dataset; upstreams: comunas,censo_comunal,censo_hogares_viviendas,establecimientos_salud,establecimientos_educacionales,distritos_electorales,finanzas_municipales,resultados_educacionales,indicadores_urbanos_siedu
- `warnings`: none

## permisos_edificacion

- `refreshed_at_utc`: `2026-09-25T19:08:42+00:00`
- `freshness`: `fresh (164.94h / 1080h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_region, codigo_comuna, nombre_comuna, unidades_total, superficie_m2_total, unidades_casas, superficie_m2_casas, unidades_departamentos, superficie_m2_departamentos, estado_dato, fuente, url_fuente, fecha_fuente`
- `notes`: descubrimiento: repositorio-biblionumber; descarga falló, usando snapshot versionado minvu_permisos_edificacion_anual_20260925T190842Z.xlsx (Failed to perform, curl: (35) BoringSSL SSL_connect: Connection closed abruptly (SSL_ERROR_SYSCALL; error queue empty) in connection to catalogo.minvu.cl:443. See https://curl.se/libcurl/c/libcurl-errors.html first for more details.); 8650 filas desde 'minvu_permisos_edificacion_anual_20260925T190842Z.xlsx' (hojas: número_total, m2_total, número_departamentos, m2_departamentos, número_casas, m2_casas; años provisionales: [2024, 2025, 2026])
- `warnings`: none

## pobreza_comunal

- `refreshed_at_utc`: `2026-10-02T16:03:55.590063+00:00`
- `freshness`: `fresh (0.02h / 175200h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, dimension, tasa, limite_inferior, limite_superior, metodologia, fuente, url_fuente, fecha_fuente`
- `notes`: ingresos: 345 comunas con estimación desde URL oficial; multidimensional: 345 comunas con estimación desde URL oficial
- `warnings`: cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación

## provincias

- `refreshed_at_utc`: `2026-10-02T16:03:12.617795+00:00`
- `freshness`: `fresh (0.03h / 2160h)`
- `coverage`: `Cobertura completa: 56/56 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## regiones

- `refreshed_at_utc`: `2026-10-02T16:03:12.617795+00:00`
- `freshness`: `fresh (0.03h / 2160h)`
- `coverage`: `Cobertura completa: 16/16 filas respecto del baseline esperado.`
- `fields`: `codigo_region, nombre_region`
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1
- `warnings`: none

## resultados_educacionales

- `refreshed_at_utc`: `2026-10-02T16:03:47.195662+00:00`
- `freshness`: `fresh (0.02h / 8760h)`
- `coverage`: `Sin baseline de cobertura por cardinalidad para esta capa.`
- `fields`: `anio, codigo_comuna, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados`
- `notes`: privacy_safe_comuna_year_aggregation; sit_fin_r_Y=retirado T=trasladado asistencia_only_for_P_R_students; source_file: mineduc_rendimiento_2024.rar, comunas_agregadas: 345
- `warnings`: none
