# Establecimientos de salud

Directorio vigente de establecimientos de salud publicado por el Ministerio de Salud.

## Fuente y licencia

- Fuente: MINSAL mediante datos.gob.cl.
- Formato de origen: CSV separado por punto y coma.
- Licencia: CC0.
- Frecuencia declarada por la fuente: mensual.

## Esquema

`codigo_establecimiento`, `nombre_establecimiento`, `tipo_establecimiento`, `dependencia_administrativa`, `nivel_atencion`, `codigo_region`, `nombre_region`, `codigo_comuna`, `nombre_comuna`, `tiene_servicio_urgencia`, `tipo_urgencia`, `latitud`, `longitud`, `estado_funcionamiento`.

## Uso

```python
from chile_hub import ChileHub

df = ChileHub().load_polars("establecimientos_salud")
```

```sql
SELECT codigo_comuna, count(*) AS establecimientos
FROM 'data/normalized/establecimientos_salud.parquet'
GROUP BY codigo_comuna
ORDER BY establecimientos DESC;
```

## Limitaciones

El directorio mezcla establecimientos públicos y privados y conserva las clasificaciones entregadas por MINSAL. La ausencia de coordenadas no se imputa.

## Registro de cambios

- 2026-06: primera versión con identidad, clasificación, urgencia, estado y coordenadas.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/establecimientos_salud.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_establecimiento` | `VARCHAR` | `"101101"` | Sí | PK |
| `nombre_establecimiento` | `VARCHAR` | `"Hospital Dr. Ernesto Torres Galdames"` | Sí | — |
| `tipo_establecimiento` | `VARCHAR` | `"Hospital"` | Sí | — |
| `nivel_atencion` | `VARCHAR` | `"Alta Complejidad"` | No | — |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | — |
| `tiene_servicio_urgencia` | `VARCHAR` | `"SI"` / `"NO"` | No | — |
| `latitud` / `longitud` | `DOUBLE` | `"Coordenadas geográficas"` | No | — |
| `estado_funcionamiento` | `VARCHAR` | `"Vigente"` | No | — |

<!-- END_DATASET_SCHEMA -->
