# chile-hub dataset catalog

- `generated_at_utc`: `2026-07-06T15:21:31.259458+00:00`
- `dataset_count`: `19`

| Dataset | Source | Mode | Freshness | Reuse | Records | Confidence | Join Keys | Validation |
| :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `regiones` | BCN ArcGIS | `live` | `fresh (0.17h / 2160h)` | `open-attribution (CC BY)` | 16 | `Tier B` | `codigo_region` | `ok` |
| `provincias` | BCN ArcGIS | `live` | `fresh (0.17h / 2160h)` | `open-attribution (CC BY)` | 56 | `Tier B` | `codigo_provincia, codigo_region` | `ok` |
| `comunas` | BCN ArcGIS | `live` | `fresh (0.17h / 2160h)` | `open-attribution (CC BY)` | 346 | `Tier B` | `codigo_comuna, codigo_region` | `ok` |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `fresh (0.17h / 2160h)` | `open-attribution (CC BY)` | 346 | `Tier B` | `codigo_comuna` | `ok` |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `fresh (0.15h / 72h)` | `open-attribution (Reproducción libre con citación (BCCh / INE))` | 454 | `Tier A/B` | `fecha, codigo_indicador` | `ok` |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `fresh (0.15h / 87600h)` | `open-attribution (CC BY 4.0)` | 346 | `Tier A` | `codigo_comuna, codigo_region` | `ok` |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `fresh (0.15h / 1080h)` | `open-attribution (CC0)` | 5707 | `Tier A` | `codigo_establecimiento, codigo_comuna` | `ok` |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `fresh (0.15h / 8760h)` | `open-attribution (CC-BY-3.0)` | 12898 | `Tier A` | `codigo_comuna` | `ok` |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `fresh (0.15h / 87600h)` | `open-attribution (CC BY 4.0)` | 346 | `Tier A` | `codigo_comuna, codigo_region` | `ok` |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `fresh (0.15h / 87600h)` | `open-attribution (CC0)` | 346 | `Tier A` | `codigo_comuna` | `ok` |
| `finanzas_municipales` | SINIM - SUBDERE | `fallback` | `fresh (0.15h / 8760h)` | `public-api-review-terms (Datos públicos municipales; términos de reutilización sujetos a revisión)` | 3 | `Tier B` | `anio, codigo_comuna` | `ok` |
| `resultados_educacionales` | Centro de Estudios MINEDUC - Rendimiento 2024 | `live` | `fresh (0.15h / 8760h)` | `open-attribution (CC-BY-3.0)` | 345 | `Tier B` | `anio, codigo_comuna` | `ok` |
| `indicadores_urbanos_siedu` | INE - Sistema de Indicadores y Estándares de Desarrollo Urbano | `live` | `fresh (0.15h / 8760h)` | `open-attribution (Licencia de Datos Abiertos INE)` | 6701 | `Tier B` | `anio, codigo_comuna, codigo_indicador` | `ok` |
| `perfil_territorial_comunal` | chile-hub | `fallback` | `fresh (0.0h / 1080h)` | `open-attribution (Derivada de fuentes abiertas con atribución)` | 346 | `Tier B` | `codigo_comuna` | `ok` |
| `empresas` | Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES) | `live` | `fresh (0.13h / 1080h)` | `open-attribution (CC-BY)` | 1572116 | `Tier B` | `rut` | `ok` |
| `pobreza_comunal` | Observatorio Social — Ministerio de Desarrollo Social y Familia | `fallback` | `fresh (0.13h / 175200h)` | `open-attribution (Datos abiertos MDS)` | 3 | `Tier A` | `codigo_comuna, codigo_region` | `ok` |
| `consumo_electrico_comunal` | CNE — Energía Abierta | `fallback` | `fresh (0.13h / 17520h)` | `open-attribution (CC BY)` | 3 | `Tier A` | `codigo_comuna, codigo_region` | `ok` |
| `partidos_politicos` | Cámara de Diputadas y Diputados (datos abiertos) + SERVEL | `live` | `fresh (0.13h / 87600h)` | `open-attribution (CC-BY)` | 36 | `Tier B` | `id_partido` | `ok` |
| `autoridades_electas` | Cámara de Diputadas y Diputados + Senado de Chile | `live` | `fresh (0.13h / 87600h)` | `open-attribution (CC-BY)` | 205 | `Tier B` | `distrito_electoral, circunscripcion_senatorial, codigo_region` | `ok` |

## regiones

Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/regiones.md`
- `freshness`: `fresh (0.17h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Derivada de datos abiertos BCN reutilizables con atribucion."}`
- `fields`: `codigo_region, nombre_region`
- `join_keys`: `codigo_region`
- `outputs`: `{"parquet": "data/normalized/regiones.parquet", "json": "data/normalized/regiones.json", "duckdb_table": "regiones", "sqlite_table": "regiones", "excel_sheet": "Regiones"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('regiones')", "duckdb": "SELECT *\nFROM 'data/normalized/regiones.parquet'\nORDER BY codigo_region;", "cli": "chile-hub show regiones"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## provincias

Capa derivada de provincias para cruces intermedios entre region y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/provincias.md`
- `freshness`: `fresh (0.17h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Derivada de datos abiertos BCN reutilizables con atribucion."}`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `join_keys`: `codigo_provincia, codigo_region`
- `outputs`: `{"parquet": "data/normalized/provincias.parquet", "json": "data/normalized/provincias.json", "duckdb_table": "provincias", "sqlite_table": "provincias", "excel_sheet": "Provincias"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('provincias')", "duckdb": "SELECT *\nFROM 'data/normalized/provincias.parquet'\nWHERE codigo_region = '13';", "cli": "chile-hub show provincias"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## comunas

Base territorial normalizada para cruces por region, provincia y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/comunas.md`
- `freshness`: `fresh (0.17h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Fuente operativa BCN dentro de su superficie de datos abiertos; atribucion requerida."}`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/comunas.parquet", "json": "data/normalized/comunas.json", "duckdb_table": "comunas", "sqlite_table": "comunas", "excel_sheet": "Comunas y Regiones"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('comunas')", "duckdb": "SELECT codigo_comuna, nombre_comuna, nombre_region\nFROM 'data/normalized/comunas.parquet'\nLIMIT 10;", "cli": "chile-hub path comunas --output parquet"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## comunas_enriquecidas

Comunas con coordenadas de cabecera y poblacion estimada INE, listas para analisis territorial sin joins adicionales.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/comunas_enriquecidas.md`
- `freshness`: `fresh (0.17h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Derivada de datos abiertos BCN con coordenadas e informacion INE."}`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `join_keys`: `codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/comunas.parquet", "json": "data/normalized/comunas.json", "duckdb_table": "comunas_enriquecidas", "sqlite_table": "comunas_enriquecidas", "excel_sheet": "Comunas y Regiones"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('comunas_enriquecidas')", "duckdb": "SELECT codigo_comuna, nombre_comuna, latitud_cabecera, longitud_cabecera, poblacion_estimada\nFROM 'data/normalized/comunas.parquet'\nORDER BY poblacion_estimada DESC LIMIT 10;", "cli": "chile-hub show comunas_enriquecidas"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## indicadores

Serie de indicadores economicos diarios de referencia para analisis y software.

- `source_url`: https://mindicador.cl/api
- `documentation`: `docs/datasets/indicadores.md`
- `freshness`: `fresh (0.15h / 72h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "Reproducción libre con citación (BCCh / INE)", "license_url": "https://www.bcentral.cl/web/banco-central/terminos-y-condiciones", "attribution_required": true, "redistribution_ok": true, "summary": "Datos del Banco Central de Chile (BCCh) e INE. Libre reproducción con citación. Acceso vía mindicador.cl (API pública de la comunidad)."}`
- `fields`: `fecha, codigo_indicador, valor`
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `indicator_delivery`: `{"dolar": "live", "euro": "live", "ipc": "published_backfill", "uf": "live", "utm": "live"}`
- `join_keys`: `fecha, codigo_indicador`
- `outputs`: `{"parquet": "data/normalized/indicadores.parquet", "json": "data/normalized/indicadores_hoy.json", "duckdb_table": "indicadores", "sqlite_table": "indicadores", "excel_sheet": "Indicadores Diarios"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('indicadores')", "duckdb": "SELECT *\nFROM 'data/normalized/indicadores.parquet'\nORDER BY fecha DESC, codigo_indicador;", "cli": "chile-hub show indicadores"}`
- `warnings`: indicadores live refresh reused last published artifact for missing codes: ipc
- `notes`: published_backfills_used_for_codes: ipc

## censo_comunal

Perfil demografico comunal del Censo 2024 con sexo y grandes grupos de edad.

- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx
- `documentation`: `docs/datasets/censo_comunal.md`
- `freshness`: `fresh (0.15h / 87600h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY 4.0", "license_url": "https://www.ine.gob.cl/terminos-de-uso", "attribution_required": true, "redistribution_ok": true, "summary": "Resultados oficiales del Censo 2024 publicados por el INE."}`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, poblacion_censada, hombres, mujeres, razon_hombre_mujer, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/censo_comunal.parquet", "json": "data/normalized/censo_comunal.json", "duckdb_table": "censo_comunal", "sqlite_table": "censo_comunal", "excel_sheet": "Censo Comunal"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('censo_comunal')", "duckdb": "SELECT * FROM 'data/normalized/censo_comunal.parquet' ORDER BY poblacion_censada DESC;", "cli": "chile-hub show censo_comunal"}`
- `warnings`: none
- `notes`: age_bands_derived_from_quinquennial_groups

## establecimientos_salud

Directorio vigente de establecimientos de salud con tipo, dependencia, urgencia y ubicacion.

- `source_url`: https://datos.gob.cl/dataset/3bf4cf7c-f638-4735-9a01-f65faae4beca/resource/2c44d782-3365-44e3-aefb-2c8b8363a1bc/download/establecimientos_20260630.csv
- `documentation`: `docs/datasets/establecimientos_salud.md`
- `freshness`: `fresh (0.15h / 1080h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC0", "license_url": "http://www.opendefinition.org/licenses/cc-zero", "attribution_required": false, "redistribution_ok": true, "summary": "Directorio oficial MINSAL publicado en datos.gob.cl bajo CC0."}`
- `fields`: `codigo_establecimiento, nombre_establecimiento, tipo_establecimiento, dependencia_administrativa, nivel_atencion, codigo_region, nombre_region, codigo_comuna, nombre_comuna, tiene_servicio_urgencia, tipo_urgencia, latitud, longitud, estado_funcionamiento`
- `join_keys`: `codigo_establecimiento, codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/establecimientos_salud.parquet", "json": "data/normalized/establecimientos_salud.json", "duckdb_table": "establecimientos_salud", "sqlite_table": "establecimientos_salud", "excel_sheet": "Establecimientos Salud"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('establecimientos_salud')", "duckdb": "SELECT codigo_comuna, count(*) FROM 'data/normalized/establecimientos_salud.parquet' GROUP BY 1;", "cli": "chile-hub show establecimientos_salud"}`
- `warnings`: none

## establecimientos_educacionales

Directorio oficial del Ministerio de Educación (MINEDUC) con Rol Base de Datos (RBD), ubicación y dependencia administrativa.

- `source_url`: https://datosabiertos.mineduc.cl/wp-content/uploads/2025/11/Directorio-Oficial-EE-2025.rar
- `documentation`: `docs/datasets/establecimientos_educacionales.md`
- `freshness`: `fresh (0.15h / 8760h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC-BY-3.0", "license_url": "https://creativecommons.org/licenses/by/3.0/cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Directorio oficial MINEDUC publicado por el Centro de Estudios del Ministerio de Educación de Chile bajo licencia CC BY."}`
- `fields`: `rbd, dv_rbd, nombre_establecimiento, codigo_region, codigo_comuna, dependencia_administrativa, latitud, longitud, estado_funcionamiento`
- `join_keys`: `codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/establecimientos_educacionales.parquet", "json": "data/normalized/establecimientos_educacionales.json", "duckdb_table": "establecimientos_educacionales", "sqlite_table": "establecimientos_educacionales", "excel_sheet": "Establecimientos Educacionales"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('establecimientos_educacionales')", "duckdb": "SELECT nombre_establecimiento, dependencia_administrativa FROM 'data/normalized/establecimientos_educacionales.parquet' LIMIT 10;", "cli": "chile-hub show establecimientos_educacionales"}`
- `warnings`: none

## censo_hogares_viviendas

Viviendas y hogares censados por comuna, ocupacion y tamano medio del hogar.

- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/V1_Viviendas-y-hogares-censados.xlsx
- `documentation`: `docs/datasets/censo_hogares_viviendas.md`
- `freshness`: `fresh (0.15h / 87600h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY 4.0", "license_url": "https://www.ine.gob.cl/terminos-de-uso", "attribution_required": true, "redistribution_ok": true, "summary": "Resultados oficiales del Censo 2024 publicados por el INE."}`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, viviendas_censadas, viviendas_particulares_ocupadas, viviendas_particulares_desocupadas, viviendas_colectivas, hogares_censados, promedio_personas_hogar`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/censo_hogares_viviendas.parquet", "json": "data/normalized/censo_hogares_viviendas.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('censo_hogares_viviendas')", "duckdb": "SELECT * FROM 'data/normalized/censo_hogares_viviendas.parquet';", "cli": "chile-hub show censo_hogares_viviendas"}`
- `warnings`: none

## distritos_electorales

Asociación de comunas a distritos electorales (diputados) y circunscripciones senatoriales.

- `source_url`: https://www.bcn.cl/siit/observatorio/ley20840
- `documentation`: `docs/datasets/distritos_electorales.md`
- `freshness`: `fresh (0.15h / 87600h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC0", "license_url": "http://www.opendefinition.org/licenses/cc-zero", "attribution_required": false, "redistribution_ok": true, "summary": "Asociación comunal a distritos y circunscripciones electorales basada en Ley N° 20.840."}`
- `fields`: `codigo_comuna, nombre_comuna, distrito_electoral, circunscripcion_senatorial`
- `join_keys`: `codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/distritos_electorales.parquet", "json": "data/normalized/distritos_electorales.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('distritos_electorales')", "duckdb": "SELECT * FROM 'data/normalized/distritos_electorales.parquet';", "cli": "chile-hub show distritos_electorales"}`
- `warnings`: none

## finanzas_municipales

Indicadores financieros municipales anuales desde SINIM/SUBDERE. CAPA PARCIAL/CANDIDATO: 3 de 346 comunas (0.9%). Usar con precaución; no representa cobertura nacional.

- `source_url`: https://datos.sinim.gov.cl/datos_municipales.php
- `documentation`: `docs/datasets/finanzas_municipales.md`
- `freshness`: `fresh (0.15h / 8760h)`
- `reuse_policy`: `{"status": "public-api-review-terms", "license": "Datos públicos municipales; términos de reutilización sujetos a revisión", "license_url": "https://datos.sinim.gov.cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Información municipal pública publicada por SINIM/SUBDERE; citar fuente oficial."}`
- `fields`: `anio, codigo_comuna, nombre_comuna, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion`
- `join_keys`: `anio, codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/finanzas_municipales.parquet", "json": "data/normalized/finanzas_municipales.json", "duckdb_table": "finanzas_municipales", "sqlite_table": "finanzas_municipales", "excel_sheet": "Finanzas Municipales"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('finanzas_municipales')", "duckdb": "SELECT * FROM 'data/normalized/finanzas_municipales.parquet' WHERE codigo_comuna = '13101';", "cli": "chile-hub show finanzas_municipales"}`
- `warnings`: finanzas_municipales source_mode is fallback; review before publication
- `notes`: official_landing_snapshot_saved; fallback_curated_rows_used: official_landing_fetch_failed

## resultados_educacionales

Resultados educacionales agregados por comuna y año, sin registros personales.

- `source_url`: https://datosabiertos.mineduc.cl/wp-content/uploads/2025/04/Rendimiento_2024.rar
- `documentation`: `docs/datasets/resultados_educacionales.md`
- `freshness`: `fresh (0.15h / 8760h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC-BY-3.0", "license_url": "https://creativecommons.org/licenses/by/3.0/cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Datos agregados desde publicaciones del Centro de Estudios MINEDUC; citar fuente oficial."}`
- `fields`: `anio, codigo_comuna, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados`
- `join_keys`: `anio, codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/resultados_educacionales.parquet", "json": "data/normalized/resultados_educacionales.json", "duckdb_table": "resultados_educacionales", "sqlite_table": "resultados_educacionales", "excel_sheet": "Resultados Educacionales"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('resultados_educacionales')", "duckdb": "SELECT anio, codigo_comuna, matricula_total FROM 'data/normalized/resultados_educacionales.parquet';", "cli": "chile-hub show resultados_educacionales"}`
- `warnings`: none
- `notes`: privacy_safe_comuna_year_aggregation; sit_fin_r_Y=retirado T=trasladado asistencia_only_for_P_R_students; source_file: mineduc_rendimiento_2024.rar, comunas_agregadas: 345

## indicadores_urbanos_siedu

Indicadores urbanos SIEDU en formato largo con cobertura comunal parcial esperada.

- `source_url`: https://www.ine.gob.cl/docs/default-source/sistema-de-indicadores-y-estandares-de-desarrollo-urbano/indicadores/actualizaci%C3%B3n-2019/matriz-siedu-publicacion.xlsm
- `documentation`: `docs/datasets/indicadores_urbanos_siedu.md`
- `freshness`: `fresh (0.15h / 8760h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "Licencia de Datos Abiertos INE", "license_url": "https://www.ine.gob.cl/terminos-de-uso", "attribution_required": true, "redistribution_ok": true, "summary": "Indicadores urbanos SIEDU publicados por INE para comunas urbanas seleccionadas."}`
- `fields`: `anio, codigo_comuna, codigo_indicador, nombre_indicador, categoria, valor, unidad, fuente_original, cobertura_tipo`
- `join_keys`: `anio, codigo_comuna, codigo_indicador`
- `outputs`: `{"parquet": "data/normalized/indicadores_urbanos_siedu.parquet", "json": "data/normalized/indicadores_urbanos_siedu.json", "duckdb_table": "indicadores_urbanos_siedu", "sqlite_table": "indicadores_urbanos_siedu", "excel_sheet": "SIEDU"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('indicadores_urbanos_siedu')", "duckdb": "SELECT * FROM 'data/normalized/indicadores_urbanos_siedu.parquet' WHERE codigo_indicador = 'siedu_acceso_areas_verdes';", "cli": "chile-hub show indicadores_urbanos_siedu"}`
- `warnings`: indicadores_urbanos_siedu has intentionally partial urban coverage
- `notes`: partial_urban_coverage_expected; deduplicado_anno_mas_reciente_por_indicador_comuna; 5_mediciones_2018_2022_consolidadas; live_data: xlsm parseado, 6701 registros, 117 comunas, 68 indicadores

## perfil_territorial_comunal

Perfil comunal curado que consolida DPA, censo, salud, educación, finanzas, SIEDU y distritos.

- `source_url`: https://github.com/cortega26/chile-hub
- `documentation`: `docs/datasets/perfil_territorial_comunal.md`
- `freshness`: `fresh (0.0h / 1080h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "Derivada de fuentes abiertas con atribución", "license_url": "https://github.com/cortega26/chile-hub", "attribution_required": true, "redistribution_ok": true, "summary": "Capa derivada a partir de datasets validados de chile-hub."}`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada, poblacion_censada, poblacion_hombres, poblacion_mujeres, poblacion_0_14, poblacion_15_29, poblacion_30_44, poblacion_45_64, poblacion_65_mas, viviendas_censadas, hogares_censados, promedio_personas_por_hogar, establecimientos_salud_total, establecimientos_educacionales_total, distrito_electoral, circunscripcion_senatorial, anio_finanzas, ingresos_totales, gastos_totales, ingresos_propios_permanentes, fondo_comun_municipal, gasto_personal, gasto_inversion, anio_resultados_educacionales, matricula_total, asistencia_promedio, tasa_aprobacion, tasa_reprobacion, tasa_retiro, establecimientos_reportados, indicadores_siedu_total, valor_promedio_siedu`
- `join_keys`: `codigo_comuna`
- `outputs`: `{"parquet": "data/normalized/perfil_territorial_comunal.parquet", "json": "data/normalized/perfil_territorial_comunal.json", "duckdb_table": "perfil_territorial_comunal", "sqlite_table": "perfil_territorial_comunal", "excel_sheet": "Perfil Territorial"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\nhub = ChileHub()\ndf = hub.load_polars('perfil_territorial_comunal')", "duckdb": "SELECT codigo_comuna, nombre_comuna, establecimientos_salud_total FROM 'data/normalized/perfil_territorial_comunal.parquet';", "cli": "chile-hub show perfil_territorial_comunal"}`
- `warnings`: none
- `notes`: derived_dataset; upstreams: comunas,censo_comunal,censo_hogares_viviendas,establecimientos_salud,establecimientos_educacionales,distritos_electorales,finanzas_municipales,resultados_educacionales,indicadores_urbanos_siedu

## empresas

Registro de Empresas y Sociedades (RES) con RUT, razon social, tipo societario, capital, fecha de constitucion y comuna de domicilio.

- `source_url`: https://datos.gob.cl/dataset/registro-de-empresas-y-sociedades
- `documentation`: `docs/datasets/empresas.md`
- `freshness`: `fresh (0.13h / 1080h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC-BY", "license_url": "https://creativecommons.org/licenses/by/3.0/cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Registro de Empresas y Sociedades (RES) del Ministerio de Economia, publicado en datos.gob.cl bajo CC-BY. Solo incluye constituciones bajo Ley 20.659 (regimen simplificado) desde 2013."}`
- `fields`: `rut, razon_social, codigo_sociedad, tipo_actuacion, capital, fecha_actuacion, fecha_registro, fecha_aprobacion_sii, anio, mes, comuna_tributaria, region_tributaria, comuna_social, region_social`
- `join_keys`: `rut`
- `outputs`: `{"parquet": "data/normalized/empresas.parquet", "duckdb_table": "empresas", "excel_sheet": "Empresas RES"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('empresas')\n# Empresas por comuna\ndf.group_by('comuna_tributaria').len().sort('len', descending=True)", "duckdb": "SELECT comuna_tributaria, count(*) AS n\nFROM 'data/normalized/empresas.parquet'\nGROUP BY 1 ORDER BY n DESC LIMIT 10;", "cli": "chile-hub show empresas"}`
- `warnings`: found 1 RUTs with invalid format; unknown sociedad codes (new types?): ['SpA']; RES solo cubre constituciones bajo Ley 20.659 (regimen simplificado). No incluye empresas del regimen tradicional (Diario Oficial) ni empresas anteriores a mayo 2013.
- `notes`: Solo incluye empresas constituidas bajo el Regimen Simplificado (Ley 20.659) desde mayo 2013.; No contiene dirección postal (solo comuna y región).; No contiene actividad económica (giro).; No refleja cese de actividades ni modificaciones posteriores.; Los codigos de region usan el formato numerico del SII (1-15), distinto del codigo CUT (01-16). Verificar antes de cruzar con DPA.

## pobreza_comunal

Estimaciones de pobreza comunal por ingresos y multidimensional derivadas de la encuesta CASEN mediante metodología SAE (Estimación de Áreas Pequeñas). Incluye tasa, límite inferior y superior del intervalo de confianza por comuna, año y dimensión.

- `source_url`: https://observatorio.ministeriodesarrollosocial.gob.cl/storage/docs/pobreza-comunal/2022/Estimaciones_Tasa_Pobreza_Ingresos_Comunas_2022.xlsx
- `documentation`: `docs/datasets/pobreza_comunal.md`
- `freshness`: `fresh (0.13h / 175200h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "Datos abiertos MDS", "license_url": "https://observatorio.ministeriodesarrollosocial.gob.cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Estimaciones de pobreza comunal publicadas por el Observatorio Social del MDS. Atribución requerida."}`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, dimension, tasa, limite_inferior, limite_superior, metodologia, fuente, url_fuente, fecha_fuente`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/pobreza_comunal.parquet", "json": "data/normalized/pobreza_comunal.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('pobreza_comunal')\n# Filtrar pobreza por ingresos 2022\npobreza_2022 = df.filter(pl.col('anio') == 2022, pl.col('dimension') == 'ingresos')", "duckdb": "SELECT codigo_comuna, nombre_comuna, tasa, limite_inferior, limite_superior\nFROM 'data/normalized/pobreza_comunal.parquet'\nWHERE anio = 2022 AND dimension = 'ingresos'\nORDER BY tasa DESC;", "cli": "chile-hub show pobreza_comunal"}`
- `warnings`: cobertura SAE: 2/346 comunas (0.6%) — parcial por diseño; comunas sin muestra no tienen estimación; pobreza_comunal source_mode is fallback; usando datos de muestra mínima.
- `notes`: ingresos: 0 comunas con estimación desde URL oficial; multidimensional: 0 comunas con estimación desde URL oficial

## consumo_electrico_comunal

Consumo eléctrico anual por comuna y tipo de cliente (Residencial, Comercial, Industrial, Agrícola, Alumbrado Público, Otros), publicado por la Comisión Nacional de Energía (CNE) en el portal Energía Abierta.

- `source_url`: http://datos.energiaabierta.cl/dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/
- `documentation`: `docs/datasets/consumo_electrico_comunal.md`
- `freshness`: `fresh (0.13h / 17520h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "http://energiaabierta.cl/", "attribution_required": true, "redistribution_ok": true, "summary": "Consumo eléctrico anual por comuna publicado por la CNE en Energía Abierta. Atribución requerida."}`
- `fields`: `codigo_region, codigo_comuna, nombre_comuna, anio, tipo_cliente, consumo_kwh, numero_clientes, fuente, url_fuente, fecha_fuente`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/consumo_electrico_comunal.parquet", "json": "data/normalized/consumo_electrico_comunal.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('consumo_electrico_comunal')\n# Consumo residencial por comuna\nresidencial = df.filter(pl.col('tipo_cliente') == 'Residencial')", "duckdb": "SELECT codigo_comuna, nombre_comuna, tipo_cliente, consumo_kwh\nFROM 'data/normalized/consumo_electrico_comunal.parquet'\nWHERE tipo_cliente = 'Residencial'\nORDER BY consumo_kwh DESC;", "cli": "chile-hub show consumo_electrico_comunal"}`
- `warnings`: tipos de cliente: ['Comercial', 'Residencial']; años disponibles: [2023]; consumo_electrico_comunal source_mode is fallback; usando datos de muestra mínima.
- `notes`: fallback: usando datos de muestra (HTTPConnectionPool(host='datos.energiaabierta.cl', port=80): Max retries exceeded with url: /dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/ (Caused by NameResolutionError("HTTPConnection(host='datos.energiaabierta.cl', port=80): Failed to resolve 'datos.energiaabierta.cl' ([Errno -2] Name or service not known)")))

## partidos_politicos

Roster de partidos políticos de Chile (Cámara de Diputadas y Diputados), con estado_legal y fecha_constitucion completados por join de nombre contra el registro público de SERVEL.

- `source_url`: https://opendata.camara.cl/camaradiputados/WServices/WSComun.asmx/retornarPartidosPoliticos
- `documentation`: `docs/datasets/partidos_politicos.md`
- `freshness`: `fresh (0.13h / 87600h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC-BY", "license_url": "https://creativecommons.org/licenses/by/4.0/", "attribution_required": true, "redistribution_ok": true, "summary": "Roster institucional de partidos políticos (Cámara de Diputadas y Diputados), enriquecido con estado legal y fecha de constitución desde SERVEL. ambito (nacional/regional) queda nullable: no se encontró esa señal en ninguna fuente."}`
- `fields`: `id_partido, nombre, sigla, estado_legal, fecha_constitucion, ambito, fuente, url_fuente, fecha_consulta`
- `join_keys`: `id_partido`
- `outputs`: `{"parquet": "data/normalized/partidos_politicos.parquet", "json": "data/normalized/partidos_politicos.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars(\"partidos_politicos\")\n# Partidos con estado legal constituido\nconstituidos = df.filter(pl.col(\"estado_legal\") == \"constituido\")", "duckdb": "SELECT nombre, sigla, estado_legal, fecha_constitucion\nFROM 'data/normalized/partidos_politicos.parquet'\nWHERE estado_legal = 'constituido'\nORDER BY fecha_constitucion;", "cli": "chile-hub show partidos_politicos"}`
- `warnings`: estado_legal poblado (vía SERVEL) en 15/36 partidos
- `notes`: Roster de partidos de la Cámara (incluye vigentes e históricos).; estado_legal/fecha_constitucion vía SERVEL: 15/36 matcheados por nombre.; ambito (nacional/regional) no provisto por ninguna fuente encontrada (nullable).

## autoridades_electas

Autoridades electas en ejercicio de Chile (diputados y senadores): partido, distrito electoral/circunscripción senatorial, región y período de mandato.

- `source_url`: https://opendata.camara.cl/camaradiputados/WServices/WSDiputado.asmx/retornarDiputadosPeriodoActual
- `documentation`: `docs/datasets/autoridades_electas.md`
- `freshness`: `fresh (0.13h / 87600h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC-BY", "license_url": "https://creativecommons.org/licenses/by/4.0/", "attribution_required": true, "redistribution_ok": true, "summary": "Autoridades electas en ejercicio (diputados y senadores) desde la Cámara de Diputadas y Diputados y el Senado de Chile. Gobernador_regional y alcalde viven en el dataset segregado autoridades_locales (CC-BY-SA)."}`
- `fields`: `id_autoridad, nombre, cargo, institucion, partido, pacto, distrito_electoral, circunscripcion_senatorial, codigo_comuna, codigo_region, periodo_inicio, periodo_fin, estado_mandato, fuente, url_fuente, fecha_consulta`
- `join_keys`: `distrito_electoral, circunscripcion_senatorial, codigo_region`
- `outputs`: `{"parquet": "data/normalized/autoridades_electas.parquet", "json": "data/normalized/autoridades_electas.json"}`
- `usage_examples`: `{"python": "from chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars(\"autoridades_electas\")\n# Senadores por región\nsenadores = df.filter(pl.col(\"cargo\") == \"senador\")", "duckdb": "SELECT nombre, cargo, partido, codigo_region\nFROM 'data/normalized/autoridades_electas.parquet'\nWHERE cargo = 'senador'\nORDER BY codigo_region;", "cli": "chile-hub show autoridades_electas"}`
- `warnings`: none
- `notes`: v1: diputados (155) + senadores (50). Gobernador_regional/alcalde viven en el dataset segregado autoridades_locales (licencia CC-BY-SA).; distrito_electoral vía Scrapling: 155/155 diputados.; codigo_region/periodo de senadores: 50/50 poblados desde senado.cl (REGION/PERIODOS).; RUT (Cámara) y email/teléfono (Senado) descartados (línea roja de datos personales).
