# Acceso HTTP estático

Los artefactos publicados de chile-hub (Parquet, JSON, catálogo) se sirven como
archivos estáticos en un base URL estable, sin necesidad de instalar la librería
Python ni clonar el repositorio:

```
https://tooltician.com/chile-hub/data/normalized/
```

> **Nota de estabilidad**: este directorio refleja siempre la **última build**
> publicada (`latest`), no una versión pinada. Para reproducibilidad exacta sobre
> una versión específica, usa el bundle ZIP versionado de
> [GitHub Releases](https://github.com/cortega26/chile-hub/releases) en su lugar
> (ver [Fijación de versión](installation.md#fijacion-de-version)).

## Descubrir los datasets: `data.json` (DCAT)

[`data.json`](https://tooltician.com/chile-hub/data/normalized/data.json) es un
catálogo cosechable estilo DCAT-US (el perfil que usa data.gov y la mayoría de
los portales de datos abiertos gubernamentales basados en CKAN) generado
automáticamente desde `datapackage.json`. Lista cada dataset con su
`downloadURL` absoluta:

```bash
curl -s https://tooltician.com/chile-hub/data/normalized/data.json | jq '.dataset[0]'
```

## Python

```python
import io

import polars as pl
import requests

url = "https://tooltician.com/chile-hub/data/normalized/comunas.parquet"
df = pl.read_parquet(io.BytesIO(requests.get(url, timeout=60).content))
print(df.head())
```

> **Por qué no `pl.read_parquet(url)` directo:** GitHub Pages no envía el header
> `Content-Length` y el reader HTTP de polars lo exige (`Content-Length Header
> missing from response`). Descarga con `requests` (como arriba) o usa DuckDB
> con `httpfs`, que sí lo soporta.

O usando la librería, con el descriptor Frictionless:

```python
from chile_hub import ChileHub

hub = ChileHub.from_datapackage("https://tooltician.com/chile-hub/data/normalized/datapackage.json")
```

> `from_datapackage(url)` valida el descriptor remoto pero todavía no devuelve un
> `ChileHub` funcional sobre datos remotos (ver `docs/adr/ADR-010-acceso-http-estatico-y-dcat.md`,
> Preguntas abiertas). Para consumir datos hoy, usa `ChileHub()` sin argumentos
> (descarga y cachea el bundle automáticamente) o lee el Parquet directo por HTTP
> como en el ejemplo de arriba.

## R (arrow)

```r
library(arrow)

df <- read_parquet("https://tooltician.com/chile-hub/data/normalized/comunas.parquet")
head(df)
```

Ver [Uso desde R](r-quickstart.md) para más recetas con `arrow` y `duckdb`.

## JavaScript / Observable

```javascript
const response = await fetch(
  "https://tooltician.com/chile-hub/data/normalized/comunas.json"
);
const comunas = await response.json();
console.log(comunas[0]);
```

## DuckDB (SQL, cualquier lenguaje)

```sql
INSTALL httpfs; LOAD httpfs;
SELECT codigo_comuna, nombre_comuna
FROM 'https://tooltician.com/chile-hub/data/normalized/comunas.parquet'
LIMIT 5;
```

## Hugging Face Hub (cero instalación, también para agentes)

El bundle publicable se replica en
[Hugging Face Hub](https://huggingface.co/datasets/cortega26/chile-hub) con un
**subset por capa** (selector "Subset" del visor y SQL Console incluidos). Es el
camino más corto para explorar los datos sin instalar nada:

```python
from datasets import load_dataset

comunas = load_dataset("cortega26/chile-hub", "comunas", split="train")
```

DuckDB 1.5+ lee el repositorio directamente con el protocolo `hf://`
(extensión `httpfs`, sin descargar el bundle):

```sql
INSTALL httpfs; LOAD httpfs;
SELECT codigo_comuna, nombre_comuna
FROM 'hf://datasets/cortega26/chile-hub/data/comunas.parquet'
LIMIT 5;
```

> La revisión `@~parquet` (`hf://datasets/cortega26/chile-hub@~parquet/…`)
> contiene la copia auto-convertida por Hugging Face; los archivos bajo
> `data/` son los originales del bundle. El mirror publica únicamente el carril
> `stable_publishable`; para el carril `candidate` usa el sitio estático o el
> paquete Python.
