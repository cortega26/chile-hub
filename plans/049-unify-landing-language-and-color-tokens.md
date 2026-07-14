# Plan 049: Unificar idioma (español) y reemplazar colores hex sueltos por tokens en las tarjetas del catálogo

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html app.js`.
> Además, confirma que el Plan 045 (`plans/045-dataset-badge-monthly-color.md`) ya
> está `DONE` en `plans/README.md` antes de empezar — este plan depende de él (ver
> "Depends on"). Si los archivos cambiaron desde que se escribió este plan, compara
> los extractos de "Estado actual" contra el código real antes de continuar.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW-MED — el riesgo principal es tocar por error una cadena de texto que
  `scripts/verify_landing.py` verifica textualmente (ver "Fuera de alcance", es
  crítico leerlo antes de tocar `app.js`).
- **Depends on**: `plans/045-dataset-badge-monthly-color.md` (este plan toca la misma
  región CSS de `.dataset-badge.*`; ejecutar 045 primero evita que ambos planes editen
  la misma línea en paralelo y generen conflictos de merge)
- **Category**: tech-debt (content i18n + design tokens)
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

El sitio es 100% en español (`<html lang="es">`, y absolutamente todo el copy visible
—títulos, botones, descripciones— está en español). Sin embargo, las tarjetas del
catálogo de datos (la sección más visitada del sitio) mezclan español e inglés sin
ningún patrón consistente:

- Etiquetas de la mini-grilla de datos: "FUENTE", "REGISTROS", "TAMAÑO" están en
  español, pero **"FRESHNESS"** (`app.js:920`) quedó en inglés.
- Los badges de estado muestran literalmente el valor crudo de `source_mode`:
  **"LIVE"**, **"FALLBACK"**, **"MONTHLY"** (`app.js:907`) — inglés, sin traducir.
- El indicador de advertencias en cada tarjeta dice **"N warnings"** (`app.js:897`) —
  inglés, en un botón que convive con "Ver Ficha" y "Parquet" en español.

Además, en la misma zona hay colores hex sueltos que no usan el sistema de variables
`--accent-warm-*` / `--accent-green-*` ya definido en `:root` (`index.html:298-326`):
- `app.js:566` — `background: #fffbeb; border: 1px solid #fef3c7; color: #92400e;`
  para el bloque "Acción recomendada" del drawer.
- `app.js:1079` — `style="color: #f87171;"` en el mensaje de error de la tabla de
  comunas.

Estos hex (`#fffbeb`/`#fef3c7`/`#92400e`, una paleta ámbar estilo Tailwind) casi
coinciden en *intención* (advertencia/alerta) con los tokens que el sitio ya declara
para ese mismo propósito (`--accent-warm-bg: #fbf3ed`, `--accent-warm-border:
#f0decb`, `--accent-warm: #a6522c`), pero usan valores distintos — es una segunda
paleta de "advertencia" viviendo junto a la oficial, probablemente porque se copiaron
de un ejemplo genérico de Tailwind al escribir esa feature en vez de reutilizar los
tokens del sitio.

## Alcance deliberadamente acotado — lee esto antes de tocar nada

`scripts/verify_landing.py` (el smoke test que corre en CI vía `make verify-landing`)
verifica **textualmente** algunas cadenas específicas del drawer de detalle:

```python
# scripts/verify_landing.py:494-497
if (
    "Procedencia técnica:" not in provenance_meta
    or top_issue_source_detail not in provenance_meta
    or f"Warnings: {top_issue_warning_count}" not in provenance_meta
):
```
y
```python
# scripts/verify_landing.py:572-573
if not any(f"Warnings: {top_issue_warning_count}" in line for line in top_issue_meta):
```

Esa cadena `"Warnings: {n}"` viene de `app.js:563`
(`` `... · Warnings: <strong>${escapeHtml(String(dataset.warning_count ?? 0))}</strong>` ``),
**dentro del panel "Ficha Técnica" del drawer** — es una línea *distinta* de la que
este plan sí toca (el tag "N warnings" de la tarjeta del catálogo, `app.js:897`,
usa un texto y una clase diferentes y no aparece en `verify_landing.py`).

**Por eso este plan excluye explícitamente `app.js:563` (el "Warnings: N" del drawer)
de su alcance.** Traducirla requeriría también actualizar
`scripts/verify_landing.py` en el mismo cambio, lo cual es razonable pero es una
decisión aparte con su propio riesgo — se deja fuera para mantener este plan de
riesgo bajo-medio en vez de medio-alto. Si se quiere unificar también esa línea, debe
ser un plan de seguimiento explícito que toque ambos archivos a la vez.

Por la misma razón, el vocabulario del panel "Estado operativo" / dashboard de salud
(`ok`/`warn`/`error`, `live`/`fallback`/`stale`/`drifted` en `.pill.*`,
`.health-badge.*`) queda **fuera de alcance** — es terminología operacional/técnica de
un panel de estado (un patrón común en dashboards de este tipo, distinto del copy
orientado al usuario final que sí se corrige aquí), y tocarlo tiene su propia
superficie de riesgo con `verify_landing.py` (que sí verifica varios de esos pills
textualmente, ver `scripts/verify_landing.py:373-387`).

## Estado actual

`app.js:889-932` (extracto relevante, `renderCatalog`):
```js
const warningBadge = dataset.warning_count > 0
    ? `<span class="dataset-tag warning">${dataset.warning_count} warnings</span>`
    : "";

return `
    <article class="dataset-card" id="dataset-${escapeHtml(dataset.dataset)}" ...>
        <div class="dataset-card-top">
            <div>
                <h4 class="dataset-name">${escapeHtml(dataset.dataset)}</h4>
                <div class="dataset-desc">${escapeHtml(dataset.description || "")}</div>
            </div>
            <span class="dataset-badge ${escapeHtml(dataset.source_mode || "fallback")}">${escapeHtml(dataset.source_mode || "unknown")}</span>
        </div>

        <div class="dataset-facts-grid">
            <div class="dataset-fact-mini">
                <span class="dataset-fact-mini-label">Fuente</span>
                <span class="dataset-fact-mini-value" title="...">${escapeHtml(dataset.source_name || "N/D")}</span>
            </div>
            <div class="dataset-fact-mini">
                <span class="dataset-fact-mini-label">Registros</span>
                <span class="dataset-fact-mini-value">${escapeHtml(recordCount)}</span>
            </div>
            <div class="dataset-fact-mini">
                <span class="dataset-fact-mini-label">Freshness</span>
                <span class="dataset-fact-mini-value">${escapeHtml(formatFreshness(runtimeFreshness))}</span>
            </div>
            <div class="dataset-fact-mini">
                <span class="dataset-fact-mini-label">Tamaño</span>
                <span class="dataset-fact-mini-value">${escapeHtml(sizeBytes)}</span>
            </div>
        </div>

        <div style="margin-top: 0.75rem; display: flex; gap: 0.35rem; flex-wrap: wrap;">
            ${(dataset.join_keys || []).map(key => `<span class="dataset-tag key-tag">key: ${escapeHtml(key)}</span>`).join("")}
            ${warningBadge}
        </div>
        ...
`;
```

`app.js:560-570` (bloque "Acción recomendada" del drawer, con el hex suelto):
```js
${dataset.warning_count > 0 && (dataset.degradation?.recommended_action || dataset.drift?.recommended_action)
    ? `<div class="dataset-meta-line" style="background: #fffbeb; border: 1px solid #fef3c7; padding: 0.75rem; border-radius: 6px; color: #92400e; margin-top: 0.5rem;">
         <strong>Acción recomendada:</strong> ${escapeHtml(dataset.degradation?.recommended_action || dataset.drift?.recommended_action)}
       </div>`
    : ""}
```

`app.js:1079` (mensaje de error de la tabla de comunas):
```js
<td colspan="6" class="no-results" style="color: #f87171;">
```
(revisa el contexto de esta línea con `grep -n -B3 -A3 "color: #f87171" app.js` antes
de editarla — confirma que sigue siendo un mensaje de error de carga y no cambió de
propósito).

Tokens ya disponibles en `index.html:298-326` (`:root`), a reutilizar:
```css
--accent-warm: #a6522c;
--accent-warm-hover: #8c4220;
--accent-warm-bg: #fbf3ed;
--accent-warm-border: #f0decb;
```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 (crítico en este plan — corre después de cada paso) |

## Scope

**En alcance**:
- `app.js:897` — traducir "N warnings" → "N advertencias".
- `app.js:907` — mapear el texto visible de `source_mode` a español, **sin** cambiar
  el valor usado como clase CSS (`escapeHtml(dataset.source_mode || "fallback")` debe
  seguir intacto para que el CSS de los Planes 045/048 siga funcionando).
- `app.js:920` — traducir la etiqueta "Freshness" → "Frescura" (sólo la etiqueta
  estática; el *valor* que muestra al lado, `formatFreshness(...)`, queda igual — ver
  "Fuera de alcance").
- `app.js:566` y `app.js:1079` (y cualquier otro hex de advertencia/error idéntico que
  encuentres con `grep -n "#fffbeb\|#fef3c7\|#92400e\|#f87171" app.js`) — reemplazar
  por los tokens `--accent-warm-*` ya existentes.

**Fuera de alcance (no tocar)**:
- `app.js:563` (`"Warnings: N"` del drawer) — verificado textualmente por
  `scripts/verify_landing.py:496,573`. Ver sección de arriba.
- El valor devuelto por `formatFreshness()` (`app.js:118-125`, cadenas como "fresh",
  "stale", "unknown") — es vocabulario de un contrato de datos (`freshness.status`)
  compartido con el dashboard de salud y el pipeline Python; traducirlo de forma
  consistente en todos los consumidores es un esfuerzo mayor y fuera de alcance aquí.
- El dashboard "Estado operativo" completo (`.health-badge`, `.pill.*`, y todo el
  vocabulario `ok/warn/error/live/fallback/stale/drifted` ahí) — ver justificación
  arriba.
- El color decorativo del corazón en el manifiesto (`index.html`, sección
  `.manifesto`, `style="color: #f87171;"` junto a "Hecho con ♥ en Chile") — es un
  acento puramente decorativo, no un color de estado/advertencia; no forma parte del
  problema de tokens que este plan corrige.
- `.dataset-badge.live` / `.dataset-badge.fallback` / `.dataset-badge.monthly` — sus
  colores de fondo ya deberían estar resueltos por el Plan 045 antes de que empieces
  este; no los vuelvas a tocar aquí salvo que quieras además migrarlos de hex sueltos
  a tokens (opcional, ver Paso 3 nota).

## Pasos

### Paso 1: Traducir las etiquetas y el texto de advertencias

En `app.js`:

1. Línea 897, cambia:
   ```js
   ? `<span class="dataset-tag warning">${dataset.warning_count} warnings</span>`
   ```
   por:
   ```js
   ? `<span class="dataset-tag warning">${dataset.warning_count} advertencias</span>`
   ```

2. Línea 920, cambia:
   ```js
   <span class="dataset-fact-mini-label">Freshness</span>
   ```
   por:
   ```js
   <span class="dataset-fact-mini-label">Frescura</span>
   ```

**Verify**: `grep -n "warnings</span>\|>Freshness<" app.js` → no debe devolver
coincidencias (ambas ya están traducidas). `grep -n "Warnings: <strong>" app.js` →
debe seguir devolviendo la línea 563 intacta (confirma que NO tocaste la línea fuera
de alcance).

### Paso 2: Mapear el texto del badge de `source_mode` a español, sin tocar la clase

En `app.js:907`, cambia:
```js
<span class="dataset-badge ${escapeHtml(dataset.source_mode || "fallback")}">${escapeHtml(dataset.source_mode || "unknown")}</span>
```
por (agregando una función de mapeo y usándola sólo para el texto visible):
```js
<span class="dataset-badge ${escapeHtml(dataset.source_mode || "fallback")}">${escapeHtml(SOURCE_MODE_LABELS[dataset.source_mode] || dataset.source_mode || "desconocido")}</span>
```

Y agrega, cerca de las otras constantes/funciones de formato de `app.js` (junto a
`formatFreshness`, `formatBytes`, etc. — busca con
`grep -n "^function format" app.js` para ubicar esa zona):
```js
const SOURCE_MODE_LABELS = {
    live: "en vivo",
    fallback: "respaldo",
    monthly: "mensual",
};
```

Nota: el `text-transform: uppercase` que ya aplica `.dataset-badge` en CSS
(`index.html:2342-2350`) se encarga de mostrar estos textos en mayúsculas — no hace
falta escribirlos en mayúsculas aquí.

**Verify**: `grep -n "SOURCE_MODE_LABELS" app.js` → debe mostrar tanto la definición
como el uso (2 coincidencias). La clase CSS (`dataset.source_mode || "fallback"`, el
primer argumento dentro de `class="dataset-badge ..."`) debe seguir usando el valor
crudo en inglés (`live`/`fallback`/`monthly`) — confirma que no cambiaste esa parte.

### Paso 3: Reemplazar los hex sueltos de advertencia por tokens

En `app.js:566`, cambia:
```js
? `<div class="dataset-meta-line" style="background: #fffbeb; border: 1px solid #fef3c7; padding: 0.75rem; border-radius: 6px; color: #92400e; margin-top: 0.5rem;">
```
por:
```js
? `<div class="dataset-meta-line" style="background: var(--accent-warm-bg); border: 1px solid var(--accent-warm-border); padding: 0.75rem; border-radius: 6px; color: var(--accent-warm); margin-top: 0.5rem;">
```

En `app.js:1079` (confirma el contexto primero con
`grep -n -B3 -A3 "color: #f87171" app.js`), cambia:
```js
<td colspan="6" class="no-results" style="color: #f87171;">
```
por:
```js
<td colspan="6" class="no-results" style="color: var(--accent-warm);">
```

Busca cualquier otra ocurrencia de estos mismos hex que hayas podido pasar por alto:
`grep -n "#fffbeb\|#fef3c7\|#92400e\|#f87171\|#ef4444" app.js` — si aparece alguna más
en un contexto de advertencia/error (no decorativo), aplica el mismo reemplazo; si
aparece en un contexto distinto, no la toques y anótalo en tu reporte final.

**Verify**: `grep -n "#fffbeb\|#fef3c7\|#92400e" app.js` → no debe devolver
coincidencias. `grep -n "#f87171" app.js` → no debe devolver coincidencias (la única
que quedaría, la del corazón decorativo, vive en `index.html`, no en `app.js` — no la
toques, está fuera de alcance).

### Paso 4: Verificación visual con Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    first_card = page.locator(".dataset-card").first
    print("card text:", first_card.inner_text())
    first_card.screenshot(path="card_after_i18n.png")
    browser.close()
```

**Verify**: el texto de la tarjeta ya no debe contener "FRESHNESS", "LIVE",
"FALLBACK", "MONTHLY", ni "warnings" en inglés — debe mostrar "FRESCURA", "EN VIVO" /
"RESPALDO" / "MENSUAL", y "N advertencias" según corresponda al dataset.

### Paso 5: Smoke test del repo (crítico en este plan)

**Verify**: `make verify-landing` → exit 0. Si falla mencionando "Warnings:" o algo
del panel de estado operativo, revisa inmediatamente si tocaste por error alguna de
las líneas marcadas como "fuera de alcance" — es la forma más probable de que este
plan rompa CI.

## Test plan

No hay tests automatizados de contenido/texto en `tests/` para el frontend. La
verificación es el Paso 4 (visual) más el Paso 5 (smoke test, que sí incluye
aserciones textuales sobre partes de `app.js` no tocadas por este plan — es la mejor
red de seguridad disponible).

## Done criteria

- [ ] `grep -n "warnings</span>\|>Freshness<" app.js` no devuelve coincidencias
- [ ] `grep -n "Warnings: <strong>" app.js` sigue devolviendo la línea original
      (intacta, fuera de alcance)
- [ ] `grep -n "SOURCE_MODE_LABELS" app.js` muestra definición + uso
- [ ] La clase CSS del badge sigue usando el valor crudo de `source_mode`
      (`live`/`fallback`/`monthly`), sólo el texto visible cambió
- [ ] `grep -n "#fffbeb\|#fef3c7\|#92400e" app.js` no devuelve coincidencias
- [ ] El script del Paso 4 confirma que el texto de la tarjeta está en español
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `app.js`
- [ ] `plans/README.md` actualizado

## STOP conditions

Detente y reporta si:

- `make verify-landing` falla después de este cambio — antes de intentar arreglarlo,
  confirma si tocaste por error `app.js:563` o el vocabulario del dashboard de salud
  (ambos fuera de alcance); si es así, revierte esa línea específica y vuelve a
  correr el smoke test.
- Encuentras que `dataset.source_mode` puede traer un valor no listado en
  `SOURCE_MODE_LABELS` (además de `live`/`fallback`/`monthly`) — el fallback
  `|| dataset.source_mode || "desconocido"` ya cubre ese caso mostrando el valor
  crudo, pero repórtalo para que se considere agregarlo al mapa.
- Los extractos de "Estado actual" ya no coinciden con `app.js`.

## Maintenance notes

- Si se agrega un cuarto `source_mode` en el backend en el futuro, debe agregarse
  tanto a `SOURCE_MODE_LABELS` (este plan) como a la regla CSS `.dataset-badge.<valor>`
  (patrón establecido en el Plan 045) — considera dejar un comentario cruzado entre
  ambos lugares.
- La traducción de `app.js:563` ("Warnings: N" del drawer) y del vocabulario del
  dashboard de salud quedaron explícitamente diferidas — si se quiere completar la
  unificación de idioma en el futuro, ese es un plan de seguimiento que debe tocar
  `scripts/verify_landing.py` en el mismo cambio.
