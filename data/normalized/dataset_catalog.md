# chile-hub dataset catalog

- `generated_at_utc`: `2026-06-12T15:58:17.707652+00:00`
- `dataset_count`: `4`

| Dataset | Source | Mode | Freshness | Reuse | Records | Confidence | Join Keys | Validation |
| :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `regiones` | BCN ArcGIS | `live` | `fresh (263.97h / 2160h)` | `open-attribution (CC BY)` | 16 | `Tier B` | `codigo_region` | `ok` |
| `provincias` | BCN ArcGIS | `live` | `fresh (263.97h / 2160h)` | `open-attribution (CC BY)` | 56 | `Tier B` | `codigo_provincia, codigo_region` | `ok` |
| `comunas` | BCN ArcGIS | `live` | `fresh (263.97h / 2160h)` | `open-attribution (CC BY)` | 346 | `Tier B` | `codigo_comuna, codigo_region` | `ok` |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `fresh (12.73h / 72h)` | `open-attribution (Reproducción libre con citación (BCCh / INE))` | 424 | `Tier A/B` | `fecha, codigo_indicador` | `ok` |

## regiones

Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/regiones.md`
- `freshness`: `fresh (263.97h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Derivada de datos abiertos BCN reutilizables con atribucion."}`
- `fields`: `codigo_region, nombre_region`
- `join_keys`: `codigo_region`
- `outputs`: `{"parquet": "data/normalized/regiones.parquet", "json": "data/normalized/regiones.json", "duckdb_table": "regiones", "sqlite_table": "regiones", "excel_sheet": "Regiones"}`
- `usage_examples`: `{"python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('regiones')", "duckdb": "SELECT *\nFROM 'data/normalized/regiones.parquet'\nORDER BY codigo_region;", "cli": "python -m src.chile_hub show regiones"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## provincias

Capa derivada de provincias para cruces intermedios entre region y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/provincias.md`
- `freshness`: `fresh (263.97h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Derivada de datos abiertos BCN reutilizables con atribucion."}`
- `fields`: `codigo_region, nombre_region, codigo_provincia, nombre_provincia`
- `join_keys`: `codigo_provincia, codigo_region`
- `outputs`: `{"parquet": "data/normalized/provincias.parquet", "json": "data/normalized/provincias.json", "duckdb_table": "provincias", "sqlite_table": "provincias", "excel_sheet": "Provincias"}`
- `usage_examples`: `{"python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('provincias')", "duckdb": "SELECT *\nFROM 'data/normalized/provincias.parquet'\nWHERE codigo_region = '13';", "cli": "python -m src.chile_hub show provincias"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## comunas

Base territorial normalizada para cruces por region, provincia y comuna.

- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `documentation`: `docs/datasets/comunas.md`
- `freshness`: `fresh (263.97h / 2160h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "CC BY", "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn", "attribution_required": true, "redistribution_ok": true, "summary": "Fuente operativa BCN dentro de su superficie de datos abiertos; atribucion requerida."}`
- `fields`: `codigo_region, nombre_region, abreviatura, codigo_provincia, nombre_provincia, codigo_comuna, nombre_comuna, nombre_comuna_clean, latitud_cabecera, longitud_cabecera, poblacion_estimada`
- `join_keys`: `codigo_comuna, codigo_region`
- `outputs`: `{"parquet": "data/normalized/comunas.parquet", "json": "data/normalized/comunas.json", "duckdb_table": "comunas", "sqlite_table": "comunas", "excel_sheet": "Comunas y Regiones"}`
- `usage_examples`: `{"python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('comunas')", "duckdb": "SELECT codigo_comuna, nombre_comuna, nombre_region\nFROM 'data/normalized/comunas.parquet'\nLIMIT 10;", "cli": "python -m src.chile_hub path comunas --output parquet"}`
- `warnings`: none
- `notes`: bcn_skipped_null_code_records: 1; bcn_supplemented_missing_comunas: 1

## indicadores

Serie de indicadores economicos diarios de referencia para analisis y software.

- `source_url`: https://mindicador.cl/api
- `documentation`: `docs/datasets/indicadores.md`
- `freshness`: `fresh (12.73h / 72h)`
- `reuse_policy`: `{"status": "open-attribution", "license": "Reproducción libre con citación (BCCh / INE)", "license_url": "https://www.bcentral.cl/web/banco-central/terminos-y-condiciones", "attribution_required": true, "redistribution_ok": true, "summary": "Datos del Banco Central de Chile (BCCh) e INE. Libre reproducción con citación. Acceso vía mindicador.cl (API pública de la comunidad)."}`
- `fields`: `fecha, codigo_indicador, valor`
- `indicator_codes`: `dolar, euro, ipc, uf, utm`
- `indicator_delivery`: `{"dolar": "live", "euro": "live", "ipc": "published_backfill", "uf": "live", "utm": "live"}`
- `join_keys`: `fecha, codigo_indicador`
- `outputs`: `{"parquet": "data/normalized/indicadores.parquet", "json": "data/normalized/indicadores_hoy.json", "duckdb_table": "indicadores", "sqlite_table": "indicadores", "excel_sheet": "Indicadores Diarios"}`
- `usage_examples`: `{"python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('indicadores')", "duckdb": "SELECT *\nFROM 'data/normalized/indicadores.parquet'\nORDER BY fecha DESC, codigo_indicador;", "cli": "python -m src.chile_hub show indicadores"}`
- `warnings`: indicadores live refresh returned empty series for: ipc/2026; indicadores live refresh reused last published artifact for missing codes: ipc
- `notes`: empty_live_pairs: ipc/2026; published_backfills_used_for_codes: ipc
