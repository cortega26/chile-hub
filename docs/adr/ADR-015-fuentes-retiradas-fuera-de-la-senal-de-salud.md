# ADR-015: Las fuentes muertas salen de la señal de salud, no del paquete

**Fecha:** 2026-07-29
**Estado:** accepted
**Decision:** Un dataset con `maturity_status: "deprecated"` en
`data/source_registry.json` se marca `retired: true` en `hub_health.json` y
**deja de participar en todos los contadores de salud**, pero conserva su
entrada visible en el artefacto, su lugar en el catálogo, su extractor y su
miembro del enum público `Dataset`. `dataset_count` no cambia.

Supersede parcialmente a **ADR-014**, que registraba "los 3 restantes son
problemas reales: `empresas`, `indicadores`, `consumo_electrico_comunal`". Ese
inventario era correcto al escribirse; a partir de aquí `consumo_electrico_comunal`
sale del cómputo. ADR-014 se conserva sin editar: los ADR son registro histórico.

## Contexto

`consumo_electrico_comunal` estaba permanentemente en `drifted` sin acción
posible. `data/source_registry.json` ya documentaba el diagnóstico completo
(investigado 2026-07-07, `AGENTS.md` §6): CNE decomisionó el catálogo Junar de
energiaabierta.cl y la página del dataset no ofrece archivo ni API de reemplazo.
El dataset **nunca tuvo un fetch en vivo exitoso** — solo publica `FALLBACK_ROWS`
de muestra (3 filas), en carril `candidate` y fuera del bundle público. Su
`review_by` era 2027-06-30: once meses más de contador rojo.

Es el mismo daño que atacó el Plan 066 (ADR-014) por otra vía. La diferencia
importa: allí el drift era **ruido de clasificación**; aquí el drift es **real**
pero la acción no existe. Ambos casos terminan igual — un contador que nadie
puede bajar enseña a no mirarlo.

## Decision

### 1. `retired` es un estado derivado del registry, nunca una lista en el código

`_load_retired_datasets()` lee `maturity_status == "deprecated"`. No hay nombres
de dataset hardcodeados en la lógica de salud. La política es "la fuente murió",
no "este dataset molesta".

**Quién puede retirar y con qué evidencia**: solo el registry, y la entrada debe
traer un `next_action` que documente la investigación de la caída (URL revisada,
fecha, ausencia de reemplazo). Es el mismo criterio de auditabilidad que ADR-014
exige para declarar un warning como esperado.

### 2. Regla única de contadores

**Todos** los contadores de `hub_health.json` describen el conjunto **activo**
(`ok_count`, `warn_count`, `error_count`, `live_count`, `fallback_count`,
`stale_count`, `drifted_count`, `degraded_count`, coberturas, `warning_count`…).
Solo `dataset_count` y `retired_count` describen el inventario completo.

Consecuencia deliberada: `live_count + fallback_count` ya no suma
`dataset_count`; la diferencia es exactamente `retired_count`. Se prefirió una
regla única y explicable a una lista de excepciones por contador.

### 3. El retirado se muestra, no se esconde

La entrada permanece en `datasets` con `retired: true`. Un dataset que
desaparece del artefacto es indistinguible de un bug del pipeline; uno marcado
es una decisión legible. `drift_report.json` sigue reportándolo como `drifted`
— eso es cierto y no se altera; lo que cambia es que no cuenta en la señal.

### 4. No se toca la superficie pública

`Dataset.CONSUMO_ELECTRICO_COMUNAL` y `hub.load_polars("consumo_electrico_comunal")`
siguen funcionando. Retirarlos sería un BREAKING CHANGE sobre un paquete ya
publicado en PyPI (1.21.x) con semantic-release automático, forzando un 2.0.0
que el proyecto decidió explícitamente no forzar (`plans/README.md`, hallazgos
diferidos 2026-07-18) — y no resolvería nada que esta decisión no resuelva ya.

## Consecuencias

- `drifted_count` 3 → **2** (`empresas`, `indicadores`); `warn_count` 3 → **2**;
  `retired_count: 1`; `dataset_count` sigue **19**; `overall_status` sigue `warn`.
- Gates nuevos en `verify_pipeline.py`: `retired` booleano y presente en cada
  entrada; `retired_count` entero entre 0 y `dataset_count`. Ninguno existente
  se relajó y ningún enum ganó valores.
- Si CNE (o el Coordinador Eléctrico Nacional) publica un reemplazo oficial, el
  camino de vuelta es una sola línea del registry — no un cambio de código.

## Alternativas descartadas

- **Borrar el dataset del enum y del catálogo**: BREAKING CHANGE con bump mayor
  forzado; además `check_extractors()` (Plan 058) exigiría borrar también el
  extractor, perdiendo el trabajo si la fuente reaparece.
- **Dejarlo como estaba**: es la opción que crea el problema — once meses de
  alarma inaccionable degradando la credibilidad de las que sí importan.
- **Buscar fuente de reemplazo ahora**: ADR-011 limita la estrategia a
  profundizar sobre fuentes ya validadas y el anti-patrón #10 sigue vigente. Un
  reemplazo sería un dataset nuevo con su propia evaluación.
