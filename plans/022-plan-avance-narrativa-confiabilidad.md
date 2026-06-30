# Plan 022: Plan de avance — narrativa de confiabilidad, honestidad de datos, señales pasivas y expansión de catálogo por valor de cruce

> **Naturaleza de este plan**: es un **plan maestro estratégico** (no un plan de
> implementación de una sola superficie como 014/020/021). Define dirección, orden,
> secuencia, esfuerzo, riesgo y tradeoffs de varias líneas de trabajo, y un
> **protocolo de reevaluación** para reordenar prioridades con el tiempo. Cada fase
> remite a tareas concretas; las tareas grandes se desglosarán en sub-planes
> numerados (023+) al momento de ejecutarlas.
>
> **Executor instructions**: No ejecutes varias fases en paralelo sin pasar por el
> *gate* de decisión de cada fase (ver §8). Antes de iniciar cualquier tarea, corre
> el "Drift check" de su fase. Al cerrar cada fase, completa el registro de
> reevaluación (§9) y actualiza la fila de estado en `plans/README.md`.

## Status

- **Priority**: P1 (dirección prioritaria del proyecto)
- **Effort**: L (programa de ~12+ semanas, dos tracks paralelos)
- **Risk**: MED (la Fase 3 y la Ola B2 — scraping/fuentes frágiles — concentran el riesgo; el resto es LOW)
- **Depends on**: ninguno para empezar. **Track A** (Fases 1-4) y **Track B** (expansión de catálogo) corren en paralelo.
- **Category**: estrategia / narrativa / datos / observabilidad / expansión de catálogo
- **Planned at**: 2026-06-30, a partir del análisis de dirección estratégica
- **Revised at**: 2026-06-30 — el operador decidió que el catálogo es demasiado delgado para investigadores que cruzan datos; se añade **Track B** (expansión por valor de cruce, co-primario). Ver §7B y registro §9.4.
- **Status**: TODO

---

## 1. Contexto y tesis (autocontenido)

`chile-hub` es una capa de datos reproducible y curada sobre datasets públicos
oficiales de Chile (15 capas, pipeline determinista fail-loud, contratos JSON
Schema, provenance, refresh diario por CI, librería + CLI `ChileHub`, landing en
`tooltician.com/chile-hub/`). Su función estratégica **no es ser un negocio**, sino
un **activo técnico, reputacional y open-source**, y una puerta de entrada elegante
y no invasiva al ecosistema Tooltician.

**Diagnóstico (2026-06-30).** El proyecto **no tiene un problema de ingeniería**: el
backlog estratégico está 100% cerrado (`docs/backlog/scorecard.md`), hay 490 tests,
ADRs, y calidad de datos promedio A (93.5, `data/normalized/dataset_quality.md`).
Tiene un problema de **conversión de atención en confianza profesional**: la
maquinaria que demuestra habilidad real es **invisible** para quien llega, y existe
una **fuga de credibilidad** puntual.

**Tesis.** La dirección de mayor apalancamiento es **hacer visible y verificable la
confiabilidad ya construida** (narrativa técnica anclada en artefactos), sostenida
sobre una **corrección de honestidad previa**. No construir más features.

> **chile-hub debe crecer como activo técnico, reputacional y open-source, no como
> negocio directo.** Toda decisión de este plan se subordina a ese principio.

## 2. Evidencia que fundamenta el plan

**Fuerte (verificada el 2026-06-30):**

- **`finanzas_municipales.parquet` = 3 filas (3/346 comunas)**, pero figura como
  "capa 11" de pleno derecho en `README.md` (~línea 155) y en `datapackage.json`.
  Grado B (75) en `dataset_quality.md`. Es la única fuga de credibilidad concreta.
- **Drift del README:** la tabla marca `resultados_educacionales` e
  `indicadores_urbanos_siedu` como `🟡 fallback`, pero el pipeline ya los promovió a
  live (345 y 6.701 filas; `hub_health.json: live_count 13, fallback_count 2`). La
  cara pública, mantenida a mano, **subvende** el estado real.
- **Adopción real pequeña vs. métrica vanidosa:** PyPI marca **3.224 descargas/mes**,
  pero el **bundle de GitHub Releases acumula ~3 descargas por release (44 histórico
  total)**. El bundle se cachea tras la primera descarga y `data_dir=` local lo
  evita, así que subcuenta recurrentes; aun así el orden de magnitud dice que las
  **activaciones reales están en decenas, no en miles**. El número de PyPI está
  dominado por mirrors/CI/bots.
- **El público correcto ya llega, pero la atención decae:** referrers dominados por
  LinkedIn (532 visitas combinadas), luego GitHub (59), Google (28), PyPI (23). Las
  vistas diarias cayeron de 399 (18 jun) a un dígito (27-29 jun). No hay motivo
  renovable para volver/compartir.
- **Madurez de ingeniería:** 490 tests, contratos en runtime
  (`src/chile_hub/contracts.py`, `contracts/datasets/`), 5 ADRs (`docs/adr/`),
  semantic-release (28 tags), CodeQL, dependency-review, refresh diario.
- **Limpieza legal del bundle:** `redistribution_report.json: ready_count 15` (todo
  CC-BY/CC0). Es un activo que **no se debe ensuciar**.
- **Decisión previa ya tomada:** `docs/backlog/08-evaluacion-producto-comercial.md`
  descartó con evidencia una API premium / producto de pago. No se reabre aquí.

**Supuestos a validar (marcados como incertidumbre):**

- Que el tráfico de LinkedIn es la red profesional del autor (reclutadores/pares) y
  no usuarios finales. Lo sugiere el patrón, no hay dato de usuario.
- Que Google (28 visitas) es SEO incipiente capitalizable.

## 3. Restricción operativa: ejecución SIN retroalimentación externa

No hay feedback (0 issues, 0 discussions, 0 telemetría). Por tanto **el plan no
puede depender de demanda externa para decidir**. Regla operativa:

> Cada hito se valida contra **artefactos internos verificables** (reportes máquina,
> tests, 0-drift) y **señales pasivas** (descargas del bundle, analítica web sin
> PII), nunca contra "lo que piden los usuarios" — porque hoy nadie pide nada.

## 4. Decisiones transversales

### 4.1 Telemetría mínima — **SÍ, pero solo pasiva; NO _phone-home_ en la librería**

**Tradeoff declarado:** instrumentar `ChileHub` para que "llame a casa" daría señal
por-dataset precisa, pero **contradice frontalmente el activo central del proyecto**
(confianza/trazabilidad), es un detonante clásico de reputación negativa en open
source, roza Ley 19.628/GDPR y añade infraestructura (endpoint, almacenamiento,
política de privacidad) para un mantenedor único. El costo supera al beneficio.

**Decisión, en orden de prioridad:**

1. **Cosechar descargas del bundle (GitHub Releases API).** Cero código en la
   librería, cero privacidad comprometida. Es la métrica de **uso real** que hoy no
   se lee. Script tipo `scripts/usage_snapshot.py` que registre semanalmente
   `assets[].download_count` por release.
2. **Tendencia PyPI** (vía `pypistats`), **etiquetada como "incluye bots"** — nunca
   como métrica de éxito.
3. **Analítica web sin cookies ni PII en la landing** (Plausible / GoatCounter /
   Cloudflare Web Analytics), **declarada** en una nota de privacidad. Da lo que hoy
   falta: profundidad de atención (tiempo, scroll) y, vía eventos de descarga sobre
   los `*.parquet` que `index.html` ya expone, un **proxy ético de qué dataset
   interesa** — sin tocar la librería.
4. **NO** instrumentar `ChileHub`. Si en el futuro se necesita uso por-dataset
   preciso, la única vía aceptable es **opt-in explícito, apagado por defecto**
   (variable de entorno). **Diferido** hasta tener una pregunta concreta.

### 4.2 Scraping con Scrapling + curl — **SÍ, condicionado, y solo para sanar/endurecer; NO para agregar datasets**

**Contexto técnico:** `curl_cffi==0.15.0` y `playwright==1.61.0` **ya son
dependencias** del pipeline, así que Scrapling (fetcher dinámico basado en Playwright
+ AutoMatch para selectores cambiantes) no introduce una categoría de dependencia
nueva. La cadencia ≤ 1 vez/mes propuesta es correcta: baja cadencia = baja
exposición a mantenimiento (un scraper mensual que se rompe es un problema mensual,
no un incendio diario).

**Tradeoff declarado:** el scraping puede **sanar** `finanzas_municipales` (mejor que
solo relabelarlo) y endurecer fallbacks, pero el HTML de portales gubernamentales es
el input **menos estable** y el de mayor riesgo legal. Se acepta **solo** bajo 5
guardarraíles, todos ya reglas del repo:

1. **Legal primero** (`AGENTS.md §6` + semáforo de redistribución). Scrapear ≠ poder
   redistribuir. **El scraping no debe degradar la limpieza del bundle**
   (`ready_count 15`). Una fuente con términos dudosos puede usarse para
   **derivar/verificar** pero quizá **no** entrar al bundle público.
2. **Snapshot crudo append-only + provenance + fail-loud.** Guardar el crudo en
   `data/raw/` (invariante #3), registrar URL + timestamp + modo, y **abortar** si la
   página cambió. Envolver Scrapling dentro del contrato `BaseExtractor`
   (`src/extractors/base.py`).
3. **Preferir "encontrar el archivo/endpoint oculto" (curl) antes que renderizar.**
   Es lo que funcionó con SIEDU (`.xlsm` directo) y MINEDUC (RAR). curl/`curl_cffi`
   para estáticos; Scrapling-AutoMatch para HTML frágil; **Scrapling dinámico
   (Playwright) solo cuando el JS es inevitable** (caso SINIM: requiere JS/POST).
4. **Workflow mensual aislado**, desacoplado del refresh diario, con **fallback al
   último snapshot bueno**. Un scrape inestable nunca rompe el build diario.
5. **Honestidad de cadencia.** Un dataset scrapeado mensual **no** se marca `live`
   (que implica extracción por build); se declara cadencia "mensual/programada".

**Disciplina de alcance:** usar scraping para (a) sanar `finanzas_municipales` y
(b) endurecer fallbacks existentes. **No** como pretexto para "más datasets" — eso
contradiría la tesis ("menos datasets, más confiables").

**Secuencia clave:** relabelar `finanzas_municipales` con honestidad **ya** (Fase 1,
barato, cierra la fuga hoy); intentar el scrape como **sanación que, si funciona, lo
asciende** (Fase 3). **No bloquear la corrección honesta al éxito del scrape.**

## 5. Mapa de líneas de trabajo y dependencias

Dos tracks **co-primarios** que corren en paralelo:

```
TRACK A — confiabilidad, narrativa y observabilidad
  Fase 1  Honestidad y base de confianza        (sem 1-2)   ── prerequisito de 3
  Fase 2  Narrativa técnica visible             (sem 3-5)   ── independiente de 1, recomendable después
  Fase 3  Señales pasivas + sanación (scraping) (sem 6-9)   ── requiere Fase 1
  Fase 4  Distribución + decisión playground    (sem 10-12) ── requiere Fase 2

TRACK B — expansión de catálogo por valor de cruce (ver §7B)
  Ola B1  CASEN pobreza + consumo eléctrico CNE  (sem 2-6)  ── 'accepted', al bundle público
  Ola B2  CEAD delincuencia + electoral          (sem 7+)   ── candidate/needs-research, fuera del bundle; requiere gate B1
```

Orden recomendado de Track A: **1 → 2 → 3 → 4**, con la analítica web (2.3) iniciada en
la Fase 2 para acumular datos antes de la Fase 4. Las Fases 1 y 2 pueden solaparse; 3 y 4
**no** deben adelantarse a sus prerrequisitos.

**Convergencia entre tracks:** la Ola B2 (CEAD, scraping mensual) **reutiliza** el workflow
mensual aislado de la Fase 3.3; por eso B2 se programa después de que la Fase 3 establezca esa
infraestructura. La corrección de `finanzas` (1.1) y la expansión (B1) son independientes y
arrancan ambas de inmediato.

## 6. Escala de estimación

- **Esfuerzo:** S (≤1 día), M (2-5 días), L (>1 semana).
- **Riesgo:** LOW / MED / HIGH.
- Convenciones del repo: español neutral; rutas relativas a `__file__`; workflows con
  acciones pineadas por SHA; `uv` como gestor; commits Conventional Commits; no push
  ni PR salvo indicación del operador.

## 7. Plan por fases (detalle)

### Fase 1 — Honestidad y base de confianza (sem 1-2)

**Drift check:** `git diff --stat HEAD -- README.md data/dataset_catalog_config.json data/normalized/hub_health.json` y verificar que `finanzas_municipales` siga en ~3 filas (`pyarrow.parquet.ParquetFile("data/normalized/finanzas_municipales.parquet").metadata.num_rows`).

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| 1.1 | Relabelar `finanzas_municipales` | Cerrar la fuga de credibilidad (3/346) | `README.md`, `data/dataset_catalog_config.json` | S | LOW | Baja el conteo "headline" de capas → se reencuadra como rigor, no retroceso | Ninguna capa <50% cobertura se presenta como completa; etiqueta "parcial/candidato" visible |
| 1.2 | Auto-generar el bloque de capas del README desde reportes | Eliminar el drift manual README↔reportes | `src/builders/landing.py`, `src/builders/reports.py`, plantilla README | M | LOW | Más complejidad de build vs. README a mano; se acota a un bloque marcado entre delimitadores | 0 inconsistencias README↔`hub_health.json`; se regenera en cada build |
| 1.3 | Cosechar descargas del bundle (telemetría pasiva #1) | Tener la métrica de uso **real** | nuevo `scripts/usage_snapshot.py` | S | LOW | Señal subcuenta recurrentes (cache) → se documenta la limitación | Serie histórica semanal de descargas del bundle archivada |

**Gate de salida Fase 1:** la fuga está cerrada y el README no puede volver a
driftear. Sin esto, **no** se inicia la narrativa (Fase 2) ni el scraping (Fase 3):
contar una historia de confiabilidad sobre una fuga visible la destruye.

### Fase 2 — Narrativa técnica visible (sem 3-5)

**Drift check:** confirmar que existen y están frescos `data/normalized/provenance_report.md`, `redistribution_report.md`, `hub_health.md` y `contracts/datasets/*.json`.

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| 2.1 | Sección README "Por qué puedes confiar" | Hacer visible la maquinaria (contratos, fail-loud, provenance, drift) | `README.md` → enlaza reportes y `contracts/datasets/` | S | LOW | Riesgo de tono autopromocional → cada afirmación ancla a un artefacto ejecutable | Prueba de confiabilidad legible en <2 min; enlaces a reportes funcionando |
| 2.2 | Case study "Cómo está construido chile-hub" | Activo reputacional central + funnel suave a Tooltician | nuevo en `docs/` + landing | M | LOW | Riesgo "CV disfrazado" → narrativa de ingeniería (problema→arquitectura→resultado→aprendizajes), no de marketing | Enlazable desde LinkedIn como prueba de skill; sin CTAs comerciales |
| 2.3 | Analítica web cookieless (telemetría #3) | Medir profundidad de atención + interés por dataset | `index.html`, nota de privacidad, `app.js` | S-M | LOW | Cualquier analítica añade un tercero → se elige herramienta sin cookies ni PII y se declara | Panel de atención operativo y declarado; eventos de descarga de `*.parquet` capturados |

**Gate de salida Fase 2:** existe una historia técnica verificable y una forma de
medir si la atención profundiza. Recién aquí tiene sentido distribuir (Fase 4).

### Fase 3 — Señales pasivas operativas + sanación de fuentes vía scraping (sem 6-9)

**Drift check:** `git diff --stat HEAD -- data/source_registry.json src/extractors/` y revisar `AGENTS.md §6` y `docs/datasets/finanzas_municipales-degradacion.md` por si las condiciones de la fuente cambiaron.

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| 3.1 | Revisión legal de fuentes candidatas | No degradar la limpieza del bundle | `AGENTS.md §6`, `DATA_LICENSES.md`, `data/source_registry.json` | S | LOW | Tiempo de análisis antes de código vs. avanzar rápido → se prioriza no ensuciar `ready_count 15` | Cada fuente clasificada (redistribuible / derive-only / no usar) **antes** de tocar código |
| 3.2 | PoC scrape `finanzas_municipales` (SINIM) | Sanar la única capa rota | nuevo `src/extractors/sinim_*`, `data/raw/`, contrato en `contracts/datasets/` | M-L | **HIGH** | El portal requiere JS/POST y es frágil → Scrapling dinámico + fail-loud + fallback; aceptar "no avanzar" como resultado válido | Cobertura comunal validada **o** decisión fundada y documentada de no avanzar |
| 3.3 | Workflow mensual aislado | Desacoplar scraping del build diario | nuevo `.github/workflows/monthly-scrape.yml` | M | MED | Otro workflow que mantener vs. seguridad del build diario → el diario nunca depende del scrape | Build diario verde aunque el scrape falle; fallback al último snapshot bueno |
| 3.4 | Metadata de cadencia honesta | No marcar scrape mensual como `live` | `data/source_registry.json`, builders de reportes | S | LOW | "live" se ve mejor que "mensual" → se prioriza honestidad sobre estética | `source_mode`/cadencia reflejan la realidad en health y README |

> Si 3.2 logra cobertura plena, `finanzas_municipales` **asciende** de "parcial"
> (Fase 1) a capa completa — sin haber bloqueado la honestidad en el intento. Si
> falla, queda relabelada y honesta, que es un estado aceptable.

**Gate de salida Fase 3:** las fuentes problemáticas están sanas o declaradas con
honestidad, y existe una observabilidad de uso real (3.x + 1.3) sin telemetría
intrusiva.

### Fase 4 — Distribución sobre lo validado + decisión playground (sem 10-12)

**Drift check:** `git diff --stat HEAD -- CHANGELOG.md docs/release.md plans/020-duckdb-wasm-playground.md` y revisar la analítica acumulada de la Fase 2.

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| 4.1 | Release notes legibles para humanos | Recircular tráfico hacia el relato, no al repo crudo | `CHANGELOG.md`, `docs/release.md` | S | LOW | Doble mantenimiento (Conventional Commits + notas) → notas solo en minor/major | Cada release minor+ cuenta una historia legible |
| 4.2 | 1 post técnico basado en el case study | Reactivar atención con profundidad | externo (LinkedIn) | S | MED | Promoción sin sustancia daña → publicar **solo** tras Fase 2 | Segundo pico de tráfico con mayor profundidad de sesión que el de junio |
| 4.3 | Decisión go/no-go del playground DuckDB-Wasm | Demo viva solo si la atención lo justifica | `plans/020-duckdb-wasm-playground.md`, landing | M (si go) | MED | Feature atractiva pero costosa → **gate explícito** con datos de Fase 2-3 | Decisión basada en métrica de atención, no en estética |

**Gate de salida Fase 4:** el proyecto tiene narrativa, observabilidad, distribución
mínima y una decisión informada sobre el playground. Punto natural de **reevaluación
mayor** del plan completo (§9).

## 7B. Track B — Expansión de catálogo por valor de cruce (co-primario, arranca ya)

**Por qué (evidencia y decisión).** El catálogo declara 15 capas, pero el catálogo
**temático cruzable** es delgado: 6 son andamiaje territorial/derivado (`regiones`,
`provincias`, `comunas`, `comunas_enriquecidas`, `distritos_electorales`,
`perfil_territorial_comunal`), dos son directorios (`establecimientos_salud/educacionales`),
una está rota (`finanzas_municipales`, 3 filas) y una es serie nacional, no comunal
(`indicadores`). Quedan ~6-7 capas realmente cruzables a nivel comunal. Para el
investigador socioeconómico faltan los dominios de mayor demanda: pobreza, energía,
seguridad y resultados electorales. **Decisión del operador (2026-06-30):** expandir esos
cuatro dominios. **Esto revierte explícitamente el "no más datasets" del plan original**, y
es consistente con el criterio de prioridad #2 del repo ("valor de cruce con
`codigo_comuna`").

**Principio rector (no negociable).** Se crece **por criterios, no por acumulación**
(`docs/dataset-inclusion-criteria.md`). Toda capa nueva pasa el flujo de 7 pasos de
`AGENTS.md §5`: contrato en `contracts/datasets/`, validación fail-loud, provenance y
semáforo de redistribución. **Las capas frágiles o con datos personales NO entran al bundle
público**; van al carril `candidate` con `review_by`, o se quedan en `needs-research` hasta
resolver el bloqueo. Así la expansión **cumple** la tesis de confiabilidad en vez de
romperla, y acota el costo de mantenimiento del mantenedor único.

**Drift check:** revisar `docs/dataset-ideas/` (estado de cada idea), `docs/dataset-inclusion-criteria.md` y `data/source_registry.json`; confirmar que las URLs/fuentes de CASEN y CNE siguen verificadas antes de codificar.

### Ola B1 — `accepted`, fuente verificada, bajo riesgo → bundle público (sem 2-6, en paralelo con Fases 1-2)

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| B1.1 | Capa **CASEN — pobreza comunal** | El mayor valor de cruce socioeconómico que falta (pobreza × censo × salud × educación) | nuevo `src/extractors/casen_*`, `contracts/datasets/`, `docs/datasets/`, `data/source_registry.json` | M | LOW | Comunas sin estimación CASEN → declarar NULL honesto, no inventar | Cobertura comunal validada o declarada; cruza por `codigo_comuna`; en bundle |
| B1.2 | Capa **consumo eléctrico comunal (CNE)** | Capa limpia, bajo costo, dominio energía | nuevo `src/extractors/cne_*`, contrato, ficha | M | LOW | Cadencia de refresco a confirmar (Excel + API JSON ya verificadas) | Cobertura comunal validada; en bundle; cadencia honesta |

**Gate de salida Ola B1:** ambas capas pasan criterios, tienen contrato + validación +
provenance, están en el bundle (`ready`), y el README/health se regeneran (tarea 1.2) sin
drift. Recién entonces se inicia la Ola B2.

### Ola B2 — `candidate` / `needs-research`, fuera del bundle hasta madurar (sem 7+, tras gate B1 y Fase 3.3)

| # | Tarea | Objetivo | Archivos probables | Esfuerzo | Riesgo | Tradeoff declarado | Criterio de éxito |
|---|-------|----------|--------------------|----------|--------|--------------------|-------------------|
| B2.1 | Capa **delincuencia CEAD** (carril `candidate`) | Alto valor (seguridad) | extractor `candidate`, reutiliza workflow mensual de Fase 3.3 | M-L | **HIGH** | Solo scraping frágil → carril `candidate`, fuera del bundle, `review_by 2026-09-21`, fallback; regla de salida si no madura | Datos validados en `candidate`; **NO** en bundle hasta fuente estable |
| B2.2 | Capa **resultados electorales / autoridades** | Dominio de alta demanda | research primero; luego extractor de agregados | M-L | MED | Separar agregados publicables de datos personales electorales (Ley 19.628) **antes** de codificar | Solo agregados no personales; research cerrada y documentada antes de implementar |

**Gate de salida Ola B2:** cada capa está en el carril que refleja su madurez real
(`candidate` vs `bundle`), con `review_by` y regla de salida; ninguna capa frágil o con
datos personales llegó al bundle público. El conteo de capas sube **por valor de cruce
documentado**, no por acumulación.

**Tradeoff global del Track B (declarado):** más capas = más superficie de mantenimiento
para un mantenedor único (el riesgo que `docs/backlog/NEXT_STEPS.md` ya señaló). Mitigación:
B1 son fuentes estables de bajo costo; B2 queda fuera del bundle (sin promesa de frescura) y
con regla de salida automática. Si el costo de refresco supera el beneficio, una capa se
degrada o archiva — no se mantiene por inercia.

## 8. Decisiones que NO se toman en este plan (y por qué)

- **Agregar datasets SIN pasar los criterios de inclusión** — la expansión (Track B, §7B)
  es ahora co-primaria, pero **gated**: nada entra al bundle público sin contrato,
  validación, provenance y derechos de redistribución. Capas frágiles → `candidate`; datos
  personales → se rechazan. Se crece por criterios, no por acumulación.
- **API hosted / monetización** — descartado con evidencia en
  `docs/backlog/08-evaluacion-producto-comercial.md`.
- **Telemetría _phone-home_ en la librería** — §4.1.
- **Bump a 2.0.0 por sí mismo** — es ruido de versión, no señal.
- **Integración agresiva del ecosistema / CTAs comerciales** — riesgo "folleto".
- **Lanzar el playground antes de la Fase 4** — feature antes de validar utilidad.

## 9. Protocolo de reevaluación (las prioridades pueden cambiar)

Este plan es una **hipótesis con fecha**, no un compromiso rígido. Las prioridades y
el orden **deben** reevaluarse con el paso del tiempo y ante nueva información.

### 9.1 Cadencia de revisión

- **Al cierre de cada fase** (gate): confirmar que el supuesto que justificaba la
  siguiente fase sigue vigente antes de iniciarla.
- **Mensual** (alineado con `docs/backlog/scorecard.md`, revisión semanal existente):
  releer §2 (evidencia) con datos frescos y decidir si la jerarquía cambia.
- **Reevaluación mayor** tras la Fase 4 o ante cualquier disparador "fuerte" (§9.2).

### 9.2 Disparadores que obligan a reordenar (checklist)

Marcar y actuar si ocurre cualquiera:

**Internos**
- [ ] Una fuente se rompe o cambia de términos (revisar `drift_report.json`, CI roja).
- [ ] El scrape de `finanzas` (3.2) tiene éxito → adelantar 3.4 y actualizar narrativa.
- [ ] El scrape de `finanzas` falla definitivamente → cerrar 3.2, no reintentar sin nueva vía.
- [ ] El build supera el objetivo de tiempo → priorizar rendimiento sobre narrativa.
- [ ] Aparece un bug de corrección de datos → P1 inmediato, pausa el plan.

**Externos**
- [ ] La descarga del **bundle** (señal real) sube de forma sostenida → invertir en DX/escala.
- [ ] Llega un contacto inbound cualificado (laboral/colaboración) → priorizar el case study y el funnel.
- [ ] Aparece un proyecto competidor de open-data Chile → reforzar diferenciación (provenance/contratos).
- [ ] Cambia la licencia/ToS de una fuente clave → revisión legal inmediata (Fase 3.1).
- [ ] Un spike de tráfico (LinkedIn/Reddit/HN) → adelantar 4.1/4.2 para capitalizarlo.

### 9.3 Rúbrica para re-rankear (re-aplicar en cada revisión)

Re-puntuar las líneas de trabajo candidatas (1-5, 5 = mejor; Costo/Riesgo: 5 = más
barato/seguro) sobre los mismos criterios del análisis de dirección:

`Reputación técnica · Utilidad pública · Adopción · Demostración ETL/análisis ·
Velocidad · Bajo costo · Defendibilidad · Mantenibilidad · Bajo riesgo · Aprendizaje
medible · Conversión Tooltician`

Regla de decisión: si una línea no priorizada supera a la línea activa por **≥6
puntos de suma total** en dos revisiones consecutivas, **se reordena el plan** y se
deja constancia en el registro (§9.4). Cambios menores no justifican re-planificar
(evitar el costo de cambiar de foco).

### 9.4 Registro de reevaluación (completar en cada revisión)

| Fecha | Fase en curso | Disparador observado | Decisión (mantener / reordenar / pausar) | Cambio de jerarquía | Responsable |
|-------|---------------|----------------------|------------------------------------------|---------------------|-------------|
| 2026-06-30 | — (plan creado) | Análisis de dirección | Mantener: orden 1→2→3→4 | n/a | Carlos |
| 2026-06-30 | — (plan revisado) | Dirección del operador: catálogo demasiado delgado para investigadores que cruzan datos (~6-7 capas temáticas cruzables) | **Reordenar**: añadir Track B (expansión por valor de cruce) co-primario, gated por criterios; cuatro dominios en dos olas por madurez | "Más datasets" pasa de NO-se-hace a **co-primario gated**; B1 (CASEN+CNE) al bundle, B2 (CEAD+electoral) a `candidate`/research | Carlos |
| 2026-06-30 | Fase 1 (gate de salida) | Gate Fase 1 completado: 1.1 relabel finanzas, 1.2 auto-generación README, 1.3 usage_snapshot | Mantener: orden 1→2→3→4 (con Track B en paralelo). Fase 2 inicia cuando el operador lo indique. | n/a | Claude |

## 10. Panel de métricas (todo pasivo, sin feedback)

**Accionables:** descargas del **bundle** (uso real), profundidad de atención en
README/case study (tiempo/scroll), clics a reportes/contratos, interés por
`*.parquet`, referrers nuevos fuera de LinkedIn, 0-drift README↔reportes, CI verde.

**Vanidosas (registrar, no optimizar):** descargas PyPI, stars totales, vistas brutas.

**Qué falta capturar y cómo:** profundidad de atención (analítica web, tarea 2.3);
uso real (descargas del bundle, tarea 1.3). No inventar datos de usuario que hoy no
existen.

## 11. Riesgos del plan y mitigaciones (resumen)

| Riesgo | Fase | Mitigación |
|--------|------|------------|
| Narrativa percibida como "CV disfrazado" | 2 | Anclar cada claim a un artefacto ejecutable; tono de ingeniería |
| Scraping ensucia la limpieza legal del bundle | 3 | Gate legal 3.1; derive-only; no degradar `ready_count` |
| Scraper frágil rompe el build | 3 | Workflow mensual aislado + fallback a snapshot |
| Marcar scrape mensual como "live" (sobreventa) | 3 | Honestidad de cadencia 3.4 |
| Optimizar la métrica vanidosa (PyPI) | todas | Panel separa accionables de vanidosas; KPI = bundle |
| Sobreingeniería del auto-README | 1 | Acotar a un bloque delimitado |
| Distribuir un mensaje débil antes de tener narrativa | 4 | 4.2 bloqueada hasta cerrar Fase 2 |
| Expandir el catálogo sube la superficie de mantenimiento | B (7B) | B1 son fuentes estables de bajo costo; B2 fuera del bundle con regla de salida; degradar/archivar si el costo supera el beneficio |
| Una capa nueva frágil contamina la limpieza del bundle | B2 | CEAD entra solo a `candidate`, nunca al bundle hasta fuente estable |
| Publicar datos personales electorales (Ley 19.628) | B2.2 | Cerrar research primero; solo agregados no personales; es compuerta dura, no negociable |
| Mantenedor único / fatiga | todas | Track A es de bajo mantenimiento; el costo recurrente se concentra en Fase 3 y Ola B2 (mensuales, aislados, con regla de salida) |

## 12. Done criteria del plan maestro

- [ ] Fase 1 cerrada: 0 capas <50% cobertura presentadas como completas; 0 drift README↔reportes; serie de descargas del bundle iniciada.
- [ ] Fase 2 cerrada: sección "Por qué confiar" + case study publicados; analítica web cookieless operativa y declarada.
- [ ] Fase 3 cerrada: `finanzas_municipales` sano **o** honestamente relabelado; workflow mensual aislado; cadencias honestas.
- [ ] Fase 4 cerrada: release notes legibles; ≥1 post técnico; decisión go/no-go del playground registrada.
- [ ] **Ola B1 cerrada:** CASEN y consumo eléctrico CNE en el bundle, con contrato + validación + provenance; README/health regenerados sin drift.
- [ ] **Ola B2 cerrada:** CEAD en carril `candidate` (fuera del bundle, con `review_by`); resultados electorales con research cerrada y solo agregados no personales. Ninguna capa frágil o con datos personales en el bundle público.
- [ ] Registro de reevaluación (§9.4) con al menos una entrada por gate de fase/ola.
- [ ] Fila de `plans/README.md` actualizada en cada cambio de estado.

## 13. STOP conditions

Detente y reporta (no improvises) si:

- La revisión legal (3.1) concluye que una fuente **no** es redistribuible y aun así
  se pretende incluir en el bundle público.
- El scrape (3.2) requeriría eludir mecanismos anti-bot, autenticación o términos
  explícitos de la fuente — eso queda fuera de alcance y se reporta.
- Relabelar `finanzas_municipales` (1.1) implicaría cambios en la API pública o
  romper consumidores existentes (debería ser solo metadata/presentación).
- Cualquier tarea exigiera instrumentar la librería con telemetría que se conecte a
  un servidor (viola §4.1).
- Una capa nueva (Track B) solo fuera obtenible vía scraping que eluda anti-bot/
  autenticación/términos, o contuviera datos personales electorales o sensibles
  (Ley 19.628) — compuerta dura, se rechaza o queda en `needs-research` (B2).

## 14. Maintenance notes

- Este plan **caduca conceptualmente** tras la Fase 4: en ese punto se hace una
  reevaluación mayor y, probablemente, un nuevo plan maestro con la evidencia
  acumulada (descargas del bundle, profundidad de atención, eventuales contactos
  inbound).
- Las tareas L/HIGH (especialmente 3.2 y, si va, 4.3) deben desglosarse en sub-planes
  numerados (023+) estilo `021-*` antes de ejecutarse, con sus propios "Steps",
  "Verify", "Done criteria" y "STOP conditions".
- Mantener la coherencia con `SOURCE_OF_TRUTH.md` y `AGENTS.md`: si este plan
  introduce un extractor scrapeado, documentar la fuente en `DATA_LICENSES.md` y
  seguir el flujo de 7 pasos de `AGENTS.md §5`.
