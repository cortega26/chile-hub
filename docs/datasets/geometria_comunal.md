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

## Publicación

El artefacto se genera exclusivamente mediante el workflow manual
`workflow_dispatch` **Refresh Candidate Comunal Geometry**. Tras una ejecución
validada y el despliegue de Pages, está disponible para consumo directo en:

- `https://tooltician.com/chile-hub/data/normalized/geometria_comunal.parquet`
- `https://tooltician.com/chile-hub/data/normalized/geometria_comunal.parquet.sha256`

Por ejemplo, se puede abrir directamente desde una herramienta GIS:

```python
import geopandas as gpd

url = "https://tooltician.com/chile-hub/data/normalized/geometria_comunal.parquet"
gdf = gpd.read_parquet(url)
assert len(gdf) >= 340
assert gdf.crs.to_epsg() == 4326
```

Verifica la descarga antes de usarla con `sha256sum -c` desde el directorio que
contiene ambos archivos:

```bash
sha256sum -c geometria_comunal.parquet.sha256
```

Sigue siendo datos `candidate`: queda deliberadamente fuera del bundle estable y
del build normal (el acceso es directo al archivo o vía `resolve_by_coords()`,
que lo consume bajo demanda). El workflow no fija una cadencia de refresco.

## Resolución de coordenadas a comuna (`resolve_by_coords`)

`ChileHub.resolve_by_coords()` (Plan 065) convierte coordenadas GPS en el CUT de
su comuna, contra este mismo artefacto candidate:

```bash
pip install "chile-hub[geo]"
```

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.resolve_by_coords([(-33.4489, -70.6693), (-33.1, -72.0)])
# input_lat, input_lon, codigo_comuna, nombre_comuna, matched
```

- **Tuplas `(latitud, longitud)`** en grados decimales; se preservan el orden y
  los duplicados del input (una fila por punto).
- **Esquema de salida** (Polars): `input_lat` (f64), `input_lon` (f64),
  `codigo_comuna` (str, 5 chars), `nombre_comuna` (str), `matched` (bool).
- **Fuera de Chile o de todo polígono**: `matched=False` y comuna nula — sin
  excepción. Coordenadas fuera de rango (lat ∉ [-90, 90], lon ∉ [-180, 180])
  sí lanzan `ValueError` nombrando el input.
- **Bordes**: un punto exactamente sobre un límite matchea (`covers`, no
  `contains`). Si varias comunas cubren un punto, gana el `codigo_comuna`
  lexicográficamente menor (tie-break determinístico, con warning).
- **Caché**: el artefacto se descarga una vez, se verifica contra el compañero
  `.sha256` (ADR-012) y se guarda en `platformdirs.user_cache_dir("chile-hub")`;
  un caché verificado se reutiliza sin red. `refresh_geometry=True` fuerza
  re-descarga; `geometry_path=` permite un archivo local (validado igual).
- **Límite candidate**: el artefacto se consume verificando su checksum, pero
  **no** entra al bundle estable, al catálogo ni a `load_polars()`.
- **Precisión**: la geometría generalizada + simplificación de ~100 m puede
  desplazar bordes; no usar los resultados para disputas de límites ni
  medición de precisión geodésica.

## Limitaciones

- **No usar para precisión geodésica ni catastral.** La fuente BCN es cartografía de referencia a escala nacional, no un catastro de límites legales.
- **Simplificación adicional en el artefacto:** la geometría ya "generalizada" de BCN se simplifica más (≈100 m de tolerancia) para mantener el peso del artefacto razonable. Puede afectar la precisión de `resolve_by_coords()` cerca de los bordes comunales.
- **Cobertura 345/346:** falta la comuna Antártica (`codigo_comuna=12202`) — la fuente BCN no expone su geometría.
- **Carril `candidate`:** no incluido todavía en el bundle público (`stable_publishable`) mientras madura la cadencia de refresco del extractor.
- **Solo `.parquet`:** este dataset no se publica en JSON/CSV/Excel — una sola comuna con geometría compleja puede exceder límites de celda de esos formatos (ej. Excel: 32.767 caracteres/celda).

## Registro de cambios

- v1 (2026-07-23): Primera versión. Geometría comunal generalizada desde BCN ArcGIS, GeoParquet 1.0/WKB/EPSG:4326, 345/346 comunas.
- v2 (2026-08-11): API `resolve_by_coords()` (Plan 065): contrato de distribución/caché con verificación SHA-256 y decisiones de borde/tie-break en ADR-012.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/geometria_comunal.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` | Sí | — |
| `nombre_comuna_clean` | `VARCHAR` | `"iquique"` | Sí | — |
| `nombre_region` | `VARCHAR` | `"Región de Tarapacá"` | Sí | — |
| `geometry` | `BINARY` | `"WKB — Polygon o MultiPolygon en EPSG:4326 (WGS84), geoparquet 1.0"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
