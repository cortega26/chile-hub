# Plan 137: Auditoría — trinquete `mypy --strict` por módulo

> **Executor instructions**: Plan de **ola larga**: cada step es un PR pequeño
> e independiente que endurece un módulo y no puede romper nada más. Si algo
> de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md` en cada ola.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- pyproject.toml src/`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P3
- **Effort**: M (rolling, 6–8 PRs pequeños)
- **Risk**: LOW (solo anotaciones)
- **Depends on**: 132/133/134/135 reducen el trabajo; puede arrancar por los módulos hoja sin esperarlos
- **Category**: tipado (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

`mypy --strict` reporta **767 errores en 46 archivos**: 355 `no-untyped-call`,
279 `no-untyped-def`, 120 `type-arg`. El config actual cubre un subconjunto en
modo no-strict, así que nada impide que el hueco crezca. Un trinquete por
módulo (override que exige `disallow_untyped_defs` una vez limpio) convierte
la deuda en una curva descendente sin big-bang.

## Current state

- `pyproject.toml [tool.mypy]`: `files = [src/chile_hub, src/extractors,
  src/validation.py, src/build_dev_db.py, src/builders]`; flags no estrictos
  (`warn_return_any`, `check_untyped_defs`, `ignore_missing_imports`).
- Top de errores strict: `core.py` 91, `pipeline_status_utils` 77,
  `build_dev_db` 77, `builders/reports` 60, `cli`/`metadata`/`doc_sync` 49,
  extractores 14–27 c/u.
- Métrica reproducible:
  `./.venv/bin/mypy --strict --no-incremental <rutas> | tail -1`.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Medir módulo | `./.venv/bin/mypy --strict --no-incremental src/builders/io_utils.py` | contador decreciente |
| Typecheck actual | `make typecheck` | exit 0 |
| Suite | `make test` | verde |

## Scope

**In scope**: `pyproject.toml` (overrides por módulo) + anotaciones en los
módulos de cada ola.

**Out of scope**: `--strict` global; cambiar el runtime; `ignore_missing_imports`
(se mantiene hasta que existan stubs reales).

## Steps (olas)

Cada ola: (1) anotar el módulo hasta `--strict` en 0, (2) agregar
`[[tool.mypy.overrides]] module = […] disallow_untyped_defs = true` (y
`disallow_incomplete_defs`), (3) `make typecheck && make test`, (4) commit.
Si un módulo es inmanejable aún, saltarlo y anotarlo en el plan.

- **Ola 1 — hojas pequeñas**: `src/builders/io_utils.py`, `_shared.py`,
  `_logging.py`, `src/chile_hub/text.py`, `exceptions.py`, `datasets.py`,
  `regions.py`. (Bajo riesgo, establece el patrón.)
- **Ola 2 — `src/chile_hub` restante tras 134**: `contracts.py`,
  `data_manager.py`, `_store.py`/`_reporting.py`/`_query.py`,
  `pipeline_status_utils.py`, `core.py`, `cli.py` (tras 132).
- **Ola 3 — builders** (`formats`, `metadata`, `reports`, `artifacts`,
  `catalog`, `landing`, `dcat_catalog`, `data_package`, `geo`, `doc_sync`)
  tras 132/133.
- **Ola 4 — validation** (tras 135) y `build_dev_db.py` / `registry/`.
- **Ola 5 — extractores** (tras 133), de menor a mayor conteo.
- **Ola 6 — `scripts/`**: añadir `scripts/` a `files` del mypy en tandas
  (empezar por `_verify_common.py`/helpers tras 136); los scripts grandes al
  final.

Regla transversal: al tocar la firma de una función compartida, preferir
`TypeAlias`/`TypedDict`/dataclasses existentes (`ExtractionResult`,
`DatasetSpec`) antes que `Any`.

## Test plan

- Solo `make typecheck` + suite; los tests no deberían cambiar salvo imports
  de tipos.

## Done criteria (por ola)

- [ ] Módulo objetivo en 0 errores `--strict` y override agregado
- [ ] `make typecheck`/`make test` verdes
- [ ] Fila/nota del índice actualizada al cerrar cada ola

## STOP conditions

- Si anotar un módulo exige cambiar comportamiento (p. ej. `cast` que oculta
  un bug real), STOP y reportar: puede ser un hallazgo de correctitud.
- Si `type-arg` esconde tipos genéricos mal usados (no solo falta de
  parámetro), documentar el caso y decidir con el mantenedor.
