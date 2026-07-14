---
title: "chile-hub — SECURITY.md"
description: >
  Política de seguridad para chile-hub. Versiones soportadas, cómo reportar
  vulnerabilidades, y qué información incluir en un reporte.
category: security-policy
audience: [security-researcher, user, contributor]
priority: high
last_updated: 2026-07-14
---

# Política de Seguridad

## Versiones soportadas

Las correcciones de seguridad se manejan en la default branch y se publican en el siguiente release.
Usa la última GitHub release o el paquete PyPI a menos que un mantenedor indique lo contrario.

## Reportar una vulnerabilidad

Reporta vulnerabilidades sospechadas a través del sistema de reporte privado de GitHub:

> <https://github.com/cortega26/chile-hub/security/advisories/new>

Incluye en el reporte:

| Campo | Descripción |
|---|---|
| **Versión afectada** | Release tag, commit SHA o versión de PyPI |
| **Impacto** | Qué componente se ve afectado y su explotabilidad |
| **Reproducción** | Pasos para reproducir o proof of concept mínimo |
| **Alcance** | Si afecta al código Python, a los datos empaquetados o a los artifacts del release |

> No abras un issue público para una vulnerabilidad no resuelta.
