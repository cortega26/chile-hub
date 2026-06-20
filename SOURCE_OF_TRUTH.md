# SOURCE_OF_TRUTH.md — Índice Maestro de Navegación

Lee esto primero. Luego sigue los punteros. No leas archivos completos en frío.

---

## Qué es este repositorio

`chile-hub` es una capa de datos reproducible y curada sobre datasets públicos oficiales de Chile.
Ejecuta un pipeline de extraccion → construccion → validacion → publicacion que produce artefactos
Parquet, DuckDB, JSON y ZIP consumibles en una sola linea de codigo, ademas de una landing page
estatica y una CLI/API de Python (`ChileHub`). El objetivo es tener menos datasets, mas limpios y
confiables — no una cobertura exhaustiva.

---

## Document ownership

| Documento | Propietario de | Cuando leerlo |
|---|---|---|
| **`SOURCE_OF_TRUTH.md`** ← estas aqui | Indice de navegacion, resumen de invariantes, mapa de archivos + tareas | Siempre primero — ~100 lineas |
| **`AGENTS.md`** | Reglas completas del pipeline, politica legal, flujo de 7 pasos para agregar datasets, jobs de CI/CD, antipatrones, convenciones de codigo | Al agregar un dataset · depurar el pipeline · preguntas legales · cambios en CI |
| **`CLAUDE.md`** | Redirige a AGENTS.md + SOURCE_OF_TRUTH.md; punto de entrada del proyecto para sesiones de Claude Code | Primera visita al repositorio · orientacion |

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
│   ├── base.py                    ABC BaseExtractor — 59 lineas, leer completo
│   └── {name}_extractor.py        Un archivo por dataset, extiende BaseExtractor
├── validation.py                  TODAS las validate_*() — ~760 lineas, leer por validador
├── build_dev_db.py                Orquestador del pipeline (~670 lineas) — main() + fases:
│   _load_inputs / _compute_validations / _write_data_artifacts / _generate_reports
│   El bloque validations = {…} vive en _compute_validations()
├── builders/                      Modulos del pipeline (extraidos de build_dev_db.py):
│   _shared, io_utils, formats, metadata, reports, artifacts, datasets, catalog, landing
├── chile_hub.py                   Shim de compatibilidad (21 lineas) — delega al paquete inferior
├── chile_hub/
│   ├── core.py                    Clase ChileHub + API publica completa — ~1 600 lineas
│   ├── cli.py                     Puntos de entrada de CLI (5 lineas)
│   ├── data_manager.py            Descarga de bundles, cache, SHA256 — ~200 lineas
│   └── pipeline_status_utils.py   Constructores de reportes (health, catalog, redistribution) — ~770 lineas
├── pipeline_status_utils.py       Copia del anterior para importaciones de build_dev_db.py

data/
├── raw/        Snapshots de auditoria — solo append, nunca editar
├── staging/    {dataset}.csv + {dataset}.metadata.json — entradas del pipeline
└── normalized/ Artefactos generados — NUNCA editar manualmente; siempre regenerar

tests/
├── test_chile_hub.py        Requiere data/normalized/ — ejecutar `make build` primero
├── test_extractors.py       No requiere datos normalizados
└── test_pipeline_logic.py   No requiere datos normalizados
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
| Navegar archivos grandes sin leerlos en frio | `CLAUDE.md` → seccion **CodeGraph** |
| Encontrar donde esta definido un simbolo | `codegraph find <name>` o `grep -n "def <name>" src/` |
| Leer API publica de ChileHub | `src/chile_hub/core.py` (clase ChileHub, todos los metodos publicos) |
| Leer toda la logica de validacion | `src/validation.py` (~760 lineas — leer por validador) |
| Leer contrato de extractors | `src/extractors/base.py` (59 lineas — seguro de leer completo) |

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
