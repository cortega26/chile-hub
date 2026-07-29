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

## Plan 063 — historial de salud + sparkline ✅ DONE (2026-07-25)

- [x] Drift check corrido
- [x] Branch creado (`advisor/063-hub-health-history`)
- [x] Steps del plan ejecutados (JSONL append-only + sparkline SVG)
- [x] Done criteria (8 ítems) verificados
- [x] `tests/e2e/verify_063.sh` escrito y en verde — con excepción deliberada:
      no revierte `index.html` (contiene markup/CSS a mano, no sólo build noise)
- [x] Fila de `plans/README.md` actualizada a DONE y archivada
- [x] Commits en el branch (5 commits: mecanismo backend, sparkline landing,
      tests, docs, chore de sync JSON-LD; sin merge/push — pendiente
      confirmación operador)
- Hallazgos corregidos durante la implementación: `.gitignore` no re-incluía
  `*.jsonl` bajo `data/normalized/*` (habría quedado gitignoreado para
  siempre); `hub_health_history.jsonl` no aparecía en `artifact_manifest.json`
  por `PUBLISHABLE_ARTIFACT_SUFFIXES` + `shared_artifacts` incompletos.
- Incidente autocausado y autocorregido: el primer borrador de
  `verify_063.sh` reusaba `git checkout -- ... index.html` de otros planes y
  borró los cambios a mano del sparkline una vez; recuperados manualmente y
  corregido el script para excluir `index.html` de su limpieza.

## Plan 053 (Steps 4-5) — revisar al final

- [x] Confirmado (2026-07-25): sigue bloqueado. `.pre-commit-config.yaml:11` aún
      tiene `--maxkb=500`, sin cambios desde que se escribió la fila de
      `plans/README.md`. No hay contexto nuevo que ameritara re-litigar — se
      deja tal cual, pendiente de decisión del mantenedor (subir el límite o
      workflow de CI dedicado, como `empresas.parquet`).

## Checkpoints de revisión (cada ~20 iteraciones)

- [x] Checkpoint 1 (tras 058 + 057) — hallazgos: afirmación incorrecta en spec.md
      sobre que los scripts e2e nunca escriben archivos (corregida), conflicto de
      merge esperado documentado, stash redundante descartado.
- [x] Checkpoint 2 (tras 050 + 051) — hallazgo real: `.strip()` en
      `normalize_comuna_name` divergía silenciosamente de la cadena Polars del
      extractor (documentado + test adversarial agregado); typo aritmético en
      fila de plan 051 corregido.
- [x] Checkpoint 3 (tras 054 + 059) — 2 hallazgos medium arreglados en código:
      condición de carrera en la resolución de `run_id` de `hf-publish` (ahora
      reusa el output de `release` en vez de re-resolver), y la precedencia
      fallback-vs-anomalía en `build_degradation()` (intencional, ahora
      documentada + testeada). 2 hallazgos low arreglados: `KeyError` sin
      contexto en `select_publishable_files()`, y blind spot del test de
      guardrail para el estilo YAML de lista de bloque en `needs:`.
- [x] Checkpoint 4 (tras 063, final) — revisión de los 7 branches
      (050/051/054/057/058/059/063) uno por uno: `git diff` de tres puntos contra
      su base, `tests/e2e/verify_0NN.sh` corrido en cada checkout, árbol limpio
      después de cada uno. **Los 7 quedan READY** — ningún hallazgo bloqueante,
      sin violaciones de las 5 reglas de `CLAUDE.md`, sin código de debug ni
      TODOs sueltos. Corrección de premisa del subagente: los 7 branches NO
      comparten un único merge-base (cada uno partió de `main` justo después
      del commit de `todo.md` del plan anterior) — benigno, pero significa que
      los diffs de tres puntos son correctos "a la punta de cada branch", no
      "post-merge". Único caveat no bloqueante: la cobertura de 057 en
      `verify_057.sh` es por grep de presencia de clases CSS/JS, no un test
      real de comportamiento — el chequeo Playwright fue manual, no repetible.
      Notas de orden de merge / conflictos esperados (todos triviales de
      resolver, ninguno de lógica): `plans/README.md` (los 7 branches),
      `tests/test_pipeline_logic.py` (050/051/054/058/063 agregan clases antes
      del `if __name__`), `README.md` (050/051/054/058/059/063 — badges/conteos,
      correr `make sync-docs` tras cada merge en vez de resolver a mano),
      `index.html`/`app.js` (057 + 063, secciones distintas), `AGENTS.md`
      (058/059/063), `core.py` (050/051, métodos distintos),
      `build_dev_db.py` (051/063, líneas distintas). Orden sugerido
      (menor → mayor conflicto): 050 → 058 → 059 → 054 → 051 → 057 → 063.

## Plan 066 — taxonomía drift esperado vs real (2026-07-28)

- [x] Cola previa (050/051/054/057/058/059/063) mergeada a `main` en el orden de
      Checkpoint 4, con `make sync-docs` tras cada merge; hallazgo real: la
      resolución del merge de 059 dejó una fila activa duplicada de 059 en
      `plans/README.md` (corregida) — el resto de las 7 filas se auditó una por
      una (`active=0 archived=1 file=1` en las 7).
- [x] Step 0: baseline reproducido `19 8 7 warn` con los 8 datasets esperados
      **antes** de tocar código.
- [x] Steps 1-4: `NON_FALLBACK_SOURCE_MODES` como fuente única, `coverage.expected`
      desde `coverage_policy`, `expected_warnings` declarados en el emisor,
      `build_drift` nombra sólo la condición que dispara el drift.
- [x] Step 5: landing (badge por accionables + píldora `partial esperada`),
      ADR-014, `docs/datasets/` de los 5 reclasificados, `docs/backlog/05`.
- [x] Step 6: issues #42/#43/#44 abiertos con autorización explícita del operador.
- [x] `tests/e2e/verify_066.sh` en verde; 779 tests + 1 skip; `pre-commit
      run --all-files` limpio salvo un hallazgo **preexistente en `main`** y fuera
      de alcance: `data/staging/finanzas_municipales.metadata.json` no termina en
      newline (viene del commit de CI `c8c7c70`), así que `end-of-file-fixer`
      falla también sin mis cambios — no se tocó.
- [x] Desviación: el plan pedía ADR-013, pero el Plan 054 lo tomó al mergearse;
      el entregable es ADR-014. Registrada en el propio plan y en su fila.

## Issues #42 / #43 / #44 — cierre (2026-07-29)

- [x] **#42 empresas** — el issue decía "1 RUT inválido"; eran 3 warnings y sólo
      uno era dato: el casing de `codigo_sociedad` era un bug del validador
      (`SOCIEDAD_MAP` escribe "SpA" a propósito) y la nota de cobertura RES es
      alcance de diseño → declarada esperada (ADR-014). El RUT `"0"` es un
      centinela de la fuente: se descarta con regla nombrada y conteo auditable.
      **Efecto diferido**: el warning del RUT persiste en los artefactos hasta la
      próxima extracción real (el fix vive en el extractor, y `make build` no
      re-extrae).
- [x] **#44 consumo_electrico_comunal** — Plan 068 + ADR-015. Estado `retired`
      derivado del registry; contadores sobre el conjunto activo. Alcance
      decidido por el mantenedor: NO se toca la superficie pública (habría sido
      BREAKING CHANGE con 2.0.0 forzado).
- [x] **#43 indicadores** — Plan 067 + ADR-016. El issue subestimaba el problema:
      `ipc` lleva 240 días sin dato nuevo y el backfill lo re-publicaba en cada
      build. Se cerró el modo de falla (gate override-able por edad), no la
      serie: el diagnóstico upstream necesita red y sigue abierto en el issue.
- [x] Hallazgo ajeno al trabajo: `uv.lock` estaba desincronizado en `main` por
      los PRs #37/#38 de dependabot (bumpearon `pyproject.toml` sin regenerar el
      lock) → el gate `uv lock --locked` del Plan 026 fallaba en CI. Corregido.
- [x] Hallazgo preexistente NO corregido (fuera de alcance):
      `data/staging/finanzas_municipales.metadata.json` y el snapshot xlsx de
      `data/raw/` no terminan en newline, así que `end-of-file-fixer` falla
      también sin ningún cambio mío. `data/raw/` es solo-append por la regla #3.
