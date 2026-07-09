# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commits `ba2f434` (2026-06-13), `a2cd288` (2026-06-19) y `c486e7c` (2026-07-07), y por `/improve plan` (mejoras de librerías/dependencias) en commit `140c8ea` (2026-06-29).

> **Última auditoría `/improve deep` (2026-07-07, commit `c486e7c`)**: planes **024–041**.
> Repo maduro; los grandes ítems previos ya están hechos. Lo restante es una cola de
> defectos pequeños de alta confianza (024–031; 027–031 DONE ✅), higiene de deps/CI (033 DONE ✅; 032 y 034 DONE ✅), backfill
> de tests del gate de publicación y los writers (035–036), dos refactors (037–038) y
> tres planes de diseño (039–041). Ver "Hallazgos considerados y diferidos (2026-07-07)".

> **Reevaluación de vigencia (2026-07-09)**: entre `c486e7c` y `HEAD` (`c1aa3e9`) hubo 45 commits,
> la mayoría fixes reactivos a bugs reales encontrados persiguiendo Pipeline Check #270 (cadena
> `4ebca99`…`354ad6e`, más `3f968ab`/`57e6eaf`/`9b85a23`/`df0999e`), no ejecuciones deliberadas de
> estos planes. Se revisó cada plan activo con su propio "drift check" contra `c486e7c`. Resultado:
> **034 quedó DONE de rebote** (el fix reactivo `4ebca99` corrigió exactamente el `--group dev` →
> `--extra pipeline --extra dev` que el plan pedía) y se archivó. **039 quedó resuelto en sustancia**
> para los 3 datasets (ver su fila) pero sigue `TODO` porque falta el ADR formal. **Todos los demás
> planes activos (027–033, 035–038, 040–041) siguen 100% vigentes** — se verificó línea por línea que
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

## Planes activos

| # | Plan | Prioridad | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|----------|--------|-----------|--------|
| 035 | [Tests de caracterización del gate `verify_pipeline`](035-characterization-tests-publish-gate.md) | P2 | L | LOW | — | DONE — `scripts` en coverage.source (pyproject.toml:170), `tests/test_verify_pipeline.py` con 26 tests (14 golden + 4 corruption + 6 synthetic + 1 main smoke + 1 readiness), `validate_puntos_interes` con 4 tests en `test_validation.py`, cobertura de `verify_pipeline.py` subió de ~0% a 64%. |
| 036 | [Tests golden de writers de artefactos](036-golden-output-tests-artifact-writers.md) | P2 | M | LOW | — (030 DONE) | TODO |
| 038 | [Deduplica `pipeline_status_utils.py`](038-deduplicate-pipeline-status-utils.md) | P3 | M | MED | — | TODO — riesgo confirmado en vivo: entre `c486e7c` y `HEAD` ambas copias (`src/pipeline_status_utils.py` y `src/chile_hub/pipeline_status_utils.py`) recibieron el mismo parche de 54 líneas a mano dos veces (siguen siendo byte-idénticas por ahora, pero es exactamente el modo de fallo que el plan anticipa). |
| 039 | [Diseño: resuelve capas comunales 3/346 en el bundle](039-design-resolve-sparse-comunal-layers.md) | P2 | S (era M) | LOW (era MED) | — (024 y 034 DONE) | TODO — **resuelto en sustancia por fixes reactivos, falta el ADR formal.** `consumo_electrico_comunal`: RE-CARRIL ya implementado (`57e6eaf`, fuente confirmada muerta permanentemente, `maturity_status="deprecated"`/`candidate`, fuera del bundle). `pobreza_comunal`: FILL ya en código (`3f968ab` corrigió el mapeo de columnas del XLSX real de MDS; producirá 345 comunas × 2 = 690 filas en el próximo extract en vivo — la causa raíz no era la que suponía el plan). `finanzas_municipales`: FILL ya logrado (scrape mensual corriendo tras 034; snapshot comprometido con 345/346 municipios). Trabajo restante: escribir `docs/adr/NNN-comunal-coverage-decision.md` documentando estas 3 decisiones ya tomadas, y confirmar que el próximo build recoge el `pobreza_comunal` real (no requiere código nuevo). |
| 040 | [Diseño: superficie SQL `hub.sql()` sobre Parquet](040-design-hub-sql-query-surface.md) | P2 | S-M | LOW | — (032 DONE) | TODO |
| 041 | [Diseño: import/validate de `datapackage.json`](041-design-datapackage-import-validate.md) | P3 | S | LOW | — | TODO |
| 023 | [Datasets `autoridades_electas` y `partidos_politicos`](023-autoridades-electas-partidos-politicos.md) | P2 | M-L | MED | — (deriva de Plan 022 · Ola B2.2, research cerrada) | 🔶 Ola A y B `stable_publishable` y en el bundle público (2026-07-06): `partidos_politicos` (36, 15 con estado_legal/fecha vía SERVEL) y `autoridades_electas` (diputados+senadores, 205, senadores con codigo_region/periodo completos). `autoridades_locales` (gobernadores+alcaldes, 240, CC-BY-SA segregado) queda `candidate` — cobertura de alcaldes insuficiente a criterio del operador, pendiente mejorar el extractor. No se archiva hasta resolver ese follow-up. |
| 020 | [Explorador SQL en la landing con DuckDB-Wasm](020-duckdb-wasm-playground.md) | P2 | M | MED | — | BLOCKED — gate 4.3: NO-GO (2026-06-30). Ver `docs/gate-4-3-decision-playground.md` para condiciones de re-evaluación. |

## Planes archivados (auditoría 2026-07-07)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 037 | [Vectoriza DV de RUT + elimina `rutificador`](archive/037-vectorize-rut-validation.md) | M | MED | DONE — ejecutado en `advisor/037-vectorize-rut` commit `6062f45`; `_expected_dv_vectorized` reemplaza `map_elements` con Polars vectorizado, `rutificador` eliminado de `pyproject.toml`, 95 tests pasan + 1 skipped (equivalencia con `importorskip`), lint y format-check OK. |
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
  032 (DONE) → 040           (040 ya sabe que duckdb va en extra pipeline)
  — (030 DONE) → 036            (036 puede afirmar el guard de Excel de 030)
  033 (DONE) → —                 (CI ya bloquea mypy/bandit/pip-audit en cada push/PR)
  035 038 041                    (independientes; 032, 033 y 034 quedaron DONE)
  039                           (024 y 034 DONE; ya solo falta escribir el ADR — ver su fila)

Planes previos:
  023 (independiente)  ← autoridades_electas + partidos_politicos; queda abierto por autoridades_locales
  020 (independiente)  ← bloqueado por gate 4.3 (no-go 2026-06-30). DIR-01/Plan 040 es su hermano no-bloqueado
```

**Interacciones clave de la auditoría 2026-07-07:** **026** (regenerar lock), **032** (adelgazar deps),
**033** (mypy/bandit/pip-audit en CI) y **037** (vectorizar RUT, eliminar `rutificador`) quedaron DONE.
La ola de higiene deps/CI está completa 🎉.
**040** ya sabe que `duckdb` va en el extra `pipeline`. **039** solo necesita el ADR retroactivo.
**020** sigue bloqueado (gate 4.3 NO-GO).

## Orden de ejecución recomendado

**Auditoría 2026-07-07 (024–041) — orden sugerido por olas (actualizado 2026-07-09; 024, 025, 026, 032, 033 y
034 ya están DONE/archivados, no aparecen abajo):**

1. **Ola de fixes P2, un archivo cada uno, sin dependencias entre sí** — **COMPLETA** 🎉
   (027, 028, 029, 030 y 031 DONE — archivados).
2. **Higiene de deps/CI** — **COMPLETA** 🎉 (032, 033 y 034 DONE).
3. **Backfill de tests**: **035** (gate de publicación — baseline de verificación) → **036** (writers).
   035 primero porque es la red de seguridad que los refactors de la ola siguiente deberían tener antes
   de tocar código de build.
4. **Refactors**: **037** ✅ DONE (vectoriza RUT) y **038**
   (dedup `pipeline_status_utils.py`; MED por el acoplamiento `__init__ → core`). Sin orden estricto
   entre ambos.
5. **Diseño/spikes**: **039** (024 y 034 ya DONE — el spike se reduce a redactar el ADR retroactivo,
   es el más rápido de cerrar de los tres) → **040** (coordinar con 032) → **041**.

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
| 036 | ninguno | Vigente, sin cambios. |
| 037 | `pyproject.toml` (solo bump de versión) | Vigente; `rutificador` sigue importado vía `map_elements`. |
| 038 | ambas copias +54 líneas cada una (edición manual paralela) | Vigente; se confirmó que siguen byte-idénticas, pero el riesgo que el plan describe se ejercitó en vivo. |
| 039 | `source_registry.json`/`dataset_catalog.json` reescritos | **Sustancialmente resuelto**, sigue `TODO` solo para el ADR — ver nota en el archivo del plan y su fila arriba. |
| 040 | `README.md` +53/-13 (sección DuckDB, no la API) | Vigente, sin cambios en `core.py`. |
| 041 | `pyproject.toml` (solo bump de versión) | Vigente, sin cambios. |
| 023 | sin diff en extractores relevantes | Sin cambios; la nota granular existente en su fila sigue siendo precisa. |
| 020 | sin diff | Sin cambios; sigue BLOCKED por el gate 4.3. |

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
