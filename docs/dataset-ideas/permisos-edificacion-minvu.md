# Idea: Permisos de edificación por comuna (MINVU CEDOC)

## Estado

- **Decision actual**: accepted
- **Prioridad tentativa**: P1
- **Esfuerzo estimado**: S (fuente tabular limpia, un archivo anual)
- **Riesgo**: LOW
- **Categoria**: civic-data / economy / housing
- **Registrado**: 2026-09-15
- **Implementado**: dataset `permisos_edificacion` (extractor + validación + contrato + docs)

## Propuesta

Publicar viviendas autorizadas (unidades y superficie) por comuna y año desde
las estadísticas de permisos de edificación del CEDOC (MINVU), serie 2002 en
adelante, como proxy de actividad económica y dinamismo local.

## Valor

- Dolor recurrente: la actividad constructora comunal solo existe en el
  "Sistema de Edificación" del INE (requiere login) o en tabulados dispersos;
  el CEDOC la publica abierta pero hay que normalizarla a mano.
- Cruce directo con `codigo_comuna` (346/346 comunas, cobertura total).
- Complementa `finanzas_municipales` y enriquece `perfil_territorial_comunal`
  con una señal económica anual de bajo costo.
- Fuente tabular estable, un archivo anual, licencia con autorización
  explícita de uso con cita.

## Decisiones de alcance

- Archivo **anual** por comuna (el mensual queda como extensión futura).
- Grano ancho: 6 métricas (unidades/superficie × total/casas/departamentos)
  por (año, comuna); total == casas + departamentos como invariante validada.
- Serie histórica de Ñuble fusionada (secciones "Biobío" + "Ñuble
  (ex-Biobío)" complementarias).
- `estado_dato` provisional para años `(*)` y el último en curso.

## Mini-scorecard

`valor alto (proxy económico comunal, hueco real) · legal uso-con-cita limpio · tamaño chico (~9k filas) · cadencia mensual barata · fragilidad baja (un XLSX estable + descubrimiento por biblionumber) → accepted`
