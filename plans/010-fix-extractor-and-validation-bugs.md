# Plan 010: Corregir bugs en extractores y validación

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- src/extractors/censo_hogares_viviendas_extractor.py src/extractors/censo_extractor.py src/extractors/salud_extractor.py src/validation.py`
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

Cinco bugs reales en extractores y validación que causan fallos silenciosos o
crash del pipeline: (1) `TypeError` al hacer `float(None)` cuando una celda Excel
está vacía, (2) fuga de file handles de openpyxl que agota descriptores en CI,
(3) `validate_censo_hogares_viviendas` reporta falsos errores con códigos de
comuna nulos porque omite `.drop_nulls()`, (4) `except Exception` en tres
extractores traga `KeyboardInterrupt` y `SystemExit`, y (5) respuestas HTTP sin
cerrar en 8 extractores que agotan conexiones y puertos efímeros.

## Current state

### Archivos relevantes

- `src/extractors/censo_hogares_viviendas_extractor.py` — extractor de censo hogares; bug de None y fuga openpyxl (líneas 75, 87, 112)
- `src/extractors/censo_extractor.py` — extractor de censo comunal; fuga openpyxl y bare except (líneas 69, 73, 81)
- `src/extractors/salud_extractor.py` — extractor de establecimientos de salud; bare except y HTTP leaks (líneas 47, 51, 57)
- `src/validation.py` — validadores; omisión de `.drop_nulls()` (línea 184)
- `src/extractors/res_extractor.py` — extractor RES; HTTP leaks en loop (líneas 107, 124)
- `src/extractors/subdere_extractor.py` — extractor DPA; HTTP leak (línea ~456)
- `src/extractors/bcentral_extractor.py` — extractor indicadores; HTTP leak (línea ~132)
- `src/extractors/mineduc_establecimientos_extractor.py` — extractor MINEDUC; HTTP leak (línea 59)
- `src/extractors/source_adapter.py` — helper HTTP; HTTP leak (línea 42)

### Bug 1: TypeError con celda vacía (None)

`src/extractors/censo_hogares_viviendas_extractor.py:112`:
```python
"promedio_personas_hogar": None if row[7] == "-" else float(row[7]),
```
Cuando `openpyxl` con `data_only=True` encuentra una celda vacía, retorna
`None`. `None == "-"` es `False`, así que se ejecuta `float(None)` →
`TypeError`. El guard `if not row[4]` no protege el índice 7.

### Bug 2: Workbooks openpyxl sin cerrar

`src/extractors/censo_extractor.py:81`:
```python
workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
```
`src/extractors/censo_hogares_viviendas_extractor.py:87`:
```python
workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
```
En modo `read_only`, el workbook mantiene un file handle abierto que solo se
libera al hacer garbage collection. En CI o ejecuciones repetidas, esto agota
los descriptores de archivo del sistema.

### Bug 3: drop_nulls() omitido

`src/validation.py:184`:
```python
unknown = set(df["codigo_comuna"].to_list()) - set(valid_commune_codes)
```
Todos los demás validadores que usan este patrón incluyen `.drop_nulls()`:
- `validate_establecimientos_salud` (línea 159): `.drop_nulls().to_list()`
- `validate_establecimientos_educacionales` (línea 218): `.drop_nulls().to_list()`
- `validate_distritos_electorales` (línea 296): `.drop_nulls().to_list()`

### Bug 4: except Exception traga señales

Tres extractores usan `except Exception:` que captura `KeyboardInterrupt` y
`SystemExit`:
- `censo_extractor.py:73`
- `censo_hogares_viviendas_extractor.py:79`
- `salud_extractor.py:57`

### Bug 5: Respuestas HTTP sin cerrar

Ocho extractores llaman `requests.get(url)` sin context manager, dejando la
conexión TCP en el pool sin liberar hasta garbage collection:
- `censo_extractor.py:69`
- `censo_hogares_viviendas_extractor.py:75`
- `salud_extractor.py:47,51`
- `res_extractor.py:107,124`
- `mineduc_establecimientos_extractor.py:59`
- `subdere_extractor.py:456`
- `bcentral_extractor.py:132`
- `source_adapter.py:42`

### Convenciones del repo

- Paths relativos a `__file__`, snake_case en español para columnas.
- Formato: Ruff (doble comilla, line-length=100), lint: `ruff check`.
- Tests: `pytest -v`, archivos `test_*.py`, clases `*Tests`.
- Commits: conventional commits (`feat:`, `fix:`, `test:`).
- Ver el patrón correcto de HTTP en `data_manager.py:169`: `with self.session.get(...) as response:`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint | `.venv/bin/python -m ruff check src/extractors/ src/validation.py` | exit 0 |
| Extract | `.venv/bin/python src/extractors/censo_hogares_viviendas_extractor.py` | exit 0 |
| Extract | `.venv/bin/python src/extractors/censo_extractor.py` | exit 0 |
| Extract | `.venv/bin/python src/extractors/salud_extractor.py` | exit 0 |
| Tests | `.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -v` | all pass |
| Full build | `make build` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `src/extractors/censo_hogares_viviendas_extractor.py`
- `src/extractors/censo_extractor.py`
- `src/extractors/salud_extractor.py`
- `src/extractors/res_extractor.py`
- `src/extractors/subdere_extractor.py`
- `src/extractors/bcentral_extractor.py`
- `src/extractors/mineduc_establecimientos_extractor.py`
- `src/extractors/source_adapter.py`
- `src/validation.py`

**Out of scope** (do NOT touch):
- `src/extractors/electoral_extractor.py` — no tiene estos bugs
- `src/extractors/sinim_finanzas_extractor.py` — no tiene estos bugs
- `src/extractors/mineduc_resultados_extractor.py` — no tiene estos bugs
- `src/extractors/siedu_extractor.py` — no tiene estos bugs
- `src/build_dev_db.py` — no modificar el pipeline principal
- `src/chile_hub/` — no modificar la API pública

## Git workflow

- Branch: `advisor/010-extractor-validation-bugs`
- Commit por step; mensaje estilo conventional commits como `fix(extractors): ...`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Corregir TypeError con None en censo_hogares_viviendas_extractor

En `src/extractors/censo_hogares_viviendas_extractor.py:112`, cambiar:
```python
"promedio_personas_hogar": None if row[7] == "-" else float(row[7]),
```
Por:
```python
"promedio_personas_hogar": None if row[7] in ("-", None) else float(row[7]),
```
Y agregar un guard de longitud de tupla antes del acceso `row[7]`:
```python
if len(row) < 8:
    continue
```

**Verify**: `make extract` — el extractor de censo hogares debe completar sin TypeError.

### Step 2: Usar context manager en openpyxl

En `src/extractors/censo_extractor.py:81`, cambiar:
```python
workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
totals = {}
for row in workbook["2"].iter_rows(min_row=6, values_only=True):
    ...
```
Por:
```python
with openpyxl.load_workbook(path, read_only=True, data_only=True) as workbook:
    totals = {}
    for row in workbook["2"].iter_rows(min_row=6, values_only=True):
        ...
```
Ajustar la indentación del resto del bloque y el `return` final dentro del `with`.

El mismo cambio en `src/extractors/censo_hogares_viviendas_extractor.py:87`:
```python
with openpyxl.load_workbook(path, read_only=True, data_only=True) as workbook:
    records = {}
    for row in workbook["6"].iter_rows(min_row=5, values_only=True):
        ...
```

**Verify**: Ejecutar ambos extractores:
```
.venv/bin/python src/extractors/censo_extractor.py
.venv/bin/python src/extractors/censo_hogares_viviendas_extractor.py
```
Ambos deben completar sin error.

### Step 3: Agregar .drop_nulls() en validate_censo_hogares_viviendas

En `src/validation.py:184`, cambiar:
```python
unknown = set(df["codigo_comuna"].to_list()) - set(valid_commune_codes)
```
Por:
```python
unknown = set(df["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
```

**Verify**: Ejecutar los tests de validación:
```
.venv/bin/python -m pytest tests/test_pipeline_logic.py::ValidatorTests -v -k "censo_hogares"
```

### Step 4: Narrow exceptions en extractores

En tres archivos, cambiar `except Exception:` por `except (requests.RequestException, OSError):`

`src/extractors/censo_extractor.py:73`:
```python
except Exception:
```
→
```python
except (requests.RequestException, OSError):
```

`src/extractors/censo_hogares_viviendas_extractor.py:79`:
```python
except Exception:
```
→
```python
except (requests.RequestException, OSError):
```

`src/extractors/salud_extractor.py:57`:
```python
except Exception:
```
→
```python
except (requests.RequestException, OSError):
```

**Verify**: Ejecutar tests de extractores:
```
.venv/bin/python -m pytest tests/test_extractors.py -v
```

### Step 5: Cerrar respuestas HTTP con context manager

Envolver cada `requests.get(url)` con `with` en los 8 extractores:

**Patrón a seguir** (ejemplo para `salud_extractor.py:47,51`):
```python
# Antes:
package = requests.get(PACKAGE_API_URL, timeout=30)
...
response = requests.get(resource["url"], timeout=60)

# Después:
with requests.get(PACKAGE_API_URL, timeout=30) as package:
    package.raise_for_status()
    payload = package.json()["result"]
    ...
with requests.get(resource["url"], timeout=60) as response:
    response.raise_for_status()
    ...
```

Aplicar el mismo patrón en:
- `censo_extractor.py:69`
- `censo_hogares_viviendas_extractor.py:75`
- `res_extractor.py:107` y `:124`
- `mineduc_establecimientos_extractor.py:59`
- `subdere_extractor.py:456`
- `bcentral_extractor.py:132`
- `source_adapter.py:42`

**IMPORTANTE**: Al usar `with`, el cuerpo del bloque debe estar indentado. Si hay
lógica después que depende de `response.content` o `response.json()`, esa lógica
debe estar dentro del `with` o debes extraer los datos a variables antes de salir.

**Verify**: Ejecutar el extract más ligero:
```
.venv/bin/python src/extractors/bcentral_extractor.py
.venv/bin/python src/extractors/salud_extractor.py
```
Ambos deben completar sin error.

### Step 6: Lint y tests completos

```
.venv/bin/python -m ruff check src/extractors/ src/validation.py
.venv/bin/python -m ruff format --check src/extractors/ src/validation.py
.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -v
```

## Test plan

- **Validator test para drop_nulls**: Agregar a `tests/test_pipeline_logic.py::ValidatorTests`
  un test que construye un DataFrame con un `codigo_comuna` nulo y verifica que
  `validate_censo_hogares_viviendas` no reporta la comuna nula como desconocida.
  Seguir el patrón de `test_validate_censo_hogares_viviendas_*` existente.

- **Verificación**: `.venv/bin/python -m pytest tests/test_pipeline_logic.py::ValidatorTests -v`
  → todos los tests existentes más el nuevo pasan.

## Done criteria

- [ ] `.venv/bin/python -m ruff check src/extractors/ src/validation.py` exit 0
- [ ] `.venv/bin/python -m ruff format --check src/extractors/ src/validation.py` exit 0
- [ ] `.venv/bin/python -m pytest tests/test_extractors.py tests/test_pipeline_logic.py -v` all pass
- [ ] `make extract` completa sin errores (todos los extractores)
- [ ] `make build` completa sin errores
- [ ] `grep -rn "except Exception:" src/extractors/censo_extractor.py src/extractors/censo_hogares_viviendas_extractor.py src/extractors/salud_extractor.py` retorna 0 matches
- [ ] `grep -rn "= openpyxl.load_workbook" src/extractors/censo_extractor.py` muestra `with openpyxl.load_workbook` (no asignación sin with)
- [ ] `grep -rn "\.to_list()) - set" src/validation.py` muestra que la línea 184 tiene `.drop_nulls().to_list()`
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions

Stop and report back (do not improvise) if:

- El código en las ubicaciones de "Current state" no coincide con los excerpts
  (el código ha cambiado desde que se escribió este plan).
- `make extract` falla para un extractor no modificado (fallo preexistente).
- Un `with requests.get(...)` rompe el flujo de un extractor porque hay lógica
  que usa `response` fuera del bloque y no se puede extraer a variable.
- El test de `validate_censo_hogares_viviendas` con nulls requiere cambios en
  el fixture que están fuera del scope.
- Algún paso de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- Si se agregan nuevos extractores, deben seguir el patrón `with requests.get(...)`
  y usar `except (requests.RequestException, OSError)` en lugar de `except Exception`.
- Si INE cambia el formato de sus Excel y las columnas se mueven, el guard
  `len(row) < 8` en `censo_hogares_viviendas_extractor.py` protegerá contra
  accesos fuera de rango.
- La validación `validate_censo_hogares_viviendas` ahora es consistente con las
  demás en el manejo de nulls; si se extrae una función helper para el patrón
  `set(df["codigo_comuna"].drop_nulls().to_list())`, aplicarla aquí también.
