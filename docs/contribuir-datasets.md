---
title: "Aportar un dataset — chile-hub"
description: >
  Cómo proponer o aportar una capa de datos al hub: requisitos mínimos, qué no
  entra, cómo se evalúa y qué pasa con tu aporte.
category: contribution-guide
audience: [user, contributor, data-scientist]
priority: high
related_docs:
  - dataset-inclusion-criteria.md  # Criterios completos y estados de decisión
  - dataset-compatibility-policy.md
last_updated: 2026-09-26
---

# Aportar un dataset

¿Conoces un dato público chileno que debería estar en chile-hub? **No hace falta
que sepas programar ni que traigas los datos limpios**: basta con la fuente y para
qué sirve. Esta es la puerta por la que entran todas las capas.

## Para quién es

- Personas que conocen una fuente oficial y quieren verla lista para análisis.
- Equipos que tienen datos de una fuente pública y quieren una versión versionada.
- Personas o equipos que necesitan un dato que hoy no existe y quieren pedirlo.
- Desarrolladores que quieren mantener una capa dentro del pipeline.

## ¿Solicitas o aportas?

Son dos caminos distintos y los dos sirven:

| | **Solicitar** | **Aportar** |
|:--|:---|:---|
| Qué expresas | Una necesidad: "este dato debería existir" | Una oferta: "tengo la fuente / quiero implementarla" |
| Qué necesitamos de ti | El caso de uso (y la fuente si la conoces) | Fuente, licencia, formato y llave de cruce |
| Cómo se usa después | Señal de demanda: se prioriza cuando se repite | Entra a evaluación y, si pasa, se implementa |
| Formulario | [Solicitar un dataset](https://github.com/cortega26/chile-hub/issues/new?template=dataset_request.yml) | [Aportar un dataset](https://github.com/cortega26/chile-hub/issues/new?template=dataset_contribution.yml) |

> Si no estás seguro, usa **Solicitar**: el formulario te pregunta si puedes ayudar
> y te deriva al de aporte cuando corresponde. No se pierde nada.

## Las 4 compuertas y la pregunta abierta

Cuatro preguntas binarias definen si la propuesta avanza:

| # | Pregunta | Si cumple | Si no cumple |
|:--|:---|:---|:---|
| 1 | ¿La fuente es oficial o claramente autoritativa? | Sigue | No entra: necesitamos trazabilidad |
| 2 | ¿Se descarga de forma estable (API, CSV/XLSX/ZIP)? | Sigue | Solo scraping HTML: normalmente no entra |
| 3 | ¿La licencia permite reutilizar y redistribuir con atribución? | Sigue | `restricted`: no entra al bundle público |
| 4 | ¿Se cruza con comunas/regiones u otra llave estable (CUT, estación, RUT)? | Sigue | Se evalúa si el valor justifica una llave nueva |

Y una pregunta abierta, que no es de sí o no: **¿qué decisión o análisis
desbloquea?** Cuéntala con un caso concreto en el formulario; sin un caso de uso
claro la propuesta no se prioriza, aunque cumpla las cuatro compuertas.

Los criterios completos y los estados de decisión (`accepted`, `under-review`,
`needs-research`, `deferred`, `rejected`) están en
[Criterios de inclusión](dataset-inclusion-criteria.md).

## Qué NO entra

- Datos personales o que permitan identificar personas (Ley 19.628).
- Fuentes con licencia restrictiva o términos ambiguos.
- Scraping HTML frágil como única vía de acceso.
- Datos sin fuente primaria verificable.

## Cómo se ve el proceso

1. **Propones** con el formulario (2 minutos, no necesitas cuenta técnica).
2. **Evaluación**: se contrasta contra los criterios; puede pedirse la URL exacta o una muestra.
3. **Carril `candidate`**: si pasa, la capa se implementa y prueba sin entrar al bundle público.
4. **Promoción**: si la fuente se mantiene estable, pasa al bundle con su documentación,
   contratos de esquema y validaciones.
5. **Atribución**: cada capa cita a su fuente; tu aporte queda registrado en el issue público.

> No prometemos fechas. Las propuestas se priorizan por demanda y estabilidad de la
> fuente, y todas quedan registradas públicamente.

## Ejemplos reales

- **Buena propuesta**: fuente oficial, descarga estable, licencia clara y cruce por CUT.
  Ejemplo de forma: "Población censada por comuna (Censo 2024, INE), XLSX, CC BY 4.0,
  llave `codigo_comuna`".
- **Necesita investigación**: valiosa, pero falta confirmar API o licencia. Queda en
  `needs-research` hasta aclararlo; ver
  [DGA + DMC](https://github.com/cortega26/chile-hub/issues/107) o
  [energía/CNE](https://github.com/cortega26/chile-hub/issues/108).
- **No entra**: datos raspados de sitios sin fuente primaria ni licencia clara, como
  [desastres 2024-2026](https://github.com/cortega26/chile-hub/issues/109) mientras
  no exista un origen oficial estructurado.

## Empieza

- **[Solicitar un dataset](https://github.com/cortega26/chile-hub/issues/new?template=dataset_request.yml)** —
  si necesitas un dato que aún no existe (2 minutos).
- **[Aportar un dataset](https://github.com/cortega26/chile-hub/issues/new?template=dataset_contribution.yml)** —
  si traes la fuente, los datos o el trabajo de implementación.
- **[Ver los criterios completos](dataset-inclusion-criteria.md)** — las reglas con
  las que se evalúa cada propuesta, sin letra chica.
- **[Explorar las capas actuales](datasets/README.md)** — revisa qué existe antes de
  proponer, para no duplicar.
