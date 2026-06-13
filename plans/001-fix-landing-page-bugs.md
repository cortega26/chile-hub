# Plan 001: Corregir bugs visibles en la landing page — KPIs históricos y crash de coordenadas

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**: `git diff --stat ba2f434..HEAD -- app.js`
> If `app.js` changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `ba2f434`, 2026-06-13

## Why this matters

Dos bugs en `app.js` degradan la experiencia del usuario en la landing page
pública. El primero (BUG-01) hace que los KPI cards de UF, Dólar, Euro y UTM
muestren el valor más antiguo de la serie en vez del más reciente — un error
visible que transmite datos desactualizados. El segundo (BUG-02) provoca que
una coordenada `null` o `undefined` en el JSON de comunas crashee toda la
tabla territorial con un `TypeError`, dejando la sección inutilizable sin
mensaje de error. Ambos son de bajo esfuerzo y alto impacto.

## Current state

- `app.js:695-715` — `loadKPIs()`: fetch a `indicadores_hoy.json`, busca
  valores con `Array.prototype.find()`, que retorna el **primer** elemento
  que cumple el predicado. Como el JSON está ordenado por fecha ascendente,
  `find()` devuelve el valor más antiguo para cada indicador.

```javascript
// app.js:695-716 (loadKPIs)
function loadKPIs() {
    fetch("data/normalized/indicadores_hoy.json")
        .then(res => {
            if (!res.ok) throw new Error("No se pudo cargar los indicadores");
            return res.json();
        })
        .then(data => {
            const findValue = (code) => data.find(i => i.codigo_indicador === code);
            
            updateKPICard("kpi-uf", findValue("uf"));
            updateKPICard("kpi-dolar", findValue("dolar"), true);
            updateKPICard("kpi-euro", findValue("euro"), true);
            updateKPICard("kpi-utm", findValue("utm"));
        })
```

- `app.js:811-822` — `renderTable()`: llama a `.toFixed(4)` sobre
  `latitud_cabecera` y `longitud_cabecera` sin verificar que no sean `null` o
  `undefined`. Un solo registro con coordenadas nulas lanza `TypeError` y
  rompe todo el render de la tabla.

```javascript
// app.js:811-822 (dentro de renderTable)
    paginatedRows.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><span class="comuna-code">${escapeHtml(c.codigo_comuna)}</span></td>
            <td style="font-weight: 500; color: var(--text-primary);">${escapeHtml(c.nombre_comuna)}</td>
            <td>${escapeHtml(c.nombre_provincia)}</td>
            <td>${escapeHtml(c.nombre_region)}</td>
            <td>${formatNum.format(c.poblacion_estimada)}</td>
            <td style="font-size: 0.85rem; font-family: monospace;">${c.latitud_cabecera.toFixed(4)}, ${c.longitud_cabecera.toFixed(4)}</td>
        `;
        tableBody.appendChild(tr);
    });
```

- Convención del proyecto: `escapeHtml()` en `app.js:42-49` se usa para
  sanitizar todo valor dinámico insertado en `innerHTML`. Mantener ese
  patrón.
- `app.js` no usa frameworks; es vanilla JavaScript con funciones puras
  y manipulación directa del DOM.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Verify landing page smoke tests | `make verify-landing` | exit 0 |
| Lint check | `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `app.js`

**Out of scope** (do NOT touch):
- `index.html` — solo CSS y estructura; no se modifica en este plan.
- `scripts/verify_landing.py` — el smoke test ya verifica elementos del DOM;
  puede necesitar ajustes si cambian los textos esperados, pero solo si los
  tests fallan.
- Cualquier cambio en el backend o en el formato de `indicadores_hoy.json`.

## Steps

### Step 1: Corregir KPI cards para que muestren el valor más reciente

En `loadKPIs()` (línea ~702), reemplazar la función `findValue` que usa
`.find()` (primer match) por una que busque el registro con la fecha más
reciente para cada código de indicador.

La estrategia más simple y robusta: ordenar `data` por fecha descendente
antes de buscar, para que `.find()` retorne el más reciente. Esto no requiere
cambiar la estructura del resto de la función.

```javascript
// Versión corregida dentro de .then(data => {...}):
// Ordenar por fecha descendente para que find() retorne el más reciente
data.sort((a, b) => (b.fecha || "").localeCompare(a.fecha || ""));
const findValue = (code) => data.find(i => i.codigo_indicador === code);
```

**Verify**: `make verify-landing` → exit 0, y los tests de KPI deben seguir
pasando (verifican estructura del DOM, no valores específicos).

### Step 2: Agregar null-safety a la renderización de coordenadas

En `renderTable()` (línea ~819), reemplazar la interpolación directa de
`.toFixed(4)` por una expresión segura que maneje `null` y `undefined`.

```javascript
// Reemplazar la línea:
// <td style="font-size: 0.85rem; font-family: monospace;">${c.latitud_cabecera.toFixed(4)}, ${c.longitud_cabecera.toFixed(4)}</td>
// Por:
const lat = c.latitud_cabecera != null ? c.latitud_cabecera.toFixed(4) : "N/D";
const lon = c.longitud_cabecera != null ? c.longitud_cabecera.toFixed(4) : "N/D";
// y usar ${lat}, ${lon} en el template literal
```

O, más conciso, usar optional chaining con fallback:

```javascript
<td style="font-size: 0.85rem; font-family: monospace;">${c.latitud_cabecera?.toFixed(4) ?? "N/D"}, ${c.longitud_cabecera?.toFixed(4) ?? "N/D"}</td>
```

**Verify**: `make verify-landing` → exit 0. El smoke test ya verifica que la
tabla de comunas tenga filas con coordenadas; si los datos actuales tienen
coordenadas válidas, el test sigue pasando sin cambios.

## Test plan

- Los tests existentes en `scripts/verify_landing.py` cubren la presencia de
  KPI cards, tabla de comunas, y coordenadas. Ejecutar `make verify-landing`
  después de cada paso.
- No se agregan nuevos tests unitarios porque `app.js` no tiene framework de
  tests; la verificación es vía smoke test con Playwright.
- Si se desea verificar manualmente: abrir `index.html` en un servidor local
  (`python -m http.server 8000` desde la raíz del repo), verificar que los
  KPIs de UF/Dólar/Euro/UTM muestran valores con fecha reciente, y que la
  tabla de comunas renderiza todas las filas sin errores en consola.

## Done criteria

- [ ] `make verify-landing` sale con exit 0
- [ ] Los KPI cards muestran el valor de la fecha más reciente del dataset
      (verificable inspeccionando `data/normalized/indicadores_hoy.json` y
      comparando el último registro de cada código contra lo que muestra la
      landing page)
- [ ] La tabla de comunas renderiza correctamente; cero errores en consola
      del navegador relacionados con `.toFixed(4)`
- [ ] `make lint` sale con exit 0 (ruff no aplica a archivos .js; este paso
      verifica que no se rompió nada en Python accidentalmente)
- [ ] Ningún archivo fuera de `app.js` fue modificado (`git diff --stat`)

## STOP conditions

Stop and report back (do not improvise) if:

- `app.js` no coincide con los excerpts de "Current state" (el código ha
  cambiado desde que este plan fue escrito).
- `make verify-landing` falla después de aplicar los cambios y el error no
  es trivial de diagnosticar.
- Los KPI cards dejan de mostrarse completamente después del cambio en Step 1
  (indica que el sort introdujo un problema).
- La tabla de comunas deja de renderizar filas después del cambio en Step 2.

## Maintenance notes

- Si se agregan más indicadores al dataset (nuevos códigos además de UF,
  Dólar, Euro, UTM, IPC), los KPI cards necesitarán nuevas tarjetas en
  `index.html` y nuevas llamadas en `loadKPIs()`.
- Si el orden de `indicadores_hoy.json` cambia en el backend (e.g., se ordena
  descendente), el sort agregado en Step 1 es redundante pero inofensivo.
- `escapeHtml()` debe seguir aplicándose a cualquier valor dinámico nuevo que
  se inserte en el DOM.
