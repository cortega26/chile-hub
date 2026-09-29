# Plan 121: Lighthouse mide `performance` y deja reporte como artefacto (solo observación)

> **Executor instructions**: Sigue los pasos y verifica cada uno. Si algo de
> "STOP conditions" ocurre, detente y reporta. Actualiza tu fila en
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- scripts/run_lighthouse.sh scripts/check_lighthouse.py .github/workflows/pipeline-check.yml tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf / observabilidad
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

El job `landing` corre Lighthouse pero **sin la categoría `performance`** y el
JSON de reporte queda en `/tmp` del runner sin subirse. Resultado: no hay
baseline ni señal de regresión de peso (index.html 138 KB, app.js 84 KB,
`mapa_comunal.geojson` 604 KB, WASM de 39 MB on-demand). Cualquier trabajo
futuro de performance no tiene con qué justificarse. Este plan agrega la
categoría y publica el reporte como artefacto, **sin umbral bloqueante**
(scores de performance en runners compartidos son ruidosos).

## Current state

- `scripts/run_lighthouse.sh:21-28`:
  ```bash
  npx --yes lighthouse@12.8.2 "http://127.0.0.1:$PORT/" --quiet \
    --chrome-flags="--headless=new --no-sandbox --disable-gpu" \
    --output=json --output-path="$REPORT" \
    --only-categories=accessibility,seo,best-practices

  "$PYTHON_BIN" scripts/check_lighthouse.py "$REPORT"
  ```
  `REPORT="${LIGHTHOUSE_REPORT:-/tmp/chile-hub-lighthouse.json}"`.
- `scripts/check_lighthouse.py:22-26`:
  ```python
  DEFAULT_MIN_SCORES = {
      "accessibility": 100,
      "seo": 100,
      "best-practices": 100,
  }
  ```
  `check()` itera solo las categorías de `min_scores`; `performance` no está.
- `.github/workflows/pipeline-check.yml:549-550` — step `Lighthouse
  (accesibilidad, SEO, buenas prácticas)` → `bash scripts/run_lighthouse.sh`.
- `tests/test_ci_config.py:1485-1560` (`LighthouseGuardrailTests` y
  `CheckLighthouseScriptTests`) ya prueban umbrales y el script con un JSON
  sintético.
- Pin de upload-artifact usado en el repo:
  `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`
  (`pipeline-check.yml:445-448`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests focal | `./.venv/bin/pytest tests/test_ci_config.py -k "Lighthouse" -v` | declared | verde |
| Landing smoke | `make verify-landing` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `scripts/run_lighthouse.sh`
- `scripts/check_lighthouse.py`
- `.github/workflows/pipeline-check.yml` (job `landing`, solo el step de Lighthouse)
- `tests/test_ci_config.py`

**Out of scope**:
- Optimizar el sitio (este plan solo mide; los hallazgos se priorizan después).
- Volver `performance` bloqueante.
- Cambiar los umbrales 100 de a11y/SEO/best-practices.

## Git workflow

- Branch: `advisor/121-lighthouse-performance-baseline`
- Commit: `chore(ci): mide performance en Lighthouse y sube el reporte`
- No push/PR.

## Steps

### Step 0: Baseline

`./.venv/bin/pytest tests/test_ci_config.py -k Lighthouse -v` verde. Si no, STOP.

### Step 1: Categoría `performance`

- `run_lighthouse.sh:25-28`: agrega `performance` a `--only-categories`.
- `check_lighthouse.py`: agrega soporte de `--min-performance` **opcional**
  (default `None` = no umbral), e incluye el score de performance en el
  resumen impreso. Mantén el default de a11y/SEO/best-practices en 100.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "CheckLighthouse" -v`
→ verde tras actualizar/extender el test que corre el script con un JSON
sintético (agrega un caso con `performance` presente y otro sin él → error de
categoría faltante como hoy).

### Step 2: Artefacto y resumen en CI

En `pipeline-check.yml`, job `landing` (después del step de Lighthouse):

```yaml
      - name: Upload Lighthouse report
        if: always()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: lighthouse-report
          path: /tmp/chile-hub-lighthouse.json
          if-no-files-found: warn
          retention-days: 7
```

- Mantén el nombre exacto del paso de Lighthouse o actualiza los guardrails
  que lo referencian (grep `Lighthouse` en `tests/test_ci_config.py`).
- Opcional (si es simple): imprimir el score de performance en
  `$GITHUB_STEP_SUMMARY` desde `check_lighthouse.py` — no lo hagas si requiere
  reescribir la salida actual del script.

**Verify**: `grep -n "lighthouse-report" .github/workflows/pipeline-check.yml`
→ 1 match.

### Step 3: Guardrail

En `tests/test_ci_config.py`, extiende `LighthouseGuardrailTests`:
1. `run_lighthouse.sh` contiene `performance` en `--only-categories`.
2. `pipeline-check.yml` contiene `lighthouse-report` + `actions/upload-artifact`.
3. Docstring: por qué se mide sin umbral (varianza del runner).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k Lighthouse -v` → verde.

## Test plan

- `CheckLighthouseScriptTests` cubre el JSON sintético (agrega `performance`).
- Guardrail de texto para el workflow.
- `make verify-landing` sigue verde (no cambia el sitio).

## Done criteria

- [ ] `grep -n "performance" scripts/run_lighthouse.sh` → en `--only-categories`
- [ ] `grep -n "lighthouse-report" .github/workflows/pipeline-check.yml` → 1
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -k Lighthouse -v` → verde
- [ ] `make verify-landing` → exit 0
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Si Lighthouse 12.8.2 no soporta `performance` en `--only-categories` (poco
  probable), STOP y reporta.
- Si el check actual ya corre `performance` por otro flag, no dupliques.
- Si `if: always()` en el upload rompe algún guardrail de la suite, reporta.

## Maintenance notes

- Con `performance` sin umbral, la señal es el artefacto: revisarlo cuando se
  proponga trabajo de peso en la landing. Si en 2-3 meses la varianza en CI es
  baja, abrir un plan para fijar un umbral conservador (p. ej. 90).
- **Deferred:** métricas P50/LCP en el step summary y presupuesto de bytes por
  asset — requieren historial estable; reevaluar con el artefacto acumulado.
