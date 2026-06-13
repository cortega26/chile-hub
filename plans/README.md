# Plans — Chile-hub

Planes de implementación generados por auditoría `/improve deep` en commit `e3951f0` (2026-06-12).

## Orden de ejecución recomendado

Los planes están organizados en cuatro grupos. Ejecutar grupo por grupo; dentro de cada grupo los planes sin dependencias entre sí pueden correr en paralelo.

### Grupo A — Infraestructura y seguridad (P1)

| # | Plan | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|--------|-----------|--------|
| 001 | [Limpiar y pinear dependencias](001-limpiar-y-pinear-deps.md) | S | LOW | — | DONE |
| 002 | [Cache de CI (pip + Playwright)](002-cache-ci.md) | S | LOW | 001 (idealmente) | DONE |
| 003 | [Cron refresh diario en CI](003-cron-refresh-diario.md) | M | LOW | 002 | DONE |
| 004 | [Fix XSS tabla de comunas en `index.html`](004-xss-tabla-comunas.md) | S | LOW | — | DONE |

### Grupo B — Tests (P1–P2, independientes entre sí salvo 007)

| # | Plan | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|--------|-----------|--------|
| 005 | [Tests de invariantes CUT y validadores](005-tests-invariantes-y-validadores.md) | S | LOW | — | DONE |
| 006 | [Tests de fallback de indicadores BCCh](006-tests-fallback-indicadores.md) | M | LOW | — | DONE |
| 007 | [Tests de extractores con HTTP mocking](007-tests-extractores.md) | L | LOW | 006 | DONE |

### Grupo C — Correctness y arquitectura (P1–P2)

| # | Plan | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|--------|-----------|--------|
| 008 | [Pre-validar artefactos antes del ZIP](008-pre-validar-artefactos-zip.md) | M | LOW | — | DONE |
| 009 | [Centralizar registro de datasets](009-centralizar-registro-datasets.md) | M | LOW | — | DONE |
| 010 | [Deduplicar helpers compartidos](010-deduplicar-helpers.md) | S | LOW | — | DONE |
| 011 | [Agregar ruff, formatter y pre-commit hooks](011-linter-formatter.md) | M | LOW | 001 | DONE |

### Grupo D — Dirección / nuevas capacidades (P2–P3)

| # | Plan | Esfuerzo | Riesgo | Depende de | Estado |
|---|------|----------|--------|-----------|--------|
| 012 | [Capa de enriquecimiento territorial publicable](012-capa-enriquecimiento-territorial.md) | M | LOW | 009 (opt) | DONE |
| 013 | [Clase base `BaseExtractor`](013-base-extractor-template.md) | M | MED | 012 (opt) | DONE |

## Grafo de dependencias

```
001 ──► 002 ──► 003
        │
        └──► 011

004  (independiente)
005  (independiente)
006 ──► 007
008  (independiente)
009 ──► 012 ──► 013
010  (independiente)
```

## Hallazgos considerados y rechazados

Los siguientes hallazgos de la auditoría fueron verificados y rechazados antes de crear planes:

| Hallazgo | Motivo del rechazo |
|----------|-------------------|
| **CORRECTNESS-03**: `raise_for_status()` dispara antes de `save_raw_snapshot()` causando que no se guarden snapshots en error | **Por diseño**: no se guarda una respuesta 5xx como snapshot; el fallback usa el snapshot del último éxito. Ver `bcentral_extractor.py:114-118`. |
| **TEST-10**: `build_indicator_delivery` está indefinida | **Falso positivo**: la función SÍ está definida en `build_dev_db.py:210`. El subagente la buscó en el lugar equivocado. |
| **TECH-DEBT-01**: falta `CLAUDE.md` | **Obsoleto**: el archivo fue creado en la misma sesión de auditoría antes de este plan. |
| **ARCH-04**: las líneas 1394-1410 de `main()` en `build_dev_db.py` son "código duplicado muerto" | **Por diseño**: es un build de dos fases intencional. Fase 1 crea manifest/bundle/overview sin ZIP. Fase 2 crea el ZIP, lo adjunta al manifest, y reconstruye bundle/overview con los metadatos del paquete ZIP. Eliminar la Fase 2 rompería los metadatos del bundle publicable. |

## Columnas de estado

- `TODO` — pendiente de ejecución
- `IN PROGRESS` — en ejecución activa
- `DONE` — completado (actualizar con el commit SHA)
- `BLOCKED` — bloqueado (indicar por qué)
- `SKIP` — descartado después de análisis adicional

## Notas de mantenimiento de estos planes

- Los excerpts de código en cada plan corresponden al commit `e3951f0`. Ejecutar el **drift check** al inicio de cada plan para detectar si el código evolucionó.
- Los planes del Grupo D son de dirección — implementan capacidades nuevas, no corrigen bugs. Ejecutarlos solo cuando los grupos A-C estén completos.
- Si se agrega un nuevo extractor de datos, los planes 009, 012 y 013 proveen el patrón a seguir.
