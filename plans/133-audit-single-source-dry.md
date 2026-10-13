# Plan 133: Auditoría — extractores: fuente única (DRY) y descomposición

> **Executor instructions**: Sigue los pasos en orden. Los extractores
> alimentan datos publicados: cada step termina con tests de extractores
> verdes. Si algo de "STOP conditions" ocurre, detente y reporta. Actualiza tu
> fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- src/extractors/region_utils.py src/chile_hub/regions.py src/extractors/sinim_finanzas_extractor.py src/extractors/sinim_finanzas_live_extractor.py src/extractors/_sinim_shared.py src/extractors/autoridades_electas_extractor.py src/extractors/autoridades_locales_extractor.py src/extractors/estadisticas_vitales_extractor.py src/extractors/res_extractor.py src/extractors/permisos_edificacion_extractor.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M-L
- **Risk**: LOW-MED
- **Depends on**: 131 (B/C4/RUF en select; C901 disponible si 132 ya corrió)
- **Category**: refactor / DRY (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

La auditoría encontró tres duplicaciones reales en extractores (D1, D3, D4),
estado global mutable (C4) que el modelo `ExtractionResult` ya existe para
portar, y los god functions más grandes fuera del build: `_parse_comuna_sheet`
F61/186 L, `fetch_data` E40/143 L, `normalize_dpa` 195 L, `process_indicators`
D26, `_parse_sheet` (permisos) D28. Es la lógica que toca datos publicados:
cada duplicación que pueda divergir es un riesgo silencioso de joins.

## Current state

- D1 — `extractors/region_utils.py:29-64` replica `REGION_A_CODIGO` como
  fallback (`except ModuleNotFoundError`) del canónico en
  `chile_hub/regions.py:20-62` (pylint R0801). Determinar primero si el
  fallback es alcanzable (el idioma `sys.path` de extractores hace que
  `from src.chile_hub…` funcione al correr como script; ver §2½ de AGENTS).
- D3 — muestra fallback SINIM embebida dos veces:
  `sinim_finanzas_extractor.py:52:90` ≈ `sinim_finanzas_live_extractor.py:377:413`.
  `_sinim_shared.py` ya concentra normalización/metadata (Plan 099).
- D4 — `SCHEMA` duplicado: `autoridades_electas_extractor.py:76:97` ≈
  `autoridades_locales_extractor.py:70:91`.
- C4 — `global _LAST_FETCH_MODE` en `estadisticas_vitales_extractor.py:603` y
  `res_extractor.py:188`; `_LAST_SENTINEL_DROP_COUNT` en `res_extractor.py:323`.
  El modelo Phase 4 (`src/extractors/result.py`, `ExtractionResult`) existe
  para provenance/tiempo final.
- God functions (radon): `estadisticas_vitales_extractor.py:376`
  `_parse_comuna_sheet` F61; `:593` `fetch_data` E40;
  `permisos_edificacion_extractor.py:335` `_parse_sheet` D28;
  `bcentral_extractor.py:590` `process_indicators` D26; `subdere_extractor.py:454`
  `normalize_dpa` (195 L, C12 pero linealmente enorme).
- C901 quedó habilitado en 132e (umbral 35): ruff-mccabe **no** marca a estos
  extractores (radon sí: `_parse_comuna_sheet` 61, `fetch_data` 40), así que no
  hay noqa pendiente acá; el umbral se baja cuando este plan los descomponga.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Tests extractores | `./.venv/bin/pytest tests/test_extractors.py -q` | verde |
| Focal por clase | `./.venv/bin/pytest tests/test_extractors.py -q -k "<Nombre>"` | verde |
| Extractores en dry-run | `./.venv/bin/python src/extractors/<x>_extractor.py` (con staging/raw existentes) | sin excepción |
| Complejidad | `uvx radon@6.0.1 cc -s --min C src/extractors` | decreciente |
| Lint | `make lint` | exit 0 |

## Scope

**In scope**: los archivos del drift check + `src/extractors/result.py`
(consumo), tests de extractores relacionados.

**Out of scope**: cambiar contratos de staging (columnas, metadata), el fetch
efímero de CI, extractores sin hallazgos.

## Steps

### Step 0 — Baseline y modo standalone

`pytest tests/test_extractors.py` verde. Verificar el run standalone real de
un extractor (`python src/extractors/subdere_extractor.py` desde la raíz) y
documentar cómo resuelve imports; esto decide el Step 1.

### Step 1 — D1: una sola fuente para alias de regiones

- Si el fallback de `region_utils` es inalcanzable en modo soportado →
  eliminarlo y quedarse con el import canónico (la copia desaparece).
- Si es alcanzable (p. ej. ejecución sin raíz en `sys.path`) → dejarlo, pero
  **guardrail de igualdad**: test que compare `region_utils.REGION_A_CODIGO`
  con `chile_hub.regions.REGION_A_CODIGO` (y los alias de `text`) para que las
  copias no puedan divergir en silencio. Docstring con el incidente (audit
  2026-10-13).
- En ambos casos: test que normalice las 16 regiones por ambos caminos y
  compare códigos.

### Step 2 — D3: muestra SINIM en `_sinim_shared`

- Mover las filas de fallback a `_sinim_shared.FALLBACK_FINANZAS_ROWS` (o JSON
  embebido en el módulo compartido) e importarlas desde stub y live.
- Test existente de `_sinim_shared` (equivalencia stub/live, Plan 099) cubre
  la no-divergencia; extender si hace falta.

### Step 3 — D4: `SCHEMA` compartido de autoridades

- Nuevo módulo `src/extractors/autoridades_shared.py` con el `SCHEMA` común
  (y lo que ambos comparten); ambos extractores lo importan.
- Test: ambos salientes de staging conservan exactamente las columnas
  declaradas (test de extractores ya lo verifica; añadir comparación directa).

### Step 4 — C4: fuera los globales de estado

- Reemplazar `_LAST_FETCH_MODE`/`_LAST_SENTINEL_DROP_COUNT` por campos de
  `ExtractionResult` (o retorno explícito) en `estadisticas_vitales_extractor`
  y `res_extractor`; `write_staging(...)` ya recibe el result (Plan 125).
- Test: dos ejecuciones consecutivas con modos distintos no se contaminan
  (el bug que el global permite).

### Step 5 — Descomposición de god functions (orden por grade)

- `_parse_comuna_sheet`: extraer `_detect_group_row`, `_build_colmap`,
  `_iter_data_rows`; el layout por años queda como tabla de variantes.
- `fetch_data` (estadísticas): separar descubrimiento de documentos
  (`_discover_anuario_docs` ya existe), descarga y parseo.
- `_parse_sheet` (permisos), `process_indicators` (bcentral), `normalize_dpa`
  (subdere): extraer helpers por sección; `normalize_dpa` puede partirse en
  `fetch_*` + `normalize_*` ya existentes.
- Remover los `# noqa: C901  # 133` al terminar cada uno; radon sin E/F en
  `src/extractors`.

### Step 6 — Cierre

`pytest tests/test_extractors.py`, `make test`, `make lint`, `make doctor`;
`plans/README.md` actualizado.

## Test plan

- `tests/test_extractors.py` es el contrato por extractor; añadir los tests de
  Steps 1/4 (igualdad de alias, no contaminación de estado).
- Para los parsers: fixture de filas ya existente en los tests (reusar);
  los refactors son move-only y no deben cambiar salidas.

## Done criteria

- [ ] Sin R0801 entre los pares D1/D3/D4 (o guardrail de igualdad para D1)
- [ ] Sin `global _LAST_*` en `src/extractors`
- [ ] radon sin D/E/F nuevo; noqas `# 133` removidos
- [ ] Tests de extractores + suite + doctor verdes
- [ ] Fila del índice actualizada

## STOP conditions

- Si el fallback de `region_utils` resulta necesario y no hay forma de
  testear ambos caminos, deja la copia + guardrail de igualdad (no borrar a
  ciegas).
- Si mover la muestra SINIM cambia el resultado de un test de equivalencia,
  STOP y reportar el diff.
