# comunas

## Resumen

Base territorial normalizada para cruces por región, provincia y comuna.

Es una capa base transversal: ayuda a limpiar nombres, preservar códigos CUT con ceros a la izquierda y dar una llave consistente para software, análisis y datasets futuros.

## Estado

- `status`: activo en MVP
- `confidence`: Tier B
- `primary_join_key`: `codigo_comuna`
- `update_mode`: semi-automatizado

## Fuente

- capa comunal servida vía BCN ArcGIS como fuente operativa actual
- referencia territorial administrativa de SUBDERE como fallback secundario
- procesamiento local desde [`src/extractors/subdere_extractor.py`](/home/carlos/VS_Code_Projects/chile-hub/src/extractors/subdere_extractor.py:1)

## Método de acceso actual

- consulta HTTP a un `FeatureServer` de BCN con región, provincia, comuna y código comunal
- suplementación local explícita para la comuna `Antártica (12202)` si la fuente no la trae
- fallback a SUBDERE si falla la fuente BCN
- fallback local embebido como última barrera

## Por qué existe esta capa

Problemas que resuelve:

- nombres de comunas escritos de forma inconsistente
- pérdida de ceros iniciales en códigos CUT
- falta de una llave territorial estable para cruces
- necesidad de búsquedas insensibles a acentos

## Outputs

- `data/normalized/comunas.parquet`
- `data/normalized/comunas.json`
- `data/staging/comunas.metadata.json`
- tabla `comunas` en `data/normalized/chile_data.duckdb`
- tabla `comunas` en `data/normalized/chile_data.db`
- hoja `Comunas y Regiones` en `data/normalized/chile_data_latest.xlsx`

## Schema actual

Fuente observada: `data/normalized/chile_data.duckdb`

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `codigo_region` | `VARCHAR` | Código CUT de región, preservando ceros |
| `nombre_region` | `VARCHAR` | Nombre oficial de región |
| `abreviatura` | `VARCHAR` | Abreviatura corta |
| `codigo_provincia` | `VARCHAR` | Código CUT de provincia |
| `nombre_provincia` | `VARCHAR` | Nombre oficial de provincia |
| `codigo_comuna` | `VARCHAR` | Código CUT de comuna |
| `nombre_comuna` | `VARCHAR` | Nombre oficial de comuna |
| `nombre_comuna_clean` | `VARCHAR` | Nombre normalizado sin acentos para búsqueda |
| `latitud_cabecera` | `DOUBLE` | Latitud de cabecera comunal |
| `longitud_cabecera` | `DOUBLE` | Longitud de cabecera comunal |
| `poblacion_estimada` | `BIGINT` | Referencia poblacional |

## Normalizaciones aplicadas

- padding de códigos a 2, 3 y 5 caracteres
- creación de `nombre_comuna_clean` en minúsculas y sin vocales acentuadas
- selección de columnas canónicas en orden consistente

## Join value

Campos recomendados para cruce:

- `codigo_comuna`: mejor llave para unir datasets locales o futuros
- `codigo_region`: útil para agregaciones
- `nombre_comuna_clean`: apoyo para matching cuando el dato externo está sucio

## Caveats

- la fuente BCN actual entrega una fila `Zona sin demarcar` sin códigos y omite `Antártica (12202)`, por lo que el extractor aplica un pequeño parche defensivo
- SUBDERE sigue disponible solo como fallback secundario y su URL conocida hoy es inestable
- el extractor tiene fallback embebido para proteger el pipeline, pero eso implica cobertura limitada si fallan las fuentes remotas
- los campos geográficos y poblacionales del fallback no deben interpretarse como una base nacional completa
- la lógica de normalización de acentos cubre casos comunes, no todos los edge cases lingüísticos
- el modo efectivo del último refresh queda registrado en `data/staging/comunas.metadata.json` y consolidado en `data/normalized/pipeline_metadata.json`

## Notas legales

- tratar como derivado de una fuente pública administrativa
- antes de redistribuir masivamente, conviene documentar con más precisión la licencia exacta de la fuente operativa final

## Recomendación de evolución

Esta capa debería seguir en MVP, pero necesita:

1. validación de cobertura esperada contra un total oficial de comunas
2. reducir o eliminar el parche manual para `Antártica (12202)` con una fuente territorial más completa
3. tests de schema y unicidad de `codigo_comuna`
