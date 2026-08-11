# Comunas enriquecidas

Dataset territorial de 346 comunas con códigos CUT, jerarquía administrativa,
coordenadas de cabecera y población estimada. Reutiliza la capa `comunas` ya
enriquecida durante la extracción y la expone como superficie explícita para
análisis geoespacial y demográfico.

## Fuentes y reutilizacion

- División territorial: BCN ArcGIS, CC BY con atribución.
- Coordenadas: tabla de referencia territorial incluida en el proyecto.
- Población: estimaciones y proyecciones INE, base Censo 2017, referencia 2022.

## Esquema

| Columna | Tipo | Descripcion |
|---|---|---|
| `codigo_comuna` | string(5) | Código CUT de comuna |
| `nombre_comuna` | string | Nombre oficial |
| `nombre_comuna_clean` | string | Nombre normalizado para búsqueda |
| `codigo_provincia` | string(3) | Código CUT de provincia |
| `nombre_provincia` | string | Nombre de provincia |
| `codigo_region` | string(2) | Código CUT de región |
| `nombre_region` | string | Nombre de región |
| `latitud_cabecera` | float64 | Latitud de la cabecera comunal |
| `longitud_cabecera` | float64 | Longitud de la cabecera comunal |
| `poblacion_estimada` | int32 | Población estimada de referencia |

## Uso

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("comunas_enriquecidas")
```

```sql
SELECT nombre_comuna, poblacion_estimada
FROM 'data/normalized/comunas_enriquecidas.parquet'
ORDER BY poblacion_estimada DESC
LIMIT 10;
```

Las coordenadas representan cabeceras comunales, no centroides administrativos.
Los valores de población son estimaciones de referencia y no reemplazan cifras
censales oficiales para decisiones regulatorias.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/comunas_enriquecidas.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` | Sí | — |
| `nombre_comuna_clean` | `VARCHAR` | `"iquique"` | No | — |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` | Sí | — |
| `codigo_region` | `VARCHAR(2)` | `"01"` | Sí | — |
| `latitud_cabecera` | `DOUBLE` | `-20.2138` | Sí | — |
| `longitud_cabecera` | `DOUBLE` | `-70.1508` | Sí | — |
| `poblacion_estimada` | `INTEGER` | `223400` | Sí | — |

<!-- END_DATASET_SCHEMA -->
