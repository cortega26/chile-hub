// Explorador SQL con DuckDB-Wasm. Inicialización diferida: el bundle WASM se carga
// solo al primer clic en "Ejecutar", para no romper el smoke test.
import * as duckdb from "./vendor/duckdb/duckdb-browser.mjs";

const WASM_PATH = "./duckdb-mvp.wasm";
const WORKER_PATH = "./vendor/duckdb/duckdb-browser-mvp.worker.js";

let dbPromise = null;

async function getDb() {
  if (!dbPromise) {
    dbPromise = (async () => {
      // Pre-fetch WASM in the main thread: the worker's internal fetch goes
      // through Cloudflare's CDN compression which corrupts the binary for
      // WebAssembly.instantiate(). Fetching here (browser decompresses) and
      // passing as Blob URL bypasses this.
      const wasmResp = await fetch("./vendor/duckdb/duckdb-mvp.wasm");
      const buf = await wasmResp.arrayBuffer();
      const blob = new Blob([buf], { type: "application/wasm" });
      const blobUrl = URL.createObjectURL(blob);

      const worker = new Worker(WORKER_PATH);
      const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
      await db.instantiate(blobUrl, null);
      URL.revokeObjectURL(blobUrl);
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
  if (!runBtn) return;
  const sqlInput = document.getElementById("sql-input");
  const statusEl = document.getElementById("sql-status");
  const resultEl = document.getElementById("sql-result");
  runBtn.addEventListener("click", () =>
    runQuery(sqlInput.value, statusEl, resultEl)
  );
}

document.addEventListener("DOMContentLoaded", init);
