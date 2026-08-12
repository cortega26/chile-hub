# Uso desde R

El hub publica artefactos (Parquet, DuckDB, ZIP) que R lee nativamente;
no hace falta instalar el paquete Python.

## Opción A — ZIP del bundle (recomendada)

Descarga el bundle completo desde GitHub Releases y lee los Parquet individuales:

```r
url <- "https://github.com/cortega26/chile-hub/releases/latest/download/chile-hub-publishable-bundle.zip"
tmp <- tempfile(fileext = ".zip")
download.file(url, tmp, mode = "wb")
unzip(tmp, exdir = "chile-hub-data")

library(arrow)
comunas <- read_parquet("chile-hub-data/data/normalized/comunas.parquet")
head(comunas)
```

Para verificar la integridad del ZIP descargado, compara su hash con el archivo
`chile-hub-publishable-bundle.zip.sha256` que se adjunta al mismo release
(usa el paquete `digest` o `openssl dgst -sha256` en terminal).

> **Nota:** la URL `releases/latest/download/` es estable entre versiones;
> apunta siempre al release publicado más reciente. El bundle contiene los
> artefactos bajo el prefijo `data/normalized/` (ver la Opción B para leer
> sin descargar).

## Opción B — Parquet individual por URL directa

Lee un dataset directamente desde el sitio estático sin descargar el bundle completo:

```r
library(arrow)
comunas <- read_parquet("https://tooltician.com/chile-hub/data/normalized/comunas.parquet")
head(comunas)
```

Reemplaza `comunas.parquet` por el nombre del dataset que necesitas (ver la
[documentación de datasets](docs/datasets/) para la lista completa).

## Opción C — DuckDB (cruces SQL)

El bundle publicable no incluye `chile_data.duckdb` (no viaja en el ZIP;
solo se publican Parquet + JSON). Para cruces SQL con DuckDB, lee los
Parquet directamente desde el bundle descargado (rutas locales, sin
extensiones):

```r
library(duckdb)
con <- dbConnect(duckdb())

dbGetQuery(con,
  "SELECT c.nombre_comuna, c.nombre_region, cc.poblacion_censada
   FROM read_parquet('chile-hub-data/data/normalized/comunas.parquet') c
   JOIN read_parquet('chile-hub-data/data/normalized/censo_comunal.parquet') cc
     USING (codigo_comuna)
   ORDER BY cc.poblacion_censada DESC
   LIMIT 10"
)

dbDisconnect(con, shutdown = TRUE)
```

> **Nota:** las rutas locales no requieren la extensión `httpfs`. Si prefieres
> consultar los Parquet **remotos** directamente (sin descargar el bundle),
> ejecuta primero `dbExecute(con, "INSTALL httpfs; LOAD httpfs;")` y usa las
> URLs de la Opción B.

## Notas importantes

- **`codigo_comuna` es un string de 5 caracteres** con cero inicial
  (p. ej. `"01101"` para Iquique). Al leer con `arrow::read_parquet()`, la
  columna llega como `character` — nunca como número. Si haces joins con datos
  propios, asegúrate de que tu columna también sea `character` con
  `sprintf("%05d", tu_columna)` o equivalente.
- Consulta los schemas en el [repositorio de datasets](https://github.com/cortega26/chile-hub/tree/main/docs/datasets) para conocer los
  campos disponibles en cada dataset.
- Para el ecosistema Python, ver [`docs/installation.md`](installation.md).
