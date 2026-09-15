# Perfil Territorial Comunal

> **Carril:** `stable_publishable` — incluido en el bundle público (Plan
> 084). Capa derivada en `build_dev_db.py` de 12 datasets upstream; su
> `freshness_policy` es `derivada`, no una fuente viva.

## Descripción

Tabla derivada con una fila por comuna que consolida la DPA, Censo 2024, hogares y viviendas, salud, educación, distritos electorales, finanzas municipales, resultados educacionales, resumen SIEDU, crecimiento natural (estadísticas vitales), viviendas autorizadas (permisos de edificación) y MP2.5 promedio (calidad del aire).

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
| `crecimiento_natural_ultimo_anio` | `INTEGER` | `12` | No | — |
| `anio_estadisticas_vitales` | `INTEGER` | `2023` | No | — |
| `viviendas_autorizadas_ultimo_anio` | `INTEGER` | `2451` | No | — |
| `superficie_autorizada_m2_ultimo_anio` | `INTEGER` | `187320` | No | — |
| `anio_permisos_edificacion` | `INTEGER` | `2023` | No | — |
| `mp25_promedio_ultimo_anio` | `DOUBLE` | `18.4` | No | — |
| `anio_calidad_aire` | `INTEGER` | `2026` | No | — |

<!-- END_DATASET_SCHEMA -->
