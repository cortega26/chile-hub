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
- `hub_health.json`
- `hub_health.md`
- `hub_bundle.json`
- `redistribution_report.json`
- `redistribution_report.md`
- `provenance_report.json`
- `provenance_report.md`
- `dataset_catalog.json`
- `dataset_catalog.md`
- `artifact_manifest.json`
- `chile-hub-publishable-bundle.zip`
- `chile-hub-publishable-bundle.zip.sha256`

Además, los extractores dejan metadata intermedia en `data/staging` para dejar trazabilidad de:

- origen efectivo (`live` o `fallback`)
- timestamp de refresh
- cantidad de registros
- campos publicados

Política del repo:

- `data/staging` y binarios pesados locales no deberían versionarse
- artefactos publicables de `data/normalized` como catálogos, metadata, JSON, Parquet, el ZIP del bundle y su sidecar `.sha256` sí pueden publicarse para hacer visible el estado real del hub
- `artifact_manifest.json` publica hashes y tamaños para esos artefactos ligeros
- el ZIP publicable aparece como `package` dentro del manifest, no como `artifact`, para evitar autorreferencia circular
- el ZIP publica además un sidecar `*.sha256` para verificación directa fuera del repo

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
python -m src.chile_hub example indicadores --kind duckdb
python -m src.chile_hub artifacts comunas
python -m src.chile_hub shared-artifacts --shared-type hub_health --format json
python -m src.chile_hub report drift_report --format markdown
python -m src.chile_hub overview
python -m src.chile_hub inventory
python -m src.chile_hub health
python -m src.chile_hub bundle
python -m src.chile_hub packages
python -m src.chile_hub redistribution
python -m src.chile_hub provenance
python -m src.chile_hub drift
```

`summary` e `inventory` ahora exponen también `freshness_status`, `freshness_age_hours`, `coverage_status` y `coverage_ratio` por capa, para detectar builds envejecidos o con regresión de cobertura sin tener que abrir los JSON crudos.
También exponen `reuse_status`, `reuse_license` y si la capa requiere atribución.
También exponen `degradation_status` para distinguir una capa sana de una capa operativamente degradada.
Además incluyen `warning_count`, que sube automáticamente cuando una capa queda `stale`, `unknown` o entra en fallback con advertencias operativas.
`health` entrega una vista agregada del hub con `overall_status`, counts por severidad y breakdown por capa.
También agrega conteos de publicabilidad: cuántas capas están listas para redistribución y cuántas siguen en `review_terms`.
Y ahora agrega conteos de degradación operativa y cobertura parcial, para distinguir warnings genéricos de capas realmente degradadas o con regresión de cardinalidad.
`bundle` entrega un único índice machine-readable que consolida health, catálogo, reportes tipados y artefactos publicables por dataset.
`packages` expone los paquetes publicables del hub, incluido el ZIP listo para descarga.
`shared-artifacts` lista artefactos compartidos del hub usando `shared_type` y `format`, sin depender de nombres de archivo.
`report` resuelve metadata de un reporte compartido específico usando la misma semántica.
`overview` entrega una vista compacta del estado actual del hub: counts agregados, reportes publicados y estado breve por capa.
Esa misma vista también se publica como `overview.json` y `overview.md` dentro de `data/normalized/`.
`redistribution` entrega un inventario explícito de publicabilidad por capa con licencia, acción recomendada y cautelas de redistribución.
`provenance` entrega un inventario explícito de procedencia efectiva por capa, incluyendo fuente, modo, detalle y timestamp del último refresh.
`drift` entrega una vista explícita de drift operativo por capa, consolidando fallback, cobertura parcial, degradación y acción recomendada.
Además, cada dataset del catálogo y del bundle publica ahora una sección `degradation` con impacto y acción recomendada cuando la capa cae a fallback o warning operativo.
También publica `coverage`, con baseline esperado, ratio y resumen legible para detectar drift territorial o regresiones de cobertura en el último build.

### SQLite

```bash
sqlite3 data/normalized/chile_data.db
```

## Cómo correr el pipeline

Bootstrap recomendado:

```bash
make bootstrap
make doctor
```

`make bootstrap` también instala `Chromium` para que `make verify-landing` funcione desde el mismo entorno del proyecto.
Si ya tienes la `.venv` lista y solo quieres preparar browsers para la landing, usa `make install-browsers`.

Si prefieres hacerlo a mano:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

El `Makefile` usa `./.venv/bin/python` automáticamente cuando existe, así que desde ese punto la ruta más simple es:

```bash
make refresh
```

Eso ejecuta:

- extractores
- build de outputs
- verificación de artefactos
- smoke tests del helper
- smoke test de la landing en navegador

Si quieres correr pasos sueltos:

```bash
make extract
make build
make verify
make verify-landing
make test
```

O si prefieres comandos directos:

```bash
./.venv/bin/python src/extractors/subdere_extractor.py
./.venv/bin/python src/extractors/bcentral_extractor.py
./.venv/bin/python src/build_dev_db.py
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

Revisa la salud agregada del hub:

```bash
cat data/normalized/hub_health.json
```

O consume el entrypoint consolidado:

```bash
cat data/normalized/hub_bundle.json
```

O genera/redistribuye el paquete descargable:

```bash
make package-bundle
```

Ese manifest ahora incluye `dataset` y `output_type` para cada artefacto publicable derivado de una capa.
La landing reutiliza esa metadata para mostrar tipo de output y hash corto junto a los links de descarga.
La política de `freshness` también se convierte en warnings operativos dentro de `pipeline_metadata.json` y `dataset_catalog.json` cuando una capa queda envejecida o indeterminada.
Además se consolida en `hub_health.json` y `hub_health.md` como resumen agregado del estado del hub.
Ese resumen ahora incluye también señales de publicabilidad agregada como `publishable_count` y `review_terms_count`.
Además, `redistribution_report.json` y `redistribution_report.md` convierten esas señales en una vista accionable por dataset.
`provenance_report.json` y `provenance_report.md` hacen lo mismo para la procedencia efectiva del último build.
Para consumidores externos, `hub_bundle.json` funciona como punto único de entrada para descubrir estado, datasets, outputs, reportes y artefactos sin abrir varios archivos por separado.
La landing local ahora usa `hub_bundle.json` como fuente primaria para renderizar estado global y capas publicadas.
El contrato del hub publica además `reuse_policy` por dataset para distinguir capas abiertas con atribución de capas públicas cuyo régimen de redistribución todavía conviene revisar.

O usa el verificador local:

```bash
./.venv/bin/python scripts/verify_pipeline.py
```

Smoke tests del helper y contratos del catálogo:

```bash
./.venv/bin/python -m unittest discover -s tests
```

Secuencia mínima recomendada para validar el hub localmente:

```bash
make build
make verify
make test
make verify-landing
```

Atajos del proyecto:

```bash
make build
make verify
make test
make check
make status
make hub-list
make hub-example
make hub-artifacts
make hub-shared-artifacts
make hub-report
make hub-inventory
make hub-overview
make hub-health
make hub-bundle
make hub-redistribution
make hub-provenance
make hub-drift
make hub-packages
make package-bundle
```

Y para un resumen humano del último estado:

```bash
make status
```

Ese comando también genera `data/normalized/pipeline_status.md`.
La landing local en `index.html` consume `dataset_catalog.json` para reflejar el estado real de las capas publicadas.
También expone links directos a documentación y artefactos `JSON`/`Parquet` por dataset usando `dataset_catalog.json` y `artifact_manifest.json`.
Además deja accesos rápidos a `pipeline_status.md`, `hub_health.json`, `hub_health.md`, `dataset_catalog.json`, `dataset_catalog.md` y `artifact_manifest.json`, junto con la URL fuente de cada capa.
También expone `hub_bundle.json` como punto de entrada único para consumo automatizado.
También expone `redistribution_report.json` y `redistribution_report.md` como vista directa de publicabilidad por capa.
También expone `provenance_report.json` y `provenance_report.md` como vista directa de procedencia efectiva por capa.
También expone `overview.json` y `overview.md` como snapshot compacto del estado actual del hub.
Y muestra el `Bundle ZIP` como descarga directa del paquete publicable.
Además dedica un bloque visible al paquete descargable, con tamaño y hash abreviado del ZIP del último build.
Ese mismo bloque incluye una receta copiables para verificar la integridad del ZIP con `shasum -a 256`.
También muestra `freshness`, `coverage` y `degradation` por dataset, además de conteos agregados de capas `stale`, `degraded` y con cobertura parcial para detectar drifting del hub.
También muestra metadata de reuso por capa, incluyendo licencia o cautela de redistribución y si requiere atribución.
Y el banner superior resume cuántas capas siguen en `review_terms`.
También incluye recetas breves de consumo para `Python`, `DuckDB` y la `CLI` local del proyecto.
Esas recetas en la landing son copiables directamente desde la interfaz.
Cada dataset card además muestra ejemplos específicos por capa para `python`, `duckdb` y `cli`, tomados desde el catálogo generado.
Esos ejemplos por dataset también son copiables y responden al tab activo en cada card.
La landing también se puede smoke-testear en navegador con `make verify-landing`.
Ese smoke test cubre estado, quick-start, metadata de artefactos, recetas por dataset y flujos de copia.
También cubre la presencia de `freshness`, `coverage` y `degradation` en la superficie visible de la landing.
El workflow `pipeline-check` ejecuta esa verificación de landing además del build, verify y smoke tests del helper.
El workflow de CI publica un artifact `chile-hub-publishable-bundle` con los outputs ligeros, `hub_health`, `hub_bundle`, `redistribution_report`, `provenance_report`, `drift_report`, el ZIP publicable y su `SHA256`, además del manifest asociado.
Ahora ese artifact también incluye `overview.json` y `overview.md`.
El `GITHUB_STEP_SUMMARY` también incluye ahora `overview.md` junto a las vistas agregadas de redistribución, procedencia y drift, además del estado técnico del hub.

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
