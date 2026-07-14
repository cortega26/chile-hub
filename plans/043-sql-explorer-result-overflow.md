# Plan 043: El Explorador SQL envuelve sus resultados en un contenedor con scroll horizontal

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando
> de verificación y confirma el resultado esperado antes de avanzar. Si algo
> en "STOP conditions" ocurre, detente y reporta — no improvises. Al terminar,
> actualiza la fila de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**: `git diff --stat 901f5b9..HEAD -- index.html playground.js`
> Si alguno de estos archivos cambió desde que se escribió este plan, compara
> los extractos de "Estado actual" contra el código real antes de continuar;
> si no coinciden, trátalo como un STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `901f5b9`, 2026-07-13

## Por qué importa

`playground.js` renderiza los resultados de cualquier consulta SQL del "Explorador SQL"
(`#sql-result`) como una tabla `<table>` sin ninguna clase CSS y sin contenedor con
scroll. Se verificó empíricamente con Playwright contra el sitio servido localmente:

- La tabla resultante mide `1805px` de ancho (`table.scrollWidth`).
- Su contenedor `#sql-result` mide `1056px` de ancho (`clientWidth`) y tiene
  `overflow-x: visible` (verificado con `getComputedStyle`).
- `body` tiene `overflow-x: hidden` (`index.html` línea 345).

El resultado neto: cualquier consulta que devuelva más de ~6-7 columnas (algo trivial
con `SELECT *` sobre casi cualquier dataset del hub, ver ejemplo por defecto en el
propio `<textarea>`) deja columnas completamente inaccesibles — no aparece scrollbar
en ningún lado porque `body` recorta el overflow. El usuario no puede ver ni desplazarse
para alcanzar esos datos.

Este patrón (contenedor con `overflow-x: auto` alrededor de una tabla ancha) **ya existe
tres veces en este mismo archivo** y funciona correctamente en cada caso:
- `.table-wrapper` (índice `index.html:1670-1674`) para la tabla de comunas.
- `.health-table-wrap` (`index.html:2515-2519`) para el dashboard de salud.
- `.dataset-preview-table-wrap` (`index.html:1121-1126`) para la vista previa en el drawer.

El Explorador SQL es la feature más nueva del sitio (Plan 020, completado 2026-07-10);
que su output se vea roto en el primer uso real socava justo la confianza que el resto
del sitio construye con cuidado.

## Estado actual

- `playground.js:38-58` — función `renderResult(rows, container)`: construye el HTML de
  la tabla a mano, sin clases:
  ```js
  function renderResult(rows, container) {
      if (!rows || rows.length === 0) {
          container.innerHTML = "<p>La consulta no devolvió filas.</p>";
          return;
      }
      const columns = Object.keys(rows[0]);
      let html = "<table><thead><tr>";
      for (const col of columns) {
          html += `<th>${escapeHtml(col)}</th>`;
      }
      html += "</tr></thead><tbody>";
      for (const row of rows) {
          html += "<tr>";
          for (const col of columns) {
              html += `<td>${escapeHtml(row[col])}</td>`;
          }
          html += "</tr>";
      }
      html += "</tbody></table>";
      container.innerHTML = html;
  }
  ```
- `index.html:2811` — el contenedor destino: `<div id="sql-result"></div>`, sin clase,
  sin regla CSS propia en absoluto (confirmado: `grep -n "sql-result" index.html` no
  devuelve ninguna regla en el `<style>`).
- Patrón de referencia ya usado en el mismo archivo — `.dataset-preview-table-wrap`
  (`index.html:1121-1134`):
  ```css
  .dataset-preview-table-wrap {
      overflow-x: auto;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      max-width: 100%;
  }
  .dataset-preview-table {
      width: max-content;
      min-width: 100%;
      border-collapse: collapse;
      font-size: 0.74rem;
      text-align: left;
  }
  .dataset-preview-table th {
      font-family: var(--font-mono);
      background-color: var(--bg-color);
      color: var(--text-primary);
      padding: 0.4rem 0.6rem;
      border-bottom: 1px solid var(--border-color);
      font-weight: 600;
  }
  .dataset-preview-table td {
      padding: 0.4rem 0.6rem;
      border-bottom: 1px solid rgba(0,0,0,0.03);
      color: var(--text-secondary);
      white-space: nowrap;
  }
  ```

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Servir el sitio localmente | `python3 -m http.server 8877` (desde la raíz del repo) | sirve en `http://localhost:8877/` |
| Smoke test de la landing | `make verify-landing` | exit 0 |
| Verificación visual (ver Paso 3) | script Playwright ad hoc (ver abajo) | tabla con scroll horizontal contenido, sin recorte |

No hay `lint`/`format` de Python aplicable — este plan solo toca `index.html` y
`playground.js` (HTML/CSS/JS estáticos, fuera del alcance de `ruff`).

## Scope

**En alcance**:
- `index.html` — agregar una regla CSS nueva (wrapper + tabla) para `#sql-result`.
- `playground.js` — envolver el `<table>` generado en un `<div>` con la clase wrapper
  nueva, y agregar clases a `<table>`/`<th>`/`<td>` para que hereden el estilo.

**Fuera de alcance (no tocar)**:
- La lógica de `runQuery`, `getDb`, el manejo de WASM/Blob URL (`playground.js:1-30`) —
  nada de esto se relaciona con el bug de layout.
- El bloque `<!-- START_DATA_CATALOG_JSON_LD --> ... <!-- END_DATA_CATALOG_JSON_LD -->`
  (`index.html:42-289`) y la línea `<script src="app.js?v=...">` — estos los regenera
  `src/builders/landing.py` en cada build; no los edites a mano.
- `app.js` — no participa en el Explorador SQL.

## Pasos

### Paso 1: Agregar las reglas CSS para el resultado del Explorador SQL

En `index.html`, dentro del bloque `<style>`, cerca de la sección "Comunas Table Data
Grid" (`index.html:1662` `/* Comunas Table Data Grid */`) o inmediatamente después de
la sección `#explorador` que ya tiene sus propios estilos, agrega:

```css
/* SQL Explorer result table */
.sql-result-wrap {
    overflow-x: auto;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    max-width: 100%;
    margin-top: 0.75rem;
}

.sql-result-table {
    width: max-content;
    min-width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    text-align: left;
}

.sql-result-table th {
    font-family: var(--font-mono);
    background-color: var(--bg-color);
    color: var(--text-primary);
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border-color);
    font-weight: 600;
    white-space: nowrap;
}

.sql-result-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid rgba(0,0,0,0.03);
    color: var(--text-secondary);
    white-space: nowrap;
}

.sql-result-empty {
    color: var(--text-secondary);
    font-size: 0.88rem;
    margin-top: 0.5rem;
}
```

Sigue el patrón de nombres del resto del archivo (`dataset-preview-table*`,
`health-table*`): prefijo del componente + `-wrap` para el contenedor con scroll,
`-table` para el elemento tabla.

**Verify**: `grep -n "sql-result-wrap\|sql-result-table" index.html` → debe mostrar las
reglas nuevas.

### Paso 2: Envolver la tabla generada en `playground.js` con las clases nuevas

Modifica `renderResult` en `playground.js:38-58` para que el HTML generado use las
clases del Paso 1:

```js
function renderResult(rows, container) {
  if (!rows || rows.length === 0) {
    container.innerHTML = '<p class="sql-result-empty">La consulta no devolvió filas.</p>';
    return;
  }
  const columns = Object.keys(rows[0]);
  let html = '<div class="sql-result-wrap"><table class="sql-result-table"><thead><tr>';
  for (const col of columns) {
    html += `<th>${escapeHtml(col)}</th>`;
  }
  html += "</tr></thead><tbody>";
  for (const row of rows) {
    html += "<tr>";
    for (const col of columns) {
      html += `<td>${escapeHtml(row[col])}</td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table></div>";
  container.innerHTML = html;
}
```

Cambios: el `<p>` de "sin filas" usa `class="sql-result-empty"`; el `<table>` se envuelve
en `<div class="sql-result-wrap">...</div>` y gana `class="sql-result-table"`.

**Verify**: `grep -n "sql-result-wrap\|sql-result-table\|sql-result-empty" playground.js`
→ debe mostrar las 3 clases nuevas en uso.

### Paso 3: Verificación visual con Playwright

Sirve el sitio localmente y confirma que el bug está resuelto:

```bash
python3 -m http.server 8877 &
```

Luego ejecuta un script Playwright equivalente a:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8877/index.html")
    page.wait_for_load_state("networkidle")
    page.locator("#sql-run-btn").click()
    page.wait_for_timeout(6000)  # primera carga del motor WASM puede tardar
    info = page.evaluate("""() => {
        const wrap = document.querySelector('.sql-result-wrap');
        const table = wrap ? wrap.querySelector('table') : null;
        return {
            hasWrap: !!wrap,
            wrapOverflowX: wrap ? getComputedStyle(wrap).overflowX : null,
            tableScrollWidth: table ? table.scrollWidth : null,
            wrapClientWidth: wrap ? wrap.clientWidth : null,
        };
    }""")
    print(info)
    browser.close()
```

**Verify**: la salida debe mostrar `hasWrap: True`, `wrapOverflowX: 'auto'`, y
`tableScrollWidth` puede seguir siendo mayor que `wrapClientWidth` (la tabla real sigue
siendo ancha) — la diferencia es que ahora el *contenedor* tiene scroll propio en vez de
que `body` recorte el contenido. Confirma manualmente arrastrando/haciendo scroll
horizontal dentro de `#sql-result` en un navegador real, o con
`wrap.scrollLeft = 100; wrap.scrollLeft` vía `page.evaluate` para comprobar que el
scroll responde (valor > 0 después de asignarlo).

Detén el servidor local (`kill %1` o el PID del `http.server`) al terminar.

### Paso 4: Smoke test del repo

**Verify**: `make verify-landing` → exit 0. Este smoke test no ejercita el Explorador
SQL (evita descargar el WASM en CI — ver comentario en
`scripts/verify_landing.py` cerca de la línea 578, "Explorador SQL: verificar
presencia (no ejecutar...)"), pero sí verifica que `index.html` sigue siendo válido y
que ningún otro elemento se rompió.

## Test plan

No hay suite de tests automatizados de frontend en este repo más allá del smoke test
de Playwright (`scripts/verify_landing.py`, que deliberadamente no ejecuta el
Explorador SQL). La verificación de este plan es manual/visual (Paso 3) — no crees un
test nuevo en `tests/` para esto, sería un test end-to-end de UI real que este repo no
tiene infraestructura para correr en CI sin descargar WASM.

## Done criteria

Todos deben cumplirse:

- [ ] `grep -n "sql-result-wrap\|sql-result-table" index.html` muestra las reglas CSS nuevas
- [ ] `grep -n "sql-result-wrap\|sql-result-table\|sql-result-empty" playground.js` muestra las 3 clases en uso
- [ ] El script de verificación del Paso 3 confirma `hasWrap: True` y `wrapOverflowX: 'auto'`
- [ ] `make verify-landing` sale con exit 0
- [ ] `git status` no muestra archivos modificados fuera de `index.html` y `playground.js`
- [ ] `plans/README.md` actualizado con el estado de este plan

## STOP conditions

Detente y reporta si:

- El código actual de `renderResult` en `playground.js` ya no coincide con el extracto
  de "Estado actual" (alguien lo cambió desde que se escribió este plan).
- `#sql-result` ya tiene una clase o regla CSS que no se detectó aquí (revisa de nuevo
  con `grep -n "sql-result" index.html` antes de asumir que no existe).
- `make verify-landing` falla por una razón no relacionada con este cambio — no lo
  arregles a ciegas, reporta el error completo.

## Maintenance notes

- Si en el futuro se agrega paginación o virtualización a los resultados del
  Explorador SQL, este wrapper debe seguir envolviendo el contenedor scrolleable — no
  lo elimines.
- Un revisor de PR debería confirmar visualmente (screenshot) que una consulta con
  muchas columnas (ej. `SELECT * FROM read_parquet('data/normalized/perfil_territorial_comunal.parquet') LIMIT 5;`,
  que tiene decenas de columnas) muestra scroll horizontal dentro de la tabla y no
  recorta datos.
