# ME7: Nuevas capacidades de API

**Estado:** Pendiente
**Impacto:** Medio
**Esfuerzo:** M
**Riesgo:** Bajo
**Target:** Cuando se active la capa premium de API
**Dependencias:** ME6 (necesita `ChileHubDatasetError`)

## Resumen

Cuatro adiciones a la API pública:

1. `cross_view()` — vista pre-joined por CUT para evitar joins manuales repetitivos
2. `validate_user_data()` — validación de datos externos contra JSON Schemas del hub
3. `--exit-code` en CLI — para que `health`, `status`, `check-sources` fallen pipelines CI
4. `search_datasets()` — búsqueda programática con filtros por keyword, fuente, categoría

## Plan completo

→ [`plans/017-new-api-capabilities.md`](../../plans/017-new-api-capabilities.md)

## ¿Por qué está en backlog?

Nuevas capacidades de API pública. Se implementarán cuando la capa API se active
como producto premium. Ninguna de estas capacidades es necesaria para el pipeline
de build ni para los extractores.
