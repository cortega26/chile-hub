# Plan 017: Nuevas capacidades de API — cruces, validación de usuario, exit codes, y búsqueda

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/chile_hub/core.py`
> Si el archivo cambió desde que se escribió este plan, compara los excerpts de
> "Current state" contra el código vivo antes de proceder; si hay diferencias,
> trata como STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW
- **Depends on**: Plan 011 (ChileHubDatasetError para mensajes de error) y Plan 013 (cache para rendimiento de cruces)
- **Category**: direction
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

Cuatro adiciones a la API que resuelven fricción documentada de los usuarios,
todas de bajo riesgo por ser puramente aditivas: (1) vista pre-joined por CUT
para que los usuarios no reescriban el mismo join de 3 líneas en cada script, (2)
validación de datos externos contra los JSON Schemas del hub para que usuarios
puedan verificar sus propios datos, (3) exit codes para CI de manera que
`chile-hub health` pueda fallar un pipeline sin parsear JSON, y (4) búsqueda
programática de datasets más allá de `list_datasets()`.

## Current state

### Archivo relevante

- `src/chile_hub/core.py` — clase ChileHub (~1750 líneas), CLI parser (línea 1247)

### D1: Usuarios reescriben joins manualmente

README (líneas 42-46) y los notebooks de ejemplo muestran el mismo patrón:
```python
comunas = hub.load_polars("comunas")
censo = hub.load_polars("censo_comunal")
df = comunas.join(censo, on="codigo_comuna")
```
El builder ya sabe hacer este join: `perfil_territorial_comunal` (en
`source_registry.json:262-292`) es una vista consolidada de 8 datasets unidos
por CUT, pero está en track `candidate` y no llega a usuarios.

### D2: JSON Schemas existen pero no se exponen

`contracts/datasets/*.schema.json` (15 archivos) definen schemas completos.
`scripts/verify_pipeline.py:115-164` tiene `verify_dataset_contract()` que valida
datos contra estos schemas vía `fastjsonschema`. Pero no hay API pública para que
un usuario valide su propio DataFrame.

### D3: CLI siempre retorna exit 0

`src/chile_hub/core.py:1741-1746`:
```python
def main(argv=None):
    try:
        return _main(argv)
    except ChileHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
```
Solo `ChileHubError` produce exit 1. Comandos como `health`, `status`, y
`check-sources` siempre retornan 0 aunque los datos estén stale.

### D4: list_datasets() es plano

`src/chile_hub/core.py:189-190`:
```python
def list_datasets(self) -> list[str]:
    return sorted(self.catalog.keys())
```
No hay búsqueda por keyword, categoría, fuente, o descripción. El catálogo JSON
ya tiene `description`, `source_name`, `reuse_policy` para cada dataset.

### Convenciones del repo

- Snake_case español para API pública.
- Métodos que retornan DataFrames usan Polars.
- CLI se define con `argparse` en `build_parser()`.
- Tests en `tests/test_chile_hub.py::ChileHubTests` y `ChileHubCliTests`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/chile_hub/core.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_chile_hub.py -v` | all pass |
| Build | `make build` (necesario para tener datos normalizados) | exit 0 |

## Scope

**In scope**:
- `src/chile_hub/core.py` — 4 nuevas capacidades:
  1. `cross_view()` — join predefinido de datasets por CUT
  2. `validate_user_data()` — validación contra JSON Schema
  3. `--exit-code` en CLI parser para `health`, `status`, `check-sources`
  4. `search_datasets()` — búsqueda con filtros

**Out of scope** (do NOT touch):
- `src/build_dev_db.py` — no modificar el pipeline
- `contracts/datasets/` — los schemas existentes no cambian
- `data/normalized/` — no modificar artefactos
- `docs/` — no actualizar documentación en este plan
- `perfil_territorial_comunal` como dataset estable — requiere estabilizar fallbacks (ME4)

## Git workflow

- Branch: `advisor/017-new-api-capabilities`
- Commit por cada capacidad; mensaje estilo `feat(api): ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Implementar cross_view()

Agregar método a `ChileHub` en `core.py`:

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
    """
    if len(datasets) < 2:
        raise ChileHubDatasetError("cross_view requiere al menos 2 datasets.")

    dfs = []
    for name in datasets:
        df = self.load_polars(name)
        # Si hay columnas duplicadas (aparte de la clave), prefijar con el nombre del dataset
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
assert 'comunas_nombre_comuna' in df.columns
assert 'censo_comunal_poblacion_censada' in df.columns
print('OK')
"
```

### Step 2: Implementar validate_user_data()

Agregar método a `ChileHub`:

```python
def validate_user_data(self, df: pl.DataFrame, dataset_name: str) -> dict:
    """Valida un DataFrame de usuario contra el contrato de schema del dataset.

    Args:
        df: DataFrame de Polars a validar.
        dataset_name: Nombre del dataset de referencia (ej. "comunas").

    Returns:
        Dict con status ("ok"/"error"), errors (lista), y schema_used.
    """
    import json
    from pathlib import Path

    # Cargar el schema contract
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "datasets"
        / f"{dataset_name}.schema.json"
    )
    if not schema_path.exists():
        raise ChileHubDatasetError(
            f"No existe contrato de schema para '{dataset_name}'. "
            f"Datasets disponibles: {self.list_datasets()}"
        )

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Validar columnas requeridas
    required_cols = schema.get("required", [])
    df_cols = df.columns
    missing = [c for c in required_cols if c not in df_cols]
    if missing:
        return {
            "status": "error",
            "errors": [f"Columnas requeridas faltantes: {missing}"],
            "schema_used": str(schema_path),
        }

    # Validar tipos (básico: verificar que las columnas existen)
    properties = schema.get("properties", {})
    type_errors = []
    for col, prop in properties.items():
        if col in df_cols:
            expected_type = prop.get("type", "string")
            # Verificación básica de tipo Polars → JSON Schema
            polars_dtype = str(df[col].dtype).lower()
            type_map = {
                "string": ["string", "str", "utf8"],
                "integer": ["int64", "int32", "int16", "int8"],
                "number": ["float64", "float32"],
                "boolean": ["bool"],
            }
            if polars_dtype not in type_map.get(expected_type, []):
                type_errors.append(
                    f"Columna '{col}': se esperaba {expected_type}, "
                    f"se encontró {polars_dtype}"
                )

    if type_errors:
        return {
            "status": "error",
            "errors": type_errors,
            "schema_used": str(schema_path),
        }

    return {"status": "ok", "errors": [], "schema_used": str(schema_path)}
```

**Verify**:
```
.venv/bin/python -c "
import polars as pl
from chile_hub import ChileHub

h = ChileHub()
# DataFrame válido
df = pl.DataFrame({'codigo_comuna': ['01101'], 'nombre_comuna': ['Iquique']})
result = h.validate_user_data(df, 'comunas')
assert result['status'] == 'ok', f'Esperaba ok, obtuve {result}'
print('OK: validación de datos de usuario')
"
```

### Step 3: Implementar --exit-code en CLI

En `build_parser()` (línea ~1247 de `core.py`), agregar flag `--exit-code` a los
subcomandos `health`, `status`, y `check-sources`:

```python
# En el parser de 'health':
health_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code no cero si el hub no está saludable.",
)

# En el parser de 'status':
status_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code no cero si el estado no es 'ok'.",
)

# En el parser de 'check-sources':
check_sources_parser.add_argument(
    "--exit-code",
    action="store_true",
    help="Retorna exit code no cero si alguna fuente está offline.",
)
```

Luego en el handler de cada comando en `_main()`, verificar el flag y ajustar
`SystemExit`:

```python
if args.command == "health":
    result = hub.health()
    _print_result(result, args.format, args.output)
    if args.exit_code and result.get("overall_status") != "ok":
        raise SystemExit(1)
    return

if args.command == "status":
    result = hub.status()
    _print_result(result, args.format, args.output)
    if args.exit_code and result.get("status") != "ok":
        raise SystemExit(1)
    return

if args.command == "check-sources":
    result = hub.check_sources()
    _print_result(result, args.format, args.output)
    if args.exit_code:
        offline_sources = [s for s in result if s.get("status") == "offline"]
        if offline_sources:
            raise SystemExit(1)
    return
```

**Verify**:
```
# Con --exit-code, debe fallar si hay problemas
.venv/bin/python -m chile_hub health --exit-code
echo "Exit code: $?"
```

### Step 4: Implementar search_datasets()

Agregar método a `ChileHub`:

```python
def search_datasets(
    self, query: str = "", source: str = "", category: str = ""
) -> list[dict]:
    """Busca datasets por keyword, fuente, o categoría.

    Args:
        query: Texto libre para buscar en nombre y descripción.
        source: Filtrar por fuente (ej. "INE", "MINSAL").
        category: Filtrar por categoría (ej. "demografía", "economía").

    Returns:
        Lista de dicts con información de cada dataset que coincide.
    """
    results = []
    query_lower = query.lower()

    # Cargar source_registry para metadatos adicionales
    source_registry = self._load_json_artifact("source_readiness.json")

    for name in self.catalog:
        entry = self.catalog[name]
        desc = entry.get("description", "").lower()
        source_name = entry.get("reuse_policy", {}).get("source_name", "").lower()

        # Filtro por query
        if query_lower:
            if query_lower not in name.lower() and query_lower not in desc:
                continue

        # Filtro por fuente
        if source and source.lower() not in source_name:
            continue

        # Filtro por categoría (del source_registry)
        if category:
            registry_entry = source_registry.get(name, {})
            cats = registry_entry.get("category", [])
            if category.lower() not in [c.lower() for c in cats]:
                continue

        results.append({
            "name": name,
            "description": entry.get("description", ""),
            "source": entry.get("reuse_policy", {}).get("source_name", ""),
            "record_count": entry.get("expected_record_count", 0),
            "fields": entry.get("fields", []),
        })

    return results
```

**Verify**:
```
.venv/bin/python -c "
from chile_hub import ChileHub
h = ChileHub()
# Buscar datasets de salud
results = h.search_datasets(query='salud')
assert len(results) >= 1, f'Esperaba al menos 1 resultado, obtuve {len(results)}'
print(f'Datasets de salud: {[r[\"name\"] for r in results]}')

# Buscar datasets del INE
results = h.search_datasets(source='INE')
assert len(results) >= 1
print(f'Datasets del INE: {[r[\"name\"] for r in results]}')
print('OK')
"
```

### Step 5: Agregar comandos CLI correspondientes

En `build_parser()`, agregar:

```python
# Subcomando: cross
cross_parser = subparsers.add_parser("cross", help="Cruza datasets por clave territorial")
cross_parser.add_argument("datasets", nargs="+", help="Datasets a cruzar")
cross_parser.add_argument("--on", default="codigo_comuna", help="Clave de join")
cross_parser.add_argument("--format", choices=["json", "table"], default="table")
cross_parser.add_argument("--output", choices=["csv", "parquet", "json"], default=None)

# Subcomando: search
search_parser = subparsers.add_parser("search", help="Busca datasets por keyword o filtros")
search_parser.add_argument("query", nargs="?", default="", help="Texto de búsqueda")
search_parser.add_argument("--source", default="", help="Filtrar por fuente")
search_parser.add_argument("--category", default="", help="Filtrar por categoría")
search_parser.add_argument("--format", choices=["json", "table"], default="table")

# Subcomando: validate
validate_parser = subparsers.add_parser("validate", help="Valida un archivo CSV/Parquet contra un schema")
validate_parser.add_argument("path", help="Ruta al archivo a validar")
validate_parser.add_argument("--dataset", required=True, help="Dataset de referencia")
```

Agregar handlers en `_main()`:

```python
if args.command == "cross":
    df = hub.cross_view(args.datasets, on=args.on)
    _output_dataframe(df, args.output, args.format)
    return

if args.command == "search":
    results = hub.search_datasets(args.query, source=args.source, category=args.category)
    _print_result(results, args.format, args.output)
    return

if args.command == "validate":
    if args.path.endswith(".csv"):
        df = pl.read_csv(args.path)
    elif args.path.endswith(".parquet"):
        df = pl.read_parquet(args.path)
    else:
        raise ChileHubError(f"Formato no soportado: {args.path}. Use CSV o Parquet.")
    result = hub.validate_user_data(df, args.dataset)
    _print_result(result, args.format, args.output)
    if result["status"] == "error":
        raise SystemExit(1)
    return
```

**Verify**:
```
.venv/bin/python -m chile_hub search salud
.venv/bin/python -m chile_hub cross comunas censo_comunal --format table
```

### Step 6: Lint y tests

```
.venv/bin/python -m ruff check src/chile_hub/core.py
.venv/bin/python -m ruff format --check src/chile_hub/core.py
.venv/bin/python -m pytest tests/test_chile_hub.py -v
```

## Test plan

- **test_cross_view_basic**: `cross_view(["comunas", "censo_comunal"])` retorna
  DataFrame con columnas prefijadas y 346 filas.
- **test_cross_view_single_dataset_error**: `cross_view(["comunas"])` levanta
  `ChileHubDatasetError`.
- **test_validate_user_data_ok**: DataFrame con columnas correctas → status "ok".
- **test_validate_user_data_missing_column**: DataFrame sin columna requerida →
  status "error".
- **test_search_datasets_query**: `search_datasets("salud")` retorna al menos 1
  resultado.
- **test_search_datasets_source**: `search_datasets(source="INE")` retorna al
  menos 1 resultado.
- **test_cli_cross**: `self.run_cli("cross", "comunas", "censo_comunal")`
  retorna output no vacío.
- **test_cli_search**: `self.run_cli("search", "salud")` retorna output con
  "establecimientos_salud".
- **test_cli_health_exit_code**: Verificar que `--exit-code` causa exit 1 cuando
  `overall_status != "ok"` (mockeando `hub.health()`).

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/chile_hub/core.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py -v` all pass (incluyendo ≥9 tests nuevos)
- [ ] `hub.cross_view(["comunas", "censo_comunal"])` retorna DataFrame con 346 filas
- [ ] `hub.validate_user_data(df, "comunas")` retorna dict con status "ok"/"error"
- [ ] `hub.search_datasets("salud")` retorna resultados que incluyen datasets de salud
- [ ] `chile-hub health --exit-code` retorna exit 1 si overall_status != "ok"
- [ ] `chile-hub cross` y `chile-hub search` aparecen en `chile-hub --help`
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- `contracts/datasets/{name}.schema.json` no existe para algún dataset — el
  validador de usuario depende de estos archivos.
- `_output_dataframe()` no existe como helper — implementarlo como:
  ```python
  def _output_dataframe(df, output, format):
      if output == "csv":
          df.write_csv(sys.stdout)
      elif output == "parquet":
          df.write_parquet(sys.stdout.buffer)
      else:
          print(df)
  ```
- `cross_view` con datasets grandes (empresas, 1.57M filas) consume demasiada
  memoria. Si ocurre, documentar como limitación conocida y recomendar
  `load_polars` + join manual.
- La validación de tipos en `validate_user_data` es demasiado laxa o estricta
  para los schemas existentes. Ajustar el type_map según lo que los schemas
  realmente declaran.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- `cross_view` usa prefijos `{dataset}_` para columnas no-clave. Si dos datasets
  tienen columnas con el mismo nombre, se desambiguan automáticamente.
- `validate_user_data` hace validación básica de columnas y tipos. No reemplaza
  una validación completa con `fastjsonschema` — si se requiere validación
  exhaustiva (valores enum, patrones regex, rangos numéricos), migrar a usar
  `fastjsonschema` en una versión futura.
- `search_datasets` depende de que `source_registry.json` tenga campo `category`.
  Si no existe, la búsqueda por categoría no rompe pero retorna vacío.
- Los nuevos comandos CLI (`cross`, `search`, `validate`) deben documentarse en
  `README.md` y `AGENTS.md` en un plan de docs futuro.
