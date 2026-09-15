# Estadísticas Vitales

Nacimientos y defunciones por comuna de residencia y sexo, desde los Anuarios de Estadísticas Vitales del Instituto Nacional de Estadísticas (INE). Serie anual de anuarios definitivos desde 2010.

## Fuente y licencia

- **Fuente:** Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales
- **Formato de origen:** 1 XLSX por año (anuario definitivo, tabla 1.2.2-04 "por sexo, según región, provincia y comuna de residencia")
- **Reutilización:** CC BY 4.0 con atribución requerida
- **URL:** https://www.ine.gob.cl/estadisticas-por-tema/demografia-y-poblacion/estadisticas-vitales

## Esquema

`anio`, `codigo_region`, `codigo_comuna`, `nombre_comuna`, `evento` (nacimiento | defuncion), `sexo` (hombre | mujer | indeterminado | total), `cantidad`, `estado_dato` (definitivo), `fuente`, `url_fuente`, `fecha_fuente`

Grano: una fila por (año, comuna, evento, sexo). Los anuarios 2010-2020 publican totales sin split de sexo (`sexo = "total"`); desde 2021 el INE publica el split hombre/mujer/indeterminado. El crecimiento natural comunal se deriva como nacimientos menos defunciones; no se almacena como fila para no mezclar grano fuente con grano derivado.

## Uso

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("estadisticas_vitales")

# Crecimiento natural por comuna 2023
nat = (
    df.filter(pl.col("anio") == 2023)
    .group_by("codigo_comuna")
    .agg(
        (pl.col("cantidad").filter(pl.col("evento") == "nacimiento").sum()
         - pl.col("cantidad").filter(pl.col("evento") == "defuncion").sum()
        ).alias("crecimiento_natural")
    )
    .sort("crecimiento_natural")
)
print(nat)
```

```sql
SELECT anio, sum(cantidad) AS nacimientos
FROM 'data/normalized/estadisticas_vitales.parquet'
WHERE evento = 'nacimiento'
GROUP BY 1 ORDER BY 1;
```

## Limitaciones

- **Solo anuarios definitivos:** los boletines provisionales y coyunturales del INE publican agregados nacional/región sin desglose comunal, por lo que no entran al dataset. La columna `estado_dato` existe para futuros definitivos y hoy vale siempre `"definitivo"`. El último año disponible tiene ~1 año de rezago (anuarios definitivos).
- **Sin tasas:** se publican conteos crudos. Las tasas (por mil habitantes) requieren denominadores de proyecciones de población que cambian de base censal; calcularlas es decisión metodológica del consumidor.
- **Layouts heterogéneos por año:** la tabla 1.2.2-04 cambió de formato entre 2010 y 2023 (totales vs split por sexo, convención de indentado, archivos separados en 2016). El extractor normaliza a un único esquema; los totales nacionales de cada año se reconcilian contra la fila TOTAL del anuario y quedan registrados en `data/staging/estadisticas_vitales.metadata.json`.
- **Residencia habitual:** los hechos se asignan por comuna de residencia habitual de la madre (nacimientos) o del fallecido (defunciones), no por lugar de ocurrencia.

## Registro de cambios

- v1 (2026-09-14): Primera versión. Anuarios definitivos 2010-2023, 346 comunas, cobertura total verificada contra totales nacionales publicados.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/estadisticas_vitales.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `anio` | `INTEGER` | `2023` | Sí | PK |
| `codigo_region` | `VARCHAR(2)` | `"13"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Santiago"` | Sí | — |
| `evento` | `VARCHAR` | `"nacimiento"` | Sí | PK |
| `sexo` | `VARCHAR` | `"hombre"` | Sí | PK |
| `cantidad` | `INTEGER` | `4521` | Sí | — |
| `estado_dato` | `VARCHAR` | `"definitivo"` | Sí | — |
| `fuente` | `VARCHAR` | `"Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales"` | Sí | — |
| `url_fuente` | `VARCHAR` | `"https://www.ine.gob.cl/docs/default-source/.../2023/....xlsx"` | Sí | — |
| `fecha_fuente` | `VARCHAR` | `"2026-09-14"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
