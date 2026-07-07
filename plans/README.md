# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commits `ba2f434` (2026-06-13), `a2cd288` (2026-06-19) y `c486e7c` (2026-07-07), y por `/improve plan` (mejoras de librerías/dependencias) en commit `140c8ea` (2026-06-29).

> **Última auditoría `/improve deep` (2026-07-07, commit `c486e7c`)**: planes **024–041**.
> Repo maduro; los grandes ítems previos ya están hechos. Lo restante es una cola de
> defectos pequeños de alta confianza (024–031), higiene de deps/CI (032–034), backfill
> de tests del gate de publicación y los writers (035–036), dos refactors (037–038) y
> tres planes de diseño (039–041). Ver "Hallazgos considerados y diferidos (2026-07-07)".

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
> 3. **Archiva el trabajo terminado.** Cuando un plan pasa a `DONE`, mueve su fichero `.md` a
>    `archive/` **de inmediato** y borra su fila de la tabla de activos — no lo dejes en la tabla
>    activa ni en `plans/` raíz. Si merece mención, añádelo a la sección "Planes archivados"
>    correspondiente. Para un **plan maestro multi-fase**, no lo archives hasta que **todas** sus
>    fases/olas estén `DONE`; mientras tanto, mantén su fila activa con el estado granular del
>    paso 1.
> 4. **Verifica coherencia**: el grafo de dependencias y el "Orden de ejecución recomendado" de
>    abajo deben seguir siendo válidos tras el cambio; ajústalos si una dependencia se resolvió o
>    cambió de prioridad.

## Planes activos

| # | Plan | Prioridad | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|----------|--------|-----------|--------|
| 025 | [Sincroniza enum `Dataset` (+docs) con el catálogo de 19](025-sync-dataset-enum-and-docs-with-catalog.md) | P1 | S | LOW | — | TODO |
| 027 | [Provenance real en scrape SINIM exitoso](027-sinim-finanzas-provenance-label.md) | P2 | S | LOW | — | TODO |
| 028 | [Elimina verificación unrar no-op y engañosa](028-remove-unrar-tofu-integrity-noop.md) | P2 | S | LOW | — | TODO |
| 029 | [Corrige 3 docstrings desubicadas en `core.py`](029-fix-misplaced-docstrings-core.md) | P2 | S | LOW | — | TODO |
| 030 | [Guarda Excel para tablas masivas + dedup SHA bundle](030-excel-large-table-guard-and-bundle-sha-dedup.md) | P2 | S | LOW | — | TODO |
| 031 | [Arregla la cache muerta de `load_polars`](031-fix-dead-load-polars-cache.md) | P2 | S | LOW | — | TODO |
| 032 | [Adelgaza deps runtime del paquete instalado](032-slim-runtime-dependencies.md) | P2 | S | MED | — (026 DONE) | TODO |
| 033 | [Ejecuta mypy/bandit/pip-audit/interrogate en CI](033-enforce-quality-gates-in-ci.md) | P2 | S-M | MED | — | TODO |
| 034 | [Arregla el workflow `monthly-scrape` (`--group dev`)](034-fix-monthly-scrape-workflow.md) | P2 | S | LOW | — | TODO |
| 035 | [Tests de caracterización del gate `verify_pipeline`](035-characterization-tests-publish-gate.md) | P2 | L | LOW | — | TODO |
| 036 | [Tests golden de writers de artefactos](036-golden-output-tests-artifact-writers.md) | P2 | M | LOW | 030 (opc.) | TODO |
| 037 | [Vectoriza DV de RUT + elimina `rutificador`](037-vectorize-rut-validation.md) | P2 | M | MED | coord. 032 | TODO |
| 038 | [Deduplica `pipeline_status_utils.py`](038-deduplicate-pipeline-status-utils.md) | P3 | M | MED | — | TODO |
| 039 | [Diseño: resuelve capas comunales 3/346 en el bundle](039-design-resolve-sparse-comunal-layers.md) | P2 | M | MED | 034 (024 DONE) | TODO |
| 040 | [Diseño: superficie SQL `hub.sql()` sobre Parquet](040-design-hub-sql-query-surface.md) | P2 | S-M | LOW | coord. 032 | TODO |
| 041 | [Diseño: import/validate de `datapackage.json`](041-design-datapackage-import-validate.md) | P3 | S | LOW | — | TODO |
| 023 | [Datasets `autoridades_electas` y `partidos_politicos`](023-autoridades-electas-partidos-politicos.md) | P2 | M-L | MED | — (deriva de Plan 022 · Ola B2.2, research cerrada) | 🔶 Ola A y B `stable_publishable` y en el bundle público (2026-07-06): `partidos_politicos` (36, 15 con estado_legal/fecha vía SERVEL) y `autoridades_electas` (diputados+senadores, 205, senadores con codigo_region/periodo completos). `autoridades_locales` (gobernadores+alcaldes, 240, CC-BY-SA segregado) queda `candidate` — cobertura de alcaldes insuficiente a criterio del operador, pendiente mejorar el extractor. No se archiva hasta resolver ese follow-up. |
| 020 | [Explorador SQL en la landing con DuckDB-Wasm](020-duckdb-wasm-playground.md) | P2 | M | MED | — | BLOCKED — gate 4.3: NO-GO (2026-06-30). Ver `docs/gate-4-3-decision-playground.md` para condiciones de re-evaluación. |

## Planes archivados (auditoría 2026-07-07)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 024 | [Extractores: preserva ceros CUT + timestamps ISO](archive/024-extractor-cut-and-timestamp-integrity.md) | S | LOW | DONE — ejecutado en `advisor/024-extractor-cut-timestamp` commit `3ad6ab9`; `grep` de timestamps, overrides/zfill, diff de `pipeline_status_utils`, pytest focal (`221 passed`), lint y format-check OK. |
| 026 | [Regenera `uv.lock` + guardia `--locked` en CI](archive/026-regenerate-uv-lock-and-ci-guard.md) | S | LOW | DONE — ejecutado en `advisor/026-uv-lock-sync` commit `a6b22b8`; `uv lock --locked`, `uv sync --extra pipeline --extra dev --locked` y `WorkflowContractTests` OK. |

## Planes archivados (docs, 2026-07-04)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 021 | [Publicar documentación de API con MkDocs Material + mkdocstrings](archive/021-mkdocs-api-docs.md) | M | LOW | DONE — sitio de docs (`mkdocs.yml`, `docs/index.md`, `docs/reference.md`), targets `docs-build`/`docs-serve`, build integrado en `pages-deploy.yml` (servido en `/reference/`). |

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
  031 025 027 028 029 030       (independientes — cada uno un archivo/área distinta)
  032 → 037                     (lock limpio resuelto por 026; 037 quita rutificador que 032 reubica)
  032 ⇠ 040                     (040 hub.sql necesita duckdb; reconciliar con la reubicación de 032)
  030 → 036 (opcional)          (036 puede afirmar el guard de Excel de 030)
  033 034 035 038 041           (independientes)
  034 → 039                     (024 DONE; 039 decide capas comunales tras arreglar el scrape SINIM)

Planes previos:
  023 (independiente)  ← autoridades_electas + partidos_politicos; queda abierto por autoridades_locales
  020 (independiente)  ← bloqueado por gate 4.3 (no-go 2026-06-30). DIR-01/Plan 040 es su hermano no-bloqueado
```

**Interacciones clave de la auditoría 2026-07-07:** **026** (regenerar lock) quedó DONE el
2026-07-07, así que **032** (adelgazar deps) ya puede partir de un lock limpio; **037** elimina `rutificador`, que **032**
solo reubica — coordinar; **040** (`hub.sql`) reintroduce la necesidad de `duckdb` que **032** saca de
runtime, así que ambos deben acordar si `duckdb` vuelve a runtime o va en un extra `query`. **039**
depende ahora de **034** (scrape SINIM roto); **024** ya resolvió el bug CUT que bloqueaba
`consumo_electrico`. El resto de 025 y 027–031 son fixes de un archivo, ejecutables en cualquier
orden. **020** sigue bloqueado (gate 4.3 NO-GO); **021** (MkDocs) quedó DONE el 2026-07-04.

## Orden de ejecución recomendado

**Auditoría 2026-07-07 (024–041) — orden sugerido por olas:**

1. **Ola de fixes P1** (independiente, S/LOW): **025**. Defecto que desincroniza la API pública del enum
   con el catálogo — alto apalancamiento, verificación limpia. (**024** ya está DONE.)
2. **Ola de fixes P2** (independientes, S/LOW): **027, 028, 029, 030, 031**. Un archivo cada uno.
3. **Higiene de deps/CI**: **032**, luego **033** y **034**. (033 puede sacar a la luz un backlog de
   mypy/interrogate — ver su Step 1 y sus STOP conditions.)
4. **Backfill de tests**: **035** (gate de publicación — baseline de verificación), luego **036** (writers).
5. **Refactors**: **037** (vectoriza RUT; coordinar con 032) y **038** (dedup; MED por el acoplamiento
   `__init__ → core`).
6. **Diseño/spikes**: **039** (después de 034; 024 ya está DONE), **040** (coordinar con 032), **041**.

Planes previos aún vigentes:
- **023** — autoridades_electas + partidos_politicos: DONE para diputados/senadores/partidos; queda abierto
  el follow-up de `autoridades_locales` (cobertura de alcaldes). Se cruza con **DIR-04** de esta auditoría.
- **020** — DuckDB-Wasm playground: solo si lo aprueba una re-evaluación futura del gate 4.3. **Plan 040**
  entrega el mismo valor "explora los datos" a la audiencia que sí existe, sin depender del tráfico de la landing.

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
| **TECHDEBT-06 / DX-06**: split diario-vs-mensual de extracción no documentado; `make bootstrap` no instala `--extra scraping` | **Diferido — S, docs.** Anotado en 034 (Maintenance). Documentar los dos carriles de extracción y la degradación de `autoridades_electas` sin scrapling. |
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

## Columnas de estado

- `TODO` — pendiente de ejecución
- `IN PROGRESS` — en ejecución activa
- `DONE` — completado
- `BLOCKED` — bloqueado (indicar por qué)
- `BACKLOG` — diferido a backlog (ver `docs/backlog/`)
- `SKIP` — descartado después de análisis adicional
