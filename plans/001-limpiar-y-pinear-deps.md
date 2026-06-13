# Plan 001: Limpiar dependencias no usadas y pinear versiones exactas

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar. Si algo en la sección "Condiciones de STOP" ocurre, detente y reporta — no improvises.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- requirements.txt`
> Si `requirements.txt` cambió desde que se escribió este plan, compara el estado actual con los excerpts de "Estado actual" antes de continuar. Si difiere, es condición de STOP.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: S
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: deps
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

`requirements.txt` incluye dos dependencias que no se usan en ningún archivo fuente (`pandera`, `openpyxl`) y una que es opcional con fallback graceful ya implementado (`curl_cffi`). Además, todas las versiones usan `>=` sin cota superior, lo que contradice explícitamente `AGENTS.md §10` ("Las versiones flotantes pueden romper el pipeline silenciosamente en CI"). Cada CI run puede instalar versiones distintas, haciendo los bugs no reproducibles. Este plan limpia el dead weight y fija versiones exactas contra el entorno local probado.

## Estado actual

Archivo relevante: `requirements.txt` (raíz del repo)

```
polars>=0.20.0
duckdb>=0.10.0
requests>=2.31.0
curl_cffi>=0.7.0
pandas>=2.1.0
pyarrow>=14.0.0
xlsxwriter>=3.1.0
openpyxl>=3.1.0
pandera>=0.18.0
playwright>=1.58.0
```

**Evidencia de dependencias no usadas:**
- `pandera`: cero ocurrencias de `import pandera` o `from pandera` en `src/`, `scripts/`, `tests/`
- `openpyxl`: cero ocurrencias de `import openpyxl` en fuentes; `build_dev_db.py` usa `engine="xlsxwriter"` explícitamente en todas sus llamadas a `pd.ExcelWriter`
- `curl_cffi`: usada únicamente en `src/extractors/subdere_extractor.py:10` como import opcional con fallback ya implementado:

```python
# src/extractors/subdere_extractor.py:10-13
try:
    from curl_cffi import requests as _cffi_requests
    _CFFI_AVAILABLE = True
except ImportError:
    _CFFI_AVAILABLE = False
```

`bcentral_extractor.py` no la importa. El patrón `ImportError` ya está — curl_cffi puede salir de requirements sin romper nada.

**Versiones instaladas actualmente** (obtenidas del `.venv` local):

```
polars==1.X.X   # verificar con: .venv/bin/pip show polars
duckdb==X.X.X
requests==X.X.X
pandas==X.X.X
pyarrow==X.X.X
xlsxwriter==X.X.X
playwright==X.X.X
```

La convención del repo es `snake_case` en español para nombres; no aplica a este archivo. Mantener el orden actual.

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Ver versiones instaladas | `.venv/bin/pip freeze` | lista de `paquete==versión` |
| Verificar ausencia de imports | `grep -r "import pandera\|import openpyxl\|from pandera\|from openpyxl" src/ scripts/ tests/` | sin output |
| Instalar desde requirements | `.venv/bin/pip install -r requirements.txt` | exit 0 |
| Correr tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Correr pipeline | `make build` | exit 0 |

## Alcance

**En scope** (únicos archivos a modificar):
- `requirements.txt`

**Fuera de scope** (no tocar):
- `src/extractors/subdere_extractor.py` — el bloque `try/except ImportError` ya está correcto
- Cualquier otro archivo fuente

## Git workflow

- Rama: `advisor/001-limpiar-y-pinear-deps`
- Estilo de commit: `feat: limpiar dependencias no usadas y pinear versiones exactas`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Obtener versiones exactas instaladas

Ejecutar:

```bash
.venv/bin/pip show polars duckdb requests pandas pyarrow xlsxwriter playwright | grep -E "^Name:|^Version:"
```

Anotar las versiones. También ejecutar:

```bash
.venv/bin/pip freeze | grep -E "^(polars|duckdb|requests|pandas|pyarrow|XlsxWriter|playwright)=="
```

**Verificar**: El output incluye versiones fijas sin `>=`.

### Paso 2: Escribir el nuevo `requirements.txt`

Reemplazar el contenido completo de `requirements.txt` con las versiones exactas obtenidas en el paso 1 para las 7 dependencias que quedan (eliminando `openpyxl`, `pandera`, `curl_cffi`). El archivo resultante debe tener exactamente 7 líneas, cada una con `paquete==X.Y.Z`. Ejemplo de formato (reemplazar con versiones reales del paso 1):

```
polars==1.41.2
duckdb==1.3.0
requests==2.32.3
pandas==3.0.3
pyarrow==24.0.0
xlsxwriter==3.2.5
playwright==1.52.0
```

**Verificar**: `wc -l requirements.txt` devuelve 7. `grep ">=" requirements.txt` devuelve vacío.

### Paso 3: Verificar ausencia de imports de deps eliminadas

```bash
grep -rn "import pandera\|from pandera\|import openpyxl\|from openpyxl" src/ scripts/ tests/
```

**Verificar**: sin output (exit 0, cero líneas).

### Paso 4: Reinstalar desde el nuevo requirements.txt

```bash
.venv/bin/pip install -r requirements.txt
```

**Verificar**: exit 0, sin errores de resolución.

### Paso 5: Correr el build completo

```bash
make build
```

**Verificar**: exit 0. `data/normalized/dataset_catalog.json` existe y tiene fecha reciente.

### Paso 6: Correr los tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, ninguno falla.

## Plan de tests

No se escriben nuevos tests en este plan. Los tests existentes son la verificación de regresión.

## Criterios de done

- [ ] `requirements.txt` tiene exactamente 7 líneas, todas con `==`
- [ ] `grep ">=" requirements.txt` devuelve vacío
- [ ] `grep -r "import pandera\|import openpyxl" src/ scripts/ tests/` devuelve vacío
- [ ] `make build` sale con exit 0
- [ ] `.venv/bin/python -m unittest discover -s tests` sale con exit 0, todos pasan
- [ ] Solo `requirements.txt` modificado (`git status` confirma)
- [ ] `plans/README.md` fila de estado actualizada a DONE

## Condiciones de STOP

- Si `grep -r "import pandera" src/` encuentra matches — la dependencia sí se usa, abortar y reportar.
- Si `grep -r "import openpyxl" src/` encuentra matches — ídem.
- Si `make build` falla después de actualizar requirements.txt — reportar el error exacto.
- Si las versiones del pip freeze difieren del `.venv` instalado (entorno inconsistente) — reportar.

## Notas de mantenimiento

- Cuando se actualice cualquier dependencia en el futuro, actualizar la versión exacta en `requirements.txt` y volver a correr `make build && make test` antes de commitear.
- Si se decide agregar `curl_cffi` en el futuro (anti-bot más agresivo), agregarla como dependencia explícita con versión fija.
- `playwright` se mantiene aquí porque `make bootstrap` la instala junto al entorno base. Si en algún momento se separa en `requirements-dev.txt`, actualizar `make bootstrap` en el Makefile.
