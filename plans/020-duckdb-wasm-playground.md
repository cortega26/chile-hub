# Plan 020: Explorador SQL en la landing con DuckDB-Wasm (consultas en el navegador)

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar, actualiza la fila de estado de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat 140c8ea..HEAD -- index.html app.js scripts/verify_landing.py`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `140c8ea`, 2026-06-29

## Why this matters

La landing (`index.html`) hoy muestra los datos pero no deja **explorarlos**: el
visitante debe descargar Parquet o copiar un snippet. Con DuckDB-Wasm se puede
ejecutar SQL real contra los Parquet publicados **dentro del navegador**, sin
instalar nada y sin backend. Los archivos ya se sirven al mismo origen
(`https://tooltician.com/chile-hub/data/normalized/*.parquet`, confirmado por
`PUBLIC_DATA_BASE` en `app.js:46`), así que no hay problema de CORS. Esto convierte
la página de un escaparate estático en una herramienta exploratoria — el mayor salto
de "utilidad" del proyecto, y coherente con el lema "consume en una línea".

## Current state

Archivos relevantes:

- `index.html` — landing estática. Tiene CSP estricta en un `<meta http-equiv>`
  (línea 5) y la sección "Uso rápido" (`id="uso"`, líneas 2584–2623) que ya muestra
  un snippet de SQL DuckDB estático. El explorador va justo después de esa sección.
- `app.js` — script clásico (`<script src="app.js" defer>`, `index.html:2758`).
  `PUBLIC_DATA_BASE = "https://tooltician.com/chile-hub/data/normalized"` (línea 46).
- `data/normalized/dataset_catalog.json` — fuente para poblar un selector de dataset:
  cada `datasets[].outputs.parquet` da la ruta del Parquet.
- `scripts/verify_landing.py` — **smoke test con Playwright**. Punto crítico (líneas
  176–187): captura errores de consola y **falla el build si hay cualquiera**, tras
  `page.goto(url, wait_until="networkidle")`.

CSP actual (`index.html:5`, exacta):

```
default-src 'self'; base-uri 'self'; form-action 'self' https://formspree.io; object-src 'none'; script-src 'self' https://analytics.ahrefs.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://analytics.ahrefs.com https://formspree.io; manifest-src 'self'; media-src 'self'; worker-src 'self' blob:; upgrade-insecure-requests
```

Sección "Uso rápido" donde se inyecta el explorador (`index.html:2584` y `:2623`):

```html
        <section class="quickstart-section" id="uso">
            ...
            </div>
        </section>
        <!-- ⬅ el explorador SQL va aquí, como nueva <section> -->
        <section class="participate-section" id="participar">
```

**Dos restricciones de diseño no negociables** (derivan de `verify_landing.py`):

1. **Inicialización diferida (lazy)**: DuckDB-Wasm NO debe cargarse al renderizar la
   página. Debe instanciarse **solo al primer clic** en "Ejecutar". Razón: el bundle
   WASM pesa varios MB; cargarlo en `load` rompería `wait_until="networkidle"` y
   ralentizaría la página.
2. **Cero errores de consola en carga**: cualquier `console.error` o `pageerror`
   durante el render hace fallar `verify_landing.py`. El módulo del explorador debe
   manejar todos los errores con try/catch y mostrarlos en la UI, nunca dejarlos
   propagar a la consola en el flujo de carga.

Convención del repo: HTML/JS en español neutral; CSP estricta y "self-first" (es un
valor del proyecto, ver Plan 002). Por eso este plan **auto-hospeda** (vendoriza)
DuckDB-Wasm en vez de cargarlo desde un CDN: mantiene la CSP sin nuevos orígenes
externos y da control de cadena de suministro (archivos pineados y revisables).

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Servir landing local | `.venv/bin/python -m http.server 8000` (en la raíz del repo) | sirve en :8000 |
| Smoke test landing | `make verify-landing` | exit 0, "landing OK" |
| Listar archivos vendor | `ls vendor/duckdb/` | los 5 archivos del Step 1 |

Para `make verify-landing` se necesita Chromium de Playwright: si falla por navegador
ausente, ejecuta `make install-browsers` primero.

## Scope

**In scope** (únicos archivos a crear/modificar):
- `vendor/duckdb/` — **crear**: archivos pineados de DuckDB-Wasm (auto-hospedados).
- `playground.js` — **crear**: módulo ES que implementa el explorador (lazy init).
- `index.html` — añadir la `<section>` del explorador + el `<script type="module">`
  + ajustar la CSP (`'wasm-unsafe-eval'`).
- `scripts/verify_landing.py` — añadir verificación de que los elementos del
  explorador existen (sin ejecutar la consulta, para no descargar WASM en CI).

**Out of scope** (NO tocar):
- `app.js` — el explorador es un módulo separado; no se mezcla con el script clásico.
- La carga de datos existente (catálogo, tabla de comunas, drawers) — no se modifica.
- Ejecutar DuckDB dentro del smoke test de CI — solo se verifica la presencia de la
  UI; la ejecución real se valida manualmente (ver Test plan).
- Añadir orígenes de CDN a la CSP — este plan auto-hospeda; el CDN es un follow-up
  documentado en Maintenance notes.

## Git workflow

- Branch: `advisor/020-duckdb-wasm-playground`
- Commits estilo conventional commits: ej.
  `feat(landing): explorador SQL en el navegador con DuckDB-Wasm`.
- Los `.wasm` son binarios; commitéalos (vendor pineado). Nota en el mensaje de
  commit la versión exacta de DuckDB-Wasm vendorizada.
- No hagas push ni abras PR salvo indicación del operador.

## Steps

### Step 1: Vendorizar DuckDB-Wasm (auto-hospedar, pineado)

Fija una versión estable de `@duckdb/duckdb-wasm` (al escribir este plan, usa
`1.29.0`; si esa versión ya no existe, elige la última estable e indícalo en el
commit). Descarga los archivos del bundle desde jsDelivr a `vendor/duckdb/`.

Primero confirma los nombres exactos de archivo del `dist/` en la versión elegida
abriendo `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist/` (listado del
paquete). Los archivos necesarios para el bundle MVP/EH (sin SharedArrayBuffer) son:

```
duckdb-browser.mjs            (loader ESM)
duckdb-mvp.wasm
duckdb-browser-mvp.worker.js
duckdb-eh.wasm
duckdb-browser-eh.worker.js
```

Descárgalos (ajusta versión/nombres según el listado real):

```bash
mkdir -p vendor/duckdb
BASE="https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/dist"
for f in duckdb-browser.mjs duckdb-mvp.wasm duckdb-browser-mvp.worker.js duckdb-eh.wasm duckdb-browser-eh.worker.js; do
  curl -fsSL "$BASE/$f" -o "vendor/duckdb/$f"
done
```

**Verify**: `ls -la vendor/duckdb/` → los 5 archivos presentes y los `.wasm` con
tamaño > 1 MB. Si algún `curl` devuelve 404, el nombre/versión no coincide → STOP y
reporta el listado real.

### Step 2: Ajustar la CSP para WebAssembly

En `index.html:5`, añade `'wasm-unsafe-eval'` a la directiva `script-src` (es lo que
permite compilar WebAssembly bajo CSP). Cambia exactamente:

```
script-src 'self' https://analytics.ahrefs.com;
```

por:

```
script-src 'self' 'wasm-unsafe-eval' https://analytics.ahrefs.com;
```

No toques las demás directivas: `worker-src 'self' blob:` ya permite el worker
auto-hospedado, y `connect-src 'self' ...` ya permite leer los Parquet del mismo
origen.

**Verify**: `grep -c "wasm-unsafe-eval" index.html` → `1`.

### Step 3: Crear el módulo del explorador `playground.js`

Crea `playground.js` como módulo ES con **inicialización diferida**. Estructura:

```js
// Explorador SQL con DuckDB-Wasm. Inicialización diferida: el bundle WASM se carga
// solo al primer clic en "Ejecutar", para no romper el smoke test (networkidle /
// cero errores de consola en carga).
import * as duckdb from "./vendor/duckdb/duckdb-browser.mjs";

const MANUAL_BUNDLES = {
  mvp: {
    mainModule: "./vendor/duckdb/duckdb-mvp.wasm",
    mainWorker: "./vendor/duckdb/duckdb-browser-mvp.worker.js",
  },
  eh: {
    mainModule: "./vendor/duckdb/duckdb-eh.wasm",
    mainWorker: "./vendor/duckdb/duckdb-browser-eh.worker.js",
  },
};

let dbPromise = null; // se crea en el primer "Ejecutar"

async function getConnection() {
  if (!dbPromise) {
    dbPromise = (async () => {
      const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
      const worker = new Worker(bundle.mainWorker);
      const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
      await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
      return db;
    })();
  }
  const db = await dbPromise;
  return db.connect();
}

function renderResult(rows, container) {
  // Construye una <table> simple con los resultados. Escapa el texto.
}

async function runQuery(sql, statusEl, resultEl) {
  statusEl.textContent = "Cargando motor SQL…";
  try {
    const conn = await getConnection();
    const result = await conn.query(sql);
    renderResult(result.toArray().map((r) => r.toJSON()), resultEl);
    statusEl.textContent = `${result.numRows} filas`;
    await conn.close();
  } catch (err) {
    // NUNCA dejar que el error llegue a la consola en el flujo normal:
    statusEl.textContent = `Error: ${err.message}`;
  }
}

function init() {
  const runBtn = document.getElementById("sql-run-btn");
  if (!runBtn) return; // la sección puede no existir en otras páginas
  const sqlInput = document.getElementById("sql-input");
  const statusEl = document.getElementById("sql-status");
  const resultEl = document.getElementById("sql-result");
  runBtn.addEventListener("click", () => runQuery(sqlInput.value, statusEl, resultEl));
}

document.addEventListener("DOMContentLoaded", init);
```

Notas para el executor:
- `db.instantiate(...)` — el segundo argumento varía entre versiones de DuckDB-Wasm.
  Para el bundle MVP/EH suele ser `bundle.pthreadWorker` (puede ser `undefined`, lo
  cual es válido). Si la API de la versión vendorizada difiere, consulta el README de
  `@duckdb/duckdb-wasm` de esa versión y adapta — NO inventes la firma.
- La consulta por defecto sugerida para el textarea (ver Step 4) usa la URL same-origin
  del Parquet, p. ej.:
  `SELECT * FROM read_parquet('data/normalized/comunas.parquet') LIMIT 10;`
- `init()` debe ser barato y no lanzar errores aunque falte la sección.

**Verify**: `node --check playground.js` si hay Node disponible; si no,
`.venv/bin/python -c "import esprima" 2>/dev/null || echo "skip JS lint"` (no es
crítico). La verificación real es funcional en el Step 5.

### Step 4: Inyectar la sección del explorador en `index.html`

Después de `</section>` de la sección "Uso rápido" (`index.html:2623`) y antes de
`<section class="participate-section" id="participar">` (`:2625`), inserta una nueva
sección. Reutiliza las clases existentes del proyecto (`section-shell`,
`catalog-header`, `catalog-title`, `quickstart-code`) para mantener el estilo:

```html
        <section class="section-shell" id="explorador">
            <div class="catalog-header">
                <div>
                    <h2 class="catalog-title">Explorador SQL</h2>
                    <div class="catalog-meta">Ejecuta SQL contra los Parquet publicados, en tu navegador. El motor se carga al primer clic.</div>
                </div>
            </div>
            <label for="sql-input" class="visually-hidden">Consulta SQL</label>
            <textarea id="sql-input" class="quickstart-code" rows="4" spellcheck="false">SELECT * FROM read_parquet('data/normalized/comunas.parquet') LIMIT 10;</textarea>
            <div class="quickstart-head">
                <button id="sql-run-btn" class="btn btn-primary">Ejecutar</button>
                <span id="sql-status" aria-live="polite"></span>
            </div>
            <div id="sql-result"></div>
        </section>
```

Al final del `<body>`, después de `<script src="app.js" defer></script>`
(`index.html:2758`), añade el módulo:

```html
    <script type="module" src="playground.js"></script>
```

(`visually-hidden` debe existir en el CSS; si no existe esa clase, usa una etiqueta
visible o `aria-label` en el textarea — verifica con `grep -n "visually-hidden" index.html`.)

**Verify**: `grep -nE "id=\"explorador\"|sql-run-btn|playground.js" index.html` →
3 coincidencias.

### Step 5: Verificación funcional manual + smoke de presencia

**Funcional (manual, una vez)**: levanta `.venv/bin/python -m http.server 8000`,
abre `http://localhost:8000/`, ve a la sección "Explorador SQL", haz clic en
"Ejecutar". Debe cargar el motor (estado "Cargando motor SQL…") y luego mostrar 10
filas de comunas. Abre la consola del navegador: NO debe haber errores tras la carga
inicial de la página (los errores de la consulta, si los hay, aparecen en `#sql-status`,
no en consola).

**Smoke de presencia (CI)**: en `scripts/verify_landing.py`, tras los chequeos de
a11y existentes, añade una verificación de que los elementos del explorador existen
(sin hacer clic, para no descargar WASM en CI):

```python
        # Explorador SQL: verificar presencia (no ejecutar — evita descargar WASM en CI)
        if page.locator("#sql-run-btn").count() != 1:
            fail("Falta el botón del explorador SQL (#sql-run-btn)")
        if page.locator("#sql-input").count() != 1:
            fail("Falta el textarea del explorador SQL (#sql-input)")
```

**Verify**: `make verify-landing` → exit 0 (sin errores de consola, elementos
presentes). Si falla por errores de consola, revisa que `playground.js` NO instancie
DuckDB en `init()` (debe ser solo en el clic).

## Test plan

- No hay tests unitarios de JS en el repo; la verificación es el smoke test de
  Playwright (`make verify-landing`), ampliado en el Step 5 para chequear presencia.
- Caso manual obligatorio: ejecutar la consulta por defecto y una consulta con un
  nombre con acento (`SELECT * FROM read_parquet('data/normalized/comunas.parquet')
  WHERE nombre_comuna_clean LIKE '%nunoa%';`) y confirmar resultados.
- Caso de error manual: ejecutar SQL inválido y confirmar que el error aparece en
  `#sql-status` y NO en la consola del navegador.

## Done criteria

Todas deben cumplirse:

- [ ] `vendor/duckdb/` contiene los 5 archivos pineados; los `.wasm` > 1 MB.
- [ ] `index.html` tiene `'wasm-unsafe-eval'` en `script-src` (y solo eso cambió en CSP).
- [ ] `playground.js` existe, es `type="module"`, e instancia DuckDB **solo** en el clic.
- [ ] `index.html` tiene la sección `#explorador` con `#sql-input`, `#sql-run-btn`,
      `#sql-status`, `#sql-result`, y carga `playground.js`.
- [ ] `make verify-landing` exit 0 (cero errores de consola; elementos presentes).
- [ ] Manual: la consulta por defecto devuelve 10 filas en el navegador.
- [ ] `app.js` SIN cambios (`git status`).
- [ ] Fila de `plans/README.md` actualizada.

## STOP conditions

Detente y reporta (no improvises) si:

- Algún `curl` del Step 1 da 404 (versión/nombres de archivo distintos a los del plan).
- `make verify-landing` falla por errores de consola que no se resuelven asegurando
  la inicialización diferida (posible incompatibilidad de CSP o de la API de la
  versión vendorizada).
- La API `db.instantiate(...)` / `selectBundle(...)` de la versión vendorizada difiere
  de la del Step 3 y no encuentras la firma correcta en el README de esa versión.
- Cargar el explorador requeriría añadir orígenes de CDN a la CSP (eso es el
  follow-up deferido, no este plan).
- `wait_until="networkidle"` nunca se resuelve tras tu cambio (señal de que algo se
  carga en `load` que no debería).

## Maintenance notes

- **Tamaño del repo**: vendorizar añade varios MB de `.wasm` al repositorio. Es el
  tradeoff aceptado a cambio de una CSP sin orígenes externos y control de cadena de
  suministro. Si el peso molesta, el **follow-up CDN** es: cargar DuckDB-Wasm desde
  `https://cdn.jsdelivr.net` y añadir ese origen a `script-src`, `connect-src` y
  `worker-src` de la CSP, idealmente con SRI. Documentar el cambio de superficie de
  seguridad antes de hacerlo.
- **Actualizar DuckDB-Wasm**: re-descargar los archivos del Step 1 con la nueva
  versión y re-verificar la firma de `instantiate` en `playground.js`.
- **Datasets en el selector**: hoy la consulta por defecto apunta a `comunas.parquet`.
  Como follow-up, poblar un `<select>` desde `dataset_catalog.json` con todos los
  `outputs.parquet` disponibles.
- En revisión de PR: confirmar inicialización diferida (grep que DuckDB no se instancia
  en `init`/`DOMContentLoaded`), que la CSP solo añadió `'wasm-unsafe-eval'`, y que
  `verify-landing` pasa.
