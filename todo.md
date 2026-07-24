# todo.md — cola de ejecución (sesión 2026-07-24)

Ver `spec.md` para el detalle de cómo se trabaja cada ítem. Marcar `[x]` sólo cuando
el done-criteria completo del plan pasa (no cuando "parece listo").

## Housekeeping

- [x] Archivar planes DONE (055, 056, 060, 061, 062) a `plans/archive/`
- [x] Actualizar tabla de planes activos + grafo de dependencias en `plans/README.md`
- [x] Crear `spec.md` (orquestación delgada, sin duplicar los planes)
- [x] Crear `todo.md` (este archivo)
- [ ] Crear `tests/e2e/` con un script de verificación por plan + `run_all.sh`

## Plan 058 — campo `extractor` + tabla README

- [ ] Drift check corrido, sin discrepancias
- [ ] Branch `advisor/058-catalog-extractor-field` creado
- [ ] Step 1: campo `extractor` en las 21 entradas del catálogo
- [ ] Step 2: `check_extractors()` en `check_companion_paths.py`
- [ ] Step 3: `sync_readme_extractor_table()` en `doc_sync.py`
- [ ] Step 4: marcadores en README + `make sync-docs`
- [ ] Step 5: `AGENTS.md` §12 actualizado
- [ ] Step 6: tests `ExtractorRegistryAndReadmeTableTests`
- [ ] Todos los done criteria (9 ítems) verificados
- [ ] `tests/e2e/verify_058.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 057 — skeletons de carga + polish de interacción

- [ ] Drift check corrido
- [ ] Branch `advisor/057-loading-skeletons` creado
- [ ] Steps del plan ejecutados (leer plan completo antes de empezar)
- [ ] Done criteria (12 ítems) verificados
- [ ] `tests/e2e/verify_057.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 050 — `resolve_comunas()` (nombres → CUT)

- [ ] Drift check corrido (ojo: solapa con 053 en core.py/subdere_extractor.py — confirmar que 053 sigue pausado)
- [ ] Branch creado
- [ ] Steps del plan ejecutados
- [ ] ADR-009 escrito con preguntas abiertas
- [ ] Done criteria (9 ítems) verificados
- [ ] `tests/e2e/verify_050.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 051 — capa HTTP estática + catálogo DCAT

- [ ] Drift check corrido
- [ ] Branch creado
- [ ] Steps del plan ejecutados
- [ ] ADR-010 escrito
- [ ] Fix `from_datapackage(url)` incluido
- [ ] Done criteria (8 ítems) verificados
- [ ] `tests/e2e/verify_051.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 054 — validación de anomalías temporales

- [ ] Drift check corrido
- [ ] Branch creado
- [ ] Steps del plan ejecutados (warn + drift flag, nunca SystemExit)
- [ ] ADR-013 escrito
- [ ] Done criteria (10 ítems) verificados
- [ ] `tests/e2e/verify_054.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

## Plan 059 — publicación Hugging Face Hub

- [ ] Drift check corrido
- [ ] Branch creado
- [ ] Steps del plan ejecutados (script --dry-run, job CI, dataset card)
- [ ] Nota registrada: secret `HF_TOKEN` pendiente de creación manual por el mantenedor (no bloquea implementación)
- [ ] Done criteria (9 ítems) verificados
- [ ] `tests/e2e/verify_059.sh` escrito y en verde
- [ ] Fila de `plans/README.md` actualizada a DONE
- [ ] Commit(s) en el branch

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
