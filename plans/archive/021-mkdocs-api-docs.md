# Plan 021: Publicar documentación de API con MkDocs Material + mkdocstrings

> **✅ DONE (2026-07-04).** Implementado con dos ajustes sobre el plan original:
> (1) `mkdocstrings[python]` se pineó a `==1.0.4` (la serie ya es 1.x, no `>=0.27`);
> (2) los SHAs pineados de `pages-deploy.yml` se tomaron de los vivos en
> `pipeline-check.yml` (`setup-python` v6.3.0 `ece7cb06…`, no el v6.2.0 del plan —
> drift confirmado). `timeout-minutes` del deploy subido de 5 a 10 por el paso de build.
> `docstring_style: google` confirmado. Verificado: `make docs-build` exit 0, la
> referencia de API extrae `ChileHub`/`ChileHubDataManager`/excepciones, `make lint`
> exit 0, `index.html`/`app.js` sin cambios, `/reference/` ignorado.

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar, actualiza la fila de estado de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat 140c8ea..HEAD -- pyproject.toml .github/workflows/pages-deploy.yml Makefile docs/ .gitignore`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `140c8ea`, 2026-06-29

## Why this matters

El proyecto invierte en docstrings (los exige con `interrogate`, ver `pyproject.toml`
`[tool.interrogate]`) y tiene una API pública rica en `src/chile_hub/core.py` (clase
`ChileHub`, ~40 métodos públicos), pero esos docstrings **no se publican** en ningún
sitio navegable. Además `docs/` ya contiene guías valiosas (instalación, ADRs, fichas
de datasets) que solo se leen como markdown crudo en GitHub. MkDocs Material +
mkdocstrings genera un sitio de documentación profesional que: (1) renderiza las guías
existentes y (2) autogenera la referencia de API desde los docstrings — sin duplicar
contenido. Es una mejora aditiva, de bajo riesgo, que aprovecha trabajo ya hecho.

## Current state

Archivos relevantes:

- `src/chile_hub/core.py` — clase `ChileHub` con docstrings en formato Google/NumPy
  (Args/Returns/Raises), p. ej. `validate_user_data` (líneas 343–362). Es el objetivo
  principal de la referencia autogenerada. El paquete vive bajo `src/`.
- `docs/` — guías existentes en markdown: `installation.md`, `product-spec.md`,
  `versioning-policy.md`, `adr/ADR-00X-*.md`, `datasets/*.md`, etc. **No hay
  `docs/index.md`** (hay que crearlo como home del sitio).
- `pyproject.toml` — `[project.optional-dependencies].dev` (líneas 57–73) es donde van
  las dependencias de docs. `[tool.interrogate].paths = ["src/chile_hub"]`.
- `.github/workflows/pages-deploy.yml` — **deploy de producción de la landing**. Hoy
  solo hace checkout y sube `path: .` (todo el repo) a GitHub Pages. Aquí se añade el
  build de docs antes del upload.
- `.gitignore` — ignora `data/*` con excepciones; NO ignora la raíz en general.

`pages-deploy.yml` actual (relevante, líneas 25–36):

```yaml
    steps:
      - name: Checkout repository
        uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0

      - name: Configure Pages
        uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: .
```

Pasos de setup pineados ya usados en `pipeline-check.yml` (reúsalos verbatim):

```yaml
      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
```

**Restricción de diseño**: la landing (`index.html`) se sirve en `/` del sitio
Pages. El sitio de docs se construye en una **subcarpeta** (`reference/`) y se sirve
en `https://tooltician.com/chile-hub/reference/`. NO se toca `index.html` ni la
estructura raíz de la landing.

Convención del repo: español neutral; dependencias pineadas; workflows con acciones
pineadas por SHA + comentario de versión; `uv` como gestor.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Instalar deps dev | `uv sync --extra dev` | exit 0 |
| Build docs | `.venv/bin/mkdocs build` | exit 0; crea `reference/` |
| Servir docs local | `.venv/bin/mkdocs serve` | sirve en :8000 |
| Lint (no debe romperse) | `make lint` | exit 0 |

## Scope

**In scope** (únicos archivos a crear/modificar):
- `pyproject.toml` — añadir `mkdocs-material` y `mkdocstrings[python]` a dev.
- `mkdocs.yml` — **crear** en la raíz: configuración del sitio.
- `docs/index.md` — **crear**: home del sitio de docs.
- `docs/reference.md` — **crear**: referencia de API con directivas mkdocstrings.
- `.github/workflows/pages-deploy.yml` — añadir build de docs antes del upload.
- `Makefile` — añadir targets `docs-build` y `docs-serve`.
- `.gitignore` — ignorar la carpeta de salida `reference/`.

**Out of scope** (NO tocar):
- `index.html`, `app.js` y la estructura raíz de la landing.
- El contenido de las guías existentes en `docs/` (solo se añaden index.md y
  reference.md; no se reescriben las demás).
- `--strict` en el build inicial (las guías existentes pueden tener enlaces relativos
  que generen warnings; limpiarlos es un follow-up — ver Maintenance notes).

## Git workflow

- Branch: `advisor/021-mkdocs-api-docs`
- Commits estilo conventional commits: ej.
  `docs(site): publicar referencia de API con MkDocs Material + mkdocstrings`.
- No hagas push ni abras PR salvo indicación del operador.

## Steps

### Step 1: Añadir dependencias de docs

En `pyproject.toml`, sección `[project.optional-dependencies].dev` (líneas 57–73),
añade dos líneas (pínealas a una versión reciente; verifica la última estable):

```toml
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.27",
```

Instala: `uv sync --extra dev`.

**Verify**: `.venv/bin/mkdocs --version` → imprime la versión de mkdocs.

### Step 2: Crear `mkdocs.yml`

Crea `mkdocs.yml` en la raíz del repo. `site_dir: reference` evita colisión con la
landing (`/`) y con `docs/` (fuente). `mkdocstrings` apunta a `src/` para encontrar el
paquete `chile_hub`:

```yaml
site_name: chile-hub
site_description: Datos públicos de Chile curados, normalizados y validados.
site_url: https://tooltician.com/chile-hub/reference/
repo_url: https://github.com/cortega26/chile-hub
docs_dir: docs
site_dir: reference

theme:
  name: material
  language: es
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy
  palette:
    - scheme: default
      primary: cyan
      toggle:
        icon: material/weather-night
        name: Modo oscuro
    - scheme: slate
      primary: cyan
      toggle:
        icon: material/weather-sunny
        name: Modo claro

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            members_order: source

nav:
  - Inicio: index.md
  - Instalación: installation.md
  - Referencia de API: reference.md
  - Política de versionado: versioning-policy.md
  - Criterios de inclusión: dataset-inclusion-criteria.md
  - Compatibilidad de datasets: dataset-compatibility-policy.md
```

Nota: si `docstring_style` real no es Google sino NumPy, ajústalo (`numpy`); revisa un
docstring en `core.py` para decidir. Los `nav` listados deben existir en `docs/`
(verifícalo con `ls docs/`); si alguno no existe, quítalo del nav.

**Verify**: `grep -n "site_dir: reference" mkdocs.yml` → 1 coincidencia.

### Step 3: Crear `docs/index.md` y `docs/reference.md`

`docs/index.md` (home del sitio — texto breve, en español neutral):

```markdown
# chile-hub

Capa de datos reproducible y curada sobre datasets públicos oficiales de Chile.

- **Instalación**: ver [Instalación](installation.md).
- **API de Python**: ver [Referencia de API](reference.md).
- Repositorio: <https://github.com/cortega26/chile-hub>
```

`docs/reference.md` (referencia autogenerada desde docstrings):

```markdown
# Referencia de API

## ChileHub

::: chile_hub.core.ChileHub

## Gestión de datos

::: chile_hub.data_manager.ChileHubDataManager

## Excepciones

::: chile_hub.exceptions
```

(Confirma los nombres de símbolo con `grep -n "^class " src/chile_hub/core.py
src/chile_hub/data_manager.py src/chile_hub/exceptions.py`. Si `ChileHubDataManager`
o el módulo `exceptions` tienen otra ruta, ajusta las directivas `:::`.)

**Verify**: `test -f docs/index.md && test -f docs/reference.md` → ambos existen.

### Step 4: Construir el sitio localmente

```bash
.venv/bin/mkdocs build
```

Debe terminar exit 0 y crear `reference/index.html` y `reference/reference/index.html`
(o `reference/reference.html` según `use_directory_urls`). Pueden aparecer *warnings*
por enlaces relativos en guías existentes — son aceptables en este primer cut (NO uses
`--strict`).

**Verify**:
- `.venv/bin/mkdocs build` → exit 0
- `test -f reference/index.html` → existe
- `grep -rl "ChileHub" reference/ | head -1` → al menos un HTML menciona `ChileHub`
  (confirma que mkdocstrings extrajo la API).

### Step 5: Ignorar la salida de build

En `.gitignore`, añade la carpeta de salida para no commitear el sitio generado en
desarrollo local:

```
/reference/
```

**Verify**: `git check-ignore reference/index.html` → imprime `reference/index.html`.

### Step 6: Añadir targets al Makefile

Añade a `Makefile` (junto a los demás targets; recuerda declararlos en `.PHONY`):

```makefile
docs-build:
	$(PYTHON) -m mkdocs build

docs-serve:
	$(PYTHON) -m mkdocs serve
```

**Verify**: `make docs-build` → exit 0; `reference/index.html` existe.

### Step 7: Integrar el build de docs en el deploy de Pages

En `.github/workflows/pages-deploy.yml`, inserta pasos de build **entre** "Configure
Pages" y "Upload Pages artifact". Reusa los SHAs pineados de `pipeline-check.yml`:

```yaml
      - name: Setup Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
        with:
          python-version: "3.12"

      - name: Setup uv
        uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0

      - name: Build API docs
        run: |
          uv sync --extra dev
          uv run mkdocs build
```

El `mkdocs build` genera `reference/` en el workspace; el paso "Upload Pages artifact"
(`path: .`) lo sube junto a la landing. No cambies `path: .`.

**Verify** (local, simulando el orden): tras `uv sync --extra dev && uv run mkdocs
build`, `test -d reference` → existe. La verificación real del deploy ocurre en CI al
hacer merge (fuera de alcance de la ejecución local).

### Step 8: Verificación final

**Verify**:
- `make docs-build` → exit 0
- `make lint` → exit 0 (no se rompió nada de Python)
- `git status` → solo los archivos en alcance modificados; `reference/` NO aparece
  (está ignorado).

## Test plan

- No hay tests automatizados de docs; la verificación es que `mkdocs build` termina
  exit 0 y que la referencia de API se genera (Step 4).
- Verificación manual recomendada: `.venv/bin/mkdocs serve`, abrir
  `http://localhost:8000/reference.html` (o `/reference/`) y confirmar que se ven los
  métodos de `ChileHub` con sus docstrings.

## Done criteria

Todas deben cumplirse:

- [ ] `mkdocs-material` y `mkdocstrings[python]` están en `[project.optional-dependencies].dev`.
- [ ] `mkdocs.yml` existe con `site_dir: reference` y el handler `python` con `paths: [src]`.
- [ ] `docs/index.md` y `docs/reference.md` existen; `reference.md` usa `::: chile_hub...`.
- [ ] `make docs-build` exit 0 y genera `reference/index.html`.
- [ ] La referencia generada menciona `ChileHub` (mkdocstrings funcionó).
- [ ] `.gitignore` ignora `/reference/`; `git status` no lista la salida de build.
- [ ] `pages-deploy.yml` construye los docs (con SHAs pineados) antes del upload.
- [ ] `make lint` exit 0; `index.html`/`app.js` SIN cambios.
- [ ] Fila de `plans/README.md` actualizada.

## STOP conditions

Detente y reporta (no improvises) si:

- `mkdocs build` falla con un **error** (no warning) que requiera modificar el
  contenido de guías existentes en `docs/` (fuera de alcance).
- mkdocstrings no encuentra `chile_hub` ni con `paths: [src]` (posible cambio en el
  layout del paquete respecto a "Current state").
- Los nombres de símbolo (`ChileHub`, `ChileHubDataManager`, `exceptions`) no
  coinciden con los del código (drift) — repórtalo en vez de adivinar.
- Integrar el build en `pages-deploy.yml` haría fallar el deploy de la landing y no
  puedes aislar la causa.

## Maintenance notes

- **Riesgo de deploy acoplado**: tras el Step 7, un fallo de `mkdocs build` en CI
  bloquea el redeploy de la landing (comparten un único sitio Pages). Es coherente con
  el principio "fallar con estridencia" del proyecto, pero el revisor debe saberlo.
- **Follow-up `--strict`**: una vez limpiados los enlaces relativos de las guías
  existentes y añadidas todas al `nav`, cambiar a `mkdocs build --strict` para
  convertir warnings en errores y garantizar docs sin enlaces rotos.
- **Follow-up cobertura de docstrings**: el `nav` se puede ampliar con las fichas de
  `docs/datasets/*.md` y los ADRs. mkdocstrings también puede documentar
  `src/validation.py` y los builders si se desea referencia interna.
- **Enlace desde la landing**: añadir en `index.html` un enlace a `/reference/` (no
  incluido aquí para respetar el "out of scope" de la landing).
- En revisión de PR: confirmar que la landing raíz no cambió y que `reference/` no se
  commiteó.
