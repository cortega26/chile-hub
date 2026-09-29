# Plan 110: Programa de patrocinios — sostenibilidad y plan de ataque

> **Qué es:** el diseño operativo del programa de patrocinios de chile-hub:
> tiers, beneficios, reglas de independencia, plan de ataque por segmento
> (doctrina Carnegie), priorización con la tracción actual (~100 estrellas),
> el play para CAF vía contacto cálido, activos requeridos y gobernanza.
>
> **Qué NO es:** no toca código, datos, extractores, validaciones, workflows ni
> contratos. Ningún cambio de este plan puede alterar el pipeline ni la
> publicación. La independencia editorial del proyecto es condición de diseño,
> no un detalle (ADR-023 y principio 4 de `docs/product-spec.md`).
>
> **Drift check (ejecutar primero)**:
> ```bash
> git rev-parse --short HEAD     # anotar hash de referencia al iniciar la Wave 0
> git status --short             # esperado: vacío
> ```
> Este plan es de relaciones y activos de comunicación; si el repo cambió en
> algo que afecte métricas (nuevo release, HF, PyPI), refrescar la sección 0.1
> antes de usarlo con un sponsor. Gana el repo, no este documento.

## Status

- **Priority**: P2 (estratégico; no bloquea release ni pipeline)
- **Effort**: M en Wave 0 (activos) + continuo (relaciones)
- **Risk**: MED — reputacional y de foco del mantenedor si se ejecuta sin reglas;
  MITIGADO por §1.3 (reglas de independencia) y §7 (fair use del tiempo)
- **Category**: sostenibilidad / dirección
- **Planned at**: commit de referencia, 2026-09-29
- **Ejecuta**: operador (relaciones, firma) + agente (redacción de activos, tracker, reportes)
- **No decide aquí**: persona jurídica/vehículo de cobro definitivo (Step 0.3), que
  requiere asesoría contable/legal externa

---

## 0. Contexto

### 0.1 El activo (baseline 2026-09-26; refrescar desde `data/normalized/adoption.json`)

| Qué | Valor | Fuente |
|:---|:---|---:|
| Instalaciones PyPI | ~2.218 / mes · 1.172 / semana | `adoption.json` |
| Descargas mirror HF | 135–197 / mes | API HF |
| GitHub | ~90–100 stars (creciendo), 10 forks | API GitHub / usuario |
| Distribución | 21 capas publicables, 22 construibles, DOI Zenodo, 347 páginas por comuna | README / launch-pack |
| Ingeniería | 1.106 tests, calidad 94/100, CI diario con publicación automática | launch-pack |
| Atención | Post LinkedIn 141–148 reacciones, 16–17 comentarios, 3 leads con issue (#107, #108, #109) | adoption-review / launch-pack |
| Mantenedor | **uno** (bus factor = 1) | NEXT_STEPS (§Largo plazo) |

**Conclusión de contexto:** hay producto, distribución y una audiencia técnica real,
pero no hay capa de financiamiento. Hoy `FUNDING.yml` solo ofrece donación
individual (GitHub Sponsors, Buy Me a Coffee). El patrocinio institucional no es
"pedir plata": es **reducir el bus factor** y dar continuidad a una pieza que ya
usan analistas, desarrolladores, periodistas y docentes.

### 0.2 Lo que un patrocinio SÍ y NO es aquí

| Es | No es |
|:---|:---|
| Financiar mantención, CI, hosting, documentación y continuidad | Comprar datos, capas, prioridades ni silencio |
| Visibilidad honesta ante una audiencia técnica y cívica | Influencia sobre fuentes, validaciones o carriles |
| Alineación de marca con infraestructura pública digital | Afiliación oficial al Estado (ADR-023) |
| Un acuerdo público y divulgado | Exclusividad de categoría o endoso implícito |

### 0.3 Los 5 principios no negociables del programa

1. **Lo abierto sigue abierto** (product-spec, principio 4): ningún pago crea
   muro, versión "premium" del dato ni adelanto de acceso. Se puede patrocinar
   la operación; nunca comprar el dato.
2. **La fuente oficial manda** (product-spec, principio 1): un sponsor no
   cambia qué se publica, de dónde se extrae ni cómo se valida. Los pedidos de
   datos entran por `dataset_request` y pasan `docs/dataset-inclusion-criteria.md`.
3. **Sin afiliación oficial**: ningún logo, carta o comunicación puede sugerir
   que chile-hub es del Estado, de datos.gob.cl o de una institución fuente.
4. **Divulgación**: todos los sponsors se publican (`SPONSORS.md` + sección en
   landing). El uso de fondos se resume anualmente.
5. **Derecho a decir no**: se rechaza dinero de data brokers, vigilancia,
   partidos/campañas, apuestas o cualquier actor cuyo modelo dependa de cerrar
   o ensuciar el dato público. Criterio escrito en `SPONSORS.md`.

---

## 1. Doctrina Carnegie aplicada

> La regla madre: **no vendemos un patrocinio; presentamos una oportunidad de
> que ELLOS ganen algo que ya quieren.** El dinero es la consecuencia, no el pitch.
> Si no hay "sí" hoy, debe quedar una relación útil.

| Principio | Qué significa en chile-hub | Antipatrón prohibido |
|:---|:---|:---|
| No criticar ni quejarse | Nunca decir "tus datos/portal están desordenados"; decir "nosotros hacemos la última milla de lo que ustedes ya publican" | "Los portales chilenos son un desastre" |
| Interés genuino | Investigar su memoria anual, su agenda de datos/ESG/educación **antes** de escribir; citarles algo puntual y real | Correo genérico enviado a 20 organizaciones |
| Despertar el deseo | Abrir por el resultado de ELLOS (menos soporte, más reuso, clase lista, caso de uso, talento) | Abrir hablando de nuestras necesidades y costos |
| Hablar en su interés | Métrica por segmento: INE quiere reuso; un banco quiere decisión territorial; HF quiere showcase | Mismo deck para todos |
| Hacerlos sentir importantes | "Nadie en LatAm tiene esto; serían los primeros en habilitarlo" | "Somos un proyecto chico que necesita plata" |
| Ver su punto de vista | Respetar procurement, presupuesto anual, legal, impuestos, tiempos | Apurar cierres "antes de fin de mes" |
| Que la idea sea de ellos | Ofrecer opciones (in-kind / Semilla / Aliado / adopta una capa) y co-diseñar el beneficio | Llegar con un contrato único e innegociable |
| Dramatizar | Demo en vivo: `pip install chile-hub`, SQL en el navegador, 31 comunas en un join | PDF de 40 páginas sin demo |
| Dar aprecio sincero | Reconocer lo que su organización ya hace por los datos abiertos, con ejemplo concreto | Halago vacío de LinkedIn |
| Retar (challenge) | "Ser el primer patrocinador institucional de la infraestructura de datos abiertos de Chile" | "Cualquier aporte sirve" |

**Estructura canónica de todo primer mensaje (5 bloques, ≤150 palabras):**
1. Gancho personalizado sobre ELLOS (algo real y verificado).
2. Su problema/agenda en una frase.
3. Qué hace chile-hub + una prueba dura (métrica o demo).
4. La oportunidad para ellos (2–3 opciones concretas).
5. El pedido mínimo: 15 minutos, o un "¿te hago llegar el brief?".

**Cadencia de seguimiento:** D+0 mensaje; D+5 recordatorio con algo nuevo
(dato nuevo, release, caso); D+20 cierre cordial ("te dejo en la lista de
novedades; si cambia el ciclo de presupuesto, me avisas"). Nunca más de 2
seguimientos. Nunca pedir que "voten" ni difundir por favores personales.

---

## 2. Tiers de patrocinio

### 2.1 Estructura

| Tier | Aporte anual (USD) | Perfil típico | Cupos |
|:---|:---|:---|:---|
| **Semilla** | 250–500 | ONGs pequeñas, comunidades, individuos, medios | sin límite |
| **Colaborador** | 1.000–2.500 | Universidades, ONGs medianas, startups, centros de estudio | sin límite |
| **Aliado** | 5.000–7.500 | Empresas, fundaciones corporativas, consultoras | sin límite |
| **Estratégico** | 15.000+ | Corporativos, multilaterales, fondos filantrópicos | 5 (por capacidad de acompañamiento) |
| **Infra (in-kind)** | valorizado ≥ 2.500 | Vendors de herramientas del stack (créditos, CI, hosting, CDN) | 6 |
| **Fundador** | tier + compromiso 2 años | Primeros 3 en entrar (cualquier tier) | **3, por única vez** |

**Founding (acelerador de arranque):** los primeros 3 patrocinadores de cualquier
tier obtienen mención permanente "Funding Sponsor" en `SPONSORS.md` y en la
landing, con precio anual congelado por 2 años. Es la "oportunidad única" real:
no hay nada que comprar después que sea equivalente.

### 2.2 Matriz de beneficios

| Beneficio | Semilla | Colaborador | Aliado | Estratégico | Infra |
|:---|:--:|:--:|:--:|:--:|:--:|
| Nombre/logo en `SPONSORS.md` + reporte anual | ✓ | ✓ | ✓ | ✓ | ✓ |
| Logo + enlace (UTM) en README/landing, sección Patrocinios | — | ✓ | ✓ | ✓ destacado | ✓ |
| Reporte trimestral de impacto (métricas reales + casos anonimizados) | anual | ✓ | ✓ | ✓ a medida | ✓ |
| Sesión de onboarding técnico para su equipo (1/año) | — | ✓ | ✓ | ✓ | — |
| Caso de estudio co-firmado / post conjunto | — | — | ✓ | ✓ | ✓ (técnico) |
| Briefing trimestral del roadmap (sin voto sobre fuentes) | — | — | ✓ | ✓ + mesa | — |
| Prioridad de respuesta en issues de integración (fair use, §7) | — | 1 sesión | 2 h/mes | 6 h/mes | 1 sesión |
| "Adopta una capa": financiar la mantención de una capa estable existente | — | — | ✓ | ✓ | — |
| Link de reclutamiento ("trabaja en X") | — | — | ✓ | ✓ | — |
| Nombramiento en el release Zenodo + charla para su equipo | — | — | — | ✓ | — |

**Regla de "Adopta una capa":** financia el mantenimiento de una capa que YA
está `stable_publishable`; no compra su inclusión, su exclusividad, ni cambios
en su contenido. Si la capa se retira por criterios técnicos, el aporte se
redirige a mantención general (cláusula en el acuerdo).

### 2.3 Uso de fondos y fulfillment

- **≥70%** mantención y continuidad (horas del mantenedor, co-mantenedor,
  respuesta a incidencias); **≤20%** infraestructura (CI, dominios, hosting,
  DOI); **≤10%** reserva legal/contable.
- Resumen anual público en `SPONSORS.md` (montos agregados, sin detalle
  confidencial).
- **Costo de fulfillment:** cada tier consume horas de mantenedor (onboarding,
  reportes, briefings). Esas horas se presupuestan en §7 y son la razón de los
  cupos de los tiers Estratégico/Infra.

---

## 3. Plan de ataque por segmento

> Formato: qué quiere ELLOS primero; después qué ofrecemos y qué pedimos.
> Los nombres son objetivos de estudio, no compromisos: validar cada uno contra
> su agenda pública antes del primer contacto (§1, interés genuino).

### 3.1 Vendors del stack (Infra / in-kind)

| Campo | Detalle |
|:---|:---|
| Objetivos | DuckDB Labs / MotherDuck, Polars Inc., Astral (uv/ruff), Hugging Face, Cloudflare, GitHub/Microsoft, AWS, Google Cloud, Zenodo, Apache Arrow |
| **Qué quieren ELLOS** | Casos de uso públicos y creíbles; adopción de sus herramientas; feedback real; comunidad; un showcase cívico en LatAm que hoy no tienen |
| Qué ofrecemos | Vitrina técnica: DuckDB-WASM en la landing, export DuckDB/SQLite en cada release, Polars en la API, uv/ruff en CI, mirror HF, Pages en Cloudflare, Actions en GitHub |
| Ask | In-kind (créditos CI/cloud, hosting/CDN, listing en su página de adopción) o tier Infra; caso de estudio conjunto |
| Entrada | DevRel / Open Source Program / GitHub Discussions / Discord oficial — **nunca** ventas |
| Prueba | 1.106 tests, CI diario, pipeline determinista, 21 capas, DOI |
| Objeción → respuesta | "No patrocinamos proyectos chicos" → "No pedimos dinero: pedimos permiso/in-kind para publicar el caso; si su programa existe, aplicamos" |

**Primer movimiento:** 2 correos cortos (EN) a DevRel de DuckDB y Polars citando
el uso real en `src/builders/formats.py` y la landing; un issue/discussion público
en Astral pidiendo su programa OSS; aplicación a los programas de créditos de
Cloudflare/AWS/GCP. Objetivo: 2 logos in-kind que den prueba social a la Wave 2.

### 3.2 Universidades y centros (Colaborador)

| Campo | Detalle |
|:---|:---|
| Objetivos | U. de Chile (DCC, FEN, CMM), PUC (DCC, Economía, CEP, CPP), UAI (GobLab, Data Science), USACH, UDP (periodismo de datos), U. de Concepción, U. Austral, CEAZA, IMFD, CENIA, Observatorio de Ciudades UC |
| **Qué quieren ELLOS** | Clases con datos reales sin gastar semanas limpiando; investigación reproducible; papers/tesis con DOI citable; menos soporte a alumnos |
| Qué ofrecemos | "Dataset listo para tu curso": 346 comunas, notebooks Colab, contratos de esquema, DOI; guest lecture; temas de tesis/memoria; pasantías |
| Ask | 1.000–2.500 USD/año (presupuesto de docencia/investigación) o in-kind: pasantía, horas de ayudante, hosting del sitio |
| Entrada | Profesor/a de un ramo concreto (no el rectorado); intro por alumni; ofrecer primero el uso gratis del dataset en un curso y luego la mantención |
| Prueba | DOI (`10.5281/zenodo.22968698`), 347 páginas por comuna, citation.md, notebooks |
| Objeción → respuesta | "No hay presupuesto" → in-kind o Semilla; "¿lo van a mantener?" → este programa existe justamente para eso; mostrar compromiso de 2 años |

**Primer movimiento:** elegir 3 ramos concretos (uno de ingeniería, uno de
ciencias sociales, uno de periodismo) y escribir al profesor con el notebook de
su área; el lead de CEAZAmet (#107) es la puerta de entrada al mundo centros.

### 3.3 ONGs, fundaciones y periodismo de datos (Semilla / Colaborador)

| Campo | Detalle |
|:---|:---|
| Objetivos | Fundación Ciudadano Inteligente, CIPER, Fundación Datos Protegidos, Espacio Público, LaBot, Fundación País Digital, Fundación Chile; internacionales: Open Knowledge Foundation, ODI, Derechos Digitales, Internews |
| **Qué quieren ELLOS** | Capacidad de investigación territorial sin contratar ingeniería; credibilidad; capacitación; un bien común que su comunidad usa |
| Qué ofrecemos | Semilla; taller de 1–2 h para su equipo de datos; caso de uso co-firmado; respuesta preferente fair use; visibilidad ante audiencia técnica |
| Ask | 250–2.500 USD/año **o** amplificación + caso de uso (si no hay caja) |
| Entrada | Editor/a de datos o director/a de investigación; los comentarios del post LinkedIn ya dieron 3 leads |
| Prueba | Datos comunales con fuente por capa, DOI, reportes de salud del hub |
| Objeción → respuesta | "Somos una ONG chica" → Semilla o trueque por caso/difusión; el patrocinio no es obligación para usar los datos |

**Primer movimiento:** responder los comentarios pendientes del post (Tushar,
Cristian, Luis — ver `docs/launch-pack.md` §5), agradecer y **no vender**; a las
2 semanas, ofrecer a CIPER/FCI un taller gratuito. El taller convierte mejor que
cualquier correo.

### 3.4 Empresas que monetizan decisiones territoriales (Aliado / Estratégico)

| Campo | Detalle |
|:---|:---|
| Objetivos | Inmobiliario: Toctoc, Portal Inmobiliario. Retail/banca/seguros: Falabella, Cencosud, BCI, Banco de Chile, Santander, RIMAC. Telecom/energía: Entel, Enel. Consultoría: Deloitte, PwC, EY, Cadem/GfK. Startups: Citify (ya identificada en `docs/backlog/08-evaluacion-producto-comercial.md`) |
| **Qué quieren ELLOS** | Decisiones de expansión/riesgo más rápidas; analistas que dejan de mantener planillas; narrativa ESG/datos abiertos; marca empleadora ante devs y analistas |
| Qué ofrecemos | Aliado/Estratégico; onboarding para su equipo de datos; caso de estudio (previa aprobación); "Adopta una capa"; link de reclutamiento |
| Ask | 5.000–15.000+ USD/año |
| Entrada | Jefatura de Data/Analytics, Expansión, Riesgo o Sostenibilidad — no compras ni marketing corporativo |
| Prueba | Ahorro de horas de ingeniería; 21 capas cruzan por CUT; reproducibilidad y linaje que su auditoría puede citar |
| Objeción → respuesta | "Lo hacemos interno" → costo total de mantenerlo: extractores, validaciones, cambios de fuente, CI; aquí ya está resuelto. "¿Qué obtengo?" → visibilidad + onboarding + caso + continuidad |

**Orden obligatorio:** primero **Citify** como design partner (caso de uso real
con su nombre), y solo después los grandes. Sin caso, la banca no conversa.
Regla: nunca aceptar un pedido de dato como condición del patrocinio (§0.3).

### 3.5 Sector público y fondos nacionales (convenio / fondo)

| Campo | Detalle |
|:---|:---|
| Objetivos | datos.gob.cl / Secretaría de Gobierno Digital, INE, BCN, SUBDERE, MINSAL, MINEDUC, MMA; fondos: ANID/FONDEF, CORFO, Laboratorio de Gobierno |
| **Qué quieren ELLOS** | Más reuso de sus datos con menos soporte; detección temprana de enlaces roto y cambios de esquema; cumplir metas de gobierno abierto/transparencia |
| Qué ofrecemos | Reporte público de problemas aguas arriba (principio 3 "buen vecino"); talleres; vitrina de sus datos a través de chile-hub (sin implicar afiliación) |
| Ask | Convenio de colaboración o postulación conjunta a fondo de innovación; **no** un "patrocinio" comercial |
| Entrada | Unidad de datos abiertos / transparencia; universidad como co-postulante para ANID/FONDEF |
| Prueba | Los issues de leads (#107 DGA/DMC, #108 energía) muestran que la comunidad pide datos; chile-hub reporta fallas upstream |
| Objeción → respuesta | "Ya publicamos en datos.gob.cl" → "Ustedes publican; nosotros hacemos la última milla que sus usuarios reclaman" |

**Advertencia de independencia:** jamás insinuar endoso estatal. Para
instituciones públicas la palabra "sponsor" no aplica (no pueden patrocinar
comercialmente); usar "convenio de colaboración" y aprobar cada comunicación
con su unidad de comunicaciones. Si el convenio condiciona el contenido
publicado, se rechaza.

### 3.6 Multilaterales y fondos filantrópicos (grant / programa)

| Campo | Detalle |
|:---|:---|
| Objetivos | **CAF (prioritario, §4)**, BID, Banco Mundial, CEPAL, UNICEF; fondos: Chan Zuckerberg Initiative (EOSS), McGovern Foundation, NLnet, Omidyar/Luminate; fiscal hosts: NumFOCUS, Open Source Collective |
| **Qué quieren ELLOS** | Bienes públicos digitales replicables país por país; evidencia de impacto medible; complementar la agenda de transformación digital regional sin construir desde cero |
| Qué ofrecemos | Piloto LatAm de infraestructura de datos: Chile funcionando + interés real de Perú y Bolivia (leads de `docs/launch-pack.md` §5); metodología abierta; métricas; gobernanza; plan de escalamiento |
| Ask | Grant/programa 20.000–100.000 USD o cooperación técnica; en el caso de fiscal hosts, hosting de fondos |
| Entrada | Programa de transformación digital/datos, no oficina de comunicaciones; **siempre warm intro** (§4) |
| Prueba | DOI + adopción + pipeline auditable + reporte de uso de fondos |
| Objeción → respuesta | "¿Por qué no lo hace el Estado chileno?" → velocidad e independencia; ya trabajamos con sus datos y les devolvemos reportes; "¿es sostenible?" → programa de patrocinios diversificado y resumen anual |

---

## 4. Priorización estratégica (con ~100 estrellas)

### 4.1 Diagnóstico honesto

Con ~90–100 estrellas, un cold pitch a procurement corporativo convierte cerca
de cero: no hay prueba social que mitigue el riesgo percibido. Los activos
reales son (a) **calidez** (contactos personales, leads, vendors que ya se
benefician gratis), (b) **nicho** (datos chilenos no tienen competencia directa),
(c) **costo de oportunidad bajo para el sponsor** (tiers accesibles). Por lo
tanto: **primero los que ya nos conocen o ganan con nuestro éxito; los logos
grandes vienen después de los primeros casos.**

### 4.2 Modelo de scoring (0–3 por criterio, 15 máx.)

Calidez (ya nos conoce/alguien nos presenta) + Capacidad (puede pagar) +
Fit de misión + Facilidad (bajo esfuerzo de entrada) + Seguridad (bajo riesgo
reputacional). Se recalcula cada mes en el tracker.

### 4.3 Olas de ataque

| Ola | Cuándo | A quién | Objetivo de salida (prueba social) |
|:---|:---|:---|:---|
| **Wave 0 — activos** | Semanas 1–3 | Nadie. Construir §6 (SPONSORS.md, sección landing, brief, política, tracker) | Todo listo; sin activos no se contacta a nadie |
| **Wave 1 — calidez** | Semanas 3–8 | Contacto CAF (§5, pedir consejo), leads #107–#109 y CEAZAmet, vendors in-kind (3.1) | 1 conversación CAF + 2 sponsors in-kind = primeros logos |
| **Wave 2 — misión** | Mes 2–4 | Universidades (3.2) y ONGs/periodismo (3.3) | 2–3 Semilla/Colaborador + 2 casos de uso escritos |
| **Wave 3 — escala** | Mes 3–6 | Multilaterales/fondos (3.6) con dossier + cartas de interés; Fiscal host decidido | 1 propuesta de grant enviada |
| **Wave 4 — dinero grande** | Mes 4–9 | Empresas territoriales (3.4), Citify primero | 1 Aliado + 1 caso publicado con cliente |
| **Wave 5 — público** | Mes 6+ | Convenios/fondos nacionales (3.5), con universidad co-postulante | 1 postulación conjunta |

**Regla de secuencia:** ninguna ola arranca en frío; cada una usa logos, casos
o cartas de la anterior. Si la Wave 1 no produce ningún "sí", se revisa el pitch
antes de gastar la Wave 2 (no se escala lo que no funciona).

### 4.4 Top 10 inicial (scoring preliminar, a validar)

| # | Objetivo | Segmento | Score est. | Primer movimiento |
|:--:|:---|:---|:--:|:---|
| 1 | **CAF** (vía contacto) | Multilateral | 14 | Reunión de consejo, cero pedido de dinero (§5) |
| 2 | Hugging Face | Vendor | 13 | DevRel: ya alojan el mirror; ofrecer dataset card + caso |
| 3 | DuckDB Labs / MotherDuck | Vendor | 12 | Caso del playground WASM + export en cada release |
| 4 | Polars Inc. | Vendor | 12 | Caso de API de datos cívicos con Polars |
| 5 | CEAZAmet (lead real) | Centro/ONG | 12 | Cerrar respuesta de #107 y proponer taller |
| 6 | Citify | Empresa/startup | 12 | Design partner → caso → luego Aliado |
| 7 | U. de Chile / PUC / UAI (ramos) | Universidad | 11–13 | 3 profesores concretos, dataset de su área |
| 8 | Astral (uv/ruff) | Vendor | 11 | Programa OSS; caso CI |
| 9 | CIPER / Fundación Ciudadano Inteligente | ONG | 11 | Taller gratuito → Semilla/Colaborador |
| 10 | Open Source Collective / NumFOCUS | Fiscal host | 12 | Aplicar como vehículo para recibir fondos |

> Los scores son estimaciones de trabajo (no datos); viven en el tracker privado
> y se actualizan tras cada contacto. No se publican ni se citan como hechos.

---

## 5. El play de CAF (contacto cálido de 30 años)

> Premisa Carnegie: **primero consejo, no dinero.** Un amigo con buen puesto
> ayuda más (y más rápido) si lo consultas como experto que si le pides un favor
> que debe tramitar. La amistad es el canal; el proyecto debe venderse solo.

### Fase A — Conversación de consejo (30 min, sin pedir nada)

- Apertura: aprecio sincero y específico por su trayectoria; cero pitch largo.
- Encuadre textual: *"No vengo a pedirte plata ni a pedirte que gestiones nada.
  Vengo a pedirte perspectiva: llevo chile-hub, un proyecto de datos abiertos
  de Chile, y quiero entender cómo se ve esto desde donde tú estás."*
- Preguntas (que él hable el 80%):
  1. ¿Qué prioridades tiene la agenda de transformación digital/datos de la
     región este año?
  2. ¿Qué instrumentos usan para apoyar bienes públicos digitales (cooperación
     técnica, fondos, programas)?
  3. ¿Qué tendría que demostrar un proyecto como chile-hub para que valga la
     pena apoyarlo?
  4. ¿Quién más debería ver esto y por qué?
  5. ¿Te parece que te haga llegar un brief de 2 páginas?
- Cierre Carnegie: agradecer el tiempo y **devolver algo** (datos listos para
  un informe suyo, una demo, una charla para su equipo) — reciprocidad real.

### Fase B — Brief de 2 páginas + demo de 20 min

- Encuadre regional: **piloto de infraestructura pública digital** ya funcionando
  en Chile, con interés registrado de Perú y Bolivia; replicable por diseño.
- Una página de métricas duras (adopción, validación, DOI) y una de gobernanza
  (independencia, licencias, uso de fondos, sostenibilidad).
- Reciprocidad explícita: informes regionales con datos limpios, publicaciones
  conjuntas, visibilidad de CAF como habilitador (con su aprobación previa de
  comunicaciones).

### Fase C — Instrumento y propuesta

- Preguntar directamente: *"¿Cómo se financias esto dentro de CAF: cooperación
  técnica, fondo de innovación, programa regional, o a través de un socio local
  (universidad/fundación)?"* — el vehículo lo define él, no nosotros.
- Pedir lo mínimo valioso: **carta de interés** aunque no haya fondos directos
  (abre puertas y da legitimidad para la Wave 2/3).
- Si hay señal, co-diseñar una propuesta de 2–3 páginas con hitos medibles
  (replicar en un segundo país, cobertura, transferencia de metodología).

### Fase D — La red como premio

- Pedir 2 intro ducciones cualificadas (BID, ministerio, fundación aliada).
  El activo del contacto es la red; el cheque es un posible subproducto.

### Guardrails del play

- **No nombrar a la persona ni a CAF en público** (docs, posts, pitch a otros)
  sin permiso explícito por escrito.
- No usar presión de amistad ni mencionar "mi amigo en CAF" a terceros.
- Aceptar un "no" con elegancia total: se agradece, se mantiene la relación, se
  pide feedback sobre el brief.
- Registrar cada reunión en el tracker privado: fecha, qué pidió, qué ofrecimos,
  siguiente paso. Reciprocidad y seguimiento impecable.

---

## 6. Activos requeridos (Wave 0, checklist)

| # | Activo | Contenido mínimo | Verificación |
|:--:|:---|:---|:---|
| 1 | `SPONSORS.md` | Tiers, beneficios, política de independencia (5 reglas), sectores excluidos, sponsors actuales, resumen de uso de fondos | Enlazado desde README; `make doctor` exit 0 |
| 2 | Sección "Patrocinios" en landing + README | Tiers, cómo aportar, sponsors actuales, CTA de contacto | `make verify-landing` verde; bloque JSON-LD intacto (`scripts/check_landing_sync.py`) |
| 3 | Brief de impacto (1–2 páginas, ES + EN) | Misión, métricas reales (`adoption.json`), gobernanza, tiers, qué financia tu aporte, contacto | Revisado contra `adoption.json`; sin cifras estimadas |
| 4 | Vehículo de cobro y facturación | Decisión entre facturación local (ecosistema Tooltician) y fiscal host internacional; números de cuenta/contratos | Asesoría contable; documentado en `SPONSORS.md` |
| 5 | Plantilla de acuerdo (2 páginas) | Alcance, sin SLA de datos, sin influencia, uso de marca, divulgación, vigencia, salida, adopción de capa | Revisión legal simple; coherente con §0.3 |
| 6 | Política de divulgación y conflicto de interés | Qué se publica, qué no; quién aprueba; exclusión de sectores | Parte de `SPONSORS.md` |
| 7 | UTMs y medición de valor | Links `?utm_source=<sponsor>` en README/landing; reporte trimestral de clicks | 1 link por sponsor verificado antes de publicar |
| 8 | Plantillas de outreach (ES/EN) | §Apéndice A | Revisadas por un tercero (claridad, tono) |
| 9 | Tracker privado | Embudo, scores, contactos, próximos pasos, consentimiento de datos | **Fuera del repo** si contiene datos personales (Ley 21.719) |
| 10 | Página/lista de espera de tiers limitados | Founding (3) y Estratégico (5) con cupos visibles | Lenguaje de escasez honesto (cupos reales por capacidad) |

> Anti-drift: los activos 2 y 3 dependen de artefactos que ya se regeneran
> (`adoption.json`, `hub_health.json`). No duplicar sus cifras a mano en la
> landing; enlazar o regenerar.

---

## 7. Gobernanza, métricas y time budget

### 7.1 Embudo (medición mensual en el tracker)

Contactos → respuestas → reuniones → propuestas → cierres, por ola y segmento.
KPIs: tasa de respuesta (>20% en cálidos; si es menor, el pitch está mal),
reunión→propuesta, propuesta→cierre.

### 7.2 Cartera

- Ingreso anual recurrente (cash + valorizado in-kind, separados).
- **Diversificación:** ningún sponsor > 35% del total; si ocurre, priorizar
  el siguiente cierre sobre renovar al grande.
- Renovación anual ≥ 70% (meta año 1). Renovación = reporte de impacto 90 días
  antes + conversación, nunca cobro automático.

### 7.3 Valor entregado

Clicks UTM por sponsor/mes, menciones, casos publicados, reuniones de
onboarding realizadas. Es la prueba para renovar y para pedir referidos.

### 7.4 Time budget del mantenedor (fair use)

| Tier | Horas/mes tope |
|:---|:---:|
| Semilla | 0 |
| Colaborador | 2 |
| Aliado | 4 |
| Estratégico | 8 |
| Infra | 2 |

Si la demanda supera el tope: se contrata ayuda con el propio financiamiento
(esto es parte del pitch, no una excusa). Ninguna obligación de sponsor puede
retrasar el pipeline ni la publicación diaria.

---

## 8. Riesgos y aspectos no cubiertos (lo que faltaba)

| # | Aspecto | Decisión/plan |
|:--:|:---|:---|
| 1 | **Vehículo legal y tributario** | Wave 0, activo 4. Sin vehículo claro no se recibe dinero. La facturación local (Tooltician) simplifica lo local; el fiscal host (Open Source Collective/NumFOCUS) habilita lo internacional con fee. Asesoría contable obligatoria. |
| 2 | **Privacidad de contactos** | No scrapear correos de LinkedIn. Trackear solo con consentimiento; datos personales fuera del repo (Ley 21.719). El launch-pack ya publica comentaristas: no ampliar esa exposición. |
| 3 | **Neutralidad política** | Partidos, campañas y candidatos quedan excluidos por política (no por caso). Escrito en `SPONSORS.md`. |
| 4 | **Uso de marca** | Lineamientos de logo chile-hub para sponsors y de logos de sponsors en el sitio (tamaño, disposición, `rel="sponsored"` en enlaces para no canibalizar SEO). |
| 5 | **Bus factor** | Mensaje central: el patrocinio compra **continuidad**, no features. Los hitos de sostenibilidad (co-mantenedor, fondo de reserva) se reportan. |
| 6 | **Expectativa de exclusividad** | No se vende. Si un sponsor la exige, se ofrece co-marketing intenso en su vertical sin exclusividad. Si insiste, se declina. |
| 7 | **Costo oculto de beneficios** | Cada beneficio tiene horas (§7.4). Antes de vender un Estratégico, verificar capacidad real de acompañamiento. |
| 8 | **Ciclos de presupuesto** | Universidades y empresas definen presupuesto en Q4 para el año siguiente; fondos tienen convocatorias. El tracker guarda la "ventana" de cada objetivo. |
| 9 | **Transparencia** | `SPONSORS.md` + resumen anual de fondos. La transparencia es también el antídoto reputacional ante "¿por qué aceptan dinero de X?". |
| 10 | **Fracaso del programa** | Plan B declarado: si a los 6 meses no hay cierres, se replantea a grants + Open Collective + apoyo en especie (no se fuerza la venta ni se baja la ética). |
| 11 | **Legalidad de "sponsor" público** | Entidades públicas no patrocinan comercialmente: convenio/fondo. Nunca logo de institución pública junto a "sponsors" comerciales. |
| 12 | **Idioma** | Vendors y multilaterales en inglés; universidades, ONGs y empresas en español. Brief en ambos idiomas (activo 3). |
| 13 | **Accesibilidad** | La sección de patrocinios debe cumplir lo mismo que el resto de la landing (contraste, foco, alt). `make verify-landing` + revisión manual. |
| 14 | **Concentración de poder** | La mesa de retroalimentación (Estratégico) es consultiva y su existencia se publica; las decisiones de fuentes siguen en `dataset-inclusion-criteria.md`. |
| 15 | **Tiempo de respuesta** | Regla de cortesía: responder a todo sponsor en < 48 h hábiles; un sponsor ignorado es una renovación perdida. |

---

## 9. Steps de ejecución y done criteria

### Step 0 — Wave 0: activos (sin outreach)

- Crear los activos §6 (1–10). Ningún contacto antes de tener brief, política y
  vehículo de cobro decidido.
- **Done:** `make doctor` exit 0; `make verify-landing` verde; `SPONSORS.md`
  enlazado desde README; brief revisado contra `adoption.json`; tracker creado
  (privado); 0 solicitudes enviadas.

### Step 1 — Wave 1: calidez

- Reunión de consejo con el contacto CAF (§5, Fase A).
- 3 contactos in-kind (Hugging Face, DuckDB, Polars) + solicitudes a programas
  OSS (Astral, Cloudflare/AWS/GCP).
- Cerrar los leads #107–#109 con agradecimiento y taller ofrecido.
- **Done (métricas de salida):** 1 reunión CAF registrada con próximos pasos;
  ≥2 sponsors in-kind confirmados; ≥3 conversaciones cálidas documentadas.

### Step 2 — Wave 2: misión

- 3 profesores (ramos concretos), 2 ONGs/medios con taller gratuito primero.
- Publicar la sección de patrocinios con los primeros logos (prueba social).
- **Done:** ≥2 Semilla/Colaborador cerrados; ≥2 casos de uso escritos; logos
  publicados con UTM midiendo.

### Step 3 — Wave 3: escala

- Dossier regional + propuesta a CAF/relevantes (BID, fondos) usando cartas de
  interés de Wave 1–2. Fiscal host operativo.
- **Done:** ≥1 propuesta de grant enviada; vehículo internacional operable;
  meta intermedia de ingresos = cubrir CI + dominio + 0,5 FTE de mantenedor.

### Step 4 — Wave 4: empresas

- Citify design partner → caso → 3 conversaciones con banca/retail/inmobiliario.
- **Done:** ≥1 Aliado cerrado; 1 caso público con cliente; 0 promesas de dato
  hechas a cambio de dinero (auditoría de promesas).

### Step 5 — Revisión y registro

- Registrar avance en `docs/adoption-review.md` (nueva entrada "Programa de
  patrocinios") o documento companion, con métricas reales del tracker.
- Recalcular scores y olas el primer lunes de cada mes.
- **Done:** entrada fechada; `make doctor` exit 0; sin cambios en `data/`.

## STOP conditions (detente y reconsidera)

- No hay vehículo de cobro claro → **no recibir dinero** (activar fiscal host).
- Un sponsor condiciona el aporte a cambiar fuentes, capas o validaciones →
  declinar y documentar.
- El contacto CAF pide no ser mencionado o no quiere participar → respetarlo y
  buscar la vía institucional sin él.
- El programa consume >8 h/mes sin cierres a los 3 meses → pausar y revisar
  pitch antes de seguir.
- Cualquier activo propuesto toca `data/normalized/`, extractores o workflows →
  fuera de alcance de este plan (abrir plan técnico aparte).

---

## Apéndice A — Plantillas de primer mensaje

> Todas ≤150 palabras, personalizadas en la primera línea (investigar antes).
> Adjunto sugerido: brief §6-3; nunca un deck de 40 diapositivas.

**A.1 Vendor in-kind (EN, DevRel):**
```
Subject: chile-hub ships <tool> in a daily civic-data pipeline — showcase?

Hi <name> — I maintain chile-hub (github.com/cortega26/chile-hub), an open data
layer for Chilean public data: 22 validated layers, ~2.2k PyPI installs/month,
1,100+ tests, daily CI, DuckDB/Parquet outputs.

<tool> is already core to the stack: <uso concreto>. I'm setting up an
infra-sponsors program (in-kind credits or just a published case study) and
<org> is the first name that came to mind.

Not asking for money today — would 15 minutes with your team make sense?
```

**A.2 Universidad (ES, profesor/a):**
```
Asunto: Datos comunales listos para tu curso (sin limpieza previa)

Hola <nombre>: vi que dictas <ramo> y que trabajas con <tema>. Mantengo
chile-hub, una librería con 346 comunas, Códigos CUT como texto, contratos
de esquema validados y DOI para citar (zenodo.org/...).

Te dejo el dataset y el notebook de <área> para tu curso, sin costo. Si les
sirve y quieren sostener la mantención, tenemos un programa de patrocinio
desde US$250/año. ¿15 minutos para mostrarte cómo usarlo en una clase?
```

**A.3 ONG / periodismo (ES):**
```
Asunto: Para tus investigaciones territoriales: datos listos en una línea

Hola <nombre>: seguí <investigación reciente> y pensé en ustedes. Mantengo
chile-hub: 21 capas comunales (censo, salud, educación, pobreza, finanzas)
limpias, cruzables por CUT y con fuente citable por capa.

Ofrezco un taller de 1 h para su equipo de datos, gratis. Si además quieren
que el proyecto siga mantenido, existe un tier Semilla (US$250–500/año) con
reconocimiento público. ¿Les tinca el taller?
```

**A.4 Empresa (ES, jefatura de datos/expansión):**
```
Asunto: Perfil territorial comunal sin mantener planillas internas

Hola <nombre>: <gancho de su negocio: apertura de sucursales, riesgo,
expansión>. Mantengo chile-hub, la capa de datos comunales que usan equipos
de análisis en Chile: 21 capas validadas, cruce por CUT, actualización diaria
y linaje auditable.

Puedo mostrarle en 20 minutos cuánto tiempo de ingeniería ahorra a su equipo
y cómo se vería <su caso>. Tenemos tiers Aliado/Estratégico (desde US$5k/año)
con onboarding, caso conjunto y visibilidad. ¿Agendamos?
```

**A.5 Multilateral (ES, vía intro):**
```
Asunto: Piloto replicable de infraestructura de datos abiertos (Chile → LatAm)

Hola <nombre>: <referencia al intro>. chile-hub es una capa de datos públicos
chilenos ya operando: 21 capas, 2.2k instalaciones/mes, DOI, pipeline
auditable. Hay interés concreto de equipos en Perú y Bolivia.

Buscamos un programa/cooperación técnica para financiar la mantención y
replicar la metodología en un segundo país. Adjunto brief de 2 páginas con
métricas, gobernanza y plan. ¿Les parece una conversación de 30 minutos?
```

**A.6 Seguimiento (D+5, cualquiera):**
```
Hola <nombre>: te dejo una novedad mientras decides: <release/dato/caso nuevo>.
Si no es el momento, sin problema — quedo atento y no vuelvo a insistir.
```

---

## Apéndice B — Objeciones frecuentes

| Objeción | Respuesta (tono Carnegie: sin discutir, desde su interés) |
|:---|:---|
| "Los datos son gratis, ¿por qué pagar?" | "No venden datos — eso queda abierto. Tu aporte paga que sigan limpios, validados y en línea; el costo real es mantener el pipeline todos los días." |
| "No está en el presupuesto" | "Entiendo. ¿Te hago llegar el brief para el próximo ciclo? Mientras tanto, el tier Semilla o el in-kind no requieren procurement." |
| "Debería financiarlo el Estado" | "El Estado publica los datos; la independencia de esta capa es justamente su valor. Depender solo de fondos públicos la haría frágil." |
| "¿Cuál es el ROI?" | "Visibilidad ante ~2.200 instalaciones/mes, reporte trimestral con clicks medidos, onboarding para tu equipo y continuidad de algo que ya usas." |
| "¿Y si el mantenedor desaparece?" | "Ese es exactamente el riesgo que tu patrocinio reduce: financia continuidad, documentación y un eventual co-mantenedor." |
| "Denos exclusividad" | "No vendemos exclusividad, por la misma razón ética por la que no vendemos el dato. Sí podemos hacer co-marketing intenso en su vertical." |
| "¿Pueden agregar/cambiar X dataset por el aporte?" | "Los pedidos entran por el proceso público de criterios, igual para todos. El patrocinio no compra contenido; financia mantención." |
| "Muéstrame que no es un hobby" | "1.106 tests, CI diario con gates, publicación automática, DOI y 22 releases; el brief tiene el detalle auditable." |
| "Mandémoslo a marketing" | "Perfecto — ¿me presentas a quien maneja datos/ESG? El caso es técnico y su equipo es quien más gana." |

---

*Este plan se actualiza tras cada ola (ver rutina en `plans/README.md`).
El tracker operativo (con contactos) vive fuera del repo. Toda promesa hecha a
un sponsor debe poder rastrearse a una fila de §2.2 — lo que no está en la
matriz, no se promete.*
