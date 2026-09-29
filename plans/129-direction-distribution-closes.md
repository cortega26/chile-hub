# Plan 129: Cierres de distribución y superficie (métrica HF, registry MCP, `resolve_regiones`)

> **Executor instructions**: Los tres pasos son independientes; cada uno tiene
> su verificación. Si algo de "STOP conditions" ocurre, detente y reporta.
> Este plan es mixto: Step 1 y 3 son código; Step 2 es un spike con una parte
> que requiere acción del operador (auth en el registry MCP). Actualiza tu fila
> en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- scripts/fetch_adoption_stats.py .github/workflows/adoption-stats.yml docs/adoption-review.md README.md docs/mcp.md src/chile_hub/text.py src/chile_hub/core.py src/chile_hub/cli.py src/extractors/region_utils.py tests/`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: S (1 y 3) / M (2, spike)
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

Tres asimetrías de superficie con evidencia en el propio repo:

1. **La señal de adopción no mide HF** aunque `docs/adoption-review.md:42`
   define el umbral de Kaggle como "HF ≥ 270 descargas/mes sostenido". El
   artefacto `data/normalized/adoption.json` solo trae `pypi` y
   `github_releases`; HF (274 descargas al 2026-09-29) se registra a mano en
   docs. El gate que el proyecto se escribió es inexigible desde artefactos.
2. **El servidor MCP es invisible para agentes**: no hay `server.json` ni
   referencia al registry oficial (verificado por búsqueda); la única vía es
   configurar el cliente a mano (`docs/mcp.md:22-35`). Y `README.md:353-355`
   promete "catálogo, consultas y **salud**" — no existe tool de salud en
   `mcp_tools.py` (solo `list_datasets`, `get_dataset`, `resolve_comunas`,
   `get_indicadores`).
3. **`resolve_regiones()` no existe** aunque ADR-009 pregunta abierta #2 lo
   deja "trivial de implementar si se decide", y el propio repo ya mantiene la
   tabla de alias en `src/extractors/region_utils.py:17-55` para dos
   extractores. La misma asimetría interna→API pública justificó
   `resolve_comunas()` (Plan 050).

## Current state

- `scripts/fetch_adoption_stats.py` — `PYPI_STATS_URL`, `GITHUB_RELEASES_URL`;
  payload con claves `generated_at_utc`, `pypi`, `github_releases`
  (`data/normalized/adoption.json`). Degradación con gracia por fuente; si
  ambas fallan, exit 1 sin escribir.
- `.github/workflows/adoption-stats.yml:1` — nombre "Adoption Stats (PyPI +
  GitHub Releases)", cron semanal.
- `docs/adoption-review.md:41-46` — umbrales; `:13` y `:66` registran HF a
  mano.
- `README.md:353-355` — claim MCP con "salud".
- `src/chile_hub/text.py` — `normalize_comuna_name()` (helper puro de Plan 050,
  consumido por `resolve_comunas` y por `subdere_extractor`, con guardrail
  anti-divergencia en tests).
- `src/extractors/region_utils.py` — `REGION_A_CODIGO` + `norm_text()` +
  `region_nombre_a_codigo()`.
- `src/chile_hub/core.py:350` — `resolve_comunas()`; `cli.py:350-365` —
  subcomando `resolve`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Tests adopción | `./.venv/bin/pytest tests/test_ci_config.py -k Adoption -v` | declared | verde |
| Tests core | `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v -k "resolve or region"` | declared | verde |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope**:
- `scripts/fetch_adoption_stats.py`, `data/normalized/adoption.json` (regenerado),
  `docs/adoption-review.md` (nota de fuente), tests de adopción
- `server.json` (nuevo, raíz del repo), `README.md`, `docs/mcp.md`
- `src/chile_hub/text.py` (o `regions.py` nuevo), `src/chile_hub/core.py`,
  `src/chile_hub/cli.py`, `src/extractors/region_utils.py`, tests

**Out of scope**:
- Publicar el paquete en el registry MCP (acción del operador; el plan deja el
  manifiesto listo y las instrucciones)
- Tools MCP nuevas (`health`, coords): gateadas por `docs/adoption-review.md:43`
- Kaggle/conda-forge (siguen diferidos; Step 1 solo habilita medirlos)

## Git workflow

- Branch: `advisor/129-direction-distribution-closes`
- Commits por paso: `feat(dist): mide HF en adoption.json`,
  `docs(mcp): ...`, `feat(core): resolve_regiones()`
- No push/PR.

## Steps

### Step 1: Métrica de HF en `adoption.json`

1. En `scripts/fetch_adoption_stats.py`, agrega:
   - `HUGGINGFACE_URL = "https://huggingface.co/api/datasets/cortega26/chile-hub"`.
   - `fetch_huggingface() -> dict | None` con `_http_get_json`; extrae
     `downloads`, `likes`, `lastModified` (nombres del API público) y devuelve
     `None` en fallo.
   - En el payload: `"huggingface": {...}` o `None`; la regla "si TODAS las
     fuentes fallan → exit 1" pasa a "si pypi y github fallan → exit 1" **o**
     más simple: mantén la regla actual sobre las dos fuentes originales y HF
     degrada sola (documenta la decisión en el docstring).
2. Modo `--offline`: extiende el fixture de tests (`tests/fixtures/`) con una
   respuesta HF de ejemplo y cubre: HF ok, HF 404 (None), HF red caída (None).
3. Regenera `data/normalized/adoption.json` en modo real si hay red; si no,
   deja la regeneración al workflow semanal y anota en el PR.
4. `docs/adoption-review.md`: agrega una línea en "Registro" indicando que
   `adoption.json` ahora trae la señal HF (fuente: API pública, misma política
   sin telemetría).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k Adoption -v` →
verde; `python scripts/fetch_adoption_stats.py --offline <fixture>` escribe un
payload con clave `huggingface`.

### Step 2: Registry MCP (spike + manifiesto) y claim del README

1. Lee la especificación vigente del registry oficial
   (`registry.modelcontextprotocol.io`, docs de `server.json`; usa web) y crea
   `server.json` en la raíz con:
   - `name: "io.github.cortega26/chile-hub"` (namespace verificado por GitHub),
   - `packages[0]`: `registryType: "pypi"`, `identifier: "chile-hub"`,
   - el marcador `mcp-name: io.github.cortega26/chile-hub` que el registry
     busca en el README (agrégalo a `README.md` en una línea discreta).
2. Valida el archivo contra el schema del registry (el repo de
   `modelcontextprotocol/registry` publica un validador; usa `npx`/`docker` si
   está disponible). Si no puedes validar sin credenciales, documenta el
   comando exacto y deja el archivo.
3. **Decide y documenta** cómo resuelve el extra `chile-hub[mcp]` el cliente
   (el registry instala `chile-hub`, no el extra). Opciones:
   a) `packages[].runtimeArguments`/`environmentVariables` no cubren extras →
   publicar un paquete-alias `chile-hub-mcp` (trabajo extra, otro issue);
   b) listar igual y documentar en `docs/mcp.md` que la instalación es
   `pip install chile-hub[mcp]` antes de configurar. Elige (b) si (a) excede
   el spike y anótalo.
4. Corrige el claim: `README.md:353-355` → "catálogo, consultas y resolución
   de comunas" (lo que las 4 tools realmente hacen). Revisa `docs/mcp.md` por
   overclaims equivalentes.
5. Publicación (operador): documenta en `docs/mcp.md` el comando oficial de
   publicación (`mcp-publisher`/PR al registry, según la spec vigente). El
   executor **no** publica.

**Verify**: `python -c "import json; json.load(open('server.json'))"` → sin
error; `grep -n "mcp-name" README.md` → 1; `grep -in "salud" README.md` en la
sección MCP → 0.

### Step 3: `resolve_regiones()`

1. Promueve la tabla de alias al paquete (dependencia permitida: el paquete
   **no** puede importar extractores; el precedente es
   `chile_hub.text.normalize_comuna_name` usado por extractores):
   - Agrega a `src/chile_hub/text.py` (o un `regions.py` nuevo):
     `REGION_ALIASES` (copia exacta de `REGION_A_CODIGO`),
     `normalize_region_name(texto)` (reusa `norm_text`), y
     `region_name_to_code(texto)`.
   - `src/extractors/region_utils.py` pasa a delegar en el paquete
     (`from chile_hub.text import ...` o re-export), conservando su API pública
     (`region_nombre_a_codigo`, `norm_text`, `REGION_A_CODIGO` como alias
     leído). Mantén el guardrail anti-divergencia: un test que afirme que
     ambas rutas devuelven lo mismo para las 16 regiones + alias.
2. En `core.py`, agrega `resolve_regiones(names)` con el contrato exacto de
   `resolve_comunas` (`codigo_region` como `pl.String`, columna `matched`,
   no-match explícito, orden preservado). Reutiliza/extrae el helper común si
   sale sin fricción.
3. En `cli.py`, agrega subcomando `resolve-regiones` modelado sobre `resolve`
   (`cli.py:350-365`).
4. Tests: en `tests/test_core.py` (patrón `ResolveComunasTests`), 5 casos
   (exacto, alias "RM"/"Metropolitana", tildes, no-match, orden/duplicados);
   guardrail de paridad con `region_utils`.

**Verify**: `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v -k "resolve or region"` → verde;
`python -m src.chile_hub resolve-regiones "Metropolitana" "Ñuble"` → tabla con
`13` y `16`.

## Test plan

- Adopción: 3 casos offline de HF.
- MCP: sin tests (manifiesto/validación); guardrail de texto del claim.
- `resolve_regiones`: 5 tests + paridad con extractor.
- Verificación global: pytest focal + `make lint/format`.

## Done criteria

- [ ] `python -c "import json; d=json.load(open('data/normalized/adoption.json')); print(d.keys())"` → incluye `huggingface` (si hubo red) o el código lo soporta (fixture)
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -k Adoption -v` → verde, con caso HF
- [ ] `server.json` existe y parsea; README con marcador `mcp-name` y sin el claim "salud"
- [ ] `python -m src.chile_hub resolve-regiones "Metropolitana"` → `13`
- [ ] `./.venv/bin/pytest tests/test_core.py tests/test_chile_hub.py -v -k "resolve or region"` → verde
- [ ] `make lint && make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` solo in-scope
- [ ] Fila del índice actualizada

## STOP conditions

- Step 2: si el registry exige credenciales/publicación para validar el
  `server.json` y no puedes completar la validación, deja el archivo + comandos
  documentados y marca ese step como BLOCKED (acción de operador), sin
  bloquear los otros dos.
- Step 3: si `src/extractors/region_utils.py` no puede importar
  `chile_hub.text` por `sys.path` en extractores standalone, usa el patrón de
  Plan 050 (`PYTHONPATH=src`, ya es como corre `make extract`) y verifica con
  `PYTHONPATH=src python src/extractors/autoridades_electas_extractor.py --help`
  o el test correspondiente; si no funciona, STOP.
- Si al mover la tabla a `text.py` aparece una diferencia real entre el mapping
  y el comportamiento actual de los extractores, NO unifiques a ciegas:
  reporta la diferencia.

## Maintenance notes

- `adoption.json` ahora depende de 3 fuentes; el workflow semanal debe seguir
  commit `[skip ci]`. Si HF cambia su API, degrada a `null` sin romper.
- El registry MCP es preview; si se publica, anotar en `docs/mcp.md` la versión
  y fecha, y revalidar en cada release que `server.json` no quede stale.
- `resolve_regiones` cierra la pregunta #2 de ADR-009; actualizar el ADR
  (agregar una sección "Resuelto en Plan 129") en el mismo PR.
- **Deferred:** fuzzy matching y entrada `Series/DataFrame` (ADR-009 preguntas
  1 y 3) siguen diferidos; `resolve_regiones` no los aborda.
