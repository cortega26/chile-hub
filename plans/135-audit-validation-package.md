# Plan 135: Auditoría — `src/validation/`: paquete con fachada (SRP)

> **Executor instructions**: Refactor **move-only** (sin cambios de lógica de
> validación). La superficie pública (`from src.validation import validate_x`)
> no debe cambiar. Si algo de "STOP conditions" ocurre, detente y reporta.
> Actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- src/validation.py scripts/check_validation_registration.py tests/test_validation.py tests/test_pipeline_logic.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (contrato de registro §5)
- **Depends on**: 132 (si ese plan tocó `_compute_validations`/checker; coordinar)
- **Category**: refactor / SOLID (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

`validation.py` tiene 1 960 líneas, 33 funciones y MI C (0.00): 25+ validadores
de dominios distintos (DPA, censo, economía, educación, salud, territorio,
anomalías temporales) en un archivo. Es la última defensa antes de publicar
datos y el módulo con peor señal de mantenibilidad del repo. Partirlo por
dominio con una fachada de re-export elimina el riesgo de navegación sin
tocar comportamiento.

## Current state

- `src/validation.py` — 1 960 L, 33 funciones, sin docstring de módulo;
  validadores con grade D/C: `validate_estadisticas_vitales` (D29),
  `validate_permisos_edificacion` (D25), `detect_series_anomalies` (D24),
  `validate_empresas`/`validate_puntos_interes`/`validate_calidad_aire` (C20)…
- Registro de validadores: bloque `validations = {…}` en
  `src/build_dev_db.py::_compute_validations`; el checker
  `scripts/check_validation_registration.py` compara `validate_*()` de
  `src/validation.py` contra ese bloque (AGENTS §5). **Si validation pasa a
  paquete, el checker debe escanear el paquete en el mismo commit** + su
  guardrail (`tests/test_ci_config.py::…`/`test_pipeline_logic.py`).
- Tests: `tests/test_validation.py` (2 393 L) importa por nombre; la fachada
  mantiene compatibilidad.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Tests validación | `./.venv/bin/pytest tests/test_validation.py -q` | verde |
| Registro | `./.venv/bin/python scripts/check_validation_registration.py` | ok |
| Suite | `make test` | verde |
| Tipos | `make typecheck` | exit 0 |

## Scope

**In scope**: `src/validation.py` → `src/validation/` (paquete),
`scripts/check_validation_registration.py`, tests afectados.

**Out of scope**: cambiar reglas de validación, mensajes, severidades o el
bloque `validations` de build_dev_db (salvo que 132 lo haya tabulado).

## Steps

### Step 0 — Baseline

`pytest tests/test_validation.py` + `check_validation_registration.py` verdes.
Listar las 33 funciones y agruparlas por dominio (propuesta:
`_dpa.py`, `_poblacion.py` (censo/hogares/vitales), `_educacion.py`,
`_salud.py`, `_economia.py` (indicadores/empresas/finanzas),
`_territorio.py` (siedu/geometría/calidad_aire/permisos),
`_anomalias.py` (detect_series_anomalies), `_helpers.py` (shared helpers).

### Step 1 — Paquete move-only

- `git mv src/validation.py src/validation/__init__.py` como punto de
  partida; luego mover bloques por dominio a submódulos **sin editar
  cuerpos**.
- `__init__.py` re-exporta **todo** lo público (`from ._dpa import *` o
  explícito) para que `from src.validation import validate_x` siga
  funcionando idéntico.
- Verificación mecánica del move: hash del AST de cada función antes/después
  (o `diff` de cuerpos) — sin cambios de lógica.
- Docstring de módulo en `__init__.py` (mata D100 de este archivo).

### Step 2 — Checker y guardrails

- Actualizar `scripts/check_validation_registration.py` para recorrer el
  paquete (`src/validation/**/*.py`) en vez del archivo único; conservar la
  semántica (mismo conteo de `validate_*`).
- Correr `python scripts/check_validation_registration.py` + su test; si
  algún guardrail en `test_ci_config.py`/`test_pipeline_logic.py` asume la
  ruta `src/validation.py`, actualizarlo con el porqué (este plan).

### Step 3 — Navegabilidad (opcional si hay presupuesto)

- Con el paquete ya separado, partir las dos funciones D-grade más grandes
  (`validate_estadisticas_vitales`, `validate_permisos_edificacion`) en
  helpers por bloque de chequeo (una función = una aserción semántica), con
  los tests existentes como contrato. Quitar sus `# noqa: C901` si 132 los
  dejó.

### Step 4 — Cierre

`make test`, `make typecheck`, `make lint`, `make doctor`;
`plans/README.md` actualizado. Los conteos de AGENTS §8 (tabla de archivos de
test) no cambian; `scripts/check_agents_sync.py` debe quedar verde.

## Test plan

- Move-only: la suite existente es el contrato; añadir un test que importe
  cada submódulo y verifique que `__init__` re-exporta el inventario completo
  (lista de nombres vs `dir`).

## Done criteria

- [ ] `src/validation/` por dominio; `__init__` re-exporta todo
- [ ] Checker escanea el paquete y pasa; guardrails actualizados
- [ ] Suite/tipos/doctor verdes; ningún cuerpo de validador cambió
- [ ] Fila del índice actualizada

## STOP conditions

- Si el checker no puede adaptarse sin cambiar el contrato del bloque
  `validations` de `build_dev_db.py`, coordinar con 132 y detenerse.
- Si algún test importa `src.validation` por ruta de archivo (no por módulo),
  listarlo antes de mover.
