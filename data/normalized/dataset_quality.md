# chile-hub — Calidad de datasets

- `generated_at_utc`: `2026-06-18T18:20:03.516188+00:00`
- `dataset_count`: `15`
- `average_score`: `92.1`
- `grade_distribution`: A=12, B=3, C=0, D=0, F=0

| Dataset | Nota | Valid | Contrato | Madurez | Frescura | Cobert | Reúso | Bloqueadores |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `censo_comunal` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `censo_hogares_viviendas` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `comunas` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `comunas_enriquecidas` | **A** (90.0) | 100 | 100 | 50 | 100 | 100 | 100 | Madurez de fuente incompleta |
| `distritos_electorales` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `empresas` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `establecimientos_educacionales` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `establecimientos_salud` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `finanzas_municipales` | **B** (75.0) | 100 | 100 | 50 | 100 | 0 | 50 | Fuente en fallback_only — Configure stable direct SINIM export and replace curated fallback rows.; Cobertura not_applicable; Reutilización: public-api-review-terms |
| `indicadores` | **A** (90.0) | 100 | 100 | 100 | 100 | 0 | 100 | Cobertura not_applicable |
| `indicadores_urbanos_siedu` | **B** (87.0) | 100 | 100 | 50 | 100 | 70 | 100 | Fuente en fallback_only — Replace partial fallback with stable official SIEDU export.; Cobertura partial |
| `perfil_territorial_comunal` | **A** (90.0) | 100 | 100 | 50 | 100 | 100 | 100 | Fuente no lista para live; Capa derivada — depende de datasets upstream no publicables |
| `provincias` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `regiones` | **A** (100.0) | 100 | 100 | 100 | 100 | 100 | 100 | — |
| `resultados_educacionales` | **B** (80.0) | 100 | 100 | 50 | 100 | 0 | 100 | Fuente en fallback_only — Replace curated fallback with stable official aggregate export.; Cobertura not_applicable |
