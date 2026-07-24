# spec.md — Ejecución de la cola de planes activos (sesión 2026-07-24)

> Este archivo es una capa de orquestación **delgada** sobre `plans/`. No duplica el
> detalle de cada plan — cada `plans/NNN-*.md` ya es su propia spec completa (contexto,
> steps, test plan, done criteria, STOP conditions). Este archivo solo fija: qué política
> de archivado sigo, en qué orden ejecuto la cola, y cómo verifico cada entrega antes de
> pasar a la siguiente.

## Goal

1. Mantener `plans/README.md` sincronizado con la realidad: todo plan `DONE` se archiva
   de inmediato (política ya escrita en el propio README, líneas 68-90 — este archivo
   solo la hace cumplir, no la reemplaza).
2. Implementar, uno por uno y de forma secuencial (no en paralelo, no delegado a
   subagentes de ejecución), los planes activos restantes, en el orden fijado abajo.
3. Cada plan se ejecuta exactamente como su propio `.md` lo especifica: mismo branch,
   mismos commits convencionales, mismo scope, mismos done criteria. Este spec no
   introduce alcance nuevo sobre ningún plan.

## Política de archivado (ya vigente, solo se aplica)

Cuando un plan pasa a `DONE`:
1. `git mv plans/NNN-*.md plans/archive/`.
2. Actualizar el link en la tabla de "Planes activos" → mover la fila completa a una
   sección "Planes archivados (fecha)", apuntando al nuevo path `archive/NNN-*.md`.
3. Borrar la fila de la tabla activa.
4. Verificar que el grafo de dependencias y el "Orden de ejecución recomendado" del
   README sigan siendo coherentes; anotar un update breve si no.

## Cola de ejecución esta sesión

Orden elegido (ver razonamiento en `plans/README.md` líneas 303-391 — "Actualización
2026-07-24" — y confirmado con el advisor): fully-unblocked primero, en orden de riesgo
creciente; los dos ítems con dependencia externa real (secret de mantenedor / decisión
de límite de CI) se anotan pero no bloquean el resto de la cola.

| Orden | Plan | Por qué este lugar en la cola |
|---|---|---|
| 1 | **058** — campo `extractor` + tabla README | Disjunto de todo, LOW risk, cierra hueco de `AGENTS.md §12`. |
| 2 | **057** — skeletons landing | Disjunto, LOW risk, cierra el carril B (055/056 ya DONE). |
| 3 | **050** — `resolve_comunas()` | Solapa archivos con 053 (`core.py`, `subdere_extractor.py`) pero 053 está pausado (Steps 0-3 mergeados, 4-5 diferidos) — seguro correr ahora. Spike con ADR-009. |
| 4 | **051** — capa HTTP estática + DCAT | Spike con ADR-010; absorbe fix de `from_datapackage(url)`. |
| 5 | **054** — validación de anomalías temporales | Foso de confianza; ADR-013. Sin dependencia dura, pero sigue en el orden original tras 053/050/051. |
| 6 | **059** — publicación Hugging Face Hub | Implementable completo (script + dry-run + workflow + tests) sin que el secret `HF_TOKEN` exista todavía — el secret sólo lo necesita la **ejecución real** del job en CI, no la implementación. Se anota como nota operativa, no bloqueante. |
| 7 | **063** — historial de salud + sparkline | Después de 054 (consume sus flags de drift) y después de que el carril B (057) haya cerrado (comparten `index.html`/`app.js`). |
| — | **053 Steps 4-5** (`resolve_by_coords()` + CI wiring) | **Diferido explícitamente** (ya registrado en `plans/README.md`): el artefacto GeoParquet excede el límite de 500 KB de `check-added-large-files`. Requiere decisión del mantenedor (subir el límite o CI dedicado). Se revisita solo si el resto de la cola se completa y no hay novedad; no se re-pregunta en cada iteración. |

## Cómo trabajo cada plan (idéntico para los 7)

1. Leer el `.md` completo del plan otra vez inmediatamente antes de empezar (por si
   hubo drift desde que se armó esta cola).
2. Correr el "Drift check" que el propio plan trae en su cabecera. Si hay discrepancia
   con "Estado actual", tratarlo como STOP y reportar — no improvisar alcance nuevo.
3. Crear el branch indicado en "Git workflow" del plan (patrón `advisor/NNN-slug`).
4. Ejecutar los "Steps" del plan en orden, corriendo el comando "Verify" de cada uno
   antes de avanzar.
5. Escribir/actualizar los tests que el plan pide en su "Test plan".
6. Correr los "Done criteria" del plan uno por uno; todos deben cumplirse.
7. Correr el script de verificación de esta cola: `tests/e2e/verify_NNN.sh` (ver
   sección Verification abajo) — reproduce los done criteria de forma no interactiva
   para que se pueda re-correr sin releer el plan.
8. Commit(s) en el branch, mensajes convencionales en español (o inglés si el plan usa
   inglés en sus ejemplos — seguir la convención del plan, no inventar una nueva).
9. Actualizar la fila de estado del plan en `plans/README.md` (a `DONE` con el resumen
   de qué se hizo, igual que las filas archivadas existentes).
10. **No hacer merge a `main` ni push a `origin` sin confirmación explícita del
    operador.** El branch queda listo para review; se batchea la confirmación de
    merge/push en checkpoints, no plan por plan (evita interrumpir el flujo por algo
    que no cambia de respuesta). **Conflicto esperado al mergear**: como cada branch
    parte de `main` y cada uno archiva su propio plan en `plans/README.md`, dos
    branches que borran filas vecinas de la tabla "Planes activos" van a chocar ahí
    al mergear en secuencia (delete/delete adyacente) — es cosmético y se resuelve
    borrando ambas líneas; no es señal de un problema real.
11. Marcar el ítem correspondiente en `todo.md`.
12. Cada ~20 iteraciones (steps + fixes acumulados across planes), lanzar un subagente
    fresco con el prompt "review spec.md and the current implementation for gaps" y
    resolver su feedback antes de seguir.

## Verification (cómo pruebo cada pieza)

No se inventa un harness genérico nuevo: los "Done criteria" de cada plan **son** la
verificación, y ya usan los gates existentes del repo (`make doctor`, `make lint`,
`make format-check`, `make verify-landing`, `pytest`). `tests/e2e/` (nueva carpeta,
**no** colisiona con la suite pytest de `tests/*.py`) contiene un script de shell por
plan que re-ejecuta exactamente esos comandos de done-criteria de forma no interactiva,
más un `run_all.sh` que los corre todos en el orden de la cola. Uso:

```
tests/e2e/verify_058.sh   # sólo Plan 058
tests/e2e/run_all.sh      # todos los planes ya marcados DONE esta sesión, en orden
```

Cada script:
- Sale con el código de salida del primer comando que falle (`set -euo pipefail`).
- Imprime cada done-criterion y su resultado (no silencia salida).
- No toca git (ni commits, ni `main`, ni red/push) — pero **puede escribir archivos
  locales generados** cuando el propio done-criteria del plan lo pide (p. ej.
  `verify_058.sh` corre `make sync-docs`, que reescribe bloques delimitados de
  README.md/AGENTS.md si están desincronizados — igual que en CI). Esa escritura es
  intencional y reproduce el done-criteria tal cual está escrito en el plan, no un
  efecto secundario oculto.

Un plan se considera "verificado" cuando su script `verify_NNN.sh` sale con exit 0 en
el branch del plan, **y** `make doctor` sigue en exit 0 (regresión global).

## No-goals

- No se re-audita ni se re-decide el contenido de los planes 050/051/054/057/058/
  059/063 — ya están escritos y aprobados por auditorías previas.
- No se toca el alcance de 053 más allá de anotar su estado (su Step 4/5 quedan tal
  como el README ya los describe: diferidos).
- No se agregan datasets nuevos ni se reabre el anti-patrón #10 (fuera de alcance de
  toda esta cola).
- No se hace merge/push autónomo a `main`/`origin`.
