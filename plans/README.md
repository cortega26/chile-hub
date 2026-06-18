# Plans — chile-hub

Planes de implementación generados por auditoría `/improve deep` en commit `ba2f434` (2026-06-13).

## Orden de ejecución recomendado

Los planes 001–004 son independientes entre sí y pueden ejecutarse en paralelo.
Los planes 005–007 tienen dependencias.

| # | Plan | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|--------|-----------|--------|
| 001 | [Fix landing page bugs — KPIs antiguos y crash de coordenadas](archive/001-fix-landing-page-bugs.md) | S | LOW | — | DONE (archivado) |
| 002 | [Agregar CSP a la landing page](archive/002-csp-landing-page.md) | S | LOW | — | DONE (archivado; CSP meta tag already in index.html:5) |
| 003 | [Validar metadata JSON antes del build](archive/003-guard-metadata-json.md) | S | LOW | — | DONE (archivado; guardas para metadata en build_dev_db.py) |
| 004 | [Limpiar dependencias — pyarrow, dev/prod, curl_cffi](archive/004-cleanup-dependencies.md) | S | LOW | — | DONE (archivado) |
| 005 | [Eliminar escrituras redundantes del build](archive/005-eliminate-redundant-build-writes.md) | S | LOW | 003 (idealmente) | DONE (archivado) |
| 006 | [Consolidar lógica duplicada y corregir violación de capas](archive/006-consolidate-duplicated-logic.md) | S | LOW | — | DONE (archivado) |
| 007 | [Mejoras de tooling — pre-commit, editorconfig, CI](archive/007-tooling-improvements.md) | S | LOW | 004 | DONE (archivado) |
| 008 | [Hardening de source readiness, schema contracts y quality gates](archive/008-hardening-source-readiness-schema-contracts-quality.md) | L | MED | — | DONE (archivado) |
| 009 | [Separar carriles stable_publishable y candidate](archive/009-split-stable-publishable-and-candidate-tracks.md) | M | MED | 008 | DONE (archivado) |

## Grafo de dependencias

```
001  (independiente)
002  (independiente)
003  (independiente) ──► 005
004  (independiente) ──► 007
006  (independiente)
008  (partes implementadas: source registry + contracts) ──► 009
```

## Hallazgos considerados y rechazados

Los siguientes hallazgos de la auditoría fueron verificados y rechazados antes de crear planes:

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **PERF-08**: `comunas_enriquecidas` duplica byte a byte a `comunas` en 5 formatos | **Por diseño**: el catálogo lo presenta como capa semánticamente distinta. Las columnas de enriquecimiento (lat, lon, población) se aplican en el extractor antes de que build las herede. Es redundante en almacenamiento pero distinto para el consumidor. |
| **PERF-10**: CI serializa quality antes de build-and-test | **Por diseño**: `needs: quality` evita gastar minutos de CI en build+test si el código no pasa lint. Es una optimización de recursos, no un problema. |
| **ARCH-12**: `indicadores_hoy.json` inconsistente con `{dataset}.json` | **Por diseño**: el nombre "hoy" comunica que es una vista puntual del último valor, no la serie histórica completa. |
| **ARCH-13**: `import json` redundante dentro de `build_flat_files()` | **Trivial**: no justifica un plan propio. Se puede arreglar inline en cualquier otro cambio. |
| **DM-08**: `requests` + `curl_cffi` overlap de HTTP clients | **Por diseño**: el patrón de fallback es intencional (curl_cffi con impersonate, requests como fallback). Está bien implementado. |
| **DM-09**: `pandas` podría removerse | **No justifica el esfuerzo (L)**: pandas se usa en 3 lugares con propósito real (SQLite `to_sql`, Excel output vía xlsxwriter, XLS lectura en SUBDERE). Reemplazarlo tocaría formatos de salida verificados. |
| **BUG-04**: BCN ArcGIS `returnGeometry=false` → coordenadas siempre cero | **Por diseño**: la capa consultada (Capa_Factores) es tabla de atributos sin geometría. Las coordenadas vienen del CSV de referencia estático (`comunas_coords.csv`). El código de `extract_coords` es defensivo para cuando se consulte una capa con geometría. |
| **BUG-05**: `== 0.0` float equality en enriquecimiento de coordenadas | **Riesgo puramente teórico**: las coordenadas de Chile están en rangos lejanos a cero (-18 a -56 lat, -67 a -75 lon). Ningún cálculo produce near-zero. |
| **BUG-06**: `derive_geography_layers` sin subset en `.unique()` | **Por diseño**: `validate_regiones` y `validate_provincias` detectan duplicados y fallan el build. Es mejor fallar ruidosamente que silenciosamente elegir un nombre arbitrario. |
| **BUG-07**: `int(attrs["cod_comuna"])` sin try/except | **Riesgo bajo**: la API de BCN es estable y siempre ha retornado códigos numéricos. El `except Exception` externo en `normalize_dpa()` ya provee fallback. |
| **BUG-08**: CSV export con `encodeURI` | **Riesgo bajo**: los nombres de comunas chilenos no contienen comas ni newlines. |
| **BUG-09**: `format` shadows built-in en `shared_artifacts()` | **Sin impacto real hoy**: el método no usa `format()`. |
| **BUG-10**: `os.remove()` antes de `duckdb.connect()` | **Riesgo bajo**: si `duckdb.connect()` falla, el próximo build regenera la BD desde cero. |

## Columnas de estado

- `TODO` — pendiente de ejecución
- `IN PROGRESS` — en ejecución activa
- `PARTIAL` — implementado parcialmente; quedan criterios pendientes
- `DONE` — completado
- `BLOCKED` — bloqueado (indicar por qué)
- `SKIP` — descartado después de análisis adicional
