# Sostenibilidad de chile-hub — índice de decisiones

> **Qué es.** Es el punto de entrada para cualquier trabajo sobre financiamiento,
> patrocinios, grants, o métricas de adopción que vayan a usarse en material externo.
> Registra qué se decidió, en qué orden y dónde está cada análisis.
>
> **Regla.** Antes de proponer o ejecutar algo en este tema, lee el estado
> vigente y la [Auditoría 3](auditoria-3-2026-09-29.md).

## Estado vigente (2026-09-30)

**HOLD. Veredicto D de la [Auditoría 3](auditoria-3-2026-09-29.md): todavía no se ejecuta sponsorship institucional.**

| Permitido | No permitido hasta cumplir el gate (§G de la Auditoría 3) |
|:---|:---|
| Mantener sin cambios `FUNDING.yml` y el pedido de apoyo que muestra la CLI (carril 1) | Crear tiers, `SPONSORS.md` o una sección de patrocinios en la landing o el README |
| Ejecutar el experimento de discovery (§E): máximo 15 h y sin pedir dinero | Pedir dinero a organizaciones, contactar vendors o financiadores, o presentar propuestas de grant |
| Consultar a un contador sobre el vehículo de cobro (no implica contacto externo) | Ejecutar [`plans/110-programa-de-patrocinios.md`](../../plans/110-programa-de-patrocinios.md), que está en HOLD |
| Atender la demanda de servicios que llegue sola (Tooltician, carril 5) | Lanzar pilotos de servicios por iniciativa propia sin cumplir las condiciones 2, 3 y 5 del gate |
| Tener una conversación de escucha con CAF, sin pedir nada, **solo si** §E encuentra al menos 3 organizaciones con uso verificable | Presentar las descargas de PyPI como "instalaciones", "usuarios" o "audiencia" ([`AGENTS.md` §10](../../AGENTS.md)) |

- **Próxima acción:** completar el Paso 0 de §E y luego enviar hasta 15 mensajes de discovery. La decisión se toma entre el día 30 y el 45.
- **Revisión obligatoria:** abril de 2027, si §E termina en Stop.

## Cronología

| # | Fecha | Documento | Qué es | Resultado | Estado |
|:--:|:---|:---|:---|:---|:---|
| 0a | 2026-06-19 | [`docs/backlog/08-evaluacion-producto-comercial.md`](../backlog/08-evaluacion-producto-comercial.md) | Antecedente: evaluación de una API premium y de un producto comercial | Sin paywall, porque el dato es abierto. Monetizar primero con reportes o consultoría. Validar en una "Etapa 0" | Pendiente de evaluación |
| 0b | 2026-06-30 | [`docs/gate-4-3-decision-playground.md`](../gate-4-3-decision-playground.md) | Antecedente: primera lectura del uso real | La señal de PyPI es "vanidosa". La señal real es la descarga del bundle, del orden de decenas | Histórico |
| 0c | 2026-09-26 | [`docs/adoption-review.md`](../adoption-review.md) · [`docs/launch-pack.md`](../launch-pack.md) | Antecedente: línea base post-lanzamiento y material de difusión | Usa la cifra de "instalaciones PyPI", que la Auditoría 3 corrige | Vigente, con nota |
| **1** | 2026-09-29 | [`plans/110-programa-de-patrocinios.md`](../../plans/110-programa-de-patrocinios.md) (idéntico a [`e2fd831`](https://github.com/cortega26/chile-hub/blob/e2fd831/plans/110-programa-de-patrocinios.md)) | **Auditoría 1 / Propuesta A:** programa completo de patrocinio institucional | Tiers, beneficios, 5 olas y play de CAF | **HOLD**: no ejecutar |
| **2** | 2026-09-29 | [Issue #125, §4 a §8 del cuerpo](https://github.com/cortega26/chile-hub/issues/125) | **Auditoría 2 / Propuesta B:** reconstrucción adversarial | 5 carriles; el sponsor no compra tiempo; Wave −1 de discovery | Revisada en la Auditoría 3 y adoptada como contabilidad |
| **3** | 2026-09-29, con adenda del 30-sep | [`auditoria-3-2026-09-29.md`](auditoria-3-2026-09-29.md) · [comentario en #125](https://github.com/cortega26/chile-hub/issues/125#issuecomment-5895632160) | **Auditoría 3:** auditoría del caso más revisión de las Auditorías 1 y 2 | **D:** no ejecutar todavía; experimento §E; gate §G | **Vigente** |
| 4 | por definir | Resultado del experimento §E | Decisión entre Avanzar, Servicios, Pivotear o Stop | — | Pendiente |

## Conclusiones de la Auditoría 3 (resumen)

1. **No hay comprador identificado.** Hoy no se puede nombrar ninguna organización que use el proyecto de forma verificable:
   - 0 dependents;
   - 0 repos públicos que importen `chile_hub`;
   - 0 interacciones de terceros;
   - 0 sponsors.
2. **Las descargas de PyPI miden la cadencia de releases, no la adopción.** Los releases explican entre el 94% y el 97% de la varianza diaria, a razón de unas 80 a 100 descargas por release. Las activaciones reales, medidas por las descargas del bundle, son unas 27 al mes.
3. **Aunque hubiera demanda, hoy no hay cómo cobrar.**
   - chile-hub no es persona jurídica.
   - La Ley 21.440 no permite que una persona natural reciba donaciones con beneficio tributario.
   - Los organismos públicos compran servicios vía Compra Ágil, no patrocinan.
4. **La infraestructura cuesta ≈ USD 0, así que el aporte in-kind no financia nada.** Lo escaso es el tiempo del mantenedor, y el riesgo principal es la continuidad del proyecto.
5. **Si el sponsorship incluye horas, se vuelve consultoría barata.** Además, los tiers altos de la Propuesta A superan lo que un solo mantenedor puede atender. Las horas se venden como servicios (Tooltician), en un contrato aparte.
6. **Los grants solo son viables a través de un socio institucional y con evidencia de uso, en un horizonte de 12 a 24 meses.** Los instrumentos que listaba la Propuesta A están cerrados o no aceptan un proyecto en esta etapa.
7. **CAF sirve para aprender y para ampliar la red, no para conseguir caja.** Solo se conversa con CAF después de §E, y únicamente si aparecen al menos 3 organizaciones. El "piloto regional" no está demostrado.
8. **El bus factor se reduce con un plan de continuidad, no con dinero:** un segundo administrador, un modo de degradación y un runbook de traspaso.

La evidencia robusta, las hipótesis y los desconocidos críticos están en la [Auditoría 3, §G](auditoria-3-2026-09-29.md#g-first-cut-gate).

## Reglas para agentes

1. **No ejecutar** `plans/110-programa-de-patrocinios.md` ni construir tiers o activos comerciales. Cualquier reescritura parte del delta de §F de la Auditoría 3, y solo después de cumplir el gate de §G.
2. **No contactar** a sponsors, vendors, CAF ni financiadores fuera de lo que permite el estado vigente. El discovery no pide dinero.
3. **No presentar las descargas de PyPI** como instalaciones, usuarios ni audiencia. Antes de citar cualquier cifra, refréscala con el Anexo M de la Auditoría 3.
4. **No publicar** datos personales de contactos ni términos comerciales de terceros. El tracker se mantiene fuera del repo (Ley 21.719).
5. **Registrar cada análisis o decisión nueva en la cronología,** con su fecha, documento, resultado y estado. Si contradice a la Auditoría 3, reconcílialo de forma explícita antes de cambiar el estado vigente: indica qué evidencia nueva cambia qué conclusión.

## Enlaces

- Índice general del repo: [`SOURCE_OF_TRUTH.md`](../../SOURCE_OF_TRUTH.md)
- Estado de los planes: [`plans/README.md`](../../plans/README.md) (fila 110) · [`ROADMAP.md`](../../ROADMAP.md) §5
- Largo plazo: [`docs/backlog/NEXT_STEPS.md`](../backlog/NEXT_STEPS.md)
- Principio "lo abierto sigue abierto" y posicionamiento: [`docs/product-spec.md`](../product-spec.md) · [ADR-023](../adr/ADR-023-posicionamiento-ultima-milla-no-portal.md)
