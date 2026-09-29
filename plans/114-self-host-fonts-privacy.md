# Plan 114: La landing sirve sus fuentes localmente y la página de privacidad deja de ser inexacta

> **Executor instructions**: Sigue los pasos en orden. Verifica cada uno. Si algo
> de "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md` al terminar.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- index.html scripts/verify_landing.py privacy.html scripts/check_landing_sync.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: LOW
- **Depends on**: none (coordinación de archivos con Plan 113 Step 3 y Plan 122)
- **Category**: security / privacy
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`index.html:335-337` carga Google Fonts (`fonts.googleapis.com` y
`fonts.gstatic.com`) en cada visita, y el CSP de producción lo permite. Al
mismo tiempo `privacy.html:56,64` afirma: "La landing en sí no ejecuta ningún
otro servicio de analítica ni envía datos de uso a terceros" y "No compartimos
datos con terceros". Cada visita revela IP y `Referer` a Google — una
contradicción publicada con el propio valor del proyecto (independencia, sin
tracking), además de exposición GDPR conocida.

La solución recomendada es **auto-hospedar** los tres subsets de fuentes
(Inter, JetBrains Mono, Source Serif 4) en `vendor/fonts/`, con `@font-face`
propio, y eliminar los orígenes de Google del CSP y del HTML.

## Current state

- `index.html:335-337`:
  ```html
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:...&family=JetBrains+Mono:...&family=Source+Serif+4:...&display=swap" rel="stylesheet">
  ```
- CSP de producción espejado en `scripts/verify_landing.py:15-` (`PRODUCTION_CSP`,
  incluye `style-src`/`font-src` con `fonts.googleapis.com`/`fonts.gstatic.com`).
  El server de smoke test inyecta ese CSP (`verify_landing.py:58`).
- `privacy.html:56,64` (afirmaciones citadas arriba).
- `vendor/` ya existe con assets vendorizados (DuckDB-Wasm, 42 MB) — precedente
  de vendorizar sin CDN.
- `scripts/check_landing_sync.py` no chequea CSP ni `<link>`; no debería
  romperse, pero `index.html` es artefacto parcialmente generado: `make build`
  solo parchea el bloque JSON-LD y dos constantes de versión
  (`src/builders/landing.py`), el resto es editable a mano.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Landing smoke (Playwright) | `make verify-landing` | declared | exit 0 |
| Sync check | `python scripts/check_landing_sync.py` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `index.html` (bloque `<head>`: links de fuentes + `@font-face` + CSP meta si existe; y las reglas `font-family`)
- `vendor/fonts/` (nuevos `.woff2`)
- `scripts/verify_landing.py` (`PRODUCTION_CSP`)
- `privacy.html` (solo si la redacción necesita precisión)

**Out of scope**:
- Cambiar la tipografía elegida (eso fue Plan 055; aquí solo cambia el origen
  del archivo).
- `docs/stylesheets/` o MkDocs (usan su propio tema).
- `app.js` / `playground.js` (usan `var(--font-*)`, no cargan fuentes).

## Git workflow

- Branch: `advisor/114-self-host-fonts-privacy`
- Commits: `fix(landing): sirve las fuentes localmente` (estilo repo).
- No push/PR.

## Steps

### Step 0: Baseline

`make verify-landing` verde en checkout limpio. Si no, STOP (necesita Playwright
instalado por `make bootstrap`).

### Step 1: Obtener los woff2

1. Identifica las familias/pesos exactos del `<link>` actual (`index.html:337`).
2. Descarga los `.woff2` desde Google Fonts con un user-agent moderno, solo
   los subsets `latin` (el sitio es es-CL) y los pesos usados:
   - Inter: 400, 500, 600, 700 + itálicas 400/600 si el CSS las usa (grep
     `font-style: italic` no hace falta si se cargan las 2 itálicas ya
     declaradas).
   - JetBrains Mono: 400, 600 + italic 400.
   - Source Serif 4: 400, 500, 600, 700 + italics 400/600.
3. Guárdalos en `vendor/fonts/<familia>/<archivo>.woff2`.
4. Documenta en `vendor/fonts/README.md` la URL de origen, fecha y licencia
   (las tres familias son SIL OFL 1.1) — obligatorio para la atribución.

**Verify**: `find vendor/fonts -name '*.woff2' | wc -l` ≥ 10; todos los
archivos pesan > 5 KB.

### Step 2: Reemplazar los `<link>` por `@font-face`

- Elimina las tres líneas `fonts.googleapis.com`/`gstatic`.
- Agrega en el `<style>` de `index.html` un bloque `@font-face` por peso con
  `font-family` idéntico a los nombres ya usados (`Inter`, `JetBrains Mono`,
  `Source Serif 4`), `src: url("vendor/fonts/...") format("woff2")`,
  `font-display: swap`, y el `unicode-range` latin.
- No cambies las variables `--font-sans/--font-mono/--font-serif` ni el resto
  de reglas.

### Step 3: CSP

- En `scripts/verify_landing.py`, elimina `https://fonts.googleapis.com` de
  `style-src` (o `default-src`, donde esté) y `https://fonts.gstatic.com` de
  `font-src`. Deja el resto del CSP intacto.
- Si `index.html` tiene un `<meta http-equiv="Content-Security-Policy">` (el
  sitio se sirve con CSP de host; verifica con `grep -n "Content-Security-Policy"
  index.html`) actualízalo igual.

### Step 4: `privacy.html`

- La afirmación pasa a ser exacta sin cambios; verifica que no mencione fuentes.
- Opcional: agrega una línea "Las tipografías se sirven desde este mismo sitio;
  no se realiza ninguna petición a Google Fonts." con fecha.

### Step 5: Verificación funcional

- `make verify-landing` → exit 0 (Playwright carga la página con el nuevo CSP).
- `python scripts/check_landing_sync.py` → exit 0.
- `grep -rn "fonts.googleapis\|fonts.gstatic" index.html scripts/verify_landing.py privacy.html` → 0 matches.
- Verificación visual: abre la página local y confirma que los títulos usan
  Source Serif 4 y el código JetBrains Mono (el smoke test ya lo verifica por
  computed styles? si no, agrega un assert de `font-family` en
  `scripts/verify_landing.py` para `.hero h1`).

## Test plan

- `make verify-landing` es el test de contrato (CSP + render).
- Si `scripts/verify_landing.py` tiene asserts de `font-src` con Google,
  actualízalos (es el mismo archivo del Step 3).
- Test nuevo (si el smoke no lo cubre): assert en `verify_landing.py` de que
  `document.fonts.check("16px 'Source Serif 4'")` es true tras `load`.

## Done criteria

- [ ] `grep -rc "fonts.gstatic\|fonts.googleapis" index.html` → 0
- [ ] `find vendor/fonts -name '*.woff2' | wc -l` ≥ 10
- [ ] `make verify-landing` → exit 0
- [ ] `python scripts/check_landing_sync.py` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si no puedes descargar los woff2 (sin red), STOP y reporta; **no** sustituyas
  por system fonts sin decisión del mantenedor (cambia el diseño del Plan 055).
- Si el sitio se sirve con CSP definido fuera del repo (Cloudflare) y el smoke
  no lo refleja, reporta: el cambio de CSP de host no puede hacerse desde el
  repo.
- Si Playwright falla por fuentes locales faltantes, reporta el archivo que el
  CSS referencia y no existe.

## Maintenance notes

- Actualizar fuentes = re-descargar woff2 + actualizar `vendor/fonts/README.md`.
  No hay gate automático de skew; si el mantenimiento se vuelve frecuente,
  considerar una fuente variable única por familia.
- El peso de `vendor/fonts/` entra al deploy de Pages (todo el directorio se
  sube); mantén el subset latin y `woff2` para no inflar el sitio.
- **Deferred:** subsetting a los glifos realmente usados (es-CL, tildes) —
  ahorro marginal frente a latin completo; reevaluar si el deploy crece.
