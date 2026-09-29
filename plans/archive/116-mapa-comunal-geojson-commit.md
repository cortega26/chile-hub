# Plan 116: El refresh de geometría commitea también `mapa_comunal.geojson`

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- .github/workflows/geometria-comunal.yml scripts/build_geometria_comunal.py tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`scripts/build_geometria_comunal.py:83` escribe el asset visual
`data/normalized/mapa_comunal.geojson` que consume el coropleto de la landing
(`app.js:1618` lo descarga). El workflow candidate
(`.github/workflows/geometria-comunal.yml`) commitea solo parquet + metadata +
checksum (`:115-118`), y `tests/test_ci_config.py:672-688` fija esa lista como
contrato. Resultado: en el próximo refresh, el parquet publicado avanza y el
GeoJSON commiteado se queda atrás (runner descarta el archivo regenerado), y el
mapa de la landing muestra una geometría distinta de la que publica el
artefacto candidate. El build diario no regenera ese archivo (solo este
script), así que la deriva persiste hasta un commit manual.

## Current state

- `.github/workflows/geometria-comunal.yml:111-127`:
  ```yaml
        - name: Commit validated candidate artifacts
          run: |
            ...
            for path in \
              data/normalized/geometria_comunal.parquet \
              data/staging/geometria_comunal.metadata.json \
              data/normalized/geometria_comunal.parquet.sha256
            do
              [ -e "$path" ] && git add -f "$path"
            done
  ```
- `scripts/build_geometria_comunal.py:27` importa
  `write_mapa_comunal_geojson`; `:37` `OUTPUT_MAPA_PATH =
  NORMALIZED_DIR / "mapa_comunal.geojson"`; `:83` lo escribe.
- `src/builders/geo.py:58` define el writer; no hay otro caller
  (`grep -rn "write_mapa_comunal_geojson"` → solo el script y tests).
- `data/normalized/mapa_comunal.geojson` está trackeado (`git ls-files`), y
  `.gitignore` lo re-incluye explícitamente (`!data/normalized/*.geojson`).
- `tests/test_ci_config.py:672-688` (`test_commit_stages_only_durable_geometry_artifacts`)
  compara `staged_paths == expected_paths` (lista exacta y ordenada).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Test focal | `./.venv/bin/pytest tests/test_ci_config.py -k "durable" -v` | declared | verde |
| Tests geometría | `./.venv/bin/pytest tests/test_pipeline_logic.py -k "Geo or mapa" -v` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**:
- `.github/workflows/geometria-comunal.yml` (solo el bloque `for path in`)
- `tests/test_ci_config.py` (`expected_paths`)

**Out of scope**:
- `scripts/build_geometria_comunal.py` (ya escribe el archivo).
- `src/builders/geo.py`.
- Añadir el GeoJSON al ZIP/manifiesto/catálogo (no es un dataset; el
  comentario del workflow y ADR-021 documentan que los que se archivan son
  parquet+metadata+sha).
- Regenerar el archivo en este plan (lo hará el próximo workflow run).

## Git workflow

- Branch: `advisor/116-mapa-geojson-commit`
- Commit: `fix(ci): commitea el geojson del mapa junto al parquet candidate`
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_ci_config.py -k durable -v` verde. Si no, STOP.

### Step 1: Agregar la ruta al commit

En `.github/workflows/geometria-comunal.yml`, agrega
`data/normalized/mapa_comunal.geojson \` a la lista `for path in`. El orden
importa para el test: agrégalo después de
`data/normalized/geometria_comunal.parquet.sha256` (el test compara listas
exactas; actualiza el test en consecuencia en el mismo commit).

Ajusta también el comentario del bloque (dice "Sólo artefactos durables:
parquet + metadata + checksum") para nombrar el geojson y por qué viaja
(asset visual derivado que consume la landing; sin él el mapa diverge).

### Step 2: Actualizar el guardrail

En `tests/test_ci_config.py`, `expected_paths` (`:672-688`) agrega
`"data/normalized/mapa_comunal.geojson"` en la posición correspondiente y
extiende el docstring: el GeoJSON es un asset derivado versionado
(ADR-021 excluye raw/imágenes, no este).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k durable -v` → verde.

### Step 3: Verificación de que el script lo genera

Con datos de geometría presentes (si el repo ya tiene
`data/normalized/geometria_comunal.parquet`):
- `PYTHONPATH=src ./.venv/bin/python scripts/build_geometria_comunal.py --help`
  lista el modo/flag que escribe el mapa (verifica que el flujo normal del
  workflow lo incluye; si el script tiene un flag para omitirlo, confirma que
  el workflow no lo usa).
- Si el script requiere red/geo deps para una corrida real, basta la
  inspección: `grep -n "OUTPUT_MAPA_PATH" scripts/build_geometria_comunal.py`
  muestra escritura incondicional tras el fetch (línea 83).

**Verify**: `grep -n "is_file\|exists" scripts/build_geometria_comunal.py | head`
no muestra una rama que lo omita; si la hay, reporta.

## Test plan

- Guardrail de texto actualizado (`test_commit_stages_only_durable_geometry_artifacts`).
- No se agrega test de workflow real; el contrato es el grep del test.

## Done criteria

- [ ] `grep -n "mapa_comunal.geojson" .github/workflows/geometria-comunal.yml` → 1 match en el bloque de commit
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -k durable -v` → verde
- [ ] `make lint && make format-check` → exit 0
- [ ] `make doctor` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `build_geometria_comunal.py` no escribe el geojson cuando corre en el
  workflow (p. ej. flag `--skip-mapa` en el workflow), detente y reporta: el
  fix sería distinto (remover el flag, no commitear).
- Si el GeoJSON supera el límite de pre-commit `check-added-large-files`
  (`--maxkb=500`), reporta el tamaño: hoy ~604 KB y el workflow commitea con
  `git add -f` (hook local no corre en CI, pero un contributor podría
  bloquearse). Si es así, STOP y propone excepción en `.pre-commit-config.yaml`
  en vez de improvisar.

## Maintenance notes

- Al agregar un asset derivado nuevo al refresh de geometría, agregarlo a la
  misma lista y al test.
- El mapa de la landing y el parquet candidate ahora avanzan juntos; si el
  workflow falla a mitad, el commit es atómico (un solo `git add`/`commit`).
- **Deferred:** regenerar el mapa en el build diario (para que un refresh
  manual sin workflow no deje el asset viejo) — hoy el script requiere el
  fetch BCN y no debe correr a diario; reevaluar si cambia la cadencia.
