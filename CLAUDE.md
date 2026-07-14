---
title: "chile-hub — CLAUDE.md"
description: >
  Punto de entrada para sesiones Claude Code en chile-hub.
  Redirige a AGENTS.md y SOURCE_OF_TRUTH.md; incluye comandos esenciales,
  reglas no negociables y mapa de archivos.
category: ai-entrypoint
audience: [claude-code, ai-agent]
priority: critical
entrypoint_for: [SOURCE_OF_TRUTH.md, AGENTS.md]
related_docs:
  - SOURCE_OF_TRUTH.md
  - AGENTS.md
  - CONTRIBUTING.md
last_updated: 2026-07-14
---

# CLAUDE.md — Punto de Entrada para Claude Code

> **chile-hub** es una capa de datos reproducible y curada sobre datasets públicos
> oficiales de Chile. Pipeline determinista: extract → build → verify → test → publish.

## Navegación rápida

| Pregunta | Respuesta |
|---|---|
| ¿Por dónde empiezo? | **[`SOURCE_OF_TRUTH.md`](./SOURCE_OF_TRUTH.md)** — 5 invariantes + mapa de archivos (~100 líneas) |
| ¿Reglas completas? | **[`AGENTS.md`](./AGENTS.md)** — pipeline, testing, CI/CD, legal, anti-patterns |
| ¿Cómo contribuyo? | **[`CONTRIBUTING.md`](./CONTRIBUTING.md)** — verificaciones locales y flujo de PR |

## Comandos esenciales

```bash
# Configuración inicial
make bootstrap          # Crea .venv, instala dependencias + Playwright/Chromium
make doctor             # Verifica Python, dependencias críticas, gates anti-drift

# Pipeline completo
make refresh            # extract → build → verify → test → verify-landing → lint

# Pasos individuales
make extract            # 14 extractores → data/staging/
make build              # Artefactos → data/normalized/
make verify             # Integridad (SHA-256, conteos, schema)
make test               # pytest — lee data/normalized/, NO corre el pipeline

# Calidad de código
make lint               # Ruff check
make format-check       # Ruff format check
```

## 5 reglas que NUNCA debes romper

1. **Códigos CUT siempre `VARCHAR`** — `"01101"`, nunca `1101` (pierde el cero de Tarapacá)
2. **Fallar con estridencia** — `raise SystemExit(...)` en errores de validación, nunca warnings silenciosos
3. **`data/raw/` es solo-append** — snapshots de auditoría, nunca modificar
4. **`nombre_comuna_clean` siempre presente** — minúsculas, sin tildes, sin `ñ`
5. **Paths relativos a `__file__`** — nunca relativos a CWD (rompe en CI)

## Mapa de archivos clave

| Archivo | Cuándo leerlo |
|---|---|
| `src/extractors/base.py` (73 líneas) | Entender contrato de extractores |
| `src/validation.py` (1 194 líneas) | Agregar funciones `validate_*()` — leer por validador |
| `src/build_dev_db.py` (867 líneas) | Depurar el pipeline — `_compute_validations()` contiene el bloque `validations = {…}` |
| `src/chile_hub/core.py` (2 302 líneas) | API pública de `ChileHub` |
| `data/dataset_catalog_config.json` | Fuente de verdad de qué datasets existen |
| `data/source_registry.json` | Carril, maturity_status, confidence_tier, review_by |

## Herramientas AI-native disponibles

- **CodeGraph** (`.codegraph/codegraph.db`): índice estructural para `codegraph search`, `callers`, `callees`, `explore`, `impact`
- **AGENTS.md §12**: política anti-drift con `check_companion_paths.py` y bloques delimitados auto-sincronizados
- **`make doctor`**: verifica versiones, dependencias, registros de validación, contratos y documentación

## Al agregar o modificar código

1. ¿Cambiaste `src/validation.py`? → Actualiza el bloque `validations = {…}` en `build_dev_db.py`
2. ¿Agregaste un extractor? → Registra en `data/dataset_catalog_config.json` + crea `docs/datasets/{nombre}.md`
3. ¿Cambiaste schemas? → Actualiza `contracts/datasets/{nombre}.schema.json`
4. ¿Agregaste lógica nueva del pipeline? → Agrega tests en `tests/` (el gate de co-cambio de CI lo exige)
5. Ejecuta `make doctor` antes de commit

> **Detalle completo en [`AGENTS.md`](./AGENTS.md).** Este archivo es solo el mapa rápido.
