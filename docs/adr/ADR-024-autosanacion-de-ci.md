# ADR-024: Política de autosanación de CI (self-correct, self-heal, self-improve)

**Fecha:** 2026-10-13
**Estado:** proposed (pasa a accepted al mergear este PR)
**Decisión:**
- **Self-correct.** Un fallo de CI se repara desde la fuente de verdad, no
  actualizando el literal que falló. Un guardrail que se rompe por el bump de
  una dependencia se des-brittlea: verifica el invariante (p. ej. "el workflow
  usa un SHA de 40 hex"), no el valor móvil. La igualdad entre superficies
  solo se reemplaza por una eliminación real de la duplicación; nunca se
  relaja a ciegas.
- **Self-heal.** El drift determinista y regenerable lo corrige un bot en el
  evento que lo origina: `dependabot-lock.yml` regenera `uv.lock` en PRs de
  Dependabot; el job main-only `docs-autosync` regenera docs tras carreras con
  release. Reglas: `--check` antes de escribir; GITHUB_TOKEN + `[skip ci]`;
  jobs con `contents: write` separados y main-only, nunca en el job `quality`
  (lección P1 del PR #60). Un fallo no determinista no se auto-sana: alerta.
- **Self-improve.** Todo incidente de CI deja, en el mismo arreglo: (a) un
  guardrail mecánico que habría fallado antes del fix; (b) el incidente
  documentado en el docstring del guardrail (PR/run/commit); (c) si es posible,
  la eliminación de la derivación en lugar de un chequeo literal nuevo.
- Orden de preferencia ante una deriva: **eliminar la duplicación > auto-sanar
  > detectar y bloquear**. Es "un hecho, un dueño" (§12 de `AGENTS.md`)
  aplicado también a versiones de herramientas y pines.

## Contexto

La misma clase de fallo reapareció cuatro veces en 30 días: un hecho duplicado
entre superficies, sincronizado a mano.

1. **ruff, cuatro drifts.** 0.15.17→0.16.7 (Plan 094, `972ffbb`), 0.16.8
   (`94fddf6`), 0.16.9→0.16.10 (`7f5d467`), 0.16.10→0.17.0 (#160: `pyproject`
   y `uv.lock` subieron, pre-commit y CI quedaron atrás; `RuffPinSingleSourceTests`
   puso rojo `main` — run 38394297445 — hasta alinearlos en #165).
2. **mypy.** La auditoría del 2026-10-13 encontró `mypy==2.4.0` en `pyproject`
   vs `mirrors-mypy v2.3.1` en pre-commit (sin guardrail que lo cubriera) y
   `tenacity==9.1.4` en `additional_dependencies` vs 9.2.1 en `uv.lock`.
3. **Pin de una acción como literal.** El guardrail de Lighthouse fijaba
   `actions/upload-artifact@v7.0.1`; el bump de Dependabot a v7.0.2 (PR #163,
   run 38387365191) lo rompió. Des-brittleado a un invariante de 40 hex en #165.
4. **Barrido de pins incompleto.** El test de pins solo cubría
   `pipeline-check.yml` y el prefijo `actions/`, así que
   `codecov/codecov-action@v7` (step muerto, tag flotante) nunca dio señal.

Ya existían dos mecanismos de auto-sanación con este espíritu
(`dependabot-lock.yml` para el lock y el job `docs-autosync` para las carreras
con release); esta ADR los declara política y define cuándo aplican.

## Decisión

1. **Toolchain de una sola superficie (self-correct estructural).** Los hooks
   de ruff/mypy pasan a `repo: local` + `language: system` con `uv run`
   (dev-pin de `pyproject.toml` + `uv.lock`), y CI corre `uv run ruff` en
   lugar de `uvx ruff@X`: la versión deja de existir en tres lugares. Se
   elimina el step muerto de Codecov, los `uvx twine` sin pin de los jobs de
   packaging pasan a `uv run --frozen --extra dev` (lock) y el barrido de
   pins se generaliza a todos los workflows exigiendo SHA de 40 hex +
   comentario `# vX.Y.Z`.
2. **Guardrails de automejora.** `SingleSourceToolingGuardrailTests` prohíbe
   reintroducir los `rev` de mirrores; `NoHardcodedActionPinGuardrailTests`
   prohíbe embeber SHAs de acciones como literal en tests/scripts;
   `test_all_workflows_pin_third_party_actions` cubre todos los workflows; el
   job `quality` valida el config de pre-commit.
3. **Los self-heals existentes quedan como están** (`dependabot-lock.yml`,
   `docs-autosync`) y satisfacen el contrato self-heal; no se agregan bots con
   escritura nuevos.

## Alternativas consideradas

- **Bot `sync_pins` que reescriba los `rev`/pines en el PR de Dependabot.**
  Rechazado: el push con GITHUB_TOKEN no dispara workflows, así que el estado
  sanado no se valida antes del merge; el `rev` de un mirror puede no existir
  cuando el paquete sí (guardrail verde, pre-commit de todos roto); y abre una
  superficie donde un bot reescribe la ejecución de CI sin validación.
- **Solo gate (`--check`) sin tocar las superficies.** Rechazado: mantiene
  tres fuentes y obliga a un commit humano por cada bump; la clase ya
  reapareció cuatro veces.
- **Pinear el step muerto de Codecov.** Rechazado: mantiene deuda y ruido de
  Dependabot por un step que no corre; reactivarlo es re-agregarlo con pin.
- **Allowlist para Codecov en el barrido de pins.** Rechazado: las excepciones
  envejecen; eliminar el step deja el invariante sin excepciones.

## Consecuencias

- Los hooks locales requieren `uv` (igual que pip-audit/interrogate/bandit,
  que ya lo hacían); `uv run` usa el venv sincronizado con `uv.lock`.
- El `rev` de ruff/mypy deja de verse en `.pre-commit-config.yaml`; la versión
  vive solo en `pyproject.toml` y `uv.lock`.
- Reactivar Codecov = re-agregar el step con SHA pinneado.
- Rollback: revertir el commit; no hay migración de datos ni cambios de
  contrato de API.
