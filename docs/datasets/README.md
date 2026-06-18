# Catálogo de datasets

Este catálogo describe las capas de datos publicadas hoy por `chile-hub`.

Cada ficha busca responder cinco preguntas rápido:

1. qué contiene la capa
2. de dónde viene
3. qué tan confiable y automatizable es
4. cómo se cruza con otros datos
5. qué advertencias debes conocer antes de usarla

Las propuestas de nuevas capas se evalúan con los criterios públicos de
[`docs/dataset-inclusion-criteria.md`](../dataset-inclusion-criteria.md).

## Capas actuales

- [regiones](./regiones.md)
- [provincias](./provincias.md)
- [comunas](./comunas.md)
- [comunas_enriquecidas](./comunas_enriquecidas.md)
- [indicadores](./indicadores.md)
- [censo_comunal](./censo_comunal.md)
- [censo_hogares_viviendas](./censo_hogares_viviendas.md)
- [establecimientos_salud](./establecimientos_salud.md)
- [distritos_electorales](./distritos_electorales.md)
- [establecimientos_educacionales](./establecimientos_educacionales.md)
- [finanzas_municipales](./finanzas_municipales.md)
- [resultados_educacionales](./resultados_educacionales.md)
- [indicadores_urbanos_siedu](./indicadores_urbanos_siedu.md)
- [perfil_territorial_comunal](./perfil_territorial_comunal.md)
- [empresas](./empresas.md)
- [status_changelog](./status_changelog.md)

## Convenciones de confianza

- `Tier A`: altamente automatizable. Fuente estable, estructurada y con bajo costo de mantenimiento.
- `Tier B`: semi-automatizable. Requiere vigilancia por drift, ajustes manuales o validaciones más fuertes.
- `Tier C`: experimental o manual. No apto para MVP como capa crítica.

## Qué debería tener toda nueva capa

- propósito claro
- fuente y método de acceso
- frecuencia esperada
- notas legales
- esquema
- reglas de normalización
- campos de join sugeridos
- advertencias
- nivel de confianza
