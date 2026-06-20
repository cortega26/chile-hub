"""Módulos de construcción del pipeline de ChileHub.

Este paquete descompone el antiguo God module `src/build_dev_db.py` en
módulos cohesivos:

- `_shared`: rutas, constantes y configuración de catálogo compartidas.
- `io_utils`: escritura atómica de archivos (JSON, Parquet, Excel) y hashing.
- `formats`: builders de formato (DuckDB, SQLite, Excel, archivos planos).
- `metadata`: carga, validación y enriquecimiento de metadatos y contratos.
- `reports`: builders de reportes y estados del hub (JSON).
- `artifacts`: índice de artefactos, manifiesto y bundles publicables.
- `datasets`: builders de datasets derivados (perfil territorial, capas geográficas).
- `catalog`: escritura del metadata del pipeline y del catálogo de datasets.
- `landing`: sincronización de metadatos JSON-LD en la landing page.

`build_dev_db.py` re-exporta los nombres públicos para mantener
compatibilidad con scripts externos (`scripts/verify_pipeline.py`) y tests.
"""
