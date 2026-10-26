# Precipitaciones DGAC — serie histórica diaria

**Capa:** `precipitaciones_dgac`. **Granularidad:** `(fecha, id_estacion)`.
**Estado de integración:** `stable_publishable` desde el 2026-10-25. Se publica
en el bundle y tiene tarjeta propia en el catálogo del sitio; su reevaluación
(`review_by`) está fijada al 2027-01-15 en `data/source_registry.json`.

## Fuente y reutilización

Dirección General de Aeronáutica Civil (DGAC), [datos.gob.cl](https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil).
La serie agrega 143 archivos-mes abiertos (CC BY/CC0) desde enero 2013 hasta
junio 2026, **sin continuidad total**, a partir de 24 paquetes CKAN.

**Nunca redistribuimos** los períodos 2014 ni enero-junio 2015, que solo
identificamos en un paquete legado **CC-NC**. El mes enero 2017 no es lluvia:
se publicó bajo ese nombre un CSV con `T.Maxima`/`T.Minima` y permanece en
cuarentena. El segundo semestre de 2026 no constaba como publicado al verificar
la fuente. No hay imputación de lluvia ni asociación arbitraria estación-comuna.

La fuente oficial otorga las licencias por **archivo/paquete**; el campo
`licencia_fuente`, la URL del recurso y el archivo sidecar de extracción
permiten atribuir y comprobar cada observación. La licencia MIT del software
**no sustituye** las licencias CC BY/CC0 de los datos.

## Datos y ejemplos

En la cosecha comprobada el 17 de octubre de 2026: **141.436 filas**,
**33 estaciones** y **143 meses** aprovechables. El número puede cambiar si
la DGAC revisa las publicaciones. Las estaciones y fechas no siempre forman
series densas/comparables: antes de estimar tendencias climáticas, verificar
cobertura por estación y posibles cambios instrumentales.

```python
from chile_hub import ChileHub
import polars as pl

df = ChileHub().load_polars("precipitaciones_dgac")
lluvia_observada = df.filter(pl.col("precipitacion_mm").is_not_null())
totales = lluvia_observada.group_by("id_estacion").agg(
    pl.col("precipitacion_mm").sum().alias("total_mm")
)
print(totales)
```

```sql
SELECT id_estacion, EXTRACT(YEAR FROM CAST(fecha AS DATE)) AS anio,
       SUM(precipitacion_mm) AS total_mm
FROM 'data/normalized/precipitaciones_dgac.parquet'
WHERE precipitacion_mm IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 2;
```

**Interpretación:** `precipitacion_mm = null` es ausencia de medida,
**no** cero. `latitud_dms` y `altitud_m` se conservan del origen;
no existe longitud verificada ni código CUT en la fuente seleccionada.

**Procedencia y controles:** la [documentación de extracción histórica](../research-dgac-precipitaciones.md)
incluye el SHA-256 del CSV, hashes por mes, fechas, cobertura,
duplicados resueltos e incidencias; [CI DGAC
#38991196698](https://github.com/cortega26/chile-hub/actions/runs/38991196698).

## Refresco y mantenimiento

El registro canónico utiliza `access_method: api` y
`fallback_policy: none`, valores admitidos por los controles de publicación.
En concreto, `api` identifica consultas al catálogo CKAN oficial de
datos.gob.cl y descargas de archivos CSV por recurso; `none` prohíbe
sustituir una descarga fallida por datos ficticios o un snapshot no validado.

El extractor de producción `src/extractors/precipitaciones_dgac_extractor.py`
reutiliza el parser DGAC auditado y escribe en `data/staging/` solo al
completar toda la cobertura aprobada. El workflow de actualización
trimestral conservará un snapshot auténtico, sin datos de muestra.
Una publicación nueva requiere actualizar la lista de paquetes verificados
y los tests; el script no fabrica datos de meses ausentes.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/precipitaciones_dgac.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `fecha` | `VARCHAR` | `"2013-01-01"` | Sí | PK |
| `id_estacion` | `VARCHAR(6)` | `"180005"` | Sí | PK |
| `nombre_estacion` | `VARCHAR` | `"Chacalluta, Arica Ap."` | Sí | — |
| `latitud_dms` | `VARCHAR` | `"18° 21' 20'' S"` | Sí | — |
| `altitud_m` | `DOUBLE` | `50` | Sí | — |
| `precipitacion_mm` | `DOUBLE` | `0.5` | Sí | — |
| `url_fuente` | `VARCHAR` | `"https://datos.gob.cl/dataset/.../download/precipitacion_012013.csv"` | Sí | — |
| `licencia_fuente` | `VARCHAR` | `"cc-by"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
