# Establecimientos de salud

Directorio vigente de establecimientos de salud publicado por el Ministerio de Salud.

## Fuente y licencia

- Fuente: MINSAL mediante datos.gob.cl.
- Formato de origen: CSV separado por punto y coma.
- Licencia: CC0.
- Frecuencia declarada por la fuente: mensual.

## Schema

`codigo_establecimiento`, `nombre_establecimiento`, `tipo_establecimiento`, `dependencia_administrativa`, `nivel_atencion`, `codigo_region`, `nombre_region`, `codigo_comuna`, `nombre_comuna`, `tiene_servicio_urgencia`, `tipo_urgencia`, `latitud`, `longitud`, `estado_funcionamiento`.

## Uso

```python
from src.chile_hub import ChileHub

df = ChileHub().load_polars("establecimientos_salud")
```

```sql
SELECT codigo_comuna, count(*) AS establecimientos
FROM 'data/normalized/establecimientos_salud.parquet'
GROUP BY codigo_comuna
ORDER BY establecimientos DESC;
```

## Limitaciones

El directorio mezcla establecimientos publicos y privados y conserva las clasificaciones entregadas por MINSAL. La ausencia de coordenadas no se imputa.

## Changelog

- 2026-06: primera version con identidad, clasificacion, urgencia, estado y coordenadas.
