# Geometría Comunal

Límites poligonales (GeoParquet) de las 345/346 comunas de Chile, geometría **"generalizada"** — simplificada para cartografía a escala nacional, **no apta para trabajo de precisión geodésica ni catastral**. Artefacto separado del dataset [`comunas`](comunas.md) (nunca una columna de ese dataset); se une por `codigo_comuna`.

Es el dataset hermano de `resolve_comunas()` (nombre → CUT, Plan 050): éste resuelve **coordenadas → comuna** vía `resolve_by_coords()` (extra `[geo]`, cuando esté disponible).

## Fuente y licencia

- **Fuente:** BCN ArcGIS — capa `tematico/Comunas_Generalizadas` (`arcgiswebad.bcn.cl`), la misma familia de servicios que usa `comunas` para atributos DPA.
- **Licencia:** uso libre con atribución obligatoria a la Biblioteca del Congreso Nacional de Chile. Declaración textual (`bcn.cl/siit/mapas_vectoriales`): *"Los mapas vectoriales son puestos a disposición en virtud del principio de transparencia de la función pública. Las personas o instituciones pueden usar libremente esta información, señalando como fuente a la Biblioteca del Congreso Nacional de Chile."*
- **URL:** https://www.bcn.cl/siit/mapas_vectoriales/index_html
- **Gate de licencia completo:** [`docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md`](../adr/ADR-012-geometria-comunal-y-reverse-geocoding.md)
- **Carril:** `candidate` — cobertura 345/346 (falta `codigo_comuna=12202`, Antártica; mismo hueco que `comunas` ya suplementa a mano).

## Formato del artefacto

`data/normalized/geometria_comunal.parquet` es **GeoParquet 1.0** (footer `geo` estándar, geometría codificada **WKB**, CRS **EPSG:4326 / WGS84**) — no un Parquet con una columna de texto WKT. Herramientas GIS (QGIS, geopandas, DuckDB con la extensión `spatial`, deck.gl, Observable) lo leen directamente como una capa geoespacial.

La geometría es **simplificada** (tolerancia Douglas-Peucker ≈ 0.001° ≈ 100 m, topología preservada) para mantener el artefacto liviano — sin simplificar pesa ~28 MB (dominado por los fiordos e islas de Magallanes); simplificado, ~5 MB. Ver ADR-012 para la comparativa de tolerancias evaluadas.

## Esquema

`codigo_region` (string, 2), `codigo_comuna` (string, 5 — clave primaria, FK hacia `comunas`), `nombre_comuna`, `nombre_comuna_clean` (sin tildes/ñ), `nombre_region`, `geometry` (binario WKB — `Polygon` o `MultiPolygon`).

## Uso

`geometry` es binario (WKB), no una columna soportada por `hub.load_polars()` para análisis geoespacial directo — usa `geopandas.read_parquet()`:

```python
import geopandas as gpd

gdf = gpd.read_parquet("data/normalized/geometria_comunal.parquet")
print(gdf.crs)          # EPSG:4326
print(gdf.geometry.iloc[0].geom_type)  # Polygon | MultiPolygon

# Join con otro dataset chile-hub por codigo_comuna
from chile_hub import ChileHub
hub = ChileHub()
pobreza = hub.load_polars("pobreza_comunal").to_pandas()
gdf_pobreza = gdf.merge(pobreza, on="codigo_comuna")
gdf_pobreza.plot(column="tasa")
```

```sql
-- DuckDB con la extensión spatial lee GeoParquet directamente
INSTALL spatial; LOAD spatial;
SELECT codigo_comuna, nombre_comuna, ST_Area(geometry) AS area
FROM 'data/normalized/geometria_comunal.parquet'
ORDER BY area DESC;
```

## Limitaciones

- **No usar para precisión geodésica ni catastral.** La fuente BCN es cartografía de referencia a escala nacional, no un catastro de límites legales.
- **Simplificación adicional en el artefacto:** la geometría ya "generalizada" de BCN se simplifica más (≈100 m de tolerancia) para mantener el peso del artefacto razonable. Puede afectar la precisión de `resolve_by_coords()` cerca de los bordes comunales.
- **Cobertura 345/346:** falta la comuna Antártica (`codigo_comuna=12202`) — la fuente BCN no expone su geometría.
- **Carril `candidate`:** no incluido todavía en el bundle público (`stable_publishable`) mientras madura la cadencia de refresco del extractor.
- **Solo `.parquet`:** este dataset no se publica en JSON/CSV/Excel — una sola comuna con geometría compleja puede exceder límites de celda de esos formatos (ej. Excel: 32.767 caracteres/celda).

## Registro de cambios

- v1 (2026-07-23): Primera versión. Geometría comunal generalizada desde BCN ArcGIS, GeoParquet 1.0/WKB/EPSG:4326, 345/346 comunas.
