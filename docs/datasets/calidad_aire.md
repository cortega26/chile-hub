# Calidad del Aire

Promedios diarios de contaminantes atmosféricos (MP2.5, MP10, SO2, NO2, CO, O3) por estación de monitoreo, desde el Sistema de Información Nacional de Calidad del Aire (SINCA) del Ministerio del Medio Ambiente.

## Fuente y licencia

- **Fuente:** SINCA — Ministerio del Medio Ambiente (API JSON pública + CSV por estación)
- **Formato de origen:** JSON diario con inventario de estaciones y series horarias de 24 h
- **Reutilización:** datos públicos MMA sin licencia explícita; citar fuente oficial
- **URL:** https://sinca.mma.gob.cl/

## Esquema

`fecha` (YYYY-MM-DD), `id_estacion`, `nombre_estacion`, `codigo_region`, `codigo_comuna`, `nombre_comuna`, `latitud`, `longitud`, `codigo_contaminante` (mp25 | mp10 | so2 | no2 | co | o3), `nombre_contaminante`, `unidad` (ug/m3 | ug/m3N | ppbv | ppmv), `valor_promedio_diario`, `valor_max_horario`, `horas_validas`, `estado_dato` (definitivo | provisional), `fuente`, `url_fuente`, `fecha_fuente`

Grano: una fila por (fecha, estación, contaminante) con días completos o parciales según horas válidas.

## Uso

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("calidad_aire")

# Peor MP2.5 diario por comuna (última fecha disponible)
ultima = df["fecha"].max()
peor = (
    df.filter(
        (pl.col("fecha") == ultima) & (pl.col("codigo_contaminante") == "mp25")
    )
    .sort("valor_promedio_diario", descending=True)
    .head(10)
)
print(peor)
```

```sql
SELECT fecha, codigo_comuna, avg(valor_promedio_diario) AS mp25
FROM 'data/normalized/calidad_aire.parquet'
WHERE codigo_contaminante = 'mp25'
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;
```

## Limitaciones

- **Cobertura parcial por diseño (~19% de comunas):** solo las comunas con estación de monitoreo tienen datos (~65 de 346). Ausencia de una comuna NO significa aire limpio, sino sin medición. No interpolar.
- **Serie incremental desde la primera cosecha:** el JSON del SINCA solo expone 24 h; no hay backfill histórico. La serie crece un día por build diario.
- **Validación nivel 1:** los datos en línea son provisorios y el operador puede revisarlos; `estado_dato` es `"provisional"` para la fecha en curso y `"definitivo"` para días cerrados.
- **Representatividad puntual:** la medición representa el volumen de aire en el punto de la estación, no necesariamente toda la comuna (especialmente comunas extensas o con varias fuentes).
- **Unidades por contaminante:** MP2.5/MP10 en µg/m³, SO2 en µg/m³N, NO2/O3 en ppbv, CO en ppmv. No comparar valores crudos entre contaminantes.

## Registro de cambios

- v1 (2026-09-15): Primera versión. Serie incremental desde 2026-09-13, ~125 estaciones, 6 contaminantes.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/calidad_aire.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `fecha` | `VARCHAR` | `"2026-09-14"` | Sí | PK |
| `id_estacion` | `VARCHAR` | `"271"` | Sí | PK |
| `nombre_estacion` | `VARCHAR` | `"Quilicura"` | Sí | — |
| `codigo_region` | `VARCHAR(2)` | `"13"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"13144"` | Sí | — |
| `nombre_comuna` | `VARCHAR` | `"Quilicura"` | Sí | — |
| `latitud` | `DOUBLE` | `-33.36` | Sí | — |
| `longitud` | `DOUBLE` | `-70.73` | Sí | — |
| `codigo_contaminante` | `VARCHAR` | `"mp25"` | Sí | PK |
| `nombre_contaminante` | `VARCHAR` | `"MP 2,5"` | Sí | — |
| `unidad` | `VARCHAR` | `"ug/m3"` | Sí | — |
| `valor_promedio_diario` | `DOUBLE` | `18.4` | Sí | — |
| `valor_max_horario` | `DOUBLE` | `42.0` | Sí | — |
| `horas_validas` | `INTEGER` | `24` | Sí | — |
| `estado_dato` | `VARCHAR` | `"definitivo"` | Sí | — |
| `fuente` | `VARCHAR` | `"SINCA — Ministerio del Medio Ambiente"` | Sí | — |
| `url_fuente` | `VARCHAR` | `"https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/"` | Sí | — |
| `fecha_fuente` | `VARCHAR` | `"2026-09-15"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
