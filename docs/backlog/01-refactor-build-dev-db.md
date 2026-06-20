# [01] Refactorizar `build_dev_db.py` en modulos `src/builders/`

**Scorecard:** `docs/backlog/scorecard.md`
**Estado:** ✅ Completado (2026-06-20)
**Impacto:** Alto
**Esfuerzo estimado:** Alto
**Riesgo:** Medio
**Target:** Q3 2026

> **Resultado:** `build_dev_db.py` pasó de 2867 → 668 líneas (solo orquestación). Se
> crearon 9 módulos en `src/builders/` (`_shared`, `io_utils`, `formats`, `metadata`,
> `reports`, `artifacts`, `datasets`, `catalog`, `landing`) y `main()` se descompuso en
> 5 subfunciones. 410 tests pasan; salida del pipeline byte-idéntica salvo timestamps.
> Los nombres de módulo propuestos abajo difieren levemente de los finales (se
> consolidaron módulos relacionados), pero el criterio de aceptación se cumplió.

---

## Problema que resuelve

El archivo `src/build_dev_db.py` tiene **3206 lineas** y concentra toda la logica de
construccion del pipeline en un solo modulo (God module). Esto produce:

1. **Baja mantenibilidad**: cualquier cambio en un builder de formato (Parquet,
   DuckDB, SQLite, Excel, JSON) requiere navegar un archivo enorme.
2. **Dificultad para testear**: las funciones de builder estan acopladas al flujo
   principal (`main()`) y no pueden importarse ni probarse aisladamente.
3. **Duplicacion logica**: `build_flat_files()` (linea 2434) mezcla escritura de
   Parquet y JSON en una sola funcion; `write_parquet_atomic()` (linea 2428) y
   `write_json_atomic()` (linea 782) estan separadas pero en el mismo archivo.
4. **Onboarding lento**: un nuevo contribuidor debe entender 3200 lineas para
   modificar cualquier aspecto del pipeline.

---

## Evidencia actual

### Archivo God module

- **`src/build_dev_db.py`**: 3206 lineas, 60+ definiciones de funciones.
- **Funciones de builder de formato**:
  - `build_duckdb()` — linea 2142
  - `build_sqlite()` — linea 2207
  - `build_excel()` — linea 2305
  - `build_flat_files()` — linea 2434 (Parquet + JSON)
- **Funciones de metadata/report**:
  - `build_hub_status()` — linea 1083
  - `build_dataset_status()` — linea 1105
  - `build_dataset_changelog()` — linea 1250
  - `build_redistribution_report()` — linea 1306
  - `build_provenance_report()` — linea 1361
  - `build_drift_report()` — linea 1412
  - `build_overview()` — linea 1467
  - `build_source_readiness()` — linea 1533
  - `build_dataset_quality()` — linea 1618
- **Funciones auxiliares de metadata**:
  - `validate_metadata_schema()` — linea 743
  - `load_metadata()` — linea 769
  - `write_json_atomic()` — linea 782
  - `write_pipeline_metadata()` — linea 832
  - `write_dataset_catalog()` — linea 863
  - `compute_sha256()` — linea 909
  - `build_publishable_artifact_index()` — linea 917
- **Logica de validacion en `src/validation.py`**: 14 funciones `validate_*` importadas
  en la linea 27-47, pero la logica de schema contracts esta en `load_schema_contract()`
  (linea 723 de `build_dev_db.py`) en vez de en `src/validation.py`.
- **Funcion `main()`**: linea 2526-3200 (~674 lineas) que orquesta todo el pipeline.

---

## Propuesta de implementacion

### Paso 1: Crear estructura de modulos `src/builders/`

```
src/builders/
    __init__.py
    format_parquet.py      # write_parquet_atomic, build_parquet_outputs
    format_duckdb.py       # build_duckdb
    format_sqlite.py       # build_sqlite
    format_excel.py        # build_excel, pd_excel_writer
    format_json.py         # write_json_atomic, build_json_outputs
    metadata.py            # load_metadata, validate_metadata_schema, load_schema_contract
    reports.py             # build_hub_status, build_dataset_status, build_dataset_changelog
    reports_redistribution.py  # build_redistribution_report
    reports_provenance.py      # build_provenance_report
    reports_drift.py           # build_drift_report
    reports_overview.py        # build_overview
    reports_quality.py         # build_source_readiness, build_dataset_quality
    artifacts.py           # build_publishable_artifact_index, compute_sha256
    catalog.py             # write_dataset_catalog
    pipeline_utils.py      # write_pipeline_metadata, sync_landing_metadata
```

**Esfuerzo:** 2-3 sprints (~3-4 semanas)
- Creacion de archivos y migracion de funciones: 1 sprint
- Ajuste de imports en `build_dev_db.py`: 1 dia
- Pruebas de regresion con pipeline completo: 1 sprint

### Paso 2: Migrar funciones por grupo (orden seguro)

1. Mover funciones auxiliares puras: `write_parquet_atomic`, `write_json_atomic`,
   `compute_sha256`, `pd_excel_writer` (sin dependencias del pipeline).
2. Mover builders de formato: `build_duckdb`, `build_sqlite`, `build_excel`,
   `build_flat_files`.
3. Mover metadata y validacion: `load_metadata`, `validate_metadata_schema`,
   `load_schema_contract`, `enrich_dataset_metadata`.
4. Mover report builders: `build_hub_status`, `build_dataset_status`,
   `build_dataset_changelog`, `build_redistribution_report`, `build_provenance_report`,
   `build_drift_report`, `build_overview`, `build_source_readiness`,
   `build_dataset_quality`.
5. Mover catalog y artifacts: `write_dataset_catalog`, `build_publishable_artifact_index`,
   `write_artifact_manifest`, `write_hub_bundle_json`.
6. Refactorizar `build_dev_db.py` para que quede como orquestador (~500-800 lineas)
   que importa desde `src/builders/`.

### Paso 3: Refactorizar `main()` en subfunciones orquestadas

La funcion `main()` actual (linea 2526-3200) debe descomponerse en:

- `build_all_datasets()` — orquesta extractores (lineas 2540-2800 actual)
- `compute_validations()` — ejecuta validaciones (lineas 2800-2900 actual)
- `write_all_outputs()` — llama a builders de formato (lineas 2900-2950 actual)
- `generate_reports()` — genera todos los reportes (lineas 2950-3175 actual)
- `print_summary()` — muestra resumen al usuario (lineas 3176-3200 actual)

### Paso 4: Agregar tests para cada modulo builder

Crear `tests/builders/test_format_parquet.py`, `tests/builders/test_reports.py`, etc.
Cada test debe probar el builder en aislamiento con datos dummy.

---

## Criterio de aceptacion

1. `src/build_dev_db.py` tiene entre 500 y 800 lineas y solo contiene logica de
   orquestacion (llamadas a builders importados).
2. Todos los builders de formato estan en `src/builders/format_*.py`.
3. Todos los report builders estan en `src/builders/reports_*.py`.
4. `from src.builders import ...` funciona limpiamente.
5. `python src/build_dev_db.py` produce exactamente el mismo output que antes
   (verificar con diff sobre hub_health.json y dataset_catalog.json).
6. Los tests existentes en `tests/test_pipeline_logic.py` pasan sin modificaciones.
7. `make build` o equivalente ejecuta el pipeline completo sin errores.

---

## Dependencias

- Los tests existentes en `tests/test_pipeline_logic.py` sirven como red de
  seguridad para la regresion.
- `src/build_dev_db.py` debe mantener compatibilidad con `scripts/verify_pipeline.py`
  que importa `DATASET_CATALOG_CONFIG` desde el modulo (linea 18 de verify_pipeline.py).
  Esta constante debe seguir siendo accesible desde `src.build_dev_db`.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|:-------|:-----------:|:-------:|:-----------|
| Romper importaciones cruzadas entre builders | Alta | Alto | Migrar una funcion a la vez y ejecutar pipeline completo tras cada migracion |
| Duplicar logica al mover funciones | Media | Medio | Revision de codigo (code review) obligatoria en cada PR de migracion |
| Perder compatibilidad con scripts externos | Baja | Alto | Mantener `DATASET_CATALOG_CONFIG` y `load_schema_contract` como re-exportaciones en `__init__.py` de builders |
| El diff de outputs no es identico por orden de keys en JSON | Alta | Bajo | Usar `json.dumps(sort_keys=True)` en el diff de verificacion |

---

## Notas de disenio

### Decision: modulos planos vs jerarquicos

Se opta por `src/builders/reports_*.py` (modulos planos con prefijo) en vez de
`src/builders/reports/*.py` (subdirectorio) para mantener la profundidad de
import baja: `from src.builders.reports_drift import build_drift_report`.

### Decision: mantener DATASET_CATALOG_CONFIG en build_dev_db.py

Aunque es grande (~350 lineas, lineas 71-420), modificar `DATASET_CATALOG_CONFIG`
es frecuente al anadir/quitar datasets. Dejarlo en `build_dev_db.py` evita
importaciones circulares con los extractores. Si en el futuro se extrae a
`src/builders/config.py`, debe hacerse en un paso separado.

### Alternativa considerada: extraer todo a un solo archivo `src/pipeline.py`

Descartado porque no resuelve el problema de modularidad — solo mueve el God module
a otro archivo. La descomposicion en `src/builders/` permite crecimiento futuro
(anadir un builder de formato nuevo sin tocar el orquestador).
