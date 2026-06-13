# Plan 005: Agregar tests para invariantes de códigos CUT y funciones validate_*

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- src/build_dev_db.py tests/test_chile_hub.py`
> Si alguno de estos archivos cambió, compara los excerpts de "Estado actual" con el código real antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: S
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: tests
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

El proyecto declara en `AGENTS.md §4.1` que los códigos CUT deben preservarse como strings con ceros iniciales (`"01101"`, no `1101`). Sin embargo, ningún test verifica que el tipo de dato sea `pl.String` ni que los valores tengan la longitud fija esperada. Un refactor accidental (ej. cambiar `schema_overrides` en `build_dev_db.py:1253`) silenciosamente corrompería todos los joins downstream sin que ningún test fallara.

Además, las funciones `validate_regiones()`, `validate_provincias()`, y `validate_comunas()` de `src/build_dev_db.py` son la última línea de defensa antes de publicar datos. Actualmente solo se importa `validate_indicadores` en los tests. Las otras tres no tienen cobertura.

## Estado actual

### Funciones a testear en `src/build_dev_db.py`

```python
# build_dev_db.py:373-400
def validate_comunas(df_comunas, metadata):
    errors = []
    row_count = df_comunas.height
    duplicate_count = row_count - df_comunas["codigo_comuna"].n_unique()
    if duplicate_count > 0:
        errors.append(f"codigo_comuna must be unique, found {duplicate_count} duplicate rows")
    if metadata and metadata.get("source_mode") == "live" and row_count < EXPECTED_LIVE_COMUNAS_COUNT:
        errors.append(...)
    if metadata and metadata.get("source_mode") == "fallback":
        ...
    return {"dataset": "comunas", "status": "error" if errors else "ok", ...}

# build_dev_db.py:402-415
def validate_regiones(df_regiones):
    errors = []
    if df_regiones.height == 0:
        errors.append("regiones dataset is empty")
    duplicate_count = df_regiones.height - df_regiones["codigo_region"].n_unique()
    if duplicate_count > 0:
        errors.append(...)
    return {"dataset": "regiones", "status": "error" if errors else "ok", ...}

# build_dev_db.py:417-432
def validate_provincias(df_provincias):
    ...
    # verifica unicidad de (codigo_region, codigo_provincia)
```

Constantes relevantes:

```python
# build_dev_db.py:27-29
FALLBACK_COMUNAS_COUNT = 18
EXPECTED_LIVE_COMUNAS_COUNT = 346
```

### Cómo `build_dev_db.py` carga los DataFrames (patrón a verificar)

```python
# build_dev_db.py:1253-1264 (aprox) — schema_overrides preserva leading zeros
df_comunas = pl.read_csv(
    COMUNAS_CSV_PATH,
    schema_overrides={
        "codigo_comuna": pl.String,
        "codigo_provincia": pl.String,
        "codigo_region": pl.String,
    },
)
```

### Patrón de test existente en `tests/test_chile_hub.py`

Los tests actuales leen de `data/normalized/`. Para las funciones `validate_*` necesitamos tests unitarios que construyan DataFrames de Polars en memoria (no de disco). Patrón de los tests existentes de pipeline logic:

```python
# tests/test_pipeline_logic.py:20-67 — patrón de test con tempdir y datos en memoria
class PipelineLogicTests(unittest.TestCase):
    def test_clean_publishable_removes_only_manifest_declared_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ...
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr suite completa | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Correr solo el nuevo test | `.venv/bin/python -m unittest tests.test_pipeline_logic.ValidatorTests -v` | todos pasan |
| Correr solo test de hub | `.venv/bin/python -m unittest tests.test_chile_hub.ChileHubTests.test_load_polars -v` | pasa |

## Alcance

**En scope**:
- `tests/test_pipeline_logic.py` — agregar la nueva clase `ValidatorTests` y la clase `CUTInvariantTests`

**Fuera de scope**:
- `tests/test_chile_hub.py` — no modificar los tests existentes de integración
- `src/build_dev_db.py` — no modificar las funciones `validate_*`

## Git workflow

- Rama: `advisor/005-tests-invariantes-y-validadores`
- Estilo de commit: `test: agregar tests para invariantes CUT y funciones validate_*`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar imports necesarios en `test_pipeline_logic.py`

Al inicio del archivo, después de los imports existentes, agregar:

```python
import polars as pl
from src.build_dev_db import (
    validate_comunas,
    validate_regiones,
    validate_provincias,
    validate_indicadores,
    EXPECTED_LIVE_COMUNAS_COUNT,
    FALLBACK_COMUNAS_COUNT,
    EXPECTED_INDICATOR_CODES,
)
```

**Verificar**: `python3 -c "from src.build_dev_db import validate_comunas, validate_regiones, validate_provincias; print('OK')"` imprime `OK`.

### Paso 2: Agregar la clase `ValidatorTests`

Agregar la siguiente clase al final de `test_pipeline_logic.py`:

```python
class ValidatorTests(unittest.TestCase):
    """Tests para las funciones validate_* de build_dev_db.py."""

    # ── validate_regiones ──────────────────────────────────────────────────

    def test_validate_regiones_ok_with_valid_data(self):
        df = pl.DataFrame({
            "codigo_region": ["01", "02", "03"],
            "nombre_region": ["Tarapacá", "Antofagasta", "Atacama"],
        })
        result = validate_regiones(df)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["errors"], [])

    def test_validate_regiones_error_when_empty(self):
        df = pl.DataFrame({"codigo_region": pl.Series([], dtype=pl.String), "nombre_region": pl.Series([], dtype=pl.String)})
        result = validate_regiones(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_regiones_error_on_duplicate_codigo(self):
        df = pl.DataFrame({
            "codigo_region": ["01", "01"],
            "nombre_region": ["Tarapacá", "Tarapacá-dup"],
        })
        result = validate_regiones(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))

    # ── validate_provincias ────────────────────────────────────────────────

    def test_validate_provincias_ok_with_valid_data(self):
        df = pl.DataFrame({
            "codigo_region": ["01", "01", "02"],
            "codigo_provincia": ["011", "012", "021"],
            "nombre_provincia": ["Iquique", "Tamarugal", "Antofagasta"],
        })
        result = validate_provincias(df)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_validate_provincias_error_when_empty(self):
        df = pl.DataFrame({
            "codigo_region": pl.Series([], dtype=pl.String),
            "codigo_provincia": pl.Series([], dtype=pl.String),
            "nombre_provincia": pl.Series([], dtype=pl.String),
        })
        result = validate_provincias(df)
        self.assertEqual(result["status"], "error")

    def test_validate_provincias_error_on_duplicate_key(self):
        df = pl.DataFrame({
            "codigo_region": ["01", "01"],
            "codigo_provincia": ["011", "011"],
            "nombre_provincia": ["Iquique", "Iquique-dup"],
        })
        result = validate_provincias(df)
        self.assertEqual(result["status"], "error")

    # ── validate_comunas ───────────────────────────────────────────────────

    def test_validate_comunas_ok_live_with_sufficient_rows(self):
        # Construir un DataFrame con EXPECTED_LIVE_COMUNAS_COUNT filas únicas
        codes = [str(i).zfill(5) for i in range(1, EXPECTED_LIVE_COMUNAS_COUNT + 1)]
        df = pl.DataFrame({"codigo_comuna": codes})
        metadata = {"source_mode": "live"}
        result = validate_comunas(df, metadata)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_validate_comunas_error_live_with_insufficient_rows(self):
        df = pl.DataFrame({"codigo_comuna": ["01101", "01102"]})
        metadata = {"source_mode": "live"}
        result = validate_comunas(df, metadata)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("incomplete" in e for e in result["errors"]))

    def test_validate_comunas_error_on_duplicates(self):
        df = pl.DataFrame({"codigo_comuna": ["01101", "01101"]})
        metadata = {"source_mode": "live"}
        result = validate_comunas(df, metadata)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))

    def test_validate_comunas_fallback_warning(self):
        codes = [str(i).zfill(5) for i in range(1, FALLBACK_COMUNAS_COUNT + 1)]
        df = pl.DataFrame({"codigo_comuna": codes})
        metadata = {"source_mode": "fallback"}
        result = validate_comunas(df, metadata)
        # fallback debe producir warnings pero no errors de duplicados
        self.assertEqual(result["status"], "ok")
        self.assertTrue(len(result["warnings"]) > 0)
        self.assertTrue(any("fallback" in w for w in result["warnings"]))
```

**Verificar**: `.venv/bin/python -m unittest tests.test_pipeline_logic.ValidatorTests -v` — todos pasan.

### Paso 3: Agregar la clase `CUTInvariantTests`

Agregar después de `ValidatorTests`:

```python
class CUTInvariantTests(unittest.TestCase):
    """Verifica que los códigos CUT en data/normalized/ sean pl.String con longitud fija."""

    @classmethod
    def setUpClass(cls):
        cls.normalized_dir = ROOT_DIR / "data" / "normalized"

    def _load_parquet(self, name):
        path = self.normalized_dir / f"{name}.parquet"
        if not path.exists():
            self.skipTest(f"{name}.parquet no existe — correr make build primero")
        return pl.read_parquet(path)

    def test_comunas_codigo_comuna_is_string_type(self):
        df = self._load_parquet("comunas")
        self.assertEqual(df["codigo_comuna"].dtype, pl.String)

    def test_comunas_codigo_comuna_has_length_5(self):
        df = self._load_parquet("comunas")
        lengths = df["codigo_comuna"].str.len_chars()
        self.assertTrue((lengths == 5).all(),
            f"Hay códigos de comuna con longitud != 5: {df.filter(lengths != 5)['codigo_comuna'].to_list()[:5]}")

    def test_comunas_codigo_region_is_string_type(self):
        df = self._load_parquet("comunas")
        self.assertEqual(df["codigo_region"].dtype, pl.String)

    def test_comunas_codigo_region_has_length_2(self):
        df = self._load_parquet("comunas")
        lengths = df["codigo_region"].str.len_chars()
        self.assertTrue((lengths == 2).all())

    def test_comunas_codigo_provincia_has_length_3(self):
        df = self._load_parquet("comunas")
        lengths = df["codigo_provincia"].str.len_chars()
        self.assertTrue((lengths == 3).all())

    def test_comunas_leading_zeros_preserved(self):
        """Verifica que al menos una región empiece con '0' (Tarapacá = '01')."""
        df = self._load_parquet("comunas")
        has_leading_zero = df["codigo_region"].str.starts_with("0").any()
        self.assertTrue(has_leading_zero,
            "Ninguna región empieza con '0' — los ceros iniciales podrían haberse perdido")

    def test_regiones_codigo_region_is_string_type(self):
        df = self._load_parquet("regiones")
        self.assertEqual(df["codigo_region"].dtype, pl.String)

    def test_provincias_codigo_provincia_has_length_3(self):
        df = self._load_parquet("provincias")
        lengths = df["codigo_provincia"].str.len_chars()
        self.assertTrue((lengths == 3).all())
```

**Verificar**: `.venv/bin/python -m unittest tests.test_pipeline_logic.CUTInvariantTests -v` — todos pasan (o se skipean si no hay data).

### Paso 4: Correr la suite completa

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos los tests pasan, incluyendo los nuevos de `ValidatorTests` y `CUTInvariantTests`. El número total de tests sube respecto al baseline.

## Criterios de done

- [ ] `grep -n "class ValidatorTests\|class CUTInvariantTests" tests/test_pipeline_logic.py` retorna ambas clases
- [ ] `.venv/bin/python -m unittest tests.test_pipeline_logic.ValidatorTests -v` — todos pasan
- [ ] `.venv/bin/python -m unittest tests.test_pipeline_logic.CUTInvariantTests -v` — todos pasan (o skipean si sin data)
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan, sin regresiones
- [ ] Solo `tests/test_pipeline_logic.py` modificado
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si las funciones `validate_*` en `build_dev_db.py` tienen firmas distintas a los excerpts (el código drifteó) — reportar y no continuar.
- Si `EXPECTED_LIVE_COMUNAS_COUNT` o `FALLBACK_COMUNAS_COUNT` no son exportables (nombres diferentes) — reportar.

## Notas de mantenimiento

- Si el número esperado de comunas cambia (nueva división administrativa en Chile), actualizar `EXPECTED_LIVE_COMUNAS_COUNT` en `build_dev_db.py` y el test `test_comunas_codigo_comuna_has_length_5` si los códigos cambian de longitud.
- Los tests `CUTInvariantTests` son tests de integración — requieren que `make build` haya corrido. Si se quieren en CI, asegurarse de que el paso de tests ocurra después del build.
