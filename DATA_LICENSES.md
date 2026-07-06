# Licencias de datos y atribución

El código de `chile-hub` se distribuye bajo la licencia MIT.

Los datasets publicados por `chile-hub` mantienen sus términos de reutilización,
licencias y requisitos de atribución específicos de cada fuente. La fuente de
verdad canónica y legible por máquina es el metadata generado en:

- `data/normalized/dataset_catalog.json`
- `data/normalized/redistribution_report.json`
- `data/normalized/provenance_report.json`

El paquete PyPI no incluye los datasets generados en la wheel. Descarga
assets verificados de GitHub Release y utiliza el metadata anterior para
exponer información sobre fuente, licencia, procedencia, redistribución y
atribución.

Las familias de fuentes actuales incluyen BCN ArcGIS, Banco Central de Chile vía
`mindicador.cl`, INE, MINSAL/datos.gob.cl, BCN/SERVEL (mapeos legales), MINEDUC,
SINIM/SUBDERE, Ministerio de Economía/datos.gob.cl, y artefactos derivados de perfil/estado de chile-hub. Antes de
redistribuir artefactos derivados, inspecciona:

```bash
chile-hub redistribution
chile-hub provenance
```

Si una fuente tiene términos ambiguos o restrictivos, la política del proyecto es
excluirla de los paquetes públicos hasta que se resuelva el estado de
redistribución.

## Datasets con licencia share-alike (segregados)

El dataset **`autoridades_locales`** (gobernadores regionales; carril `candidate`) se
compila desde **Wikipedia**, cuya licencia es **CC-BY-SA 4.0 (share-alike)**. Para
evitar que la obligación share-alike se propague al resto del bundle (mayormente CC-BY /
CC0), este dataset se mantiene **segregado**: los cargos de fuente oficial (diputados y
senadores) viven en `autoridades_electas` (CC-BY) y **no** se mezclan con los de
Wikipedia. Quien redistribuya `autoridades_locales` debe cumplir CC-BY-SA (atribución +
share-alike). Ver `docs/datasets/autoridades_locales.md`.
