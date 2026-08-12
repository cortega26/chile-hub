# Plan 073: Contratos disponibles para consumidores instalados (wheel + bundle)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/chile_hub/core.py src/chile_hub/contracts.py pyproject.toml src/builders/artifacts.py tests/test_chile_hub.py tests/test_packaging_runtime.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: bug / dx
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`ChileHub.validate_dataset()` / `validate_user_data()` / CLI `validate`
resuelven los contratos en `self.root_dir / "contracts" / "datasets"`, donde
`root_dir` deriva del directorio de datos descargado (`core.py:668,711`).
El wheel (`packages = ["src/chile_hub"]`) y el bundle ZIP (56 entradas) **no
contienen `contracts/`** — un consumidor instalado (PyPI) que corra
`chile-hub validate mi_archivo.csv --dataset comunas` falla con
`ChileHubDatasetError: No existe contrato de schema`. La validación de datos
de usuario — la función que existe para que consumidores cotejen sus CSVs —
es inalcanzable sin clonar el repo.

## Current state

- `src/chile_hub/core.py:668` (`validate_dataset`) y `:711`
  (`validate_user_data`):
  ```python
  contract_path = self.root_dir / "contracts" / "datasets" / f"{dataset_name}.schema.json"
  ```
- `pyproject.toml:122-129` — `[tool.hatch.build.targets.wheel] packages = ["src/chile_hub"]`
  (no incluye `contracts/`).
- `src/builders/artifacts.py` — el ZIP publicable no incluye `contracts/`.
- `scripts/check_companion_paths.py` — el registry valida que cada dataset
  tenga contrato en `contracts/datasets/`, pero no valida que viaje.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build wheel | `python -m build --wheel --outdir /tmp/opencode/dist` | success |
| Instalar | `pip install /tmp/opencode/dist/*.whl` (venv limpio) | success |
| Smoke instalado | `chile-hub validate <csv> --dataset comunas` (venv limpio) | status ok |
| Tests | `./.venv/bin/pytest tests/test_chile_hub.py tests/test_packaging_runtime.py -q` | all pass |

## Scope

**In scope**:
- `pyproject.toml` (wheel: incluir `contracts/datasets/`)
- `src/chile_hub/core.py` (resolución con fallback a `importlib.resources`)
- `src/builders/artifacts.py` (bundle: incluir contratos — decidir en Step 1)
- `scripts/check_companion_paths.py` (si el registry debe validar el empaquetado)
- `tests/test_packaging_runtime.py`, `tests/test_chile_hub.py`

**Out of scope**:
- El CLI `validate` en sí (ya funciona si el contrato existe).
- Los contratos en runtime del pipeline (`scripts/verify_pipeline.py`).

## Git workflow

- Branch: `advisor/073-contracts-for-consumers`
- Conventional commits, uno por paso lógico.
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Decide el alcance (wheel, bundle, o ambos)

Analiza `test_packaging_runtime.py` (qué cubre hoy) y decide: mínimo viable es
el **wheel** (la vía PyPI — el caso reportado). El bundle es deseable pero
toca `check_companion_paths.py` y el manifiesto. Recomendación: wheel primero;
bundle como Step opcional si el mantenimiento lo permite.

**Verify**: decisión documentada en el commit.

### Step 2: Empaqueta los contratos en el wheel

En `pyproject.toml`, agrega los contratos al wheel (p. ej.
`[tool.hatch.build.targets.wheel] packages = ["src/chile_hub"]` +
`force-include` de `contracts/datasets/*.schema.json` dentro del paquete como
`src/chile_hub/contracts/datasets/`, o via `include`). Verifica el contenido
del wheel con `unzip -l`.

**Verify**: `python -m build --wheel` → el wheel contiene `*.schema.json`.

### Step 3: Resolución con fallback

En `core.py`, resuelve el contrato así:
1. `self.root_dir / "contracts" / "datasets"` (checkout / bundle con contratos)
2. fallback: `importlib.resources.files("chile_hub") / "contracts" / "datasets"`
   (wheel instalado)

Extrae la resolución a un helper (p. ej. `_contract_path(dataset_name)`) usado
por `validate_dataset`, `validate_user_data` y el CLI `validate`.

**Verify**: en un venv limpio con el wheel, `chile-hub validate <csv> --dataset comunas` → `status: ok`.

### Step 4: Tests

En `tests/test_packaging_runtime.py` (o `test_chile_hub.py`), test que con
`root_dir` sin contratos la resolución cae al fallback del paquete; y que el
wheel incluye los schemas.

**Verify**: `./.venv/bin/pytest tests/test_packaging_runtime.py tests/test_chile_hub.py -q` → all pass.

## Test plan

- Test de fallback: `root_dir` vacío → contrato resuelto desde el paquete.
- Test de wheel: `unzip -l` del wheel contiene schemas.
- Modelar sobre los tests existentes de `test_packaging_runtime.py`.

## Done criteria

- [ ] El wheel contiene `contracts/datasets/*.schema.json`
- [ ] `chile-hub validate <csv> --dataset comunas` funciona en venv limpio
- [ ] Test de fallback existe y pasa
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- `importlib.resources` no puede acceder a archivos del wheel (problema de
  empaquetado — verificar con `unzip -l` primero).
- El fallback rompe la resolución en checkout (orden incorrecto de los paths).

## Maintenance notes

- Al agregar un dataset, `check_companion_paths.py` valida el contrato en el
  repo; este plan no cambia eso — el empaquetado es un paso adicional.
- Revisar en el PR: que `self.root_dir` siga siendo la primera opción (el
  bundle descargado debe poder sobreescribir los contratos del paquete).
