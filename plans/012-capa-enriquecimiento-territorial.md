# Plan 012: Exponer la capa de enriquecimiento territorial como dataset publicable

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- src/extractors/subdere_extractor.py src/build_dev_db.py`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P2
- **Esfuerzo**: M
- **Riesgo**: LOW
- **Depende de**: 009 (registro de datasets centralizado, facilita el registro)
- **Categoría**: direction
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

El extractor de comunas ya computa un enriquecimiento demográfico completo (coords + población INE 2022) internamente, pero estos datos solo se exponen integrados en el dataset de comunas. Un dataset `comunas_enriquecidas` (o `demografia_base`) daría acceso directo a la combinación más frecuente en análisis: código CUT + coordenadas + población + jerarquía territorial. El costo de pipeline es cero (los datos ya se calculan) y el caso de uso está validado en `examples/demo_usage.py:57-62`.

Este plan NO agrega nuevas fuentes ni extrae nuevos datos. Solo expone como artefacto publicable lo que el pipeline ya produce.

## Estado actual

### El enriquecimiento ocurre en `src/extractors/subdere_extractor.py:330-387`

```python
# subdere_extractor.py:330-387 — enriquecimiento de coords e INE
df_clean = df_clean.join(coords_ref, on="codigo_comuna", how="left").with_columns([
    pl.when(pl.col("latitud_cabecera") == 0.0).then(pl.col("_lat_ref"))...
])
df_clean = df_clean.join(pob_ref, on="codigo_comuna", how="left").with_columns(
    pl.when(pl.col("poblacion_estimada") == 0).then(pl.col("_pob_ref"))...
)
```

El CSV de staging `data/staging/comunas.csv` ya contiene el enriquecimiento completo. Las columnas son:

```
codigo_comuna, nombre_comuna, nombre_comuna_clean,
codigo_provincia, nombre_provincia,
codigo_region, nombre_region,
latitud_cabecera, longitud_cabecera, poblacion_estimada
```

### Cómo `DATASET_CATALOG_CONFIG` registra un dataset (patrón existente en `build_dev_db.py:34-65`)

```python
DATASET_CATALOG_CONFIG = {
    "regiones": {
        "description": "...",
        "join_keys": ["codigo_region"],
        "confidence_tier": "Tier B",
        "expected_record_count": 16,
        "reuse_policy": { "status": "open-attribution", "license": "CC BY", ... },
        "freshness_policy": { "max_age_hours": 24 * 90, "label": "estable" },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('regiones')",
            "duckdb": "SELECT *\nFROM 'data/normalized/regiones.parquet'\nORDER BY codigo_region;",
            "cli": "python -m src.chile_hub show regiones",
        },
        "outputs": {
            "parquet": "data/normalized/regiones.parquet",
            "json": "data/normalized/regiones.json",
            "duckdb_table": "regiones",
            "sqlite_table": "regiones",
            "excel_sheet": "Regiones",
        },
        "documentation": "docs/datasets/regiones.md",
    },
    ...
}
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr extractor de comunas | `.venv/bin/python src/extractors/subdere_extractor.py` | exit 0 |
| Build completo | `make build` | exit 0 |
| Verificar dataset | `python3 -c "import polars as pl; df = pl.read_parquet('data/normalized/comunas_enriquecidas.parquet'); print(df.shape)"` | `(346, 10)` o similar |
| Tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| CLI | `.venv/bin/python -m src.chile_hub show comunas_enriquecidas` | imprime schema |

## Alcance

**En scope**:
- `src/build_dev_db.py` — agregar entrada en `DATASET_CATALOG_CONFIG` y lógica de construcción del artefacto
- `tests/test_chile_hub.py` — agregar test de carga del nuevo dataset
- `docs/datasets/comunas_enriquecidas.md` — crear

**Fuera de scope**:
- `src/extractors/subdere_extractor.py` — no modificar; el enriquecimiento ya ocurre ahí
- El dataset `comunas` existente — no cambiar

## Git workflow

- Rama: `advisor/012-capa-enriquecimiento-territorial`
- Estilo de commit: `feat: exponer capa de enriquecimiento territorial como dataset publicable`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Decidir el nombre y schema del nuevo dataset

El dataset se llamará `comunas_enriquecidas`. Es un alias del dataset `comunas` con la misma fuente — la diferencia es conceptual: hace explícito que estos datos incluyen enriquecimiento de coords y población INE que la fuente primaria (BCN ArcGIS) no siempre provee.

Schema idéntico al de `comunas`:
```
codigo_comuna (str, 5 chars), nombre_comuna (str), nombre_comuna_clean (str),
codigo_provincia (str, 3 chars), nombre_provincia (str),
codigo_region (str, 2 chars), nombre_region (str),
latitud_cabecera (float64), longitud_cabecera (float64), poblacion_estimada (int32)
```

### Paso 2: Registrar en `DATASET_CATALOG_CONFIG`

Agregar la entrada `"comunas_enriquecidas"` en `DATASET_CATALOG_CONFIG` en `src/build_dev_db.py`, después de la entrada `"comunas"`:

```python
"comunas_enriquecidas": {
    "description": (
        "Dataset de comunas con enriquecimiento de coordenadas (INE/BCN) y "
        "proyección de población INE 2022. Útil para análisis con dimension geoespacial "
        "o demográfica sin necesidad de joins adicionales."
    ),
    "join_keys": ["codigo_comuna"],
    "confidence_tier": "Tier B",
    "expected_record_count": 346,
    "reuse_policy": {
        "status": "open-attribution",
        "license": "CC BY",
        "license_url": "https://datos.bcn.cl/es/informacion/lo-que-esta-haciendo-bcn",
        "attribution_required": True,
        "redistribution_ok": True,
        "summary": "Derivada de datos abiertos BCN con enriquecimiento de coords e INE.",
    },
    "freshness_policy": {
        "max_age_hours": 24 * 90,
        "label": "estable",
    },
    "usage_examples": {
        "python": (
            "from src.chile_hub import ChileHub\n\n"
            "hub = ChileHub()\n"
            "df = hub.load_polars('comunas_enriquecidas')\n"
            "# df tiene coords y población directamente"
        ),
        "duckdb": (
            "SELECT codigo_comuna, nombre_comuna, latitud_cabecera, "
            "longitud_cabecera, poblacion_estimada\n"
            "FROM 'data/normalized/comunas_enriquecidas.parquet'\n"
            "ORDER BY poblacion_estimada DESC LIMIT 10;"
        ),
        "cli": "python -m src.chile_hub show comunas_enriquecidas",
    },
    "outputs": {
        "parquet": "data/normalized/comunas_enriquecidas.parquet",
        "json": "data/normalized/comunas_enriquecidas.json",
        "duckdb_table": "comunas_enriquecidas",
        "sqlite_table": "comunas_enriquecidas",
        "excel_sheet": "ComunasEnriquecidas",
    },
    "documentation": "docs/datasets/comunas_enriquecidas.md",
},
```

### Paso 3: Agregar la lógica de build en `build_dev_db.py`

Buscar dónde `build_dev_db.py` escribe el dataset `comunas` (parquet, json, duckdb, sqlite, excel). Es el mismo DataFrame. Reutilizarlo para `comunas_enriquecidas`:

En el bloque `main()` o en la función de build que procesa `comunas`, después de escribir `comunas.parquet`, agregar:

```python
# comunas_enriquecidas es un alias enriquecido de comunas — mismo DataFrame
df_comunas_enriquecidas = df_comunas  # ya tiene coords y población del extractor
df_comunas_enriquecidas.write_parquet(
    os.path.join(NORMALIZED_DIR, "comunas_enriquecidas.parquet")
)
df_comunas_enriquecidas.write_ndjson(
    os.path.join(NORMALIZED_DIR, "comunas_enriquecidas.json")
)
# Registrar en DuckDB y SQLite con el nombre "comunas_enriquecidas"
# (seguir el mismo patrón que se usa para comunas)
```

**Nota para el ejecutor**: Buscar en `build_dev_db.py` la función o bloque donde se escribe `comunas.parquet` y replicar el patrón para `comunas_enriquecidas`. No es necesario un extractor separado.

**Verificar**: `ls data/normalized/comunas_enriquecidas.*` — lista los artefactos generados.

### Paso 4: Agregar el nuevo dataset a la validación

Agregar en `build_dev_db.py` una entrada de validación para `comunas_enriquecidas` que reutilice `validate_comunas`:

```python
validation_comunas_enriquecidas = validate_comunas(df_comunas_enriquecidas, comunas_metadata)
validation_comunas_enriquecidas["dataset"] = "comunas_enriquecidas"
```

### Paso 5: Correr el build

```bash
make build
```

**Verificar**: exit 0. `ls data/normalized/comunas_enriquecidas.*` muestra `.parquet` y `.json`.

### Paso 6: Verificar el dataset via CLI

```bash
.venv/bin/python -m src.chile_hub show comunas_enriquecidas
.venv/bin/python -m src.chile_hub list
```

**Verificar**: `comunas_enriquecidas` aparece en la lista y `show` muestra el schema.

### Paso 7: Agregar tests

En `tests/test_chile_hub.py`, agregar al final de `ChileHubTests`:

```python
def test_load_polars_comunas_enriquecidas(self):
    df = self.hub.load_polars("comunas_enriquecidas")
    self.assertGreater(df.height, 0)
    self.assertIn("codigo_comuna", df.columns)
    self.assertIn("latitud_cabecera", df.columns)
    self.assertIn("poblacion_estimada", df.columns)
    # Verificar que los datos de enriquecimiento están presentes
    non_zero_coords = df.filter(pl.col("latitud_cabecera") != 0.0).height
    self.assertGreater(non_zero_coords, 300,
        "La mayoría de comunas debe tener coordenadas (enriquecimiento activo)")
    non_zero_pop = df.filter(pl.col("poblacion_estimada") > 0).height
    self.assertGreater(non_zero_pop, 300,
        "La mayoría de comunas debe tener población estimada (enriquecimiento INE activo)")
```

**Verificar**: `.venv/bin/python -m unittest tests.test_chile_hub.ChileHubTests.test_load_polars_comunas_enriquecidas -v` — pasa.

### Paso 8: Crear `docs/datasets/comunas_enriquecidas.md`

Crear el archivo con descripción breve, schema, fuentes de enriquecimiento, ejemplos de uso y limitaciones. Seguir el patrón de `docs/datasets/comunas.md`.

## Criterios de done

- [ ] `data/normalized/comunas_enriquecidas.parquet` existe después de `make build`
- [ ] `data/normalized/comunas_enriquecidas.json` existe
- [ ] `.venv/bin/python -m src.chile_hub list` incluye `comunas_enriquecidas`
- [ ] `.venv/bin/python -m src.chile_hub show comunas_enriquecidas` muestra schema sin error
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] `docs/datasets/comunas_enriquecidas.md` existe
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si el DataFrame de `comunas` en `build_dev_db.py` no tiene `latitud_cabecera` o `poblacion_estimada` (columnas que provee el enriquecimiento) — el extractor no corrió o el enriquecimiento falló. Correr `make extract` primero y verificar.
- Si registrar el dataset en el catálogo rompe la cuenta de `dataset_count` en tests existentes — actualizar la assertion del test correspondiente.

## Notas de mantenimiento

- `comunas_enriquecidas` y `comunas` comparten la misma fuente de datos. Si cambia la normalización de comunas, ambos datasets se actualizan automáticamente en el mismo build.
- Si en el futuro se incorpora una fuente de población más reciente (Censo 2024), actualizar `comunas_poblacion.csv` en `src/data/` y ambos datasets se actualizarán.
