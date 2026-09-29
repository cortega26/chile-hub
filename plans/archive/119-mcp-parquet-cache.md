# Plan 119: El servidor MCP cachea el Parquet por proceso (y no materializa 1.5M filas para devolver 10)

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/chile_hub/mcp_tools.py tests/test_pipeline_logic.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`chile_hub/mcp_tools.py` es el backend del servidor MCP (`chile-hub-mcp`,
Plan 104). Cada tool call pasa por `_read_dataset()`
(`mcp_tools.py:31-41`), que descarga el Parquet público con `requests.get` y lo
parsea con `pl.read_parquet` **sin caché**. Un servidor stdio de vida larga
paga red + parseo en cada llamada: `get_dataset("empresas", limite=10)`
descarga y materializa 29 MB / 1.57 M filas para devolver 10; dos llamadas
seguidas descargan dos veces. `df.height` en `get_dataset` (`:59`) fuerza la
materialización completa aunque el usuario pida 10 filas.

## Current state

- `src/chile_hub/mcp_tools.py:22` `PUBLIC_DATA_BASE = "https://tooltician.com/chile-hub/data/normalized"`.
- `:25-41`:
  ```python
  def _read_dataset(name: str, base_url: str) -> pl.DataFrame:
      dataset = Dataset.from_string(name)
      url = _parquet_url(base_url, dataset.value)
      if url.startswith(("http://", "https://")):
          response = requests.get(url, timeout=60)
          response.raise_for_status()
          return pl.read_parquet(io.BytesIO(response.content))
      return pl.read_parquet(url)
  ```
- `:52-69` `get_dataset`: `df = _read_dataset(...)`; `head = df.head(min(limite, MAX_LIMIT))`;
  devuelve `"filas_totales": df.height`.
- `:97-115` `get_indicadores` y `:72-92` `resolve_comunas` repiten `_read_dataset`.
- Tests existentes en `tests/test_pipeline_logic.py:5140-5260`
  (`McpToolsTests`-style, en realidad la clase se define más arriba; usa
  `base_url=tmpdir` con Parquet local y `requests` monkeypatcheado para el caso
  HTTP): reutiliza ese patrón.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests focal | `./.venv/bin/pytest tests/test_pipeline_logic.py -k "mcp or Mcp" -v` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `src/chile_hub/mcp_tools.py`
- `tests/test_pipeline_logic.py` (clase MCP)

**Out of scope**:
- `src/chile_hub/mcp_server.py` (registro de tools).
- Cambiar el contrato de las tools (nombres, campos de retorno).
- Descarga del bundle (`data_manager`) — MCP usa la capa HTTP a propósito.

## Git workflow

- Branch: `advisor/119-mcp-parquet-cache`
- Commit: `perf(mcp): cachea parquet por proceso en las tools`
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_pipeline_logic.py -k "mcp or Mcp" -v` verde. Si
no, STOP.

### Step 1: Caché acotada por proceso

Agrega en `mcp_tools.py`:

```python
from functools import lru_cache

# Caché por proceso: el servidor MCP vive toda la sesión del cliente y los
# Parquet publicados son inmutables dentro de una sesión (se regeneran a
# diario). maxsize chico a propósito: las capas grandes (empresas, 29 MB) no
# deben acumularse.
_CACHE_MAX_BYTES = 64 * 1024 * 1024


@lru_cache(maxsize=16)
def _read_parquet_cached(url: str) -> pl.DataFrame:
    ...
```

Detalles:
- `_read_dataset(name, base_url)` construye la URL y llama a
  `_read_parquet_cached(url)`; mantén el `Dataset.from_string(name)` antes
  (validación de nombre) y los dos caminos http/local.
- Respeta el caso HTTP sin `Content-Length` (test existente
  `test_read_dataset_over_http_without_content_length`): sigue descargando con
  `requests` y parseando bytes.
- `maxsize=16` en `lru_cache` da un tope de entradas; si quieres un tope real
  de bytes, envuelve: si `df.estimated_size() > _CACHE_MAX_BYTES`, devuelve sin
  cachear (no llames a una función cacheada en ese caso).
- Expón `_read_parquet_cached.cache_clear()` para los tests.
- No cachees errores: `lru_cache` no cachea excepciones (comportamiento
  correcto; déjalo documentado en un comentario).

### Step 2: Evitar materializar todo para `limite`

En `get_dataset`, para el camino HTTP puedes obtener las filas totales sin
bajar el archivo? No: el Parquet es remoto y `requests` ya bajó todo el
archivo (caché lo amortiza). Con la caché, el costo se paga una vez por
proceso. Sin embargo, puedes evitar el `pl.read_parquet` completo usando
`pl.scan_parquet(io.BytesIO(...))` para `limite` y `height`:

```python
    lazy = pl.scan_parquet(io.BytesIO(response.content))
    total = lazy.select(pl.len()).collect().item()
    head = lazy.head(min(limite, MAX_LIMIT)).collect()
```

Si esto último complica el caché (guardar bytes vs DataFrame), prioriza la
caché del DataFrame — es el 95% del beneficio; deja un comentario con por qué.
Elige UNA estrategia y no mezcles.

### Step 3: Tests

1. `test_read_dataset_uses_cache`: con `base_url` HTTP local (patrón del test
   `test_read_dataset_over_http_without_content_length`, que ya monta un
   `ThreadingHTTPServer`), ejecuta `get_dataset` dos veces y afirma que el
   handler contó **una sola** descarga (contador en el handler).
2. `test_cache_key_includes_base_url`: dos `base_url` distintos no comparten
   entrada.
3. `test_cache_clear_resets`: `cache_clear()` → vuelve a descargar.
4. Ajusta los tests existentes si importan `_read_dataset` directamente.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -k "mcp or Mcp" -v`
→ verde con ≥3 tests nuevos.

### Step 4: Cierre

`make lint`, `make format-check`, actualizar índice.

## Test plan

- 3 tests nuevos de caché (contador HTTP, clave por URL, clear).
- Patrón: `test_read_dataset_over_http_without_content_length`
  (`tests/test_pipeline_logic.py`, ~`:5237`).
- Verificación: pytest focal verde.

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py -k "mcp or Mcp" -v` → verde
- [ ] `grep -n "lru_cache\|cache_clear" src/chile_hub/mcp_tools.py` → presentes
- [ ] `grep -n "def _read_dataset" src/chile_hub/mcp_tools.py` → sigue existiendo y pasa por el caché
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si el patrón del test HTTP local no permite contar descargas (p. ej. el
  handler es compartido entre tests), detente y reporta; no agregues sleeps.
- Si `pl.scan_parquet` sobre bytes no soporta el Parquet publicado (probar con
  un archivo real de `data/normalized/` si existe), usa solo la caché de
  DataFrame y documenta.
- Si algún consumidor (mcp_server tests) depende de que `_read_dataset` no
  cachee, STOP.

## Maintenance notes

- Los datos se regeneran a diario en el sitio, pero el servidor MCP es de vida
  corta por sesión de cliente; una caché por proceso es correcta. Si algún día
  el server corre como servicio de larga vida, agregar TTL.
- `MAX_LIMIT` y `DEFAULT_LIMIT` no cambian (contrato documentado en
  `docs/mcp.md`).
- **Deferred:** `llms-full.txt`/tools extra (health, coords) están gateados por
  `docs/adoption-review.md`; este plan no los agrega.
