# Plan 122: Integridad de la señal de tests — cobertura de `scripts/`, smoke del MCP y xdist en CI

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- Makefile .github/workflows/pipeline-check.yml pyproject.toml tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S-M
- **Risk**: LOW-MED
- **Depends on**: none (coordina con Plan 126 en `pipeline-check.yml`: ejecutar secuencialmente, no en worktrees simultáneos)
- **Category**: tests / dx
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Tres defectos que hacen que la señal de CI mienta:

1. **La cobertura ignora `scripts/`**: `pyproject.toml:203-215` declara
   `source = ["src", "scripts"]`, pero `Makefile:171` y
   `pipeline-check.yml:410` corren `pytest --cov=src`, y `--cov` **reemplaza**
   el `source` de config (verificado). Resultado: ~4.4k líneas de `scripts/`
   (incluido `verify_pipeline.py`, 1 940 líneas y el gate diario de
   publicación) nunca se miden; el badge `coverage_badge.json` y cualquier
   patch gate quedan ciegos justo ahí.
2. **El servidor MCP nunca se construye en CI**: `mcp` es un extra separado
   (`pyproject.toml:80-82`) que CI no instala (solo `--extra pipeline --extra
   dev`), así que el test `test_pipeline_logic.py:5270-5283` siempre toma la
   rama `ImportError`; `build_server()` (registro de las 4 tools) jamás corre
   en el runner.
3. **CI corre pytest serial** (`pipeline-check.yml:410`) mientras `make test`
   usa `-n auto` (Plan 080, ~66s → ~18s verificado). El feedback loop de PR
   es 3-4x más lento de lo necesario.

## Current state

- `pyproject.toml:203-215`:
  ```toml
  [tool.coverage.run]
  branch = true
  source = ["src", "scripts"]
  omit = [...]
  ```
- `Makefile:170-171`:
  ```make
  coverage:
  	$(PYTHON) -m pytest --cov=src --cov-report=term-missing --cov-report=xml
  ```
- `pipeline-check.yml:409-410`:
  ```yaml
      - name: Run unit and contract tests
        run: python -m pytest -v --cov=src --cov-report=term-missing --cov-report=xml
  ```
- `pipeline-check.yml:71,175,222,521` — `uv sync --extra pipeline --extra dev`
  (sin `mcp`).
- `tests/test_pipeline_logic.py:5270-5283` — test que ramifica en
  `import mcp`; en CI toma la rama de ausencia.
- `Makefile:162-165` — `test: $(PYTHON) -m pytest -n auto` con el comentario
  del Plan 080.
- El badge de cobertura se genera con un target del Makefile
  (`coverage-badge:`) y vive en `data/normalized/coverage_badge.json`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests con cobertura | `./.venv/bin/pytest -n auto --cov=src --cov=scripts --cov-report=term-missing` | declared | verde |
| Tests focal MCP | `./.venv/bin/pytest tests/test_pipeline_logic.py -k "mcp or Mcp" -v` | declared | verde |
| Badge | `make coverage-badge` | declared | `data/normalized/coverage_badge.json` regenerado |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `Makefile` (target `coverage`)
- `.github/workflows/pipeline-check.yml` (step de tests; step nuevo de MCP)
- `data/normalized/coverage_badge.json` (regenerado)
- `tests/test_ci_config.py` (guardrails)

**Out of scope**:
- Subir cobertura de `scripts/` (eso lo hace el Plan 123).
- Reactivar el upload a Codecov (sigue deshabilitado, `if: false`).
- Cambiar umbrales de coverage o `fail-under` (no hay).

## Git workflow

- Branch: `advisor/122-ci-test-integrity`
- Commits: `fix(tests): mide scripts/ en cobertura y corre MCP en CI` (estilo repo).
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest -n auto tests/test_ci_config.py -v` verde. Si no, STOP.

### Step 1: Cobertura sobre `src` + `scripts`

- `Makefile:171`: `--cov=src --cov=scripts`.
- `pipeline-check.yml:410`: `python -m pytest -n auto -v --cov=src --cov=scripts --cov-report=term-missing --cov-report=xml`
  (el `-n auto` es el Step 3; puedes hacer ambos de una vez si prefieres, pero
  verifica por separado).
- Regenera el badge: `make coverage-badge` y commitea
  `data/normalized/coverage_badge.json` si cambia (bajará; es la cifra
  honesta). Si el target no existe con ese nombre exacto, grep
  `coverage-badge` en el Makefile.

**Verify**: `./.venv/bin/pytest -n auto --cov=src --cov=scripts
--cov-report=term-missing tests/test_ci_config.py` muestra filas de `scripts/`
en el reporte (grep `scripts/check_source_urls.py` en la salida).

### Step 2: Smoke del MCP en CI

Agrega en `pipeline-check.yml`, en el job `build-and-test` después del step de
tests (mismo job, para no duplicar checkout/sync):

```yaml
      - name: MCP server smoke (extra [mcp])
        run: |
          uv run --extra mcp python - <<'PY'
          from chile_hub.mcp_server import build_server
          server = build_server()
          tools = getattr(server, "_tool_manager", None)
          print("MCP server construido")
          PY
```

Notas para el ejecutor:
- Verifica el nombre real de la API de `mcp` 2.x leyendo
  `src/chile_hub/mcp_server.py:35-105` (cómo registra las tools) y ajusta el
  smoke a algo estable (basta con que `build_server()` no lance; no dependas
  de atributos privados si puedes evitarlo). Si `build_server()` no expone
  nada, deja `print` y nada más.
- El paso `uv run --extra mcp` sincroniza el extra en el venv del job (ya
  sincronizado con pipeline+dev); documenta en un comentario que el costo es
  aceptable (una vez por run).

**Verify**: `grep -n "MCP server smoke" .github/workflows/pipeline-check.yml`
→ 1; localmente `uv run --extra mcp python -c "from chile_hub.mcp_server import build_server; build_server(); print('ok')"`
→ `ok`.

### Step 3: xdist en CI

Agrega `-n auto` al pytest de CI (ver Step 1). Si `pytest-cov` + xdist emite
warning de combinación, usa `--cov` igual (pytest-cov lo soporta desde 4.x;
el repo tiene 7.1.0).

**Verify**: la corrida local `./.venv/bin/pytest -n auto --cov=src --cov=scripts
tests/test_ci_config.py -q` termina sin errores de cobertura.

### Step 4: Guardrails

En `tests/test_ci_config.py`, clase nueva (o extensión de
`LighthouseGuardrailTests` no — clase propia `TestSignalIntegrityGuardrailTests`):
1. `--cov=src --cov=scripts` aparece en `Makefile` y en `pipeline-check.yml`.
2. `pipeline-check.yml` contiene `--extra mcp` y `build_server`.
3. El pytest de CI contiene `-n auto`.
4. Docstring con el incidente (cobertura vanidosa + rama muerta del MCP).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "SignalIntegrity" -v`
→ verde.

## Test plan

- Guardrails de texto (4 asserts) — patrón `tests/test_ci_config.py`.
- No hay test de cobertura en sí; el smoke del MCP es la verificación
  funcional.
- Verificación: pytest focal + `make coverage-badge` regenerado.

## Done criteria

- [ ] `grep -n "\-\-cov=src --cov=scripts" Makefile .github/workflows/pipeline-check.yml` → 2 matches
- [ ] `grep -n "\-n auto" .github/workflows/pipeline-check.yml` → 1 (en el step de tests)
- [ ] `grep -n "\-\-extra mcp" .github/workflows/pipeline-check.yml` → 1
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -v` → verde (con la clase nueva)
- [ ] `data/normalized/coverage_badge.json` regenerado y commiteado si cambió
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `--cov=src --cov=scripts` no habilita `scripts/` (porque `--cov` es
  aditivo y funciona distinto a lo esperado), detente y reporta el output
  exacto; la alternativa es quitar `--cov` y confiar en `[tool.coverage.run]
  source` (el `pytest-cov` lo respeta cuando no se pasa `--cov`).
- Si `uv run --extra mcp` re-resuelve el entorno y rompe el lock (`--locked`
  falla), reporta; alternativa: `uv sync --extra pipeline --extra dev --extra
  mcp` + `python -c ...`.
- Si `-n auto` hace fallar tests de `test_verify_pipeline.py` (golden copy por
  clase), STOP y reporta cuáles.

## Maintenance notes

- El conjunto de `source` de cobertura debe seguir siendo el mismo que el de
  `--cov`; el guardrail lo fija. Si se agrega otro directorio (p. ej.
  `examples/`), actualizar ambos en el mismo PR.
- El smoke MCP sincroniza un extra más en el job; si el tiempo del job crece
  demasiado, moverlo a un job aparte con cache de uv.
- **Deferred:** reactivar Codecov o un patch gate de cobertura — el badge
  autogenerado es la señal actual; reevaluar tras el Plan 123.
