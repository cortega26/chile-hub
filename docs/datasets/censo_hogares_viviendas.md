# Censo 2024: hogares y viviendas

Capa comunal oficial con viviendas censadas, viviendas particulares ocupadas y desocupadas, viviendas colectivas, hogares censados y promedio de personas por hogar.

## Fuente y licencia

- Fuente: Instituto Nacional de Estadisticas, Censo 2024.
- Formato de origen: XLSX oficial.
- Licencia: CC BY 4.0; atribucion requerida.
- Actualizacion esperada: decenal.

## Claves y schema

La clave primaria es `codigo_comuna` (`str`, cinco caracteres). Incluye tambien `codigo_region`, `codigo_provincia`, nombres territoriales y las seis medidas censales descritas arriba.

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
