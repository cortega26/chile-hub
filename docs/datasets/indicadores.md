# indicadores

## Resumen

Serie de indicadores económicos diarios de alta reutilización para software, análisis y reporting.

Es una capa de conveniencia: evita que cada proyecto tenga que consultar o parsear por su cuenta valores como UF, dólar, euro o UTM.

## Estado

- `status`: activo en MVP
- `confidence`: Tier A/B
- `primary_join_key`: `fecha` + `codigo_indicador`
- `update_mode`: automatizado con refresh incremental, recuperación parcial y fallback

## Fuente

- consumo actual desde `mindicador.cl`
- procesamiento local desde [`src/extractors/bcentral_extractor.py`](https://github.com/cortega26/chile-hub/blob/main/src/extractors/bcentral_extractor.py)

## Método de acceso actual

- llamada HTTP a `https://mindicador.cl/api`
- refresh incremental del año en curso cuando ya existe staging
- si una serie falla, recuperación desde `data/raw` cuando hay snapshot utilizable
- si un código esperado ya no está en staging, reuso del último artifact publicado para no degradar silenciosamente la capa
- si no se logra construir un dataset usable, generación local de registros de fallback

## Señales operativas publicadas

El estado efectivo del último refresh ya no queda solo en staging; también se publica en los artifacts compartidos del hub.

Campos relevantes:

- `source_mode`: `live` o `fallback`
- `source_detail`: distingue live sano de recuperación parcial
- `indicator_codes`: lista de códigos esperados presentes en el artifact
- `indicator_delivery`: mapa compacto por código con estado `live`, `raw_recovery`, `preserved_existing` o `published_backfill`
- `warnings`: explica fallas parciales detectadas durante el refresh
- `notes`: deja trazabilidad compacta de series vacías, backfills y recuperaciones
- `degradation`, `drift` y `top_issue`: consolidan la acción operativa sugerida

Ejemplo real del estado actual:

- `source_mode`: `live`
- `source_detail`: `public_api_with_published_backfill`
- `indicator_delivery`: `ipc` quedó como `published_backfill`, mientras `dolar`, `euro`, `uf` y `utm` siguieron `live`
- `warnings`: la API devolvió serie vacía para `ipc/2026` y el hub reutilizó el último artifact publicado para ese código

## Por qué existe esta capa

Problemas que resuelve:

- consultas repetidas para indicadores de uso cotidiano
- inconsistencias entre formatos de fecha y nombres de indicador
- necesidad de una salida local y simple para pipelines o dashboards

## Salidas

- `data/normalized/indicadores.parquet`
- `data/normalized/indicadores_hoy.json`
- `data/staging/indicadores.metadata.json`
- tabla `indicadores` en `data/normalized/chile_data.duckdb`
- tabla `indicadores` en `data/normalized/chile_data.db`
- hoja `Indicadores Diarios` en `data/normalized/chile_data_latest.xlsx`

## Esquema actual

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

## Advertencias

- la salida puede provenir de datos live, de una mezcla live + recuperación parcial o de fallback local
- `indicadores_hoy.json` es un nombre orientado a consumo, pero el dataset puede incluir más de una fecha
- la cobertura histórica sigue siendo oportunista; no es todavía un archivo histórico oficial curado capa por capa
- la capa sirve bien para conveniencia operativa, pero no aún como fuente definitiva de archivo histórico
- el modo efectivo del último refresh queda registrado en `data/staging/indicadores.metadata.json` y consolidado en `data/normalized/pipeline_metadata.json`
- cuando una serie viene vacía desde la fuente, el hub prioriza no perder cobertura ya publicada y deja ese hecho visible en `warnings`, `notes`, `drift` y `top_issue`

## Notas legales

- la API actual es pública y está orientada a desarrolladores, pero no expone una licencia abierta explícita en la superficie revisada
- si esta capa se redistribuye fuera del repo, conviene revisar términos vigentes de la fuente y mantener atribución visible

## Recomendación de evolución

Esta capa puede seguir en MVP, pero todavía conviene mejorar en:

1. una estrategia más robusta para series que la API devuelve vacías aunque el resto del refresh siga sano
2. una política explícita para distinguir backfill desde raw local versus backfill desde artifact publicado
3. una estrategia histórica más clara para IPC y UTM frente a snapshots parciales del agregador
