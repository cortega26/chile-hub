---
license: other
pretty_name: chile-hub — Datos públicos de Chile curados
language: [es]
tags: [chile, open-data, government, tabular, parquet]
size_categories: [100K<n<1M]
---

# chile-hub

Datos públicos de Chile curados, normalizados y validados — 19 capas
(DPA, Censo 2024, indicadores económicos, salud, educación, finanzas
municipales, electoral y más). Espejo en Hugging Face Hub del bundle oficial
publicado en GitHub Releases: https://github.com/cortega26/chile-hub

## Uso

```python
from datasets import load_dataset
comunas = load_dataset("cortega26/chile-hub", data_files="data/comunas.parquet")
```

## Capas y licencias

{{DATASET_TABLE}}

Cada capa documenta su fuente y licencia en
https://github.com/cortega26/chile-hub/tree/main/docs/datasets — atribución
requerida según la licencia de cada fuente (ver DATA_LICENSES.md).
