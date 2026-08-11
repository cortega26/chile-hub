# Censo 2024: hogares y viviendas

Capa comunal oficial con viviendas censadas, viviendas particulares ocupadas y desocupadas, viviendas colectivas, hogares censados y promedio de personas por hogar.

## Fuente y licencia

- Fuente: Instituto Nacional de Estadísticas, Censo 2024.
- Formato de origen: XLSX oficial.
- Licencia: CC BY 4.0; atribución requerida.
- Actualización esperada: decenal.

## Claves y esquema

La clave primaria es `codigo_comuna` (`str`, cinco caracteres). Incluye también `codigo_region`, `codigo_provincia`, nombres territoriales y las seis medidas censales descritas arriba.

## Uso

```python
from chile_hub import ChileHub

df = ChileHub().load_polars("censo_hogares_viviendas")
```

```sql
SELECT nombre_comuna, hogares_censados, promedio_personas_hogar
FROM 'data/normalized/censo_hogares_viviendas.parquet'
ORDER BY hogares_censados DESC;
```

## Limitaciones

Los valores representan el Censo 2024 y no deben interpretarse como estimaciones intercensales.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/censo_hogares_viviendas.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `viviendas_censadas` | `INTEGER` | `85000` | Sí | — |
| `viviendas_particulares_ocupadas` | `INTEGER` | `75000` | No | — |
| `viviendas_colectivas` | `INTEGER` | `200` | No | — |
| `hogares_censados` | `INTEGER` | `73000` | Sí | — |
| `promedio_personas_hogar` | `DOUBLE` | `3.06` | No | — |

<!-- END_DATASET_SCHEMA -->
