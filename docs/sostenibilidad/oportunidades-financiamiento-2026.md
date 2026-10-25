# Oportunidades de financiamiento 2026 — índice ejecutivo

> **Qué es.** La vista de una página sobre qué vía de financiamiento ejecutar,
> cuál esperar y cuál descartar, con la aritmética económica a la vista.
>
> **Qué no es.** No reemplaza [`README.md`](README.md), que sigue siendo el
> documento canónico del estado de sostenibilidad y del HOLD. Este índice no
> cambia el veredicto D ni autoriza ninguna postulación.

- **Fecha:** 2026-10-25 (America/Santiago).
- **Base:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`, árbol limpio.
- **Registro completo (13 fichas):** [`registro-oportunidades.md`](registro-oportunidades.md).
- **Decisión y acciones humanas:** [`financiamiento-30d-decision.md`](financiamiento-30d-decision.md).

## 1. Resumen en una tabla

| Vía | Veredicto | ¿Acción externa posible hoy? | Qué la desbloquea |
|:--|:--|:--|:--|
| **GitHub Secure Open Source Fund** (USD 10.000) | **NO-GO** | No | Uso demostrable. Hoy: 0 dependents |
| **GitHub Sponsors** | PASS operativo, USD 0 | Ya activo | Verificación de cobro (humano) |
| **Buy Me a Coffee** | UNKNOWN, USD 0 | Ya activo | Verificación de cobro (humano) |
| **FLOSS/fund** (USD 10.000–100.000) | **CONDITIONAL** | No | El mismo gate de uso demostrable |
| NLnet Restack / CodeSupply | NO-GO | No | Dimensión europea + política GenAI + encaje |
| Start-Up Chile Ignite | NO-GO | No (cerrada) | Ser una empresa con ventas: contradice el proyecto |
| CORFO / Sercotec | NO-GO | No | Ninguna convocatoria admite OSS sin empresa |
| Sovereign Tech Fund | NO-GO | No | Mínimo €50k y prevalencia |
| D//F, PSF Grants | NO-GO | No | Convocatorias cerradas |
| AWS Open Data | NO-GO | No | In-kind sobre un costo que ya es ≈ 0 |

**Lectura:** las dos únicas vías con dinero real y encaje posible —GitHub Fund y
FLOSS/fund— dependen **de la misma variable**: que exista uso demostrable. No son
dos problemas, es uno.

## 2. Qué ejecutar, qué esperar, qué descartar

### Ejecutar ahora (sin acción externa)

1. **Restaurar la publicación diaria.** Es la única acción que mejora a la vez la
   promesa del producto, la evidencia de impacto y la credibilidad de cualquier
   postulación futura. Issue #195, abierto desde el 2026-10-18, diez corridas
   fallidas. **No** es una tarea de financiamiento: es la prioridad del proyecto.
2. **Verificar la capacidad de cobro** de GitHub Sponsors y BMC (humano, §3 de
   [`financiamiento-30d-decision.md`](financiamiento-30d-decision.md)).
3. **Registrar Search Console.** Está pendiente desde el plan 107. Sin eso,
   "descubrimiento orgánico" es una hipótesis sin dato. Es una acción de operador
   ya documentada, no un experimento nuevo.
4. **Llevar la pregunta tributaria al contador**, con la lista cerrada de §4.

### Esperar (no gastar horas)

- **GitHub Fund** y **FLOSS/fund**: revisar solo cuando exista una señal de la
  lista de disparadores de
  [`github-secure-oss-fund-eligibilidad.md`](github-secure-oss-fund-eligibilidad.md#4-disparadores-de-reevaluación).
- **Ignite**: reevaluar solo si el proyecto cambia de naturaleza, cosa que el
  `product-spec` excluye.

### Descartar (archivar y no volver a buscar)

- **NLnet Restack y CodeSupply.** Cierran el 2026-11-03. Tres gates fallidos; ver
  [`nlnet-compatibilidad-2026.md`](nlnet-compatibilidad-2026.md).
- **Sovereign Tech Fund**, **D//F**, **PSF Grants**, **AWS Open Data**,
  **CORFO**, **Sercotec**, mientras el proyecto siga siendo un commons sin
  empresa ni costo de infraestructura.

## 3. Matriz económica

**Supuesto interno, no tarifa de mercado:** CLP 45.000/h, la hipótesis que el
informe externo usa para valorar tiempo. Se muestra sensibilidad porque no es un
hecho. Tipo de cambio 2026-10-23: **USD 1 = CLP 986,58** (mindicador.cl).

| Vía | Caja potencial | Costo antes de adjudicar | Costo total si adjudica | Valor bruto por hora total |
|:--|--:|--:|--:|--:|
| GitHub Fund | USD 10.000 (CLP 9.865.800) | 4–6 h (estimado) | 24–26 h (incluye 20 h de programa) | ≈ CLP 379.000/h |
| FLOSS/fund | USD 10.000–100.000 | ≈2 h | ≈2 h (soporte a sostenibilidad, sin hitos publicados) | ≈ CLP 4.900.000/h al mínimo |
| Sponsors / BMC | Variable, hoy USD 0 | 0 h | 0 h | — |
| NLnet | €5.000–50.000 | 6–10 h | cientos de h | No aplica (NO-GO) |
| Ignite | CLP 30 MM | >20 h + constituir sociedad | 4 meses de programa | No aplica (NO-GO) |

### El cálculo que importa

El costo de postular al GitHub Fund es, antes de adjudicar, **4–6 horas**. El
premio es CLP 9,87 millones. La **probabilidad de indiferencia** —el punto en que
el esfuerzo se paga a CLP 45.000/h— es:

| Base de costo | Probabilidad de indiferencia |
|:--|--:|
| Solo el costo de postular (6 h) | **2,7%** |
| Postular + programa completo (26 h) | **11,9%** |

Es aritmética, **no una estimación de la probabilidad real**. No se asigna esa
probabilidad: el programa no la publica y no hay base para inventarla.

**Conclusión operativa:** no es racional *no* postular por costo. Es racional no
postular porque el gate de elegibilidad está escrito y no se cumple. La
probabilidad es la única variable que importa, y la única palanca real sobre ella
es la adopción demostrable, no la calidad del formulario.

### Lo que no se suma

- Los **USD 10.000 en créditos Azure** (y hasta USD 150.000 de Microsoft for
  Startups) son in-kind, separados, y **no** son caja. No entran en ninguna suma.
- Los grants hipotéticos **no** entran en ningún forecast. El ingreso recibido a
  la fecha es **USD 0**.
- Las descargas de PyPI **no** se convierten en usuarios ni en ingreso.

## 4. Hechos legales y tributarios que faltan

Este documento **no** resuelve la situación tributaria. Solo identifica qué
hechos bloquean qué oportunidad, y formula las preguntas para un contador.

| Hecho | Por qué importa | Estado |
|:--|:--|:--|
| Vehículo para cobrar | GitHub Fund paga vía Sponsors; FLOSS/fund exige cuenta bancaria y documentos tributarios | `NO CONFIRMADO` |
| Persona natural vs. sociedad | chile-hub no es persona jurídica. Ignite exige persona jurídica con fines de lucro; el resto no lo exige explícitamente | Auditoría 3 §0.2 y §D.8 |
| Inicio de actividades | Determina si un aporte del exterior es renta y qué documento emitir | `NO CONFIRMADO` |
| Remesas del exterior y retenciones | Un pago de EE.UU. o de la UE puede tener retención en origen y formularios (p. ej. W-8BEN) | `NO CONFIRMADO` |
| Ley 21.440 | La Auditoría 3 concluye que una persona natural no puede recibir donaciones con beneficio tributario. No se revalida aquí: es materia legal | Citado, no revalidado |
| Uso de la marca "chile-hub" | Relevante si se constituye una entidad | `NO CONFIRMADO` |
| Obligación de rendición | Un aporte sin contraprestación y un grant por hitos se tratan distinto | `NO CONFIRMADO` |

**Regla:** no se constituye una SpA para una oportunidad hipotética. La pregunta
al contador se hace **antes** de cualquier postulación, no después.

## 5. Apoyo pasivo: estado y qué no hacer

| Elemento | Estado verificado | Acción |
|:--|:--|:--|
| `FUNDING.yml` con GitHub + BMC | Presente | **No tocar** mientras rija HOLD |
| Perfil de GitHub Sponsors | Publicado (`hasSponsorsListing: true`), **0 sponsors** | Verificar cobro (humano) |
| Buy Me a Coffee | Página responde 200, **0 supporters públicos** | Verificar cobro (humano) |
| Pedido de apoyo en la CLI | Existe desde 2026-07-29 | **No tocar** |
| Search Console | **Sin registrar** | Registrarlo: es medición, no monetización |
| Tiers, `SPONSORS.md`, sección comercial en landing | No existen | **No crear** mientras rija HOLD |

**Sobre el "único cambio pequeño post-gate":** la evidencia **no** muestra fricción
medible, porque el descubrimiento orgánico no se mide (Search Console sin
registrar). Proponer un experimento de conversión sin línea base sería inventar la
fricción. Por eso no se propone ningún experimento nuevo: la acción pendiente ya
existe y está documentada en
[`docs/adoption-funnel.md`](../adoption-funnel.md#4-descubrimiento-web-sin-medir).

## 6. Presupuesto de horas

Tope del plan operativo: 22 h de investigación y preparación, con una puerta de
continuidad a las 8–10 h.

| Bloque | Estimado | Nota |
|:--|--:|:--|
| Reconocimiento, SHA, documentos canónicos, duplicados | 2,0 h | Protocolo §3 |
| GitHub Fund: bases, formulario, elegibilidad, evidencia | 5,0 h | Incluye abrir y leer los 35 campos |
| Seguridad: controles operativos, Scorecard, brechas | 3,5 h | Incluye ejecutar Scorecard |
| NLnet Restack + CodeSupply | 1,5 h | Triage hasta resolver gates duros |
| Otros fondos (7 vías) | 3,5 h | CORFO, Sercotec, Ignite, STF, FLOSS/fund, D//F, PSF, AWS |
| Redacción de entregables y verificación | 3,0 h | 7 documentos + cronología |
| **Total** | **≈18,5 h** | Bajo el tope de 22 h |

Las horas son **estimación**, no medición instrumentada. No se ejecutó trabajo de
ingeniería ni de datos.

## 7. Dictamen global

> **No hay ninguna vía de efectivo ejecutable hoy sin violar el HOLD o los gates
> del programa.**
>
> Lo que sí está disponible es barato y verificable: los canales pasivos ya
> existen y están a la espera de demanda real; la preparación del expediente está
> hecha; y la única palanca seria sobre las dos oportunidades viables es producir
> evidencia de uso, que hoy es cero y que además está siendo erosionada por diez
> días de publicación detenida.
>
> La recomendación no es "postular mejor". Es "no postular todavía, y arreglar
> primero lo que hace que el proyecto no tenga usuarios demostrables".
