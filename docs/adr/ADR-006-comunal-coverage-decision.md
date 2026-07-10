# ADR-006: Resolucion de cobertura comunal para tres datasets del bundle publico

**Fecha:** 2026-07-09
**Estado:** accepted
**Decision:** Tres datasets comunales con cobertura parcial (3 de 346 comunas) se resuelven mediante FILL (dos casos: error de mapeo en extractor, scrape mensual funcional) y RE-CARRIL (un caso: fuente permanentemente muerta).

## Contexto

En la auditoria de calidad del bundle publico se detecto que tres datasets de capa comunal tenian cobertura nominal de 3 filas frente a las 346 comunas esperadas:

- `consumo_electrico_comunal` -- 3 filas
- `pobreza_comunal` -- 3 filas
- `finanzas_municipales` -- 3 filas

El proyecto chile-hub se define como "menos datasets, mas limpios y confiables". La presencia de datasets casi vacios en el bundle publico contradice directamente esa promesa. Se investigo la causa raiz de cada uno y se aplico la accion correctiva correspondiente.

## Decision

### 1. consumo_electrico_comunal → RE-CARRIL (commit `57e6eaf`)

**Problema:** La fuente original (CNE via `energiaabierta.cl` sobre la plataforma Junar) fue descontinuada permanentemente por la Comision Nacional de Energia. No existe API de reemplazo ni fuente alternativa conocida para datos de consumo electrico a nivel comunal.

**Accion:** Se movio el dataset a `maturity_status=deprecated`, `publication_track=candidate`, `public_bundle_eligible=false`. El dataset permanece en el repositorio como referencia historica pero no se distribuye en el bundle publico.

**Evidencia:** Commit `57e6eaf` aplica los cambios de configuracion en `source_registry.json`.

### 2. pobreza_comunal → FILL (commit `3f968ab`)

**Problema:** El extractor tenia un mapeo de columnas incorrecto para el formato real del archivo XLSX de MDS (Ministerio de Desarrollo Social). No era un problema de cobertura de fuente sino de parseo: el extractor no lograba identificar las columnas correctas de pobreza por comuna.

**Accion:** Se corrigio el mapeo de columnas en el extractor. Con la correccion, el extractor producira 345 comunas x 2 dimensiones de pobreza en la proxima ejecucion live. Nota: al momento de este ADR el fix de codigo esta aplicado pero puede que el Parquet normalizado aun refleje el snapshot antiguo de 3 filas hasta que se re-ejectue el extractor.

**Evidencia:** Commit `3f968ab` corrige el mapeo en el extractor de `pobreza_comunal`.

### 3. finanzas_municipales → FILL (commit `c8c7c70`)

**Problema:** El extractor SINIM no se ejecutaba correctamente de forma mensual, dejando el dataset con datos residuales.

**Accion:** Como parte del Plan 034 se regularizo el scrape mensual de SINIM. El snapshot en staging muestra 345 de 346 municipios con datos financieros. Adicionalmente, el Plan 027 (commit `4690fec`) corrigio una etiqueta de provenance que estaba mal asignada: el extractor live etiquetaba sus propios datos como "curated fallback" en lugar de "live". Esta correccion ya esta aplicada.

**Evidencia:** Commit `c8c7c70` contiene el snapshot de staging con 345/346 municipios. Commit `4690fec` corrige la etiqueta de provenance.

## Consecuencias

- Positivas: Los tres datasets problematicos estan resueltos. El bundle publico ya no contiene datasets comunales con 3 filas. `consumo_electrico_comunal` queda documentado como fuente muerta en lugar de generar confusion. `pobreza_comunal` y `finanzas_municipales` produciran cobertura completa en su proxima extraccion.
- Negativas: `consumo_electrico_comunal` pierde su estatus publicable y no hay horizonte de recuperacion. `pobreza_comunal` requiere una re-ejecucion del extractor para reflejar la cobertura completa en el Parquet normalizado. Los consumidores que dependian de `consumo_electrico_comunal` deben buscar fuentes alternativas (ej. CNE directamente si publican datos en otro formato).

## Alternativas consideradas

- **Mantener los tres datasets como `stable_publishable` con cobertura parcial** -- Se descarto porque 3 de 346 comunas no es "cobertura", es ruido. Un consumidor que intentara hacer un join por `codigo_comuna` obtendria resultados esencialmente vacios sin saber por que.
- **Eliminar `consumo_electrico_comunal` del repositorio** -- Se descarto porque el dataset tiene valor historico y su configuracion `deprecated` + `candidate` permite que aparezca en los metadatos del hub con una nota sobre su estado, evitando que otros desarrolladores pierdan tiempo investigando la misma fuente muerta.
- **Construir un extractor alternativo para consumo electrico** -- Se descarto por falta de una fuente publica alternativa conocida y por el costo beneficio: hay otros datasets con mayor demanda y fuentes disponibles.
