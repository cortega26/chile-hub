# Plan 150: Publicación parcial — publicar las capas sanas y retener las degradadas en su última versión buena

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3400c81..HEAD -- scripts/verify_pipeline.py src/build_dev_db.py src/builders/ src/chile_hub/pipeline_status_utils.py data/source_registry.json AGENTS.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M-L (6–10 h: build en dos fases, verificador, reportes, tests)
- **Risk**: MEDIUM-HIGH (toca el contrato de publicación, el bundle, el manifiesto y la superficie pública)
- **Depends on**: plan 147 (diagnóstico del 403 de SINCA: bloqueo a nivel IP, no fingerprint)
- **Category**: direction / reliability
- **Planned at**: commit `3400c810`, 2026-10-25

## Why this matters

Desde el 2026-10-16 el publish diario falla **once veces consecutivas** y los datos
están congelados al 2026-10-15. La causa no es un bug: es que la política de
publicación es **todo-o-nada**. Si *una* capa `stable_publishable` está en
`fallback`, se rechaza el build completo y las otras ~20 capas sanas no se
publican.

El estado actual, medido el 2026-10-25:

| Dataset | Causa | ¿Dato degradado? |
|:--|:--|:--|
| `establecimientos_educacionales` | `datosabiertos.mineduc.cl` caído ("sitio temporalmente fuera de servicio") | **No**: el fallback recupera el snapshot versionado, 12.898 filas, idéntico a lo publicado |
| `resultados_educacionales` | misma caída de MINEDUC | **Sí**: 3 filas curadas vs 345 publicadas (−99,1%) |
| `perfil_territorial_comunal` | derivado de los dos anteriores | **Sí**, por herencia |
| `calidad_aire` | 403 de SINCA al runner (bloqueo de IP; ver plan 147) | **Sí**: serie truncada, 2.244 vs 8.462 (−73,5%) |

El plan 147 ya cerró el diagnóstico de SINCA y dejó la decisión explícitamente
abierta: *"publish correctamente bloqueado por fail-loud hasta que SINCA
desbloquee o el mantenedor decida política"*. Este plan implementa esa política.

**Lo que NO cambia.** El invariante de `AGENTS.md` §4.2 —"nunca publicar datos
degradados"— se mantiene intacto. Lo que se acota es el **radio de impacto**: hoy
una capa degradada bloquea veinte; después, esa capa se retiene en su última
versión buena y marcada, y las demás avanzan. Ningún dato degradado llega al
bundle.

## Current state

Hechos leídos en el código y en el pipeline real (2026-10-25):

- `scripts/verify_pipeline.py:555` — `verify_publication_policy()` recorre
  `stable_publishable_dataset_names(registry)` y agrega una violación por cada
  dataset con `source_mode not in NON_FALLBACK_SOURCE_MODES`, `freshness != fresh`
  o `fallback_policy == "allowed_for_dev_blocked_for_publication"` con
  `source_mode == "fallback"`. Al final: `if violations: fail(...)`.
- `scripts/verify_pipeline.py:519` — `record_drop_violations()` compara
  `record_count_delta` de `dataset_changelog.json` contra
  `DEFAULT_MAX_RECORD_DROP_PCT = 20.0`, con override por
  `--allow-record-drop <dataset>`.
- `src/build_dev_db.py` — construye **todos** los artefactos de una pasada y
  escribe `data/normalized/`. No existe ningún concepto de "conservar el
  artefacto anterior".
- `data/source_registry.json` — 26 entradas con `publication_track`,
  `maturity_status`, `fallback_policy`, `public_bundle_eligible`.
- `src/chile_hub/pipeline_status_utils.py:91` — `_load_retired_datasets()` ya
  implementa el concepto vecino: `maturity_status == "deprecated"` excluye un
  dataset de los contadores de salud (ADR-015). **Es el precedente de diseño a
  imitar**, no a reutilizar: retirar es permanente, retener es temporal.
- `.github/workflows/pipeline-check.yml:357` — el perfil `publication` se usa en
  `schedule` o en `workflow_dispatch` con `publish=true`; en cualquier otro caso
  corre `readiness`.

## Scope

**In scope** (los únicos archivos que se deben modificar):

- `src/build_dev_db.py` y `src/builders/` — fase de retención y agregados.
- `scripts/verify_pipeline.py` — aceptar el estado `held` en el perfil `publication`.
- `src/chile_hub/pipeline_status_utils.py` — exponer `held_count` y el estado.
- `data/source_registry.json` — solo si hace falta un campo de configuración nuevo.
- `tests/test_pipeline_logic.py`, `tests/test_verify_pipeline.py` — casos nuevos.
- `AGENTS.md` §4.2 y §9 — precisar el alcance del invariante (de "todo el build
  falla" a "ningún dato degradado se publica").
- `docs/adr/ADR-025-publicacion-parcial.md` — decisión y alternativas descartadas.
- `plans/README.md` — fila de este plan.

**Out of scope** (NO tocar):

- `data/normalized/` a mano — se regenera, nunca se edita.
- La política de `candidate`: ese carril no participa.
- `AGENTS.md` §4.1, §4.3, §4.4, §4.5 y §10 — invariantes no relacionadas.
- `plans/110` y todo lo de sostenibilidad.
- La landing y `README.md`: desde el plan 109 no llevan datos del día, así que
  una publicación parcial **no** debe cambiar esos archivos. Si el diff los
  toca, es un STOP.

## Diseño propuesto

### Concepto

Un dataset `stable_publishable` puede estar en uno de tres estados por build:

| Estado | Condición | Qué se publica |
|:--|:--|:--|
| `fresh` | Cumple `source_mode`, frescura y umbral de `record_count` | Su artefacto nuevo |
| `held` | Incumple, **pero existe un artefacto publicado previo** | El artefacto previo, byte a byte, marcado |
| `unrecoverable` | Incumple y **no** hay artefacto previo | Nada: el build falla |

### Regla de escalamiento (anti-olvido)

Una retención no puede ser permanente ni silenciosa:

- Se registra `publication_hold.since_utc` (primera vez retenido, se arrastra
  entre builds) y `publication_hold.builds_held` (contador).
- A los **7 builds retenidos** (≈1 semana), el build **falla** con un mensaje que
  nombra el dataset y su causa. Eso convierte una degradación silenciosa en una
  decisión que alguien tiene que tomar.
- `held_count` se expone en `hub_health.json` y en `pipeline_status.md`.

Umbral justificado: el schedule es diario, así que 7 builds ≈ una semana, la
misma ventana que el issue automático de fallo de schedule.

### Flujo del build

1. **Snapshot previo.** Antes de escribir, copiar a un directorio temporal los
   artefactos por dataset de `data/normalized/` y el `dataset_catalog.json`
   previo.
2. **Clasificar.** Para cada `stable_publishable`: `fresh` / `held` /
   `unrecoverable`, con la misma lógica que hoy vive en el verificador (moverla
   a una función compartida en `src/builders/`, no duplicarla).
3. **Construir.** Los `fresh` se construyen normal.
4. **Retener.** Para cada `held`: restaurar `<dataset>.parquet` y `<dataset>.json`
   desde el snapshot, y sustituir su entrada de metadata por la previa más un
   bloque `publication_hold`.
5. **Reagregar.** Regenerar catálogo, manifiesto, changelog, calidad, salud y
   reportes **desde la metadata ya mezclada**.
6. **Fallar** si algún dataset es `unrecoverable` o si superó el umbral de retención.

### Verificador

`verify_publication_policy()` deja de emitir violación por un dataset `held` y en
su lugar:

- Falla si `held` sin `publication_hold.previous_generated_at_utc`.
- Falla si `held` sin `publication_hold.reason`.
- Falla si `builds_held > 7`.
- Falla si un `held` aparece en el manifiesto **sin** la marca `retained: true`.
- Reporta `Publication policy passed: N fresh, M held, K candidate excluded`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Baseline health | `make doctor` | declared | exit 0 |
| Lint + format | `make lint && make format-check` | declared | exit 0 |
| Build | `python src/build_dev_db.py` | declared | exit 0 |
| Verificación de publicación | `python scripts/verify_pipeline.py --profile publication` | declared | exit 0 con `M held` |
| Tests focalizados | `pytest tests/test_pipeline_logic.py tests/test_verify_pipeline.py -v` | declared | todos verdes |
| Reproducir un `held` | mover `data/staging/resultados_educacionales.metadata.json` a `source_mode=fallback` y reconstruir | propio | el dataset aparece `held`, el resto publica |

## Git workflow

- Branch: `advisor/150-publicacion-parcial`
- Un commit por unidad lógica; conventional commits (`feat(build): ...`,
  `test(verify): ...`, `docs(adr): ...`).
- No push ni PR sin instrucción explícita del operador.

## Steps

### Step 0: Baseline verde

- `make doctor` → exit 0. Si falla en el checkout sin modificar, **STOP**.
- `python scripts/verify_pipeline.py --profile readiness` → exit 0.
- Confirmar que `data/normalized/` está limpio (`git status --short`).

### Step 1: Extraer la clasificación a una función pura

Mover la lógica de "¿este dataset es publicable?" desde
`verify_publication_policy()` a `src/builders/publication_gate.py` (función pura,
sin I/O). El verificador y el build deben llamar a la **misma** función: dos
implementaciones divergen, y ese es justo el bug que este plan no debe introducir.

**Verificar**: `pytest tests/test_pipeline_logic.py -k publication -v` verde sin
cambios de comportamiento.

### Step 2: Fase de retención en el build

Implementar §"Flujo del build" pasos 1–5. La metadata retenida debe conservar
`record_count`, `fields` y `refreshed_at_utc` **del artefacto previo**, no del
nuevo.

**Verificar**: build sobre staging real produce 23 datasets, y los 3 de MINEDUC
aparecen `held` con `previous_generated_at_utc` igual al del snapshot publicado.

### Step 3: Verificador

Implementar §"Verificador" y el umbral de 7 builds.

**Verificar**: `--profile publication` sale 0 y reporta `M held`.
**Verificar**: quitar el artefacto previo de un `held` → falla con mensaje
explícito.

### Step 4: Reportes y superficie pública

`hub_health.json` gana `held_count`; `pipeline_status.md` y `dataset_catalog.md`
marcan el estado. `ChileHub.health()` lo expone sin romper el contrato actual
(campo nuevo, ningún campo eliminado).

**Verificar**: `pytest tests/test_chile_hub.py tests/test_core.py` — actualizar
solo las constantes que cambian por la publicación de 23 capas
(`EXPECTED_DATASET_COUNT` 22→23, `EXPECTED_BUILD_TOP_ISSUE` según el build real),
con el porqué en el commit.

### Step 5: Documentación

- `AGENTS.md` §4.2: precisar que el invariante es "ningún dato degradado se
  publica", y que la retención es el mecanismo cuando una capa no califica.
- `docs/adr/ADR-025-publicacion-parcial.md`: contexto, decisión, alternativas
  descartadas (a: esperar; c: mover a `candidate`), consecuencias y umbral de
  escalamiento.
- `plans/README.md`: fila `DONE` al terminar.

**Verificar**: `make doctor` → exit 0 (incluye `check_agents_sync`).

## Test plan

Casos nuevos, todos sin red y con staging sintético:

1. Un `stable_publishable` en fallback con artefacto previo → `held`, el resto
   `fresh`, verificador en 0.
2. El mismo, sin artefacto previo → `unrecoverable`, build falla.
3. `held` con `builds_held = 7` → build falla nombrando el dataset.
4. `held` presente en el manifiesto sin `retained: true` → verificador falla.
5. Regresión: un build sin ninguna degradación no produce ningún `held` y el
   catálogo es idéntico al de hoy (golden).
6. Regresión: `README.md`, `index.html` y `app.js` no cambian en un build con
   `held` (plan 109).

## Done criteria

- [ ] `make doctor` → exit 0; `make lint && make format-check` → exit 0.
- [ ] `pytest` completo verde, incluidos los 6 casos nuevos.
- [ ] `verify_pipeline.py --profile publication` sale 0 en un build con las 3
      capas de MINEDUC retenidas.
- [ ] `README.md`, `index.html`, `app.js` sin cambios en ese build.
- [ ] `hub_health.json` expone `held_count` y cada retenido su `publication_hold`.
- [ ] Ningún dataset `held` aparece sin marca de retención en el manifiesto ni en
      el bundle.
- [ ] `ADR-025` escrito y enlazado desde `AGENTS.md`.
- [ ] Rama con commits limpios; ningún push sin autorización.

## STOP conditions

Parar y reportar si:

- `make doctor` o `pytest` falla en el checkout sin modificar.
- La implementación exige publicar un dataset `held` sin artefacto previo.
- El diff toca `README.md`, `index.html` o `app.js` (rompería el contrato del
  plan 109).
- Un test de contrato de la API pública se rompe por un campo eliminado o
  renombrado (solo se admiten campos nuevos).
- Aparece la tentación de "arreglar" el umbral de 7 builds para que pase: es un
  STOP, no un ajuste.

## Maintenance notes

- **Deferred:** el arreglo de continuidad de `calidad_aire`. Su serie vive en
  `data/staging/`, que no está versionado; si la caché se pierde, la serie
  reinicia y el dataset queda `held` para siempre hasta que se recupere. Arreglo
  candidato: versionar `data/staging/calidad_aire.*` en git, como ya se hace con
  `precipitaciones_dgac` y `finanzas_municipales`. **No es opcional a medio
  plazo**: sin esto, este plan convierte una caída en una retención permanente.
- **Deferred:** notificación al mantenedor cuando `held_count > 0`. El issue
  automático de schedule sigue siendo la señal; ampliarlo es trabajo aparte.
- A reviewer should scrutinize: que el build no pueda emitir un `held` sin
  artefacto previo; que el bundle no incluya datos degradados; que el umbral de
  escalamiento no se relaje.
- Follow-up: alimentar el resultado en `ROADMAP.md §5` si la política cambia el
  estado del carril `stable_publishable`.
