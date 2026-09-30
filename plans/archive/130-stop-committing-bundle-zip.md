# Plan 130: Dejar de versionar el ZIP publicable (mantener su entrega por Release/HF)

> **Executor instructions**: Este plan tiene un gate de decisión en el Step 0.
> Si el mantenedor no confirma la estrategia de descarga, detente (no hay plan).
> Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- .gitignore .github/workflows/pipeline-check.yml index.html scripts/verify_landing.py tests/test_phase1_characterization.py tests/test_chile_hub.py README.md CONTRIBUTING.md src/builders/artifacts.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P3
- **Effort**: S-M
- **Risk**: MED
- **Depends on**: none (decisión de mantenedor en Step 0)
- **Category**: perf / repo
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`data/normalized/chile-hub-publishable-bundle.zip` (~30 MB) se re-commitea a
diario por el job `publish` (`.gitignore:16-19` lo re-incluye explícitamente;
`pipeline-check.yml:597-602` hace `git add --all data/normalized/`). Es un
reempaquetado de Parquet/JSON que ya viajan por separado, y ya existe como
asset de Release + espejo HF. Costo medido: 61 blobs del ZIP en el pack (~122
MB, ~2 MB por versión tras delta), 57 versiones sueltas, pack total ~160 MB y
crecimiento estable de ~2 MB/día (~0.7 GB/año); `fetch-depth: 0` en CI
(`pipeline-check.yml:568`) clona ese historial todos los días.

El beneficio es repo/CI; el riesgo es consumer-facing (la landing enlaza el ZIP
por ruta relativa). Por eso el Step 0 y los STOP.

## Current state

- `.gitignore:12-19`:
  ```
  data/normalized/*
  !data/normalized/*.json
  ...
  !data/normalized/*.zip
  !data/normalized/*.sha256
  ```
- `pipeline-check.yml:597-602` (job `publish`, schedule/dispatch): commit
  `chore(data): daily refresh [skip ci]` con `git add --all data/normalized/`.
- `index.html` enlaza `data/normalized/chile-hub-publishable-bundle.zip`
  (~`:3499`; verifica la línea exacta antes de editar).
- `scripts/verify_landing.py` y `tests/test_phase1_characterization.py:57,204-205,418-423,503-520`
  referencian el ZIP y su `.sha256` como artefactos de `data/normalized/`
  (los tests corren tras `make build`, no dependen de que esté en git).
- `src/builders/artifacts.py` genera el ZIP + `.sha256` y los liga al
  manifiesto (`attach_publishable_package_to_manifest`).
- `pypi-release.yml:349-366` adjunta el ZIP y `.sha256` al GitHub Release, y
  `hf-publish` sube el catálogo a HF.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Build | `make build` | declared | ZIP + sha en `data/normalized/` |
| Bundle | `make package-bundle` | declared | ZIP regenerado |
| Landing smoke | `make verify-landing` | declared | exit 0 |
| Tests artefactos | `./.venv/bin/pytest tests/test_phase1_characterization.py tests/test_builders_artifacts.py tests/test_chile_hub.py -v` | declared | verde |

## Scope

**In scope**:
- `.gitignore`
- `index.html` (link de descarga), `scripts/verify_landing.py` si assertea el href
- `README.md` / `CONTRIBUTING.md` (nota de clone parcial, opcional pero recomendada)
- tests que asumen que el ZIP está versionado (no que se construya)

**Out of scope**:
- Reescribir el historial de git (ADR-021 excluyó explícitamente reescribir
  historia).
- Cambiar el contenido del ZIP o el manifiesto.
- Borrar el ZIP del último commit (queda como está; solo se deja de actualizar).

## Git workflow

- Branch: `advisor/130-stop-committing-bundle-zip`
- Commits: `chore(repo): deja de versionar el ZIP publicable` (estilo repo).
- No push/PR.

## Steps

### Step 0: Decisión (obligatoria)

Confirma con el mantenedor (o si hay instrucción previa en el PR/issue):

- ¿La descarga del ZIP en la landing puede apuntar al asset del **último
  Release** (`https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip`)
  o al espejo HF?
- ¿Se acepta que entre releases el ZIP de la landing quede en la versión del
  último Release en vez del refresh diario?

Si la respuesta es "mantener la ruta relativa del repo", **STOP**: no hay plan.

Recomendación del advisor: sí — el ZIP es un paquete "todo en uno" para
descarga manual; los consumidores de datos usan Parquet/DuckDB/paquetes, que sí
siguen actualizándose a diario en el repo. El asset de Release está versionado
y es reproducible.

### Step 1: Ignorar el ZIP (dejar de commitearlo)

En `.gitignore`, elimina `!data/normalized/*.zip` (y decide sobre
`!data/normalized/*.sha256`: el sidecar sin el ZIP versionado no aporta;
recomendado quitarlo también y subirlo solo al Release). Deja un comentario
explicando que el ZIP viaja por Release/HF y no por git (evita que alguien lo
re-agregue).

Nota: `git rm --cached data/normalized/chile-hub-publishable-bundle.zip*` NO es
necesario para que deje de actualizarse, pero el próximo publish ya no lo
commiteará. **No** borres el archivo del árbol de trabajo.

**Verify**: `git check-ignore -v data/normalized/chile-hub-publishable-bundle.zip`
→ imprime la regla; `make build` sigue dejando el ZIP en disco.

### Step 2: Link de la landing al Release

- `index.html`: cambia el `href` del botón de descarga del bundle a
  `https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip`.
- Si `scripts/verify_landing.py` verifica el `href` o que el archivo local
  exista, actualízalo (el objetivo sigue existiendo en disco tras `make build`;
  el smoke local no debe depender de que exista en git).
- Si el botón muestra el tamaño del archivo desde un JSON, verifica de dónde
  sale y ajusta si es necesario.

**Verify**: `make verify-landing` → exit 0; `grep -n "releases/latest/download"
index.html` → 1; con red, `curl -sI <href> | head -1` → 302/200.

### Step 3: Documentar clone parcial

- `README.md` (sección de desarrollo) y/o `CONTRIBUTING.md`: agrega
  "Para clones más livianos: `git clone --filter=blob:none
  https://github.com/cortega26/chile-hub`".
- No cambies `fetch-depth: 0` del CI (lo necesita semantic-release).

### Step 4: Ajustar tests que asumen versionado

`grep -rn "publishable-bundle" tests/` y revisa cada assert:
- Los que verifican existencia/consistencia tras `make build` siguen igual.
- Si alguno afirma que el archivo está **en git** (p. ej. `git ls-files`),
  actualízalo.

**Verify**: `./.venv/bin/pytest tests/test_phase1_characterization.py
tests/test_builders_artifacts.py tests/test_chile_hub.py -v` → verde.

### Step 5: Cierre

`make lint`, `make format-check`, `make doctor`, índice. Deja constancia en el
PR del ahorro estimado (~2 MB/día) y de la decisión del Step 0.

## Test plan

- Los tests de artefactos existentes deben pasar sin cambios (construyen el
  ZIP en runtime).
- Nuevo guardrail opcional: en `tests/test_ci_config.py`, un assert de que
  `.gitignore` ignora `*.zip` bajo `data/normalized` (evita re-drift).

## Done criteria

- [ ] `git check-ignore -v data/normalized/chile-hub-publishable-bundle.zip` → match
- [ ] `grep -n "releases/latest/download" index.html` → 1
- [ ] `make verify-landing` → exit 0
- [ ] `./.venv/bin/pytest tests/test_phase1_characterization.py tests/test_builders_artifacts.py tests/test_chile_hub.py -v` → verde
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Step 0 sin confirmación → STOP.
- Si el botón de descarga del sitio se alimenta de un asset que solo existe en
  `data/normalized/` (p. ej. un JSON con `file` local) y no hay URL de Release
  viable, STOP y reporta el mecanismo.
- Si quitar `*.sha256` del versionado rompe `verify_pipeline` o el manifest,
  deja el sha versionado y quita solo el ZIP; reporta la diferencia.
- Si el diff de `tests/` excede ajustes de 1-2 asserts, STOP (señal de
  dependencia oculta).

## Maintenance notes

- El ZIP de disco sigue generándose en cada build/publish para adjuntarse al
  Release; lo único que cambia es que no se versiona.
- La landing ahora sirve la versión del último Release con assets
  (`ready=true`); si la cadencia de releases se detiene, revisar si conviene
  volver a versionarlo.
- **Deferred:** limpiar el historial (BFG/filter-repo + coordinación de todos
  los clones) — explosivo y excluido por ADR-021; reevaluar solo si el tamaño
  del clon causa un incidente real.
