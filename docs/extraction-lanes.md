# Carriles de extracción

Cómo se actualiza cada dataset y con qué cadencia. Resuelve el hueco de
documentación del split diario-vs-mensual (TECHDEBT-06): la fuente de verdad
operativa son los workflows, esta página es la vista de referencia.

## Los cuatro carriles

| Carril | Workflow / comando | Cadencia | Datasets |
|:---|:---|:---|:---|
| **Diario** | `make extract` · job `build-and-test` de `pipeline-check.yml` | diaria (10:00 UTC) | regiones, provincias, comunas, comunas_enriquecidas, indicadores, censo_comunal, censo_hogares_viviendas, establecimientos_salud, distritos_electorales, establecimientos_educacionales, resultados_educacionales, indicadores_urbanos_siedu, empresas, pobreza_comunal, consumo_electrico_comunal, partidos_politicos, autoridades_electas |
| **Mensual** | `monthly-scrape.yml` | mensual (manual + workflow_dispatch) | finanzas_municipales (`sinim_finanzas_live_extractor.py`), delincuencia_comunal (`cead_delincuencia_live_extractor.py`) |
| **Ad hoc / candidate** | manual (workflow_dispatch, sin schedule) | a demanda | geometria_comunal (`geometria-comunal.yml`), autoridades_locales (BCN SIIT + Wikipedia, sin cadencia automática) |
| **Stub (no operativo)** | — | nunca desde jobs programados | `sinim_finanzas_extractor.py` es un fallback de desarrollo; el job diario **no** debe invocarlo (guardrail: `tests/test_ci_config.py::SinimDailyJobGuardrailTests`) |

## Reglas

1. **Un extractor por carril.** Los extractores diarios corren en `make extract`;
   los mensuales, en `monthly-scrape.yml`; los candidate, en su workflow propio.
   Nunca mezclar un extractor en dos carriles.
2. **El override INE es parte del carril diario de `indicadores`.** Cuando
   mindicador.cl no entrega el IPC del año en curso, `ine_ipc.py` scrapea la
   variación mensual de la página pública del INE (fuente autoritativa, Plan
   069) ANTES de recurrir al backfill — el publish diario depende de ese
   parseo HTML, y su edad está gateada (ADR-016).
3. **El stub SINIM nunca corre en un job programado.** `sinim_finanzas_extractor.py`
   siempre escribe 3 filas de muestra; el snapshot real mensual vive versionado en
   git y lo restaura `pipeline-check.yml` tras un restore de caché obsoleto.
4. **Degradación de `autoridades_electas` sin scrapling.** En CI este extractor se
   invoca con `uv run --no-project --with "scrapling[fetchers]"` (entorno efímero,
   conflicto de `click` con el extra `dev` — ver `pyproject.toml`). Sin scrapling
   degrada a 155 registros (0 senadores) y rompe el gate "Check build-synced files".
5. **`perfil_territorial_comunal` no tiene extractor**: es derivado en
   `build_dev_db.py` a partir de otros datasets.
6. **`geometria_comunal` es candidate (ADR-012)**: su artefacto se publica desde
   `geometria-comunal.yml`, fuera del bundle estable y del guard de 500 KB.

## Cómo verificar el carril de un dataset

La fuente de verdad del mapeo dataset↔extractor es `data/dataset_catalog_config.json`
(campo `extractor`); el carril de publicación (`candidate`/`stable_publishable`),
`maturity_status` y `confidence_tier` viven en `data/source_registry.json`.
