# chile-hub — Calidad de datasets

- `generated_at_utc`: `2026-07-20T01:57:09.237058+00:00`
- `dataset_count`: `19`
- `average_score`: `94.2`
- `grade_distribution`: A=18, B=1, C=0, D=0, F=0

| Dataset | Nota | Valid | Contrato | Madurez | Frescura | Cobert | Reúso | Bloqueadores |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `autoridades_electas` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `censo_comunal` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `censo_hogares_viviendas` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `comunas` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `comunas_enriquecidas` | **A** (90.0) | 100 | 100 | 50 | 100 | 100 | 100 | Madurez de fuente incompleta |
| `consumo_electrico_comunal` | **B** (80.0) | 100 | 100 | 50 | 100 | 0 | 100 | Fuente en fallback_only — Fuente confirmada caída de forma permanente (investigado 2026-07-07): CNE decomisionó el catálogo Junar de energiaabierta.cl; la página del dataset no ofrece archivo ni API de reemplazo (el enlace API del sitio apunta a /visualizaciones/en-mantencion/). El dataset nunca tuvo un fetch en vivo exitoso — solo publica FALLBACK_ROWS de muestra. Degradado a deprecated/candidate por AGENTS.md §6 (protocolo de fuente permanentemente caída); reevaluar solo si CNE publica un reemplazo oficial.; Cobertura not_applicable |
| `distritos_electorales` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `empresas` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `establecimientos_educacionales` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `establecimientos_salud` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `finanzas_municipales` | **A** (92.0) | 100 | 100 | 100 | 100 | 70 | 50 | Cobertura partial; Reutilización: public-api-review-terms |
| `indicadores` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `indicadores_urbanos_siedu` | **A** (97.0) | 100 | 100 | 100 | 100 | 70 | 100 | Cobertura partial |
| `partidos_politicos` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `perfil_territorial_comunal` | **A** (90.0) | 100 | 100 | 50 | 100 | 100 | 100 | Fuente no lista para live; Capa derivada — depende de datasets upstream no publicables |
| `pobreza_comunal` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `provincias` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `regiones` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `resultados_educacionales` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
