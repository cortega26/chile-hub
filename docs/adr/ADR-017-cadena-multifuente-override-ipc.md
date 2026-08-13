# ADR-017: Cadena multi-fuente para el IPC — override del INE como último recurso

**Fecha:** 2026-08-12
**Estado:** proposed
**Decision:** La serie `ipc` de `indicadores` se entrega por una cadena
multi-fuente con override de último recurso: la serie histórica viene del
agregador (mindicador.cl) y, cuando el IPC del año en curso falta o falla,
`ine_ipc.py` scrapea la variación mensual de la página pública del INE
(fuente autoritativa del índice). El delivery queda **visible** como
`ine_override` (Plan 069) para que el gate de publicación evalúe el dato
real, y la edad del dato entregado se mide igual que un backfill (ADR-016).

## Contexto

mindicador.cl dejó de publicar la serie IPC en diciembre de 2025 (issue #43).
El INE es el emisor original del índice y publica la variación mensual en su
página pública. El override replica el patrón validado del proyecto Monedario
(`ineIpc.ts`, observado estable desde 2026-05-16): ancla el match al
encabezado `<h1>` del IPC para no tomar la tarjeta de un índice hermano
(ICT/IPP) si el INE reordena el layout (refinado en el Plan 075).

AGENTS.md §10 prohíbe el scraping HTML frágil como **fuente principal** —
esta es la excepción de último recurso: la fuente principal sigue siendo
mindicador.cl, y solo cuando una serie mensual esperada llega vacía o falla
se consulta al INE. El HTML no se república: se extrae el dato y su fecha.

La dependencia de la cadena diaria sobre un parseo HTML anclado era
**silenciosa**: el publish de `indicadores` podía romperse ante un rediseño
de `ine.gob.cl` sin señal previa. Este ADR la hace visible y decide el
escape hatch.

## Decision

### 1. La cadena multi-fuente es el diseño, no un parche

`bcentral_extractor.py` procesa en orden: serie del agregador → fallback a
staging/raw → **override INE** → backfill del artefacto publicado. El
override gana sobre el backfill en la etiqueta de delivery (`ine_override`
se asigna después de `published_backfill` — Plan 069), porque etiquetar un
valor recién scrapeado del INE como "reutilización del artefacto publicado"
sería falso y escondería el dato real al gate.

### 2. El delivery es visible y la edad se gatea (ADR-016)

`indicator_delivery.ipc = "ine_override"` expone el origen a
`verify_pipeline.py`, que trata el override con el mismo criterio que
`published_backfill`: la edad se mide sobre el dato **entregado**, con el
umbral de cadencia mensual (70 días). Un override INE con el mismo valor mes
tras mes es tan stale como un backfill repetido (P1 de la review del Plan
069).

### 3. Escape hatch si el INE rediseña y el regex falla

Si el scrape falla (HTML reestructurado, clase o `<h1>` cambiados), el
extractor **degrada al backfill publicado** en vez de abortar: la serie se
entrega con su última versión y el gate de edad (ADR-016) empieza a contar.
El mantenedor ve `published_backfill` + la señal de edad, y el issue se
reabre con evidencia — no se insiste en el scrape roto.

## Consecuencias

- El publish diario de `indicadores` depende de un parseo HTML del INE;
  su edad está gateada por ADR-016 y su origen visible en
  `indicator_delivery` de `pipeline_metadata.json`.
- `docs/extraction-lanes.md` documenta el override como parte del carril
  diario de `indicadores` (regla 2).
- AGENTS.md §1 y `docs/datasets/indicadores.md` referencian este ADR.

## Preguntas abiertas

- **¿API de series del INE cuando exista?** Si el INE publica una API de
  series estable, el override HTML se migra a la API y este ADR registra la
  transición.
- **¿UTM tiene un override análogo (SII)?** La UTM es emitida por el SII y
  el agregador la entrega al día; si deja de hacerlo, la misma cadena
  multi-fuente aplica con la página del SII — decidir al momento, con ADR
  propio o extensión de este.
- **¿Backfill congelado vs retirar la serie?** Si el INE deja de publicar
  IPC y mindicador.cl no lo retoma, la decisión es congelar la serie en su
  última versión (ADR-016 ya la gatea) o retirarla — del mantenedor, con
  evidencia del issue.

## Alternativas descartadas

- **Retirar la serie IPC del bundle**: el IPC es un indicador central de
  la capa económica; perderlo por un hueco del agregador castiga a los
  consumidores por un fallo ajeno a la fuente autoritativa.
- **Scrapear el INE como fuente principal**: violaría AGENTS.md §10 y
  duplicaría el trabajo del agregador sin beneficio.
- **Override sin etiqueta visible**: el valor INE se vería como "live" o
  "backfill" según la ruta tomada, y el gate de publicación no podría
  distinguir el dato real del reuso — exactamente el modo de falla que
  ADR-016 existe para exponer.
