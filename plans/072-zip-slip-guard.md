# Plan 072: Validar miembros del ZIP antes de extractall (zip-slip/symlink)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/chile_hub/data_manager.py tests/test_data_manager.py tests/test_chile_hub.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`_extract_bundle` hace `archive.extractall()` sobre el ZIP descargado sin
inspeccionar `namelist()`. El checksum SHA-256 verifica el bundle contra un
`.sha256` de la **misma** release de GitHub — no añade un dominio de
confianza distinto. Si la release se viera comprometida (supply chain), un
miembro con `../` o un symlink permitiría escritura arbitraria fuera del
directorio de caché en la máquina de cada consumidor que corre
`chile-hub cache update`. Es el clásico zip-slip, atenuado solo por la
confianza en el mantenedor.

## Current state

- `src/chile_hub/data_manager.py:371-375`:
  ```python
  def _extract_bundle(self, bundle_path: Path) -> None:
      if self.normalized_dir.exists():
          shutil.rmtree(self.normalized_dir)
      with zipfile.ZipFile(bundle_path) as archive:
          archive.extractall(self.version_cache_dir)
  ```
- El bundle legítimo (`chile-hub-publishable-bundle.zip`) tiene 56 entradas,
  todas bajo `data/normalized/` — el allowlist no rompería nada actual.
- El patrón de errores del módulo es `ChileHubDataError` (ver `clear()` en
  `data_manager.py:199-207`).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `./.venv/bin/pytest tests/test_data_manager.py tests/test_chile_hub.py -q` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope**:
- `src/chile_hub/data_manager.py` (`_extract_bundle`)
- `tests/test_data_manager.py`

**Out of scope**:
- El descargador (`update()`/checksum) — ya es robusto.
- Otros consumers de ZIP en el repo.

## Git workflow

- Branch: `advisor/072-zip-slip-guard`
- Conventional commits, uno por paso lógico.
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Valida los miembros antes de extraer

En `_extract_bundle`, antes de `extractall`, itera `archive.infolist()` y
rechaza (con `ChileHubDataError` y el nombre del miembro en el mensaje):
- `member.filename` que no empiece por `data/normalized/`
- `member.filename` con `..` o `\` (path traversal)
- `member.is_symlink()` o `member.is_dir()` con path absoluto (`/` inicial)
- `member.filename` vacío o `.`

Extrae miembro a miembro con `arcname` sanitizado, o mantén `extractall`
solo tras validar toda la lista (equivalente si el allowlist es estricto).

**Verify**: `./.venv/bin/pytest tests/test_data_manager.py -q` → all pass.

### Step 2: Tests de regresión

En `tests/test_data_manager.py` (modelar sobre `GeoCacheIntegrityTests` /
`ChileHubDataManagerUnitTests`), agrega:
- `test_extract_rejects_zip_slip_member` — ZIP sintético con miembro
  `../evil.txt`; assert `ChileHubDataError` y que el archivo NO se creó.
- `test_extract_rejects_symlink_member` — ZIP con symlink; assert error.
- `test_extract_accepts_legitimate_bundle` — ZIP con entradas bajo
  `data/normalized/`; assert extracción ok (reusa el patrón del bundle
  sintético existente en `ChileHubDataManagerUnitTests`).

**Verify**: `./.venv/bin/pytest tests/test_data_manager.py -q -k "extract"` → all pass.

## Test plan

- 3 tests nuevos en `tests/test_data_manager.py` (los del Step 2).
- Modelar sobre `ChileHubDataManagerUnitTests::test_extract_bundle_cleans_existing_normalized_dir`.
- Verificación: suite focal + suite completa.

## Done criteria

- [ ] `_extract_bundle` rechaza miembros fuera de `data/normalized/`
- [ ] 3 tests nuevos pasan
- [ ] El bundle legítimo se extrae sin cambios
- [ ] `make lint && make format-check` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

- Algún bundle legítimo del pasado tiene entradas fuera de `data/normalized/`
  (el allowlist rompería `cache update` para cachés existentes — investigar
  antes de continuar).

## Maintenance notes

- Si en el futuro el bundle incluye `contracts/` (Plan 074), ampliar el
  allowlist a ese prefijo — el test de bundle legítimo lo detectará.
