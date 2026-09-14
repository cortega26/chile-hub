# Idea: Estadísticas vitales comunales (nacimientos y defunciones)

## Estado

- **Decision actual**: accepted
- **Prioridad tentativa**: P1
- **Esfuerzo estimado**: M (layouts heterogéneos 2010-2023 ya resueltos en el extractor)
- **Riesgo**: LOW
- **Categoria**: civic-data / demography / health
- **Registrado**: 2026-09-14
- **Implementado**: dataset `estadisticas_vitales` (extractor + validación + contrato + docs)

## Propuesta

Publicar nacimientos y defunciones por comuna de residencia y sexo desde los
Anuarios de Estadísticas Vitales del INE, en serie anual desde 2010.

## Valor

- Dolor recurrente: demografía comunal actualizada solo existía vía censo
  (decenal) o REDATAM interactivo; los tabulados anuales del INE requieren
  limpieza manual por sus layouts heterogéneos.
- Cruce directo con `codigo_comuna` (346/346 comunas, cobertura total).
- Utilidad transversal: salud pública, planificación municipal, periodismo de
  datos, investigación (crecimiento natural comunal, fecundidad, mortalidad).
- Bajo costo operacional: un anuario definitivo al año, descubrimiento
  automático de archivos.

## Decisiones de alcance

- Solo anuarios **definitivos**: los boletines provisionales/coyunturales no
  traen desglose comunal (verificado 2026-09-14).
- Grano fuente (`evento` × `sexo` según lo publicado), sin tasas ni
  crecimiento natural almacenados (derivables por el consumidor).
- Fuera del MVP: matrimonios, AUC, defunciones fetales/infantiles por comuna
  (existen en los mismos anuarios; extensión natural).

## Mini-scorecard

`valor alto (demografía anual comunal, hueco real) · legal CC BY 4.0 limpio · tamaño chico (~14k filas) · cadencia anual barata · fragilidad media (layouts por año, mitigada con reconciliación contra fila TOTAL) → accepted`
