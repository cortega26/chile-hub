# Plan 106: Snapshot de release liviano (geometría fuera de git + wasm no usado)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 61b65b8..HEAD -- .github/workflows/geometria-comunal.yml tests/test_ci_config.py playground.js vendor/duckdb/ docs/datasets/geometria_comunal.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: MED (cambia qué se versiona; el artefacto publicado no cambia)
- **Depends on**: none
- **Category**: infra / release
- **Planned at**: commit `61b65b8`, 2026-09-25

## Why this matters

Zenodo archiva el **tarball del repo en cada tag**. El árbol de `v1.37.6` pesa
**412 MB**, y su ingesta quedó en "Received" (spinner) por ~1 h sin publicar el
DOI. Los archivos que lo inflan no son el artefacto publicado:

| Archivo | Peso | Rol real |
|---|---:|---|
| `data/raw/bcn_geometria_comunal_*.json` (×2) | 162 MB | auditoría cruda (gitignored por defecto; geometría fue la excepción force-add de Plan 064) |
| `data/staging/geometria_comunal.csv` | 75 MB | intermedio del workflow de geometría (el build diario no lo lee) |
| `vendor/duckdb/duckdb-eh.wasm` | 36 MB | variante EH **no referenciada** (playground.js usa solo mvp) |

Quitarlos deja el snapshot en ~140 MB sin tocar ningún artefacto publicado
(parquet, metadata, catálogo, bundle). Los raw/CSV de geometría pasan a un
release de auditoría (`geometry-audit`) — permanentes, fuera del árbol.

## Current state

- `git ls-tree -r -l HEAD` ordenado: 81.2+81.2 MB raw, 75.4 MB CSV, 38.7+34.0 MB wasm, resto ≤29 MB.
- `.github/workflows/geometria-comunal.yml:100-121` commitea (force-add) parquet, CSV, metadata, sha256 y raw JSONs.
- `tests/test_ci_config.py:667-685` (`test_commit_stages_only_allowed_geometry_artifacts_and_checksum`) fija esa lista exacta de rutas.
- `playground.js` usa `vendor/duckdb/duckdb-mvp.wasm`; `duckdb-eh.wasm` no aparece en ningún import/fetch.
- `src/builders/_shared.py`/`build_dev_db.py` no referencian staging de geometría; `scripts/verify_pipeline.py:117` sólo excluye su **metadata** (que se mantiene).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Tamaño del árbol | `git ls-tree -r -l HEAD \| awk '{s+=$4} END {printf "%.1f MB\n", s/1024/1024}'` | declared | ≤ 150 MB tras el cambio |
| Guardrails CI | `./.venv/bin/pytest tests/test_ci_config.py -q -k "Geometria or Wasm"` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |
| Landing | `make verify-landing` | declared | passed |

## Scope

**In scope**:
- `.github/workflows/geometria-comunal.yml` (commit list + upload de auditoría)
- `tests/test_ci_config.py` (guardrail de rutas + asserts del upload)
- `vendor/duckdb/duckdb-eh.wasm` (eliminar)
- `docs/datasets/geometria_comunal.md` (dónde vive la auditoría)
- `docs/adr/ADR-021-*.md` (decisión)
- `data/raw/bcn_geometria_comunal_*.json`, `data/staging/geometria_comunal.csv` (untrack)

**Out of scope** (do NOT touch):
- `data/normalized/geometria_comunal.parquet` + `.sha256` + `data/staging/geometria_comunal.metadata.json`: se siguen versionando (contrato del carril candidate).
- `duckdb-mvp.wasm` (40 MB): se mantiene vendoreado. Moverlo a CDN exige cambiar la CSP host-wide de Cloudflare (espejada en `scripts/verify_landing.py`) y agrega una dependencia externa al playground; se difiere hasta que el snapshot liviano no baste (ver ADR-021).
- Historia de git (`.git` ~2.1 GB): reescribirla está fuera de alcance; Zenodo archiva el árbol del tag, no la historia.

## Git workflow

- Branch: `advisor/106-slim-release-snapshot`.
- Commits convencionales (`chore(release-snapshot): ...`); no dispara release.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Untrack geometría cruda + staging CSV

`git rm --cached data/raw/bcn_geometria_comunal_*.json data/staging/geometria_comunal.csv`
(mantiene los archivos en disco; `data/*` ya los ignora). Verificar que
`git status` no muestre los archivos como untracked (ignorados) y que el
tamaño del árbol baje ~237 MB.

**Verify**: `git ls-tree -r -l HEAD | awk '{s+=$4} END {printf "%.1f MB\n", s/1024/1024}'` ≤ 175 MB.

### Step 2: Workflow — commit sólo artefactos durables + auditoría a release

En `geometria-comunal.yml`, el loop del step "Commit validated candidate
artifacts" deja sólo parquet, metadata y sha256. Agregar antes/después un step
"Upload raw audit to release assets" con `GH_TOKEN` que cree (si falta) un
**prerelease** `geometry-audit` (`gh release create geometry-audit --target main --prerelease ...`) y suba `data/raw/bcn_geometria_comunal_*.json` +
`data/staging/geometria_comunal.csv` con `--clobber`. El tag `geometry-audit`
no colisiona con PSR (`tag_format = "v{version}"`).

**Verify**: `grep -n "geometry-audit" .github/workflows/geometria-comunal.yml` y `grep -c "data/raw"` en el commit block = 0.

### Step 3: Eliminar el wasm EH no usado

`git rm vendor/duckdb/duckdb-eh.wasm` (no hay referencias en `playground.js`,
`index.html` ni tests). Confirmar que el playground sigue con mvp.

**Verify**: `grep -rn "duckdb-eh\|eh.wasm" --include="*.js" --include="*.html" . | grep -v .venv` → sin resultados; `make verify-landing` OK.

### Step 4: Guardrails

En `tests/test_ci_config.py`:
- Actualizar `test_commit_stages_only_allowed_geometry_artifacts_and_checksum` a las 3 rutas durables.
- Nuevo test: el commit block **no** contiene `data/raw/` ni `data/staging/geometria_comunal.csv`, y el workflow tiene el step de auditoría con `gh release upload` y `geometry-audit`.
- Nuevo test: `vendor/duckdb/duckdb-eh.wasm` no existe y `playground.js` no lo referencia.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -q` → all pass.

### Step 5: ADR + docs

Escribir `docs/adr/ADR-021-snapshot-release-liviano.md` (contexto, decisión,
alternativas: CDN wasm diferido, LFS descartado, history rewrite descartado).
Agregar a `docs/datasets/geometria_comunal.md` una nota de que la auditoría
cruda vive en el prerelease `geometry-audit`.

**Verify**: `make doctor` (sync_docs actualiza el conteo de ADRs del README) y `make docs-build` exit 0.

## Test plan

- Actualizar/extender guardrails de `GeometriaCandidateWorkflowGuardrailTests` (3 asserts nuevos).
- Regresión: `make doctor`, `make verify-landing`, suite completa.
- Medición: tamaño del árbol antes/después (412 → ≤150 MB).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `git ls-tree -r -l HEAD | awk '{s+=$4} END {printf "%.1f MB\n", s/1024/1024}'` ≤ 150 MB
- [ ] `git ls-files data/raw/bcn_geometria_comunal_*.json data/staging/geometria_comunal.csv` vacío
- [ ] `test -f data/normalized/geometria_comunal.parquet && test -f data/staging/geometria_comunal.metadata.json`
- [ ] `test ! -f vendor/duckdb/duckdb-eh.wasm`
- [ ] `grep -q "gh release upload" .github/workflows/geometria-comunal.yml`
- [ ] `./.venv/bin/pytest tests/ -q` exits 0 y `make doctor` exits 0 y `make verify-landing` OK
- [ ] `plans/README.md` status row + `ROADMAP.md` actualizados

## STOP conditions

Stop and report back (do not improvise) if:

- El build diario o `verify_pipeline` resultan depender del CSV/raw de geometría (el grep de recon dice que no; si aparece una dependencia real, detenerse).
- `gh release create --prerelease` con tag `geometry-audit` interfiere con PSR (verificar `tag_format` y el próximo release).
- El tamaño del árbol no baja de 150 MB (indicaría archivos pesados no inventariados).

## Maintenance notes

- El prerelease `geometry-audit` acumula snapshots con timestamp; si supera ~100 assets, podar los más viejos.
- Si en el futuro el snapshot liviano aún tarda en Zenodo, evaluar la parte 3 (mvp.wasm a CDN) con el cambio de CSP en Cloudflare.
