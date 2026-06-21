# Ideas de datasets

Esta carpeta registra ideas de capas evaluadas contra los criterios de
inclusión, junto con su estado de decisión. Una idea permanece aquí hasta que se
promueve a `plans/` como plan ejecutable.

Usar este espacio cuando una propuesta necesita validar fuente, licencia,
estabilidad, volumen, demanda o encaje de producto antes de convertirse en un
plan de trabajo. Una idea registrada aqui puede terminar como:

- `accepted`: pasa criterios y merece plan de implementacion.
- `under-review`: tradeoff neto positivo pese a ser imperfecto en una dimensión blanda; entra al carril `candidate` con `review_by` y regla de salida.
- `needs-research`: requiere validar fuente, licencia, esquema o costo.
- `deferred`: es razonable, pero no tiene prioridad por ahora.
- `rejected`: falla criterios bloqueantes o no encaja con el hub.

Cuando una idea pase a implementacion, moverla a `plans/` como plan ejecutable
y actualizar `docs/dataset-inclusion-criteria.md` si cambia el criterio de
decision.

## Ideas registradas

| Idea | Estado | Nota |
|---|---|---|
| [Pobreza comunal (CASEN / SAE)](pobreza-comunal-casen.md) | accepted | Fuente XLSX comunal del Observatorio Social verificada; pendiente el manejo de comunas sin estimación. |
| [Consumo eléctrico comunal (CNE / Energía Abierta)](consumo-electrico-comunal.md) | accepted | Descarga Excel + API JSON verificadas; capa limpia de bajo costo operacional. |
| [Delincuencia comunal (CEAD / DMCS)](delincuencia-cead.md) | under-review | Alto valor (seguridad), pero solo scraping frágil; carril `candidate`, `review_by` 2026-09-21. |
| [Plus Codes y puntos de referencia vial](plus-codes-road-reference-layer.md) | needs-research | Requiere validar fuente vial redistribuible y volumen nacional. |
| [Apoyos formales para emprendedores](entrepreneurship-support-programs.md) | needs-research | Requiere evaluar si Chile Emprende u otra fuente expone datos estructurados. |
| [Resultados electorales, autoridades electas y partidos](electoral-results-authorities-parties.md) | needs-research | Requiere separar datos agregados publicables de datos personales electorales excluidos. |
