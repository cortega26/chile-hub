---
title: "chile-hub — DATA_LICENSES.md"
description: >
  Política de licencias de datos y atribución para chile-hub.
  Código bajo MIT; datasets mantienen licencias de sus fuentes oficiales.
  Incluye manejo de datasets share-alike segregados.
category: legal-policy
audience: [user, contributor, redistributor]
priority: high
source_of_truth_for: >
  Licencias de datasets, requisitos de atribución, política de exclusión,
  manejo de datasets CC-BY-SA.
related_docs:
  - AGENTS.md §6           # Política legal completa y semáforo de reutilización
  - docs/datasets/autoridades_locales.md  # Dataset share-alike segregado
last_updated: 2026-07-14
---

# Licencias de Datos y Atribución

## Visión general

| Componente | Licencia |
|---|---|
| **Código Python** (`chile-hub`) | [MIT](LICENSE) |
| **Datasets publicados** | Licencias específicas de cada fuente oficial |

Los datasets publicados por `chile-hub` mantienen sus términos de reutilización,
licencias y requisitos de atribución específicos de cada fuente. La fuente de
verdad canónica y legible por máquina es el metadata generado en:

| Archivo | Contenido |
|---|---|
| `data/normalized/dataset_catalog.json` | Catálogo completo con schemas y metadatos |
| `data/normalized/redistribution_report.json` | Estado legal de reúso por dataset |
| `data/normalized/provenance_report.json` | Trazabilidad de origen y marcas de tiempo |

El paquete PyPI no incluye los datasets generados en la wheel. Descarga
assets verificados de GitHub Release y utiliza el metadata anterior para
exponer información sobre fuente, licencia, procedencia, redistribución y
atribución.

## Fuentes actuales

BCN ArcGIS, Banco Central de Chile vía `mindicador.cl`, INE, MINSAL/datos.gob.cl,
BCN/SERVEL (mapeos legales), MINEDUC, SINIM/SUBDERE, Ministerio de Economía/datos.gob.cl,
y artefactos derivados de perfil/estado de chile-hub. Antes de redistribuir artefactos
derivados, inspecciona:

```bash
chile-hub redistribution
chile-hub provenance
```

Si una fuente tiene términos ambiguos o restrictivos, la política del proyecto es
**excluirla** de los paquetes públicos hasta que se resuelva el estado de
redistribución.

## Datasets con licencia share-alike (segregados)

El dataset **`autoridades_locales`** (gobernadores regionales; carril `candidate`) se
compila desde **Wikipedia**, cuya licencia es **CC-BY-SA 4.0 (share-alike)**. Para
evitar que la obligación share-alike se propague al resto del bundle (mayormente CC-BY /
CC0), este dataset se mantiene **segregado**: los cargos de fuente oficial (diputados y
senadores) viven en `autoridades_electas` (CC-BY) y **no** se mezclan con los de
Wikipedia. Los alcaldes provienen de BCN SIIT (dato público gubernamental, 100% cobertura);
los gobernadores regionales son de Wikipedia (CC-BY-SA). Quien redistribuya
`autoridades_locales` debe cumplir ambas licencias (CC BY para alcaldes, CC-BY-SA para
gobernadores). Ver `docs/datasets/autoridades_locales.md`.
