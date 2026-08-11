# Distritos Electorales

Mapeo comunal oficial de la asociación de comunas de Chile con sus respectivos distritos electorales para la Cámara de Diputadas y Diputados, y circunscripciones senatoriales para el Senado.

## Fuente y licencia

- Fuente: Biblioteca del Congreso Nacional (BCN) / Ley Orgánica Constitucional sobre Votaciones Populares y Escrutinios (Ley N° 20.840).
- Formato de origen: Mapeo de ley estática local.
- Licencia: CC0 / Dominio Público (redistribución libre sin restricciones).
- Actualización esperada: Estable (estática, solo se actualiza ante reformas electorales del Estado de Chile).

## Claves y esquema

La clave primaria es `codigo_comuna` (`str`, cinco caracteres).

| Columna | Tipo | Descripción | Ejemplo |
|:---|:---|:---|:---|
| `codigo_comuna` | `VARCHAR` / `str` | Código CUT de la comuna (5 caracteres) | `"13114"` |
| `nombre_comuna` | `VARCHAR` / `str` | Nombre oficial de la comuna | `"Las Condes"` |
| `distrito_electoral` | `VARCHAR` / `str` | Identificador o número de distrito electoral de diputados | `"11"` |
| `circunscripcion_senatorial` | `VARCHAR` / `str` | Identificador o número de circunscripción senatorial de senadores | `"7"` |

## Uso

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("distritos_electorales")
```

```sql
SELECT nombre_comuna, distrito_electoral, circunscripcion_senatorial
FROM 'data/normalized/distritos_electorales.parquet'
ORDER BY codigo_comuna;
```

## Limitaciones

Este mapeo representa la división político-electoral estipulada por la legislación chilena vigente. No incluye locales de votación ni padrón electoral, únicamente la definición geográfica-jurisdiccional de los distritos y circunscripciones.

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/distritos_electorales.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` | Sí | PK |
| `nombre_comuna` | `VARCHAR` | `"Las Condes"` | Sí | — |
| `distrito_electoral` | `VARCHAR` | `"10"` | Sí | — |
| `circunscripcion_senatorial` | `VARCHAR` | `"3"` | Sí | — |

<!-- END_DATASET_SCHEMA -->
