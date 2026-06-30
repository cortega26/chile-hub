// Configuración y Estado de la aplicación
let comunas = [];
let filteredComunas = [];
let currentPage = 1;
const rowsPerPage = 10;

// Elementos del DOM
const tableBody = document.getElementById("table-body");
const searchInput = document.getElementById("search-input");
const regionFilter = document.getElementById("region-filter");
const exportBtn = document.getElementById("export-csv-btn");
const prevBtn = document.getElementById("prev-page-btn");
const nextBtn = document.getElementById("next-page-btn");
const pageInfo = document.getElementById("page-info");
const statusSubtitle = document.getElementById("status-subtitle");
const statusMeta = document.getElementById("status-meta");
const statusPills = document.getElementById("status-pills");
const statusActions = document.getElementById("status-actions");
const packageMeta = document.getElementById("package-meta");
const packageActions = document.getElementById("package-actions");
const packageVerifyCopy = document.getElementById("package-verify-copy");
const catalogGeneratedAt = document.getElementById("catalog-generated-at");
const catalogGrid = document.getElementById("catalog-grid");
const catalogSearchInput = document.getElementById("catalog-search-input");
const catalogCount = document.getElementById("catalog-count");
const supportActions = document.getElementById("support-actions");
const quickstartCopyButtons = document.querySelectorAll(".quickstart-copy");

// Drawer Elements
const drawer = document.getElementById("dataset-drawer");
const drawerBackdrop = document.getElementById("drawer-backdrop");
const drawerClose = document.getElementById("drawer-close");
const drawerTitle = document.getElementById("drawer-title");
const drawerDesc = document.getElementById("drawer-desc");
const drawerTabFicha = document.getElementById("drawer-tab-ficha");
const drawerTabPreview = document.getElementById("drawer-tab-preview");
const drawerTabReceta = document.getElementById("drawer-tab-receta");
const drawerPanelFicha = document.getElementById("drawer-panel-ficha");
const drawerPanelPreview = document.getElementById("drawer-panel-preview");
const drawerPanelReceta = document.getElementById("drawer-panel-receta");

let currentCatalogDatasets = [];
let currentActiveDatasetInDrawer = null;
let artifactManifestByPath = {};
let packageManifestByPath = {};
const PUBLIC_DATA_BASE = "https://tooltician.com/chile-hub/data/normalized";
const PREVIEW_ROW_LIMIT = 5;
const SUPPORT_LINKS = [
    {
        label: "GitHub Sponsors",
        href: "https://github.com/sponsors/cortega26",
        className: "btn btn-primary",
    },
    {
        label: "Buy Me a Coffee",
        href: "https://www.buymeacoffee.com/cortega26",
        className: "dataset-action muted",
    },
];

// Formateador de moneda en pesos chilenos (CLP)
const formatCLP = new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 2
});

// Formateador de número para población
const formatNum = new Intl.NumberFormat("es-CL");

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatTimestamp(isoValue) {
    if (!isoValue) return "N/D";
    const date = new Date(isoValue);
    if (Number.isNaN(date.getTime())) return isoValue;
    return new Intl.DateTimeFormat("es-CL", {
        dateStyle: "medium",
        timeStyle: "short"
    }).format(date);
}

function formatBytes(sizeBytes) {
    if (typeof sizeBytes !== "number" || Number.isNaN(sizeBytes)) return "";
    if (sizeBytes < 1024) return `${sizeBytes} B`;
    if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
    return `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatFreshness(freshness) {
    if (!freshness) return "N/D";
    const status = freshness.status || "unknown";
    if (typeof freshness.age_hours !== "number" || typeof freshness.max_age_hours !== "number") {
        return status;
    }
    return `${status} · ${freshness.age_hours}h / ${freshness.max_age_hours}h`;
}

function parseIsoDate(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function computeRuntimeFreshness(dataset) {
    const persisted = dataset?.freshness || {};
    const refreshedAt = parseIsoDate(dataset?.refreshed_at_utc);
    const maxAgeHours = persisted.max_age_hours;
    if (!refreshedAt || typeof maxAgeHours !== "number") {
        return {
            status: "unknown",
            age_hours: null,
            max_age_hours: maxAgeHours ?? null,
        };
    }
    const ageHours = Math.max((Date.now() - refreshedAt.getTime()) / 3600000, 0);
    return {
        status: ageHours <= maxAgeHours ? "fresh" : "stale",
        age_hours: Number(ageHours.toFixed(2)),
        max_age_hours: maxAgeHours,
    };
}

function statusRank(status) {
    return { ok: 0, warn: 1, error: 2 }[status] ?? 1;
}

function computeRuntimeOverallStatus(buildStatus, runtimeFreshnessByDataset) {
    const freshnessValues = Object.values(runtimeFreshnessByDataset);
    const hasUnknown = freshnessValues.some(freshness => freshness.status === "unknown");
    const hasStale = freshnessValues.some(freshness => freshness.status === "stale");
    const runtimeFreshnessStatus = hasUnknown || hasStale ? "warn" : "ok";
    return statusRank(runtimeFreshnessStatus) > statusRank(buildStatus)
        ? runtimeFreshnessStatus
        : buildStatus;
}

function computeAttentionPriority(dataset, runtimeFreshness) {
    const warningCount = dataset.warning_count ?? 0;
    const runtimeStatus = runtimeFreshness?.status || "unknown";
    if (warningCount > 0 || runtimeStatus === "stale" || runtimeStatus === "unknown") {
        return 0;
    }
    if (dataset.drift?.status === "drifted" || dataset.degradation?.status === "warning" || dataset.degradation?.status === "degraded") {
        return 1;
    }
    return 2;
}

function formatCoverage(coverage) {
    if (!coverage) return "N/D";
    const status = coverage.status || "unknown";
    if (typeof coverage.actual_record_count !== "number" || typeof coverage.expected_record_count !== "number") {
        return status;
    }
    return `${status} · ${coverage.actual_record_count}/${coverage.expected_record_count}`;
}

function formatReusePolicy(reusePolicy) {
    if (!reusePolicy) return "N/D";
    const status = reusePolicy.status || "unknown";
    const license = reusePolicy.license;
    return license ? `${status} · ${license}` : status;
}

function formatArtifactLabel(path, fallbackLabel) {
    const manifestEntry = artifactManifestByPath[path];
    if (!manifestEntry?.output_type) return fallbackLabel;
    return manifestEntry.output_type.toUpperCase();
}

function buildArtifactLink(path, fallbackLabel) {
    if (!path) return "";
    const manifestEntry = artifactManifestByPath[path];
    const sizeLabel = manifestEntry ? ` · ${formatBytes(manifestEntry.size_bytes)}` : "";
    const label = formatArtifactLabel(path, fallbackLabel);
    return `
        <a class="dataset-action" href="${escapeHtml(path)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(label)}${escapeHtml(sizeLabel)}
        </a>
    `;
}

function buildArtifactMeta(path) {
    const manifestEntry = artifactManifestByPath[path];
    if (!manifestEntry) return "";
    const shortHash = manifestEntry.sha256 ? manifestEntry.sha256.slice(0, 12) : "N/D";
    const type = manifestEntry.output_type || "N/D";
    return `<div class="dataset-artifact-meta">tipo: ${escapeHtml(type)} · sha256: ${escapeHtml(shortHash)}</div>`;
}

function buildSimpleLink(path, label) {
    if (!path) return "";
    return `
        <a class="dataset-action muted" href="${escapeHtml(path)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(label)}
        </a>
    `;
}

function renderSupportLinks() {
    if (!supportActions) return;
    supportActions.innerHTML = SUPPORT_LINKS.map(link => `
        <a class="${escapeHtml(link.className)}" href="${escapeHtml(link.href)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(link.label)}
        </a>
    `).join("");
}

function findReportPath(reports, sharedType, format, fallbackPath) {
    const reportEntries = Object.values(reports || {});
    const matched = reportEntries.find(entry => entry?.shared_type === sharedType && entry?.format === format);
    return matched?.path || fallbackPath;
}

function buildDatasetExample(dataset, preferredKind = "python") {
    const parquetName = dataset.outputs?.parquet?.split("/").pop();
    const jsonName = dataset.outputs?.json?.split("/").pop();
    const examples = {
        python: parquetName
            ? `import polars as pl\n\ndf = pl.read_parquet("${PUBLIC_DATA_BASE}/${parquetName}")\nprint(df.head())`
            : null,
        duckdb: parquetName
            ? `SELECT *\nFROM read_parquet('${PUBLIC_DATA_BASE}/${parquetName}')\nLIMIT 10;`
            : null,
        curl: jsonName
            ? `curl -L "${PUBLIC_DATA_BASE}/${jsonName}" -o ${jsonName}`
            : null,
    };
    const kinds = ["python", "duckdb", "curl"].filter(kind => examples[kind]);
    if (kinds.length === 0) return "";

    const activeKind = kinds.includes(preferredKind) ? preferredKind : kinds[0];
    const exampleId = `dataset-example-${escapeHtml(dataset.dataset)}`;
    const tabs = kinds.map(kind => `
        <button class="dataset-example-tab ${kind === activeKind ? "active" : ""}" data-kind="${escapeHtml(kind)}" role="tab" aria-selected="${kind === activeKind ? "true" : "false"}" tabindex="${kind === activeKind ? "0" : "-1"}">
            ${escapeHtml(kind)}
        </button>
    `).join("");

    return `
        <div class="dataset-example" data-dataset-example data-examples='${escapeHtml(JSON.stringify(examples))}'>
            <div class="dataset-example-head">
                <span class="dataset-example-title">Receta de uso</span>
                <div class="dataset-example-tabs" role="tablist" aria-label="Formatos de recetas de uso">
                    ${tabs}
                    <button class="dataset-example-copy" data-copy-target="${exampleId}">Copiar</button>
                </div>
            </div>
            <pre class="dataset-example-code" id="${exampleId}" role="tabpanel" tabindex="0">${escapeHtml(examples[activeKind])}</pre>
        </div>
    `;
}

function formatPreviewValue(value) {
    if (value === null || value === undefined) return "N/D";
    if (typeof value === "number") return formatNum.format(value);
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}

function buildPreviewTable(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
        return `<p class="dataset-preview-state">El archivo no contiene filas para mostrar.</p>`;
    }
    const columns = Object.keys(rows[0]).slice(0, 6);
    return `
        <div class="dataset-preview-table-wrap">
            <table class="dataset-preview-table">
                <thead><tr>${columns.map(column => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
                <tbody>${rows.slice(0, PREVIEW_ROW_LIMIT).map(row => `
                    <tr>${columns.map(column => `<td>${escapeHtml(formatPreviewValue(row[column]))}</td>`).join("")}</tr>
                `).join("")}</tbody>
            </table>
        </div>
        <p class="dataset-preview-note">Primeras ${Math.min(rows.length, PREVIEW_ROW_LIMIT)} filas · ${columns.length} columnas visibles</p>
    `;
}

async function loadDatasetPreview(button) {
    const target = document.getElementById(button.dataset.previewTarget);
    if (!target) return;
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    target.hidden = expanded;
    if (expanded || target.dataset.loaded === "true") return;

    target.innerHTML = `<p class="dataset-preview-state">Cargando muestra...</p>`;
    try {
        const response = await fetch(button.dataset.previewPath);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const rows = await response.json();
        target.innerHTML = buildPreviewTable(rows);
        target.dataset.loaded = "true";
    } catch (error) {
        console.error("No se pudo cargar la vista previa:", error);
        target.innerHTML = `<p class="dataset-preview-state error">No se pudo cargar la muestra. El archivo JSON sigue disponible para descarga.</p>`;
    }
}

function wireDatasetPreviewInteractions() {
    document.querySelectorAll("[data-preview-target]").forEach(button => {
        button.addEventListener("click", () => loadDatasetPreview(button));
    });
}

function buildMonedarioBridge(dataset) {
    if (dataset.dataset !== "indicadores") return "";

    return `
        <aside class="monedario-bridge" aria-label="Contexto financiero en Monedario">
            <p><strong>¿Qué significan estos indicadores para tu bolsillo?</strong> Chile Hub publica los datos; Monedario explica cómo la UF, el IPC y los reajustes aparecen en arriendos, créditos y otros gastos cotidianos.</p>
            <a href="https://monedario.cl/guias/uf-costo-de-vida/" target="_blank" rel="noopener noreferrer">Entender la UF y la inflación en Monedario <span aria-hidden="true">→</span></a>
        </aside>
    `;
}

function activateDatasetExample(container, nextKind) {
    const examples = JSON.parse(container.dataset.examples || "{}");
    if (!examples[nextKind]) return;

    container.querySelectorAll(".dataset-example-tab").forEach(tab => {
        const isActive = tab.dataset.kind === nextKind;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", isActive ? "true" : "false");
        tab.setAttribute("tabindex", isActive ? "0" : "-1");
    });

    const code = container.querySelector(".dataset-example-code");
    if (code) code.textContent = examples[nextKind];
}

function wireDatasetExampleInteractions() {
    document.querySelectorAll("[data-dataset-example]").forEach(container => {
        container.querySelectorAll(".dataset-example-tab").forEach(button => {
            button.addEventListener("click", () => {
                activateDatasetExample(container, button.dataset.kind);
            });
        });
        const copyButton = container.querySelector(".dataset-example-copy");
        if (copyButton) {
            copyButton.addEventListener("click", () => {
                copyTextFromTarget(copyButton, copyButton.dataset.copyTarget);
            });
        }
    });
}

function filterCatalog() {
    if (!catalogGrid || !catalogCount) return;
    const query = (catalogSearchInput?.value || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim();
    const cards = [...catalogGrid.querySelectorAll(".dataset-card")];
    let visibleCount = 0;
    cards.forEach(card => {
        const haystack = (card.dataset.search || card.textContent)
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
        const visible = !query || haystack.includes(query);
        card.hidden = !visible;
        if (visible) visibleCount += 1;
    });

    const categories = [...catalogGrid.querySelectorAll(".catalog-category")];
    categories.forEach(cat => {
        const hasVisibleCards = [...cat.querySelectorAll(".dataset-card")].some(card => !card.hidden);
        cat.hidden = !hasVisibleCards;
    });

    catalogCount.textContent = `${visibleCount} ${visibleCount === 1 ? "capa" : "capas"}`;
}

function fallbackCopyText(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    let copied = false;
    try {
        copied = document.execCommand("copy");
    } catch (error) {
        copied = false;
    }

    document.body.removeChild(textarea);
    return copied;
}

// Drawer panel switching
function setActiveDrawerTab(tabName) {
    const tabs = {
        ficha: { btn: drawerTabFicha, panel: drawerPanelFicha },
        preview: { btn: drawerTabPreview, panel: drawerPanelPreview },
        receta: { btn: drawerTabReceta, panel: drawerPanelReceta }
    };

    Object.entries(tabs).forEach(([name, els]) => {
        if (!els.btn || !els.panel) return;
        const isActive = name === tabName;
        els.btn.classList.toggle("active", isActive);
        els.btn.setAttribute("aria-selected", isActive ? "true" : "false");
        els.panel.classList.toggle("active", isActive);
    });

    if (tabName === "preview" && currentActiveDatasetInDrawer) {
        loadDrawerPreview(currentActiveDatasetInDrawer);
    }
}

// Drawer Preview Table Loading
async function loadDrawerPreview(dataset) {
    const container = document.getElementById("drawer-panel-preview");
    if (!container) return;

    if (container.dataset.loadedFor === dataset.dataset) return; // already loaded

    const jsonPath = dataset.outputs?.json;
    if (!jsonPath) {
        container.innerHTML = `<p class="dataset-preview-state" style="padding:1.5rem; text-align:center; color:var(--text-secondary);">Vista previa no disponible para este dataset (no tiene output JSON).</p>`;
        return;
    }

    container.innerHTML = `<p class="dataset-preview-state" style="padding:1.5rem; text-align:center; color:var(--text-secondary);">Cargando muestra...</p>`;
    try {
        const response = await fetch(jsonPath);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const rows = await response.json();

        if (!Array.isArray(rows) || rows.length === 0) {
            container.innerHTML = `<p class="dataset-preview-state" style="padding:1.5rem; text-align:center; color:var(--text-secondary);">El archivo no contiene filas para mostrar.</p>`;
            return;
        }

        const columns = Object.keys(rows[0]);
        const visibleCols = columns.slice(0, 10);

        container.innerHTML = `
            <div class="drawer-preview-table-container">
                <table class="drawer-preview-table dataset-preview-table">
                    <thead><tr>${visibleCols.map(column => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
                    <tbody>${rows.slice(0, 10).map(row => `
                        <tr>${visibleCols.map(column => `<td>${escapeHtml(formatPreviewValue(row[column]))}</td>`).join("")}</tr>
                    `).join("")}</tbody>
                </table>
            </div>
            <p class="dataset-preview-note" style="margin-top: 0.75rem; font-size: 0.8rem; color: var(--text-secondary);">
                Primeras ${Math.min(rows.length, 10)} filas · ${visibleCols.length} de ${columns.length} columnas visibles.
            </p>
        `;
        container.dataset.loadedFor = dataset.dataset;
    } catch (error) {
        console.error("No se pudo cargar la vista previa en drawer:", error);
        container.innerHTML = `<p class="dataset-preview-state error" style="padding:1.5rem; text-align:center; color: #ef4444;">No se pudo cargar la muestra. El archivo JSON sigue disponible para descarga.</p>`;
    }
}

// Open Drawer Details
function showDatasetDrawer(dataset) {
    const runtimeFreshness = computeRuntimeFreshness(dataset);
    currentActiveDatasetInDrawer = dataset;

    drawerTitle.textContent = dataset.dataset;
    drawerDesc.textContent = dataset.description || "";

    // Switch tabs to "Ficha Técnica" by default
    setActiveDrawerTab("ficha");

    // Populate Ficha Técnica
    const parquetMeta = dataset.outputs?.parquet ? artifactManifestByPath[dataset.outputs.parquet] || packageManifestByPath[dataset.outputs.parquet] : null;
    const parquetSize = parquetMeta?.size_bytes ? formatBytes(parquetMeta.size_bytes) : (dataset.outputs?.parquet ? "N/D" : "N/D");
    const parquetHash = parquetMeta?.sha256 || dataset.outputs?.parquet?.sha256 || "N/D";

    const jsonMeta = dataset.outputs?.json ? artifactManifestByPath[dataset.outputs.json] || packageManifestByPath[dataset.outputs.json] : null;
    const jsonSize = jsonMeta?.size_bytes ? formatBytes(jsonMeta.size_bytes) : (dataset.outputs?.json ? "N/D" : "N/D");
    const jsonHash = jsonMeta?.sha256 || dataset.outputs?.json?.sha256 || "N/D";

    // Fields tags
    const fieldsHtml = (dataset.fields || []).map(f => `<span class="dataset-tag" style="margin-bottom: 0.25rem; display: inline-block;">${escapeHtml(f)}</span>`).join(" ");

    document.getElementById("drawer-panel-ficha").innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- Facts block -->
            <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.75rem;">Metadatos y Contrato</h4>
                <div class="dataset-facts" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Join keys</span>
                        <span class="dataset-fact-value">${escapeHtml((dataset.join_keys || []).join(", ") || "N/D")}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Confianza</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.confidence_tier || "N/D")}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Reuso</span>
                        <span class="dataset-fact-value">${escapeHtml(formatReusePolicy(dataset.reuse_policy))}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Coverage</span>
                        <span class="dataset-fact-value">${escapeHtml(formatCoverage(dataset.coverage))}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Drift</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.drift?.status || "N/D")}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Degradación</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.degradation?.status || "N/D")}</span>
                    </div>
                </div>
            </div>

            <!-- Fields Dictionary -->
            <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Diccionario de Columnas</h4>
                <div>
                    ${fieldsHtml || `<span style="font-size: 0.85rem; color: var(--text-secondary);">No hay información de columnas disponible.</span>`}
                </div>
            </div>

            <!-- Procedencia block -->
            <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.75rem;">Procedencia y Freshness</h4>
                <div style="font-size: 0.85rem; line-height: 1.5; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.4rem;">
                    <div class="dataset-meta-line">Validación: <strong>${escapeHtml(dataset.validation_status || "N/D")}</strong> · Actualizado: ${escapeHtml(formatTimestamp(dataset.refreshed_at_utc))} · Requiere atribución: <strong>${dataset.reuse_policy?.attribution_required ? "sí" : "no"}</strong></div>
                    <div class="dataset-meta-line">Procedencia técnica: <strong>${escapeHtml(dataset.source_detail || "N/D")}</strong> · Warnings: <strong>${escapeHtml(String(dataset.warning_count ?? 0))}</strong></div>
                    <div class="dataset-meta-line">Freshness build: ${escapeHtml(formatFreshness(dataset.freshness))} · Freshness actual: ${escapeHtml(formatFreshness(runtimeFreshness))}</div>
                    ${dataset.warning_count > 0 && (dataset.degradation?.recommended_action || dataset.drift?.recommended_action)
                        ? `<div class="dataset-meta-line" style="background: #fffbeb; border: 1px solid #fef3c7; padding: 0.75rem; border-radius: 6px; color: #92400e; margin-top: 0.5rem;">
                             <strong>Acción recomendada:</strong> ${escapeHtml(dataset.degradation?.recommended_action || dataset.drift?.recommended_action)}
                           </div>`
                        : ""}
                </div>
            </div>

            <!-- Descargas block -->
            <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.75rem;">Artefactos y Descargas</h4>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${dataset.outputs?.parquet ? `
                        <div class="dataset-artifact-meta" style="border: 1px solid var(--border-color); padding: 0.75rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                            <div>
                                <strong style="color: var(--text-primary);">Formato Parquet</strong>
                                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.15rem;">tipo: parquet · sha256: ${parquetHash}</div>
                            </div>
                            <a class="btn btn-primary" href="${escapeHtml(dataset.outputs.parquet)}" download style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">Descargar</a>
                        </div>
                    ` : ""}
                    ${dataset.outputs?.json ? `
                        <div class="dataset-artifact-meta" style="border: 1px solid var(--border-color); padding: 0.75rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                            <div>
                                <strong style="color: var(--text-primary);">Formato JSON</strong>
                                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.15rem;">tipo: json · sha256: ${jsonHash}</div>
                            </div>
                            <a class="btn btn-primary" href="${escapeHtml(dataset.outputs.json)}" download style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">Descargar</a>
                        </div>
                    ` : ""}
                </div>
            </div>
        </div>
    `;

    // Populate Receta
    document.getElementById("drawer-panel-receta").innerHTML = buildDatasetExample(dataset);
    wireDatasetExampleInteractions();

    // Show panel
    drawer.classList.add("active");
    drawerBackdrop.classList.add("active");
    drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
    drawer.classList.remove("active");
    drawerBackdrop.classList.remove("active");
    drawer.setAttribute("aria-hidden", "true");
    currentActiveDatasetInDrawer = null;

    // Clear preview loadedFor state so it can reload next time
    drawerPanelPreview.removeAttribute("data-loaded-for");
    drawerPanelPreview.innerHTML = "";
}

function handleHashChange() {
    const hash = window.location.hash;
    if (hash.startsWith("#dataset-")) {
        const datasetName = hash.replace("#dataset-", "");
        const dataset = currentCatalogDatasets.find(d => d.dataset === datasetName);
        if (dataset) {
            showDatasetDrawer(dataset);
            return;
        }
    }
    closeDrawer();
}

async function loadHubHealth() {
    const tbody = document.getElementById("health-tbody");
    const tableWrap = document.getElementById("health-table-wrap");
    const badge = document.getElementById("health-badge");
    if (!tbody) return;

    try {
        const res = await fetch("data/normalized/hub_health.json");
        if (!res.ok) throw new Error("Not found");
        const health = await res.json();

        // Summary metrics
        document.getElementById("health-dataset-count").textContent = health.dataset_count || "—";
        document.getElementById("health-ok-count").textContent = health.ok_count ?? "—";
        document.getElementById("health-warn-count").textContent = health.warn_count ?? "—";
        document.getElementById("health-error-count").textContent = health.error_count ?? "—";
        document.getElementById("health-live-count").textContent = health.live_count ?? "—";
        document.getElementById("health-fallback-count").textContent = health.fallback_count ?? "—";
        document.getElementById("health-stale-count").textContent = health.stale_count ?? "—";
        document.getElementById("health-drifted-count").textContent = health.drifted_count ?? "—";

        // Generated at
        const genEl = document.getElementById("health-generated-at");
        if (genEl && health.generated_at_utc) {
            genEl.textContent = formatTimestamp(health.generated_at_utc);
        }

        // Overall badge
        if (badge) {
            const status = health.overall_status || "unknown";
            badge.textContent = status;
            badge.className = "health-badge " + status;
        }

        // Per-dataset table
        if (tbody && Array.isArray(health.datasets)) {
            tableWrap?.classList.remove("health-hidden");
            tbody.innerHTML = health.datasets.map(function(entry) {
                const sev = entry.severity || "unknown";
                return '<tr class="severity-' + sev + '">' +
                    '<td>' + escapeHtml(entry.dataset) + '</td>' +
                    '<td><span class="pill ' + sev + '">' + sev + '</span></td>' +
                    '<td><span class="pill ' + (entry.source_mode || "unknown") + '">' + escapeHtml(entry.source_mode || "unknown") + '</span></td>' +
                    '<td><span class="pill ' + (entry.validation_status || "unknown") + '">' + escapeHtml(entry.validation_status || "unknown") + '</span></td>' +
                    '<td><span class="pill ' + (entry.freshness_status || "unknown") + '">' + escapeHtml(entry.freshness_status || "unknown") + '</span></td>' +
                    '<td><span class="pill ' + (entry.coverage_status || "unknown") + '">' + escapeHtml(entry.coverage_status || "unknown") + '</span></td>' +
                    '<td><span class="pill ' + (entry.drift_status || "unknown") + '">' + escapeHtml(entry.drift_status || "unknown") + '</span></td>' +
                    '<td>' + (entry.warning_count ?? 0) + '</td>' +
                    '</tr>';
            }).join("");
        }
    } catch (_e) {
        // No health data — section stays hidden (graceful degradation)
        if (badge) { badge.className = "health-badge unknown"; badge.textContent = "no data"; }
    }
}

function loadCatalog() {
    Promise.all([
        fetch("data/normalized/hub_bundle.json").then(res => {
            if (!res.ok) throw new Error("No se pudo cargar el bundle");
            return res.json();
        }),
        fetch("data/normalized/artifact_manifest.json")
            .then(res => res.ok ? res.json() : null)
            .catch(() => null)
    ])
        .then(([bundle, manifest]) => {
            // Sincroniza la versión del badge con el bundle (fuente única de verdad).
            var versionBadge = document.querySelector(".badge-alpha");
            if (versionBadge && bundle.version) {
                versionBadge.textContent = "v" + bundle.version;
            }

            artifactManifestByPath = Object.fromEntries(
                (manifest?.artifacts || []).map(entry => [entry.path, entry])
            );
            packageManifestByPath = Object.fromEntries(
                (manifest?.packages || []).map(entry => [entry.path, entry])
            );
            renderCatalog(bundle);
        })
        .catch(err => {
            console.error("Error cargando catálogo:", err);
            statusSubtitle.textContent = "No se pudo cargar el estado del hub.";
            statusMeta.textContent = "Sin información de estado disponible.";
            statusPills.innerHTML = `<span class="status-pill">Catálogo no disponible</span>`;
            statusActions.innerHTML = `
                <a class="dataset-action muted" href="data/normalized/hub_bundle.json" target="_blank" rel="noopener noreferrer">Bundle JSON</a>
            `;
            packageMeta.textContent = "Bundle no disponible.";
            packageActions.innerHTML = `
                <a class="dataset-action muted" href="data/normalized/hub_bundle.json" target="_blank" rel="noopener noreferrer">Bundle JSON</a>
            `;
            document.getElementById("package-verify-code").textContent = "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256";
            catalogGeneratedAt.textContent = "";
            catalogGrid.innerHTML = `
                <div class="dataset-card">
                    <div class="dataset-name">Catálogo no disponible</div>
                    <div class="dataset-desc">Compila el pipeline para ver los datasets aquí.</div>
                </div>
            `;
        });
}

function renderCatalog(bundle) {
    const datasets = bundle.datasets || [];
    const health = bundle.health || {};
    const reports = bundle.reports || {};
    const persistedTopIssue = health.top_issue || bundle.top_issue || null;
    const datasetsByName = Object.fromEntries(
        datasets.map(dataset => [dataset.dataset, dataset])
    );
    const runtimeFreshnessByDataset = Object.fromEntries(
        datasets.map(dataset => [dataset.dataset, computeRuntimeFreshness(dataset)])
    );
    const liveCount = health.live_count ?? datasets.filter(d => d.source_mode === "live").length;
    const warningCount = health.warning_count ?? datasets.reduce((acc, d) => acc + (d.warning_count || 0), 0);
    const staleCount = Object.values(runtimeFreshnessByDataset).filter(
        freshness => freshness.status === "stale"
    ).length;
    const unknownFreshnessCount = Object.values(runtimeFreshnessByDataset).filter(
        freshness => freshness.status === "unknown"
    ).length;
    const reviewTermsCount = health.review_terms_count ?? datasets.filter(d => d.publishability_status === "review_terms").length;
    const degradedCount = health.degraded_count ?? datasets.filter(d => d.degradation?.status === "degraded").length;
    const partialCoverageCount = health.partial_coverage_count ?? datasets.filter(d => d.coverage?.status === "partial").length;
    const driftedCount = health.drifted_count ?? datasets.filter(d => d.drift?.status === "drifted").length;
    const buildOverallStatus = bundle.overall_status || "ok";
    const currentOverallStatus = computeRuntimeOverallStatus(buildOverallStatus, runtimeFreshnessByDataset);
    const zipPackage = (bundle.packages || []).find(pkg => pkg.package_type === "zip");
    const zipLabel = zipPackage
        ? `Bundle ZIP · ${formatBytes(zipPackage.size_bytes)}`
        : "Bundle ZIP";
    const zipHash = zipPackage?.sha256 ? zipPackage.sha256.slice(0, 12) : "N/D";
    const verifyCommand = zipPackage?.verification_command
        || (zipPackage?.checksum_path ? `shasum -a 256 -c ${zipPackage.checksum_path}` : "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256");

    statusSubtitle.textContent = `${datasets.length} capas disponibles. Último build: ${formatTimestamp(bundle.generated_at_utc)}.`;
    packageMeta.textContent = zipPackage
        ? `Tamaño: ${formatBytes(zipPackage.size_bytes)} · sha256: ${zipHash} · generado junto al último build`
        : "No hay package ZIP disponible en este build.";
    document.getElementById("package-verify-code").textContent = verifyCommand;
    packageActions.innerHTML = `
        ${zipPackage ? buildSimpleLink(zipPackage.path, zipLabel) : ""}
        ${zipPackage?.checksum_path ? buildSimpleLink(zipPackage.checksum_path, "SHA256") : ""}
        ${buildSimpleLink(findReportPath(reports, "hub_bundle", "json", "data/normalized/hub_bundle.json"), "Bundle JSON")}
        ${buildSimpleLink(findReportPath(reports, "artifact_manifest", "json", "data/normalized/artifact_manifest.json"), "Manifest")}
    `;

    catalogGeneratedAt.textContent = `Actualizado: ${formatTimestamp(bundle.generated_at_utc)}`;

    const orderedDatasets = [...datasets].sort((left, right) => {
        if (persistedTopIssue?.dataset && left.dataset === persistedTopIssue.dataset && right.dataset !== persistedTopIssue.dataset) return -1;
        if (persistedTopIssue?.dataset && right.dataset === persistedTopIssue.dataset && left.dataset !== persistedTopIssue.dataset) return 1;
        const leftFreshness = runtimeFreshnessByDataset[left.dataset] || { status: "unknown" };
        const rightFreshness = runtimeFreshnessByDataset[right.dataset] || { status: "unknown" };
        const leftPriority = computeAttentionPriority(left, leftFreshness);
        const rightPriority = computeAttentionPriority(right, rightFreshness);
        if (leftPriority !== rightPriority) return leftPriority - rightPriority;
        return left.dataset.localeCompare(right.dataset, "es");
    });
    const fallbackTopAttentionDataset = orderedDatasets.find(dataset => {
        const runtimeFreshness = runtimeFreshnessByDataset[dataset.dataset] || { status: "unknown" };
        return computeAttentionPriority(dataset, runtimeFreshness) === 0;
    });
    const activeTopIssue = persistedTopIssue || (
        fallbackTopAttentionDataset
            ? {
                dataset: fallbackTopAttentionDataset.dataset,
                diagnostic_summary: fallbackTopAttentionDataset.degradation?.impact
                    || fallbackTopAttentionDataset.drift?.summary
                    || "",
                recommended_action: fallbackTopAttentionDataset.degradation?.recommended_action
                    || fallbackTopAttentionDataset.drift?.recommended_action
                    || "",
            }
            : null
    );
    const activeTopIssueDatasetName = activeTopIssue?.dataset || null;
    const activeTopIssueDataset = activeTopIssueDatasetName
        ? (datasetsByName[activeTopIssueDatasetName] || null)
        : null;
    const topIssueReason = activeTopIssue
        ? (activeTopIssue.diagnostic_summary || "")
        : "";
    const topIssueAction = activeTopIssue
        ? (activeTopIssue.recommended_action || "")
        : "";
    const topIssueSourceDetail = activeTopIssue
        ? (activeTopIssue.source_detail || activeTopIssueDataset?.source_detail || "unknown")
        : "unknown";

    statusPills.innerHTML = `
        <span class="status-pill">Estado build: ${buildOverallStatus}</span>
        <span class="status-pill">Estado actual: ${currentOverallStatus}</span>
        ${activeTopIssueDatasetName ? `<span class="status-pill">Top issue: ${escapeHtml(activeTopIssueDatasetName)}</span>` : ""}
        <span class="status-pill">Capas: ${datasets.length}</span>
        <span class="status-pill">Live: ${liveCount}</span>
        <span class="status-pill">Stale: ${staleCount}</span>
        <span class="status-pill">Freshness unknown: ${unknownFreshnessCount}</span>
        <span class="status-pill">Drifted: ${driftedCount}</span>
        <span class="status-pill">Degraded: ${degradedCount}</span>
        <span class="status-pill">Partial coverage: ${partialCoverageCount}</span>
        <span class="status-pill">Review terms: ${reviewTermsCount}</span>
        <span class="status-pill">Warnings: ${warningCount}</span>
    `;

    statusMeta.textContent = activeTopIssueDatasetName
        ? `${activeTopIssueDatasetName}: ${topIssueReason}${topIssueAction ? ` · ${topIssueAction}` : ""}${topIssueSourceDetail && topIssueSourceDetail !== "unknown" ? ` · Fuente: ${topIssueSourceDetail}` : ""}`
        : "";

    statusActions.innerHTML = `
        ${buildSimpleLink(findReportPath(reports, "pipeline_status", "markdown", "data/normalized/pipeline_status.md"), "Status")}
        ${buildSimpleLink(findReportPath(reports, "hub_status", "json", "data/normalized/hub_status.json"), "Status JSON")}
        ${buildSimpleLink(findReportPath(reports, "hub_health", "json", "data/normalized/hub_health.json"), "Health JSON")}
        ${buildSimpleLink(findReportPath(reports, "hub_health", "markdown", "data/normalized/hub_health.md"), "Health MD")}
        ${buildSimpleLink(findReportPath(reports, "hub_bundle", "json", "data/normalized/hub_bundle.json"), "Bundle JSON")}
        ${buildSimpleLink(findReportPath(reports, "redistribution_report", "json", "data/normalized/redistribution_report.json"), "Reuse JSON")}
        ${buildSimpleLink(findReportPath(reports, "redistribution_report", "markdown", "data/normalized/redistribution_report.md"), "Reuse MD")}
        ${buildSimpleLink(findReportPath(reports, "provenance_report", "json", "data/normalized/provenance_report.json"), "Provenance JSON")}
        ${buildSimpleLink(findReportPath(reports, "provenance_report", "markdown", "data/normalized/provenance_report.md"), "Provenance MD")}
        ${buildSimpleLink(findReportPath(reports, "drift_report", "json", "data/normalized/drift_report.json"), "Drift JSON")}
        ${buildSimpleLink(findReportPath(reports, "drift_report", "markdown", "data/normalized/drift_report.md"), "Drift MD")}
        ${buildSimpleLink(findReportPath(reports, "overview", "json", "data/normalized/overview.json"), "Overview JSON")}
        ${buildSimpleLink(findReportPath(reports, "overview", "markdown", "data/normalized/overview.md"), "Overview MD")}
        ${buildSimpleLink(findReportPath(reports, "dataset_catalog", "json", "data/normalized/dataset_catalog.json"), "Catalog JSON")}
        ${buildSimpleLink(findReportPath(reports, "dataset_catalog", "markdown", "data/normalized/dataset_catalog.md"), "Catalog MD")}
        ${buildSimpleLink(findReportPath(reports, "artifact_manifest", "json", "data/normalized/artifact_manifest.json"), "Manifest")}
        ${activeTopIssueDatasetName ? `<a class="dataset-action muted" href="#dataset-${escapeHtml(activeTopIssueDatasetName)}">Ver top issue</a>` : ""}
    `;

    currentCatalogDatasets = orderedDatasets;

    const CATEGORIES = {
        territorio: {
            title: "Core Territorial (DPA y derivados)",
            datasets: ["regiones", "provincias", "comunas", "comunas_enriquecidas", "distritos_electorales", "perfil_territorial_comunal"]
        },
        demografia: {
            title: "Demografía y Estadísticas",
            datasets: ["censo_comunal", "censo_hogares_viviendas", "finanzas_municipales", "resultados_educacionales", "indicadores_urbanos_siedu"]
        },
        directorios: {
            title: "Directorios Oficiales y Economía",
            datasets: ["establecimientos_salud", "establecimientos_educacionales", "empresas", "indicadores"]
        }
    };

    const categoriesHtml = Object.entries(CATEGORIES).map(([catKey, catMeta]) => {
        const catDatasets = orderedDatasets.filter(d => catMeta.datasets.includes(d.dataset));
        if (catDatasets.length === 0) return "";

        const cardsHtml = catDatasets.map(dataset => {
            const runtimeFreshness = runtimeFreshnessByDataset[dataset.dataset] || { status: "unknown" };
            const recordCount = typeof dataset.record_count === "number"
                ? formatNum.format(dataset.record_count)
                : "N/D";
            const parquetMeta = dataset.outputs?.parquet ? artifactManifestByPath[dataset.outputs.parquet] || packageManifestByPath[dataset.outputs.parquet] : null;
            const sizeBytes = parquetMeta?.size_bytes ? formatBytes(parquetMeta.size_bytes) : "N/D";
            const warningBadge = dataset.warning_count > 0
                ? `<span class="dataset-tag warning">${dataset.warning_count} warnings</span>`
                : "";

            return `
                <article class="dataset-card" id="dataset-${escapeHtml(dataset.dataset)}" data-search="${escapeHtml([dataset.dataset, dataset.description, dataset.source_name, ...(dataset.join_keys || []), ...Object.keys(dataset.outputs || {})].filter(Boolean).join(" "))}">
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
                            <span class="dataset-fact-mini-value" title="${escapeHtml(dataset.source_name)}">${escapeHtml(dataset.source_name || "N/D")}</span>
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

                    ${buildMonedarioBridge(dataset)}

                    <div class="dataset-card-actions">
                        <a href="#dataset-${escapeHtml(dataset.dataset)}" class="btn-card-action primary btn-details">Ver Ficha</a>
                        ${dataset.outputs?.parquet ? `<a class="btn-card-action" href="${escapeHtml(dataset.outputs.parquet)}" download>Parquet</a>` : ""}
                    </div>
                </article>
            `;
        }).join("");

        return `
            <section class="catalog-category" id="cat-${catKey}">
                <div class="catalog-category-header">
                    <h3 class="catalog-category-title">
                        ${escapeHtml(catMeta.title)}
                        <span class="catalog-category-count">${catDatasets.length}</span>
                    </h3>
                </div>
                <div class="catalog-grid-sub">
                    ${cardsHtml}
                </div>
            </section>
        `;
    }).join("");

    catalogGrid.innerHTML = categoriesHtml;

    filterCatalog();

    if (packageVerifyCopy && !packageVerifyCopy.dataset.wired) {
        packageVerifyCopy.addEventListener("click", () => {
            copyTextFromTarget(packageVerifyCopy, packageVerifyCopy.dataset.copyTarget);
        });
        packageVerifyCopy.dataset.wired = "true";
    }
}

if (catalogSearchInput) {
    catalogSearchInput.addEventListener("input", filterCatalog);
}

async function copyTextFromTarget(button, targetId) {
    const target = document.getElementById(targetId);
    if (!target) return;

    const text = target.innerText;
    const originalLabel = button.textContent;

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else if (!fallbackCopyText(text)) {
            throw new Error("clipboard_unavailable");
        }
        button.textContent = "Copiado";
        button.classList.add("copied");
    } catch (error) {
        const copied = fallbackCopyText(text);
        if (copied) {
            button.textContent = "Copiado";
            button.classList.add("copied");
        } else {
            console.error("No se pudo copiar el snippet:", error);
            button.textContent = "Error";
        }
    }

    window.setTimeout(() => {
        button.textContent = originalLabel;
        button.classList.remove("copied");
    }, 1400);
}

async function copyQuickstartSnippet(button) {
    return copyTextFromTarget(button, button.dataset.copyTarget);
}

// Cargar indicadores económicos en KPI Cards
function loadKPIs() {
    fetch("data/normalized/indicadores_hoy.json")
        .then(res => {
            if (!res.ok) throw new Error("No se pudo cargar los indicadores");
            return res.json();
        })
        .then(data => {
            // Buscar el valor mas reciente que no sea futuro (<= hoy)
            const today = new Date().toISOString().split("T")[0];
            const findValue = (code) => {
                const matches = data
                    .filter(i => i.codigo_indicador === code && i.fecha <= today)
                    .sort((a, b) => a.fecha.localeCompare(b.fecha));
                return matches[matches.length - 1];
            };

            updateKPICard("kpi-uf", findValue("uf"));
            updateKPICard("kpi-dolar", findValue("dolar"), true);
            updateKPICard("kpi-euro", findValue("euro"), true);
            updateKPICard("kpi-utm", findValue("utm"));
        })
        .catch(err => {
            console.error("Error cargando indicadores:", err);
            showKPIError("kpi-uf", "UF");
            showKPIError("kpi-dolar", "Dólar");
            showKPIError("kpi-euro", "Euro");
            showKPIError("kpi-utm", "UTM");
        });
}

function updateKPICard(id, dataObj, isCurrencySymbol = false) {
    const card = document.getElementById(id);
    if (dataObj) {
        const valueSpan = card.querySelector(".kpi-value");
        const dateSpan = card.querySelector(".kpi-date");

        valueSpan.textContent = formatCLP.format(dataObj.valor);
        dateSpan.textContent = `Vigencia: ${dataObj.fecha}`;
    } else {
        showKPIError(id, card.querySelector(".kpi-label").textContent);
    }
}

function showKPIError(id, label) {
    const card = document.getElementById(id);
    card.querySelector(".kpi-value").textContent = "N/D";
    card.querySelector(".kpi-date").textContent = "Sin datos disponibles";
    card.querySelector(".kpi-value").style.color = "var(--text-secondary)";
}

// Cargar datos territoriales
function loadComunas() {
    fetch("data/normalized/comunas.json")
        .then(res => {
            if (!res.ok) throw new Error("No se pudo cargar la DPA");
            return res.json();
        })
        .then(data => {
            comunas = data;
            filteredComunas = [...comunas];
            populateRegionFilter();
            renderTable();
        })
        .catch(err => {
            console.error("Error cargando comunas:", err);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="no-results" style="color: #f87171;">
                        Error al cargar los datos territoriales. Levanta un servidor local y compila los datos en data/normalized/.
                    </td>
                </tr>
            `;
        });
}

// Llenar select de regiones de forma dinámica
function populateRegionFilter() {
    const regionesUnicas = [];
    const regionesMap = {};

    comunas.forEach(c => {
        if (!regionesMap[c.codigo_region]) {
            regionesMap[c.codigo_region] = c.nombre_region;
            regionesUnicas.push({
                codigo: c.codigo_region,
                nombre: c.nombre_region
            });
        }
    });

    // Ordenar regiones por código
    regionesUnicas.sort((a, b) => a.codigo.localeCompare(b.codigo));

    regionesUnicas.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r.codigo;
        opt.textContent = `${r.codigo} - ${r.nombre}`;
        regionFilter.appendChild(opt);
    });
}

// Renderizar la tabla de comunas basándose en filtros y paginación
function renderTable() {
    tableBody.innerHTML = "";

    if (filteredComunas.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="no-results">
                    No se encontraron comunas que coincidan con la búsqueda.
                </td>
            </tr>
        `;
        pageInfo.textContent = "Mostrando 0 - 0 de 0 comunas";
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
    }

    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = Math.min(startIdx + rowsPerPage, filteredComunas.length);
    const paginatedRows = filteredComunas.slice(startIdx, endIdx);

    paginatedRows.forEach(c => {
        const tr = document.createElement("tr");
        const lat = c.latitud_cabecera?.toFixed(4) ?? "N/D";
        const lon = c.longitud_cabecera?.toFixed(4) ?? "N/D";
        tr.innerHTML = `
            <td><span class="comuna-code">${escapeHtml(c.codigo_comuna)}</span></td>
            <td style="font-weight: 500; color: var(--text-primary);">${escapeHtml(c.nombre_comuna)}</td>
            <td>${escapeHtml(c.nombre_provincia)}</td>
            <td>${escapeHtml(c.nombre_region)}</td>
            <td>${formatNum.format(c.poblacion_estimada)}</td>
            <td style="font-size: 0.85rem; font-family: monospace;">${lat}, ${lon}</td>
        `;
        tableBody.appendChild(tr);
    });

    // Actualizar estado de paginador
    pageInfo.textContent = `Mostrando ${startIdx + 1} - ${endIdx} de ${filteredComunas.length} comunas`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = endIdx >= filteredComunas.length;
}

// Filtro y búsqueda reactiva
function applyFilters() {
    const query = searchInput.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const selectedRegion = regionFilter.value;

    filteredComunas = comunas.filter(c => {
        // Filtro por Región
        const matchRegion = !selectedRegion || c.codigo_region === selectedRegion;

        // Filtro de Texto (sobre comuna, provincia y región desnormalizada)
        const matchText = !query ||
            c.nombre_comuna_clean.includes(query) ||
            c.nombre_provincia.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(query) ||
            c.nombre_region.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(query) ||
            c.codigo_comuna.includes(query);

        return matchRegion && matchText;
    });

    currentPage = 1; // Reseteamos a la página 1 tras cambiar filtros
    renderTable();
}

// Eventos de usuario
searchInput.addEventListener("input", applyFilters);
regionFilter.addEventListener("change", applyFilters);

prevBtn.addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        renderTable();
    }
});

nextBtn.addEventListener("click", () => {
    if ((currentPage * rowsPerPage) < filteredComunas.length) {
        currentPage++;
        renderTable();
    }
});

// Exportación de datos filtrados a CSV del lado del cliente
exportBtn.addEventListener("click", () => {
    if (filteredComunas.length === 0) return;

    const headers = ["codigo_comuna", "nombre_comuna", "codigo_provincia", "nombre_provincia", "codigo_region", "nombre_region", "poblacion_estimada", "latitud", "longitud"];

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += headers.join(",") + "\n";

    filteredComunas.forEach(c => {
        const row = [
            `"${c.codigo_comuna}"`, // Encapsulado para no perder ceros iniciales
            `"${c.nombre_comuna}"`,
            `"${c.codigo_provincia}"`,
            `"${c.nombre_provincia}"`,
            `"${c.codigo_region}"`,
            `"${c.nombre_region}"`,
            c.poblacion_estimada,
            c.latitud_cabecera,
            c.longitud_cabecera
        ];
        csvContent += row.join(",") + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `chile_data_comunas_filtered.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

quickstartCopyButtons.forEach(button => {
    button.addEventListener("click", () => {
        copyQuickstartSnippet(button);
    });
});

// Inicialización
window.addEventListener("DOMContentLoaded", () => {
    renderSupportLinks();
    loadKPIs();
    loadHubHealth();
    loadCatalog();
    loadComunas();

    // Drawer and Routing Init
    window.addEventListener("hashchange", handleHashChange);

    if (drawerTabFicha) drawerTabFicha.addEventListener("click", () => setActiveDrawerTab("ficha"));
    if (drawerTabPreview) drawerTabPreview.addEventListener("click", () => setActiveDrawerTab("preview"));
    if (drawerTabReceta) drawerTabReceta.addEventListener("click", () => setActiveDrawerTab("receta"));

    if (drawerClose) {
        drawerClose.addEventListener("click", () => {
            window.location.hash = "";
        });
    }
    if (drawerBackdrop) {
        drawerBackdrop.addEventListener("click", () => {
            window.location.hash = "";
        });
    }
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && drawer && drawer.classList.contains("active")) {
            window.location.hash = "";
        }
    });

    // Check hash on load
    handleHashChange();
});
