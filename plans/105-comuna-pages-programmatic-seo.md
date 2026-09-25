# Plan 105: Páginas por comuna (SEO programático) generadas desde el perfil territorial

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 039fc03..HEAD -- scripts/build_comuna_pages.py .gitignore .github/workflows/pages-deploy.yml sitemap.xml tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (contenido generado en masa: debe ser útil y único, no thin content)
- **Depends on**: 102 (el `sitemap.xml` index declara `comunas/sitemap.xml`)
- **Category**: distribution
- **Planned at**: commit `039fc03`, 2026-09-25

## Why this matters

chile-hub publica 346 comunas, pero no tiene una sola URL por comuna. El
long-tail de búsqueda ("población comuna X", "colegios comuna X", "pobreza
comuna X") está sin reclamar, y cada municipalidad, periodista o estudiante que
busca una comuna aterriza en portales lentos o de terceros. La capa
`perfil_territorial_comunal` ya trae 49 métricas consolidadas por comuna
(población, vivienda, salud, educación, finanzas, aire, vitales) más pobreza
SAE en `pobreza_comunal`; generar una página estática única por comuna desde
esos datos es costo marginal cero y contenido genuinamente útil, verificable y
atribuido. La página se genera en el deploy, no se commitea.

## Current state

- `data/normalized/perfil_territorial_comunal.parquet` — 346 filas × 49 columnas
  (`codigo_comuna`, `nombre_comuna`, `nombre_comuna_clean`, `poblacion_censada`,
  `establecimientos_salud_total`, `matricula_total`, `ingresos_totales`,
  `mp25_promedio_ultimo_anio`, etc.). `grep -c` de duplicados en
  `nombre_comuna_clean` = **0** (slugs sin colisión hoy).
- `data/normalized/pobreza_comunal.parquet` — 346×2 filas, `dimension` ∈
  `{ingresos, multidimensional}`, año 2022.
- `.github/workflows/pages-deploy.yml:55-58` — `uv run mkdocs build` (site_dir
  `reference/`) y sube `.` como artefacto de Pages. El job **no** corre `make build`:
  lee los Parquet ya committeados.
- `.gitignore:51` ignora `/reference/`; no existe regla para `/comunas/`.
- `sitemap.xml` pasa a sitemapindex en el Plan 102 y ya declara
  `comunas/sitemap.xml`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Generar | `./.venv/bin/python scripts/build_comuna_pages.py --out-dir /tmp/chile-hub-comunas` | declared | `347 páginas` + sitemap |
| Tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "ComunaPages"` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**:
- `scripts/build_comuna_pages.py` (nuevo, generador determinista)
- `.gitignore` (regla `/comunas/`)
- `.github/workflows/pages-deploy.yml` (step de generación post-mkdocs)
- `tests/test_pipeline_logic.py` (`ComunaPagesTests`)

**Out of scope**:
- Commitear las 346 páginas: se generan en el deploy (igual que `reference/`).
- Rediseñar la landing (`index.html`/`app.js`): no se tocan.
- Graficar series históricas por comuna: versión 1 es tabla de indicadores + JSON-LD.
- Reescribir/duplicar cifras: los valores salen siempre del Parquet, nunca
  hardcodeados en el script.

## Git workflow

- Branch: `advisor/distribution-wave-1` (wave 101–105).
- Commit por step; conventional commits (ej. `feat(seo): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Render puro de una comuna

Implementar en `scripts/build_comuna_pages.py` funciones puras (sin I/O) para
testear:
- `comuna_slug(row)` → `nombre_comuna_clean` con espacios reemplazados por `-`;
  si hay colisión en el dataset, sufijo `-{codigo_comuna}` (hoy no ocurre, pero
  el generador debe fallar ruidoso si detecta una colisión sin resolver).
- `render_comuna_page(row, pobreza_ingresos, pobreza_multidim)` → HTML completo
  con: `<title>` y meta description únicos ("Comuna de {nombre}: población,
  pobreza y datos oficiales"), tabla de indicadores agrupada (identidad,
  demografía, hogares, pobreza, servicios, municipio, territorio), links al
  Parquet/JSON del perfil, atribución por fuente y `Dataset` JSON-LD
  (`spatialCoverage` = comuna, `isPartOf` = catálogo). **Escapar todo valor de
  texto** (`html.escape`) — hay nombres con tildes y apóstrofes.
- `render_index(rows)` → página hub agrupada por región con enlaces.
- `render_sitemap(urls)` → XML con `lastmod` fijo de la fecha de generación
  pasada como argumento (no `datetime.now()` oculto), para que sea determinista
  en tests.

**Verify**: `./.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from scripts.build_comuna_pages import comuna_slug; print(comuna_slug({'nombre_comuna_clean':'nunoa','codigo_comuna':'13120'}))"` → `nunoa`.

### Step 2: Generador CLI

`main(argv)` con `--out-dir` (default `comunas/`), `--perfil`, `--pobreza`,
`--site-url` y `--generated-at`. Lee los Parquet con Polars, hace el join de
pobreza por `codigo_comuna` (dimensiones `ingresos` y `multidimensional`),
valida 346 filas únicas de `codigo_comuna`/`nombre_comuna_clean` (STOP si no),
y escribe `index.html`, `{slug}/index.html` y `sitemap.xml`. Falla ruidoso si
falta un Parquet o hay columnas requeridas ausentes.

**Verify**: `./.venv/bin/python scripts/build_comuna_pages.py --out-dir /tmp/chile-hub-comunas` → imprime `346 comunas + 1 índice + sitemap`; `find /tmp/chile-hub-comunas -name index.html | wc -l` → 347.

### Step 3: Wiring de deploy + `.gitignore`

En `pages-deploy.yml`, después del step del Plan 102, agregar la generación
`uv run python scripts/build_comuna_pages.py --out-dir comunas
--site-url https://tooltician.com/chile-hub`. Agregar `/comunas/` a
`.gitignore`.

**Verify**: `grep -n "build_comuna_pages" .github/workflows/pages-deploy.yml` y `git check-ignore -v comunas/x` → matchea la regla.

### Step 4: Tests

En `tests/test_pipeline_logic.py`, clase `ComunaPagesTests` con fixtures
sintéticas (2 comunas, una con tilde/ñ y una con apóstrofe):
- `render_comuna_page` incluye el nombre escapado, el CUT como texto de 5 y un
  bloque JSON-LD parseable.
- `comuna_slug` colisiona → STOP explícito (SystemExit con mensaje).
- `render_sitemap` contiene exactamente las URLs dadas y escapa `&`.
- El generador con Parquet sintéticos en `tmp_path` produce 347 archivos y es
  determinista (dos corridas con el mismo `--generated-at` → bytes iguales).

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k ComunaPages` → all pass.

## Test plan

- Nuevos: `ComunaPagesTests` (≥5 tests, sin red ni `data/normalized/`).
- Regresión: `make doctor` y el generador real sobre los Parquet del repo.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `./.venv/bin/python scripts/build_comuna_pages.py --out-dir /tmp/chile-hub-comunas` exit 0 con 347 `index.html` y `sitemap.xml`
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py -q` exits 0
- [ ] `make doctor` exits 0
- [ ] `grep -q "build_comuna_pages" .github/workflows/pages-deploy.yml` y `.gitignore` ignora `/comunas/`
- [ ] `git diff --name-only 039fc03...HEAD` lista sólo archivos in-scope
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog actualizados

## STOP conditions

Stop and report back (do not improvise) if:

- `perfil_territorial_comunal.parquet` no tiene 346 filas únicas por
  `codigo_comuna` o cambia de esquema.
- Hay colisión de `nombre_comuna_clean` sin una regla de slug definida.
- El generador necesita generar más de ~400 páginas o tarda >30 s (el job de
  Pages tiene timeout de 10 min: sería señal de un join mal hecho).
- Una verificación falla dos veces tras un intento razonable de fix.

## Maintenance notes

- La fuente única de las cifras es el Parquet: nunca copiar valores al script.
- Reviewer: verificar que cada página tenga meta description y `<title>` únicos
  (dos comunas no deben compartir título) y que la atribución de fuentes
  (`DATA_LICENSES.md`) esté visible.
- Deferido: páginas por región/provincia y gráficos históricos; sólo si el
  long-tail por comuna muestra impresiones en Search Console.
