# Plan 075: Acoplar valor y período en el regex del override INE

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/extractors/ine_ipc.py tests/test_extractors.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW-MED
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

El regex del override INE ancla el `<h1>` del IPC y captura el primer
`<p class="cifraV3">…%` siguiente con `[\s\S]*?` hasta el
`periodoCifraV3` con "Variación mensual". Si el INE reordena el layout y pone
otra tarjeta (variación anual, acumulada, de otro índice) entre el h1 del IPC
y su cifra mensual, el valor capturado puede ser el de otra tarjeta mientras
el período es el del IPC — un valor erróneo entra silenciosamente al dataset
y al bundle. El único freno (anomalías, Plan 074) está debilitado.

## Current state

- `src/extractors/ine_ipc.py:46-52` — `_PATTERN`:
  ```python
  _PATTERN = re.compile(
      rf"<h1[^>]*>[^<]*[ÍI]ndice\s+de\s+Precios\s+al\s+Consumidor[^<]*</h1>"
      rf"[\s\S]*?<p[^>]*class=\"[^\"]*\bcifraV3\b[^\"]*\"[^>]*>\s*(-?\d+(?:[,.]\d+)?)\s*%\s*</p>"
      rf"[\s\S]*?<p[^>]*class=\"[^\"]*\bperiodoCifraV3\b[^\"]*\"[^>]*>\s*Variaci[oó]n\s+mensual\s+"
      rf"({_MONTH_PATTERN})\s+(\d{{4}})",
      re.IGNORECASE,
  )
  ```
- Fixture real: `tests/fixtures/ine_ipc_page.html` (julio 2026, 0.1%).
- Tests: `tests/test_extractors.py:424-499` (`IneIpcExtractorTests`),
  incluido `test_parse_anchors_to_ipc_card_not_sibling_card`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests focal | `./.venv/bin/pytest tests/test_extractors.py -q -k "IneIpc"` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope**: `src/extractors/ine_ipc.py`, `tests/test_extractors.py`
**Out of scope**: el fetch (`fetch_ine_ipc`), la cadena multi-fuente (DIR-04).

## Steps

### Step 1: Restringe el span entre cifra y período

Reemplaza el `[\s\S]*?` entre `cifraV3` y `periodoCifraV3` por un span
acotado (p. ej. `[^<]{0,200}`) que impida saltar a otra tarjeta: el par debe
estar en el mismo bloque contenedor. Alternativa más robusta: parsear la
tarjeta completa (desde el h1 hasta el cierre de su contenedor) y extraer
cifra+período dentro de ese subárbol.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "IneIpc"` → all pass (fixture real sigue parseando 0.1%).

### Step 2: Tests adversariales con tarjetas reordenadas

En `tests/test_extractors.py` (`IneIpcExtractorTests`), agrega:
- `test_parse_rejects_mismatched_sibling_card` — HTML con h1 del IPC, luego
  la cifra de OTRA tarjeta, y luego el período mensual del IPC → el parser
  debe devolver el valor del IPC o `None`, nunca el valor ajeno.
- `test_parse_sibling_card_between_h1_and_value` — tarjeta hermana (ICT)
  intercalada entre el h1 y la cifra del IPC → sin falsos positivos.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "IneIpc"` → all pass (nuevos incluidos).

## Done criteria

- [ ] El regex no puede casar valor de una tarjeta con período de otra
- [ ] 2 tests adversariales pasan
- [ ] El fixture real sigue parseando 0.1% jul-2026
- [ ] Suite completa verde
- [ ] `plans/README.md` status row updated

## STOP conditions

- El span acotado rompe el parseo del fixture real (el layout actual tiene
  más de 200 chars entre cifra y período — medir antes).

## Maintenance notes

- Si el INE cambia el layout, este test adversarial es la primera alerta —
  no "arreglar" el test, revisar el patrón.
- La fragilidad estructural (publish diario depende de HTML externo) se
  documenta en DIR-04 (ADR multi-fuente).
