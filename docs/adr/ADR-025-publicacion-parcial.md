# ADR-025: Publicación parcial con retención marcada

- **Estado:** accepted (ratificado por el mantenedor el 2026-10-26)
- **Fecha:** 2026-10-25
- **Decisores:** mantenedor
- **Contexto técnico:** plan 147 (diagnóstico del 403 de SINCA), plan 150 (implementación)

## Contexto

Hasta hoy la política de publicación era **todo-o-nada**: si una sola capa
`stable_publishable` quedaba en `source_mode=fallback`, `verify_pipeline.py
--profile publication` rechazaba el build completo y las demás capas —sanas— no se
publicaban.

Esa política es correcta en su objetivo (nunca publicar datos degradados) pero
tiene un radio de impacto que no está justificado: el 2026-10-16 al 2026-10-25
produjo **once corridas diarias fallidas consecutivas** y congeló las 23 capas al
snapshot del 2026-10-15. Las causas eran tres fuentes externas:

- `datosabiertos.mineduc.cl` caído ("sitio temporalmente fuera de servicio"),
  que afecta `establecimientos_educacionales` y `resultados_educacionales`.
- `sinca.mma.gob.cl` devolviendo HTTP 403 al rango de IPs de los runners de
  GitHub (plan 147: es bloqueo de IP, no de fingerprint; desde una IP residencial
  responde con normalidad).
- `observatorio.ministeriodesarrollosocial.gob.cl` con timeout desde el runner.

Ninguna de las tres es un defecto del proyecto, y ninguna se resuelve escribiendo
código.

## Decisión

Un dataset `stable_publishable` que en un build no califica para publicar pasa a
uno de tres estados:

| Estado | Condición | Qué se publica |
|:--|:--|:--|
| `fresh` | Cumple fuente, frescura y umbral de `record_count` | Su artefacto nuevo |
| `held` | Incumple, pero existe artefacto publicado previo | El artefacto previo, marcado |
| `unrecoverable` | Incumple y no hay artefacto previo | Nada: el build falla |

La sustitución ocurre **antes de construir cualquier formato** (parquet, JSON,
DuckDB, SQLite, Excel, ZIP): el frame y los metadatos del dataset retenido se
reemplazan por los del snapshot publicado. Así ningún entregable mezcla datos
degradados con datos buenos.

La marca `publication_hold` viaja en el catálogo, el manifiesto (`retained: true`)
y `hub_health.json` (`held_count`), con `reason`, `previous_generated_at_utc`,
`since_utc` y `builds_held`.

**Escalamiento:** a los `MAX_HELD_DAYS` (7) días retenido el build
**falla**. Una retención no puede volverse silenciosa ni permanente; obliga a
decidir entre reparar la fuente, sacar el dataset del carril
`stable_publishable` o retirarlo (AGENTS.md §6).

## Alternativas consideradas

1. **Esperar a que las fuentes se recuperen (statu quo).** Descartada: congela 20
   capas sanas por tiempo indefinido y no hay señal de que MINEDUC vuelva pronto.
2. **Mover las capas afectadas a `candidate`.** Descartada: castiga a tres
   datasets por una caída temporal y los saca del bundle, que es justo lo que el
   usuario consume.
3. **Permitir publicar el fallback marcado** (relajar `fallback_policy`).
   Descartada: publicaría datos degradados —`resultados_educacionales` caía de
   345 a 3 filas— que es exactamente lo que el invariante §4.2 prohíbe.
4. **Override manual con `--allow-record-drop`.** Descartada: no cubre el caso de
   `source_mode=fallback` y deja la decisión fuera del build, sin marca ni tope.

## Consecuencias

**Positivas**

- Una fuente caída deja de congelar el resto del catálogo.
- El consumidor puede distinguir un dato refrescado de uno retenido sin leer
  prosa: `publication_hold` en el catálogo y `retained` en el manifiesto.
- La retención tiene fecha de caducidad operativa (7 días), no se eterniza.

**Negativas y riesgos**

- `hub_health.json` suma `held_count` y un `held` aparece `drifted`: los
  consumidores que cuenten drift verán un valor más mientras dure la retención.
  Es señal, no ruido: el dato efectivamente no se refrescó.
- El mecanismo depende de que exista un snapshot previo en `data/normalized/`.
  En un checkout limpio sin historia, la retención no aplica (comportamiento
  anterior).
- **Dependencia no resuelta:** `calidad_aire` acumula su serie en
  `data/staging/`, que no está versionado. Si la caché se pierde, la serie
  reinicia y el dataset quedará `held` hasta recuperar 8.462 filas. El arreglo
  —versionar su staging como ya se hace con `precipitaciones_dgac` y
  `finanzas_municipales`— queda como trabajo aparte.

## Cumplimiento

- `AGENTS.md` §4.2 documenta la regla y sus límites.
- `tests/test_publication_hold.py` fija las propiedades: sin artefacto previo
  falla, el frame publicado es el anterior, el contador acumula y el tope escala.
- `scripts/verify_pipeline.py` valida la integridad de la marca y no relaja
  ninguna comprobación para datasets `fresh`.
