# ADR-022: Las regresiones de datos se bloquean en `verify_pipeline`, no con el diff de la documentación

**Fecha:** 2026-09-26
**Estado:** proposed (pasa a accepted al mergear el plan 108)
**Decisión:**
- El gate "Check build-synced files" solo falla si `index.html` o `app.js` quedaron desactualizados.
- Si cambia `README.md`, el gate solo lo informa, porque los bloques de datos del README los commitea el job `publish`.
- Las regresiones de datos las rechaza el perfil `publication` de `verify_pipeline.py`. Rechaza dos casos: un `source_mode` en fallback (ya existía) y una caída de `record_count` mayor al 20% respecto del último publicado (nuevo). Ese rechazo admite un override explícito y auditable.

## Contexto

`README.md` contiene bloques que se generan desde los datos de cada build: la tabla de capas con conteos y estado, `HEALTH_SUMMARY` y `QUALITY_SUMMARY`. Desde `378eba0` (2026-07-08), el gate exigía que esos bloques ya estuvieran commiteados antes del publish. Pero el único paso que los commitea es el propio publish, y el publish depende de ese gate. Por eso, cualquier cambio legítimo de conteo (una actualización mensual de salud, la serie incremental de calidad del aire) abortaba el publish, el README no se actualizaba y el siguiente schedule volvía a fallar.

El schedule no publicó desde el 2026-08-13 hasta el 2026-09-26, y nada avisó de la falla (plan 108).

Mientras tanto, el gate cumplía una función que no estaba declarada: el diff del README era la única señal ante una regresión de datos en modo live. En el incidente de `autoridades_electas` del 2026-07-19/20, el extractor bajó de 205 a 155 registros (0 senadores) sin caer en fallback.

## Decisión

1. **Separar responsabilidades.**
   - El gate de archivos sincronizados vigila la deriva *estructural*. `index.html`/`app.js` fallan fuerte; la deriva de los hechos del README la cubre `sync_docs.py --check` en cada push y PR.
   - `verify_pipeline.py --profile publication` vigila la *calidad de los datos*. Es un único lugar, ya bloquea la publicación y está testeado.
2. **Guard de caída de conteo.** Usa `record_count_delta` de `dataset_changelog.json`, que el build calcula contra el `pipeline_metadata.json` publicado. Aplica a todo dataset `stable_publishable`. El umbral es `DEFAULT_MAX_RECORD_DROP_PCT = 20`. Calibración: en 116 versiones publicadas, la peor caída en modo live fue 3,1%; las caídas grandes fueron todas fallbacks, y esas ya se rechazaban.
3. **Override auditable.** `--allow-record-drop <dataset>` se expone como input del `workflow_dispatch`. Se registra en `pipeline_artifact_provenance.json` y el release lo reutiliza al re-verificar, con el mismo patrón que `--allow-stale-backfills` (ADR-016). Los inputs llegan al shell por variables de entorno, sin interpolarse en el script.

## Alternativas consideradas

- **Que el job de build auto-commitee el README antes del gate.** Agrega un segundo escritor en `main` y reabre las carreras entre release y publish ya documentadas. Descartado.
- **Volver al gate en modo `::warning::` para todo (como en `8f58430`).** Se pierde la señal de regresión sin reemplazarla. Descartado.
- **Umbrales por dataset en el registro desde el inicio.** Obliga a cambiar el dataclass de la spec, la proyección y el JSON legacy para un solo valor, que hoy basta con uno global. Diferido al plan 109 y se evaluará cuando algún dataset lo necesite.

## Consecuencias

- El schedule vuelve a publicar cuando los conteos cambian legítimamente. El README se actualiza en el commit `daily refresh`.
- Una caída de filas en modo live aborta el publish con un mensaje explícito que nombra el dataset, el porcentaje y el override. Antes, la señal era un diff de tabla.
- Riesgo residual: una regresión que no reduce filas, como valores nulos o columnas vacías, no la detecta este guard. La cubren los contratos y validaciones por dataset. Si un caso lo requiere, se extenderá con expectativas declarativas (plan 109).
- Rollback: revertir el commit. No requiere migración de datos.
