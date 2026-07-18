# Plan 061: Quickstart de consumo desde R (arrow + duckdb)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- docs/ mkdocs.yml README.md .github/workflows/pypi-release.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction / docs
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

La audiencia secundaria del product-spec (investigadores, periodistas, civic
tech) usa R masivamente, y los artefactos del hub **ya son consumibles desde R
sin escribir una línea de código nuevo**: el ZIP del bundle se descarga desde
GitHub Releases y los Parquet/DuckDB los leen `arrow` y `duckdb` nativamente.
Lo único que falta es documentación: hoy no existe ni una mención a R en el
repo (grep verificado). Es la expansión de audiencia más barata posible — solo
recetas sobre artefactos existentes.

## Current state

- `docs/installation.md` — **estilo a imitar**: secciones cortas con bloques de
  código copy-pasteables ("PyPI", "Caché de datos", "Artefactos locales y sin
  conexión"). Español, tono directo.
- `mkdocs.yml` nav (L51–58):

  ```yaml
  nav:
    - Sitio público: https://tooltician.com/chile-hub/
    - Inicio: index.md
    - Instalación: installation.md
    - Referencia de API: api.md
    - Criterios de inclusión: dataset-inclusion-criteria.md
    - Compatibilidad de datasets: dataset-compatibility-policy.md
    - Política de versionado: versioning-policy.md
  ```

- El bundle se adjunta a cada GitHub Release como
  `chile-hub-publishable-bundle.zip` (verificado en
  `.github/workflows/pypi-release.yml` L170–187), por lo que la URL
  `https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip`
  es estable.
- El sitio estático sirve `data/normalized/` (los badges del README apuntan a
  `https://tooltician.com/chile-hub/data/normalized/*.json`) — Parquet
  individuales también son accesibles por URL, p. ej.
  `https://tooltician.com/chile-hub/data/normalized/comunas.parquet`
  (el executor debe verificar una URL real con `curl -sI` en Step 2 antes de
  publicarla en la doc).
- `docs/index.md` — portada del sitio MkDocs (mirar su estructura antes de
  enlazar; el quickstart se agrega al nav y se menciona desde installation).
- Verificación de docs: `make docs-build` (mkdocs build, existe en Makefile —
  target `docs-build` confirmado en plan 021 archivado).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Build docs | `make docs-build` | exit 0 (mkdocs sin warnings de nav) |
| Verificar URL bundle | `curl -sIL -o /dev/null -w "%{http_code}" https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip` | `200` |
| Verificar URL parquet estático | `curl -sI https://tooltician.com/chile-hub/data/normalized/comunas.parquet` | `200` (o ajustar la receta a la URL real) |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope** (the only files you should modify/create):
- `docs/r-quickstart.md` (crear)
- `docs/installation.md` (1 párrafo de enlace al final)
- `mkdocs.yml` (1 línea en `nav:`)
- `README.md` (opcional: 1 línea en la sección de instalación/consumo, fuera
  de bloques delimitados)

**Out of scope** (do NOT touch, even though they look related):
- `src/`, `data/`, workflows — no hay código nuevo.
- Snippets ejecutables en CI: no hay R en CI; la verificación de los snippets
  es manual/local (ver Maintenance notes).
- Traducción al inglés de la doc (decisión de i18n ya tomada en plan 049: el
  repo unificó a español; el quickstart va en español).
- Un paquete R (`chilehub` en CRAN) — explícitamente fuera; esto es solo docs.

## Git workflow

- Branch: `advisor/061-r-quickstart`
- Commit: `docs(r): quickstart de consumo desde R con arrow y duckdb`
- No pushear ni abrir PR salvo instrucción del operador.

## Steps

### Step 1: Crear `docs/r-quickstart.md`

Estructura (siguiendo el tono de `installation.md`):

1. **Frontmatter YAML** igual estilo que otros docs del repo (mirar
   `docs/installation.md` líneas 1–12 si tiene frontmatter; si no tiene, sin
   frontmatter — imitar el archivo vecino).
2. `# Uso desde R` + párrafo: el hub publica artefactos (Parquet, DuckDB, ZIP)
   que R lee nativamente; no hace falta el paquete Python.
3. **Opción A — ZIP del bundle (recomendada)**:

   ```r
   url <- "https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip"
   tmp <- tempfile(fileext = ".zip")
   download.file(url, tmp, mode = "wb")
   unzip(tmp, exdir = "chile-hub-data")

   library(arrow)
   comunas <- read_parquet("chile-hub-data/comunas.parquet")
   head(comunas)
   ```

   Nota bajo el bloque: verificar integridad con
   `chile-hub-publishable-bundle.zip.sha256` (`tools::md5sum` no aplica; usar
   `openssl dgst -sha256` o el paquete `digest`) — una línea, sin código
   elaborado.
4. **Opción B — Parquet individual por URL** (solo si el `curl` de la tabla de
   comandos confirma 200; si no, omitir la opción B y dejar solo A + C):

   ```r
   library(arrow)
   comunas <- read_parquet("https://tooltician.com/chile-hub/data/normalized/comunas.parquet")
   ```
5. **Opción C — DuckDB (cruces SQL)**:

   ```r
   library(duckdb)
   con <- dbConnect(duckdb(), "chile-hub-data/chile_data.duckdb", read_only = TRUE)
   dbGetQuery(con, "SELECT nombre_comuna, poblacion_censada FROM comunas JOIN censo_comunal USING (codigo_comuna) ORDER BY poblacion_censada DESC LIMIT 10")
   dbDisconnect(con, shutdown = TRUE)
   ```

   (Verificar el nombre real de la tabla DuckDB de censo en
   `data/dataset_catalog_config.json` → `outputs.duckdb_table` antes de
   escribir el query; usar solo tablas que existen.)
6. **Notas finales**: `codigo_comuna` es string de 5 chars con cero inicial
   (leer con `col_types`/`schema` string, nunca numérico — mismo invariante del
   hub); enlace a `docs/datasets/` para schemas y a `docs/installation.md` para
   el ecosistema Python.

**Verify**: `grep -c "read_parquet" docs/r-quickstart.md` → ≥2 · y
`grep -c "duckdb" docs/r-quickstart.md` → ≥1

### Step 2: Verificar las URLs publicadas

Corre los dos `curl` de la tabla de comandos. Si la URL del ZIP no da 200,
revisa el último release (`gh release view --json assets` si `gh` está
disponible, o la página de releases) y ajusta el nombre del asset en la receta
— el nombre correcto es el que sube `pypi-release.yml`. Si el Parquet estático
no da 200, elimina la Opción B.

**Verify**: ambas URLs verificadas (o la decisión documentada en el PR de
omitir B).

### Step 3: Enlazar en nav e instalación

- `mkdocs.yml`: agrega `- Uso desde R: r-quickstart.md` después de la línea
  `- Instalación: installation.md` (indentación YAML de 2 espacios, igual que
  las vecinas).
- `docs/installation.md`: al final, un párrafo "## Desde R" de 2 líneas que
  enlace a `r-quickstart.md`.
- (Opcional) `README.md`: una línea en la sección de instalación, **fuera** de
  cualquier bloque `<!-- START_* -->`.

**Verify**: `make docs-build` → exit 0, sin warnings de nav por
`r-quickstart.md` · y (si se tocó README)
`python scripts/sync_docs.py --check` → exit 0

## Test plan

- Sin tests nuevos (doc-only). Verificaciones: `make docs-build` (nav válido),
  `make doctor` (gates anti-drift — `docs/` no dispara reglas de co-cambio
  para este cambio; confirmarlo corriéndolo), y los `curl` de Step 2.
- Los snippets R no se ejecutan en CI (no hay R): el executor DEBE ejecutar al
  menos la Opción A localmente si R está instalado (`which Rscript`); si no lo
  está, documentar en el PR que los snippets fueron revisados sintácticamente
  pero no ejecutados (checkbox en la descripción del PR, no en el código).

## Done criteria

- [ ] `docs/r-quickstart.md` existe con ≥3 opciones (o 2 + decisión documentada)
- [ ] `make docs-build` exit 0 sin warnings de nav
- [ ] URL del ZIP verificada con `curl` (200)
- [ ] Tablas/columnas citadas existen en el catálogo/contratos
- [ ] `make doctor` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) si:

- La URL `releases/latest/download/chile-hub-publishable-bundle.zip` no
  existe y el mecanismo de publicación cambió (la premisa de la receta queda
  inválida — requiere decisión, no improvisación).
- `docs/installation.md` o los docs vecinos tienen frontmatter YAML y el
  formato exacto no es deducible (imitar, no inventar campos).
- Se descubre que el sitio estático dejó de servir `data/normalized/`
  (afectaría también a los badges del README — es un incidente mayor que este
  plan; reportar).
- Un step falla dos veces tras un intento razonable de fix.

## Maintenance notes

- Si el nombre del asset del bundle cambia en `pypi-release.yml`, hay que
  actualizar la receta (es texto, no hay verificación mecánica — candidato a
  guardrail de texto en `tests/test_ci_config.py` si alguna vez drifta;
  diferido hasta que ocurra una vez).
- Follow-up natural (fuera de scope): agregar snippets R a `usage_examples`
  del catálogo (`data/dataset_catalog_config.json`) para que aparezcan en la
  landing y en `docs/datasets/*.md` — hoy el catálogo solo lleva
  `python`/`duckdb`/`cli`.
- En review, escrutar: que la receta DuckDB use tablas reales del catálogo
  (`outputs.duckdb_table`) y que el aviso del cero inicial de `codigo_comuna`
  esté presente (es el error #1 que cometería un usuario R con
  `read_parquet` + joins).
