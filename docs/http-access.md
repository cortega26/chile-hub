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
import polars as pl

df = pl.read_parquet("https://tooltician.com/chile-hub/data/normalized/comunas.parquet")
print(df.head())
```

O usando la librería, con el descriptor Frictionless:

```python
from chile_hub import ChileHub

hub = ChileHub.from_datapackage(
    "https://tooltician.com/chile-hub/data/normalized/datapackage.json"
)
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
