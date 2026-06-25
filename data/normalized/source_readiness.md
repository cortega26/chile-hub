# chile-hub — Madurez de fuente

- `generated_at_utc`: `2026-06-25T11:01:38.705135+00:00`
- `stable_count`: `13`
- `candidate_count`: `2`
- `experimental_count`: `0`
- `deprecated_count`: `0`
- `live_ready_count`: `13`
- `fallback_only_count`: `1`
- `publish_blocking_count`: `15`

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
| `finanzas_municipales` | `candidate` | `sinim_finanzas_municipales` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Buscar fuente alternativa: SUBDERE directa, Portal de Transparencia, o datos.gob.cl. Ver docs/datasets/finanzas_municipales-degradacion.md. |
| `resultados_educacionales` | `stable` | `mineduc_resultados_educacionales` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Actualizar URL anualmente (año en nombre de archivo). Verificar columnas SIT_FIN_R si MINEDUC cambia metodología. |
| `indicadores_urbanos_siedu` | `stable` | `ine_siedu_indicadores` | `live` | `✓` | `permitido` | `✓` | `implemented` | `—` | Monitorear si INE publica una 6ta medición (post-2022) y actualizar URL y SHEET_YEARS. |
| `perfil_territorial_comunal` | `candidate` | `chile_hub_perfil_territorial` | `fallback` | `✗` | `permitido` | `✓` | `derived` | `—` | Track readiness inherited from upstream component datasets. |
| `empresas` | `stable` | `ministerio_economia_res` | `live` | `✓` | `no` | `✓` | `implemented` | `—` | Keep large-output behavior documented and verify Parquet-first consumption. |
