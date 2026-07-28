# ADR-013: Validación de anomalías temporales sobre series numéricas

**Fecha:** 2026-07-25
**Estado:** accepted
**Decision:** Se agrega `detect_series_anomalies()` en `src/validation.py`, un
detector de saltos atípicos (z-score robusto MAD sobre log-retornos) integrado en
`validate_indicadores()` como **warning**, nunca como `error`. La señal se
propaga al `drift_report` (vía `build_degradation()`/`build_drift()`, sin canal
nuevo) y al gate de publicación (`scripts/verify_pipeline.py`, perfil
`publication`), que la trata como motivo de **rechazo de publicación
override-able** — nunca aborta el build.

## Contexto

El valor entero de chile-hub es confianza: "puedes cargar esto sin verificarlo".
La validación existente es de **forma** (schema, integridad referencial, sumas de
cohortes), no de **valor**: `validate_indicadores` chequeaba que la serie no
estuviera vacía y que estuvieran todos los códigos esperados, pero nada detectaba
un valor 10× equivocado (typo de fuente, cambio de unidad, bug de parseo) que
pasa todas las validaciones de forma y se publica.

Los `indicadores` económicos (UF, Dólar, Euro, UTM, IPC) son series diarias con
histórico desde 2010 — base de sobra para una ventana de referencia estadística.

## Decision

### 1. Método: z-score robusto (MAD) sobre log-retornos

`detect_series_anomalies(df, *, value_col="valor", key_col="codigo_indicador",
date_col="fecha", z_threshold=4.0, min_history=4)` agrupa por serie, ordena por
fecha, calcula el log-retorno día a día (`ln(v[i]/v[i-1])`), y compara el
**último** log-retorno contra la mediana y el MAD (median absolute deviation) de
los log-retornos de referencia (todos los anteriores). Requiere al menos
`min_history` log-retornos de referencia antes de evaluar — series nuevas o
cortas no emiten señal.

**Por qué MAD y no media±desviación estándar simple**: la media y el sigma
clásico son frágiles ante los propios outliers que se buscan detectar — un solo
salto histórico grande infla el sigma y esconde saltos futuros de magnitud
similar. La mediana y el MAD son robustos a esa contaminación.

**Por qué log-retornos y no el valor absoluto**: comparar el *cambio relativo*
día a día (no el nivel) hace que la señal sea invariante a la escala de cada
indicador (UF ~40.000, Dólar ~900) y naturalmente tolerante a una tendencia real
gradual (inflación, apreciación sostenida) — una serie que sube un 1% diario
consistente no dispara la señal, porque su log-retorno más reciente no difiere
del histórico de log-retornos.

**Calibración de umbrales** (verificada contra los datos reales del repo,
`data/normalized/indicadores.parquet`, 506 filas): con `z_threshold=4.0` y
`min_history=4`, el z-score máximo observado en el histórico real es ~3.8
(dólar/euro) — cero falsos positivos con margen razonable. Se probaron además
los casos adversariales del test plan: serie estable con ruido normal (sin
señal), serie corta bajo `min_history` (sin señal, incluso con un salto 10×
inyectado), y tendencia monotónica gradual real (sin señal, por diseño del
método vía log-retornos).

### 2. Integración en `validate_indicadores`: sólo `warnings`, nunca `errors`

Cada anomalía detectada se agrega a `warnings` (mismo patrón que las señales
blandas existentes: fallback, backfill, recuperaciones raw) y la lista
estructurada completa se expone en el dict de retorno bajo `"anomalies"`. **Cero
líneas nuevas en `errors`** — verificado con
`grep -n "errors.append" src/validation.py`. Un salto grande **legítimo** (shock
cambiario real, revisión de censo) también dispara la señal, por diseño: la
función detecta que el valor es estadísticamente atípico frente a su propio
histórico, no si es "correcto". Esa decisión es humana, no del build.

### 3. Propagación a drift: reusa la maquinaria existente, sin canal nuevo

`build_degradation()` (`src/builders/metadata.py`) ya tenía un fallback genérico
("si hay warnings → status=warning") que habría capturado la anomalía de forma
indirecta pero con un mensaje genérico. Se agregó una rama específica **antes**
de ese fallback: si `validation["anomalies"]` no está vacío, `degradation`
retorna `status="warning"`, `anomaly_detected=True`,
`anomaly_indicator_codes=[...]`, y un `recommended_action` **accionable**
("Revisar valor atípico en `<código>` del `<fecha>`; confirmar con la fuente
antes de publicar"). `build_drift()` ya promueve cualquier
`degradation.status in {"warning","degraded"}` a `drift_status="drifted"` — sin
tocar `reports.py` ni inventar un campo nuevo en `drift_report.json`: el
`recommended_action` específico llega ahí gratis porque `build_drift()` ya lo
hereda de `degradation`.

**Precedencia frente al fallback de `source_mode` (co-ocurrencia rara, revisada
en checkpoint de sesión)**: las ramas específicas de `source_mode == "fallback"`
para `comunas`/`regiones`/`provincias`/`indicadores` (líneas previas de
`build_degradation()`) retornan **antes** de llegar a la rama de anomalías. Si
`indicadores` está simultáneamente en modo fallback **y** tiene una anomalía
detectada, `degradation`/`drift_report.json` muestran sólo el mensaje de
fallback ("valores provenientes de fallback local..."), no el de la anomalía —
`anomaly_detected`/`anomaly_indicator_codes` no se poblarían en ese caso. Esto
es **intencional, no un bug**: en modo fallback los valores son datos sintéticos
de desarrollo (ver warning "synthetic development data" en
`validate_indicadores`), así que una anomalía estadística sobre datos ya
sabidos-no-reales no aporta señal útil — el mensaje de fallback es la
información más accionable. Tampoco crea un hueco de seguridad: la publicación
ya se rechaza de forma independiente para cualquier dataset en `source_mode ==
"fallback"` (`verify_publication_policy()`,
`scripts/verify_pipeline.py`, chequeo de `source_mode` sobre datasets
`stable_publishable`) — el gate de anomalías (§4) es una capa adicional, no la
única que bloquea ese caso. El único costo es de observabilidad: la anomalía
en sí queda visible únicamente en `warnings` dentro de `pipeline_metadata.json`
(vía `validate_indicadores`), no en `drift_report.json`, mientras coincida con
fallback. Se documenta aquí para que quede explícito, no oculto.

### 4. Gate de publicación: rechazo override-able, no `SystemExit` del build

`scripts/verify_pipeline.py` agrega, dentro de los "Strict checks for
indicadores" de `verify_publication_policy()` (perfil `publication` /
`--require-live`), una comprobación: si
`indicadores.degradation.anomaly_indicator_codes` tiene códigos no presentes en
`--allow-known-anomalies` (nuevo flag CLI, lista separada por comas), se agrega
a `violations` → rechaza la publicación con `fail(...)`. **El build en sí nunca
aborta** — sólo el perfil `publication` (el gate que ya rechaza fallback/stale
hoy) evalúa esta condición.

**Ruta de override**: un mantenedor que revisa el `drift_report`/logs, confirma
que el salto es un shock legítimo (no un bug de fuente), y vuelve a correr
`verify_pipeline.py --profile publication --allow-known-anomalies uf` (o via
`workflow_dispatch` manual, pasando el mismo flag) para permitir la publicación
sin esperar a que el indicador salga de la ventana de anomalía por sí solo.

## Consecuencias

- Positivas: cierra el modo de fallo más caro para la marca — un valor plausible
  en forma pero falso en valor que pasa todas las validaciones. La señal es
  barata (histórico ya existe desde 2010) y de alto retorno. Reusa el 100% de la
  maquinaria de drift/gate existente; cero artefactos nuevos.
- Negativas: un shock legítimo (crisis cambiaria real) bloqueará la publicación
  automática hasta que un humano confirme con `--allow-known-anomalies` — es el
  trade-off deliberado (ver STOP conditions del plan): preferir un falso
  positivo ocasional revisable a un falso negativo silencioso publicado. El
  override es manual hoy (flag CLI); no está wireado a un input de
  `workflow_dispatch` en `.github/workflows/*.yml` (fuera de alcance de este
  plan — ver Preguntas abiertas).

## Preguntas abiertas

1. **¿Wirear `--allow-known-anomalies` como input de `workflow_dispatch`?** Hoy
   el override requiere invocar `verify_pipeline.py` manualmente (local o vía
   shell en el runner). Agregar un input al workflow de publicación es un
   follow-up de UX de bajo riesgo, fuera de alcance de este plan
   (`.github/workflows/**` no está en el scope).
2. **¿Un allowlist persistente en `source_registry.json`** (en vez de un flag
   efímero por invocación) **para indicadores con volatilidad estructuralmente
   alta?** Se descartó para la primera versión: un allowlist persistente por
   indicador oculta el default seguro (todo se revisa) y requiere decidir cuándo
   expira. El flag por invocación fuerza revisión consciente en cada shock.
3. **¿Extender `detect_series_anomalies` a otras series con histórico?** (censo
   intercensal, finanzas municipales año a año). No se hace aquí — validar
   primero el diseño en `indicadores` (única serie diaria con histórico denso
   desde 2010) antes de generalizar.
4. **¿El umbral `z_threshold=4.0`/`min_history=4` sigue siendo el correcto a
   medida que la serie crece?** Calibrado contra 506 filas reales hoy, con
   margen (~3.8 máximo histórico vs. umbral 4.0). Recalibrar si el margen se
   erosiona con datos futuros (monitorear falsos positivos en producción).

## Alternativas consideradas

- **Media ± N·desviación estándar simple** — Descartada: frágil ante los propios
  outliers que se busca detectar (ver Decision #1).
- **Umbral de salto relativo fijo (ej. "> 20% vs. ayer")** — Descartada: no se
  adapta a la volatilidad propia de cada indicador (UF es mucho menos volátil
  día a día que Dólar/Euro); un umbral fijo sería demasiado laxo para UF y
  demasiado estricto para Dólar/Euro. El z-score normaliza por la volatilidad
  histórica de cada serie individualmente.
- **Abortar el build (`SystemExit`) ante anomalía** — Rechazada de plano (ver
  STOP conditions del plan): trabaría el cron diario ante un shock legítimo,
  bloqueando datos correctos junto con los sospechosos. Es exactamente el modo
  de fallo que la Invariante #2 (fallar ruidoso) no cubre bien para señales
  *estadísticas* en vez de *estructurales*.
- **Canal de reporte nuevo (campo dedicado en `drift_report.json` o artefacto
  separado)** — Descartada: `build_degradation()`/`build_drift()` ya propagan
  cualquier warning a `drift_status="drifted"` con `recommended_action`; la
  única adición necesaria fue una rama que genere un mensaje específico en vez
  del genérico. Inventar un canal nuevo hubiera duplicado esa maquinaria sin
  beneficio.
