# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commits `ba2f434` (2026-06-13), `a2cd288` (2026-06-19) y `c486e7c` (2026-07-07), y por `/improve plan` (mejoras de librerías/dependencias) en commit `140c8ea` (2026-06-29).

> **Auditoría `/improve next` — dirección/roadmap (2026-07-26, commit `63cc106`)**:
> se revalidaron los cinco hallazgos con mayor palanca: resolución nombres→CUT
> (**050**), acceso HTTP/DCAT (**051**), publicación de la geometría candidate
> (**064**), resolución coordenadas→CUT (**065**), anomalías temporales (**054**) y
> ownership catálogo→extractor (**058**). El Plan 053 dejó completos sus Steps 0–3;
> sus dos entregables restantes se separan en 064/065 para aislar riesgos de CI y de
> API runtime. No se propone un dataset nuevo: ADR-011 sigue priorizando profundidad
> sobre fuentes oficiales existentes, no amplitud de fuentes frágiles.

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

> **Auditoría `/improve deep` 2026-08-12 (commit `53781e2`)**: planes **069–085**
> (17 hallazgos net-positivos + 4 de dirección). Re-auditoría tras 3 días de
> cambios densos (release chain, IPC INE, CLI refactor, landing, merge queue).
> Cuatro subagentes por categoría (correctness/security, perf/deps, tests/DX,
> docs/direction); todos los hallazgos vetados por el advisor contra el código
> y los artefactos reales. **Los 3 primeros (069–071) están confirmados en
> producción** (metadata real, mirror HF real, ZIP real) — son bugs que
> violan la política declarada, no opiniones.

| # | Plan | Prioridad | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|----------|--------|-----------|--------|
| 069 | [Override INE como delivery visible (no enmascarado como backfill)](069-ine-override-delivery-visible.md) | P1 | M | MED | — | DONE (2026-08-12, commit 6ef22fd — delivery visible en extractor + gates; branch advisor/069 sin merge) |
| 070 | [Filtrar HF por publication_track (nunca candidate/deprecated)](070-hf-publication-track-filter.md) | P1 | M | MED | — | DONE (2026-08-12, commit d34462f — registry como fuente de carril; branch advisor/070 sin merge) |
| 071 | [El catálogo del bundle ZIP solo declara capas realmente incluidas](071-bundle-catalog-consistency.md) | P1 | M | MED | coordina 070 | DONE (2026-08-12, commit e9d6041 — catálogo filtrado en el ZIP; branch advisor/071 sin merge) |
| 072 | [Validar miembros del ZIP antes de extractall (zip-slip/symlink)](072-zip-slip-guard.md) | P2 | S | LOW | — | TODO |
| 073 | [Contratos disponibles para consumidores instalados (wheel + bundle)](073-contracts-for-consumers.md) | P2 | M | MED | — | TODO |
| 074 | [Anomalías temporales sobre el punto más reciente (IPC negativo)](074-anomalies-last-point-attribution.md) | P2 | S | LOW | — | TODO |
| 075 | [Acoplar valor y período en el regex del override INE](075-ine-regex-value-period-coupling.md) | P2 | S | LOW-MED | — | TODO |
| 076 | [RES incremental — descargar solo el año en curso](076-res-incremental-fetch.md) | P2 | M | MED | — | TODO |
| 077 | [Caracterizar build_dev_db.py (cobertura 21% → ≥60%)](077-characterize-build-dev-db.md) | P2 | L | MED | — | TODO |
| 078 | [Paralelizar CEAD y geometría (scrapes secuenciales)](078-parallelize-cead-geometria.md) | P2 | M | MED | — | TODO |
| 079 | [Cobertura de writers y extractores sin test (geo, CEAD, reports)](079-cover-geo-cead-reports.md) | P2 | M | LOW | 077 (helper) | TODO |
| 080 | [Higiene de tests (red real, sleeps, staleness, e2e, Makefile)](080-test-hygiene-batch.md) | P3 | M | LOW-MED | — | TODO |
| 081 | [Docs — quickstart R, marcas de carril, inventario de extractores](081-docs-quickstart-lanes-inventory.md) | P3 | S | LOW | — | TODO |
| 082 | [Mostrar el carril candidate en la landing](082-landing-candidate-lane.md) | P3 | M | MED | 070, 071 | TODO |
| 083 | [Señal proactiva de review_by inminente](083-review-approaching-signal.md) | P3 | S-M | LOW | — | TODO |
| 084 | [Promover perfil_territorial_comunal al bundle estable](084-promote-perfil-territorial.md) | P3 (decisión) | S-M | MED | 070, 071 | TODO |
| 085 | [ADR multi-fuente para el override de IPC](085-adr-multi-source-ipc-override.md) | P3 | M | LOW | 069, 075 | TODO |

## Dependencias y orden recomendado

**Lote 1 (bugs confirmados en producción — P1):**
069 → 070 → 071. 069 (delivery INE visible) debe preceder a 070 (ambos tocan
el flujo de indicadores); 071 coordina con 070 en la noción de "publicable".

**Lote 2 (seguridad/consumidor):**
072, 073 (independientes).

**Lote 3 (correctness del override + perf diaria):**
074, 075 (el guard del valor INE), 076 (RES incremental, mayor ahorro diario).

**Lote 4 (tests):**
077 (caracterización build_dev_db, base para 079) → 079 (helper compartido),
078 (paralelización), 080 (higiene).

**Lote 5 (docs + dirección):**
081 (docs), 082/083/084/085 (dirección — los 4 requieren decisión o
ratificación del mantenedor; 084 es decisión de producto).

## Hallazgos considerados y rechazados (2026-08-12)

- **PERF-01 (builds incrementales)**: confirmado correctamente diferido — sin
  telemetría de duración y con timeout real de CI de 30 min < umbral de 45;
  el accionable es medir (dentro del lote de perf), no implementar deltas hoy.
- **PERF-6 (re-lectura de parquet en verify)**: coste aceptado — el guard
  post-build independiente tiene valor anti-regresión.
- **PERF-7 (fallback por-comuna de geometría)**: solo aplica en degradación;
  absorbido por 078 (paralelización).
- **SECURITY-03 (temp paths fijos)**: race teórico sin ejecución concurrente
  (CI serializa); registrado, no planificado.
- **CORRECTNESS-05 (caché de DataFrames no invalidada)**: real pero requiere
  decisión de API; documentado como follow-up, no plan.
- **SECURITY-02 (SQL interpolado en sql())**: riesgo limitado al trust domain
  del catálogo; fragilidad de comillas real pero de bajo impacto; no plan.
- **DX-05 (cache de staging ~2 GB)**: beneficio incierto; requiere
  re-verificación en runner; no plan.
- **TC-04/05 (caracterización restante de tests)**: cubiertos por 077/079/080.

## Orden de ejecución actualizado (2026-07-26)

> **Actualización 2026-07-28 (merge de la cola)**: los planes **050, 051, 054, 057,
> 058, 059 y 063** quedaron mergeados a `main` (commits `a065a38`…`5036257`) y
> archivados; el **064** también está en `main` (PR #41) pero sigue `IN PROGRESS`
> porque sus dos últimos done criteria (dispatch autorizado + lectura desde Pages)
> dependen del operador. La secuencia vigente se reduce a los pasos 1–3 de abajo.
>
> **Cierre final (2026-08-11)**: con el 064 DONE (2026-07-29) y el 065 DONE y
> mergeado (PR #54), la secuencia se agotó. El 053 (plan maestro de geometría)
> se archivó el mismo día; ver su fila en "Planes archivados (2026-07-24)".
> La cola se reabrió con la auditoría 2026-08-12 (planes 069–085, ver
> "Planes activos").

1. **065** — DONE (2026-08-11): `resolve_by_coords()` implementado y verificado end-to-end contra el artefacto de Pages (ver fila archivada). La cola de planes está vacía.

**053 quedó archivado (2026-08-11)**: el plan maestro de geometría quedó completamente cerrado al mergearse el 065 (PR #54). Steps 0–3 entregados por el propio plan; los pendientes (publicación CI del artefacto y `resolve_by_coords()`) se ejecutaron como **064** (DONE 2026-07-29, verificado end-to-end contra Pages) y **065** (DONE 2026-08-11). Todos sus done criteria verificados en el repo: ADR-011/ADR-012 presentes, `data/normalized/geometria_comunal.parquet` con 345 comunas y `codigo_comuna` string de 5, extra `geo` en `pyproject.toml` sin deps geo en runtime, `check_companion_paths.py registry` exit 0. Ver fila archivada abajo.

**066 quedó DONE y archivado (2026-07-28)**: `drifted_count` bajó 8→3 y los 3 problemas de datos reales salieron como issues [#42](https://github.com/cortega26/chile-hub/issues/42)/[#43](https://github.com/cortega26/chile-hub/issues/43)/[#44](https://github.com/cortega26/chile-hub/issues/44). El historial de salud (063) ya registra la taxonomía corregida, y con eso se cierra también el pendiente "vocabulario del dashboard de salud" diferido en la auditoría 2026-07-13.

### Dependencias de la auditoría 2026-07-26

- 065 depende estrictamente de 064: sin una lectura remota exitosa y un checksum publicado, no hay contrato seguro de cache.
- 051 y 064 deben coordinar la documentación de la URL estática, pero no se bloquean a nivel de código.
- 054 sigue siendo el respaldo de confianza; no debe retrasar la publicación ni la API de geometría.
- 050 y 065 modifican `src/chile_hub/core.py`; ejecútalos secuencialmente, no en worktrees paralelos.

## Hallazgos considerados y rechazados (2026-07-26)

- **Agregar un dataset nuevo**: rechazado por ahora. Las ideas restantes requieren fuentes o licencias aún no consolidadas; ADR-011 limita la estrategia actual a profundizar capacidad sobre la fuente BCN ya validada.
- **Subir el límite global de 500 KB o saltar pre-commit**: rechazado. El flujo de CI de 064 resuelve la publicación de datos sin debilitar los controles locales para el código.

## Planes archivados (2026-07-24)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 053 | [Geometría comunal — parent histórico](archive/053-comuna-geometry-and-reverse-geocoding.md) | L | MED | DONE (2026-08-11) — plan maestro completamente cerrado: Steps 0–3 entregados por el propio plan (extractor `geometria_comunal_extractor.py`, validación, writer GeoParquet, licencia, docs, ADR-011/ADR-012); Steps 4–5 ejecutados como **064** (publicación CI del artefacto, DONE 2026-07-29, verificado end-to-end contra Pages) y **065** (`resolve_by_coords()`, DONE 2026-08-11, mergeado a `main` vía PR #54). Done criteria verificados en repo: `geometria_comunal.parquet` (345 comunas, `codigo_comuna` string de 5, EPSG:4326), `comunas` sin columnas nuevas, extra `geo` (`geopandas`/`shapely`/`pyarrow`) sin tocar runtime base, `check_companion_paths.py registry` exit 0, 826 tests + 1 skip. |
| 064 | [Publicar GeoParquet candidate desde CI](archive/064-publish-geometry-artifact-from-ci.md) | M | MED | DONE (2026-07-29) — **verificado end-to-end contra Pages**, no solo localmente. El mantenedor disparó el `workflow_dispatch`; el run [30490817948](https://github.com/cortega26/chile-hub/actions/runs/30490817948) validó y commiteó exactamente las 5 familias permitidas (parquet de 5.1 MB, `.sha256`, staging CSV+metadata, snapshot raw) sin tocar el guard de 500 KB. Lectura remota confirmada: `HTTP 200`, 5.106.496 bytes, **345 registros**, **EPSG:4326**, 0 geometrías nulas/vacías, `codigo_comuna` único y de 5 caracteres con cero inicial preservado (`01101`), y el `.sha256` publicado coincide byte a byte con el artefacto descargado. La geometría sigue **fuera** del bundle estable (19 datasets), del ZIP publicable, del manifiesto y del catálogo. **Dos defectos reales que solo aparecieron al ejecutarlo de verdad**, ambos corregidos: (1) el commit del bot usa `GITHUB_TOKEN`, que no dispara eventos `push`, y el workflow nuevo no estaba en el `workflow_run` de `pages-deploy.yml` → la URL pública daba **404** pese al commit exitoso; agregado, más un guardrail que exige que todo workflow que commitea datos esté en esa lista. (2) El guardián de frescura (`verify_pipeline.py` y su copia en `tests/test_chile_hub.py`) quedaba en falso positivo permanente tras cada refresh, exigiendo un rebuild que jamás tocaría el carril candidate (ADR-012); se excluye vía `OUT_OF_BAND_STAGING_METADATA`, con el test importándola en vez de duplicarla. 802 tests + 1 skip; todos los gates exit 0. |
| 065 | [Resolver coordenadas a comuna](archive/065-add-coordinate-resolver.md) | M | MED | DONE (2026-08-11) — `resolve_by_coords(points, *, refresh_geometry=False, geometry_path=None)` en `ChileHub`: tuplas `(latitud, longitud)`, `pl.DataFrame` con `input_lat/input_lon/codigo_comuna/nombre_comuna/matched`, orden y duplicados preservados, fuera de Chile → `matched=False`, lat/lon fuera de rango → `ValueError` nombrando el input, borde matchea (`covers`), tie-break determinístico (menor `codigo_comuna` + warning). Extra consumidor `geo` (`geopandas/shapely/pyarrow`); base intacta; import lazy con `ImportError` "pip install chile-hub[geo]" (patrón de `sql()`). `src/chile_hub/geo.py` nuevo: compañero `.sha256` parseado antes de aceptar descarga (formato `sha256sum`, basename verificado), descarga atómica a temporal, reemplazo del caché solo si la digest coincide, caché previo preservado ante fallo/checksum malo (Mocks, cero red real), caché en `platformdirs.user_cache_dir("chile-hub")` reutilizado sin red, validación estructural (geometry, EPSG:4326, CUT de 5 chars, sin duplicados, ≥340 geometrías), `resolve_points()` puro para tests sin red. Contrato de distribución/caché y decisiones de borde en ADR-012 (Step 1 + Step 5). Fixtures sintéticos de 3 comunas cuadradas (`tests/geo_fixtures.py`) — nunca el artefacto real de 5 MB. 15 tests nuevos (7 en `test_core.py` incl. lazy-extra; 8 en `test_chile_hub.py` incl. checksum-preserva-caché y estructurales). Verificado end-to-end contra el artefacto real publicado: Santiago centro → `13101`, mar → unmatched, duplicados preservados. Suite 826 tests + 1 skip; `make build`/`verify`/`test`/`lint`/`format-check`/`doctor` exit 0. **Desviación documentada**: `make docs-coverage` sigue rojo (43.5% vs 80%) — ya estaba rojo antes del plan (29.6% en el commit previo) y CI lo corre como informativo (`|| true`); este plan lo sube ~14 pts, pero sanear los 46 items de `core.py` está fuera del scope. Branch `advisor/065-coordinate-resolver`, sin merge/push. |
| 067 | [Backfill consciente de la edad](archive/067-backfill-consciente-de-la-edad.md) | M | MED | DONE (Steps 2–5; Step 1 operador) — cierra el grueso del issue #43. El issue decía "investigar por qué falta `ipc`"; la evidencia mostró que la serie **está muerta desde 2025-12-01** (240 días) mientras `utm` —igual de mensual y del mismo endpoint— está al día, y que `published_backfill` venía re-publicando el mismo punto en cada build. El entregable no es reparar `ipc` sino cerrar el modo de falla: `build_indicator_ages()` calcula `indicator_max_date`/`indicator_age_days` por serie **en el build** (no en el extractor: ahí quedaría inerte justo cuando el extractor no vuelve a correr, que es cuando una serie muerta se esconde); umbral por cadencia (70d mensual / 10d diaria, junto a `MONTHLY_INDICATORS` como fuente única); y violación de política de publicación **override-able** vía `--allow-stale-backfills`, reusando el patrón del gate de anomalías del Plan 054 — el build nunca aborta. Verificado end-to-end: `--profile publication` rechaza con `ipc: 240d > 70d`, el override lo deja pasar, y el perfil `dev` no cambia. 11 tests nuevos (6 de gate, 5 de cálculo), incluido el guardrail de que una serie vieja entregada **en vivo** no dispara este gate (sería frescura mal ubicada). ADR-016 escrito. **Desviación del plan**: el Step 2 decía calcular la edad en el extractor; se movió al builder por la razón de arriba. **Pendientes**: Step 1 (diagnóstico `curl` de mindicador.cl — requiere red, sigue en el issue #43) y frescura por indicador (follow-up, sin plan). 799 tests + 1 skip; todos los gates exit 0. |
| 068 | [Estado `retired` — fuentes muertas fuera de la señal de salud](archive/068-retirar-consumo-electrico-de-salud.md) | S | LOW-MED | DONE — cierra el issue #44. `_load_retired_datasets()` deriva el conjunto de `maturity_status: "deprecated"` del registry (sin nombres hardcodeados); `build_hub_health()` marca `retired` en cada entrada (siempre presente) y computa **todos** los contadores sobre el conjunto activo, con `retired_count` nuevo. `drifted_count` 3→2 y `warn_count` 3→2, `dataset_count` **intacto en 19** y sus 4 gates sin tocar. Alcance decidido por el mantenedor: NO se retira de la superficie pública — `Dataset.CONSUMO_ELECTRICO_COMUNAL` y `load_polars()` siguen funcionando (verificado), porque sacarlos del enum sería BREAKING CHANGE con bump mayor forzado sobre un paquete ya en PyPI. La entrada sigue visible marcada, y `drift_report.json` la sigue reportando `drifted` — lo que cambia es que no cuenta en la señal. Gates agregados: `retired` booleano y `0 <= retired_count <= dataset_count`. Hallazgo durante la implementación: `test_health_summary` afirmaba **cinco** invariantes de suma contra `EXPECTED_DATASET_COUNT` (el plan sólo había verificado `verify_pipeline.py`); se reexpresaron contra el conjunto activo, no se relajaron. `hub.health()` gana `retired_count` para que el resumen público cuadre. Guardrails del Plan 066 actualizados 3→2 con justificación explícita (mecanismo distinto al de ADR-014). ADR-015 escrito; ADR-014 intacto como registro histórico. 788 tests + 1 skip; build/verify/test/verify-landing/lint/format-check/doctor exit 0. |
| 066 | [Separar drift esperado de drift real](archive/066-taxonomia-drift-esperado-vs-real.md) | M | MED | DONE — clasificación, no reparación de datos: `drifted_count` 8→3 y `warn_count` 7→3 (`overall_status` sigue `warn`), con los 3 restantes siendo exactamente los problemas reales (`empresas`, `indicadores`, `consumo_electrico_comunal`). Baseline del Step 0 reproducido (`19 8 7 warn` con los 8 datasets esperados) **antes** de tocar nada. Tres mecanismos: (1) `VALID_SOURCE_MODES`/`NON_FALLBACK_SOURCE_MODES` movidos a `src/builders/_shared.py` como fuente única que `verify_pipeline.py` reexporta — el predicado de `perfil_territorial_comunal` usa pertenencia en vez de `== "live"`, así que `monthly` (finanzas_municipales) ya no lo declara `fallback`; (2) `build_coverage()` lee el `coverage_policy` del contrato (que existía y se ignoraba) y emite `coverage.expected` booleano **siempre presente** + `expected_reason`, sin tocar el enum `status`; (3) `_add_expected_warning()` en `validation.py` declara los 3 warnings de diseño (SIEDU urbano, cobertura SAE, `estado_legal` vía SERVEL) en el **emisor**, y `build_degradation()` descuenta esos de los accionables — `warnings` conserva todos los mensajes en todos los artefactos. `build_hub_health()` gana `actionable_warning_count` y `coverage_expected`; la severidad usa el accionable. Gates **agregados** (ninguno relajado, ningún enum ampliado): `coverage.expected` booleano y sólo sobre `status == partial`; `actionable_warning_count` entero `<= warning_count`. Landing: badge de atención por accionables y píldora `partial esperada`. 23 tests nuevos en `test_pipeline_logic.py` (incluido el guardrail anti-silenciador y el que fija `drifted_count == 3`) + 4 gates nuevos en `test_verify_pipeline.py`; 779 tests + 1 skip. **Desviación**: el plan pedía ADR-013, pero el Plan 054 lo tomó al mergearse — el entregable es **ADR-014**. Step 6: issues [#42](https://github.com/cortega26/chile-hub/issues/42), [#43](https://github.com/cortega26/chile-hub/issues/43) y [#44](https://github.com/cortega26/chile-hub/issues/44) abiertos con autorización del operador. `tests/e2e/verify_066.sh` en verde; `make build`/`verify`/`test`/`verify-landing`/`lint`/`format-check`/`doctor` y `pre-commit run --all-files` (incluido mypy) exit 0. Branch `advisor/066-drift-taxonomy`, sin merge/push. |
| 063 | [Historial de salud del hub + sparkline en landing](archive/063-historial-salud-hub.md) | M | MED | DONE — `append_hub_health_history()` en `src/builders/reports.py`: JSONL append-only, idempotente por `generated_at_utc` (rebuilds no duplican), cap `HUB_HEALTH_HISTORY_MAX_LINES=400`, escritura atómica (`tmp` + `os.replace`). Wired en `_generate_reports()` de `src/build_dev_db.py` entre `write_hub_health_json` y `build_hub_status`. Sparkline SVG inline en `index.html`/`app.js` (`renderHealthHistory()`), últimas 30 entradas, barras apiladas ok/warn/error normalizadas por `dataset_count`, degrada con gracia (oculto) si el fetch falla o el archivo está vacío. Dos gaps bloqueantes encontrados y corregidos durante la implementación: (1) `.gitignore` sólo re-incluía `*.json/*.md/*.parquet/*.zip/*.sha256` bajo `data/normalized/*` — sin el fix `!data/normalized/*.jsonl` el artefacto habría quedado permanentemente gitignoreado, contradiciendo la premisa de persistencia entre builds vía el job `publish`; (2) `hub_health_history.jsonl` no aparecía en `artifact_manifest.json` por dos causas simultáneas — `PUBLISHABLE_ARTIFACT_SUFFIXES` no incluía `.jsonl` y `build_publishable_artifact_index()` requería una entrada explícita en `shared_artifacts` — corregidas ambas en `src/builders/_shared.py` y `src/builders/artifacts.py`. Tests: `HubHealthHistoryTests` (5 tests) en `tests/test_pipeline_logic.py` cubriendo creación, idempotencia por timestamp, orden cronológico, tope de líneas y tolerancia a líneas malformadas. `tests/e2e/verify_063.sh` reproduce los done criteria de punta a punta — con una excepción deliberada respecto al patrón de otros `verify_NNN.sh`: no revierte `index.html` en su limpieza, porque en este plan ese archivo contiene markup/CSS del sparkline escrito a mano, no sólo ruido de build (el script original sí lo revertía y borró esos cambios una vez durante el desarrollo; recuperados manualmente y corregido el script). Commits en `advisor/063-hub-health-history`. |
| 058 | [Campo `extractor` en el catálogo + tabla de extractores auto-generada en README](archive/058-catalogo-campo-extractor-y-tabla-readme.md) | M | LOW | DONE — campo `extractor` agregado a las **22** entradas del catálogo (drift desde que el plan se escribió: `geometria_comunal` se sumó en Plan 053; mapeado a `geometria_comunal_extractor.py`, dominio Territorio); `check_extractors()` nuevo en `check_companion_paths.py registry` (valida existencia + detecta huérfanos); `sync_readme_extractor_table()` en `doc_sync.py` genera la tabla de README preservando el agrupamiento editorial exacto + fila derivada de `perfil_territorial_comunal`; `AGENTS.md §12` actualizado (tabla de propietarios + pendiente de extractores retirado); 7 tests nuevos (`ExtractorRegistryTests`, +3 en `DocSyncTests`); suite completa 696 tests + 1 skip, `make doctor`/`lint`/`format-check` OK. Branch `advisor/058-catalog-extractor-field`, sin merge/push (pendiente de confirmación del operador). |
| 055 | [Overhaul tipográfico: legibilidad profesional de datos](archive/055-typography-and-readability-overhaul.md) | M | LOW | DONE — Source Serif 4, Inter, and JetBrains Mono integrated in `index.html`; Google Fonts link updated; verified with `make verify-landing` and CI checks; commit in `advisor/055-typography-overhaul`. |
| 056 | [Ritmo visual, espaciado y jerarquía de secciones](archive/056-visual-rhythm-spacing-hierarchy.md) | M | LOW | DONE — header sticky con backdrop blur; 3 tiers de espaciado (`--space-section-tight/normal/loose`) con overrides contextuales; separadores `::before` en `.section-shell` y `.manifesto`; verificado con `make verify-landing`, `make lint`, `make format-check`, `make doctor`; commits en `advisor/056-visual-rhythm-spacing`; mergeado a `main` en `8259e09`. |
| 060 | [Notebook flagship — cruce multi-capa por `codigo_comuna`](archive/060-notebook-flagship-cruce-capas.md) | S | LOW | DONE — `examples/notebooks/04_perfil_territorial_pobreza.ipynb` created and verified to run successfully on Python 3 with clean outputs; joins `perfil_territorial_comunal`, `pobreza_comunal`, and `resultados_educacionales`; commit in `advisor/060-flagship-notebook`. |
| 061 | [Quickstart de consumo desde R (arrow + duckdb)](archive/061-quickstart-r.md) | S | LOW | DONE — `docs/r-quickstart.md` created, nav entry added, `docs/installation.md` updated, checked with `make doctor` and `make docs-build`. |
| 062 | [Playbook de contribución de extractores](archive/062-playbook-contribucion-extractores.md) | S | LOW | DONE — sección `## Contribuir un extractor (dataset nuevo)` añadida a `CONTRIBUTING.md`; checklist 8-pasos + encuadre + nota de expectativa; `make doctor` exit 0; commit `928cec1` en `advisor/062-extractor-contribution-playbook`. |
| 050 | [Resolutor público `resolve_comunas()` (nombres → CUT)](archive/050-resolve-comunas-name-to-cut.md) | M | LOW-MED | DONE — `src/chile_hub/text.py::normalize_comuna_name()` (helper puro, reproduce exactamente la cadena de `subdere_extractor.py`); `ChileHub.resolve_comunas(names)` determinista (normaliza + match exacto contra `nombre_comuna_clean`), devuelve DataFrame de 5 columnas con `codigo_comuna` como `pl.String`, no-matches explícitos (`matched=False`) sin excepción; subcomando CLI `resolve` modelado sobre `cross`; `ADR-009` con las 4 preguntas abiertas (fuzzy diferido, `resolve_regiones()`, Series/DF de entrada, colisiones — 0 encontradas en las 346 comunas hoy); 10 tests nuevos (5 en `test_core.py` incluido el guardrail anti-divergencia obligatorio, 5 en `test_pipeline_logic.py`); suite completa 699 tests + 1 skip, `make doctor`/`lint`/`format-check` OK. Nota: el plan decía modelar los tests sobre `cross_view` en `test_core.py`, pero esos tests reales viven en `test_chile_hub.py` — se usaron como modelo estructural igual, y los tests nuevos se escribieron en `test_core.py` (el archivo que el propio "In scope" del plan designa). Branch `advisor/050-resolve-comunas`, sin merge/push. |
| 059 | [Publicación del bundle en Hugging Face Hub](archive/059-publicacion-huggingface-hub.md) | M | MED | DONE — `scripts/publish_hf_dataset.py` (`--dry-run` + subida real perezosa de `huggingface_hub`) selecciona las 19 capas `stable_publishable` con `redistribution_ok is True`; **fix sobre el propio plan**: `comunas_enriquecidas` es un alias intencional que apunta al mismo Parquet que `comunas` (Plan 014/PERF-08) — sin nombrar el archivo de destino por clave de catálogo en vez del basename fuente, el mirror colapsaba a 18 archivos en vez de 19; corregido y verificado (`grep -c "data/.*\.parquet"` → `19`). Job `hf-publish` en `pypi-release.yml`, `needs: release` con nuevos `outputs: released/ready` expuestos en el job `release`, gateado también en `ready` (no sólo `released`) para no intentar publicar sin datos verificados; falla explícito si `HF_TOKEN` no está configurado, nunca bloquea el release. `docs/hf/dataset-card.md` con placeholder `{{DATASET_TABLE}}`. 4 guardrails nuevos en `test_ci_config.py` (job presente, script con `redistribution_ok`/`--dry-run`, carril candidate nunca nombrado, `hf-publish` nunca bloqueante). `AGENTS.md` §9/§11 y badge HF en README actualizados. Suite completa 693 tests + 1 skip, `make doctor`/`lint`/`format-check` OK. Secret `HF_TOKEN` pendiente de creación manual por el mantenedor (no bloquea la implementación). Branch `advisor/059-huggingface-publish`, sin merge/push. |
| 054 | [Validación de anomalías temporales sobre series numéricas](archive/054-temporal-anomaly-validation-numeric-series.md) | M | MED | DONE — `detect_series_anomalies()` (z-score robusto MAD sobre log-retornos día a día) detecta saltos atípicos en `indicadores`; calibrado contra los 506 registros reales del repo (z_threshold=4.0, min_history=4 — máximo z histórico real ~3.8, cero falsos positivos) y contra los 4 casos adversariales del test plan (ruido estable, serie corta, tendencia gradual legítima). Integrado en `validate_indicadores` **sólo como warning** (`grep -c "errors.append.*anomal"` = 0, frontera dura verificada). Propagado a `drift_status: "drifted"` + `recommended_action` accionable vía `build_degradation()`/`build_drift()` en `src/builders/metadata.py` (el plan sugería `reports.py`, pero el mecanismo real de cómputo vive en `metadata.py`; `reports.py` lo hereda sin cambios, sin canal nuevo). Gate de publicación en `verify_pipeline.py` (`--profile publication`) rechaza ante anomalía no revisada, con override real `--allow-known-anomalies uf,dolar,...`; el **build nunca aborta** (verificado con `make build` + perfil `dev`). `ADR-013` documenta método, calibración, umbral, ruta de override y 4 preguntas abiertas (wiring a `workflow_dispatch`, allowlist persistente, extensión a otras series, recalibración futura). 15 tests nuevos (6 en `test_validation.py` para `detect_series_anomalies` + anomalía en `validate_indicadores`, 3 en `test_verify_pipeline.py` para el gate); suite completa 698 tests + 1 skip, `make doctor`/`lint`/`format-check` OK. Branch `advisor/054-anomaly-validation`, sin merge/push. |
| 051 | [Capa de acceso HTTP estática + catálogo DCAT `data.json`](archive/051-static-http-access-and-dcat-catalog.md) | M | LOW | DONE — `ADR-010` (perfil DCAT-US por default, DCAT-AP de datos.gob.cl no verificable → pregunta abierta; 0 pinning por versión); `src/builders/dcat_catalog.py` genera `data/normalized/data.json` desde `datapackage.json` (19 datasets, `downloadURL` absolutas bajo `https://tooltician.com/chile-hub/`), enganchado en `build_dev_db.py` junto a `write_data_package_json`; `docs/http-access.md` con ejemplos Python/R/JS/DuckDB, agregado a `mkdocs.yml`. `from_datapackage(url)` ya no lanza `FileNotFoundError` — detecta URL y valida el descriptor via frictionless, pero **corrigiendo una asunción incorrecta del propio plan**: `ChileHub.__init__` no tiene ningún mecanismo para leer `data_dir` remoto (verificado en el código, no asumido), así que en vez de devolver un `ChileHub` silenciosamente roto, levanta `ChileHubDataError` con las alternativas reales (`ChileHub()` sin argumentos, o consumir la URL directo vía `docs/http-access.md`); la limitación queda documentada como follow-up explícito en el ADR (Pregunta abierta #5). 8 tests nuevos (3 en `test_core.py`, 5 en `test_pipeline_logic.py`, path local de `test_data_package.py` sin regresión); suite completa 697 tests + 1 skip, `make doctor`/`lint`/`format-check`/`mkdocs build` OK. Branch `advisor/051-static-http-dcat`, sin merge/push. |
| 057 | [Skeleton loading states + polish de interacción](archive/057-loading-skeletons-and-interaction-polish.md) | M | LOW | DONE — el plan se escribió contra un `app.js`/`index.html` hipotético (spinner inyectado por JS, `filteredCount`, tarjetas con atributo `data-dataset`) que nunca coincidió con el código real (drift check confirmó cero diff en `app.js` desde el commit citado, pero ninguno de esos patrones existe ahí). Implementación adaptada al código real: skeletons como placeholders **estáticos** en `index.html` (catálogo: 4 `.skeleton-card`; KPIs: `.skeleton-pulse` reemplaza el `<div class="spinner">` de cada `.kpi-value`/`.kpi-date`) — más simple que inyección por JS, sin carrera con el fetch; `.no-results-message` agregado a `filterCatalog()` en `app.js` (variable real `visibleCount`, no `filteredCount`); tarjetas clickeables vía handler delegado sobre `.dataset-card` que reusa el enrutamiento por hash existente (`window.location.hash = card.id`, mismo camino que el enlace "Ver Ficha" → `showDatasetDrawer`); tecla Escape **ya existía** en el código real (no requirió cambios). Verificado con Playwright ad-hoc (captura del estado skeleton, click de tarjeta abre el drawer correcto, Escape cierra, "Ver Ficha" sigue funcionando, no-results aparece/desaparece); `make verify-landing`, `make lint`, `make format-check`, `make doctor` OK. Diff acotado a `index.html` + `app.js`. Branch `advisor/057-loading-skeletons`, sin merge/push. |

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

> **Actualización 2026-07-24**: 055, 056, 060, 061 y 062 quedaron `DONE` y se archivaron
> (ver "Planes archivados (2026-07-24)"). El resto de la secuencia de abajo (redactada
> 2026-07-18) sigue válida tal cual para los planes que quedan activos — sólo se
> saltan los pasos ya archivados al recorrerla. Carril A activo: 050, 051, 053 (🔶
> Steps 0-3 done, Step 4/5 diferidos), 054. Carril B activo: sólo 057. Carril C activo:
> 058, 059, 063. Ejecución inline y secuencial de aquí en más (sin worktrees paralelos
> por plan) — ver `spec.md`/`todo.md` en la raíz del repo para el orden concreto elegido
> esta sesión.

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
