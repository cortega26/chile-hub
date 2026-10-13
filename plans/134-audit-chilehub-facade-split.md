# Plan 134: Auditoría — ChileHub: fachada, store y presentación (SRP) + fuga de caché

> **Executor instructions**: Cambio de alto impacto en la API pública más usada
> del proyecto: **la superficie pública no debe cambiar** (nombres, firmas,
> retornos). Ejecutar en PR propio, revisado por el advisor antes de mergear
> (regla global de AGENTS). Si algo de "STOP conditions" ocurre, detente y
> reporta. Actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- src/chile_hub/core.py src/chile_hub/data_manager.py tests/test_core.py tests/test_chile_hub.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: L (2–3 PRs: store → presentación → query)
- **Risk**: MED
- **Depends on**: 131 (B019 fuera de ignore al cerrar este plan); idealmente 132–133 ya mergeados para reducir conflictos
- **Category**: refactor / SOLID (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

`ChileHub` tiene 77 métodos y 2 078 líneas (MI C, 23 % docstrings): mezcla
*artifact store* (13 loaders + caché), motor de consulta (`sql`, `cross_view`,
`resolve_*`), contratos (`validate*`, `frictionless*`) y **presentación**
(`summary_table`, `snapshot_text/table`, `top_issue*`). Además los 11
`@functools.lru_cache` sobre **métodos de instancia** retienen `self` → un hub
nunca se libera (B019): un consumidor que crea hubs por request tiene fuga de
memoria real.

## Current state

- `core.py` 2 078 L / 77 métodos; método más largo: `validate_user_data`
  (C17), `search_datasets` (C13); `snapshot_text/table` ~100 L c/u.
- `core.py:132-190` — `_load_catalog`, `_load_json_artifact` y 12
  `_load_*_report` con `lru_cache(maxsize=1)` (B019 ×11).
- Presentación en `core.py`: `top_issue`, `top_issue_table`, `summary`,
  `summary_table`, `snapshot_text`, `snapshot_table`, `artifacts`,
  `example_usage` (string de ejemplos).
- `test_core.py` (957 L) y `test_chile_hub.py` cubren la superficie; hay
  contratos de artefactos en `ArtifactContractTests`.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Tests API | `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -q` | verde |
| Suite | `make test` | verde |
| Tipos | `make typecheck` | exit 0 |
| Lint | `make lint` | exit 0 |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**: `src/chile_hub/core.py` y módulos nuevos internos
(`_store.py`, `_reporting.py`, `_query.py` o nombres equivalentes), tests
afectados.

**Out of scope**: cambiar firmas/salidas públicas; `cli.py` (132);
`pipeline_status_utils` (132); `validation` (135).

## Steps

### Step 0 — Baseline

`make test` verde. Advisor consultado con este plan (segunda opinión adversaria
antes de tocar `core.py`).

### Step 1 — `ArtifactStore` (resuelve B019)

- Nuevo `src/chile_hub/_store.py`: `ArtifactStore(normalized_dir)` con
  `_load_json(name)` y los loaders (`manifest()`, `hub_health()`, …). Caché
  como **dict de instancia** (vive y muere con el hub) — sin `lru_cache` sobre
  métodos.
- `ChileHub.__init__` instancia el store; los métodos `_load_*` de `core.py`
  pasan a delegar (o se eliminan del todo si nada externo los usa; verificar
  con `grep` + tests).
- Test de regresión de fuga: crear N hubs, borrar referencias, `gc.collect()`
  y verificar que el store no retiene instancias (o al menos que no hay caché
  a nivel clase). Test de comportamiento: dos hubs con distinto
  `normalized_dir` no comparten datos.
- Al mergear: quitar `B019` del ignore de ruff (131) y quitar el docstring
  temporal.

### Step 2 — `_reporting.py`: presentación fuera del hub

- Mover a funciones/módulo la composición de tablas y textos
  (`summary_table`, `snapshot_*`, `top_issue*`, `check_sources_table`), que
  hoy construyen strings dentro del hub. `ChileHub` mantiene los **métodos
  públicos** delegando (compatibilidad).
- `test_core.py`/`test_chile_hub.py` son el contrato de salida (texto exacto
  donde aplique). Añadir un guardrail de superficie: el set de métodos públicos
  de `ChileHub` no cambia (test con `dir()` filtrado + allowlist nueva, o
  actualizar uno existente si ya lo cubre).

### Step 3 — `_query.py`: consulta y resolución

- Mover `sql`, `cross_view`, `resolve_comunas/regiones`, `resolve_by_coords`,
  helpers de read_parquet a un módulo interno (funciones o clase
  `QueryEngine`); `ChileHub` delega.
- `load_polars`/cachés de DataFrames (`_df_cache`) se quedan donde el store
  decida (probablemente en el store/engine, no en el hub).

### Step 4 — Cierre de contrato

- `core.py` objetivo ≤ ~900 L; MI del archivo sube a A/B (radon).
- `make typecheck` sigue verde (si 137 aún no corrió, no introducir `Any`
  nuevos sin motivo; anotar lo nuevo).
- Advisor review final del diff completo antes del merge.

## Test plan

- Suites de API + contratos + un test nuevo de no-fuga/no-caché-compartida.
- `make verify-landing` no aplica (sin cambios de datos), pero correr
  `make verify` no está de más si el hub toca lectura de artefactos.

## Done criteria

- [ ] `core.py` ≤ ~900 L, sin `lru_cache` sobre métodos, MI A/B
- [ ] Superficie pública intacta (guardrail) + suites verdes
- [ ] `B019` removido del ignore de ruff
- [ ] Advisor revisó; fila del índice actualizada

## STOP conditions

- Si un método público no se puede delegar sin cambiar salida exacta
  (formatos de tabla), deja ese método en `core.py` y anótalo en el plan —
  mejor incompleto que con deriva de contrato.
- Si el test de superficie revela métodos usados fuera del repo (docs,
  notebooks, `examples/`), ampliar la superficie permitida y documentar.
