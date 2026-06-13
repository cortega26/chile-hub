# Plan 011: Agregar linter, formatter y pre-commit hooks

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- requirements.txt Makefile .github/workflows/pipeline-check.yml`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P2
- **Esfuerzo**: M
- **Riesgo**: LOW
- **Depende de**: 001 (requirements.txt estabilizado)
- **Categoría**: dx
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

El proyecto no tiene linter, formatter ni pre-commit hooks configurados. Las revisiones de código cargan con toda la responsabilidad de estilo, lo que escala mal. Ningún gate impide que código mal formateado o con problemas obvios llegue al repo. Este plan agrega `ruff` (linter + formatter en un solo binario), hooks de pre-commit locales, targets de Makefile y un gate de lint en CI, todo con configuración mínima que no rompe el código existente.

## Estado actual

```
# requirements.txt — sin herramientas de dev
# Makefile — sin targets lint/format
# .github/workflows/pipeline-check.yml — sin paso de lint
# Sin .pre-commit-config.yaml, sin pyproject.toml, sin ruff.toml
```

El `Makefile` actual tiene los siguientes targets relevantes como referencia de estilo:

```makefile
# Makefile:89-90 — patrón existente
test:
	$(PYTHON) -m unittest discover -s tests

check: build verify test verify-landing
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Instalar ruff | `.venv/bin/pip install ruff` | exit 0 |
| Correr lint | `.venv/bin/python -m ruff check src/ tests/ scripts/` | exit 0 o lista de warnings |
| Correr format check | `.venv/bin/python -m ruff format --check src/ tests/ scripts/` | exit 0 o diff |
| Aplicar format | `.venv/bin/python -m ruff format src/ tests/ scripts/` | exit 0 |
| Tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |

## Alcance

**En scope**:
- `requirements.txt` — agregar `ruff` con versión fija (al final, separado por comentario)
- `pyproject.toml` — crear con configuración mínima de ruff y metadatos del proyecto
- `Makefile` — agregar targets `lint`, `format`, `lint-fix`
- `.github/workflows/pipeline-check.yml` — agregar paso de lint antes de tests
- `.pre-commit-config.yaml` — crear con hook de ruff

**Fuera de scope**:
- No modificar el código fuente de `src/` o `scripts/` para cumplir lint (el linter se configura para ignorar las reglas que el código existente no cumple)
- No agregar mypy ni type annotations (eso es un proyecto separado más grande)

## Git workflow

- Rama: `advisor/011-linter-formatter`
- Estilo de commit: `feat: agregar ruff, pre-commit hooks y targets de lint en Makefile`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Crear `pyproject.toml` con configuración de ruff

Crear `pyproject.toml` en la raíz del repo:

```toml
[project]
name = "chile-hub"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
# Reglas base: pycodestyle (E,W) + pyflakes (F)
select = ["E", "W", "F"]
ignore = [
    "E501",  # line too long — ruff format lo maneja
    "F401",  # imported but unused — hay imports condicionales (curl_cffi)
    "E402",  # module level import not at top — sys.path.insert patterns en tests
    "W291",  # trailing whitespace — ruff format lo limpia
    "W293",  # whitespace before ':'
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Verificar**: `python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"` (Python 3.11+) imprime `OK`.

### Paso 2: Agregar `ruff` a `requirements.txt`

Al final de `requirements.txt`, agregar (con versión fija — verificar con `.venv/bin/pip index versions ruff 2>/dev/null | head -1` o instalar y hacer freeze):

```
# dev tools
ruff==0.11.13
```

Luego instalar:

```bash
.venv/bin/pip install ruff==0.11.13
```

(Ajustar la versión al último release estable disponible.)

**Verificar**: `.venv/bin/python -m ruff --version` imprime la versión.

### Paso 3: Correr el formatter una vez para establecer la línea base

```bash
.venv/bin/python -m ruff format src/ tests/ scripts/ index.html 2>/dev/null || true
.venv/bin/python -m ruff format src/ tests/ scripts/
```

Esto aplica el formatter al código existente. Los cambios de formato deben commitearse como parte de este plan (sin cambio de lógica).

**Verificar**: `.venv/bin/python -m ruff format --check src/ tests/ scripts/` sale con exit 0 después de formatear.

### Paso 4: Correr el linter y ajustar `pyproject.toml` si hay warnings inevitables

```bash
.venv/bin/python -m ruff check src/ tests/ scripts/
```

Si hay errores que no son ignorables y que requieren cambiar código, agregar las reglas específicas a `[tool.ruff.lint] ignore` en `pyproject.toml` en lugar de modificar el código fuente. El objetivo de este plan es establecer la línea base, no corregir todo el código existente.

Documentar en `pyproject.toml` con un comentario qué se ignoró y por qué.

**Verificar**: `.venv/bin/python -m ruff check src/ tests/ scripts/` sale con exit 0 (sin errores no ignorados).

### Paso 5: Agregar targets al Makefile

Agregar después del target `test`:

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

También agregar `lint format-check` al target `check`:

```makefile
check: build verify test verify-landing lint format-check
```

Agregar los nuevos targets a la línea `.PHONY` al inicio del Makefile.

**Verificar**: `make lint` sale con exit 0.

### Paso 6: Agregar paso de lint en CI

En `.github/workflows/pipeline-check.yml`, agregar un paso de lint **antes** de los tests (después de "Install dependencies"):

```yaml
    - name: Lint with ruff
      run: |
        python -m ruff check src/ tests/ scripts/
        python -m ruff format --check src/ tests/ scripts/
```

**Verificar**: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('OK')"` imprime `OK`.

### Paso 7: Crear `.pre-commit-config.yaml`

Crear en la raíz:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.13  # ajustar al mismo tag que la versión instalada
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
```

**Nota**: `pre-commit` es una herramienta de dev que no está en requirements.txt. Para usarla localmente, el desarrollador debe instalarla con `pip install pre-commit` e inicializarla con `pre-commit install`. Documentar esto en el README o CLAUDE.md si hace falta.

**Verificar**: `python3 -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml')); print('OK')"` imprime `OK`.

### Paso 8: Correr los tests para verificar que no hay regresiones

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan.

## Criterios de done

- [ ] `pyproject.toml` existe con `[tool.ruff]` configurado
- [ ] `ruff==X.Y.Z` en `requirements.txt`
- [ ] `.pre-commit-config.yaml` existe
- [ ] `make lint` sale con exit 0
- [ ] `make format-check` sale con exit 0
- [ ] `grep -n "Lint with ruff" .github/workflows/pipeline-check.yml` retorna match
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si `ruff check` reporta más de 50 errores en el código existente que no son ignorables sin cambiar código — reportar la lista de reglas antes de proceder. Este plan no incluye corregir código.
- Si el formatter cambia código de forma que los tests fallan — revertir el formato de ese archivo e ignorarlo en `pyproject.toml` con `exclude`.
- Si la versión de ruff en pre-commit-config no coincide con la instalada — ajustar para que coincidan.

## Notas de mantenimiento

- `ruff` combina linter + formatter; no se necesitan `flake8`, `black` ni `isort` por separado.
- La configuración en `pyproject.toml` es la fuente de verdad; la versión en `pre-commit-config.yaml` debe mantenerse sincronizada con la de `requirements.txt`.
- Si en el futuro se quiere agregar type-checking (`mypy` o `pyright`), agregar como herramienta separada en `requirements.txt` y un target `typecheck` en el Makefile.
