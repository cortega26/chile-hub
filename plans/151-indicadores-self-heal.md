# Plan 151: Auto-recuperación de `indicadores` sin bloquear el publish

> **Estado:** DONE (2026-10-26, commit de este PR)

## Por qué

El gate de publicación de `indicadores` trataba **cualquier** diagnóstico como
fallo fatal:

```python
failed_diagnostics = {campo: valor for campo in (
    "fetch_failures", "raw_recoveries",
    "preserved_existing_pairs", "empty_live_pairs") if valor}
if failed_diagnostics:
    violations.append(...)
```

`raw_recoveries` y `preserved_existing_pairs` son **recuperaciones exitosas**, no
fallos. Además, sus entregas (`raw_recovery`, `preserved_existing`) estaban en la
lista de "unsafe delivery".

Consecuencia medida: el run [40322837402](https://github.com/cortega26/chile-hub/actions/runs/40322837402)
(2026-10-26) falló porque mindicador.cl devolvió 4 *read timeouts* y 2 errores
SSL, el extractor se recuperó desde los snapshots crudos —con datos válidos— y
el publish se rechazó igual. Un hipo de la fuente detuvo el hub completo.

## Decisión

Ver ADR-025, enmienda 2026-10-26, punto 3.

1. Bloquea solo un fallo **sin ruta de recuperación**
   (`indicadores: unrecovered fetch failures=[…]`).
2. `raw_recovery` y `preserved_existing` pasan a ser entregas aceptadas.
3. La **edad del dato entregado** se gatea también para las recuperaciones, con
   el mismo umbral por cadencia que los backfills (ADR-016): 10 días para series
   diarias, 70 para mensuales.

## Red de seguridad

Lo que impide que esto sea "publicar cualquier cosa":

- `raw_recovery` de una serie con edad > umbral → rechazo
  (`stale delivery in [...]`), con el override auditable
  `--allow-stale-backfills` de siempre.
- Un fallo sin recuperación → rechazo.
- `verify_indicadores_diagnostics` sigue exigiendo la nota y el warning que
  hacen visible la recuperación en el artefacto.

## Tests

`tests/test_pipeline_logic.py`:

- `test_publication_policy_acepta_una_recuperacion_valida` — recuperación fresca
  publica.
- `test_publication_policy_rechaza_una_recuperacion_stale` — edad 30 días en una
  serie diaria rechaza.
- `test_publication_policy_rechaza_un_fallo_sin_recuperacion` — sin ruta, bloquea.

## Alcance mayor: self-correct / self-heal / self-improve

Este plan resuelve la capa **self-heal** para la clase de fallo más frecuente
(fuente transitoria + recuperación válida). El estado del proyecto por capa:

| Capa | Estado | Mecanismo |
|:--|:--|:--|
| **Self-correct** | Existe | Gates que rechazan estado inválido: validaciones, contratos, `verify_pipeline`, anti-drift de docs |
| **Self-heal** | Existe, ampliado aquí | Retención (plan 150), cadena de recuperación de `indicadores`, backfill con edad gateada, `raw_snapshot_recovery` |
| **Self-improve** | **No existe** | Requiere que el sistema cambie su propio código o criterios; hoy toda mejora pasa por una persona o un agente autorizado |

Sobre **self-improve**, la posición honesta: automatizar la *detección* ya está
hecho (issues de schedule, `source-urls.yml`, retención vencida, health). Lo que
no existe —ni conviene improvisar— es un bucle que modifique código o política
sin revisión. El siguiente paso razonable sería un **triage semanal automático**
que abra un issue con las señales accionables ordenadas por impacto, no un agente
con permiso de escritura.

## Rollback

Revertir el commit restaura el comportamiento anterior: cualquier diagnóstico
vuelve a bloquear. No hay migración de datos ni cambio de esquema.
