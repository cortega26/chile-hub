# Plan 118: `estadisticas_vitales` descarga solo los anuarios faltantes (incremental como RES)

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/extractors/estadisticas_vitales_extractor.py tests/test_extractors.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S-M
- **Risk**: MED
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`estadisticas_vitales` re-descarga y re-parsea **todos** los anuarios
definitivos del INE en cada corrida del pipeline diario. En el log del
schedule 2026-09-29 (`run 36596507138`) ese extractor tardó ~89 s, ~57% del
paso de extracción completo; descarga ~14 XLSX (~28 MB) aunque el staging ya
tenga esos años, y `data/raw/` acumula snapshots idénticos (3 copias de cada
año en 11 días; ese directorio viaja en el cache de staging de CI). `RES` ya
implementó el patrón incremental (Plan 076 DONE,
`res_extractor.py:122-143,188-215`): este plan lo replica.

Regla de negocio: INE puede **republicar** un anuario histórico corregido
(poco frecuente). La política será: re-descargar siempre el año más reciente
descubierto + los años ausentes del staging; el resto se conserva. Un refresh
total queda disponible por variable de entorno para mantenimiento.

## Current state

- `src/extractors/estadisticas_vitales_extractor.py`
  - `:557-580` `fetch_data()` descubre anuarios y crea `jobs` con
    `preset_path=None` para todos (siempre descarga):
    ```python
    jobs: list[tuple[int, str, str, Path | None]] = [
        (year, title, url, None) for (year, title, url) in anuarios
    ]
    ```
  - `:600-625` por job: `_download_xlsx(url, year)` o snapshot local si falla.
  - `:729-742` `process_estadisticas_vitales()` normaliza `rows` y escribe
    `STAGING_CSV_PATH` completo (sin merge).
  - `:760-778` `write_staging` del `BaseExtractor` (path no-dry, usado solo
    por `run()`; no tocar aquí).
- Patrón de referencia: `src/extractors/res_extractor.py:122-143`
  (`_staging_years_present()` con `pl.scan_csv(...).select("anio")`) y
  `:188-215` (selección de recursos + `_LAST_FETCH_MODE` + degradación a full
  si el naming cambió).
- Tests del extractor: `tests/test_extractors.py` tiene una clase para vitales
  (grep `class .*Vitales`); los tests corren `run(dry_run=True)` y stubean
  `fetch_data`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests extractor | `./.venv/bin/pytest tests/test_extractors.py -v -k vitales` | declared | verde |
| Tests validación | `./.venv/bin/pytest tests/test_validation.py -v -k vitales` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |
| Build (si hay staging) | `make build` | declared | exit 0 |

## Scope

**In scope**:
- `src/extractors/estadisticas_vitales_extractor.py`
- `tests/test_extractors.py` (clase de vitales)

**Out of scope**:
- `FALLBACK_ROWS` / semántica de fallback (no cambia).
- El metadata schema / `build_metadata` (no cambia; solo se enriquecen `notes`).
- Los tests de `run(dry_run=True)` (siguen igual).

## Git workflow

- Branch: `advisor/118-vitales-incremental-fetch`
- Commits: `perf(vitales): descarga incremental de anuarios` (estilo Plan 076:
  `git log --oneline --grep="incremental"` muestra el precedente RES).
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_extractors.py -v -k vitales` verde. Si no, STOP.
Mide el baseline local si tienes staging: la primera corrida completa no debe
cambiar de comportamiento.

### Step 1: Helper de años presentes en staging

Agrega en el extractor, junto a las constantes de paths:

```python
def _staging_years_present() -> set[int] | None:
    """Años en el staging consolidado (columna `anio`); None si no se puede leer."""
    if not os.path.exists(STAGING_CSV_PATH):
        return None
    try:
        years = (
            pl.scan_csv(STAGING_CSV_PATH, infer_schema_length=0)
            .select("anio")
            .unique()
            .collect()["anio"]
            .cast(pl.Int32, strict=False)
            .to_list()
        )
    except Exception:
        return None
    return {y for y in years if y is not None}
```

Copia el patrón exacto de `res_extractor.py:122-143` (incluido el
`except Exception` que degrada a full).

### Step 2: Selección incremental en `fetch_data`

- Agrega el parámetro `force_full: bool = False` (o lee
  `os.environ.get("CHILE_HUB_VITALES_FULL") == "1"`; elige una — se sugiere el
  env porque `Makefile` invoca `process_*` sin args).
- Tras descubrir `anuarios` y antes de construir `jobs`:

```python
    present = None if force_full else _staging_years_present()
    if present is None:
        jobs = [(y, t, u, None) for (y, t, u) in anuarios]
        fetch_mode = "full"
    else:
        latest = max((y for (y, _t, _u) in anuarios), default=None)
        jobs = [
            (y, t, u, None)
            for (y, t, u) in anuarios
            if y not in present or y == latest
        ]
        fetch_mode = "incremental"
        notes.append(
            f"fetch incremental: {len(jobs)} de {len(anuarios)} anuarios "
            f"(faltantes + año más reciente {latest})"
        )
```

- Si `jobs` queda vacío (no debería, el último año siempre entra), degrada a
  full con nota — igual que RES.

**Verify**: con un staging sintético de 3 años y `anuarios` de 4,
`jobs` contiene solo los 2 años que corresponden (el que falta + el máximo).

### Step 3: Merge en `process_estadisticas_vitales`

El write actual (`:735-739`) escribe solo lo fetcheado. Cámbialo por:

```python
    df_new = normalize_rows(rows)
    if fetch_mode == "incremental" and os.path.exists(STAGING_CSV_PATH):
        prev = pl.read_csv(
            STAGING_CSV_PATH,
            schema_overrides={c: pl.String for c in REQUIRED_COLUMNS},
        )
        fetched_years = sorted(df_new["anio"].unique().to_list())
        prev = prev.filter(~pl.col("anio").is_in(fetched_years))
        df = pl.concat([prev, df_new], how="diagonal_relaxed").sort(
            ["anio", "codigo_comuna", "sexo"]
        )
    else:
        df = df_new
```

- Mantén los dtypes de `REQUIRED_COLUMNS` como hoy (revisa el `normalize_rows`
  para el orden/columnas exactos; `anio` es `Int32`/`Int64`).
- `record_count` y metadata se recalculan sobre `df` (merge), como hoy.
- El sort debe dejar la misma salida que un fetch full (comparar con un
  staging de prueba): si el orden difiere, ajusta el sort para reproducirlo.

**Verify**: con un staging de prueba de 2 años y un fetch simulado de 1 año
nuevo, el CSV resultante tiene las filas de los 3 años y
`metadata.record_count == len(df)`.

### Step 4: Tests

En la clase de vitales de `tests/test_extractors.py`:

1. `test_fetch_incremental_descarga_solo_faltantes_y_ultimo`: mockea
   `_discover_anuario_docs` (4 años) y `_download_xlsx` (contador); con staging
   temporal que tiene 2 de los 4 años, afirma que se descargan exactamente los
   2 que faltan + el máximo (si el máximo ya está, se re-descarga).
2. `test_process_merge_preserva_años_no_fetcheados`: staging con años 2020-2021;
   fetch simulado de 2022 con 2 filas; el CSV final tiene 3 años y el metadata
   cuenta el total.
3. `test_sin_staging_fetch_completo`: sin CSV, se descargan todos (no regresión).
4. `test_staging_corrupto_degrada_a_full`: CSV ilegible → todos.

Usa `tempfile.TemporaryDirectory` + `patch.object` de las constantes de path
(`STAGING_CSV_PATH`) — el patrón ya existe en la clase.

## Test plan

- 4 tests nuevos (arriba) + los existentes verdes.
- Patrón estructural: la clase de vitales en `tests/test_extractors.py` y los
  tests incrementales de RES (`-k res`).
- Verificación: `./.venv/bin/pytest tests/test_extractors.py -v -k vitales` →
  verde; si hay staging local, `make extract && make build` no debe cambiar el
  CSV publicado más allá de filas nuevas (diff de conteos).

## Done criteria

- [ ] `./.venv/bin/pytest tests/test_extractors.py -v -k vitales` → verde (con ≥4 tests nuevos)
- [ ] `grep -n "_staging_years_present\|incremental" src/extractors/estadisticas_vitales_extractor.py` → helper + rama presentes
- [ ] `grep -c "CHILE_HUB_VITALES_FULL" src/extractors/estadisticas_vitales_extractor.py` → 1
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si `normalize_rows` no garantiza tipos estables para `pl.concat`, detente y
  reporta las columnas incompatibles en vez de forzar casts silenciosos.
- Si el orden canónico del CSV cambia de forma que `verify_pipeline`/contratos
  fallen, STOP (compara contra el CSV committeado antes de tocar el sort).
- Si el INE usa un naming de años que no puedes parsear del descubrimiento
  (`anio` en el título), degrada a full con nota y reporta.

## Maintenance notes

- Política de revisión de históricos: un anuario histórico corregido por el
  INE **no** se detecta con este plan. Correr
  `CHILE_HUB_VITALES_FULL=1 python src/extractors/estadisticas_vitales_extractor.py`
  una vez al año (o al detectar una revisión) — anotarlo en
  `docs/extraction-lanes.md`.
- El `data/raw/` seguirá acumulando snapshots de los años re-descargados; el
  ahorro principal es de ancho de banda/tiempo, no de limpieza de raw (raw es
  append-only por invariante).
- **Deferred:** poda de snapshots raw duplicados por año (rompe la invariante
  de append-only; decisión del mantenedor).
