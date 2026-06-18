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
