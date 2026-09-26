# Plan 108: el gate "Check build-synced files" bloquea el publish diario con datos del día

> **Requiere aprobación del operador**: toca `.github/workflows/pipeline-check.yml`
> y `scripts/verify_pipeline.py`. No se editó ningún workflow.
>
> **Drift check**: `git log -1 --format=%h origin/main` en `aeb2c0f` o un
> descendiente, y `grep -n "Build-synced files are stale" .github/workflows/pipeline-check.yml`
> debe devolver una sola línea dentro del step "Check build-synced files".

## Status

- **Priority**: P1 (el schedule diario no publica desde 2026-08-13)
- **Effort**: S
- **Risk**: MED (toca el camino de publicación)
- **Category**: CI / pipeline
- **Planned at**: commit `aeb2c0f`, 2026-09-26

## Diagnóstico

Runs programados de `pipeline-check.yml`: el último `success` fue el
2026-08-12. Desde el 2026-08-13 todos fallan en *Build and verify data*, en el
step "Check build-synced files". Run de referencia: #702, id `36150508540`,
del 2026-09-25, sobre `039fc03`.

El gate hace `git diff --quiet -- index.html app.js README.md` después de
`python src/build_dev_db.py`. Desde `378eba0` (2026-07-08), `README.md` está
incluido en esa comparación. El README lleva bloques **derivados de los datos
del día**:

- La tabla de capas, con conteos y estado live/fallback por dataset.
- `HEALTH_SUMMARY`, con el conteo `ok`/`warn`, que depende de la frescura y por
  lo tanto de la fecha.
- `QUALITY_SUMMARY`.

Este es el diff real del run #702, sacado del log del job `108122522900`:

| Capa | README commiteado | Build de CI | Tipo |
|:---|:---|:---|:---|
| Establecimientos de Salud | 5717 | 5743 | dato nuevo (mensual) |
| Empresas (RES) | ~1 590 979 | ~1 609 373 | dato nuevo (mensual) |
| Partidos Políticos | 36 | 37 | dato nuevo |
| Calidad del Aire | 756 | 1 510 | dato nuevo (diaria) |
| Permisos de Edificación | 8 650 live | 2 fallback | **regresión real**: `039fc03` no tenía el snapshot MINVU, que llegó en `8d30636` |
| Health summary | 20 ok / 1 warn | 19 ok / 2 warn | derivado |

El diff no muestra timestamps ni cambios de orden. Se descarta el no
determinismo (tipo b) por inspección.

### Por qué es un deadlock y no una regeneración olvidada

El único paso que escribe el README regenerado en `main` es *Publish verified
data* (`git add ... README.md` en "Commit refreshed artifacts"). Ese job
depende del gate. Cada vez que un conteo cambia legítimamente, el gate falla y
el publish se salta, así que el README nunca se actualiza y el día siguiente
vuelve a fallar. Solo sale del ciclo si alguien regenera el README a mano y
luego un run pasa el mismo día. Eso ocurrió el 2026-09-25: el refresh manual en
`8d30636`, más el `workflow_dispatch` `36180604630` en success, publicaron
`c2b04b1`. El próximo cambio mensual de salud o empresas, o la variación diaria
de calidad del aire, vuelve a bloquear el schedule.

## Qué protege hoy el gate sobre README (y no se debe perder)

| Incidente | ¿Lo atrapa otra cosa? |
|:---|:---|
| `permisos_edificacion` en fallback (2026-09-2x) | **Sí.** `verify_pipeline.py --profile publication` (`verify_publication_policy`) exige `source_mode ∈ {live, monthly}` a los datasets `stable_publishable`, y el registro marca `permisos_edificacion` como `allowed_for_dev_blocked_for_publication`. |
| `autoridades_electas` con 155 filas y 0 senadores (2026-07-19/20) | **No.** Corre en modo live con `fallback_to_last_snapshot`, el contrato no exige filas mínimas ni verifica los senadores, y `verify_pipeline.py` no revisa caídas de conteo. Hoy lo detecta solo este gate. |

## Cambio propuesto

### 1. Gate: `index.html`/`app.js` siguen fallando fuerte; README se informa y se publica

```diff
       - name: Check build-synced files
         if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
         run: |
-          if ! git diff --quiet -- index.html app.js README.md; then
-            git diff -- index.html app.js README.md
-            echo "::error::Build-synced files are stale. Run python src/build_dev_db.py and commit index.html/app.js/README.md."
+          # README.md lleva bloques derivados de los datos del día (tabla de
+          # capas, health/quality). Los lleva a main el job publish ("Commit
+          # refreshed artifacts"); exigir que ya estén commiteados bloquea el
+          # publish que los actualizaría (deadlock 2026-08-13 → 2026-09-25, plan 108).
+          if ! git diff --quiet -- README.md; then
+            git diff -- README.md
+            echo "::notice::README.md cambia con los datos del día; lo commitea el job publish."
+          fi
+          if ! git diff --quiet -- index.html app.js; then
+            git diff -- index.html app.js
+            echo "::error::Build-synced files are stale. Run python src/build_dev_db.py and commit index.html/app.js."
             exit 1
           fi
```

`index.html` y `app.js` no dependen de conteos diarios. Sus derivados son el
JSON-LD del catálogo y el cache-buster, y `check_landing_sync.py` ya los valida
en cada push. Por eso conservan el fail-loud. La deriva estructural del README
(hechos hardcodeados) la sigue atrapando `sync_docs.py --check` en cada push y
PR.

### 2. Compensación obligatoria: guard de caída de conteo en el perfil `publication`

Este cambio va en el mismo PR que el paso 1, **no después**. En
`verify_publication_policy` de `scripts/verify_pipeline.py`, para cada dataset
`stable_publishable`, se compara el `record_count` del build contra el de
`data/normalized/pipeline_metadata.json` en `HEAD` (el último publicado, con
`git show HEAD:...`). Se registra una violación si cae más de un umbral, con 20%
como punto de partida. Además:

- Se agrega un override explícito (`--allow-record-drop <dataset>`) para caídas
  legítimas.
- Se agregan tests: uno con una caída de 205→155 que debe fallar, y uno con
  756→1510 o 5717→5743 que debe pasar.

Con esto, el incidente de autoridades sigue abortando el publish, y ahora con
un mensaje explícito en vez de un diff de README.

### Alternativa descartada

Hacer que el step de build auto-commitee el README antes del gate, como el job
"Auto-sync docs". Eso duplica la escritura en `main`, que ya hace publish, y
reabre las carreras release↔publish documentadas en el workflow.

## Verificación

1. `make doctor` y `.venv/bin/python -m pytest tests/ -q` (incluye
   `test_ci_config.py`: revisar si algún guardrail fija el texto del gate y
   actualizarlo en el mismo commit).
2. Tras el merge: el operador dispara `gh workflow run pipeline-check.yml -f publish=true`
   (o espera el schedule de ~14:30 UTC) y confirma lo siguiente:
   - "Build and verify data" en success, con el `::notice` si hay diff de README.
   - "Publish verified data" en success.
   - Un commit `chore(data): daily refresh` que incluye `README.md`.
3. Un segundo schedule consecutivo en success confirma que el deadlock no se
   repite.

## Riesgos

- **Pérdida de señal.** Una regresión de datos que antes se veía como diff de
  README ahora pasa, salvo que la atrape `verify_pipeline`. Por eso el paso 2 es
  obligatorio. Las regresiones a fallback ya están cubiertas.
- **Umbral mal calibrado.** Un umbral muy bajo produce falsos positivos en
  datasets volátiles como calidad del aire. En ese caso se ajusta el umbral por
  dataset en el registro, no se desactiva el guard.

## Rollback

Revertir el commit del PR. El gate vuelve a comparar README y el schedule
vuelve a depender de refrescos manuales. No hay migración de datos.
