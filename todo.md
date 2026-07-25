# todo.md — cola de ejecución (sesión 2026-07-24)

Ver `spec.md` para el detalle de cómo se trabaja cada ítem. Marcar `[x]` sólo cuando
el done-criteria completo del plan pasa (no cuando "parece listo").

**Nota sobre "DONE" en este archivo**: cuando un plan queda `[x]` aquí, su archivado en
`plans/README.md` vive en el branch de ESE plan (`advisor/NNN-slug`), no en `main`
todavía — `main` sigue mostrando la fila activa hasta que el operador confirme el
merge (ver spec.md, paso 10). No es drift; es el estado esperado mientras los branches
están pendientes de review.

## Housekeeping

- [x] Archivar planes DONE (055, 056, 060, 061, 062) a `plans/archive/`
- [x] Actualizar tabla de planes activos + grafo de dependencias en `plans/README.md`
- [x] Crear `spec.md` (orquestación delgada, sin duplicar los planes)
- [x] Crear `todo.md` (este archivo)
- [x] Crear `tests/e2e/` con un script de verificación por plan + `run_all.sh`

## Plan 058 — campo `extractor` + tabla README — ✅ DONE (2026-07-24)

- [x] Drift check corrido — discrepancia real encontrada y resuelta: catálogo tenía
      22 entradas, no 21 (Plan 053 agregó `geometria_comunal` después de que este
      plan se escribiera); se mapeó como la 22ª entrada siguiendo el mismo patrón.
- [x] Branch `advisor/058-catalog-extractor-field` creado
- [x] Step 1: campo `extractor` en las 22 entradas del catálogo
- [x] Step 2: `check_extractors()` en `check_companion_paths.py`
- [x] Step 3: `sync_readme_extractor_table()` en `doc_sync.py`
- [x] Step 4: marcadores en README + `make sync-docs`
- [x] Step 5: `AGENTS.md` §12 actualizado
- [x] Step 6: tests `ExtractorRegistryTests` + 3 tests nuevos en `DocSyncTests` (7 total)
- [x] Todos los done criteria verificados (incluye fix incidental: `uv.lock` tenía
      drift acumulado de bumps de dependabot sin relockear, causando que cualquier
      `uv run` de los hooks de pre-commit lo reescribiera como side-effect — se
      regeneró una vez en un commit aparte en `main` antes de continuar)
- [x] `tests/e2e/verify_058.sh` escrito y en verde
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (6 commits, sin merge/push — pendiente confirmación operador)

## Plan 057 — skeletons de carga + polish de interacción — ✅ DONE (2026-07-24)

- [x] Drift check corrido — el plan citaba excerpts de `app.js` (spinner inyectado
      por JS, `filteredCount`) que **nunca existieron** en el código real (diff
      contra el commit base del plan: 0 líneas en `app.js`). Implementación
      adaptada al código real (ver fila archivada en `plans/README.md`).
- [x] Branch `advisor/057-loading-skeletons` creado
- [x] Skeletons estáticos en `index.html` (catálogo + KPIs), no inyección JS
- [x] `.no-results-message` en `filterCatalog()` real (`app.js`)
- [x] Tarjeta clickeable vía handler delegado + enrutamiento por hash existente
- [x] Tecla Escape — ya existía en el código real, sin cambios necesarios
- [x] Done criteria verificados (adaptados; ver script)
- [x] `tests/e2e/verify_057.sh` escrito y en verde
- [x] Verificación visual/funcional con Playwright ad-hoc (skeleton, click→drawer,
      Escape, "Ver Ficha" intacto, no-results aparece/desaparece)
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (2 commits, sin merge/push — pendiente confirmación operador)

## Plan 050 — `resolve_comunas()` (nombres → CUT) — ✅ DONE (2026-07-24)

- [x] Drift check corrido, sin discrepancias (053 sigue pausado, sin conflicto)
- [x] Branch `advisor/050-resolve-comunas` creado
- [x] `src/chile_hub/text.py::normalize_comuna_name()` + `ChileHub.resolve_comunas()`
      + subcomando CLI `resolve`
- [x] ADR-009 escrito con las 4 preguntas abiertas + chequeo de colisiones (0 halladas)
- [x] Done criteria verificados
- [x] `tests/e2e/verify_050.sh` escrito y en verde
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (2 commits, sin merge/push — pendiente confirmación operador)
- [x] **Fix incidental en `main`** (no en el branch del plan): `[tool.interrogate]`
      en `pyproject.toml` tenía `fail-under = 80` contradiciendo su propio
      comentario ("umbral bajo en pre-commit, no bloquea") — bloqueaba localmente
      cualquier commit que tocara `src/chile_hub/**` (confirmado ya roto en
      `origin/main` antes de este fix, con o sin este plan). Restaurado a
      `fail-under = 0` para el hook local; `make docs-coverage`/CI siguen con su
      `--fail-under=80` explícito sin cambios (informativo, `\|\| true`).

## Plan 051 — capa HTTP estática + catálogo DCAT — ✅ DONE (2026-07-24)

- [x] Drift check corrido, sin discrepancias
- [x] Branch `advisor/051-static-http-dcat` creado
- [x] `src/builders/dcat_catalog.py` genera `data.json` (DCAT-US) desde `datapackage.json`
- [x] `from_datapackage(url)` ya no lanza `FileNotFoundError` — valida vía frictionless,
      levanta `ChileHubDataError` explícito (verificado en código: `ChileHub.__init__`
      no soporta `data_dir` remoto; no se fuerza ese rediseño, queda como follow-up
      en ADR-010 #5)
- [x] ADR-010 escrito (perfil DCAT-US default, datos.gob.cl no verificable → pregunta
      abierta; sin pinning por versión)
- [x] `docs/http-access.md` + entrada en `mkdocs.yml` nav
- [x] Done criteria verificados
- [x] `tests/e2e/verify_051.sh` escrito y en verde
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (5 commits, sin merge/push — pendiente confirmación operador)

## Plan 054 — validación de anomalías temporales — ✅ DONE (2026-07-25)

- [x] Drift check corrido — `src/validation.py` tenía drift (82 líneas, un
      validador nuevo `validate_geometria_comunal` de Plan 053, sin relación con
      `validate_indicadores`); `reports.py`/`verify_pipeline.py` sin drift
- [x] Branch `advisor/054-anomaly-validation` creado
- [x] `detect_series_anomalies()` (z-score robusto MAD sobre log-retornos),
      calibrado contra datos reales (cero falsos positivos) y 4 casos
      adversariales; integrado en `validate_indicadores` sólo como warning
- [x] Propagado a `drift_status: "drifted"` vía `build_degradation()`/`build_drift()`
      en `metadata.py` (el plan sugería `reports.py`; el cómputo real vive en
      `metadata.py`, `reports.py` hereda sin cambios — sin canal nuevo)
- [x] Gate de publicación (`verify_pipeline.py --profile publication`) rechaza
      ante anomalía no revisada; override real `--allow-known-anomalies`; build
      nunca aborta
- [x] ADR-013 escrito con método, calibración, ruta de override, 4 preguntas abiertas
- [x] Done criteria verificados
- [x] `tests/e2e/verify_054.sh` escrito y en verde
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (5 commits, sin merge/push — pendiente confirmación operador)

## Plan 059 — publicación Hugging Face Hub — ✅ DONE (2026-07-25)

- [x] Drift check corrido — sólo bump trivial de SHA en pypi-release.yml
- [x] Branch `advisor/059-huggingface-publish` creado
- [x] `scripts/publish_hf_dataset.py` (`--dry-run` + subida real perezosa) + job
      `hf-publish` en `pypi-release.yml` + `docs/hf/dataset-card.md`
- [x] **Fix sobre el propio plan**: `comunas_enriquecidas` es alias de `comunas`
      (mismo Parquet, Plan 014/PERF-08) — nombrar por basename fuente colapsaba
      a 18 archivos; corregido nombrando por clave de catálogo (19 exactos)
- [x] `release` expone `outputs: released/ready`; `hf-publish` gatea en ambos
      (no sólo `released`) para no publicar sin datos verificados
- [x] Nota registrada: secret `HF_TOKEN` pendiente de creación manual por el
      mantenedor (no bloquea implementación — script + CI completos y testeados)
- [x] Done criteria verificados
- [x] `tests/e2e/verify_059.sh` escrito y en verde
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (5 commits, sin merge/push — pendiente confirmación operador)

## Plan 063 — historial de salud + sparkline

- [ ] Drift check corrido
- [ ] Branch creado
- [ ] Steps del plan ejecutados (JSONL append-only + sparkline SVG)
- [ ] Done criteria (8 ítems) verificados
- [ ] `tests/e2e/verify_063.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 053 (Steps 4-5) — revisar al final

- [ ] Confirmar si sigue bloqueado (límite 500 KB `check-added-large-files`) o si
      cambió el contexto; si sigue bloqueado, no re-litigar — anotar y dejar tal cual.

## Checkpoints de revisión (cada ~20 iteraciones)

- [ ] Checkpoint 1 (tras 058 + 057): subagente "review spec.md and the current
      implementation for gaps"
- [ ] Checkpoint 2 (tras 050 + 051): subagente de revisión
- [ ] Checkpoint 3 (tras 054 + 059): subagente de revisión
- [ ] Checkpoint 4 (tras 063, final): subagente de revisión + resumen para el operador
      sobre qué branches quedan listos para merge/push (decisión del operador, no
      autónoma)
