# Establecimientos educacionales

Directorio oficial de establecimientos educacionales vigentes en Chile, publicado por el Ministerio de Educación (MINEDUC).

## Fuente y licencia

- Fuente: Centro de Estudios del Ministerio de Educación de Chile (datosabiertos.mineduc.cl).
- Formato de origen: RAR conteniendo un archivo CSV.
- Licencia: CC BY 3.0 CL.
- Frecuencia declarada por la fuente: anual (Directorio Oficial de Establecimientos).

## Esquema

`rbd`, `dv_rbd`, `nombre_establecimiento`, `codigo_region`, `codigo_comuna`, `dependencia_administrativa`, `latitud`, `longitud`, `estado_funcionamiento`.

## Uso

```python
from chile_hub import ChileHub

df = ChileHub().load_polars("establecimientos_educacionales")
```

```sql
SELECT dependencia_administrativa, count(*) AS total_establecimientos
FROM 'data/normalized/establecimientos_educacionales.parquet'
GROUP BY dependencia_administrativa
ORDER BY total_establecimientos DESC;
```

## Limitaciones

El directorio se filtra para excluir establecimientos cerrados permanentemente. Las coordenadas provienen de la georreferenciación oficial del Ministerio de Educación.

## Registro de cambios

- 2026-06: Primera versión con RBD, nombre del establecimiento, comuna, región, dependencia administrativa y coordenadas.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/establecimientos_educacionales.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `rbd` | `VARCHAR` | `"1234-5"` | Sí | PK |
| `dv_rbd` | `VARCHAR` | `"4"` | Sí | — |
| `nombre_establecimiento` | `VARCHAR` | `"Liceo Abate Molina"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | — |
| `dependencia_administrativa` | `VARCHAR` | `"Municipal"` | No | — |
| `latitud` / `longitud` | `DOUBLE` | `"Coordenadas geográficas"` | No | — |
| `estado_funcionamiento` | `VARCHAR` | `"Vigente"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
