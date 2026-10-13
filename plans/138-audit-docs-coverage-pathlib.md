# Plan 138: Auditoría — PEP-257, trinquete de docstrings/cobertura y `pathlib`

> **Executor instructions**: Plan de higiene en marco ADR-024 (trinquetes, no
> big-bang). Ejecutar al final de la ola (después de 132–136) porque toca
> módulos que esos planes mueven. Si algo de "STOP conditions" ocurre, detente
> y reporta. Actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- pyproject.toml .github/workflows/pipeline-check.yml scripts/ src/`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P3
- **Effort**: M (varias PRs)
- **Risk**: LOW
- **Depends on**: 132–136 (mueven archivos y funciones)
- **Category**: docs / calidad (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

Tres trinquetes baratos que hoy no existen: (a) docstrings —`interrogate` da
44 % en `src`+`scripts` y 12 módulos públicos sin docstring de módulo,
incluyendo `core.py`, `validation.py`, `build_dev_db.py`, `verify_pipeline.py`;
(b) cobertura — el badge es 73.3 % global sin piso por módulo, y los
validadores/extractores son la lógica de mayor riesgo; (c) idiomas modernos
—~600 usos de `os.path` que impiden pensar en `pathlib` (PTH apagado).

## Current state

- `interrogate`: 44 % (`src`+`scripts`); calidad del job: `uv run interrogate
  --fail-under=80 src/chile_hub || true` (no bloqueante).
- D100 (módulo sin docstring): 12 archivos (`scripts/check_companion_paths.py`,
  `check_validation_registration.py`, `package_publishable_bundle.py`,
  `pipeline_status.py`, `sync_docs.py`, `verify_landing.py`,
  `verify_pipeline.py`, `src/build_dev_db.py`, `src/chile_hub/__main__.py`,
  `core.py`, `extractors/subdere_extractor.py`, `validation` (paquete tras
  135)).
- `[tool.coverage.report]` sin `fail_under`; omit documentado
  (`cli.py`, `__main__.py`, `pipeline_status_utils.py`).
- PTH: `PTH118` 276, `PTH123` 80, `PTH110` 60, `PTH120` 50, `PTH100` 43…
  concentrados en `scripts/` y extractores.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Docstrings | `./.venv/bin/interrogate -v src/chile_hub scripts` | % sube |
| Cobertura | `make build && .venv/bin/pytest -n auto --cov=src --cov=scripts --cov-report=term` | % medido |
| Lint/format | `make lint && make format-check` | exit 0 |
| Suite | `make test` | verde |

## Scope

**In scope**: docstrings de módulos/funciones públicas, config `interrogate`/
`ruff (D-selección)`/coverage, migración PTH por tandas, tests/guardrails de
trinquete.

**Out of scope**: docstrings de tests (no aplica), reescribir lógica,
`E501` (decisión de 131), D-rules conflictivas (D203/D211, D212/D213: elegir
el set compatible con el formato elegido y no habilitar ambas).

## Steps

### Step 1 — Docstrings de módulo (los 12)

- Un PR corto: docstring de módulo en cada archivo de la lista (1–3 líneas,
  foco en responsabilidad y contrato, no en narrar el código). Mata D100.
- Guardrail: `ruff` select += `D100` para `src/` y `scripts/` (D100 ya queda
  cubierto); docstring del guardrail cita el audit.

### Step 2 — Docstrings de API pública + interrogate bloqueante

- Backfill de funciones/clases públicas en `src/chile_hub` (hoy 23 % en
  `core.py`, 17 % en `pipeline_status_utils`). Coordinar con 134 (el split
  mueve métodos) para no documentar dos veces.
- Configurar `[tool.interrogate]` (fail-under por invocación) y volver
  bloqueante el step de calidad: primero `--fail-under=<medido+2>` y subir
  por tandas hasta ≥90 % en `src/chile_hub`; `scripts/` con umbral propio más
  bajo (p. ej. 70 %).
- Añadir D-subset (`D101`, `D103`) por `per-file-ignores` a `src/chile_hub`
  solo cuando el backfill lo deje en 0.

### Step 3 — Piso de cobertura por módulo

- Añadir `fail_under` global conservador en `[tool.coverage.report]` (medir
  primero; p. ej. 70) y subirlo por tandas.
- Opcional (si el ejecutor tiene presupuesto): `scripts/check_coverage_floors.py`
  que lea `coverage.json` y aplique pisos por ruta (p. ej. `src/validation`
  ≥ X, `src/extractors` ≥ Y) con los valores medidos menos 2 puntos; corre en
  `build-and-test` tras pytest. Si no, dejarlo como deferred con medición
  registrada.

### Step 4 — PTH por tandas

- Tanda 1: `src/chile_hub` + `src/builders` (con `--fix` donde aplique y
  revisión manual de `os.path` no trivial); select `PTH` con
  `per-file-ignores` para el resto del árbol.
- Tanda 2: extractores; Tanda 3: `scripts/`. Cada tanda quita su ignore.
- Cuidado: `data/raw` y rutas de staging no cambian de semántica; tests de
  paths (`check_agents_sync`, `check_companion_paths`) verdes.

### Step 5 — Cierre

`make test`, `make lint`, `make doctor`, `sync_docs --check`;
`plans/README.md` actualizado.

## Test plan

- Cambios de docs/config: suite como contrato; guardrails nuevos para cada
  trinquete (D100, interrogate, coverage floor).
- PTH: tests de builders/extractores + `make build` sin diff de artefactos.

## Done criteria

- [ ] Los 12 módulos con docstring; D100 verde en `src`+`scripts`
- [ ] `interrogate` bloqueante en `quality` con umbral escalonado
- [ ] `fail_under` (y pisos por módulo si aplica) en CI
- [ ] PTH habilitado por directorio convertido (3 tandas)
- [ ] Suite/lint/doctor verdes; fila del índice actualizada

## STOP conditions

- Si subir el umbral de interrogate rompe el job `quality` por archivos no
  previstos, ajustar el umbral al medido y listar los pendientes.
- Si un paso `--fix` de PTH cambia comportamiento (p. ej. `os.path.exists` con
  bytes), revertir ese caso y documentarlo.
