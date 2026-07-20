# chile-hub provenance report

- `generated_at_utc`: `2026-07-20T17:19:49.387572+00:00`
- `dataset_count`: `19`
- `live_count`: `17`
- `fallback_count`: `2`

| Dataset | Source | Mode | Detail | Refreshed | Freshness | Warnings | Reuse |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-07-20T17:18:28.849680+00:00` | `fresh (0.02h / 2160h)` | 0 | `open-attribution` |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-07-20T17:18:28.849680+00:00` | `fresh (0.02h / 2160h)` | 0 | `open-attribution` |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-07-20T17:18:28.849680+00:00` | `fresh (0.02h / 2160h)` | 0 | `open-attribution` |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-07-20T17:18:28.849680+00:00` | `fresh (0.02h / 2160h)` | 0 | `open-attribution` |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `2026-07-20T17:18:40.211198+00:00` | `fresh (0.02h / 72h)` | 1 | `open-attribution` |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `2026-07-20T17:18:42.726362+00:00` | `fresh (0.02h / 87600h)` | 0 | `open-attribution` |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `2026-07-20T17:18:45.886816+00:00` | `fresh (0.02h / 1080h)` | 0 | `open-attribution` |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `2026-07-20T17:18:48.193411+00:00` | `fresh (0.02h / 8760h)` | 0 | `open-attribution` |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `2026-07-20T17:18:44.159462+00:00` | `fresh (0.02h / 87600h)` | 0 | `open-attribution` |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `2026-07-20T17:18:46.044445+00:00` | `fresh (0.02h / 87600h)` | 0 | `open-attribution` |
| `finanzas_municipales` | SINIM - SUBDERE | `monthly` | `curated_fallback_pending_direct_export` | `2026-07-08T19:27:07.437842+00:00` | `fresh (285.88h / 8760h)` | 0 | `public-api-review-terms` |
| `resultados_educacionales` | Centro de Estudios MINEDUC - Rendimiento 2024 | `live` | `mineduc_rendimiento_2024_rar_agregado_por_comuna` | `2026-07-20T17:18:54.342056+00:00` | `fresh (0.02h / 8760h)` | 0 | `open-attribution` |
| `indicadores_urbanos_siedu` | INE - Sistema de Indicadores y Estándares de Desarrollo Urbano | `live` | `ine_siedu_xlsm_cinco_mediciones_2018_2022` | `2026-07-20T17:18:57.829704+00:00` | `fresh (0.01h / 8760h)` | 1 | `open-attribution` |
| `perfil_territorial_comunal` | chile-hub | `fallback` | `derived_from_validated_chile_hub_layers` | `2026-07-20T17:19:49.384442+00:00` | `fresh (0.0h / 1080h)` | 0 | `open-attribution` |
| `empresas` | Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES) | `live` | `datos_gob_cl_ckan_api` | `2026-07-20T17:19:21.635593+00:00` | `fresh (0.01h / 1080h)` | 3 | `open-attribution` |
| `pobreza_comunal` | Observatorio Social — Ministerio de Desarrollo Social y Familia | `live` | `Estimaciones de Pobreza Comunal vía SAE desde encuesta CASEN` | `2026-07-20T17:19:24.920152+00:00` | `fresh (0.01h / 175200h)` | 1 | `open-attribution` |
| `consumo_electrico_comunal` | CNE — Energía Abierta | `fallback` | `Consumo eléctrico anual por comuna y tipo de cliente` | `2026-07-20T17:19:29.939434+00:00` | `fresh (0.01h / 17520h)` | 3 | `open-attribution` |
| `partidos_politicos` | Cámara de Diputadas y Diputados (datos abiertos) + SERVEL | `live` | `WSComun.asmx/retornarPartidosPoliticos + servel.cl/partidos-politicos (estado legal)` | `2026-07-20T17:19:33.172598+00:00` | `fresh (0.0h / 87600h)` | 1 | `open-attribution` |
| `autoridades_electas` | Cámara de Diputadas y Diputados + Senado de Chile | `live` | `WSDiputado.asmx/retornarDiputadosPeriodoActual + camara.cl + senado.cl (Scrapling)` | `2026-07-20T17:19:38.462081+00:00` | `fresh (0.0h / 87600h)` | 0 | `open-attribution` |

## regiones

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-07-20T17:18:28.849680+00:00`
- `freshness`: `fresh (0.02h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/regiones.md`

## provincias

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-07-20T17:18:28.849680+00:00`
- `freshness`: `fresh (0.02h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/provincias.md`

## comunas

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-07-20T17:18:28.849680+00:00`
- `freshness`: `fresh (0.02h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/comunas.md`

## comunas_enriquecidas

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-07-20T17:18:28.849680+00:00`
- `freshness`: `fresh (0.02h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/comunas_enriquecidas.md`

## indicadores

- `source_name`: Banco Central de Chile (via mindicador.cl)
- `source_url`: https://mindicador.cl/api
- `source_mode`: `live`
- `source_detail`: `public_api_with_published_backfill`
- `refreshed_at_utc`: `2026-07-20T17:18:40.211198+00:00`
- `freshness`: `fresh (0.02h / 72h)`
- `warning_count`: `1`
- `diagnostic_summary`: indicadores live refresh reused last published artifact for missing codes: ipc
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/indicadores.md`

## censo_comunal

- `source_name`: Instituto Nacional de Estadisticas - Censo 2024
- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx
- `source_mode`: `live`
- `source_detail`: `official_xlsx`
- `refreshed_at_utc`: `2026-07-20T17:18:42.726362+00:00`
- `freshness`: `fresh (0.02h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: age_bands_derived_from_quinquennial_groups
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/censo_comunal.md`

## establecimientos_salud

- `source_name`: Ministerio de Salud - Establecimientos de Salud
- `source_url`: https://datos.gob.cl/dataset/3bf4cf7c-f638-4735-9a01-f65faae4beca/resource/2c44d782-3365-44e3-aefb-2c8b8363a1bc/download/establecimientos_20260714.csv
- `source_mode`: `live`
- `source_detail`: `datos_gob_csv`
- `refreshed_at_utc`: `2026-07-20T17:18:45.886816+00:00`
- `freshness`: `fresh (0.02h / 1080h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/establecimientos_salud.md`

## establecimientos_educacionales

- `source_name`: Ministerio de Educación - Directorio Oficial de Establecimientos
- `source_url`: https://datosabiertos.mineduc.cl/wp-content/uploads/2025/11/Directorio-Oficial-EE-2025.rar
- `source_mode`: `live`
- `source_detail`: `mineduc_datos_abiertos_rar`
- `refreshed_at_utc`: `2026-07-20T17:18:48.193411+00:00`
- `freshness`: `fresh (0.02h / 8760h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/establecimientos_educacionales.md`

## censo_hogares_viviendas

- `source_name`: Instituto Nacional de Estadisticas - Censo 2024
- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/V1_Viviendas-y-hogares-censados.xlsx
- `source_mode`: `live`
- `source_detail`: `official_xlsx`
- `refreshed_at_utc`: `2026-07-20T17:18:44.159462+00:00`
- `freshness`: `fresh (0.02h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/censo_hogares_viviendas.md`

## distritos_electorales

- `source_name`: BCN / Biblioteca del Congreso Nacional de Chile
- `source_url`: https://www.bcn.cl/siit/observatorio/ley20840
- `source_mode`: `live`
- `source_detail`: `bcn_electoral_mapping_generated`
- `refreshed_at_utc`: `2026-07-20T17:18:46.044445+00:00`
- `freshness`: `fresh (0.02h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/distritos_electorales.md`

## finanzas_municipales

- `source_name`: SINIM - SUBDERE
- `source_url`: https://datos.sinim.gov.cl/datos_municipales.php
- `source_mode`: `monthly`
- `source_detail`: `curated_fallback_pending_direct_export`
- `refreshed_at_utc`: `2026-07-08T19:27:07.437842+00:00`
- `freshness`: `fresh (285.88h / 8760h)`
- `warning_count`: `0`
- `diagnostic_summary`: live: Playwright configurando filtros SINIM
- `reuse_status`: `public-api-review-terms`
- `documentation`: `docs/datasets/finanzas_municipales.md`

## resultados_educacionales

- `source_name`: Centro de Estudios MINEDUC - Rendimiento 2024
- `source_url`: https://datosabiertos.mineduc.cl/wp-content/uploads/2025/04/Rendimiento_2024.rar
- `source_mode`: `live`
- `source_detail`: `mineduc_rendimiento_2024_rar_agregado_por_comuna`
- `refreshed_at_utc`: `2026-07-20T17:18:54.342056+00:00`
- `freshness`: `fresh (0.02h / 8760h)`
- `warning_count`: `0`
- `diagnostic_summary`: privacy_safe_comuna_year_aggregation
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/resultados_educacionales.md`

## indicadores_urbanos_siedu

- `source_name`: INE - Sistema de Indicadores y Estándares de Desarrollo Urbano
- `source_url`: https://www.ine.gob.cl/docs/default-source/sistema-de-indicadores-y-estandares-de-desarrollo-urbano/indicadores/actualizaci%C3%B3n-2019/matriz-siedu-publicacion.xlsm
- `source_mode`: `live`
- `source_detail`: `ine_siedu_xlsm_cinco_mediciones_2018_2022`
- `refreshed_at_utc`: `2026-07-20T17:18:57.829704+00:00`
- `freshness`: `fresh (0.01h / 8760h)`
- `warning_count`: `1`
- `diagnostic_summary`: indicadores_urbanos_siedu has intentionally partial urban coverage
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/indicadores_urbanos_siedu.md`

## perfil_territorial_comunal

- `source_name`: chile-hub
- `source_url`: https://github.com/cortega26/chile-hub
- `source_mode`: `fallback`
- `source_detail`: `derived_from_validated_chile_hub_layers`
- `refreshed_at_utc`: `2026-07-20T17:19:49.384442+00:00`
- `freshness`: `fresh (0.0h / 1080h)`
- `warning_count`: `0`
- `diagnostic_summary`: derived_dataset
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/perfil_territorial_comunal.md`

## empresas

- `source_name`: Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES)
- `source_url`: https://datos.gob.cl/dataset/registro-de-empresas-y-sociedades
- `source_mode`: `live`
- `source_detail`: `datos_gob_cl_ckan_api`
- `refreshed_at_utc`: `2026-07-20T17:19:21.635593+00:00`
- `freshness`: `fresh (0.01h / 1080h)`
- `warning_count`: `3`
- `diagnostic_summary`: found 1 RUTs with invalid format
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/empresas.md`

## pobreza_comunal

- `source_name`: Observatorio Social — Ministerio de Desarrollo Social y Familia
- `source_url`: https://observatorio.ministeriodesarrollosocial.gob.cl/storage/docs/pobreza-comunal/2022/Estimaciones_Tasa_Pobreza_Ingresos_Comunas_2022.xlsx
- `source_mode`: `live`
- `source_detail`: `Estimaciones de Pobreza Comunal vía SAE desde encuesta CASEN`
- `refreshed_at_utc`: `2026-07-20T17:19:24.920152+00:00`
- `freshness`: `fresh (0.01h / 175200h)`
- `warning_count`: `1`
- `diagnostic_summary`: cobertura SAE: 345/346 comunas (99.7%) — parcial por diseño; comunas sin muestra no tienen estimación
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/pobreza_comunal.md`

## consumo_electrico_comunal

- `source_name`: CNE — Energía Abierta
- `source_url`: http://datos.energiaabierta.cl/dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/
- `source_mode`: `fallback`
- `source_detail`: `Consumo eléctrico anual por comuna y tipo de cliente`
- `refreshed_at_utc`: `2026-07-20T17:19:29.939434+00:00`
- `freshness`: `fresh (0.01h / 17520h)`
- `warning_count`: `3`
- `diagnostic_summary`: tipos de cliente: ['Comercial', 'Residencial']
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/consumo_electrico_comunal.md`

## partidos_politicos

- `source_name`: Cámara de Diputadas y Diputados (datos abiertos) + SERVEL
- `source_url`: https://opendata.camara.cl/camaradiputados/WServices/WSComun.asmx/retornarPartidosPoliticos
- `source_mode`: `live`
- `source_detail`: `WSComun.asmx/retornarPartidosPoliticos + servel.cl/partidos-politicos (estado legal)`
- `refreshed_at_utc`: `2026-07-20T17:19:33.172598+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `warning_count`: `1`
- `diagnostic_summary`: estado_legal poblado (vía SERVEL) en 15/36 partidos
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/partidos_politicos.md`

## autoridades_electas

- `source_name`: Cámara de Diputadas y Diputados + Senado de Chile
- `source_url`: https://opendata.camara.cl/camaradiputados/WServices/WSDiputado.asmx/retornarDiputadosPeriodoActual
- `source_mode`: `live`
- `source_detail`: `WSDiputado.asmx/retornarDiputadosPeriodoActual + camara.cl + senado.cl (Scrapling)`
- `refreshed_at_utc`: `2026-07-20T17:19:38.462081+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: v1: diputados (155) + senadores (50). Gobernador_regional/alcalde viven en el dataset segregado autoridades_locales (licencia CC-BY-SA).
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/autoridades_electas.md`
