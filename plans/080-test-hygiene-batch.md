# Plan 080: Higiene de tests (red real, sleeps inefectivos, staleness, e2e)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- tests/test_core.py tests/test_chile_hub.py tests/test_extractors.py tests/test_validation.py tests/e2e/run_all.sh tests/e2e/verify_066.sh src/extractors/http_utils.py pyproject.toml Makefile`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW-MED
- **Depends on**: none
- **Category**: tests / dx
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

Cinco fricciones de tests medidas:
1. **~20s (29% de la suite) dependen de red real**: `check_sources` ×2
   (`test_core.py:366-373`, `test_chile_hub.py:1614-1618`) y el fetch live a
   BCN SIIT (`test_extractors.py:2356-2367`). El test de alcaldes falla si
   BCN está vivo pero entrega <340 filas.
2. **3 `@patch("tenacity.nap.sleep")` inefectivos** (`test_extractors.py:
   1557,1576,1598`): tenacity 9.1.4 captura `sleep` en import-time; los tests
   duermen 8s reales con el patch "activo".
3. **Staleness guard inconsistente**: `_assert_normalized_not_stale`
   (`test_chile_hub.py:68-101`) se llama solo en 3 de 9 clases; `test_core.py`
   (73 tests) y `ChileHubCliTests` pasan contra artefactos stale.
4. **`test_equivalencia_con_rutificador` skip permanente**
   (`test_validation.py:999`): `rutificador` no está en el venv.
5. **`tests/e2e/run_all.sh` no incluye `verify_066.sh`** (y los verify_NNN
   con aserciones de datos vivos se rompen con el tiempo).
6. **Makefile**: `verify` ≡ `verify-dev`, `verify-live` obsoleto, help de
   `test` engañoso.
7. **pytest-xdist declarado y nunca usado**.

## Current state

- Ver Current state de cada finding en el Why (evidencia con líneas).
- `src/extractors/http_utils.py:34-65` — `fetch_with_retry` usa
  `@retry(wait=wait_exponential(min=2, max=8))` con `sleep` default capturado.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_core.py tests/test_extractors.py tests/test_validation.py -q` | all pass |
| Timing | `time ./.venv/bin/pytest -q` | < 60s tras el plan |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**: los archivos listados en el drift check.
**Out of scope**: re-diseño de fixtures grandes; cambiar el contrato de
`check_sources` (solo mocks en tests).

## Steps

### Step 1: Mockear red en check_sources y alcaldes

Parchea `requests.head` con respuestas fake en los 2 tests de `check_sources`
(consolidando en uno si son redundantes); convierte el test de alcaldes a
fixture HTML/JSON sintético con N filas (el parseo se testea sin red). La
señal de liveness ya la cubre `source-urls.yml` (semanal).

**Verify**: `time ./.venv/bin/pytest tests/test_core.py tests/test_extractors.py -q` → baja ~20s.

### Step 2: Fix de los sleeps de tenacity

Añade parámetro `sleep` a `fetch_with_retry` y pásalo al `@retry` (tenacity
lo acepta como kwarg), o en los tests construye el `Retrying` manualmente con
`sleep=mock`. Verifica que `mock.call_count > 0` en un test.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "retry\|timeout"` → all pass, sin sleeps reales (medir).

### Step 3: Staleness guard en todas las clases

Llama `_assert_normalized_not_stale` en `setUpClass` de `test_core.py` y
`ChileHubCliTests` (moverlo a un helper compartido si es necesario).

**Verify**: suite completa verde con `make build` previo.

### Step 4: rutificador + e2e + Makefile

- `test_equivalencia_con_rutificador`: añade `rutificador` al extra `dev` o
  reemplaza el oráculo por una implementación DV inline (10 líneas).
- `run_all.sh`: añade `066` al array o congela los scripts en
  `plans/archive/` (decisión documentada — las aserciones de datos vivos se
  rompen con el tiempo).
- Makefile: elimina `verify-dev` o `verify`, elimina `verify-live`, corrige
  el help de `test`; prueba `pytest -n auto` y si pasa fíjalo en Makefile/CI
  (si no, elimina la dependencia xdist).

**Verify**: `make doctor` exit 0; suite completa verde; `time make test` < 60s.

## Done criteria

- [ ] Suite sin red real (los 3 tests mockeados)
- [ ] 8s de sleeps inefectivos eliminados
- [ ] Staleness guard en todas las clases con `data/normalized/`
- [ ] `test_equivalencia_con_rutificador` corre (no skip)
- [ ] `run_all.sh` coherente (066 incluido o scripts congelados)
- [ ] Makefile sin targets muertos/duplicados
- [ ] `plans/README.md` status row updated

## STOP conditions

- `pytest -n auto` rompe fixtures compartidos (revertir a serial y eliminar
  la dependencia — documentar).
- El fixture de alcaldes no puede construirse sin la respuesta real
  (el parseo depende de shape no documentado).

## Maintenance notes

- Los tests con red eran la única señal de liveness en la suite; la
  cobertura queda en `source-urls.yml` — mantenerlo como el gate semanal.
- La decisión e2e (incluir 066 vs congelar) debe documentarse en el commit
  con el razonamiento.
