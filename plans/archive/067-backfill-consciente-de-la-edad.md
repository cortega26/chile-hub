# Plan 067: Backfill consciente de la edad — una serie muerta no puede esconderse

> **Executor instructions**: este plan **no** repara la serie `ipc` ni toca datos.
> Hace visible y bloqueante una condición que hoy degrada en silencio. Si la única
> forma de avanzar es abortar el build o relajar un gate, es una STOP condition.
>
> **Drift check (córrelo primero)**: `git diff --stat HEAD -- src/extractors/bcentral_extractor.py scripts/verify_pipeline.py src/builders/metadata.py`

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED (toca el gate de publicación de `indicadores`, dataset `stable_publishable`)
- **Depends on**: ninguno
- **Category**: correctness / foso de confianza
- **Cierra**: issue #43 (el Step 3 queda como follow-up)

## Por qué importa

El issue #43 se abrió como "investigar por qué falta `ipc` en el refresh live".
La evidencia dice algo peor:

```
data/staging/indicadores.csv y data/normalized/indicadores.parquet
  ipc → 1 fila,  fecha 2025-12-01      ← ~8 meses de antigüedad
  utm → 8 filas, hasta 2026-08-01      ← tambien mensual, y al dia
```

`utm` es mensual igual que `ipc`, sale del mismo endpoint y está corriente: la
cadencia no explica nada. **La serie `ipc` está muerta desde diciembre de 2025** y
`published_backfill` viene re-publicando el mismo punto único en cada build.

El mecanismo funciona como fue diseñado (degradación con gracia ante un hueco
transitorio), pero no distingue un hueco de una defunción. Un backfill que se
repite ocho meses ya no es degradación con gracia: es un dato obsoleto publicado
con cara de fresco. Y la próxima serie que muera se esconderá igual de bien.

Ese es el entregable de este plan: **no** arreglar `ipc` (eso depende de un
diagnóstico con red que el ejecutor puede no tener), sino cerrar el modo de falla.

## Estado actual

- `load_existing_staging()` (`src/extractors/bcentral_extractor.py:143-177`)
  activa `published_backfills` cuando un código está **completamente ausente**
  del staging, y lo rellena desde el parquet publicado.
- `MONTHLY_INDICATORS = {"utm", "ipc"}` (`:58`) ya distingue cadencias.
- Los metadatos de staging exponen `indicator_delivery`
  (`{"ipc": "published_backfill", …}`) y `published_backfills`, pero **ninguna
  señal de la edad** del dato entregado.
- `verify_publication_policy()` (`scripts/verify_pipeline.py:505-543`) ya trata
  `published_backfill` como delivery **segura** (`:530`), así que hoy no genera
  ninguna violación por antigüedad.
- El precedente exacto a reusar está en el mismo bloque: el gate de anomalías del
  Plan 054 (`:535-542`) → violación **override-able** vía `--allow-known-anomalies`,
  nunca `SystemExit` del build. Este plan replica esa forma con
  `--allow-stale-backfills`.
- La frescura es **por dataset** (`freshness_policy: 72h, "diaria"`), pese a que
  el dataset mezcla series diarias (UF, dólar, euro) y mensuales (UTM, IPC).

## Alcance

**En alcance**: `src/extractors/bcentral_extractor.py` (metadatos de edad),
`scripts/verify_pipeline.py` (gate + flag), tests, ADR-016, docs del dataset.

**Fuera de alcance**: reparar la serie `ipc` (Step 1, requiere red y decisión de
fuente), frescura por indicador (Step 3, follow-up), y cualquier cambio de datos.

## Git workflow

- Branch: `advisor/043-indicadores-backfill-age`
- Commit: `feat(indicadores): hace el backfill consciente de la edad`

## Pasos

### Step 1 (operador, requiere red): diagnosticar `ipc` upstream

```bash
curl -s https://mindicador.cl/api/ipc/2026 | head -c 400
curl -s https://mindicador.cl/api/utm/2026 | head -c 400   # control: deberia traer datos
```

Determina cuál de las tres es: (a) mindicador.cl dejó de exponer `ipc`, (b) el
código cambió de nombre, (c) es un bug de parseo en `fetch_indicator_year()`.
**No bloquea los Steps 2 y 4**: el arreglo estructural es correcto en los tres casos.

### Step 2: Exponer la edad del dato entregado

En los metadatos de staging de `indicadores`, agrega `indicator_max_date`
(`{code: "YYYY-MM-DD"}`) y `indicator_age_days` (`{code: int}`), calculados sobre
el DataFrame final para **todos** los códigos, no solo los backfilleados — así la
señal existe antes de que haga falta.

**Verifica**: los metadatos traen `ipc` con su fecha real (2025-12-01) y una edad
de tres dígitos, y `uf`/`dolar` con edad pequeña.

### Step 3: Umbral por cadencia, no global

Un solo umbral es incorrecto: 40 días de atraso en el dólar es una emergencia y
en el IPC es normal. Define en el extractor (fuente única, junto a
`MONTHLY_INDICATORS`):

- series mensuales: `MAX_BACKFILL_AGE_DAYS_MONTHLY = 70` (dos publicaciones perdidas);
- series diarias: `MAX_BACKFILL_AGE_DAYS_DAILY = 10`.

Documenta el porqué de cada número junto a la constante.

### Step 4: Gate de publicación override-able

En `verify_publication_policy()`, siguiendo el patrón del Plan 054: si un código
viene por `published_backfill` **y** su `indicator_age_days` supera el umbral de
su cadencia → violación con mensaje accionable, override vía
`--allow-stale-backfills uf,ipc`.

**Nunca** `SystemExit` del build ni error de validación: el build sigue
produciendo artefactos; lo que se bloquea es la **publicación** sin revisión humana.

**Verifica**: con el estado actual, `verify_pipeline.py --profile publication`
rechaza por `ipc`; con `--allow-stale-backfills ipc` pasa. El perfil `dev`
(`make verify`) sigue exit 0 en ambos casos.

### Step 5: ADR-016 y documentación

Por qué el umbral depende de la cadencia; por qué es override-able y no un error
duro; por qué la edad se mide sobre el dato entregado y no sobre
`refreshed_at_utc` (que solo dice cuándo corrió el extractor, no cuán viejo es lo
que trae). Registra `ipc` como el caso que lo motivó, con su diagnóstico abierto.

## Follow-up (no en este plan)

**Frescura por indicador**: hoy el `stale` del dataset no distingue "el dólar no
se actualizó" de "el IPC lleva 8 meses muerto". Requiere decidir cómo conviven
una `freshness_policy` de dataset y una por serie; abrir plan propio si este
gate demuestra que hace falta.

## Test plan

- Edad calculada por código, incluyendo un código sin filas.
- Umbral mensual vs diario: una serie mensual a 60 días pasa; a 80 no. Una diaria
  a 12 días no pasa.
- El gate solo aplica a códigos entregados por `published_backfill`: una serie
  `live` y vieja no dispara (eso es problema de frescura, no de backfill).
- El override `--allow-stale-backfills` convierte la violación en pase.
- Regresión: `make verify` (perfil dev) no cambia de comportamiento.

## Done criteria

- [ ] Los metadatos traen edad y fecha máxima por indicador.
- [ ] El umbral distingue cadencia mensual de diaria, con la justificación junto a la constante.
- [ ] El gate de publicación rechaza `ipc` hoy, y el override lo deja pasar.
- [ ] El build **nunca** aborta por esta condición.
- [ ] ADR-016 escrito; issue #43 referenciado.
- [ ] `make build && make verify && make test && make lint && make format-check && make doctor` → exit 0.

## STOP conditions

- La única forma de que pase el gate es relajar el umbral sin evidencia de la fuente.
- El cambio obliga a abortar el build o a marcar `ipc` como error de validación.
- El gate dispara sobre series entregadas en vivo (sería un gate de frescura mal ubicado).
