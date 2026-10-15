# Perfil Territorial Comunal

> **Carril:** `stable_publishable` — incluido en el bundle público (Plan
> 084). Capa derivada en `build_dev_db.py` de 13 datasets upstream; su
> `freshness_policy` es `derivada`, no una fuente viva.

## Descripción

Tabla derivada con una fila por comuna que consolida la DPA, Censo 2024, hogares y viviendas, salud, educación, distritos electorales, finanzas municipales, resultados educacionales, resumen SIEDU, crecimiento natural (estadísticas vitales), viviendas autorizadas (permisos de edificación), MP2.5 promedio (calidad del aire) y tasas de pobreza SAE por ingresos y multidimensional (pobreza comunal).

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
- Pobreza SAE (2026-10): `tasa_pobreza_ingresos_ultimo_anio`, `tasa_pobreza_multidimensional_ultimo_anio` y `anio_pobreza` del último año con datos (nulos donde no hay estimación, p. ej. Antártica).

## Anexo: spike de densidad de empresas (2026-10, sin cambio al build)

Se evaluó agregar conteo de empresas por comuna desde `empresas.comuna_tributaria`
(1 628 433 filas, 0 nulas) contra `nombre_comuna_clean` vía `normalize_comuna_name()`:
match directo del **97,73 % de las filas** (330/346 valores distintos). Los 16
variantes no emparejados (36 940 filas, 2,27 %) son todos atribuibles con un mapa
de alias: abreviaturas (`est central`, `san vicente t-t`, `san fco de mostazal`),
espaciado/guiones (`con con` → `concon`, `til-til`, `llay-llay`), artículo
(`puerto natales` → `natales`, `la calera` → `calera`, esta última exige
desambiguación con Calera de Tango) y variante ortográfica de la fuente
(`trehuaco` → `treguaco`, código BCN de la comuna).

**Recomendación: diferir.** El join es técnicamente viable (~100 % con mapa de
~16 alias), pero `comuna_tributaria` es domicilio tributario ante el SII, no
ubicación física de la actividad: una columna headline de "empresas por comuna"
misatribuiría sedes y resultaría engañosa en la API insignia. Además el RES solo
cubre el régimen simplificado (Ley 20.659, desde 2013), no el stock total, y la
llave de texto libre exige mantener el mapa de alias en cada cosecha. Vía
alternativa a explorar: `comuna_social` (dirección social) como llave con mayor
validez semántica, o publicar la densidad como análisis separado con caveats
explícitos en vez de columna del perfil.

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
| `tasa_pobreza_ingresos_ultimo_anio` | `DOUBLE` | `9.0` | No | — |
| `tasa_pobreza_multidimensional_ultimo_anio` | `DOUBLE` | `19.5` | No | — |
| `anio_pobreza` | `INTEGER` | `2022` | No | — |

<!-- END_DATASET_SCHEMA -->
