# Plan 002: Agregar Content Security Policy a la landing page de producción

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**: `git diff --stat ba2f434..HEAD -- index.html scripts/verify_landing.py`
> If either file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `ba2f434`, 2026-06-13
- **Resolved**: 2026-06-17 — fixed independently; CSP meta tag already present in `index.html:5`

## Why this matters

La landing page (`index.html`) se despliega en GitHub Pages sin ningún
Content Security Policy (CSP). El CSP existe definido en
`scripts/verify_landing.py:11-18` como constante `PRODUCTION_CSP`, y se
inyecta vía header HTTP solo durante los smoke tests con Playwright. En
producción, GitHub Pages no agrega headers CSP automáticamente, así que la
página queda sin esta defensa en profundidad.

Agregar un `<meta http-equiv="Content-Security-Policy">` en el `<head>` de
`index.html` con la misma política ya probada en los smoke tests cierra esta
brecha sin riesgo de regresión. La política ya fue validada: permite
`'unsafe-inline'` para los estilos (necesario porque el CSS está inline en
`<style>`), bloquea `object-src` y `frame-ancestors`, y restringe scripts a
`'self'` (que incluye `app.js`).

## Current state

- `index.html:1-8` — el `<head>` actual no tiene meta tag CSP:

```html
<!-- index.html:1-8 -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>chile-hub — Capas de Datos de Chile</title>
    <link rel="canonical" href="https://cortega26.github.io/chile-hub/">
    <link rel="icon" href="data:image/svg+xml,…">
```

- `scripts/verify_landing.py:11-18` — el CSP de referencia, ya validado:

```python
# scripts/verify_landing.py:11-18
PRODUCTION_CSP = (
    "default-src 'self'; base-uri 'self'; form-action 'self' https://formspree.io; "
    "frame-ancestors 'none'; object-src 'none'; "
    "script-src 'self' https://analytics.ahrefs.com; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; font-src 'self'; "
    "connect-src 'self' https://analytics.ahrefs.com https://formspree.io; "
    "manifest-src 'self'; media-src 'self'; worker-src 'self' blob:; upgrade-insecure-requests"
)
```

- `index.html:10-41` — el `<style>` inline en el `<head>` requiere
  `style-src 'unsafe-inline'` (ya contemplado en la política).
- `index.html:1492` — el único script externo es `<script src="app.js" defer>`.
- `app.js` usa `fetch()` para cargar JSON desde `data/normalized/` — esto está
  cubierto por `connect-src 'self'`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Smoke test landing page | `make verify-landing` | exit 0 |
| Lint check | `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `index.html`

**Out of scope** (do NOT touch):
- `scripts/verify_landing.py` — ya tiene el CSP correcto; no modificarlo.
- `app.js` — no se modifica en este plan.
- Cualquier otro archivo.

## Steps

### Step 1: Agregar el meta tag CSP en el `<head>` de index.html

Insertar una línea `<meta http-equiv="Content-Security-Policy" content="…">`
después del `<meta charset="UTF-8">` y antes del `<meta name="viewport">`.

El valor de `content` debe ser exactamente la constante `PRODUCTION_CSP` de
`verify_landing.py:11-18`, copiada como string en una sola línea (el valor
del atributo `content`).

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'self'; form-action 'self' https://formspree.io; frame-ancestors 'none'; object-src 'none'; script-src 'self' https://analytics.ahrefs.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://analytics.ahrefs.com https://formspree.io; manifest-src 'self'; media-src 'self'; worker-src 'self' blob:; upgrade-insecure-requests">
```

**Verify**: `make verify-landing` → exit 0. El smoke test del landing page
debe seguir pasando. Inspeccionar visualmente que la página se renderiza
correctamente (el navegador no debería bloquear ningún recurso con la nueva
política porque es idéntica a la que el test ya inyecta vía header).

### Step 2: Verificar que no hay regresión visual ni funcional

Abrir `index.html` con un servidor local y confirmar:

- Los KPI cards cargan datos.
- La tabla de comunas se renderiza.
- El catálogo de datasets se muestra correctamente.
- La consola del navegador no muestra errores de violación CSP.

**Verify**: Cero errores CSP en consola del navegador al cargar la página
completa.

## Test plan

- El smoke test existente (`make verify-landing`) ya verifica que la página
  funciona con exactamente esta política CSP (lo hace inyectando el header).
  Agregar el meta tag no debería cambiar el comportamiento.
- Si se quiere una verificación adicional, inspeccionar las DevTools del
  navegador → pestaña Network → confirmar que todas las requests (app.js,
  JSON files) cargan con status 200 y sin bloqueos CSP.

## Done criteria

- [ ] `make verify-landing` sale con exit 0
- [ ] El meta tag CSP está presente en `index.html` con el contenido exacto
      de `PRODUCTION_CSP`
- [ ] `make lint` sale con exit 0
- [ ] Ningún archivo fuera de `index.html` fue modificado (`git diff --stat`)
- [ ] La página carga sin errores CSP en consola del navegador

## STOP conditions

Stop and report back (do not improvise) if:

- `index.html` no coincide con el excerpt de "Current state" (el código ha
  cambiado desde que este plan fue escrito).
- `make verify-landing` falla después de agregar el meta tag.
- La consola del navegador muestra errores de violación CSP después del
  cambio (indicaría que la política en `verify_landing.py` ya no es correcta
  y necesita actualizarse también).
- Algún recurso externo nuevo (no contemplado en la política actual) dejó de
  cargar.

## Maintenance notes

- Si se agrega un nuevo origen externo (CDN para fuente tipográfica, analytics
  adicional, API externa), la política CSP debe actualizarse tanto en
  `index.html` (meta tag) como en `scripts/verify_landing.py` (constante
  `PRODUCTION_CSP`). Ambos deben mantenerse sincronizados.
- GitHub Pages no permite configurar headers HTTP personalizados, por eso el
  enfoque de meta tag es la única opción viable para producción.
- Si en el futuro se migra a un hosting con control de headers (Netlify,
  Vercel, Cloudflare), es preferible mover el CSP a un header HTTP y remover
  el meta tag.
