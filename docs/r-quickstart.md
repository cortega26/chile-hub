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
comunas <- read_parquet("chile-hub-data/comunas.parquet")
head(comunas)
```

Para verificar la integridad del ZIP descargado, compara su hash con el archivo
`chile-hub-publishable-bundle.zip.sha256` que se adjunta al mismo release
(usa el paquete `digest` o `openssl dgst -sha256` en terminal).

> **Nota:** la URL `releases/latest/download/` es estable entre versiones;
> apunta siempre al release publicado más reciente.

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

Conecta directamente al archivo DuckDB del bundle para hacer cruces SQL:

```r
library(duckdb)
con <- dbConnect(duckdb(), "chile-hub-data/chile_data.duckdb", read_only = TRUE)

dbGetQuery(con,
  "SELECT c.nombre_comuna, c.nombre_region, cc.poblacion_censada
   FROM comunas c
   JOIN censo_comunal cc USING (codigo_comuna)
   ORDER BY cc.poblacion_censada DESC
   LIMIT 10"
)

dbDisconnect(con, shutdown = TRUE)
```

## Notas importantes

- **`codigo_comuna` es un string de 5 caracteres** con cero inicial
  (p. ej. `"01101"` para Iquique). Al leer con `arrow::read_parquet()`, la
  columna llega como `character` — nunca como número. Si haces joins con datos
  propios, asegúrate de que tu columna también sea `character` con
  `sprintf("%05d", tu_columna)` o equivalente.
- Consulta los schemas en el [repositorio de datasets](https://github.com/cortega26/chile-hub/tree/main/docs/datasets) para conocer los
  campos disponibles en cada dataset.
- Para el ecosistema Python, ver [`docs/installation.md`](installation.md).
