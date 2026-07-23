# ADR-012: Geometría comunal — fuente, licencia y decisión técnica

**Fecha:** 2026-07-23
**Estado:** accepted (compuerta de licencia del Plan 053 Step 1 — decisión técnica, no requiere ratificación de estrategia de producto; ver ADR-011 para esa compuerta separada)
**Decision:** Se confirma fuente y licencia redistribuible para la geometría de límites comunales de Chile. El Plan 053 **continúa** hacia el Step 2 (extracción), sujeto a que ADR-011 (estrategia) sea ratificado por el mantenedor antes de publicar el artefacto.

## Contexto

El Plan 053 Step 1 exige confirmar, de forma explícita y separada de los atributos DPA (ya
verdes en `AGENTS.md` §6), que **la geometría** (los polígonos, no solo la tabla de atributos)
tiene licencia redistribuible. Esta es una compuerta que puede matar el plan si no se confirma.

## Investigación

### Fuente candidata

Se exploró la familia de servicios ArcGIS de BCN (`arcgiswebad.bcn.cl/arcgis/rest/services/`,
la misma raíz que ya usa `subdere_extractor.py` para atributos DPA). Se enumeraron las carpetas
`Hosted`, `SIIT` y `tematico`. La capa `tematico/Comunas_Generalizadas` (MapServer, layer 0,
nombre interno `chilegeneralizado`, `geometryType: esriGeometryPolygon`) expone polígonos
comunales de todo Chile con los campos `cod_comuna` (entero, CUT sin padding), `nom_com`,
`nom_reg`, `nom_prov`, `codregion`, entre otros.

Verificación funcional (`returnGeometry=true`, filtro `cod_comuna=13101`):

```
curl -s ".../tematico/Comunas_Generalizadas/MapServer/0/query?where=cod_comuna=13101&outFields=cod_comuna,nom_com,nom_reg&returnGeometry=true&f=json"
```

devuelve `geometry.rings` no vacío para Santiago (Región Metropolitana) — la capa es funcional
y consultable por `cod_comuna`, que mapea 1:1 al `codigo_comuna` (CUT) del resto del hub (tras
zero-pad a 5 caracteres, invariante #1 — el campo llega como entero, ej. `13101`, y para
regiones como Tarapacá se debe verificar que no se pierda el cero inicial al castear a string).

El nombre `Comunas_Generalizadas` ("generalizada" = geometría simplificada para cartografía a
escala nacional) es una señal favorable para el plan: reduce de entrada el riesgo de tamaño de
artefacto que el Step 3 pide evaluar.

### Licencia

BCN publica sus mapas vectoriales (SIIT) también como descarga estática en
`https://www.bcn.cl/siit/mapas_vectoriales/index_html`, con una sección explícita de
condiciones de uso:

> "Los mapas vectoriales son puestos a disposición en virtud del principio de transparencia de
> la función pública. Las personas o instituciones pueden usar libremente esta información,
> señalando como fuente a la Biblioteca del Congreso Nacional de Chile."

Esa misma página lista explícitamente **"División comunal" (30.6 MB)** entre las capas
descargables — es decir, la geometría de límites comunales (no solo los atributos) está
cubierta por esta declaración de uso libre con atribución. Advertencia declarada en la misma
página: el material es de referencia y no debe usarse para trabajo que requiera precisión
geodésica — no es una restricción de redistribución, es un disclaimer de precisión (que además
refuerza que simplificar geometría para reducir tamaño del artefacto, per Step 3, no degrada
nada que la fuente ya garantice).

La capa ArcGIS `tematico/Comunas_Generalizadas` es la misma división comunal de BCN servida por
un canal técnico distinto (REST en vez de shapefile descargable) bajo el mismo dominio
institucional (`bcn.cl` / `arcgiswebad.bcn.cl`) — se trata de la misma fuente y la misma
declaración de condiciones de uso aplica.

**Clasificación bajo el semáforo de `AGENTS.md` §6**: 🟢 `open-attribution` — cumple el primer
criterio de "origen primario es redistribuible" (institución pública chilena, acceso público,
declaración explícita de uso libre con atribución) y además supera el criterio mínimo: no es
solo "sin restricción explícita", hay una declaración *afirmativa* de uso libre con atribución,
equivalente en efecto a CC-BY.

## Decision

- **Fuente confirmada**: capa ArcGIS `tematico/Comunas_Generalizadas` (MapServer, layer 0,
  `chilegeneralizado`) de `arcgiswebad.bcn.cl`, respaldada por la declaración de condiciones de
  uso de `bcn.cl/siit/mapas_vectoriales` que cubre explícitamente "División comunal".
- **Licencia confirmada**: uso libre con atribución obligatoria a "Biblioteca del Congreso
  Nacional de Chile" — clasificación 🟢 `open-attribution`. El dataset `geometria_comunal.md`
  (Step 5) debe incluir esta cita de atribución literal.
- **La compuerta del Step 1 PASA.** El plan continúa hacia el Step 2 (extracción a staging),
  Step 3 (artefacto GeoParquet) y Step 4 (`resolve_by_coords()`, opcional/desacoplado) — sujetos
  a la ratificación de ADR-011 (estrategia construir-por-delante-de-demanda), que sigue
  `proposed` y requiere revisión del mantenedor antes de que el artefacto se considere
  autorizado para publicación.
- **Decisión técnica preliminar para el Step 2** (a confirmar al ejecutarlo): crear un extractor
  nuevo `src/extractors/geometria_comunal_extractor.py` en vez de extender
  `subdere_extractor.py`, tal como recomienda el plan, para no arriesgar el dataset base
  `comunas`. Debe castear `cod_comuna` a string de 5 caracteres con zero-pad (invariante #1) y
  validar que las 346 comunas del DPA existen en la respuesta.

## Consecuencias

- Positivas: no hace falta un fallback de "solo enlazar la fuente" (§6, regla conservadora) —
  el hub puede redistribuir el artefacto GeoParquet completo, que es el entregable flagship del
  plan.
- Negativas / riesgo residual: la geometría es "generalizada" (simplificada), no de precisión
  geodésica — aceptable y hasta deseable para el caso de uso de reverse geocoding y para
  mantener el artefacto liviano, pero debe documentarse explícitamente en
  `docs/datasets/geometria_comunal.md` (Step 5) para que nadie la use para trabajo catastral o
  de precisión legal de límites.
- El campo fuente es `cod_comuna` entero (no string de 5 con padding) — el extractor del Step 2
  debe manejar el cast con cuidado para no repetir el bug de invariante #1 que el proyecto
  activamente previene (pérdida de cero inicial en códigos de Tarapacá y similares).

## Alternativas consideradas

- **Usar la descarga estática del shapefile "División comunal" (30.6 MB) en vez del endpoint
  ArcGIS REST** — no descartada, sigue siendo una fuente válida bajo la misma licencia; se
  prefiere el endpoint REST en el Step 2 porque es consultable programáticamente (mismo patrón
  que ya usa `subdere_extractor.py` para atributos) y no requiere manejo de un ZIP/shapefile
  binario en el pipeline. Si el endpoint REST cambia o se degrada, el shapefile estático es el
  fallback documentado aquí.
- **Reconstruir polígonos desde OpenStreetMap** — descartada sin necesidad de evaluarla a fondo:
  la fuente BCN ya es oficial, ya está en uso por el hub, y tiene licencia confirmada; no hay
  motivo para introducir una fuente adicional (anti-patrón de dispersión que ADR-011 explícitamente excluye).
