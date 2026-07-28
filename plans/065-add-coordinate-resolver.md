# Plan 065: Expose verified coordinate-to-comuna resolution

> **Executor instructions**: Follow every step and verification gate. Do not make
> candidate geometry part of the stable bundle and do not add geo libraries to the
> base installation. If an artifact URL cannot be integrity-verified, STOP and
> report it. Update this plan's row in `plans/README.md` only when all done
> criteria are true.
>
> **Drift check (run first)**: `git diff --stat 63cc106..HEAD -- src/chile_hub/core.py src/chile_hub/data_manager.py src/chile_hub/exceptions.py pyproject.toml tests/test_core.py tests/test_chile_hub.py docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md docs/datasets/geometria_comunal.md`
> If source behavior differs from Current state, STOP rather than silently changing
> the API contract.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: Plan 064
- **Category**: direction / API
- **Planned at**: commit `63cc106`, 2026-07-26

## Why this matters

Users with GPS points, geocoded addresses, sensors, or field observations need an
official comuna CUT before joining hub data. The repository now has official,
license-cleared geometry but no public point-in-polygon API. This is the spatial
counterpart to Plan 050's name-to-CUT resolver.

The API must use a separately cached, integrity-verified candidate artifact. The
normal data manager downloads only the stable publishable bundle; pulling geometry
into it would violate the publication-track architecture and impose GIS libraries
on every consumer.

## Current state

- `src/chile_hub/core.py` exposes public Polars-returning methods such as
  `cross_view`, `search_datasets`, and `sql`, but no coordinate resolver.
- `src/chile_hub/data_manager.py` downloads, SHA-256-verifies, and extracts only
  the stable release bundle. It must not be repurposed to replace that bundle with
  a candidate artifact.
- `pyproject.toml:45-63` has `pipeline`, `query`, and `validation` extras.
  `shapely`/`geopandas` are build-time dependencies in `pipeline`, not a public
  consumer `geo` extra.
- `src/builders/geo.py` writes GeoParquet 1.0 (WKB, EPSG:4326). ADR-012 keeps it
  out of the daily generated catalog and requires direct-file access.
- Plan 064 provides the Pages artifact and its adjacent `.sha256` companion.
  That immutable pair is the required integrity contract for this API.

## Commands you will need

| Purpose | Command | Expected result |
|---|---|---|
| Optional geo environment | `uv sync --extra geo --extra dev --locked` | exit 0 |
| Build stable fixture data | `make build` | exit 0 |
| Core tests | `uv run pytest tests/test_core.py -v` | all pass |
| Cache/API tests | `uv run pytest tests/test_chile_hub.py -v -k "DataManager or resolve_by_coords"` | selected tests pass |
| Full regression | `make test` | exit 0 |
| Quality | `make lint && make format-check && make docs-coverage` | exit 0 |

## Scope

**In scope**:

- `pyproject.toml`, `uv.lock` — consumer-only `geo` extra.
- `src/chile_hub/geo.py` (create) — lazy download/cache, checksum verification,
  GeoParquet validation, and pure spatial helpers.
- `src/chile_hub/core.py` — `ChileHub.resolve_by_coords()`.
- `src/chile_hub/exceptions.py` only if `ChileHubDataError` cannot express the
  final failure clearly.
- `tests/test_core.py`, `tests/test_chile_hub.py`, ADR-012, geometry dataset docs,
  and `plans/README.md`.

**Out of scope**:

- Base `dependencies`; `data/dataset_catalog_config.json`; `Dataset` enum;
  `make extract`; `build_dev_db.py`; CLI; stable bundle/release workflows.
- Artifact publication and checksum creation (Plan 064),
  fuzzy matching, addresses, roads, or a map UI.

## Git workflow

- Branch: `advisor/065-coordinate-resolver`
- Commit: `feat(geo): agrega resolve_by_coords para comunas`
- Do not push or publish a package without explicit operator instruction.

## Steps

### Step 1: Freeze the distribution and cache contract

Read the completed Plan 064 workflow and documentation before writing code.
Record these decisions in ADR-012:

- the HTTPS GeoParquet URL;
- the adjacent `.sha256` URL and its digest/path parsing rules;
- a versioned cache directory under `platformdirs.user_cache_dir("chile-hub")`;
- default behavior: reuse a verified cache, refresh only with
  `refresh_geometry=True`; and
- offline/missing/checksum failure behavior.

The public method must not accept an unchecked arbitrary URL. It may accept a
keyword-only `geometry_path: Path | None` for offline and test use; the local file
must still pass structural GeoParquet validation.

**Verify**: `rg -n "SHA-256|cache|refresh_geometry|geometry_path" docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md` → all concepts appear.

### Step 2: Add a lazy, consumer-only geo extra

Add `geo` under `[project.optional-dependencies]`, separate from `pipeline`, with
the smallest compatible set needed for GeoParquet reading and point-in-polygon
work (expected: geopandas, shapely, and pyarrow if required). Keep existing
pipeline dependencies intact and regenerate `uv.lock` using the normal uv flow.

Import geo libraries only inside the new geo module or its helpers. Without them,
`resolve_by_coords()` must raise `ImportError` containing exactly
`pip install chile-hub[geo]`, following `ChileHub.sql()`'s lazy-extra pattern.

**Verify**: `uv sync --extra geo --extra dev --locked` → exit 0; an import-mocked
test proves `ChileHub()` construction does not import geopandas and method use
without the extra gives the specified error.

### Step 3: Implement verified artifact acquisition and validation

Create `src/chile_hub/geo.py`; keep network/spatial details out of `core.py`.
Implement helpers that:

1. fetch and parse the Plan 064 `.sha256` companion before accepting a download;
2. download atomically to a temporary sibling file, calculate SHA-256, and
   replace the cache only when it equals the descriptor digest;
3. preserve any previous verified cache on failed download or bad checksum;
4. validate GeoParquet: geometry column, EPSG:4326, string-like five-character
   `codigo_comuna`, no duplicate CUT, at least 340 non-empty geometries; and
5. expose a pure function taking an already loaded GeoDataFrame plus points for
   network-free tests.

Use `ChileHubDataError` unless its existing semantics make the root cause unclear.
Do not reuse the stable bundle extractor because it replaces the normalized cache.

**Verify**: fixture tests prove a checksum mismatch leaves an existing cache
untouched, malformed GeoParquet raises a useful data error, and a valid local
fixture triggers no HTTP request.

### Step 4: Add the public coordinate resolver with a fixed contract

Add this method near the other data-access methods:

```python
def resolve_by_coords(
    self,
    points: list[tuple[float, float]],
    *,
    refresh_geometry: bool = False,
    geometry_path: Path | None = None,
) -> pl.DataFrame:
```

Each tuple is `(latitud, longitud)`. Preserve input order and duplicates. Return
one row per input with exactly `input_lat`, `input_lon`, `codigo_comuna`,
`nombre_comuna`, and `matched`. Valid points outside Chile yield null comuna
fields and `matched=False`; latitude outside `[-90, 90]` or longitude outside
`[-180, 180]` raises `ValueError` naming the invalid input.

Use `geometry.covers(point)`, not `contains`, so boundary points match. If several
geometries cover a point, return the lexicographically smallest `codigo_comuna`
and emit a module-log warning; document this deterministic tie-break.

**Verify**: a Santiago-center point matches a five-character CUT; a sea point is
unmatched; a synthetic boundary fixture proves `covers`; duplicated input yields
duplicated output rows in the same order.

### Step 5: Document and test supported failure modes

Update geometry docs with `pip install "chile-hub[geo]"`, tuple order, output
schema, cache behavior, candidate/stable-bundle boundary, out-of-Chile behavior,
and the generalized-boundary precision disclaimer. Add the final cache, integrity,
and boundary decisions to ADR-012.

Model lazy-import tests on `ChileHubSQLTests`; model cache/SHA tests on current
data-manager unit tests. Use a tiny synthetic GeoParquet fixture, never the 5 MB
production artifact.

**Verify**: `make test && make lint && make format-check && make docs-coverage` → all exit 0.

## Test plan

- Known match, unmatched point, duplicate/order preservation, invalid coordinates,
  boundary match, and deterministic overlap handling.
- Lazy extra behavior and base-instantiation no-import behavior.
- Companion/download success, checksum mismatch cache preservation, offline use
  with a verified cache, offline failure without one.
- Structural failures: missing geometry/CRS, bad CUT width, duplicate CUT, too few rows.
- Complete suite, lint, formatting, and docs coverage.

## Done criteria

- [ ] Plan 064 is DONE; this plan uses its documented artifact/checksum contract.
- [ ] `geo` is optional and base dependencies/install behavior are unchanged.
- [ ] Remote artifacts are verified before replacing cache; bad data preserves cache.
- [ ] API returns the specified Polars schema and documented boundary behavior.
- [ ] Candidate geometry remains outside the stable catalog and publishable bundle.
- [ ] All tests and quality commands above exit 0.
- [ ] ADR and dataset docs specify cache, integrity, input, output, and precision behavior.

## STOP conditions

- No stable Pages artifact URL plus `.sha256` companion is available from Plan 064.
- Plan 064 has not successfully published and read back the artifact.
- Dependencies require a base-install change or violate the documented Python range.
- Structural validation fails on a known valid artifact or border policy is not deterministic.
- The design requires adding geometry to the stable bundle or generated catalog.

## Maintenance notes

The cache URL and checksum companion are a deliberate coupling to Plan 064; change
them together and preserve a migration path. Review coordinate order, lazy imports,
checksum-before-replace behavior, and the explicit non-cadastral precision limit.
