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

- consumo actual desde `mindicador.cl` (agregador; fuente original BCCh e INE)
- **override de IPC desde el INE** (`src/extractors/ine_ipc.py`): cuando
  mindicador.cl no entrega la serie `ipc` del año en curso (muerta upstream
  desde 2025-12, issue #43), la variación mensual se toma de la página pública
  del INE — la fuente autoritativa — antes de recurrir al backfill. El patrón
  de parseo (anclado al `<h1>` del IPC) es el validado en el proyecto Monedario
  desde 2026-05-16.
- procesamiento local desde [`src/extractors/bcentral_extractor.py`](https://github.com/cortega26/chile-hub/blob/main/src/extractors/bcentral_extractor.py)

## Método de acceso actual

- llamada HTTP a `https://mindicador.cl/api`
- refresh incremental del año en curso cuando ya existe staging
- si una serie falla, recuperación desde `data/raw` cuando hay snapshot utilizable
- si `ipc` del año en curso viene vacío o falla, override desde el INE
  (`https://www.ine.gob.cl/.../indice-de-precios-al-consumidor`) — solo para
  el año en curso (el INE publica el último mes, no historial)
- si un código esperado ya no está en staging, reuso del último artifact publicado para no degradar silenciosamente la capa
- si no se logra construir un dataset usable, generación local de registros de fallback

## Señales operativas publicadas

El estado efectivo del último refresh ya no queda solo en staging; también se publica en los artifacts compartidos del hub.

Campos relevantes:

- `source_mode`: `live` o `fallback`
- `source_detail`: distingue live sano de recuperación parcial
- `indicator_codes`: lista de códigos esperados presentes en el artifact
- `indicator_delivery`: mapa compacto por código con estado `live`, `raw_recovery`, `preserved_existing`, `ine_override` o `published_backfill`
- `warnings`: explica fallas parciales detectadas durante el refresh
- `notes`: deja trazabilidad compacta de series vacías, overrides INE, backfills y recuperaciones
- `degradation`, `drift` y `top_issue`: consolidan la acción operativa sugerida

Ejemplo real del estado actual:

- `source_mode`: `live`
- `source_detail`: `public_api_with_published_backfill`
- `indicator_delivery`: `ipc` quedó como `ine_override` (serie tomada de la
  fuente autoritativa INE cuando mindicador.cl no la entrega — Plan 069),
  mientras `dolar`, `euro`, `uf` y `utm` siguieron `live`
- `warnings`: la API devolvió serie vacía para `ipc/2026` y el hub usó el
  override del INE para ese código

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

## Vigencia de las series (ADR-016)

`pipeline_metadata.json` expone `indicator_max_date` e `indicator_age_days` por
serie: la antigüedad se mide sobre el **dato entregado**, no sobre cuándo corrió
el extractor. Las edades negativas son normales — la UF y la UTM se publican por
adelantado.

Si una serie se entrega vía `published_backfill` (reuso del último artefacto
publicado ante un hueco de la fuente) y su último dato supera el umbral de su
cadencia — 70 días para mensuales (UTM, IPC), 10 para diarias (UF, dólar, euro)
—, el gate de publicación **rechaza el build** hasta que alguien confirme el
estado contra la fuente y use `--allow-stale-backfills`.

El delivery `ine_override` (serie tomada del INE, la fuente autoritativa del
IPC) **no** es un backfill: no dispara el gate de edad ni se marca como unsafe
— es la provenance honesta de un dato nuevo, visible en el build (Plan 069).


**Estado conocido**: la serie `ipc` no recibe datos nuevos desde 2025-12-01. El
diagnóstico upstream está abierto en el issue #43.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/indicadores.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `fecha` | `DATE` | `"2026-05-30"` | Sí | PK |
| `codigo_indicador` | `VARCHAR` | `"uf"` | Sí | PK |
| `valor` | `DOUBLE` | `39420.5` | Sí | — |

<!-- END_DATASET_SCHEMA -->
