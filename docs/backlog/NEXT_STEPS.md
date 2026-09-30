# Próximos pasos — ChileHub

**Fecha:** 2026-06-29
**Estado:** 🎉 Backlog estratégico completado (7/7)

---

## Resumen

Todas las mejoras del backlog están implementadas y en producción:

| # | Mejora | Estado |
|:-:|:-------|:------:|
| 4 | Estabilización de fallbacks | ✅ |
| 1 | Refactor `build_dev_db.py` | ✅ |
| 6 | API error handling | ✅ |
| 2 | Contratos JSON Schema en runtime | ✅ |
| 3 | Constantes de datasets como `Dataset(StrEnum)` | ✅ |
| 5 | Dashboard público de salud | ✅ |
| 7 | API capacidades avanzadas | ✅ |

**490 tests pasan, 0 regresiones.**

---

## Direcciones futuras (no backlog)

### Corto plazo
- **Release 2.0.0** — el proyecto acumuló suficientes cambios como para
  justificar un salto de versión. Incluye refactor mayor (`build_dev_db.py`),
  nuevas APIs públicas y backlog completo.
- **Adopción y métricas** — monitorear descargas PyPI, abrir issues de
  feedback, medir qué datasets se usan realmente para priorizar mejoras.
- **Documentación de API con MkDocs** — **completada** (Plan 021 archivado); el
  sitio se publica en `/reference/`.

### Mediano plazo
- **Mejora continua de extractores** — monitorear fuentes upstream,
  actualizar si cambian sus APIs.
- **Perfil de rendimiento** — evaluar si el build completo sigue bajo
  los 45 min objetivo. Si no, considerar builds incrementales.
- **Pipeline Status Dashboard** — el dashboard de salud ya está en la
  landing page. Se puede extender con históricos (gráfico de drift,
  changelog visual).

### Largo plazo
- **Modelo de contribución** — definir cómo aceptar extractores de la
  comunidad.
- **Estrategia de sostenibilidad** — el proyecto lo mantiene una sola
  persona. El estado, la cronología y las conclusiones están en
  [`docs/sostenibilidad/README.md`](../sostenibilidad/README.md). La Auditoría 3
  (2026-09-29) dio veredicto **D**: todavía no se ejecuta sponsorship
  institucional; primero va un experimento de discovery con su gate. El
  [Plan 110](../../plans/110-programa-de-patrocinios.md) queda en HOLD.

---

## Issues de GitHub

Todos los issues de estabilización (#4-#7) y mejoras están cerrados.
El siguiente release puede abrir issues nuevos si surgen bugs o
solicitudes de usuarios.
