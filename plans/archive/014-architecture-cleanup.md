# Plan 014: Limpieza de arquitectura — remanentes (reconciliado)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, reply with exactly the report format
> shown at the end.
>
> **Drift check (run first)**: `git diff --stat 0aea153..HEAD -- src/extractors/subdere_extractor.py src/extractors/base.py src/extractors/source_adapter.py src/builders/metadata.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: — (independiente; Plan 010 ya está DONE)
- **Category**: tech-debt
- **Planned at**: commit `0aea153`, 2026-06-30
- **Reconciliado de**: commit `a2cd288` (2026-06-19) — ver §Reconciliation notes

## Why this matters

Cuatro mejoras pequeñas de arquitectura que reducen deuda técnica residual. Las
deudas mayores del plan original (extracción de `DATASET_CATALOG_CONFIG` a JSON,
alias DuckDB/SQLite de `comunas_enriquecidas`, estandarización de imports en 9
de 10 extractores) ya se resolvieron independientemente. Quedan cuatro remanentes
de bajo riesgo:

1. `subdere_extractor.py` es el único extractor que aún conserva los bloques
   `try/except ModuleNotFoundError` — los otros 9 ya usan imports absolutos
   limpios (el Makefile ya inyecta `PYTHONPATH=src` en todas las invocaciones).

2. `BaseExtractor.run()` en `base.py:52-59` es código muerto — ningún extractor
   lo llama ni lo sobreescribe (14 clases heredan de `BaseExtractor`, ninguna
   usa `run()`).

3. El docstring de `source_adapter.py` aún dice "Úsalo solo en extractores
   candidatos o nuevos" — 6 extractores ya lo usan, y es el estándar de facto.

4. `comunas_enriquecidas` ya tiene `alias_for: comunas` en el catálogo externo,
   y los formatos DuckDB/SQLite ya usan VIEWs. Pero `metadata.py` aún genera una
   entrada de catálogo completa (duplicada) para `comunas_enriquecidas`, y los
   archivos `data/normalized/comunas_enriquecidas.{parquet,json}` son artefactos
   stale de builds anteriores (el código actual solo escribe `comunas.parquet`).

## Current state

### Archivos relevantes

- `src/extractors/subdere_extractor.py` — 2 bloques `try/except ModuleNotFoundError` (líneas 11-18 y 20-23)
- `src/extractors/base.py` — `BaseExtractor.run()` (líneas 52-59), código muerto
- `src/extractors/source_adapter.py` — docstring con caveat (líneas 7-9)
- `src/builders/metadata.py` — entrada duplicada `comunas_enriquecidas` (líneas 349-359)
- `data/normalized/comunas_enriquecidas.parquet` — artefacto stale (~15 KB)
- `data/normalized/comunas_enriquecidas.json` — artefacto stale (~132 KB)

### Remanente 1: subdere_extractor.py try/except

`src/extractors/subdere_extractor.py:11-23`:
```python
try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry
```

El Makefile ya ejecuta todos los extractores con `PYTHONPATH=src` (líneas
87-99), así que el fallback `except ModuleNotFoundError` nunca se usa.

### Remanente 2: BaseExtractor.run() código muerto

`src/extractors/base.py:52-59`:
```python
def run(self, dry_run: bool = False, **kwargs: Any) -> dict[str, Any]:
    raw_data = self.fetch(**kwargs)
    df = self.normalize(raw_data)
    metadata = {"dataset": self.dataset_name, "dry_run": dry_run}
    validation = self.validate(df, metadata)
    if not dry_run:
        self.write_staging(df, metadata)
    return validation
```

- 14 clases heredan de `BaseExtractor` (SubdereExtractor, BCentralExtractor,
  CensoExtractor, CensoHogaresViviendasExtractor, SaludExtractor,
  ElectoralExtractor, ResExtractor, MineducEstablecimientosExtractor,
  MineducResultadosExtractor, SieduExtractor, SinimFinanzasExtractor,
  PobrezaComunalExtractor, ConsumoElectricoExtractor, CeaddelincuenciaLiveExtractor,
  SinimFinanzasLiveExtractor).
- Ninguna sobreescribe `run()` ni lo llama.
- Los extractores se ejecutan como scripts standalone vía `python -m` o
  `python src/extractors/<name>.py` desde el Makefile, usando `process_*()`
  o el bloque `if __name__ == "__main__"`.

### Remanente 3: source_adapter.py docstring

`src/extractors/source_adapter.py:7-9`:
```
Úsalo solo en extractores candidatos o nuevos. Los extractores estables
con lógica de extracción compleja (subdere, bcentral, censo, RES) no
necesitan adaptarse a este módulo.
```

Este caveat ya no refleja la realidad: 6+ extractores usan `build_standard_metadata()`,
incluyendo extractores complejos como `cead_delincuencia_live_extractor.py` y
`sinim_finanzas_live_extractor.py`. El mensaje debe cambiarse para reflejar que
es el estándar recomendado.

### Remanente 4: comunas_enriquecidas — entrada de catálogo duplicada y archivos stale

`src/builders/metadata.py:349-359`:
```python
"comunas_enriquecidas": {
    **comunas_metadata,
    "dataset": "comunas_enriquecidas",
    "record_count": df_comunas.height,
    "fields": df_comunas.columns,
    "reuse_policy": DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["reuse_policy"],
    "freshness": build_freshness(
        comunas_metadata.get("refreshed_at_utc"),
        DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["freshness_policy"]["max_age_hours"],
    ),
},
```

Esta entrada es byte-idéntica a la de `comunas` (mismos datos, mismas columnas).
El `dataset_catalog_config.json` ya declara `"alias_for": "comunas"`, y
`get_output_path()` en `core.py:288-290` ya resuelve el alias. Pero el catálogo
generado (`dataset_catalog.json`) lista `comunas_enriquecidas` como dataset
independiente, y `comunas_enriquecidas.json` (132 KB) en `data/normalized/` es
un volcado JSON completo del dataset, duplicado byte a byte de `comunas.json`.

Archivos stale en `data/normalized/`:
- `comunas_enriquecidas.parquet` (15183 bytes) — mismo contenido que `comunas.parquet`
- `comunas_enriquecidas.json` (132226 bytes) — mismo contenido que `comunas.json`

### Convenciones del repo

- `PYTHONPATH=src` ya se usa en todas las invocaciones del Makefile (líneas 87+).
- Commits: conventional commits (`refactor: ...`).
- Los extractores usan imports absolutos `from src.extractors.base import ...`.
- El patrón para imports en extractores (post-limpieza) es:
  ```python
  from src.extractors.base import BaseExtractor, ensure_staging_directories, write_staging_metadata
  from src.extractors.http_utils import fetch_with_retry
  ```
  Ejemplo de referencia: `src/extractors/censo_hogares_viviendas_extractor.py:17`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/` | exit 0 |
| Format check | `.venv/bin/python -m ruff format --check src/` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/ -v` | all pass |
| Build | `make build` | exit 0 |
| Subdere import | `.venv/bin/python -c "from src.extractors.subdere_extractor import process"` | exit 0 |
| API alias | `.venv/bin/python -c "from chile_hub import ChileHub; h = ChileHub(); c = h.load_polars('comunas'); ce = h.load_polars('comunas_enriquecidas'); assert c.shape == ce.shape; print('OK')"` | OK |

## Scope

**In scope**:
- `src/extractors/subdere_extractor.py` — remover bloques `try/except ModuleNotFoundError`
- `src/extractors/base.py` — remover `run()` (líneas 52-59)
- `src/extractors/source_adapter.py` — actualizar docstring
- `src/builders/metadata.py` — simplificar entrada `comunas_enriquecidas` (indicar que es alias)
- `data/normalized/comunas_enriquecidas.parquet` — eliminar (stale)
- `data/normalized/comunas_enriquecidas.json` — eliminar (stale)

**Out of scope** (do NOT touch):
- `src/chile_hub/` — la API pública no cambia
- `src/builders/formats.py` — ya usa VIEWs para DuckDB/SQLite
- `data/dataset_catalog_config.json` — ya tiene `alias_for`
- Migrar extractores legacy a `build_standard_metadata()` — difiere a otro plan
- `src/extractors/http_utils.py` — su bloque `except ImportError` está fuera de scope
- Cualquier otro archivo no listado en "In scope"

## Git workflow

- Branch: `advisor/014-architecture-cleanup`
- Un commit por step; mensaje estilo `refactor: ...`
- No hacer push ni abrir PR.

## Steps

### Step 1: Limpiar imports de subdere_extractor.py

En `src/extractors/subdere_extractor.py`, reemplazar los dos bloques
`try/except ModuleNotFoundError` por imports absolutos directos:

```python
# ANTES (líneas 11-23):
try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

# DESPUÉS:
from src.extractors.base import (
    BaseExtractor,
    ensure_staging_directories,
    write_staging_metadata,
)
from src.extractors.http_utils import fetch_with_retry
```

Dejar el resto del archivo intacto (incluyendo el bloque `try/except ImportError`
de `curl_cffi` en líneas 27-32, que es intencional — es una dependencia opcional).

**Verify**:
```
.venv/bin/python -c "from src.extractors.subdere_extractor import process; print('OK')"
```
Exit 0, output "OK".

```
grep -c "except ModuleNotFoundError:" src/extractors/subdere_extractor.py
```
Debe retornar 0.

### Step 2: Eliminar BaseExtractor.run()

En `src/extractors/base.py`, eliminar el método `run()` (líneas 52-59). Agregar
un comentario en el docstring de la clase explicando que los extractores se
ejecutan como scripts standalone (vía `process_*()` desde `__main__`), no a
través de `run()`.

```python
# ANTES (líneas 30-59):
class BaseExtractor(ABC):
    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nombre canónico registrado en el catálogo de datasets."""

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Any:
        """Obtiene datos desde la fuente o su estrategia de fallback."""

    @abstractmethod
    def normalize(self, raw_data: Any) -> pl.DataFrame:
        """Convierte los datos obtenidos al esquema canónico."""

    @abstractmethod
    def validate(self, df: pl.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
        """Retorna el resultado de validación del dataset."""

    @abstractmethod
    def write_staging(self, df: pl.DataFrame, metadata: dict[str, Any]) -> Path:
        """Persiste el dataset normalizado y sus metadatos en staging."""

    def run(self, dry_run: bool = False, **kwargs: Any) -> dict[str, Any]:
        raw_data = self.fetch(**kwargs)
        df = self.normalize(raw_data)
        metadata = {"dataset": self.dataset_name, "dry_run": dry_run}
        validation = self.validate(df, metadata)
        if not dry_run:
            self.write_staging(df, metadata)
        return validation

# DESPUÉS:
class BaseExtractor(ABC):
    """Contrato común para extractores de chile-hub.

    Los extractores se ejecutan como scripts standalone a través de funciones
    ``process_*()`` invocadas desde el bloque ``if __name__ == "__main__"``
    de cada módulo.  No se usa un método ``run()`` centralizado porque cada
    extractor define su propio pipeline de fetching, normalización y
    post-procesamiento.
    """

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nombre canónico registrado en el catálogo de datasets."""

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Any:
        """Obtiene datos desde la fuente o su estrategia de fallback."""

    @abstractmethod
    def normalize(self, raw_data: Any) -> pl.DataFrame:
        """Convierte los datos obtenidos al esquema canónico."""

    @abstractmethod
    def validate(self, df: pl.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
        """Retorna el resultado de validación del dataset."""

    @abstractmethod
    def write_staging(self, df: pl.DataFrame, metadata: dict[str, Any]) -> Path:
        """Persiste el dataset normalizado y sus metadatos en staging."""
```

**Verify**:
```
grep -n "def run" src/extractors/base.py
```
Debe retornar 0 matches.

```
.venv/bin/python -m pytest tests/ -v
```
Todos los tests deben pasar (las 14 clases que heredan de BaseExtractor deben
seguir funcionando sin `run()`).

### Step 3: Actualizar docstring de source_adapter.py

En `src/extractors/source_adapter.py`, reemplazar el párrafo del caveat
(líneas 7-9):

```python
# ANTES:
Úsalo solo en extractores candidatos o nuevos. Los extractores estables
con lógica de extracción compleja (subdere, bcentral, censo, RES) no
necesitan adaptarse a este módulo.

# DESPUÉS:
Es el estándar recomendado para todos los extractores del proyecto.
Los extractores legacy se migrarán progresivamente a este módulo.
```

**Verify**:
```
grep "solo en extractores candidatos" src/extractors/source_adapter.py
```
Debe retornar 0 matches.

### Step 4: Limpiar duplicación de comunas_enriquecidas

Tres cambios:

**4a. Eliminar archivos stale de normalized/**:
```
rm data/normalized/comunas_enriquecidas.parquet
rm data/normalized/comunas_enriquecidas.json
```

**4b. En `src/builders/metadata.py:349-359`**, reemplazar la entrada completa de
`comunas_enriquecidas` por una que indique explícitamente que es un alias:

```python
# ANTES (líneas 349-359):
"comunas_enriquecidas": {
    **comunas_metadata,
    "dataset": "comunas_enriquecidas",
    "record_count": df_comunas.height,
    "fields": df_comunas.columns,
    "reuse_policy": DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["reuse_policy"],
    "freshness": build_freshness(
        comunas_metadata.get("refreshed_at_utc"),
        DATASET_CATALOG_CONFIG["comunas_enriquecidas"]["freshness_policy"]["max_age_hours"],
    ),
},

# DESPUÉS:
"comunas_enriquecidas": {
    **comunas_metadata,
    "dataset": "comunas_enriquecidas",
    "alias_for": "comunas",
    "record_count": df_comunas.height,
    "fields": df_comunas.columns,
    "reuse_policy": DATASET_CATALOG_CONFIG["comunas"]["reuse_policy"],
    "freshness": build_freshness(
        comunas_metadata.get("refreshed_at_utc"),
        DATASET_CATALOG_CONFIG["comunas"]["freshness_policy"]["max_age_hours"],
    ),
},
```

El cambio clave: referenciar `DATASET_CATALOG_CONFIG["comunas"]` en vez de
`DATASET_CATALOG_CONFIG["comunas_enriquecidas"]` para `reuse_policy` y
`freshness_policy`, y agregar `"alias_for": "comunas"` para documentar la
relación en el catálogo generado.

**Verify**:
```
make build
```
Exit 0.

```
.venv/bin/python -c "
from chile_hub import ChileHub
h = ChileHub()
c = h.load_polars('comunas')
ce = h.load_polars('comunas_enriquecidas')
assert c.shape == ce.shape, f'Shape mismatch: {c.shape} vs {ce.shape}'
assert c.columns == ce.columns, f'Columns mismatch'
print('OK: comunas y comunas_enriquecidas tienen los mismos datos')
"
```
Exit 0, output "OK: comunas y comunas_enriquecidas tienen los mismos datos".

```
ls data/normalized/comunas_enriquecidas.parquet 2>&1
```
Debe retornar "No such file or directory" (el archivo ya no debe existir).

### Step 5: Lint y tests completos

```
.venv/bin/python -m ruff check src/
.venv/bin/python -m ruff format --check src/
.venv/bin/python -m pytest tests/ -v
make build
```

## Test plan

- No se requieren tests nuevos para estos cambios. Los tests existentes
  (`tests/test_chile_hub.py`, `tests/test_extractors.py`) cubren:
  - Carga de `comunas` y `comunas_enriquecidas` vía API
  - Instanciación de extractores que heredan de `BaseExtractor`
- El test `test_comunas_enriquecidas_loads` (si existe) verifica que
  `load_polars("comunas_enriquecidas")` sigue funcionando.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/` exit 0
- [ ] `.venv/bin/python -m pytest tests/ -v` all pass
- [ ] `make build` exit 0
- [ ] `grep -c "except ModuleNotFoundError:" src/extractors/subdere_extractor.py` retorna 0
- [ ] `grep -c "def run" src/extractors/base.py` retorna 0
- [ ] `grep "solo en extractores candidatos" src/extractors/source_adapter.py` retorna 0 matches
- [ ] `hub.load_polars("comunas_enriquecidas")` sigue funcionando y retorna los mismos datos que `comunas`
- [ ] `data/normalized/comunas_enriquecidas.parquet` NO existe
- [ ] `data/normalized/comunas_enriquecidas.json` NO existe
- [ ] No files outside the in-scope list are modified

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- `make build` falla después de eliminar los archivos stale (Step 4).
- `load_polars("comunas_enriquecidas")` deja de funcionar después de Step 4.
- Eliminar `run()` rompe algún test que dependa de él.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Reconciliation notes

Este plan se escribió originalmente contra `a2cd288` (2026-06-19) con 5 deudas.
Al reconciliar contra `0aea153` (2026-06-30), tres deudas ya estaban resueltas:

| Deuda original | Estado |
|----------------|--------|
| ① `DATASET_CATALOG_CONFIG` inline (71-519) | ✅ Extraído a `data/dataset_catalog_config.json`, importado vía `src.builders._shared` |
| ③ `try/except ImportError` en 9/10 extractores | ✅ Limpios; solo `subdere_extractor.py` pendiente |
| ⑤ DuckDB/SQLite VIEW alias + `alias_for` en config + `get_output_path()` | ✅ Hecho; solo quedan archivos stale y entrada de catálogo duplicada |

Las deudas ② (migrar extractores legacy a `build_standard_metadata`) y ④
(`BaseExtractor.run()`) no se tocaron. Este plan reconciliado aborda solo
los remanentes de bajo riesgo: ③ (subdere), ④ (run), ② docstring, y ⑤ (stale files).

## Maintenance notes

- `subdere_extractor.py` ahora usa imports absolutos estándar como todos los
  demás extractores.
- `BaseExtractor` es una ABC pura sin lógica de ejecución. Si en el futuro se
  quiere un entry point común, diseñar una función `run_extractor()` separada.
- `source_adapter.py` es el estándar recomendado para metadata de extractores.
- `comunas_enriquecidas` es un alias documentado de `comunas`. No debe volver a
  generarse como archivo independiente. Si se agregan columnas específicas en
  el futuro, deshacer el alias.

---

## Executor report format

When finished, reply with exactly this format:

```
STATUS: COMPLETE | STOPPED
STEPS: per step — done/skipped + verification command result
STOPPED BECAUSE: (only if STOPPED) which STOP condition, what was observed
FILES CHANGED: list
NOTES: anything the reviewer should know (deviations, surprises, judgment calls)
```
