# Plan 152: Triaje semanal automático de señales

> **Estado:** DONE (2026-10-26, commit de este PR)

## Por qué

El proyecto produce señales de sobra —`hub_health.json`, `dataset_quality.json`,
`source_readiness.json`, `drift_report.json`, issues de schedule y de retención—
pero la **agenda** la arma una persona leyendo reportes a mano. Eso no escala y
depende de que alguien se acuerde.

Este plan añade la capa más pequeña que falta: un job que lee el estado
publicado, ordena lo accionable por impacto y lo publica como un único issue.

## Qué hace

`.github/workflows/weekly-triage.yml` — lunes 12:00 UTC (después del publish de
las 10:00), `workflow_dispatch` manual disponible.

1. `scripts/weekly_triage.py` lee los artefactos y emite Markdown.
2. El workflow publica el informe como issue con label `triage`:
   - no existe → lo crea;
   - existe → comenta con la foto de la semana;
   - cero señales → comenta y cierra el issue.
3. No abre nada si no hay señales.

## Orden de impacto (decisión editorial, no score inventado)

1. **Errores de validación** — un dato publicado que no pasa su validación.
2. **Retención vencida** — tiene fecha límite y ya pasó; enlaza el issue `data-hold`.
3. **Datos stale** — el consumidor recibe algo viejo.
4. **Advertencias accionables** — requieren mirada humana.
5. **Calidad C/D** — grado del scorecard.
6. **Revisiones de registro vencidas**.

Fuera de las señales, como **contexto**: capas retenidas vigentes, revisiones
"por vencer" (<90 d) y los contadores del build.

> Criterio explícito: si una señal se repite cada semana sin cambiar (retención
> vigente, revisión a 66 días), no es una señal: es ruido. Va al pie.

## Diseño

- **Solo stdlib.** El workflow no instala dependencias (ni `uv sync`), así que el
  script no puede importar `polars` ni `src.*`. Hay un test que lo verifica.
- **Tolerante a artefactos ausentes.** Si falta un JSON, lo declara y sigue; un
  fallo de lectura no puede tumbar el triaje.
- **Sin permisos de escritura sobre código.** El job solo tiene `issues: write`;
  el resto del workflow queda en `contents: read`.
- **Un issue, no uno por semana.** Se actualiza por comentario y se cierra al
  quedar limpio, para que el histórico quede en el hilo y el tablero no se llene.

## Tests

`tests/test_weekly_triage.py` (10 casos, sin red): señales limpias, artefacto
ausente, orden error → vencida → advertencias, retención vigente como contexto,
`review_approaching` que no dispara y `review_due` que sí, stale y advertencias
con su dataset, calidad A que no dispara y C que sí, retirados excluidos, CLI
`--count`/`--output` y stdlib-only.

## Lo que este plan NO hace

- No corrige nada: no toca datos, código ni políticas.
- No decide prioridades de producto; ordena señales con un criterio explícito.
- No reemplaza la revisión humana: la hace más barata.

## Rollback

Borrar el workflow y el script. No hay estado persistente más allá del issue,
que se puede cerrar a mano.
