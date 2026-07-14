# Plan 045: Agregar color al badge `.dataset-badge.monthly`

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html`
> Si el archivo cambió desde que se escribió este plan, compara el extracto de
> "Estado actual" contra el código real antes de continuar; si no coincide,
> trátalo como un STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

Cada tarjeta del catálogo muestra un badge de estado basado en `dataset.source_mode`
(`app.js:907`). El backend emite tres valores posibles para este campo — confirmado
en `src/extractors/sinim_finanzas_live_extractor.py:365,371` (`source_mode = "monthly"`
/ `"fallback"`) y `src/chile_hub/pipeline_status_utils.py:309` (que agrupa
explícitamente `"live"` y `"monthly"` como fuentes sanas: `entry["source_mode"] in
{"live", "monthly"}`).

Pero el CSS sólo define color para dos de los tres:

```css
/* index.html:2352-2360 */
.dataset-badge.live {
    background: #ecfdf5;
    color: #065f46;
}
.dataset-badge.fallback {
    background: #fffbeb;
    color: #92400e;
}
/* no existe .dataset-badge.monthly */
```

Se verificó visualmente (captura de pantalla, dataset `finanzas_municipales`, que
tiene `source_mode: "monthly"`): el badge "MONTHLY" se renderiza sin fondo ni color
propio — hereda sólo las propiedades base de `.dataset-badge` (tipografía, padding,
`border: 1px solid transparent`), apareciendo como texto con borde invisible junto a
badges vecinos que sí tienen un pill de color sólido (verde para "LIVE", ámbar para
"FALLBACK"). Es inconsistente y, más importante: el propio backend considera
`monthly` una fuente **sana** (agrupada con `live`), pero visualmente el badge sin
estilo comunica lo contrario — parece un estado roto o sin definir, justo en la
sección que existe para transmitir confianza en la procedencia de los datos.

## Estado actual

`index.html:2342-2360`:
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

.dataset-badge.live {
    background: #ecfdf5;
    color: #065f46;
}

.dataset-badge.fallback {
    background: #fffbeb;
    color: #92400e;
}
```

(Nota: estos colores hex sueltos —`#ecfdf5`/`#065f46`/`#fffbeb`/`#92400e`— no usan las
variables `--accent-green-light` / `--accent-warm-bg` del sitio. Ese problema más
amplio de tokens se aborda en el Plan 049; **este plan sólo agrega la regla que falta
para `monthly`**, sin tocar `.live`/`.fallback` para mantener el cambio mínimo y no
pisar el trabajo del Plan 049.)

`app.js:907` — de dónde sale la clase y el texto del badge:
```js
<span class="dataset-badge ${escapeHtml(dataset.source_mode || "fallback")}">${escapeHtml(dataset.source_mode || "unknown")}</span>
```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 |

## Scope

**En alcance**:
- `index.html` — una regla CSS nueva: `.dataset-badge.monthly`.

**Fuera de alcance**:
- `.dataset-badge.live` / `.dataset-badge.fallback` — no cambies sus colores; ese
  trabajo de migrar a tokens es el Plan 049.
- `app.js` — no genera nada nuevo, sólo usa la clase que ya existe en los datos.
- Cualquier lógica de `source_mode` en `src/` (Python) — es un valor de contrato de
  datos, no se toca desde un plan de CSS.

## Pasos

### Paso 1: Agregar la regla `.dataset-badge.monthly`

En `index.html`, inmediatamente después de `.dataset-badge.fallback`
(`index.html:2357-2360`), agrega una tercera variante. Usa un tono distinto a verde
(live) y ámbar (fallback) para que las tres sean visualmente distinguibles a simple
vista — por ejemplo azul/índigo, coherente con el uso que ya hace el sitio de
`.pill.partial { background: #e0e7ff; color: #3730a3; }` (`index.html:2561`) para un
estado "intermedio" (ni completamente ok ni completamente en warning):

```css
.dataset-badge.monthly {
    background: #e0e7ff;
    color: #3730a3;
}
```

**Verify**: `grep -n "dataset-badge.monthly" index.html` → debe mostrar la regla nueva.

### Paso 2: Verificación visual con Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    badge = page.locator(".dataset-badge.monthly").first
    if badge.count() == 0:
        print("No se encontró ningún badge .monthly en los datos actuales — revisa "
              "si finanzas_municipales sigue teniendo source_mode=monthly en "
              "data/normalized/hub_bundle.json antes de continuar")
    else:
        style = badge.evaluate("el => getComputedStyle(el).backgroundColor")
        print("background computado:", style)
    browser.close()
```

**Verify**: si existe al menos una tarjeta con `source_mode: "monthly"` en los datos
locales (`data/normalized/hub_bundle.json`, actualmente `finanzas_municipales`), el
`background` computado ya no debe ser `rgba(0, 0, 0, 0)` / transparente.

### Paso 3: Smoke test del repo

**Verify**: `make verify-landing` → exit 0.

## Test plan

No hay tests automatizados de CSS en este repo. La verificación es el Paso 2 más el
smoke test del Paso 3.

## Done criteria

- [ ] `grep -n "dataset-badge.monthly" index.html` muestra la regla nueva
- [ ] El script del Paso 2 confirma un `background` no transparente para
      `.dataset-badge.monthly` (si existe un dataset con ese `source_mode` en los
      datos locales)
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `index.html`
- [ ] `plans/README.md` actualizado

## STOP conditions

Detente y reporta si:

- `data/normalized/hub_bundle.json` ya no contiene ningún dataset con
  `source_mode: "monthly"` (verifica con
  `grep -o '"source_mode": *"monthly"' data/normalized/hub_bundle.json`) — en ese caso
  el fix sigue siendo correcto (cubre el enum completo que el backend puede emitir),
  pero no podrás verificarlo visualmente contra datos reales; nota esto en el reporte.
- Las líneas citadas en "Estado actual" ya no coinciden con `index.html`.

## Maintenance notes

- Si en el futuro se agrega un cuarto valor de `source_mode` (ver
  `src/extractors/source_adapter.py` y los extractores que lo emiten), este mismo
  patrón (`.dataset-badge.<nuevo_valor>`) debe repetirse — considera agregar un
  comentario en el CSS listando los tres valores conocidos hoy (`live`, `fallback`,
  `monthly`) para que el próximo cambio no vuelva a olvidar uno.
