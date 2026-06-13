# Plan 010: Deduplicar helpers compartidos entre módulos

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- src/build_dev_db.py src/chile_hub.py scripts/verify_pipeline.py src/pipeline_status_utils.py`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P2
- **Esfuerzo**: S
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: arch
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

La misma función `parse_iso_datetime` está implementada dos veces con lógica idéntica (una en `build_dev_db.py:161` y otra como `_parse_iso_datetime` en `chile_hub.py:62`). La misma función `load_json` está duplicada en `pipeline_status_utils.py:17` y en `verify_pipeline.py:55`. Además, `build_dev_db.py` usa un import relativo (`from pipeline_status_utils import ...`) mientras `chile_hub.py` usa uno absoluto (`from src.pipeline_status_utils import ...`), creando inconsistencia. Este plan consolida los helpers en `src/pipeline_status_utils.py` (que ya es el módulo compartido) y normaliza los imports.

## Estado actual

### Duplicación 1: `parse_iso_datetime`

```python
# src/build_dev_db.py:161-170
def parse_iso_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

# src/chile_hub.py:62-71 — idéntica lógica
@staticmethod
def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
```

### Duplicación 2: `load_json`

```python
# src/pipeline_status_utils.py:17-19
def load_metadata(path=PIPELINE_METADATA_PATH):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

# scripts/verify_pipeline.py:55-57
def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
```

`load_metadata` en `pipeline_status_utils.py` tiene un default path; `load_json` en `verify_pipeline.py` no. Son funcionalmente equivalentes para paths arbitrarios.

### Inconsistencia 3: import de `pipeline_status_utils`

```python
# src/build_dev_db.py:9 — import relativo (sin prefijo src.)
from pipeline_status_utils import (
    build_hub_health,
    write_status_markdown_file,
    ...
)

# src/chile_hub.py:8 — import absoluto con prefijo src.
from src.pipeline_status_utils import format_top_issue_summary
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Build | `make build` | exit 0 |
| Tests | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Verify | `.venv/bin/python scripts/verify_pipeline.py` | exit 0 |
| Check imports | `python3 -c "from src.pipeline_status_utils import parse_iso_datetime; print('OK')"` | `OK` tras el cambio |

## Alcance

**En scope**:
- `src/pipeline_status_utils.py` — agregar `parse_iso_datetime` y un alias `load_json`
- `src/build_dev_db.py` — eliminar la copia local de `parse_iso_datetime` y actualizar el import a absoluto
- `src/chile_hub.py` — reemplazar `_parse_iso_datetime` con llamada al import
- `scripts/verify_pipeline.py` — reemplazar `load_json` local con import desde `pipeline_status_utils`

**Fuera de scope**:
- No cambiar la lógica de ninguna función
- No refactorizar `_load_*` de `ChileHub` en este plan (es más grande — pertenece a un plan de arquitectura posterior)

## Git workflow

- Rama: `advisor/010-deduplicar-helpers`
- Estilo de commit: `refactor: deduplicar parse_iso_datetime y load_json en pipeline_status_utils`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar `parse_iso_datetime` y `load_json` en `pipeline_status_utils.py`

Al inicio de `src/pipeline_status_utils.py`, después de los imports existentes, agregar los imports necesarios si faltan:

```python
from datetime import datetime, timezone
```

Luego agregar las funciones (idealmente cerca del principio del archivo, después de los imports):

```python
def parse_iso_datetime(value):
    """Parsea un string ISO 8601 a datetime UTC-aware. Retorna None si inválido."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json(path):
    """Carga y parsea un archivo JSON desde un Path o string."""
    import json
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
```

**Verificar**: `python3 -c "from src.pipeline_status_utils import parse_iso_datetime, load_json; print('OK')"` imprime `OK`.

### Paso 2: Actualizar `src/build_dev_db.py`

**2a.** Cambiar el import de `pipeline_status_utils` de relativo a absoluto:

```python
# ANTES (línea 9):
from pipeline_status_utils import (...)

# DESPUÉS:
from src.pipeline_status_utils import (
    build_hub_health,
    write_status_markdown_file,
    write_dataset_catalog_markdown_file,
    write_hub_health_markdown_file,
    write_redistribution_report_markdown_file,
    write_provenance_report_markdown_file,
    write_drift_report_markdown_file,
    write_overview_markdown_file,
    parse_iso_datetime,  # ← agregar
)
```

**2b.** Eliminar la definición local de `parse_iso_datetime` (líneas 161-170). La función ahora viene del import.

**Verificar**: `grep -n "^def parse_iso_datetime" src/build_dev_db.py` devuelve vacío.

**Verificar**: `python3 -c "from src.build_dev_db import parse_iso_datetime; print('OK')"` — si la función sigue siendo necesaria en el namespace del módulo para algún test, verificarlo antes de eliminar.

### Paso 3: Actualizar `src/chile_hub.py`

Agregar `parse_iso_datetime` al import existente:

```python
# chile_hub.py:8 — agregar al import existente
from src.pipeline_status_utils import format_top_issue_summary, parse_iso_datetime
```

Reemplazar el uso de `self._parse_iso_datetime(value)` por `parse_iso_datetime(value)` en todos los métodos de la clase que lo llamen. Buscar las ocurrencias:

```bash
grep -n "_parse_iso_datetime" src/chile_hub.py
```

Para cada ocurrencia, reemplazar `self._parse_iso_datetime(` por `parse_iso_datetime(`.

Luego eliminar la definición del método `_parse_iso_datetime` de la clase `ChileHub` (líneas 61-71).

**Verificar**: `grep -n "_parse_iso_datetime" src/chile_hub.py` devuelve vacío.

### Paso 4: Actualizar `scripts/verify_pipeline.py`

Agregar el import de `load_json` desde `pipeline_status_utils`:

```python
# Al inicio de verify_pipeline.py, después de los imports existentes
import sys
_SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
from pipeline_status_utils import load_json as _load_json_from_utils
```

Luego reemplazar la función local:

```python
# ANTES (líneas 55-57):
def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# DESPUÉS — alias del import:
load_json = _load_json_from_utils
```

**Verificar**: `python3 scripts/verify_pipeline.py` — exit 0.

### Paso 5: Correr el build completo y los tests

```bash
make build
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: ambos salen con exit 0. Todos los tests pasan.

## Criterios de done

- [ ] `grep -n "def parse_iso_datetime" src/pipeline_status_utils.py` retorna la definición
- [ ] `grep -n "^def parse_iso_datetime" src/build_dev_db.py` devuelve vacío
- [ ] `grep -n "_parse_iso_datetime" src/chile_hub.py` devuelve vacío
- [ ] `grep -n "from src.pipeline_status_utils" src/build_dev_db.py` retorna el import absoluto
- [ ] `make build` sale con exit 0
- [ ] `.venv/bin/python scripts/verify_pipeline.py` sale con exit 0
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] Solo los 4 archivos en scope modificados
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si `from src.pipeline_status_utils import ...` falla cuando `build_dev_db.py` se ejecuta directamente como script (`python src/build_dev_db.py`) — puede fallar si `src/` no está en `sys.path`. En ese caso, verificar si `build_dev_db.py` tiene un bloque que ajusta `sys.path` al inicio, o agregar uno.
- Si `_parse_iso_datetime` se usa en algún lugar dentro de `chile_hub.py` que no sea un método de instancia (ej. como referencia a función en un dict) — reportar antes de eliminar.
- Si algún test importa `parse_iso_datetime` directamente de `build_dev_db` — actualizar el import del test.

## Notas de mantenimiento

- `pipeline_status_utils.py` se convierte en el módulo utilitario compartido. Futuros helpers puros (funciones de formato, parseo de fechas) deben vivir aquí.
- El import absoluto (`from src.pipeline_status_utils import ...`) es el estándar del repo. Si `build_dev_db.py` necesita ser ejecutable tanto como script (`python src/build_dev_db.py`) como módulo (`python -m src.build_dev_db`), agregar al inicio del archivo:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
