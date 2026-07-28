# Indicadores Urbanos SIEDU

## Descripción

Indicadores urbanos del Sistema de Indicadores y Estándares de Desarrollo Urbano en formato largo. La cobertura parcial es esperada: SIEDU no cubre necesariamente las 346 comunas.

## Fuente y licencia

- Fuente: INE - Sistema de Indicadores y Estándares de Desarrollo Urbano
- URL: https://www.ine.gob.cl/herramientas/portal-de-mapas/siedu
- Licencia: Licencia de Datos Abiertos INE

## Esquema

| Campo | Tipo | Descripción |
|---|---|---|
| `anio` | integer | Año del indicador. |
| `codigo_comuna` | string | Código CUT comunal de 5 caracteres. |
| `codigo_indicador` | string | Identificador estable del indicador. |
| `nombre_indicador` | string | Nombre descriptivo. |
| `categoria` | string | Categoría temática. |
| `valor` | float | Valor del indicador. |
| `unidad` | string | Unidad de medida. |
| `fuente_original` | string | Fuente original declarada. |
| `cobertura_tipo` | string | Tipo de cobertura, normalmente urbana. |

## Uso

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("indicadores_urbanos_siedu")
```

```sql
SELECT codigo_comuna, codigo_indicador, valor
FROM 'data/normalized/indicadores_urbanos_siedu.parquet';
```

## Limitaciones

`coverage.status` se marca como parcial cuando corresponde. No debe interpretarse la ausencia de una comuna como valor cero.

## Registro de cambios

- v1: Dataset agregado con cobertura parcial explícita y validación de claves largas.

## Clasificación de salud (ADR-014)

La cobertura urbana es intencional: SIEDU mide sólo comunas urbanas. El contrato
lo declara con `coverage_policy: "partial_expected"` y el warning
"intentionally partial urban coverage" está registrado como *esperado*, así que
el dataset no cuenta como drift ni eleva la severidad del hub. El warning sigue
apareciendo íntegro en `warnings`.
