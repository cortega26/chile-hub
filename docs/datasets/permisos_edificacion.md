# Permisos de Edificación

Viviendas autorizadas en unidades y superficie (m²) por comuna y año —total, casas y departamentos— desde las estadísticas de permisos de edificación del Centro de Estudios de Ciudad y Territorio (CEDOC) del MINVU. Serie anual desde 2002.

## Fuente y licencia

- **Fuente:** MINVU — Centro de Estudios de Ciudad y Territorio (CEDOC), en base a permisos otorgados por las Direcciones de Obras Municipales e INE
- **Formato de origen:** 1 XLSX ("Viviendas unidades y superficie según año y comuna", 6 hojas: número/m² × total/casas/departamentos)
- **Reutilización:** uso autorizado citando la fuente (política del CEDOC desde 2023)
- **URL:** https://centrodeestudios.minvu.gob.cl/repositorio/categoria/permisos-de-edificacion

## Modo de extracción (`monthly`)

El archivo se sirve desde `catalogo.minvu.cl`, que **bloquea a los runners de
GitHub** (medido 2026-09-25): el TCP conecta pero el handshake TLS se corta para
todos los clientes probados — curl/requests (OpenSSL), curl_cffi (Firefox,
Safari, Chrome, Edge, Tor) y browsers stealth de scrapling
(`StealthyFetcher`/`DynamicFetcher`). Es filtrado por IP de origen, no por
fingerprint: ninguna librería cliente lo sortea.

Por eso el extractor reutiliza un **snapshot crudo versionado** en
`data/raw/minvu_permisos_edificacion_anual_*.xlsx` y lo publica con
`source_mode: monthly` (fuente genuina no re-fetcheada en cada build diario,
mismo contrato que `finanzas_municipales`). La frescura usa la fecha del
snapshot (política de 1080 h); si la descarga live vuelve a funcionar desde el
runner, el modo regresa solo a `live`. Para refrescar el snapshot desde una red
sin bloqueo: `python src/extractors/permisos_edificacion_extractor.py` y
commitear el XLSX nuevo en `data/raw/`.

## Esquema

`anio`, `codigo_region`, `codigo_comuna`, `nombre_comuna`, `unidades_total`, `superficie_m2_total`, `unidades_casas`, `superficie_m2_casas`, `unidades_departamentos`, `superficie_m2_departamentos`, `estado_dato` (definitivo | provisional), `fuente`, `url_fuente`, `fecha_fuente`

Grano: una fila por (año, comuna). `unidades_total` es siempre la suma exacta de casas + departamentos (igual en superficie); la validación lo exige como invariante.

## Uso

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("permisos_edificacion")

# Actividad constructora por comuna 2023 (proxy de dinamismo local)
top = df.filter(pl.col("anio") == 2023).sort("unidades_total", descending=True).head(10)
print(top)
```

```sql
SELECT anio, sum(unidades_total) AS viviendas_autorizadas
FROM 'data/normalized/permisos_edificacion.parquet'
GROUP BY 1 ORDER BY 1;
```

## Limitaciones

- **Solo vivienda residencial:** cubre casas y departamentos autorizados; no incluye edificación no habitacional (industria, comercio, servicios). Para actividad constructora total, complementar con INE.
- **Intención de construir, no construcción efectiva:** el permiso mide la intención (Formulario Único de Edificación); una fracción no se ejecuta o se ejecuta años después.
- **Años provisionales:** los años marcados `(*)` en la fuente y el último año de la serie (aún en curso) van con `estado_dato = "provisional"` y se revisan al alza en versiones siguientes. No mezclar con definitivos sin ponderar.
- **Serie histórica de Ñuble:** las comunas de Ñuble aparecen bajo "Biobío" y bajo "Ñuble (ex-Biobío)" con series complementarias (corte 2018); el extractor las fusiona sumando. Los totales nacionales se reconcilian contra la fila "Total País" del archivo.
- **Año parcial en curso:** el último año trae datos a julio (~7 meses); comparar contra años completos subestima la actividad.

## Registro de cambios

- v1 (2026-09-15): Primera versión. Serie 2002-2026, 346 comunas, cobertura total verificada contra totales nacionales del archivo.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/permisos_edificacion.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `anio` | `INTEGER` | `2023` | Sí | PK |
| `codigo_region` | `VARCHAR(2)` | `"13"` | Sí | — |
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Santiago"` | Sí | — |
| `unidades_total` | `INTEGER` | `2451` | Sí | — |
| `superficie_m2_total` | `INTEGER` | `187320` | Sí | — |
| `unidades_casas` | `INTEGER` | `312` | Sí | — |
| `superficie_m2_casas` | `INTEGER` | `24810` | Sí | — |
| `unidades_departamentos` | `INTEGER` | `2139` | Sí | — |
| `superficie_m2_departamentos` | `INTEGER` | `162510` | Sí | — |
| `estado_dato` | `VARCHAR` | `"definitivo"` | Sí | — |
| `fuente` | `VARCHAR` | `"MINVU — Centro de Estudios de Ciudad y Territorio (CEDOC)"` | Sí | — |
| `url_fuente` | `VARCHAR` | `"https://catalogo.minvu.cl/cgi-bin/koha/opac-retrieve-file.pl?id=..."` | Sí | — |
| `fecha_fuente` | `VARCHAR` | `"2026-09-15"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
