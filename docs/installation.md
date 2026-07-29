# Instalación

## PyPI

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()
comunas = hub.load_polars("comunas")
```

## Caché de datos

La wheel no incluye los archivos de datos generados. En el primer uso, `ChileHub()`
descarga el archivo verificado `chile-hub-publishable-bundle.zip` desde GitHub
Releases, verifica su archivo SHA256 y lo extrae en el directorio de caché del usuario.

Usa la CLI para gestionar la caché:

```bash
chile-hub cache status
chile-hub cache update
chile-hub cache clear
```

Configura `CHILE_HUB_CACHE_DIR` para sobrescribir la ubicación de la caché.

Con la caché `latest`, chile-hub consulta GitHub Releases como máximo una vez por semana para avisar si existe una versión más reciente de los datos. No envía información de uso y los problemas de red no interrumpen la carga. Configura `CHILE_HUB_NO_UPDATE_CHECK=1` para desactivarlo o `CHILE_HUB_LANG=es|en` para elegir el idioma del aviso.

## Artefactos locales y sin conexión

Para uso sin conexión, puebla la caché antes de desconectarte:

```bash
chile-hub cache update
```

Para usar artefactos construidos desde una copia local, pasa el directorio normalizado:

```python
from chile_hub import ChileHub

hub = ChileHub(data_dir="data/normalized")
```

## Fijación de versión

Fija la versión del paquete con pip:

```bash
pip install chile-hub==1.15.0
```

Fija los datos seleccionando el tag de release correspondiente al actualizar la caché:

```bash
chile-hub cache update --data-version v1.15.0
```

## Desde R

Los artefactos del hub (Parquet, DuckDB, ZIP) son consumibles directamente
desde R sin instalar el paquete Python. Ver
[Uso desde R](r-quickstart.md) para recetas con `arrow` y `duckdb`.
