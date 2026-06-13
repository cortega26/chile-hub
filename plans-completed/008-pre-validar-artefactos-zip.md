# Plan 008: Pre-validar artefactos antes de crear el ZIP publicable

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- src/build_dev_db.py`
> Si `build_dev_db.py` cambió, compara los excerpts de "Estado actual" con el código real antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: M
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: correctness
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

`write_publishable_bundle_zip()` itera sobre los artefactos del manifest y los agrega al ZIP sin verificar que existan en disco. Si un archivo falta (por un error en el build, un path incorrecto en el manifest, o una condición de carrera), `zipfile.ZipFile.write()` lanza `FileNotFoundError`, el ZIP queda truncado en disco, y no se lanza una excepción clara que explique qué archivo faltó. Además, el ZIP truncado permanece en `data/normalized/` y podría publicarse sin que el pipeline lo detecte. Este plan agrega una validación previa de existencia y una verificación de integridad post-escritura.

## Estado actual

### `write_publishable_bundle_zip()` en `src/build_dev_db.py:1022-1033`

```python
def write_publishable_bundle_zip():
    manifest_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    output_path = os.path.join(NORMALIZED_DIR, PUBLISHABLE_BUNDLE_ZIP_NAME)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in manifest.get("artifacts", []):
            relative_path = artifact["path"]
            absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
            archive.write(absolute_path, arcname=relative_path)  # ← sin verificar existencia
    return output_path
```

No hay validación de que `absolute_path` exista antes de `archive.write()`. Si falla a mitad del loop, el ZIP queda en disco pero truncado.

### `compute_sha256()` en el mismo archivo (función auxiliar existente)

```python
def compute_sha256(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### Constantes relevantes

```python
# build_dev_db.py:31-32
PUBLISHABLE_BUNDLE_ZIP_NAME = "chile-hub-publishable-bundle.zip"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr el build | `make build` | exit 0 |
| Correr tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Verificar ZIP | `python3 -c "import zipfile; z = zipfile.ZipFile('data/normalized/chile-hub-publishable-bundle.zip'); print(len(z.namelist()), 'archivos')"` | número > 0 |

## Alcance

**En scope**:
- `src/build_dev_db.py` — solo la función `write_publishable_bundle_zip()`

**Fuera de scope**:
- `write_publishable_bundle_sha256()` — no tocar
- `attach_publishable_package_to_manifest()` — no tocar
- Cualquier otro archivo

## Git workflow

- Rama: `advisor/008-pre-validar-artefactos-zip`
- Estilo de commit: `fix: validar existencia de artefactos y verificar integridad del ZIP antes de publicar`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar pre-validación de paths antes del loop

Modificar `write_publishable_bundle_zip()` para verificar que todos los artefactos existen antes de crear el ZIP:

```python
def write_publishable_bundle_zip():
    manifest_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    artifacts = manifest.get("artifacts", [])

    # Pre-validación: verificar que todos los artefactos existen antes de crear el ZIP
    missing = []
    for artifact in artifacts:
        relative_path = artifact["path"]
        absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
        if not os.path.exists(absolute_path):
            missing.append(relative_path)
    if missing:
        raise SystemExit(
            f"Error: no se puede crear el ZIP — faltan {len(missing)} artefactos: "
            + ", ".join(missing[:5])
            + (" (y más)" if len(missing) > 5 else "")
        )

    output_path = os.path.join(NORMALIZED_DIR, PUBLISHABLE_BUNDLE_ZIP_NAME)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in artifacts:
            relative_path = artifact["path"]
            absolute_path = os.path.join(DATA_DIR, os.path.relpath(relative_path, "data"))
            archive.write(absolute_path, arcname=relative_path)

    # Post-verificación: el ZIP es legible y no está vacío
    with zipfile.ZipFile(output_path, "r") as check:
        bad_file = check.testzip()
        if bad_file is not None:
            raise SystemExit(f"Error: ZIP corrupto — primer archivo fallido: {bad_file}")
        if len(check.namelist()) != len(artifacts):
            raise SystemExit(
                f"Error: ZIP incompleto — esperados {len(artifacts)} archivos, "
                f"encontrados {len(check.namelist())}"
            )

    return output_path
```

**Verificar**: `grep -n "missing\|Pre-validación\|Post-verificación" src/build_dev_db.py` retorna las líneas agregadas.

### Paso 2: Correr el build completo

```bash
make build
```

**Verificar**: exit 0. El ZIP se genera correctamente.

### Paso 3: Verificar el ZIP generado

```bash
python3 -c "
import zipfile
z = zipfile.ZipFile('data/normalized/chile-hub-publishable-bundle.zip')
print(f'ZIP OK: {len(z.namelist())} archivos')
print(z.testzip() or 'Sin archivos corruptos')
"
```

**Verificar**: imprime el número de archivos y "Sin archivos corruptos".

### Paso 4: Correr los tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, sin regresiones.

## Plan de tests

Agregar en `tests/test_pipeline_logic.py` un test que verifica el comportamiento con manifest que apunta a archivos inexistentes:

```python
def test_write_publishable_bundle_zip_fails_on_missing_artifact(self):
    """Si el manifest apunta a un archivo que no existe, write_publishable_bundle_zip debe fallar con error claro."""
    import json
    from src.build_dev_db import write_publishable_bundle_zip

    with tempfile.TemporaryDirectory() as tmpdir:
        normalized = Path(tmpdir) / "data" / "normalized"
        normalized.mkdir(parents=True)
        manifest = {
            "artifacts": [{"path": "data/normalized/no-existe.parquet"}]
        }
        manifest_path = normalized / "artifact_manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        with patch("src.build_dev_db.NORMALIZED_DIR", str(normalized)), \
             patch("src.build_dev_db.DATA_DIR", str(Path(tmpdir) / "data")):
            with self.assertRaises(SystemExit):
                write_publishable_bundle_zip()
```

**Verificar**: `.venv/bin/python -m unittest tests.test_pipeline_logic.PipelineLogicTests.test_write_publishable_bundle_zip_fails_on_missing_artifact -v` — pasa.

## Criterios de done

- [ ] `grep -n "Pre-validación\|missing\|testzip" src/build_dev_db.py` muestra las líneas nuevas
- [ ] `make build` sale con exit 0
- [ ] `python3 -c "import zipfile; print(zipfile.ZipFile('data/normalized/chile-hub-publishable-bundle.zip').testzip())"` imprime `None`
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] Solo `src/build_dev_db.py` (y opcionalmente `tests/test_pipeline_logic.py`) modificados
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si la función `write_publishable_bundle_zip` tiene una firma o estructura diferente a la del excerpt — reportar y no continuar.
- Si el path de `absolute_path` se calcula diferente en el código real — adaptar la pre-validación al path real; no usar el del excerpt si difiere.
- Si `make build` falla después del cambio con un error diferente al de los artefactos faltantes — reportar el traceback.

## Notas de mantenimiento

- Si se cambia la estructura del manifest (ej. los artifacts pasan a estar bajo otra clave), actualizar la pre-validación para iterar sobre la nueva estructura.
- El `testzip()` verifica integridad de cada entrada del ZIP — es O(n) sobre el tamaño del ZIP; para bundles de cientos de MB podría ser lento. En ese caso, reemplazar por una verificación de solo el `namelist()` count.
