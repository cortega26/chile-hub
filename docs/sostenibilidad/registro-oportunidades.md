# Registro de oportunidades de financiamiento — 2026

> **Qué es.** Registro trazable de las vías de financiamiento evaluadas para
> chile-hub, con fuente primaria, fecha de consulta y veredicto. Es el anexo
> operativo de [`oportunidades-financiamiento-2026.md`](oportunidades-financiamiento-2026.md).
>
> **Qué no es.** No es un plan de negocio, no autoriza postulaciones y no
> reemplaza el estado vigente de [`README.md`](README.md) (HOLD / veredicto D).
>
> **Regla de lectura.** `VERIFICADO` = leído en fuente primaria y citado con
> fecha. `INFERENCIA` = deducción propia, marcada como tal. `NO CONFIRMADO` = no
> se pudo comprobar. `NO APLICA` = requisito sin efecto para este caso.
> Ninguna oportunidad de este registro está postulada, adjudicada ni cobrada.

- **Fecha de consulta de todo el registro:** 2026-10-25 (America/Santiago).
- **Base del repositorio:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`.
- **Sin información personal, tributaria ni bancaria:** por diseño. Lo que
  requiere credenciales o declaración del titular se marca `HUMAN_ACTION_REQUIRED`.

## 1. Resumen

| ID | Oportunidad | Institución | Estado | Monto | Efectivo o in-kind | Veredicto | Bloqueador |
|:--|:--|:--|:--|:--|:--|:--|:--|
| F-01 | GitHub Secure Open Source Fund | GitHub | `OPEN` (rolling) | USD 10.000 | Efectivo (+ créditos Azure in-kind) | **NO-GO (hoy)** | Tracción demostrable: 0 dependents |
| F-02 | GitHub Sponsors | GitHub | `RECURRENT` | Variable | Efectivo | **PASS operativo / USD 0 recibidos** | Verificación de cobro (`HUMAN_ACTION_REQUIRED`) |
| F-03 | Buy Me a Coffee | BMC | `RECURRENT` | Variable | Efectivo | **UNKNOWN / USD 0** | Cobro no verificable sin cuenta |
| F-04 | NLnet Restack | NLnet / CE | `CLOSED` 2026-11-03 | €5.000–50.000 | Efectivo | **NO-GO** | Dimensión europea + política GenAI 2.0 |
| F-05 | NLnet CodeSupply | NLnet / CE | `CLOSED` 2026-11-03 | €5.000–50.000 | Efectivo | **NO-GO** | Encaje (metadatos de paquetes de software) + mismos gates |
| F-06 | Start-Up Chile Ignite | Corfo | `ANNOUNCED` | CLP 30 MM (+20 MM) | Efectivo | **NO-GO** | Exige empresa con ventas; no es un commons |
| F-07 | CORFO — catálogo abierto | Corfo | `OPEN` (33 convocatorias) | Variable | Efectivo | **NO-GO** | Ninguna convocatoria admite OSS sin empresa |
| F-08 | Sercotec — fondos concursables | Sercotec | `RECURRENT` | Variable | Efectivo | **NO-GO** | Solo mipymes formalizadas |
| F-09 | Sovereign Tech Fund | Sovereign Tech Agency (DE) | `RECURRENT` | ≥ €50.000 | Efectivo | **NO-GO** | Mínimo €50k + prevalencia en el ecosistema |
| F-10 | FLOSS/fund | Zerodha | `RECURRENT` (trimestral) | USD 10.000–100.000 | Efectivo | **CONDITIONAL** | "minimal usage" excluido explícitamente |
| F-11 | Digital Infrastructure Insights Fund | Ford / Sloan | `CLOSED` 2026-09-07 | USD 5.000 | Efectivo | **NO-GO** | Convocatoria final cerrada antes de este análisis |
| F-12 | PSF Grants Program | Python Software Foundation | `CLOSED` 2026-08-25 | ≤ USD 2.000 | Efectivo | **NO-GO** | Ronda 2026 solo conferencias/talleres; desarrollo en pausa |
| F-13 | AWS Open Data Sponsorship | AWS | `RECURRENT` | In-kind | In-kind | **NO-GO** | Costo de infraestructura actual ≈ USD 0 |

## 2. Fichas

### F-01 — GitHub Secure Open Source Fund

| Campo | Valor |
|:--|:--|
| `id` | F-01 |
| `nombre` | GitHub Secure Open Source Fund |
| `institucion` | GitHub, con funding partners (Sloan Foundation, Microsoft, Stripe, Shopify, 1Password, Datadog, Vercel, entre otros) |
| `url_oficial` | https://github.com/open-source/github-secure-open-source-fund |
| `url_bases` | FAQ de la misma página + formulario https://forms.office.com/r/YN3MWEKQ5m |
| `consulta_utc` | 2026-10-25 |
| `estado` | `OPEN` — "Applications are open on a rolling basis and will be considered for all Program Sessions"; el formulario declara "Applications are accepted year-round—one application keeps you eligible for all future sessions" |
| `apertura/cierre` | Sin fecha de cierre publicada |
| `monto_moneda` | USD 10.000 por proyecto |
| `cash_o_in_kind` | Efectivo. Los USD 10.000 en créditos Azure y hasta USD 150.000 de Microsoft for Startups son **separados y no son caja** |
| `desembolsos` | USD 6.000 durante el programa + USD 2.000 al mes 6 + USD 2.000 al mes 12 |
| `cofinanciamiento` | No exigido en las bases publicadas |
| `contraparte_elegible` | Mantenedor individual o equipo de máximo 2 personas |
| `exigencia_de_traccion` | **Sí, requisito explícito.** FAQ: "Open source first project with demonstrated community traction and adoption". Formulario, campo 35: "Have an active and growing set of users as determined by GitHub" |
| `pais/residencia` | Región soportada por GitHub Sponsors; **Chile figura en la lista** ([docs](https://docs.github.com/en/sponsors/getting-started-with-github-sponsors/about-github-sponsors)) |
| `persona_natural_o_juridica` | Persona natural (pago vía GitHub Sponsors) |
| `estado_tributario` | No especificado en las bases. El tratamiento local de un pago del exterior es materia de contador (`HUMAN_ACTION_REQUIRED`, ver `financiamiento-30d-decision.md`) |
| `uso_de_IA_permitido` | `NO CONFIRMADO` — las bases publicadas no regulan el uso de IA en la postulación |
| `propiedad_intelectual/licencias` | Exige "clear open source license". No exige cesión de derechos ni cambio de licencia |
| `gastos_financiables` | Tiempo de mantenedor y trabajo de seguridad alineado al programa |
| `obligaciones_y_reportes` | 15 h en 3 semanas + 2,5 h al mes 6 + 2,5 h al mes 12 = **20 h**; asistir a ≥80% de los módulos con cámara encendida; check-ins de seguridad semestrales |
| `requisitos_documentales` | Formulario de 35 campos (verificados uno a uno en `github-secure-oss-fund-eligibilidad.md`). No pide documentos tributarios ni bancarios |
| `restricciones_de_exclusividad` | No publicadas |
| `tiempo_de_postulacion` | ≈4–6 h (estimación propia: 35 campos, sin ensayos largos, varias preguntas de impacto) |
| `horas_de_ejecucion` | 20 h |
| `costos_y_riesgos` | Riesgo principal: **exagerar adopción** para "pasar". Riesgo secundario: reuniones en Pacific Time. No hay costo de postulación |
| `fuente_primaria_evidencia` | FAQ completo y texto íntegro del formulario, capturados el 2026-10-25 (ver `github-secure-oss-fund-eligibilidad.md` §1) |
| `contradicciones` | Ninguna detectada entre FAQ, formulario y blog de anuncio |
| `veredicto` | **NO-GO hoy.** Un gate duro no se cumple (adopción). Ver matriz campo por campo |
| `bloqueador` | `demonstrated community traction and adoption` / `active and growing set of users`: hoy 0 dependents en GitHub y en deps.dev, 0 issues de terceros, 1 PR externo (jun-2026) |
| `siguiente_accion` | Ninguna acción externa. Reevaluar solo si aparece evidencia de uso verificable (rúbrica U1–U3 de la Auditoría 3) |
| `responsable` | Mantenedor |

### F-02 — GitHub Sponsors

| Campo | Valor |
|:--|:--|
| `id` | F-02 |
| `nombre` | GitHub Sponsors (perfil de mantenedor) |
| `institucion` | GitHub |
| `url_oficial` | https://github.com/sponsors/cortega26 |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` — perfil publicado (`hasSponsorsListing: true` vía GraphQL) |
| `monto_moneda` | Variable; sin tiers configurados (`totalCount` de tiers = 0 según la Auditoría 3) |
| `cash_o_in_kind` | Efectivo |
| `comisiones` | 0% en aportes desde cuentas personales; hasta 6% en aportes desde cuentas de organización (3% tarjeta + 3% GitHub), según docs consultadas |
| `exigencia_de_traccion` | Ninguna |
| `pais/residencia` | Chile soportado |
| `estado_tributario` | Remesa del exterior; tratamiento local `NO CONFIRMADO` → contador |
| `uso_de_IA_permitido` | `NO APLICA` |
| `obligaciones_y_reportes` | Ninguna más allá de la declaración tributaria del titular |
| `requisitos_documentales` | `HUMAN_ACTION_REQUIRED`: verificación de identidad, cuenta bancaria y datos fiscales en el panel privado |
| `restricciones_de_exclusividad` | No publicadas |
| `tiempo_de_postulacion` | 0 h (ya habilitado) |
| `costos_y_riesgos` | Exposición pública del perfil, ya existente |
| `fuente_primaria_evidencia` | GraphQL `hasSponsorsListing: true`, `sponsors.totalCount: 0` (2026-10-25); `.github/FUNDING.yml` con `github: cortega26` |
| `veredicto` | **PASS operativo.** Habilitado y con 0 aportes |
| `bloqueador` | No hay bloqueador técnico. La **capacidad efectiva de cobro** (KYC, banco, datos fiscales) no es verificable por API y queda como acción humana |
| `siguiente_accion` | Confirmar en el panel privado que el perfil puede recibir pagos (no hacerlo desde el repositorio) |
| `responsable` | Mantenedor |

### F-03 — Buy Me a Coffee

| Campo | Valor |
|:--|:--|
| `id` | F-03 |
| `nombre` | Buy Me a Coffee |
| `institucion` | Buy Me a Coffee (tercero, fuera de GitHub) |
| `url_oficial` | https://buymeacoffee.com/cortega26 |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` — la página responde HTTP 200; enlace declarado en `.github/FUNDING.yml` |
| `monto_moneda` | Variable |
| `cash_o_in_kind` | Efectivo |
| `exigencia_de_traccion` | Ninguna |
| `pais/residencia` | Cobro internacional; disponibilidad para Chile `NO CONFIRMADO` (requiere cuenta y datos de pago) |
| `estado_tributario` | `NO CONFIRMADO` |
| `obligaciones_y_reportes` | Ninguna reportada |
| `requisitos_documentales` | `HUMAN_ACTION_REQUIRED`: verificación de cuenta y método de cobro |
| `tiempo_de_postulacion` | 0 h |
| `fuente_primaria_evidencia` | HTTP 200 del perfil (2026-10-25); `.github/FUNDING.yml`; 0 supporters públicos (Auditoría 3) |
| `veredicto` | **UNKNOWN** — canal declarado, cobro no verificado, USD 0 recibidos |
| `bloqueador` | Verificación de cobro fuera del alcance del agente |
| `siguiente_accion` | Verificar en el panel privado que la cuenta puede retirar fondos |
| `responsable` | Mantenedor |

### F-04 — NLnet Restack

| Campo | Valor |
|:--|:--|
| `id` | F-04 |
| `nombre` | Restack (Open Internet Stack) |
| `institucion` | NLnet Foundation, con financiamiento de la Comisión Europea (Horizon Europe, grant 101299072) |
| `url_oficial` | https://nlnet.nl/restack/ |
| `url_bases` | https://nlnet.nl/restack/eligibility/ · https://nlnet.nl/restack/guideforapplicants · https://nlnet.nl/foundation/policies/generativeAI/2.0/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `CLOSED` — primera convocatoria abierta 2026-09-03, cierra **2026-11-03 12:00 CET** |
| `monto_moneda` | €5.000–50.000 por propuesta inicial, escalable si hay potencial probado |
| `cash_o_in_kind` | Efectivo (grant por hitos) |
| `contraparte_elegible` | Sin exclusiones categóricas de personas, **pero** el proyecto debe tener "strong European dimension" |
| `exigencia_de_traccion` | No exige tracción; exige encaje con el "Open Internet Stack" |
| `pais/residencia` | Vía obvia: personas de países elegibles Horizon Europe que reciban **≥60% de los fondos**. Excepción discrecional si el proyecto es "of exceptional quality" y el proponente tiene "unique technical expertise" |
| `uso_de_IA_permitido` | **No.** GenAI Policy v2.0: prohibido usar IA generativa para escribir propuestas; en el proyecto financiado, GenAI solo en modo lectura |
| `propiedad_intelectual/licencias` | Resultados bajo licencia libre reconocida |
| `obligaciones_y_reportes` | Grant por hitos con reportes |
| `tiempo_de_postulacion` | 6–10 h si hubiera encaje |
| `fuente_primaria_evidencia` | Páginas de Restack y de elegibilidad; política GenAI v2.0 del 2026-10-20, todas consultadas el 2026-10-25 |
| `veredicto` | **NO-GO** por tres motivos independientes (ver `nlnet-compatibilidad-2026.md`) |
| `bloqueador` | (1) Dimensión europea; (2) política GenAI; (3) encaje temático |
| `siguiente_accion` | Ninguna. No se prepara borrador de propuesta |
| `responsable` | Mantenedor |

### F-05 — NLnet CodeSupply

| Campo | Valor |
|:--|:--|
| `id` | F-05 |
| `nombre` | CodeSupply (Open Internet Stack) |
| `institucion` | NLnet Foundation / Comisión Europea (Horizon Europe, grant 101298846) |
| `url_oficial` | https://nlnet.nl/codesupply/ |
| `url_bases` | https://nlnet.nl/codesupply/eligibility/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `CLOSED` — cierra **2026-11-03 12:00 CET** |
| `monto_moneda` | €5.000–50.000 |
| `cash_o_in_kind` | Efectivo |
| `exigencia_de_traccion` | No; exige contribuir a **metadatos de paquetes de software** y seguridad de supply chain |
| `pais/residencia` | Idéntico a F-04: dimensión europea fuerte |
| `uso_de_IA_permitido` | No para escribir propuestas; solo lectura en el proyecto |
| `veredicto` | **NO-GO** |
| `bloqueador` | El objeto de CodeSupply es metadatos de **paquetes de software** (origen, licencias, vulnerabilidades), no procedencia de datos públicos. Chile-hub no es infraestructura de software supply chain. Presentarlo como tal sería derivar una propuesta artificial |
| `siguiente_accion` | Ninguna |
| `responsable` | Mantenedor |

### F-06 — Start-Up Chile Ignite

| Campo | Valor |
|:--|:--|
| `id` | F-06 |
| `nombre` | Ignite |
| `institucion` | Start-Up Chile / Corfo |
| `url_oficial` | https://startupchile.org/postula/ignite/ |
| `url_bases` | Resolución exenta Corfo N° 1457 de 2025 (PDF enlazado desde la página del programa) |
| `consulta_utc` | 2026-10-25 |
| `estado` | `ANNOUNCED` — la portada declara **"¡Postulaciones cerradas!"** y el programa "¡Atentos a la próxima convocatoria!" |
| `monto_moneda` | CLP 30.000.000 equity-free + hasta CLP 20.000.000 de extensión |
| `cash_o_in_kind` | Efectivo (subsidio) |
| `contraparte_elegible` | Startups con producto funcional, validación temprana y menos de 3 años de desarrollo. Bases: el beneficiario es **persona jurídica con fines de lucro constituida en Chile**; la persona natural participa como "Líder de Equipo" |
| `exigencia_de_traccion` | Sí: etapa de producto con ventas o levantamiento de capital |
| `gastos_financiables` | Comercialización, ventas, empaquetamiento comercial, capital de trabajo |
| `uso_de_IA_permitido` | `NO CONFIRMADO` |
| `tiempo_de_postulacion` | >20 h (formulario + plan de negocio + constitución previa) |
| `fuente_primaria_evidencia` | Portada y página del programa (2026-10-25); bases Corfo 2025 leídas en el PDF oficial |
| `veredicto` | **NO-GO** |
| `bloqueador` | Requiere constituir una sociedad con fines de lucro y un producto que "escale ventas". chile-hub es un commons abierto sin intención comercial mientras rija HOLD. Convertirlo en startup contradice `docs/product-spec.md` ("lo abierto sigue abierto") |
| `siguiente_accion` | Ninguna. Registrar para no repetir la búsqueda |
| `responsable` | Mantenedor |

### F-07 — CORFO, catálogo abierto

| Campo | Valor |
|:--|:--|
| `id` | F-07 |
| `nombre` | Programas y convocatorias Corfo |
| `institucion` | Corfo |
| `url_oficial` | https://www.corfo.gob.cl/sites/cpp/programasyconvocatorias/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `OPEN` — **33 convocatorias** activas al 2026-10-25 |
| `monto_moneda` | Variable por convocatoria |
| `cash_o_in_kind` | Efectivo (cofinanciamiento) |
| `contraparte_elegible` | Mipymes y personas jurídicas con actividad económica formalizada; convocatorias territoriales |
| `exigencia_de_traccion` | Ventas y actividad económica vigente en la mayoría |
| `fuente_primaria_evidencia` | Revisión del catálogo completo (33 resultados) el 2026-10-25: reactivación por inundaciones, inversión productiva regional, turismo, pisco, agricultura, redes asociativas |
| `veredicto` | **NO-GO** |
| `bloqueador` | Ninguna de las 33 convocatorias abiertas admite mantenimiento de software libre ni datos públicos. Todas exigen empresa formalizada y gasto productivo |
| `siguiente_accion` | Revisar solo si aparece una convocatoria de base tecnológica/commons. Frecuencia recomendada: mensual |
| `responsable` | Mantenedor |

### F-08 — Sercotec

| Campo | Valor |
|:--|:--|
| `id` | F-08 |
| `nombre` | Fondos concursables Sercotec |
| `institucion` | Sercotec |
| `url_oficial` | https://www.sercotec.cl/convocatorias/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` |
| `contraparte_elegible` | Micro y pequeñas empresas formalizadas, cooperativas, gremios y ferias libres |
| `gastos_financiables` | Inversión, capital de trabajo, digitalización de pymes, asesorías |
| `fuente_primaria_evidencia` | Catálogo de programas revisado el 2026-10-25 |
| `veredicto` | **NO-GO** |
| `bloqueador` | Todos los instrumentos exigen negocio formalizado (inicio de actividades). No existe línea para OSS o datos abiertos |
| `siguiente_accion` | Ninguna |
| `responsable` | Mantenedor |

### F-09 — Sovereign Tech Fund

| Campo | Valor |
|:--|:--|
| `id` | F-09 |
| `nombre` | Sovereign Tech Fund |
| `institucion` | Sovereign Tech Agency (Alemania, fondos del Bundestag) |
| `url_oficial` | https://www.sovereign.tech/programs/fund |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` — postulación por plataforma, sin fecha de cierre |
| `monto_moneda` | **Mínimo €50.000** por postulación |
| `cash_o_in_kind` | Efectivo |
| `exigencia_de_traccion` | Criterio de "Prevalence": "how widely adopted is the technology within the open source ecosystem" |
| `propiedad_intelectual/licencias` | OSI o FSF aprobadas (MIT cumple) |
| `obligaciones_y_reportes` | Proceso de scoping, revisión legal y contrato (≈6 meses hasta inicio) |
| `fuente_primaria_evidencia` | Página de requisitos y criterios, consultada el 2026-10-25 |
| `veredicto` | **NO-GO** |
| `bloqueador` | (1) Mínimo €50.000 muy por encima de lo que el proyecto puede ejecutar con un mantenedor; (2) financia "open digital base technologies" y explícitamente **no** aplicaciones orientadas a usuario final; (3) prevalencia: 0 dependents |
| `siguiente_accion` | Ninguna |
| `responsable` | Mantenedor |

### F-10 — FLOSS/fund

| Campo | Valor |
|:--|:--|
| `id` | F-10 |
| `nombre` | FLOSS/fund |
| `institucion` | Zerodha |
| `url_oficial` | https://floss.fund/faq/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` — evaluación trimestral por comité interno; el FAQ no publica fechas de ronda |
| `monto_moneda` | USD 10.000 mínimo, hasta USD 100.000/año, en múltiplos de USD 25.000 |
| `cash_o_in_kind` | Efectivo |
| `contraparte_elegible` | Individuos, proyectos, grupos, comunidades u organizaciones; requiere cuenta bancaria y documentos tributarios |
| `exigencia_de_traccion` | **Sí**: "our focus is on supporting existing, widely used, and impactful projects… Very new projects or projects with minimal usage are not considered" |
| `uso_de_IA_permitido` | Sin política publicada → `NO CONFIRMADO` |
| `requisitos_documentales` | Publicar un manifiesto `funding.json` (fundingjson.org) y enviar su URL al directorio público |
| `tiempo_de_postulacion` | ≈2 h (redactar `funding.json` + envío) |
| `costos_y_riesgos` | Publicar el manifiesto hace visible la postulación; requiere decisión del mantenedor |
| `fuente_primaria_evidencia` | FAQ completo consultado el 2026-10-25 |
| `veredicto` | **CONDITIONAL** — el único gate es uso demostrado, y hoy no se cumple |
| `bloqueador` | "minimal usage" excluido de forma explícita. Con 0 dependents y ~27–80 activaciones de bundle al mes, no se cumple |
| `siguiente_accion` | Reevaluar junto con F-01. Si se supera el gate de adopción, es la postulación de menor costo de todo el registro |
| `responsable` | Mantenedor |

### F-11 — Digital Infrastructure Insights Fund (D//F)

| Campo | Valor |
|:--|:--|
| `id` | F-11 |
| `nombre` | 2026 Limited RFP — Digital Infrastructure Insights Fund |
| `institucion` | Ford Foundation y Alfred P. Sloan Foundation |
| `url_oficial` | https://newsletter.infrastructureinsights.fund/ · https://fordfoundation.forms.fm/2026-limited-rfp-digital-infrastructure-insights-fund-2 |
| `consulta_utc` | 2026-10-25 |
| `estado` | `CLOSED` — "final limited open call", cierre **2026-09-07** |
| `monto_moneda` | USD 5.000 por reporte exploratorio (hasta 10 pp. + blog) |
| `cash_o_in_kind` | Efectivo |
| `fuente_primaria_evidencia` | Convocatoria y newsletter consultadas el 2026-10-25; un directorio de financiadores lo reporta además como "ceased operations" (secundario, no prevalece) |
| `veredicto` | **NO-GO** |
| `bloqueador` | Convocatoria final ya cerrada. No se inventa una ventana futura |
| `siguiente_accion` | Ninguna. Archivar |
| `responsable` | Mantenedor |

### F-12 — PSF Grants Program

| Campo | Valor |
|:--|:--|
| `id` | F-12 |
| `nombre` | 2026 PSF Grants Program Funding Round |
| `institucion` | Python Software Foundation |
| `url_oficial` | https://www.python.org/psf/grants/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `CLOSED` — ventana de postulación 2026-08-04 a 2026-08-25; la ronda 2026 se limita a conferencias y talleres entre 2026-12-01 y 2027-04-30 |
| `monto_moneda` | Hasta USD 2.000 (conferencias) / USD 1.500 (talleres) |
| `cash_o_in_kind` | Efectivo |
| `contraparte_elegible` | Eventos y talleres con ≥60% de contenido Python |
| `fuente_primaria_evidencia` | Página oficial de grants; declara explícitamente que "Development work" está **en pausa** como categoría |
| `veredicto` | **NO-GO** |
| `bloqueador` | Cerrada, y el financiamiento de desarrollo está suspendido |
| `siguiente_accion` | Revisar el blog de la PSF cuando anuncie la próxima ronda. Frecuencia: trimestral |
| `responsable` | Mantenedor |

### F-13 — AWS Open Data Sponsorship Program

| Campo | Valor |
|:--|:--|
| `id` | F-13 |
| `nombre` | AWS Open Data Sponsorship Program |
| `institucion` | Amazon Web Services |
| `url_oficial` | https://aws.amazon.com/opendata/open-data-sponsorship-program/ |
| `consulta_utc` | 2026-10-25 |
| `estado` | `RECURRENT` |
| `monto_moneda` | In-kind: cubre el costo de almacenar y compartir datasets públicos en el Registry of Open Data on AWS |
| `cash_o_in_kind` | In-kind |
| `exigencia_de_traccion` | Criterios publicados: accesibilidad (licencia abierta, formatos no propietarios), *cloud readiness*, compromiso comunitario y **"Demand: is there demonstrated interest in your dataset(s)?"** |
| `obligaciones_y_reportes` | Firmar T&C, crear una cuenta AWS exclusiva, publicar una entrada YAML en `awslabs/open-data-registry`, documentación, notebook tutorial con un reto comunitario |
| `fuente_primaria_evidencia` | Página del programa consultada el 2026-10-25 (criterios y proceso de onboarding). Costo actual de infraestructura del proyecto ≈ USD 0 (GitHub Pages, Actions, HF, Zenodo y PyPI gratuitos para repos públicos) |
| `veredicto` | **NO-GO** |
| `bloqueador` | (1) No reduce ningún costo presente: el proyecto no paga infraestructura. Un crédito in-kind no financia el recurso escaso, que es tiempo de mantenedor. (2) El criterio "Demand" repite el mismo gate de adopción que F-01 |
| `siguiente_accion` | Solo reconsiderar si aparece un costo real de hospedaje |
| `responsable` | Mantenedor |

## 3. Vías descartadas por definición (no son oportunidades)

| Vía | Motivo | Fuente |
|:--|:--|:--|
| Consultoría, venta institucional, cold outreach, patrocinios corporativos, API de pago | Fuera de la estrategia de no-prospección y bajo HOLD | `docs/sostenibilidad/README.md`; este plan, §2 clase D |
| Productos digitales de autoservicio (P3) | No hay evidencia de demanda: 0 sponsors, 0 supporters, 0 pedidos de cotización, Search Console sin registrar. Construir antes de medir intención de compra sería intuición | Auditoría 3 §0.2 (fila "Disposición a pagar": "Sin señal") |
| Open Collective / patrocinio fiscal (p. ej. Open Source Collective) | No es un fondo: es un **vehículo** para recibir dinero. Crear la relación es decisión del mantenedor (clase C) y no resuelve por sí solo la falta de demanda | Auditoría 3 §D.8 y adenda 3a |

## 4. Fuentes consultadas

Todas con `consulta_utc = 2026-10-25`.

| Fuente | URL |
|:--|:--|
| GitHub Secure Open Source Fund (FAQ + estado) | https://github.com/open-source/github-secure-open-source-fund |
| Formulario del programa (35 campos) | https://forms.office.com/r/YN3MWEKQ5m |
| Proyectos ya financiados (188) | https://github.com/open-source/github-secure-open-source-fund/projects |
| GitHub Sponsors — regiones y comisiones | https://docs.github.com/en/sponsors/getting-started-with-github-sponsors/about-github-sponsors |
| NLnet Restack | https://nlnet.nl/restack/ |
| NLnet Restack — elegibilidad | https://nlnet.nl/restack/eligibility/ |
| NLnet CodeSupply | https://nlnet.nl/codesupply/ |
| NLnet CodeSupply — elegibilidad | https://nlnet.nl/codesupply/eligibility/ |
| NLnet — GenAI Policy v2.0 | https://nlnet.nl/foundation/policies/generativeAI/2.0/ |
| NLnet — anuncio de política (2026-10-20) | https://nlnet.nl/news/2026/20261020-AI-policy.html |
| Start-Up Chile — portada (convocatorias cerradas) | https://startupchile.org/ |
| Start-Up Chile — Ignite | https://startupchile.org/postula/ignite/ |
| Corfo — catálogo de convocatorias | https://www.corfo.gob.cl/sites/cpp/programasyconvocatorias/ |
| Sercotec — convocatorias | https://www.sercotec.cl/convocatorias/ |
| Sovereign Tech Fund | https://www.sovereign.tech/programs/fund |
| FLOSS/fund — FAQ | https://floss.fund/faq/ |
| D//F — convocatoria final | https://newsletter.infrastructureinsights.fund/ |
| PSF Grants Program | https://www.python.org/psf/grants/ |
| deps.dev — dependents | https://api.deps.dev/v3alpha/systems/pypi/packages/chile-hub/versions/1.51.0:dependents |
| GitHub — dependents | https://github.com/cortega26/chile-hub/network/dependents |
