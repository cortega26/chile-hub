# Comunas enriquecidas

Dataset territorial de 346 comunas con codigos CUT, jerarquia administrativa,
coordenadas de cabecera y poblacion estimada. Reutiliza la capa `comunas` ya
enriquecida durante la extraccion y la expone como superficie explicita para
analisis geoespacial y demografico.

## Fuentes y reutilizacion

- Division territorial: BCN ArcGIS, CC BY con atribucion.
- Coordenadas: tabla de referencia territorial incluida en el proyecto.
- Poblacion: estimaciones y proyecciones INE, base Censo 2017, referencia 2022.

## Schema

| Columna | Tipo | Descripcion |
|---|---|---|
| `codigo_comuna` | string(5) | Codigo CUT de comuna |
| `nombre_comuna` | string | Nombre oficial |
| `nombre_comuna_clean` | string | Nombre normalizado para busqueda |
| `codigo_provincia` | string(3) | Codigo CUT de provincia |
| `nombre_provincia` | string | Nombre de provincia |
| `codigo_region` | string(2) | Codigo CUT de region |
| `nombre_region` | string | Nombre de region |
| `latitud_cabecera` | float64 | Latitud de la cabecera comunal |
| `longitud_cabecera` | float64 | Longitud de la cabecera comunal |
| `poblacion_estimada` | int32 | Poblacion estimada de referencia |

## Uso

```python
from src.chile_hub import ChileHub

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
Los valores de poblacion son estimaciones de referencia y no reemplazan cifras
censales oficiales para decisiones regulatorias.
