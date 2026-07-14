---
title: "chile-hub — CONTRIBUTING.md"
description: >
  Guía de contribución para chile-hub. Verificaciones locales, cambios de datos,
  flujo de pull requests y convenciones de commits.
category: contribution-guide
audience: [contributor, developer]
priority: high
source_of_truth_for: >
  Verificaciones locales pre-PR, flujo de contribución, cambios de datos.
related_docs:
  - AGENTS.md              # Reglas completas del pipeline y arquitectura
  - SOURCE_OF_TRUTH.md     # Índice de navegación y 5 invariantes
  - docs/release.md        # Proceso de release
last_updated: 2026-07-14
---

# Contribuir

Gracias por ayudar a mantener chile-hub confiable.

## Verificaciones locales

Ejecuta las verificaciones útiles más pequeñas antes de abrir un pull request:

```bash
make lint
make format-check
make test
make doctor
```

`make doctor` corre `scripts/check_companion_paths.py registry`: verifica que cada
dataset de `data/dataset_catalog_config.json` tenga su contrato en
`contracts/datasets/` y su doc en `docs/datasets/`. En CI, un chequeo adicional por
pull request (`check_companion_paths.py companions`) exige que ciertos cambios de
código (`src/validation.py`, `src/extractors/**`, `data/dataset_catalog_config.json`,
entre otros — ver `AGENTS.md §12`) vengan acompañados de su test o documento
asociado en el mismo diff. Si CI marca una ruta compañera faltante, actualiza el
doc/test indicado en el mismo PR.

Para cambios que afectan archivos públicos generados, ejecuta:

```bash
make build
make verify
make verify-landing
```

## Cambios de datos

Los nuevos conjuntos de datos deben seguir `AGENTS.md §5`: evalúa los derechos de la fuente primero,
agrega un extractor, escribe metadatos de staging, valida en `src/validation.py`, conecta la compilación,
agrega pruebas, actualiza CI y documenta el conjunto de datos.

> **Nunca edites `data/normalized/` manualmente.** Regenera los datos a través del pipeline.

## Pull requests

Usa prefijos de commits convencionales en los títulos de los commits cuando sea posible:
`fix:`, `feat:`, `docs:`, `chore:`. Los lanzamientos se generan a partir del historial de commits
después de que el pipeline completo pase.
