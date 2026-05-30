# chile-hub dataset catalog

- `generated_at_utc`: `2026-05-30T20:35:29.457773+00:00`
- `dataset_count`: `4`

| Dataset | Source | Mode | Records | Confidence | Join Keys | Validation |
| :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `regiones` | BCN ArcGIS | `live` | 16 | `Tier B` | `codigo_region` | `ok` |
| `provincias` | BCN ArcGIS | `live` | 56 | `Tier B` | `codigo_provincia, codigo_region` | `ok` |
| `comunas` | BCN ArcGIS | `live` | 346 | `Tier B` | `codigo_comuna, codigo_region` | `ok` |
| `indicadores` | mindicador.cl | `live` | 5 | `Tier A/B` | `fecha, codigo_indicador` | `ok` |

## regiones

Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/regiones.md`
- `fields`: `codigo_region, nombre_region`
- `join_keys`: `codigo_region`
- `outputs`: `{"parquet": "data/normalized/regiones.parquet", "json": "data/normalized/regiones.json", "duckdb_table": "regiones", "sqlite_table": "regiones", "excel_sheet": "Regiones"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## provincias

Capa derivada de provincias para cruces intermedios entre region y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/provincias.md`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `join_keys`: `codigo_provincia, codigo_region`
- `outputs`: `{"parquet": "data/normalized/provincias.parquet", "json": "data/normalized/provincias.json", "duckdb_table": "provincias", "sqlite_table": "provincias", "excel_sheet": "Provincias"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## comunas

Base territorial normalizada para cruces por region, provincia y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/comunas.md`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/comunas.parquet", "json": "data/normalized/comunas.json", "duckdb_table": "comunas", "sqlite_table": "comunas", "excel_sheet": "Comunas y Regiones"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## indicadores

Serie de indicadores economicos diarios de referencia para analisis y software.

- `source_url`: https://mindicador.cl/api
- `documentation`: `docs/datasets/indicadores.md`
- `fields`: `fecha, codigo_indicador, valor`
- `join_keys`: `fecha, codigo_indicador`
- `outputs`: `{"parquet": "data/normalized/indicadores.parquet", "json": "data/normalized/indicadores_hoy.json", "duckdb_table": "indicadores", "sqlite_table": "indicadores", "excel_sheet": "Indicadores Diarios"}`
- `warnings`: none
