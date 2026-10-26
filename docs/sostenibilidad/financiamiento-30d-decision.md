# Financiamiento — registro de decisión a 30 días

> **Qué es.** El registro de lo decidido, lo que requiere al mantenedor y las
> fechas que importan. Cierra el paquete de investigación iniciado el 2026-10-25.
>
> **Qué no es.** No modifica el estado vigente de sostenibilidad. El veredicto D y
> el HOLD siguen exactamente donde estaban.

- **Fecha:** 2026-10-25.
- **Base:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`.
- **Lectura previa:** [`oportunidades-financiamiento-2026.md`](oportunidades-financiamiento-2026.md).

## 1. Hechos verificados

| # | Hecho | Fuente | Fecha |
|--:|:--|:--|:--|
| 1 | El gate 149 ya se ejecutó y mantuvo HOLD (Path A). El registro fechado existe en la cronología | `docs/sostenibilidad/README.md` fila 8; `plans/149-...`; commit `e3b452e` | 2026-10-22 |
| 2 | El GitHub Secure Open Source Fund acepta postulaciones **todo el año**, sin fecha de cierre | FAQ + formulario oficiales | 2026-10-25 |
| 3 | El formulario está operativo y tiene 35 campos; se leyó su estructura. No se completó | `forms.office.com/r/YN3MWEKQ5m` | 2026-10-25 |
| 4 | El programa exige, en la casilla contractual, "an active and growing set of users as determined by GitHub" | Campo 35 del formulario | 2026-10-25 |
| 5 | GitHub declara **0 repositorios y 0 paquetes** dependientes de chile-hub | Página oficial de dependents | 2026-10-25 |
| 6 | deps.dev confirma 0 dependientes para la versión 1.51.0 | API deps.dev | 2026-10-25 |
| 7 | En 4 meses: 0 issues de terceros, 1 PR externo (junio) | API de GitHub | 2026-10-25 |
| 8 | PyPI sigue midiendo cadencia: 87,7 descargas por release, R² = 0,933, n = 127 | Regresión propia sobre pypistats | 2026-10-25 |
| 9 | 189 descargas acumuladas del bundle; el número de releases con el asset bajó de 80 a 69 | API de releases | 2026-10-25 |
| 10 | Chile está entre las regiones soportadas por GitHub Sponsors | Docs de GitHub | 2026-10-25 |
| 11 | El perfil de GitHub Sponsors está publicado y tiene 0 sponsors | GraphQL | 2026-10-25 |
| 12 | Las releases de GitHub no tienen firma ni procedencia; PyPI sí tiene atestación | OpenSSF Scorecard + API de integridad de PyPI | 2026-10-25 |
| 13 | OpenSSF Scorecard: 6,2/10 en `3400c810`, con 0 vulnerabilidades y 0 alertas de CodeQL | Scorecard v5.6.0 | 2026-10-25 |
| 14 | La publicación diaria lleva **10 corridas fallidas consecutivas**; datos congelados desde el 2026-10-15 | `gh run list` + logs + `make doctor` | 2026-10-25 |
| 15 | NLnet cerró el paso a propuestas escritas con IA y limita el uso de LLM a lectura en proyectos financiados | Política GenAI v2.0 | 2026-10-20 |
| 16 | Ignite está cerrada y exige persona jurídica con fines de lucro y producto con ventas | Start-Up Chile + bases Corfo | 2026-10-25 |
| 17 | Ninguna de las 33 convocatorias Corfo abiertas admite OSS sin empresa | Catálogo Corfo | 2026-10-25 |
| 18 | D//F celebró su convocatoria final el 2026-09-07; PSF cerró el 2026-08-25 y mantiene desarrollo en pausa | Páginas oficiales | 2026-10-25 |

## 2. Inferencias (marcadas como tales)

| # | Inferencia | Base | Qué la debilitaría |
|--:|:--|:--|:--|
| 1 | La probabilidad de selección del GitHub Fund es la única variable económica relevante; el costo de postular (4–6 h) es despreciable | Aritmética de §3 del índice | Que el programa publicara una tasa de aceptación alta |
| 2 | El conjunto de 188 proyectos financiados sugiere una escala de adopción muy superior a la de chile-hub | Lista pública de proyectos | Que se conociera un proyecto financiado con 0 dependents |
| 3 | La visibilidad actual depende de la red personal de LinkedIn, no de descubrimiento sostenido | 288 de las 316 visitas con referrer registrado vienen de LinkedIn (`linkedin.com` 201 + `com.linkedin.android` 79 + `lnkd.in` 8); 55% de los visitantes únicos se concentran en un solo día | Search Console mostrando tráfico orgánico relevante |
| 4 | Sin restaurar la publicación diaria, cualquier narrativa de impacto es indefendible | 10 días de datos congelados | Que el fallback se resolviera solo |

## 3. Desconocidos

| # | Desconocido | Cómo se resolvería |
|--:|:--|:--|
| 1 | Si el perfil de Sponsors puede efectivamente **cobrar** (KYC, banco, datos fiscales) | Panel privado del titular |
| 2 | Si Buy Me a Coffee permite retirar fondos desde Chile | Panel privado del titular |
| 3 | Tráfico y consultas de búsqueda reales | Search Console (sin registrar) |
| 4 | Tratamiento tributario de un pago del exterior | Contador |
| 5 | Si existe uso institucional no observable (academia, mirrors, uso interno) | Rúbrica U1–U3 de la Auditoría 3 §E, que no se ha ejecutado |
| 6 | Tasa de aceptación del GitHub Fund | No publicada. No se estima |

## 4. Acciones ejecutadas

Todas internas, de solo lectura o de documentación. **Ninguna** acción externa.

| Acción | Resultado |
|:--|:--|
| Protocolo de verificación §3 (pwd, remotes, rama, SHA, estado, fetch) | `main` @ `3400c810`, igual a `origin/main`, árbol limpio |
| Lectura de documentos canónicos (SOURCE_OF_TRUTH, AGENTS, product-spec, sostenibilidad, plan 149, Auditoría 3, embudo) | Estado HOLD confirmado; plan 149 ya ejecutado con Path A |
| Inventario de trabajo equivalente (issues, PRs, planes, docs) | Nada duplicado: no existían documentos de financiamiento |
| Auditoría de elegibilidad del GitHub Fund | [`github-secure-oss-fund-eligibilidad.md`](github-secure-oss-fund-eligibilidad.md) |
| Dossier de evidencia de adopción | [`github-secure-oss-fund-evidencia.md`](github-secure-oss-fund-evidencia.md) |
| Diagnóstico de seguridad operativo + OpenSSF Scorecard | [`security-readiness-funding.md`](security-readiness-funding.md) |
| Triage NLnet | [`nlnet-compatibilidad-2026.md`](nlnet-compatibilidad-2026.md) |
| Registro de 13 oportunidades | [`registro-oportunidades.md`](registro-oportunidades.md) |
| Entrada fechada en la cronología de sostenibilidad | `docs/sostenibilidad/README.md` |
| `make doctor` | **exit 0** (con advertencia de frescura de 247 h) |

## 5. Decisiones que requieren al mantenedor

Solo las que no puede tomar un agente. Cada una con recomendación.

### D1 — Confirmar que el veredicto D y el HOLD siguen vigentes al 2026-11-01

- **Estado:** ya registrado como Path A por el plan 149 (2026-10-22). La revisión
  formal es el 2026-11-01.
- **Qué se pide:** confirmar que el registro existente es la decisión definitiva y
  que no hace falta una nueva.
- **Recomendación:** confirmar. Nada de lo encontrado en este trabajo cambia las
  conclusiones de la Auditoría 3; al contrario, las refuerza (0 dependents
  revalidado, 0 sponsors, 0 organizaciones verificables).
- **Si no se confirma:** el trabajo de este paquete queda como insumo, no como
  decisión.

### D2 — Aceptar el NO-GO del GitHub Secure Open Source Fund

- **Opciones:** (a) aceptar el NO-GO y no postular; (b) autorizar una postulación
  pese al gate de adopción, declarando la limitación de forma explícita.
- **Recomendación:** (a). La opción (b) exige firmar una casilla que afirma "an
  active and growing set of users"; con 0 dependents, hacerlo sería una
  declaración falsa ante el financiador.
- **Reversibilidad:** alta. El programa es rolling: no hay ventana que se pierda.

### D3 — Autorizar (o no) la remediación de procedencia de releases

- **Qué es:** añadir `actions/attest-build-provenance` al job `release` de
  `pypi-release.yml`, para que el bundle ZIP y su `.sha256` tengan atestación
  verificable. Detalle en
  [`security-readiness-funding.md`](security-readiness-funding.md#brecha-1--las-releases-de-github-no-tienen-procedencia-material).
- **Por qué requiere decisión:** su validación exige **una release real en
  producción**. No se puede verificar en local ni en un PR, y toca el workflow más
  crítico del proyecto.
- **Recomendación:** autorizar, pero ejecutarlo **después** de restaurar la
  publicación diaria. Hoy un release no ocurre porque el pipeline está bloqueado;
  la atestación sería un cambio sin oportunidad de validarse.
- **Costo:** ~1 h de implementación + 1 release de observación.

### D4 — Verificar la capacidad de cobro de Sponsors y BMC

- **Qué es:** confirmar en los paneles privados que ambas cuentas pueden recibir y
  retirar dinero (identidad, banco, datos fiscales).
- **Por qué es humano:** exige credenciales, identificación y datos bancarios. El
  agente no debe verlos ni almacenarlos.
- **Recomendación:** hacerlo. Es la única forma de saber si el canal pasivo
  funciona; hoy no se sabe.
- **Resultado esperado:** `puede cobrar` / `no puede cobrar` / `falta X`.

### D5 — Registrar Search Console

- **Qué es:** verificar la propiedad del sitio para empezar a medir descubrimiento
  orgánico.
- **Por qué es humano:** requiere una cuenta y un token.
- **Recomendación:** hacerlo antes de cualquier discusión sobre conversión. Sin
  línea base, cualquier propuesta de mejora pasiva sería intuición.
- **Nota:** no es un experimento nuevo; es una acción pendiente desde el plan 107.

### D6 — Llevar la lista de preguntas al contador

- **Qué es:** resolver los hechos de §4 de
  [`oportunidades-financiamiento-2026.md`](oportunidades-financiamiento-2026.md#4-hechos-legales-y-tributarios-que-faltan).
- **Recomendación:** hacerlo **antes** de cualquier postulación, no después. Y no
  constituir una sociedad para una oportunidad hipotética.
- **Costo:** una consulta.

### D7 — Decidir si hace falta una próxima fecha de revisión

- **Hecho:** según `docs/sostenibilidad/README.md`, la revisión de abril de 2027
  solo se activa si §E se ejecuta y termina en Stop. Si §E nunca se ejecuta,
  **no queda una fecha de revisión futura**.
- **Opciones:** (a) dejar el HOLD sin fecha, como está; (b) fijar una revisión
  periódica (p. ej. anual) aunque §E no se ejecute; (c) ejecutar §E con su tope de
  15 h.
- **Recomendación:** (b), una revisión anual, para que el HOLD no se convierta en
  olvido. No se implementa aquí: cambiar el estado vigente es decisión del
  mantenedor.
- **Nota:** la opción (c) es la única que podría producir el uso demostrable que
  hoy bloquea las dos vías de efectivo, pero exige contacto y el plan operativo no
  lo autoriza.

### D8 — Priorizar la restauración de la publicación diaria

- **Qué es:** el schedule lleva 10 días fallando y los datos están congelados al
  2026-10-15.
- **Por qué se eleva:** no es una tarea de financiamiento, pero es el hecho que más
  afecta la credibilidad de cualquier postulación y la promesa del producto.
- **Recomendación:** tratarlo como la prioridad del proyecto por encima de
  cualquier gestión de fondos.
- **Nota:** ya existe el issue #195. No se duplica.

## 6. Acciones humanas (`HUMAN_ACTION_REQUIRED`)

| # | Acción | Dónde | Bloquea |
|--:|:--|:--|:--|
| H1 | Confirmar identidad, banco y datos fiscales de GitHub Sponsors | Panel privado de GitHub | F-02 |
| H2 | Confirmar método de retiro de Buy Me a Coffee | Panel privado de BMC | F-03 |
| H3 | Verificar propiedad del sitio en Search Console | Google Search Console | Medición de descubrimiento |
| H4 | Consulta contable con la lista de §4 | Contador habilitado | Cualquier postulación futura |
| H5 | Confirmar dedicación de 20 h y zona horaria, si algún día se postula | Agenda personal | F-01 |
| H6 | Envío de cualquier formulario | Portal del programa | Clase C: nunca por el agente |

## 7. Hitos y fechas

| Fecha | Qué ocurre | Acción |
|:--|:--|:--|
| 2026-10-30 | Revisión de adopción del issue #184 | Evaluar contra la rúbrica U1–U3. Si sigue en 0, el NO-GO se confirma |
| 2026-11-01 | Revisión del gate de sostenibilidad (plan 149) | Confirmar D1 |
| 2026-11-03 08:00 CLT | Cierre de Restack y CodeSupply | **Ninguna.** Documentado como NO-GO |
| Continuo | Publicación diaria | Restaurar (issue #195) |
| Sin fecha | Revisión futura | Depende de D7 |

**No hay ninguna fecha de cierre que obligue a actuar en los próximos 30 días.**
El único programa con dinero y encaje (GitHub Fund) es rolling, y su gate no se
resuelve con urgencia sino con uso real.

## 8. Conciliación con el HOLD

Este trabajo **no** modificó el estado vigente. Correspondencia explícita:

| Regla vigente | Cómo se cumplió |
|:--|:--|
| Leer el estado y la Auditoría 3 antes de proponer (§README) | Se leyeron ambos, más el plan 149 y el embudo de adopción |
| No ejecutar `plans/110` ni construir tiers, `SPONSORS.md` o sección comercial | No se creó ninguno |
| No contactar sponsors, vendors, CAF ni financiadores | Cero contactos. Solo lectura de páginas públicas |
| No presentar propuestas de grant | No se presentó ni se redactó ninguna. El documento de NLnet es un análisis de elegibilidad, no una propuesta |
| No presentar descargas de PyPI como instalaciones, usuarios ni audiencia | Se usaron literalmente las frases permitidas de `docs/adoption-funnel.md` |
| No publicar PII ni términos comerciales de terceros | Cero PII. Lo que requiere credenciales está marcado `HUMAN_ACTION_REQUIRED` |
| Registrar cada análisis o decisión en la cronología | Entrada fechada añadida a `docs/sostenibilidad/README.md` |
| Reconciliar de forma explícita cualquier contradicción con la Auditoría 3 | No se encontró contradicción: los datos de hoy refuerzan sus conclusiones |

**Sobre issue #184** ("No pedir dinero, preparar grants ni activar planes de
sponsorship mientras el veredicto D/HOLD siga vigente"): este trabajo **no preparó
un grant**. Preparó una auditoría de elegibilidad cuyo resultado es NO-GO, que es
precisamente lo contrario de preparar una postulación. El paquete de candidatura
descrito en §5.4 del plan operativo **no se redactó**, porque su precondición
—dictamen GO o CONDITIONAL razonable— no se cumple.

## 9. Reporte de continuidad

- **¿Continuar?** No en exploración de fondos. El retorno marginal de buscar una
  decimocuarta vía es cero: los filtros duros (Chile, persona natural, OSS,
  adopción) eliminan el resto del universo identificable.
- **¿Reducir?** Sí: el trabajo restante es mantenimiento de estado, no
  investigación.
- **¿Descartar?** Sí, archivar las 9 vías NO-GO para no repetir la búsqueda.
- **Costo restante:** ≈0 h, salvo las ~2 h de D3 y la consulta contable.

## 10. Reproducibilidad

Todo el paquete se apoya en comandos públicos documentados en cada archivo. El
punto de entrada es:

```bash
make doctor                      # debe dar exit 0
gh api repos/cortega26/chile-hub --jq '{stars:.stargazers_count,forks:.forks_count}'
gh api repos/cortega26/chile-hub/dependabot/alerts --paginate -q 'group_by(.state)|map({state:.[0].state,n:length})'
```

Los detalles por documento están en §6 de
[`security-readiness-funding.md`](security-readiness-funding.md#6-reproducibilidad)
y en §2 del [`registro-oportunidades.md`](registro-oportunidades.md).
