# Plan 136: Auditoría — verificadores de publicación: utilidades comunes y descomposición

> **Executor instructions**: `scripts/verify_pipeline.py` es el gate de
> publicación diaria y `scripts/verify_landing.py` el smoke del sitio:
> cualquier cambio debe pasar sus propios comandos de verificación **antes**
> de tocar otra cosa. Si algo de "STOP conditions" ocurre, detente y reporta.
> Actualiza tu fila en `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 886a062..HEAD -- scripts/verify_pipeline.py scripts/verify_landing.py src/builders/artifacts.py tests/test_verify_pipeline.py tests/test_ci_config.py`
> Mismatch con "Current state" = STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (gates de publicación)
- **Depends on**: 133 (D5 artefacto→formato single-source puede tocarlo), 132 (C901 disponible)
- **Category**: refactor / mantenibilidad (auditoría 2026-10-13)
- **Planned at**: commit `886a062`, 2026-10-13

## Why this matters

`verify_pipeline.py` (MI C 0.00, 1 961 L) y `verify_landing.py` (MI C 3.88)
son la última línea de defensa antes de publicar datos y de dar por buena la
landing, y son también los archivos con peor maintainability del repo.
`verify_landing()` es **una sola función de 739 líneas** con 7 % docstrings;
`verify_pipeline` tiene 34 funciones con responsabilidades mezcladas
(contratos de esquema, registry, política de publicación, manifiestos,
reportes). La descomposición mejora exactamente lo que más caro sale de
mantener mal.

## Current state

- `scripts/verify_landing.py` — `verify_landing()` en `:171` (739 L, sin
  docstring); helpers ya existen arriba (`compute_runtime_*`, `status_rank`,
  `local_server`, `verify_no_inline_handlers`); sin docstring de módulo (D100).
- `scripts/verify_pipeline.py` — 34 funciones; grupos naturales:
  contratos/data-package (`verify_schema_contracts`, `verify_data_package`),
  registry/política (`verify_source_registry`, `verify_publication_policy`,
  `record_drop_violations`, `stable_publishable_dataset_names`),
  artefactos/manifiestos/metadata (`verify_artifact_manifest`,
  `verify_pipeline_metadata`, `verify_required_files`), reportes
  (`verify_hub_*`, `verify_overview`, `verify_*_report`), CLI
  (`build_parser`, `main:1906`).
- D5 — mapeo artefacto→(nombre, formato): `builders/artifacts.py:219:237` ≈
  `verify_pipeline.py:1516:1534` (pylint R0801); ver 133.
- Tests: `tests/test_verify_pipeline.py` (1 318 L) importa funciones por
  nombre; `test_ci_config.py` guarda textos del workflow (no de los scripts).

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Verify publicación | `make verify-publication` | exit 0 (sobre artefactos locales) |
| Verify readiness | `make verify-readiness` | exit 0 |
| Verify básico | `make verify` | exit 0 |
| Landing | `make verify-landing` | exit 0 |
| Tests | `./.venv/bin/pytest tests/test_verify_pipeline.py -q` | verde |
| Suite | `make test` | verde |

## Scope

**In scope**: `scripts/verify_pipeline.py`, `scripts/verify_landing.py`, un
módulo común nuevo (`scripts/_verify_common.py` si aplica), tests asociados.

**Out of scope**: cambiar reglas/umbrales de verificación (solo estructura);
`src/builders/*` salvo el punto único de D5 (133).

## Steps

### Step 0 — Baseline

`make verify` + `make verify-publication` + `make verify-landing` verdes
(sobre el árbol local). Registrar el output para comparar.

### Step 1 — `verify_landing()`: partir en checks

- Extraer de la función de 739 L: `_check_assets`, `_check_json_ld`,
  `_check_inline_handlers` (existe), `_check_runtime_freshness`,
  `_check_tables/status`, etc. La función principal queda como orquestador
  <60 L que agrega resultados y llama a `fail()`.
- Docstring de módulo + docstrings de las funciones nuevas (D100/D103).
- Contrato: **mismo stdout/stderr y mismo código de salida**; comparar el
  output baseline antes/después en el PR.

### Step 2 — Utilidades compartidas reales (no especulativas)

- Buscar duplicación efectiva entre `verify_pipeline` y `verify_landing`
  (`fail()`, parsing ISO, `status_rank`, formateo de reportes). Solo mover lo
  que esté duplicado hoy; `_verify_common.py` con docstring y tests.
- No forzar simetría donde no existe: si solo comparten `fail()`, mover solo
  eso.

### Step 3 — `verify_pipeline.py` por grupos

- Mover los grupos a un paquete `scripts/verifiers/` (p. ej.
  `contracts.py`, `registry.py`, `artifacts.py`, `reports.py`) y dejar
  `verify_pipeline.py` como CLI + re-exports; **los tests importan por
  nombre** → re-exportar todo desde `verify_pipeline.py` para no tocar
  `tests/test_verify_pipeline.py` (si el repo prefiere actualizar tests,
  hacerlo en el mismo commit y decirlo).
- Cuidado con el patrón `sys.path` de scripts (ver docstring del propio
  script): mantener los imports funcionando al invocarse como script y como
  módulo.
- `main()` (1906) queda como orquestador de perfiles (`readiness`,
  `publication`) sin lógica de checks inline.

### Step 4 — D5 si 133 no lo cerró

- El mapeo artefacto→formato debe tener una sola definición (importable por
  ambos). Ver Plan 133; si ya está, marcar aquí solo la verificación.

### Step 5 — Cierre

`make verify*`, `pytest tests/test_verify_pipeline.py`,
`make test`, `make lint`, `make doctor`; quitar `# noqa: C901  # 136` que 132
haya dejado en estos archivos; `plans/README.md` actualizado.

## Test plan

- Comparación byte a byte de stdout/exit code de los comandos `make verify*`
  antes/después (evidencia en el PR).
- Suite de `test_verify_pipeline` + `test_ci_config` (si toca textos).

## Done criteria

- [ ] `verify_landing()` ≤ ~60 L de orquestación; sin función >150 L en
      `scripts/verify_*.py`
- [ ] `verify_pipeline.py` como CLI + re-exports; grupos en
      `scripts/verifiers/`
- [ ] Outputs de los gates idénticos (evidencia antes/después)
- [ ] Suite/lint/doctor verdes; fila del índice actualizada

## STOP conditions

- Si el output de un gate cambia sin que el cambio sea intencional, revertir
  el step: los consumidores (CI, notify-schedule-failure) parsean estas
  salidas.
- Si `make verify-landing` no corre localmente por entorno (Playwright), usar
  CI del PR como verificación y anotarlo.
