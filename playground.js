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
      // Pre-fetch WASM in the main thread to avoid CDN compression issues
      // that corrupt the binary in the worker's fetch context.
      const wasmUrl = new URL(
        "./vendor/duckdb/duckdb-mvp.wasm",
        import.meta.url
      ).href;
      const wasmResponse = await fetch(wasmUrl);
      const wasmBuffer = await wasmResponse.arrayBuffer();
      const wasmBlob = new Blob([wasmBuffer], { type: "application/wasm" });
      const wasmObjectUrl = URL.createObjectURL(wasmBlob);

      const worker = new Worker("./vendor/duckdb/duckdb-browser-mvp.worker.js");
      const logger = new duckdb.ConsoleLogger();
      const db = new duckdb.AsyncDuckDB(logger, worker);
      // Pass the object URL instead of the raw path — the worker fetches
      // it from the blob: URL, bypassing Cloudflare's compression.
      await db.instantiate(wasmObjectUrl, null);
      URL.revokeObjectURL(wasmObjectUrl);
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

    // DuckDB-Wasm no soporta read_parquet con URLs HTTP. Cada archivo debe
    // registrarse como buffer: fetch() desde el hilo principal (el navegador
    // maneja decompresión) y registerFileBuffer (evita que CDN sirva bytes
    // comprimidos que DuckDB no puede interpretar).
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
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(
            `No se pudo descargar ${basename} (HTTP ${response.status})`
          );
        }
        const buffer = await response.arrayBuffer();
        await db.registerFileBuffer(basename, new Uint8Array(buffer));
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
