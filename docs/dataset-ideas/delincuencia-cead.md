# Idea: Delincuencia comunal (CEAD / DMCS)

## Estado

- **Decisión actual**: under-review (para revisión)
- **Prioridad tentativa**: P1 por valor, condicionada por la fuente
- **Esfuerzo estimado**: M si aparece una descarga estructurada estable; L si hay
  que mantener un extractor sobre scraping
- **Riesgo**: HIGH — fragilidad de fuente
- **Categoría**: seguridad / civic-data / data-quality
- **Registrado**: 2026-06-21
- **review_by**: 2026-09-21 (`stalled_after_days`: 90)
- **Carril de destino**: `candidate` (fuera del bundle público)
- **Fuente verificada**: sí — sin descarga oficial estable; el acceso real es
  scraping de tablas HTML (2026-06-21); ver Referencias.

## Mini-scorecard

`valor: muy alto (seguridad, el dominio más demandado que falta) · legal: ok
(casos agregados por comuna, no personal; atribución) · tamaño: chico (~1 MB
agregable) · cadencia: trimestral · fragilidad: alta (solo scraping; el portal
rompió flujos en 2024 y 2025) → under-review (carril candidate)`

## Propuesta

Publicar una capa comunal de casos policiales de Delitos de Mayor Connotación
Social (DMCS) y otras categorías (VIF, drogas, armas, incivilidades) a partir del
Centro de Estudios y Análisis del Delito (CEAD) de la Subsecretaría de Prevención
del Delito. Abre el dominio de seguridad, hoy ausente del hub y uno de los más
demandados por periodismo de datos y civic-tech.

## Por qué es `under-review` y no `accepted`

El valor es máximo, pero la fuente **falla el criterio bloqueante de fuente
inspeccionable**: CEAD no expone una descarga oficial CSV/Excel estable; el único
acceso comprobado es scraping de tablas HTML, que ya se rompió con cambios del
sitio en 2024 y tras un ciberataque/cambio de ministerio en 2025. Por eso no entra
al carril publicable, pero su tradeoff neto positivo justifica registrarlo en el
carril `candidate` con fecha de revisión, en vez de rechazarlo.

## Qué lo promovería a `accepted`

- Una fuente estructurada y estable: un mirror en datos.gob.cl, un export oficial
  del propio CEAD, o una entrega formal de datos solicitada a la SPD.
- Confirmar licencia/atribución y la unidad de los casos (recuento vs tasa).

## Qué lo degradaría a `rejected`

- Llega `review_by` sin una fuente estructurada y el extractor sobre scraping
  sigue rompiéndose (supera `stalled_after_days`).
- El costo de mantención del scraping supera el valor de la capa.

## Riesgos y costos

- Fragilidad alta: un extractor sobre scraping exige mantención reactiva cada vez
  que el portal cambia.
- Hay que distinguir casos policiales (Carabineros + PDI) de otras métricas y no
  mezclar definiciones entre años si CEAD cambia categorías.
- La tasa por 100.000 habitantes depende de la población; documentar la base
  (proyección INE o Censo) usada como denominador.

## Enfoque recomendado

1. No construir el extractor live todavía: primero buscar una fuente estructurada
   estable (orden: datos.gob.cl → export oficial CEAD → solicitud formal a la SPD).
2. Si aparece, promover a `accepted` y a plan de implementación.
3. Si solo queda scraping y el valor lo justifica, implementar como `candidate`
   con snapshot periódico y validación estricta, nunca en el bundle público.
4. Mantener `review_by` y degradar si el dataset no madura.

## Esquema exploratorio

```text
dataset: delincuencia_comunal

codigo_region
codigo_comuna
nombre_comuna
anio
periodo                    # anual | trimestral (según fuente)
grupo_delito               # DMCS | VIF | drogas | armas | incivilidades | ...
tipo_delito
casos                      # casos policiales (Carabineros + PDI)
tasa_100k                  # casos por 100.000 habitantes
fuente
url_fuente
fecha_fuente
```

## Referencias iniciales

- Portal CEAD (Subsecretaría de Prevención del Delito):
  https://cead.minsegpublica.gob.cl/
- Ficha ChileAtiende del CEAD:
  https://www.chileatiende.gob.cl/fichas/114579-centro-de-estudios-y-analisis-del-delito-cead
- Evidencia del método de acceso real (scraping; fragilidad documentada en 2024 y
  2025): https://github.com/bastianolea/delincuencia_chile
