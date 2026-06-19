# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commits `ba2f434` (2026-06-13) y `a2cd288` (2026-06-19).

## Planes activos (auditoría 2026-06-19)

| # | Plan | Prioridad | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|----------|--------|-----------|--------|
| 010 | [Corregir bugs en extractores y validación](010-fix-extractor-and-validation-bugs.md) | P1 | S | LOW | — | TODO |
| 011 | [Robustecer manejo de errores en API pública](011-harden-api-error-handling.md) | P1 | S | LOW | — | TODO |
| 012 | [Hardening de seguridad — TOCTOU, integridad binario y paths](012-security-hardening.md) | P2 | S | LOW | — | TODO |
| 013 | [Cache en memoria para la API de ChileHub](013-api-performance-caching.md) | P2 | S | LOW | — | TODO |
| 014 | [Limpieza de arquitectura — catálogo externo, imports, alias](014-architecture-cleanup.md) | P2 | M | MED | 010 | TODO |
| 015 | [Robustez de tests — HTTP mocking, CLI coverage, assertions](015-test-robustness.md) | P2 | M | LOW | 011 | TODO |
| 016 | [Cache de staging en CI](016-ci-staging-cache.md) | P3 | S | MED | — | TODO |
| 017 | [Nuevas capacidades de API — cruces, validación, exit codes, búsqueda](017-new-api-capabilities.md) | P3 | M | LOW | 011, 013 | TODO |

## Planes archivados (auditoría 2026-06-13, completados)

| # | Plan | Esfuerzo | Riesgo | Estado |
|---|------|----------|--------|--------|
| 001 | Fix landing page bugs — KPIs antiguos y crash de coordenadas | S | LOW | DONE |
| 002 | Agregar CSP a la landing page | S | LOW | DONE |
| 003 | Validar metadata JSON antes del build | S | LOW | DONE |
| 004 | Limpiar dependencias — pyarrow, dev/prod, curl_cffi | S | LOW | DONE |
| 005 | Eliminar escrituras redundantes del build | S | LOW | DONE |
| 006 | Consolidar lógica duplicada y corregir violación de capas | S | LOW | DONE |
| 007 | Mejoras de tooling — pre-commit, editorconfig, CI | S | LOW | DONE |
| 008 | Hardening de source readiness, schema contracts y quality gates | L | MED | DONE |
| 009 | Separar carriles stable_publishable y candidate | M | MED | DONE |

## Grafo de dependencias (planes activos)

```
010 (independiente) ───────────────────────────────────────────► 014
011 (independiente) ──► 015, 017
012 (independiente)
013 (independiente) ──► 017
016 (independiente)
017 ── depende de 011, 013
```

## Orden de ejecución recomendado

1. **Primero**: 010, 011, 012, 013 (independientes, esfuerzo S, máximo leverage)
2. **Segundo**: 014 (depende de 010), 015 (depende de 011)
3. **Tercero**: 016, 017 (menor criticidad; 017 depende de 011 y 013)

## Hallazgos considerados y rechazados (2026-06-19)

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **PERF-05**: 9× `to_list()` de comunas | Micro-optimización: 346 strings, ~2ms total. No justifica un plan. |
| **ARCH-08**: convención de paths mixta `os.path.join` vs `Path /` | Cosmético, sin impacto funcional. Se estandariza gradualmente en otros planes. |
| **DEP-03**: versiones 1 patch detrás | duckdb 1.5.3→1.5.4, ruff 0.15.17→0.15.18: bumps triviales. Se actualizan en el próximo release. |
| **PERF-07**: iloc copy en Excel chunking | ~525K filas extra en memoria para 1.57M dataset — memoria total <3GB, aceptable para build offline. |
| **PERF-04**: build paralelo | Diferido: el riesgo MED de paralelizar DuckDB+SQLite+Excel juntos no justifica el ahorro de ~30s de wall-clock hoy. Reconsiderar cuando el build supere 5 min. |
| **TC-02**: cobertura medida contra 5% del código | Diferido: ajustar `source` en `pyproject.toml` requiere primero cubrir `build_dev_db.py` y `validation.py` (backlog ME1). |
| **TC-04**: 34/40 funciones de build_dev_db.py sin tests | Incluido en backlog ME1 (Refactorizar build_dev_db.py). |
| **ARCH-03**: build_dev_db.py god module | Incluido en backlog ME1. No duplicar plan. |
| **DIR-03/04**: fallback stabilization | Incluido en backlog ME4. No duplicar plan. |
| **DIR-01**: runtime contracts | Incluido en backlog ME2. No duplicar plan. |
| **DIR-07**: health dashboard | Incluido en backlog ME5. No duplicar plan. |

## Hallazgos considerados y rechazados (2026-06-13, heredados)

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **PERF-08**: `comunas_enriquecidas` duplica byte a byte a `comunas` en 5 formatos | **Revertido en 2026-06-19**: el Plan 014 ahora lo aborda como alias (no duplicado). El costo de superficie de código (38 archivos mantienen este concepto duplicado) justifica el cambio. |
| **PERF-10**: CI serializa quality antes de build-and-test | Por diseño. |
| **ARCH-12**: `indicadores_hoy.json` inconsistente | Por diseño. |
| **ARCH-13**: `import json` redundante | Trivial. |
| **DM-08**: `requests` + `curl_cffi` overlap | Por diseño. |
| **DM-09**: `pandas` podría removerse | No justifica esfuerzo. |
| **BUG-04 a BUG-10**: varios bugs de bajo riesgo | Riesgo bajo o por diseño. |

## Columnas de estado

- `TODO` — pendiente de ejecución
- `IN PROGRESS` — en ejecución activa
- `DONE` — completado
- `BLOCKED` — bloqueado (indicar por qué)
- `SKIP` — descartado después de análisis adicional
