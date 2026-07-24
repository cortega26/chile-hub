# Plan 052: Señal de adopción — descargas PyPI + GitHub Releases en un badge/artefacto

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de avanzar. Si ocurre algo de
> "STOP conditions", detente y reporta — no improvises. Al terminar, actualiza la fila
> de estado en `plans/README.md`.
>
> **Restricción ética dura**: este proyecto es de datos abiertos y su modelo de valor
> descansa en no encerrar nada. **Cero telemetría en el artefacto distribuido** (la
> librería instalada y el bundle NO deben "llamar a casa"). Todas las métricas de este
> plan se leen desde **APIs públicas de plataforma** (PyPI, GitHub) en CI, nunca desde
> código que corre en la máquina del usuario. Si te ves agregando tracking al paquete,
> **para** (STOP condition).
>
> **Drift check (córrelo primero)**:
> `git diff --stat 7ebf94b..HEAD -- scripts/generate_coverage_badge.py .github/workflows/monthly-scrape.yml README.md`
> Si algo cambió, compara los excerptos de "Estado actual" contra el código vivo antes
> de continuar; ante discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `7ebf94b`, 2026-07-14

## Why this matters

El proyecto tiene un círculo vicioso documentado: el anti-patrón #10 (`AGENTS.md:714`)
prohíbe sumar datasets *"hasta que los existentes tengan señales de adopción
documentadas (descargas, issues con casos de uso, menciones externas)"*, y
`docs/backlog/NEXT_STEPS.md:31` pide *"monitorear descargas PyPI… medir qué datasets se
usan realmente para priorizar mejoras"* — **pero nada mide la adopción de la ruta
principal**. La landing tiene analítica sin cookies (`app.js:8`, GoatCounter), pero eso
sólo cubre descargas desde la página; la vía real de consumo — instalación PyPI y el
bundle ZIP en GitHub Releases (`docs/backlog/08-evaluacion-producto-comercial.md:26`) —
no se mide en ningún lado. Sin esta señal, las dos ideas de dataset restantes
(`plus-codes`, `entrepreneurship`, ambas `needs-research` y gated en demanda en
`docs/dataset-ideas/README.md`) no tienen criterio de desbloqueo.

Este plan cierra el hueco con el patrón **más barato y compatible con la ética**: un
script que lee estadísticas públicas de PyPI y GitHub en CI y las publica como un
artefacto JSON + un badge, exactamente como el proyecto ya hace con cobertura y
frescura.

## Current state

- `scripts/generate_coverage_badge.py` — **el modelo exacto a seguir**. Un script
  stdlib que produce un JSON de shields.io endpoint en `data/normalized/`:
  ```python
  # scripts/generate_coverage_badge.py:37-44
  return {
      "schemaVersion": 1,
      "label": "coverage",
      "message": f"{coverage_pct}%",
      "color": color,
      "namedLogo": "pytest",
      "cacheSeconds": 3600,
  }
  # ...
  BADGE_PATH.write_text(json.dumps(badge, ensure_ascii=False) + "\n", encoding="utf-8")
  ```
  Existe también `scripts/generate_freshness_badge.py` con el mismo patrón.

- `README.md:20-21` — cómo se consumen esos badges (shields endpoint sobre el hosting
  estático):
  ```
  [![Coverage](https://img.shields.io/endpoint?url=https://tooltician.com/chile-hub/data/normalized/coverage_badge.json)](...)
  [![Data](https://img.shields.io/endpoint?url=https://tooltician.com/chile-hub/data/normalized/freshness_badge.json)](...)
  ```
  El repo GitHub es `cortega26/chile-hub` (ver `README.md:17`, badge de CI/CD).

- `.github/workflows/monthly-scrape.yml` — **el modelo del workflow programado que
  commitea artefactos**: `permissions: contents: write`, cron, y un paso de commit
  tolerante a "sin cambios":
  ```yaml
  # monthly-scrape.yml:85-90
  if git diff --staged --quiet; then
    echo "No changes to commit"
  else
    git commit -m "chore(data): monthly SINIM scrape refresh [skip ci]"
    git push
  fi
  ```

- Artefactos servidos: `.gitignore:7-11` reabre `data/normalized/*.json`, así que un
  `adoption*.json` commiteado ahí se sirve en Pages automáticamente.

Convenciones:

- `src/builders/doc_sync.py` es **100% stdlib** a propósito (§12 `AGENTS.md`). Mantén
  este script igual: usa `urllib.request` de stdlib, **sin nuevas dependencias**.
- Los scripts leen/escriben paths relativos a `__file__` (invariante #5), como hace
  `generate_coverage_badge.py:14-16`. Replica ese patrón.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Correr el script (offline con fixture) | `./.venv/bin/python scripts/fetch_adoption_stats.py --offline tests/fixtures/adoption_sample.json` | escribe los JSON, exit 0 |
| Tests del parseo/badge (sin red) | `./.venv/bin/pytest tests/test_pipeline_logic.py -v -k adoption` | pasan |
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Validar YAML del workflow (si `yamllint`/`actionlint` no están, salta) | `./.venv/bin/python -c "import yaml;yaml.safe_load(open('.github/workflows/adoption-stats.yml'))"` | exit 0 |

## Scope

**In scope**:

- `scripts/fetch_adoption_stats.py` (crear) — lee PyPI + GitHub, escribe
  `data/normalized/adoption.json` y `data/normalized/adoption_badge.json`.
- `tests/fixtures/adoption_sample.json` (crear) — fixture para el modo offline y tests.
- `tests/test_pipeline_logic.py` — tests de parseo/construcción de badge (sin red).
- `.github/workflows/adoption-stats.yml` (crear) — workflow programado semanal.
- `README.md` — un badge nuevo consumiendo `adoption_badge.json` (junto a los badges
  existentes, líneas 20-24).
- `plans/README.md` — fila de estado.

**Out of scope** (NO tocar):

- El paquete (`src/chile_hub/**`) — **cero** instrumentación en el artefacto que corre
  en la máquina del usuario. Este plan sólo agrega un script de CI.
- La landing (`app.js`, `index.html`, `src/builders/landing.py`) — surface en el
  dashboard de salud es un follow-up de mayor riesgo (toca la landing generada).
- El pipeline de build (`build_dev_db.py`, `Makefile refresh`) — el fetch de adopción
  depende de red externa; **no** lo encadenes al build determinista (rompería builds
  offline y `--require-live`). Corre en su propio workflow.

## Git workflow

- Branch: `advisor/052-adoption-stats`
- Conventional commits (ej. `feat(ci): publica señal de adopción PyPI + Releases`).
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Crea el fixture (primero — el script y sus verificaciones lo consumen)

Crea `tests/fixtures/adoption_sample.json` con una forma que tu script consuma en
`--offline` (elige la forma que tu parser espere, p. ej. un objeto con las respuestas
crudas de ambas APIs). Incluye valores plausibles (ej. `last_month: 1234`,
`total_downloads: 567`). **Este paso va primero a propósito**: el Step 2 y varios de sus
comandos de verificación leen este fixture; si no existe todavía, esas verificaciones
fallan con `FileNotFoundError`.

**Verify**: `test -f tests/fixtures/adoption_sample.json && ./.venv/bin/python -c "import json; json.load(open('tests/fixtures/adoption_sample.json')); print('fixture ok')"` → imprime `fixture ok`.

### Step 2: Escribe `scripts/fetch_adoption_stats.py`

Script stdlib (`urllib.request`, `json`, `os`, `sys`, `argparse`). Debe:

1. Aceptar `--offline <path>` para leer un JSON de fixture en vez de la red (para
   tests/CI reproducible y para no golpear las APIs en cada corrida local).
2. En modo online, leer dos fuentes públicas (sin auth para PyPI; con
   `GITHUB_TOKEN` opcional del entorno para GitHub, para evitar rate-limit):
   - **PyPI**: `https://pypistats.org/api/packages/chile-hub/recent` →
     `{"data": {"last_day", "last_week", "last_month"}}`.
   - **GitHub Releases**: `https://api.github.com/repos/cortega26/chile-hub/releases`
     → suma de `assets[].download_count` sobre todos los releases (header
     `Authorization: Bearer $GITHUB_TOKEN` si la env var existe).
3. **Degradar con gracia**: si una fuente falla (red, rate-limit, 404 porque el paquete
   aún no tiene descargas), NO abortar; usar `None`/0 para esa fuente y seguir. La señal
   es informativa, no un gate.
4. Escribir dos archivos (patrón de `generate_coverage_badge.py`):
   - `data/normalized/adoption.json` — payload completo:
     `{"generated_at_utc", "pypi": {...}, "github_releases": {"total_downloads": N}}`.
   - `data/normalized/adoption_badge.json` — shields endpoint:
     `{"schemaVersion":1, "label":"instalaciones/mes", "message": "<pypi last_month o 'n/d'>", "color":"blue", "cacheSeconds":86400}`.

Forma del builder de badge (reúsa el estilo de `build_badge` de coverage):

```python
def build_badge(pypi_last_month: int | None) -> dict:
    return {
        "schemaVersion": 1,
        "label": "instalaciones/mes",
        "message": f"{pypi_last_month}" if pypi_last_month is not None else "n/d",
        "color": "blue",
        "namedLogo": "pypi",
        "cacheSeconds": 86400,
    }
```

**Verify**: `./.venv/bin/python scripts/fetch_adoption_stats.py --offline tests/fixtures/adoption_sample.json && ./.venv/bin/python -c "import json; b=json.load(open('data/normalized/adoption_badge.json')); assert b['schemaVersion']==1 and b['label']=='instalaciones/mes'; a=json.load(open('data/normalized/adoption.json')); assert 'pypi' in a and 'github_releases' in a; print('ok', b['message'])"` → imprime `ok <valor>`.

### Step 3: Tests sin red

En `tests/test_pipeline_logic.py` agrega tests que ejerciten **sólo el parseo y la
construcción del badge/payload** desde el fixture (importa las funciones puras del
script; NO hagas requests de red en tests). Cubre: happy path (ambas fuentes
presentes), degradación (PyPI ausente → `message == "n/d"`, sin excepción), y que
`adoption_badge.json` cumple el contrato shields (`schemaVersion == 1`, tiene `label`,
`message`, `color`). Modela sobre los tests existentes de builders en
`tests/test_pipeline_logic.py` (`grep -n "badge\|def test_" tests/test_pipeline_logic.py`).

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -v -k adoption` → pasan los nuevos.

### Step 4: Workflow programado

Crea `.github/workflows/adoption-stats.yml` modelado sobre `monthly-scrape.yml`:
`permissions: contents: write`, `on: schedule` (semanal, p. ej. `cron: "0 4 * * 1"`) +
`workflow_dispatch`, un job que hace checkout, setup Python + uv, corre
`python scripts/fetch_adoption_stats.py` (modo online, con `GITHUB_TOKEN:
${{ secrets.GITHUB_TOKEN }}` en el env del paso), y commitea con el patrón tolerante a
"sin cambios" y **`[skip ci]`** en el mensaje (copia el bloque de `monthly-scrape.yml:85-90`).
Mensaje sugerido: `chore(data): refresh adoption stats [skip ci]`.

**Verify**: `./.venv/bin/python -c "import yaml; d=yaml.safe_load(open('.github/workflows/adoption-stats.yml')); assert d['permissions']['contents']=='write'; print('workflow ok')"` → imprime `workflow ok`. (Si `pyyaml` no está en el venv, verifica manualmente que el YAML parsea con `python -c "import yaml"` — si falla el import, salta esta verificación y confía en el review humano del YAML.)

### Step 5: Badge en el README

Agrega una línea de badge junto a los existentes (`README.md:20-24`), consumiendo
`adoption_badge.json` por el mismo mecanismo shields-endpoint:

```
[![Instalaciones](https://img.shields.io/endpoint?url=https://tooltician.com/chile-hub/data/normalized/adoption_badge.json)](https://pypi.org/project/chile-hub/)
```

Confirma el base URL real con `grep -n "tooltician.com/chile-hub" README.md` antes de
pegarlo; no inventes dominio. **Ojo con `sync_docs.py`**: si el badge queda dentro de un
bloque delimitado `<!-- START_X -->`, `scripts/sync_docs.py --check` podría reescribirlo.
Colócalo **fuera** de cualquier bloque delimitado (junto a los badges estáticos de
License/Python que tampoco están en bloques), y luego corre el check de sync.

**Verify**: `grep -c "adoption_badge.json" README.md` → 1; y
`./.venv/bin/python scripts/sync_docs.py --check` → exit 0 (el badge no rompe el sync).

## Test plan

- `tests/test_pipeline_logic.py`: tests sin red descritos en Step 3 (parseo desde
  fixture, degradación, contrato shields del badge).
- No se testea el fetch de red (es no determinista y depende de servicios externos);
  el modo `--offline` + fixture es la superficie testeable.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -v` → todos pasan, con los nuevos.

## Done criteria

- [ ] `scripts/fetch_adoption_stats.py` existe, es stdlib-only (`grep -nE "^import (requests|httpx|urllib3)" scripts/fetch_adoption_stats.py` → sin coincidencias) y corre en modo `--offline` produciendo ambos JSON.
- [ ] `data/normalized/adoption_badge.json` cumple el contrato shields (`schemaVersion:1`, `label`, `message`, `color`).
- [ ] `.github/workflows/adoption-stats.yml` existe con `permissions: contents: write`, `schedule`, y commit con `[skip ci]`.
- [ ] Badge nuevo en `README.md` consumiendo `adoption_badge.json`, fuera de bloques delimitados; `scripts/sync_docs.py --check` exit 0.
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py` exit 0 con los tests nuevos.
- [ ] `make lint` y `make format-check` exit 0.
- [ ] Ningún archivo bajo `src/chile_hub/**` modificado (`git status`) — cero telemetría en el paquete.
- [ ] `git status` sin archivos fuera de "In scope".
- [ ] Fila de estado en `plans/README.md` actualizada.

## STOP conditions

Detente y reporta si:

- `generate_coverage_badge.py`, `monthly-scrape.yml` o los badges del README no
  coinciden con "Estado actual" (drift desde `7ebf94b`).
- Te ves tentado a instrumentar el paquete instalado o el bundle para reportar uso: es
  la línea roja ética — **no lo hagas**, sólo APIs de plataforma en CI.
- pypistats.org o la API de GitHub requieren auth/pago que no está disponible: degrada a
  `n/d` y reporta; no bloquees el plan por una fuente caída.
- Encadenar el fetch al build determinista (`make build`/`refresh`) parece necesario:
  no lo es — corre en su propio workflow; reporta si algo lo empuja hacia el build.
- Cualquier verificación falla dos veces tras un intento razonable.

## Maintenance notes

- **Follow-up deferido**: surface la señal en el dashboard de salud de la landing
  (`app.js` / `src/builders/landing.py`) — mayor riesgo porque toca la landing generada;
  hacerlo cuando se quiera visibilidad en el sitio, con su propio plan.
- **Qué escrutar en el PR**: que el script degrade con gracia (una API caída no debe
  romper el workflow ni escribir basura); que no se agregó ninguna dependencia nueva; y
  que nada del paquete instalado quedó tocado.
- **Nombre del repo/paquete**: el script asume repo `cortega26/chile-hub` y paquete PyPI
  `chile-hub` (confirmados en `README.md`). Si alguno cambia, actualiza las URLs del
  script.
- **Interacción con adopción → catálogo**: cuando esta señal muestre uso real, es el
  input que desbloquea el anti-patrón #10 para evaluar `plus-codes` /
  `entrepreneurship` (`docs/dataset-ideas/`).
