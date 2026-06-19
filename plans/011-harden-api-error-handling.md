# Plan 011: Robustecer el manejo de errores en la API pública

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/chile_hub/core.py src/chile_hub/data_manager.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

Tres bugs en la API pública que degradan la experiencia del usuario y un bug de
fuga de conexiones HTTP: (1) `load_polars()` expone tracebacks crudos de
Polars/PyArrow cuando un archivo Parquet está corrupto o no existe, (2)
`_load_catalog()` crashea con `FileNotFoundError` sin mensaje amigable cuando el
usuario pasa un `data_dir` inválido, (3) `DataManager.clear()` destruye
silenciosamente cualquier directorio si `$CHILE_HUB_CACHE_DIR` apunta a una ruta
inesperada, y (4) `check_sources()` reasigna la variable `response` del HEAD sin
cerrar la respuesta anterior, fugando conexiones TCP.

## Current state

### Archivos relevantes

- `src/chile_hub/core.py` — clase ChileHub; `load_polars()` (línea 211),
  `_load_catalog()` (línea 71), `check_sources()` (línea 786)
- `src/chile_hub/data_manager.py` — ChileHubDataManager; `clear()` (línea 128)

### Bug 1: load_polars sin try/except

`src/chile_hub/core.py:211-213`:
```python
def load_polars(self, dataset_name: str) -> pl.DataFrame:
    path = self.get_output_path(dataset_name, "parquet")
    return pl.read_parquet(path)
```
Si el Parquet no existe, está corrupto, o es incompatible con la versión de
Polars, el usuario ve `FileNotFoundError`, `polars.exceptions.ComputeError`, o
`pyarrow.lib.ArrowInvalid` — tracebacks completos sin contexto.

`main()` (línea 1741-1746) solo captura `ChileHubError`, así que estas
excepciones crudas escapan también por CLI.

### Bug 2: _load_catalog sin guardia

`src/chile_hub/core.py:71-73`:
```python
def _load_catalog(self) -> dict[str, Any]:
    with self.catalog_path.open("r", encoding="utf-8") as f:
        return json.load(f)
```
Cuando el usuario llama `ChileHub(data_dir="/ruta/incorrecta")`, el constructor
llega a `_load_catalog()` sin verificar que el archivo existe. El
`FileNotFoundError` crudo no le dice al usuario qué hacer.

### Bug 3: DataManager.clear() destructivo

`src/chile_hub/data_manager.py:128-129`:
```python
def clear(self) -> None:
    shutil.rmtree(self.cache_root, ignore_errors=True)
```
`cache_root` se puede configurar vía `$CHILE_HUB_CACHE_DIR`. Si un usuario la
configura mal (ej. `$HOME`), `clear()` destruye todo el directorio sin
confirmación y `ignore_errors=True` suprime incluso errores de permisos que
podrían servir como red de seguridad.

### Bug 4: check_sources fugas de HTTP

`src/chile_hub/core.py:789-793`:
```python
try:
    # Intenta HEAD primero
    response = requests.head(url, timeout=timeout, allow_redirects=True)
    if response.status_code >= 400:
        response = requests.get(url, timeout=timeout, stream=True)

    status = "online" if response.status_code < 400 else "offline"
```
Cuando el status es >= 400, la variable `response` se reasigna con un nuevo
objeto GET. La respuesta HEAD anterior queda sin referencias y sin `.close()`.
Ninguna de las dos respuestas usa context manager. Con ~17 datasets, cada
llamada a `check_sources()` puede fugar hasta 34 conexiones.

### Convenciones del repo

- Errores de API: `ChileHubError` y sus subclases en `core.py`.
- El patrón correcto de HTTP con cierre está en `data_manager.py:169`:
  `with self.session.get(...) as response:`.
- Mensajes de error en español: `f"Error: ..."`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/chile_hub/core.py src/chile_hub/data_manager.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_chile_hub.py -v` | all pass |
| Tests específicos | `.venv/bin/python -m pytest tests/test_chile_hub.py::ChileHubTests -v` | all pass |
| Smoke test | `.venv/bin/python -c "from chile_hub import ChileHub; h = ChileHub(); print(h.list_datasets())"` | lista datasets |

## Scope

**In scope**:
- `src/chile_hub/core.py` — `load_polars()`, `_load_catalog()`, `check_sources()`
- `src/chile_hub/data_manager.py` — `clear()`

**Out of scope** (do NOT touch):
- `src/build_dev_db.py` — no es parte de la API pública
- `src/chile_hub/cli.py` — no modificar entry points
- `src/extractors/` — cubiertos por Plan 010
- Cualquier cambio en el contrato público de `ChileHub` (métodos, parámetros)

## Git workflow

- Branch: `advisor/011-api-error-handling`
- Commit por step; mensaje estilo `fix(api): ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Envolver load_polars con try/except

En `src/chile_hub/core.py:211-213`, cambiar:
```python
def load_polars(self, dataset_name: str) -> pl.DataFrame:
    path = self.get_output_path(dataset_name, "parquet")
    return pl.read_parquet(path)
```
Por:
```python
def load_polars(self, dataset_name: str) -> pl.DataFrame:
    path = self.get_output_path(dataset_name, "parquet")
    try:
        return pl.read_parquet(path)
    except FileNotFoundError:
        raise ChileHubDatasetError(
            f"Dataset '{dataset_name}' no encontrado en {path}. "
            f"Ejecuta 'chile-hub cache update' para descargar los datos, "
            f"o 'chile-hub list' para ver datasets disponibles."
        )
    except Exception as exc:
        raise ChileHubDatasetError(
            f"No se pudo cargar el dataset '{dataset_name}' desde {path}: {exc}"
        )
```

**Verify**: Forzar un error:
```
.venv/bin/python -c "from chile_hub import ChileHub; h = ChileHub(); h.load_polars('no_existe')"
```
Debe mostrar `ChileHubDatasetError` con mensaje descriptivo, no un traceback de Polars.

### Step 2: Agregar guardia en _load_catalog

En `src/chile_hub/core.py:71-73`, cambiar:
```python
def _load_catalog(self) -> dict[str, Any]:
    with self.catalog_path.open("r", encoding="utf-8") as f:
        return json.load(f)
```
Por:
```python
def _load_catalog(self) -> dict[str, Any]:
    try:
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ChileHubDataError(
            f"Catálogo de datasets no encontrado en {self.catalog_path}. "
            f"Usa ChileHub() sin argumentos para descargar el bundle automáticamente, "
            f"o asegúrate de que el directorio '{self.catalog_path.parent}' contiene "
            f"los datos normalizados (ejecuta 'make build' si estás en desarrollo)."
        )
```

**Verify**: Forzar el error:
```
.venv/bin/python -c "from chile_hub import ChileHub; h = ChileHub(data_dir='/tmp/no_existe')"
```
Debe mostrar `ChileHubDataError` con mensaje descriptivo.

### Step 3: Agregar validación de seguridad en DataManager.clear()

En `src/chile_hub/data_manager.py:128-129`, cambiar:
```python
def clear(self) -> None:
    shutil.rmtree(self.cache_root, ignore_errors=True)
```
Por:
```python
def clear(self) -> None:
    # Validar que cache_root es un subdirectorio esperado
    expected_parent = platformdirs.user_cache_dir("chile-hub")
    cache_path = Path(self.cache_root).resolve()
    if not str(cache_path).startswith(str(Path(expected_parent).resolve())):
        raise ChileHubDataError(
            f"Por seguridad, 'cache clear' solo opera dentro del directorio de cache "
            f"esperado ({expected_parent}). El directorio configurado es {cache_path}. "
            f"Verifica la variable de entorno CHILE_HUB_CACHE_DIR."
        )
    if not cache_path.exists():
        return  # nothing to clear
    shutil.rmtree(str(cache_path))
```

IMPORTANTE: Agregar `import platformdirs` al inicio del archivo si no está, y
`from pathlib import Path` (verificar imports existentes en línea 6-10).

**Verify**: Test manual:
```
.venv/bin/python -c "
import os
os.environ['CHILE_HUB_CACHE_DIR'] = '/tmp/test_chile_hub_clear'
from chile_hub.data_manager import ChileHubDataManager
m = ChileHubDataManager()
m.clear()
print('OK: clear en /tmp funcionó')
"
```

### Step 4: Cerrar respuestas HTTP en check_sources

En `src/chile_hub/core.py:789-800`, cambiar el bloque try:
```python
try:
    # Intenta HEAD primero
    response = requests.head(url, timeout=timeout, allow_redirects=True)
    if response.status_code >= 400:
        response.close()
        response = requests.get(url, timeout=timeout, stream=True)

    status = "online" if response.status_code < 400 else "offline"
    status_code = response.status_code
    latency_ms = round(response.elapsed.total_seconds() * 1000, 2)
    error = None
    response.close()
except Exception as e:
    status = "offline"
```

**Verify**: Ejecutar el comando check-sources:
```
.venv/bin/python -m chile_hub check-sources --timeout 5
```
Debe listar todas las fuentes sin errores de conexión.

### Step 5: Lint y tests

```
.venv/bin/python -m ruff check src/chile_hub/core.py src/chile_hub/data_manager.py
.venv/bin/python -m ruff format --check src/chile_hub/core.py src/chile_hub/data_manager.py
.venv/bin/python -m pytest tests/test_chile_hub.py -v
```

## Test plan

- **test_load_polars_missing_dataset**: En `tests/test_chile_hub.py::ChileHubTests`,
  llamar `hub.load_polars('dataset_inexistente')` y verificar que levanta
  `ChileHubDatasetError` con un mensaje que contiene el nombre del dataset.
- **test_load_polars_corrupt_parquet**: Crear un archivo Parquet inválido en un
  directorio temporal, apuntar `ChileHub(data_dir=tmpdir)` y verificar
  `ChileHubDatasetError`.
- **test_init_missing_catalog**: `ChileHub(data_dir='/tmp/no_existe')` debe
  levantar `ChileHubDataError`.
- **test_cache_clear_safety**: Con `CHILE_HUB_CACHE_DIR=/`, llamar `clear()` y
  verificar que levanta `ChileHubDataError`.
- Seguir el patrón de assertions existente: `with self.assertRaises(ChileHubDatasetError):`.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/chile_hub/core.py src/chile_hub/data_manager.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/chile_hub/core.py src/chile_hub/data_manager.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py -v` all pass
- [ ] `grep -rn "return pl.read_parquet" src/chile_hub/core.py` retorna 0 matches (debe estar envuelto en try)
- [ ] `grep -rn "with self.catalog_path.open" src/chile_hub/core.py` muestra un bloque try/except alrededor
- [ ] `grep -rn "ignore_errors=True" src/chile_hub/data_manager.py` retorna 0 matches
- [ ] `grep -rn "response = requests.get" src/chile_hub/core.py` en check_sources muestra `.close()` después
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- `ChileHubDatasetError` o `ChileHubDataError` no existen en `core.py` (verificar
  imports y definiciones al inicio del archivo).
- La validación de `clear()` con `platformdirs.user_cache_dir` retorna una ruta
  diferente a la esperada en el sistema donde se ejecuta.
- Un step de verificación falla dos veces tras un intento razonable de corrección.
- La modificación de `check_sources()` rompe el comando CLI `check-sources`.

## Maintenance notes

- Si se agregan nuevas excepciones a `load_polars()` (ej. para DuckDB), seguir
  el mismo patrón de try/except con `ChileHubDatasetError`.
- El guard de seguridad en `clear()` asume que `platformdirs.user_cache_dir`
  retorna una ruta bajo el home del usuario. Si en el futuro se soportan rutas
  de sistema (ej. `/var/cache/chile-hub`), ajustar la validación.
- Los tests de error en `load_polars` requieren `data/normalized/` poblado por
  `make build` previo para los casos de éxito; los casos de error usan tmpdir.
