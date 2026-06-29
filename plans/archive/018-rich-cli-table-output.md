# Plan 018: Renderizar las tablas de la CLI con `rich` en vez de padding manual

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar, actualiza la fila de estado de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat 140c8ea..HEAD -- src/chile_hub/core.py pyproject.toml tests/test_core.py`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `140c8ea`, 2026-06-29
- **Executed at**: commit `140c8ea`, 2026-06-29
- **Verdict**: APPROVED por `claude` — todos los criterios cumplidos
- **Ejecutor**: `general-purpose` (worktree `agent-a6b5599ae45b98a4b`)

## Why this matters

La CLI tiene 16 métodos `*_table()` en `src/chile_hub/core.py` que construyen tablas
de texto con padding manual (`f"{valor:<11}"`) y líneas de guiones escritas a mano.
Esto es frágil: el ancho de columna está hardcodeado, no se adapta al contenido, y
los nombres con acentos/`ñ` (frecuentes en datos chilenos) desalinean las columnas
porque el conteo de caracteres no coincide con el ancho visual. `rich` ya está en
`uv.lock` como dependencia transitiva (versión 14.3.4), así que promoverlo a
dependencia directa no añade peso nuevo al árbol. El resultado: menos código a
mano, alineación correcta de columnas Unicode, y una base para colorear la salida
más adelante.

## Current state

Archivos relevantes:

- `src/chile_hub/core.py` — clase `ChileHub`; contiene los 16 métodos `*_table()`
  (líneas ~236 a ~1521) y el dispatch de CLI en `_main()` (líneas ~1834 a ~2110).
- `pyproject.toml` — `dependencies` (líneas 37–43) no incluye `rich`; está solo
  como transitiva.
- `tests/test_core.py` — verifica las tablas por **subcadena de título**, no por
  formato exacto. Esto es lo que hay que preservar.

Patrón actual de un método `*_table()` (`src/chile_hub/core.py:526-545`):

```python
def summary_table(self):
    rows = self.summary()
    lines = ["chile-hub summary", ""]
    lines.append(
        "dataset      mode      records  freshness  coverage        validation  drift     warnings"
    )
    lines.append(
        "-----------  --------  -------  ---------  --------------  ----------  --------  --------"
    )
    for entry in rows:
        lines.append(
            f"{entry.get('dataset', 'unknown'):<11}  "
            f"{entry.get('source_mode', 'unknown'):<8}  "
            f"{str(entry.get('record_count', 'N/D')):<7}  "
            # ... más columnas con padding manual ...
        )
    return "\n".join(lines) + "\n"
```

Cómo lo consume la CLI (`src/chile_hub/core.py:1967-1971`) — siempre imprime el
string devuelto con `end=""`:

```python
if args.command == "status":
    if args.format == "table":
        print(hub.status_table(), end="")
    else:
        print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
```

Cómo lo verifican los tests (`tests/test_core.py:40-44`) — **solo subcadenas**:

```python
def test_summary_table_returns_string(self):
    table = self.hub.summary_table()
    self.assertIsInstance(table, str)
    self.assertIn("chile-hub summary", table)
    self.assertIn("dataset", table.lower())
```

Los 16 métodos a migrar (verifica con `grep -nE "def [a-z_]+_table" src/chile_hub/core.py`):
`top_issue_table`, `summary_table`, `snapshot_table`, `shared_artifacts_table`,
`report_index_table`, `inventory_table`, `overview_table`, `check_sources_table`,
`status_table`, `health_table`, `freshness_audit_table`, `runtime_status_table`,
`packages_table`, `redistribution_table`, `provenance_table`, `drift_table`.

Cada uno comienza con una línea de título literal (`"chile-hub summary"`,
`"chile-hub health"`, `"chile-hub status"`, etc.) que **los tests verifican por
subcadena** — esos títulos NO pueden cambiar.

Convención del repo: idioma español neutral en comentarios/docstrings (sin voseo),
comillas dobles (ruff format), líneas ≤100 (E501 está ignorado pero respétalo en
código nuevo). Tipado con type hints; mypy corre sobre `src/chile_hub`.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Typecheck | `.venv/bin/python -m mypy` | exit 0, sin errores nuevos |
| Tests (foco) | `.venv/bin/python -m pytest tests/test_core.py -q` | todos pasan |
| Suite completa | `make test` | todos pasan |
| Smoke CLI | `.venv/bin/python -m chile_hub summary --format table` | imprime tabla |

`make test` y los métodos `*_table()` requieren `data/normalized/` poblado. Si no
existe, ejecuta `make build` primero (es pesado, ~minutos). Si `make build` falla
por falta de datos de staging, eso es una STOP condition — repórtalo.

## Scope

**In scope** (únicos archivos a modificar):
- `pyproject.toml` — promover `rich` a dependencia de runtime.
- `src/chile_hub/_render.py` — **crear**: helper de renderizado con `rich`.
- `src/chile_hub/core.py` — migrar los 16 métodos `*_table()` para usar el helper.
- `tests/test_render.py` — **crear**: tests del helper nuevo.

**Out of scope** (NO tocar, aunque parezcan relacionados):
- El dispatch de CLI en `_main()` y `build_parser()` — la migración argparse→typer
  es un follow-up deferido (ver Maintenance notes). El `print(..., end="")` se queda.
- Los métodos que devuelven JSON (`summary()`, `status()`, etc.) — solo cambian los
  `*_table()`.
- Las líneas de título literales (`"chile-hub summary"` etc.) — deben preservarse
  carácter por carácter porque los tests las verifican.
- **No introduzcas códigos de color ANSI en el string devuelto** — ver Step 2 (los
  métodos devuelven texto que también consumen tests y posibles scripts; el color
  es un follow-up deferido).

## Git workflow

- Branch: `advisor/018-rich-cli-table-output`
- Commit por unidad lógica; estilo conventional commits (ver `git log`):
  ej. `refactor(cli): renderizar tablas con rich en vez de padding manual`.
- No hagas push ni abras PR salvo que el operador lo indique.

## Steps

### Step 1: Promover `rich` a dependencia de runtime

En `pyproject.toml`, dentro de `[project].dependencies` (líneas 37–43), añade
`rich` después de `platformdirs`. Usa el rango `>=14.0` (la versión resuelta en
`uv.lock` es 14.3.4):

```toml
dependencies = [
    "polars>=1.41.2",
    "pyarrow>=24.0.0",
    "requests>=2.34.2",
    "platformdirs>=4.10.0",
    "rich>=14.0",
]
```

**Verify**: `grep -n '"rich' pyproject.toml` → muestra la línea en `dependencies`.

### Step 2: Crear el helper de renderizado `src/chile_hub/_render.py`

Crea un módulo con una función que reciba un título, encabezados y filas, y
devuelva un string de tabla renderizada por `rich` **sin códigos de color ANSI**
(para no romper tests ni la salida en pipes). El patrón:

```python
"""Renderizado de tablas de la CLI con rich.

Devuelve texto plano (box-drawing Unicode, sin ANSI) para que la salida sea
estable en tests y en pipes. El color es un follow-up deferido.
"""

from __future__ import annotations

import io
from typing import Sequence

from rich.console import Console
from rich.table import Table


def render_table(
    title: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    width: int = 120,
) -> str:
    """Renderiza una tabla a texto plano, precedida por `title`.

    El título se emite tal cual en la primera línea (los tests lo verifican por
    subcadena). La tabla se renderiza sin color para mantener la salida estable.
    """
    table = Table(show_edge=True, expand=False)
    for header in headers:
        table.add_column(header, overflow="fold")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    buffer = io.StringIO()
    console = Console(
        file=buffer,
        width=width,
        force_terminal=False,  # sin ANSI
        no_color=True,
        highlight=False,
    )
    console.print(table)
    return f"{title}\n\n{buffer.getvalue()}"
```

**Verify**:
`.venv/bin/python -c "from src.chile_hub._render import render_table; print(render_table('chile-hub demo', ['a','b'], [['1','2']]))"`
→ imprime `chile-hub demo` seguido de una tabla con bordes y sin secuencias `\x1b[`.

### Step 3: Migrar los 16 métodos `*_table()` para usar `render_table`

Para cada método, reemplaza la construcción manual de `lines` por una llamada a
`render_table(title, headers, rows)`. Reglas:

1. **Preserva el título literal exacto** que el método ya emite (`"chile-hub
   summary"`, `"chile-hub health"`, etc.). Confírmalo leyendo cada método antes de
   editarlo.
2. Los `headers` son los nombres de columna que el método ya usaba (en minúscula
   donde los tests verifican `.lower()`; cuando dudes, mantén minúscula).
3. Las `rows` son listas de strings, una por entrada, con los mismos campos y
   orden que el padding manual original.
4. La firma del método NO cambia: sigue siendo `def x_table(self) -> str` (o con
   los args que ya tuviera, como `shared_artifacts_table(self, shared_type, format)`).
5. Si un método tenía secciones múltiples o texto libre además de la tabla (p. ej.
   `snapshot_table`, `top_issue_table`), conserva ese texto y solo reemplaza el
   bloque tabular; no fuerces todo a una sola tabla.

Ejemplo de migración de `summary_table` (`src/chile_hub/core.py:526`):

```python
def summary_table(self) -> str:
    rows = self.summary()
    table_rows = [
        [
            entry.get("dataset", "unknown"),
            entry.get("source_mode", "unknown"),
            str(entry.get("record_count", "N/D")),
            entry.get("freshness_status", "unknown"),
            entry.get("coverage_status", "unknown"),
            entry.get("validation_status", "unknown"),
            entry.get("drift_status", "unknown"),
            str(entry.get("warning_count", 0)),
        ]
        for entry in rows
    ]
    return render_table(
        "chile-hub summary",
        ["dataset", "mode", "records", "freshness", "coverage", "validation", "drift", "warnings"],
        table_rows,
    )
```

Añade el import al inicio de `core.py` junto a los demás imports relativos:
`from ._render import render_table` (si `core.py` usa imports absolutos
`from chile_hub...`, sigue ese estilo; revisa los imports existentes del archivo).

**Verify tras migrar todos**:
- `make lint` → exit 0
- `.venv/bin/python -m pytest tests/test_core.py -q` → todos pasan
- `grep -cE ":<[0-9]+" src/chile_hub/core.py` → cuenta de padding manual debe bajar
  drásticamente (idealmente a 0 dentro de los métodos `*_table`; puede quedar en
  otros lugares fuera de alcance — inspecciona que los restantes NO estén en
  métodos `*_table`).

### Step 4: Tests del helper

Crea `tests/test_render.py` siguiendo el estilo de `tests/test_core.py` (unittest
o funciones `test_*`, revisa cuál usa el archivo). Cubre:
- Devuelve `str` y empieza con el título dado.
- La salida contiene cada header y cada valor de celda.
- La salida NO contiene la secuencia de escape ANSI `\x1b[`.
- Una tabla con un nombre con acento/`ñ` (ej. `"Ñuñoa"`) no lanza excepción y el
  valor aparece en la salida.

**Verify**: `.venv/bin/python -m pytest tests/test_render.py -q` → todos pasan.

### Step 5: Smoke de la CLI y suite completa

**Verify**:
- `.venv/bin/python -m chile_hub summary --format table` → imprime tabla con bordes.
- `.venv/bin/python -m chile_hub health --format table` → imprime tabla; la salida
  contiene `chile-hub health`.
- `make test` → toda la suite pasa.
- `make format-check` → exit 0.
- `.venv/bin/python -m mypy` → sin errores nuevos.

## Test plan

- Nuevo archivo `tests/test_render.py` (4 casos del Step 4), modelado sobre
  `tests/test_core.py`.
- Los tests existentes de `tests/test_core.py` (`test_*_table_returns_string`)
  deben seguir pasando sin modificarlos. Si alguno falla por una subcadena de
  título, NO cambies el test: corrige el método para preservar el título original.
- Verificación: `make test` → todos pasan, incluyendo los nuevos de `test_render.py`.

## Done criteria

Todas deben cumplirse:

- [ ] `grep -n '"rich' pyproject.toml` muestra `rich` en `[project].dependencies`.
- [ ] `src/chile_hub/_render.py` existe y exporta `render_table`.
- [ ] Los 16 métodos `*_table()` usan `render_table` (sin bloques de padding
      `f"{...:<N}"` propios).
- [ ] `make test` exit 0; `tests/test_render.py` existe y pasa.
- [ ] `make lint` y `make format-check` exit 0.
- [ ] `.venv/bin/python -m mypy` sin errores nuevos.
- [ ] La salida de `chile-hub summary --format table` no contiene `\x1b[`
      (sin ANSI): `chile-hub summary --format table | grep -c $'\x1b\\['` → `0`.
- [ ] Ningún archivo fuera del alcance fue modificado (`git status`).
- [ ] Fila de `plans/README.md` actualizada.

## STOP conditions

Detente y reporta (no improvises) si:

- El código en los métodos `*_table()` no coincide con los extractos de "Current
  state" (el código derivó desde que se escribió este plan).
- `make build` falla por falta de datos de staging y no puedes poblar
  `data/normalized/` para correr los tests que dependen de él.
- Un test de `test_core.py` falla por una razón que NO sea una subcadena de título
  faltante (indicaría un cambio de comportamiento no previsto).
- Migrar un método requeriría cambiar su firma pública o el formato JSON asociado.

## Maintenance notes

- **Follow-up deferido — color**: una vez confirmado que la salida `table` es solo
  para humanos (no parseada por scripts), se puede habilitar color en `render_table`
  (quitar `no_color=True`) detectando TTY. Revisa antes los targets `hub-*-table`
  del `Makefile` y consumidores externos.
- **Follow-up deferido — typer**: migrar `build_parser()`/`_main()` (argparse, ~40
  subcomandos) a `typer` daría ayuda y autocompletado más ricos, pero es un rewrite
  L de una CLI ya probada (riesgo MED-HIGH de regresión). No se incluyó aquí a
  propósito; evalúalo como plan aparte si la CLI crece.
- En revisión de PR: confirmar que cada título literal se preservó y que no se
  introdujeron ANSI en los strings devueltos.
