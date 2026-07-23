# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commits `ba2f434` (2026-06-13), `a2cd288` (2026-06-19) y `c486e7c` (2026-07-07), y por `/improve plan` (mejoras de librerías/dependencias) en commit `140c8ea` (2026-06-29).

> **Auditoría `/improve next` — dirección/roadmap (2026-07-14, commit `7ebf94b`)**: planes
> **050–052**. Foco exclusivo en la categoría *dirección* (hacia dónde llevar el proyecto),
> no en bugs. Contexto: repo muy maduro — la lista "deseable post-MVP" del `product-spec`
> ya está casi entera entregada (`search_datasets`, `cross_view`, `sql`, `from_datapackage`,
> `validate_user_data`, dashboard, playground), y el anti-patrón #10 prohíbe sumar datasets
> antes de validar adopción. Por eso los hallazgos **no** son "más features ni más datasets"
> sino cerrar 3 asimetrías de superficie ya insinuadas por la arquitectura: un resolutor
> público de nombres→CUT (**050**, el más grounded, ataca el criterio de éxito #4 del
> product-spec), documentar+cosechar la capa HTTP estática que ya se sirve y consume
> (**051**, absorbe el fix de `from_datapackage(url)`), y una señal de adopción PyPI/Releases
> que desbloquea el anti-patrón #10 (**052**). Los 3 seleccionados por el usuario. Ver
> "Hallazgos considerados y diferidos (2026-07-14 — dirección)" para lo excluido.

> **Decisión de producto — construir capacidad por delante de la demanda (2026-07-14)**:
> el mantenedor autorizó explícitamente desafiar el anti-patrón #10 con "a veces hay que
> crear la oferta para generar la demanda". **Principio arquitectónico que la
> reconcilia con la tesis del proyecto** ("menos datasets, más limpios"): la excepción
> aplica a **profundidad de capacidad y distribución sobre fuentes existentes de alta
> calidad** (geometría, capa HTTP/DCAT, resolución de entidades) — que *generan* demanda
> —, **NO** a amplitud de datasets sobre fuentes frágiles (scraping HTML), que sigue
> gated por adopción. Fruto de esta decisión: planes **053** (geometría comunal
> GeoParquet + `resolve_by_coords()` reverse geocoding — el *flagship* generador de
> demanda) y **054** (validación de anomalías temporales — foso de confianza que respalda
> la apuesta). La decisión debe ratificarse en **ADR-011** (el Plan 053 lo escribe como
> Step 0; requiere aprobación humana `proposed`→`accepted`). El Plan 052 (señal de
> adopción) pasa de "desbloquear crecimiento" a **medir la demanda que esta oferta
> genere**.

> **Auditoría `/improve next` — dirección/roadmap (2026-07-18, commit `6bf6b08`)**: planes
> **058–063**. Segunda auditoría de dirección sobre el mismo estado estratégico (decisión
> construir-por-delante-de-demanda del 2026-07-14; drift desde la última: 2 commits
> docs-only). El foco ya no es "qué construir de capacidad" (050–054) ni diseño de landing
> (055–057) sino **los canales que esa capacidad no cubre**: distribución por
> descubrimiento (**059**, Hugging Face — complemento de 051, que es capa de acceso, no de
> descubrimiento), cierre del último hueco anti-drift que `AGENTS.md §12` nombra explícito
> (**058**, campo `extractor` en el catálogo + tabla README auto-generada), demostración de
> la tesis de cruce (**060**, notebook flagship), expansión barata de audiencia (**061**,
> quickstart R), conversión de la gobernanza existente en embudo de contribuciones
> (**062**, playbook de extractores — el issue template `dataset_request.yml` **ya existe**,
> verificado en recon, por eso el plan es solo el lado código) y profundidad del dashboard
> de salud (**063**, historial JSONL + sparkline; secuencia después de 054). Los 6
> seleccionados por el usuario de 6 presentados. Ver "Hallazgos considerados y diferidos
> (2026-07-18 — dirección)" para lo excluido (Kaggle, conda-forge, docs en inglés,
> Release 2.0.0 forzado).

> **Última auditoría `/improve deep` (2026-07-07, commit `c486e7c`)**: planes **024–041**.
> Repo maduro; los grandes ítems previos ya están hechos. Lo restante es una cola de
> defectos pequeños de alta confianza (024–031; 027–031 DONE ✅), higiene de deps/CI (032, 033, 034 DONE ✅), backfill
> de tests del gate de publicación (035 DONE ✅) y los writers (036 DONE ✅), dos refactors (037–038 DONE ✅) y
> tres planes de diseño (039 DONE ✅, 040 DONE ✅, 041 DONE ✅). Ver "Hallazgos considerados y diferidos (2026-07-07)".

> **Reevaluación de vigencia (2026-07-09)**: entre `c486e7c` y `HEAD` (`c1aa3e9`) hubo 45 commits,
> la mayoría fixes reactivos a bugs reales encontrados persiguiendo Pipeline Check #270 (cadena
> `4ebca99`…`354ad6e`, más `3f968ab`/`57e6eaf`/`9b85a23`/`df0999e`), no ejecuciones deliberadas de
> estos planes. Se revisó cada plan activo con su propio "drift check" contra `c486e7c`. Resultado:
> **034 quedó DONE de rebote** (el fix reactivo `4ebca99` corrigió exactamente el `--group dev` →
> `--extra pipeline --extra dev` que el plan pedía) y se archivó. **039 quedó DONE** (ADR-006 escrito y
> committeado). **Todos los demás
> planes activos (027–033, 035–038, 040 DONE ✅, 041 DONE ✅) siguen 100% vigentes** — se verificó línea por línea que
> el defecto descrito sigue presente en el código actual; en dos casos la evidencia es ahora más
> fuerte que en la auditoría original (ver notas en 027 y 038 abajo). Detalle completo de la
> reevaluación al final de este archivo, sección "Reevaluación 2026-07-09".

> ## Rutina obligatoria tras cada iteración / actualización / cambio
>
> Al cerrar **cualquier** iteración de trabajo sobre un plan (una tarea, una fase, una ola o el
> plan completo), ejecuta estos pasos **en orden** antes de dar el trabajo por terminado. No los
> dejes "para después": el índice y el backlog deben reflejar siempre el estado real.
>
> 1. **Actualiza la fila de estado** del plan en la tabla "Planes activos" de este archivo
>    (`TODO` → `IN PROGRESS` → `DONE`; para planes maestros multi-fase usa un estado granular,
>    p. ej. `🔶 Fase 1 ✓ (fecha)`).
> 2. **Actualiza el backlog y el scorecard** si existen y el cambio los toca:
>    `docs/backlog/scorecard.md` (métricas de avance y revisión semanal),
>    `docs/backlog/NEXT_STEPS.md` y la ficha de backlog correspondiente en `docs/backlog/`.
>    Si el plan tiene su propio registro interno (p. ej. el "registro de reevaluación" del Plan
>    022, §9.4), añade también ahí la entrada de la iteración.
> 3. **Archiva el trabajo terminado.** Cuando un plan pasa a `DONE`, mueve automáticamente su
>    fichero `.md` a `archive/` **de inmediato** y borra su fila de la tabla de activos — no lo
>    dejes en la tabla activa ni en `plans/` raíz. Si merece mención, añádelo a la sección
>    "Planes archivados" correspondiente. Para un **plan maestro multi-fase**, no lo archives
>    hasta que **todas** sus fases/olas estén `DONE`; mientras tanto, mantén su fila activa con
>    el estado granular del paso 1.
> 4. **Verifica coherencia**: el grafo de dependencias y el "Orden de ejecución recomendado" de
>    abajo deben seguir siendo válidos tras el cambio; ajústalos si una dependencia se resolvió o
>    cambió de prioridad.

> **Auditoría `/improve` UX/UI, contenido, layout, estilo, espaciado y tipografía
> (2026-07-13, commit `901f5b9`)**: planes **043–049**, enfocados exclusivamente en la
> landing page (`index.html`, `app.js`, `playground.js`, `privacy.html` — el único
> frontend del repo). Todos los hallazgos se verificaron empíricamente con Playwright
> (estilos computados + capturas de pantalla contra el sitio servido en local), no sólo
> por lectura de código. Se confirmó con `src/builders/landing.py` que estos 4 archivos
> son fuente editable directamente (el builder sólo parchea el bloque JSON-LD y dos
> constantes de versión, nada más — no hay generación de la que preocuparse). Ver
> "Hallazgos considerados y diferidos (2026-07-13)" para lo que quedó fuera de alcance
> a propósito (vocabulario del dashboard de salud, `freshness.status`, la línea
> "Warnings: N" del drawer verificada por `scripts/verify_landing.py`).
>
> **Batch 043–049 completo (2026-07-14)**: los 7 planes quedaron `DONE`, revisados
> independientemente por el advisor (no sólo por el executor) y mergeados a `main` en
> commits separados por plan; se archivaron juntos el mismo día. Ver la sección
> "Planes archivados (auditoría UX/UI 2026-07-13)" para el detalle de cada uno.

## Planes activos

| # | Plan | Prioridad | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|----------|--------|-----------|--------|
| 050 | [Resolutor público `resolve_comunas()` (nombres → CUT)](050-resolve-comunas-name-to-cut.md) | P2 | M | LOW-MED | — | TODO — spike con entregable de código: resolutor determinista + `ADR-009`; fuzzy queda como pregunta abierta. |
| 051 | [Capa de acceso HTTP estática + catálogo DCAT `data.json`](051-static-http-access-and-dcat-catalog.md) | P2 | M | LOW | — | TODO — spike: contrato + `ADR-010` + prototipo generador DCAT + fix `from_datapackage(url)` + docs. Sólo archivos estáticos, sin servidor. |
| 053 | [Geometría comunal (GeoParquet) + `resolve_by_coords()` reverse geocoding](053-comuna-geometry-and-reverse-geocoding.md) | **P1** | L | MED | — (complementa 050) | TODO — **flagship** de la estrategia construir-por-delante-de-demanda. Feasibility-spike: Step 0 escribe ADR-011 (estrategia); Step 1 es un **gate de licencia que puede matar el plan**. Entregable primario = artefacto GeoParquet (dep-cero); `resolve_by_coords()` tras extra `[geo]`. Geometría **nunca** como columna de `comunas`. |
| 054 | [Validación de anomalías temporales sobre series numéricas](054-temporal-anomaly-validation-numeric-series.md) | P2 | M | MED | — | TODO — foso de confianza (no generador de demanda; respalda 053). Anomalía = warning + flag de drift + gate de publicación override-able, **nunca** `SystemExit` del build. Alcance inicial: `indicadores`. |
| 055 | [Overhaul tipográfico: legibilidad profesional de datos](055-typography-and-readability-overhaul.md) | **P1** | M | LOW | — | DONE — Source Serif 4, Inter, and JetBrains Mono integrated in `index.html`; Google Fonts link updated; verified with `make verify-landing` and CI checks; commit in `advisor/055-typography-overhaul`. |
| 056 | [Ritmo visual, espaciado y jerarquía de secciones](056-visual-rhythm-spacing-hierarchy.md) | P2 | M | LOW | 055 | TODO — sticky header + 3 tiers de espaciado + separadores visuales. Depende de 055 (métricas de fuente). |
| 057 | [Skeleton loading states + polish de interacción](057-loading-skeletons-and-interaction-polish.md) | P2 | M | LOW | — (055 recomendado) | TODO — skeletons para catálogo y KPIs, empty state de búsqueda, tarjetas clickeables, tecla Escape en drawer. |
| 058 | [Campo `extractor` en el catálogo + tabla de extractores auto-generada en README](058-catalogo-campo-extractor-y-tabla-readme.md) | P2 | M | LOW | — | TODO — cierra el hueco que `AGENTS.md §12` nombra explícito: campo `extractor` en las 21 entradas + validación en `check_companion_paths registry` + `sync_readme_extractor_table()`. Disjunto de 050–057. |
| 059 | [Publicación del bundle en Hugging Face Hub](059-publicacion-huggingface-hub.md) | P2 | M | MED | — (052 recomendado antes, no gate) | TODO — canal de *descubrimiento* (complementa 051 = capa de acceso). Script `--dry-run` + job `hf-publish` en `pypi-release.yml` + dataset card. Requiere secret `HF_TOKEN` (paso manual del mantenedor). Carril `candidate` excluido por construcción. |
| 060 | [Notebook flagship — cruce multi-capa por `codigo_comuna`](060-notebook-flagship-cruce-capas.md) | P2 | S | LOW | — | DONE — `examples/notebooks/04_perfil_territorial_pobreza.ipynb` created and verified to run successfully on Python 3 with clean outputs; joins `perfil_territorial_comunal`, `pobreza_comunal`, and `resultados_educacionales`; commit in `advisor/060-flagship-notebook`. |
| 061 | [Quickstart de consumo desde R (arrow + duckdb)](061-quickstart-r.md) | P3 | S | LOW | — | DONE — `docs/r-quickstart.md` created, nav entry added, `docs/installation.md` updated, checked with `make doctor` and `make docs-build`. |
| 062 | [Playbook de contribución de extractores](062-playbook-contribucion-extractores.md) | P3 | S | LOW | — | DONE — sección `## Contribuir un extractor (dataset nuevo)` añadida a `CONTRIBUTING.md`; checklist 8-pasos + encuadre + nota de expectativa; `make doctor` exit 0; commit `928cec1` en `advisor/062-extractor-contribution-playbook`. |
| 063 | [Historial de salud del hub + sparkline en landing](063-historial-salud-hub.md) | P3 | M | MED | — (054 recomendado antes) | TODO — `hub_health_history.jsonl` append-only (cap 400, idempotente por timestamp) + sparkline SVG en el dashboard. Primer artefacto acumulativo del pipeline — Step 1 verifica la premisa de persistencia con un probe. |

## Planes archivados (2026-07-23)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 052 | [Señal de adopción PyPI + GitHub Releases (badge/artefacto)](archive/052-adoption-signal-pypi-release-stats.md) | S | LOW | DONE — `scripts/fetch_adoption_stats.py` (stdlib-only: `urllib.request`/`json`/`argparse`) lee pypistats.org + suma de `download_count` de assets en GitHub Releases, con degradación con gracia (None/0, nunca aborta) y modo `--offline` para tests reproducibles; publica `data/normalized/adoption.json` + `adoption_badge.json` (contrato shields) siguiendo el patrón de `generate_coverage_badge.py`. `.github/workflows/adoption-stats.yml` (cron semanal lunes 04:00 UTC + `workflow_dispatch`) modelado sobre `monthly-scrape.yml`: `permissions: contents: write`, commit tolerante a "sin cambios" con `[skip ci]`. Badge "Instalaciones" agregado al README junto a Coverage/Data, fuera de bloques delimitados. 8 tests nuevos sin red (`AdoptionStatsTests`) cubren parseo happy-path, degradación de cada fuente y contrato shields del badge — 158/158 tests pasan, `make lint` y `make format-check` OK, cero cambios en `src/chile_hub/**`. Ejecutado en worktree `agent-ac4a2d3c99742948f`, branch `advisor/052-adoption-stats`, commit `91a8b09`. |

## Planes archivados (2026-07-10)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 020 | [Explorador SQL en la landing con DuckDB-Wasm](archive/020-duckdb-wasm-playground.md) | M | MED | DONE — implementado 2026-07-10, archivado 2026-07-18. 5 archivos DuckDB-Wasm + apache-arrow/flatbuffers/tslib vendorizados, CSP con `wasm-unsafe-eval`, `playground.js` con lazy init, smoke test pasa con presencia confirmada, funcional manual 10 filas ✅. |

## Planes archivados (auditoría UX/UI 2026-07-13)

Los 7 planes de esta auditoría (043–049) quedaron `DONE` y se archivaron juntos como
batch el 2026-07-14, una vez confirmado que los 7 estaban mergeados en `main`.

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 043 | [Scroll horizontal en resultados del Explorador SQL](archive/043-sql-explorer-result-overflow.md) | S | LOW | DONE — `.sql-result-wrap`/`.sql-result-table`/`.sql-result-empty` agregadas a `index.html`; `renderResult` en `playground.js` envuelve la tabla; verificado con Playwright (wrap con `overflow-x: auto`, `scrollLeft` responde, `body.scrollWidth` ya no se desborda con tabla de 42 columnas); `make verify-landing` OK. |
| 044 | [Estilizar `.dataset-tag` (pills "key:"/"warnings")](archive/044-style-dataset-tag-pills.md) | S | LOW | DONE — opción (A) implementada: reglas `.dataset-tag`/`.dataset-tag.key-tag`/`.dataset-tag.warning` agregadas a `index.html` (reutilizan tokens de `.dataset-badge`); verificado con Playwright (background/padding/border-radius ya no en cero, font-size 10.88px vs 16px original, capturas desktop+móvil OK); `make verify-landing` exit 0. Ejecutado en worktree `worktree-agent-afe5a6a7768f37423`, commit `a965e8e`. |
| 045 | [Color del badge `.dataset-badge.monthly`](archive/045-dataset-badge-monthly-color.md) | S | LOW | DONE — regla `.dataset-badge.monthly` (`background: #e0e7ff`, `color: #3730a3`) agregada al bloque `.dataset-badge` de línea ~2408-2426 (el que aplica por cascada al ser el último en el documento; el bloque duplicado de línea ~914 quedó intencionalmente fuera de alcance, cubierto por el plan 048); verificado con Playwright (`background-color` computado `rgb(224, 231, 255)`, `color` `rgb(55, 48, 163)`, texto "MONTHLY" sobre `finanzas_municipales`, único dataset local con `source_mode: monthly`); `make verify-landing` exit 0; diff acotado a `index.html` (+5 líneas). Ejecutado en worktree `worktree-agent-ae7ce7730e9f2c706`, commit `4006f12`. |
| 046 | [`privacy.html` fuera de marca](archive/046-privacy-page-brand-consistency.md) | S | LOW | DONE — `<style>` reescrito con tokens del sitio (fondo `#f7f6f0`, texto `#1a221f`, enlaces `#123d30`/hover `#0a241c`, fallback de `--font-sans`, sin `#6C47FF` ni `system-ui`); envuelto con `<header>` (link "← chile-hub") y `<footer>` ("Volver a chile-hub") mínimos; `index.html` no tocado. Verificado con Playwright (`background-color` body `rgb(247, 246, 240)`, color de enlace de header `rgb(26, 34, 31)`, captura visual confirma paleta crema/verde sin morado); `make verify-landing` exit 0; diff acotado a `privacy.html` (+44/-3 líneas). Ejecutado en worktree `worktree-agent-a73e6fe3389241f0d`, commit `00ef134`. |
| 047 | [`--space-lg` no definida + fuente Fira Code no cargada](archive/047-fix-space-lg-and-fira-code-fallback.md) | S | LOW | DONE — `margin-top:var(--space-lg)` → `margin-top:2rem` en el link "Leer el caso de estudio completo →"; `font-family: 'Fira Code', 'Courier New', Courier, monospace` → `var(--font-mono)` en `.playground-console` (opción recomendada del plan, reutiliza IBM Plex Mono ya cargada). Verificado con Playwright (`margin-top` computado `32px` vs `0px` original, `console font-family` resuelve a `"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, monospace`); `make verify-landing` exit 0; diff acotado a `index.html` (+2/-2 líneas). Ejecutado en worktree `worktree-agent-a7123712f5de317a9`, commit `d338675`. |
| 048 | [CSS duplicado de `.dataset-card` + `!important` en `.catalog-grid`](archive/048-cleanup-duplicate-dataset-card-css.md) | M | MED | DONE — Grupo 1 (13 selectores 100% muertos: `.dataset-badges`, `.dataset-facts-primary`, `.dataset-actions`, `.dataset-details*`, `.dataset-detail-*`, `.dataset-meta-label`, `.dataset-artifacts`, `.dataset-tags`, `.dataset-preview` contenedor) eliminado; Grupo 2 (`.dataset-card` y familia, `.dataset-name`, `.dataset-desc`, `.dataset-badge` y variantes) fusionado en una sola definición cada uno, preservando por propiedad el valor que ya ganaba en la cascada; `.catalog-grid` con una sola definición sin `!important`. Cero cambio visual verificado independientemente por el revisor (no sólo por el executor): capturas Playwright antes/después normal+hover pixel-idénticas, captura de grid completo (10 tarjetas, 2 categorías) idéntica salvo el contador de freshness (drift esperado entre cargas), `getComputedStyle` confirma `position: relative`, `overflow: hidden`, `::before` opacity 0→1 en hover y `#catalog-grid` `display: flex` intactos; el único cambio real (`align-items: start` → `normal`) confirmado inerte porque `.catalog-category` tiene `width: 100%` explícito. `make verify-landing` exit 0, re-verificado por el revisor. Diff acotado a `index.html` (+38/-211 líneas). Desviación documentada y aceptada: `.dataset-details` dentro del selector compuesto `.technical-details summary, .dataset-details summary, .package-verify summary` (línea 643) se dejó sin tocar por estar fuera del alcance explícito del plan (selector compartido con clases vivas). Ejecutado en worktree `worktree-agent-a925853d8c8cf75bc`, commit `5417a12`. |
| 049 | [Unificar idioma + tokens de color en tarjetas del catálogo](archive/049-unify-landing-language-and-color-tokens.md) | M | LOW-MED | DONE — dependía de 045. Traducido al español: "N warnings"→"N advertencias" (`app.js:906`), badge `source_mode` vía `SOURCE_MODE_LABELS` (`live`→"en vivo", `fallback`→"respaldo", `monthly`→"mensual"; la clase CSS sigue usando el valor crudo en inglés, sin romper el CSS de los planes 045/048), "Freshness"→"Frescura" (`app.js:926`); hex sueltos de advertencia/error (`#fffbeb`/`#fef3c7`/`#92400e`/`#f87171`, y un `#ef4444` adicional hallado por el propio grep del plan en `app.js:493`, drawer preview error) reemplazados por los tokens `--accent-warm-*`. Fuera de alcance respetado: `app.js:569` ("Warnings: N" del drawer, verificado textualmente por `scripts/verify_landing.py`) y el vocabulario del dashboard de salud quedaron intactos. Verificado independientemente por el revisor: los 5 `grep` de done criteria confirmados, `getComputedStyle` del bloque "Acción recomendada" coincide exactamente con los tokens (`rgb(251,243,237)`/`rgb(240,222,203)`/`rgb(166,82,44)`), Playwright sobre las 15 tarjetas reales del catálogo confirma "FRESCURA"/"EN VIVO"/"RESPALDO"/"MENSUAL"/"N advertencias" sin ningún resto en inglés y sin caer en el fallback "desconocido". `make verify-landing` exit 0, re-verificado por el revisor. Diff acotado a `app.js` (+8/-6 líneas). Ejecutado en worktree `worktree-agent-a04ca42d61648bace`, commit `4ef7e24`. |

## Planes archivados (auditoría 2026-07-07)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 042 | [Ampliar cobertura de alcaldes al 100% vía BCN SIIT](archive/042-ampliar-cobertura-alcaldes-main-article.md) | S-M | LOW | DONE — `fetch_alcaldes_bcn()` + `fetch_alcalde_bcn()` implementados con `ThreadPoolExecutor`; `fetch_alcaldes()` reescrito con BCN SIIT como fuente primaria y Wikipedia como enriquecimiento de `periodo_inicio`; cobertura 165→346/346 (100%); 6 tests nuevos; `expected_record_count` 240→362; ficha y contrato actualizados. Commit `27ba534`. |
| 023 | [Datasets `autoridades_electas` y `partidos_politicos`](archive/023-autoridades-electas-partidos-politicos.md) | M-L | MED | DONE — Ola A y B `stable_publishable` en el bundle público. Plan 042 cerró el follow-up de cobertura de alcaldes; este plan queda completamente cerrado. |
| 041 | [Import/validate de `datapackage.json`](archive/041-design-datapackage-import-validate.md) | S | LOW | DONE — `from_datapackage()` y `frictionless_validate()` implementados con lazy frictionless import; 4 tests pasan; extra `validation` en pyproject.toml; ADR-008 committeado. |
| 040 | [Superficie SQL `hub.sql()` sobre Parquet](archive/040-design-hub-sql-query-surface.md) | S-M | LOW | DONE — `ChileHub.sql()` implementado con DuckDB lazy import + vistas Parquet; 3 tests pasan; extra `query` en `pyproject.toml`; ADR-007 committeado. |
| 039 | [Resuelve capas comunales 3/346 en el bundle](archive/039-design-resolve-sparse-comunal-layers.md) | S | LOW | DONE — decisiones de cobertura ya implementadas vía fixes reactivos (`57e6eaf`, `3f968ab`, `c8c7c70`); ADR-006 escrito y committeado documentando FILL/RE-CARRIL para los 3 datasets; verificación confirma finanzas_municipales 345 filas, consumo_electrico ausente del bundle. |
| 038 | [Deduplica `pipeline_status_utils.py`](archive/038-deduplicate-pipeline-status-utils.md) | M | MED | DONE — ejecutado en `advisor/038-dedup-pipeline-status-utils` commit `77931b2`; shim PEP 562 `__getattr__` (21 líneas) reemplaza copia de 936 líneas, docstring de sincronización manual eliminado del canónico, 324 tests pasan, lint y format-check OK. |
| 037 | [Vectoriza DV de RUT + elimina `rutificador`](archive/037-vectorize-rut-validation.md) | M | MED | DONE — ejecutado en `advisor/037-vectorize-rut` commit `6062f45`; `_expected_dv_vectorized` reemplaza `map_elements` con Polars vectorizado, `rutificador` eliminado de `pyproject.toml`, 95 tests pasan + 1 skipped, lint y format-check OK. |
| 036 | [Tests golden de writers de artefactos](archive/036-golden-output-tests-artifact-writers.md) | M | LOW | DONE — ejecutado en `advisor/036-artifact-writer-tests` commit `4310cf6`; `test_builders_formats.py` (10 tests) + `test_builders_artifacts.py` (8 tests), 18/18 pasan, round-trip Parquet/DuckDB/SQLite/Excel + integridad SHA-256 + consistencia manifiesto↔ZIP, `make lint` y `format-check` OK. |
| 035 | [Tests de caracterización del gate `verify_pipeline`](archive/035-characterization-tests-publish-gate.md) | L | LOW | DONE — `scripts` en coverage.source, `test_verify_pipeline.py` con 26 tests, cobertura de `verify_pipeline.py` subió de ~0% a 64%. |
| 033 | [Ejecuta mypy/bandit/pip-audit/interrogate en CI](archive/033-enforce-quality-gates-in-ci.md) | S-M | MED | DONE — ejecutado en `advisor/033-ci-quality-gates` commit `172014b`; 3 gates blocking (mypy/bandit/pip-audit) + interrogate informativo (`\|\| true`), `make docs-coverage`, `fail-under = 80`, fix de cast en `_logging.py`. |
| 032 | [Adelgaza deps runtime del paquete instalado](archive/032-slim-runtime-dependencies.md) | S | MED | DONE — ejecutado en `advisor/032-slim-runtime-deps` commit `8032069`; `[project.dependencies]` reducido a 4 entradas, 5 deps pipeline bajo extra `pipeline`, install-smoke `rows: 346`, `make package-smoke` OK, wheel METADATA confirma solo 4 `Requires-Dist`, pre-commit hooks pasan limpiamente. |
| 031 | [Cache de load_polars en ruta por defecto](archive/031-fix-dead-load-polars-cache.md) | S | LOW | DONE — `advisor/031-load-polars-cache` commit `7b1f065`; eliminado `not validate or` del guard. 55 tests pasan, lint OK. |
| 030 | [Guarda Excel + dedup SHA bundle](archive/030-excel-large-table-guard-and-bundle-sha-dedup.md) | S | LOW | DONE — `advisor/030-excel-guard` commit `a6aa9ef`; `_EXCEL_MAX_ROWS_SKIP = 500_000`, SHA se computa 1 vez. 150 tests pasan, build OK. |
| 029 | [Docstrings restaurados en core.py](archive/029-fix-misplaced-docstrings-core.md) | S | LOW | DONE — `advisor/029-fix-misplaced-docstrings` commit `1d7a963`; `__doc__` restaurado en 3 métodos. 228 tests pasan. |
| 028 | [Elimina verificación unrar no-op y engañosa](archive/028-remove-unrar-tofu-integrity-noop.md) | S | LOW | DONE — ejecutado en `advisor/028-remove-unrar-noop` commit `add5afa`; eliminados `_verify_unrar_integrity()`, `_UNRAR_EXPECTED_SHA256` e `import hashlib` de ambos extractores MINEDUC (-88 líneas), reemplazados por verificación real de disponibilidad vía `shutil.which()`. 108/108 tests pasan, lint y format-check OK. |
| 027 | [Provenance real en scrape SINIM exitoso](archive/027-sinim-finanzas-provenance-label.md) | S | LOW | DONE — ejecutado en `advisor/027-sinim-provenance-label` commit `4690fec`; `source_mode != "fallback"` reemplaza la rama muerta `== "live"`, 2 tests nuevos (`test_build_metadata_monthly_sets_live_provenance` + `test_build_metadata_fallback_sets_curated_provenance`), 9/9 tests pasan, lint y format-check OK. |
| 024 | [Extractores: preserva ceros CUT + timestamps ISO](archive/024-extractor-cut-and-timestamp-integrity.md) | S | LOW | DONE — ejecutado en `advisor/024-extractor-cut-timestamp` commit `3ad6ab9`; `grep` de timestamps, overrides/zfill, diff de `pipeline_status_utils`, pytest focal (`221 passed`), lint y format-check OK. |
| 025 | [Sincroniza enum `Dataset` (+docs) con el catálogo de 19](archive/025-sync-dataset-enum-and-docs-with-catalog.md) | S | LOW | DONE — ejecutado en `advisor/025-sync-dataset-enum`; `Dataset.values()` = 19, `Dataset.from_string()` resuelve los datasets nuevos, pytest focal (`39 passed, 130 deselected`), lint y format-check OK. Commit pendiente: el hook pre-commit local no encontró `interrogate`. |
| 026 | [Regenera `uv.lock` + guardia `--locked` en CI](archive/026-regenerate-uv-lock-and-ci-guard.md) | S | LOW | DONE — ejecutado en `advisor/026-uv-lock-sync` commit `a6b22b8`; `uv lock --locked`, `uv sync --extra pipeline --extra dev --locked` y `WorkflowContractTests` OK. |

## Planes archivados (resueltos por fixes reactivos a Pipeline Check #270, 2026-07-08)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 034 | [Arregla el workflow `monthly-scrape` (`--group dev`)](archive/034-fix-monthly-scrape-workflow.md) | S | LOW | DONE — **no ejecutado como plan**: resuelto de rebote por el commit reactivo `4ebca99` (`fix(ci): harden release artifact gates`), que cambió `uv sync --group dev` → `uv sync --extra pipeline --extra dev` en ambos jobs (Steps 1–2 del plan, verbatim). Endurecido después por `974b502`/`f0f8096`/`57e6eaf` (commit tolerante a `data/*` en `.gitignore`) y confirmado end-to-end por `c8c7c70` (refresh mensual de SINIM exitoso, 345/346 municipios). Único cabo suelto: el Step 3 del plan (test que impida que reaparezca `uv sync --group`) no se agregó — `tests/test_ci_config.py` guarda otras regresiones de esta misma cadena pero no esa línea específica; follow-up de bajo esfuerzo si se quiere el guardrail. |

## Planes archivados (docs, 2026-07-04)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 021 | [Publicar documentación de API con MkDocs Material + mkdocstrings](archive/021-mkdocs-api-docs.md) | M | LOW | DONE — sitio de docs (`mkdocs.yml`, `docs/index.md`, `docs/api.md`), targets `docs-build`/`docs-serve`, build integrado en `pages-deploy.yml` (servido en `/reference/`). |

## Planes archivados (mejoras de librerías/dependencias, 2026-06-29)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 018 | [Renderizar tablas de la CLI con `rich`](archive/018-rich-cli-table-output.md) | M | MED | DONE |
| 019 | [Publicar `datapackage.json` (Frictionless) como artefacto adicional](archive/019-frictionless-datapackage.md) | M | LOW | DONE |

## Planes archivados (plan maestro 2026-06-30)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 022 | [Plan de avance — confiabilidad/narrativa (Track A) + expansión de catálogo por valor de cruce (Track B)](archive/022-plan-avance-narrativa-confiabilidad.md) | L | MED | DONE — Track A (Fase 1–4) + Track B (Ola B1–B2) completos. Implementación de autoridades_electas y partidos_politicos diferida a Plan 023. |

## Planes archivados (auditoría 2026-06-19)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 010 | [Corregir bugs en extractores y validación](archive/010-fix-extractor-and-validation-bugs.md) | S | LOW | DONE |
| 011 | [Robustecer manejo de errores en API pública](archive/011-harden-api-error-handling.md) | S | LOW | DONE |
| 012 | [Hardening de seguridad — TOCTOU, integridad binario y paths](archive/012-security-hardening.md) | S | LOW | DONE |
| 013 | [Cache en memoria para la API de ChileHub](archive/013-api-performance-caching.md) | S | LOW | DONE |
| 014 | [Limpieza de arquitectura — catálogo externo, imports, alias](archive/014-architecture-cleanup.md) | S | LOW | DONE |
| 015 | [Robustez de tests — HTTP mocking, CLI coverage, assertions](archive/015-test-robustness.md) | M | LOW | DONE |
| 016 | [Cache de staging en CI](archive/016-ci-staging-cache.md) | S | MED | DONE |
| 017 | [Nuevas capacidades de API — cruces, validación, exit codes, búsqueda](archive/017-new-api-capabilities.md) | M | LOW | DONE |

## Planes archivados (auditoría 2026-06-13, completados)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 001 | Fix landing page bugs — KPIs antiguos y crash de coordenadas | S | LOW | DONE |
| 002 | Agregar CSP a la landing page | S | LOW | DONE |
| 003 | Validar metadata JSON antes del build | S | LOW | DONE |
| 004 | Limpiar dependencias — pyarrow, dev/prod, curl_cffi | S | LOW | DONE |
| 005 | Eliminar escrituras redundantes del build | S | LOW | DONE |
| 006 | Consolidar lógica duplicada y corregir violación de capas | S | LOW | DONE |
| 007 | Mejoras de tooling — pre-commit, editorconfig, CI | S | LOW | DONE |
| 008 | Hardening de source readiness, schema contracts y quality gates | L | MED | DONE |
| 009 | Separar carriles stable_publishable y candidate | M | MED | DONE |

## Grafo de dependencias (planes activos)

```
Auditoría 2026-07-07 (024–041):
  025                      (independientes — cada uno un archivo/área distinta)
  032 (DONE) → 040 (DONE)    (040 DONE: hub.sql() implementado, ADR-007 committeado)
  — (030 DONE) → 036 (DONE)            (036 afirma el guard de Excel de 030, ambos DONE)
  033 (DONE) → —                 (CI ya bloquea mypy/bandit/pip-audit en cada push/PR)
  035 (DONE) → —          (035 ya archivado: gate de publicación con 26 tests)
  041 (DONE)                    (041 DONE: from_datapackage() + frictionless_validate(), ADR-008)
  — (DONE)                     (039 DONE: ADR-006 escrito, decisiones ya implementadas)

Auditoría /improve next — dirección (050–052):
  050, 051, 052   (los tres independientes entre sí — archivos/áreas distintas, sin orden forzado).
                   051 absorbe el fix de from_datapackage(url) (antes considerado DIR-C aparte).
                   052 es prerrequisito conceptual para reevaluar el anti-patrón #10 (ingesta de datasets nuevos).

Decisión construir-por-delante-de-demanda (053–054):
  053 (flagship, P1)   Step 0 = ADR-011 (estrategia, requiere aprobación humana
                       proposed→accepted). Step 1 = gate de licencia (kill-switch).
                       ADR-011 es la compuerta de aprobación humana del sub-carril
                       ENTERO: gate de 053 Y de 054 (054 "respalda la apuesta"). Si
                       ADR-011 se rechaza, 053+054 caen y 050/051 pasan a ser toda la
                       historia de datos. Entregable primario = artefacto GeoParquet.
  054 (P2)             secuencia DESPUÉS de 053 (foso de confianza, no generador de
                       demanda). Alimenta drift + gate de publicación, no el build.
  050 ∩ 053            solapan en core.py y subdere_extractor.py — NO correr en worktrees
                       simultáneos; secuenciar o merge-coordinar.
  051 sube de relevancia bajo esta estrategia (distribución = alcance = demanda);
  052 pasa a medir la demanda generada (S/LOW; baseline conveniente pre-053, no gate).

Auditoría UX/UI 2026-07-13 (043–049) — TODOS DONE Y ARCHIVADOS (2026-07-14):
  043, 044, 045, 046, 047 (todos independientes entre sí — archivos/zonas de CSS distintas)
  045 → 049  (049 tocaba la misma región CSS de .dataset-badge.* que 045; se ejecutó 045
              primero para evitar que ambos editaran la misma línea en paralelo)
  048 (independiente — tocaba la región CSS *vieja*/muerta de .dataset-card, distinta de
       la que 045/049 tocaban)

Auditoría UX/UI 2026-07-14 (055–057) — diseño y experiencia de usuario:
  055 (P1, tipografía)   independiente — sólo toca index.html (3 vars CSS + <link> Google Fonts)
  055 → 056 (P2)         el espaciado usa métricas de fuente que dependen de las nuevas familias
  057 (P2)               independiente — recomendado ejecutar después de 055 para probar skeletons
                         con las nuevas fuentes, pero no es dependencia dura

Auditoría /improve next 2026-07-18 (058–063) — dirección, canales y superficie:
  058 (catálogo+README)  independiente — archivos disjuntos de 050–057 (catálogo JSON,
                         check_companion_paths, doc_sync, README, AGENTS.md §12)
  059 (Hugging Face)     lazo blando: 052 antes da baseline de medición limpio (no gate).
                         060 alimenta su dataset card (contenido, no bloqueo).
  060 (notebook)         independiente — sólo crea examples/notebooks/04_*.ipynb
  061 (quickstart R)     independiente — sólo docs (docs/r-quickstart.md + mkdocs.yml;
                         su Step 3 opcional toca README.md — ver nota abajo)
  062 (playbook contrib) independiente — sólo CONTRIBUTING.md
  058 ∩ 059 ∩ 061        co-toque de README.md (058 obligatorio; 059 Step 6 y 061 Step 3
                         opcionales): en worktrees paralelos, esos pasos van tras 058.
  063 (historial salud)  lazo blando: 054 antes le da señal de anomalías que mostrar (no gate).
                         Solapa con 055–057 en index.html/app.js — NO correr en worktrees
                         simultáneos con el carril B de landing; secuenciar.
```

**Interacciones clave de la auditoría 2026-07-07:** **026** (regenerar lock), **032** (adelgazar deps),
**033** (mypy/bandit/pip-audit en CI), **035** (tests gate de publicación), **037** (vectorizar RUT) y
**038** (dedup pipeline_status_utils) quedaron DONE. La ola de higiene deps/CI y los dos refactors están completos 🎉.
**036** (tests de writers) quedó DONE — el backfill de tests del gate y los writers está cerrado.
**040** ya sabe que `duckdb` va en el extra `pipeline`. **039** DONE ✅ (ADR-006). **040** DONE ✅ (hub.sql() + ADR-007). **041** DONE ✅ (from_datapackage() + frictionless_validate() + ADR-008).
**023** y **042** DONE ✅ (BCN SIIT completa cobertura de alcaldes 346/346 y cierra Plan 023).
**020** DONE ✅ (explorador SQL DuckDB-Wasm en la landing, 2026-07-10).

## Orden de ejecución recomendado

**Planes activos (050–063) — tres carriles paralelos (actualizado 2026-07-18):**

050–054 tocan el **paquete Python / capa de datos** (carril A); 055–057 tocan la
**landing** (`index.html`/`app.js`/`playground.js`) (carril B); 058–063 son
**canales/superficie** (carril C — catálogo/docs/ejemplos/CI, mayormente disjunto de A y
B). Los tres carriles apenas comparten archivos entre sí, así que el óptimo son
**tres carriles en paralelo** (el repo ya opera así vía worktrees), cada uno ordenado
internamente — ver la secuencia serial unificada más abajo para el modo de un solo hilo.

**Carril A — datos/librería (Python):**

1. **053 Step 0 + Step 1 primero** — ADR-011 (aprobación humana) + gate de licencia
   (kill-switch). Es la compuerta de todo el sub-carril construir-por-delante-de-demanda:
   gate de 053 **Y** 054. Barato de saber temprano; si se rechaza, 053+054 caen y 050/051
   pasan a ser toda la historia de datos.
2. **053** completo — sólo si la compuerta pasa. Artefacto GeoParquet (generador de
   demanda) + `resolve_by_coords()`.
3. **050** — superficie hermana (resolución por nombre); la más grounded (criterio #4 del
   product-spec).
4. **051** — capa de distribución; absorbe el fix `from_datapackage(url)`.
5. **054** — foso de confianza; secuencia DESPUÉS de 053.

> ⚠ **050 y 053 solapan** en `src/chile_hub/core.py` y `src/extractors/subdere_extractor.py`
> (comparar sus drift-check globs): NO correrlos en worktrees simultáneos — secuenciar o
> merge-coordinar. El resto del carril A es disjunto en archivos.

**Carril B — landing (en paralelo al carril A):**

`055 → { 056, 057 }`. **055** (P1, LOW) es la base; **056** depende **duro** de él
(métricas de fuente). **057** sólo tiene el lazo blando "055 recomendado", así que tras
055, **056 y 057 pueden ir en paralelo**.

**052 (P3, S, LOW)** es el quick-win independiente: su hueco ideal es la **espera de
aprobación de ADR-011** (mientras un humano ratifica el ADR, el ejecutor no está bloqueado;
llena la ventana con 055 del carril B y 052). Landearlo antes de que 053 publique da un
baseline pre-flagship limpio — conveniente, **no** un gate (los conteos de GitHub Releases
son acumulativos y PyPI `recent` es backfillable).

**Secuencia serial unificada (si un solo ejecutor, un hilo) — los 14 planes activos
(actualizada 2026-07-18; reemplaza al interleaving 2026-07-14, que sólo cubría 050–057):**

> **053 Step 0 → 053 Step 1** (dispara el reloj humano: aprobación ADR-011 y gate de
> licencia; en paralelo el mantenedor crea el secret `HF_TOKEN`) →
> **062 → 061 → 060** (trío S/LOW — quick wins que además sirven de *capability probe*
> del ejecutor; 060 produce contenido para la dataset card de 059) →
> **055 → 056 ∥ 057** (carril B; P1 de landing) →
> **052** (baseline de adopción — debe estar vivo antes de que 053 y 059 generen
> demanda, o el efecto no es medible) →
> **058** (M/LOW, disjunto; cierra el hueco de `AGENTS.md §12`) →
> **053 completo** (tras aprobación ADR-011; flagship) → **050** (solapa archivos con
> 053 — nunca en paralelo) → **051** → **054** →
> **059** (con 052 ya midiendo y `HF_TOKEN` creado) →
> **063** (último: necesita la señal de 054 y que el carril B haya cerrado, por solape
> en `index.html`/`app.js`)

Criterios que ordenan esa secuencia (para reevaluarla si cambia el contexto):

1. **Los relojes asíncronos se disparan primero** — la aprobación humana de ADR-011 y la
   creación manual de `HF_TOKEN` no consumen ejecutor; arrancarlos en el paso 1 elimina
   el único cuello de botella que no es código.
2. **Riesgo creciente del ejecutor** — el trío S/LOW primero (sonda de capacidad), M/LOW
   después, los dos planes con más superficie de deriva (059: CI+servicio externo; 063:
   estado+frontend) al final, cuando ya hay confianza y revisión acumulada.
3. **Medición antes que demanda** — 052 precede a 053 y 059, o sus efectos son
   indistinguibles del ruido.
4. **Nunca dos planes en los mismos archivos en paralelo** — 050∩053
   (`core.py`/`subdere_extractor.py`), 063∩055–057 (`index.html`/`app.js`).

**Auditoría 2026-07-18 (058–063) — notas de encaje con los carriles existentes:**

1. **058 primero dentro del carril C por leverage** — S–M, LOW, cierra un hueco que el
   propio `AGENTS.md §12` nombra; deja el mapeo dataset↔extractor como dato validado en
   CI (beneficia a todo lo demás). En la secuencia serial unificada cede el paso al trío
   S/LOW sólo por granularidad de riesgo, no por prioridad.
2. **060, 061, 062** — los tres S/LOW, independientes entre sí y de casi todo lo activo;
   ideales como relleno de ventanas de espera (p. ej. la aprobación de ADR-011).
   ⚠ Matiz de "independencia": 058 (obligatorio), 059 (Step 6 opcional) y 061 (Step 3
   opcional) pueden tocar **README.md** — en modo worktrees paralelos, correr esos pasos
   de README sólo después de mergeado 058, o descartar los pasos opcionales.
3. **059** — tras 052 (baseline de medición) y con el secret `HF_TOKEN` ya creado por el
   mantenedor; es el generador de demanda del batch.
4. **063 al final** — después de 054 (señal de anomalías) y sin solaparse con 055–057 en
   `index.html`/`app.js` (si el carril B sigue activo, secuenciar).

> ⚠ **063 solapa con 055–057** en `index.html`/`app.js`: no correr en worktrees
> simultáneos con el carril B. El resto del carril C es disjunto en archivos con A y B
> (salvo el matiz de README.md del punto 2).

**Auditoría 2026-07-07 (024–041) — orden sugerido por olas (actualizado 2026-07-09; 024, 025, 026, 032, 033 y
034 ya están DONE/archivados, no aparecen abajo):**

1. **Ola de fixes P2, un archivo cada uno, sin dependencias entre sí** — **COMPLETA** 🎉
   (027, 028, 029, 030 y 031 DONE — archivados).
2. **Higiene de deps/CI** — **COMPLETA** 🎉 (032, 033 y 034 DONE).
3. **Backfill de tests**: **COMPLETA** 🎉: **035** ✅ DONE (gate de publicación) y **036** ✅ DONE (writers).
4. **Refactors** — **COMPLETA** 🎉: **037** ✅ (vectoriza RUT) y **038** ✅ (dedup pipeline_status_utils).
5. **Diseño/spikes**: **COMPLETA** 🎉: **039** ✅ DONE (ADR-006), **040** ✅ DONE (hub.sql() + ADR-007), **041** ✅ DONE (from_datapackage() + ADR-008).

**Auditoría UX/UI 2026-07-13 (043–049) — COMPLETA 🎉 (los 7 planes DONE y archivados,
ver "Planes archivados (auditoría UX/UI 2026-07-13)"). Orden en que se ejecutaron:**

1. **Bugs visibles de mayor impacto, sin dependencias entre sí** — **043** (scroll del
   Explorador SQL, la feature más nueva del sitio), **044** (pills `.dataset-tag` sin
   estilo, visible en las 15 tarjetas del catálogo), **045** (badge `monthly` sin
   color).
2. **Consistencia de marca, bajo riesgo** — **046** (`privacy.html`), **047**
   (`--space-lg` + fuente `Fira Code`).
3. **Higiene de CSS** — **048** (consolidar `.dataset-card` duplicado; M/MED, requirió
   verificación visual antes/después).
4. **Pulido de contenido** — **049** (unificar idioma + tokens de color), después de
   **045** por tocar la misma región de `.dataset-badge.*`.

## Hallazgos considerados y diferidos (2026-07-18 — dirección)

Auditoría `/improve next` (foco: dirección/roadmap; commit `6bf6b08`). Los 6 hallazgos
presentados (D1–D6) fueron **todos seleccionados** y son los planes 058–063. Lo
considerado y **no** convertido en plan, para que no se re-audite:

| Hallazgo | Motivo |
|----------|--------|
| **Kaggle Datasets como canal de distribución** | **Diferido — hacer 059 (HF) primero.** Mismo mecanismo de valor (descubrimiento), pero upload manual/fricción mayor y automatización más débil que HF Hub. Reconsiderar cuando 059 esté live y 052 muestre su efecto. |
| **Publicación en conda-forge** | **Diferido — sin tracción que lo justifique.** La audiencia objetivo resuelve hoy con `pip` (paquete puro-Python, 4 deps runtime); conda-forge agrega un feedstock que mantener. Reevaluar si PyPI muestra adopción del segmento científico (052). |
| **README/docs en inglés** | **Rechazado por ahora — contradice la decisión i18n recién landeada.** El plan 049 (2026-07-14) unificó deliberadamente la landing al español; el producto es datos chilenos para audiencia primaria chilena (product-spec). Una versión inglesa es decisión de producto nueva, no extensión obvia. |
| **Forzar Release 2.0.0** (nota stale de `NEXT_STEPS.md` 2026-06-29) | **Decisión del mantenedor, no plan de código.** El versionado es automático vía python-semantic-release; un bump major forzado es un acto de comunicación, no de ingeniería. La nota de NEXT_STEPS quedó stale (el proyecto ya está en 1.21.x). |
| **Re-scope de D3 (carril de contribución)** | **Verificado en recon, no es hallazgo nuevo.** El issue template `.github/ISSUE_TEMPLATE/dataset_request.yml` **ya existe** y cubre las preguntas bloqueantes — por eso el plan 062 es solo el playbook del lado código en `CONTRIBUTING.md`. |
| **Tests de notebooks en CI** (ejecutar `examples/` en un job) | **Diferido — convención actual es notebooks sin ejecutar en CI.** El plan 060 se verifica localmente con `nbconvert --execute`. Un job de CI para notebooks es discutible pero requiere decidir caching del bundle en CI; abrir solo si 060 drifta una vez. |

## Hallazgos considerados y diferidos (2026-07-14 — dirección)

Auditoría `/improve next` (foco: dirección/roadmap; commit `7ebf94b`). Considerados y
**no** convertidos en plan propio, para que no se re-auditen:

| Hallazgo | Motivo |
|----------|--------|
| **DIR-C: `from_datapackage()` promete URL pero sólo maneja paths locales** (`core.py:454-460`) | **No es un plan de dirección aparte — es un defecto, absorbido por el Plan 051.** El docstring dice "Ruta local o URL" pero `Path(path_or_url).exists()` hace fallar cualquier URL. Es el lado cliente natural de la capa HTTP estática, así que se arregla como primer entregable del Plan 051, no como hallazgo de dirección independiente. |
| **DIR-D: decisión `delincuencia_comunal` (CEAD) antes de `review_by 2026-09-21`** (`source_registry.json:388`) | **Decisión del mantenedor con fecha, no plan de código.** El extractor y el workflow existen; el `next_action` ("buscar fuente estructurada oficial; degradar a `rejected` si no madura") ya está escrito. Igual que se manejó DIR-05 en la auditoría 2026-07-07. Sólo tener presente que la fecha cae ~2 meses después de esta auditoría. |
| **Añadir datasets nuevos** (`plus-codes`, `entrepreneurship`, ambos `needs-research` en `docs/dataset-ideas/`) | **Sigue gated tras la decisión construir-por-delante-de-demanda (2026-07-14).** El matiz de esa decisión (ADR-011) es preciso: autoriza **profundidad de capacidad sobre fuentes existentes de alta calidad** (por eso el Plan 053 de geometría procede), pero **NO** amplitud hacia fuentes frágiles/scraping. `plus-codes` y `entrepreneurship` son `needs-research` sobre fuentes no consolidadas → siguen bloqueados hasta que el Plan 052 muestre adopción. La geometría (053) NO cae aquí: es la misma fuente BCN ya usada, no una fuente nueva. |
| **API Premium / ChileHub Cloud** | **Rechazado por evaluación previa (ME8, `docs/backlog/08-...md`).** El dato es CC-BY redistribuible y pequeño; no justifica un paywall ni infra 24/7 con mantenedor único. El Plan 051 entrega justamente la alternativa que ME8 sí recomienda (API gratuita estática). |
| **Instrumentar el paquete/bundle para medir uso** | **Rechazado por ética de apertura.** Telemetría en el artefacto que corre en la máquina del usuario contradice el modelo de valor. El Plan 052 mide adopción sólo vía APIs públicas de plataforma (PyPI/GitHub) en CI. |

## Hallazgos considerados y diferidos (2026-07-13 — auditoría UX/UI)

Considerados en la auditoría `/improve` (foco: UX/UI, contenido, layout, estilo,
espaciado, fuentes; commit `901f5b9`) y **no** convertidos en plan, para que no se
re-auditen:

| Hallazgo | Motivo |
|----------|--------|
| **Contraste de color / WCAG** | **Fuera de alcance deliberado.** Cubierto por la skill dedicada `accessibility`; auditar contraste desde una sesión de `/improve` enfocada en UX/UI hubiera duplicado esa cobertura en vez de complementarla. |
| **Vocabulario inglés del dashboard "Estado operativo"** (`ok`/`warn`/`error`, `.pill.live/fallback/stale/drifted`, `.health-badge.*`) | **Diferido — distinto del Plan 049.** Es terminología operacional de un panel de estado (patrón común en dashboards técnicos), no copy orientado al usuario final. Varios de esos textos los verifica textualmente `scripts/verify_landing.py:373-387`; tocarlos tiene su propio riesgo de romper CI y merece un plan propio si se decide unificar. |
| **`app.js:563` — "Warnings: N" del drawer, en inglés** | **Diferido — explícitamente excluido del Plan 049.** Verificado byte a byte por `scripts/verify_landing.py:496,573`; traducirlo requiere tocar el smoke test en el mismo cambio. Anotado como follow-up dentro del propio Plan 049. |
| **`formatFreshness()` — valores "fresh"/"stale"/"unknown" en inglés** (`app.js:118-125`) | **Diferido — vocabulario de contrato de datos.** `freshness.status` es un valor compartido entre el pipeline Python, el dashboard de salud y las tarjetas del catálogo; traducirlo de forma consistente en todos los consumidores es un esfuerzo mayor (toca `src/`, no sólo la landing) y no encaja en el alcance "UX/UI de la landing" de esta auditoría. |
| **Rediseño visual de `.dataset-card`** (más allá de consolidar el CSS duplicado del Plan 048) | **No se propuso.** El Plan 048 preserva el resultado visual actual a propósito (es limpieza, no rediseño); un rediseño deliberado de las tarjetas es una decisión de producto/diseño que le corresponde al mantenedor, no un hallazgo de auditoría. |
| **Auditoría del pipeline Python** (extractores, validación, builders) | **Fuera de alcance.** El usuario pidió explícitamente UX/UI/contenido/diseño; el pipeline ya tiene su propia cola de planes vigentes (024–038) de auditorías previas. |

## Hallazgos considerados y diferidos (2026-07-07 — auditoría deep)

Considerados en la auditoría `/improve deep` (commit `c486e7c`) y **no** convertidos en plan, para que no se
re-auditen. (Los defectos accionables sí están en 024–041.)

| Hallazgo | Motivo |
|----------|--------|
| **PERF-01**: el pipeline regenera todos los artefactos de todos los datasets en cada corrida (sin deltas) | **Diferido — L, MED.** Coincide con la pregunta abierta PQ4 (`.audit/open-questions.md`) y el rechazo previo de "build paralelo": el ahorro no justifica el riesgo mientras el build completo tome <45 min. Rebuild incremental necesita hash por dataset + coherencia del contenedor DuckDB/SQLite/ZIP. Reconsiderar cuando el build supere 45 min. |
| **PERF-06**: `overview`/`snapshot`/`runtime_status` recomputan `freshness_audit`/`summary` varias veces por invocación | **Diferido — magnitud baja.** Las lecturas JSON/Parquet ya están memoizadas; la recomputación es iteración en memoria sub-ms. Cleanup "solo si se toca el archivo". |
| **SEC-02**: guardia de contención en `data_manager.clear()` usa `startswith` de strings de path | **Diferido — LOW.** Ruta auto-infligida (el usuario setea el env var). Cambiar a `is_relative_to` es un one-liner; hacerlo la próxima vez que se toque `data_manager.py`. |
| **SEC-03**: atributos `class` en la tabla de salud de `app.js` sin `escapeHtml` | **Diferido — LOW.** Valores internos enum + `script-src 'self'` mitigan; no es XSS vivo. Corregir en el template de `src/builders/landing.py` (no en el `app.js` autogenerado) cuando se edite la landing. |
| **CORRECTNESS-04**: `validate_user_data` resuelve contratos desde `ROOT_DIR` de módulo, no `self.root_dir` | **Diferido — MED.** Real en modo instalado/bundle, pero requiere decidir dónde viven los contratos para usuarios instalados. Anotado en el Plan 029 (Maintenance notes) como follow-up. |
| **TECHDEBT-02**: `core.py` (2302 líneas) es god module; ~600 líneas de CLI viven ahí en vez de `cli.py` | **Diferido — L, MED.** Alto valor pero rewrite grande con red de seguridad solo de smoke tests. Mover la CLU a `cli.py` primero sería la rebanada de mayor valor; abrir plan propio cuando haya apetito. |
| **TECHDEBT-03**: `sinim_finanzas_extractor.py` y `sinim_finanzas_live_extractor.py` son copias divergentes | **Diferido — M, MED.** El Plan 027 corrige el bug de provenance de la copia live; la consolidación de `normalize_rows`/`build_metadata` compartidas queda como follow-up. |
| **TECHDEBT-05**: cinco idiomas distintos de resolución de raíz/`data/` (`parents[N]`, `_find_root`, etc.) | **Diferido — M, MED.** Consolidar en `_find_root()` toca muchos archivos; cosmético-funcional. Estandarizar gradualmente. |
| **TECHDEBT-06 / DX-06**: split diario-vs-mensual de extracción no documentado; `make bootstrap` no instala `--extra scraping` | **Diferido — S, docs.** Anotado en el Plan 034 archivado (Maintenance notes, `archive/034-fix-monthly-scrape-workflow.md`). Documentar los dos carriles de extracción y la degradación de `autoridades_electas` sin scrapling. Sigue sin hacerse — el fix reactivo que archivó 034 resolvió el bug de `--group dev`, no esta documentación. |
| **TC-04 / TC-05 / TC-07**: characterization de `build_dev_db.py`; tests de los 2 extractores live; split de `test_chile_hub.py` que hoy exige un build previo | **Diferido — backlog de tests.** Los planes 035 (gate) y 036 (writers) cubren el riesgo de publicación más alto primero; el resto del backfill queda como follow-up. |
| **DIR-04**: promover o aceptar `autoridades_locales` (cola abierta del Plan 023) | **No duplicar** — sigue rastreado por el Plan 023 activo (cobertura de alcaldes). |
| **DIR-05**: decidir `delincuencia_comunal` (CEAD) antes de su `review_by 2026-09-21` | **Decisión del mantenedor, no plan de código.** El extractor y el workflow existen; el `next_action` en `data/source_registry.json` fuerza la decisión. |

## Hallazgos considerados y diferidos (2026-06-29 — mejoras de librerías)

| Hallazgo | Motivo |
|----------|--------|
| **`pandera` (backend Polars) para consolidar validación** | **Diferido — tradeoff dudoso.** El ADR-005 decidió deliberadamente mantener los contratos `*.schema.json` como formato propio (más expresivo que JSON Schema para ancho fijo/cobertura/outputs; los tipos de Polars no mapean 1:1 a estándares). Pandera añadiría una **tercera** representación de esquema junto a `contracts/datasets/` y `src/validation.py`, y el ADR ya reconoce que los validadores de dominio (dígito verificador RUT, longitud CUT, sumas de cohortes) deben permanecer en Python de todos modos. La consolidación real sería marginal y el riesgo de divergencia, alto. Reconsiderar solo si se decide reemplazar por completo `validation.py`. |
| **`typer` para reemplazar el `argparse` de la CLI** | **Diferido — incluido como follow-up en el Plan 018.** La CLI es un `argparse` probado con ~40 subcomandos; migrarla es un rewrite L con riesgo MED-HIGH de regresión, y el beneficio (ayuda/autocompletado) es marginal frente al `rich` del Plan 018, que captura la mayor parte del valor de UX con riesgo bajo. |
| **`orjson`/`msgspec` para (de)serialización JSON** | **Rechazado.** Micro-optimización sin cuello de botella demostrado: el JSON I/O del pipeline no domina el wall-clock (lo dominan DuckDB/SQLite/Excel). No justifica una dependencia nueva. |
| **`httpx` en lugar de `requests`** | **Rechazado.** Solo aportaría async, que el proyecto no necesita hoy (extractores secuenciales con `tenacity`). `requests` + `curl_cffi` ya cubren el caso por diseño (ver rechazo DM-08 de 2026-06-13). |

## Hallazgos considerados y rechazados (2026-06-19)

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **PERF-05**: 9× `to_list()` de comunas | Micro-optimización: 346 strings, ~2ms total. No justifica un plan. |
| **ARCH-08**: convención de paths mixta `os.path.join` vs `Path /` | Cosmético, sin impacto funcional. Se estandariza gradualmente en otros planes. |
| **DEP-03**: versiones 1 patch detrás | duckdb 1.5.3→1.5.4, ruff 0.15.17→0.15.18: bumps triviales. Se actualizan en el próximo release. |
| **PERF-07**: iloc copy en Excel chunking | ~525K filas extra en memoria para 1.57M dataset — memoria total <3GB, aceptable para build offline. |
| **PERF-04**: build paralelo | Diferido: el riesgo MED de paralelizar DuckDB+SQLite+Excel juntos no justifica el ahorro de ~30s de wall-clock hoy. Reconsiderar cuando el build supere 5 min. |
| **TC-02**: cobertura medida contra 5% del código | Diferido: ajustar `source` en `pyproject.toml` requiere primero cubrir `build_dev_db.py` y `validation.py` (backlog ME1). |
| **TC-04**: 34/40 funciones de build_dev_db.py sin tests | Incluido en backlog ME1 (Refactorizar build_dev_db.py). |
| **ARCH-03**: build_dev_db.py god module | Incluido en backlog ME1. No duplicar plan. |
| **DIR-03/04**: fallback stabilization | Incluido en backlog ME4. No duplicar plan. |
| **DIR-01**: runtime contracts | Incluido en backlog ME2. No duplicar plan. |
| **DIR-07**: health dashboard | Incluido en backlog ME5. No duplicar plan. |

## Hallazgos considerados y rechazados (2026-06-13, heredados)

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **PERF-08**: `comunas_enriquecidas` duplica byte a byte a `comunas` en 5 formatos | **Revertido en 2026-06-19**: el Plan 014 ahora lo aborda como alias (no duplicado). El costo de superficie de código (38 archivos mantienen este concepto duplicado) justifica el cambio. |
| **PERF-10**: CI serializa quality antes de build-and-test | Por diseño. |
| **ARCH-12**: `indicadores_hoy.json` inconsistente | Por diseño. |
| **ARCH-13**: `import json` redundante | Trivial. |
| **DM-08**: `requests` + `curl_cffi` overlap | Por diseño. |
| **DM-09**: `pandas` podría removerse | No justifica esfuerzo. |
| **BUG-04 a BUG-10**: varios bugs de bajo riesgo | Riesgo bajo o por diseño. |

## Reevaluación 2026-07-09

Contexto: entre la auditoría `/improve deep` de `c486e7c` (2026-07-07) y `HEAD` (`c1aa3e9`, 2026-07-09)
hubo 45 commits. La mayoría no fueron ejecuciones de estos planes sino **fixes reactivos** a bugs reales
descubiertos persiguiendo el fallo de CI "Pipeline Check #270": la cadena `4ebca99` → `dc5a882` →
`0229cc3` → `f056684` → `974b502` → `f0f8096` → `fcc7f6f` → `57e6eaf` → `3ad6ab9` (Plan 024, ese sí
ejecutado) → `88187f0`/`71bc263` (Plan 025) → `9b85a23` → `df0999e` → `3f968ab` → `354ad6e`. Se pidió
reevaluar si `plans/` sigue vigente. Método: cada plan activo trae su propio comando de "drift check"
(`git diff --stat c486e7c..HEAD -- <archivos-del-plan>`) — se ejecutó para los 15 planes activos y se
verificó el código/config real donde hubo diff.

**Resultado por plan:**

| Plan | Diff en sus archivos desde `c486e7c` | Veredicto |
|---|---|---|
| 027 | ninguno | Vigente. El bug (etiqueta de provenance) sigue presente y ahora es **observable en datos reales** committeados (ver su fila arriba). |
| 028 | ninguno | Vigente, sin cambios. |
| 029 | ninguno | Vigente; se confirmaron las 3 líneas exactas del defecto. |
| 030 | `build_dev_db.py` +2 líneas (import de `sync_all_docs`, no relacionado) | Vigente; el guard de Excel sigue ausente. |
| 031 | ninguno | Vigente; se confirmó la línea exacta del guard invertido. |
| 032 | `pyproject.toml` (solo bump de versión), `AGENTS.md`, `uv.lock` | Vigente; las 5 deps solo-pipeline siguen en `[project.dependencies]`. |
| 033 | `pipeline-check.yml` +81/-7, `Makefile` +9 | Vigente; el job `quality` creció (lock-sync, docs-sync, companion-paths) pero mypy/bandit/pip-audit/interrogate siguen sin CI. |
| 034 | `monthly-scrape.yml` reescrito | **DONE de rebote** — archivado (ver tabla de archivados arriba). |
| 035 | `verify_pipeline.py` +43/-, tests +1355 líneas | Vigente; cobertura de `verify_*` subió de 4 a 6 funciones de ~24, pero el deliverable del plan no existe. |
| 036 | ninguno | **DONE** — ejecutado 2026-07-09, commit `4310cf6`. |
| 037 | `pyproject.toml` (solo bump de versión) | Vigente; `rutificador` sigue importado vía `map_elements`. |
| 038 | ambas copias +54 líneas cada una (edición manual paralela) | Vigente; se confirmó que siguen byte-idénticas, pero el riesgo que el plan describe se ejercitó en vivo. |
| 039 | `source_registry.json`/`dataset_catalog.json` reescritos | **Sustancialmente resuelto**, sigue `TODO` solo para el ADR — ver nota en el archivo del plan y su fila arriba. |
| 040 | `README.md` +53/-13 (sección DuckDB, no la API) | Vigente, sin cambios en `core.py`. |
| 041 | `pyproject.toml` (solo bump de versión) | Vigente, sin cambios. |
| 023 | sin diff en extractores relevantes | Sin cambios; la nota granular existente en su fila sigue siendo precisa. |
| 020 | +index.html +scripts/verify_landing.py +playground.js +vendor/ | DONE 2026-07-10. |

**Conclusión**: de 15 planes activos, 13 siguen 100% vigentes tal como están escritos (sus propios
drift-checks los blindan contra los cambios de línea/número que sí ocurrieron), 1 se archivó por estar
resuelto (034) y 1 se redujo de alcance por estar resuelto en sustancia (039, falta solo el ADR). No se
encontró ningún plan activo que un fix reactivo haya vuelto obsoleto por completo ni ninguno cuya premisa
ya no aplique.

## Columnas de estado

- `TODO` — pendiente de ejecución
- `IN PROGRESS` — en ejecución activa
- `DONE` — completado
- `BLOCKED` — bloqueado (indicar por qué)
- `BACKLOG` — diferido a backlog (ver `docs/backlog/`)
- `SKIP` — descartado después de análisis adicional
