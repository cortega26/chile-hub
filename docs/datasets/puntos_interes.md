# Puntos de Interés — OpenStreetMap

> **Estado:** archivado. `puntos_interes` no forma parte del catálogo público actual
> de `chile-hub`, no está incluido en `data/normalized/` y no debe usarse con
> `hub.load_polars("puntos_interes")`. El extractor basado en Overpass API fue
> retirado porque la fuente resultó demasiado inestable para CI; esta ficha queda
> como referencia histórica hasta que exista una fuente oficial chilena de POIs.

Dataset de puntos de interés (POI) georreferenciados extraídos de
OpenStreetMap vía Overpass API. Incluye comercios, servicios, oficinas,
talleres y atracciones turísticas con nombre, dirección postal y coordenadas.

## Fuente

| Campo | Valor |
|:---|:---|
| **Nombre** | OpenStreetMap contributors |
| **Acceso** | Overpass API (https://overpass-api.de) |
| **Licencia** | ODbL 1.0 |
| **Atribución** | "© OpenStreetMap contributors" |
| **Formato** | JSON vía API REST |
| **Actualización** | Quincenal (recomendada) |
| **Cobertura** | Parcial: densidad urbana > rural |

## Esquema

| Columna | Tipo | Descripción |
|:---|:---|:---|
| `osm_id` | `Int64` | Identificador único del nodo en OpenStreetMap |
| `nombre` | `String` | Nombre del establecimiento |
| `categoria` | `String` | Categoría principal: `amenidad`, `comercio`, `turismo`, `oficina`, `oficio` |
| `tipo` | `String` | Tipo específico: `restaurante`, `supermercado`, `hotel`, `banco`, etc. |
| `direccion` | `String` | Dirección postal (calle + número) |
| `comuna` | `String` | Comuna según OSM (`addr:city`) |
| `codigo_comuna` | `String` | Código CUT de comuna (si se resolvió en el cruce con la DPA) |
| `codigo_region` | `String` | Código CUT de región (si se resolvió en el cruce con la DPA) |
| `telefono` | `String` | Teléfono (si está disponible en OSM) |
| `sitio_web` | `String` | URL del sitio web (si está disponible en OSM) |
| `latitud` | `Float64` | Latitud en WGS84 |
| `longitud` | `Float64` | Longitud en WGS84 |

## Categorías

| Categoría | Tag OSM | Ejemplos de tipos |
|:---|:---|:---|
| `amenidad` | `amenity=*` | restaurante, cafetería, bar, banco, farmacia, combustible |
| `comercio` | `shop=*` | supermercado, panadería, ropa, peluquería, ferretería |
| `turismo` | `tourism=*` | hotel, hostal, museo, atracción, galería |
| `oficina` | `office=*` | empresa, abogado, contador, arquitecto, notaría |
| `oficio` | `craft=*` | carpintero, electricista, fontanero, cerrajero |

## Uso histórico

Los ejemplos siguientes se conservan solo como referencia del diseño original.
No funcionan en la versión actual mientras `puntos_interes` siga archivado.

### Python

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("puntos_interes")

# Top 10 comunas con mas POIs
print(df.group_by("comuna").len().sort("len", descending=True).head(10))

# Todos los restaurantes de Providencia
restaurantes = df.filter(
    (pl.col("tipo") == "restaurante")
    & (pl.col("codigo_comuna") == "13123")
)
print(restaurantes.select("nombre", "direccion", "telefono"))

# Mapa de categorias
print(df.group_by("categoria").len().sort("len", descending=True))
```

### DuckDB / SQL

```sql
-- POIs por categoria
SELECT categoria, count(*) AS n
FROM 'data/normalized/puntos_interes.parquet'
GROUP BY 1 ORDER BY n DESC;

-- Buscar por nombre
SELECT * FROM 'data/normalized/puntos_interes.parquet'
WHERE nombre ILIKE '%farmacia%' AND codigo_comuna = '13101';

-- Restaurantes con telefono cerca del centro
SELECT nombre, direccion, telefono, latitud, longitud
FROM 'data/normalized/puntos_interes.parquet'
WHERE tipo = 'restaurante'
  AND comuna = 'Santiago'
  AND telefono IS NOT NULL;
```

### CLI

```bash
chile-hub show puntos_interes
chile-hub path puntos_interes --output parquet
```

## Limitaciones

1. **Cobertura parcial.** Mayor densidad en zonas urbanas (Santiago, Valparaíso,
   Concepción). Zonas rurales y ciudades pequeñas tienen cobertura limitada.
   Este dataset NO es un censo.
2. **Datos comunitarios.** Los datos dependen de contribuidores voluntarios de
   OpenStreetMap. Un negocio puede estar mapeado hoy y haber cerrado sin que
   OSM lo refleje.
3. **Sin RUT.** No es posible cruzar directamente con el dataset `empresas`
   (RES). El cruce sería por nombre + comuna (fuzzy match).
4. **Categorías no oficiales.** Las categorías son tags de OSM, no equivalen a
   la clasificación CIIU oficial ni al registro de actividades del SII.
5. **Direcciones incompletas.** No todos los POIs tienen `addr:street` y
   `addr:housenumber`. Algunos solo tienen coordenadas.
6. **Cruce con DPA.** Aproximadamente 60-80% de los POIs logran cruzar con la
   DPA por nombre de comuna. El resto queda sin `codigo_comuna`.

## Notas de integración

- **Tier histórico:** C — fuente comunitaria con cobertura parcial.
- **Join keys históricos:** `osm_id` (principal). `codigo_comuna` para cruce territorial.
- **Bundle:** No incluido en el ZIP público actual.
- **Atribución histórica:** Todo uso público de estos datos debía incluir:
  "© OpenStreetMap contributors".

## Registro de cambios

- **2026-06-18:** Dataset archivado; no forma parte del catálogo público actual.
- **2026-06-17:** Dataset agregado a chile-hub (extractor Overpass API,
  validación, tests, documentación).
