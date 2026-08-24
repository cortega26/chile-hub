# ADR-019: Gates de equivalencia y elegibilidad de releases reproducibles

**Fecha:** 2026-08-23
**Estado:** accepted
**Decisión:** Las migraciones internas se promueven mediante equivalencia
conductual y de artefactos explícitamente caracterizada, no mediante una meta de
cobertura. Una release que pretenda ser reproducible solo puede promoverse si
todos sus datasets y artefactos públicos resuelven la procedencia requerida de
snapshots durables conforme a una política de archivo aceptada.

## Contexto

El pipeline tiene garantías públicas que no se reducen a líneas ejecutadas:
validación fail-closed (ADR-001), carriles de publicación (ADR-004), contratos,
paths, bundle, checksums, caché y URLs `latest`. La hoja de ruta congelada
requiere reemplazar partes internas sin cambiar esas garantías.

Las releases inmutables de Phases 8–9 dependerán de snapshots durables creados
en Phase 7. Declarar una release reproducible antes de poder resolver sus
materiales fuente sería una afirmación falsa, incluso si los artefactos finales
pasaran verificación de checksum.

## Decisión

### Promoción por equivalencia

Una sustitución se promueve solo cuando una matriz conductual revisada y sus
gates objetivos prueban, para entradas fijas, que conserva:

- resultados de validación y fallas relevantes;
- membresía, paths, schemas y checksums de artefactos públicos, salvo metadatos
  volátiles permitidos explícitamente;
- reportes y decisiones de elegibilidad de publicación;
- comportamiento público de API/CLI y errores documentados que toque el cambio.

La cobertura de línea o rama se medirá como diagnóstico para detectar escenarios
no ejercitados. No es un umbral de promoción ni sustituye la equivalencia.

### Elegibilidad de snapshots durables

Antes de que una shadow release pueda satisfacer los gates para convertirse en
el modelo de publicación de producción, **cada dataset y artefacto incluido en
esa release pública** debe resolver a la procedencia de snapshot fuente durable
requerida por la política de archivo aceptada. La referencia y el hash deben ser
verificables; no basta un nombre local o un timestamp no resoluble.

Una release nunca debe afirmar reproducibilidad si el material fuente necesario
no puede resolverse durablemente. Si una fuente no puede archivarse por razones
legales o técnicas, Phase 7 debe definir y documentar una excepción explícita,
su evidencia, y la regla de elegibilidad resultante. La ausencia de una política
no es una excepción y bloquea la promoción de esa release.

Esto hace obligatorio el orden Phase 7 → Phase 8 → Phase 9: snapshots durables,
manifiestos shadow, y solo después publicación atómica como modelo de producción.

## Consecuencias

- Phase 1 debe caracterizar comportamientos, clasificar cada aserción como
  garantía o detalle interno, y mantener una allowlist mínima para volatilidad.
- Phase 7 debe resolver proveedor, retención, legalidad, credenciales y manejo
  de fallos antes de que una release pueda volverse elegible.
- Phases 8–9 no pueden usar el manifiesto como una afirmación de reproducibilidad
  sin vínculos verificables hacia snapshots durables.

## Diferido expresamente

Este ADR no determina campos finales de `ExtractionResult` (Phase 4), proveedor
ni retención de archivo (Phase 7), formato/ID/firma de manifiesto o rollback
(Phases 8–9), ni rediseño del cliente/caché (Phase 10).
