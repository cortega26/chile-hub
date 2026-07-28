# Plan 063: Historial de salud del hub (`hub_health_history.jsonl`) + sparkline en landing

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- src/builders/reports.py src/build_dev_db.py app.js index.html scripts/verify_landing.py tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (primer artefacto con estado/acumulativo en un pipeline deliberadamente stateless + cambio en landing)
- **Depends on**: none hard. **Recomendado ejecutar DESPUÉS del plan 054** (validación de anomalías temporales): 054 producirá flags de drift que este historial hará visibles; sin 054 el sparkline muestra solo conteos ok/warn/error.
- **Category**: direction
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

`docs/backlog/NEXT_STEPS.md` (mediano plazo) propone extender el dashboard de
salud con **históricos** ("gráfico de drift, changelog visual"). Hoy
`hub_health.json` es una foto del último build: no hay forma de ver si la salud
del hub mejora o empeora en el tiempo, ni de detectar una degradación lenta que
nunca gatilla un gate individual. Un JSONL append-only (una línea por build)
es el artefacto mínimo que habilita esa vista sin cambiar el modelo del
pipeline, y el sparkline en la landing lo hace visible públicamente — coherente
con la apuesta de transparencia del hub (dashboard público de salud ya existe).

## Current state

- **Generación de salud**: `src/build_dev_db.py::main()` llama
  `_generate_reports(...)` (L864). Dentro de `_generate_reports` (L771–841):
  `hub_health_output = write_hub_health_json(hub_health)` (L775) y **después**
  `artifact_manifest_output, artifact_manifest = write_artifact_manifest()`
  (L805). Este orden importa: cualquier archivo nuevo escrito entre L775 y
  L805 queda incluido en el manifiesto automáticamente.
- `src/builders/reports.py` L22–26:

  ```python
  def write_hub_health_json(health):
      output_path = os.path.join(NORMALIZED_DIR, "hub_health.json")
      ...
  ```

- `hub_health.json` (excerpt real, 2026-07-08): claves
  `generated_at_utc, overall_status, dataset_count, ok_count, warn_count,
  error_count, live_count, fallback_count, stale_count, drifted_count,
  degraded_count, warning_count, top_issue, datasets[]`. Valores actuales:
  `overall_status: "warn"`, `ok_count: 12`, `warn_count: 7`, `error_count: 0`,
  `drifted_count: 8`.
- **Persistencia entre builds**: el job `publish` de
  `.github/workflows/pipeline-check.yml` (L373+) commitea `data/normalized/`
  a `main` cada día ("chore(data): daily refresh [skip ci]"). El siguiente
  build parte del checkout de `main`, que **incluye** el `data/normalized/`
  del último publish — por eso un archivo acumulativo en `data/normalized/`
  sobrevive de un build al siguiente. El executor debe verificar en Step 1 que
  el build local no borra archivos ajenos de `data/normalized/` (escribe
  encima, no limpia el directorio).
- **Landing**: `app.js` L641–695 hace `fetch(dataUrl("data/normalized/hub_health.json"))`
  y rellena `health-tbody`, `health-badge`, contadores
  (`health-ok-count`, etc.); degradación grácil: si el fetch falla, la sección
  queda oculta (`health-hidden`). `index.html` L2368+ define
  `.health-section`, `.health-summary`, `.health-badge`, `.health-table-wrap`.
- `scripts/verify_landing.py` verifica strings textuales del dashboard de salud
  (L373–387 y otras) — **no romper esos strings**; el sparkline es aditivo.
- Tests de builders de reportes viven en `tests/test_pipeline_logic.py`
  (ver tabla de tests en `AGENTS.md §8`: cubre "builders (`reports`,
  `pipeline_status_utils`)").

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Build (2×, idempotencia) | `make build && make build` | exit 0 ambos; history crece correctamente |
| Tests focales | `./.venv/bin/pytest tests/test_pipeline_logic.py -v` | all pass |
| Verify pipeline | `make verify` | exit 0 (manifiesto incluye el nuevo archivo) |
| Landing smoke | `make verify-landing` | exit 0 (strings del dashboard intactos) |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `src/builders/reports.py` (función append)
- `src/build_dev_db.py` (1 línea: llamada entre L775 y L805, dentro de `_generate_reports`)
- `app.js` (fetch + render del sparkline, degradación grácil)
- `index.html` (contenedor + CSS del sparkline)
- `tests/test_pipeline_logic.py` (tests de la función append)
- `AGENTS.md` (§2 estructura o §3: mención de 1 línea al artefacto nuevo, si la sección lo amerita — ver Step 5)

**Out of scope** (do NOT touch, even though they look related):
- `scripts/verify_landing.py` — sus strings verificados NO cambian; si tu
  cambio lo exige, es señal de que rompiste algo (STOP).
- `hub_health.json` (su schema no cambia; el historial es un archivo aparte).
- El dashboard de salud existente (tabla, badges, contadores) — aditivo only.
- `docs/` de datasets, `data/dataset_catalog_config.json` (el historial es un
  artefacto compartido, no un dataset del catálogo).
- Gráficos con librerías (Chart.js etc.) — el sparkline es SVG inline generado
  a mano, cero dependencias nuevas en la landing.

## Git workflow

- Branch: `advisor/063-hub-health-history`
- Commits: `feat(pipeline): historial append-only de salud del hub (hub_health_history.jsonl)`,
  `feat(landing): sparkline de salud historica en dashboard`,
  `test(pipeline): tests de append_hub_health_history`.
- No pushear ni abrir PR salvo instrucción del operador.

## Steps

### Step 1: Verificar la premisa de persistencia

Antes de escribir código: crea `data/normalized/_probe.txt`, corre
`make build`, y confirma que `_probe.txt` sigue existiendo (el build no limpia
el directorio). Borra el probe.

**Verify**: `touch data/normalized/_probe.txt && make build >/dev/null 2>&1 && test -f data/normalized/_probe.txt && echo "persiste" && rm data/normalized/_probe.txt` → `persiste`
Si imprime otra cosa → STOP (el modelo acumulativo no es viable así; reportar).

### Step 2: `append_hub_health_history()` en `reports.py`

Agrega a `src/builders/reports.py` (junto a `write_hub_health_json`, mismas
convenciones: `os.path.join(NORMALIZED_DIR, ...)`, stdlib `json`):

```python
HUB_HEALTH_HISTORY_NAME = "hub_health_history.jsonl"
HUB_HEALTH_HISTORY_MAX_LINES = 400  # ~13 meses de builds diarios

def append_hub_health_history(health):
    """Appende una línea JSONL con el resumen de salud del build.

    Idempotente por timestamp: si la última línea tiene el mismo
    generated_at_utc, no duplica (rebuilds del mismo artifact). Trunca a
    HUB_HEALTH_HISTORY_MAX_LINES conservando las más recientes.
    """
    entry = {
        "generated_at_utc": health.get("generated_at_utc"),
        "overall_status": health.get("overall_status"),
        "ok_count": health.get("ok_count"),
        "warn_count": health.get("warn_count"),
        "error_count": health.get("error_count"),
        "drifted_count": health.get("drifted_count"),
        "fallback_count": health.get("fallback_count"),
        "stale_count": health.get("stale_count"),
        "warning_count": health.get("warning_count"),
        "dataset_count": health.get("dataset_count"),
    }
    path = os.path.join(NORMALIZED_DIR, HUB_HEALTH_HISTORY_NAME)
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
    if lines:
        last = json.loads(lines[-1])
        if last.get("generated_at_utc") == entry["generated_at_utc"]:
            return path  # rebuild idempotente: nada que agregar
    lines.append(json.dumps(entry, ensure_ascii=False))
    lines = lines[-HUB_HEALTH_HISTORY_MAX_LINES:]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
```

### Step 3: Cablear en `_generate_reports`

En `src/build_dev_db.py`, dentro de `_generate_reports`, **después** de
`hub_health_output = write_hub_health_json(hub_health)` (L775) y **antes** de
`write_artifact_manifest()` (L805), agrega la llamada
`append_hub_health_history(hub_health)` (importarla junto a
`write_hub_health_json` en el import de L104). La posición garantiza que el
archivo quede incluido en `artifact_manifest.json`.

**Verify**: `make build && make build` → exit 0 ambos; luego
`wc -l data/normalized/hub_health_history.jsonl` → `1` (el segundo build fue
idempotente por timestamp) o `2` (si regenerated_at difiere — ambos válidos;
lo que NO debe pasar es que crezca sin bound ni que falle); y
`python3 -c "import json; m=json.load(open('data/normalized/artifact_manifest.json')); assert any(a['path'].endswith('hub_health_history.jsonl') for a in m['artifacts']); print('en manifiesto')"` → `en manifiesto`
· y `make verify` → exit 0.

### Step 4: Sparkline en la landing

`index.html`: dentro de `.health-section`, después del bloque
`.health-summary`, agrega un contenedor
`<div id="health-history-wrap" class="health-hidden"><svg id="health-history-sparkline" role="img" aria-label="Historial de salud del hub"></svg><p class="health-history-caption">Historial reciente: capas ok / warn / error por build</p></div>`
+ CSS mínimo (alto fijo ~48px, ancho 100%, reuse de tokens `--accent-*`
existentes para los colores ok/warn/error — NO introducir hex sueltos; el plan
049 unificó tokens, revisar qué tokens usan `.health-badge.ok/.warn/.error` y
reusar esos mismos colores vía `currentColor` o variables).

`app.js`: nueva función `renderHealthHistory()` invocada junto al init de
salud existente: `fetch(dataUrl("data/normalized/hub_health_history.jsonl"))`;
si 404/falla → dejar el wrap oculto (mismo patrón de degradación grácil del
dashboard, L694). Parsea líneas JSONL, toma las últimas 30, y genera un SVG
inline de barras apiladas (ok=verde/warn=ámbar/error=rojo) normalizadas al
`dataset_count` de cada línea, `width` fraccionario por build. Sin librerías,
sin strings nuevos verificados por `verify_landing.py`.

**Verify**: `make verify-landing` → exit 0 · y servir local
(`python3 -m http.server` o el servidor que use `verify_landing`) y confirmar
en browser/Playwright que con el JSONL presente el SVG tiene `>0` rects y que
borrando el JSONL la sección vuelve a ocultarse sin errores de consola.

### Step 5: Documentar el artefacto

En `AGENTS.md`, agrega una línea donde corresponda (§2 árbol de
`data/normalized/` o §3) documentando `hub_health_history.jsonl` como
artefacto acumulativo append-only (una línea por build, cap 400, idempotente
por timestamp). Si la edición resulta forzada en ambas secciones, omítela y
anótalo en el PR (no romper la prosa curada por una línea).

**Verify**: `make doctor` → exit 0 (los gates anti-drift no deben verse
afectados).

## Test plan

En `tests/test_pipeline_logic.py`, clase `HubHealthHistoryTests` (patrón:
tests de `reports` existentes en ese archivo; usa `patch` de `NORMALIZED_DIR`
a un `tmp_path` si así lo hacen los tests vecinos, o monkeypatch del
constante del módulo):

1. Append sobre archivo inexistente → crea el JSONL con 1 línea válida (JSON
   parseable, 10 claves).
2. Append con mismo `generated_at_utc` que la última línea → no duplica.
3. Append con timestamp distinto → 2 líneas, orden cronológico.
4. Cap: sembrar 400 líneas + append → sigue en 400, la primera es la más
   antigua retenida (la 2 original).
5. Líneas vacías/espurias en el archivo previo → se ignoran sin romper.
6. Integración: tras `make build`, el archivo existe y está en el manifiesto
   (puede ser test que lea `data/normalized` si el archivo de test ya está en
   la categoría "requiere build" — si no, dejarlo como verificación manual del
   Step 3; seguir la convención del archivo de tests).

**Verification**: `./.venv/bin/pytest tests/test_pipeline_logic.py -v` → all
pass, ≥5 tests nuevos.

## Done criteria

- [ ] `make build && make build` exit 0; `hub_health_history.jsonl` existe y no duplica por timestamp
- [ ] El archivo aparece en `artifact_manifest.json` y `make verify` exit 0
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py -v` exit 0 con los nuevos tests
- [ ] `make verify-landing` exit 0 sin tocar `scripts/verify_landing.py`
- [ ] Con JSONL ausente, la landing no muestra el sparkline ni errores de consola (degradación grácil)
- [ ] `make lint && make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) si:

- El probe de Step 1 muestra que el build limpia `data/normalized/` (la
  persistencia acumulativa no funciona como se asumió — el diseño necesita
  otra ubicación, p. ej. commitear el JSONL fuera de normalized o regenerarlo
  en el job publish; decisión de arquitectura, no del executor).
- `write_artifact_manifest()` ya no se llama después de
  `write_hub_health_json()` dentro de `_generate_reports` (el orden de fases
  cambió — el archivo quedaría fuera del manifiesto).
- `verify_landing.py` falla tras el cambio de landing **sin** que hayas tocado
  strings verificados (acoplamiento no evidente — investigar antes de seguir,
  no "arreglar" el smoke test).
- El JSONL crece sin bound en builds repetidos locales (la idempotencia por
  timestamp no alcanza — p. ej. `generated_at_utc` se regenera por fase).
- Un step falla dos veces tras un intento razonable de fix.

## Maintenance notes

- **Evolución del schema de línea**: cuando el plan 054 (anomalías temporales)
  landee, agregar sus flags (p. ej. `anomaly_count`) como clave nueva de la
  línea — JSONL tolera claves nuevas sin migración; el sparkline las ignora
  hasta que se rendericen.
- El cap de 400 líneas es deliberado (bounded, ~13 meses); si se quiere
  historia completa, archivar el JSONL anualmente es un follow-up manual, no
  código.
- La sección de landing depende del orden de keys del JSONL? No — parsea por
  línea JSON; mantenerlo así (no asumir orden de claves en consumers futuros).
- En review, escrutar: (a) que la escritura sea atómica-en-la-práctica para el
  caso CI (write completo de 400 líneas, no append syscall — evita líneas
  parciales si el build muere a mitad); (b) que el sparkline reuse tokens de
  color existentes (plan 049); (c) que la degradación grácil esté realmente
  probada en ambos sentidos (con y sin archivo).
