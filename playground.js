// Explorador SQL con DuckDB-Wasm. Inicialización diferida: el bundle WASM se carga
// solo al primer clic en "Ejecutar", para no romper el smoke test.
import * as duckdb from "./vendor/duckdb/duckdb-browser.mjs";

const WASM_PATH = "./duckdb-mvp.wasm";
const WORKER_PATH = "./vendor/duckdb/duckdb-browser-mvp.worker.js";

// Consultas de ejemplo: las recetas más pedidas, listas para ejecutar.
const EXAMPLES = {
  comunas: `SELECT codigo_comuna, nombre_comuna, nombre_region, poblacion_estimada
FROM read_parquet('data/normalized/comunas.parquet')
ORDER BY poblacion_estimada DESC
LIMIT 10;`,
  censo: `SELECT nombre_comuna, poblacion_censada, hombres, mujeres
FROM read_parquet('data/normalized/censo_comunal.parquet')
ORDER BY poblacion_censada DESC
LIMIT 10;`,
  pobreza: `SELECT nombre_comuna, tasa, limite_inferior, limite_superior
FROM read_parquet('data/normalized/pobreza_comunal.parquet')
WHERE dimension = 'ingresos' AND anio = 2022
ORDER BY tasa DESC
LIMIT 10;`,
  permisos: `SELECT anio, SUM(unidades_total) AS unidades
FROM read_parquet('data/normalized/permisos_edificacion.parquet')
GROUP BY anio
ORDER BY anio;`,
  salud: `SELECT c.nombre_comuna,
       COUNT(DISTINCT s.codigo_establecimiento) AS salud,
       COUNT(DISTINCT e.rbd) AS educacion
FROM read_parquet('data/normalized/comunas.parquet') c
LEFT JOIN read_parquet('data/normalized/establecimientos_salud.parquet') s
  ON c.codigo_comuna = s.codigo_comuna
LEFT JOIN read_parquet('data/normalized/establecimientos_educacionales.parquet') e
  ON c.codigo_comuna = e.codigo_comuna
GROUP BY c.nombre_comuna
ORDER BY salud DESC
LIMIT 10;`,
  indicadores: `SELECT fecha, codigo_indicador, valor
FROM read_parquet('data/normalized/indicadores.parquet')
WHERE codigo_indicador = 'uf'
ORDER BY fecha DESC
LIMIT 10;`,
};

let dbPromise = null;
let lastResult = null; // { columns, rows } de la última consulta exitosa

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

async function runQuery(sql, statusEl, resultEl) {
  statusEl.textContent = "Cargando motor SQL…";
  statusEl.className = "";
  resultEl.innerHTML = "";
  const startedAt = performance.now();
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
    const elapsed = Math.round(performance.now() - startedAt);
    statusEl.textContent = `${arrowTable.numRows} filas · ${elapsed} ms`;
    statusEl.className = "";
    lastResult = rows.length
      ? { columns: Object.keys(rows[0]), rows }
      : { columns: [], rows: [] };
    toggleExportButton();
    await conn.close();
  } catch (err) {
    console.error("SQL Explorer:", err);
    statusEl.textContent = `Error: ${err.message}`;
    statusEl.className = "sql-error";
  }
}

function toggleExportButton() {
  const exportBtn = document.getElementById("sql-export");
  if (!exportBtn) return;
  exportBtn.disabled = !(lastResult && lastResult.rows.length > 0);
}

function exportCsv() {
  if (!lastResult || lastResult.rows.length === 0) return;
  const escapeCell = (value) => {
    const text = value === null || value === undefined ? "" : String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  const lines = [
    lastResult.columns.map(escapeCell).join(","),
    ...lastResult.rows.map((row) =>
      lastResult.columns.map((column) => escapeCell(row[column])).join(",")
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "consulta_chile_hub.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function init() {
  const runBtn = document.getElementById("sql-run-btn");
  if (!runBtn) return;
  const sqlInput = document.getElementById("sql-input");
  const statusEl = document.getElementById("sql-status");
  const resultEl = document.getElementById("sql-result");
  const exampleSelect = document.getElementById("sql-example");
  const exportBtn = document.getElementById("sql-export");

  const run = () => runQuery(sqlInput.value, statusEl, resultEl);

  runBtn.addEventListener("click", run);
  sqlInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      run();
    }
  });
  if (exampleSelect) {
    exampleSelect.addEventListener("change", () => {
      const example = EXAMPLES[exampleSelect.value];
      if (example) sqlInput.value = example;
    });
  }
  if (exportBtn) {
    exportBtn.addEventListener("click", exportCsv);
  }
}

document.addEventListener("DOMContentLoaded", init);
