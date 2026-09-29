# Plan 125: Consolidar `write_staging` en `BaseExtractor` (helper único, CSV atómico, metadata canónica)

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- src/extractors/base.py src/extractors/ tests/test_extractors.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW-MED
- **Depends on**: none (soft: Plan 123 cubre el merge de calidad_aire, uno de los overrides)
- **Category**: tech-debt
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`BaseExtractor.write_staging` es abstracto (`base.py:100-102`) y **las 22
subclases lo reimplementan** con tres contratos distintos de metadata y con
`df.write_csv(...)` directo al path final (no atómico), mientras
`write_staging_metadata` sí es atómico. Ejemplos:
- 13 overrides pasan la metadata sin tocarla (`salud_extractor.py:141`,
  `partidos_politicos_extractor.py:288`, …).
- 4 agregan `{dataset, fields, record_count, reuse_policy}` sin
  `refreshed_at_utc` (`bcentral_extractor.py:579`, `censo_hogares…:74`,
  `res_extractor.py:376`, `subdere_extractor.py:667`).
- 5 agregan `{dataset, record_count, refreshed_at_utc}` sin `fields`
  (`pobreza_extractor.py:343`, `calidad_aire…:525`, `consumo_electrico…:362`,
  `estadisticas_vitales…:766`, `permisos_edificacion…:641`).

Un cambio de contrato de staging hoy requiere 22 ediciones en lockstep; un
crash a mitad de `write_csv` deja staging parcial; y el path real de `run()`
no-dry no está cubierto por tests (solo `run(dry_run=True)`).

## Current state

- `src/extractors/base.py:28-48` — `write_staging_metadata(path, metadata)`
  atómico (tmp + `os.replace`).
- `src/extractors/base.py:100-117`:
  ```python
      @abstractmethod
      def write_staging(self, df: pl.DataFrame, metadata: dict[str, Any]) -> Path:
          """Persiste el dataset normalizado y sus metadatos en staging."""

      def run(self, dry_run: bool = False, **kwargs: Any) -> dict[str, Any]:
          ...
          validation = self.validate(df, metadata)
          if not dry_run:
              self.write_staging(df, metadata)
  ```
- `grep -rln "def write_staging" src/extractors/ | wc -l` → 23 (base + 22
  subclases, incluida la neutralizada CEAD).
- `write_staging` **no se usa en la ruta diaria**: los `process_*()` escriben
  directo (`df.write_csv(STAGING_CSV_PATH)` + `write_staging_metadata`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests extractores | `./.venv/bin/pytest tests/test_extractors.py -v` | declared | verde |
| Suite de pipeline | `./.venv/bin/pytest tests/test_pipeline_logic.py -v -k "extract"` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |
| Typecheck | `make typecheck` | declared | exit 0 |

## Scope

**In scope**:
- `src/extractors/base.py` (helper nuevo)
- Las 22 subclases con `write_staging` (solo el cuerpo del método)
- `tests/test_extractors.py` (test del helper + contrato)

**Out of scope**:
- Refactor de los `process_*()` de la ruta diaria (grande y riesgoso; se deja
  como Deferred).
- Cambiar paths de staging o schemas de CSV.
- `run()` semántica más allá de usar el helper.

## Git workflow

- Branch: `advisor/125-consolidate-write-staging`
- Commits por lote: `refactor(extractors): consolida write_staging en BaseExtractor`
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_extractors.py -v` verde. Si no, STOP.

### Step 1: Helper en `BaseExtractor`

Agrega en `base.py` (junto a `write_staging_metadata`):

```python
def write_staging_csv_atomic(df: pl.DataFrame, csv_path: str, metadata_path: str,
                             metadata: dict[str, Any]) -> Path:
    """Escribe CSV (tmp + os.replace) y metadata canónica en staging.

    Campos canónicos que siempre se completan/sobrescriben:
    dataset, refreshed_at_utc, record_count, fields (columnas del frame).
    El resto del dict pasa intacto.
    """
    merged = {
        **metadata,
        "dataset": metadata.get("dataset"),
        "refreshed_at_utc": metadata.get("refreshed_at_utc")
        or datetime.datetime.now(datetime.UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
    }
    csv = Path(csv_path)
    tmp = csv.with_suffix(csv.suffix + ".tmp")
    df.write_csv(tmp)
    os.replace(tmp, csv)
    write_staging_metadata(metadata_path, merged)
    return csv
```

Ajusta imports de `base.py` (`datetime`, `Path`, `os` — verifica cuáles ya
están). El helper es de módulo (como `write_staging_metadata`), no método, para
que los overrides lo importen igual que hoy importan `write_staging_metadata`.

### Step 2: Convertir overrides estándar

Convierte cada override cuyo cuerpo sea: `ensure_staging_directories()` +
`df.write_csv(...)` + merge de metadata + `write_staging_metadata(...)` a una
llamada al helper. Método esperado por clase:

```python
    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        return write_staging_csv_atomic(df, STAGING_CSV_PATH, METADATA_PATH, metadata)
```

Lista de partida (verifica cada cuerpo antes de convertir; si uno escribe
varios archivos o un formato distinto, **déjalo y anótalo en el PR**):

`bcentral_extractor.py:579`, `calidad_aire_extractor.py:525`,
`censo_extractor.py:168`, `censo_hogares_viviendas_extractor.py:74`,
`consumo_electrico_extractor.py:362`, `electoral_extractor.py:356`,
`estadisticas_vitales_extractor.py:766`,
`geometria_comunal_extractor.py:368`, `mineduc_establecimientos_extractor.py:227`,
`mineduc_resultados_extractor.py:276`, `partidos_politicos_extractor.py:288`,
`pobreza_extractor.py:343`, `res_extractor.py:376`, `salud_extractor.py:141`,
`siedu_extractor.py:357`, `subdere_extractor.py:667`,
`permisos_edificacion_extractor.py:641`,
`autoridades_electas_extractor.py:384`, `autoridades_locales_extractor.py:626`,
`sinim_finanzas_extractor.py:153`, `sinim_finanzas_live_extractor.py:473`.
(CEAD neutralizado y `base.py` abstracto quedan fuera.)

- Mantén las firmas exactas.
- Si un override usa una función de metadata propia (`write_metadata`, etc.),
  pásala por el dict antes de llamar al helper o deja el override; no mezcles.

### Step 3: Guardrail de no-divergencia

En `tests/test_extractors.py` agrega:
1. `test_write_staging_csv_atomic_writes_atomic_and_canonical`: escribe un
   frame a un tmpdir, afirma CSV + metadata con los 4 campos canónicos, y que
   no queda `.tmp`.
2. `test_all_write_staging_overrides_use_helper`: con `ast`, recorre los
   archivos de `src/extractors/*.py`, encuentra los `def write_staging` y
   afirma que su body llama a `write_staging_csv_atomic` **o** está en una
   lista explícita de excepciones documentadas (define la lista en el test con
   comentario por cada excepción).

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -v -k "write_staging"` → verde.

### Step 4: Cierre

`make lint`, `make format-check`, `make typecheck`, suite de extractores
completa. Actualizar índice.

## Test plan

- 2 tests nuevos (helper atómico + guardrail AST).
- Los tests existentes de extractores (dry-run) deben quedar intactos.
- Verificación: `./.venv/bin/pytest tests/test_extractors.py -v` completo.

## Done criteria

- [ ] `grep -c "def write_staging" src/extractors/*.py | awk -F: '{s+=$2} END {print s}'` → mismo número de métodos, pero ≥15 llaman al helper
- [ ] `grep -L "write_staging_csv_atomic" $(grep -rl "def write_staging" src/extractors/)` → solo excepciones documentadas
- [ ] `./.venv/bin/pytest tests/test_extractors.py -v` → verde
- [ ] `make typecheck` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si un override construye metadata con semántica que el helper rompería
  (p. ej. `source_mode` condicional), déjalo y lístalo como excepción; no
  fuerces la conversión.
- Si `df.write_csv(tmp)` con `with_suffix` choca con paths que ya terminan en
  `.tmp` u otro formato, usa `csv.parent / (csv.name + ".tmp")` (el patrón del
  repo).
- Si algún test existente mockea `write_csv` verificando el path final y se
  rompe, actualízalo solo si el contrato nuevo (tmp → replace) es el correcto;
  si no, STOP.
- Si `subdere_extractor` escribe múltiples CSV, no lo conviertas (excepción).

## Maintenance notes

- El helper es el único lugar donde se define la metadata canónica de staging;
  cualquier campo obligatorio nuevo (AGENTS §4.4) se agrega ahí.
- La ruta diaria (`process_*`) sigue escribiendo directo: el mismo crash
  puede dejar CSV parcial ahí. Migrarla es el follow-up real, con test de
  idempotencia por dataset.
- **Deferred:** migrar los `process_*()` al helper (M-L; 22 funciones, algunas
  con lógica de merge propia como calidad_aire/vitales). Requiere el Plan 123
  como red para el merge incremental.
