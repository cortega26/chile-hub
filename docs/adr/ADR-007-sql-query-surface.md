# ADR-007: Superficie de consulta SQL con DuckDB sobre Parquet

**Fecha:** 2026-07-09
**Estado:** accepted
**Decision:** Se agrega un metodo `ChileHub.sql(query)` que registra cada dataset
como vista DuckDB respaldada por Parquet y ejecuta consultas SQL arbitrarias,
con duckdb como dependencia opcional bajo el extra `query`.

## Contexto

El repositorio ya trata el acceso SQL a los datos publicados como un modo de
consumo de primera clase:

- `duckdb` es dependencia del pipeline (`pipeline` extra).
- `build_duckdb` genera `chile_data.duckdb`.
- `README.md` tiene una seccion "Consultas SQL con DuckDB".
- Cada dataset en `dataset_catalog.json` incluye un recipe DuckDB copiable.
- `chile-hub example <capa> --kind duckdb` muestra ejemplos DuckDB.

Sin embargo, la API de Python solo expone `load_polars()` y `cross_view()`.
No existe un metodo `sql`/`query` que permita al usuario ejecutar SQL
directamente contra los datasets publicados. El usuario debe escribir su
propio boilerplate para conectar DuckDB, registrar las vistas y ejecutar la
consulta.

## Decision

1. **API shape**: `ChileHub.sql(query: str) -> pl.DataFrame`. Cada dataset
   del catalogo se registra como una vista DuckDB con el mismo nombre del
   dataset. Las vistas se respaldan con Parquet via `read_parquet()` y se
   registran de forma lazy en la primera llamada a `sql()`.

2. **Backing store**: Las vistas consultan los archivos Parquet, no el
   archivo `.duckdb` empaquetado. El `.duckdb` de ~70 MB no esta en el
   bundle pip — solo se distribuye Parquet.

3. **Dependencia**: Se agrega el extra opcional `query = ["duckdb>=1.5.4"]`
   en `pyproject.toml`. La importacion de `duckdb` es perezosa dentro de
   `sql()` con un mensaje de error claro si no esta instalado.

4. **Registro lazy**: Las vistas se registran una sola vez en la primera
   llamada a `sql()`, no en `__init__`. Esto evita overhead en la
   construccion de `ChileHub` y permite que instancias que nunca usan SQL
   no paguen el costo de conectar DuckDB.

5. **Manejo de errores**: Si el Parquet de un dataset no esta disponible
   (por ejemplo, datasets candidate que no se distribuyen en el bundle),
   ese dataset se omite silenciosamente y no se registra como vista.

## Consecuencias

- Positivas: Los usuarios pueden ejecutar SQL arbitrario multi-dataset con
  una sola llamada. Los recipes DuckDB en `dataset_catalog.json` se vuelven
  ejecutables como `hub.sql(...)`. `cross_view` podria eventualmente
  convertirse en azucar sobre `sql()`.

- Negativas: DuckDB no esta en las dependencias runtime base — el usuario
  debe instalar `chile-hub[query]` explicitamente. La conexion DuckDB es
  en memoria y vive mientras exista la instancia `ChileHub`; en queries
  muy grandes podria haber presion de memoria.

## Alternativas consideradas

- **Usar el archivo `.duckdb` empaquetado como backend** — Se descarto
  porque el `.duckdb` no se distribuye en el bundle pip. Solo Parquet esta
  disponible en la instalacion base.

- **Incluir `duckdb` en las dependencias runtime** — Se descarto por
  consistencia con el Plan 032 (separar dependencias del pipeline de las
  de consumo). La mayoria de los usuarios solo usa `load_polars()` y no
  necesita DuckDB.

- **CLI `chile-hub query`** — Se difiere para un futuro PR. El valor del
  CLI es menor que el de la API de Python, y el CLI ya cubre los casos de
  uso principales (list, show, cross, export, validate). Se reconsiderara
  si hay demanda.

- **Registrar vistas en `__init__`** — Se descarto para mantener
  `ChileHub()` rapido y evitar efectos secundarios en la construccion.
  La mayoria de las instancias nunca ejecutan SQL.
