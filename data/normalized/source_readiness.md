# chile-hub — Madurez de fuente

- `generated_at_utc`: `2026-06-18T18:20:03.516188+00:00`
- `stable_count`: `11`
- `candidate_count`: `4`
- `experimental_count`: `0`
- `deprecated_count`: `0`
- `live_ready_count`: `11`
- `fallback_only_count`: `3`
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
| `finanzas_municipales` | `candidate` | `sinim_finanzas_municipales` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Configure stable direct SINIM export and replace curated fallback rows. |
| `resultados_educacionales` | `candidate` | `mineduc_resultados_educacionales` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Replace curated fallback with stable official aggregate export. |
| `indicadores_urbanos_siedu` | `candidate` | `ine_siedu_indicadores` | `fallback` | `✗` | `permitido` | `✓` | `fallback_only` | `—` | Replace partial fallback with stable official SIEDU export. |
| `perfil_territorial_comunal` | `candidate` | `chile_hub_perfil_territorial` | `fallback` | `✗` | `permitido` | `✓` | `derived` | `—` | Track readiness inherited from upstream component datasets. |
| `empresas` | `stable` | `ministerio_economia_res` | `live` | `✓` | `no` | `✓` | `implemented` | `—` | Keep large-output behavior documented and verify Parquet-first consumption. |
