# chile-hub provenance report

- `generated_at_utc`: `2026-06-16T20:24:31.852447+00:00`
- `dataset_count`: `10`
- `live_count`: `10`
- `fallback_count`: `0`

| Dataset | Source | Mode | Detail | Refreshed | Freshness | Warnings | Reuse |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | :--- |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-16T20:24:16.914195+00:00` | `fresh (0.0h / 2160h)` | 0 | `open-attribution` |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-16T20:24:16.914195+00:00` | `fresh (0.0h / 2160h)` | 0 | `open-attribution` |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-16T20:24:16.914195+00:00` | `fresh (0.0h / 2160h)` | 0 | `open-attribution` |
| `comunas_enriquecidas` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-16T20:24:16.914195+00:00` | `fresh (0.0h / 2160h)` | 0 | `open-attribution` |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api_with_published_backfill` | `2026-06-16T20:24:23.281851+00:00` | `fresh (0.0h / 72h)` | 1 | `open-attribution` |
| `censo_comunal` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `2026-06-16T20:24:24.124863+00:00` | `fresh (0.0h / 87600h)` | 0 | `open-attribution` |
| `establecimientos_salud` | Ministerio de Salud - Establecimientos de Salud | `live` | `datos_gob_csv` | `2026-06-16T20:24:28.139467+00:00` | `fresh (0.0h / 1080h)` | 0 | `open-attribution` |
| `establecimientos_educacionales` | Ministerio de Educación - Directorio Oficial de Establecimientos | `live` | `mineduc_datos_abiertos_rar` | `2026-06-16T20:24:28.839180+00:00` | `fresh (0.0h / 8760h)` | 0 | `open-attribution` |
| `censo_hogares_viviendas` | Instituto Nacional de Estadisticas - Censo 2024 | `live` | `official_xlsx` | `2026-06-16T20:24:24.994197+00:00` | `fresh (0.0h / 87600h)` | 0 | `open-attribution` |
| `distritos_electorales` | BCN / Biblioteca del Congreso Nacional de Chile | `live` | `bcn_electoral_mapping_generated` | `2026-06-16T20:24:28.310540+00:00` | `fresh (0.0h / 87600h)` | 0 | `open-attribution` |

## regiones

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-16T20:24:16.914195+00:00`
- `freshness`: `fresh (0.0h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/regiones.md`

## provincias

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-16T20:24:16.914195+00:00`
- `freshness`: `fresh (0.0h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/provincias.md`

## comunas

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-16T20:24:16.914195+00:00`
- `freshness`: `fresh (0.0h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/comunas.md`

## comunas_enriquecidas

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-16T20:24:16.914195+00:00`
- `freshness`: `fresh (0.0h / 2160h)`
- `warning_count`: `0`
- `diagnostic_summary`: bcn_skipped_null_code_records: 1
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/comunas_enriquecidas.md`

## indicadores

- `source_name`: Banco Central de Chile (via mindicador.cl)
- `source_url`: https://mindicador.cl/api
- `source_mode`: `live`
- `source_detail`: `public_api_with_published_backfill`
- `refreshed_at_utc`: `2026-06-16T20:24:23.281851+00:00`
- `freshness`: `fresh (0.0h / 72h)`
- `warning_count`: `1`
- `diagnostic_summary`: indicadores live refresh reused last published artifact for missing codes: ipc
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/indicadores.md`

## censo_comunal

- `source_name`: Instituto Nacional de Estadisticas - Censo 2024
- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx
- `source_mode`: `live`
- `source_detail`: `official_xlsx`
- `refreshed_at_utc`: `2026-06-16T20:24:24.124863+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: age_bands_derived_from_quinquennial_groups
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/censo_comunal.md`

## establecimientos_salud

- `source_name`: Ministerio de Salud - Establecimientos de Salud
- `source_url`: https://datos.gob.cl/dataset/3bf4cf7c-f638-4735-9a01-f65faae4beca/resource/2c44d782-3365-44e3-aefb-2c8b8363a1bc/download/establecimientos_20260609.csv
- `source_mode`: `live`
- `source_detail`: `datos_gob_csv`
- `refreshed_at_utc`: `2026-06-16T20:24:28.139467+00:00`
- `freshness`: `fresh (0.0h / 1080h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/establecimientos_salud.md`

## establecimientos_educacionales

- `source_name`: Ministerio de Educación - Directorio Oficial de Establecimientos
- `source_url`: https://datosabiertos.mineduc.cl/wp-content/uploads/2025/11/Directorio-Oficial-EE-2025.rar
- `source_mode`: `live`
- `source_detail`: `mineduc_datos_abiertos_rar`
- `refreshed_at_utc`: `2026-06-16T20:24:28.839180+00:00`
- `freshness`: `fresh (0.0h / 8760h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/establecimientos_educacionales.md`

## censo_hogares_viviendas

- `source_name`: Instituto Nacional de Estadisticas - Censo 2024
- `source_url`: https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/V1_Viviendas-y-hogares-censados.xlsx
- `source_mode`: `live`
- `source_detail`: `official_xlsx`
- `refreshed_at_utc`: `2026-06-16T20:24:24.994197+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/censo_hogares_viviendas.md`

## distritos_electorales

- `source_name`: BCN / Biblioteca del Congreso Nacional de Chile
- `source_url`: https://www.bcn.cl/siit/observatorio/ley20840
- `source_mode`: `live`
- `source_detail`: `bcn_electoral_mapping_generated`
- `refreshed_at_utc`: `2026-06-16T20:24:28.310540+00:00`
- `freshness`: `fresh (0.0h / 87600h)`
- `warning_count`: `0`
- `diagnostic_summary`: Sin observaciones operativas.
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/distritos_electorales.md`
