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
const quickstartCopyButtons = document.querySelectorAll(".quickstart-copy");
let artifactManifestByPath = {};
let packageManifestByPath = {};

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

function findReportPath(reports, sharedType, format, fallbackPath) {
    const reportEntries = Object.values(reports || {});
    const matched = reportEntries.find(entry => entry?.shared_type === sharedType && entry?.format === format);
    return matched?.path || fallbackPath;
}

function buildDatasetExample(dataset, preferredKind = "python") {
    const examples = dataset.usage_examples || {};
    const kinds = ["python", "duckdb", "cli"].filter(kind => examples[kind]);
    if (kinds.length === 0) return "";

    const activeKind = kinds.includes(preferredKind) ? preferredKind : kinds[0];
    const exampleId = `dataset-example-${escapeHtml(dataset.dataset)}`;
    const tabs = kinds.map(kind => `
        <button class="dataset-example-tab ${kind === activeKind ? "active" : ""}" data-kind="${escapeHtml(kind)}">
            ${escapeHtml(kind)}
        </button>
    `).join("");

    return `
        <div class="dataset-example" data-dataset-example data-examples='${escapeHtml(JSON.stringify(examples))}'>
            <div class="dataset-example-head">
                <span class="dataset-example-title">Receta de uso</span>
                <div class="dataset-example-tabs">
                    ${tabs}
                    <button class="dataset-example-copy" data-copy-target="${exampleId}">Copiar</button>
                </div>
            </div>
            <pre class="dataset-example-code" id="${exampleId}">${escapeHtml(examples[activeKind])}</pre>
        </div>
    `;
}

function activateDatasetExample(container, nextKind) {
    const examples = JSON.parse(container.dataset.examples || "{}");
    if (!examples[nextKind]) return;

    container.querySelectorAll(".dataset-example-tab").forEach(tab => {
        tab.classList.toggle("active", tab.dataset.kind === nextKind);
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
            statusSubtitle.textContent = "No se pudo cargar el estado del hub local.";
            statusMeta.textContent = "Sin top issue diagnosticado en este momento.";
            statusPills.innerHTML = `<span class="status-pill">Catálogo no disponible</span>`;
            statusActions.innerHTML = `
                <a class="dataset-action muted" href="data/normalized/hub_bundle.json" target="_blank" rel="noopener noreferrer">Bundle JSON</a>
            `;
            packageMeta.textContent = "Sin package metadata local";
            packageActions.innerHTML = `
                <a class="dataset-action muted" href="data/normalized/hub_bundle.json" target="_blank" rel="noopener noreferrer">Bundle JSON</a>
            `;
            document.getElementById("package-verify-code").textContent = "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256";
            catalogGeneratedAt.textContent = "Sin metadata local";
            catalogGrid.innerHTML = `
                <div class="dataset-card">
                    <div class="dataset-name">Catálogo no disponible</div>
                    <div class="dataset-desc">Compila el pipeline para generar \`data/normalized/hub_bundle.json\`.</div>
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

    statusSubtitle.textContent = `${liveCount}/${datasets.length} capas operativas en modo live. Estado build: ${buildOverallStatus}. Estado actual: ${currentOverallStatus}. ${staleCount === 0 ? "Sin capas stale." : `${staleCount} capas stale.`} ${unknownFreshnessCount === 0 ? "Sin capas con freshness unknown." : `${unknownFreshnessCount} capas con freshness unknown.`} ${driftedCount === 0 ? "Sin capas con drift." : `${driftedCount} capas con drift.`} ${degradedCount === 0 ? "Sin capas degradadas." : `${degradedCount} capas degradadas.`} ${partialCoverageCount === 0 ? "Sin regresiones de cobertura." : `${partialCoverageCount} capas con cobertura parcial.`} ${reviewTermsCount === 0 ? "Sin capas en review_terms." : `${reviewTermsCount} capas en review_terms.`} ${warningCount === 0 ? "Sin warnings activos." : `${warningCount} warnings activos.`}`;
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
                    || "Sin detalle adicional.",
                recommended_action: fallbackTopAttentionDataset.degradation?.recommended_action
                    || fallbackTopAttentionDataset.drift?.recommended_action
                    || "Ninguna.",
            }
            : null
    );
    const activeTopIssueDatasetName = activeTopIssue?.dataset || null;
    const activeTopIssueDataset = activeTopIssueDatasetName
        ? (datasetsByName[activeTopIssueDatasetName] || null)
        : null;
    const topIssueReason = activeTopIssue
        ? (activeTopIssue.diagnostic_summary || "Sin detalle adicional.")
        : "Sin top issue activo en este build.";
    const topIssueAction = activeTopIssue
        ? (activeTopIssue.recommended_action || "Ninguna.")
        : "Sin top issue activo en este build.";
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
        ? `Motivo del top issue (${activeTopIssueDatasetName}): ${topIssueReason} · Procedencia técnica: ${topIssueSourceDetail} · Acción recomendada: ${topIssueAction}`
        : topIssueReason;

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

    catalogGrid.innerHTML = orderedDatasets.map(dataset => {
        const runtimeFreshness = runtimeFreshnessByDataset[dataset.dataset] || { status: "unknown" };
        const needsAttention = dataset.dataset === activeTopIssueDataset?.dataset
            || (dataset.warning_count ?? 0) > 0
            || runtimeFreshness.status === "stale"
            || runtimeFreshness.status === "unknown"
            || dataset.drift?.status === "drifted"
            || dataset.degradation?.status === "warning"
            || dataset.degradation?.status === "degraded";
        const outputs = Object.keys(dataset.outputs || {}).map(key => `<span class="dataset-tag">${escapeHtml(key)}</span>`).join("");
        const warnings = (dataset.warning_count && dataset.warning_count > 0)
            ? `<span class="dataset-tag">${escapeHtml(`${dataset.warning_count} warnings`)}</span>`
            : `<span class="dataset-tag">sin warnings</span>`;
        const jsonPath = dataset.outputs?.json;
        const parquetPath = dataset.outputs?.parquet;
        const docsPath = dataset.documentation;
        const sourceUrl = dataset.source_url;
        const recordCount = typeof dataset.record_count === "number"
            ? formatNum.format(dataset.record_count)
            : "N/D";

        return `
            <article class="dataset-card ${needsAttention ? "attention" : ""}" id="dataset-${escapeHtml(dataset.dataset)}" data-search="${escapeHtml([dataset.dataset, dataset.description, dataset.source_name, ...(dataset.join_keys || []), ...Object.keys(dataset.outputs || {})].filter(Boolean).join(" "))}">
                <div class="dataset-card-top">
                    <div>
                        <div class="dataset-name">${escapeHtml(dataset.dataset)}</div>
                        <div class="dataset-desc">${escapeHtml(dataset.description || "Sin descripción")}</div>
                    </div>
                    <div class="dataset-badges">
                        <span class="dataset-badge ${escapeHtml(dataset.source_mode || "fallback")}">${escapeHtml(dataset.source_mode || "unknown")}</span>
                        ${needsAttention ? `<span class="dataset-badge attention">atención</span>` : ""}
                    </div>
                </div>
                <div class="dataset-facts dataset-facts-primary">
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Fuente</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.source_name || "N/D")}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Registros</span>
                        <span class="dataset-fact-value">${escapeHtml(recordCount)}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Freshness</span>
                        <span class="dataset-fact-value">${escapeHtml(formatFreshness(runtimeFreshness))}</span>
                    </div>
                </div>
                <div class="dataset-actions">
                    ${buildArtifactLink(parquetPath, "Parquet")}
                    ${buildArtifactLink(jsonPath, "JSON")}
                    ${docsPath ? `<a class="dataset-action muted" href="${escapeHtml(docsPath)}" target="_blank" rel="noopener noreferrer">Docs</a>` : ""}
                </div>
                <details class="dataset-details">
                    <summary>Metadatos, fuente y recetas</summary>
                    <div class="dataset-facts">
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Join keys</span>
                        <span class="dataset-fact-value">${escapeHtml((dataset.join_keys || []).join(", ") || "N/D")}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Confianza</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.confidence_tier || "N/D")}</span>
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
                        <span class="dataset-fact-label">Reuso</span>
                        <span class="dataset-fact-value">${escapeHtml(formatReusePolicy(dataset.reuse_policy))}</span>
                    </div>
                    <div class="dataset-fact">
                        <span class="dataset-fact-label">Degradación</span>
                        <span class="dataset-fact-value">${escapeHtml(dataset.degradation?.status || "N/D")}</span>
                    </div>
                </div>
                <div class="dataset-meta-line">
                    Validación: <strong>${escapeHtml(dataset.validation_status || "N/D")}</strong> ·
                    Actualizado: ${escapeHtml(formatTimestamp(dataset.refreshed_at_utc))} ·
                    Requiere atribución: <strong>${dataset.reuse_policy?.attribution_required ? "sí" : "no"}</strong>
                </div>
                <div class="dataset-meta-line">
                    Procedencia técnica: <strong>${escapeHtml(dataset.source_detail || "N/D")}</strong> ·
                    Warnings: <strong>${escapeHtml(String(dataset.warning_count ?? 0))}</strong>
                </div>
                <div class="dataset-meta-line">Freshness build: ${escapeHtml(formatFreshness(dataset.freshness))} · Freshness actual: ${escapeHtml(formatFreshness(runtimeFreshness))}</div>
                ${dataset.warning_count > 0 && (dataset.degradation?.recommended_action || dataset.drift?.recommended_action)
                    ? `<div class="dataset-meta-line">Acción recomendada: ${escapeHtml(dataset.degradation?.recommended_action || dataset.drift?.recommended_action)}</div>`
                    : ""}
                ${dataset.drift?.summary ? `<div class="dataset-meta-line">Drift: ${escapeHtml(dataset.drift.summary)}</div>` : ""}
                ${dataset.coverage?.summary ? `<div class="dataset-meta-line">Cobertura: ${escapeHtml(dataset.coverage.summary)}</div>` : ""}
                ${dataset.degradation?.impact ? `<div class="dataset-meta-line">Impacto: ${escapeHtml(dataset.degradation.impact)}</div>` : ""}
                <div class="dataset-actions">
                    ${sourceUrl ? `<a class="dataset-action muted" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">Fuente</a>` : ""}
                </div>
                ${buildArtifactMeta(parquetPath)}
                ${buildArtifactMeta(jsonPath)}
                ${buildDatasetExample(dataset)}
                <div class="dataset-tags">${outputs}</div>
                <div class="dataset-tags">${warnings}</div>
                </details>
            </article>
        `;
    }).join("");

    wireDatasetExampleInteractions();
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
            const findValue = (code) => data.find(i => i.codigo_indicador === code);
            
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
    card.querySelector(".kpi-date").textContent = "Sin datos hoy";
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
                        Error al cargar los datos territoriales locales. Asegúrate de levantar un servidor web local y compilar los datos en data/normalized/.
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
    loadKPIs();
    loadCatalog();
    loadComunas();
});
