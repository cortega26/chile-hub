# Plan 017: Nuevas capacidades de API — cruces, validación de usuario, exit codes, y búsqueda

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 17ed6e9..HEAD -- src/chile_hub/core.py`
> Si el archivo cambió desde que se escribió este plan, compara los excerpts de
> "Current state" contra el código vivo antes de proceder; si hay diferencias,
> trata como STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW
- **Depends on**: Plan 011 (ChileHubDatasetError — DONE ✓) y Plan 013 (cache en memoria — DONE ✓)
- **Category**: direction
- **Planned at**: commit `17ed6e9`, 2026-06-19

## Why this matters

Cuatro adiciones a la API que resuelven fricción documentada de los usuarios,
todas de bajo riesgo por ser puramente aditivas: (1) vista pre-joined por CUT
para que los usuarios no reescriban el mismo join de 3 líneas en cada script, (2)
validación de datos externos contra los contratos de schema del hub para que
usuarios puedan verificar sus propios datos, (3) exit codes para CI de manera que
`chile-hub health` pueda fallar un pipeline sin parsear JSON, y (4) búsqueda
programática de datasets más allá de `list_datasets()`.

## Current state

### Archivo relevante

- `src/chile_hub/core.py` — clase ChileHub (~1790 líneas), build_parser() (línea 1286), _main() (línea 1535)

### Estructuras de datos reales

El catálogo (`self.catalog`, línea 71) se carga desde `dataset_catalog.json` y tiene esta forma:
```python
# self.catalog = {
#     "generated_at_utc": "...",
#     "dataset_count": 15,
#     "datasets": [
#         {
#             "dataset": "comunas",
#             "description": "...",
#             "source_name": "BCN ArcGIS",
#             "record_count": 346,
#             "fields": [...],
#             "reuse_policy": {...},
#             ...
#         },
#         ...
#     ]
# }
```
Métodos existentes que iteran el catálogo — `list_datasets()` (línea 211) y `get_dataset()` (línea 214) — usan `self.catalog.get("datasets", [])`.

Los contratos de schema en `contracts/datasets/*.schema.json` usan un formato **propietario**, NO JSON Schema estándar. Ejemplo real (`contracts/datasets/comunas.schema.json`):
```json
{
  "dataset": "comunas",
  "primary_key": ["codigo_comuna"],
  "required_columns": ["codigo_region", "codigo_provincia", "codigo_comuna", "nombre_comuna", "nombre_comuna_clean"],
  "column_types": {
    "codigo_region": "string",
    "codigo_provincia": "string",
    "codigo_comuna": "string",
    "nombre_comuna": "string"
  },
  "nullable_columns": [],
  "fixed_width_columns": {"codigo_region": 2, "codigo_provincia": 3, "codigo_comuna": 5},
  "expected_record_count": 346,
  "coverage_policy": "full",
  "publish_outputs": ["parquet", "json"]
}
```

Campos disponibles en `source_readiness.json` (cargado por `_load_source_readiness()`, línea 127): `dataset`, `maturity_status` (`"stable"` / `"candidate"`), `source_name`, `license_status`, `source_mode`, `access_method`, `live_ready`, `fallback_allowed`, etc. **No existe campo `category`.**

### D1: Usuarios reescriben joins manualmente

README (líneas 42-46) y los notebooks de ejemplo muestran el mismo patrón:
```python
comunas = hub.load_polars("comunas")
censo = hub.load_polars("censo_comunal")
df = comunas.join(censo, on="codigo_comuna")
```
El builder ya sabe hacer este join: `perfil_territorial_comunal` es una vista consolidada de 8 datasets unidos por CUT, pero está en track `candidate` y no todos los usuarios lo conocen.

### D2: Contratos de schema existen pero no se exponen

`contracts/datasets/*.schema.json` (15 archivos) definen schemas con `required_columns`, `column_types`, `primary_key` y `expected_record_count`. `scripts/verify_pipeline.py` tiene `verify_dataset_contract()` que valida datos contra estos contratos. Pero no hay API pública para que un usuario valide su propio DataFrame.

### D3: CLI siempre retorna exit 0

`src/chile_hub/core.py:1780-1785`:
```python
def main(argv=None):
    try:
        return _main(argv)
    except ChileHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
```
Solo `ChileHubError` produce exit 1. Comandos como `health`, `status`, y `check-sources` siempre retornan 0 aunque los datos estén stale. `hub.health()` retorna `{"overall_status": "ok"|"warn"|"error", ...}`. `hub.status()` retorna `{"overall_status": "ok"|"warn"|"error", ...}`. `hub.check_sources()` retorna `list[dict]` con `"status": "online"|"offline"` por entrada.

### D4: list_datasets() es plano

`src/chile_hub/core.py:211-212`:
```python
def list_datasets(self) -> list[str]:
    return [entry["dataset"] for entry in self.catalog.get("datasets", [])]
```
No hay búsqueda por keyword, fuente, o maturity. El catálogo ya tiene `description`, `source_name`, y `source_readiness.json` tiene `maturity_status` y `source_name` para cada dataset.

### Convenciones del repo

- Snake_case español para API pública.
- Métodos que retornan DataFrames usan Polars. `import polars as pl` ya está en core.py:11.
- CLI se define con `argparse` en `build_parser()` (línea 1286). Handlers en `_main()` (línea 1535) usan `print(json.dumps(...))` para salida JSON y métodos `_table()` para formato tabla.
- No existe helper `_print_result` ni `_output_dataframe` — cada handler usa `print()` directamente.
- Excepciones importadas (línea 14-21): `ChileHubDataError`, `ChileHubDatasetError`, `ChileHubError`, `ChileHubExampleError`, `ChileHubOutputError`.
- Método auxiliar existente: `_load_source_readiness()` (línea 127) — wrapper con `@functools.lru_cache` alrededor de `_load_json_artifact("source_readiness.json")`.
- Tests en `tests/test_chile_hub.py`: clase `ChileHubTests` (línea 89) para API Python, clase `ChileHubCliTests` (línea 996) para CLI. Ambos requieren `data/normalized/` (ejecutar `make build` antes). Patrón CLI: `self.run_cli(*args)` retorna `CompletedProcess` con `.stdout`/`.stderr`/`.returncode`; `self.run_cli_raw(*args)` igual pero con `check=False`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build (prerequisito) | `make build` | exit 0, `data/normalized/` poblado |
| Lint | `.venv/bin/python -m ruff check src/chile_hub/core.py` | exit 0 |
| Format check | `.venv/bin/python -m ruff format --check src/chile_hub/core.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_chile_hub.py -v` | all pass |
| Single test | `.venv/bin/python -m pytest tests/test_chile_hub.py::ChileHubTests::test_cross_view_basic -v` | 1 passed |

## Scope

**In scope** (`src/chile_hub/core.py` y `tests/test_chile_hub.py`):
- `src/chile_hub/core.py` — 4 nuevas capacidades en clase `ChileHub`:
  1. `cross_view()` — join predefinido de datasets por clave territorial común
  2. `validate_user_data()` — validación contra contratos de schema (`required_columns`, `column_types`)
  3. `--exit-code` en CLI parser para `health`, `status`, `check-sources`
  4. `search_datasets()` — búsqueda con filtros por query, source_name, y maturity_status
- `tests/test_chile_hub.py` — tests nuevos en `ChileHubTests` y `ChileHubCliTests`

**Out of scope** (do NOT touch):
- `src/build_dev_db.py` — no modificar el pipeline
- `src/validation.py` — no modificar validadores
- `contracts/datasets/` — los schemas existentes no cambian
- `data/normalized/` — no modificar artefactos
- `docs/` — no actualizar documentación en este plan
- `perfil_territorial_comunal` como dataset estable — requiere estabilizar fallbacks (backlog ME4)

## Git workflow

- Branch: `advisor/017-new-api-capabilities`
- Commit por cada capacidad; mensaje estilo `feat(api): agregar cross_view() para joins predefinidos`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Implementar helper functions

Antes de agregar las capacidades, crear dos helpers que los steps siguientes usarán.
Agregar en `core.py`, antes de la definición de `class ChileHub` (después de `_format_available`, línea 42):

```python
def _print_result(result, fmt="json", output=None):
    """Imprime un resultado dict/list en el formato solicitado."""
    if output:
        import polars as pl
        if isinstance(result, pl.DataFrame):
            if output == "csv":
                result.write_csv(sys.stdout)
            elif output == "parquet":
                result.write_parquet(sys.stdout.buffer)
            elif output == "json":
                result.write_json(sys.stdout, row_oriented=True)
            return
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # table: convertir dict a string formateado
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"{k}: {v}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    print(json.dumps(item, ensure_ascii=False, indent=2))
                else:
                    print(item)
        else:
            print(result)


def _output_dataframe(df, output, fmt):
    """Escribe un DataFrame a stdout o archivo según output y fmt."""
    import sys
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if output.endswith(".csv"):
            df.write_csv(out_path)
        elif output.endswith(".parquet"):
            df.write_parquet(out_path)
        elif output.endswith(".json"):
            df.write_json(out_path, row_oriented=True)
        else:
            raise ValueError(f"Formato de archivo no soportado: {output}. Use .csv, .parquet o .json")
        print(f"Escrito en {output}")
    elif fmt == "json":
        df.write_json(sys.stdout, row_oriented=True)
    else:
        print(df)
```

**Verify**:
```
.venv/bin/python -c "
from src.chile_hub.core import _print_result, _output_dataframe
print('Helpers importados correctamente')
"
```

### Step 2: Implementar cross_view()

Agregar método a la clase `ChileHub` en `core.py`, después de `load_polars()` (~línea 250):

```python
def cross_view(
    self, datasets: list[str], on: str = "codigo_comuna", how: str = "left"
) -> pl.DataFrame:
    """Retorna un cruce predefinido de datasets vinculados por clave territorial.

    Args:
        datasets: Lista de nombres de datasets a cruzar (ej. ["comunas", "censo_comunal"]).
        on: Clave de join (default: "codigo_comuna").
        how: Tipo de join (default: "left").

    Returns:
        DataFrame de Polars con el cruce de todos los datasets.

    Raises:
        ChileHubDatasetError: Si se pasan menos de 2 datasets.
    """
    if len(datasets) < 2:
        raise ChileHubDatasetError(
            f"cross_view requiere al menos 2 datasets. Recibido: {len(datasets)}"
        )

    dfs = []
    for name in datasets:
        df = self.load_polars(name)
        # Prefijar columnas no-clave con el nombre del dataset para evitar colisiones
        cols_to_prefix = [c for c in df.columns if c != on]
        df = df.select(
            [pl.col(on)]
            + [pl.col(c).alias(f"{name}_{c}") for c in cols_to_prefix]
        )
        dfs.append(df)

    result = dfs[0]
    for df in dfs[1:]:
        result = result.join(df, on=on, how=how)
    return result
```

**Verify**:
```
.venv/bin/python -c "
from chile_hub import ChileHub
h = ChileHub()
df = h.cross_view(['comunas', 'censo_comunal'])
print(df.columns)
print(f'Filas: {df.height}')
assert 'comunas_nombre_comuna' in df.columns, f'Falta columna comunas_nombre_comuna, columnas: {df.columns}'
assert 'censo_comunal_poblacion_censada' in df.columns, f'Falta columna censo'
assert df.height == 346, f'Esperaba 346 filas, obtuve {df.height}'
print('OK: cross_view básico')
"
```

### Step 3: Implementar validate_user_data()

Agregar método a la clase `ChileHub`, después de `cross_view()`:

```python
def validate_user_data(self, df: pl.DataFrame, dataset_name: str) -> dict:
    """Valida un DataFrame de usuario contra el contrato de schema del dataset.

    Usa los archivos de contrato en contracts/datasets/*.schema.json, que definen
    required_columns, column_types, primary_key y expected_record_count.

    Args:
        df: DataFrame de Polars a validar.
        dataset_name: Nombre del dataset de referencia (ej. "comunas").

    Returns:
        Dict con:
        - status: "ok" si pasa todas las validaciones, "error" si falla alguna.
        - errors: lista de strings con mensajes de error (vacía si status=="ok").
        - warnings: lista de strings con advertencias no bloqueantes.
        - schema_used: ruta absoluta del schema usado.

    Raises:
        ChileHubDatasetError: Si no existe contrato para el dataset solicitado.
    """
    schema_path = (
        ROOT_DIR / "contracts" / "datasets" / f"{dataset_name}.schema.json"
    )
    if not schema_path.exists():
        raise ChileHubDatasetError(
            f"No existe contrato de schema para '{dataset_name}'. "
            f"Datasets disponibles: {self.list_datasets()}"
        )

    import json as json_module  # evitar colisión con json del scope
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json_module.load(f)

    errors = []
    warnings = []

    # 1. Validar columnas requeridas (required_columns, no "required")
    required_cols = schema.get("required_columns", [])
    df_cols = df.columns
    missing = [c for c in required_cols if c not in df_cols]
    if missing:
        errors.append(f"Columnas requeridas faltantes: {missing}")

    # 2. Validar tipos (column_types, no "properties")
    column_types = schema.get("column_types", {})
    type_map = {
        "string":  ["String", "Utf8", "str"],
        "integer": ["Int64", "Int32", "Int16", "Int8", "UInt32", "UInt16"],
        "number":  ["Float64", "Float32"],
        "boolean": ["Boolean"],
        "date":    ["Date"],
    }
    for col, expected_type in column_types.items():
        if col not in df_cols:
            continue  # ya reportado en missing arriba
        actual_dtype = str(df[col].dtype)
        expected_names = type_map.get(expected_type, [expected_type])
        if actual_dtype not in expected_names:
            errors.append(
                f"Columna '{col}': se esperaba {expected_type}, "
                f"se encontró {actual_dtype}"
            )

    # 3. Validar clave primaria (primary_key)
    primary_key = schema.get("primary_key", [])
    if primary_key:
        pk_cols = [c for c in primary_key if c in df_cols]
        if pk_cols:
            if df.select(pk_cols).null_count().sum(axis=1).to_series().sum() > 0:
                errors.append(f"Clave primaria {primary_key} contiene valores nulos")
            pk_df = df.select(pk_cols)
            if pk_df.height != pk_df.unique().height:
                errors.append(f"Clave primaria {primary_key} tiene valores duplicados")

    # 4. Verificar expected_record_count (solo advertencia)
    expected = schema.get("expected_record_count")
    if expected is not None and df.height != expected:
        warnings.append(
            f"Cantidad de registros ({df.height}) difiere de la esperada ({expected})"
        )

    status = "ok" if not errors else "error"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "schema_used": str(schema_path),
    }
```

**Verify**:
```
.venv/bin/python -c "
import polars as pl
from chile_hub import ChileHub

h = ChileHub()

# DataFrame válido
df = pl.DataFrame({
    'codigo_comuna': ['01101', '01107'],
    'nombre_comuna': ['Iquique', 'Alto Hospicio'],
    'codigo_provincia': ['011', '011'],
    'codigo_region': ['01', '01'],
    'nombre_comuna_clean': ['iquique', 'alto hospicio'],
})
result = h.validate_user_data(df, 'comunas')
assert result['status'] == 'ok', f'Esperaba ok, obtuve: {result}'
print('OK: validación pasa con datos correctos')

# DataFrame con error (falta columna requerida)
df_bad = pl.DataFrame({'codigo_comuna': ['01101']})
result = h.validate_user_data(df_bad, 'comunas')
assert result['status'] == 'error', f'Esperaba error, obtuve: {result}'
assert len(result['errors']) > 0
print('OK: validación detecta columnas faltantes')

# Dataset inexistente
try:
    h.validate_user_data(df, 'dataset_que_no_existe')
    assert False, 'Debió lanzar ChileHubDatasetError'
except Exception as e:
    print(f'OK: lanza {type(e).__name__} para dataset inexistente')
"
```

### Step 4: Implementar search_datasets()

Agregar método a la clase `ChileHub`, después de `validate_user_data()`:

```python
def search_datasets(
    self, query: str = "", source_name: str = "", maturity: str = ""
) -> list[dict]:
    """Busca datasets por keyword, fuente, o nivel de madurez.

    Args:
        query: Texto libre para buscar en nombre y descripción.
        source_name: Filtrar por fuente (ej. "INE", "MINSAL"). Coincidencia parcial
            sin distinción de mayúsculas.
        maturity: Filtrar por maturity_status (ej. "stable", "candidate").

    Returns:
        Lista de dicts con información de cada dataset que coincide:
        {"name", "description", "source_name", "record_count", "maturity_status", "fields"}.
    """
    results = []
    query_lower = query.lower().strip() if query else ""
    source_lower = source_name.lower().strip() if source_name else ""
    maturity_lower = maturity.lower().strip() if maturity else ""

    # Cargar source_readiness para maturity_status (usa el método existente con cache)
    source_readiness = self._load_source_readiness()
    maturity_by_dataset = {
        entry["dataset"]: entry.get("maturity_status", "")
        for entry in source_readiness.get("datasets", [])
    }

    for entry in self.catalog.get("datasets", []):
        name = entry.get("dataset", "")
        desc = entry.get("description", "").lower()

        # Filtro por query: busca en nombre y descripción
        if query_lower:
            if query_lower not in name.lower() and query_lower not in desc:
                continue

        # Filtro por fuente (del catálogo, campo source_name en el entry)
        entry_source = entry.get("source_name", "").lower()
        if source_lower and source_lower not in entry_source:
            continue

        # Filtro por maturity_status (de source_readiness.json)
        if maturity_lower:
            entry_maturity = maturity_by_dataset.get(name, "").lower()
            if maturity_lower != entry_maturity:
                continue

        results.append({
            "name": name,
            "description": entry.get("description", ""),
            "source_name": entry.get("source_name", ""),
            "record_count": entry.get("record_count", 0),
            "maturity_status": maturity_by_dataset.get(name, ""),
            "fields": entry.get("fields", []),
        })

    return results
```

**Verify**:
```
.venv/bin/python -c "
from chile_hub import ChileHub
h = ChileHub()

# Búsqueda por keyword
results = h.search_datasets(query='salud')
assert len(results) >= 1, f'Esperaba al menos 1 resultado, obtuve {len(results)}'
names = [r['name'] for r in results]
assert 'establecimientos_salud' in names, f'Falta establecimientos_salud en {names}'
print(f'Datasets de salud: {names}')

# Búsqueda por fuente
results = h.search_datasets(source_name='INE')
assert len(results) >= 1, f'Esperaba al menos 1 resultado para INE, obtuve {len(results)}'
print(f'Datasets del INE: {[r[\"name\"] for r in results]}')

# Búsqueda por maturity
results = h.search_datasets(maturity='stable')
assert len(results) >= 1
print(f'Datasets stable: {len(results)}')

# Búsqueda combinada
results = h.search_datasets(query='censo', maturity='stable')
assert len(results) >= 1
print(f'Datasets censo + stable: {[r[\"name\"] for r in results]}')

# Sin resultados
results = h.search_datasets(query='zzz_no_existe')
assert len(results) == 0, f'Esperaba 0 resultados, obtuve {len(results)}'
print('OK: búsqueda vacía retorna lista vacía')

print('OK: search_datasets')
"
```

### Step 5: Implementar --exit-code en CLI

En `build_parser()` (~línea 1286 de `core.py`), agregar flag `--exit-code` a los parsers existentes de `health` (línea 1408), `status` (línea 1395), y `check-sources` (línea 1516).

Las líneas exactas a modificar — agregar después del `add_argument("--format", ...)` de cada parser:

```python
# En health_parser (~línea 1414, después de --format):
health_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code 1 si overall_status no es 'ok'.",
)

# En status_parser (~línea 1403, después de --format):
status_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code 1 si overall_status no es 'ok'.",
)

# En check_sources_parser (~línea 1531, después de --timeout):
check_sources_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code 1 si alguna fuente está offline.",
)
```

Luego, en `_main()` (~línea 1535), modificar los handlers de `health`, `status`, y `check-sources`. **No reemplazar** los handlers completos — solo agregar la lógica de exit code después del print existente, usando `raise SystemExit(1)`:

```python
# Handler de health (~línea 1687-1692). Agregar después del bloque if/else de format:
if args.command == "health":
    if args.format == "table":
        print(hub.health_table(), end="")
    else:
        print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
    if getattr(args, "exit_code", False):
        health_data = hub.health()
        if health_data.get("overall_status") != "ok":
            raise SystemExit(1)
    return

# Handler de status (~línea 1664-1669). Agregar después del bloque if/else de format:
if args.command == "status":
    if args.format == "table":
        print(hub.status_table(), end="")
    else:
        print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
    if getattr(args, "exit_code", False):
        status_data = hub.status()
        if status_data.get("overall_status") != "ok":
            raise SystemExit(1)
    return

# Handler de check-sources (~línea 1580-1587). Agregar después del bloque if/else de format:
if args.command == "check-sources":
    timeout = getattr(args, "timeout", 5)
    results = hub.check_sources(timeout=timeout)
    if args.format == "table":
        print(hub.check_sources_table(results), end="")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    if getattr(args, "exit_code", False):
        # check_sources retorna list[dict] con "status": "online"|"offline"
        offline = [s for s in results if s.get("status") == "offline"]
        if offline:
            raise SystemExit(1)
    return
```

**Verify**:
```
# Sin --exit-code, siempre exit 0 (incluso con overall_status != "ok")
.venv/bin/python -m chile_hub health --format json; echo "exit=$?"

# Con --exit-code: verifica que el flag existe en help
.venv/bin/python -m chile_hub health --help | grep -F -- "--exit-code"

# Con --exit-code: verifica comportamiento (nota: el exit code depende del estado real,
# pero podemos verificar que no crashea)
.venv/bin/python -m chile_hub health --exit-code --format json; echo "exit=$?"
.venv/bin/python -m chile_hub status --exit-code --format json; echo "exit=$?"
.venv/bin/python -m chile_hub check-sources --exit-code; echo "exit=$?"
```

### Step 6: Agregar comandos CLI para cross, search, y validate

En `build_parser()`, agregar tres nuevos subparsers. Insertar después de `check_sources_parser` (~línea 1532, antes de `return parser`):

```python
# Subcomando: cross
cross_parser = subparsers.add_parser(
    "cross", help="Cruza datasets por clave territorial comun"
)
cross_parser.add_argument("datasets", nargs="+", help="Datasets a cruzar (min 2)")
cross_parser.add_argument(
    "--on", default="codigo_comuna", help="Clave de join (default: codigo_comuna)"
)
cross_parser.add_argument(
    "--format", choices=["json", "table"], default="table",
    help="Formato de salida (default: table)"
)
cross_parser.add_argument(
    "--output", default=None,
    help="Archivo de salida (.csv, .parquet, o .json)"
)

# Subcomando: search
search_parser = subparsers.add_parser(
    "search", help="Busca datasets por keyword, fuente o madurez"
)
search_parser.add_argument(
    "query", nargs="?", default="", help="Texto de búsqueda en nombre y descripción"
)
search_parser.add_argument(
    "--source", default="", help="Filtrar por fuente (ej. 'INE', 'MINSAL')"
)
search_parser.add_argument(
    "--maturity", default="", help="Filtrar por madurez ('stable' o 'candidate')"
)
search_parser.add_argument(
    "--format", choices=["json", "table"], default="json",
    help="Formato de salida (default: json)"
)

# Subcomando: validate
validate_parser = subparsers.add_parser(
    "validate", help="Valida un archivo CSV o Parquet contra un schema del hub"
)
validate_parser.add_argument("path", help="Ruta al archivo a validar (.csv o .parquet)")
validate_parser.add_argument(
    "--dataset", required=True, help="Dataset de referencia (ej. 'comunas')"
)
```

Agregar handlers en `_main()`, antes de `if args.command == "summary":` (~línea 1772):

```python
if args.command == "cross":
    df = hub.cross_view(args.datasets, on=args.on)
    _output_dataframe(df, args.output, args.format)
    return

if args.command == "search":
    results = hub.search_datasets(
        query=args.query,
        source_name=args.source,
        maturity=args.maturity,
    )
    _print_result(results, args.format)
    return

if args.command == "validate":
    # Leer archivo de entrada
    path = Path(args.path)
    if not path.exists():
        raise ChileHubError(f"Archivo no encontrado: {args.path}")
    if path.suffix == ".csv":
        df = pl.read_csv(path)
    elif path.suffix == ".parquet":
        df = pl.read_parquet(path)
    else:
        raise ChileHubError(
            f"Formato no soportado: {path.suffix}. Use .csv o .parquet."
        )
    result = hub.validate_user_data(df, args.dataset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error":
        raise SystemExit(1)
    return
```

**Verify**:
```
# Los nuevos comandos aparecen en help
.venv/bin/python -m chile_hub --help | grep -E "cross|search|validate"

# search con keyword
.venv/bin/python -m chile_hub search salud

# search con filtro de fuente
.venv/bin/python -m chile_hub search --source INE

# search con filtro de madurez
.venv/bin/python -m chile_hub search --maturity stable

# cross con 2 datasets
.venv/bin/python -m chile_hub cross comunas censo_comunal --format table

# validate con archivo CSV válido
.venv/bin/python -c "
import polars as pl
pl.DataFrame({
    'codigo_comuna': ['01101'],
    'nombre_comuna': ['Iquique'],
    'codigo_provincia': ['011'],
    'codigo_region': ['01'],
    'nombre_comuna_clean': ['iquique'],
}).write_csv('/tmp/test_comunas.csv')
"
.venv/bin/python -m chile_hub validate /tmp/test_comunas.csv --dataset comunas
```

### Step 7: Lint, format y tests

```
.venv/bin/python -m ruff check src/chile_hub/core.py
.venv/bin/python -m ruff format --check src/chile_hub/core.py
.venv/bin/python -m ruff check tests/test_chile_hub.py
.venv/bin/python -m ruff format --check tests/test_chile_hub.py
.venv/bin/python -m pytest tests/test_chile_hub.py -v
```

## Test plan

Todos los tests nuevos van en `tests/test_chile_hub.py`. Requieren `make build` previo.

### En ChileHubTests (API Python)

Seguir el patrón de `test_load_polars` (línea 129): usar `self.hub` y `self.catalog_by_dataset` del `setUpClass`.

| Test | Qué verifica |
|------|-------------|
| `test_cross_view_basic` | `hub.cross_view(["comunas", "censo_comunal"])` retorna DataFrame con 346 filas y columnas prefijadas (`comunas_nombre_comuna`, `censo_comunal_poblacion_censada`) |
| `test_cross_view_single_dataset_error` | `hub.cross_view(["comunas"])` lanza `ChileHubDatasetError` |
| `test_cross_view_three_datasets` | `hub.cross_view(["comunas", "censo_comunal", "censo_hogares_viviendas"])` retorna DataFrame con 346 filas |
| `test_validate_user_data_ok` | DataFrame con columnas requeridas → status "ok" |
| `test_validate_user_data_missing_column` | DataFrame sin `nombre_comuna` → status "error", errors no vacío |
| `test_validate_user_data_unknown_dataset` | `validate_user_data(df, "no_existe")` lanza `ChileHubDatasetError` |
| `test_validate_user_data_duplicate_pk` | DataFrame con `codigo_comuna` duplicado → status "error" |
| `test_search_datasets_query` | `hub.search_datasets(query="salud")` retorna ≥1 resultado incluyendo "establecimientos_salud" |
| `test_search_datasets_source` | `hub.search_datasets(source_name="INE")` retorna ≥1 resultado |
| `test_search_datasets_maturity` | `hub.search_datasets(maturity="stable")` retorna ≥1 resultado |
| `test_search_datasets_no_results` | `hub.search_datasets(query="zzz_no_existe")` retorna lista vacía |

### En ChileHubCliTests (CLI)

Seguir el patrón de `test_cli_list` (línea 1034): usar `self.run_cli(*args)` para éxito y `self.run_cli_raw(*args)` para verificar exit codes.

| Test | Qué verifica |
|------|-------------|
| `test_cli_cross` | `run_cli("cross", "comunas", "censo_comunal", "--format", "json")` exit 0, stdout contiene columnas |
| `test_cli_search` | `run_cli("search", "salud")` exit 0, stdout contiene "establecimientos_salud" |
| `test_cli_search_source` | `run_cli("search", "--source", "INE")` exit 0, stdout no vacío |
| `test_cli_search_maturity` | `run_cli("search", "--maturity", "stable")` exit 0, stdout no vacío |
| `test_cli_validate_ok` | Crear CSV temporal válido, `run_cli("validate", path, "--dataset", "comunas")` exit 0 |
| `test_cli_validate_error` | Crear CSV con columnas faltantes, `run_cli_raw("validate", path, "--dataset", "comunas")` exit 1 |
| `test_cli_health_exit_code` | `run_cli("health", "--exit-code", "--format", "json")` no crashea (exit code depende del estado) |

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m ruff check tests/test_chile_hub.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py -v` all pass (≥18 tests nuevos)
- [ ] `hub.cross_view(["comunas", "censo_comunal"])` retorna DataFrame con 346 filas y columnas prefijadas
- [ ] `hub.validate_user_data(df, "comunas")` valida contra `required_columns` y `column_types` del contrato real
- [ ] `hub.search_datasets("salud")` retorna resultados que incluyen datasets de salud
- [ ] `hub.search_datasets(maturity="stable")` retorna solo datasets con maturity_status "stable"
- [ ] `chile-hub health --exit-code` retorna exit 1 si `overall_status != "ok"`
- [ ] `chile-hub status --exit-code` retorna exit 1 si `overall_status != "ok"`
- [ ] `chile-hub check-sources --exit-code` retorna exit 1 si hay fuentes offline
- [ ] `chile-hub cross`, `chile-hub search`, y `chile-hub validate` aparecen en `chile-hub --help`
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones citadas en "Current state" no coincide con los excerpts (el código ha cambiado desde que se escribió este plan).
- `contracts/datasets/{name}.schema.json` no existe para algún dataset referenciado — `validate_user_data` depende de estos archivos.
- `source_readiness.json` no existe en `data/normalized/` — `search_datasets(maturity=...)` lo requiere.
- `self.catalog` no tiene la estructura `{"datasets": [ {...}, ... ]}` descrita en Current state — `search_datasets` y los métodos existentes dependen de este formato.
- `cross_view` con datasets grandes (empresas, ~1.57M filas) consume demasiada memoria. Si ocurre, documentar como limitación conocida y recomendar `load_polars` + join manual.
- La validación de tipos en `validate_user_data` es demasiado laxa o estricta para los schemas existentes. Ajustar `type_map` según lo que los contratos realmente declaran en `column_types`.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- `cross_view` usa prefijos `{dataset}_` para columnas no-clave. Si dos datasets tienen columnas con el mismo nombre, se desambiguan automáticamente. Si el nombre prefijado resultante excede el límite de nombres de columna de algún formato de salida, se necesitará truncamiento.
- `validate_user_data` hace validación de columnas requeridas, tipos y unicidad de PK. No valida restricciones `fixed_width_columns` ni `nullable_columns` — eso requeriría `fastjsonschema` o una segunda pasada, diferida a una versión futura.
- `search_datasets` usa `maturity_status` de `source_readiness.json`. Si en el futuro se agrega un campo `category` u otros metadatos, extender los filtros sin cambiar la firma (agregar parámetros opcionales).
- Los nuevos comandos CLI (`cross`, `search`, `validate`) deben documentarse en `README.md` y `AGENTS.md` en un plan de docs futuro.
- `_print_result` y `_output_dataframe` son nuevos helpers. Si en el futuro se consolidan con patrones existentes de pretty-printing, revisar todos los call sites.
- El flag `--exit-code` usa `getattr(args, "exit_code", False)` porque argparse convierte `--exit-code` en `args.exit_code`. Si el parser no define el flag para un comando, `getattr` evita `AttributeError`.
