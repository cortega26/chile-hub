# GitHub Secure Open Source Fund — elegibilidad y dictamen

> **Qué es.** Auditoría de elegibilidad campo por campo contra las fuentes
> oficiales vigentes al 2026-10-25, con dictamen y próximos pasos humanos.
>
> **Qué no es.** No es una postulación, no es un borrador de postulación y no
> contiene datos personales. El formulario **no se completó**.
>
> **Estado del expediente:** `PREPARADO PARA DECISIÓN` — sin acción externa.

- **Consulta:** 2026-10-25 (America/Santiago).
- **Base:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`.
- **Evidencia de adopción:** [`github-secure-oss-fund-evidencia.md`](github-secure-oss-fund-evidencia.md).
- **Seguridad:** [`security-readiness-funding.md`](security-readiness-funding.md).

## 1. Fuentes y qué se pudo verificar

| Elemento | Estado de verificación | Evidencia |
|:--|:--|:--|
| Página del programa y FAQ | **VERIFICADO** — leída íntegra (acordeones desplegados) | https://github.com/open-source/github-secure-open-source-fund, 2026-10-25 |
| Formulario de postulación | **VERIFICADO** — se abrió y se leyó su estructura (35 campos). **No se rellenó ni se envió** | https://forms.office.com/r/YN3MWEKQ5m → redirige a `forms.cloud.microsoft` |
| Ventana de postulación | **VERIFICADO**: "Applications are open on a rolling basis and will be considered for all Program Sessions"; el formulario añade "Applications are accepted year-round—one application keeps you eligible for all future sessions" | FAQ + encabezado del formulario |
| Monto y tramos | **VERIFICADO**: USD 10.000 = 6.000 + 2.000 (mes 6) + 2.000 (mes 12) | FAQ, sección "What's the funding amount?" |
| Dedicación exigida | **VERIFICADO**: 15 h en 3 semanas + 2,5 h al mes 6 + 2,5 h al mes 12 = 20 h | FAQ, "What do I have to do if I'm selected?" |
| Regiones de GitHub Sponsors | **VERIFICADO**: Chile está en la lista | https://docs.github.com/en/sponsors/getting-started-with-github-sponsors/about-github-sponsors |
| Créditos Azure | **VERIFICADO como in-kind separado**: USD 10.000 en créditos, hasta USD 150.000 vía Microsoft for Startups. **No es caja** | FAQ, "What do I get if my project is selected?" |
| Proyectos ya financiados | **VERIFICADO**: 188, con nombres y categorías | https://github.com/open-source/github-secure-open-source-fund/projects |
| Criterios internos de selección | **NO CONFIRMADO**: "Projects will be evaluated upon the program and funding ability to impact security" es toda la información publicada | FAQ |
| Tasa de aceptación | **NO CONFIRMADO** — no se publica. No se estima | — |

## 2. Matriz de requisitos

Requisitos tomados literalmente de dos fuentes: el FAQ público y el campo 35 del
formulario ("By checking this box you agree that you must:").

| # | Requisito (literal) | Fuente | Estado | Evidencia |
|--:|:--|:--|:--|:--|
| R1 | "Anyone who is a current maintainer of an open source project" | FAQ | **PASS** | 1 mantenedor documentado; `CONTRIBUTING.md` y `CODEOWNERS` |
| R2 | "You can also apply as a team… (max of 2 people)" | FAQ | **PASS** | Equipo de 1 |
| R3 | "Be age eighteen (18) or older" | FAQ / form | **UNKNOWN — human** | No verificable sin declaración del titular |
| R4 | "Have an active online profile on GitHub" | FAQ / form | **PASS** | `@cortega26`, actividad diaria |
| R5 | "Be located in one of the regions supported by GitHub Sponsors" | FAQ / form | **PASS** | Chile en la lista oficial |
| R6 | "Not be a current employee or contractor of GitHub… (including Microsoft)" | form | **UNKNOWN — human** | Declaración personal |
| R7 | "Clear open source license" | FAQ / form | **PASS** | MIT (`LICENSE`); datos con licencias por fuente en `DATA_LICENSES.md` |
| R8 | "Open source first project with demonstrated community traction and adoption" | FAQ | **FAIL** | 0 dependents (GitHub y deps.dev), 0 issues de terceros, 1 PR externo en 4 meses |
| R9 | "Have an active and growing set of users as determined by GitHub" | form §35 | **FAIL** | Misma evidencia. GitHub es quien lo determina y su propia página de dependents dice 0 |
| R10 | "Clear governance structure prior to kick-off" | FAQ / form | **PARCIAL** | `CONTRIBUTING.md` define autoridad de decisión, `CODEOWNERS`, `docs/release.md`. Faltan `CODE_OF_CONDUCT.md` y un documento de gobernanza dedicado |
| R11 | "Interest and willingness to engage and improve security" | FAQ / form | **PASS** | CodeQL activo y verde, Dependabot con 27 alertas resueltas y 0 abiertas, `SECURITY.md`, atestaciones de PyPI |
| R12 | "Commitment from core leaders to participate" | FAQ / form | **PASS** | El mantenedor es el núcleo |
| R13 | "Agree to Code of Conduct and Privacy Statement" | FAQ / form | **PASS (humano)** | Casilla del formulario; aceptación personal |
| R14 | "Understand how you want to grow and maintain, and secure your open source project" | form §35 | **PARCIAL** | Hay plan técnico (docs, ADRs, CI); no hay plan de crecimiento con usuarios |
| R15 | "Have a plan for how the funding would be used" | form §35 | **PARCIAL** | Existe un objetivo claro (§4), pero preparar el plan de uso forma parte del paquete de candidatura, que no se redacta sin GO |
| R16 | Capacidad de dedicar 15 h en 3 semanas + 2,5 h × 2 | FAQ | **UNKNOWN — human** | Reuniones en Pacific Time; requiere disponibilidad del titular |
| R17 | "Are you signed up for GitHub Sponsors?" (campo 14) | form | **PASS (habilitación) / UNKNOWN (cobro)** | `hasSponsorsListing: true`; verificación de identidad y banco no verificables por API |
| R18 | "Does your project have a Security Lead or Committee?" (campo 15) | form | **NO** | No existe rol formalizado. Es una pregunta, no un requisito de elegibilidad |
| R19 | Agree to Privacy Statement y Code of Conduct de GitHub | form §35 | **PASS (humano)** | Enlaces en el formulario |

**Recuento:** 9 PASS · 3 PARCIAL · 2 FAIL · 3 UNKNOWN human · 1 NO declarado.

## 3. Dictamen

> ### NO-GO (al 2026-10-25)
>
> Motivo único y decisivo: **R8/R9 — adopción demostrable.**
>
> No es un `CONDITIONAL`. Un `CONDITIONAL` implicaría que falta un dato por
> confirmar; aquí el dato existe y es cero: la página oficial de dependents de
> GitHub responde "We haven't found any dependents for this repository yet" y
> deps.dev confirma `dependentCount: 0`.

**Por qué no se degrada a "puede que pase igual":**

1. El requisito está escrito en dos superficies independientes (FAQ y casilla
   contractual del formulario). El solicitante **firma** que cumple.
2. El conjunto publicado de 188 proyectos es, en palabras del propio programa,
   infraestructura "used by millions of developers and organizations". No se usa
   como umbral numérico inventado, sino como evidencia de la escala típica.
3. Presentar 6.372 descargas de PyPI como usuarios constituiría exactamente la
   exageración que `AGENTS.md` §10 prohíbe y que la Auditoría 3 desmontó.

**Lo que sí es favorable y no se debe perder:** licencia, país, mantenimiento
activo (30 commits y actividad de issues en 90 días según OpenSSF Scorecard),
seguridad operativa real y un control de integridad de datos poco común
(rechazo automático de fallbacks). Si la adopción se materializa, el resto del
expediente ya está listo.

## 4. Disparadores de reevaluación

No son umbrales de GitHub: son condiciones internas para volver a abrir el caso.
Se expresan cualitativamente, salvo donde la rúbrica canónica ya existe.

| Disparador | Por qué cambia el veredicto | Fuente de la definición |
|:--|:--|:--|
| ≥1 organización con uso verificable (U1 + U2 + U3) | Es la prueba que el programa pide y la que la Auditoría 3 ya definió | Auditoría 3 §E |
| ≥1 repositorio dependiente verificable (GitHub o deps.dev) | Convierte "sin dependencia observable" en dependencia observable | Medición directa |
| Un tercero abre un issue o PR de uso (no de cortesía) | Evidencia de que alguien ejecuta el código | Historial del repo |
| Publicación diaria restaurada y estable | Sin esto, cualquier afirmación de impacto operativo es falsa | Issue #195 |

Si ninguno ocurre, el caso sigue cerrado. No se vuelve a evaluar por el paso del
tiempo.

## 5. Estado del formulario y pasos humanos

El formulario está **operativo y abierto**. Se leyó su estructura; no se
completó ninguna respuesta.

Campos que **solo** puede completar el titular (no se responden aquí, ni con
datos reales ni de ejemplo):

| Campo | Por qué es humano |
|:--|:--|
| 1–6 (email, nombre, ciudad, región, país) | Datos personales |
| 13 (dedicación full-time a OSS) | Declaración personal |
| 14 (¿está en GitHub Sponsors?) | Requiere confirmar estado real de la cuenta |
| 16–18 (formación y nivel en seguridad, incluida seguridad de IA) | Autoevaluación |
| 24 (autopercepción como persona subrepresentada) | Voluntario y sensible |
| 28 (financiamiento recibido a la fecha) | Declaración |
| 33–34 (LinkedIn, X) | Datos personales |
| 35 (aceptación de términos) | Acto jurídico del titular |

Si en el futuro se autoriza postular, el orden obligatorio es el del checklist
§6 de este documento, seguido del registro de decisión en
[`financiamiento-30d-decision.md`](financiamiento-30d-decision.md).

## 6. Checklist previo a cualquier envío

Se activa **solo** con GO explícito del mantenedor y con el gate de sostenibilidad
resuelto.

- [ ] Gate canónico y aprobación humana documentados por escrito.
- [ ] Convocatoria verificada como abierta el mismo día del envío.
- [ ] R8/R9 resueltos con evidencia nueva fechada, no con una reformulación.
- [ ] Borrador redactado **y revisado por el titular**, con su voz.
- [ ] Presupuesto de 20 h aceptado en calendario real.
- [ ] Capacidad de cobro confirmada (KYC, banco, datos fiscales).
- [ ] Consulta a contador sobre el tratamiento del pago del exterior, por escrito.
- [ ] Revisión de que ninguna cifra infringe `AGENTS.md` §10.
- [ ] Envío ejecutado por el titular.
- [ ] Comprobante archivado **fuera del repositorio**.

## 7. Lo que no se hizo (y por qué)

| Acción | Motivo |
|:--|:--|
| Redactar el paquete de candidatura (§5.4 del plan operativo) | Su precondición es "dictamen GO/CONDITIONAL razonable". El dictamen es NO-GO. Además, `README.md` de sostenibilidad e issue #184 prohíben preparar grants mientras rija HOLD |
| Enviar el formulario | Clase C: requiere aprobación explícita |
| Crear cuenta, verificar identidad, aceptar términos | Clase D: acto jurídico y datos personales |
| Contactar al programa por correo | Cold outreach a financiador: prohibido |
