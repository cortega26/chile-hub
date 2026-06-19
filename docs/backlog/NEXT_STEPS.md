# Próximos pasos — ChileHub

**Fecha:** 2026-06-19
**Estado actual:** Alpha · 14% de backlog completado (#6 + inicio de #4)
**Objetivo:** Cerrar backlogs en orden de impacto estratégico

---

## Resumen de estado

| # | Mejora | Estado actual | Progreso |
|:--:|:---|:---|:--:|
| 4 | Estabilización fallbacks | En progreso | Infraestructura corregida, SINIM degradado, MINEDUC URLs confirmadas |
| 1 | Refactor `build_dev_db.py` | Pendiente | 0% — 3206 líneas monolíticas |
| 2 | Contratos JSON Schema en runtime | Pendiente | 0% — contratos existen pero no se ejecutan en pipeline |
| 3 | Constantes de datasets | Pendiente | 0% — strings mágicos en ~200 ubicaciones |
| 5 | Dashboard público de salud | Pendiente | 0% — depende de #4 completo |
| 7 | API capacidades avanzadas | Pendiente | Diseño completo, implementación 0% |

---

## Orden recomendado

### 1. Cerrar estabilización de fallbacks (#4) — Finalizar lo empezado

**Meta:** 2 datasets con extracción live real, 1 correctamente degradado.

#### 1a. Implementar extractor MINEDUC `resultados_educacionales` (🟢 viable)

URLs directas confirmadas:

| Fuente | URL | Formato | Datos |
|:---|:---|:---|:---|
| Desvinculación | `https://datosabiertos.mineduc.cl/wp-content/uploads/2025/10/OFICIAL-Tasa-Incidencia-Desvinculacion-2010-2024.xlsx` | XLSX | `tasa_retiro` por comuna |
| Rendimiento | `https://datosabiertos.mineduc.cl/wp-content/uploads/2025/04/Rendimiento_2024.rar` | RAR→CSVs | `tasa_aprobacion`, `tasa_reprobacion` por estudiante |

**Pasos concretos:**
1. Descargar y examinar estructura del XLSX de Desvinculación
2. Descargar y examinar CSVs dentro del RAR de Rendimiento 2024
3. Escribir `fetch_data()` que descargue ambos, descomprima, agregue a nivel comuna+año
4. Mapear columnas al contrato: `anio`, `codigo_comuna`, `matricula_total`, `asistencia_promedio`, `tasa_aprobacion`, `tasa_reprobacion`, `tasa_retiro`, `establecimientos_reportados`
5. Implementar usando el patrón de `mineduc_establecimientos_extractor.py` (descarga directa + `unrar` + `pl.read_csv`)
6. Agregar test con datos de muestra + verificar `source_mode: "live"`
7. Actualizar `source_registry.json`: `live_extractor_status: "implemented"`, `maturity_status: "stable"`

#### 1b. Implementar extractor SIEDU `indicadores_urbanos_siedu` (🟡 viable con navegador)

La Matriz de Indicadores Excel está tras pestañas JS en `siedu.ine.cl`. No accesible vía HTTP fetch.

**Pasos concretos:**
1. Usar Playwright para abrir `siedu.ine.cl`, click en pestaña INDICADORES, capturar URL del Excel
2. Alternativa: buscar "Matriz de Indicadores SIEDU" en `datos.gob.cl` o repositorio documental del INE
3. Si se encuentra URL: descargar con `requests`, parsear con `pl.read_excel()`, mapear al contrato
4. Si NO se encuentra en 1 semana: degradar a `candidate` igual que SINIM
5. Agregar test + actualizar `source_registry.json`

#### 1c. SINIM `finanzas_municipales` (✅ ya degradado)

Nada pendiente aquí. El dataset queda como `candidate` permanente. Si en el futuro aparece fuente alternativa (SUBDERE, Transparencia), se podrá reactivar.

#### 1d. `perfil_territorial_comunal` (⬜ derivado)

Una vez que MINEDUC o SIEDU estén live, modificar `build_perfil_territorial_comunal()` en `build_dev_db.py` para que acepte modo mixto (mezcla de upstreams live y fallback). Actualmente espera que TODOS los upstreams estén live.

---

### 2. Refactorizar `build_dev_db.py` (#1) — Prioridad máxima tras #4

**Archivo:** `src/build_dev_db.py` — 3206 líneas, 60+ funciones, 1 solo módulo.

**Plan de extracción (de menor a mayor riesgo):**

| Módulo nuevo | Líneas origen | Contenido | Riesgo |
|:---|:--:|:---|:--:|
| `src/builders/write_parquet.py` | ~80 | `write_parquet_atomic()` | Bajo |
| `src/builders/write_json.py` | ~60 | `write_json_atomic()` | Bajo |
| `src/builders/build_duckdb.py` | ~150 | `build_duckdb()` | Bajo |
| `src/builders/build_sqlite.py` | ~150 | `build_sqlite()` | Bajo |
| `src/builders/build_excel.py` | ~200 | `build_excel()` | Bajo |
| `src/builders/build_flat_files.py` | ~200 | `build_flat_files()` (Parquet + JSON) | Medio |
| `src/builders/build_metadata.py` | ~300 | `validate_metadata_schema()`, metadata helpers | Medio |
| `src/builders/build_reports.py` | ~500 | `build_hub_status()`, `build_provenance_report()`, etc. | Medio |
| `src/builders/build_datasets.py` | ~800 | `build_perfil_territorial_comunal()` y builders de datasets derivados | Alto |
| `src/build_dev_db.py` | ~600 | `main()`, orquestación, catálogo | — |

**Estrategia:** Extraer de a un módulo por vez. Cada extracción:
1. Mover funciones a `src/builders/<modulo>.py`
2. Importar desde `build_dev_db.py`
3. Correr `tests/test_pipeline_logic.py` (157 tests) + `tests/test_extractors.py` (54 tests)
4. Commit atómico

**Resultado esperado:** `build_dev_db.py` pasa de 3206 → ~600 líneas. Cada builder es testeable por separado.

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
Semana 1-2:  Finalizar #4 (MINEDUC extractor + SIEDU investigación)
Semana 3-5:  #1 — Refactor build_dev_db.py (extracción progresiva)
Semana 6:    #2 — Contratos en runtime (depende de #1 para integrar limpiamente)
Semana 7:    #3 — Constantes Dataset (paralelizable con #2)
Semana 8+:   #4 completo habilita #5 (dashboard)
Futuro:      #7 (API capacidades)
```

---

## Issues de GitHub relacionados

| Issue | Backlog | Estado |
|:---|:---|:---|
| #4 | Plan general estabilización | Actualizado con diagnóstico corregido |
| #5 | SINIM finanzas_municipales | Cerrable — degradado a candidate |
| #6 | MINEDUC resultados_educacionales | URLs confirmadas, extractor pendiente |
| #7 | SIEDU indicadores_urbanos | Investigación completada, extractor pendiente |
