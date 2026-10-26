# GitHub Secure Open Source Fund — dossier de evidencia (adopción e impacto)

> **Qué es.** Evidencia pública, fechada y reproducible sobre comunidad, adopción
> e impacto de seguridad de chile-hub, para decidir si existe base real para
> postular al GitHub Secure Open Source Fund.
>
> **Qué no es.** No es una postulación. No se envió nada, no se abrió cuenta, no
> se completó formulario.
>
> **Regla.** Cada cifra lleva fuente, fecha de consulta y límite de lectura. Las
> frases sobre descargas siguen literalmente [`docs/adoption-funnel.md`](../adoption-funnel.md);
> las descargas de PyPI **nunca** se presentan como "instalaciones", "usuarios"
> ni "audiencia" ([`AGENTS.md` §10](../../AGENTS.md)).

- **Consulta:** 2026-10-25 (America/Santiago).
- **Base:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`, árbol limpio.
- **Ventana de comparación:** revisión previa del 2026-10-15
  ([`docs/adoption-review.md`](../adoption-review.md#2026-10-15--revisión-plan-144-método-anexo-m)).

## 1. Dependencia real (lo único que cuenta como adopción)

| Señal | Valor al 2026-10-25 | Fuente | Límite de lectura |
|:--|:--|:--|:--|
| Repositorios dependientes en GitHub | **0** ("We haven't found any dependents for this repository yet") | https://github.com/cortega26/chile-hub/network/dependents | Página oficial de GitHub. Un `0` puede excluir repos privados; no se corrige al alza sin evidencia |
| Dependientes en deps.dev | **0** (`dependentCount: 0`, `directDependentCount: 0`, `indirectDependentCount: 0`) | `https://api.deps.dev/v3alpha/systems/pypi/packages/chile-hub/versions/1.51.0:dependents` | Solo versión 1.51.0; coincide con el `0` de GitHub |
| Issues abiertos por terceros (histórico) | **0** (15 issues en total; el único ajeno al mantenedor lo abrió `github-actions[bot]`, #195) | `gh api repos/cortega26/chile-hub/issues?state=all` | Los issues #107–#109 los abrió el mantenedor a partir de comentarios de LinkedIn |
| Pull requests de terceros (histórico) | **1** (#9, `KrlitosForever`, 2026-06-21, fusionado) | `gh api repos/cortega26/chile-hub/pulls?state=all` | Es el único aporte externo de código en toda la vida del repo |
| Organizaciones con uso verificable (rúbrica U1–U3) | **0 al 2026-10-15**, sin novedad al 2026-10-25 | Issue #184; Auditoría 3 §E | El tracker es privado (Ley 21.719); aquí solo se reporta el conteo |
| Citaciones downstream del DOI | Sin dato nuevo | — | Última lectura: 0 citas al 2026-09-29. No se releyó hoy: se reporta como `sin dato`, no como cero |

**Lectura.** No existe hoy una dependencia observable. Un `0` en dependents no
significa que nadie use el proyecto; significa que **no se puede demostrar** que
alguien dependa de él, que es lo que el programa pide.

## 2. Señales contextuales (se registran; no son adopción)

### 2.1 PyPI — mide cadencia de publicación, no uso

- **Frase permitida, con fecha:** "Al 2026-10-25, chile-hub suma 6.372 descargas
  en PyPI en los últimos 30 días (2026-09-25 → 2026-10-24) con 51 releases en el
  período (≈125 por release): mide cadencia de publicación, no usuarios."
- **Fuente:** `pypistats /overall?mirrors=false` + `pypi.org/pypi/chile-hub/json`.
- **Reproducible:** [`Anexo M`](auditoria-3-2026-09-29.md#anexo-m-método-reproducible).
- **Regresión propia, ejecutada hoy (2026-10-25), n=127 días:**

  | Régimen | n | Descargas por release | R² |
  |:--|--:|--:|--:|
  | Serie completa 2026-06-16 → 2026-10-24 | 127 | 87,7 | 0,933 |
  | Antes del cambio de conteo de PyPI (2026-08-24) | 65 | 104,2 | 0,955 |
  | Después del cambio de conteo | 62 | 79,3 | 0,946 |

  Días sin release: 94, media 40,4 descargas/día. Días con al menos un release:
  33, media 416,2 descargas/día. **Conclusión:** la serie la explica la cadencia
  de publicación, no una base de usuarios.
- **Contraste con la revisión del 2026-10-15:** entonces se reportaron ≈109
  descargas por release; hoy ≈125. El nivel total bajó (6.638 → 6.372), pero el
  número de releases también bajó. Coherente con la misma explicación.
- **Límite:** el 87% de las descargas no reporta SO ni versión de Python
  (Auditoría 3 §0.3); parte es CI y mirrors no filtrados.

### 2.2 Bundle publicable — el mejor proxy de activación

- **Frase permitida, con fecha:** "Al 2026-10-25, el bundle publicable acumula
  **189** descargas en GitHub Releases (**69** releases con el asset), frente a
  169 y 80 releases el 2026-10-15."
- **Fuente:** `gh api --paginate 'repos/cortega26/chile-hub/releases?per_page=100'`,
  134 releases en total; 113 descargas acumuladas del asset `.sha256`.
- **Discrepancia honesta:** el número de releases con el asset **bajó** de 80 a 69
  en diez días, señal de limpieza de releases antiguos. Por eso el delta
  (189 − 169 = **+20**) está **subestimado** y no se presenta como tasa mensual.
- **Límite:** no se puede atribuir a personas ni a organizaciones; GitHub cuenta
  descargas de assets, incluidas las de CI.

### 2.3 Hugging Face

- **Frase permitida, con fecha:** "Al 2026-10-25, el espejo de Hugging Face
  registra 314 descargas y 0 likes."
- **Fuente:** `https://huggingface.co/api/datasets/cortega26/chile-hub`
  (`lastModified: 2026-10-13`).
- **Límite:** ventana móvil, no acumulado; HF cuenta re-descargas y CI. La cifra
  bajó frente a las 444 del 2026-10-15 porque la ventana se movió, no porque el
  uso haya caído necesariamente.

### 2.4 Interés y visibilidad

| Señal | 2026-10-25 | 2026-10-15 | Fuente |
|:--|--:|--:|:--|
| Stars | 134 | 129 | `gh api repos/cortega26/chile-hub` |
| Forks | 12 | 12 | idem |
| Sponsors | 0 | 0 | GraphQL `sponsors.totalCount` |
| Supporters públicos BMC | sin dato hoy | 0 al 2026-09-29 | Auditoría 3 §0.1 |

- **Tráfico del repositorio (solo mantenedor, no citable en material externo):**
  540 vistas / 333 únicos en 14 días. De esos 333 únicos, **184 (55%) se
  concentraron el 2026-10-15**; fuera de ese pico el rango es 1–45 únicos/día.
  Referrers dominantes: `linkedin.com` (201) y `com.linkedin.android` (79).
- **Lectura:** la visibilidad sigue el patrón de una red profesional personal, no
  de un canal de descubrimiento sostenido. Es exactamente lo que la Auditoría 3
  llamó "audiencia de lanzamiento".

### 2.5 Estado operativo (afecta a cualquier afirmación de impacto)

- **Hecho verificado:** la publicación programada lleva **10 ejecuciones
  consecutivas fallidas** (2026-10-16 → 2026-10-25). El último snapshot publicado
  es `data/normalized/pipeline_metadata.json`, generado el **2026-10-15**
  (commit `bd77d34`).
- **Causa registrada en el log del run 40200343251:** 5 datasets en
  `source_mode=fallback` sobre carril `stable_publishable` (política de
  publicación los rechaza) y dos caídas de `record_count` sobre el umbral del 20%
  (`autoridades_electas` 205 → 155; `resultados_educacionales` 345 → 3).
- **Fuente:** `gh run list --workflow=pipeline-check.yml --event=schedule`;
  logs del job "Build and verify data"; issue #195.
- **Consecuencia para el dossier:** el proyecto se describe como "actualización
  diaria". Hoy esa frase es **falsa** y no debe usarse en material externo. Es
  también la evidencia más concreta de riesgo de continuidad (bus factor) del
  proyecto.

## 3. Impacto de seguridad: qué protege realmente chile-hub

El programa financia **seguridad**, no datasets. La pregunta correcta no es
"¿tenemos CodeQL?" sino "¿quién queda más seguro si este proyecto se rompe?".

### 3.1 Superficie de ataque real

| Superficie | Qué puede salir mal | Control existente hoy | Estado |
|:--|:--|:--|:--|
| Publicación de datos oficiales | Un fallback silencioso o un dato stale se publica como si fuera output de la fuente, y un consumidor toma decisiones con él | `verify_pipeline.py --profile publication` rechaza `source_mode=fallback`, datos stale y caídas de `record_count` >20% | **Activo y funcionando**: es la causa de que el publish lleve 10 días bloqueado |
| Distribución del bundle (ZIP) | Reemplazo del ZIP y de su `.sha256` de forma consistente: la verificación seguiría pasando | Checksum SHA-256 + `artifact_manifest.json` por release | **Parcial**: el checksum detecta corrupción, no compromiso de la release. No hay firma ni atestación del asset |
| Paquete PyPI | Sustitución del artefacto publicado | Trusted publishing OIDC + **atestación de publicación verificada** (`/integrity/.../provenance` responde 200, publisher `GitHub`, workflow `pypi-release.yml`) | **Completo** |
| Contratos de datos | Cambio de esquema silencioso que rompe consumidores | `contracts/datasets/*.schema.json` + gate de coherencia | **Completo** |
| Cadena de build | Ejecución de código de un PR de fork con token de escritura | Sin `pull_request_target` ni `issue_comment`; 21 bloques `permissions`; acciones fijadas por SHA (57/57 de GitHub, 18/18 de terceros) | **Completo** |
| Revisión de cambios | Código sin revisión entra a `main` | Rama lineal, sin force-push, sin borrado, conversación resuelta | **Parcial**: sin revisiones requeridas ni status checks obligatorios; `enforce_admins` desactivado |

### 3.2 Quién queda más seguro, en concreto

1. **Un investigador que cita una cifra comunal.** Hoy puede afirmar que el
   número publicado proviene de la corrida validada de la fuente, porque el
   pipeline **se niega a publicar** un fallback (evidencia: lleva 10 días
   negándose). Esa garantía es el valor de seguridad del proyecto, y es
   verificable en los logs.
2. **Un consumidor del paquete PyPI.** Puede verificar que el artefacto salió del
   workflow de este repositorio, vía atestación de PyPI.
3. **Un consumidor del bundle ZIP.** Puede verificar integridad, pero **no
   procedencia**: si la release se compromete, nada lo delata. Es la brecha
   material del proyecto.

### 3.3 Calibración contra proyectos ya seleccionados

La página oficial declara **188 proyectos financiados**, entre ellos AutoGPT,
CPython, Log4j, Ollama, pandas, SciPy, Bootstrap, curl y OpenCV. Sí hay proyectos
cívicos y de datos (`AirQo`, `Proyecto Respira`, `OpenBB Platform`), lo que
descarta que "datos públicos" sea descalificante por sí mismo.

> **No se convierte esto en un umbral numérico.** No hay una cifra pública de
> "dependents mínimos". Lo que el conjunto publicado muestra es un patrón:
> infraestructura fundacional o plataforma con usuarios demostrables. Se registra
> como contexto, no como regla inventada.

**Fuente:** https://github.com/open-source/github-secure-open-source-fund/projects
(lista completa desplegada y leída el 2026-10-25).

## 4. Qué se puede afirmar y qué no

| Afirmación | ¿Usable en material externo? | Condición |
|:--|:--|:--|
| "134 stars, 12 forks" | Sí | Con fecha. No implica uso |
| "6.372 descargas en PyPI en 30 días" | Sí | Solo como descargas, con la frase del §2.1 |
| "189 descargas acumuladas del bundle" | Sí | Con la salvedad de limpieza de releases |
| "314 descargas y 0 likes en Hugging Face" | Sí | Ventana móvil, con fecha |
| "Actualización diaria de datos" | **No** | Falso al 2026-10-25: 10 días sin publicar |
| "Usado por organizaciones" | **No** | 0 verificables con rúbrica U1–U3 |
| "Miles de usuarios" / "instalaciones" | **No** | Prohibido por `AGENTS.md` §10 |
| "Dependientes en el ecosistema" | **No** | 0 en GitHub y 0 en deps.dev |
| "Cobertura en 346 comunas, 1.449 pruebas automatizadas y 26 contratos de esquema" | Sí | Es calidad y alcance, no adopción |

## 5. Veredicto de este dossier

- **Adopción demostrable: FAIL.** Cero dependientes en dos fuentes
  independientes, cero issues de terceros en cuatro meses, un solo PR externo.
- **Impacto de seguridad: REAL pero ACOTADO.** El control que impide publicar
  datos degradados es genuino y hoy está en uso activo (bloqueando el publish).
  La procedencia del bundle, en cambio, no está cubierta.
- **Riesgo de continuidad: DEMOSTRADO.** Diez días de publicación detenida es la
  mejor prueba de que el proyecto depende de una sola persona.

Con esto, el requisito "demonstrated community traction and adoption" no se
cumple. El dictamen y sus condiciones están en
[`github-secure-oss-fund-eligibilidad.md`](github-secure-oss-fund-eligibilidad.md).
