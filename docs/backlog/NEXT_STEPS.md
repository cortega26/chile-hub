# Próximos pasos — ChileHub

**Fecha:** 2026-06-20 (actualizado — Mejora #1 completada)
**Estado actual:** Alpha · 57% de backlog completado (#4, #6, #1 completadas)
**Objetivo:** Cerrar backlogs en orden de impacto estratégico

---

## Resumen de estado

| # | Mejora | Estado actual | Progreso |
|:--:|:---|:---|:--:|
| 4 | Estabilización fallbacks | **Completado** ✓ | MINEDUC live (#6), SIEDU live (#7), SINIM degradado (#5) |
| 1 | Refactor `build_dev_db.py` | **Completado** ✓ | 2867 → 668 líneas; 9 módulos en `src/builders/` |
| 2 | Contratos JSON Schema en runtime | Pendiente | 0% — contratos existen pero no se ejecutan en pipeline |
| 3 | Constantes de datasets | Pendiente | 0% — strings mágicos en ~200 ubicaciones |
| 5 | Dashboard público de salud | Pendiente | 0% — #4 ya completado, puede iniciarse |
| 7 | API capacidades avanzadas | Pendiente | Diseño completo, implementación 0% |

---

## Orden recomendado

### 1. ~~Cerrar estabilización de fallbacks (#4)~~ ✅ COMPLETADO

**Resultado:** `fallback_count: 0`, `live_count: 15` en `hub_health.json`.

| Dataset | Estado | Resultado |
|:---|:---|:---|
| `resultados_educacionales` (MINEDUC) | ✅ Live | 345 registros por (anio, comuna), RAR 42MB |
| `indicadores_urbanos_siedu` (INE/SIEDU) | ✅ Live | 6.701 registros, 117 comunas, 68 indicadores |
| `finanzas_municipales` (SINIM) | ✅ Degradado | `candidate` permanente, portal requiere JS/POST |
| `perfil_territorial_comunal` | ✅ Derivado live | Upstream SIEDU y MINEDUC ya en modo live |

---

### 2. ~~Refactorizar `build_dev_db.py` (#1)~~ ✅ COMPLETADO

**Resultado:** `build_dev_db.py` pasó de **2867 → 668 líneas** (solo orquestación). Se
extrajeron 9 módulos a `src/builders/`:

| Módulo | Líneas | Contenido |
|:---|--:|:---|
| `_shared.py` | 51 | Rutas, constantes, `DATASET_CATALOG_CONFIG` |
| `io_utils.py` | 37 | Escritura atómica (JSON/Parquet/Excel), SHA-256 |
| `formats.py` | 379 | `build_duckdb/sqlite/excel/flat_files` |
| `metadata.py` | ~530 | Carga/validación + builders (freshness, degradación, cobertura, drift, enrich) + `build_dataset_metadata` |
| `reports.py` | 724 | Builders de reportes/estados del hub |
| `artifacts.py` | 432 | Índice de artefactos, manifiesto, bundles |
| `datasets.py` | 128 | Perfil territorial + capas geográficas |
| `catalog.py` | 89 | Metadata del pipeline + catálogo |
| `landing.py` | 133 | Sincronización JSON-LD de la landing |

`main()` quedó descompuesto en 5 subfunciones (`_load_inputs`, `_compute_validations`,
`_write_data_artifacts`, `build_dataset_metadata`, `_generate_reports`) más un orquestador
delgado. Verificación: 410 tests pasan, lint limpio, y el pipeline produce artefactos
byte-idénticos a la línea base salvo timestamps.

---

### 3. Contratos JSON Schema en runtime (#2)

**Problema:** Hay 15 contratos en `contracts/datasets/*.schema.json`. La validación contra ellos solo se ejecuta en `scripts/verify_pipeline.py` (fuera del pipeline principal). Si `build_dev_db.py` produce datos que violan el contrato, no se detecta hasta que alguien corre `verify_pipeline.py` manualmente o en CI.

**Solución:**
1. Crear `src/contracts/validator.py` con una función `validate_dataframe_against_contract(df, contract_path)` que use `jsonschema` para validar tipos, columnas requeridas, primary keys, y rangos.
2. Integrar en `build_dev_db.py`: después de cada `build_*()`, llamar al validador de contratos.
3. Si `--strict`: fallar el build. Si no: warning.
4. Tests: cargar cada contrato, construir DataFrame válido e inválido, verificar que el validador detecta violaciones.

---

### 4. Constantes de datasets como enum (#3)

**Problema:** Los nombres de dataset se pasan como strings mágicos en ~200 ubicaciones (`"comunas"`, `"finanzas_municipales"`, etc.). Un typo no se detecta hasta runtime.

**Solución:**
1. Crear `src/chile_hub/datasets.py` con:
```python
from enum import StrEnum

class Dataset(StrEnum):
    COMUNAS = "comunas"
    REGIONES = "regiones"
    PROVINCIAS = "provincias"
    # ... 15 miembros
```
2. Reemplazar strings mágicos progresivamente (grep + replace). Priorizar `build_dev_db.py`, luego `validation.py`, luego extractores.
3. Actualizar tests.

---

### 5. Dashboard público de salud (#5) — Depende de #4

Una vez que los extractores reporten `source_mode` honesto y al menos 2 datasets tengan extracción live, el dashboard mostrará datos reales. Sin #4 completado, el dashboard mostraría falsos positivos.

No empezar hasta que #4 esté cerrado.

---

### 6. API capacidades avanzadas (#7) — Baja prioridad

El diseño está completo (`docs/backlog/07-api-capabilities.md`). Incluye:
- `chile-hub cross` — cruzar datasets por código de comuna
- `chile-hub validate` — validar un CSV externo contra contratos
- `chile-hub search` — buscar conceptos en metadatos

Implementar solo después de #1 (refactor) porque las capacidades nuevas se beneficiarán de builders modulares.

---

## Orden de ejecución

```
✅ Semana 1-2:  #4 completado (MINEDUC + SIEDU live, SINIM degradado)
Semana 3-5:  #1 — Refactor build_dev_db.py (extracción progresiva)
Semana 6:    #2 — Contratos en runtime (depende de #1 para integrar limpiamente)
Semana 7:    #3 — Constantes Dataset (paralelizable con #2)
Semana 8+:   #5 (dashboard) ya desbloqueado por #4 completado
Futuro:      #7 (API capacidades)
```

---

## Issues de GitHub

Todos los issues de estabilización de fallbacks cerrados al 2026-06-19.

### Issue #5 — SINIM finanzas_municipales ✅ CERRADO

Dataset degradado a `candidate` permanente. El portal SINIM requiere sesión PHP +
formulario POST + JS; no tiene API pública ni CSV/Excel descargable vía GET.

### Issue #6 — MINEDUC resultados_educacionales ✅ CERRADO

Extractor live implementado: `Rendimiento_2024.rar` (42 MB) → CSV 3.5M filas →
345 registros por (anio, codigo_comuna). `source_mode: "live"`.

### Issue #7 — SIEDU indicadores_urbanos ✅ CERRADO

Extractor live implementado: `matriz-siedu-publicacion.xlsm` (504 KB, INE) →
5 hojas → 6.701 registros (117 comunas, 68 indicadores). `source_mode: "live"`.

URL directa encontrada en servidor de documentación INE (no requería Playwright).

### Issue #4 — Plan general de estabilización ✅ CERRADO

Todos los requisitos cumplidos:
- ✅ Issue #6 cerrado (MINEDUC live)
- ✅ Issue #7 cerrado (SIEDU live)
- ✅ `source_registry.json` actualizado para todos los datasets
- ✅ `fallback_count: 0` en `hub_health.json`
