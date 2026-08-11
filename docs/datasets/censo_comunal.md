# Censo comunal 2024

Perfil demográfico de las 346 comunas de Chile construido desde los resultados oficiales del Censo de Población y Vivienda 2024 del INE.

## Fuente y licencia

- Fuente: Instituto Nacional de Estadísticas, tabla D1 del Censo 2024.
- Formato de origen: XLSX oficial.
- Reutilización: CC BY 4.0; citar al INE.

## Esquema

`codigo_region`, `nombre_region`, `codigo_provincia`, `nombre_provincia`, `codigo_comuna`, `nombre_comuna`, `poblacion_censada`, `hombres`, `mujeres`, `razon_hombre_mujer`, `poblacion_0_14`, `poblacion_15_29`, `poblacion_30_44`, `poblacion_45_64`, `poblacion_65_mas`.

Los códigos CUT son strings de longitud fija. Los grupos amplios de edad se derivan de los grupos quinquenales publicados por el INE.

## Uso

```python
from chile_hub import ChileHub

df = ChileHub().load_polars("censo_comunal")
```

```sql
SELECT nombre_comuna, poblacion_censada, poblacion_65_mas
FROM 'data/normalized/censo_comunal.parquet'
ORDER BY poblacion_censada DESC;
```

## Limitaciones

Es un corte censal de 2024, no una estimación anual. No incluye microdatos ni variables que puedan aumentar el riesgo de reidentificación.

## Registro de cambios

- 2026-06: primera versión comunal con sexo y cinco grupos amplios de edad.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/censo_comunal.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` | Sí | — |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` | Sí | — |
| `poblacion_censada` | `INTEGER` | `223400` | Sí | — |
| `hombres` / `mujeres` | `INTEGER` | `"111200` / `112200"` | No | — |
| `razon_hombre_mujer` | `DOUBLE` | `99.11` | No | — |
| `poblacion_0_14` … `poblacion_65_mas` | `INTEGER` | `"5 tramos etarios"` | No | — |

<!-- END_DATASET_SCHEMA -->
