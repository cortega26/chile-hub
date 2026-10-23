# chile-hub — reutilización de datos públicos (datos.gob.cl + SGD)

> **Estado:** documento de preparación, listo para ejecución por el operador. Ninguna acción de abajo implica contactar a nadie ni pedir dinero.

## 1. Qué es chile-hub

chile-hub es una capa de acceso curada, versionada y fácil de consumir para datos públicos de Chile. Toma los datos que el Estado ya publica (en datos.gob.cl y en cada institución pública: INE, BCN, MINSAL, MINEDUC, MDS, SUBDERE, MMA, entre otras) y los deja listos para usar: normalizados sobre claves territoriales comunes (CUT), validados, versionados y con procedencia verificable, para cruzarlos en una línea de código.

chile-hub es **independiente y trabaja aguas abajo** de las instituciones públicas. No es una fuente del Estado, no está afiliado a datos.gob.cl ni a las instituciones que producen los datos, y no reemplaza a datos.gob.cl: lo complementa. Varias capas se extraen directamente de la API de datos.gob.cl (`establecimientos_salud`, `empresas`). Cada capa enlaza a su fuente pública; si un dato de chile-hub contradice a su fuente pública, vale la fuente.

## 2. Números honestos (método Anexo M, Auditoría 3)

Todas las cifras están fechadas y se refieren a contadores públicos, sin telemetría. Ninguna se presenta como medida de uso de la librería (ver §4). Los reportes vivos se enlazan en vez de hardcodear conteos.

| Señal | Valor (fecha) | Qué mide | Reporte vivo |
|:---|:---|:---|:---|
| Activaciones del bundle | ~27 al mes (169 acumuladas en GitHub Releases, 80 releases con el asset; 2026-10-15) | Proxy real de activación de la librería | `data/normalized/hub_health.md` |
| Capas públicas en el bundle | 21 (de 25 registradas en el catálogo) | Alcance del bundle publicable | `dataset_quality.md` |
| Espejo Hugging Face | 444 descargas, 0 likes (2026-10-15; 274 al 2026-09-29) | Uso vía `hf://` y subsets | `redistribution_report.md` |
| PyPI | 6.638 descargas sin espejos en 30 días (2026-09-15 → 2026-10-14), ~109 por release | Cadencia de publicación, **no** adopción | `data/normalized/hub_health.md` |
| Uso verificable | 0 organizaciones (rúbrica U/D/W, 2026-10-15) | Adopción verificable | `hub_health.md` |
| Dependents / sponsors / terceros | 0 / 0 / 0 (2026-10-15) | Contexto, no adopción | `hub_health.md` |

Veredicto de la Auditoría 3 (2026-09-30): **D** — no búsqueda activa de sponsorship; 0 evidencia de adopción verificable. Las descargas de PyPI miden la cadencia de releases, no el uso real de la librería ([`AGENTS.md` §10](https://github.com/cortega26/chile-hub/blob/main/AGENTS.md)).

> Los números se refrescan mediante el método Anexo M de la Auditoría 3 y se registran en `docs/adoption-review.md`. Este documento nunca lleva conteos sueltos sin fecha.

## 3. Las 4 acciones de operador (ROADMAP §7)

Todas las acciones se preparan aquí; ninguna se ejecuta sin el mantenedor, y ninguna implica pedir dinero ni contactar a una organización como peticionario.

### Acción 1 — Registrar chile-hub en "Reutilización" de datos.gob.cl
- **Dónde:** datos.gob.cl, sección "Reutilización" (ingreso con ClaveÚnica).
- **Método:** el mantenedor inicia sesión con ClaveÚnica y completa el formulario de reutilización del proyecto.
- **Evidencia:** URL del registro en datos.gob.cl una vez creado; captura del formulario enviado.
- **Resultado esperado:** chile-hub aparece como reutilizador visible dentro del catálogo de datos abiertos del Estado.
- **Dueño:** mantenedor (operador, cuenta propia).

### Acción 2 — Pedir la delincuencia comunal estructurada del CEAD por canales del Estado
- **Dónde:** datos.gob.cl, sección "Sugerencias"; o Ley 20.285 (acceso a la información pública).
- **Método:** formulario de sugerencias de datos.gob.cl, o solicitud escrita bajo la Ley 20.285 dirigida al CEAD/Subsecretaría de Prevención del Delito, pidiendo el dato estructurado que hoy solo se obtiene por scraping frágil.
- **Evidencia:** número de radicado o confirmación de envío de la sugerencia/solicitud.
- **Resultado esperado:** el CEAD publica o canaliza el dato estructurado, eliminando la necesidad de scrapeo y mejorando la cobertura del dataset `delincuencia_comunal`.
- **Dueño:** mantenedor (operador, cuenta propia).

### Acción 3 — Reportar el bulk 2015 de delincuencia con enlaces muertos
- **Dónde:** datos.gob.cl, botón "Notifica un error" en la ficha del dataset.
- **Método:** el mantenedor usa "Notifica un error" señalando que el bulk de delincuencia de 2015 tiene enlaces muertos.
- **Evidencia:** confirmación de reporte enviado.
- **Resultado esperado:** se corrigen o retiran los enlaces muertos del bulk 2015.
- **Dueño:** mantenedor (operador, cuenta propia).

### Acción 4 (opcional) — Presentar el proyecto a la mesa de ayuda de la Secretaría de Gobierno Digital
- **Dónde:** mesa de ayuda de la Secretaría de Gobierno Digital (SGD).
- **Método:** presentación del proyecto y consulta sobre el estado de la norma técnica de datos abiertos.
- **Evidencia:** respuesta de la mesa de ayuda.
- **Resultado esperado:** orientación sobre la norma técnica de datos abiertos y posible visibilidad del proyecto dentro del ecosistema de datos públicos del Estado.
- **Dueño:** mantenedor (operador, cuenta propia).

> Ninguna de estas acciones pide dinero, tiers, ni propuesta de grant. El estado vigente de sostenibilidad es HOLD / sin búsqueda activa (revisión 2026-11-01).

## 4. Lista de lo que nunca se dice (AGENTS.md §10)

- No presentar las descargas de PyPI como medida de adopción: miden la cadencia de releases, no el uso real de la librería.
- No prometer acceso de pago ni datos detrás de muro (principio 4: lo abierto sigue abierto).
- No afirmar que chile-hub es una fuente del Estado ni está afiliado a datos.gob.cl ni a las instituciones públicas (es un reutilizador independiente, aguas abajo).
- No scrapeazar donde existe un canal del Estado (principio 3: buen vecino del ecosistema); los datos que faltan se piden por esos mismos canales.
- No publicar datos personales de contactos ni términos comerciales de terceros (Ley 21.719).

## 5. Referencias

- [`docs/sostenibilidad/README.md`](sostenibilidad/README.md) — estado vigente de sostenibilidad y cronología de decisiones.
- [`docs/adoption-review.md`](adoption-review.md) — registro de métricas públicas (método Anexo M).
- [`docs/adoption-funnel.md`](adoption-funnel.md) — etapas y frases permitidas del embudo de adopción.
- [`docs/product-spec.md`](product-spec.md) — misión, visión y "quién hace qué" (ADR-023).
- [`AGENTS.md` §10](AGENTS.md) — antipatrones: nunca presentar PyPI como adopción.
- [`ROADMAP.md` §7](ROADMAP.md) — las cuatro acciones de operador preparadas en este documento.
