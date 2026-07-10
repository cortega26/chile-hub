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
    const db = await getDb();
    const base = new URL(".", window.location.href).href;

    // DuckDB-Wasm no soporta read_parquet con URLs HTTP directas: cada archivo
    // debe registrarse explícitamente con registerFileURL y luego referenciarse
    // por su nombre registrado.
    const parquetRegex = /read_parquet\s*\(\s*'([^']+)'\s*\)/g;
    let modifiedSql = sql;
    let match;
    while ((match = parquetRegex.exec(sql)) !== null) {
      const path = match[1];
      if (path.startsWith("data/") || path.startsWith("./")) {
        const basename = path.split("/").pop();
        const url = path.startsWith("data/")
          ? base + path
          : base + path.replace(/^\.\//, "");
        await db.registerFileURL(basename, url, duckdb.DuckDBDataProtocol.HTTP, false);
        modifiedSql = modifiedSql.replace(path, basename);
      }
    }

    const conn = await db.connect();
    const arrowTable = await conn.query(modifiedSql);
    const rows = arrowTable.toArray().map((row) => row.toJSON());
    renderResult(rows, resultEl);
    statusEl.textContent = `${arrowTable.numRows} filas`;
    statusEl.className = "";
    await conn.close();
  } catch (err) {
    console.error("SQL Explorer:", err);
    statusEl.textContent = `Error: ${err.message}`;
    statusEl.className = "sql-error";
  }
}

function init() {
  const runBtn = document.getElementById("sql-run-btn");
  if (!runBtn) return; // la sección puede no existir en otras páginas
  const sqlInput = document.getElementById("sql-input");
  const statusEl = document.getElementById("sql-status");
  const resultEl = document.getElementById("sql-result");
  runBtn.addEventListener("click", () =>
    runQuery(sqlInput.value, statusEl, resultEl)
  );
}

document.addEventListener("DOMContentLoaded", init);
