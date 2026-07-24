# Plan 051: Capa de acceso HTTP estática documentada + catálogo DCAT (`data.json`)

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de avanzar. Si ocurre algo de
> "STOP conditions", detente y reporta — no improvises. Al terminar, actualiza la
> fila de estado en `plans/README.md`.
>
> **Este es un plan de diseño/spike.** El entregable principal es una **decisión de
> contrato** (ADR) más un generador prototipo y su documentación — no una API 24/7.
> El proyecto **excluye explícitamente** "una API pública que deba mantenerse en
> línea 24/7" (`docs/product-spec.md:129`). Todo lo que produces aquí son **archivos
> estáticos + un descriptor cosechable**, servidos por el hosting que ya existe. Si
> en algún punto te ves diseñando un servidor, un endpoint dinámico, auth o billing,
> **para** (STOP condition).
>
> **Drift check (córrelo primero)**:
> `git diff --stat 7ebf94b..HEAD -- src/chile_hub/core.py src/builders/data_package.py src/build_dev_db.py .github/workflows/pages-deploy.yml README.md`
> Si algo cambió, compara los excerptos de "Estado actual" contra el código vivo
> antes de continuar; ante discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: M (spike: contrato + prototipo generador + docs + fix de `from_datapackage(url)`)
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `7ebf94b`, 2026-07-14

## Why this matters

La capa de acceso HTTP estática **ya existe y ya se consume en producción** — sólo que
no está documentada como modo de acceso ni es cosechable por terceros. Evidencia
concreta:

- Los artefactos normalizados están **commiteados** (`.gitignore:7-11` reabre
  `data/normalized/*.{json,md,parquet}`) y se **sirven en GitHub Pages** vía
  `pages-deploy.yml` (`path: .`).
- El `README.md` **ya consume** esos artefactos por HTTP con URL estable: los badges
  de líneas `README.md:20-21` apuntan a
  `https://tooltician.com/chile-hub/data/normalized/coverage_badge.json` y
  `.../freshness_badge.json`. O sea: `https://tooltician.com/chile-hub/data/normalized/`
  ya es un **base URL público y estable** que devuelve JSON/Parquet.
- `src/builders/data_package.py:89` ya genera `data/normalized/datapackage.json`, un
  descriptor **Frictionless** — la fuente natural para traducir a un catálogo DCAT.

Dos cosas faltan para convertir hosting ya pagado en superficie de producto real:

1. **Descubribilidad estándar**: no hay un catálogo cosechable (`data.json` /
   **DCAT-AP**, el estándar que usa **datos.gob.cl** para federar datos públicos
   chilenos). Con él, un consumidor no-Python (R, JS/Observable, un periodista de
   datos) o un cosechador gubernamental descubre y baja los datasets sin clonar ni
   instalar la librería. Esta es la recomendación explícita de la evaluación comercial
   ME8 (`docs/backlog/08-evaluacion-producto-comercial.md:54`: *"exponer una API
   gratuita estática (Parquet/JSON en CDN) como funnel, costo casi nulo"*) y del
   product-spec (`docs/product-spec.md:146`: *"índice de archivos alojado o catálogo
   de versiones"*).

2. **El cliente Python no puede consumir su propio hosting**: `ChileHub.from_datapackage()`
   (`core.py:422`) promete en su docstring *"Ruta local o URL a un archivo
   datapackage.json"* pero la implementación sólo maneja rutas locales (defecto — ver
   Estado actual). Arreglarlo cierra el círculo: `ChileHub.from_datapackage("https://…/datapackage.json")`.

## Current state

- `src/builders/data_package.py:89-91` — genera el descriptor Frictionless:
  ```python
  def build_data_package(...):
      """Genera y escribe data/normalized/datapackage.json. Retorna la ruta."""
      output_path = os.path.join(NORMALIZED_DIR, "datapackage.json")
  ```
  Léelo completo antes de escribir el generador DCAT — reúsa su forma de descubrir
  datasets/recursos en vez de reinventarla.

- `src/chile_hub/core.py:454-460` — el **defecto** de `from_datapackage`: acepta el
  parámetro `path_or_url` pero sólo maneja paths locales:
  ```python
  path = Path(path_or_url)
  if not path.exists():
      raise FileNotFoundError(f"Descriptor no encontrado: {path}")
  _ = frictionless.Package(str(path))
  data_dir = path.parent
  return cls(data_dir=data_dir)
  ```
  Con una URL, `Path(url).exists()` es `False` → lanza `FileNotFoundError`. El
  docstring (`core.py:431`) dice "Ruta local o URL": promesa no cumplida.

- `.github/workflows/pages-deploy.yml` — corre `mkdocs build` y sube `path: .` (todo
  el repo, incluidos los artefactos de `data/normalized/`). El sitio de docs se sirve
  bajo `/reference/` (`mkdocs.yml:3`, `site_dir: reference`).

- `src/build_dev_db.py::main()` — orquesta el build y llama a los builders (incluido
  `build_data_package` y los sync de docs). Aquí se engancharía el generador nuevo,
  igual que se enganchan los demás artefactos.

Convenciones:

- Los artefactos de `data/normalized/*.json` se generan por el pipeline y se
  commitean; no se editan a mano (§10 `AGENTS.md`). El `data.json` nuevo debe ser
  **generado**, no escrito a mano.
- Todo hecho documentado derivable del código declara su fuente de verdad (§12
  `AGENTS.md`). El catálogo debe derivarse de `datapackage.json` /
  `dataset_catalog.json`, no duplicar su contenido a mano.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Build completo (genera artefactos) | `make build` | exit 0 |
| Test del generador (no requiere normalized) | `./.venv/bin/pytest tests/test_data_package.py -v` | pasan |
| Instalar extra de validación (para from_datapackage) | `./.venv/bin/pip install -e ".[validation]"` o `uv sync --extra validation` | exit 0 |
| Lint / format | `make lint` && `make format-check` | exit 0 |

## Scope

Este spike se entrega en **dos capas**; la Capa 1 es obligatoria, la Capa 2 (DCAT) es
el prototipo que el ADR decide si se promueve.

**In scope**:

- `docs/adr/ADR-010-acceso-http-estatico-y-dcat.md` (crear) — **el entregable central**.
- `src/chile_hub/core.py` — arreglar `from_datapackage()` para soportar URLs.
- `tests/test_core.py` — test del fix de URL (con un descriptor local servido o
  mockeado; ver Test plan).
- `src/builders/dcat_catalog.py` (crear) — prototipo del generador `data.json` DCAT.
- `src/build_dev_db.py` — enganchar el generador prototipo en `main()` (una línea,
  junto a los demás builders).
- `tests/test_pipeline_logic.py` — test del generador DCAT.
- `docs/http-access.md` (crear) — página de docs del modo de acceso HTTP + `mkdocs.yml`
  (agregar a la nav).
- `plans/README.md` — fila de estado.

**Out of scope** (NO tocar):

- Cualquier servidor, endpoint dinámico, FastAPI/Flask, auth, billing — la línea roja
  del product-spec. Sólo archivos estáticos.
- El bundle ZIP y su manifiesto (`src/builders/artifacts.py`) — el descubrimiento va
  por `datapackage.json`/`data.json`, no toques el empaquetado.
- Los badges existentes del README — ya funcionan; no los reformatees.
- El dominio real de hosting: usa `https://tooltician.com/chile-hub/` como base URL
  **sólo si** lo confirmas en `README.md:20-21`; no inventes otro dominio.

## Git workflow

- Branch: `advisor/051-static-http-dcat`
- Conventional commits (ej. `feat(dist): genera catálogo DCAT data.json` /
  `fix(api): from_datapackage acepta URLs`). Sepáralos por unidad lógica.
- No push ni PR salvo instrucción del operador.

## Steps

### Step 0 (spike): Investiga y decide el contrato — escribe ADR-010 primero

Antes de escribir generador o fix, decide y documenta en
`docs/adr/ADR-010-acceso-http-estatico-y-dcat.md` (formato de los ADR existentes; lee
`docs/adr/ADR-008-datapackage-consumer-validation.md` como plantilla). Resuelve:

1. **Base URL y contrato de estabilidad**: confirma el base URL real
   (`grep -n "tooltician.com" README.md`). Decide qué garantía se ofrece: ¿`.../data/normalized/`
   es "latest" mutable? ¿Se necesita una URL pinada por versión/release para
   reproducibilidad? Documenta la política (aunque la implementación de pinning quede
   como follow-up).
2. **Perfil de catálogo**: ¿`data.json` estilo DCAT-US (el de data.gov, `dataset[]`
   con `distribution[]`) o DCAT-AP (el de la UE / datos.gob.cl)? Investiga cuál cosecha
   **datos.gob.cl** (busca su documentación de harvesting; si no la puedes verificar,
   **regístralo como pregunta abierta** y usa DCAT-US como default por ser el más
   simple y ampliamente soportado). No inventes un perfil no estándar.
3. **Fuente de verdad**: el `data.json` se deriva de `datapackage.json` +
   `dataset_catalog.json`. Documenta el mapeo campo→campo en el ADR (ej. Frictionless
   `resources[].path` → DCAT `distribution[].downloadURL` como URL absoluta bajo el
   base URL).
4. **Preguntas abiertas** (sección explícita): pinning por versión; si publicar
   `data.json` implica comprometerse a estabilidad de URLs de descarga; si datos.gob.cl
   efectivamente cosecha este formato.

**Verify**: `test -f docs/adr/ADR-010-acceso-http-estatico-y-dcat.md && grep -c "Preguntas abiertas" docs/adr/ADR-010-acceso-http-estatico-y-dcat.md` → ≥ 1

### Step 1: Arregla `from_datapackage()` para soportar URLs

Modifica `core.py:454-460`. Detecta si `path_or_url` es una URL (`str` que empieza con
`http://`/`https://`) y, en ese caso, delega en `frictionless.Package(str(path_or_url))`
(frictionless resuelve URLs remotas nativamente) en vez de `Path(...).exists()`. Para
el `data_dir` resultante: cuando es URL, deriva el directorio remoto (todo hasta el
último `/`) y pásalo de forma que `ChileHub` pueda resolver los Parquet remotos — **o**,
si eso excede el alcance del spike, documenta en el docstring y el ADR que
`from_datapackage(url)` valida y resuelve el descriptor pero requiere que los recursos
sean URLs absolutas, y agrega un STOP/pregunta abierta si el modelo de `data_dir`
remoto no encaja con `ChileHub.__init__`. Mantén el comportamiento local **idéntico**
(no rompas el path existente ni sus tests).

**Verify**: `./.venv/bin/pytest tests/test_core.py -v -k datapackage` → pasan, incluido
el test nuevo de URL (ver Test plan). El path local sigue verde.

### Step 2: Prototipo del generador DCAT `data.json`

Crea `src/builders/dcat_catalog.py` con una función que lea `datapackage.json` (y
`dataset_catalog.json` si necesita descripciones/fuentes) desde `NORMALIZED_DIR` y
escriba `data/normalized/data.json` con el perfil decidido en el ADR. Reúsa las
constantes de path y el patrón de escritura de `src/builders/data_package.py` (mismo
`NORMALIZED_DIR`, mismo estilo de `json.dump` con `ensure_ascii=False, indent=2`). Cada
`distribution[].downloadURL` debe ser una **URL absoluta** bajo el base URL confirmado.

Engancha la función en `src/build_dev_db.py::main()` junto a la llamada existente a
`build_data_package` (busca `build_data_package` en `build_dev_db.py` y agrega la nueva
llamada inmediatamente después).

**Verify**: `make build && ./.venv/bin/python -c "import json; d=json.load(open('data/normalized/data.json')); assert d.get('dataset'), 'sin datasets'; u=d['dataset'][0]['distribution'][0]['downloadURL']; assert u.startswith('https://'), u; print('datasets:', len(d['dataset']), 'ejemplo:', u)"` →
imprime el conteo de datasets y una `downloadURL` absoluta `https://…`.

### Step 3: Documenta el modo de acceso HTTP

Crea `docs/http-access.md`: explica el base URL estable, cómo listar datasets vía
`data.json`, cómo bajar un Parquet directo por URL, y ejemplos **copiables** en al
menos R (`arrow::read_parquet(url)`) y JS/`fetch`, más Python
(`ChileHub.from_datapackage("https://…/datapackage.json")`). Agrega la página a la nav
de `mkdocs.yml` (mira la estructura `nav:` existente; si no hay `nav:` explícita,
mkdocs auto-descubre — en ese caso sólo crea el `.md` y verifica que aparezca en el
build).

**Verify**: `./.venv/bin/mkdocs build 2>&1 | tail -5` → build sin errores; y
`test -f docs/http-access.md` → exit 0.

### Step 4: ADR final + registro

Completa ADR-010 con lo efectivamente implementado (fix de URL, generador prototipo,
página de docs) y marca claramente qué quedó como **follow-up** (pinning por versión,
registro formal ante datos.gob.cl, promover el prototipo DCAT a artefacto verificado
por `sync_docs.py`).

**Verify**: `grep -c "follow-up\|Follow-up\|Consecuencias" docs/adr/ADR-010-acceso-http-estatico-y-dcat.md` → ≥ 1

## Test plan

- `tests/test_core.py`: test del fix de `from_datapackage(url)`. Como no debes depender
  de red en tests, sirve un `datapackage.json` local vía un file server temporal
  (`http.server` en un thread) **o**, más simple, testea la **rama de detección de URL**
  con un descriptor local y un assert de que una string `http://…` inexistente ya no
  lanza `FileNotFoundError` por el chequeo `Path.exists()` sino que intenta el camino
  remoto (puedes mockear `frictionless.Package`). Modela sobre los tests existentes de
  `from_datapackage`/`frictionless_validate` (`grep -n "datapackage" tests/test_core.py`).
- `tests/test_pipeline_logic.py`: test del generador DCAT — dado un `datapackage.json`
  mínimo de fixture, `data.json` resultante tiene `dataset[]` no vacío y cada
  `distribution[].downloadURL` es `https://…` absoluta. Modela sobre
  `tests/test_data_package.py`.

**Verify**: `make build && ./.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py tests/test_data_package.py -v` → todos pasan, con los nuevos.

## Done criteria

- [ ] `docs/adr/ADR-010-acceso-http-estatico-y-dcat.md` existe con secciones Decisión, Consecuencias, "Preguntas abiertas" y follow-ups.
- [ ] `from_datapackage()` ya no lanza `FileNotFoundError` para un argumento URL antes de intentar resolverlo; el path local sigue funcionando (tests verdes).
- [ ] `make build` genera `data/normalized/data.json` con `dataset[]` no vacío y `downloadURL` absolutas.
- [ ] `docs/http-access.md` existe con ejemplos en Python + R + JS y `mkdocs build` pasa.
- [ ] `./.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py tests/test_data_package.py` → exit 0 con los tests nuevos.
- [ ] `make lint` y `make format-check` → exit 0.
- [ ] `git status` sin archivos fuera de "In scope".
- [ ] Fila de estado en `plans/README.md` actualizada.

## STOP conditions

Detente y reporta si:

- El código de `from_datapackage` o `data_package.py` no coincide con "Estado actual"
  (drift desde `7ebf94b`).
- Te descubres diseñando un servidor, endpoint dinámico, auth o billing — eso viola la
  línea roja del product-spec; el spike es **sólo archivos estáticos**.
- No puedes confirmar el base URL real en `README.md` — no inventes un dominio;
  reporta y pregunta.
- El modelo de `data_dir` remoto para `from_datapackage(url)` no encaja limpiamente con
  `ChileHub.__init__` (que asume un directorio local con Parquet) — implementa sólo la
  detección+validación de URL, documenta la limitación como follow-up en el ADR, y no
  fuerces un rediseño de `__init__` en este spike.
- No puedes verificar qué perfil DCAT cosecha datos.gob.cl — usa DCAT-US como default y
  regístralo como pregunta abierta; no bloquees el plan por esto.
- Cualquier verificación falla dos veces tras un intento razonable.

## Maintenance notes

- **Acople con §12 (anti-drift)**: si el prototipo `data.json` se promueve a artefacto
  oficial, agrégalo a la tabla de propietarios canónicos de `AGENTS.md §12` y considera
  cubrirlo con `scripts/sync_docs.py` o `verify_pipeline.py`. En este spike es un
  artefacto generado más, sin gate — anótalo como follow-up.
- **Qué escrutar en el PR**: que ninguna `downloadURL` sea relativa (rompería la
  cosecha externa); que el fix de `from_datapackage` no altere el comportamiento del
  path local (regresión silenciosa para usuarios actuales).
- **Follow-ups deferidos** (regístralos en el ADR): pinning de URLs por versión de
  release; registro/anuncio formal ante datos.gob.cl; promover el catálogo a artefacto
  verificado; y — si hay demanda — un índice de versiones históricas.
