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

| Dataset | Categoría |
|---|---|
| [regiones](./regiones.md) | Territorio base |
| [provincias](./provincias.md) | Territorio base |
| [comunas](./comunas.md) | Territorio base |
| [comunas_enriquecidas](./comunas_enriquecidas.md) | Territorio base |
| [indicadores](./indicadores.md) | Economía |
| [censo_comunal](./censo_comunal.md) | Demografía |
| [censo_hogares_viviendas](./censo_hogares_viviendas.md) | Demografía |
| [establecimientos_salud](./establecimientos_salud.md) | Servicios públicos |
| [distritos_electorales](./distritos_electorales.md) | Electoral |
| [establecimientos_educacionales](./establecimientos_educacionales.md) | Servicios públicos |
| [finanzas_municipales](./finanzas_municipales.md) | Economía |
| [resultados_educacionales](./resultados_educacionales.md) | Educación |
| [indicadores_urbanos_siedu](./indicadores_urbanos_siedu.md) | Indicadores urbanos |
| [perfil_territorial_comunal](./perfil_territorial_comunal.md) | Derivado |
| [empresas](./empresas.md) | Economía |
| [status_changelog](./status_changelog.md) | Meta |

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
