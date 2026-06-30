# Delincuencia comunal — CEAD

> **Carril:** `candidate` — NO incluido en el bundle público.
> **Fuente:** Centro de Estudios y Análisis del Delito (CEAD), Subsecretaría de Prevención del Delito, Ministerio del Interior.
> **review_by:** 2026-09-21 · **stalled_after_days:** 90

## Descripción

Casos policiales de Delitos de Mayor Connotación Social (DMCS) y otras categorías
por comuna y mes, reportados por Carabineros y la Policía de Investigaciones (PDI)
al Ministerio del Interior. Los datos se obtienen vía scraping del endpoint PHP del
portal CEAD y se publican exclusivamente en el carril `candidate` (fuera del bundle
público), por fragilidad de la fuente y falta de licencia explícita.

## Schema

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `anio` | integer | Año de los casos |
| `mes` | integer | Mes (1-12) |
| `nombre_mes` | string | Nombre del mes |
| `codigo_comuna` | string(5) | Código CUT de la comuna |
| `nombre_comuna` | string | Nombre de la comuna |
| `familia_delito` | string | Clave canónica de la familia de delito |
| `nombre_familia` | string | Nombre descriptivo de la familia |
| `casos` | integer | Número de casos policiales |
| `fuente` | string | Organismo emisor |
| `url_fuente` | string | URL del portal CEAD |

## Familias de delito

| Clave | Descripción |
|-------|-------------|
| `delitos_contra_la_vida` | Homicidios, femicidios, lesiones, etc. |
| `robos_violentos` | Robos con violencia o intimidación |
| `violencia_intrafamiliar` | Violencia intrafamiliar (VIF) |
| `delitos_asociados_a_drogas` | Tráfico, microtráfico y otros delitos de drogas |
| `delitos_asociados_a_armas` | Porte y tenencia ilegal de armas |
| `delitos_contra_propiedad_no_violentos` | Hurtos, robos frustrados y otros |
| `incivilidades` | Desórdenes públicos, comercio ilegal, etc. |
| `otros_delitos_o_faltas` | Resto de delitos y faltas no clasificados |

## Cobertura

- **Geográfica:** 346 comunas (teórica; real depende del éxito del scraping)
- **Temporal:** 2005 en adelante (según disponibilidad del portal CEAD)
- **Frecuencia de actualización:** mensual (workflow programado)

## Limitaciones

1. **Fuente frágil:** el scraping depende de un endpoint PHP sin API pública
   documentada. Cambios en el portal pueden romper el extractor sin aviso.
2. **Sin licencia explícita:** el portal CEAD no declara términos de
   redistribución. Por esto el dataset va en carril `candidate`, no en el
   bundle público.
3. **Agregación por familia:** este extractor obtiene datos a nivel de
   *familia* de delito (8 categorías). Para subcategorías (hurtos, robos en
   lugar habitado, etc.) se requiere un desarrollo adicional.
4. **Casos, no denuncias:** los valores corresponden a casos policiales
   (Carabineros + PDI), no a denuncias civiles ni a condenas judiciales.
5. **Scraping por comuna individual:** se requiere una petición HTTP por
   comuna (~346 por año), lo que toma 10-15 minutos.

## Regla de salida

Si para `review_by` (2026-09-21) no aparece una fuente estructurada estable
(API, descarga CSV/Excel oficial, o mirror en datos.gob.cl) y el scraping
sigue rompiéndose, este dataset se degrada a `rejected` y se archiva.

## Referencias

- Portal CEAD: https://cead.minsegpublica.gob.cl/estadisticas-delictuales/
- Ficha ChileAtiende: https://www.chileatiende.gob.cl/fichas/114579-centro-de-estudios-y-analisis-del-delito-cead
- Scraper R de referencia: https://github.com/bastianolea/delincuencia_chile
- Revisión legal: `docs/legal/fase-3-legal-review.md` §2
- Plan 022 — Ola B2.1: `plans/022-plan-avance-narrativa-confiabilidad.md`
