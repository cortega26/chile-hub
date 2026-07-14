---
title: "chile-hub — SOURCE_OF_TRUTH.md"
description: >
  Índice maestro de navegación para chile-hub. Resumen de 5 invariantes, mapa de archivos,
  flujo del pipeline y tabla de tareas comunes con punteros a la documentación relevante.
category: navigation-index
audience: [ai-agent, contributor, developer]
priority: critical
entrypoint: true
source_of_truth_for: >
  Navegación general del repositorio, invariantes críticas resumidas,
  mapa de archivos anotado, tareas comunes y punteros.
related_docs:
  - AGENTS.md              # Reglas completas del pipeline, legal, testing, CI/CD
  - CLAUDE.md              # Punto de entrada para sesiones Claude Code
  - CONTRIBUTING.md        # Verificaciones locales y flujo de PR
  - docs/dataset-inclusion-criteria.md  # Criterios de aceptación/deprecación
last_updated: 2026-07-14
---

# SOURCE_OF_TRUTH.md — Índice Maestro de Navegación

> **Lee esto primero.** Luego sigue los punteros. No leas archivos completos en frío.
> **Tiempo de lectura:** ~3 minutos. **Propósito:** Orientarte antes de abrir cualquier archivo.

---

## ¿Qué es este repositorio?

`chile-hub` es una capa de datos reproducible y curada sobre datasets públicos oficiales de Chile.
Ejecuta un pipeline de extracción → construcción → validación → publicación que produce artefactos
Parquet, DuckDB, JSON y ZIP consumibles en una sola línea de código, además de una landing page
estática y una CLI/API de Python (`ChileHub`). El objetivo es tener **menos datasets, más limpios y
confiables** — no una cobertura exhaustiva.

---

## Document ownership

| Documento | Propietario de | Cuando leerlo |
|---|---|---|
| **`SOURCE_OF_TRUTH.md`** ← estas aqui | Indice de navegacion, resumen de invariantes, mapa de archivos + tareas | Siempre primero — ~100 lineas |
| **`AGENTS.md`** | Reglas completas del pipeline, politica legal, flujo de 7 pasos para agregar datasets, jobs de CI/CD, antipatrones, convenciones de codigo | Al agregar un dataset · depurar el pipeline · preguntas legales · cambios en CI |
| **`CLAUDE.md`** | Redirige a AGENTS.md + SOURCE_OF_TRUTH.md; punto de entrada del proyecto para sesiones de Claude Code | Primera visita al repositorio · orientacion |
| **`docs/dataset-inclusion-criteria.md`** | Criterios de aceptacion/deprecacion de datasets, carriles `candidate`/`stable_publishable` | Al evaluar si un dataset nuevo entra al MVP · al reevaluar un `candidate` |

---

## 5 invariantes no negociables

1. **Los codigos CUT son strings de longitud fija** — `"01"` (region), `"011"` (provincia), `"01101"` (comuna). Nunca int.
2. **Fallar con estridencia** — `raise SystemExit(...)` en errores de validacion. Nunca advertencias silenciosas para datos incorrectos.
3. **`data/raw/` es solo append** — snapshots de auditoria. Nunca modificar despues de escribir.
4. **`nombre_comuna_clean` debe existir** — minusculas, sin acentos, sin `ñ`. Clave de join para busqueda difusa de texto.
5. **Rutas siempre relativas a `__file__`** — nunca relativas a CWD (`"data"`); se rompe en CI.

→ Detalles completos de invariantes con ejemplos de codigo: **`AGENTS.md §4`**

---

## Mapa de archivos — delimita tus lecturas

```
src/
├── extractors/
│   ├── base.py                    ABC BaseExtractor — 73 lineas, leer completo
│   └── {name}_extractor.py        Un archivo por dataset, extiende BaseExtractor
├── validation.py                  TODAS las validate_*() — 1 194 lineas, leer por validador
├── build_dev_db.py                Orquestador del pipeline (867 lineas) — main() + fases:
│   _load_inputs / _compute_validations / _write_data_artifacts / _generate_reports
│   El bloque validations = {…} vive en _compute_validations()
├── builders/                      Modulos del pipeline (extraidos de build_dev_db.py):
│   _shared, io_utils, formats, metadata, reports, artifacts, datasets, catalog, landing
├── chile_hub.py                   Shim de compatibilidad (21 lineas) — delega al paquete inferior
├── chile_hub/
│   ├── core.py                    Clase ChileHub + API publica completa — 2 302 lineas
│   ├── cli.py                     Puntos de entrada de CLI (5 lineas)
│   ├── data_manager.py            Descarga de bundles, cache, SHA256 — ~200 lineas
│   └── pipeline_status_utils.py   Constructores de reportes (health, catalog, redistribution) — 888 lineas
├── pipeline_status_utils.py       Copia del anterior para importaciones de build_dev_db.py — 888 lineas

data/
├── raw/        Snapshots de auditoria — solo append, nunca editar
├── staging/    {dataset}.csv + {dataset}.metadata.json — entradas del pipeline
└── normalized/ Artefactos generados — NUNCA editar manualmente; siempre regenerar

tests/                      9 archivos — inventario completo en AGENTS.md §8, no lo dupliques aqui
├── test_chile_hub.py        Requiere data/normalized/ — ejecutar `make build` primero
├── test_core.py             Requiere data/normalized/
└── test_extractors.py, test_pipeline_logic.py, test_validation.py, test_data_package.py,
    test_packaging_runtime.py, test_render.py, test_ci_config.py   No requieren datos normalizados
```

---

## Tareas comunes → donde mirar

| Tarea | Ir a |
|---|---|
| Ejecutar pipeline completo | `CLAUDE.md` → **Comandos esenciales** → `make refresh` |
| Ejecutar un paso | `CLAUDE.md` → `make extract` / `make build` / `make test` |
| Agregar un nuevo dataset | **`AGENTS.md §5`** — lista de verificacion de 7 pasos |
| Escribir una funcion `validate_*()` | `src/validation.py` — luego importar en `build_dev_db.py` |
| Entender los jobs de CI/CD | **`AGENTS.md §9`** |
| Verificar estado legal de redistribucion de una fuente | **`AGENTS.md §6`** |
| Revisar que antipatrones evitar | **`AGENTS.md §10`** |
| CI marca un documento/test desincronizado del codigo | **`AGENTS.md §12`** — `scripts/check_companion_paths.py` |
| Navegar archivos grandes sin leerlos en frio | `CLAUDE.md` → seccion **CodeGraph** |
| Encontrar donde esta definido un simbolo | `codegraph find <name>` o `grep -n "def <name>" src/` |
| Leer API publica de ChileHub | `src/chile_hub/core.py` (clase ChileHub, todos los metodos publicos) |
| Leer toda la logica de validacion | `src/validation.py` (1 194 lineas — leer por validador) |
| Leer contrato de extractors | `src/extractors/base.py` (73 lineas — seguro de leer completo) |

---

## Flujo del pipeline (resumen de un vistazo)

```
make extract        →  data/staging/{dataset}.{csv,metadata.json}  +  data/raw/
make build          →  data/normalized/  (Parquet, DuckDB, JSON, ZIP, manifests)
make verify         →  verificacion de integridad (SHA-256, conteo de registros, schema)
make test           →  pytest (lee normalized/ — NO ejecuta el pipeline)
make verify-landing →  pruebas smoke con Playwright contra index.html
```

**Un solo comando para todo:** `make refresh` ejecuta los cinco en orden + lint + verificacion de formato.
