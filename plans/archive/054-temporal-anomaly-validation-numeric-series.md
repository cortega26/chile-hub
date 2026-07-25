# Plan 054: Validación de anomalías temporales sobre las series numéricas (foso de confianza)

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada verificación
> antes de avanzar. Si ocurre algo de "STOP conditions", detente y reporta. Al terminar,
> actualiza la fila de estado en `plans/README.md`.
>
> **Principio de diseño no negociable de este plan**: la detección de anomalías
> **NO** debe abortar el build con `SystemExit`. Un salto grande **legítimo** (un shock
> cambiario real, una revisión de censo) trabaría el cron diario y bloquearía datos
> correctos. La anomalía se expresa como **advertencia + flag de drift**, y alimenta el
> **gate de publicación** (`§9`, que un humano puede override vía dispatch), no la
> validación que corta el build. Ver Step 3.
>
> **Drift check (córrelo primero)**:
> `git diff --stat 7ebf94b..HEAD -- src/validation.py src/builders/reports.py scripts/verify_pipeline.py`
> Ante discrepancia con los excerptos de "Estado actual", trátalo como STOP.

## Status

- **Priority**: P2 (foso de confianza; sigue a 053 en la secuencia — es seguro, no
  generador de demanda)
- **Effort**: M
- **Risk**: MED (mal diseñado, traba el cron o genera ruido de falsos positivos — por
  eso el gate correcto es publicación, no build)
- **Depends on**: none
- **Category**: direction (confiabilidad como diferenciador de producto)
- **Planned at**: commit `7ebf94b`, 2026-07-14

## Why this matters

El valor entero de `chile-hub` es **confianza**: "puedes cargar esto sin verificarlo".
Pero la validación actual es de **forma** (schema, integridad referencial, sumas de
cohortes), no de **valor**. Evidencia: [validate_indicadores](../src/validation.py#L297)
chequea que no esté vacío y que estén todos los códigos esperados — pero un grep por
outlier/rango/z-score/spike no devuelve nada.

Consecuencia concreta y cara: un valor de UF que llegue **10× equivocado** desde upstream
(un typo de la fuente, un cambio de unidad, un bug de parseo) **pasa todas las
validaciones y se publica**. El `drift_report` es descriptivo (su `drift_status` es un
enum `{healthy, drifted}` que
[verify_pipeline sólo valida estructuralmente](../scripts/verify_pipeline.py#L900-L904)),
no una compuerta sobre si el valor es sano. Publicar un dato *plausible en forma pero
falso en valor* es el peor modo de fallo para un producto cuya promesa es la
confiabilidad — es exactamente lo que erosiona la marca.

Los `indicadores` económicos son series temporales diarias **con histórico desde 2010**:
hay base de sobra para detectar "el valor de hoy está fuera de N desviaciones / saltó
más de X% respecto de la ventana reciente". Esto es infraestructura de confianza barata
y de alto retorno.

## Current state

- `src/validation.py:297` — `validate_indicadores(df_indicadores, metadata)`. Devuelve
  `{"dataset": "indicadores", "status": "error"|"ok", "record_count", "errors", "warnings", …}`.
  **Patrón clave**: usa dos listas — `errors` (→ `status: "error"` → el build **aborta**
  aguas arriba, invariante #2) y `warnings` (no fatal). Las señales blandas (fallback,
  backfill, series vacías) ya van a `warnings`, no a `errors`:
  ```python
  # src/validation.py (dentro de validate_indicadores)
  if row_count == 0:
      errors.append("indicadores dataset is empty")     # ← fatal
  ...
  if metadata and metadata.get("source_mode") == "fallback":
      warnings.append("indicadores source_mode is fallback; ...")   # ← no fatal
  ```
  **La anomalía va a `warnings` (y al flag de drift), nunca a `errors`.**
- `src/builders/reports.py:361` — `build_drift_report(dataset_catalog)`; lee
  `drift.status` por dataset (`drift_status = drift.get("status", "healthy")`, `:370`) y
  `recommended_action` (`:391`). `drift_status ∈ {healthy, drifted}`.
- `scripts/verify_pipeline.py` — el gate de publicación. `fail(msg)` (`:115-117`) hace
  `SystemExit(1)` para **rechazar la publicación** (distinto de abortar el build). Ya
  rechaza fallback/stale/fetch fallido (`§9`). Un humano puede override esperando el
  siguiente `schedule` o via `workflow_dispatch`.
- Histórico: `indicadores` tiene `codigo_indicador`, `fecha`, `valor` con datos desde
  2010 → base para la ventana de referencia.

Convenciones:

- **Invariante #2** (`AGENTS.md:224`): fallar ruidoso ante errores de **validación**. La
  anomalía **no** es un error de validación de datos malformados; es una **sospecha
  estadística** que puede ser un valor real. Por eso su lugar correcto es advertencia +
  gate de publicación humano-override, no `SystemExit` del build.
- Cada `validate_*` se registra en el bloque `validations = {…}` de `build_dev_db.py` y
  su test compañero en `tests/test_validation.py` (gate `check_companion_paths.py`).

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Tests de validación (no requieren normalized) | `./.venv/bin/pytest tests/test_validation.py -v` | pasan |
| Build (ejercita drift/health) | `make build` | exit 0 |
| Gate de publicación (dry) | `./.venv/bin/python scripts/verify_pipeline.py` | exit 0 en datos sanos |
| Registro de validaciones | `./.venv/bin/python scripts/check_validation_registration.py` | exit 0 |
| Lint / format | `make lint && make format-check` | exit 0 |

## Scope

**In scope**:

- `src/validation.py` — función de detección de anomalías + integración en
  `validate_indicadores` (a `warnings`, con detalle estructurado).
- `tests/test_validation.py` — tests de la detección (gate de co-cambio).
- `src/builders/reports.py` (y/o `src/chile_hub/pipeline_status_utils.py`) — propagar la
  anomalía al `drift_report`/health como `drifted` + `recommended_action`.
- `scripts/verify_pipeline.py` + `tests/test_verify_pipeline.py` — señal de anomalía en
  el gate de publicación (bloqueante-pero-override), **no** en el build.
- `docs/adr/ADR-013-validacion-de-anomalias-temporales.md` (lo escribe el executor;
  documenta el umbral elegido y por qué es warn+gate, no abort).
- `plans/README.md` — fila de estado.

**Out of scope (NO tocar)**:

- **La rama `errors` de cualquier `validate_*`.** La anomalía nunca va a `errors` (eso
  abortaría el build). Frontera dura.
- Otros datasets numéricos que no sean series temporales con histórico
  (`finanzas_municipales`, etc. son anuales de un corte; empezar solo por `indicadores`).
- El umbral no debe hardcodearse de forma que un shock legítimo quede permanentemente
  bloqueado sin ruta de override.

## Git workflow

- Branch: `advisor/054-anomaly-validation`
- Conventional commits (ej. `feat(validation): detecta anomalías temporales en indicadores`).
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Función pura de detección de anomalías

En `src/validation.py`, agrega una función pura `detect_series_anomalies(df, *, value_col="valor", key_col="codigo_indicador", date_col="fecha", z_threshold=..., min_history=...)` que, por cada serie (`codigo_indicador`), compare el valor más reciente contra una ventana de referencia del histórico y devuelva una lista de anomalías estructuradas: `[{"codigo_indicador", "fecha", "valor", "esperado_rango", "z_score", "motivo"}]`. Elige un método robusto y documenta el umbral en ADR-013 (recomendación: z-score sobre variación logarítmica / MAD robusto, o "salto relativo > X% vs mediana de la ventana"; evita media±σ simple que es frágil a outliers). Requiere `min_history` observaciones antes de emitir señal (no marques series nuevas o cortas).

**Verify**: `./.venv/bin/python -c "import polars as pl; from src.validation import detect_series_anomalies; df=pl.DataFrame({'codigo_indicador':['uf']*6,'fecha':['2026-01-0'+str(i) for i in range(1,7)],'valor':[100.0,100.1,100.2,100.1,100.3,1000.0]}); a=detect_series_anomalies(df, z_threshold=4.0, min_history=4); assert len(a)==1 and a[0]['codigo_indicador']=='uf'; print('anomalía detectada:', a[0]['motivo'])"` → detecta el salto 100→1000.

### Step 2: Integra como WARNING en `validate_indicadores` (nunca error)

Llama a `detect_series_anomalies` dentro de `validate_indicadores` y, por cada anomalía,
agrega una entrada a `warnings` (patrón de las señales blandas existentes) **y** expón la
lista estructurada en el dict de retorno bajo una clave nueva (p. ej. `"anomalies"`) para
que los reportes la consuman. **No** agregues nada a `errors`.

**Verify**: `./.venv/bin/python -c "import polars as pl; from src.validation import validate_indicadores; df=pl.DataFrame({'codigo_indicador':['uf']*6,'fecha':['2026-01-0'+str(i) for i in range(1,7)],'valor':[100,100.1,100.2,100.1,100.3,1000.0]}); r=validate_indicadores(df, None); assert r['status']!='error'; assert any('anomal' in w.lower() for w in r['warnings']); print('status:', r['status'], '| warnings con anomalía OK')"` → `status` NO es `error`, hay warning de anomalía.

### Step 3: Propaga a drift + gate de publicación (override-able), no al build

**Flujo de datos (léelo antes de codificar)**: `verify_pipeline.py` NO ve el retorno
en memoria de `validate_indicadores`; sólo lee **artefactos persistidos**
(`drift_report.json`, `dataset_status.json`, etc.). Por lo tanto la señal de anomalía
debe viajar así: `validate_indicadores` la marca → se **persiste** en el `drift_report`
(como `drift_status: "drifted"` + `recommended_action`) durante el build → el gate de
publicación **lee ese artefacto**. Sin el paso de persistencia del punto 1, el punto 2
no tiene nada que leer.

Dos integraciones, ambas **no fatales para el build**:

1. **Drift/health** (`src/builders/reports.py` / `pipeline_status_utils.py`): cuando
   `indicadores` reporte anomalías, refleja `drift_status: "drifted"` con un
   `recommended_action` accionable (ej. "Revisar valor atípico en <codigo> del <fecha>;
   confirmar con la fuente antes de publicar"). Reusa la maquinaria existente de drift;
   no inventes un canal nuevo.
2. **Gate de publicación** (`scripts/verify_pipeline.py`): agrega una comprobación que,
   en modo publicación (`--require-live`), trate una anomalía no reconocida como motivo
   de **rechazo de publicación** (`fail(...)`), igual que ya trata fallback/stale. Clave:
   esto **bloquea la publicación automática, no el build** — el mantenedor puede override
   esperando revisión o via `workflow_dispatch`. Documenta en ADR-013 cómo se reconoce/
   silencia una anomalía confirmada como legítima (p. ej. un allowlist en
   `source_registry.json` o un umbral por indicador) para no trabar el cron
   indefinidamente ante un shock real.

**Verify**: `make build && ./.venv/bin/python scripts/verify_pipeline.py` → exit 0 con los
datos sanos actuales (sin anomalías reales, el gate no rompe nada); y el `drift_report`
generado tiene el esquema válido: `./.venv/bin/pytest tests/test_verify_pipeline.py -v` → pasa.

### Step 4: ADR-013 + registro

Crea `docs/adr/ADR-013-validacion-de-anomalias-temporales.md` (formato de los ADR;
plantilla `docs/adr/ADR-005-contratos-esquema-json-schema.md`). Documenta: el método y
umbral elegidos; **por qué es warn+gate de publicación y no `SystemExit` del build**; el
alcance inicial (solo `indicadores`); y la ruta de override para shocks legítimos. Corre
el registro de validaciones.

**Verify**: `test -f docs/adr/ADR-013-validacion-de-anomalias-temporales.md && ./.venv/bin/python scripts/check_validation_registration.py` → exit 0.

## Test plan

- `tests/test_validation.py`:
  - `detect_series_anomalies`: (a) detecta un salto 10× inyectado; (b) NO marca una serie
    estable con ruido normal; (c) NO marca una serie con menos de `min_history` puntos;
    (d) un shock monotónico gradual (tendencia real) no dispara falso positivo con el
    método elegido.
  - `validate_indicadores` con anomalía: `status != "error"`, warning presente,
    `anomalies` poblado en el retorno.
  - **Regresión de contrato de valor**: un caso que documente el incidente motivante
    (patrón `AGENTS.md §8`): "un valor 10× fuera de rango se publicaba sin señal; este
    test falla sin la detección y pasa con ella".
- `tests/test_verify_pipeline.py`: el gate rechaza publicación ante anomalía no
  reconocida, y **permite** el build (no `SystemExit` en fase build).

**Verify**: `./.venv/bin/pytest tests/test_validation.py tests/test_verify_pipeline.py -v` → todos pasan, incluidos los nuevos.

## Done criteria

- [ ] `detect_series_anomalies` existe y detecta un salto 10× inyectado en un test.
- [ ] La anomalía aparece en `warnings` de `validate_indicadores`, **nunca** en `errors`; `status` de una serie con anomalía puntual no es `"error"`.
- [ ] `grep -n "errors.append" src/validation.py` no muestra ninguna línea que agregue una anomalía a `errors` (verificación de la frontera dura).
- [ ] La anomalía se refleja como `drift_status: "drifted"` + `recommended_action` en el reporte de drift/health.
- [ ] El gate de publicación (`verify_pipeline.py --require-live`) rechaza publicación ante anomalía no reconocida, con ruta de override documentada; el **build** no se aborta.
- [ ] ADR-013 existe y justifica warn+gate vs abort.
- [ ] `check_validation_registration.py` exit 0; `make lint && make format-check` exit 0.
- [ ] `make build && ./.venv/bin/pytest tests/test_validation.py tests/test_verify_pipeline.py` exit 0 con los tests nuevos.
- [ ] `git status` sin archivos fuera de "In scope".
- [ ] Fila de estado en `plans/README.md` actualizada.

## STOP conditions

Detente y reporta si:

- Te ves agregando la anomalía a `errors` / un `SystemExit` en la fase build para "fallar
  ruidoso" — para: eso trabaría el cron ante un shock legítimo. Es warn + gate de
  publicación override-able.
- No hay suficiente histórico en `indicadores` para una ventana de referencia estable
  (menos de `min_history` por serie en los datos reales) — reporta; no bajes el umbral
  hasta volverlo ruido.
- El método elegido genera falsos positivos sobre los datos reales actuales al correr
  `make build` (el gate rompería publicaciones sanas) — recalibra el umbral **una vez** y,
  si persiste, reporta antes de relajar la señal a inútil.
- `validate_indicadores`, `build_drift_report` o `verify_pipeline.py` no coinciden con
  "Estado actual" (drift desde `7ebf94b`).
- Cualquier verificación falla dos veces tras un intento razonable.

## Maintenance notes

- **Esto es seguro, no marketing**: 054 protege la marca ("chile-hub nunca publica
  basura") pero no genera demanda como 053. Si la prioridad es la estrategia
  construir-oferta→demanda (ADR-011), 053 va primero; 054 lo respalda.
- **Extensión futura**: una vez estable en `indicadores`, el mismo `detect_series_anomalies`
  puede aplicarse a otras series con histórico (censo intercensal, finanzas municipales
  año a año). No lo hagas aquí — valida primero el diseño en `indicadores`.
- **Qué escrutar en el PR**: (1) que ninguna anomalía llegue a `errors`; (2) que exista
  ruta de override para shocks legítimos (si no, el primer shock real traba el proyecto);
  (3) que el umbral esté justificado con datos, no elegido a ojo.
- **Interacción con el gate**: si el Plan 051 (capa HTTP) o cambios en `verify_pipeline`
  aterrizan después, revisar que la señal de anomalía siga enganchada al `--require-live`.
