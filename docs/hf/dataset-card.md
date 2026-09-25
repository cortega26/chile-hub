---
license: other
license_name: chile-hub-data-licenses
license_link: https://github.com/cortega26/chile-hub/blob/main/DATA_LICENSES.md
pretty_name: chile-hub — Datos públicos de Chile curados
language: [es]
tags: [chile, open-data, government, tabular, parquet]
size_categories: [1M<n<10M]
{{DATASET_CONFIGS}}
---

# chile-hub

Datos públicos de Chile curados, normalizados y validados — {{DATASET_COUNT}} capas
(DPA, Censo 2024, indicadores económicos, salud, educación, finanzas
municipales, electoral y más). Espejo en Hugging Face Hub del bundle oficial
publicado en GitHub Releases: https://github.com/cortega26/chile-hub

Cada capa es una **configuración** independiente del dataset (selector "Subset"
en el visor): `comunas`, `censo_comunal`, `establecimientos_salud`,
`indicadores`, `pobreza_comunal`, `perfil_territorial_comunal`, etc.

## Uso

```python
from datasets import load_dataset

comunas = load_dataset("cortega26/chile-hub", "comunas", split="train")
```

```python
import duckdb

# Cero instalación de chile-hub: los Parquet del repo se leen por `hf://`
duckdb.sql("SELECT * FROM 'hf://datasets/cortega26/chile-hub/data/comunas.parquet' LIMIT 5").show()
```

## Capas y licencias

{{DATASET_TABLE}}

Cada capa documenta su fuente y licencia en
https://github.com/cortega26/chile-hub/tree/main/docs/datasets — atribución
requerida según la licencia de cada fuente (ver DATA_LICENSES.md).
