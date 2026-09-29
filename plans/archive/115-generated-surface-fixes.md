# Plan 115: Superficie pública generada — año de finanzas, reemplazo en el playground y URL base única

> **Executor instructions**: Sigue los pasos en orden; cada uno verifica solo.
> Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md` al terminar.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- scripts/build_comuna_pages.py playground.js scripts/inject_dataset_json_ld.py src/builders/landing.py tests/test_pipeline_logic.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (coordinación con Plan 113 Step 3 en `landing.py`/`inject_dataset_json_ld.py`: no correr en worktrees simultáneos)
- **Category**: bug
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Tres defectos visibles en la superficie pública generada:

1. **`anio_finanzas` se muestra "2.024"** en las 346 fichas comunales: el campo
   está en el bloque `MUNICIPIO` (`build_comuna_pages.py:99`) pero
   `YEAR_FIELDS` (`:129`) no lo incluye, así que `_fmt` (`:294-305`) cae al
   formateo numérico con separador de miles. Es el dato más básico de la
   tarjeta municipal y contradice la promesa de datos curados.
2. **El SQL Explorer reemplaza solo la primera aparición de cada path** y su
   regex no acepta comillas dobles (`playground.js:107,125`). Un self-join
   contra el mismo Parquet falla; `read_parquet("...")` nunca se registra.
3. **La URL pública canónica tiene 4 fuentes**, y las fichas de comuna ignoran
   `--site-url` para los enlaces de descarga (`build_comuna_pages.py:34,447-448`
   usa `PARQUET_BASE` hardcodeado); `inject_dataset_json_ld.py` tiene su propio
   default hardcodeado y `pages-deploy.yml:61` lo invoca sin `--site-url`. El
   día que el dominio cambie (p. ej. `www`), cientos de páginas generadas
   quedan apuntando al host viejo.

## Current state

- `scripts/build_comuna_pages.py`
  - `:98-106` `MUNICIPIO` incluye `("Año de finanzas", "anio_finanzas")`.
  - `:129` `YEAR_FIELDS = {"anio_permisos_edificacion"}`.
  - `:294-305` `_fmt`: `field in YEAR_FIELDS → str(int(value))`; si no,
    `f"{int(value):,}".replace(",", ".")`.
  - `:33-34` `PUBLIC_SITE_URL = "https://tooltician.com/chile-hub/"`;
    `PARQUET_BASE = "https://tooltician.com/chile-hub/data/normalized"`.
  - `:447-448` los botones "Descargar Parquet/JSON" usan `{PARQUET_BASE}`
    aunque la función recibe `site_url`.
  - `:585` `parser.add_argument("--site-url", default=PUBLIC_SITE_URL)`.
- `playground.js:105-127`:
  ```js
    const parquetRegex = /read_parquet\s*\(\s*'([^']+)'\s*\)/g;
    ...
        modifiedSql = modifiedSql.replace(path, basename);
  ```
- `scripts/inject_dataset_json_ld.py:56` — default de `--site-url` hardcodeado;
  `pages-deploy.yml:60-61` lo invoca sin flag.
- `src/builders/landing.py` / `scripts/check_landing_sync.py` ya leen
  `[tool.chile_hub] public_site_url` de `pyproject.toml:178-179`
  (`read_project_version`/config helpers en `src/builders/io_utils.py`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests focal | `./.venv/bin/pytest tests/test_pipeline_logic.py -k "ComunaPages or Playground or JsonLd" -v` | declared | verde |
| Landing smoke | `make verify-landing` | declared | exit 0 |
| Sync check | `python scripts/check_landing_sync.py` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `scripts/build_comuna_pages.py`
- `playground.js`
- `scripts/inject_dataset_json_ld.py`
- `tests/test_pipeline_logic.py` (tests de páginas de comuna / JSON-LD)
- `.github/workflows/pages-deploy.yml` (solo el comando de generación, si elige pasar flag)

**Out of scope**:
- `index.html`/`app.js` (Plan 114/122).
- Reestructurar los generadores o mover a un builder.
- Cambiar la URL real del sitio.

## Git workflow

- Branch: `advisor/115-generated-surface-fixes`
- Commits: `fix(seo): ...` / `fix(landing): ...` (estilo repo).
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_pipeline_logic.py -k ComunaPages -v` verde. Si
no, STOP.

### Step 1: Año de finanzas

- En `scripts/build_comuna_pages.py:129`, cambia a
  `YEAR_FIELDS = {"anio_permisos_edificacion", "anio_finanzas"}`.
- En `tests/test_pipeline_logic.py`, `ComunaPagesTests` (`:5286`), agrega un
  assert al test de render existente: una fila con `anio_finanzas=2024` produce
  `Año de finanzas` → `2024` y **no** `2.024`.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -k ComunaPages -v`
→ verde, incluido el assert nuevo.

### Step 2: Playground

En `playground.js`:

```js
    const parquetRegex = /read_parquet\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
    ...
        modifiedSql = modifiedSql.replaceAll(path, basename);
```

`replaceAll` sobre un string argument reemplaza todas las apariciones (la ruta
es literal, no regex). Mantén el resto del loop igual.

**Verify**: agrega/actualiza el test de `playground.js` si existe (grep
`playground` en tests/ y en `scripts/verify_landing.py`): si el smoke test no
ejecuta SQL, agrega una consulta en `verify_landing.py` con el mismo Parquet
dos veces y `read_parquet(...)` con comillas dobles, y afirma resultado sin
error. `make verify-landing` → exit 0.

### Step 3: URL base única

- En `build_comuna_pages.py`, deriva la base de descargas del `site_url`
  recibido: p. ej. `parquet_base = args.site_url.rstrip("/") + "/data/normalized"`
  pasada a la función de render (o calculada dentro a partir de `site_url`).
  Elimina la constante `PARQUET_BASE` o conviértela en default del parser si
  algún test la importa (grep `PARQUET_BASE` en tests/).
- En `inject_dataset_json_ld.py`, haz que el default de `--site-url` lea
  `[tool.chile_hub] public_site_url` (`pyproject.toml:178-179`) con el mismo
  helper que usa `src/builders/landing.py` (reusa `read_project_version` o el
  helper de config existente en `src/builders/io_utils.py`). El script corre en
  `pages-deploy` desde el repo, así que pyproject está disponible.
- En `pages-deploy.yml`, si el script ya no necesita flag, déjalo; si prefieres
  explícito, pasa `--site-url` en ambos steps y deja el default por pyproject
  como fallback.

**Verify**: `python scripts/inject_dataset_json_ld.py --help` muestra el
default desde pyproject; con un `--site-url https://example.test/x` el JSON-LD
generado usa ese host (puedes verificarlo con un tmpdir y grep);
`make verify-landing` → exit 0.

### Step 4: Cierre

`make lint`, `make format-check`, actualizar índice.

## Test plan

- `ComunaPagesTests`: assert de año (Step 1) + assert de que los links de
  descarga usan el `site_url` pasado (Step 3).
- Playground: si no hay test ejecutable en el smoke, agrega el caso doble al
  `verify_landing.py` (es el lugar donde ya se corren queries del explorador).
- Validación final `make verify-landing`.

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py -v` → verde
- [ ] `grep -n 'YEAR_FIELDS' scripts/build_comuna_pages.py` → incluye `anio_finanzas`
- [ ] `grep -n 'replaceAll' playground.js` → 1 match
- [ ] `grep -c 'PARQUET_BASE' scripts/build_comuna_pages.py` → 0 (o usado solo como default del parser y documentado)
- [ ] `grep -n 'fonts' ...` no aplica (otro plan)
- [ ] `make verify-landing` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `PARQUET_BASE` se importa desde tests u otro script (grep antes), no la
  elimines: conviértela en default y sigue.
- Si el smoke de Playwright no puede ejecutar SQL en CI (vendor ausente), NO
  agregues asserts frágiles: deja el fix de JS sin test de humo y documenta en
  Maintenance notes.
- Si `inject_dataset_json_ld.py` no puede importar helpers de `src.builders`
  (corre con cwd distinto), usa `tomllib` localmente; no inventes un path.

## Maintenance notes

- Toda URL de descarga en páginas generadas debe derivar de `site_url`/
  `pyproject`. Si se agrega una tercera página generada, extender el mismo
  patrón; `scripts/check_landing_sync.py` podría extenderse para comparar la
  base de páginas generadas con pyproject (hoy solo `index.html`/`app.js`).
- `write_mapa_comunal_geojson` → ver Plan 116 para el asset del mapa.
- **Deferred:** unificar `PUBLIC_DATA_BASE` de `mcp_tools.py:22` y `geo.py:35`
  con pyproject en runtime del paquete — el paquete instalado no tiene
  pyproject; requiere otro mecanismo (variable de build). No vale hoy.
