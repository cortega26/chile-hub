# 🇨🇱 chile-hub

[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![License](https://img.shields.io/badge/license-CC--BY--4.0-blue.svg)]()

Capas de datos chilenas curadas, normalizadas y fáciles de consumir, a partir de fuentes abiertas o legalmente reutilizables.

`chile-hub` no busca "tener todos los datos de Chile". Busca reducir el costo de encontrar, limpiar, entender, cruzar y consumir datasets confiables de Chile.

## Qué problema resuelve

Trabajar con datos chilenos casi siempre parte igual:

- enlaces rotos o poco mantenidos
- Excels deformes
- códigos territoriales inconsistentes
- nombres difíciles de cruzar
- documentación insuficiente
- scrapers frágiles para obtener datos básicos

El valor del proyecto está en transformar esas fuentes en capas listas para usar con:

- esquema estable
- trazabilidad de origen
- outputs útiles para análisis y software
- ejemplos de consumo simples

## Qué es y qué no es

### Sí es

- un hub de capas de datos reutilizables de Chile
- un pipeline de extracción, normalización y empaquetado
- un catálogo técnico con foco en confianza y consumo inmediato

### No es

- un reemplazo de las fuentes oficiales
- un catálogo infinito de links
- una promesa de cobertura universal desde el día uno
- una API compleja como requisito del MVP

## Estado actual

El repo hoy parte con un MVP acotado:

- capas territoriales derivadas: regiones, provincias y comunas
- capa territorial base: regiones, provincias y comunas
- indicadores económicos diarios de alta reutilización

Eso no define el límite del producto. Define el punto de partida.

La visión de largo plazo es incorporar nuevas capas de datos solo cuando cumplan criterios razonables de:

- utilidad transversal
- calidad de fuente
- claridad legal
- factibilidad de automatización
- bajo costo de mantenimiento

## Capas incluidas hoy

### 1. `regiones`

Capa territorial derivada para filtros, agregaciones y joins de alto nivel.

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `codigo_region` | `VARCHAR` | Código CUT de la región (2 chars) | `"01"` |
| `nombre_region` | `VARCHAR` | Nombre oficial de la región | `"Tarapacá"` |

### 2. `provincias`

Capa territorial derivada para cruces intermedios entre región y comuna.

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `codigo_region` | `VARCHAR` | Código CUT de la región (2 chars) | `"01"` |
| `nombre_region` | `VARCHAR` | Nombre oficial de la región | `"Tarapacá"` |
| `codigo_provincia` | `VARCHAR` | Código CUT de la provincia (3 chars) | `"011"` |
| `nombre_provincia` | `VARCHAR` | Nombre oficial de la provincia | `"Iquique"` |

### 3. `comunas`

Base territorial normalizada con códigos CUT y campos preparados para cruces.

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `codigo_comuna` | `VARCHAR` | Código CUT de la comuna (5 chars) | `"01101"` |
| `nombre_comuna` | `VARCHAR` | Nombre oficial normalizado con acentos | `"Iquique"` |
| `nombre_comuna_clean` | `VARCHAR` | Nombre en minúsculas y sin acentos | `"iquique"` |
| `codigo_provincia` | `VARCHAR` | Código CUT de la provincia (3 chars) | `"011"` |
| `nombre_provincia` | `VARCHAR` | Nombre oficial de la provincia | `"Iquique"` |
| `codigo_region` | `VARCHAR` | Código CUT de la región (2 chars) | `"01"` |
| `nombre_region` | `VARCHAR` | Nombre oficial de la región | `"Tarapacá"` |
| `latitud_cabecera` | `DOUBLE` | Latitud de la capital comunal | `-20.2138` |
| `longitud_cabecera` | `DOUBLE` | Longitud de la capital comunal | `-70.1508` |
| `poblacion_estimada` | `INTEGER` | Proyección o referencia poblacional | `223400` |

### 4. `indicadores`

Serie de indicadores económicos diarios de referencia.

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `fecha` | `DATE` | Fecha de aplicación (YYYY-MM-DD) | `2026-05-30` |
| `codigo_indicador` | `VARCHAR` | Identificador corto (`uf`, `dolar`, `utm`, `euro`) | `"uf"` |
| `valor` | `DOUBLE` | Valor del indicador | `39420.50` |

## Outputs disponibles

El pipeline actual genera entregables locales en [`data/normalized`](/home/carlos/VS_Code_Projects/chile-hub/data/normalized):

- `chile_data.duckdb`
- `chile_data.db`
- `chile_data_latest.xlsx`
- `regiones.parquet`
- `provincias.parquet`
- `comunas.parquet`
- `indicadores.parquet`
- `regiones.json`
- `provincias.json`
- `comunas.json`
- `indicadores_hoy.json`
- `pipeline_metadata.json`
- `pipeline_status.md`
- `dataset_catalog.json`
- `dataset_catalog.md`
- `artifact_manifest.json`

Además, los extractores dejan metadata intermedia en `data/staging` para dejar trazabilidad de:

- origen efectivo (`live` o `fallback`)
- timestamp de refresh
- cantidad de registros
- campos publicados

Política del repo:

- `data/staging` y binarios pesados locales no deberían versionarse
- artefactos livianos de `data/normalized` como catálogos, metadata, JSON y Parquet sí pueden publicarse para hacer visible el estado real del hub
- `artifact_manifest.json` publica hashes y tamaños para esos artefactos ligeros

## Uso rápido

### DuckDB

```sql
SELECT *
FROM 'data/normalized/regiones.parquet';

SELECT *
FROM 'data/normalized/provincias.parquet';

SELECT *
FROM 'data/normalized/comunas.parquet';

SELECT *
FROM 'data/normalized/indicadores.parquet'
ORDER BY fecha DESC, codigo_indicador;
```

### Python con Polars

```python
import polars as pl

df_comunas = pl.read_parquet("data/normalized/comunas.parquet")
df_indicadores = pl.read_parquet("data/normalized/indicadores.parquet")
```

### Python helper del hub

```python
from src.chile_hub import ChileHub

hub = ChileHub()
print(hub.list_datasets())
df_comunas = hub.load_polars("comunas")
```

### CLI mínima del hub

```bash
python -m src.chile_hub list
python -m src.chile_hub show comunas
python -m src.chile_hub path comunas --output parquet
```

### SQLite

```bash
sqlite3 data/normalized/chile_data.db
```

## Cómo correr el pipeline

Instala dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta extractores:

```bash
python src/extractors/subdere_extractor.py
python src/extractors/bcentral_extractor.py
```

Compila los outputs:

```bash
python src/build_dev_db.py
```

Revisa metadata y validaciones:

```bash
cat data/normalized/pipeline_metadata.json
```

Explora el catálogo machine-readable:

```bash
cat data/normalized/dataset_catalog.json
```

Revisa el manifest de artefactos publicables:

```bash
cat data/normalized/artifact_manifest.json
```

O usa el verificador local:

```bash
python scripts/verify_pipeline.py
```

Smoke tests del helper y contratos del catálogo:

```bash
python -m unittest discover -s tests
```

Secuencia mínima recomendada para validar el hub localmente:

```bash
python src/build_dev_db.py
python scripts/verify_pipeline.py
python -m unittest discover -s tests
```

Atajos del proyecto:

```bash
make build
make verify
make test
make check
make status
make hub-list
```

Y para un resumen humano del último estado:

```bash
python scripts/pipeline_status.py
```

Ese comando también genera `data/normalized/pipeline_status.md`.
La landing local en `index.html` consume `dataset_catalog.json` para reflejar el estado real de las capas publicadas.
El workflow de CI publica un artifact `chile-hub-publishable-bundle` con los outputs ligeros y el manifest asociado.

## Criterio para crecer

Una nueva capa de datos no debería entrar solo porque "suena útil". Debería justificar:

1. dolor recurrente de usuario
2. valor de cruce con otras capas
3. fuente confiable y accesible
4. licencia clara o reutilización defendible
5. costo de mantenimiento razonable

La visión y criterios de producto están documentados en [docs/product-spec.md](/home/carlos/VS_Code_Projects/chile-hub/docs/product-spec.md).
El catálogo de capas actualmente disponibles está en [docs/datasets/README.md](/home/carlos/VS_Code_Projects/chile-hub/docs/datasets/README.md).

## Fuentes actuales

- BCN ArcGIS para la capa territorial operativa actual, con fallback secundario a SUBDERE
- mindicador.cl como fuente pública de indicadores en esta fase

## Licencia y atribución

Este repo empaqueta transformaciones y datasets derivados de fuentes públicas o reutilizables. La redistribución de cada capa debe evaluarse según su fuente y condiciones específicas.

El código y la estructura del proyecto se distribuyen bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es). Si reutilizas outputs o transformaciones, atribuye también las fuentes originales cuando corresponda.

## Próximo foco

El próximo objetivo razonable no es abrir el scope sin control, sino convertir este repo en un catálogo confiable de capas de datos chilenas, empezando por pocas capas muy útiles y mantenibles.
