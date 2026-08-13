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
tests/e2e/verify_058.sh     # un plan puntual (solo planes activos)
tests/e2e/run_all.sh        # todos los planes activos ya marcados DONE, en orden de la cola
make e2e                    # equivalente a run_all.sh desde la raíz
```

Salida: cada script imprime cada criterio antes de correrlo y sale con el código de
salida del primer comando que falle (`set -euo pipefail`).

## Scripts congelados (Plan 080)

Los `verify_NNN.sh` de planes **archivados** viven en `plans/archive/e2e/` y **no se
ejecutan**: sus aserciones de datos vivos se rompen con la evolución del pipeline —
el `verify_059.sh` (17 parquets del mirror HF) ya exigió un fix con el Plan 084
(18 parquets tras promover perfil). Se conservan como registro histórico de los
"Done criteria"; la señal viva de liveness/frescura la dan `source-urls.yml`,
`verify_pipeline.py` y la suite pytest.
