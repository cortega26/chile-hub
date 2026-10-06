# chile-hub — Madurez de fuente

- `generated_at_utc`: `2026-10-06T16:28:11.793983+00:00`
- `stable_count`: `21`
- `candidate_count`: `2`
- `experimental_count`: `0`
- `deprecated_count`: `2`
- `live_ready_count`: `20`
- `fallback_only_count`: `2`
- `publish_blocking_count`: `22`
- `review_approaching_count`: `22`
- `review_due_count`: `0`

| Dataset | Madurez | Source ID | Modo | Live Ready | Fallback | Bloquea Pub | Extractor | Estancado | Próxima acción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `regiones` | `stable` | `bcn_regiones` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Maintain DPA cardinality and CUT format checks. |
| `provincias` | `stable` | `bcn_provincias` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Maintain DPA cardinality and CUT format checks. |
| `comunas` | `stable` | `bcn_comunas` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Maintain 346-comuna invariant and enrichment references. |
| `comunas_enriquecidas` | `stable` | `bcn_comunas_enriquecidas` | `live` | `✓` | `permitido` | `✓` | `derived` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Keep derived schema aligned with comunas. |
| `indicadores` | `stable` | `mindicador_indicadores` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitor empty monthly IPC responses and published backfill behavior. |
| `censo_comunal` | `stable` | `ine_censo_comunal_2024` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Keep decennial source and schema documentation current. |
| `censo_hogares_viviendas` | `stable` | `ine_censo_hogares_viviendas_2024` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Keep decennial source and schema documentation current. |
| `establecimientos_salud` | `stable` | `minsal_establecimientos_salud` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitor monthly source freshness and geocoding coverage. |
| `distritos_electorales` | `stable` | `bcn_servel_distritos` | `live` | `✓` | `no` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Update only when electoral district law changes. |
| `establecimientos_educacionales` | `stable` | `mineduc_establecimientos` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitor annual source package and RAR extraction dependency. |
| `finanzas_municipales` | `stable` | `sinim_finanzas_municipales` | `monthly` | `✓` | `permitido` | `—` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Fase 3.2 PoC exitoso: extractor live implementado (sinim_finanzas_live_extractor.py). Cobertura 345/346 municipios (2024). Pendiente: workflow mensual (3.3) y metadata de cadencia (3.4). |
| `resultados_educacionales` | `stable` | `mineduc_resultados_educacionales` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Actualizar URL anualmente (año en nombre de archivo). Verificar columnas SIT_FIN_R si MINEDUC cambia metodología. |
| `indicadores_urbanos_siedu` | `stable` | `ine_siedu_indicadores` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitorear si INE publica una 6ta medición (post-2022) y actualizar URL y SHEET_YEARS. |
| `perfil_territorial_comunal` | `stable` | `chile_hub_perfil_territorial` | `live` | `✗` | `permitido` | `—` | `derived` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Track readiness inherited from upstream component datasets (12 upstreams desde 2026-09: +estadisticas_vitales, +permisos_edificacion, +calidad_aire). |
| `empresas` | `stable` | `ministerio_economia_res` | `live` | `✓` | `no` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Keep large-output behavior documented and verify Parquet-first consumption. |
| `pobreza_comunal` | `stable` | `mds_pobreza_comunal` | `live` | `✓` | `permitido` | `—` | `implemented` | `—` | Monitorear publicación de próxima ronda CASEN (2024-2025). |
| `consumo_electrico_comunal` | `deprecated` | `cne_consumo_electrico_comunal` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Fuente confirmada caída de forma permanente (investigado 2026-07-07): CNE decomisionó el catálogo Junar de energiaabierta.cl; la página del dataset no ofrece archivo ni API de reemplazo (el enlace API del sitio apunta a /visualizaciones/en-mantencion/). El dataset nunca tuvo un fetch en vivo exitoso — solo publica FALLBACK_ROWS de muestra. Degradado a deprecated/candidate por AGENTS.md §6 (protocolo de fuente permanentemente caída); reevaluar solo si CNE publica un reemplazo oficial. |
| `geometria_comunal` | `candidate` | `bcn_arcgis_geometria_comunal` | `not_built` | `✗` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-10-21 — 14 días. Cobertura 345/346 (falta codigo_comuna=12202/Antártica, hueco conocido de la fuente BCN — ver ADR-012). Evaluar promoción a stable_publishable una vez confirmada cadencia de refresco y estabilidad del endpoint ArcGIS (region 12/Magallanes requiere fallback comuna-por-comuna por payload combinado grande). |
| `delincuencia_comunal` | `deprecated` | `cead_delincuencia_comunal` | `not_built` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | DEGRADADO a rejected 2026-09-15 (review anticipada): en 90+ días no apareció descarga estructurada oficial (datos.gob.cl solo tiene bulk 2015 con links muertos; portal CEAD con protección anti-bots y solo PDF/presentaciones) y el dataset nunca fue redistribuible. Extractor neutralizado (NotImplementedError) y removido del scrape mensual. Reevaluar solo si el CEAD publica descarga oficial. |
| `partidos_politicos` | `stable` | `camara_partidos_politicos` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Review 2026-10-05: extractor live y validación OK; último build publicó 37 registros, 16/37 con estado_legal vía SERVEL. La variación del roster es esperable porque Cámara incluye partidos vigentes e históricos. Mantener stable_publishable; ambito sigue nullable por falta de señal institucional. Próxima revisión 2026-12-31. |
| `autoridades_electas` | `stable` | `camara_senado_autoridades_electas` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Review 2026-10-05: extractor live y validación OK con 205/205 registros (155 diputados + 50 senadores); región y período de senadores continúan poblados desde senado.cl. Mantener stable_publishable. Próxima revisión 2026-12-31. |
| `autoridades_locales` | `candidate` | `wikipedia_autoridades_locales` | `not_built` | `✗` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Review 2026-10-05: la brecha de alcaldes quedó resuelta al migrar la fuente primaria a BCN SIIT (346/346 comunas). El único bloqueo para promover a stable_publishable es la licencia CC-BY-SA de los gobernadores obtenidos desde Wikipedia; buscar fuente institucional no-share-alike o definir publicación segregada compatible. Próxima revisión 2026-12-31. |
| `estadisticas_vitales` | `stable` | `ine_estadisticas_vitales` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitorear publicación del anuario 2024 (el extractor lo incorpora solo). |
| `permisos_edificacion` | `stable` | `minvu_permisos_edificacion` | `monthly` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Monitorear que el biblionumber 25583 siga resolviendo al XLSX anual vigente. |
| `calidad_aire` | `stable` | `mma_sinca_calidad_aire` | `live` | `✓` | `permitido` | `✓` | `implemented` | `⏳` | ⏳ REVIEW BY 2026-12-31 — 85 días. Vigilar estabilidad del endpoint listadomapa2k19 y crecimiento de la serie incremental. |
