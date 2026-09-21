# ADR-020: Retiro del contador GoatCounter no autorizado y política de telemetría de terceros

**Fecha:** 2026-09-21
**Estado:** accepted
**Decisión:** Se retira por completo el contador GoatCounter de la landing (`app.js`, `playground.js`, `privacy.html`, espejo CSP de `verify_landing.py`). A partir de ahora, ningún servicio de analítica de terceros puede cablearse sin (1) una cuenta creada y controlada por el mantenedor, (2) aprobación explícita del mantenedor, (3) actualización de `privacy.html` y (4) un guardrail en `tests/test_ci_config.py` que lo fije.

## Contexto

La landing cargaba `https://gc.zgo.at/count.js` y enviaba pageviews, descargas, etapas del playground y salidas a docs a `https://chile-hub.goatcounter.com/count` (PR #101, 2026-09-20). El 2026-09-21 el mantenedor declaró que **jamás abrió una cuenta en GoatCounter** y no tiene ningún correo de ese dominio: no existe dashboard asociado y nadie sabe a quién pertenecen esos datos.

La verificación en vivo confirmó que el endpoint responde **HTTP 400** (cuerpo vacío) tanto en GET como POST, desde navegador y curl: ningún hit se registra. Los pings salían igual desde cada visita — tráfico hacia un tercero desconocido sin ningún valor a cambio.

Un documento histórico (`reference/gate-4-3-decision-playground/`, junio 2026) atribuye estadísticas de lanzamiento a ese contador. Sin una cuenta del mantenedor, esos números no son atribuibles ni auditables; ese registro se conserva intacto como evidencia histórica, no como verdad operativa.

## Decisión

1. **Retiro total**: loader, `chTrack`/`trackDownload`/eventos del playground, atributos `data-dl-*`, menciones en `privacy.html` y orígenes `gc.zgo.at` / `chile-hub.goatcounter.com` del espejo CSP. Los botones de descarga siguen funcionando (eran `href` + `download`); solo dejan de medirse.
2. **Baseline**: Cloudflare Web Analytics (beacon del edge, cookieless) sigue siendo la única medición, como ya declara `privacy.html`.
3. **Regla permanente**: telemetría de terceros requiere cuenta del mantenedor + aprobación explícita + `privacy.html` + guardrail en `tests/test_ci_config.py`. Un commit que agregue un endpoint de conteo sin esos cuatro elementos se revierte.
4. **Seguimiento fuera del repo**: la regla CSP por ruta de Cloudflare para `/chile-hub/` aún permite el origen GoatCounter en el dashboard (inocuo ahora que nada lo carga). Debe estrecharse al aplicar el doc actualizado de `platform/tooltician-site`.

## Consecuencias

- Se pierde la medición de descargas, etapas del playground y salidas a docs hasta que exista un destino autorizado. Las pageviews agregadas siguen cubiertas por Cloudflare Web Analytics.
- `tests/test_ci_config.py::UnauthorizedTelemetryGuardrailTests` falla si `goatcounter`/`zgo.at` reaparece en los archivos servidos de la landing.
