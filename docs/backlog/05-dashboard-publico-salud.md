# [05] Dashboard publico de salud operativa del hub

**Scorecard:** `docs/backlog/scorecard.md`
**Estado:** Pendiente
**Impacto:** Medio
**Esfuerzo estimado:** Medio
**Riesgo:** Bajo
**Target:** Q4 2026

---

## Problema que resuelve

La landing page (`index.html`, `app.js`) actualmente muestra los datasets y sus
datos, pero **no refleja el estado operativo del hub**:

1. Un visitante no sabe si los datos estan actualizados o stale.
2. No hay indicacion de que datasets estan ok, en warning, o en error.
3. No se muestra la ultima actualizacion del pipeline.
4. Los archivos `hub_health.json` y `dataset_status.json` ya existen como
   artefactos del pipeline, pero la landing page no los consume.

Sin este dashboard, los usuarios no tienen visibilidad de la salud del proyecto,
lo que reduce la confianza en los datos.

---

## Evidencia actual

### Landing page existente

- **`index.html`**: pagina estatica con catalogo de datasets, tabla de comunas,
  seccion de paquetes, enlaces de soporte. Sin seccion de estado operativo.
- **`app.js`**: ~540 lineas, carga `dataset_catalog.json` y `artifact_manifest.json`
  mediante fetch, renderiza tabla de datos, maneja paginacion y busqueda. No carga
  `hub_health.json` ni `dataset_status.json`.

### Artefactos disponibles (no consumidos)

- **`data/normalized/hub_health.json`**: contiene `overall_status`, `dataset_count`,
  `ok_count`, `warn_count`, `error_count`, `live_count`, `fallback_count`,
  `stale_count`, `drifted_count`, `degraded_count`, `warning_count`, `generated_at_utc`,
  y detalle por dataset con severidad, modo, validacion, frescura, cobertura, drift.
  Desde ADR-014 cada entrada trae además `actionable_warning_count` (subconjunto de
  `warning_count`, descontando los warnings declarados como esperados) y
  `coverage_expected` (parcialidad declarada en el contrato). La severidad y el
  `drifted_count` se calculan con los accionables: un dataset cuya parcialidad o
  cuyos warnings son de diseño ya no aparece como drift.
- **`data/normalized/dataset_status.json`**: contiene status detallado por dataset.
- **`data/normalized/hub_status.json`**: contiene status compacto con top_issue.
- **`data/normalized/freshness_audit.json`**: (no existe como archivo independiente,
  se calcula via `freshness_audit()`, core.py linea 922).

### Como se generan estos artefactos

- `build_hub_health()` en `src/pipeline_status_utils.py` (importado en build_dev_db.py
  linea 26).
- `hub_health_output = write_hub_health_json(hub_health)` en build_dev_db.py linea 3145.
- `dataset_status_output = write_dataset_status_json(...)` linea 3148.
- Se genera en cada ejecucion del pipeline (`python src/build_dev_db.py`).

### Enlaces actuales en landing page

`app.js` linea 539-541 ya enlaza a `hub_status.json`, `hub_health.json` y
`hub_health.md` como descargas, pero no los renderiza visualmente.

---

## Propuesta de implementacion

### Paso 1: Crear seccion de estado operativo en `index.html`

Agregar al DOM:

```html
<section id="hub-status-section" class="section">
  <h2>Estado operativo del hub</h2>
  <div id="hub-status-summary" class="status-summary">
    <!-- Overall status badge, generated_at, dataset counts -->
  </div>
  <div id="hub-status-table-container">
    <table id="hub-status-table">
      <thead>
        <tr>
          <th>Dataset</th>
          <th>Estado</th>
          <th>Modo</th>
          <th>Validacion</th>
          <th>Frescura</th>
          <th>Cobertura</th>
          <th>Drift</th>
          <th>Advertencias</th>
        </tr>
      </thead>
      <tbody id="hub-status-tbody"></tbody>
    </table>
  </div>
</section>
```

**Ubicacion sugerida:** despues de la seccion de catalogo y antes de la seccion
de paquetes (o como pestaña/pill en el header).

### Paso 2: Implementar `loadHubStatus()` en `app.js`

Agregar funcion que fetchea `hub_health.json` y pinta el dashboard:

```javascript
async function loadHubStatus() {
    const response = await fetch("data/normalized/hub_health.json");
    if (!response.ok) return;
    const health = await response.json();

    // Overall status badge
    const badge = document.getElementById("hub-status-badge");
    badge.textContent = health.overall_status;
    badge.className = `badge badge-${health.overall_status}`;

    // Summary metrics
    document.getElementById("hub-generated-at").textContent =
        formatTimestamp(health.generated_at_utc);
    document.getElementById("hub-dataset-count").textContent = health.dataset_count;
    document.getElementById("hub-ok-count").textContent = health.ok_count;
    document.getElementById("hub-warn-count").textContent = health.warn_count;
    document.getElementById("hub-error-count").textContent = health.error_count;
    document.getElementById("hub-live-count").textContent = health.live_count;
    document.getElementById("hub-fallback-count").textContent = health.fallback_count;
    document.getElementById("hub-stale-count").textContent = health.stale_count;
    document.getElementById("hub-drifted-count").textContent = health.drifted_count;

    // Per-dataset table
    const tbody = document.getElementById("hub-status-tbody");
    tbody.innerHTML = health.datasets.map(entry => {
        const severityClass = `severity-${entry.severity || "unknown"}`;
        const validationClass = `validation-${entry.validation_status || "unknown"}`;
        return `<tr class="${severityClass}">
            <td>${escapeHtml(entry.dataset)}</td>
            <td><span class="pill ${severityClass}">${entry.severity || "unknown"}</span></td>
            <td>${escapeHtml(entry.source_mode || "unknown")}</td>
            <td><span class="pill ${validationClass}">${entry.validation_status || "unknown"}</span></td>
            <td>${escapeHtml(entry.freshness_status || "unknown")}</td>
            <td>${escapeHtml(entry.coverage_status || "unknown")}</td>
            <td>${escapeHtml(entry.drift_status || "unknown")}</td>
            <td>${entry.warning_count || 0}</td>
        </tr>`;
    }).join("");
}
```

### Paso 3: Anadir CSS para estados

Agregar estilos en `index.html` (o archivo CSS separado):

```css
.severity-ok { background-color: #ecfdf5; }
.severity-warn { background-color: #fffbeb; }
.severity-error { background-color: #fef2f2; }
.pill.severity-ok { background-color: #10b981; color: white; }
.pill.severity-warn { background-color: #f59e0b; color: white; }
.pill.severity-error { background-color: #ef4444; color: white; }
.pill.validation-ok { background-color: #10b981; color: white; }
.pill.validation-error { background-color: #ef4444; color: white; }
```

### Paso 4: Llamar a `loadHubStatus()` al cargar la pagina

En el `DOMContentLoaded` existente de `app.js`, agregar llamado a la nueva funcion:

```javascript
document.addEventListener("DOMContentLoaded", () => {
    loadHubStatus();
    loadDatasetCatalog();
    // ... resto del codigo existente
});
```

### Paso 5: (Opcional) Agregar actualizacion periodica

Usar `setInterval()` para refrescar el dashboard cada 5 minutos, o agregar un
boton "Refrescar estado". Esto es relevante si el hub se reconstruye
periodicamente via CI/CD.

---

## Criterio de aceptacion

1. La landing page muestra una seccion "Estado operativo del hub" con:
   - Badge de estado general (ok/warn/error) con color.
   - Fecha de ultima actualizacion (`generated_at_utc`).
   - Conteo de datasets ok, warn, error.
   - Conteo de datasets live, fallback, stale, drifted.
2. Tabla por dataset con columnas: dataset, severidad, modo, validacion,
   frescura, cobertura, drift, advertencias.
3. Cada fila tiene color de fondo segun severidad (verde/amarillo/rojo).
4. La pagina carga sin errores si `hub_health.json` no existe (el dashboard
   simplemente no se muestra).
5. Los enlaces existentes a `hub_health.json` y `hub_status.json` se mantienen.

---

## Dependencias

- **Critica**: `hub_health.json` debe generarse correctamente en el pipeline.
  Esto ya ocurre (build_dev_db.py linea 3144-3145), pero si el pipeline falla,
  el dashboard mostrara datos ausentes.
- **Recomendada**: que la mejora #4 (estabilizacion de fallbacks) este al menos
  parcialmente completada para que el dashboard no muestre 4 datasets en fallback
  permanentemente.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|:-------|:-----------:|:-------:|:-----------|
| `hub_health.json` no existe (pipeline no ejecutado) | Baja | Medio | El dashboard se oculta graciosamente si fetch falla (responsive, no bloquea) |
| CORS blocks fetch from landing page | Baja | Alto | Los archivos estan en el mismo origen (`data/normalized/` bajo el mismo dominio) |
| Datos del health report se ven desactualizados si el pipeline no se ejecuta frecuentemente | Media | Bajo | Mostrar `generated_at_utc` prominentemente para que el usuario sepa la antiguedad |
| La tabla es muy ancha en mobile | Media | Bajo | Usar `overflow-x: auto` en el contenedor; considerar vista colapsada en mobile |

---

## Notas de disenio

### Decision: consumir `hub_health.json` existente

No se genera un nuevo artefacto. `hub_health.json` ya contiene toda la informacion
necesaria: overall_status, counts y detalle por dataset. Esto evita duplicar
logica en el pipeline.

### Alternativa considerada: generar `hub_status_summary.json`

Se considero generar un archivo resumen liviano para el frontend (solo los campos
que necesita el dashboard), pero se descarto porque `hub_health.json` es pequeño
(< 10 KB para 15 datasets) y agregar otro artefacto aumenta la complejidad del
pipeline sin beneficio significativo.

### Estructura de `hub_health.json`

El archivo tiene este schema (generado por `build_hub_health()`):
- `overall_status`: "ok" | "warn" | "error"
- `dataset_count`: int
- `ok_count`, `warn_count`, `error_count`: int
- `live_count`, `fallback_count`: int
- `stale_count`, `drifted_count`, `degraded_count`: int
- `warning_count`: int
- `generated_at_utc`: ISO datetime string
- `top_issue`: dict con dataset, severity, diagnostic_summary
- `datasets`: list de objetos con dataset, severity, source_mode,
  validation_status, freshness_status, coverage_status, drift_status, warning_count

Todo esto se mapea directamente a los elementos del dashboard.

### Extension futura

Una vez implementado el dashboard basico, se puede agregar:
- Grafico de linea de `fallback_count` a traves del tiempo (consumiendo changelog).
- Badge de "nuevo dataset" para datasets agregados recientemente.
- Enlace directo al reporte de calidad por dataset.
- Indicador de "ultima vez que paso CI/CD con exito".
