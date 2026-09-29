# Plan 126: Higiene de tooling y onboarding (ruff único, hook sync-docs, shim muerto, uv documentado, doctor lock, package-smoke, extracción stealth)

> **Executor instructions**: Sigue los pasos en orden; cada uno verifica solo.
> Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- .pre-commit-config.yaml .github/workflows/pipeline-check.yml pyproject.toml Makefile src/chile_hub.py README.md CONTRIBUTING.md docs/extraction-lanes.md tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1 (ruff) / P2 (resto)
- **Effort**: S-M
- **Risk**: LOW
- **Depends on**: coordina con Plan 122 en `pipeline-check.yml` (secuencial, no worktrees paralelos)
- **Category**: dx / tech-debt
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Siete defectos de higiene que, juntos, hacen que el "single source" de tooling
que el repo declara no exista en la práctica:

1. **ruff 0.16.7 vs 0.16.8**: CI (`pipeline-check.yml:97,100`, `uvx ruff@0.16.7`)
   y pre-commit (`.pre-commit-config.yaml:19-24`, `rev: v0.16.7`) quedaron atrás
   del pin de `pyproject.toml:88` (`ruff==0.16.8`, bump de Dependabot
   `b5f31e8`). `make lint` local corre 0.16.8 → pass local, fail CI (la
   discrepancia exacta que Plan 094 eliminó).
2. **Hook `sync-docs` que nunca dispara**: `files: ^(...|src/builders/|docs/adr/|tests/|contracts/datasets/)$`
   (`.pre-commit-config.yaml:44`) — el `$` ancla el match al nombre literal de
   directorio; `tests/test_x.py` jamás matchea.
3. **Shim `src/chile_hub.py` inalcanzable**: `find_spec("src.chile_hub")`
   resuelve al paquete `src/chile_hub/__init__.py`; el archivo sobrevive en el
   sdist (`pyproject.toml:142`) y coverage omit (`:214`).
4. **`uv` sin documentar**: `make bootstrap` empieza con `uv sync`
   (`Makefile:79-82`) y ni README (`:553-567`) ni CONTRIBUTING mencionan `uv`
   (grep `-in "uv"` → 0). El primer comando de un contributor falla.
5. **`doctor` no verifica el lock**: CI bloquea con `uv lock --locked`
   (`pipeline-check.yml:92-93`) pero `make doctor` no.
6. **`package-smoke` usa el binario global**: `Makefile:218` corre
   `chile-hub --help` tras instalar el wheel; sin venv activado falla, con un
   `chile-hub` global instalado prueba el binario equivocado.
7. **Extracción stealth indocumentada**: `autoridades_electas` degrada a 155
   registros sin scrapling; `docs/extraction-lanes.md:30-34` documenta solo la
   invocación de CI, no el comando local.

## Current state

- `.pre-commit-config.yaml:19-24` (ruff `rev: v0.16.7` + comentario "single-source"),
  `:39-44` (hook local `sync-docs` con `files:` anclado).
- `pipeline-check.yml:96-100` (`uvx ruff@0.16.7 check/format`).
- `pyproject.toml:88` (`ruff==0.16.8`), `:139-152` (sdist include con
  `/src/chile_hub.py`), `:203-215` (coverage omit con
  `src/chile_hub/cli.py`, `src/chile_hub/pipeline_status_utils.py`,
  `src/chile_hub.py`).
- `src/chile_hub.py` (21 líneas) — shim que delega al paquete.
- `Makefile:79-82` (`bootstrap`), `:87-95` (`doctor`), `:162-165` (`test -n auto`),
  `:215-218` (`package-smoke`).
- `README.md:553-567` (quickstart dev), `CONTRIBUTING.md:22-31` (checklist).
- `docs/extraction-lanes.md:30-34` (comando CI efímero).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Lint | `make lint` | declared | exit 0 |
| Format | `make format-check` | declared | exit 0 |
| Doctor | `make doctor` | declared | exit 0 |
| Tests CI config | `./.venv/bin/pytest tests/test_ci_config.py -v` | declared | verde |
| Package smoke | `make package-smoke` | declared | exit 0 |

## Scope

**In scope**:
- `.pre-commit-config.yaml`
- `.github/workflows/pipeline-check.yml` (solo líneas de ruff)
- `pyproject.toml` (sdist include + coverage omit)
- `Makefile` (bootstrap, doctor, package-smoke, target nuevo si se elige)
- `src/chile_hub.py` (eliminar)
- `README.md`, `CONTRIBUTING.md`, `docs/extraction-lanes.md`
- `tests/test_ci_config.py` (guardrails; la exención del shim en `SysPathIdiomTests:994`)

**Out of scope**:
- Cambiar la versión de ruff más allá de 0.16.8 (no bumpear a mano; Dependabot).
- `make test`/`coverage` (Plan 122).
- Reestructurar `bootstrap` más allá del guard de `uv`.

## Git workflow

- Branch: `advisor/126-tooling-onboarding-hygiene`
- Commits por paso: `fix(tooling): ...`, `docs(dx): ...`, `chore: ...`.
- No push/PR.

## Steps

### Step 0: Baseline

`make lint`, `make format-check`, `make doctor`, `./.venv/bin/pytest
tests/test_ci_config.py -q` verdes. Si no, STOP.

### Step 1: ruff 0.16.7 → 0.16.8

- `.pre-commit-config.yaml:19-24`: `rev: v0.16.7` → `v0.16.8`.
- `pipeline-check.yml:96-100`: `uvx ruff@0.16.7` → `0.16.8` (dos ocurrencias).
- Actualiza los comentarios "single-source" si nombran la versión.
- Guardrail: en `tests/test_ci_config.py` agrega un test que lea
  `pyproject.toml` (regex `ruff==([\d.]+)`), `.pre-commit-config.yaml`
  (`rev: v([\d.]+)` del repo ruff-pre-commit) y `pipeline-check.yml`
  (`uvx ruff@([\d.]+)`) y afirme que los tres coinciden.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "ruff" -v` → verde;
`grep -rn "0.16.7" .pre-commit-config.yaml .github/workflows/pipeline-check.yml`
→ 0 matches.

### Step 2: Hook `sync-docs`

En `.pre-commit-config.yaml:44`, cambia los directorios por patrones que
matcheen archivos:

```yaml
        files: ^(pyproject\.toml|README\.md|AGENTS\.md|src/chile_hub/datasets\.py|src/builders/.*|scripts/sync_docs\.py|docs/adr/.*|tests/.*|data/dataset_catalog_config\.json|contracts/datasets/.*)$
```

Agrega en `tests/test_ci_config.py` un test que cargue el YAML como texto,
extraiga el `files:` del hook `sync-docs` y verifique con `re.fullmatch` que
matchea `tests/test_x.py`, `docs/adr/ADR-001-x.md`, `src/builders/landing.py`,
`contracts/datasets/comunas.schema.json` y no matchea
`data/normalized/foo.parquet`.

**Verify**: `pre-commit run sync-docs --files tests/test_ci_config.py` (el
hook debe disparar) → ejecuta `make sync-docs` sin error.

### Step 3: Eliminar el shim `src/chile_hub.py`

- Verifica primero: `grep -rn "chile_hub\.py" src/ scripts/ tests/ Makefile
  pyproject.toml` y `python -B -c "import importlib.util;
  print(importlib.util.find_spec('src.chile_hub').origin)"` (debe apuntar al
  paquete).
- Elimina `src/chile_hub.py`, la línea `/src/chile_hub.py` del sdist include
  (`pyproject.toml:142`) y `"src/chile_hub.py"` del coverage omit (`:214`).
- Actualiza `tests/test_ci_config.py::SysPathIdiomTests` (`:994`) si exime o
  menciona el shim; el comentario del propio shim (si se cita en docs) no
  aplica.
- Verifica que `python -m src.chile_hub --help` y
  `PYTHONPATH=src python -m chile_hub --help` siguen funcionando.

**Verify**: `make doctor` → exit 0; `./.venv/bin/pytest tests/test_ci_config.py -k SysPath -v`
→ verde; `test ! -f src/chile_hub.py`.

### Step 4: Documentar `uv`

- `README.md` sección de desarrollo (`:553-567`): agrega prerrequisitos:
  "Requiere [uv](https://docs.astral.sh/uv/getting-started/installation/) y
  Git. Python lo gestiona uv (`make bootstrap`)."
- `CONTRIBUTING.md:22-31`: agrega `make bootstrap` como primer paso y el link
  de instalación de uv.
- `Makefile:79-82`: primera línea de `bootstrap`:
  ```make
  bootstrap:
  	@command -v uv >/dev/null 2>&1 || { printf "ERROR: uv no está instalado. Ver https://docs.astral.sh/uv/getting-started/installation/\n"; exit 1; }
  	uv sync --extra pipeline --extra dev
  ```

**Verify**: `grep -in "uv" README.md CONTRIBUTING.md` → ≥2 matches con link.

### Step 5: `doctor` con lock

Agrega a `doctor` (`Makefile:87-95`):
```make
	@uv lock --locked
```
(después de los `$(PYTHON) -c`, antes de los checkers). El `Makefile` es
compañero de AGENTS.md/README.md por `COMPANION_RULES`; este plan toca ambos.

**Verify**: `make doctor` → exit 0.

### Step 6: `package-smoke` con el binario del venv

`Makefile:218`: `chile-hub --help` → `$(PYTHON) -m chile_hub --help`
(usa el intérprete del venv; verifica cómo se define `PYTHON` arriba y usa la
misma variable que el resto de los targets).

**Verify**: `make package-smoke` → exit 0 (requiere build local; si no hay
red para reinstalar el wheel, `uv pip install --force-reinstall dist/*.whl`
funciona offline).

### Step 7: Documentar la extracción stealth local

- `docs/extraction-lanes.md` (sección de `autoridades_electas`): agrega el
  comando local:
  ```bash
  PYTHONPATH=src uv run --no-project --with "scrapling[fetchers]" \
    --with polars --with requests --with structlog --with tenacity \
    --with curl_cffi --with defusedxml \
    python src/extractors/autoridades_electas_extractor.py
  ```
  (espeja las versiones pinneadas del Plan 112 si ese plan ya aterrizó).
- `README.md` quickstart dev: nota de una línea + link a
  `docs/extraction-lanes.md`.
- Opcional: agrega target `extract-autoridades-electas` al Makefile con ese
  comando (si lo haces, el hook `Makefile → README.md|AGENTS.md` ya está
  cubierto por este mismo PR).

**Verify**: `grep -n "scrapling" docs/extraction-lanes.md README.md` → matches.

### Step 8: Cierre

`make lint`, `make format-check`, `make doctor`, tests focal. Índice.

## Test plan

- 3 guardrails nuevos: ruff único (Step 1), regex del hook (Step 2), y el de
  SysPath actualizado (Step 3).
- Verificación manual de comandos documentados (no automatizable).

## Done criteria

- [ ] `grep -rn "0.16.7" .pre-commit-config.yaml .github/workflows/pipeline-check.yml` → 0
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -v` → verde
- [ ] `test ! -f src/chile_hub.py` → true
- [ ] `grep -c "uv" README.md CONTRIBUTING.md` → ≥1 en cada uno
- [ ] `grep -n "uv lock --locked" Makefile` → 1
- [ ] `make doctor` → exit 0
- [ ] `make package-smoke` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `uv lock --locked` en `doctor` falla en el checkout (lock desincronizado),
  detente: no regeneres el lock para "arreglar" sin entender el diff.
- Si el hook `sync-docs` con el regex corregido empieza a disparar en commits
  que no tocan hechos de docs, reporta el falso positivo antes de dejar el
  patrón.
- Si eliminar `src/chile_hub.py` rompe algún import documentado (grep),
  reporta el uso; no lo elimines si hay consumidor real.
- Si `package-smoke` falla por red, reporta.

## Maintenance notes

- Las tres superficies de ruff (pyproject, pre-commit, CI) deben moverse
  juntas; el guardrail lo exige. Si Dependabot bumpea solo pyproject, el test
  falla y el PR de Dependabot necesita el bump en los otros dos.
- `doctor` ahora incluye el lock check; mantenerlo rápido (es un no-op si el
  lock está al día).
- **Deferred:** migrar la version de ruff del workflow a `uvx --from
  "ruff==$(pyproject)"` derivado en CI — requiere parsear pyproject en YAML;
  no vale hoy.
