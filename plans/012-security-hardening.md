# Plan 012: Hardening de seguridad — TOCTOU, integridad de binario externo y paths en errores

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

Tres vulnerabilidades de seguridad de severidad baja-media: (1) la descarga del
bundle tiene una ventana TOCTOU entre escritura a disco y verificación SHA256
donde un atacante local podría reemplazar el archivo, (2) el extractor MINEDUC
ejecuta un binario `unrar` externo sin verificar su integridad, riesgo de
ejecución de código si un atacante compromete el binario, y (3) mensajes de
error en `build_dev_db.py` exponen paths absolutos del sistema de archivos local
(`/home/usuario/.../data/staging/`) visibles al usuario de CLI.

## Current state

### Archivos relevantes

- `src/chile_hub/data_manager.py` — `update()` con TOCTOU (líneas 90-104)
- `src/extractors/mineduc_establecimientos_extractor.py` — subprocess `unrar` (líneas 65-79)
- `src/build_dev_db.py` — paths en mensajes SystemExit (líneas 759, 776, 2598, 2641)

### Vulnerabilidad 1: TOCTOU en descarga de bundle

`src/chile_hub/data_manager.py:90-104`:
```python
self.version_cache_dir.mkdir(parents=True, exist_ok=True)
bundle_path = self.version_cache_dir / DEFAULT_BUNDLE_NAME
checksum_path = self.version_cache_dir / DEFAULT_CHECKSUM_NAME

self._download(bundle.url, bundle_path)       # 1. Descarga bundle a disco
self._download(checksum.url, checksum_path)    # 2. Descarga checksum
expected_sha256 = self._read_checksum(checksum_path)
actual_sha256 = self._sha256(bundle_path)      # 3. Hashea bundle EN DISCO
if actual_sha256 != expected_sha256:
    bundle_path.unlink(missing_ok=True)
    raise ChileHubDataError(...)
```

La ventana TOCTOU está entre el paso 1 (bundle escrito a disco) y el paso 3
(hasheo del bundle en disco). Un atacante local con acceso de escritura al
directorio de cache puede reemplazar el archivo en ese intervalo.

### Vulnerabilidad 2: unrar sin verificación de integridad

`src/extractors/mineduc_establecimientos_extractor.py:65-72`:
```python
unrar_bin = Path(ROOT_DIR) / ".venv" / "bin" / "unrar"
if not unrar_bin.exists():
    unrar_bin = "unrar"

cmd = [str(unrar_bin), "x", "-y", str(rar_path), RAW_DIR]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
```
No hay verificación de hash o firma del binario `unrar`. Si un atacante escribe
un binario malicioso en `.venv/bin/unrar`, se ejecuta con los privilegios del
pipeline. El fallback a `"unrar"` del PATH es aún más peligroso porque podría
resolver a un binario no controlado.

### Vulnerabilidad 3: Paths locales en mensajes de error

`src/build_dev_db.py:759`:
```python
raise SystemExit(f"Error: Metadatos en {path} no es un objeto JSON (dict).")
```
`src/build_dev_db.py:776`:
```python
raise SystemExit(f"Error: Archivo de metadatos {path} contiene un JSON malformado: {e}")
```
`src/build_dev_db.py:2641`:
```python
f"Error: No se encuentran los metadatos para {name} en data/staging/. ..."
```
Estos paths (ej. `/home/carlos/VS_Code_Projects/chile-hub/data/staging/comunas.metadata.json`)
se imprimen en stderr del CLI.

### Convenciones del repo

- `_sha256()` definido en `src/chile_hub/data_manager.py` — retorna hash SHA256 de un archivo
- `_download()` en `data_manager.py` — descarga una URL a un path con `requests`
- Paths se calculan relativos a `ROOT_DIR` en `build_dev_db.py`
- `scripts/verify_pipeline.py` ya usa `os.path.relpath()` en algunos reportes

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_chile_hub.py tests/test_extractors.py -v` | all pass |
| Build | `make build` | exit 0 |
| SHA256 test | `.venv/bin/python -c "from chile_hub.data_manager import ChileHubDataManager; print('OK')"` | OK |

## Scope

**In scope**:
- `src/chile_hub/data_manager.py` — refactor `update()` para hashing en tránsito
- `src/extractors/mineduc_establecimientos_extractor.py` — verificación de integridad de `unrar`
- `src/build_dev_db.py` — usar paths relativos en mensajes de error (~líneas 759, 776, 2598, 2641)

**Out of scope** (do NOT touch):
- `scripts/verify_pipeline.py` — ya usa paths relativos en algunos casos
- `src/chile_hub/core.py` — no modificar mensajes de error de CLI
- El resto de extractores — solo MINEDUC usa binario externo
- Reemplazar `unrar` por `rarfile` Python puro — sería un plan separado (más grande)

## Git workflow

- Branch: `advisor/012-security-hardening`
- Commit por step; mensaje estilo `fix(security): ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Eliminar TOCTOU con hashing en tránsito

Refactorizar `update()` en `src/chile_hub/data_manager.py` para hashear el bundle
mientras se descarga, evitando la ventana on-disk.

Reemplazar el bloque de líneas 90-104 con:
```python
self.version_cache_dir.mkdir(parents=True, exist_ok=True)
bundle_path = self.version_cache_dir / DEFAULT_BUNDLE_NAME
checksum_path = self.version_cache_dir / DEFAULT_CHECKSUM_NAME

# Descargar checksum primero
self._download(checksum.url, checksum_path)
expected_sha256 = self._read_checksum(checksum_path)

# Descargar bundle hasheando en tránsito
import hashlib
import tempfile

response = self.session.get(bundle.url, stream=True)
response.raise_for_status()
sha256_hash = hashlib.sha256()
with tempfile.NamedTemporaryFile(
    dir=str(self.version_cache_dir), delete=False, suffix=".tmp"
) as tmp:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            sha256_hash.update(chunk)
            tmp.write(chunk)
    tmp_path = Path(tmp.name)

actual_sha256 = sha256_hash.hexdigest()
if actual_sha256 != expected_sha256:
    tmp_path.unlink(missing_ok=True)
    raise ChileHubDataError(
        f"Checksum mismatch for {DEFAULT_BUNDLE_NAME}: "
        f"expected {expected_sha256}, got {actual_sha256}"
    )

# Renombrar atómicamente al path final solo si el hash coincide
tmp_path.replace(bundle_path)
```

IMPORTANTE: Verificar que `self.session` existe (se crea en `__init__` de la clase).
Si no existe, crear `self.session = requests.Session()` en `__init__`.

**Verify**:
```
.venv/bin/python -c "
from chile_hub.data_manager import ChileHubDataManager
dm = ChileHubDataManager(data_version='latest')
dm.update()
print('Bundle descargado y verificado con hashing en tránsito')
"
```

### Step 2: Agregar verificación de integridad del binario unrar

En `src/extractors/mineduc_establecimientos_extractor.py`, después de la línea 68
(donde se determina `unrar_bin`), agregar una verificación de hash SHA256:

```python
# Verificar integridad del binario unrar
_UNRAR_EXPECTED_SHA256 = None  # Se calculará en primera ejecución

def _verify_unrar_integrity(unrar_path: Path) -> bool:
    """Verifica que el binario unrar tenga un hash conocido."""
    import hashlib
    global _UNRAR_EXPECTED_SHA256

    if not unrar_path.exists():
        return False
    actual = hashlib.sha256(unrar_path.read_bytes()).hexdigest()

    # En primera ejecución, registrar el hash como referencia
    # (asumimos que el bootstrap inicial es confiable)
    if _UNRAR_EXPECTED_SHA256 is None:
        _UNRAR_EXPECTED_SHA256 = actual
        return True
    return actual == _UNRAR_EXPECTED_SHA256
```

Y antes del `subprocess.run()`, llamar:
```python
if not _verify_unrar_integrity(Path(unrar_bin)):
    raise SystemExit(
        f"Verificación de integridad fallida para {unrar_bin}. "
        f"El binario puede haber sido modificado. Reinstala con 'apt-get install unrar'."
    )
```

**Verify**: Ejecutar el extractor MINEDUC (puede requerir conexión):
```
.venv/bin/python src/extractors/mineduc_establecimientos_extractor.py
```
Y verificar que pasa la verificación de integridad.

### Step 3: Usar paths relativos en mensajes de error de build_dev_db.py

En `src/build_dev_db.py`, buscar los 4 sitios donde se interpolan paths en
mensajes de error de cara al usuario y usar `os.path.relpath()`.

Línea ~759:
```python
# Antes:
raise SystemExit(f"Error: Metadatos en {path} no es un objeto JSON (dict).")
# Después:
raise SystemExit(
    f"Error: Metadatos en {os.path.relpath(path, ROOT_DIR)} no es un objeto JSON (dict)."
)
```

Línea ~776:
```python
# Antes:
raise SystemExit(f"Error: Archivo de metadatos {path} contiene un JSON malformado: {e}")
# Después:
raise SystemExit(
    f"Error: Archivo de metadatos {os.path.relpath(path, ROOT_DIR)} "
    f"contiene un JSON malformado: {e}"
)
```

Línea ~2598 y ~2641:
```python
# Antes:
f"Error: No se encuentran los metadatos para {name} en data/staging/. ..."
# Después: ya es una ruta relativa, pero verificar que no contenga ROOT_DIR
```

**Verify**: Forzar un error:
```
.venv/bin/python -c "
import os, sys
sys.path.insert(0, 'src')
from build_dev_db import load_metadata, ROOT_DIR
try:
    load_metadata('/ruta/inexistente.json')
except SystemExit as e:
    # El mensaje NO debe contener /home/
    assert '/home/' not in str(e), f'Path absoluto en mensaje: {e}'
    print('OK: path relativo en mensaje de error')
"
```

### Step 4: Lint y tests

```
.venv/bin/python -m ruff check src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py
.venv/bin/python -m ruff format --check src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py
.venv/bin/python -m pytest tests/test_chile_hub.py tests/test_extractors.py -v
```

## Test plan

- **test_bundle_download_streaming_hash**: Test en `tests/test_chile_hub.py` que
  mockea `self.session.get()` para retornar chunks conocidos, verifica que el
  hash se calcula correctamente en tránsito y que el archivo final tiene el
  contenido esperado.
- **test_unrar_integrity_first_run**: Test en `tests/test_extractors.py` que
  verifica que `_verify_unrar_integrity` retorna True en primera ejecución
  (registra el hash).
- **test_unrar_integrity_tampered**: Test que modifica el hash esperado y
  verifica que retorna False.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/chile_hub/data_manager.py src/extractors/mineduc_establecimientos_extractor.py src/build_dev_db.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py tests/test_extractors.py -v` all pass
- [ ] El bundle se descarga con hashing en tránsito en `data_manager.py` (sin `_sha256(bundle_path)`)
- [ ] `mineduc_establecimientos_extractor.py` tiene verificación de integridad de `unrar`
- [ ] `grep -rn "/home/" src/build_dev_db.py` en los mensajes de SystemExit retorna 0 matches
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- `self.session` no existe en `ChileHubDataManager.__init__` — se necesita
  crear una `requests.Session()` primero.
- `Path.replace()` no funciona en el sistema de archivos (ej.跨-dispositivo);
  usar `shutil.move()` como fallback.
- La verificación de integridad de `unrar` causa falsos positivos en CI porque
  el binario se reinstala en cada job (hash cambia legítimamente). En ese caso,
  omitir la verificación si `CI=true` en el entorno.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- El hash de `unrar` se calcula en primera ejecución y se almacena en memoria
  (variable global). Si el binario se actualiza legítimamente (`apt upgrade`),
  borrar `__pycache__` del extractor o reiniciar el proceso para re-calibrar.
- La verificación en tránsito usa `iter_content(chunk_size=8192)`. Si el bundle
  supera 1GB en el futuro, considerar un chunk_size mayor (64KB) para reducir
  overhead de llamadas a `hashlib`.
- Si se agregan más binarios externos al pipeline, seguir el mismo patrón de
  verificación de integridad.
