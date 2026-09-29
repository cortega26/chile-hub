# Plan 113: Batch de hardening — unrar, vaciado del espejo HF, escape JSON-LD y quoting en dependabot-lock

> **Executor instructions**: Sigue los pasos en orden; cada uno es independiente
> y tiene su propia verificación. Si algo de "STOP conditions" ocurre, detente y
> reporta. Al terminar, actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/extractors/mineduc_establecimientos_extractor.py scripts/publish_hf_dataset.py src/builders/landing.py scripts/inject_dataset_json_ld.py .github/workflows/dependabot-lock.yml index.html tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (Step 3 y el Plan 114 tocan `index.html`; ejecutar 114 antes o después, nunca en worktrees simultáneos)
- **Category**: security
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Cuatro defectos pequeños de la misma familia (entradas no confiables tratadas
como confiables). Cada uno es barato y su fix elimina una clase de fallo:

1. **`unrar x`** en el extractor de establecimientos MINEDUC extrae un RAR
   descargado de la red respetando paths del archivo, mientras el extractor
   hermano ya usa `unrar e` dentro de un `TemporaryDirectory` (patrón seguro).
2. **`delete_patterns=["data/*.parquet"]`** en el publisher de HF: si la
   selección de capas publicables queda vacía (un rename de
   `publication_track`), el espejo público se vacía en silencio.
3. **JSON-LD sin escapar `<`** en dos emisores, mientras el generador de
   páginas de comuna ya escapaa `</script>`; un `</script>` en la metadata
   rompería el script tag.
4. **`${{ github.head_ref }}` sin comillas** en un `run:` con `contents: write`
   (hoy gateado por `github.actor == 'dependabot[bot]'`, pero es el único sitio
   del repo que interpola un branch name directamente en shell).

## Current state

- `src/extractors/mineduc_establecimientos_extractor.py:80-84`:
  ```python
  cmd = [str(unrar_bin), "x", "-y", str(rar_path), RAW_DIR]
  ```
  Patrón seguro hermano en `src/extractors/mineduc_resultados_extractor.py:179-184`
  (`unrar e -y ... tmp_dir/` dentro de `tempfile.TemporaryDirectory()`).
- `scripts/publish_hf_dataset.py:232-240`:
  ```python
      api.upload_folder(
          ...
          delete_patterns=["data/*.parquet"],
      )
  ```
  `select_publishable_files()` (`:66-124`) puede devolver `parquet_entries`
  vacío (cada dataset skipeado por `publication_track != "stable_publishable"`)
  sin que `main()` lo detecte antes de subir.
- `src/builders/landing.py:156` y `scripts/inject_dataset_json_ld.py:40` usan
  `json.dumps(...)` directo. `scripts/build_comuna_pages.py:353-355` ya tiene
  `_json_for_html` que reemplaza `<`, `>`, `&`. `check_landing_sync.py`
  compara `index.html` byte a byte contra el render (hay que regenerarlo).
- `.github/workflows/dependabot-lock.yml:66`:
  ```yaml
          git push origin HEAD:${{ github.head_ref }}
  ```
  (`:27` usa el mismo valor como `ref:` de checkout.)

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests extractores | `./.venv/bin/pytest tests/test_extractors.py -v -k mineduc` | declared | verde |
| Tests landing/sync | `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -k "Landing or JsonLd or Hf" -v` | declared | verde |
| Regenerar landing | `make build` | declared | exit 0 (regenera index.html/app.js) |
| Gate landing | `python scripts/check_landing_sync.py` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `src/extractors/mineduc_establecimientos_extractor.py`
- `scripts/publish_hf_dataset.py`
- `src/builders/landing.py`
- `scripts/inject_dataset_json_ld.py`
- `.github/workflows/dependabot-lock.yml`
- `index.html` (solo regenerado por `make build`)
- `tests/` (tests focales; ver Test plan)

**Out of scope**:
- `mineduc_resultados_extractor.py` (ya es seguro).
- Cambiar el publisher de HF más allá del guard de selección vacía.
- CSP, fuentes o `privacy.html` (Plan 114).

## Git workflow

- Branch: `advisor/113-security-hardening-batch`
- Un commit por paso: `fix(security): ...` / `fix(landing): ...` (estilo repo).
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_extractors.py -v -k mineduc` verde en checkout
limpio. Si no, STOP.

### Step 1: `unrar x` → `unrar e` en directorio temporal

En `mineduc_establecimientos_extractor.py`, reemplaza la extracción directa a
`RAW_DIR` por el patrón de `mineduc_resultados_extractor.py:179-197`:

- `with tempfile.TemporaryDirectory() as tmp_dir:` + `cmd = [str(unrar_bin),
  "e", "-y", str(rar_path), tmp_dir + "/"]`.
- El glob `*Directorio_Oficial_EE*.csv` pasa a buscar dentro de `tmp_dir`, y la
  selección del CSV se procesa antes de salir del `with` (o copia el CSV
  elegido a `RAW_DIR` con `shutil.copy2` **solo si** el flujo necesita el
  snapshot crudo; verifica qué hace hoy después de extraer).
- Mantén el `# nosec B603` con la razón actualizada.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -v -k mineduc` → verde;
`grep -n '"x", "-y"' src/extractors/mineduc_establecimientos_extractor.py` → 0 matches.

### Step 2: Guard de selección vacía en `publish_hf_dataset.py`

En `main()`, después de `parquet_entries, catalog_json_files =
select_publishable_files()` y **antes** de crear el repo temporal/staging,
agrega:

```python
    if not parquet_entries:
        raise SystemExit(
            "ERROR: la selección de capas publicables quedó vacía — se aborta "
            "para no borrar el espejo HF con delete_patterns. Revisa "
            "publication_track en data/source_registry.json."
        )
```

**Verify**: `grep -n "selección de capas publicables quedó vacía" scripts/publish_hf_dataset.py` → 1 match.
Agrega en `tests/test_ci_config.py` (o `tests/test_pipeline_logic.py`, donde
viva `HfDatasetCardTests`) un test que importe el módulo (está en `scripts/`,
ya en `sys.path` de `test_ci_config.py`) y ejecute `main()` con
`unittest.mock.patch.object(mod, "select_publishable_files", return_value=([], []))`
+ `patch.object(sys, "argv", ["publish_hf_dataset.py", "--repo-id", "x/y"])`,
esperando `SystemExit`.

### Step 3: Escape HTML en los dos emisores JSON-LD

- En `src/builders/landing.py`, dentro de `render_catalog_json_ld_block`
  (`:149-165`), reemplaza `json.dumps(...)` + indentado por una versión que
  además haga `.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")`
  sobre el string serializado (no sobre el JSON crudo antes de indentar; hazlo
  después de `json.dumps` y antes de indentar).
- En `scripts/inject_dataset_json_ld.py:40`, aplica el mismo replace al
  `body`.
- Opción preferida: extraer un helper compartido, p. ej. `json_for_html(obj)`
  en `src/builders/io_utils.py`, y usarlo en ambos + en
  `build_comuna_pages.py` (que ya tiene uno privado equivalente). Mantén el
  formato exacto del bloque para que `check_landing_sync.py` siga pasando.

**Verify**: `make build` → exit 0; `python scripts/check_landing_sync.py` →
exit 0; `./.venv/bin/pytest tests/test_pipeline_logic.py -k "JsonLd or json_ld" -v`
→ verde. Agrega un test unitario con una descripción que contenga
`</script>` y afirma que el render no contiene la secuencia literal.

### Step 4: Quoting de `github.head_ref` en dependabot-lock

En `.github/workflows/dependabot-lock.yml`, pasa el ref por `env:`:

```yaml
        env:
          HEAD_REF: ${{ github.head_ref }}
        run: |
          ...
          git push origin "HEAD:$HEAD_REF"
```

(El `ref:` del checkout en `:27` no requiere cambio; es un input de acción,
no shell.)

**Verify**: `grep -n 'HEAD:\${{' .github/workflows/dependabot-lock.yml` → 0
matches; `grep -n 'HEAD:\$HEAD_REF' ...` → 1.

### Step 5: Cierre

- `make lint`, `make format-check`.
- Actualiza la fila del índice.

## Test plan

- `unrar`: los tests existentes del extractor deben seguir verdes; si alguno
  mockea `subprocess.run` verificando el argv, actualízalo con la nueva forma.
- HF: test nuevo de `main()` con selección vacía → `SystemExit`.
- JSON-LD: test nuevo con `</script>` → secuencia escapada.
- quoting: cubierto por inspección (no hay ejecutor de workflows en tests).

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_extractors.py tests/test_pipeline_logic.py tests/test_ci_config.py -v` → verde
- [ ] `grep -n '"x", "-y"' src/extractors/mineduc_establecimientos_extractor.py` → 0
- [ ] `grep -n "quedó vacía" scripts/publish_hf_dataset.py` → 1
- [ ] `grep -rn "json.dumps" src/builders/landing.py scripts/inject_dataset_json_ld.py` → ninguno sin escape posterior (o helper `json_for_html` usado)
- [ ] `grep -n '\${{ github.head_ref }}' .github/workflows/dependabot-lock.yml` → 0 en bloques `run:`
- [ ] `python scripts/check_landing_sync.py` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si el flujo de `mineduc_establecimientos` necesita el CSV en `data/raw/`
  y copiarlo cambia el snapshot esperado por tests/verify, detente y reporta
  el layout actual antes de improvisar.
- Si `make build` regenera `index.html` con diffs ajenos al escape (p. ej.
  versión de datos), verifica que provienen solo de `make build`; si el diff
  toca secciones no relacionadas, STOP.
- Si `check_landing_sync.py` falla tras el cambio, no lo "arregles" tocando el
  script sin entender por qué el render difiere; reporta.

## Maintenance notes

- Un `delete_patterns` en cualquier futura subida HF es una operación
  destructiva: el guard de selección vacía es la última defensa. Mantenerlo.
- El helper `json_for_html` debe ser la única vía de serializar JSON dentro de
  `<script>`; un test de drifting debería cubrirlo.
- **Deferred:** escapar también `U+2028/U+2029` (riesgo solo en JS inline con
  `JSON.parse`, no en `application/ld+json`); no vale hoy.
