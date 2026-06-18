# Plan 003: Validar metadatos JSON antes de usarlos en el build pipeline

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**: `git diff --stat ba2f434..HEAD -- src/build_dev_db.py`
> If `src/build_dev_db.py` changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `ba2f434`, 2026-06-13
- **Resolved**: 2026-06-17 — fixed independently; metadata guards exist for all 10 datasets at build_dev_db.py:2092-2168, plus schema validation in load_metadata()

## Why this matters

`build_dev_db.py:main()` carga `comunas.metadata.json` y
`indicadores.metadata.json` vía `load_metadata()`, que retorna `None` cuando
el archivo no existe. El código inmediatamente intenta acceder a claves del
resultado (`indicadores_metadata["indicator_codes"]`, `**comunas_metadata`)
sin verificar que no sea `None`. Si un extractor falla parcialmente y solo
genera el CSV pero no el metadata JSON, el build crashea con un `TypeError`
poco informativo en vez de un mensaje claro. Esto es particularmente probable
en CI después de un fallo de red o un timeout durante la extracción.

## Current state

- `src/build_dev_db.py:406-410` — `load_metadata()` retorna `None` si el
  archivo no existe:

```python
# src/build_dev_db.py:406-410
def load_metadata(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

- `src/build_dev_db.py:1341-1348` — `main()` carga los metadatos sin validar
  que existan antes de usarlos:

```python
# src/build_dev_db.py:1341-1348
if not os.path.exists(comunas_csv) or not os.path.exists(indicadores_csv):
    raise SystemExit(
        "Error: No se encuentran los archivos CSV en staging. Corre los extractores primero."
    )

comunas_metadata = load_metadata(COMUNAS_METADATA_PATH)
indicadores_metadata = load_metadata(INDICADORES_METADATA_PATH)
indicadores_metadata["indicator_codes"] = sorted(
    df_code for df_code in indicadores_metadata.get("indicator_codes", [])
)
```

- Nótese que la línea 1348 usa `.get()` como defensa parcial, pero las líneas
  siguientes (1416, 1427, 1438, 1449) hacen `**comunas_metadata` sin
  verificación — si `comunas_metadata` es `None`, eso levanta `TypeError:
  cannot unpack non-iterable NoneType object`.

- Convención del proyecto: el pipeline debe fallar ruidosamente con mensajes
  claros (`raise SystemExit("Error: ...")`), no con tracebacks de Python.
  Ver `AGENTS.md` §4.2 y usos existentes como `main():1342`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Run build | `make build` | exit 0 |
| Run full pipeline | `make refresh` | exit 0 |
| Run tests | `make test` | exit 0 |
| Run lint | `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `src/build_dev_db.py`

**Out of scope** (do NOT touch):
- `src/extractors/` — los extractores son los que generan los metadata JSON,
  pero este plan solo agrega validación en el lado del build.
- `data/` — nunca modificar `data/normalized/` manualmente.
- Cambios en la estructura del metadata JSON.

## Steps

### Step 1: Agregar guardas después de cada `load_metadata()` en main()

En `main()`, después de cada llamada a `load_metadata()`, agregar una
verificación explícita de que el resultado no es `None`, con un mensaje
de error claro que indique qué archivo falta y cómo resolverlo.

```python
# Después de comunas_metadata = load_metadata(COMUNAS_METADATA_PATH)
if comunas_metadata is None:
    raise SystemExit(
        "Error: No se encuentra comunas.metadata.json en data/staging/. "
        "Corre el extractor territorial primero: python src/extractors/subdere_extractor.py"
    )

# Después de indicadores_metadata = load_metadata(INDICADORES_METADATA_PATH)
if indicadores_metadata is None:
    raise SystemExit(
        "Error: No se encuentra indicadores.metadata.json en data/staging/. "
        "Corre el extractor de indicadores primero: python src/extractors/bcentral_extractor.py"
    )
```

**Verify**: Simular el escenario de error borrando temporalmente un metadata
JSON y corriendo `make build`. Debe mostrar el mensaje de error claro y
terminar con exit code distinto de cero (SystemExit).

### Step 2: Ejecutar el pipeline completo para verificar que no hay regresión

Con los metadata JSON existentes (generados por extractores previos), correr
el build y los tests para confirmar que la validación adicional no interfiere
con el flujo normal.

**Verify**: `make build` → exit 0. `make test` → exit 0, todos los tests
pasan.

## Test plan

- Los tests existentes en `tests/test_pipeline_logic.py` (`PipelineLogicTests`)
  ya cubren el caso de staging inputs faltantes (`test_build_main_fails_when_staging_inputs_are_missing`).
  Este plan extiende ese patrón a los metadata JSON.
- Si se desea un test específico, se puede agregar a `PipelineLogicTests` un
  caso que tenga CSV presente pero metadata JSON ausente, y verificar que
  `build_main()` levanta `SystemExit` con un mensaje que contenga
  "metadata.json".
- El test existente en `test_pipeline_logic.py:40-46` sirve como patrón
  estructural (usa `patch` + `assertRaisesRegex(SystemExit, ...)`).

## Done criteria

- [ ] `make build` sale con exit 0 cuando los metadata JSON existen
- [ ] Si `comunas.metadata.json` no existe, el build falla con un mensaje
      claro que menciona el archivo faltante y cómo generarlo
- [ ] Si `indicadores.metadata.json` no existe, el build falla con un mensaje
      claro que menciona el archivo faltante y cómo generarlo
- [ ] `make test` sale con exit 0 (todos los tests existentes pasan)
- [ ] `make lint` sale con exit 0
- [ ] Ningún archivo fuera de `src/build_dev_db.py` fue modificado

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las líneas citadas en "Current state" no coincide con los
  excerpts (el archivo cambió desde que este plan fue escrito).
- `make build` o `make test` fallan en el flujo normal (con metadata JSON
  existentes) después del cambio.
- La validación agregada interfiere con algún test existente.

## Maintenance notes

- Si se agregan nuevos datasets con sus propios metadata JSON, cada uno
  necesitará una guarda equivalente en `main()`.
- Este plan no cambia el comportamiento de `load_metadata()` — solo agrega
  validación en el caller. Si en el futuro se prefiere que `load_metadata()`
  misma lance el error, se puede refactorizar, pero requeriría actualizar
  todos los call sites.
- Los extractores son responsables de generar los metadata JSON; este plan
  solo mejora el mensaje de error cuando no lo hacen.
