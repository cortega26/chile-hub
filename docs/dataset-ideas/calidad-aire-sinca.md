# Idea: Calidad del aire por estación (SINCA / MMA)

## Estado

- **Decision actual**: accepted
- **Prioridad tentativa**: P1
- **Esfuerzo estimado**: S (un JSON diario, sin scraping)
- **Riesgo**: LOW
- **Categoria**: civic-data / environment / health
- **Registrado**: 2026-09-15
- **Implementado**: dataset `calidad_aire` (extractor + validación + contrato + docs)

## Propuesta

Publicar promedios diarios de contaminantes por estación de monitoreo desde
el SINCA (MMA), con cruce a comuna vía el campo `comuna` del inventario
oficial (sin reverse-geocoding).

## Valor

- Dolor recurrente: la calidad del aire comunal solo existe en el portal
  interactivo del SINCA o vía scraping de sus CGI legacy; no hay serie
  descargable curada por comuna.
- Utilidad transversal: salud pública, GEC/planes de descontaminación,
  periodismo de datos, investigación (MP2.5 y mortalidad).
- Un solo request diario (JSON con inventario + 24 h) en vez de crawlear
  125 estaciones: costo operacional mínimo.

## Decisiones de alcance

- Grano diario (promedio + máximo + horas válidas), no horario: 6.5M de
  filas/año romperían el modelo de bundle (criterio empresas).
- Serie incremental desde la primera cosecha (el JSON no da historia);
  staging se siembra desde el Parquet publicado si se pierde el caché.
- Cobertura parcial documentada (~65 comunas); sin imputación.
- Contaminantes: MP2.5, MP10, SO2, NO2, CO, O3 con unidad explícita.

## Mini-scorecard

`valor alto (serie ambiental comunal, hueco real) · legal public-api-review-terms limpio (MMA, API abierta) · tamaño chico incremental (~750 filas/día) · cadencia diaria barata (1 request) · fragilidad baja (JSON oficial del propio mapa) → accepted`
