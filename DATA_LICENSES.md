# Data Licensing And Attribution

`chile-hub` code is distributed under the MIT License.

The datasets published by `chile-hub` keep their source-specific reuse terms,
licenses, and attribution requirements. The canonical machine-readable source
of truth is the generated metadata in:

- `data/normalized/dataset_catalog.json`
- `data/normalized/redistribution_report.json`
- `data/normalized/provenance_report.json`

The PyPI package does not bundle generated datasets in the wheel. It downloads
verified GitHub Release assets and uses the metadata above to expose source,
license, provenance, redistribution, and attribution information.

Current source families include BCN ArcGIS, Banco Central de Chile via
`mindicador.cl`, INE, MINSAL/datos.gob.cl, BCN/SERVEL legal mappings, and
MINEDUC. Before redistributing derived artifacts, inspect:

```bash
chile-hub redistribution
chile-hub provenance
```

If a source has ambiguous or restricted terms, the project policy is to exclude
it from public bundles until the redistribution status is resolved.
