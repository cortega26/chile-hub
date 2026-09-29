# Plan 120: `check_sources()` en paralelo y caché del GeoParquet en `resolve_by_coords()`

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/chile_hub/core.py src/chile_hub/geo.py tests/test_core.py tests/test_chile_hub.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW (-MED en el paso 1)
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Dos caminos de la API pública pagan trabajo evitable:

1. `ChileHub.check_sources()` (`core.py:1488-1538`) recorre el catálogo (~22
   fuentes) **en serie**, un `requests.head` (con GET de fallback) y
   `timeout=5` por dataset. Un comando de diagnóstico tarda 10-60 s típico y
   hasta ~220 s si varias fuentes están caídas. El repo ya usa
   `ThreadPoolExecutor` en extractores (`bcentral_extractor.py:310`).
2. `ChileHub.resolve_by_coords()` (`core.py:457-468`) llama a
   `load_geometry(path)` en cada invocación; `geo.py:220-227` hace
   `gpd.read_parquet` + `validate_geometry()` completo (346 geometrías) cada
   vez, aunque el artefacto es inmutable y está fijado por SHA-256 (ADR-012).

## Current state

- `src/chile_hub/core.py:1488-1538`:
  ```python
      def check_sources(self, timeout: int = 5) -> list[dict[str, Any]]:
          results = []
          for entry in self.catalog.get("datasets", []):
              ...
              response = requests.head(url, timeout=timeout, allow_redirects=True)
              if response.status_code >= 400:
                  response.close()
                  response = requests.get(url, timeout=timeout, stream=True)
              ...
  ```
- `src/chile_hub/core.py:457-468`:
  ```python
          try:
              if geometry_path is not None:
                  path = geometry_path
              else:
                  path = acquire_geometry(refresh_geometry=refresh_geometry)
              gdf = load_geometry(path)
  ```
- `src/chile_hub/geo.py:220-227`:
  ```python
  def load_geometry(path: Path) -> "GeoDataFrame":
      """Carga un GeoParquet local como GeoDataFrame, con validación estructural."""
      _require_geo()
      import geopandas as gpd

      gdf = gpd.read_parquet(path)
      validate_geometry(gdf)
      return gdf
  ```
- Tests: `tests/test_core.py:640-740` (`ResolveByCoordsTests`-style, con
  `geometry_path=self._fixture_path()` y fixtures sintéticos de
  `tests/geo_fixtures.py`); `check_sources` no tiene tests directos (grep).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests core/geo | `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v -k "coords or sources"` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |
| Typecheck | `make typecheck` | declared | exit 0 |

## Scope

**In scope**:
- `src/chile_hub/core.py` (`check_sources`, `resolve_by_coords`)
- `src/chile_hub/geo.py` (caché de `load_geometry`)
- `tests/test_core.py` / `tests/test_chile_hub.py`

**Out of scope**:
- Cambiar la firma pública de `check_sources`/`resolve_by_coords`.
- `acquire_geometry` (ya evita re-descarga/re-hash).
- Cambiar el output del reporte de `check_sources` (mismos campos y orden).

## Git workflow

- Branch: `advisor/120-core-perf-diagnostics-cache`
- Commits: `perf(core): ...` (estilo repo).
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v -k "coords or sources"` verde. Si no, STOP.

### Step 1: `check_sources` con `ThreadPoolExecutor`

- Extrae el cuerpo del loop a una función interna `_probe(entry) -> dict`
  (misma estructura de dict y misma semántica de errores: `Exception` → status
  offline con `type(e).__name__`; `response.close()` en todos los caminos).
- Usa:
  ```python
  from concurrent.futures import ThreadPoolExecutor

  entries = list(self.catalog.get("datasets", []))
  workers = min(8, max(1, len(entries)))
  with ThreadPoolExecutor(max_workers=workers) as pool:
      results = list(pool.map(_probe, entries))
  ```
  `map` preserva el orden de `entries` — no se necesita indexar.
- Mantén el `timeout` por request. No agregues retries (diagnóstico, no
  extracción).

**Verify**: test nuevo con `unittest.mock.patch("requests.head")` que devuelve
respuestas fake; afirma que `[r["dataset"] for r in results]` sigue el orden
del catálogo y que las 22 entradas están. (No testees concurrencia real con
timers; sería flaky.)

### Step 2: Caché de geometría

En `src/chile_hub/geo.py`:

```python
_GEOMETRY_CACHE: dict[tuple[str, int], "GeoDataFrame"] = {}


def load_geometry(path: Path) -> "GeoDataFrame":
    _require_geo()
    import geopandas as gpd

    stat = Path(path).stat()
    key = (str(path), stat.st_mtime_ns)
    cached = _GEOMETRY_CACHE.get(key)
    if cached is not None:
        return cached
    gdf = gpd.read_parquet(path)
    validate_geometry(gdf)
    _GEOMETRY_CACHE.clear()  # el path de caché es único; no acumular historiales
    _GEOMETRY_CACHE[key] = gdf
    return gdf


def clear_geometry_cache() -> None:
    """Vacía la caché; usado por tests y tras un refresh explícito."""
    _GEOMETRY_CACHE.clear()
```

- La clave con `st_mtime_ns` invalida automáticamente cuando
  `refresh_geometry=True` reemplaza el archivo (reemplazo atómico en
  `acquire_geometry`), sin acoplarse al flag.
- `resolve_by_coords` no cambia: sigue llamando `load_geometry(path)`.
- `path` puede no existir si el caller pasó `geometry_path` inválido: `stat()`
  lanza `FileNotFoundError` igual que hoy `read_parquet`; verifica que el
  mensaje/`ChileHubDataError` esperado en `core.py:461-467` se preserve.

**Verify**: test nuevo en `tests/test_core.py` que hace dos
`resolve_by_coords(points, geometry_path=fixture)` y afirma que
`gpd.read_parquet` fue llamado una sola vez (patch en
`geopandas.read_parquet`); y otro test que
`refresh_geometry=True`/mtime distinto invalida (simular tocando el archivo o
parchando `acquire_geometry`). Llama `clear_geometry_cache()` en
`setUp`/`tearDown` de la clase de tests de geo existente.

### Step 3: Cierre

`make lint`, `make format-check`, `make typecheck`, actualizar índice.

## Test plan

- `check_sources`: test de orden/completitud con `requests.head` parcheado.
- `load_geometry`: test de reutilización (una lectura) + invalidación por
  mtime + `clear_geometry_cache`.
- Patrón: `tests/test_core.py:640-740`.
- Verificación: pytest focal verde; suite completa si el tiempo lo permite.

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v` → verde
- [ ] `grep -n "ThreadPoolExecutor" src/chile_hub/core.py` → 1 match
- [ ] `grep -n "clear_geometry_cache\|_GEOMETRY_CACHE" src/chile_hub/geo.py` → presentes
- [ ] `make typecheck` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `requests.head` no es thread-safe con el mocking existente de la suite,
  STOP.
- Si el test de una sola lectura es imposible sin tocar más de `geo.py/core.py`
  (p. ej. hay otro caller intermedio), reporta.
- Si aparece un uso de `load_geometry` que **muta** el GeoDataFrame, STOP: la
  caché compartiría estado mutable.

## Maintenance notes

- La caché de geometría vive a nivel módulo (no por instancia): dos
  `ChileHub` en el mismo proceso comparten lectura; correcto porque el
  artefacto es inmutable por SHA. Si se agrega escritura/mutación de
  geometrías, revisar.
- `check_sources` es diagnóstico: si alguna fuente castiga concurrencia
  (rate-limit), el pool de 8 puede subir 429s; hoy se acepta.
- **Deferred:** exponer `clear_geometry_cache()` en la API pública — se usa
  solo desde tests/refresh interno; documentarlo si un consumidor lo pide.
