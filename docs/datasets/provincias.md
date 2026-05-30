# provincias

## Resumen

Capa territorial derivada para cruces intermedios entre región y comuna.

Ayuda a cubrir un nivel administrativo que suele faltar en muchos datasets de Chile, pero que sigue siendo útil para agregaciones y navegación territorial.

## Estado

- `status`: activo en MVP
- `confidence`: Tier B
- `primary_join_key`: `codigo_provincia` + `codigo_region`
- `update_mode`: derivado automáticamente desde `comunas`

## Fuente

- derivado localmente a partir de la capa `comunas`
- lógica de derivación en [`src/build_dev_db.py`](/home/carlos/VS_Code_Projects/chile-hub/src/build_dev_db.py:1)
- hereda trazabilidad y modo efectivo de refresh desde [`src/extractors/subdere_extractor.py`](/home/carlos/VS_Code_Projects/chile-hub/src/extractors/subdere_extractor.py:1)

## Método de acceso actual

- selección de `codigo_region`, `nombre_region`, `codigo_provincia` y `nombre_provincia`
- `unique()` para deduplicar
- ordenamiento por `codigo_region` y `codigo_provincia`

## Por qué existe esta capa

Problemas que resuelve:

- datasets que reportan a nivel provincia, no comuna
- necesidad de un join administrativo intermedio
- reducción de trabajo repetido para derivar provincias desde comunas

## Outputs

- `data/normalized/provincias.parquet`
- `data/normalized/provincias.json`
- metadata consolidada en `data/normalized/pipeline_metadata.json`
- tabla `provincias` en `data/normalized/chile_data.duckdb`
- tabla `provincias` en `data/normalized/chile_data.db`
- hoja `Provincias` en `data/normalized/chile_data_latest.xlsx`

## Schema actual

Fuente observada: `data/normalized/chile_data.duckdb`

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `codigo_region` | `VARCHAR` | Código CUT de región |
| `nombre_region` | `VARCHAR` | Nombre oficial de región |
| `codigo_provincia` | `VARCHAR` | Código CUT de provincia |
| `nombre_provincia` | `VARCHAR` | Nombre oficial de provincia |

## Normalizaciones aplicadas

- preservación de ceros a la izquierda en códigos CUT
- deduplicación derivada desde comunas
- orden estable por región y provincia

## Join value

Cruces sugeridos:

- `codigo_provincia` + `codigo_region` para máxima seguridad
- `codigo_provincia` en fuentes que ya usen CUT provincial consistente

## Caveats

- no es una fuente primaria independiente; depende de la calidad y cobertura de `comunas`
- la unicidad se valida sobre `codigo_region` + `codigo_provincia`, no solo sobre `codigo_provincia`
- hereda el `source_mode` y las notas operativas de la capa comunal

## Notas legales

- al ser una capa derivada, su redistribución depende de la política aplicable a la capa comunal de origen

## Recomendación de evolución

Esta capa puede seguir en MVP, pero conviene:

1. reforzar tests de unicidad sobre `codigo_region` + `codigo_provincia`
2. documentar casos de uso concretos con datasets provinciales futuros
