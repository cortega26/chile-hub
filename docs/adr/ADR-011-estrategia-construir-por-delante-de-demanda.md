# ADR-011: Estrategia — construir capacidad por delante de la demanda

**Fecha:** 2026-07-23
**Estado:** proposed
**Decision:** Se autoriza construir capacidad de producto por delante de la demanda ("crear la oferta para generar la demanda"), matizando el anti-patrón #10 (`AGENTS.md:714`, "Inflar el MVP con más datasets antes de validar adopción") para un subconjunto acotado de trabajo.

## Contexto

El anti-patrón #10 (`AGENTS.md:714`) prohíbe sumar datasets nuevos "hasta que los existentes
tengan señales de adopción documentadas (descargas, issues con casos de uso, menciones
externas)". Es una regla sana contra la dispersión, pero el repo llegó a un punto de madurez
donde la lista "deseable post-MVP" del product-spec ya está casi entera entregada
(`search_datasets`, `cross_view`, `sql`, `from_datapackage`, `validate_user_data`, dashboard,
playground) y, sin embargo, hoy **no existe ninguna señal de adopción real medida** (Plan 052
cierra ese hueco por separado). Aplicar el anti-patrón #10 de forma literal en este momento
dejaría al proyecto sin dirección de crecimiento: no puede medir demanda que no tiene forma de
generar, y no puede generar demanda si cualquier inversión de capacidad queda bloqueada
esperando una señal que todavía no existe.

El mantenedor autorizó explícitamente desafiar el anti-patrón #10 con el argumento "a veces hay
que crear la oferta para generar la demanda" (decisión de producto registrada en
`plans/README.md`, 2026-07-14). Esta ADR materializa esa decisión en el registro canónico del
repo, como exige el Step 0 del Plan 053.

## Decision

Se autoriza construir **capacidad de producto por delante de la demanda**, con un matiz que
evita que esto se convierta en barra libre para inflar el catálogo:

- **Alcance de la excepción**: aplica únicamente a **profundidad de capacidad y distribución
  sobre fuentes existentes de alta calidad ya usadas por el hub** — ejemplos concretos:
  geometría comunal + reverse geocoding (Plan 053), capa de acceso HTTP/DCAT (Plan 051),
  resolución de entidades territoriales por nombre (Plan 050).
- **Lo que NO cambia**: la excepción **no** aplica a **amplitud de datasets nuevos sobre
  fuentes frágiles** (scraping HTML, fuentes sin licencia confirmada, fuentes no usadas hoy por
  el hub). Ese trabajo sigue 100% gated por el anti-patrón #10 y por señal de adopción
  documentada — sin excepción.
- La política legal (§6, semáforo de reutilización y "regla conservadora": ante duda sobre
  licencia, no redistribuir) sigue vigente sin matices. Esta ADR autoriza *cuándo* construir,
  nunca *qué* redistribuir sin licencia confirmada — eso lo sigue decidiendo §6 caso por caso
  (ver Plan 053 Step 1, gate de licencia de la geometría).

## Consecuencias

- **Positivas**: los Planes 053 (geometría comunal + `resolve_by_coords()`) y 051 (capa
  HTTP/DCAT) pueden ejecutarse sin esperar una señal de adopción previa, porque profundizan
  sobre fuentes ya integradas y de alta confianza, no amplían la superficie de datasets
  frágiles. El Plan 052 (señal de adopción) pasa de "desbloquear crecimiento" a **medir la
  demanda que esta oferta genere** — su valor no desaparece, cambia de rol.
- **Negativas / riesgo**: invertir esfuerzo (`L` para el Plan 053) sin validación de demanda
  previa tiene costo de oportunidad si la apuesta no genera tracción. Se mitiga manteniendo el
  alcance estrictamente acotado a fuentes ya confiables (no HTML scraping nuevo) y con Plan 052
  corriendo en paralelo para poder medir el resultado cuanto antes.
- **Reversibilidad**: si Plan 052 muestra adopción estancada tras la publicación de 053/051,
  el anti-patrón #10 vuelve a aplicar sin matices para cualquier trabajo posterior — esta ADR no
  es una derogación permanente, es una excepción acotada y auditable.

## Alternativas consideradas

- **Mantener el anti-patrón #10 sin matices y esperar señal de adopción antes de cualquier
  inversión nueva** — descartada: el hub no tiene hoy ninguna señal de adopción medida (el
  hueco que cierra el Plan 052), así que esperar una señal inexistente paraliza el proyecto
  indefinidamente sin criterio de salida.
- **Levantar el anti-patrón #10 por completo (sin acotar alcance)** — descartada: abriría la
  puerta a scraping frágil o datasets de licencia dudosa sin ninguna validación de demanda,
  exactamente lo que el anti-patrón #10 existe para prevenir. El matiz de "profundidad sobre
  fuentes existentes de alta calidad, no amplitud sobre fuentes frágiles" preserva la disciplina
  original.

## Ratificación

Estado `proposed`: esta ADR fue escrita por un agente ejecutando el Step 0 del Plan 053. La
decisión de estrategia de producto que documenta ya fue autorizada verbalmente por el
mantenedor (`plans/README.md`, 2026-07-14), pero requiere su ratificación explícita
(`proposed` → `accepted`) antes de que el resto del Plan 053 (Steps 2-5, entregable de datos) se
considere autorizado para publicación. El gate de licencia del Step 1 (ADR-012) es independiente
de esta ratificación y puede ejecutarse en paralelo — es una compuerta técnica distinta.
