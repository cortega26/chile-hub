---
title: "chile-hub — Documentación técnica"
description: >
  Documentación técnica de chile-hub: capa de datos reproducible y curada
  sobre datasets públicos oficiales de Chile. Incluye guía de instalación,
  referencia de API, criterios de inclusión de datasets y políticas.
category: documentation-index
audience: [user, developer, data-scientist]
priority: high
related_docs:
  - installation.md        # Guía de instalación
  - api.md                 # Referencia de API
  - dataset-inclusion-criteria.md  # Criterios de inclusión
  - dataset-compatibility-policy.md  # Compatibilidad de datasets
  - versioning-policy.md   # Política de versionado
  - release.md             # Proceso de release
last_updated: 2026-07-14
---

# chile-hub

Documentación técnica de `chile-hub`, una capa de datos reproducible y curada sobre
datasets públicos oficiales de Chile.

El paquete normaliza, valida y publica datasets listos para análisis territorial,
productos de datos y flujos reproducibles en Python, DuckDB, Parquet y JSON.

## Primeros pasos

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()
comunas = hub.load_polars("comunas")
print(comunas.head())
```

## Dónde ir

| Necesitas | Ir a |
|---|---|
| Descargar o explorar los artefactos publicados | [Sitio público](https://tooltician.com/chile-hub/) |
| Instalar el paquete y verificar datos locales | [Instalación](installation.md) |
| Ver métodos, clases y excepciones del paquete | [Referencia de API](api.md) |
| Entender qué datasets entran al hub | [Criterios de inclusión](dataset-inclusion-criteria.md) |
| Revisar estabilidad de esquemas y versionado | [Compatibilidad de datasets](dataset-compatibility-policy.md) y [Política de versionado](versioning-policy.md) |
| Proceso de release | [Release](release.md) |

Repositorio: <https://github.com/cortega26/chile-hub>
