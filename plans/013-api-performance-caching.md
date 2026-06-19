# Plan 013: Cache en memoria para la API de ChileHub

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/chile_hub/core.py src/build_dev_db.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

La clase `ChileHub` tiene 11+ métodos que leen y parsean los mismos archivos JSON
del directorio `data/normalized/` en cada llamada. Una sola ejecución de
`hub.overview()` dispara 7+ lecturas de archivo (`hub_health.json` se lee dos
veces, `hub_bundle.json` se lee dos veces). En CLI esto es imperceptible (~50ms),
pero en uso programático donde se llama a múltiples métodos sobre la misma
instancia, el overhead es innecesario: los JSON de metadata son inmutables
durante la vida de una instancia de ChileHub.

Agregar `functools.lru_cache` en los métodos de carga de artefactos y un dict
cache simple para `load_polars()` elimina las lecturas redundantes sin cambiar
la API pública.

## Current state

### Archivo relevante

- `src/chile_hub/core.py` — clase ChileHub (~1750 líneas). Los métodos que cargan
  artefactos JSON están entre líneas 75-200. Los métodos que los llaman están
  dispersos en toda la clase.

### Métodos que re-leen los mismos archivos

Cada uno de estos métodos llama a `_load_json_artifact()` o a otro método que a
su vez lee archivos, sin cache:

| Método | Archivo leído | Llamado por |
|--------|--------------|-------------|
| `_load_artifact_manifest()` (L79) | `artifact_manifest.json` | `inventory()`, `shared_artifacts()` |
| `_load_hub_health()` (~L87) | `hub_health.json` | `health()`, `overview()`, `runtime_status_audit()` |
| `_load_hub_bundle()` (~L95) | `hub_bundle.json` | `bundle()`, `packages()` |
| `_load_dataset_status()` (~L100) | `dataset_status.json` | `status()`, `overview()` |
| `_load_dataset_changelog()` | `dataset_changelog.json` | `changelog()` |
| `_load_source_readiness()` | `source_readiness.json` | `source_readiness()` |
| `_load_dataset_quality()` | `dataset_quality.json` | `dataset_quality()` |
| `_load_provenance()` | `provenance_report.json` | `provenance()`, `top_issue()` |
| `_load_drift()` | `drift_report.json` | `drift()`, `top_issue()` |
| `_load_redistribution()` | `redistribution_report.json` | `redistribution()` |

El problema se amplifica con el encadenamiento: `overview()` → `health()` →
`_load_hub_health()`, luego `overview()` → `_load_hub_bundle()`, luego
`snapshot_text()` → `overview()` + `freshness_audit()` = más re-lecturas.

### load_polars también re-lee

`src/chile_hub/core.py:211-213`:
```python
def load_polars(self, dataset_name: str) -> pl.DataFrame:
    path = self.get_output_path(dataset_name, "parquet")
    return pl.read_parquet(path)
```
Cada llamada re-lee el Parquet del disco. Aunque el sistema operativo cachea,
Python re-parsea el archivo completo. Para datasets grandes como `empresas`
(~50MB Parquet), esto es costoso.

### Convenciones del repo

- La clase `ChileHub` se instancia una vez por sesión.
- Los artefactos en `data/normalized/` no cambian durante la vida de una instancia.
- La API usa properties con `@property` en algunos casos; `functools` aún no se usa.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/chile_hub/core.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_chile_hub.py -v` | all pass |
| Timing before | `.venv/bin/python -c "from chile_hub import ChileHub; h = ChileHub(); import time; t0=time.time(); h.overview(); h.overview(); print(f'{time.time()-t0:.3f}s')"` | imprime tiempo |
| Timing after | (mismo comando) | debe ser menor |

## Scope

**In scope**:
- `src/chile_hub/core.py` — agregar `functools.lru_cache` a los métodos de carga
  de artefactos y un cache simple para `load_polars()`

**Out of scope** (do NOT touch):
- `src/chile_hub/data_manager.py` — la descarga de bundle ya tiene su propio cache en disco
- `src/build_dev_db.py` — no es parte de la API de consumo
- Paralelización de builds — cubierto en un plan futuro si se requiere
- Cambiar la API pública — todos los métodos conservan su firma

## Git workflow

- Branch: `advisor/013-api-caching`
- Commit único; mensaje estilo `perf(api): add in-memory caching for artifact loads`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Agregar import de functools

Al inicio de `src/chile_hub/core.py`, en la sección de imports stdlib, agregar:
```python
import functools
```
(Verificar que no esté ya importado; probablemente no lo está.)

### Step 2: Cachear métodos de carga de artefactos JSON

Para cada método `_load_*()` que lee un archivo JSON del disco, agregar
`@functools.lru_cache(maxsize=1)`:

```python
@functools.lru_cache(maxsize=1)
def _load_artifact_manifest(self) -> dict[str, Any]:
    ...

@functools.lru_cache(maxsize=1)
def _load_hub_health(self) -> dict[str, Any]:
    ...

@functools.lru_cache(maxsize=1)
def _load_hub_bundle(self) -> dict[str, Any]:
    ...
```

Aplicar a TODOS los métodos `_load_*` que usan `_load_json_artifact()`.

IMPORTANTE: `lru_cache` usa los argumentos como clave de cache. Como todos estos
métodos solo reciben `self`, el cache tendrá una sola entrada por instancia. Usar
`maxsize=1` explícitamente para documentar la intención y minimizar memoria.

### Step 3: Cachear load_polars

Agregar un diccionario privado de cache para DataFrames:

```python
def __init__(self, ...):
    ...
    self._df_cache: dict[str, pl.DataFrame] = {}

def load_polars(self, dataset_name: str) -> pl.DataFrame:
    if dataset_name in self._df_cache:
        return self._df_cache[dataset_name]
    path = self.get_output_path(dataset_name, "parquet")
    try:
        df = pl.read_parquet(path)
    except FileNotFoundError:
        raise ChileHubDatasetError(...)
    except Exception as exc:
        raise ChileHubDatasetError(...)
    self._df_cache[dataset_name] = df
    return df
```

### Step 4: Verificar que los tests pasan

```
.venv/bin/python -m ruff check src/chile_hub/core.py
.venv/bin/python -m ruff format --check src/chile_hub/core.py
.venv/bin/python -m pytest tests/test_chile_hub.py -v
```

### Step 5: Verificar mejora de rendimiento

Ejecutar dos veces un comando que carga múltiples artefactos:
```
.venv/bin/python -c "
from chile_hub import ChileHub
import time

h = ChileHub()

# Primera llamada (cold cache)
t0 = time.time()
h.overview()
t1 = time.time()
print(f'Primera llamada overview(): {(t1-t0)*1000:.1f}ms')

# Segunda llamada (warm cache)
t0 = time.time()
h.overview()
t1 = time.time()
print(f'Segunda llamada overview(): {(t1-t0)*1000:.1f}ms')
"
```
La segunda llamada debe ser significativamente más rápida que la primera.

## Test plan

- **test_load_polars_cache**: Cargar el mismo dataset dos veces, verificar que
  ambos retornos son el mismo objeto (`assert df1 is df2`).
- **test_artifact_cache_invalidation**: No aplica — el cache es por instancia y
  los datos no cambian. Pero verificar que dos instancias separadas no comparten
  cache (cada una debe leer del disco independientemente).
- Seguir el patrón de `ChileHubTests` existente.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py -v` all pass
- [ ] `grep -rn "@functools.lru_cache" src/chile_hub/core.py` muestra al menos 8 decoradores
- [ ] `grep -rn "_df_cache" src/chile_hub/core.py` muestra inicialización en `__init__` y uso en `load_polars`
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- `functools.lru_cache` causa errores en tests porque los mocks esperan llamadas
  reales al sistema de archivos. En ese caso, los tests que mockean `open()` o
  `json.load()` deben ser ajustados: usar `mock.patch.object(h, '_load_artifact_manifest')`
  en lugar de mockear `open()`.
- El cache de `load_polars` causa problemas de memoria con `empresas` (1.57M
  filas). Verificar: si el proceso excede 2GB de RAM, considerar solo cachear
  datasets menores a cierto umbral, o usar `functools.lru_cache(maxsize=4)` con
  política LRU en lugar de dict infinito.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- Si en el futuro se agrega un método `refresh()` que recarga datos en vivo sin
  reinstanciar `ChileHub`, es necesario agregar `cache_clear()` en los métodos
  cacheados.
- El cache de `load_polars` usa un dict simple sin límite de tamaño. Si se
  agregan docenas de datasets grandes en el futuro, considerar `functools.lru_cache`
  con `maxsize` basado en memoria disponible.
- Los decoradores `@functools.lru_cache(maxsize=1)` en métodos de instancia
  mantienen una referencia a `self`, lo que previene que el garbage collector
  libere la instancia. Esto es aceptable porque `ChileHub` se usa como singleton
  en la práctica.
