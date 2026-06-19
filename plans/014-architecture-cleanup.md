# Plan 014: Limpieza de arquitectura — catálogo externo, imports estándar, y alias de dataset duplicado

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/build_dev_db.py src/extractors/base.py src/extractors/source_adapter.py src/extractors/bcentral_extractor.py src/extractors/subdere_extractor.py src/extractors/censo_extractor.py src/extractors/censo_hogares_viviendas_extractor.py src/extractors/salud_extractor.py src/extractors/electoral_extractor.py src/extractors/res_extractor.py src/extractors/mineduc_establecimientos_extractor.py src/extractors/mineduc_resultados_extractor.py src/extractors/sinim_finanzas_extractor.py src/extractors/siedu_extractor.py Makefile`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: Plan 010 (toca extractores que también modifica 010; ejecutar 010 primero)
- **Category**: tech-debt
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

Cinco mejoras de arquitectura que reducen deuda técnica y fricción de
mantenimiento: (1) `DATASET_CATALOG_CONFIG` es un dict de ~400 líneas incrustado
en `build_dev_db.py:71-519` — extraerlo a un archivo JSON facilita la edición y
previene conflictos de merge, (2) `source_adapter.py` solo lo usan 3 de 11
extractores — generalizar su adopción elimina construcción manual de metadata en
8 extractores, (3) 10 extractores duplican un bloque `try/except ImportError` de
3-6 líneas para soportar ejecución como script — eliminar esta duplicación
agregando `src/` al `PYTHONPATH` en el Makefile, (4) `BaseExtractor.run()` es
código muerto — nunca se llama (todos usan `process_*()` standalone), y (5)
`comunas_enriquecidas` es byte-idéntico a `comunas` pero se escribe dos veces en
todos los formatos — convertir a alias en el catálogo.

## Current state

### Archivos relevantes

- `src/build_dev_db.py` — `DATASET_CATALOG_CONFIG` (líneas 71-519), escritura de `comunas_enriquecidas` (líneas 2450-2456), builders DuckDB/SQLite/Excel con tabla duplicada
- `src/extractors/base.py` — `BaseExtractor` ABC (líneas 30-59), `run()` nunca llamado
- `src/extractors/source_adapter.py` — helpers de metadata estándar (113 líneas), usado solo por 3 extractores
- `src/extractors/*.py` (10 archivos) — bloques `try/except ImportError` duplicados
- `Makefile` — target `extract` (líneas 89-100)

### Deuda 1: DATASET_CATALOG_CONFIG inline

`src/build_dev_db.py:71`:
```python
DATASET_CATALOG_CONFIG = {
    "regiones": {
        "description": "Capa derivada de regiones...",
        ...
    },
    "provincias": { ... },
    ...
}  # ~400 líneas hasta la línea 519
```

### Deuda 2: source_adapter adopción parcial

`src/extractors/source_adapter.py:7-9` (docstring):
```
Úsalo solo en extractores candidatos o nuevos. Los extractores estables
con lógica de extracción compleja (subdere, bcentral, censo, RES) no
necesitan adaptarse a este módulo.
```
Solo `mineduc_resultados_extractor.py`, `siedu_extractor.py`, y
`sinim_finanzas_extractor.py` usan `build_standard_metadata()`. Los otros 8
construyen el dict de metadata manualmente.

### Deuda 3: try/except ImportError duplicado

Ejemplo en `src/extractors/bcentral_extractor.py:19-21`:
```python
try:
    from src.extractors.base import ensure_staging_directories, write_staging_metadata
except ImportError:
    from base import ensure_staging_directories, write_staging_metadata
```
Este mismo patrón de 3-6 líneas se repite en 10 extractores.

### Deuda 4: BaseExtractor.run() código muerto

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
Nunca llamado — `grep -rn "\.run(" src/` retorna 0 hits en extractores.

### Deuda 5: comunas_enriquecidas duplicada

`src/build_dev_db.py:2455-2456`:
```python
write_parquet_atomic(df_comunas, comunas_parquet)
write_parquet_atomic(df_comunas, comunas_enriquecidas_parquet)
```
Mismo `df_comunas`, mismas columnas. También duplicado en DuckDB (dos `CREATE
TABLE` con la misma view), SQLite (dos `to_sql`), y Excel (dos hojas).

### Convenciones del repo

- Configuración externa: el proyecto ya usa `data/source_registry.json` (314
  líneas) como archivo JSON externo para configuración de fuentes.
- `PYTHONPATH=src` ya se usa en los targets `hub-*` del Makefile (líneas 165+).
- Commits: conventional commits.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/` | exit 0 |
| Build | `make build` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/ -v` | all pass |
| Extract | `make extract` | exit 0 |
| Verify catalog | `.venv/bin/python -c "import json; c=json.load(open('data/normalized/dataset_catalog.json')); assert 'comunas_enriquecidas' in c; print('OK')"` | OK |

## Scope

**In scope**:
- `src/build_dev_db.py` — extraer `DATASET_CATALOG_CONFIG` a JSON, alias de `comunas_enriquecidas`
- `data/dataset_catalog_config.json` — nuevo archivo (crear)
- `src/extractors/base.py` — remover `run()` o documentar como entry point oficial
- `src/extractors/source_adapter.py` — remover caveat del docstring
- `src/extractors/bcentral_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/subdere_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/censo_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/censo_hogares_viviendas_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/salud_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/electoral_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/res_extractor.py` — migrar a `build_standard_metadata()`
- `src/extractors/mineduc_establecimientos_extractor.py` — migrar a `build_standard_metadata()`
- `Makefile` — agregar `PYTHONPATH=src` al target `extract`

**Out of scope** (do NOT touch):
- `src/chile_hub/` — la API pública no cambia
- Cambios en el schema de `dataset_catalog.json` generado — debe ser idéntico al actual
- `scripts/verify_pipeline.py` — ya valida el catálogo, no necesita cambios
- Cambiar el comportamiento público de `comunas_enriquecidas` — debe seguir siendo cargable con `load_polars("comunas_enriquecidas")`

## Git workflow

- Branch: `advisor/014-architecture-cleanup`
- Commit por step; mensaje estilo `refactor: ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Extraer DATASET_CATALOG_CONFIG a archivo JSON

Crear `data/dataset_catalog_config.json` con el contenido del dict
`DATASET_CATALOG_CONFIG` (líneas 71-519 de `build_dev_db.py`). Convertir el
dict de Python a JSON:

```
.venv/bin/python -c "
import json, sys
sys.path.insert(0, 'src')
from build_dev_db import DATASET_CATALOG_CONFIG
with open('data/dataset_catalog_config.json', 'w', encoding='utf-8') as f:
    json.dump(DATASET_CATALOG_CONFIG, f, ensure_ascii=False, indent=2)
print(f'Escritas {len(DATASET_CATALOG_CONFIG)} entradas de catálogo')
"
```

Luego en `src/build_dev_db.py`, reemplazar el dict inline (líneas 71-519) por:
```python
def _load_catalog_config() -> dict:
    path = os.path.join(ROOT_DIR, "data", "dataset_catalog_config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

DATASET_CATALOG_CONFIG = _load_catalog_config()
```

**Verify**: `make build` debe producir exactamente el mismo `dataset_catalog.json` que antes:
```
.venv/bin/python -c "
import json
# Hacer backup del catálogo actual
import shutil
shutil.copy('data/normalized/dataset_catalog.json', '/tmp/catalog_before.json')
"
make build
.venv/bin/python -c "
import json
with open('data/normalized/dataset_catalog.json') as f:
    after = json.load(f)
with open('/tmp/catalog_before.json') as f:
    before = json.load(f)
assert after == before, 'El catálogo cambió — verificar diferencias'
print('OK: catálogo idéntico')
"
```

### Step 2: Convertir comunas_enriquecidas en alias

En `src/build_dev_db.py`, eliminar la escritura redundante. Tres cambios:

**2a. Parquet**: Eliminar línea 2456 (`write_parquet_atomic(df_comunas, comunas_enriquecidas_parquet)`)
y la variable `comunas_enriquecidas_parquet` (línea 2450).

**2b. DuckDB** (línea ~2174-2175): Eliminar `CREATE TABLE comunas_enriquecidas AS SELECT * FROM df_comunas_view`.
Agregar en su lugar: `CREATE VIEW comunas_enriquecidas AS SELECT * FROM comunas`.

**2c. SQLite** (línea ~2243-2244): Eliminar `df_comunas.to_sql("comunas_enriquecidas", ...)`.
Agregar: `cur.execute("CREATE VIEW comunas_enriquecidas AS SELECT * FROM comunas")`.

**2d. Excel** (línea ~2330): Eliminar la hoja `Comunas Enriquecidas`.

**2e. Catálogo JSON**: En `DATASET_CATALOG_CONFIG`, cambiar la entrada de
`comunas_enriquecidas` para que apunte al mismo archivo que `comunas`:
```json
"comunas_enriquecidas": {
    ...
    "alias_for": "comunas",
    ...
}
```

**2f. API load_polars**: En `get_output_path()` (core.py), si el dataset tiene
`alias_for`, resolver al dataset canónico.

**Verify**: `make build && make test`
```
.venv/bin/python -c "
from chile_hub import ChileHub
h = ChileHub()
c = h.load_polars('comunas')
ce = h.load_polars('comunas_enriquecidas')
assert c.shape == ce.shape, f'Shape mismatch: {c.shape} vs {ce.shape}'
print('OK: comunas y comunas_enriquecidas tienen los mismos datos')
"
```

### Step 3: Estandarizar imports de extractores vía PYTHONPATH

En `Makefile`, cambiar el target `extract` (líneas 89-100) para agregar `src/`
al `PYTHONPATH`:

```makefile
extract:
	PYTHONPATH=src $(PYTHON) src/extractors/subdere_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/bcentral_extractor.py
	...
```

Luego, en cada extractor que tenga el bloque `try/except ImportError`, eliminar
el bloque y dejar solo el import absoluto:

```python
# Antes:
try:
    from src.extractors.base import ensure_staging_directories, write_staging_metadata
except ImportError:
    from base import ensure_staging_directories, write_staging_metadata

# Después:
from src.extractors.base import ensure_staging_directories, write_staging_metadata
```

Aplicar en los 10 extractores que tienen este patrón.

**Verify**: `make extract` debe completar sin errores de import.

### Step 4: Eliminar o documentar BaseExtractor.run()

Si `run()` no se usa en ningún extractor, eliminarlo de `base.py:52-59` y
agregar un comentario que explique cómo se ejecutan los extractores actualmente
(vía `process_*()` standalone desde `__main__`).

Alternativa: mantener `run()` pero documentarlo como el entry point canónico
para uso programático (no desde Makefile). Si se elige esta opción, agregar un
test que demuestre su uso.

**Verify**: `grep -rn "\.run(" src/extractors/` retorna 0 matches (si se eliminó).

### Step 5: Generalizar adopción de source_adapter

En los 8 extractores legacy, reemplazar la construcción manual del dict de
metadata por `build_standard_metadata()`:

```python
# Antes (ejemplo de bcentral_extractor):
metadata = {
    "dataset": "indicadores",
    "source_name": "Banco Central de Chile vía mindicador.cl",
    "source_url": "https://mindicador.cl/api",
    "source_mode": source_mode,
    "source_detail": source_detail,
    "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
    "record_count": df.height,
    "fields": df.columns,
    "notes": notes,
    "reuse_policy": { ... },
}

# Después:
from src.extractors.source_adapter import build_standard_metadata

metadata = build_standard_metadata(
    dataset="indicadores",
    source_name="Banco Central de Chile vía mindicador.cl",
    source_url="https://mindicador.cl/api",
    source_mode=source_mode,
    source_detail=source_detail,
    df=df,
    notes=notes,
    reuse_policy={...},
)
```

IMPORTANTE: Verificar que los keys del dict resultante son exactamente los
mismos que el dict manual producía. Si `build_standard_metadata` omite algún
campo requerido por el pipeline, agregarlo a la función en `source_adapter.py`.

Actualizar el docstring de `source_adapter.py` para remover el caveat de "solo
para extractores candidatos o nuevos".

**Verify**: `make extract && make build` — el build debe completar sin errores de
metadata faltante. Verificar que `data/staging/*.metadata.json` tienen todos los
campos requeridos.

### Step 6: Lint y tests completos

```
.venv/bin/python -m ruff check src/ scripts/
.venv/bin/python -m ruff format --check src/ scripts/
.venv/bin/python -m pytest tests/ -v
make build
```

## Test plan

- **test_comunas_enriquecidas_alias**: En `tests/test_chile_hub.py`, cargar
  `comunas` y `comunas_enriquecidas`, verificar que ambos tienen las mismas
  columnas y el mismo número de filas (346).
- **test_catalog_config_json_valid**: Verificar que `data/dataset_catalog_config.json`
  es JSON válido y tiene las 15 entradas esperadas.
- **test_extractor_imports**: Después de Step 3, verificar que `python -c "from
  src.extractors.subdere_extractor import process"` funciona sin error.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/` exit 0
- [ ] `.venv/bin/python -m pytest tests/ -v` all pass
- [ ] `make extract` exit 0
- [ ] `make build` exit 0
- [ ] `grep -rn "except ImportError:" src/extractors/` retorna 0 matches
- [ ] `grep -rn "\.run(" src/extractors/` retorna 0 matches (si se eliminó)
- [ ] `data/dataset_catalog_config.json` existe y es JSON válido
- [ ] `hub.load_polars("comunas_enriquecidas")` sigue funcionando
- [ ] Los archivos `comunas_enriquecidas.parquet` NO se generan en `data/normalized/`
  (el alias redirige a `comunas.parquet`)
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- El build produce un `dataset_catalog.json` diferente al anterior (Step 1).
- `make extract` falla después de cambiar los imports (Step 3) porque algún
  extractor tiene imports relativos que dependen del CWD.
- `build_standard_metadata()` produce un dict con keys diferentes a los que el
  pipeline espera — los `load_metadata()` en `build_dev_db.py` fallan.
- La eliminación de `comunas_enriquecidas` como archivo físico rompe algún
  consumidor externo que lee el Parquet directamente del disco.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- `data/dataset_catalog_config.json` es ahora la fuente de verdad para metadatos
  de datasets. Cualquier cambio en el catálogo debe editar este archivo, no
  `build_dev_db.py`.
- Si se agregan nuevos extractores, deben usar `build_standard_metadata()` de
  `source_adapter.py` en lugar de construir el dict manualmente.
- El alias de `comunas_enriquecidas` → `comunas` significa que la capa ya no
  tiene archivo propio. Si en el futuro se agregan columnas específicas a
  comunas_enriquecidas (ej. población INE), se debe deshacer el alias y volver a
  generar un archivo separado.
- Los extractores ahora requieren `PYTHONPATH=src` para ejecutarse como scripts.
  Documentar esto en `AGENTS.md §11` (Referencia rápida de comandos).
