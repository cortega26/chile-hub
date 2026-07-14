# Plan 046: Alinear `privacy.html` con el sistema de diseño del sitio

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- privacy.html index.html`
> Si estos archivos cambiaron desde que se escribió este plan, compara los
> extractos de "Estado actual" contra el código real antes de continuar; si no
> coinciden, trátalo como un STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (content/design consistency)
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

`privacy.html` (enlazado desde el footer de `index.html` en cada página del sitio,
`index.html:2974`: `<a href="privacy.html">Privacidad</a>`) es visualmente un producto
distinto al resto del sitio:

- Usa `font-family: system-ui, sans-serif` en vez de las fuentes del sitio (`Lora` /
  `IBM Plex Sans` / `IBM Plex Mono`, definidas como `--font-display` / `--font-sans` /
  `--font-mono` en `index.html:298-326`).
- Usa `#6C47FF` (morado/índigo brillante) como color de enlaces — un color que no
  aparece en ningún otro lugar del sitio. De hecho, `:root` en `index.html` tiene un
  alias `--accent-purple: var(--accent-warm);` marcado explícitamente como
  `/* legacy map */` (`index.html:316`), lo que sugiere que el morado fue el acento de
  una iteración de diseño anterior, ya reemplazada en el resto del sitio por el verde
  bosque / terracota actual.
- No tiene el `<header>` con logo y navegación, ni el `<footer>` con los mismos enlaces,
  que aparecen en `index.html`. Un usuario que llega aquí pierde toda referencia visual
  de que sigue en chile-hub.

Es la única otra página HTML del sitio (junto a `index.html`), tiene tráfico garantizado
(enlazada desde cada carga de página) y el costo de arreglarlo es bajo — no hay lógica,
sólo maquetación estática.

## Estado actual

`privacy.html` completo (43 líneas):

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacidad — chile-hub</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #1a1a1a; }
        a { color: #6C47FF; }
    </style>
</head>
<body>
    <p><a href="index.html">← Volver a chile-hub</a></p>
    <h1>Privacidad</h1>
    <p><strong>Última actualización:</strong> 2026-06-30</p>
    <!-- ... contenido: qué se mide, qué NO se hace, sección GoatCounter, contacto ... -->
</body>
</html>
```

Referencia de tokens del sitio (`index.html:298-326`, dentro de `:root`):
```css
--bg-color: #f7f6f0;
--panel-bg: #ffffff;
--border-color: #d6d4c9;
--text-primary: #1a221f;
--text-secondary: #5c6560;
--accent-green: #123d30;
--accent-green-hover: #0a241c;
--font-display: 'Lora', Georgia, serif;
--font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
```

`index.html:2969-2977` — el `<footer>` completo del sitio, para replicar su estructura
(no todos los enlaces, sólo el patrón visual):
```html
<footer>
    <div style="display:flex;flex-direction:column;gap:0.35rem;">
        <p>Construido con Python, Polars y DuckDB.</p>
        ...
        <p><a href="privacy.html">Privacidad</a> — este sitio no usa cookies ni recolecta datos personales.</p>
    </div>
    <a href="https://github.com/cortega26/chile-hub/issues" ...>Reportar un error →</a>
</footer>
```

`index.html:2574-2588` — el `<header>` completo, para replicar (versión simplificada,
sin necesidad de repetir cada link de navegación):
```html
<header>
    <div class="logo-section">
        <h1>chile-hub <span class="badge-alpha"></span></h1>
    </div>
    <nav class="site-nav" aria-label="Navegación principal">
        <a href="#catalogo">Datos</a>
        ...
        <a class="nav-github" href="https://github.com/cortega26/chile-hub" target="_blank" rel="noopener noreferrer">GitHub Repo</a>
    </nav>
</header>
```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 (no cubre `privacy.html`, pero confirma que `index.html` sigue intacto si tocaste algo ahí) |

## Scope

**En alcance**:
- `privacy.html` — reescribir el `<style>` y envolver el contenido con un header/footer
  mínimo consistente con el sitio.

**Fuera de alcance**:
- `index.html` — no dupliques su CSS completo dentro de `privacy.html`; usa un
  subconjunto mínimo de reglas inline o un `<style>` propio en `privacy.html` que
  reutilice los mismos valores de color/fuente (no hay hoja de estilos compartida en
  este repo — cada HTML es autocontenido por diseño, ver que `index.html` también
  tiene su CSS inline en un `<style>` propio).
- No agregues el `<nav>` completo de 8 links del sitio — un link simple "← Volver a
  chile-hub" (que ya existe) más el logo es suficiente; el objetivo es continuidad de
  marca, no replicar la navegación completa de la landing en una página de una sola
  pantalla.
- No agregues Google Fonts (`<link rel="preconnect">` + `<link href="fonts.googleapis.com...">`)
  a `privacy.html` sólo por esto — importar una fuente web completa para una página de
  texto simple es un costo de carga innecesario. Usa la pila de *fallback* del sitio
  (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`, la misma que
  `--font-sans` usa como fallback) en vez de `system-ui` genérico — es casi la misma
  fuente visualmente, pero mantiene el mismo criterio de fallback que el resto del
  sitio.

## Pasos

### Paso 1: Reemplazar el `<style>` con los tokens de color/fuente del sitio

Reemplaza el bloque `<style>` de `privacy.html` por:

```html
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        max-width: 720px;
        margin: 0 auto;
        padding: 0 1.5rem 3rem;
        line-height: 1.6;
        color: #1a221f;
        background-color: #f7f6f0;
    }
    header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 2rem 0;
        border-bottom: 1px solid #d6d4c9;
        margin-bottom: 2rem;
    }
    header h1 {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
    }
    header a {
        color: #1a221f;
        text-decoration: none;
    }
    h1 { font-size: 1.6rem; }
    h2 { font-size: 1.15rem; margin-top: 2rem; }
    a { color: #123d30; }
    a:hover { color: #0a241c; }
    footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #d6d4c9;
        font-size: 0.85rem;
        color: #5c6560;
    }
</style>
```

(Nota: estos valores son los mismos hex que `--bg-color`, `--text-primary`,
`--border-color`, `--accent-green`, `--accent-green-hover`, `--text-secondary` de
`index.html:298-326` — copiados como literales porque `privacy.html` es un archivo
HTML independiente sin acceso al `:root` de `index.html`. Si más adelante se decide
compartir un archivo de tokens entre ambas páginas, es un cambio de arquitectura más
grande, fuera de alcance aquí.)

**Verify**: `grep -n "6C47FF\|system-ui" privacy.html` → no debe devolver ninguna
coincidencia (ambos quedaron reemplazados).

### Paso 2: Envolver el contenido con header y footer mínimos

Reemplaza:
```html
<body>
    <p><a href="index.html">← Volver a chile-hub</a></p>
    <h1>Privacidad</h1>
```
por:
```html
<body>
    <header>
        <a href="index.html">← chile-hub</a>
    </header>
    <h1>Privacidad</h1>
```

Y antes de `</body>`, agrega:
```html
    <footer>
        <p><a href="index.html">Volver a chile-hub</a></p>
    </footer>
```

**Verify**: `grep -n "<header>\|<footer>" privacy.html` → debe mostrar ambos elementos.

### Paso 3: Verificación visual

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 900, "height": 900})
    page.goto("http://localhost:8877/privacy.html")
    page.screenshot(path="privacy_after.png", full_page=True)
    browser.close()
```

**Verify**: revisa `privacy_after.png` a simple vista — debe usar la misma paleta
crema/verde oscuro que `index.html` (no morado, no gris neutro de `system-ui`), y
tener un header simple arriba con el link de vuelta.

### Paso 4: Smoke test del repo

**Verify**: `make verify-landing` → exit 0 (este test no visita `privacy.html`, pero
confirma que no rompiste nada en `index.html` si tocaste algo ahí por error).

## Test plan

No hay tests automatizados para `privacy.html` en este repo. La verificación es visual
(Paso 3). No agregues `privacy.html` a `scripts/verify_landing.py` en este plan — ese
script está específicamente estructurado alrededor de `index.html` y su lógica
dinámica (`renderCatalog`, KPIs, drawer); agregar cobertura de `privacy.html` ahí es un
cambio de alcance distinto (podría proponerse como plan aparte si se considera
valioso).

## Done criteria

- [ ] `grep -n "6C47FF\|system-ui" privacy.html` no devuelve coincidencias
- [ ] `grep -n "<header>\|<footer>" privacy.html` muestra ambos elementos
- [ ] La captura del Paso 3 muestra la paleta crema/verde del sitio, no morado
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `privacy.html`
- [ ] `plans/README.md` actualizado

## STOP conditions

Detente y reporta si:

- El contenido de `privacy.html` ya no coincide con el extracto de "Estado actual"
  (alguien reescribió la página).
- Decides que hace falta compartir un archivo de tokens/CSS entre `index.html` y
  `privacy.html` en vez de duplicar los valores hex — eso es un cambio de arquitectura
  más grande que el alcance S de este plan; repórtalo como sugerencia en vez de
  implementarlo.

## Maintenance notes

- Si `index.html` cambia su paleta de colores (`--bg-color`, `--accent-green`, etc.)
  en el futuro, `privacy.html` quedará desincronizado porque los valores están
  duplicados como literales, no importados. Vale la pena revisar ambos archivos juntos
  cuando se retoque la paleta.
- Un revisor de PR debería confirmar que el link "← chile-hub" / "Volver a chile-hub"
  sigue apuntando a `index.html` (ruta relativa, no absoluta) para que funcione tanto
  en local como en producción bajo `/chile-hub/`.
