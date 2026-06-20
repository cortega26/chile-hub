# ME8: Evaluación de producto comercial (API Premium / Perfil Territorial)

**Estado:** Pendiente de evaluación (no decidido)
**Impacto:** Alto (estratégico)
**Esfuerzo:** N/A — decisión de negocio, no implementación
**Riesgo:** Alto si se ejecuta mal (reputacional, foco, soporte)
**Target:** Por validar demanda antes de comprometer trabajo
**Dependencias:** ME6 (hardening de errores) y ME7 (capacidades de API) si se avanza

## Resumen

Se evaluó la posibilidad de construir una **API Premium / ChileHub Cloud** y un
producto de **"due diligence territorial"** sobre los datos actuales. Conclusión:
**no avanzar con la API Premium todavía; el dato no justifica un paywall y la
demanda no está validada.** Queda pendiente de evaluación con clientes reales.

## Hallazgos clave (evidencia del repo, 2026-06-19)

### Sobre una API Premium

- Los 15 datasets son **CC-BY/CC0 redistribuibles** (`redistribution_report.json:
  ready_count 15`). Éticamente no se puede cobrar por el dato, solo por la
  operación encima.
- El dato es **pequeño** (14 de 15 datasets a nivel comunal, 16-12.898 filas;
  solo `empresas` es grande con 1,57M). Ya se distribuye como bundle ZIP en
  GitHub Releases bajable en una línea → no existe el problema de "datos
  difíciles de obtener" que justifica una API hosted.
- **No existe infraestructura de API** (sin FastAPI/Flask, auth, billing,
  servidor). Lo que hoy se llama "API" es la librería Python `ChileHub`.
- Mantenedor único → vender SLA es una atadura operacional de alto riesgo.

### Sobre el producto "due diligence territorial"

- Los datos soportan un **perfil territorial descriptivo**, NO un due diligence
  en sentido estricto (que implica cobertura de riesgos para una decisión y
  genera responsabilidad legal si se sobrepromete el nombre).
- **Cobertura sólida (346/346 comunas):** demografía (Censo 2024), vivienda/
  hogares, establecimientos de salud y educación (con coordenadas), distrito
  electoral, dinamismo de constituciones de empresas.
- **Tres datasets prácticamente vacíos:** `finanzas_municipales` (3/346),
  `resultados_educacionales` (3/346), `indicadores_urbanos_siedu` (3-6/346).
  El `perfil_territorial_comunal` tiene 42 columnas pero 14 son NULL para 343
  comunas.
- **Sesgo de `empresas`:** solo `tipo_actuacion = CONSTITUCIÓN` bajo régimen
  simplificado (Ley 20.659) desde 2013. No es el universo de empresas activas;
  debe declararse.
- **Faltan las capas de mayor valor y mayor riesgo legal:** precios/
  transacciones de propiedades, zonificación/plan regulador, mapas de riesgo
  (inundación/sísmico/incendio), nivel socioeconómico (CASEN), seguridad,
  conectividad. Ninguna existe en el repo.

## Recomendación de la evaluación

1. **No construir la API Premium ahora.** A lo sumo, exponer una **API gratuita
   estática** (Parquet/JSON en CDN) como funnel, costo casi nulo.
2. **Monetizar primero con reportes one-shot + consultoría**, no con suscripción
   de API. Cero infraestructura, margen alto, valida disposición real a pagar.
3. **No llamar "due diligence" al producto.** Nombre honesto: "Perfil Territorial
   Comunal" / "Ficha de Mercado por Comuna" (descriptivo, no asesoría).
4. **Prerrequisito de producto:** llenar los 3 datasets vacíos (trabajo de
   pipeline, ver ME4/estabilización de fallbacks) antes de vender nada.
5. **Frontera ética:** lo abierto sigue abierto; todo plan de pago debe poder
   responder "¿qué obtiene el cliente que no puede hacer gratis bajando el
   bundle?" con operación/SLA/integración/análisis, nunca con el dato.
6. **API Pro solo después** de varios reportes vendidos con patrón repetible y un
   cliente de diseño firmado (p. ej. Citify) que pida integración continua.

## Qué validar antes de programar (Etapa 0)

- Landing "ChileHub para empresas" + documento público "Promesa de apertura".
- 5 conversaciones con prospectos (Citify primero): qué decisión territorial
  toman hoy y qué pagarían por resolverla.
- Vender 2-3 reportes piloto producidos manualmente con la librería actual.
  Si nadie compra, esa es la respuesta.

## Por qué está en backlog

Es una decisión estratégica/comercial que requiere **validación externa de
demanda**, no trabajo técnico. Se reevalúa tras las conversaciones de Etapa 0.
Las piezas técnicas habilitantes (ME6, ME7) mejoran la librería con o sin API,
por lo que pueden avanzar independientemente.
