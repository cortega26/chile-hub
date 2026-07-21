# chile-hub — Madurez de fuente

- `generated_at_utc`: `2026-07-21T10:44:52.718145+00:00`
- `stable_count`: `17`
- `candidate_count`: `3`
- `experimental_count`: `0`
- `deprecated_count`: `1`
- `live_ready_count`: `17`
- `fallback_only_count`: `1`
- `publish_blocking_count`: `19`

| Dataset | Madurez | Source ID | Modo | Live Ready | Fallback | Bloquea Pub | Extractor | Estancado | Próxima acción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `regiones` | `stable` | `bcn_regiones` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Maintain DPA cardinality and CUT format checks. |
| `provincias` | `stable` | `bcn_provincias` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Maintain DPA cardinality and CUT format checks. |
| `comunas` | `stable` | `bcn_comunas` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Maintain 346-comuna invariant and enrichment references. |
| `comunas_enriquecidas` | `stable` | `bcn_comunas_enriquecidas` | `live` | `✓` | `permitido` | `✓` | `derived` | `—` | Keep derived schema aligned with comunas. |
| `indicadores` | `stable` | `mindicador_indicadores` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Monitor empty monthly IPC responses and published backfill behavior. |
| `censo_comunal` | `stable` | `ine_censo_comunal_2024` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Keep decennial source and schema documentation current. |
| `censo_hogares_viviendas` | `stable` | `ine_censo_hogares_viviendas_2024` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Keep decennial source and schema documentation current. |
| `establecimientos_salud` | `stable` | `minsal_establecimientos_salud` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Monitor monthly source freshness and geocoding coverage. |
| `distritos_electorales` | `stable` | `bcn_servel_distritos` | `live` | `✓` | `no` | `✓` | `implemented` | `—` | Update only when electoral district law changes. |
| `establecimientos_educacionales` | `stable` | `mineduc_establecimientos` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Monitor annual source package and RAR extraction dependency. |
| `finanzas_municipales` | `stable` | `sinim_finanzas_municipales` | `monthly` | `✓` | `permitido` | `—` | `implemented` | `—` | Fase 3.2 PoC exitoso: extractor live implementado (sinim_finanzas_live_extractor.py). Cobertura 345/346 municipios (2024). Pendiente: workflow mensual (3.3) y metadata de cadencia (3.4). |
| `resultados_educacionales` | `stable` | `mineduc_resultados_educacionales` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Actualizar URL anualmente (año en nombre de archivo). Verificar columnas SIT_FIN_R si MINEDUC cambia metodología. |
| `indicadores_urbanos_siedu` | `stable` | `ine_siedu_indicadores` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Monitorear si INE publica una 6ta medición (post-2022) y actualizar URL y SHEET_YEARS. |
| `perfil_territorial_comunal` | `candidate` | `chile_hub_perfil_territorial` | `fallback` | `✗` | `permitido` | `✓` | `derived` | `—` | Track readiness inherited from upstream component datasets. |
| `empresas` | `stable` | `ministerio_economia_res` | `live` | `✓` | `no` | `✓` | `implemented` | `—` | Keep large-output behavior documented and verify Parquet-first consumption. |
| `pobreza_comunal` | `stable` | `mds_pobreza_comunal` | `live` | `✓` | `permitido` | `—` | `implemented` | `—` | Monitorear publicación de próxima ronda CASEN (2024-2025). |
| `consumo_electrico_comunal` | `deprecated` | `cne_consumo_electrico_comunal` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Fuente confirmada caída de forma permanente (investigado 2026-07-07): CNE decomisionó el catálogo Junar de energiaabierta.cl; la página del dataset no ofrece archivo ni API de reemplazo (el enlace API del sitio apunta a /visualizaciones/en-mantencion/). El dataset nunca tuvo un fetch en vivo exitoso — solo publica FALLBACK_ROWS de muestra. Degradado a deprecated/candidate por AGENTS.md §6 (protocolo de fuente permanentemente caída); reevaluar solo si CNE publica un reemplazo oficial. |
| `delincuencia_comunal` | `candidate` | `cead_delincuencia_comunal` | `not_built` | `✗` | `permitido` | `✓` | `implemented` | `—` | Monitorear estabilidad del scraping; buscar fuente estructurada oficial (datos.gob.cl, export CEAD). Degradar a rejected si no madura para review_by. |
| `partidos_politicos` | `stable` | `camara_partidos_politicos` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | estado_legal/fecha_constitucion completados desde SERVEL (15/36 partidos matcheados por nombre; el resto son históricos no listados en SERVEL). ambito (nacional/regional) queda nullable: no se encontró esa señal en ninguna fuente institucional disponible. |
| `autoridades_electas` | `stable` | `camara_senado_autoridades_electas` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | codigo_region/periodo de senadores completados desde senado.cl (REGION/PERIODOS). gobernador_regional y alcalde viven en el dataset segregado autoridades_locales (CC-BY-SA, candidate) por decisión de licencia. |
| `autoridades_locales` | `candidate` | `wikipedia_autoridades_locales` | `not_built` | `✗` | `permitido` | `✓` | `implemented` | `—` | Ampliar cobertura de alcaldes (~165/345 identificados; ~121 sin página en Wikipedia, ~59 sin marca de vigencia clara); buscar fuente redistribuible no-share-alike para promover a stable_publishable. |
