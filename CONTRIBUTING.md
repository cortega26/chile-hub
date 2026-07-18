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
last_updated: 2026-07-18
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

## Contribuir un extractor (dataset nuevo)

Los datasets nuevos entran por el carril `candidate`, se evalúan contra
`docs/dataset-inclusion-criteria.md` y el mantenedor decide la promoción a
`stable_publishable`. **Antes de escribir código, abre un issue** con el
template [Dataset request](.github/ISSUE_TEMPLATE/dataset_request.yml) —
un PR de extractor sin issue previo aprobado probablemente se cierre.

Una vez que el mantenedor responde positivamente a las 3 preguntas bloqueantes
(licencia, formato, estabilidad), sigue este checklist:

1. **Issue aprobado** — respuesta positiva del mantenedor a licencia, formato
   y estabilidad (ver `AGENTS.md §5`, Paso 1).
2. **Extractor** en `src/extractors/{nombre}_extractor.py` siguiendo el
   contrato de `src/extractors/base.py`. Como modelo, usa un extractor simple
   existente (p. ej. `pobreza_extractor.py`).
3. **Datos de staging** — `data/staging/{nombre}.csv` +
   `data/staging/{nombre}.metadata.json` con todos los campos obligatorios
   (ver `AGENTS.md §5`, Paso 2, que los lista).
4. **Catálogo** — entrada en `data/dataset_catalog_config.json` (+ campo
   `extractor` apuntando al archivo) y en `data/source_registry.json` con
   carril `candidate` y `review_by` (ver `docs/dataset-inclusion-criteria.md`).
5. **Validación** — función `validate_{nombre}()` en `src/validation.py` +
   registro en el bloque `validations = {…}` de `build_dev_db.py`; verifica
   con `python scripts/check_validation_registration.py`.
6. **Tests** — clase `{Nombre}ExtractorTests` en `tests/test_extractors.py` +
   casos de borde en `tests/test_pipeline_logic.py` (ver `AGENTS.md §5`,
   Paso 5).
7. **Docs y contrato de esquema** — `docs/datasets/{nombre}.md` +
   `contracts/datasets/{nombre}.schema.json` (ambos los exige `make doctor`
   vía `scripts/check_companion_paths.py registry`).
8. **CI** — agrega el extractor al paso de extracción del workflow
   correspondiente (`pipeline-check.yml` diario o `monthly-scrape.yml`
   mensual; el criterio de cadencia está en `AGENTS.md §3`).

**Lo que el mantenedor revisa:** licencia y redistribución (semáforo de
`AGENTS.md §6`), que el modo fallback no llegue al bundle publicable, que
`make doctor` y `make test` pasen, y que el dataset aporte valor de cruce
(join keys con la DPA por `codigo_comuna` o `codigo_region`).

> **Expectativa honesta:** el proyecto tiene un mantenedor único; la revisión
> tarda días, no horas. Un extractor aceptado en `candidate` puede requerir
> varios ciclos antes de promover (ver `review_by` en `source_registry.json`).

## Pull requests

Usa prefijos de commits convencionales en los títulos de los commits cuando sea posible:
`fix:`, `feat:`, `docs:`, `chore:`. Los lanzamientos se generan a partir del historial de commits
después de que el pipeline completo pase.
