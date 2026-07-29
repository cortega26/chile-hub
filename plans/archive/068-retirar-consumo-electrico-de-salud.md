# Plan 068: Estado `retired` — sacar fuentes muertas de la contabilidad de salud

> **Executor instructions**: este plan **no** elimina datasets ni rompe la API
> pública. Si la única forma de avanzar es tocar el enum `Dataset`, borrar la
> entrada del catálogo o relajar un gate, es una STOP condition.
>
> **Drift check (córrelo primero)**: `git diff --stat HEAD -- src/chile_hub/pipeline_status_utils.py scripts/verify_pipeline.py data/source_registry.json`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW-MED (toca contadores del dashboard público; ningún dato)
- **Depends on**: ninguno (secuela de ADR-014 / Plan 066)
- **Category**: correctness / observabilidad
- **Cierra**: issue #44

## Por qué importa

`consumo_electrico_comunal` aparece permanentemente como `drifted` y no hay
acción posible: `data/source_registry.json` documenta que CNE decomisionó el
catálogo Junar de energiaabierta.cl (investigado 2026-07-07, `AGENTS.md` §6), sin
archivo ni API de reemplazo. El dataset **nunca tuvo un fetch en vivo exitoso** —
solo publica `FALLBACK_ROWS` de muestra (3 filas), está en carril `candidate` y
fuera del bundle público.

Es el mismo problema que resolvió el Plan 066, con otra causa: un contador rojo
que nadie puede bajar entrena a los lectores a ignorar `drifted_count`. La
diferencia es que aquí el drift **es real** — lo que no existe es la acción. Un
`review_by: 2027-06-30` significa 11 meses más de ruido.

## Decisión de alcance (tomada por el mantenedor, 2026-07-29)

Se implementa **exclusión de la contabilidad de salud**, no retiro de la
superficie pública:

- `Dataset.CONSUMO_ELECTRICO_COMUNAL`, la entrada del catálogo, el extractor y
  los artefactos **se conservan**. `hub.load_polars("consumo_electrico_comunal")`
  sigue funcionando.
- Motivo: el enum es superficie pública de un paquete ya publicado en PyPI
  (1.21.x) con semantic-release automático. Retirarlo sería un BREAKING CHANGE
  que forzaría 2.0.0 — algo que el proyecto decidió explícitamente no forzar
  (`plans/README.md`, hallazgos diferidos 2026-07-18) — y no compra nada sobre
  el problema declarado.

## Estado actual

- `build_hub_health()` (`src/chile_hub/pipeline_status_utils.py:214-300`) computa
  `error_count`/`warn_count`/`ok_count` sobre **todas** las entradas, y
  `overall_status` se deriva de ahí.
- `_load_source_registry_datasets()` (mismo archivo, ~:60-77) ya es el precedente
  del patrón a seguir: lee el registry, distingue datasets reales de fixtures
  sintéticos de tests, y filtra `top_issue`.
- `data/source_registry.json` ya declara `maturity_status: "deprecated"` para
  `consumo_electrico_comunal` — el dato existe y se ignora, igual que pasaba con
  `coverage_policy` antes del Plan 066.
- `dataset_count` está gateado contra `len(REQUIRED_DATASETS)` en **cuatro**
  puntos (`verify_pipeline.py:832, 1097, 1177, 1218`), y `REQUIRED_DATASETS`
  deriva de `config.get("outputs")` del catálogo.
- `verify_pipeline.py` **no** valida `ok + warn + error == dataset_count`, pero
  `tests/test_chile_hub.py::test_health_summary` **sí** afirma cinco invariantes
  de suma contra `EXPECTED_DATASET_COUNT`. Hay que reexpresarlas contra el
  conjunto activo (`dataset_count - retired_count`), no relajarlas.

## Alcance

**En alcance**: `src/chile_hub/pipeline_status_utils.py`, `scripts/verify_pipeline.py`,
tests, `docs/adr/ADR-015`, `docs/datasets/consumo_electrico_comunal.md`,
`plans/README.md`.

**Fuera de alcance**: `src/chile_hub/datasets.py` (enum), `data/dataset_catalog_config.json`,
`src/extractors/consumo_electrico_extractor.py`, contratos, y cualquier dato.

## Git workflow

- Branch: `advisor/044-retire-consumo-electrico`
- Commit: `feat(health): excluye fuentes retiradas de la contabilidad de salud`

## Pasos

### Step 1: Derivar el conjunto de retirados desde el registry

Agrega `_load_retired_datasets()` modelado sobre `_load_source_registry_datasets()`:
lee `maturity_status == "deprecated"` de `data/source_registry.json`. **No
hardcodees el nombre del dataset** — la política es "fuente muerta", no "este
dataset".

**Verifica**: la función devuelve `{"consumo_electrico_comunal"}` sobre el
registry real y `set()` si el archivo no existe (mismo contrato tolerante que su
hermana).

### Step 2: Marcar y excluir en `build_hub_health()`

- Cada entrada gana `"retired": true|false` (siempre presente, inspeccionable —
  mismo criterio que `coverage.expected` en ADR-014).
- `error_count`/`warn_count`/`ok_count`/`drifted_count` y demás contadores de
  severidad se computan **solo sobre las no retiradas**; `overall_status` también.
- Se agrega `retired_count`.
- `dataset_count` **no cambia** (sigue siendo 19): el dataset sigue en el
  pipeline y en los artefactos; lo que se retira es su participación en la señal
  de salud. Esto además deja los 4 gates de `dataset_count` intactos.
- La entrada **permanece** en `datasets` — se muestra, marcada, no se esconde.

**Verifica**: `drifted_count` baja de 3 a 2 (`empresas` e `indicadores`),
`retired_count == 1`, `dataset_count == 19`, `overall_status` sigue `warn`.

### Step 3: Gates

En `verify_pipeline.py`: `retired` booleano y presente en cada entrada;
`retired_count` entero `>= 0` y `<= dataset_count`. **No toques** los gates de
`dataset_count` ni ningún enum.

### Step 4: Guardrail del Plan 066 y documentación

- `test_published_artifacts_report_exactly_three_real_problems` y
  `tests/e2e/verify_066.sh` fijan `drifted_count == 3` con los 3 nombres. Hay que
  actualizarlos **deliberadamente** a 2, documentando en el commit que el cambio
  viene de un mecanismo distinto (retiro de fuente muerta), no de una
  declaración de "esperado" como las de ADR-014.
- **ADR-015**: por qué `retired` en vez de borrar del enum; por qué la entrada
  sigue visible; quién puede declarar una fuente retirada (solo el registry, con
  `next_action` documentado) y con qué evidencia.
- ADR-014 dice "los 3 restantes son problemas reales: empresas, indicadores,
  consumo_electrico_comunal". **No lo edites** — los ADR son registro histórico;
  ADR-015 lo supersede en ese punto.
- `docs/datasets/consumo_electrico_comunal.md`: sección de estado retirado.

## Done criteria

- [ ] `drifted_count` 3 → 2; `retired_count == 1`; `dataset_count == 19` sin tocar sus gates.
- [ ] `Dataset.CONSUMO_ELECTRICO_COMUNAL` y `load_polars()` siguen funcionando.
- [ ] La entrada sigue visible en `hub_health.json`, marcada `retired: true`.
- [ ] El conjunto de retirados sale del registry, no de una lista hardcodeada.
- [ ] Guardrails del Plan 066 actualizados con justificación explícita.
- [ ] ADR-015 escrito; ADR-014 intacto.
- [ ] `make build && make verify && make test && make verify-landing && make lint && make format-check && make doctor` → exit 0.

## STOP conditions

- Bajar el contador exige tocar el enum, el catálogo o un gate de `dataset_count`.
- La entrada retirada desaparece de `hub_health.json` en vez de quedar marcada.
- Un dataset **sin** `maturity_status: deprecated` en el registry cambia de estado.
