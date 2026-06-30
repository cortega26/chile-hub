# Gate 4.3 — Decisión go/no-go del playground DuckDB-Wasm

> **Plan 022 §4.3 · Fecha: 2026-06-30**
> **Regla del gate:** la decisión debe basarse en métrica de atención acumulada
> (GoatCounter + descargas del bundle), no en estética ni en "estaría bueno tenerlo".

## Datos disponibles

### Descargas del bundle (señal de uso real)

Fuente: `data/normalized/usage_snapshots.json` (1 snapshot, 2026-06-30).

| Métrica | Valor |
|---------|-------|
| Descargas totales del bundle | **36** en 27 releases |
| Mediana descargas/release | **1** |
| Releases con 0 descargas | 8 de 27 (30%) |
| Máximo en un release | 6 (v1.2.2, 2026-06-18) |
| Releases recientes (últimos 5) | v1.17.1: 3, v1.17.0: 2, v1.16.0: 0, v1.15.1: 3, v1.15.0: 3 |

**Interpretación:** ~1-3 descargas por release, con varios releases en 0. La
señal es consistente con el orden de magnitud identificado en el diagnóstico
original del plan: "activaciones reales en decenas, no en miles". No hay
tendencia de crecimiento. La métrica subcuenta usuarios recurrentes (cache
local, `data_dir=`), así que es una cota inferior.

### Atención en la landing (GoatCounter)

GoatCounter se instaló durante la Fase 2 (2026-06-30). Al cierre de este gate,
tiene **menos de 24 horas de datos**. Es demasiado pronto para leer tendencias.

Datos previos (del diagnóstico del plan, §2):
- Pico de 399 vistas el 18 jun (día del lanzamiento)
- Caída a un dígito por día para el 27-29 jun
- Referrers: LinkedIn (532 combinado), GitHub (59), Google (28)
- Sin señales de tráfico orgánico o de recomendación externa

**Interpretación:** la audiencia actual es la red profesional del autor en
LinkedIn. La atención decayó rápidamente tras el lanzamiento y no hay indicios
de un segundo canal de tráfico. La landing recibe visitas de un dígito por día.

### Señal de PyPI (vanidosa, documentada)

3,224 descargas/mes — dominadas por mirrors/CI/bots. **No se usa para esta
decisión**, por directiva del plan (§10).

## Análisis

El playground DuckDB-Wasm (Plan 020) requiere:
- **Esfuerzo:** M (2–5 días)
- **Riesgo:** MED (CSP + WASM + vendorización de binarios + superficie de
  mantenimiento)
- **Costo permanente:** ~5 MB de `.wasm` en el repo, superficie de test
  (smoke test Playwright), actualizaciones de versión de DuckDB-Wasm
- **Valor esperado:** convertir la landing de escaparate estático a herramienta
  interactiva — SQL real en el navegador contra los Parquet publicados

El **criterio del gate** es: ¿la atención acumulada justifica la inversión?

**La respuesta hoy es no.** La evidencia:

1. **La audiencia es de un dígito por día.** Un explorador SQL interactivo en el
   navegador es una feature poderosa, pero sirve a una audiencia que no existe hoy.
2. **No hay tendencia de crecimiento.** Las descargas del bundle son planas (1-3
   por release) y las vistas cayeron tras el pico de lanzamiento.
3. **El costo de oportunidad es real.** El esfuerzo M del playground compite
   directamente con la Ola B2 (CEAD + electoral), que expande el catálogo con
   capas de alto valor de cruce para los investigadores que SÍ llegan.
4. **GoatCounter no tiene datos suficientes.** Recién instalado hoy, no puede
   informar tendencias. Pero los datos previos (Plan 022 §2) ya mostraban
   atención decreciente.

## Decisión

**NO-GO — el playground DuckDB-Wasm se difiere.**

El Plan 020 queda **activo y listo para ejecutar**, pero no se inicia ahora.
La decisión se reevalúa cuando se dispare cualquiera de estas condiciones:

### Condiciones de re-evaluación

| Condición | ¿Qué indicaría? |
|-----------|-----------------|
| Bundle ≥ 10 descargas/release sostenido por 3 releases consecutivos | Crecimiento real de usuarios |
| Landing ≥ 50 vistas/día sostenido por 2 semanas en GoatCounter | Tráfico orgánico o de recomendación |
| Contacto inbound cualificado (laboral/colaboración) | Interés profesional verificable |
| Post técnico (4.2) genera segundo pico de tráfico con profundidad de sesión >2 min | Atención que justifica interactividad |

### Qué hacer mientras tanto (Ola B2)

La energía de implementación se redirige a la **Ola B2** del Track B:

- **B2.1 — CEAD delincuencia** (carril `candidate`): alto valor de cruce,
  reutiliza el workflow mensual de scraping de la Fase 3.3.
- **B2.2 — Electoral** (research primero): cierra la pregunta legal (Ley
  19.628) antes de codificar.

Ambas tareas expanden el catálogo con capas de alto valor para investigadores,
que es el uso que SÍ tiene el proyecto hoy (las descargas del bundle, aunque
pocas, existen). Esto es consistente con el principio rector del Track B:
"crecer por criterios, no por acumulación".

## Registro

| Campo | Valor |
|-------|-------|
| Fecha | 2026-06-30 |
| Gate | 4.3 — Decisión playground |
| Decisión | **NO-GO** (diferido, no cancelado) |
| Basado en | `usage_snapshots.json` (36 descargas, 27 releases), datos de atención del diagnóstico (§2), GoatCounter <24h |
| Criterio de re-evaluación | 4 condiciones documentadas arriba |
| Siguiente acción | Iniciar Ola B2 (B2.1 CEAD + B2.2 electoral) |
| Plan 020 | Sigue activo, listo para ejecutar cuando se dispare una condición |
