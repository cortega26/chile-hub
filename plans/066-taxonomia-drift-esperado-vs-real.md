# Plan 066: Separar drift esperado de drift real en el dashboard de salud

> **Executor instructions**: Sigue cada paso y su gate de verificación. Este plan
> **no repara datos**: corrige la clasificación de estados. Si en algún paso la
> única forma de bajar un contador es tocando datos o relajando un gate, es una
> STOP condition — repórtalo, no improvises. No corras `make refresh` sin red
> (todos los extractores caerían a fallback y fabricarías drift falso). Actualiza
> la fila de este plan en `plans/README.md` sólo cuando todos los done criteria
> sean verdaderos.
>
> **Drift check (córrelo primero)**: `git diff --stat b79461f..HEAD -- src/builders/metadata.py src/builders/reports.py src/chile_hub/pipeline_status_utils.py src/validation.py scripts/verify_pipeline.py contracts/datasets/ app.js`
> Si el comportamiento real difiere de "Estado actual", DETENTE en vez de cambiar
> silenciosamente el contrato de estados.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (toca el vocabulario del dashboard público de salud y contadores
  que la landing renderiza; ningún cambio de dato)
- **Depends on**: ninguno
- **Category**: correctness / observabilidad
- **Planned at**: commit `b79461f`, 2026-07-26

## Por qué importa

`hub_health.json` (snapshot 2026-07-21) reporta `drifted_count: 8` y
`warn_count: 7` sobre 19 datasets. La auditoría dataset por dataset muestra que
**4 de los 8 "drifted" son un bug de clasificación, no un problema de datos**:

| Dataset | Realidad | Por qué se marca drifted hoy |
|---|---|---|
| `perfil_territorial_comunal` | derivado de capas validadas, 346/346, **0 warnings** | su `source_mode` se calcula `"live" if all(upstream == "live") else "fallback"`; `finanzas_municipales` es `monthly` → cae a `fallback` |
| `finanzas_municipales` | 345/346, 0 warnings; su contrato **ya declara** `coverage_policy: "partial_expected"` | `build_coverage` nunca lee `coverage_policy` |
| `indicadores_urbanos_siedu` | cobertura urbana intencional (0.3382); contrato **ya declara** `partial_expected` | idem, más un warning informativo |
| `pobreza_comunal` | SAE 345/346, "parcial por diseño" según su propio warning | cualquier warning ⇒ `degradation: warning` ⇒ drifted |
| `partidos_politicos` | 36/36, `estado_legal` poblado en 15/36 (dato de SERVEL, no un fallo) | idem |

Los otros 3 son legítimos: `empresas` (1 RUT inválido), `indicadores` (reusó el
artefacto publicado para `ipc`) y `consumo_electrico_comunal` (fuente
decomisionada por CNE, AGENTS.md §6).

El costo de no arreglarlo es que el dashboard público entrena a sus lectores a
ignorar `drifted_count`: si 4 de 8 alarmas son ruido estructural, la señal de las
4 reales se pierde. `plans/README.md` dejó explícitamente fuera de alcance el
"vocabulario del dashboard de salud" en la auditoría 2026-07-13; este plan cierra
ese pendiente.

## Estado actual

- **El predicado único de drift** — `src/builders/metadata.py:228-234`:

  ```python
  drift_status = "healthy"
  if (
      source_mode == "fallback"
      or coverage_status in {"partial", "unknown"}
      or degradation_status in {"warning", "degraded"}
  ):
      drift_status = "drifted"
  ```

  No existe un concepto de "parcial esperado" ni de "warning informativo".

- **`build_coverage`** (`metadata.py:161-218`) sólo honra
  `dataset_metadata["coverage"]["status"] == "partial_expected"` — que **únicamente
  `src/extractors/siedu_extractor.py:320` produce** — y aun así lo colapsa a
  `"partial"` a secas, destruyendo la señal antes de que `build_drift` la vea.
  **No lee `coverage_policy` del contrato**, pese a que `load_schema_contract` ya
  está importado y se usa en el mismo `enrich_dataset_metadata` (`metadata.py:263`).

- **`coverage_policy` ya existe en los 22 contratos** de `contracts/datasets/`:
  `full` (8), `not_applicable` (4), `roster` (3), `partial_expected` (4:
  `delincuencia_comunal`, `finanzas_municipales`, `indicadores_urbanos_siedu`,
  `resultados_educacionales`), `partial` (2: `geometria_comunal`,
  `pobreza_comunal`).

- **`build_degradation`** (`metadata.py:117-158`): tras los casos especiales de
  fallback, `if warnings: return {"status": "warning", ...}`. Todo warning pesa
  igual. Los 3 warnings "por diseño" se emiten en `src/validation.py:530`
  (SIEDU), `:931` (pobreza SAE) y `:1114` (partidos/SERVEL).

- **`source_mode` de la capa derivada** — `metadata.py:488-503`:

  ```python
  "source_mode": "live"
  if all(
      metadata.get("source_mode") == "live"
      for metadata in (comunas_metadata, ..., finanzas_metadata, ...)
  )
  else "fallback",
  ```

  `scripts/verify_pipeline.py:108-113` ya define
  `VALID_SOURCE_MODES = {"live", "fallback", "monthly"}` y
  `NON_FALLBACK_SOURCE_MODES = {"live", "monthly"}`, con el comentario explícito
  de que `monthly` es "genuinamente obtenido de la fuente". El predicado de arriba
  contradice esa definición.

- **`severity` de `hub_health`** — `src/chile_hub/pipeline_status_utils.py:241-247`:

  ```python
  severity = "ok"
  if validation_status != "ok":        severity = "error"
  elif freshness_status in {"stale", "unknown"}: severity = "warn"
  elif source_mode == "fallback" or warning_count > 0: severity = "warn"
  ```

- **Gates de enum** (no los relajes): `drift_status ∈ {healthy, drifted}` se valida
  en `scripts/verify_pipeline.py` líneas 654, 901, 1124, 1317, 1412, 1511;
  `coverage_status` en 893, 1119, 1312, 1418, 1506; `source_mode` contra
  `VALID_SOURCE_MODES`. **Este plan no agrega valores a ningún enum.**

- **Landing**: `app.js:120` mapea `fallback: "respaldo"`; `app.js:178` decide el
  badge de atención con `drift?.status === "drifted" || degradation?.status ===
  "warning" | "degraded"`; `app.js:659-688` renderiza `fallback_count`,
  `drifted_count` y las píldoras `source_mode` / `coverage_status` / `drift_status`.

## Comandos que vas a necesitar

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Build de artefactos | `make build` | exit 0 |
| Verificación de integridad | `make verify` | exit 0 |
| Tests focales | `uv run pytest tests/test_pipeline_logic.py tests/test_verify_pipeline.py -v` | todos pasan |
| Regresión completa | `make test` | exit 0 |
| Landing sincronizada | `make verify-landing` | exit 0 |
| Calidad | `make lint && make format-check` | exit 0 |
| Gate global | `make doctor` | exit 0 |

## Alcance

**En alcance**:

- `src/builders/metadata.py` — `build_coverage`, `build_degradation`, `build_drift`
  y el `source_mode` de `perfil_territorial_comunal`.
- `src/chile_hub/pipeline_status_utils.py` — `build_hub_health` (severity).
- `src/builders/reports.py` — contadores de `build_drift_report` si cambian de
  semántica.
- `src/validation.py` — **sólo** para marcar como esperados los 3 warnings ya
  existentes (líneas 530, 931, 1114). Ninguna regla de validación nueva ni
  eliminada.
- `contracts/datasets/pobreza_comunal.schema.json` — evaluar `partial` →
  `partial_expected` (ver Step 2).
- `scripts/verify_pipeline.py` — gates para los campos nuevos.
- `app.js` / `index.html` — vocabulario y badge de atención.
- Tests, `docs/datasets/`, ADR-013, `plans/README.md`.

**Fuera de alcance**:

- **Los 3 problemas de datos reales**: `empresas` (RUT inválido), `indicadores`
  (`ipc` reusado) y `consumo_electrico_comunal` (fuente muerta). Van como issues
  separados (Step 6); son de otra naturaleza y no deben mezclarse con un cambio
  de taxonomía.
- Agregar valores a `VALID_SOURCE_MODES`, a `coverage_status` o un tercer
  `drift_status`.
- Correr extractores (`make extract` / `make refresh`), tocar `data/raw/`,
  cambiar reglas de validación, o el historial de salud (Plan 063).

## Git workflow

- Branch: `advisor/066-drift-taxonomy`
- Commits sugeridos, uno por paso: `fix(metadata): …`, `feat(health): …`
- No hagas push ni merge sin instrucción explícita del operador.

## Pasos

### Step 0: Reproduce el baseline antes de tocar nada

Todos los conteos de este plan (8 drifted, 7 warn) salen del snapshot de
`data/normalized/` con fecha **2026-07-21**, que llegó por un commit de refresh
diario de CI. Tu `data/staging/` local (30 archivos al momento de escribir esto)
puede provenir de otro build. Si el baseline no reproduce, el primer `verify` del
Step 1 falla por razones ajenas al cambio y vas a perseguir un fantasma.

Corre `make build && make verify` **sin ninguna modificación** y confirma:

```
python3 -c "import json; d=json.load(open('data/normalized/hub_health.json')); print(d['dataset_count'], d['drifted_count'], d['warn_count'], d['overall_status'])"
```

→ `19 8 7 warn`, y que los 8 drifted sean exactamente `indicadores`,
`finanzas_municipales`, `indicadores_urbanos_siedu`, `perfil_territorial_comunal`,
`empresas`, `pobreza_comunal`, `consumo_electrico_comunal`, `partidos_politicos`.

**Si no reproduce, DETENTE y repórtalo.** A partir de aquí el 8→3 es un delta
contra un baseline verificado, no contra un JSON en disco. No corras `make
extract` ni `make refresh` para "arreglar" el baseline.

### Step 1: Corrige el `source_mode` de la capa derivada

`monthly` ya está definido en el repo como fuente genuina
(`NON_FALLBACK_SOURCE_MODES`), pero el predicado de
`perfil_territorial_comunal` exige `== "live"` en los 9 upstreams. Con
`finanzas_municipales` en `monthly`, la capa derivada se declara `fallback`
teniendo 346/346 filas y cero warnings.

Reemplaza la comparación literal por pertenencia al conjunto no-fallback. Importa
el conjunto desde un único lugar (o defínelo en `metadata.py` y haz que
`verify_pipeline.py` lo consuma) para que no queden dos definiciones capaces de
divergir — CLAUDE.md regla anti-drift.

No agregues un `source_mode: "derived"`. La derivación ya está expresada en
`source_detail: "derived_from_validated_chile_hub_layers"` y en
`notes: ["derived_dataset", "upstreams: …"]`; un enum nuevo cuesta seis gates y no
compra información.

**Verifica**: `make build && python3 -c "import json; d=json.load(open('data/normalized/drift_report.json')); e=[x for x in d['datasets'] if x['dataset']=='perfil_territorial_comunal'][0]; print(e['source_mode'], e['drift_status'])"`
→ `live healthy`. Y un test unitario que fije el contrato: con un upstream en
`monthly` y el resto en `live`, la capa derivada **no** es `fallback`; con un
upstream en `fallback` real, **sí** lo es.

### Step 2: Haz que `build_coverage` honre el `coverage_policy` del contrato

`coverage_policy` ya existe en los 22 contratos y hoy se ignora. Conéctalo:

1. En `build_coverage`, carga el contrato (o recibe el ya cargado desde
   `enrich_dataset_metadata`, que lo tiene en `metadata.py:263` — preferible, para
   no duplicar I/O).
2. Cuando el resultado sea `status: "partial"` **y** `coverage_policy ==
   "partial_expected"`, agrega al dict de coverage un campo booleano nuevo
   **`expected: true`** con un `expected_reason` textual. **No cambies el valor de
   `status`**: el enum está gateado en cinco puntos de `verify_pipeline.py` y
   `partial` sigue siendo la descripción correcta de la cobertura.
3. Cuando el `status` no sea `partial`, emite `expected: false` de forma explícita
   (nunca ausente) para que el campo sea siempre inspeccionable.
4. Mantén la rama existente que lee `partial_expected` desde el metadata del
   extractor (SIEDU); ahora debe producir el mismo `expected: true`. Las dos rutas
   convergen en un solo campo.

Sobre `pobreza_comunal`: su contrato dice `coverage_policy: "partial"` pero su
propio warning dice "parcial por diseño; comunas sin muestra no tienen
estimación". Su `coverage_status` es `not_applicable` (no tiene
`expected_record_count`), así que su drift viene del Step 3, no de aquí. Corrige
el contrato a `partial_expected` **sólo** si documentas la justificación en
`docs/datasets/pobreza_comunal.md`; si no, déjalo y anótalo como pregunta abierta
en el ADR. Lo mismo aplica a `geometria_comunal`.

**Alcance real: cuatro datasets, no dos.** `coverage_policy: "partial_expected"`
está en **4** contratos: `finanzas_municipales`, `indicadores_urbanos_siedu`,
`resultados_educacionales` y `delincuencia_comunal`. Sólo los dos primeros están
hoy en el set drifted; los otros dos calculan `coverage_status` distinto de
`partial` (sin `expected_record_count`, o actual ≥ esperado), así que el flag les
queda **inerte por ahora**. Eso no los excluye del cambio: si alguno pasara a
`partial` en un build futuro, quedaría `expected: true` y dejaría de driftar sin
que ningún test lo haya ejercitado. Trátalos como parte del alcance desde el
inicio.

**Verifica**: los **4** datasets con `coverage_policy: "partial_expected"` quedan
con `coverage.expected == true` cuando su cobertura es `partial`; para
`resultados_educacionales` y `delincuencia_comunal` documenta en el test que hoy
el flag es inerte y por qué. Los de `coverage_policy: "full"` quedan con
`expected == false`. Test unitario por cada valor de `coverage_policy`
(`full`, `not_applicable`, `roster`, `partial`, `partial_expected`).

### Step 3: Distingue warnings informativos de warnings accionables

Tres warnings describen diseño confirmado, no degradación:
`src/validation.py:530` (SIEDU urbano), `:931` (cobertura SAE) y `:1114`
(`estado_legal` vía SERVEL).

Marca el origen, no el consumidor — clasificar por regex sobre el texto en
`build_degradation` se rompe la primera vez que alguien reformule el mensaje.
Diseño requerido:

1. El dict que devuelven los validadores gana una lista `expected_warnings` con el
   subconjunto de `warnings` que es informativo. **`warnings` sigue conteniendo
   todos los mensajes**, sin excepción: es el registro transparente y hay gates y
   tests que lo asumen.
2. `build_degradation` calcula los accionables como `warnings` menos
   `expected_warnings`. Devuelve `status: "warning"` sólo si quedan accionables;
   si todos eran esperados, `status: "none"` con un `impact` que **enumere los
   warnings esperados** (no los escondas: "3 observaciones esperadas: …") y
   `recommended_action: "Ninguna."`.
3. `build_hub_health` gana `actionable_warning_count` junto al `warning_count`
   existente, y la línea de severity (`pipeline_status_utils.py:246`) pasa a usar
   el accionable. `warning_count` no cambia de significado en ningún artefacto.

**Verifica**: `pobreza_comunal` y `partidos_politicos` quedan
`degradation: none`, `drift: healthy`, `severity: ok`, con `warning_count: 1` y
`actionable_warning_count: 0`. `empresas` sigue en `warning` / `drifted` /
`warn` con sus 3 warnings accionables. Test que pruebe que un warning **no**
declarado como esperado sigue degradando (evita que esto se vuelva un silenciador
genérico).

### Step 4: Actualiza `build_drift` y los gates

Con los campos nuevos en su lugar, `build_drift` (`metadata.py:221-253`) pasa a:

- no marcar drift por cobertura cuando `coverage.expected is True`;
- seguir marcando drift por `source_mode == "fallback"`, por
  `coverage_status == "unknown"` y por `degradation_status ∈ {warning, degraded}`
  (que ahora ya sólo refleja accionables);
- cuando marque drift, que el `summary` diga cuál de las tres condiciones lo
  disparó, no las tres a la vez.

En `scripts/verify_pipeline.py` agrega gates para los campos nuevos:
`coverage.expected` booleano y presente siempre; `actionable_warning_count`
entero y `<= warning_count`. **No toques** las validaciones de enum existentes.

**Ya verificado (2026-07-26): `verify_pipeline.py` no valida conjuntos exactos de
claves.** Los bloques `REQUIRED_*` (p. ej. `scripts/verify_pipeline.py:1085-1093`)
recorren claves obligatorias con `if health.get(key) is None: fail(...)`, y los
enums usan pertenencia (`not in {...}`). El único conjunto exacto es de **nombres
de dataset**, no de claves: `if dataset_names != REQUIRED_DATASETS`
(`verify_pipeline.py:1096-1098`). Por lo tanto agregar `coverage.expected` y
`actionable_warning_count` **no rompe `make verify`** por sí solo, y este paso es
"agregar gates", no "registrar claves y luego agregar gates".

**Verifica**: `make build && make verify` → exit 0, y
`python3 -c "import json; d=json.load(open('data/normalized/hub_health.json')); print(d['drifted_count'], d['warn_count'], d['overall_status'])"`
→ `3 3 warn`. Los 3 restantes deben ser exactamente `empresas`, `indicadores` y
`consumo_electrico_comunal`. **Si el conteo no da exactamente eso, DETENTE**: o
quedó un caso sin clasificar o silenciaste uno de más.

### Step 5: Sincroniza landing, documentación y ADR

- `app.js:178`: el badge de atención debe usar los accionables, no
  `degradation?.status` a secas — si no, el drawer seguirá marcando datasets ya
  clasificados como sanos.
- Píldoras de `app.js:684-688`: la cobertura parcial esperada debe distinguirse
  visualmente de la parcial inesperada (p. ej. `partial` vs `partial esperada`).
  El vocabulario en español ya vive en el mapa de `app.js:120`.
- Corre `make verify-landing` y `python3 scripts/check_landing_sync.py` (el gate
  agregado el 2026-07-26): un cambio de vocabulario que no pase por ahí se
  convierte en deriva silenciosa.
- Escribe **ADR-013** (el siguiente libre; el último es ADR-012) documentando:
  por qué no se agregó un tercer `drift_status`, por qué `warnings` conserva todos
  los mensajes, quién puede declarar un warning como esperado, y las preguntas
  abiertas de `pobreza_comunal` / `geometria_comunal` del Step 2.
- Actualiza `docs/datasets/` de los 5 datasets reclasificados explicando que su
  parcialidad es de diseño, y `docs/backlog/05-dashboard-publico-salud.md` si
  describe la semántica vieja.

**Verifica**: `make verify-landing && make doctor` → exit 0.

### Step 6: Registra los 3 problemas reales como trabajo separado

No los arregles aquí. Abre un issue por cada uno, con el diagnóstico ya conocido:

1. **`empresas`** — `found 1 RUTs with invalid format`. Decidir si se descarta la
   fila, se corrige el DV o se acepta como ruido conocido de la fuente CKAN.
2. **`indicadores`** — `live refresh reused last published artifact for missing
   codes: ipc`. Investigar por qué falta `ipc` en el refresh live.
3. **`consumo_electrico_comunal`** — CNE decomisionó el catálogo Junar
   (permanente desde 2026-07-07, AGENTS.md §6); quedan 3 filas de muestra. La
   decisión es de producto: deprecar el dataset, buscar fuente de reemplazo, o
   declararlo retirado. **No es reparable por código** y su `drifted` actual es
   correcto — debe seguir apareciendo en rojo.

**Verifica**: los 3 issues existen y este plan los referencia por número.

## Test plan

- `source_mode` derivado: upstream `monthly` no contamina; upstream `fallback` sí.
- `build_coverage` para cada valor de `coverage_policy` (`full`,
  `not_applicable`, `roster`, `partial`, `partial_expected`), incluida la ruta del
  metadata del extractor (SIEDU).
- `build_degradation`: sólo esperados → `none`; mezcla → `warning` con los
  accionables en `impact`; warning no declarado → `warning`.
- `build_drift`: parcial esperada no drifta; parcial inesperada sí; `unknown` sí;
  fallback sí.
- `build_hub_health`: `warning_count` intacto, `actionable_warning_count` nuevo,
  severity derivada del accionable.
- `verify_pipeline`: los gates nuevos fallan ante campos ausentes o
  `actionable_warning_count > warning_count`.
- Regresión de artefactos: `make build && make verify && make test`.
- Guardrail: un test que fije `drifted_count == 3` sobre el fixture, para que una
  regresión futura de clasificación sea ruidosa.

## Done criteria

- [ ] El baseline del Step 0 reprodujo `19 8 7 warn` con los 8 datasets esperados
      **antes** de la primera modificación.
- [ ] `drifted_count` baja de 8 a **3**, y esos 3 son `empresas`, `indicadores` y
      `consumo_electrico_comunal`.
- [ ] Los **4** contratos con `coverage_policy: "partial_expected"` están cubiertos
      por tests, incluidos los dos donde el flag es inerte hoy.
- [ ] `warn_count` baja de 7 a **3**; `overall_status` sigue siendo `warn`.
- [ ] Ningún enum (`drift_status`, `coverage_status`, `source_mode`) ganó valores.
- [ ] Ningún gate de `verify_pipeline.py` fue relajado; se agregaron gates para los
      campos nuevos.
- [ ] `warnings` sigue conteniendo todos los mensajes en todos los artefactos.
- [ ] Cero cambios en `data/raw/`, en reglas de validación y en datos extraídos.
- [ ] `make build && make verify && make test && make verify-landing && make lint && make format-check && make doctor` → todos exit 0.
- [ ] ADR-013 escrito; `docs/datasets/` de los 5 reclasificados actualizados.
- [ ] Los 3 issues del Step 6 abiertos y referenciados.
- [ ] `tests/e2e/verify_066.sh` escrito y en verde.

## STOP conditions

- Bajar un contador exige tocar datos, `data/raw/`, o eliminar/relajar una regla
  de validación.
- Un enum gateado necesitaría un valor nuevo para que el diseño funcione.
- Tras el Step 4 el conteo no da exactamente 3 drifted con los 3 datasets
  esperados.
- Un dataset **sin** declaración de "esperado" en contrato o validador cambia de
  `drifted` a `healthy` — eso es un silenciador, no una reclasificación.
- `make verify-landing` o `check_landing_sync.py` fallan y la única salida
  aparente es saltarse el gate.

## Notas de mantenimiento

El riesgo permanente de este cambio es que `expected_warnings` se convierta en un
basurero donde se archiva cualquier warning molesto. Mitigación: la declaración
vive junto a la regla que emite el warning (`validation.py`) o en el contrato
(`coverage_policy`), nunca en el consumidor, y el ADR fija quién puede agregar una
entrada y con qué justificación. En cada revisión de salud, audita la lista de
esperados antes que la de accionables: un `drifted_count` que baja sin que baje el
trabajo real es la falla de modo de este diseño.
