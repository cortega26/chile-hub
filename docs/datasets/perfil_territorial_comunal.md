# Perfil Territorial Comunal

> **Carril:** `candidate` — NO incluido en el bundle público. Revisión de
> carril programada (`review_by` 2026-09-18, ver `data/source_registry.json`).

## Descripción

Tabla derivada con una fila por comuna que consolida la DPA, Censo 2024, hogares y viviendas, salud, educación, distritos electorales, finanzas municipales, resultados educacionales y resumen SIEDU.

## Fuente y licencia

- Fuente: derivada de datasets validados de chile-hub.
- Reutilización: heredada de las fuentes abiertas de origen; requiere atribución.

## Esquema

Incluye campos DPA canónicos (`codigo_comuna`, `nombre_comuna`, región, provincia, coordenadas), métricas censales, conteos de establecimientos, distritos electorales y métricas headline de las capas nuevas.

## Uso

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("perfil_territorial_comunal")
```

```sql
SELECT codigo_comuna, nombre_comuna, establecimientos_salud_total
FROM 'data/normalized/perfil_territorial_comunal.parquet';
```

## Limitaciones

Las columnas derivadas de capas parciales pueden venir nulas o en cero según corresponda. SIEDU resume solo comunas presentes en la fuente urbana.

## Registro de cambios

- v1: Perfil derivado agregado con validación de 346 comunas únicas.

## Clasificación de salud (ADR-014)

Esta capa es **derivada** de capas ya validadas. Su `source_mode` se calcula a
partir de los upstreams y sólo cae a `fallback` si alguno lo es de verdad:
`monthly` (p. ej. `finanzas_municipales`) cuenta como fuente genuina, no como
respaldo. Con 346/346 comunas y cero warnings, su `drift_status` es `healthy`.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/perfil_territorial_comunal.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `poblacion_censada` | `INTEGER` | `223400` | Sí | — |
| `establecimientos_salud_total` | `INTEGER` | `140` | Sí | — |
| `establecimientos_educacionales_total` | `INTEGER` | `410` | Sí | — |
| `distrito_electoral` | `VARCHAR` | `"10"` | No | — |

<!-- END_DATASET_SCHEMA -->
