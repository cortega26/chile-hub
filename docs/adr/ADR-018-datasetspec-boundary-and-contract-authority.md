# ADR-018: Límite de DatasetSpec y autoridad independiente de contratos

**Fecha:** 2026-08-23
**Estado:** accepted
**Decisión:** Como preparación para la migración incremental a `DatasetSpec`, se
establece un único límite de autoridad para los hechos de cada dataset.
`DatasetSpec` será el registro declarativo de política y operación del dataset;
los contratos JSON existentes seguirán siendo artefactos de esquema separados y
autoritativos. Ningún hecho se redactará independientemente en ambos.

## Contexto

El catálogo, el registro de fuentes, los contratos, la documentación y los
artefactos generados hoy contienen hechos relacionados sobre los datasets. La
migración aprobada en
[architecture-migration-roadmap.md](../architecture-migration-roadmap.md) busca
eliminar esa duplicación sin reemplazar de forma silenciosa los contratos que
ADR-005 ya estableció.

Una migración que pusiera campos y tipos en `DatasetSpec` mientras los mantuviera
editables en los contratos recrearía el problema con una forma distinta. A la
vez, trasladar el esquema completo al primer piloto ampliaría innecesariamente
el alcance y rompería el límite de ADR-005 entre reglas estructurales y
validación semántica Python.

## Decisión

### Autoridad de contratos JSON

Los contratos JSON Schema existentes son la autoridad separada para:

- campos/columnas;
- tipos;
- reglas de requerido y nulabilidad;
- restricciones estructurales de esquema; y
- requisitos de compatibilidad a nivel de esquema.

`DatasetSpec` referencia el contrato por una ruta y versión estables. No lo
embebe ni lo genera. Esta frontera solo puede cambiar mediante un ADR posterior
aprobado explícitamente.

### Autoridad de DatasetSpec

`DatasetSpec` será la autoridad para:

- identidad del dataset;
- tipo y ciclo de vida;
- carril de publicación y elegibilidad pública;
- política de fuente, reúso, fallback y frescura;
- carril de extracción;
- referencia al contrato;
- referencia al validador semántico;
- aliases;
- dependencias;
- outputs/artefactos declarados que se generen; y
- metadatos de documentación y otra política operacional de dataset.

La extracción específica de una fuente y la implementación de validación
semántica siguen siendo código Python.

### Regla de proyección

Ningún hecho de dataset puede ser redactado independientemente tanto en
`DatasetSpec` como en un contrato JSON Schema. Si por compatibilidad o
interoperabilidad se requiere que la misma información aparezca en el catálogo
legacy, registro de fuentes, documentación, inventario público, metadatos DCAT/
Frictionless u otra vista, se debe proyectar mecánicamente desde la fuente que
posee ese hecho. No se permiten dos representaciones editables de la misma
autoridad.

La migración conserva rutas y contratos existentes hasta que las proyecciones
se hayan comprobado por equivalencia; no convierte artefactos generados en
nuevas fuentes de verdad.

## Consecuencias

- El piloto de Phase 2 podrá demostrar adaptadores de compatibilidad sin
  duplicar campos, tipos o nulabilidad.
- Los lectores existentes de catálogo, registro y documentación podrán migrar
  gradualmente a vistas proyectadas.
- Las reglas de rango, referenciales, cohortes y anomalías siguen siendo
  validadores Python conforme a ADR-005.
- Autores futuros deben decidir la autoridad antes de añadir un nuevo campo;
  un guardrail de migración debe detectar duplicación no proyectada.

## Diferido expresamente

Este ADR no crea `DatasetSpec`, no decide su serialización ni versión concreta,
ni decide semántica final de `ExtractionResult`, almacenamiento durable,
mecánica de release, caché o descomposición del cliente.
