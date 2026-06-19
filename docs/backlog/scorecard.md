# Scorecard de Mejoras Estratégicas — ChileHub

**Ultima actualizacion:** 2026-06-19
**Revision semanal:** viernes
**Version del proyecto:** ver `pyproject.toml` (fuente unica de verdad) · etapa Alpha
**Estado general:** En desarrollo activo · Progreso total: 21% (1/7 completada, 1/7 en progreso)

---

## Resumen ejecutivo

ChileHub (Alpha) es una libreria Python open-source que cura, normaliza, valida
y publica ~15 datasets oficiales de Chile. El proyecto se encuentra en etapa temprana:
el modulo `build_dev_db.py` concentra 3206 lineas (God module), la validacion de
contratos JSON Schema existe pero solo se ejecuta en `scripts/verify_pipeline.py`
(fuera del pipeline principal), los nombres de dataset se pasan como strings magicos
sin constantes tipadas, 4 datasets operan en modo fallback no estabilizado, y la
landing page no muestra el estado operativo en tiempo real.

Las 5 mejoras que siguen atacan estos puntos en orden de impacto estrategico.

---

## Scorecard

| # | Mejora | Impacto | Esfuerzo | Riesgo | Estado | Target | Dependencias |
|:--:|:---|:--:|:--:|:--:|:---|:---|:---|
| 1 | Refactorizar `build_dev_db.py` en modulos `src/builders/` | Alto | Alto | Medio | Pendiente | Q3 2026 | Tests de validacion existentes (`tests/test_pipeline_logic.py`) |
| 2 | Validacion de contratos JSON Schema en runtime | Alto | Medio | Bajo | Pendiente | Q3 2026 | Quick win tests (`tests/test_validation.py`) |
| 3 | Constantes de datasets como enum (`Dataset`) | Medio | Medio | Bajo | Pendiente | Q3 2026 | — |
| 4 | Estabilizacion de datasets en modo fallback | Alto | Alto | Medio | En progreso | Q3 2026 | Acceso a fuentes origen (URLs externas) |
| 5 | Dashboard publico de salud operativa del hub | Medio | Medio | Bajo | Pendiente | Q4 2026 | #4 completado (para no mostrar falsos positivos) |
| 6 | Robustecer manejo de errores en API publica | Medio | Bajo | Bajo | Completado | 2026-06-19 | — |
| 7 | Nuevas capacidades de API (cruces, validacion, busqueda) | Medio | Medio | Bajo | Pendiente | Futuro | #6 completado |

---

## Metricas de avance

| # | Mejora | Disenio | Prototipo | Implementacion | Tests | Documentacion | Despliegue |
|:--:|:---|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Refactor `build_dev_db.py` | 0% | 0% | 0% | 0% | 0% | 0% |
| 2 | Validacion contratos runtime | 0% | 0% | 0% | 0% | 0% | 0% |
| 3 | Constantes datasets | 0% | 0% | 0% | 0% | 0% | 0% |
| 4 | Estabilizacion fallbacks | 80% | 30% | 0% | 0% | 0% | 0% |
| 5 | Dashboard salud | 0% | 0% | 0% | 0% | 0% | 0% |
| 6 | API error handling | 100% | 100% | 100% | 100% | 100% | 100% |
| 7 | API capacidades | 100% | 0% | 0% | 0% | 0% | 0% |

**Progreso total:** 21% (1/7 completada — #6; #4 en progreso con diagnostico e infraestructura completados; #7 tiene plan de diseno completo)

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
- Proxima revision: 2026-06-26

### Semana 3 — (placeholder)
### Semana 4 — (placeholder)

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
