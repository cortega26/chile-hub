# Plan 109: README sin datos volátiles y alerta de schedule roto

> **Depende de**: plan 108, que debe estar mergeado y con dos schedules consecutivos en success.
>
> **Drift check**:
> - `grep -n "::notice::README.md" .github/workflows/pipeline-check.yml` devuelve una línea.
> - `grep -n "DEFAULT_MAX_RECORD_DROP_PCT" scripts/verify_pipeline.py` devuelve la constante.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (toca `doc_sync.py`, el README y el workflow)
- **Category**: CI / docs / observabilidad
- **Planned at**: 2026-09-26 (branch `fix/108-build-synced-stale`)

## Problema

El plan 108 desarmó el deadlock, pero dejó dos deudas:

1. **El bot commitea `README.md` todos los días.** La tabla de capas y los resúmenes de salud y calidad cambian con los datos. Eso genera ruido en el historial de un archivo de documentación y mantiene a `README.md` como archivo compartido por el publish y el release, lo que expone a las carreras ya documentadas en el workflow.
2. **Una falla del schedule no avisa a nadie.** El schedule falló seis semanas seguidas (2026-08-13 → 2026-09-26) sin que nadie lo notara.

## Cambios propuestos

### A. Sacar los datos volátiles del README

- En `README.md`, conservar solo lo estable de cada capa: nombre, fuente, licencia y frecuencia. La columna de conteo y el estado live/fallback salen de la tabla.
- Reemplazar esos datos por enlaces a los reportes que ya se generan en cada build: `data/normalized/hub_health.md`, `dataset_status.json` y `dataset_quality.md`. Agregar los badges dinámicos existentes (frescura y estado) en lugar de las cifras.
- Ajustar `src/builders/doc_sync.py`:
  - Los bloques `START_HEALTH_SUMMARY` y `START_QUALITY_SUMMARY` pasan a texto estable, con un enlace y sin conteos.
  - La tabla de capas se genera solo desde el registro, no desde `hub_health.json`.
- Una vez que el README deje de depender de los datos, devolver `README.md` al `exit 1` del gate "Check build-synced files" y sacarlo del `git add` del publish. Actualizar `BuildSyncedGateGuardrailTests` y `BotWriteRaceGuardrailTests`.

### B. Alerta de schedule roto

- Agregar a `pipeline-check.yml` un job `notify-schedule-failure` con:
  - `if: failure() && github.event_name == 'schedule'`
  - `needs: [build-and-test, publish]`
  - `permissions: issues: write`
- El job abre o actualiza un issue fijo, con título "Schedule diario roto" y label `ci-schedule`. El issue incluye el link al run y las anotaciones de error, que se obtienen con `gh api .../check-runs/<id>/annotations`.
- Un paso en el publish exitoso cierra ese issue si está abierto.
- **SLO de frescura**: `make doctor` avisa si el `pipeline_metadata.json` publicado tiene más de 48 h.

### C. (Opcional) Expectativas declarativas por dataset

Si algún dataset necesita un umbral distinto del 20% global (ADR-022), o validar valores requeridos (p. ej. `cargo ∈ {diputado, senador}` en autoridades), agregar `quality_expectations` a la spec (`data/dataset_specs/*.json`). El cambio incluye su proyección en `to_source_registry_entry()` y su validación en `verify_source_registry`. No se implementa hasta que haya un caso concreto.

## Verificación

- `make doctor` y `.venv/bin/python -m pytest tests/ -q` terminan en exit 0.
- **Parte A**: un schedule con cambios de conteo termina en success y el commit `daily refresh` no toca `README.md`.
- **Parte B**: un `workflow_dispatch` en un branch con un fallo forzado en un paso temporal abre el issue, y el run siguiente en success lo cierra.

## Riesgos

- **Pérdida de información en el README.** Quien lee el README deja de ver los conteos a simple vista y tiene que seguir un link. Se mitiga con los badges y un enlace destacado a `hub_health.md`.
- **Permiso de issues en el workflow.** El job de alerta amplía el alcance del token. Limitarlo a ese job, con `permissions: issues: write` a nivel del job y no del workflow.

## Rollback

Revertir las partes A y B por separado; son independientes entre sí.
