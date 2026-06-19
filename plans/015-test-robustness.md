# Plan 015: Robustez de tests — HTTP mocking, CLI coverage, y assertions fortalecidas

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- tests/test_chile_hub.py tests/test_core.py tests/test_pipeline_logic.py tests/test_extractors.py src/chile_hub/core.py src/chile_hub/data_manager.py src/validation.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: Plan 011 (test de errores de API depende de ChileHubDatasetError)
- **Category**: tests
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

Seis debilidades en la suite de tests que reducen la protección contra
regresiones: (1) dos tests de `check_sources` hacen HTTP real a APIs
gubernamentales — frágiles y causan falsos negativos en CI sin red, (2)
`data_manager.clear()` y `_read_json()` no tienen tests directos — `clear()`
puede destruir el cache del usuario sin detección, (3) 3 comandos CLI
(`source-readiness`, `dataset-quality`, `cache status`) no se ejercitan en tests
de integración, (4) `validate_puntos_interes` (119 líneas, 14 checks) tiene cero
cobertura, (5) ~25 tests en `test_core.py` solo verifican `isinstance(result,
dict)` — inflan cobertura sin proteger regresiones semánticas, y (6) 4
validatores (`finanzas`, `resultados_educacionales`, `siedu`, `perfil`) tienen
solo 1 test cada uno para 6-9 ramas de código.

## Current state

### Archivos relevantes

- `tests/test_chile_hub.py` (1559 líneas) — `ChileHubCliTests`, tests de integración CLI
- `tests/test_core.py` — `ChileHubTests` (requiere `data/normalized/`)
- `tests/test_pipeline_logic.py` (2289 líneas) — `ValidatorTests`
- `tests/test_extractors.py` (1208 líneas) — tests de extractores
- `src/chile_hub/core.py` — `check_sources()` (línea 786), CLI parser (línea 1247)
- `src/chile_hub/data_manager.py` — `clear()` (línea 128), `_read_json()` (línea ~197)
- `src/validation.py` — `validate_puntos_interes()` (línea 641), `validate_finanzas_municipales()` (~L355), `validate_resultados_educacionales()` (~L410), `validate_indicadores_urbanos_siedu()` (~L467), `validate_perfil_territorial_comunal()` (~L527)

### Debilidad 1: HTTP real en tests de check_sources

`tests/test_chile_hub.py:~1306`:
```python
result = self.run_cli("check-sources", "--timeout", "2")
```
`tests/test_core.py:~353`:
```python
result = hub.check_sources(timeout=3)
```
Estos tests llaman a `requests.head()` y `requests.get()` reales contra APIs
gubernamentales chilenas (BCN, INE, MINSAL, MINEDUC, BCCh, etc.). Si hay
problemas de red, rate-limiting, o una API cambia, los tests fallan.

### Debilidad 2: data_manager.clear y _read_json sin tests

`src/chile_hub/data_manager.py:128`:
```python
def clear(self) -> None:
    shutil.rmtree(self.cache_root, ignore_errors=True)
```
`src/chile_hub/data_manager.py:~197`:
```python
def _read_json(self, path: Path) -> dict:
    ...
```
Ninguno tiene test directo. `clear()` es particularmente peligroso.

### Debilidad 3: CLI commands sin cobertura

`ChileHubCliTests` tiene tests para ~20 subcomandos, pero NO para:
- `source-readiness`
- `dataset-quality`
- `cache status`

### Debilidad 4: validate_puntos_interes sin tests

`src/validation.py:641-759` — 119 líneas, 14 verificaciones (columnas requeridas,
osm_id único, bounding box de Chile, categorías válidas, ratio de address null,
formato CUT, integridad referencial, etc.). Cero tests.

### Debilidad 5: Assertions débiles en test_core.py

~25 tests siguen este patrón:
```python
def test_health_returns_dict_with_expected_keys(self):
    result = self.hub.health()
    self.assertIsInstance(result, dict)
    self.assertIn("overall_status", result)
    # Nada más — no verifica valores, solo estructura
```

### Debilidad 6: Validatores con cobertura fina

| Validador | Líneas | Checks | Tests actuales |
|-----------|--------|--------|---------------|
| `validate_finanzas_municipales` | 55 | 9 | 1 (duplicados + negativos) |
| `validate_resultados_educacionales` | 52 | 8 | 1 (porcentajes fuera de rango) |
| `validate_indicadores_urbanos_siedu` | 57 | 7 | 1 (partial coverage warning) |
| `validate_perfil_territorial_comunal` | 30 | 6 | 1 (wrong row count) |

### Convenciones del repo

- Tests con `unittest.TestCase`, métodos `test_*`.
- Mocks con `unittest.mock.patch`.
- Fixtures Polars: se construyen DataFrames inline con `pl.DataFrame({...})`.
- Patrón de test de validador: ver `test_validate_establecimientos_salud_*`
  (5 tests) y `test_validate_indicadores_*` (6 tests) como modelos.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint tests | `.venv/bin/python -m ruff check tests/` | exit 0 |
| All tests | `.venv/bin/python -m pytest tests/ -v` | all pass |
| Specific tests | `.venv/bin/python -m pytest tests/test_pipeline_logic.py::ValidatorTests -v` | all pass |
| CLI tests | `.venv/bin/python -m pytest tests/test_chile_hub.py::ChileHubCliTests -v` | all pass |
| Coverage | `.venv/bin/python -m pytest tests/ --cov=src/chile_hub --cov-report=term-missing` | coverage report |

## Scope

**In scope**:
- `tests/test_chile_hub.py` — mock HTTP en CLI tests, agregar tests de CLI faltantes
- `tests/test_core.py` — mock HTTP en check_sources test, fortalecer assertions
- `tests/test_pipeline_logic.py` — agregar tests para validate_puntos_interes y 4 validatores
- `tests/test_extractors.py` — (opcional) test de data_manager.clear

**Out of scope** (do NOT touch):
- `src/` — no modificar código fuente (solo tests)
- `src/build_dev_db.py` — fuera del scope de cobertura actual
- Agregar `build_dev_db.py` al scope de cobertura — eso es un plan separado (TC-02)

## Git workflow

- Branch: `advisor/015-test-robustness`
- Commits por grupo lógico; mensaje estilo `test: ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Mockear HTTP en tests de check_sources

En `tests/test_core.py`, modificar el test de `check_sources`:

```python
@patch("chile_hub.core.requests.head")
@patch("chile_hub.core.requests.get")
def test_check_sources_returns_list(self, mock_get, mock_head):
    # Simular HEAD exitoso
    mock_head_response = Mock()
    mock_head_response.status_code = 200
    mock_head_response.elapsed = timedelta(milliseconds=150)
    mock_head.return_value = mock_head_response

    result = self.hub.check_sources(timeout=3)
    self.assertIsInstance(result, list)
    self.assertGreater(len(result), 0)
    for entry in result:
        self.assertIn("source", entry)
        self.assertIn("status", entry)
```

En `tests/test_chile_hub.py`, mismo approach para el test CLI:
```python
@patch("chile_hub.core.requests.head")
@patch("chile_hub.core.requests.get")
def test_cli_check_sources(self, mock_get, mock_head):
    ...
```

**Verify**: `.venv/bin/python -m pytest tests/test_core.py::TestCore::test_check_sources_returns_list tests/test_chile_hub.py::ChileHubCliTests::test_cli_check_sources -v`

### Step 2: Agregar tests para data_manager.clear y _read_json

Crear tests en un nuevo archivo o en `tests/test_chile_hub.py`:

```python
def test_cache_clear_removes_directory(self):
    """clear() debe eliminar el directorio de cache."""
    tmpdir = tempfile.mkdtemp()
    try:
        os.environ["CHILE_HUB_CACHE_DIR"] = tmpdir
        manager = ChileHubDataManager(data_version="latest")
        # Crear un archivo dummy en el cache
        dummy = Path(tmpdir) / "test_file.txt"
        dummy.write_text("test")
        self.assertTrue(dummy.exists())

        manager.clear()
        self.assertFalse(dummy.exists())
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        os.environ.pop("CHILE_HUB_CACHE_DIR", None)
```

**Verify**: `.venv/bin/python -m pytest tests/test_chile_hub.py -k "test_cache_clear" -v`

### Step 3: Agregar tests para comandos CLI faltantes

En `ChileHubCliTests`, agregar 3 tests:

```python
def test_cli_source_readiness(self):
    result = self.run_cli("source-readiness")
    data = json.loads(result.stdout)
    self.assertIn("sources", data)

def test_cli_dataset_quality(self):
    result = self.run_cli("dataset-quality")
    data = json.loads(result.stdout)
    self.assertIsInstance(data, dict)

def test_cli_cache_status(self):
    result = self.run_cli("cache", "status")
    # Debe imprimir información del cache
    self.assertTrue(len(result.stdout) > 0)
```

**Verify**: `.venv/bin/python -m pytest tests/test_chile_hub.py::ChileHubCliTests -k "test_cli_source_readiness or test_cli_dataset_quality or test_cli_cache_status" -v`

### Step 4: Agregar tests para validate_puntos_interes

En `tests/test_pipeline_logic.py::ValidatorTests`, agregar una batería de tests:

```python
def test_validate_puntos_interes_ok(self):
    """Happy path: DataFrame válido con 100 puntos en Santiago."""
    df = pl.DataFrame({
        "osm_id": ["node/1", "node/2", "node/3"],
        "categoria": ["cajero_automatico", "cajero_automatico", "farmacia"],
        "nombre": ["ATM 1", "ATM 2", "Farm 1"],
        "direccion": ["Calle 1", "Calle 2", "Calle 3"],
        "latitud": [-33.45, -33.46, -33.47],
        "longitud": [-70.65, -70.66, -70.67],
        "codigo_region": ["13", "13", "13"],
        "codigo_provincia": ["131", "131", "131"],
        "codigo_comuna": ["13101", "13101", "13101"],
    })
    result = validate_puntos_interes(df, {"source_mode": "live"})
    self.assertEqual(result["status"], "ok")

def test_validate_puntos_interes_empty(self):
    ...

def test_validate_puntos_interes_osm_id_duplicates(self):
    ...

def test_validate_puntos_interes_out_of_bounds_coords(self):
    ...

def test_validate_puntos_interes_invalid_categoria(self):
    ...

def test_validate_puntos_interes_high_null_address(self):
    ...

def test_validate_puntos_interes_invalid_cut_length(self):
    ...
```

IMPORTANTE: `validate_puntos_interes` debe estar importada en el archivo de tests.
Verificar que el import existe; si no, agregarlo:
```python
from src.validation import validate_puntos_interes
```

**Verify**: `.venv/bin/python -m pytest tests/test_pipeline_logic.py -k "validate_puntos_interes" -v`
→ Al menos 6 tests nuevos pasan.

### Step 5: Fortalecer assertions en test_core.py

Revisar los ~25 tests que solo verifican `isinstance(result, dict)` y agregar
2-3 verificaciones semánticas adicionales por test. Ejemplo:

```python
# Antes:
def test_health_returns_dict_with_expected_keys(self):
    result = self.hub.health()
    self.assertIsInstance(result, dict)
    self.assertIn("overall_status", result)

# Después:
def test_health_returns_dict_with_expected_keys(self):
    result = self.hub.health()
    self.assertIsInstance(result, dict)
    self.assertIn("overall_status", result)
    self.assertIn(result["overall_status"], {"ok", "warn", "error"})
    self.assertIn("datasets", result)
    self.assertIsInstance(result["datasets"], dict)
```

Aplicar a: `test_health`, `test_redistribution`, `test_source_readiness`,
`test_dataset_quality`, `test_bundle`, `test_status`, `test_provenance`,
`test_drift`, `test_freshness_audit`, `test_runtime_status_audit`,
`test_top_issue`, `test_overview`, y otros con assertions débiles.

**Verify**: `.venv/bin/python -m pytest tests/test_core.py -v` → todos pasan
(incluyendo los tests fortalecidos).

### Step 6: Agregar edge cases para 4 validatores

En `tests/test_pipeline_logic.py::ValidatorTests`, agregar tests para cubrir
ramas no probadas:

**validate_finanzas_municipales** (4 tests nuevos):
```python
def test_validate_finanzas_municipales_ok(self): ...
def test_validate_finanzas_municipales_empty(self): ...
def test_validate_finanzas_municipales_missing_columns(self): ...
def test_validate_finanzas_municipales_unknown_communes(self): ...
```

**validate_resultados_educacionales** (4 tests nuevos):
```python
def test_validate_resultados_educacionales_ok(self): ...
def test_validate_resultados_educacionales_empty(self): ...
def test_validate_resultados_educacionales_missing_columns(self): ...
def test_validate_resultados_educacionales_duplicates(self): ...
```

**validate_indicadores_urbanos_siedu** (4 tests nuevos):
```python
def test_validate_indicadores_urbanos_siedu_ok(self): ...
def test_validate_indicadores_urbanos_siedu_empty(self): ...
def test_validate_indicadores_urbanos_siedu_invalid_cut(self): ...
def test_validate_indicadores_urbanos_siedu_missing_columns(self): ...
```

**validate_perfil_territorial_comunal** (3 tests nuevos):
```python
def test_validate_perfil_territorial_comunal_ok(self): ...
def test_validate_perfil_territorial_comunal_invalid_cut_length(self): ...
def test_validate_perfil_territorial_comunal_unknown_communes(self): ...
```

IMPORTANTE: Seguir el patrón de los validatores existentes bien cubiertos.
Usar `pl.DataFrame({...})` con datos sintéticos mínimos que activen cada rama.
Para los tests "ok", construir un DataFrame con la forma exacta que el validador
espera.

**Verify**: `.venv/bin/python -m pytest tests/test_pipeline_logic.py::ValidatorTests -v`
→ Al menos 15 tests nuevos pasan.

### Step 7: Lint y coverage final

```
.venv/bin/python -m ruff check tests/
.venv/bin/python -m ruff format --check tests/
.venv/bin/python -m pytest tests/ -v
.venv/bin/python -m pytest tests/ --cov=src/chile_hub --cov=src/validation --cov-report=term-missing
```

## Done criteria

- [ ] `.venv/bin/python -m ruff check tests/` exit 0
- [ ] `.venv/bin/python -m ruff format --check tests/` exit 0
- [ ] `.venv/bin/python -m pytest tests/ -v` all pass
- [ ] `grep -rn "requests.head\|requests.get" tests/` NO muestra llamadas sin mock (todos los HTTP deben estar mockeados excepto en tests de integración explícitamente marcados)
- [ ] Tests para `validate_puntos_interes` existen y cubren ≥6 ramas
- [ ] Tests para `source-readiness`, `dataset-quality`, `cache status` CLI existen
- [ ] `test_core.py` tiene ≥15 tests con assertions semánticas (no solo `isinstance`)
- [ ] 4 validatores finos tienen ≥3 tests cada uno (al menos: ok, empty, un error path)
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts.
- `validate_puntos_interes` no está definida en `src/validation.py` (fue removida
  o renombrada desde que se escribió este plan).
- Los mocks de `requests.head`/`requests.get` en `check_sources` no son efectivos
  porque la función usa `curl_cffi` en lugar de `requests` en algún camino.
- El test `test_cache_clear_removes_directory` falla porque `clear()` con la
  validación de seguridad del Plan 011 rechaza el directorio temporal.
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- Al agregar nuevos comandos CLI, agregar inmediatamente un test de integración
  en `ChileHubCliTests`.
- Al agregar nuevas funciones `validate_*`, seguir el patrón de ≥5 tests: ok,
  empty, missing columns, duplicates, y al menos un error path específico.
- Los tests de `check_sources` ahora usan mocks — si la firma de
  `requests.head()` cambia en una versión futura, actualizar los mocks.
- Si `validate_puntos_interes` se mueve a un módulo separado en el futuro,
  mover también sus tests.
