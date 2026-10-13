# Plan 131: Auditoría P0 — correctitud y quick wins

> **Executor instructions**: Sigue los pasos en orden (un commit por step).
> Si algo de "STOP conditions" ocurre, detente y reporta. Al terminar,
> actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- src/extractors/sinim_finanzas_live_extractor.py src/chile_hub/core.py src/extractors/bcentral_extractor.py src/extractors/res_extractor.py src/extractors/mineduc_establecimientos_extractor.py src/extractors/mineduc_resultados_extractor.py pyproject.toml`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P1
- **Effort**: S-M
- **Risk**: LOW-MED
- **Depends on**: none (precede a 132–139)
- **Category**: calidad / correctitud (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

La auditoría de prácticas (`docs/best-practices-audit-2026-10-13.md`) encontró
correctitud barata de arreglar y un batch de modernización mecánica. C1 es un
bug latente real (closure sobre variable de loop); C2 silencia datasets sin
Parquet; el resto es deuda acumulada con fix acotado. Este plan además habilita
el primer trinquete de ruff que los planes siguientes asumen.

## Current state

- C1 — B023 ×2: `sinim_finanzas_live_extractor.py:301,303`; `_extract_number`
  cierra sobre `cells` (variable de loop).
- C2 — `core.py:589` — `except Exception: pass` al registrar vistas SQL
  ("Skip datasets whose Parquet isn't available").
- C5 — B904 ×11: `publish_hf_dataset.py:233`, `builders/metadata.py:79`,
  `core.py:137,321,325,578,636,696`, `chile_hub/datasets.py:67`,
  `estadisticas_vitales_extractor.py:400`, `res_extractor.py:226`.
- C6 — DTZ011 ×3 (`bcentral_extractor.py:505,510`; `res_extractor.py:190`);
  PLW1510 ×2 (`mineduc_establecimientos_extractor.py:87`,
  `mineduc_resultados_extractor.py:182`).
- C7 — ISC004 ×14 (p. ej. `core.py:716`, `doc_sync.py:433`,
  `check_landing_sync.py:65,73,131`, `pipeline_status_utils.py:989`).
- Batch mecánico: RUF100 ×40 (noqa obsoletos), UP017 ×40 (`timezone.utc`),
  UP015 ×31, C420 ×14, SIM auto-fixables, B905 ×5.
- Config actual: `[tool.ruff.lint] select = ["E","W","F","I"]`,
  `ignore = ["E501","E402"]` (pyproject).

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Focal extractores | `./.venv/bin/pytest tests/test_extractors.py -q -k "Sinim or Vitales or Res or Mineduc"` | verde |
| Suite completa | `make test` | verde |
| Lint/format | `make lint && make format-check` | exit 0 |
| Doctor | `make doctor` | exit 0 |
| Scan focal | `./.venv/bin/ruff check --no-cache --select B023,B904,B905,DTZ011,PLW1510,ISC004 src scripts` | 0 hallazgos al final |

## Scope

**In scope**: fixes C1–C7, batch `--fix` de modernización, config de ruff
(primer trinquete) y su guardrail.

**Out of scope**: descomposiciones de god functions (132/133/134/136), PTH
(138), C901 (132), B019 (lo arregla 134; aquí solo se ignora documentado).

## Steps

### Step 0 — Baseline

`make test` + `make lint` verdes. Si no, STOP.

### Step 1 — C1: parametrizar `cells` (commit `fix(extractores): …`)

- Pasar `cells` como parámetro explícito de `_extract_number`
  (`def _extract_number(cells, cell_index)`) o ligarlo por default-arg; soltar
  el closure.
- Test de regresión en `tests/test_extractors.py` (clase del extractor):
  construir dos filas distintas y verificar que cada llamada extrae su propia
  fila (el patrón anterior devolvía la última si se posponía la llamada).

### Step 2 — C2: warning explícito en registro SQL

- Reemplazar el `pass` por acumulación de `skipped: list[str]` y
  `warnings.warn(...)` una vez por conexión (sin cambiar el comportamiento
  funcional: las vistas ausentes se siguen omitiendo).
- Test: dataset sin Parquet → `pytest.warns`/`assertWarns` y la consulta
  sigue funcionando para los presentes.

### Step 3 — C5: `raise … from`

- En los 11 sitios B904, añadir `from exc` (o `from None` donde el contexto no
  aporte), preservando mensajes.

### Step 4 — C6: UTC y `subprocess`

- `date.today()` → `datetime.now(timezone.utc).date()` (o `datetime.UTC` si
  UP017 ya corrió) en los 3 sitios; verificar que la semántica de ventanas de
  fechas no cambie respecto de CLT (documentar en el commit si cambia el día
  de corte).
- Los 2 `subprocess.run` sin `check`: añadir `check=False` explícito y manejar
  `returncode` (o `check=True` con try/except) según el uso real; documentar.

### Step 5 — C7: parentizar ISC004

- Para cada uno de los 14, envolver la concatenación implícita en paréntesis
  (intención explícita, mismo resultado). Si alguno resulta ser una coma
  faltante real, es un bug: arreglarlo y mencionarlo en el commit.

### Step 6 — Batch mecánico

- `ruff check --fix` para RUF100, UP017, UP015, C420 y demás UP auto-fixables;
  revisar el diff (debe ser cosmético) y dejar fuera lo que cambie semántica.
- B905 ×5: `zip(..., strict=True/False)` explícito.

### Step 7 — Trinquete de ruff (config + guardrail)

- `select` += `"B", "C4", "RET", "RUF", "SIM", "UP"`.
- `ignore` += `"COM812"` (incompatible con el formatter), `"RUF001","RUF002",
  "RUF003"` (unicode intencional en docstrings/salidas), `"B019"` (fuga de
  `lru_cache` en métodos: se elimina en 134). Mantener `E501`, `E402` con
  comentario existente/justificación.
- Si quedarán >10 offenders no auto-fixables de SIM/RET, dejar esas reglas
  fuera y anotarlo como trinquete de 2 pasos (no forzar).
- Guardrail en `tests/test_ci_config.py`: test que exija estas claves en
  `select`/`ignore` con docstring del incidente ("el audit encontró gates
  estrechos; el trinquete evita volver a E,W,F,I sin decisión").

### Step 8 — Cierre

`make lint && make format-check && make test && make doctor`;
actualizar `plans/README.md`.

## Test plan

- Regresión específica por C1/C2 (los únicos con lógica).
- Suite completa + lint con el select ampliado.

## Done criteria

- [ ] Scan focal (Comandos) en 0 hallazgos
- [ ] `make lint`/`make test`/`make doctor` verdes con el select ampliado
- [ ] Guardrail del trinquete en `test_ci_config.py`
- [ ] Fila del índice actualizada

## STOP conditions

- Si un `--fix` de UP/RUF cambia semántica (revisar diff), revertir ese fix y
  listar los casos.
- Si los cambios de fecha (C6) alteran el resultado de tests de frescura,
  STOP y reportar (ventana CLT vs UTC).
