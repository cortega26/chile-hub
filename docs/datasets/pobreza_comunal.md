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
