# ADR-021: Snapshot de release liviano — geometría cruda fuera de git y wasm EH eliminado

**Fecha:** 2026-09-25
**Estado:** accepted
**Decisión:** Los snapshots crudos de geometría (`data/raw/bcn_geometria_comunal_*.json`) y el CSV intermedio (`data/staging/geometria_comunal.csv`) dejan de versionarse; el workflow de geometría los sube como assets del prerelease `geometry-audit`. Se elimina `vendor/duckdb/duckdb-eh.wasm` (no referenciado). El `duckdb-mvp.wasm` se mantiene vendoreado; moverlo a CDN queda diferido.

## Contexto

Zenodo archiva el tarball del repositorio en cada tag. El árbol de `v1.37.6` pesa **412 MB**, y su ingesta quedó ~1 h en estado "Received" sin emitir el DOI. El peso no viene del artefacto publicado: 237 MB son snapshots de geometría (2 JSON de 81 MB + CSV de 75 MB) y 36 MB son la variante `duckdb-eh.wasm`, que ningún import del playground usa.

Plan 064 (2026-07-29) forzó el commit de las 5 familias de geometría —incluidos raw y CSV— para publicar el carril candidate desde CI sin debilitar el límite de 500 KB de pre-commit. Ese diseño no consideró el costo en el tarball de cada release; el resto de los datasets ya sigue la regla por defecto de `data/*` gitignored (raw local/CI, no versionado).

## Decisión

1. **Untrack de auditoría cruda**: `git rm --cached` de los 2 JSON y del CSV. Se mantienen en disco (ignorados) y el workflow los publica en un **prerelease** `geometry-audit` (`gh release upload --clobber`), que es permanente y no contamina el árbol. El tag `geometry-audit` no colisiona con `tag_format = "v{version}"` de PSR.
2. **Se conserva lo durable**: `geometria_comunal.parquet`, su `.sha256` y `geometria_comunal.metadata.json` siguen versionados (contrato del carril candidate y exclusión `OUT_OF_BAND_STAGING_METADATA`).
3. **Wasm EH fuera**: `duckdb-eh.wasm` se elimina por no estar referenciado. `duckdb-mvp.wasm` (40 MB) se mantiene self-hosted.
4. **CDN diferido**: mover `duckdb-mvp.wasm` a jsDelivr/unpkg exige agregar el origen a la CSP host-wide de Cloudflare (espejada en `scripts/verify_landing.py`) y crea una dependencia externa en una función del landing. No se hace ahora; se reevalúa sólo si el snapshot liviano sigue siendo lento en Zenodo.

## Alternativas consideradas

- **Git LFS**: los tarballs de GitHub no materializan objetos LFS; no reduce el snapshot de Zenodo y agrega cuota. Descartado.
- **Reescribir historia** (`.git` ~2.1 GB): no afecta el tarball del tag (Zenodo archiva el árbol, no la historia) y es destructivo. Descartado.
- **Comprimir JSON/CSV en git**: reduce menos que sacarlos y complica el flujo del extractor. Descartado.
- **CDN para mvp.wasm**: ver punto 4. Diferido.
- **Workflow artifacts para la auditoría**: expiran (90 días). Se prefirió release assets (permanentes).

## Consecuencias

- El árbol de los próximos tags baja de ~412 MB a ~140 MB (≈66%), acelerando la ingesta de Zenodo y el clonado.
- La auditoría cruda de geometría queda en `https://github.com/cortega26/chile-hub/releases/tag/geometry-audit` (assets con timestamp); si supera ~100 assets, podar los más viejos.
- `scripts/build_geometria_comunal.py --skip-fetch` ya no funciona en un clon fresco (el CSV no está en git); sigue funcionando en la misma máquina tras una extracción. Documentado en la ficha del dataset.
- Guardrails en `tests/test_ci_config.py` fijan: rutas durables del commit, upload de auditoría presente, y ausencia del wasm EH.
