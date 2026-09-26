---
title: "chile-hub — Catálogo de Datasets"
description: >
  Catálogo de capas de datos publicadas por chile-hub. Cada ficha responde:
  qué contiene, de dónde viene, nivel de confianza, cómo se cruza y advertencias.
category: dataset-catalog
audience: [user, data-scientist, developer]
priority: high
related_docs:
  - ../dataset-inclusion-criteria.md  # Criterios de aceptación/deprecación
  - ../dataset-compatibility-policy.md  # Política de compatibilidad
  - status_changelog.md              # Historial de cambios de estado
last_updated: 2026-07-14
---

# Catálogo de Datasets

Este catálogo describe las capas de datos publicadas por `chile-hub`.

Cada ficha busca responder cinco preguntas:

1. **Qué contiene** la capa
2. **De dónde viene** (fuente y método de acceso)
3. **Qué tan confiable** y automatizable es (tier A/B/C)
4. **Cómo se cruza** con otros datos (claves de join)
5. **Qué advertencias** debes conocer antes de usarla

Las propuestas de nuevas capas se evalúan con los criterios públicos de
[`docs/dataset-inclusion-criteria.md`](../dataset-inclusion-criteria.md).

## Capas actuales

<!-- START_DATASETS_INDEX -->

| Capa | Qué contiene |
|:---|:---|
| [`autoridades_electas`](autoridades_electas.md) | Autoridades electas en ejercicio de Chile (diputados y senadores): partido, distrito electoral/circunscripción senatorial, región y período de mandato. |
| [`autoridades_locales`](autoridades_locales.md) | Autoridades locales/subnacionales de Chile: gobernadores regionales (Wikipedia, CC-BY-SA) y alcaldes (BCN SIIT, dato público gubernamental). Wikipedia se mantiene como fuente de gobernadores y enriquecimiento opcional de periodo_inicio para alcaldes. Dataset segregado de autoridades_electas por licencia mixta. |
| [`calidad_aire`](calidad_aire.md) | Promedios diarios de contaminantes atmosféricos (MP2.5, MP10, SO2, NO2, CO, O3) por estación de monitoreo, desde el SINCA (MMA). Cobertura parcial: ~65 comunas con estación. |
| [`censo_comunal`](censo_comunal.md) | Perfil demografico comunal del Censo 2024 con sexo y grandes grupos de edad. |
| [`censo_hogares_viviendas`](censo_hogares_viviendas.md) | Viviendas y hogares censados por comuna, ocupacion y tamano medio del hogar. |
| [`comunas`](comunas.md) | Base territorial normalizada para cruces por region, provincia y comuna. |
| [`comunas_enriquecidas`](comunas_enriquecidas.md) | Comunas con coordenadas de cabecera y poblacion estimada INE, listas para analisis territorial sin joins adicionales. |
| [`consumo_electrico_comunal`](consumo_electrico_comunal.md) | Consumo eléctrico anual por comuna y tipo de cliente (Residencial, Comercial, Industrial, Agrícola, Alumbrado Público, Otros), publicado por la Comisión Nacional de Energía (CNE) en el portal Energía Abierta. DEPRECATED: la fuente Junar de energiaabierta.cl fue decomisionada (investigado 2026-07-07); el dataset solo publica datos de muestra (FALLBACK_ROWS), no está en el bundle público. Ver data/source_registry.json. |
| [`delincuencia_comunal`](delincuencia_comunal.md) | DEPRECATED 2026-09-15: Casos policiales de Delitos de Mayor Connotación Social (DMCS) y otras categorías por comuna y mes. Sin fuente estructurada oficial (solo scraping frágil) y no redistribuible; extractor neutralizado y fuera del scrape mensual. Ver docs/datasets/delincuencia_comunal.md. |
| [`distritos_electorales`](distritos_electorales.md) | Asociación de comunas a distritos electorales (diputados) y circunscripciones senatoriales. |
| [`empresas`](empresas.md) | Registro de Empresas y Sociedades (RES) con RUT, razon social, tipo societario, capital, fecha de constitucion y comuna de domicilio. |
| [`establecimientos_educacionales`](establecimientos_educacionales.md) | Directorio oficial del Ministerio de Educación (MINEDUC) con Rol Base de Datos (RBD), ubicación y dependencia administrativa. |
| [`establecimientos_salud`](establecimientos_salud.md) | Directorio vigente de establecimientos de salud con tipo, dependencia, urgencia y ubicacion. |
| [`estadisticas_vitales`](estadisticas_vitales.md) | Nacimientos y defunciones por comuna de residencia y sexo, desde los Anuarios de Estadísticas Vitales del INE (definitivos, 2010 en adelante). |
| [`finanzas_municipales`](finanzas_municipales.md) | Indicadores financieros municipales anuales desde SINIM/SUBDERE. CAPA PARCIAL/CANDIDATO: 3 de 346 comunas (0.9%). Usar con precaución; no representa cobertura nacional. |
| [`geometria_comunal`](geometria_comunal.md) | Límites poligonales de las 346 comunas de Chile (GeoParquet, geometría 'generalizada' — simplificada para cartografía a escala nacional, no apta para trabajo de precisión geodésica ni catastral). Fuente: BCN ArcGIS (tematico/Comunas_Generalizadas). Artefacto separado de `comunas`, unido por `codigo_comuna`. |
| [`indicadores`](indicadores.md) | Serie de indicadores economicos diarios de referencia para analisis y software. |
| [`indicadores_urbanos_siedu`](indicadores_urbanos_siedu.md) | Indicadores urbanos SIEDU en formato largo con cobertura comunal parcial esperada. |
| [`partidos_politicos`](partidos_politicos.md) | Roster de partidos políticos de Chile (Cámara de Diputadas y Diputados), con estado_legal y fecha_constitucion completados por join de nombre contra el registro público de SERVEL. |
| [`perfil_territorial_comunal`](perfil_territorial_comunal.md) | Perfil comunal curado que consolida DPA, censo, salud, educación, finanzas, SIEDU y distritos. |
| [`permisos_edificacion`](permisos_edificacion.md) | Viviendas en unidades y superficie (m2) por comuna y año —casas y departamentos— desde las estadísticas de permisos de edificación del CEDOC (MINVU), serie desde 2002. |
| [`pobreza_comunal`](pobreza_comunal.md) | Estimaciones de pobreza comunal por ingresos y multidimensional derivadas de la encuesta CASEN mediante metodología SAE (Estimación de Áreas Pequeñas). Incluye tasa, límite inferior y superior del intervalo de confianza por comuna, año y dimensión. |
| [`provincias`](provincias.md) | Capa derivada de provincias para cruces intermedios entre region y comuna. |
| [`regiones`](regiones.md) | Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel. |
| [`resultados_educacionales`](resultados_educacionales.md) | Resultados educacionales agregados por comuna y año, sin registros personales. |

<!-- END_DATASETS_INDEX -->

> La tabla se regenera desde `data/dataset_catalog_config.json` en cada build
> (`make sync-docs`); no editarla a mano.

## Tiers de confiabilidad

| Tier | Descripción | Acción |
|:---:|:---|:---|
| **A** | Altamente automatizable. Fuente estable, estructurada, bajo costo de mantenimiento. | Prioridad para bundle público |
| **B** | Semi-automatizable. Requiere vigilancia por drift, ajustes manuales o validaciones más fuertes. | Incluir con monitoreo activo |
| **C** | Experimental o manual. No apto como capa crítica. | Carril candidate o excluir |

## Checklist para nuevas capas

Toda nueva capa debe documentar:

- [ ] Propósito claro y casos de uso
- [ ] Fuente, URL y método de acceso
- [ ] Frecuencia esperada de actualización
- [ ] Notas legales (licencia, atribución, redistribución)
- [ ] Esquema completo (columnas, tipos, claves primarias)
- [ ] Reglas de normalización aplicadas
- [ ] Campos de join sugeridos
- [ ] Advertencias y limitaciones conocidas
- [ ] Tier de confiabilidad asignado
