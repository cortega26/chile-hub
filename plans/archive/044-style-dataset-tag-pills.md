# Plan 044: Estilizar `.dataset-tag` (pills de "key:" y "N warnings" en las tarjetas del catálogo)

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html app.js`
> Si estos archivos cambiaron desde que se escribió este plan, compara los
> extractos de "Estado actual" contra el código real antes de continuar; si no
> coinciden, trátalo como un STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

`app.js` genera dinámicamente las 15+ tarjetas de la sección "Capas publicadas" (el
catálogo principal del sitio). Cada tarjeta incluye spans con clase `dataset-tag`
para mostrar las claves de cruce (`key: codigo_comuna`) y, cuando aplica, un conteo de
advertencias (`2 warnings`):

- `app.js:930` — `` `<span class="dataset-tag key-tag">key: ${escapeHtml(key)}</span>` ``
- `app.js:897` — `` `<span class="dataset-tag warning">${dataset.warning_count} warnings</span>` ``
- `app.js:515` — `` `<span class="dataset-tag" style="margin-bottom: 0.25rem; display: inline-block;">...</span>` `` (nombres de columnas en el drawer)

**Ninguna de estas clases tiene una regla CSS.** Se confirmó con
`grep -n "dataset-tag" index.html`: la única coincidencia es `.dataset-tags` (con
"s" final, un contenedor distinto y no relacionado, que además está oculto con
`display: none` — ver `index.html:1109-1111`). `.dataset-tag` (singular, la clase
que `app.js` realmente usa) no tiene ningún selector que la alcance.

Se verificó empíricamente con Playwright el estilo computado de un `.dataset-tag` real
en producción:

```
{'background': 'rgba(0, 0, 0, 0)', 'padding': '0px', 'borderRadius': '0px',
 'border': '0px none rgb(26, 34, 31)', 'fontSize': '16px', 'display': 'block',
 'text': 'key: codigo_comuna'}
```

Es decir: sin fondo, sin padding, sin borde, sin radio de esquina, y con
`font-size: 16px` (el tamaño por defecto del navegador — notablemente más grande que
el resto del texto de la tarjeta, que usa la escala 0.7-0.9rem del sitio). El resultado,
confirmado con captura de pantalla, es texto plano sin estilo ("key: codigo_comuna
key: codigo_region") flotando bajo la grilla de datos de cada tarjeta, en fuerte
contraste con el resto del sistema de badges/pills del sitio (`.status-pill`,
`.dataset-badge`, `.comuna-code`, `.pill`), que sí están bien diseñados.

Esto es visible en **cada una de las 15 tarjetas** de la sección más importante del
sitio (el catálogo de datos) — es el hallazgo de mayor visibilidad de esta auditoría
después del Plan 043.

## Decisión de diseño requerida antes de implementar

Hay dos caminos razonables; **elige uno explícitamente antes de escribir CSS** (no lo
dejes implícito):

- **(A) Darles estilo de pill**, consistente con el resto de badges del sitio
  (`.status-pill`, `.comuna-code`). Recomendado: la información (claves de cruce,
  conteo de advertencias) es útil y su ausencia de estilo es claramente un descuido,
  no una decisión deliberada de ocultarla.
- **(B) Ocultarlos**, igual que ya se hace con `.dataset-tags` (plural,
  `display: none`, comentario "hidden developer metadata" en `index.html:1109-1111`) —
  si se determina que esta información es "metadata de desarrollador" que no debería
  mostrarse al usuario final.

Este plan implementa **(A)** por ser la opción de menor riesgo (agregar CSS, no
remover contenido) y la que preserva más valor informativo. Si tras revisar el
resultado visual se prefiere (B), es un cambio de una línea (agregar
`.dataset-tag { display: none; }`) — se documenta como alternativa en el Paso 1.

## Estado actual

- `index.html:1109-1111` — la única regla relacionada (para un selector distinto):
  ```css
  .dataset-tags {
      display: none; /* hidden developer metadata */
  }
  ```
- `index.html:914-922` — patrón de referencia ya usado para otro tipo de badge en la
  misma tarjeta (`.dataset-badge`), buena plantilla de la estética esperada:
  ```css
  .dataset-badge {
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      white-space: nowrap;
  }
  ```
- `app.js:889-932` — la función que genera cada tarjeta del catálogo (`renderCatalog`),
  extracto relevante:
  ```js
  const warningBadge = dataset.warning_count > 0
      ? `<span class="dataset-tag warning">${dataset.warning_count} warnings</span>`
      : "";

  return `
      <article class="dataset-card" id="dataset-${escapeHtml(dataset.dataset)}" ...>
          ...
          <div style="margin-top: 0.75rem; display: flex; gap: 0.35rem; flex-wrap: wrap;">
              ${(dataset.join_keys || []).map(key => `<span class="dataset-tag key-tag">key: ${escapeHtml(key)}</span>`).join("")}
              ${warningBadge}
          </div>
          ...
      </article>
  `;
  ```
  El contenedor (el `<div style="...">` sin clase) ya tiene `display: flex; gap: 0.35rem;
  flex-wrap: wrap;` en línea — no hace falta tocarlo, sólo los hijos `.dataset-tag`
  necesitan estilo propio.

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` (desde la raíz del repo) | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 |

## Scope

**En alcance**:
- `index.html` — agregar reglas CSS para `.dataset-tag`, `.dataset-tag.key-tag`,
  `.dataset-tag.warning`.

**Fuera de alcance (no tocar)**:
- `app.js` — el HTML generado ya usa las clases correctas (`dataset-tag`, `key-tag`,
  `warning`); no hace falta cambiar el JS, sólo agregar CSS.
- `.dataset-tags` (plural, `index.html:1109-1111`) — selector distinto, ya
  intencionalmente oculto, no lo toques.
- El bloque `<!-- START_DATA_CATALOG_JSON_LD --> ... <!-- END_DATA_CATALOG_JSON_LD -->`
  (`index.html:42-289`) — lo regenera `src/builders/landing.py`; no lo edites a mano.

## Pasos

### Paso 1: Agregar estilo de pill para `.dataset-tag`

En `index.html`, dentro del bloque `<style>`, inmediatamente después de la regla
`.dataset-badges` (`index.html:907-912`) o cerca de `.dataset-tags`
(`index.html:1109-1111`), agrega:

```css
.dataset-tag {
    display: inline-flex;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-secondary);
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    line-height: 1.25;
}

.dataset-tag.key-tag {
    color: var(--accent-green);
    background: var(--accent-green-light);
    border-color: rgba(18, 61, 48, 0.15);
}

.dataset-tag.warning {
    color: var(--accent-warm);
    background: var(--accent-warm-bg);
    border-color: var(--accent-warm-border);
}
```

Estos valores reutilizan tokens ya existentes (`--accent-green-light`,
`--accent-warm-bg`, etc. — los mismos que usa `.dataset-badge.live` /
`.dataset-badge.fallback`, ver `index.html:924-934`), así que los pills quedan
visualmente coherentes con el resto del sistema de badges sin introducir colores
nuevos.

**Alternativa (opción B, si se decide ocultar en vez de estilizar)**: reemplaza todo
lo anterior por:
```css
.dataset-tag {
    display: none;
}
```
y detente ahí — no necesitas los pasos de verificación visual de pills, sólo confirmar
que ya no aparece texto suelto (Paso 2 sigue aplicando, sólo que el DOM check busca
`display: none` en vez de colores).

**Verify**: `grep -n "\.dataset-tag {" index.html` → debe mostrar la regla nueva.

### Paso 2: Verificación visual con Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    tag = page.locator(".dataset-tag").first
    style = tag.evaluate("""el => {
        const cs = getComputedStyle(el);
        return { background: cs.backgroundColor, padding: cs.padding,
                 borderRadius: cs.borderRadius, fontSize: cs.fontSize };
    }""")
    print(style)
    page.locator(".dataset-card").first.screenshot(path="card_after.png")
    browser.close()
```

**Verify** (si implementaste la opción A, pills): `background` ya no es
`rgba(0, 0, 0, 0)`, `padding` ya no es `0px`, `borderRadius` ya no es `0px`, y
`fontSize` es menor a `16px` (debería ser `~10.9px`, equivalente a `0.68rem` con la
raíz por defecto de 16px). La captura `card_after.png` debe mostrar los tags "key:
codigo_comuna" y "N warnings" como chips con fondo y borde, no como texto plano.

### Paso 3: Smoke test del repo

**Verify**: `make verify-landing` → exit 0. Este smoke test hace clic en
`.technical-details` y lee `#status-actions .dataset-action` (clase distinta a
`.dataset-tag`, no debería verse afectada), pero confirma que nada más se rompió.

## Test plan

No hay tests automatizados de CSS/visual en este repo. La verificación es el Paso 2
(computed style + captura) más el smoke test del Paso 3. No crees tests nuevos en
`tests/` — es un cambio puramente de presentación en archivos estáticos fuera del
árbol Python que cubre `pytest`.

## Done criteria

- [ ] `grep -n "\.dataset-tag" index.html` muestra las reglas nuevas (o la regla
      `display: none` si se eligió la opción B)
- [ ] El script del Paso 2 confirma que `.dataset-tag` ya no tiene
      `background: rgba(0, 0, 0, 0)` / `padding: 0px` (opción A) o confirma
      `display: none` (opción B)
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `index.html`
- [ ] `plans/README.md` actualizado con el estado de este plan y qué opción (A o B)
      se implementó

## STOP conditions

Detente y reporta si:

- El extracto de `app.js:889-932` ya no coincide con el código real (las clases que
  genera `renderCatalog` cambiaron de nombre).
- No puedes decidir entre la opción A y B por tu cuenta — repórtalo con tu
  recomendación y espera confirmación antes de implementar.
- `make verify-landing` falla por una razón no relacionada con este cambio.

## Maintenance notes

- Si se agregan más `join_keys` a un dataset (ver `contracts/datasets/`), los pills se
  ajustan automáticamente por el `flex-wrap: wrap` ya presente en el contenedor — no
  requiere cambios adicionales.
- Un revisor de PR debería confirmar visualmente que los pills no rompen el layout en
  viewport móvil (375px) — el contenedor ya usa `flex-wrap: wrap`, así que deberían
  apilarse correctamente, pero vale la pena una captura de pantalla móvil como
  evidencia en el PR.
