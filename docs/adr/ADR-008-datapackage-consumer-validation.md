# ADR-008: Validacion consumer del datapackage.json con Frictionless

**Fecha:** 2026-07-10
**Estado:** accepted
**Decision:** Se agregan dos metodos consumer en ChileHub -- `from_datapackage()` y
`frictionless_validate()` -- que usan el descriptor Frictionless publicado como
superficie de interoperabilidad, con `frictionless` como dependencia opcional bajo
el extra `validation`.

## Contexto

chile-hub construye y publica un descriptor Frictionless `datapackage.json` (via
`src/builders/data_package.py`) que se incluye en
`chile-hub-publishable-bundle.zip`. El descriptor describe los recursos Parquet,
sus schemas, tipos, claves primarias, fuentes y licencias -- siguiendo el estandar
Frictionless Data Package.

Sin embargo, la API de consumo de chile-hub (`ChileHub`) no exponia metodos para
interactuar con este descriptor:

1. **No habia forma de abrir un bundle externo** usando su `datapackage.json` como
   punto de entrada. Un usuario que descargara el bundle solo podia usar
   `ChileHub(data_dir=...)` si sabia exactamente donde estaban los archivos.
2. **No habia validacion contra el descriptor publicado**. El metodo existente
   `validate_dataset()` valida contra los contratos internos en
   `contracts/datasets/*.schema.json`, que son la fuente de verdad de diseno
   (ADR-005), pero no contra el descriptor Frictionless que se exporta como
   superficie de interoperabilidad.
3. **Asimetria**: chile-hub exporta un estandar de interoperabilidad pero no da a
   los consumidores una forma directa de consumir o validar contra el.

## Decision

1. **`ChileHub.from_datapackage(path_or_url)`**: Metodo de clase que abre un
   descriptor `datapackage.json` (local o remoto), resuelve `resources[].path`
   relativo al directorio del descriptor, y retorna un `ChileHub` configurado
   para usar ese directorio de datos.

2. **`ChileHub.frictionless_validate(dataset_name=None)`**: Valida el bundle local
   contra el descriptor `datapackage.json` usando
   `frictionless.Package.validate_descriptor()`. La validacion es solo de
   metadatos (rapida, no carga los datos completos). Si se pasa `dataset_name`,
   verifica que el dataset exista como recurso en el descriptor.

3. **Dependencia opcional**: `frictionless` se agrega al extra `validation` en
   `pyproject.toml` y se mantiene en `dev` para CI. La importacion de
   `frictionless` es perezosa dentro de cada metodo, con un mensaje de error
   claro si no esta instalado. Sigue el mismo patron que `sql()` con DuckDB
   (ADR-007).

4. **Lazy import**: Ambos metodos importan `frictionless` solo al ejecutarse, no
   al importar el modulo. Esto evita que usuarios que no necesitan Frictionless
   paguen el costo de importarlo.

## Consecuencias

- Positivas: Los consumidores pueden abrir cualquier bundle de chile-hub por su
  descriptor. Pueden validar que el descriptor local sea conforme al estandar
  Frictionless. La API es simetrica con la publicacion -- lo que se publica se
  puede validar y reabrir.
- Negativas: `frictionless` es una dependencia pesada (~30 MB instalada). Solo
  los usuarios que necesiten validacion Frictionless deben instalarla
  (`chile-hub[validation]`). La validacion es de metadatos solamente, no de
  datos completos (para eso existe `validate_dataset()`).

## Alternativas consideradas

- **Incluir `frictionless` en las dependencias runtime base** -- Se descarto
  para mantener la instalacion base liviana. La mayoria de los usuarios solo
  usa `load_polars()` y no necesita Frictionless.
- **Usar `frictionless.Package.validate()` en vez de
  `validate_descriptor()`** -- `validate()` carga y verifica los datos
  completos, lo cual es lento y redundante con `validate_dataset()`.
  `validate_descriptor()` es metadata-only y suficiente para la superficie
  de interoperabilidad.
- **Hacer `from_datapackage()` un constructor separado** -- Se opto por un
  `@classmethod` en `ChileHub` para mantener la API cohesiva. El patron es
  familiar para usuarios de Python (ej. `pandas.read_csv`, `polars.read_parquet`).
- **Usar el descriptor Frictionless como fuente de verdad unica (reemplazar
  ADR-005)** -- Se descarto. Los contratos internos `contracts/datasets/*.schema.json`
  son mas expresivos para necesidades internas (ancho fijo, cobertura esperada,
  politica de publicacion). El descriptor Frictionless es una proyeccion de esos
  contratos. Tener ambos es intencional.
