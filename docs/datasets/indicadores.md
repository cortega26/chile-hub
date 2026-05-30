# indicadores

## Resumen

Serie de indicadores económicos diarios de alta reutilización para software, análisis y reporting.

Es una capa de conveniencia: evita que cada proyecto tenga que consultar o parsear por su cuenta valores como UF, dólar, euro o UTM.

## Estado

- `status`: activo en MVP
- `confidence`: Tier A/B
- `primary_join_key`: `fecha` + `codigo_indicador`
- `update_mode`: automatizado con fallback

## Fuente

- consumo actual desde `mindicador.cl`
- procesamiento local desde [`src/extractors/bcentral_extractor.py`](/home/carlos/VS_Code_Projects/chile-hub/src/extractors/bcentral_extractor.py:1)

## Método de acceso actual

- llamada HTTP a `https://mindicador.cl/api`
- si falla, generación local de registros de fallback

## Por qué existe esta capa

Problemas que resuelve:

- consultas repetidas para indicadores de uso cotidiano
- inconsistencias entre formatos de fecha y nombres de indicador
- necesidad de un output local y simple para pipelines o dashboards

## Outputs

- `data/normalized/indicadores.parquet`
- `data/normalized/indicadores_hoy.json`
- `data/staging/indicadores.metadata.json`
- tabla `indicadores` en `data/normalized/chile_data.duckdb`
- tabla `indicadores` en `data/normalized/chile_data.db`
- hoja `Indicadores Diarios` en `data/normalized/chile_data_latest.xlsx`

## Schema actual

Fuente observada: `data/normalized/chile_data.duckdb`

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `fecha` | `DATE` | Fecha del valor publicado |
| `codigo_indicador` | `VARCHAR` | Identificador corto del indicador |
| `valor` | `DOUBLE` | Valor numérico normalizado |

## Indicadores considerados hoy

- `uf`
- `dolar`
- `euro`
- `utm`
- `ipc`

## Normalizaciones aplicadas

- truncado de fecha ISO a `YYYY-MM-DD`
- renombre de claves de la API a un código corto canónico
- casteo consistente a `DATE`, `VARCHAR` y `DOUBLE`
- ordenamiento por `fecha` y `codigo_indicador`

## Join value

Cruces sugeridos:

- `fecha` para análisis temporales
- `codigo_indicador` para pivoteo o series comparativas

## Caveats

- el output puede provenir de datos reales o de fallback local si la API falla
- `indicadores_hoy.json` es un nombre orientado a consumo, pero el dataset puede incluir más de una fecha
- la cobertura histórica es limitada; hoy no es una serie larga oficial curada
- la capa sirve bien para conveniencia operativa, pero no aún como fuente definitiva de archivo histórico
- el modo efectivo del último refresh queda registrado en `data/staging/indicadores.metadata.json` y consolidado en `data/normalized/pipeline_metadata.json`

## Notas legales

- la fuente operativa actual es pública, pero conviene documentar de forma más estricta la política de redistribución si esta capa pasa a publicarse fuera del repo

## Recomendación de evolución

Esta capa puede seguir en MVP, pero debería mejorar en:

1. separación explícita entre modo live y modo fallback
2. metadata de frescura y origen del último refresh
3. política clara para series históricas frente a snapshot diario
