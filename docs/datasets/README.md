# Dataset catalog

Este catálogo describe las capas de datos publicadas hoy por `chile-hub`.

Cada ficha busca responder cinco preguntas rápido:

1. qué contiene la capa
2. de dónde viene
3. qué tan confiable y automatizable es
4. cómo se cruza con otros datos
5. qué caveats debes conocer antes de usarla

## Capas actuales

- [regiones](./regiones.md)
- [provincias](./provincias.md)
- [comunas](./comunas.md)
- [indicadores](./indicadores.md)

## Convenciones de confianza

- `Tier A`: altamente automatizable. Fuente estable, estructurada y con bajo costo de mantenimiento.
- `Tier B`: semi-automatizable. Requiere vigilancia por drift, ajustes manuales o validaciones más fuertes.
- `Tier C`: experimental o manual. No apto para MVP como capa crítica.

## Qué debería tener toda nueva capa

- propósito claro
- fuente y método de acceso
- frecuencia esperada
- notas legales
- schema
- reglas de normalización
- campos de join sugeridos
- caveats
- nivel de confianza
