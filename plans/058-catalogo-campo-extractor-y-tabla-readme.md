# Plan 058: Campo `extractor` en el catálogo + tabla de extractores auto-generada en README

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- data/dataset_catalog_config.json scripts/check_companion_paths.py src/builders/doc_sync.py README.md AGENTS.md tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none (disjoint from plans 050–057)
- **Category**: direction / dx
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

`AGENTS.md` §12 (política anti-drift) lista explícitamente como "Seguimiento
recomendado, no implementado todavía": agregar un campo `"extractor"` a las 21
entradas de `data/dataset_catalog_config.json`, lo que permite (a) generar
automáticamente la tabla de extractores de `README.md` — hoy manual y ya quedó
stale una vez — y (b) extender `scripts/check_companion_paths.py registry` para
validar que el extractor de cada dataset exista y que ningún extractor quede
huérfano. Es el último hueco de drift mecánico que el propio documento canónico
reconoce. Al cerrarlo, el mapeo dataset↔extractor pasa de prosa mantenida a mano
a dato validado en CI en cada push/PR.

## Current state

- `data/dataset_catalog_config.json` — dict de 21 claves. Cada entrada tiene
  `description`, `join_keys`, `confidence_tier`, `expected_record_count`,
  `reuse_policy`, `freshness_policy`, `usage_examples`, `outputs` (ausente en
  carril `candidate`), `documentation`. **No existe el campo `extractor`.**
  Claves (orden): `regiones, provincias, comunas, comunas_enriquecidas,
  indicadores, censo_comunal, censo_hogares_viviendas, establecimientos_salud,
  distritos_electorales, establecimientos_educacionales, finanzas_municipales,
  resultados_educacionales, indicadores_urbanos_siedu,
  perfil_territorial_comunal, empresas, pobreza_comunal,
  consumo_electrico_comunal, delincuencia_comunal, partidos_politicos,
  autoridades_electas, autoridades_locales`.
- `scripts/check_companion_paths.py` — `check_registry()` (L56–67) hoy valida
  contrato + doc por dataset:

  ```python
  def check_registry() -> list[str]:
      errors = []
      for key in sorted(dataset_keys()):
          if key not in ALLOWED_MISSING_CONTRACT:
              contract_path = CONTRACTS_DIR / f"{key}.schema.json"
              if not contract_path.is_file():
                  errors.append(f"falta contrato de esquema para '{key}': {contract_path}")
          ...
  ```

- `src/builders/doc_sync.py` — generadores de bloques delimitados. Patrón a
  imitar: dict curado con `SystemExit` si falta una entrada
  (`_AGENTS_TEST_DESCRIPTIONS`, L213–219), y `SYNC_FUNCS` (L424–437) donde se
  registran las funciones `sync_*`. `sync_all_docs()` corre al final de
  `make build`; `python scripts/sync_docs.py --check` verifica sin escribir
  (corre en `make doctor` y en el job `quality` de CI).
- `README.md` L682–694 — tabla **manual** dentro de un `<details>`:

  ```
  | Dominio | Extractores |
  | Territorio | `subdere_extractor.py`, `electoral_extractor.py` |
  | Demografía | `censo_extractor.py`, `censo_hogares_viviendas_extractor.py`, `pobreza_extractor.py` |
  | Servicios públicos | `salud_extractor.py`, `mineduc_establecimientos_extractor.py`, `mineduc_resultados_extractor.py` |
  | Economía | `bcentral_extractor.py`, `sinim_finanzas_extractor.py`, `sinim_finanzas_live_extractor.py`, `res_extractor.py`, `consumo_electrico_extractor.py` |
  | Indicadores urbanos | `siedu_extractor.py` |
  | Política | `partidos_politicos_extractor.py`, `autoridades_electas_extractor.py`, `autoridades_locales_extractor.py` |
  | Seguridad (carril `candidate`) | `cead_delincuencia_live_extractor.py` |
  ```

  seguida de la nota "El mapeo autoritativo dataset ↔ extractor vive en
  `data/dataset_catalog_config.json`…" (conservar esa nota).
- Tests de `doc_sync.py` viven en `tests/test_pipeline_logic.py` (~L2791+),
  patrón: `patch.object(doc_sync, "README_PATH", ...)` sobre archivos
  temporales. Úsalos como modelo estructural.

**Mapeo dataset → extractor (verificado contra `src/extractors/` y `AGENTS.md §2`):**

| Dataset | `extractor` |
|---|---|
| regiones, provincias, comunas, comunas_enriquecidas | `"src/extractors/subdere_extractor.py"` |
| indicadores | `"src/extractors/bcentral_extractor.py"` |
| censo_comunal | `"src/extractors/censo_extractor.py"` |
| censo_hogares_viviendas | `"src/extractors/censo_hogares_viviendas_extractor.py"` |
| establecimientos_salud | `"src/extractors/salud_extractor.py"` |
| distritos_electorales | `"src/extractors/electoral_extractor.py"` |
| establecimientos_educacionales | `"src/extractors/mineduc_establecimientos_extractor.py"` |
| finanzas_municipales | `["src/extractors/sinim_finanzas_extractor.py", "src/extractors/sinim_finanzas_live_extractor.py"]` |
| resultados_educacionales | `"src/extractors/mineduc_resultados_extractor.py"` |
| indicadores_urbanos_siedu | `"src/extractors/siedu_extractor.py"` |
| perfil_territorial_comunal | `null` (derivado en `build_dev_db.py`, sin extractor) |
| empresas | `"src/extractors/res_extractor.py"` |
| pobreza_comunal | `"src/extractors/pobreza_extractor.py"` |
| consumo_electrico_comunal | `"src/extractors/consumo_electrico_extractor.py"` |
| delincuencia_comunal | `"src/extractors/cead_delincuencia_live_extractor.py"` |
| partidos_politicos | `"src/extractors/partidos_politicos_extractor.py"` |
| autoridades_electas | `"src/extractors/autoridades_electas_extractor.py"` |
| autoridades_locales | `"src/extractors/autoridades_locales_extractor.py"` |

**Dominios para la tabla README (del agrupamiento actual):**
Territorio: regiones, provincias, comunas, comunas_enriquecidas,
distritos_electorales · Demografía: censo_comunal, censo_hogares_viviendas,
pobreza_comunal · Servicios públicos: establecimientos_salud,
establecimientos_educacionales, resultados_educacionales · Economía:
indicadores, finanzas_municipales, empresas, consumo_electrico_comunal ·
Indicadores urbanos: indicadores_urbanos_siedu · Política: partidos_politicos,
autoridades_electas, autoridades_locales · Seguridad (carril `candidate`):
delincuencia_comunal · `perfil_territorial_comunal`: derivado (fila aparte).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Gates anti-drift | `make doctor` | exit 0 |
| Sync docs (escribe) | `make sync-docs` | exit 0, regenera bloques |
| Sync docs (verifica) | `python scripts/sync_docs.py --check` | exit 0 |
| Registry check | `python scripts/check_companion_paths.py registry` | `check_companion_paths ok (modo: registry)` |
| Tests focales | `./.venv/bin/pytest tests/test_pipeline_logic.py -v` | all pass |
| Lint | `make lint && make format-check` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `data/dataset_catalog_config.json`
- `scripts/check_companion_paths.py`
- `src/builders/doc_sync.py`
- `README.md` (solo envolver la tabla L682–694 en marcadores delimitados)
- `AGENTS.md` (§12: tabla de propietarios + párrafo "Seguimiento recomendado")
- `tests/test_pipeline_logic.py`

**Out of scope** (do NOT touch, even though they look related):
- `src/extractors/*.py` — ningún cambio de código de extractores.
- La tabla de árbol de extractores de `AGENTS.md` (`AGENTS_EXTRACTOR_LIST`) —
  ya está auto-generada desde el filesystem; no la dupliques con el nuevo campo.
- La automatización de la tabla CLI de README (introspección de
  `build_parser()`) — sigue diferida, requiere `uv sync` en el job `quality`.
- `contracts/datasets/*`, `docs/datasets/*`.

## Git workflow

- Branch: `advisor/058-catalog-extractor-field`
- Conventional commits en español, estilo del repo: p. ej.
  `feat(catalog): agrega campo extractor a las 21 entradas del catálogo`,
  `feat(ci): valida extractores en check_companion_paths registry`,
  `feat(docs): auto-genera tabla de extractores de README`.
- No pushear ni abrir PR salvo instrucción del operador.

## Steps

### Step 1: Agregar el campo `extractor` a las 21 entradas del catálogo

En `data/dataset_catalog_config.json`, agrega a cada entrada el campo
`"extractor"` con el valor exacto de la tabla de mapeo de "Current state"
(string, lista de strings, o `null`). Colócalo alfabéticamente entre las claves
existentes (el archivo está ordenado por clave dentro de cada entrada:
`confidence_tier`, `description`, `documentation`, `expected_record_count`,
`extractor`, `freshness_policy`, …).

**Verify**: `python3 -c "import json; d=json.load(open('data/dataset_catalog_config.json')); assert len(d)==21; missing=[k for k,v in d.items() if 'extractor' not in v]; assert not missing, missing; print('21/21 entradas con campo extractor')"` → `21/21 entradas con campo extractor`

### Step 2: Extender `check_registry()` con validación de extractores

En `scripts/check_companion_paths.py`:

1. Agrega `EXTRACTORS_DIR = ROOT_DIR / "src" / "extractors"` junto a las
   constantes de L8–10.
2. Agrega una función `check_extractors() -> list[str]` con esta forma:

   ```python
   def check_extractors() -> list[str]:
       errors = []
       with open(DATASET_CATALOG_PATH, "r", encoding="utf-8") as f:
           catalog = json.load(f)
       referenced: set[str] = set()
       for key, cfg in sorted(catalog.items()):
           if "extractor" not in cfg:
               errors.append(f"'{key}': falta el campo 'extractor' (usa null si es derivado)")
               continue
           value = cfg["extractor"]
           paths = [] if value is None else ([value] if isinstance(value, str) else list(value))
           for rel in paths:
               if not (ROOT_DIR / rel).is_file():
                   errors.append(f"'{key}': extractor no existe: {rel}")
               referenced.add(rel)
       for f in sorted(EXTRACTORS_DIR.glob("*_extractor.py")):
           rel = f.relative_to(ROOT_DIR).as_posix()
           if rel not in referenced:
               errors.append(f"extractor huérfano (ningún dataset lo referencia): {rel}")
       return errors
   ```

   (El glob `*_extractor.py` excluye solo — sin necesidad de listas extra — a
   `base.py`, `http_utils.py`, `region_utils.py`, `source_adapter.py`,
   `__init__.py`.)
3. En `main()`, modo `registry`: `errors = check_registry() + check_extractors()`.
   Actualiza el `help` del subparser `registry` mencionando la nueva validación.

**Verify**: `python scripts/check_companion_paths.py registry` →
`check_companion_paths ok (modo: registry)` (exit 0)

### Step 3: Generador de la tabla README en `doc_sync.py`

En `src/builders/doc_sync.py`:

1. Agrega `_README_DATASET_DOMAINS` dict de las 21 claves → dominio (strings
   del agrupamiento de "Current state"; `perfil_territorial_comunal` mapea a
   `None` = derivado), siguiendo el patrón de `_AGENTS_TEST_DESCRIPTIONS`.
2. Agrega `sync_readme_extractor_table(check_only=False)`: agrupa datasets por
   dominio (orden de dominios = el del README actual), lista por dominio los
   extractores únicos de sus datasets (en orden de aparición en el catálogo,
   basename en backticks, separados por `, `); genera
   `| Dominio | Extractores |\n|:---|:---|` + filas + fila final
   `| Derivado en \`build_dev_db.py\` (sin extractor) | \`perfil_territorial_comunal\` |`.
   Si una clave del catálogo falta en `_README_DATASET_DOMAINS` →
   `raise SystemExit("ERROR: dataset '...' sin dominio en _README_DATASET_DOMAINS…")`
   (mismo patrón que `sync_agents_test_table`).
3. Regístrala en `SYNC_FUNCS` (al final de la lista).

**Verify**: `python3 -c "from src.builders.doc_sync import sync_readme_extractor_table; print('importable')"` → `importable`

### Step 4: Envolver la tabla de README en marcadores y regenerar

En `README.md`, envuelve la tabla `| Dominio | Extractores |…` (L684–692,
**sin** tocar el `<summary>`, el encabezado previo ni la nota "El mapeo
autoritativo…" posterior) con:

```
<!-- START_EXTRACTOR_TABLE -->
…tabla…
<!-- END_EXTRACTOR_TABLE -->
```

Luego corre `make sync-docs` para que el generador reemplace el contenido.
Compara visualmente: la tabla generada debe ser equivalente a la manual (más la
fila de derivado).

**Verify**: `python scripts/sync_docs.py --check` → exit 0 · y
`grep -c "START_EXTRACTOR_TABLE" README.md` → `1`

### Step 5: Actualizar `AGENTS.md` §12

1. En la tabla "Propietarios canónicos", agrega una fila:
   `| Mapeo dataset ↔ extractor | \`data/dataset_catalog_config.json\` (campo \`extractor\`) | \`check_companion_paths.py registry\` |`
   y una fila para la tabla README de extractores: fuente
   `data/dataset_catalog_config.json` vía `doc_sync.py`, verificada por
   `scripts/sync_docs.py --check`.
2. Reescribe el párrafo "Seguimiento recomendado, no implementado todavía":
   elimina el ítem de la tabla de extractores (ya implementado) y deja solo el
   de la tabla CLI con su explicación (requiere `uv sync` en job `quality`).

**Verify**: `grep -n "extractor" AGENTS.md | grep -c "registry"` → ≥1

### Step 6: Tests

En `tests/test_pipeline_logic.py`, agrega una clase
`ExtractorRegistryAndReadmeTableTests` (ver "Test plan").

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -k "Extractor or extractor" -v` → all pass

## Test plan

Modela los tests sobre la clase de `doc_sync` existente en
`tests/test_pipeline_logic.py` (~L2791, usa `patch.object` con archivos
temporales) y sobre el mecanismo de import de scripts que use
`tests/test_verify_pipeline.py` para `scripts/check_companion_paths.py`
(importlib desde path, si ese es el patrón ahí; si no, subprocess). Casos:

1. `check_extractors` con catálogo real → lista de errores vacía (regresión:
   las 21 entradas referencian archivos existentes y no hay huérfanos).
2. Fixture temporal: entrada con `"extractor": "src/extractors/no_existe.py"`
   → error "extractor no existe".
3. Fixture temporal: archivo `src/extractors/huerfano_extractor.py` creado en
   un árbol falso → error "extractor huérfano". (Usa `patch.object` sobre las
   constantes del módulo para apuntar a dirs temporales.)
4. Entrada sin campo `extractor` → error "falta el campo".
5. `sync_readme_extractor_table` sobre README temporal con marcadores:
   genera las 7 filas de dominio + fila derivado; `check_only=True` retorna
   `False` si el contenido difiere.
6. Dataset nuevo en catálogo fixture sin entrada en `_README_DATASET_DOMAINS`
   → `SystemExit`.

**Verification**: `./.venv/bin/pytest tests/test_pipeline_logic.py -v` → all
pass, incluyendo los ≥6 nuevos tests.

## Done criteria

- [ ] `python3 -c "import json; d=json.load(open('data/dataset_catalog_config.json')); assert all('extractor' in v for v in d.values())"` exit 0
- [ ] `python scripts/check_companion_paths.py registry` exit 0 (con la nueva validación activa)
- [ ] `make doctor` exit 0
- [ ] `make sync-docs && python scripts/sync_docs.py --check` exit 0
- [ ] `grep -c "START_EXTRACTOR_TABLE" README.md` → `1`
- [ ] `./.venv/bin/pytest tests/test_pipeline_logic.py -v` exit 0 con los nuevos tests
- [ ] `make lint && make format-check` exit 0
- [ ] `AGENTS.md` §12 ya no lista la tabla de extractores como pendiente
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- El catálogo tiene ≠21 entradas o alguna clave difiere de la tabla de mapeo
  (drift desde `6bf6b08`).
- La tabla manual de README ya no está en L682–694 o su contenido difiere del
  excerpt de "Current state" (alguien la editó; reconciliar antes de generar).
- El patrón `replace_delimited_block` no logra reproducir la tabla actual con
  el agrupamiento dado — NO cambies el agrupamiento editorial para "que calce";
  reporta la discrepancia.
- Aparece un extractor `*_extractor.py` no listado en la tabla de mapeo, o un
  dataset nuevo sin mapeo claro (p. ej. un segundo dataset derivado).
- Un step falla dos veces tras un intento razonable de fix.

## Maintenance notes

- **Al agregar un dataset nuevo** (flujo `AGENTS.md` §5): hay ahora TRES
  obligaciones mecánicas adicionales — campo `extractor` en el catálogo,
  entrada en `_README_DATASET_DOMAINS` y (si aplica) en
  `_AGENTS_EXTRACTOR_DESCRIPTIONS`. Las tres fallan ruidosamente
  (`SystemExit`/registry) si se olvidan: es intencional. Documentar el campo
  `extractor` en el Paso 3 de `AGENTS.md §5` es un follow-up barato; se dejó
  fuera de este plan para no re-editar §5 (fuera de scope) — sugerido al
  revisor como edición de 2 líneas en el mismo PR si hay acuerdo.
- Un dataset futuro con >2 extractores o con extractor fuera de
  `src/extractors/` requiere revisar `_extractor_paths`/el glob.
- En review, escrutar: que la tabla generada preserve EXACTAMENTE el
  agrupamiento editorial actual (la generación no debe re-clasificar datasets),
  y que `perfil_territorial_comunal` quede como `null` + fila "Derivado".
