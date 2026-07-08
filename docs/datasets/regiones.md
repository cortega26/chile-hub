# regiones

## Resumen

Capa territorial derivada para filtros, agregaciones y joins administrativos de alto nivel.

Su valor está en ofrecer una llave regional mínima y estable, sin obligar a cada consumidor a derivarla por su cuenta desde la capa comunal.

## Estado

- `status`: activo en MVP
- `confidence`: Tier B
- `primary_join_key`: `codigo_region`
- `update_mode`: derivado automáticamente desde `comunas`

## Fuente

- derivado localmente a partir de la capa `comunas`
- lógica de derivación en [`src/build_dev_db.py`](https://github.com/cortega26/chile-hub/blob/main/src/build_dev_db.py)
- hereda trazabilidad y modo efectivo de refresh desde [`src/extractors/subdere_extractor.py`](https://github.com/cortega26/chile-hub/blob/main/src/extractors/subdere_extractor.py)

## Método de acceso actual

- selección de `codigo_region` y `nombre_region`
- `unique()` para deduplicar
- ordenamiento por `codigo_region`

## Por qué existe esta capa

Problemas que resuelve:

- necesidad de agregaciones rápidas por región
- evitar rederivar regiones manualmente desde comunas en cada proyecto
- exponer una capa territorial más simple para casos donde comuna es demasiado granular

## Salidas

- `data/normalized/regiones.parquet`
- `data/normalized/regiones.json`
- metadata consolidada en `data/normalized/pipeline_metadata.json`
- tabla `regiones` en `data/normalized/chile_data.duckdb`
- tabla `regiones` en `data/normalized/chile_data.db`
- hoja `Regiones` en `data/normalized/chile_data_latest.xlsx`

## Esquema actual

Fuente observada: `data/normalized/chile_data.duckdb`

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `codigo_region` | `VARCHAR` | Código CUT de región |
| `nombre_region` | `VARCHAR` | Nombre oficial de región |

## Normalizaciones aplicadas

- preservación de ceros a la izquierda en `codigo_region`
- deduplicación derivada desde comunas
- orden estable por código

## Join value

Cruces sugeridos:

- `codigo_region` para agregaciones, filtros y joins administrativos

## Advertencias

- no es una fuente primaria independiente; depende de la calidad y cobertura de `comunas`
- hereda el `source_mode` y las notas operativas de la capa comunal
- si cambia el modelo territorial de base, esta capa se recompone automáticamente y puede variar en orden o cardinalidad

## Notas legales

- al ser una capa derivada, hereda la lógica de reutilización con atribución de la capa comunal de origen

## Recomendación de evolución

Esta capa puede seguir en MVP sin mucha complejidad extra, pero conviene:

1. fijar un conteo esperado mínimo de regiones en tests y validaciones
2. documentar explícitamente cambios administrativos si alguna fuente futura altera nombres oficiales
