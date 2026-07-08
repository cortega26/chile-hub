# ME6: Robustecer manejo de errores en API pública

**Estado:** Completado (Plan 011 ejecutado, 2026-06-19)
**Impacto:** Medio
**Esfuerzo:** S
**Riesgo:** Bajo
**Target:** Cuando se active la capa premium de API

## Resumen

Tres bugs en la API pública (`core.py`, `data_manager.py`) que degradan la experiencia
del usuario y un bug de fuga de conexiones HTTP:

1. `load_polars()` expone tracebacks crudos de Polars/PyArrow
2. `_load_catalog()` crashea con `FileNotFoundError` sin mensaje amigable
3. `DataManager.clear()` destruye silenciosamente cualquier directorio
4. `check_sources()` reasigna `response` sin cerrar la anterior (fuga TCP)

## Plan completo

→ [`plans/011-harden-api-error-handling.md`](https://github.com/cortega26/chile-hub/blob/main/plans/011-harden-api-error-handling.md)

## ¿Por qué está en backlog?

La API pública se perfila como capa premium futura. El hardening de errores se
ejecutará cuando se active ese carril. Mientras tanto, los scripts internos
(`build_dev_db.py`, extractores, CLI básico) no se ven afectados por estos bugs.
