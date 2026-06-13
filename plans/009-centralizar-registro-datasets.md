# Plan 009: Centralizar el registro de datasets para eliminar la duplicación

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- src/build_dev_db.py scripts/verify_pipeline.py`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P2
- **Esfuerzo**: M
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: arch
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

Agregar un nuevo dataset al hub requiere registrarlo en al menos dos lugares distintos: `DATASET_CATALOG_CONFIG` en `src/build_dev_db.py` (que define schema, outputs, freshness policy, etc.) y `REQUIRED_DATASETS` + `REQUIRED_FILES` en `scripts/verify_pipeline.py` (que hardcodea qué datasets y archivos debe existir post-build). Es fácil olvidar actualizar verify_pipeline.py, dejando el nuevo dataset sin verificación. Este plan hace que verify_pipeline.py derive sus listas desde `DATASET_CATALOG_CONFIG`, convirtiendo build_dev_db.py en la única fuente de verdad.

## Estado actual

### `DATASET_CATALOG_CONFIG` en `src/build_dev_db.py:34-160`

```python
DATASET_CATALOG_CONFIG = {
    "regiones": {
        "outputs": {
            "parquet": "data/normalized/regiones.parquet",
            "json": "data/normalized/regiones.json",
            "duckdb_table": "regiones",
            "sqlite_table": "regiones",
            "excel_sheet": "Regiones",
        },
        ...
    },
    "provincias": { ... },
    "comunas": { ... },
    "indicadores": { ... },
}
```

Cada entrada tiene una clave `"outputs"` con los paths de los artefactos por tipo.

### `REQUIRED_DATASETS` y `REQUIRED_FILES` en `scripts/verify_pipeline.py:10-47`

```python
REQUIRED_FILES = [
    STAGING_DIR / "comunas.csv",
    STAGING_DIR / "indicadores.csv",
    STAGING_DIR / "comunas.metadata.json",
    STAGING_DIR / "indicadores.metadata.json",
    NORMALIZED_DIR / "chile_data.duckdb",
    NORMALIZED_DIR / "chile_data.db",
    NORMALIZED_DIR / "chile_data_latest.xlsx",
    NORMALIZED_DIR / "regiones.parquet",
    NORMALIZED_DIR / "provincias.parquet",
    NORMALIZED_DIR / "comunas.parquet",
    NORMALIZED_DIR / "indicadores.parquet",
    # ... 20+ entradas más hardcodeadas
]

REQUIRED_DATASETS = {"regiones", "provincias", "comunas", "indicadores"}
```

`REQUIRED_DATASETS` se usa en las verificaciones de catálogo y validaciones. `REQUIRED_FILES` verifica existencia de artefactos.

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr verify | `.venv/bin/python scripts/verify_pipeline.py` | exit 0 |
| Correr tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Correr build | `make build` | exit 0 |

## Alcance

**En scope**:
- `scripts/verify_pipeline.py` — reemplazar `REQUIRED_DATASETS` y los artefactos por-dataset de `REQUIRED_FILES` con derivación desde `DATASET_CATALOG_CONFIG`

**Fuera de scope**:
- `src/build_dev_db.py` — no modificar `DATASET_CATALOG_CONFIG`
- Los archivos compartidos en `REQUIRED_FILES` que NO son por-dataset (ej. `chile_data.duckdb`, `hub_health.json`, etc.) — mantener hardcodeados en verify_pipeline.py

## Git workflow

- Rama: `advisor/009-centralizar-registro-datasets`
- Estilo de commit: `refactor: derivar REQUIRED_DATASETS y outputs de DATASET_CATALOG_CONFIG`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Importar `DATASET_CATALOG_CONFIG` en verify_pipeline.py

Al inicio de `scripts/verify_pipeline.py`, después de los imports existentes, agregar:

```python
import sys
from pathlib import Path

# Agregar src/ al path si no está
_SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from build_dev_db import DATASET_CATALOG_CONFIG
```

**Verificar**: `python3 -c "from scripts.verify_pipeline import DATASET_CATALOG_CONFIG" 2>/dev/null || python3 -c "import sys; sys.path.insert(0, 'src'); from build_dev_db import DATASET_CATALOG_CONFIG; print('OK')"` imprime `OK`.

**STOP**: Si `build_dev_db` tiene efectos secundarios en el import (ej. ejecuta código al importar fuera de `if __name__ == "__main__"`), es condición de STOP. Verificar mirando el final del archivo: si todo está dentro del `if __name__` block, el import es seguro.

### Paso 2: Reemplazar `REQUIRED_DATASETS` por derivación dinámica

Reemplazar la línea hardcodeada:

```python
# ANTES:
REQUIRED_DATASETS = {"regiones", "provincias", "comunas", "indicadores"}
```

Con:

```python
# DESPUÉS:
REQUIRED_DATASETS = set(DATASET_CATALOG_CONFIG.keys())
```

**Verificar**: `python3 -c "import sys; sys.path.insert(0, 'src'); exec(open('scripts/verify_pipeline.py').read().split('def ')[0]); print(REQUIRED_DATASETS)"` imprime el conjunto de datasets.

### Paso 3: Agregar función para derivar outputs por-dataset de REQUIRED_FILES

Identificar en `REQUIRED_FILES` qué entradas son artefactos por-dataset (ej. `regiones.parquet`, `provincias.json`) vs. artefactos compartidos (ej. `chile_data.duckdb`, `hub_health.json`).

**Artefactos compartidos a mantener hardcodeados** (no derivan de un dataset específico):
```
chile_data.duckdb, chile_data.db, chile_data_latest.xlsx,
pipeline_metadata.json, pipeline_status.md,
hub_health.json, hub_health.md, hub_status.json, hub_bundle.json,
redistribution_report.json, redistribution_report.md,
provenance_report.json, provenance_report.md,
drift_report.json, drift_report.md,
overview.json, overview.md,
dataset_catalog.json, dataset_catalog.md,
artifact_manifest.json,
chile-hub-publishable-bundle.zip,
chile-hub-publishable-bundle.zip.sha256,
```

**Artefactos por-dataset a derivar de `DATASET_CATALOG_CONFIG`** (los que tienen una entrada `outputs.parquet` y `outputs.json`):
```
regiones.parquet, regiones.json,
provincias.parquet, provincias.json,
comunas.parquet, comunas.json,
indicadores.parquet,
```

Y los de staging:
```
comunas.csv, indicadores.csv, comunas.metadata.json, indicadores.metadata.json
```

Crear una función que derive los paths por-dataset:

```python
def _derive_dataset_artifact_paths():
    """Deriva paths de artefactos por-dataset desde DATASET_CATALOG_CONFIG."""
    paths = []
    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        outputs = config.get("outputs", {})
        for output_type, relative_path in outputs.items():
            if output_type in ("parquet", "json"):
                # Solo parquet y json — duckdb_table, sqlite_table, excel_sheet son nombres, no paths
                abs_path = ROOT_DIR / relative_path
                paths.append(abs_path)
        # Staging files
        paths.append(STAGING_DIR / f"{dataset_name}.csv")
        paths.append(STAGING_DIR / f"{dataset_name}.metadata.json")
    return paths
```

### Paso 4: Reemplazar la porción por-dataset de `REQUIRED_FILES`

Mantener los artefactos compartidos hardcodeados en `REQUIRED_FILES` y reemplazar los por-dataset con la función derivada:

```python
_SHARED_FILES = [
    NORMALIZED_DIR / "chile_data.duckdb",
    NORMALIZED_DIR / "chile_data.db",
    NORMALIZED_DIR / "chile_data_latest.xlsx",
    NORMALIZED_DIR / "pipeline_metadata.json",
    NORMALIZED_DIR / "pipeline_status.md",
    NORMALIZED_DIR / "hub_health.json",
    NORMALIZED_DIR / "hub_health.md",
    NORMALIZED_DIR / "hub_status.json",
    NORMALIZED_DIR / "hub_bundle.json",
    NORMALIZED_DIR / "redistribution_report.json",
    NORMALIZED_DIR / "redistribution_report.md",
    NORMALIZED_DIR / "provenance_report.json",
    NORMALIZED_DIR / "provenance_report.md",
    NORMALIZED_DIR / "drift_report.json",
    NORMALIZED_DIR / "drift_report.md",
    NORMALIZED_DIR / "overview.json",
    NORMALIZED_DIR / "overview.md",
    NORMALIZED_DIR / "dataset_catalog.json",
    NORMALIZED_DIR / "dataset_catalog.md",
    NORMALIZED_DIR / "artifact_manifest.json",
    NORMALIZED_DIR / "chile-hub-publishable-bundle.zip",
    NORMALIZED_DIR / "chile-hub-publishable-bundle.zip.sha256",
]

REQUIRED_FILES = _SHARED_FILES + _derive_dataset_artifact_paths()
```

**Verificar**: `python3 scripts/verify_pipeline.py` — exit 0 (el pipeline ya corrió con `make build`).

### Paso 5: Verificar que no perdimos ningún archivo en la transición

```bash
# Comparar el número de archivos antes y después
python3 -c "
import sys; sys.path.insert(0, 'src')
exec(open('scripts/verify_pipeline.py').read().split('def fail')[0])
print(f'REQUIRED_FILES: {len(REQUIRED_FILES)} archivos')
print(f'REQUIRED_DATASETS: {REQUIRED_DATASETS}')
"
```

El número de archivos debe ser igual al de la lista hardcodeada original (contar las entradas en `REQUIRED_FILES` del excerpt de "Estado actual").

### Paso 6: Correr tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, sin regresiones.

## Criterios de done

- [ ] `grep -n "REQUIRED_DATASETS = set(DATASET_CATALOG_CONFIG" scripts/verify_pipeline.py` retorna match
- [ ] `grep -n "_derive_dataset_artifact_paths" scripts/verify_pipeline.py` retorna match
- [ ] `.venv/bin/python scripts/verify_pipeline.py` sale con exit 0
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] Solo `scripts/verify_pipeline.py` modificado
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si importar `build_dev_db` tiene efectos secundarios (ejecuta código fuera del `if __name__` block) — reportar y no continuar.
- Si los paths en `DATASET_CATALOG_CONFIG["outputs"]` no son paths relativos a la raíz del repo (formato diferente) — reportar.
- Si `verify_pipeline.py` después del cambio falla con errores de paths que sí existían antes — significa que la derivación perdió algunos; reportar en lugar de parchear.

## Notas de mantenimiento

- Cuando se agregue un nuevo dataset, solo hay que agregarlo a `DATASET_CATALOG_CONFIG` en `build_dev_db.py`. `verify_pipeline.py` lo detectará automáticamente.
- Los artefactos compartidos en `_SHARED_FILES` siguen siendo hardcodeados — son correctos (no derivan de un dataset específico). Si se agrega un nuevo reporte compartido, añadirlo manualmente a `_SHARED_FILES`.
