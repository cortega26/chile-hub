# Plan 048: Consolidar las reglas CSS duplicadas de `.dataset-card` y quitar el `!important` de `.catalog-grid`

> **Executor instructions**: Sigue este plan paso a paso, en orden. Este plan
> es más delicado que los demás de esta serie — requiere capturar un estado
> "antes" con Playwright antes de tocar nada, y comparar contra un estado
> "después" para garantizar cero cambio visual. No te saltes los pasos de
> captura. Si algo en "STOP conditions" ocurre, detente y reporta — no
> improvises. Al terminar, actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html app.js`
> Si estos archivos cambiaron desde que se escribió este plan, vuelve a correr
> los `grep` del "Estado actual" contra el código real antes de continuar; si
> los números de línea o el contenido no coinciden, trátalo como un STOP
> condition y re-deriva las tablas de clasificación abajo desde cero contra el
> código actual (no confíes en los números de línea de este documento si hubo
> drift).

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED — un borrado ingenuo del "bloque viejo" completo rompe estilos que el
  drawer de detalles SÍ usa hoy en producción (ver clasificación abajo). Este riesgo se
  mitiga siguiendo el método de verificación visual antes/después de este plan al pie
  de la letra.
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

`index.html` define la familia de selectores `.dataset-card` **dos veces**, en dos
regiones distintas del mismo bloque `<style>`:

- **Bloque A** ("archive card index" / estética "vintage"), `index.html:840-1292`.
- **Bloque B** ("Compact card details styling"), `index.html:2298-2427`.

Como ambos bloques usan exactamente los mismos selectores (`.dataset-card`,
`.dataset-name`, `.dataset-badge`, etc.) con la misma especificidad, la cascada CSS
resuelve **cada propiedad por separado**: para las propiedades que ambos bloques
declaran, gana el Bloque B (aparece después en el archivo); para las propiedades que
sólo declara el Bloque A y el Bloque B no las toca, esas siguen activas aunque
"parezcan" reemplazadas. Esto ya se verificó con casos concretos:

- `.dataset-card` en el Bloque A tiene `position: relative; overflow: hidden;` — el
  Bloque B no redeclara ninguna de las dos, así que **siguen activas hoy**.
- `.dataset-card::before` y `.dataset-card:hover::before` (la barra superior de acento
  verde que aparece al pasar el mouse) sólo existen en el Bloque A — **siguen activas
  hoy** porque nada las redefine.
- `.dataset-card:target` (el resaltado cuando se navega a `#dataset-X` directamente)
  sólo existe en el Bloque A — **sigue activo hoy**.

Además, `.catalog-grid` está definido **tres veces**:
1. `index.html:833-838` — `display: grid; grid-template-columns: repeat(2, ...); gap:
   1.25rem; align-items: start;` (sin `!important`).
2. `index.html:2247-2251` — `display: flex !important; flex-direction: column
   !important; gap: 2.5rem !important;` (con `!important`, forzando la victoria sobre
   la definición #1 incluso si el orden fuera al revés).
3. `index.html:2260-2264` (dentro de un `@media (max-width: 960px)`) —
   `.catalog-grid-sub` (selector distinto, no conflictivo).

El `!important` en la definición #2 es una señal de que en algún momento alguien
luchó contra la cascada en vez de resolver el conflicto de raíz. Hoy no causa un bug
visible (el `align-items: start` residual de la definición #1 no importa porque
`.catalog-category`, el hijo real, tiene `width: 100%` explícito que anula cualquier
efecto de `align-items` en el eje cruzado) — pero es una mina para el próximo cambio:
cualquiera que intente ajustar `.catalog-grid` en el futuro va a modificar la
definición equivocada, o va a necesitar su propio `!important` para ganarle al
existente, empeorando el problema.

Este plan no es un bug visible — es higiene que reduce el riesgo de la *próxima*
modificación a esta zona del CSS. Impacto MEDIO, no ALTO; se prioriza después de los
planes 043-047 que sí son bugs visibles.

## Clasificación completa: qué está muerto, qué está vivo, qué hay que fusionar

Se determinó leyendo `app.js` completo (la única fuente que genera el HTML dinámico
que usa estas clases) y contando cada uso real. Comandos usados para verificar (puedes
re-ejecutarlos para confirmar que no hay drift):

```bash
grep -c "dataset-badges\|dataset-facts-primary\|dataset-actions\"\|dataset-details\"\|dataset-detail-section\|dataset-detail-heading\|dataset-detail-grid\|dataset-detail-row\|dataset-meta-label\|dataset-artifacts\"\|dataset-tags\"\|dataset-preview\"" app.js
```

### Grupo 1 — Selectores del Bloque A totalmente muertos (0 usos en `app.js` ni en el
HTML estático de `index.html`). Seguros de **eliminar por completo**:

| Selector | Líneas (`index.html`) |
|---|---|
| `.dataset-badges` | 907-912 |
| `.dataset-facts-primary` | 946-948 |
| `.dataset-actions` | 974-980 |
| `.dataset-details`, `.dataset-details[open] summary`, `.dataset-details-body` | 1018-1034 |
| `.dataset-detail-section`, `.dataset-detail-section:first-of-type`, `.dataset-detail-section.wide` | 1036-1051 |
| `.dataset-details .dataset-facts` | 1053-1055 |
| `.dataset-detail-heading` | 1057-1062 |
| `.dataset-detail-grid` | 1064-1068 |
| `.dataset-detail-row` | 1070-1075 |
| `.dataset-meta-label` (ojo: `.dataset-meta-line` y `.dataset-meta-line strong` NO están en esta lista, están vivos — ver Grupo 3) | 1085-1089 |
| `.dataset-artifacts` (plural — `.dataset-artifact-meta`, singular, SÍ está vivo, ver Grupo 3) | 1095-1100 |
| `.dataset-tags` (plural, ya estaba `display:none`; distinto de `.dataset-tag` singular que el Plan 044 estiliza) | 1109-1112 |
| `.dataset-preview` (el contenedor, distinto de `.dataset-preview-table`/`-note`/`-state`, que SÍ están vivos) | 1114-1119 |

También en el `@media (max-width: 580px)` (`index.html:1892-1910`), estas reglas hacen
referencia a selectores del Grupo 1 y deben eliminarse junto con ellos:
```css
.dataset-detail-section.wide { grid-column: auto; }
.dataset-detail-row { grid-template-columns: 1fr; gap: 0.15rem; }
```
(`.dataset-facts` y `.dataset-details-body` en ese mismo bloque responsive — revisa
cuál de los dos selectores agrupados sigue vivo antes de tocar la línea; `.dataset-facts`
está vivo, `.dataset-details-body` no).

### Grupo 2 — Selectores duplicados en ambos bloques (requieren fusión cuidadosa, no
sólo borrado):

| Selector | Bloque A | Bloque B |
|---|---|---|
| `.dataset-card` | 841-853 | 2299-2309 |
| `.dataset-card::before` | 855-865 | *(no existe en B — mantener tal cual)* |
| `.dataset-card:hover` | 867-870 | 2311-2314 |
| `.dataset-card:hover::before` | 872-874 | *(no existe en B — mantener tal cual)* |
| `.dataset-card:target` | 876-880 | *(no existe en B — mantener tal cual)* |
| `.dataset-card-top` | 882-888 | 2316-2321 |
| `.dataset-name` | 890-897 | 2323-2329 |
| `.dataset-desc` | 899-905 | 2331-2340 |
| `.dataset-badge` | 914-922 | 2342-2350 |
| `.dataset-badge.live` | 924-928 | 2352-2355 |
| `.dataset-badge.fallback` | 930-934 | 2357-2360 |

### Grupo 3 — Selectores del Bloque A que SÍ están vivos hoy (usados por el drawer de
detalle de dataset en `app.js`). **No tocar, no mover, no eliminar**:

| Selector | Usado en `app.js` (líneas aprox.) |
|---|---|
| `.dataset-facts` (sin `-grid`, sin `-primary`) | 522 |
| `.dataset-fact`, `.dataset-fact-label`, `.dataset-fact-value` | 523-546 |
| `.dataset-action` (incluye `.dataset-action.muted`) | 73, 206, 223, 724, 728, 865 |
| `.dataset-meta-line`, `.dataset-meta-line strong` | 562-568 |
| `.dataset-artifact-meta` (singular) | 578, 587 |
| `.dataset-preview-table`, `.dataset-preview-note`, `.dataset-preview-state` | 296-325, 456-490 |
| `.dataset-example` y toda su familia (`-head`, `-title`, `-tabs`, `-tab`, `-copy`,
  `-code`) | 262-368 |
| `.monedario-bridge` (y sus hijos) | 339 |

### El resto de duplicados fuera de la familia `.dataset-card`

| Selector | Definición #1 | Definición #2 |
|---|---|---|
| `.catalog-grid` | `index.html:833-838` (sin `!important`) | `index.html:2247-2251` (con `!important`) |

## Estado actual (extractos representativos)

Bloque A, `.dataset-card` (`index.html:841-874`):
```css
.dataset-card {
    background-color: #ffffff;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 1.35rem;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    transition: var(--transition);
    position: relative;
    min-width: 0;
    overflow: hidden;
}

.dataset-card::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 20px;
    right: 20px;
    height: 2px;
    background-color: var(--accent-green);
    opacity: 0;
    transition: var(--transition);
}

.dataset-card:hover {
    border-color: var(--border-color-dark);
    box-shadow: 0 4px 12px rgba(25, 33, 30, 0.03);
}

.dataset-card:hover::before {
    opacity: 1;
}

.dataset-card:target {
    scroll-margin-top: 1.5rem;
    border-color: var(--accent-green);
    box-shadow: 0 0 0 3px rgba(18, 61, 48, 0.08);
}
```

Bloque B, `.dataset-card` (`index.html:2298-2314`):
```css
/* Compact card details styling */
.dataset-card {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: #ffffff;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 1rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.dataset-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
```

`.catalog-grid`, ambas definiciones:
```css
/* index.html:833-838 */
.catalog-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.25rem;
    align-items: start;
}

/* index.html:2247-2251 */
.catalog-grid {
    display: flex !important;
    flex-direction: column !important;
    gap: 2.5rem !important;
}
```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 |

## Scope

**En alcance**: sólo `index.html`, sólo las reglas CSS listadas en los Grupos 1 y 2 de
arriba, más las dos definiciones de `.catalog-grid`.

**Fuera de alcance (no tocar bajo ningún motivo)**:
- Cualquier selector del Grupo 3 — están vivos, borrarlos rompe el drawer de detalle.
- `.catalog-grid-sub` — selector distinto, no forma parte de este problema.
- `app.js` — no genera nada que dependa de este cambio; el HTML que emite no cambia.
- Cualquier otro selector fuera de esta lista explícita.

## Pasos

### Paso 0 (obligatorio): Capturar el estado "antes"

Antes de tocar una sola línea, sirve el sitio y captura el estado visual y computado
actual como línea base:

```bash
python3 -m http.server 8877 &
```

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    card = page.locator(".dataset-card").first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    page.screenshot(path="card_before_normal.png",
                     clip=card.bounding_box() | {"x": card.bounding_box()["x"] - 10,
                                                  "y": card.bounding_box()["y"] - 10,
                                                  "width": card.bounding_box()["width"] + 20,
                                                  "height": card.bounding_box()["height"] + 20})

    card.hover()
    page.wait_for_timeout(400)  # dejar correr la transición
    page.screenshot(path="card_before_hover.png",
                     clip=card.bounding_box() | {"x": card.bounding_box()["x"] - 10,
                                                  "y": card.bounding_box()["y"] - 10,
                                                  "width": card.bounding_box()["width"] + 20,
                                                  "height": card.bounding_box()["height"] + 20})

    computed = card.evaluate("""el => {
        const cs = getComputedStyle(el);
        return {
            position: cs.position, overflow: cs.overflow, borderRadius: cs.borderRadius,
            padding: cs.padding, gap: cs.gap, transition: cs.transition
        };
    }""")
    print("computed .dataset-card (normal):", computed)

    grid = page.locator("#catalog-grid")
    grid_style = grid.evaluate("el => ({display: getComputedStyle(el).display, alignItems: getComputedStyle(el).alignItems})")
    print("computed #catalog-grid:", grid_style)

    browser.close()
```

Guarda `card_before_normal.png`, `card_before_hover.png`, y los dos `print()` — los vas
a comparar en el Paso 4. **No avances al Paso 1 sin esto.**

### Paso 1: Eliminar los selectores totalmente muertos (Grupo 1)

Elimina del Bloque A cada regla listada en la tabla del Grupo 1 (arriba), incluyendo
sus referencias dentro del `@media (max-width: 580px)` (`index.html:1892-1910`) —
pero **sólo las líneas de ese media query que referencian selectores del Grupo 1**;
dentro de ese mismo bloque responsive hay líneas que tocan `.dataset-card`,
`.dataset-facts` (vivo) y `.dataset-details-body` (muerto) mezcladas en un mismo
selector agrupado — sepáralas con cuidado, no borres el selector completo si incluye
algo vivo.

**Verify**: después de este paso, `grep -n "dataset-badges\|dataset-facts-primary\|dataset-actions\"\|dataset-details\b\|dataset-detail-section\|dataset-detail-heading\|dataset-detail-grid\|dataset-detail-row\|dataset-meta-label\|dataset-artifacts\"\|dataset-tags\"\|dataset-preview\"" index.html` no debe devolver ninguna coincidencia.

### Paso 2: Fusionar los selectores duplicados (Grupo 2)

Para cada selector de la tabla del Grupo 2, fusiona ambas definiciones en **una sola**,
ubicada donde hoy está el Bloque B (más cerca del resto de las reglas "compactas" que
sí siguen vivas), preservando el **resultado actualmente renderizado** — es decir, para
cada propiedad, usa el valor que gana hoy en la cascada real (el que declara el
Bloque B si ambos la declaran; el del Bloque A si sólo él la declara). Ejemplo para
`.dataset-card`:

```css
.dataset-card {
    background: #ffffff;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 1rem;
    transition: border-color 0.2s, box-shadow 0.2s;
    position: relative;
    min-width: 0;
    overflow: hidden;
}

.dataset-card::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 20px;
    right: 20px;
    height: 2px;
    background-color: var(--accent-green);
    opacity: 0;
    transition: var(--transition);
}

.dataset-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

.dataset-card:hover::before {
    opacity: 1;
}

.dataset-card:target {
    scroll-margin-top: 1.5rem;
    border-color: var(--accent-green);
    box-shadow: 0 0 0 3px rgba(18, 61, 48, 0.08);
}
```

Repite el mismo criterio ("qué gana hoy, por propiedad") para `.dataset-card-top`,
`.dataset-name`, `.dataset-desc`, `.dataset-badge`, `.dataset-badge.live`,
`.dataset-badge.fallback` — en la práctica, como el Bloque B declara casi todas las
propiedades visuales de estos selectores, el resultado consolidado será casi idéntico
al Bloque B, más cualquier propiedad huérfana del Bloque A que el Bloque B nunca tocó.
Elimina las definiciones antiguas del Bloque A una vez fusionadas en su nueva ubicación.

**Verify**: `grep -c "^\s*\.dataset-card {" index.html` → debe devolver `1` (antes
devolvía `2`). Repite para `.dataset-card-top`, `.dataset-name`, `.dataset-desc`,
`.dataset-badge {`, `.dataset-badge.live`, `.dataset-badge.fallback` — cada uno debe
aparecer una sola vez.

### Paso 3: Quitar el `!important` de `.catalog-grid`

Como la definición en `index.html:2247-2251` es la única que debe sobrevivir (es la
que efectivamente se usa hoy — el layout real es `flex column`, no `grid`), elimina la
definición antigua (`index.html:833-838`) por completo y quita los tres `!important`
de la definición que queda, ya que sin el conflicto no hace falta forzar la cascada:

```css
.catalog-grid {
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
}
```

Aplica el mismo criterio a `.catalog-grid-sub` (`index.html:2253-2257` y su variante
responsive en `index.html:2260-2264`) **sólo si** al revisar el archivo confirmas que
no tiene una segunda definición en conflicto (a diferencia de `.catalog-grid`, este
selector no debería tener duplicados — confírmalo con
`grep -n "\.catalog-grid-sub {" index.html`, debe aparecer sólo en el bloque base y
dentro del `@media`, nunca dos veces fuera de un media query). Si en efecto no hay
conflicto, quitar sus `!important` es opcional pero recomendado por consistencia — no
es obligatorio para este plan si prefieres minimizar el diff.

**Verify**: `grep -c "\.catalog-grid {" index.html` → debe devolver `1`.
`grep -n "!important" index.html | grep catalog` → no debe devolver líneas de
`.catalog-grid` (las de `.catalog-grid-sub`, si decidiste no tocarlas, sí pueden
seguir apareciendo).

### Paso 4 (obligatorio): Comparar contra el estado "antes"

Repite exactamente el script del Paso 0 contra el archivo ya modificado
(`card_after_normal.png`, `card_after_hover.png`, nuevos `print()`).

**Verify**:
- `card_after_normal.png` debe verse **idéntico** a `card_before_normal.png` a simple
  vista.
- `card_after_hover.png` debe verse **idéntico** a `card_before_hover.png` — en
  particular, la barra superior de acento verde en hover (`::before`) debe seguir
  apareciendo si aparecía antes.
- Los valores de `computed .dataset-card (normal)` deben ser idénticos entre antes y
  después (`position: relative`, `overflow: hidden` deben seguir presentes).
- `computed #catalog-grid` debe mostrar `display: flex` en ambos casos (esto no
  cambia, sólo se limpia el mecanismo que lo logra).

Si **cualquiera** de estas comparaciones muestra una diferencia, es un STOP condition
— no continúes ajustando a ciegas.

### Paso 5: Smoke test del repo

**Verify**: `make verify-landing` → exit 0.

## Test plan

No hay tests automatizados de CSS en este repo. La verificación es el método
antes/después de los Pasos 0 y 4, más el smoke test del Paso 5. Conserva los 4
screenshots (`card_before_normal.png`, `card_before_hover.png`, `card_after_normal.png`,
`card_after_hover.png`) y adjúntalos como evidencia en el PR o en el reporte final.

## Done criteria

- [ ] Cada selector del Grupo 1 fue eliminado por completo (`grep` de la lista
      combinada no devuelve coincidencias)
- [ ] Cada selector del Grupo 2 aparece exactamente una vez en el archivo
- [ ] `.catalog-grid` aparece exactamente una vez, sin `!important`
- [ ] Los 4 screenshots del Paso 0/4 son visualmente idénticos (antes vs. después,
      normal vs. hover)
- [ ] Los `print()` de estilos computados del Paso 0/4 son idénticos
- [ ] Ningún selector del Grupo 3 fue tocado (`grep -c` de cada uno en la lista del
      Grupo 3 devuelve el mismo conteo que antes de este plan)
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `index.html`
- [ ] `plans/README.md` actualizado

## STOP conditions

Detente y reporta si:

- Cualquier comparación del Paso 4 muestra una diferencia visual o de estilo
  computado respecto al Paso 0.
- Al revisar el código actual, algún selector que este plan clasificó como "muerto"
  (Grupo 1) en realidad aparece en `app.js` o en el HTML estático de `index.html` —
  vuelve a correr los `grep` de clasificación contra el código real antes de asumir
  que la tabla de este documento sigue siendo precisa.
- No estás seguro de qué valor "gana hoy" para alguna propiedad al fusionar el
  Grupo 2 — usa `getComputedStyle` en el navegador para confirmar empíricamente en
  vez de adivinar por lectura de cascada.

## Maintenance notes

- Este plan consolida pero no rediseña — el resultado visual debe ser exactamente el
  mismo que hoy. Un rediseño deliberado de las tarjetas del catálogo es un plan
  distinto, no este.
- Un revisor de PR debería poder aprobar este PR mirando sólo los 4 screenshots
  (antes/después, normal/hover) sin necesidad de leer el diff línea por línea para
  confirmar "sin cambio visual".
- Si en el futuro se vuelve a necesitar una variante visual distinta para
  `.dataset-card` (ej. un rediseño A/B), agregar una clase modificadora nueva
  (`.dataset-card--compact`) es preferible a repetir el patrón de dos bloques con el
  mismo selector que causó este problema.
