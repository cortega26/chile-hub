# Plan 047: Corregir `var(--space-lg)` no definida y la fuente `Fira Code` que nunca carga

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html`
> Si el archivo cambió desde que se escribió este plan, compara los extractos de
> "Estado actual" contra el código real antes de continuar; si no coincide,
> trátalo como un STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (spacing / typography)
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

Dos defectos pequeños e independientes, agrupados en un solo plan por ser ambos
de una línea y en el mismo archivo:

**1. `var(--space-lg)` nunca se definió.** `index.html:2752` usa
`margin-top:var(--space-lg)` en un `style` inline, pero `:root` (`index.html:298-326`)
no define ninguna variable `--space-*` — se confirmó con
`grep -n "space-lg\|--space" index.html`, que sólo encuentra el único *uso*, nunca una
*definición*. Por la especificación CSS, una `var()` que referencia una variable no
definida y sin fallback es inválida en tiempo de cómputo; para una propiedad no
heredada como `margin-top`, el resultado es su valor inicial: `0`. Se confirmó
empíricamente con `getComputedStyle`: `marginTop` computa a `"0px"`. El efecto visual
(confirmado con captura de pantalla): el link "Leer el caso de estudio completo →"
queda pegado directamente debajo del grid de 4 columnas de "Los datos son tan buenos
como su procedencia", sin el respiro que el autor claramente pretendía darle.

**2. La consola del hero declara una fuente que el sitio nunca carga.**
`index.html:2020` fija `font-family: 'Fira Code', 'Courier New', Courier, monospace;`
para `.playground-console`, pero el único `<link>` de Google Fonts del sitio
(`index.html:295`) sólo importa `Lora`, `IBM Plex Mono` e `IBM Plex Sans`. Se confirmó
con `grep -n "Fira Code" index.html` (una sola coincidencia, la declaración CSS —
ningún `@font-face` ni link la carga). El navegador cae automáticamente a
`'Courier New'`, ignorando por completo el propio `--font-mono: 'IBM Plex Mono'` del
sitio que ya está cargado y que se usa consistentemente en el resto del sitio (tablas,
badges, código). El widget más prominente del hero (la consola de "inicio rápido") usa
una tipografía monoespaciada distinta a la de cualquier otro bloque de código del
sitio.

## Estado actual

`index.html:2741-2755` (sección `#confianza`, contexto completo del bug 1):
```html
<section class="section-shell" id="confianza">
    <div class="section-heading">
        <h2>Los datos son tan buenos como su procedencia</h2>
        <p>Cada capa incluye la información que necesitas para decidir si sirve en producción, análisis o investigación.</p>
    </div>
    <div class="trust-grid">
        <article class="trust-item"><h3>Procedencia</h3>...</article>
        ...
    </div>
    <p style="text-align:center; margin-top:var(--space-lg);">
        <a href="https://github.com/cortega26/chile-hub/blob/main/docs/case-study-construccion-chile-hub.md">Leer el caso de estudio completo →</a>
    </p>
</section>
```

`index.html:2014-2026` (contexto completo del bug 2):
```css
.playground-console {
    background: #0f172a;
    border-radius: 12px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.25), 0 10px 10px -5px rgba(0, 0, 0, 0.15);
    border: 1px solid #1e293b;
    overflow: hidden;
    font-family: 'Fira Code', 'Courier New', Courier, monospace;
    font-size: 0.85rem;
    color: #e2e8f0;
    display: flex;
    flex-direction: column;
    min-height: 220px;
}
```

`index.html:295` (el único `<link>` de fuentes del sitio):
```html
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=IBM+Plex+Mono:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&display=swap" rel="stylesheet">
```

`index.html:321-323` (tokens de fuente ya definidos, para reutilizar en el fix del
bug 2):
```css
--font-display: 'Lora', Georgia, serif;
--font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 |

## Scope

**En alcance**:
- `index.html:2752` — reemplazar `var(--space-lg)` por un valor concreto.
- `index.html:2020` — decidir entre (a) usar `var(--font-mono)` en vez de
  `'Fira Code'`, o (b) agregar `Fira Code` al `<link>` de Google Fonts. Ver Paso 2
  para la recomendación y el criterio de decisión.

**Fuera de alcance**:
- No introduzcas un sistema completo de variables de espaciado (`--space-sm`,
  `--space-md`, `--space-lg`, `--space-xl`...) sólo para resolver este único uso —
  este archivo no tiene ese sistema hoy (es el único lugar que referencia
  `--space-*` en todo el archivo) y crearlo de la nada para un solo consumidor es una
  abstracción prematura. Usa un valor literal en rem, consistente con cómo el resto
  del archivo maneja el espaciado (ej. `.package-verify { margin-top: 1rem; }`,
  `.explorer-heading { margin-top: 1rem; }`).
- No toques ninguna otra sección del archivo.

## Pasos

### Paso 1: Definir un valor concreto para el margen del bug 1

Reemplaza en `index.html:2752`:
```html
<p style="text-align:center; margin-top:var(--space-lg);">
```
por:
```html
<p style="text-align:center; margin-top:2rem;">
```

`2rem` se eligió porque coincide con el ritmo vertical que ya usan los quiebres de
sección mayores en este archivo (ej. `.section-shell { padding-top: 2rem; }`,
`index.html:1296`) — este link actúa como un cierre de sección antes del siguiente
bloque (`#uso`), así que un espaciado a nivel de sección es apropiado. Si tras la
verificación visual (Paso 3) el espacio se ve desproporcionado respecto a los
`trust-item` de arriba, usa tu criterio dentro de un rango de `1.5rem`–`3rem`, pero
**no lo dejes en `0` ni vuelvas a usar una variable no definida**.

**Verify**: `grep -n "space-lg" index.html` → no debe devolver ninguna coincidencia.

### Paso 2: Resolver la fuente `Fira Code` de la consola

**Recomendación**: usa `var(--font-mono)` en vez de agregar una fuente web nueva.
Razón: `.playground-console` es un widget de "código" y el sitio ya tiene una fuente
monoespaciada bien establecida (`IBM Plex Mono`) que se usa en absolutamente todos los
demás bloques de código del sitio (`.quickstart-code`, `.dataset-example-code`,
`.comuna-code`, `th`/`td` en tablas de datos). Usar la misma fuente en la consola del
hero es más consistente que importar una segunda fuente monoespaciada sólo para este
widget, y evita el costo de red de una fuente adicional.

Reemplaza en `index.html:2020`:
```css
font-family: 'Fira Code', 'Courier New', Courier, monospace;
```
por:
```css
font-family: var(--font-mono);
```

**Alternativa** (si tras ver el resultado se prefiere mantener una identidad visual
distinta para la consola, deliberadamente distinta al resto del sitio): agrega
`Fira+Code:wght@400;500;600` a la URL de Google Fonts en `index.html:295` y deja el
`font-family` como está. Si tomas este camino, documenta explícitamente en el mensaje
de commit que fue una decisión deliberada de mantener dos fuentes monoespaciadas,
no un descuido.

**Verify**: `grep -n "Fira Code" index.html` → si implementaste la recomendación, no
debe devolver ninguna coincidencia (todo `Fira Code` desapareció). Si implementaste la
alternativa, debe aparecer tanto en el `<link>` de Google Fonts como en el
`font-family` de `.playground-console`.

### Paso 3: Verificación visual con Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")

    link_p = page.locator("#confianza p").last
    margin = link_p.evaluate("e => getComputedStyle(e).marginTop")
    print("margin-top:", margin)
    link_p.scroll_into_view_if_needed()
    page.screenshot(path="trust_spacing_after.png")

    console = page.locator(".playground-console")
    font = console.evaluate("e => getComputedStyle(e).fontFamily")
    print("console font-family:", font)

    browser.close()
```

**Verify**: `margin-top` ya no es `"0px"` (debe ser `"32px"` si usaste `2rem`).
`console font-family` debe reflejar el cambio elegido en el Paso 2 (o bien ya no
menciona `Fira Code`, o bien `Fira Code` sigue ahí pero ahora está cargada por el
`<link>`). La captura `trust_spacing_after.png` debe mostrar un espacio visible entre
el grid de confianza y el link del caso de estudio.

### Paso 4: Smoke test del repo

**Verify**: `make verify-landing` → exit 0.

## Test plan

No hay tests automatizados de CSS en este repo. La verificación es el Paso 3 más el
smoke test del Paso 4.

## Done criteria

- [ ] `grep -n "space-lg" index.html` no devuelve coincidencias
- [ ] El script del Paso 3 confirma `margin-top` distinto de `"0px"`
- [ ] La decisión sobre `Fira Code` está implementada de forma consistente (o
      eliminada del todo, o cargada correctamente vía `<link>`) — no queda a medias
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `index.html`
- [ ] `plans/README.md` actualizado, indicando qué opción del Paso 2 se eligió

## STOP conditions

Detente y reporta si:

- Los extractos de "Estado actual" ya no coinciden con `index.html`.
- No estás seguro de si `2rem` es el valor visualmente correcto tras ver la captura —
  repórtalo con la captura adjunta en vez de adivinar un valor arbitrario.

## Maintenance notes

- Si en el futuro se introduce un sistema real de variables de espaciado
  (`--space-sm/md/lg/xl`), este `margin-top: 2rem` debería migrarse a
  `var(--space-lg)` en ese momento — no antes, para no crear una abstracción de un
  solo uso.
- Un revisor de PR debería confirmar con una captura de pantalla que el espaciado se
  ve proporcionado respecto a las demás secciones del sitio.
