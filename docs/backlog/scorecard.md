# Scorecard de Mejoras Estratégicas — ChileHub

**Ultima actualizacion:** 2026-06-29 (backlog completado 7/7 — ver Semana 4). Documento cerrado como registro historico el 2026-07-18; el seguimiento de mejoras activas vive en `plans/README.md`.
**Revision semanal:** cerrada (backlog completado — ya no aplica)
**Version del proyecto:** ver `pyproject.toml` (fuente unica de verdad) · etapa Alpha
**Estado general:** Backlog completado · Progreso total: 100% (7/7 completadas)

---

## Resumen ejecutivo

> **Foto de partida (2026-06-18), conservada como registro historico.** Todos
> los problemas descritos abajo fueron resueltos por las 7 mejoras del backlog
> (completado 2026-06-29, 7/7 — ver "Revisiones semanales" y
> `docs/backlog/NEXT_STEPS.md`).

ChileHub (Alpha) es una libreria Python open-source que cura, normaliza, valida
y publica ~15 datasets oficiales de Chile. Al crear este scorecard el proyecto
se encontraba en etapa temprana:
el modulo `build_dev_db.py` concentraba 3206 lineas (God module), la validacion de
contratos JSON Schema existia pero solo se ejecutaba en `scripts/verify_pipeline.py`
(fuera del pipeline principal), los nombres de dataset se pasaban como strings magicos
sin constantes tipadas, 4 datasets operaban en modo fallback no estabilizado, y la
landing page no mostraba el estado operativo en tiempo real.

Las 7 mejoras que siguen atacaron estos puntos en orden de impacto estrategico —
todas completadas (7/7).

---

## Scorecard

| # | Mejora | Impacto | Esfuerzo | Riesgo | Estado | Target | Dependencias |
|:--:|:---|:--:|:--:|:--:|:---|:---|:---|
| 1 | Refactorizar `build_dev_db.py` en modulos `src/builders/` | Alto | Alto | Medio | Completado | 2026-06-20 | Tests de validacion existentes (`tests/test_pipeline_logic.py`) |
| 2 | Validacion de contratos JSON Schema en runtime | Alto | Medio | Bajo | Completado | 2026-06-29 | Quick win tests (`tests/test_validation.py`) |
| 3 | Constantes de datasets como enum (`Dataset`) | Medio | Medio | Bajo | Completado | 2026-06-29 | — |
| 4 | Estabilizacion de datasets en modo fallback | Alto | Alto | Medio | Completado | 2026-06-19 | Acceso a fuentes origen (URLs externas) |
| 5 | Dashboard publico de salud operativa del hub | Medio | Medio | Bajo | Completado | 2026-06-29 | #4 completado (para no mostrar falsos positivos) |
| 6 | Robustecer manejo de errores en API publica | Medio | Bajo | Bajo | Completado | 2026-06-19 | — |
| 7 | Nuevas capacidades de API (cruces, validacion, busqueda) | Medio | Medio | Bajo | Completado | 2026-06-29 | #6 completado |

---

## Metricas de avance

| # | Mejora | Disenio | Prototipo | Implementacion | Tests | Documentacion | Despliegue |
|:--:|:---|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Refactor `build_dev_db.py` | 100% | 100% | 100% | 100% | 100% | 100% |
| 2 | Validacion contratos runtime | 100% | 100% | 100% | 100% | 100% | 100% |
| 3 | Constantes datasets | 100% | 100% | 100% | 100% | 100% | 100% |
| 4 | Estabilizacion fallbacks | 100% | 100% | 100% | 100% | 100% | 100% |
| 5 | Dashboard salud | 100% | 100% | 100% | — | — | 100% |
| 6 | API error handling | 100% | 100% | 100% | 100% | 100% | 100% |
| 7 | API capacidades | 100% | 100% | 100% | 100% | 100% | 100% |

**Progreso total:** 100% (7/7 completadas — todas las mejoras del backlog implementadas)

---

## Revisiones semanales

### Semana 1 — 2026-06-18
- Scorecard creado. Pendiente de planificacion.

### Semana 2 — 2026-06-19
- **#4 Estabilizacion fallbacks — Diagnostico e infraestructura completados:**
  - Corregido `source_mode` engañoso en `source_adapter.py` (requiere `data_parsed=True` explicito)
  - URLs alineadas entre extractores y `source_registry.json`
  - SINIM `finanzas_municipales` degradado a candidate permanente (portal requiere JS/POST, sin API)
  - MINEDUC `resultados_educacionales`: URLs de descarga directa confirmadas (Desvinculacion XLSX + Rendimiento RARs)
  - SIEDU `indicadores_urbanos_siedu`: confirmado que el Excel esta tras JS tabs, inaccesible via HTTP fetch
  - 4 Issues de GitHub actualizados con diagnosticos corregidos
  - 358 tests pasan sin regresiones
  - Ver `docs/backlog/NEXT_STEPS.md` para plan de siguientes pasos.
- **#4 MINEDUC completado — Issue #6 cerrado:**
  - Extractor live implementado: `Rendimiento_2024.rar` (42MB) → CSV 3.5M filas → 345 registros por comuna
  - `source_mode: "live"`, todos los campos del contrato cubiertos desde una sola fuente RAR
  - `resultados_educacionales` promovido a `stable_publishable` en `source_registry.json`
- **#4 SIEDU completado — Issue #7 cerrado:**
  - Extractor live implementado: `matriz-siedu-publicacion.xlsm` (504 KB, INE) → 5 hojas → 6.701 registros
  - 117 comunas urbanas, 68 indicadores, deduplicado por año más reciente
  - `indicadores_urbanos_siedu` promovido a `stable_publishable` en `source_registry.json`
  - `hub_health.json`: `fallback_count=0`, `live_count=15` — todos los datasets en modo live
  - Bundle público: 13 datasets (antes 12), 2 candidatos restantes
  - 410 tests pasan sin regresiones
- **#4 Issue paraguas cerrado** — todos los datasets estabilizados
- Proxima revision: 2026-06-26

### Semana 3 — 2026-06-20
- **#1 Refactor `build_dev_db.py` — Completado:**
  - God module descompuesto de 2867 a 668 lineas (solo orquestacion).
  - 9 modulos nuevos en `src/builders/`: `_shared`, `io_utils`, `formats`, `metadata`,
    `reports`, `artifacts`, `datasets`, `catalog`, `landing`.
  - `main()` descompuesto en 5 subfunciones (`_load_inputs`, `_compute_validations`,
    `_write_data_artifacts`, `build_dataset_metadata`, `_generate_reports`) + orquestador delgado.
  - Compatibilidad preservada: `DATASET_CATALOG_CONFIG` y funciones publicas re-exportadas
    desde `build_dev_db` (no se rompe `scripts/verify_pipeline.py` ni los tests).
  - Verificacion: 410 tests pasan, lint limpio, y el pipeline end-to-end produce
    artefactos byte-identicos a la linea base salvo timestamps (criterio de aceptacion #5).
  - Bug atrapado y corregido durante la verificacion: `return` perdido en
    `attach_publishable_package_to_manifest` (el camino feliz de `main()` no tenia cobertura de tests).
- Proxima revision: 2026-06-26

### Semana 4 — 2026-06-29
- **#2 Validacion contratos JSON Schema en runtime — Completado:**
  - Nuevo modulo `src/chile_hub/contracts.py` con `verify_dataset_contract()` y `contract_type()`
  - `scripts/verify_pipeline.py` delegado al modulo de libreria (retrocompatible)
  - `ChileHub.validate_dataset()` + `load_polars(validate=True)` + CLI `validate <dataset>`
  - 17 tests nuevos en `test_validation.py` y `test_chile_hub.py`
  - 480 tests pasan sin regresiones
- **#3 Constantes de datasets como enum `Dataset` — Completado:**
  - Nuevo `src/chile_hub/datasets.py` con `Dataset(str, Enum)` y `from_string()` con sugerencias
  - API publica actualizada: `get_dataset()`, `load_polars()`, `get_output_path()`, etc. aceptan `str | Dataset`
  - 10 tests nuevos en `DatasetEnumTests`
  - 490 tests pasan sin regresiones
- **#5 Dashboard publico de salud — Completado:**
  - Nueva seccion "Estado operativo del hub" en `index.html` con CSS responsivo
  - `loadHubHealth()` en `app.js` que consume `hub_health.json` y renderiza resumen + tabla
  - Degradación graceful: si no hay datos, la sección se oculta
  - 169 tests pasan sin regresiones
- **Backlog estrategico completado al 100%** — 7/7 mejoras implementadas

---

## Archivos de backlog

| # | Archivo |
|:--:|:---|
| 1 | `docs/backlog/01-refactor-build-dev-db.md` |
| 2 | `docs/backlog/02-contratos-automatizados-runtime.md` |
| 3 | `docs/backlog/03-constantes-de-datasets.md` |
| 4 | `docs/backlog/04-estabilizacion-fallbacks.md` |
| 5 | `docs/backlog/05-dashboard-publico-salud.md` |
| 6 | `docs/backlog/06-api-error-handling.md` |
| 7 | `docs/backlog/07-api-capabilities.md` |
| — | `docs/backlog/NEXT_STEPS.md` — Hoja de ruta y próximos pasos |
