# Revisión legal de fuentes candidatas — Fase 3

> **Plan 022, Tarea 3.1** · Ejecutado: 2026-06-30 · Revisor: Claude (agente IA)
> **Supervisión humana requerida** para decisión final sobre SINIM (§3).

## Objetivo

Clasificar cada fuente candidata a scraping/sanación según AGENTS.md §6
(redistribuible / derive-only / no usar) **antes de tocar código**, para no
degradar `ready_count: 15` del bundle público.

## Fuentes evaluadas

### 1. SINIM — `finanzas_municipales` ( scraping PoC, tarea 3.2)

| Dimensión | Hallazgo |
|:---|:---|
| **Organismo** | SINIM / SUBDERE — institución pública chilena |
| **URL** | `https://datos.sinim.gov.cl/datos_municipales.php` |
| **Licencia explícita** | CC BY 2.0 CL (badge) + texto: "sin fines comerciales, citar fuente" |
| **Ley 20.285** | Aplica — son datos presupuestarios municipales públicos |
| **robots.txt** | No existe (HTTP 404) — sin directivas de exclusión |
| **Mecanismo anti-bot** | No detectado — es un formulario PHP con sesión, sin CAPTCHA |
| **API pública** | No existe |
| **Datos personales** | No — son agregados presupuestarios por municipio |
| **Acceso actual** | `fetch_url_snapshot()` al HTML de la landing (no extrae datos) |

**Clasificación:** 🟡 `public-api-review-terms` → **REDISTRIBUIBLE CON CONDICIONES.**

**Fundamento:**
1. El organismo emisor (SUBDERE) es público y los datos presupuestarios
   municipales son públicos bajo Ley 20.285.
2. La restricción "sin fines comerciales" es real y debe declararse, pero
   **chile-hub es un proyecto no comercial** (MIT, sin paywall, sin revenue).
3. La redistribución con atribución es compatible con CC BY 2.0 CL.
4. No hay mecanismos anti-bot que eludir (sin robots.txt, sin CAPTCHA). El
   scraping sería de datos públicos accesibles vía formulario.

**Condición obligatoria para el bundle:**
- Actualizar `reuse_policy` para declarar explícitamente la restricción
  "sin fines comerciales" y la atribución requerida a SINIM/SUBDERE.
- Si Tooltician alguna vez comercializa productos derivados, este dataset
  debe excluirse o renegociarse.

**Riesgo residual:** La contradicción entre el badge CC BY 2.0 CL (permite uso
comercial) y el texto del sitio ("sin fines comerciales") crea ambigüedad.
Aplicamos principio conservador (§6): documentar la restricción más
restrictiva. Un operador humano debe validar esta interpretación.

---

### 2. CEAD — delincuencia comunal ( scraping Ola B2.1)

| Dimensión | Hallazgo |
|:---|:---|
| **Organismo** | SPD — Subsecretaría de Prevención del Delito (Ministerio del Interior) |
| **URL** | `https://cead.minsegpublica.gob.cl/estadisticas-delictuales/` |
| **Licencia explícita** | No encontrada en el portal |
| **ToS / restricciones** | No encontradas. Solo "Política de seguridad de la información" (PDF) |
| **API pública** | No existe |
| **Descarga estructurada** | No existe — solo consulta interactiva con filtros |
| **Datos personales** | No — son casos agregados por comuna, mes y tipo de delito |
| **Scraping previo** | Existe scraper público en R por @bastianolea (`delincuencia_chile`) funcionando desde ~2023 sin incidentes legales conocidos |
| **Fragilidad** | ALTA — el portal ya se rompió en 2024 (cambio de sitio) y 2025 (ciberataque/cambio de ministerio) |

**Clasificación:** 🟡 `public-api-review-terms` → **DERIVE-ONLY / CANDIDATE.**

**Fundamento:**
1. Institución pública chilena. Datos de seguridad pública agregados.
2. Sin licencia explícita, pero son datos públicos no personales.
3. Sin restricciones de scraping visibles en el portal.
4. La fragilidad técnica y la falta de fuente estructurada lo relegan a
   `candidate` (fuera del bundle público), que es el consenso del plan.

**Condición para el carril `candidate`:**
- Mantener `review_by: 2026-09-21` y `stalled_after_days: 90`.
- Si no aparece fuente estructurada para `review_by`, degradar a `rejected`.
- **Nunca al bundle público** sin fuente estable y licencia clara.

---

### 3. Resultados electorales / autoridades / partidos ( investigación Ola B2.2)

| Dimensión | Hallazgo |
|:---|:---|
| **Fuentes** | SERVEL, TRICEL, BCN, Cámara de Diputados, Senado |
| **Licencia** | BCN: CC BY · Cámara/Senado: datos abiertos · SERVEL: resultados públicos pero padrón RESTRINGIDO · TRICEL: públicos oficiales |
| **Ley 19.628** | **No aplica a resultados agregados.** Sí aplica a: padrón, RUN, domicilio, afiliación partidaria individual |
| **Datos personales** | **Resultados electorales agregados por mesa/comuna: NO.** Padrón/Afiliación: SÍ — **PROHIBIDO** |
| **Formatos** | Heterogéneos: XLS, XLSX, HTML, XML, PDF. Multi-elección, multi-formato. |

**Clasificación diferenciada por subcapa:**

| Subcapa | Clasificación | Fundamento |
|:---|:---|:---|
| `resultados_electorales` (agregados por comuna/mesa) | 🟢 `open-attribution` | Datos públicos oficiales. SERVEL/TRICEL publican resultados como información pública no personal. BCN los republica bajo CC BY. |
| `autoridades_electas` | 🟢 `open-attribution` | Cargos públicos — información pública por definición. Fuentes: BCN, Cámara, Senado. |
| `partidos_politicos` | 🟢 `open-attribution` | Registro público del SERVEL. Datos institucionales, no personales. |
| `padron_electoral` | 🔴 `restricted` | **PROHIBIDO.** Ley 19.628. Datos personales de electores. |
| `afiliacion_partidaria` | 🔴 `restricted` | **PROHIBIDO.** Dato personal sensible. |

**Conclusión:** 🟢 **Los agregados electorales son redistribuibles.**
La línea roja del plan (solo agregados, nunca datos personales) es
jurídicamente sólida bajo Ley 19.628. El riesgo está en la ejecución
(normalización multi-fuente), no en lo legal.

**Condición para B2.2:**
- Cerrar research antes de codificar (ya requerido por el plan).
- Cada extractor debe validar que solo procesa agregados, nunca datos
  personales. Implementar un check explícito de columnas prohibidas
  (RUN, nombres individuales, domicilio, mesa-asociada-a-persona).

---

## Tabla resumen

| Fuente | Dataset | Clasificación | Bundle público | Carril | Acción inmediata |
|:---|:---|:---|:---|:---|:---|
| SINIM | `finanzas_municipales` | 🟡 redistribuible con condiciones | Sí (con restricción NC documentada) | `stable_publishable` (si 3.2 funciona) | Proceder con PoC 3.2 |
| CEAD | `delincuencia_comunal` | 🟡 derive-only / candidate | **NO** | `candidate` | Mantener en research; solo proceder si 3.2 establece infraestructura de scraping |
| SERVEL/BCN/TRICEL | `resultados_electorales` | 🟢 open-attribution | Sí (solo agregados) | `needs-research` → `stable_publishable` | Cerrar research B2.2 antes de codificar |
| SERVEL/BCN | `autoridades_electas` | 🟢 open-attribution | Sí | `needs-research` | Ídem |
| SERVEL | `partidos_politicos` | 🟢 open-attribution | Sí | `needs-research` | Ídem |

## Efecto sobre `ready_count`

- **SINIM:** Ya está en `ready_count: 15` con `publishability_status: ready`.
  La restricción NC no cambia su elegibilidad; solo requiere documentar la
  condición. `ready_count` se mantiene en 15.
- **CEAD:** No entra al bundle → no afecta `ready_count`.
- **Electoral:** Los agregados son `open-attribution` → sumarían a
  `ready_count` si se publican. Pero están en `needs-research`, no en el
  horizonte inmediato.

## Riesgos identificados

1. **Contradicción CC BY 2.0 CL vs "sin fines comerciales" en SINIM:**
   El badge CC BY 2.0 CL permite uso comercial; el texto del sitio lo
   prohíbe. Aplicamos el principio conservador (el texto manda) y
   recomendamos validación humana. Si un operador concluye que la
   restricción NC es bloqueante, `finanzas_municipales` debe salir del
   bundle público y quedarse en `candidate`.

2. **Falta de licencia explícita en CEAD:** sin licencia clara, mantenemos
   `candidate` y fuera del bundle. Esto ya es la postura del plan.

3. **Riesgo de contaminación electoral:** la línea entre "agregado
   electoral" y "dato personal" puede ser fina en elecciones pequeñas
   (mesas con pocos votantes). Implementar umbral de privacidad: no
   publicar resultados con n < 5 votantes por celda.

## STOP conditions verificadas

- [x] Ninguna fuente clasificada `restricted` se propone para el bundle.
- [x] Los datos personales electorales (Ley 19.628) quedan explícitamente fuera.
- [x] `ready_count: 15` no se degrada.
- [x] Las fuentes con scraping frágil (CEAD) van a `candidate`, no al bundle.
