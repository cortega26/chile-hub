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
| --- | --- |
| Descargar o explorar los artefactos publicados | [Sitio público](https://tooltician.com/chile-hub/) |
| Instalar el paquete y verificar datos locales | [Instalación](installation.md) |
| Ver métodos, clases y excepciones del paquete | [Referencia de API](reference.md) |
| Entender qué datasets entran al hub | [Criterios de inclusión](dataset-inclusion-criteria.md) |
| Revisar estabilidad de esquemas y versionado | [Compatibilidad de datasets](dataset-compatibility-policy.md) y [Política de versionado](versioning-policy.md) |

Repositorio: <https://github.com/cortega26/chile-hub>
