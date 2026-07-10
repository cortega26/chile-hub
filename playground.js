// Explorador SQL con DuckDB-Wasm. Inicialización diferida: el bundle WASM se carga
// solo al primer clic en "Ejecutar", para no romper el smoke test (networkidle /
// cero errores de consola en carga).
import * as duckdb from "./vendor/duckdb/duckdb-browser.mjs";

// mainWorker: page-relative (new Worker() resuelve contra la página).
// mainModule: worker-relative (el worker hace fetch() contra su propia ubicación).
const MANUAL_BUNDLES = {
  mvp: {
    mainModule: "./duckdb-mvp.wasm",
    mainWorker: "./vendor/duckdb/duckdb-browser-mvp.worker.js",
  },
  eh: {
    mainModule: "./duckdb-eh.wasm",
    mainWorker: "./vendor/duckdb/duckdb-browser-eh.worker.js",
  },
};

let dbPromise = null; // se crea en el primer "Ejecutar"

async function getDb() {
  if (!dbPromise) {
    dbPromise = (async () => {
      const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
      const worker = new Worker(bundle.mainWorker);
      const logger = new duckdb.ConsoleLogger();
      const db = new duckdb.AsyncDuckDB(logger, worker);
      await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
      return db;
    })();
  }
  return dbPromise;
}

async function getConnection() {
  const db = await getDb();
  return db.connect();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(String(text)));
  return div.innerHTML;
}

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

async function runQuery(sql, statusEl, resultEl) {
  statusEl.textContent = "Cargando motor SQL…";
  resultEl.innerHTML = "";
  try {
    const conn = await getConnection();
    const arrowTable = await conn.query(sql);
    const rows = arrowTable.toArray().map((row) => row.toJSON());
    renderResult(rows, resultEl);
    statusEl.textContent = `${arrowTable.numRows} filas`;
    statusEl.className = "";
    await conn.close();
  } catch (err) {
    // NUNCA dejar que el error llegue a la consola en el flujo normal:
    statusEl.textContent = `Error: ${err.message}`;
    statusEl.className = "sql-error";
  }
}

function init() {
  const runBtn = document.getElementById("sql-run-btn");
  if (!runBtn) return; // la sección puede no existir en otras páginas
  const sqlInput = document.getElementById("sql-input");

  // Reemplaza la ruta relativa del Parquet por una URL absoluta same-origin
  // (DuckDB-Wasm con httpfs requiere URL completa; los datos se sirven del mismo origen).
  const base = window.location.origin + window.location.pathname.replace(/\/?$/, "/");
  const defaultPath = "data/normalized/comunas.parquet";
  if (sqlInput && sqlInput.value.includes(defaultPath)) {
    sqlInput.value = sqlInput.value.replace(defaultPath, base + defaultPath);
  }
  const statusEl = document.getElementById("sql-status");
  const resultEl = document.getElementById("sql-result");
  runBtn.addEventListener("click", () =>
    runQuery(sqlInput.value, statusEl, resultEl)
  );
}

document.addEventListener("DOMContentLoaded", init);
