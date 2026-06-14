# Censo comunal 2024

Perfil demografico de las 346 comunas de Chile construido desde los resultados oficiales del Censo de Poblacion y Vivienda 2024 del INE.

## Fuente y licencia

- Fuente: Instituto Nacional de Estadisticas, tabla D1 del Censo 2024.
- Formato de origen: XLSX oficial.
- Reutilizacion: CC BY 4.0; citar al INE.

## Schema

`codigo_region`, `nombre_region`, `codigo_provincia`, `nombre_provincia`, `codigo_comuna`, `nombre_comuna`, `poblacion_censada`, `hombres`, `mujeres`, `razon_hombre_mujer`, `poblacion_0_14`, `poblacion_15_29`, `poblacion_30_44`, `poblacion_45_64`, `poblacion_65_mas`.

Los codigos CUT son strings de longitud fija. Los grupos amplios de edad se derivan de los grupos quinquenales publicados por el INE.

## Uso

```python
from src.chile_hub import ChileHub

df = ChileHub().load_polars("censo_comunal")
```

```sql
SELECT nombre_comuna, poblacion_censada, poblacion_65_mas
FROM 'data/normalized/censo_comunal.parquet'
ORDER BY poblacion_censada DESC;
```

## Limitaciones

Es un corte censal de 2024, no una estimacion anual. No incluye microdatos ni variables que puedan aumentar el riesgo de reidentificacion.

## Changelog

- 2026-06: primera version comunal con sexo y cinco grupos amplios de edad.
