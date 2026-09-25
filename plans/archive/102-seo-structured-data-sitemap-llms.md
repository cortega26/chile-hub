# Plan 102: Datos estructurados por dataset, sitemap index y `llms.txt`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 039fc03..HEAD -- sitemap.xml robots.txt src/builders/landing.py scripts/inject_dataset_json_ld.py .github/workflows/pages-deploy.yml tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW-MED
- **Depends on**: none (coordina con 105: `comunas/sitemap.xml` se declara aquí
  y lo genera el 105 en el mismo wave)
- **Category**: distribution
- **Planned at**: commit `039fc03`, 2026-09-25

## Why this matters

El sitio tiene 87 URLs indexables (la landing + 86 páginas de mkdocs), pero
`robots.txt` declara un único sitemap (`sitemap.xml`) que contiene **1 URL**:
la documentación completa queda descubrible sólo por crawling. Peor: las
páginas `reference/datasets/{nombre}/` tienen `canonical` pero **cero markup
schema.org**, por lo que no pueden aparecer en Google Dataset Search, el
catálogo que usan periodistas, analistas y agentes para encontrar datasets
públicos. Además, ningún agente que lee el sitio tiene un `llms.txt` que le
indique qué endpoints existen.

## Current state

- `robots.txt` (4 líneas) declara `Sitemap: https://tooltician.com/chile-hub/sitemap.xml`.
- `sitemap.xml` (9 líneas) contiene **una** `<url>` (`/chile-hub/`).
- `reference/sitemap.xml` lo genera mkdocs (`site_dir: reference`, `mkdocs.yml:6`)
  con 86 URLs, pero nadie lo declara.
- `reference/datasets/comunas/index.html` tiene `<link rel="canonical">` y
  `grep -c schema.org` = **0**.
- `src/builders/landing.py:65-98` ya construye el `DataCatalog` JSON-LD de
  `index.html` con `DISPLAY_NAMES`/`CREATORS` como fuente única de nombres y
  creadores por dataset.
- `.github/workflows/pages-deploy.yml:55-58` corre `uv run mkdocs build` y sube
  `.` como artefacto de Pages.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Doctor | `make doctor` | declared | exit 0 |
| MkDocs local | `make docs-build` | declared | exit 0, `reference/sitemap.xml` regenerado |
| Inyector | `./.venv/bin/python scripts/inject_dataset_json_ld.py --site-dir reference` | declared | N páginas con JSON-LD |
| Tests | `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q` | declared | all pass |

## Scope

**In scope**:
- `sitemap.xml` (pasa a `sitemapindex`) y `sitemap-pages.xml` (nuevo)
- `llms.txt` (nuevo, raíz del repo)
- `src/builders/landing.py` (función pura `build_dataset_json_ld(key, public_site_url)`)
- `scripts/inject_dataset_json_ld.py` (nuevo, post-build de mkdocs)
- `.github/workflows/pages-deploy.yml` (un step después de `mkdocs build`)
- `tests/test_pipeline_logic.py`, `tests/test_ci_config.py`

**Out of scope**:
- `index.html` / `app.js` y su JSON-LD: ya cubiertos por `check_landing_sync.py`;
  no duplicar `render_catalog_json_ld_block()`.
- Páginas por comuna: Plan 105 (aquí sólo se declara `comunas/sitemap.xml` en el índice).
- Meta tags/description de las páginas mkdocs: el template de Material no se toca.

## Git workflow

- Branch: `advisor/distribution-wave-1` (wave 101–105).
- Commit por step; conventional commits (ej. `feat(seo): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Sitemap index + páginas base

Convertir `sitemap.xml` en un `<sitemapindex>` que declare:
`sitemap-pages.xml`, `reference/sitemap.xml` y `comunas/sitemap.xml` (este
último lo crea el Plan 105 en el mismo wave; en local puede no existir hasta
correr el generador, y eso no es error). Crear `sitemap-pages.xml` con la
landing (`/`) y `privacy.html`, con `lastmod` de fecha fija ISO (no usar la
fecha de build: el archivo se commitea).

**Verify**: `./.venv/bin/python -c "import xml.dom.minidom as m; m.parse('sitemap.xml'); m.parse('sitemap-pages.xml'); print('ok')"` → `ok`.

### Step 2: `build_dataset_json_ld()` en `landing.py`

Agregar una función pura que devuelva el dict schema.org `Dataset` de una capa:
`name` (DISPLAY_NAMES con fallback a la clave), `description`, `url`
(f"{site}reference/datasets/{key}/"), `license`/`license_url`,
`creator` (CREATORS), `isPartOf` (DataCatalog de la landing), `spatialCoverage`
("Chile"), `inLanguage` ("es"), `distribution` (Parquet de
`data/normalized/{key}.parquet` cuando `outputs.parquet` exista). No inventar
nombres ni creadores: reusar los dicts existentes.

**Verify**: `./.venv/bin/python -c "from src.builders.landing import build_dataset_json_ld; print(build_dataset_json_ld('comunas','https://tooltician.com/chile-hub/')['@type'])"` → `Dataset`.

### Step 3: Inyector post-mkdocs (`scripts/inject_dataset_json_ld.py`)

Script stdlib que, para cada clave del catálogo (`data/dataset_catalog_config.json`)
con página en `reference/datasets/{key}/index.html`, inserta antes de `</head>`
un `<script type="application/ld+json" id="chile-hub-dataset-json-ld">`.
Idempotente por marcador (re-ejecutar no duplica). Si no hay ninguna página
`reference/datasets/*/index.html`, falla ruidoso (el build de docs no corrió o
cambió de layout). Si una capa puntual no tiene página, warning y sigue (sus
docs pueden estar archivadas). Flags `--site-dir` y `--catalog` para tests.

**Verify**: `make docs-build && ./.venv/bin/python scripts/inject_dataset_json_ld.py --site-dir reference` → imprime `N páginas con Dataset JSON-LD` con N ≥ 20, exit 0; segunda corrida imprime el mismo N (idempotente).

### Step 4: Wiring en Pages Deploy + `llms.txt`

En `pages-deploy.yml`, después de `uv run mkdocs build`, agregar el step
`uv run python scripts/inject_dataset_json_ld.py --site-dir reference`.
Crear `llms.txt` en la raíz con: descripción de una línea, y secciones
`## Datos` (catálogo DCAT `data.json`, `datapackage.json`, Parquet por capa,
mirror HF) y `## Documentación` (docs, quickstart R, acceso HTTP, MCP si existe).
Sin números hardcodeados que puedan derivar.

**Verify**: `grep -n "inject_dataset_json_ld" .github/workflows/pages-deploy.yml`; `curl`-free: `test -f llms.txt`.

### Step 5: Tests

En `tests/test_pipeline_logic.py`, clase `DatasetSeoTests`:
- `build_dataset_json_ld()` produce `@type: Dataset`, URL canónica de docs y
  contiene la palabra Chile en `spatialCoverage`.
- El inyector sobre un `reference/datasets/comunas/index.html` sintético en
  `tmp_path` inserta exactamente un `<script ... id="chile-hub-dataset-json-ld">`
  y es idempotente; con cero páginas de dataset levanta `SystemExit`.
En `tests/test_ci_config.py`, guardrails de texto: `sitemap.xml` es
`sitemapindex` y menciona los 3 hijos; `pages-deploy.yml` corre el inyector;
`robots.txt` sigue declarando un sitemap existente.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q` → all pass.

## Test plan

- Nuevos: `DatasetSeoTests` (3 tests lógicos) + 3 guardrails de CI.
- No requiere `data/normalized/` (catálogo + fixtures sintéticas).
- Regresión: `make doctor` (landing sync intacto) y `make docs-build`.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -c "<sitemap>" sitemap.xml` == 3 y `grep -q "sitemap-pages.xml" sitemap.xml`
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q` exits 0
- [ ] `make doctor` exits 0 y `make docs-build` exits 0
- [ ] `grep -q "inject_dataset_json_ld" .github/workflows/pages-deploy.yml` y `test -f llms.txt`
- [ ] `git diff --name-only 039fc03...HEAD` lista sólo archivos in-scope
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog actualizados

## STOP conditions

Stop and report back (do not improvise) if:

- `mkdocs build` deja de generar `reference/datasets/*/index.html` (cambio de
  layout) o el `site_dir` cambia en `mkdocs.yml`.
- El inyector tendría que tocar `index.html`/`app.js` (fuera de scope; eso ya
  lo gobierna `check_landing_sync.py`).
- `build_catalog_json_ld()` o sus dicts cambian de forma incompatible.
- Una verificación falla dos veces tras un intento razonable de fix.

## Maintenance notes

- `build_dataset_json_ld()` es la fuente única del hecho “página docs ↔ capa”:
  si se agrega una URL canónica nueva, se cambia ahí y en ningún otro lugar.
- Reviewer: mantener `sitemap.xml` sin `lastmod` por build (evita diffs de CI
  cada día); `lastmod` sólo con fecha real de cambio estructural.
- Deferido: `llms-full.txt` con el catálogo completo embebido — sólo si
  `llms.txt` muestra tráfico de agentes medible.
