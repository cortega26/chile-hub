# Degradación de `finanzas_municipales` a candidate permanente

**Dataset:** `finanzas_municipales`
**Fuente:** SINIM (Sistema Nacional de Información Municipal) / SUBDERE
**Fecha de evaluación:** 2026-06-19
**Decisión:** Mantener como `candidate` — no viable para extracción live automatizada

---

## Análisis de la fuente

### Portal evaluado

- **URL principal:** `https://datos.sinim.gov.cl/`
- **Página de datos municipales:** `https://datos.sinim.gov.cl/datos_municipales.php`
- **Página de clasificador presupuestario:** `https://datos.sinim.gov.cl/clasificador_presupuestario.php`

### Hallazgos

1. **Sitio web dinámico con JavaScript/AJAX:** El portal SINIM es una aplicación
   PHP que carga los datos mediante llamadas AJAX después del renderizado inicial.
   Las tablas de datos no están presentes en el HTML estático.

2. **Sin API pública documentada:** No existe un endpoint REST, CSV descargable
   vía GET, ni API documentada para obtener datos de finanzas municipales.

3. **Descarga de Excel requiere interacción de formulario:** El sitio ofrece
   exportación a Excel mediante un flujo que requiere:
   - Sesión PHP (cookies)
   - Envío de formulario POST con filtros (área, año, región, municipio)
   - El Excel se genera del lado servidor y se descarga como respuesta al POST

4. **No catalogado en datos.gob.cl:** El CKAN de datos abiertos de Chile no
   contiene los datasets de finanzas municipales del SINIM. Se encontraron solo
   3 datasets irrelevantes (datos de municipios individuales, PDFs).

### Extractor actual

El extractor en `src/extractors/sinim_finanzas_extractor.py`:
- Usa `fetch_url_snapshot()` para guardar un snapshot HTML de la landing page
- **No procesa el contenido** (la respuesta HTML no contiene datos tabulares)
- Siempre retorna `FALLBACK_ROWS`: 3 filas hardcoded para 2 comunas (Santiago,
  Viña del Mar, Concepción) con datos del año 2024
- `source_mode`: ahora correctamente reporta `"fallback"` (corregido en v1.2.0)

---

## Razones para la degradación

| Factor | Evaluación |
|:---|:---|
| **Estabilidad de la fuente** | ❌ Requiere sesión + POST + JS. Cualquier cambio en el sitio rompe la extracción. |
| **API disponible** | ❌ No existe API pública. |
| **Descarga directa** | ❌ No hay CSV/Excel descargable vía GET. |
| **Scraping viable** | ❌ Frágil. Requiere simulación de formulario y manejo de sesiones PHP. |
| **Fuente alternativa** | ❌ No encontrada en datos.gob.cl ni en SUBDERE directa. |
| **Costo de mantenimiento** | ❌ Alto. Cada cambio en el sitio SINIM requiere re-ingeniería del scraper. |

---

## Impacto en el ecosistema

- `finanzas_municipales` es upstream de `perfil_territorial_comunal`
- `perfil_territorial_comunal` deberá manejar la ausencia de datos municipales
  con valores nulos o métricas no disponibles para ese campo

---

## Fuentes alternativas potenciales (investigación futura)

1. **SUBDERE directa:** La Subsecretaría de Desarrollo Regional publica
   estadísticas municipales. Explorar `https://www.subdere.gov.cl/`.
2. **Portal de Transparencia:** Los municipios reportan datos presupuestarios
   al Portal de Transparencia. Evaluar si existe un dataset consolidado.
3. **SINIM vía scraper con navegador headless:** Usar Playwright/Selenium para
   automatizar la descarga del Excel. Alto costo de mantenimiento.
4. **Colaboración externa:** Si un contribuyente externo ofrece mantener un
   adaptador SINIM, el dataset podría volver a `active`.

---

## Estado final en source_registry.json

```json
{
  "source_id": "sinim_finanzas_municipales",
  "live_extractor_status": "fallback_only",
  "maturity_status": "candidate",
  "publication_track": "candidate",
  "degradation_reason": "sinim_portal_requires_js_session_no_api_available",
  "next_action": "Buscar fuente alternativa: SUBDERE directa, Portal de Transparencia, o datos.gob.cl"
}
```
