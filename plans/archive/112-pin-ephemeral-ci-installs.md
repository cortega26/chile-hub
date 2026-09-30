# Plan 112: Los entornos efímeros de CI instalan versiones pinneadas (sin `--with` flotante)

> **Executor instructions**: Sigue este plan paso a paso y corre cada
> verificación. Si algo de "STOP conditions" ocurre, detente y reporta. Al
> terminar, actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- pyproject.toml uv.lock .github/workflows/pypi-release.yml .github/workflows/hf-publish.yml .github/workflows/pipeline-check.yml tests/test_ci_config.py`
> Si algo cambió, compara con "Current state" antes de seguir; mismatch = STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security / deps
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Tres rutas de CI instalan/ejecutan paquetes resolviendo "la última versión" en
cada corrida, fuera de `uv.lock`:

1. `pypi-release.yml:442` — `uv pip install --system huggingface_hub` en un job
   que tiene `HF_TOKEN`.
2. `hf-publish.yml:56` — `uv run --no-project --with huggingface_hub`.
3. `pipeline-check.yml:289` — el fetch de `autoridades_electas` con siete
   `--with` sin versión (alimenta datos publicados: sin scrapling el extractor
   degrada a 155 registros y el publish se aborta).

Una release upstream comprometida o simplemente rompedora cambia el resultado
de un job privilegiado sin ningún diff en el repo, violando la regla de pinning
del propio repo (AGENTS.md §7/§10: tooling de pipeline con `==` y lockfile como
contrato).

## Current state

- `pyproject.toml:36-41` runtime; `:44-102` extras (`pipeline`, `query`,
  `geo`, `validation`, `mcp`, `dev`); `:104-110` extra `scraping` con
  `scrapling[fetchers]>=0.4.10`; `:112-117` `[tool.uv] conflicts` dev↔scraping.
- `pypi-release.yml:437-443`:
  ```yaml
      - name: Publish to Hugging Face Hub
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          ...
          uv pip install --system huggingface_hub
          python scripts/publish_hf_dataset.py --repo-id cortega26/chile-hub
  ```
- `hf-publish.yml:44-58`: `uv run --no-project --with huggingface_hub python
  scripts/publish_hf_dataset.py --repo-id cortega26/chile-hub`.
- `pipeline-check.yml:283-289`: `PYTHONPATH=src uv run --no-project --with
  "scrapling[fetchers]" --with polars --with requests --with structlog --with
  tenacity --with curl_cffi --with defusedxml python src/extractors/autoridades_electas_extractor.py`.
- `scripts/publish_hf_dataset.py` importa `huggingface_hub` de forma perezosa
  (`:225-227`), por eso hoy se instala al vuelo.
- `tests/test_ci_config.py` — patrón de guardrails de texto; agrega
  `SCRIPTS_DIR`/`ROOT_DIR` a `sys.path` (`:14-24`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Relock | `uv lock` | declared | escribe `uv.lock` sin error |
| Lock check | `uv lock --locked` | declared | exit 0 |
| Sync publish extra | `uv sync --extra publish` | declared | instala `huggingface_hub` |
| Import smoke | `uv run --extra publish python -c "import huggingface_hub; print(huggingface_hub.__version__)"` | declared | imprime versión |
| Test focal | `./.venv/bin/pytest tests/test_ci_config.py -v` | declared | verde |

## Scope

**In scope**:
- `pyproject.toml` (extra nuevo `publish`)
- `uv.lock` (regenerado por `uv lock`)
- `.github/workflows/pypi-release.yml`, `.github/workflows/hf-publish.yml`,
  `.github/workflows/pipeline-check.yml` (solo las líneas de instalación)
- `tests/test_ci_config.py`

**Out of scope**:
- Subir el floor de `scrapling` en el extra `scraping` (puede quedar como está;
  el pin duro va en el `--with` del workflow, o en el extra si el lock lo
  resuelve exacto — elige una y documenta).
- Cambiar flujos, permisos o pasos de publicación.
- `scripts/publish_hf_dataset.py` (no cambia).

## Git workflow

- Branch: `advisor/112-pin-ephemeral-ci-installs`
- Commits: `fix(ci): pinnea entornos efímeros de publicación` (estilo repo).
- No push/PR salvo instrucción.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_ci_config.py -v` y `uv lock --locked` deben
pasar en el checkout limpio. Si no, STOP.

### Step 1: Agregar el extra `publish` a `pyproject.toml`

En `[project.optional-dependencies]`, agrega:

```toml
# Cliente de Hugging Face usado por scripts/publish_hf_dataset.py y por los
# jobs de publicación (pypi-release, hf-publish). Pin exacto + lock: el job
# corre con HF_TOKEN, no puede resolver "latest" desde PyPI (Plan 112).
publish = [
    "huggingface_hub==<VERSION_RESUELTA>",
]
```

Para `<VERSION_RESUELTA>` ejecuta `uv lock` una vez con un floor temporal
(`huggingface_hub>=0.30`), lee la versión exacta con
`grep -A2 'name = "huggingface_hub"' uv.lock` y fíjala con `==`; luego
`uv lock` de nuevo.

### Step 2: Usar el extra en `hf-publish.yml`

Reemplaza el `run:` de `:56` por:

```yaml
          uv run --extra publish \
            python scripts/publish_hf_dataset.py --repo-id cortega26/chile-hub $args
```

(El resto del step, formato `args` y chequeo de `HF_TOKEN`, no cambia.)

### Step 3: Usar el lock en `pypi-release.yml`

- En `pypi-release.yml`, el step `Install package build dependencies` (`:58-67`)
  pasa a `uv sync --extra dev --extra pipeline --extra publish`.
- Elimina la línea `uv pip install --system huggingface_hub` (`:442`) — el
  entorno del job ya la tiene por lock.

### Step 4: Pinnear el entorno stealth de `pipeline-check.yml`

Reemplaza `:289` por la misma línea con `==` en cada `--with`. Versiones a
usar (sácalas de `uv.lock`; el lock ya las resuelve en el fork `scraping`):

- `"scrapling[fetchers]==<v>`"
- `polars==<v>` (debe coincidir con la resuelta; el lock la fija)
- `requests==<v>`, `structlog==<v>`, `tenacity==<v>`, `curl_cffi==<v>`,
  `defusedxml==<v>`

Comando para extraer cada una:
`grep -B2 -A6 'name = "<paquete>"' uv.lock | grep 'version'`.
Si el lock no contiene el paquete (p. ej. scrapling en el fork), usa el
`version` que `uv lock` resolvió y verifica con un dry-run.

### Step 5: Guardrail test

En `tests/test_ci_config.py`, clase nueva `EphemeralInstallPinGuardrailTests`:
1. Lee `PIPELINE_CHECK_WORKFLOW` y afirma que **cada** token `--with` va
   seguido de una versión `==` (regex sobre el bloque de la línea del fetch;
   basta con afirmar que `--with "scrapling[fetchers]"` y `--with polars` no
   aparecen sin `==`).
2. Afirma que `pypi-release.yml` no contiene `uv pip install --system
   huggingface_hub` y sí `--extra publish`.
3. Afirma que `hf-publish.yml` contiene `--extra publish`.
4. Docstring con el incidente (supply-chain: último paquete sin pin en job con
   `HF_TOKEN`).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "EphemeralInstallPin" -v`
→ 3 tests pasan.

## Test plan

- Nuevos: `EphemeralInstallPinGuardrailTests` (3 asserts de texto).
- Patrón: `tests/test_ci_config.py:787` (`HfPublishJobGuardrailTests`).
- `uv lock --locked` debe seguir pasando (el lock nuevo debe quedar commiteado).

## Done criteria

- [ ] `grep -n "huggingface_hub" pyproject.toml uv.lock` → aparece con `==` en pyproject
- [ ] `grep -c "uv pip install --system huggingface_hub" .github/workflows/pypi-release.yml` → 0
- [ ] `grep -c "\-\-extra publish" .github/workflows/pypi-release.yml .github/workflows/hf-publish.yml` → ≥1 en cada uno
- [ ] `grep -n "\-\-with" .github/workflows/pipeline-check.yml` → todos con `==`
- [ ] `uv lock --locked` → exit 0
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -v` → verde
- [ ] `make lint` y `make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si agregar `publish` al lock choca con `[tool.uv] conflicts` (click u otro),
  detente y reporta: alternativa es pin inline `huggingface_hub==X` en ambos
  workflows y dejar el extra fuera.
- Si `uv run --extra publish` en CI dispara `uv sync` completo y el job
  `hf-publish` necesita `--no-project` por performance, detente y reporta el
  trade-off; no improvises un `--with huggingface_hub==X` sin lock.
- Si `uv lock` no puede resolver `scrapling` por red, STOP (entorno sin red).

## Maintenance notes

- Dependabot ya agrupa `python-pipeline`/`python-dev`; el extra `publish` debe
  quedar en un grupo similar (revisa `.github/dependabot.yml` en el mismo PR si
  existe y aplica).
- Cualquier `uv run --with` nuevo en workflows es un smell: el guardrail lo
  detecta solo si es `--with` sin `==`; un `--with` nuevo con `==` también
  debería revisarse en code review.
- **Deferred:** migrar el fetch stealth a un job que instale el extra
  `scraping` con `uv export`/`uv pip install -r` desde el lock — bloqueado por
  el conflicto click (pyproject `:112-117`); reevaluar cuando
  python-semantic-release migre de click.
