# chile-hub provenance report

- `generated_at_utc`: `2026-06-06T23:11:44.833453+00:00`
- `dataset_count`: `4`
- `live_count`: `4`
- `fallback_count`: `0`

| Dataset | Source | Mode | Detail | Refreshed | Freshness | Reuse |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `regiones` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-01T15:59:50.538076+00:00` | `fresh (127.2h / 2160h)` | `open-attribution` |
| `provincias` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-01T15:59:50.538076+00:00` | `fresh (127.2h / 2160h)` | `open-attribution` |
| `comunas` | BCN ArcGIS | `live` | `bcn_arcgis` | `2026-06-01T15:59:50.538076+00:00` | `fresh (127.2h / 2160h)` | `open-attribution` |
| `indicadores` | Banco Central de Chile (via mindicador.cl) | `live` | `public_api` | `2026-06-01T15:38:37.668778+00:00` | `stale (127.55h / 72h)` | `open-attribution` |

## regiones

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (127.2h / 2160h)`
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/regiones.md`

## provincias

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (127.2h / 2160h)`
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/provincias.md`

## comunas

- `source_name`: BCN ArcGIS
- `source_url`: https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query
- `source_mode`: `live`
- `source_detail`: `bcn_arcgis`
- `refreshed_at_utc`: `2026-06-01T15:59:50.538076+00:00`
- `freshness`: `fresh (127.2h / 2160h)`
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/comunas.md`

## indicadores

- `source_name`: Banco Central de Chile (via mindicador.cl)
- `source_url`: https://mindicador.cl/api
- `source_mode`: `live`
- `source_detail`: `public_api`
- `refreshed_at_utc`: `2026-06-01T15:38:37.668778+00:00`
- `freshness`: `stale (127.55h / 72h)`
- `reuse_status`: `open-attribution`
- `documentation`: `docs/datasets/indicadores.md`
