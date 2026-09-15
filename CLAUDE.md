---
title: "chile-hub — CLAUDE.md"
description: >
  Punto de entrada para sesiones Claude Code en chile-hub.
  Solo enruta: orden de lectura + 3 comandos. El detalle vive en
  SOURCE_OF_TRUTH.md (índice), AGENTS.md (reglas) y Makefile (comandos).
category: ai-entrypoint
audience: [claude-code, ai-agent]
priority: critical
entrypoint_for: [SOURCE_OF_TRUTH.md, AGENTS.md]
related_docs:
  - SOURCE_OF_TRUTH.md
  - AGENTS.md
  - CONTRIBUTING.md
last_updated: 2026-09-15
---

# CLAUDE.md — Punto de Entrada para Claude Code

> **chile-hub**: capa de datos reproducible sobre datasets oficiales de Chile.
> Pipeline: extract → build → verify → test → publish.

## Orden de lectura (un hecho, un dueño — no se duplica nada aquí)

1. **[`SOURCE_OF_TRUTH.md`](./SOURCE_OF_TRUTH.md)** — único índice: invariantes, mapa de archivos, a dónde ir según tu tarea.
2. **[`AGENTS.md`](./AGENTS.md)** — reglas completas (§4 invariantes, §5 agregar datasets, §6 legal, §9 CI/CD, §10 antipatrones, §12 anti-drift).
3. **`make help`** — comandos canónicos (este archivo no lista comandos).

## Arranque mínimo

```bash
make bootstrap          # una vez: .venv + deps + Chromium
make doctor             # antes de cada sesión: gates anti-drift (§12)
make refresh            # pipeline completo
```

> Al modificar código: checklist en `AGENTS.md §5` + `make doctor` antes de commit.
> Detalle completo siempre en [`AGENTS.md`](./AGENTS.md).
