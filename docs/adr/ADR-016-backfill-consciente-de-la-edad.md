# ADR-016: El backfill publicado caduca — una serie muerta no puede esconderse

**Fecha:** 2026-07-29
**Estado:** accepted
**Decision:** Una serie de `indicadores` entregada por `published_backfill` cuyo
último dato supere un umbral de antigüedad **dependiente de su cadencia** genera
una violación de la política de publicación, **override-able** vía
`--allow-stale-backfills`. Nunca aborta el build ni se convierte en error de
validación.

## Contexto

El issue #43 se abrió como "el refresh live reusa el artefacto publicado para
`ipc`". La evidencia mostró algo peor: `ipc` tenía **una sola fila, del
2025-12-01** — 240 días de antigüedad — mientras `utm`, igualmente mensual y del
mismo endpoint, estaba al día hasta 2026-08-01. La cadencia no explicaba nada:
la serie estaba muerta y `published_backfill` venía re-publicando el mismo punto
en cada build.

El mecanismo hacía exactamente lo que se diseñó: degradar con gracia ante un
hueco transitorio (`load_existing_staging()` rellena desde el parquet publicado
cuando un código está ausente del staging). Lo que no sabía hacer es distinguir
un hueco de una defunción. Ocho meses de "degradación transitoria" no son una
degradación transitoria.

El costo no era `ipc` — era que **la próxima serie que muriera se escondería
igual de bien**.

## Decision

### 1. La edad se mide sobre el dato entregado, no sobre `refreshed_at_utc`

`refreshed_at_utc` dice cuándo corrió el extractor, no cuán viejo es lo que
trae. Un extractor que corre cada día y devuelve el mismo dato de diciembre
tiene frescura perfecta y contenido muerto. `indicator_age_days` mide
`hoy - max(fecha)` por serie.

Las edades **negativas son normales y esperadas**: la UF y la UTM se publican
por adelantado.

### 2. Se calcula en el build, no en el extractor

`build_indicator_ages()` vive en `src/builders/metadata.py` y opera sobre el
DataFrame real en cada `make build`. Ponerlo en el extractor lo habría dejado
inerte justo en el escenario que importa: cuando el extractor **no** vuelve a
correr, que es cuando una serie muerta se esconde. Además, así la señal existe
para artefactos ya construidos sin necesidad de re-extraer.

Se calcula para **todos** los códigos, no solo los backfilleados: la señal debe
existir antes de que haga falta.

### 3. El umbral depende de la cadencia

Un umbral único sería incorrecto: 40 días de atraso en el dólar son una
emergencia; en el IPC son lo normal (el INE publica alrededor del día 8 del mes
siguiente).

- `MAX_BACKFILL_AGE_DAYS_MONTHLY = 70` — dos publicaciones perdidas.
- `MAX_BACKFILL_AGE_DAYS_DAILY = 10` — holgura para feriados largos y ventanas
  de reintento.

Ambas viven junto a `MONTHLY_INDICATORS` en `bcentral_extractor.py`, que ya era
la fuente única de la cadencia, y `verify_pipeline.py` las consume desde ahí.

### 4. Rechazo de publicación override-able, nunca abort del build

Reusa exactamente el patrón del gate de anomalías temporales (ADR-013, Plan 054):
el build sigue produciendo artefactos; lo que se bloquea es publicar sin revisión
humana. El override (`--allow-stale-backfills ipc`) documenta que alguien
confirmó el estado contra la fuente.

**Por qué no un error de validación**: convertiría un problema de publicación en
un pipeline roto, y el proyecto ya decidió (ADR-013) que las señales de valor
—a diferencia de las de forma— no abortan el build.

### 5. El gate solo aplica a entregas por backfill

Una serie vieja entregada **en vivo** es un problema de frescura, no de backfill.
Mezclarlos pondría el gate en el lugar equivocado y lo haría disparar por
razones que no puede explicar.

## Consecuencias

- Con el estado actual, `verify_pipeline.py --profile publication` **rechaza**
  con `indicadores: stale published_backfill in ['ipc'] (ipc: 240d > 70d)`.
  El perfil `dev` (`make verify`) no cambia.
- `pipeline_metadata.json` gana `indicator_max_date` e `indicator_age_days` por
  serie — inspeccionables sin re-ejecutar nada.
- El diagnóstico de por qué `ipc` murió upstream sigue **abierto** (issue #43,
  Step 1): requiere consultar `https://mindicador.cl/api/ipc/2026` con red. Este
  ADR no lo resuelve; hace que no se pueda volver a ignorar.

## Pendiente relacionado

**Frescura por indicador**: hoy la `freshness_policy` es del dataset
(`72h, "diaria"`) pese a que mezcla series diarias y mensuales, así que el
`stale` no distingue "el dólar no se actualizó" de "el IPC lleva 8 meses muerto".
Este gate cubre el segundo caso; el primero sigue con la granularidad vieja. Si
la práctica muestra que hace falta, abrir plan propio.

## Alternativas descartadas

- **Umbral único global**: o es tan laxo que no detecta nada en series diarias,
  o tan estricto que marca falsos positivos en cada IPC.
- **Prohibir `published_backfill`**: eliminaría una degradación con gracia que sí
  es correcta ante huecos transitorios, y dejaría al pipeline sin recurso.
- **Medir sobre `refreshed_at_utc`**: es justamente la métrica que no vio el
  problema durante ocho meses.
