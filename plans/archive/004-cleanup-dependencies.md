# Plan 004: Limpiar dependencias — remover pyarrow, separar dev de prod, declarar curl_cffi

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**: `git diff --stat ba2f434..HEAD -- requirements.txt pyproject.toml Makefile .github/workflows/pipeline-check.yml`
> If any of these files changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: deps
- **Planned at**: commit `ba2f434`, 2026-06-13
- **Resolved**: 2026-06-18 — `pyarrow` removed from runtime requirements; dev/runtime split, `curl_cffi`, bootstrap, and CI dependency handling are in place.

## Why this matters

Tres problemas en `requirements.txt` inflan innecesariamente las instalaciones
y crean ambigüedad:

1. **pyarrow** (80 MB) está listado pero nunca se importa — Polars usa su
   propio motor Arrow nativo. Es peso muerto en cada `pip install`.
2. **playwright** (descarga ~300 MB de Chromium) y **ruff** (10 MB) son
   herramientas de desarrollo y smoke testing, no dependencias de runtime.
   Cada instalación de producción descarga un navegador completo que nunca
   se usa.
3. **curl_cffi** se importa en `subdere_extractor.py:18` con un try/except
   de fallback, pero no está en `requirements.txt`. Quien instala desde
   requirements.txt nunca obtiene TLS fingerprint impersonation y puede
   enfrentar bloqueos contra la API de BCN.

## Current state

- `requirements.txt` actual:

```
polars==1.41.2
duckdb==1.5.3
requests==2.34.2
pandas==3.0.3
pyarrow==24.0.0
xlsxwriter==3.2.9
playwright==1.60.0
ruff==0.15.17
```

- `src/extractors/subdere_extractor.py:18-25` — curl_cffi sin declarar:

```python
# src/extractors/subdere_extractor.py:18-25
try:
    from curl_cffi import requests as _cffi_requests
    _CURL_CFFI_AVAILABLE = True
except ImportError:
    _CURL_CFFI_AVAILABLE = False
```

- `Makefile:95-108` — ruff y lint targets:

```makefile
lint:
	$(PYTHON) -m ruff check src/ tests/ scripts/

lint-fix:
	$(PYTHON) -m ruff check --fix src/ tests/ scripts/

format:
	$(PYTHON) -m ruff format src/ tests/ scripts/

format-check:
	$(PYTHON) -m ruff format --check src/ tests/ scripts/
```

- `Makefile:89-90` — verify-landing usa playwright:

```makefile
verify-landing:
	$(PYTHON) scripts/verify_landing.py
```

- `Makefile:62-66` — bootstrap instala todo desde requirements.txt:

```makefile
bootstrap:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt
	$(VENV_DIR)/bin/python -m playwright install chromium
```

- `.github/workflows/pipeline-check.yml:73` — CI instala todas las deps:

```yaml
- name: Install dependencies
  run: python -m pip install --requirement requirements.txt
```

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full bootstrap | `make bootstrap` | exit 0 |
| Run build | `make build` | exit 0 |
| Run tests | `make test` | exit 0 |
| Lint check | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Landing smoke test | `make verify-landing` | exit 0 |
| Verify no pyarrow imports | `grep -r "pyarrow" src/ tests/ scripts/` | no matches |

## Scope

**In scope** (files to modify):
- `requirements.txt` — dividir en prod y dev
- `Makefile` — actualizar targets bootstrap y doctor

**Out of scope** (do NOT touch):
- `pyproject.toml` — la migración a pyproject.toml como manifiesto primario
  es un plan separado.
- `uv.lock` — se aborda en el plan de tooling (007).
- CI workflow (`.github/workflows/pipeline-check.yml`) — la instalación de
  CI ya funciona con `requirements.txt`; si se cambia el nombre del archivo
  o se agrega un archivo separado, CI debe actualizarse. Pero este plan
  mantiene el nombre `requirements.txt` para prod y agrega uno nuevo para dev.

## Steps

### Step 1: Remover pyarrow de requirements.txt

Eliminar la línea `pyarrow==24.0.0` de `requirements.txt`.

**Verify**: `grep -r "pyarrow" src/ tests/ scripts/` → cero resultados.
`make bootstrap && make build && make test` → todo exit 0.

### Step 2: Crear dev-requirements.txt con playwright y ruff

Crear `dev-requirements.txt` con:

```
playwright==1.60.0
ruff==0.15.17
```

Remover `playwright==1.60.0` y `ruff==0.15.17` de `requirements.txt`.

**Verify**: `requirements.txt` ahora contiene solo: polars, duckdb, requests,
pandas, xlsxwriter.

### Step 3: Agregar curl_cffi a requirements.txt

Agregar `curl_cffi` a `requirements.txt` con un version pin. Buscar la última
versión estable publicada en PyPI:

```bash
pip index versions curl_cffi 2>/dev/null || echo "Usar curl_cffi==0.7.4"
```

Agregar `curl_cffi==0.7.4` (o la versión más reciente) a `requirements.txt`.

**Verify**: `make bootstrap` → la instalación incluye curl_cffi.
`python -c "from curl_cffi import requests; print('OK')"` → imprime "OK".

### Step 4: Actualizar Makefile bootstrap

Modificar `make bootstrap` para que instale ambos archivos de requirements:

```makefile
bootstrap:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt
	$(VENV_DIR)/bin/python -m pip install -r dev-requirements.txt
	$(VENV_DIR)/bin/python -m playwright install chromium
```

**Verify**: `make bootstrap` → exit 0. `make doctor` → muestra todas las
dependencias instaladas.

### Step 5: Actualizar CI para instalar ambos archivos

En `.github/workflows/pipeline-check.yml`, el paso "Install dependencies"
del job `build-and-test` debe instalar ambos:

```yaml
- name: Install dependencies
  run: |
    python -m pip install --requirement requirements.txt
    python -m pip install --requirement dev-requirements.txt
```

El job `quality` solo necesita ruff (de `dev-requirements.txt`):

```yaml
- name: Install Ruff
  run: python -m pip install "$(grep '^ruff==' dev-requirements.txt)"
```

**Verify**: CI pasa todos los jobs. Si no se puede probar CI localmente,
confirmar que los comandos de instalación son correctos verificando que
`pip install -r dev-requirements.txt` funciona localmente.

### Step 6: Verificación completa del pipeline

**Verify**: `make refresh` → exit 0 (extract + build + verify + test +
verify-landing). `make lint` → exit 0. `make format-check` → exit 0.

## Test plan

- Los tests existentes (`make test`) deben seguir pasando sin cambios.
- El smoke test de landing (`make verify-landing`) debe seguir funcionando
  (playwright sigue instalado vía dev-requirements.txt).
- `make lint` y `make format-check` deben seguir funcionando (ruff sigue
  instalado vía dev-requirements.txt).
- Verificar que `curl_cffi` se instaló: `python -c "from curl_cffi import requests"` → exit 0.

## Done criteria

- [ ] `requirements.txt` ya no contiene pyarrow, playwright, ni ruff
- [ ] `dev-requirements.txt` existe con playwright y ruff
- [ ] `curl_cffi` está en `requirements.txt` con version pin explícito
- [ ] `make bootstrap` completa sin errores
- [ ] `make refresh` sale con exit 0
- [ ] `make test` sale con exit 0
- [ ] `make verify-landing` sale con exit 0
- [ ] `make lint` y `make format-check` salen con exit 0
- [ ] `grep -r "pyarrow" src/ tests/ scripts/` no encuentra nada
- [ ] `python -c "from curl_cffi import requests"` funciona

## STOP conditions

Stop and report back (do not improvise) if:

- Los archivos en "Current state" no coinciden con los excerpts.
- `make bootstrap` falla después de los cambios (error de dependencias).
- `make refresh` falla en cualquier paso.
- `curl_cffi` no puede instalarse en el entorno (problemas de compilación,
  incompatibilidad con la arquitectura).
- CI falla después de actualizar el workflow (si se puede verificar).

## Maintenance notes

- pyarrow se removió porque Polars >= 1.0 usa su propio motor Arrow nativo.
  Si en el futuro se necesita PyArrow explícitamente (e.g., para
  interoperabilidad con otros sistemas), agregarlo de vuelta con un comentario
  explicando por qué.
- curl_cffi depende de libcurl. En la mayoría de los sistemas Linux modernos
  está disponible. En macOS, `pip install curl_cffi` debería funcionar con
  wheels precompilados. Si hay problemas de compilación, instalar
  `libcurl4-openssl-dev` (Linux) o `curl` (macOS) como prerrequisito del
  sistema.
- La separación prod/dev es un paso intermedio. El plan de migración a
  pyproject.toml (futuro) consolidará esto en `[project.optional-dependencies]`.
