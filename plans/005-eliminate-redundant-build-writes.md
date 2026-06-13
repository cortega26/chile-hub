# Plan 005: Eliminar escrituras redundantes en la sección final del build

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
- **Depends on**: none (pero ejecutar después del plan 003 idealmente)
- **Category**: perf
- **Planned at**: commit `ba2f434`, 2026-06-13

## Why this matters

La sección final de `main()` en `build_dev_db.py` (líneas 1491–1546) tiene
tres ineficiencias que suman tiempo de build y complejidad innecesaria:

1. **Escrituras redundantes**: `write_artifact_manifest()` se llama 3 veces
   (líneas 1516, 1530, y dentro de `attach_publishable_package_to_manifest`
   en 1533). `write_hub_bundle_json()` se llama 2 veces (1519, 1536).
   `write_overview_json()` y `write_overview_markdown_file()` se llaman 2
   veces cada una (1528–1529, 1545–1546).

2. **Patrón write-then-read-back**: 6 artifacts JSON se escriben a disco y
   en la línea siguiente se vuelven a leer con `json.load()`. El dict ya
   está en memoria antes del write; la re-lectura es puro overhead de I/O.

3. **build_hub_health() llamado 2 veces** con los mismos datos: directamente
   en línea 1498 y dentro de `write_status_markdown_file()` →
   `build_status_markdown()` → `build_hub_health()`.

La causa raíz es un build de dos fases: Fase 1 crea manifest/bundle/overview
sin ZIP; Fase 2 crea el ZIP, adjunta el package al manifest, y reconstruye
bundle/overview con los metadatos del ZIP. La Fase 2 es necesaria, pero la
Fase 1 puede ser eliminada — el manifest puede escribirse una sola vez
después de que el ZIP está listo.

## Current state

- `src/build_dev_db.py:1491-1546` — la sección a refactorizar:

```python
# Fase 1: escribe metadata, health, status, catalog, reportes, manifest
metadata_output = write_pipeline_metadata(dataset_metadata, validations_with_freshness)
with open(metadata_output, encoding="utf-8") as f:
    pipeline_metadata = json.load(f)           # ← write-then-read
write_status_markdown_file(pipeline_metadata)   # llama build_hub_health() internamente
hub_health = build_hub_health(pipeline_metadata) # ← 2ª llamada a build_hub_health
hub_health_output = write_hub_health_json(hub_health)
# ... escribe hub_status, hub_health.md, catalog, redistribution, provenance, drift ...
artifact_manifest_output = write_artifact_manifest()  # ← 1ª escritura manifest
with open(artifact_manifest_output, encoding="utf-8") as f:
    artifact_manifest = json.load(f)           # ← write-then-read
hub_bundle_output = write_hub_bundle_json(...) # ← 1ª escritura hub_bundle
with open(hub_bundle_output, encoding="utf-8") as f:
    hub_bundle = json.load(f)                  # ← write-then-read
overview = build_overview(hub_health, hub_bundle, artifact_manifest)
overview_output = write_overview_json(overview) # ← 1ª escritura overview
write_overview_markdown_file(overview)          # ← 1ª escritura overview.md

# Fase 2: crea ZIP y reconstruye todo con metadatos del paquete
artifact_manifest_output = write_artifact_manifest()  # ← 2ª escritura manifest (???)
zip_output = write_publishable_bundle_zip()
sha256_output = write_publishable_bundle_sha256(zip_output)
artifact_manifest_output = attach_publishable_package_to_manifest(zip_output, sha256_output)  # ← 3ª escritura
with open(artifact_manifest_output, encoding="utf-8") as f:
    artifact_manifest = json.load(f)           # ← write-then-read
hub_bundle_output = write_hub_bundle_json(...) # ← 2ª escritura hub_bundle
with open(hub_bundle_output, encoding="utf-8") as f:
    hub_bundle = json.load(f)                  # ← write-then-read
overview = build_overview(hub_health, hub_bundle, artifact_manifest)
overview_output = write_overview_json(overview) # ← 2ª escritura overview
write_overview_markdown_file(overview)          # ← 2ª escritura overview.md
```

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Run build | `make build` | exit 0 |
| Verify artifacts | `make verify` | exit 0 |
| Run tests | `make test` | exit 0 |
| Run lint | `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `src/build_dev_db.py` — solo la sección `main()` desde línea ~1491 hasta
  el final (línea ~1560)

**Out of scope** (do NOT touch):
- `write_publishable_bundle_zip()`, `write_publishable_bundle_sha256()`,
  `attach_publishable_package_to_manifest()` — estas funciones se mantienen
  igual; solo cambia el orden en que se llaman.
- Cualquier función fuera de `main()`.
- `scripts/package_publishable_bundle.py` — maneja ZIP para publicación
  externa; no se toca.

## Steps

### Step 1: Eliminar la Fase 1 de artifact_manifest, hub_bundle y overview

La Fase 1 debe seguir generando `pipeline_metadata.json`, `hub_status.json`,
`hub_health.json`, `dataset_catalog.json`, `redistribution_report.json`,
`provenance_report.json`, `drift_report.json` y sus correspondientes
archivos `.md`. Estos no dependen del ZIP.

Pero `artifact_manifest.json`, `hub_bundle.json`, `overview.json` y
`overview.md` solo deben generarse **una vez**, después de que el ZIP está
listo.

El código reorganizado debe ser:

```
1. write_pipeline_metadata(...)          → se lee pipeline_metadata (dict)
2. write_status_markdown_file(...)       → llama build_hub_health() interno
3. hub_health = build_hub_health(...)    → reutilizar, no recalcular
4. write_hub_health_json(hub_health)
5. build_hub_status(hub_health) + write_hub_status_json(...)
6. write_hub_health_markdown_file(hub_health)
7. write_dataset_catalog(...)            → se lee catalog (dict)
8. write_dataset_catalog_markdown_file(catalog)
9. build_redistribution_report(catalog) + write_redistribution_report_json(...) + write_redistribution_report_markdown_file(...)
10. build_provenance_report(catalog) + write_provenance_report_json(...) + write_provenance_report_markdown_file(...)
11. build_drift_report(catalog) + write_drift_report_json(...) + write_drift_report_markdown_file(...)
12. write_artifact_manifest()            → PRIMERA Y ÚNICA VEZ (sin ZIP aun)
13. zip_output = write_publishable_bundle_zip()
14. sha256_output = write_publishable_bundle_sha256(zip_output)
15. attach_publishable_package_to_manifest(zip_output, sha256_output)
16. Leer artifact_manifest actualizado
17. write_hub_bundle_json(...)           → ÚNICA VEZ
18. Leer hub_bundle
19. overview = build_overview(hub_health, hub_bundle, artifact_manifest)
20. write_overview_json(overview)        → ÚNICA VEZ
21. write_overview_markdown_file(overview) → ÚNICA VEZ
```

### Step 2: Pasar dicts en memoria en vez de hacer write-then-read-back

Donde una función de escritura retorna el path y en la línea siguiente se
hace `json.load()` del mismo archivo, pasar directamente el dict que ya está
en memoria.

Ejemplo con `write_pipeline_metadata()`:

```python
# Antes (write-then-read-back):
metadata_output = write_pipeline_metadata(dataset_metadata, validations_with_freshness)
with open(metadata_output, encoding="utf-8") as f:
    pipeline_metadata = json.load(f)

# Después (pasar el dict directamente):
metadata_output = write_pipeline_metadata(dataset_metadata, validations_with_freshness)
pipeline_metadata = {
    "generated_at_utc": datetime.now(UTC).isoformat(),
    "datasets": dataset_metadata,
    "validations": validations_with_freshness,
}
```

Como `write_pipeline_metadata()` construye el dict internamente y lo
serializa, hay dos opciones: (a) extraer la construcción del dict a una
función separada que retorne el dict, o (b) construir el dict inline en
`main()` y pasarlo tanto a la función de escritura como al código siguiente.

La opción (b) es más simple para este plan:

```python
pipeline_metadata = {
    "generated_at_utc": datetime.now(UTC).isoformat(),
    "datasets": dataset_metadata,
    "validations": validations_with_freshness,
}
write_pipeline_metadata(pipeline_metadata)  # modificada para recibir el dict
```

**Verify**: `make build && make verify` → exit 0. El contenido de los
archivos JSON debe ser idéntico al producido antes del cambio (mismos
datos, mismo `generated_at_utc` excepto el timestamp que es naturalmente
diferente en cada build).

### Step 3: Reutilizar el resultado de build_hub_health()

`write_status_markdown_file()` internamente llama `build_status_markdown()`
que a su vez llama `build_hub_health()`. Para evitar esta segunda llamada,
pasar `hub_health` como parámetro opcional.

Modificar `write_status_markdown_file()` en `pipeline_status_utils.py` para
aceptar un parámetro `health=None`. Si no se provee, calcularlo; si se
provee, usarlo directamente.

```python
# src/pipeline_status_utils.py
def write_status_markdown_file(metadata, path=STATUS_MARKDOWN_PATH, health=None):
    if health is None:
        health = build_hub_health(metadata)
    Path(path).write_text(build_status_markdown(metadata), encoding="utf-8")
```

O, más simple: en `main()`, llamar `build_hub_health()` UNA vez al principio
de la sección de reportes, y pasar el resultado a todas las funciones que lo
necesiten.

**Verify**: `make build && make verify` → exit 0.

### Step 4: Ejecutar pipeline completo y tests

**Verify**: `make refresh` → exit 0. `make test` → exit 0. `make lint` → exit 0.

## Test plan

- Los tests existentes (`make test`) validan la estructura y contenido de
  `artifact_manifest.json`, `hub_bundle.json`, `overview.json` y demás
  artifacts. Deben seguir pasando exactamente igual.
- `make verify` corre todas las verificaciones de integridad de artifacts.
- Si algún test falla, comparar el artifact generado antes y después del
  cambio con `diff` para identificar la diferencia.
- El test `test_pipeline_logic.py:131` (`test_write_publishable_bundle_zip_fails_before_creating_partial_zip`)
  prueba `write_publishable_bundle_zip()` directamente — no debería afectarse.

## Done criteria

- [ ] `make build` sale con exit 0
- [ ] `make verify` sale con exit 0
- [ ] `make test` sale con exit 0 (todos los tests pasan)
- [ ] `make lint` sale con exit 0
- [ ] `artifact_manifest.json` se escribe exactamente 1 vez durante el build
- [ ] `hub_bundle.json` se escribe exactamente 1 vez durante el build
- [ ] `overview.json` y `overview.md` se escriben exactamente 1 vez cada uno
- [ ] `build_hub_health()` se llama exactamente 1 vez durante el build
- [ ] Ningún archivo fuera de `src/build_dev_db.py` y
      `src/pipeline_status_utils.py` fue modificado

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las líneas citadas en "Current state" no coincide con los
  excerpts (el archivo cambió desde que este plan fue escrito).
- `make build` falla después de la refactorización.
- `make verify` detecta diferencias en el contenido de los artifacts
  generados (más allá del timestamp `generated_at_utc`).
- La refactorización requiere tocar funciones fuera de `main()` de una
  manera que rompe otros callers.
- El orden de las operaciones afecta la corrección de los artifacts
  (ej. `hub_bundle.json` debe incluir el package ZIP; si se genera antes,
  no lo incluirá).

## Maintenance notes

- Si se agregan nuevos reportes al pipeline, deben seguir el mismo patrón:
  escribir una vez, mantener el dict en memoria si se necesita downstream.
- `attach_publishable_package_to_manifest()` reescribe el manifest
  internamente — eso es aceptable porque necesita agregar metadata del
  paquete que no existe antes de crear el ZIP.
- Este plan no elimina la necesidad de la Fase 2 (el ZIP debe existir antes
  de adjuntarlo al manifest). Solo elimina la Fase 1 redundante.
- Si en el futuro el ZIP se mueve a un paso separado del pipeline, la
  estructura resultante de este plan (manifest → ZIP → attach → bundle →
  overview) es más fácil de dividir.
