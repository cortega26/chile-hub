# Pobreza Comunal

Estimaciones de pobreza comunal por ingresos y multidimensional derivadas de la encuesta CASEN mediante metodología SAE (Estimación de Áreas Pequeñas), publicadas por el Observatorio Social del Ministerio de Desarrollo Social y Familia (MDS).

## Fuente y licencia

- **Fuente:** Observatorio Social — Ministerio de Desarrollo Social y Familia
- **Formato de origen:** XLSX por comuna (2 archivos: tasa de pobreza por ingresos e índice de pobreza multidimensional)
- **Reutilización:** Datos abiertos MDS con atribución requerida
- **URL:** https://observatorio.ministeriodesarrollosocial.gob.cl/pobreza-comunal-2022

## Esquema

`codigo_region`, `codigo_comuna`, `nombre_comuna`, `anio`, `dimension` (ingresos | multidimensional), `tasa` (%), `limite_inferior` (%), `limite_superior` (%), `metodologia` (SAE), `fuente`, `url_fuente`, `fecha_fuente`

## Uso

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("pobreza_comunal")

# Pobreza por ingresos 2022, comunas con mayor tasa
top = (
    df.filter(pl.col("anio") == 2022, pl.col("dimension") == "ingresos")
    .sort("tasa", descending=True)
    .head(10)
)
print(top)
```

```sql
SELECT codigo_comuna, nombre_comuna, tasa, limite_inferior, limite_superior
FROM 'data/normalized/pobreza_comunal.parquet'
WHERE anio = 2022 AND dimension = 'ingresos'
ORDER BY tasa DESC;
```

## Limitaciones

- **Cobertura parcial por diseño SAE:** comunas con muestra insuficiente en CASEN no reciben estimación. La columna `tasa` será NULL para esas comunas. No se imputan valores.
- **Intervalos de confianza:** la SAE produce estimaciones con incertidumbre. Los valores `limite_inferior` y `limite_superior` deben considerarse al comparar comunas o años.
- **Comparabilidad histórica limitada:** cambios metodológicos entre rondas CASEN (líneas de pobreza, factores de expansión) pueden afectar la comparabilidad inter-anual. La columna `metodologia` ayuda a identificar la ronda.
- **Frecuencia baja:** CASEN es bienal/trienal; las estimaciones comunales se publican con rezago de 1-2 años tras la encuesta.

## Registro de cambios

- v1 (2026-06-30): Primera versión. Datos de la ronda CASEN 2022 con estimaciones SAE de pobreza por ingresos y multidimensional.

## Clasificación de salud (ADR-014)

La cobertura SAE (345/346 comunas) es **parcial por diseño**: las comunas sin
muestra no tienen estimación. Ese warning está declarado como *esperado* en la
regla que lo emite, por lo que no cuenta como degradación accionable ni como
drift. El mensaje sigue listado en `warnings` de todos los artefactos.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/pobreza_comunal.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Santiago"` | Sí | — |
| `anio` | `INTEGER` | `2022` | Sí | PK |
| `dimension` | `VARCHAR` | `"ingresos"` / `"multidimensional"` | Sí | PK |
| `tasa` | `DOUBLE` | `15.3` | Sí | — |
| `limite_inferior` | `DOUBLE` | `12.1` | Sí | — |
| `limite_superior` | `DOUBLE` | `18.9` | Sí | — |
| `metodologia` | `VARCHAR` | `"SAE"` | Sí | — |
| `fuente` | `VARCHAR` | `"Observatorio Social — MDS"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
