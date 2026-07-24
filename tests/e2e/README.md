# tests/e2e/

Scripts de verificación de los "Done criteria" de cada plan de `plans/` ejecutado en la
sesión 2026-07-24 (ver `spec.md` en la raíz del repo). **No** es parte de la suite
pytest de `tests/*.py` — son scripts de shell independientes, no se auto-descubren por
`make test` ni por `pytest`, y no colisionan con el gate de co-cambio de tests que
`AGENTS.md §12` exige para cambios de lógica de pipeline (esos tests siguen viviendo en
`tests/test_*.py`, junto al código que cubren).

Cada `verify_NNN.sh` reproduce, en orden y sin interacción, los comandos exactos de la
sección "Done criteria" de `plans/NNN-*.md` (o `plans/archive/NNN-*.md` una vez
archivado). Requiere correrse desde la raíz del repo con `.venv` ya creado
(`make bootstrap`).

Uso:

```bash
tests/e2e/verify_058.sh     # un plan puntual
tests/e2e/run_all.sh        # todos los planes ya marcados DONE, en orden de la cola
```

Salida: cada script imprime cada criterio antes de correrlo y sale con el código de
salida del primer comando que falle (`set -euo pipefail`).
