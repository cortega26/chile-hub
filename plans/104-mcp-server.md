# Plan 104: Servidor MCP (`chile-hub[mcp]`) — datos para agentes

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 039fc03..HEAD -- pyproject.toml uv.lock src/chile_hub/mcp_tools.py src/chile_hub/mcp_server.py docs/mcp.md mkdocs.yml tests/test_pipeline_logic.py tests/test_ci_config.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (dependencia opcional nueva; se aísla en su propio extra)
- **Depends on**: none (el fix del visor HF del 101 es canal complementario)
- **Category**: distribution
- **Planned at**: commit `039fc03`, 2026-09-25

## Why this matters

El canal de distribución de mayor crecimiento en 2026 son los agentes de
código (Claude Desktop/Code, Cursor, VS Code). Hoy chile-hub sólo existe para
ellos si alguien lo instala a mano. Un servidor MCP local, sin hosting ni API
propia, pone `list_datasets`, `get_dataset`, `resolve_comunas` e
`get_indicadores` en cualquier cliente MCP: cero infraestructura, datos servidos
desde la capa HTTP estática que ya existe (Plan 051). Se aísla en el extra
`mcp` para no tocar la instalación base (`polars` + `requests`).

## Current state

- No existe nada MCP en el repo (`grep -ri "mcp"` sólo matchea el prefijo
  "mcp" en logs, no código).
- `pyproject.toml:38-95` — extras `pipeline`, `query`, `geo`, `validation`,
  `dev`, `scraping`; `[project.scripts]` sólo `chile-hub = "chile_hub.cli:main"`.
- `src/chile_hub/text.py:22` — `normalize_comuna_name()` pura y reutilizable.
- `src/chile_hub/datasets.py` — `Dataset(StrEnum)` con las 22 capas.
- Base HTTP estable: `https://tooltician.com/chile-hub/data/normalized/`
  (`docs/http-access.md`), con `{capa}.parquet` por dataset.
- PyPI: `mcp` 2.2.0 disponible (verificado 2026-09-25); la API exacta de
  `FastMCP` debe confirmarse contra el paquete instalado en el Step 2.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Lock sync | `uv lock && uv lock --check` | declared | exit 0 |
| Extra MCP | `uv run --extra mcp python -c "from chile_hub.mcp_server import main; print('ok')"` | declared | `ok` |
| Tests tools | `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "Mcp"` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |

## Scope

**In scope**:
- `pyproject.toml` (extra `mcp` + entry point `chile-hub-mcp`) y `uv.lock`
- `src/chile_hub/mcp_tools.py` (funciones puras, sin importar `mcp`)
- `src/chile_hub/mcp_server.py` (wrapper con import perezoso de `mcp`)
- `docs/mcp.md` + nav en `mkdocs.yml`
- `tests/test_pipeline_logic.py` (`McpToolsTests`)
- `tests/test_ci_config.py` (guardrails)

**Out of scope**:
- Ejecución de SQL arbitrario como tool (el API ya expone `sql()`; puede ser
  un follow-up si hay demanda).
- Hosting remoto/SSE del servidor: sólo stdio local.
- Tocar las dependencias base: `mcp` vive sólo en el extra.

## Git workflow

- Branch: `advisor/distribution-wave-1` (wave 101–105).
- Commit por step; conventional commits (ej. `feat(mcp): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Herramientas puras (`mcp_tools.py`)

Implementar funciones testeables sin `mcp` ni red en import:
- `list_datasets()` → lista de dicts con `nombre`, `formato` y URL del Parquet,
  derivada de `Dataset` (no de un catálogo que puede no estar en la wheel).
- `get_dataset(nombre, limite=100, base_url=PUBLIC_DATA_BASE)` → valida con
  `Dataset.from_string`, lee `{base_url}/{nombre}.parquet` con
  `polars.read_parquet` y devuelve `{"dataset", "filas", "columnas", "registros"}`
  con `limite` acotado (máximo duro 1000).
- `resolve_comunas(nombres, base_url=...)` → reusa `normalize_comuna_name` y el
  Parquet de `comunas`; devuelve `(entrada, codigo_comuna, nombre_comuna, matched)`.
- `get_indicadores(codigo=None, desde=None, hasta=None, base_url=...)` →
  filtra el Parquet de `indicadores`; sin argumentos devuelve las últimas 100 filas.
`base_url` es inyectable para tests offline (ruta local o URL).

**Verify**: `./.venv/bin/python -c "from chile_hub.mcp_tools import list_datasets; print(len(list_datasets()))"` → ≥ 17.

### Step 2: Servidor (`mcp_server.py`) con import perezoso

Implementar `main()` que importa `mcp` **dentro** de la función y, si falta,
sale con mensaje `pip install chile-hub[mcp]`. Registrar las 4 tools con
docstrings en español (son la descripción que ve el agente). Nombre del server:
`chile-hub`. Sin estado global, sin escritura en disco. Confirmar la API real
de `FastMCP` contra el paquete instalado (`uv run --extra mcp python -c ...`) y
adaptar si 2.x renombró módulos; si la API difiere de lo asumido, registrar la
desviación en `todo.md`.

**Verify**: `uv run --extra mcp python -c "from chile_hub.mcp_server import main; print('ok')"` → `ok`; y sin el extra: `./.venv/bin/python -c "from chile_hub.mcp_server import main; print('ok')"` → `ok` (import perezoso no debe romper).

### Step 3: pyproject + lock

Agregar extra `mcp = ["mcp>=2.2,<3"]` (rango runtime, no pin de pipeline) y
`chile-hub-mcp = "chile_hub.mcp_server:main"` en `[project.scripts]`. Correr
`uv lock` y commitear `uv.lock`. Si el resolver choca con `[tool.uv] conflicts`
(`dev` vs `scraping`), documentar el conflicto y evaluar mover el extra a ese
bloque antes de improvisar pins.

**Verify**: `uv lock --check` exit 0; `uv run --extra mcp python -c "from chile_hub.mcp_server import main"` exit 0.

### Step 4: Docs + tests

Crear `docs/mcp.md` con: instalación
(`uvx --from "chile-hub[mcp]" chile-hub-mcp`), config de Claude Desktop / VS
Code (bloque JSON `mcpServers`), tabla de tools, origen de datos (HTTP estático
+ mirror HF) y política de cero telemetría. Agregar al nav.
En `tests/test_pipeline_logic.py`, `McpToolsTests`: tools contra Parquet
sintéticos en `tmp_path` (comunas con tildes/ñ, indicadores con fechas), casos
borde (límite > máximo, dataset inexistente → error claro, nombres no
matcheados). En `tests/test_ci_config.py`: guardrail del extra + entry point +
docs en nav.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q -k "Mcp or mcp"` → all pass.

## Test plan

- Nuevos: `McpToolsTests` (≥5 tests) + guardrail de packaging.
- Sin red: `base_url` apunta a `tmp_path` con Parquet sintéticos.
- Sin `mcp` instalado en CI base: los tests de tools no lo importan; el import
  del server es perezoso y se testea que no rompe sin el extra.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `uv lock --check` exits 0 y `grep -q 'mcp = \[' pyproject.toml`
- [ ] `uv run --extra mcp python -c "from chile_hub.mcp_server import main; print('ok')"` → `ok`
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py tests/test_ci_config.py -q` exits 0
- [ ] `make doctor` exits 0
- [ ] `git diff --name-only 039fc03...HEAD` lista sólo archivos in-scope (incl. `uv.lock`)
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog actualizados

## STOP conditions

Stop and report back (do not improvise) if:

- `uv lock` no resuelve `mcp` sin degradar/pinear dependencias ya fijadas por
  otro extra (documentar el conflicto y detenerse).
- La API de `FastMCP` 2.x no permite registrar tools sin un servidor de red o
  exige escribir configuración en disco.
- Un test necesita red real (debe ser inyectable con `base_url`).
- Una verificación falla dos veces tras un intento razonable de fix.

## Maintenance notes

- El extra `mcp` no es dependencia base: nunca importar `mcp` a nivel de módulo
  en `mcp_server.py` (rompería `import chile_hub`).
- Reviewer: los docstrings de las tools son UX de agente; revisar que digan qué
  devuelven y el límite de filas.
- Deferido: tool `query(sql)` con DuckDB y tools de escritura no tendrán soporte
  hasta que exista demanda; el servidor es read-only por diseño.
