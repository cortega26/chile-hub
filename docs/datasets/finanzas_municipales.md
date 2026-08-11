# Finanzas Municipales

## Descripción

Indicadores financieros municipales anuales provenientes de SINIM/SUBDERE, normalizados por comuna para cruces territoriales.

## Fuente y licencia

- Fuente: SINIM - SUBDERE
- URL: https://datos.sinim.gov.cl/datos_municipales.php
- Reutilización: datos públicos municipales con atribución; términos sujetos a revisión operativa.

## Esquema

| Campo | Tipo | Descripción |
|---|---|---|
| `anio` | integer | Año presupuestario. |
| `codigo_comuna` | string | Código CUT comunal de 5 caracteres. |
| `nombre_comuna` | string | Nombre de la comuna. |
| `ingresos_totales` | float | Ingresos municipales totales. |
| `gastos_totales` | float | Gastos municipales totales. |
| `ingresos_propios_permanentes` | float | Ingresos propios permanentes. |
| `fondo_comun_municipal` | float | Aportes o ingresos asociados al Fondo Común Municipal. |
| `gasto_personal` | float | Gasto en personal. |
| `gasto_inversion` | float | Gasto de inversión. |

## Uso

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("finanzas_municipales")
```

```sql
SELECT anio, codigo_comuna, ingresos_totales, gastos_totales
FROM 'data/normalized/finanzas_municipales.parquet';
```

## Limitaciones

La primera versión usa una capa fallback curada hasta configurar una exportación directa estable desde SINIM. Los metadatos `source_mode` y `source_detail` indican si el build es publicable como live.

## Registro de cambios

- v1: Dataset agregado al pipeline con validación centralizada y artefactos Parquet/JSON/DuckDB/SQLite/Excel.

## Clasificación de salud (ADR-014)

El contrato declara `coverage_policy: "partial_expected"`: SINIM no publica el
universo completo de municipios en cada corte. Cuando la cobertura resulta
`partial`, el artefacto marca `coverage.expected: true` y el dataset **no**
cuenta como drift — la parcialidad es de diseño, no una degradación.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/finanzas_municipales.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `anio` | `INTEGER` | `2024` | Sí | PK |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `ingresos_totales` / `gastos_totales` | `DOUBLE` | `245000000000.0` | No | — |
| `ingresos_propios_permanentes` | `DOUBLE` | `162000000000.0` | No | — |
| `fondo_comun_municipal` | `DOUBLE` | `39000000000.0` | No | — |

<!-- END_DATASET_SCHEMA -->
