# Plan 111: Los consumidores de `workflow_run` validan el repositorio y evento disparadores

> **Executor instructions**: Sigue este plan paso a paso. Corre cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no
> improvises. Al terminar, actualiza la fila de este plan en `plans/README.md`
> (a menos que un reviewer te haya dicho que él mantiene el índice).
>
> **Drift check (run first)**: `git diff --stat 1464109..HEAD -- .github/workflows/pypi-release.yml .github/workflows/pages-deploy.yml .github/workflows/pipeline-check.yml tests/test_ci_config.py`
> Si algún archivo in-scope cambió desde este plan, compara los extractos de
> "Current state" contra el código vivo antes de proceder; si no coinciden,
> es STOP condition.

## Status

- **Priority**: P1
- **Effort**: S-M
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `1464109`, 2026-09-29

## Why this matters

`PyPI Release` (y `Pages Deploy`) se disparan con `workflow_run` de `Pipeline
Check` filtrando **solo por nombre de branch** (`branches: [main]`). El job
`release` descarga el artefacto del run disparador y adopta su contenido sobre
`data/normalized/` confiando en un `pipeline_artifact_provenance.json` que el
propio run produjo (auto-declarado), y el job `hf-publish` — que tiene
`HF_TOKEN` — publica ese mismo artifact al espejo público.

Un run de `Pipeline Check` disparado por un PR de fork también sube el
artefacto (`pipeline-check.yml:445-461`, sin gate por evento), el filtro
`branches` de `workflow_run` evalúa la branch **head** del run disparador (la
del fork), y nada verifica `head_repository`. Eso permite que un artifact
producido fuera del repo entre al release y al espejo HF si pasa la
re-verificación de `verify_pipeline --profile release`. El check de frescura
(`artifact_sha != main_sha`) hoy solo emite un `::warning::`.

Este plan agrega el gate de identidad estándar (repo + evento) y convierte el
chequeo de SHA en una comprobación de ancestría real, sin romper el fallback
diseñado (adoptar el último run `schedule`/`workflow_dispatch`
publication-grade, que casi nunca coincide con HEAD).

## Current state

- `.github/workflows/pypi-release.yml`
  - `:3-8` trigger `workflow_run` + `workflow_dispatch`.
  - `:34` `if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'`.
  - `:132-136` resuelve `run_id` desde `github.event.workflow_run.id`.
  - `:145-173` `try_download` adopta el artifact si su provenance declara
    `verification_profile == "publication"` y `require_live is True`.
  - `:181-186` mismatch de SHA solo emite warning.
  - `:388-443` job `hf-publish` reusa `assets_run_id`/`run_id` y corre con
    `HF_TOKEN`.
- `.github/workflows/pages-deploy.yml`
  - `:6-19` mismo trigger `workflow_run` (Pipeline Check, PyPI Release,
    Adoption Stats, geometría) con `branches: [main]`; `:34` gate por
    `conclusion == 'success'`. No descarga el artifact (hace checkout), pero
    hoy un run de fork puede disparar un deploy del sitio.
- `.github/workflows/pipeline-check.yml`
  - `:200-202` job `build-and-test` corre también en `pull_request`.
  - `:445-461` sube `data/normalized/` + `README.md` + `index.html` + `app.js`
    sin gate por evento.
- `tests/test_ci_config.py` — patrón de guardrails de texto; agrega
  `SCRIPTS_DIR` a `sys.path` (`:14-24`) y ya tiene clases que leen
  `PYPI_RELEASE_WORKFLOW` (`:22`). Modela tu test sobre
  `AutoridadesElectasScraplingGuardrailTests` (`:118`) o
  `ReleaseArtifactLayoutGuardrailTests` (`:1399`).
- Comandos del repo: `uv` + Makefile; tests con `.venv/bin/pytest`.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Baseline tests (gate) | `./.venv/bin/pytest tests/test_ci_config.py -v` | declared | todo verde en el checkout sin cambios |
| Lint | `make lint` | declared | exit 0 |
| Format | `make format-check` | declared | exit 0 |
| Test focal | `./.venv/bin/pytest tests/test_ci_config.py -k "WorkflowRunTrust" -v` | declared | nuevos tests pasan |

## Scope

**In scope** (los únicos archivos que debes modificar):
- `.github/workflows/pypi-release.yml`
- `.github/workflows/pages-deploy.yml`
- `tests/test_ci_config.py` (clase nueva de guardrail)

**Out of scope** (NO tocar, aunque parezca relacionado):
- `pipeline-check.yml` — el upload del artifact se deja igual (lo consumen
  otros flujos y el sandbox de PR no tiene secretos).
- `scripts/verify_pipeline.py` — su lógica de perfiles no cambia.
- Secretos, environments o permisos de los jobs.
- `.github/workflows/hf-publish.yml` (lo toca el Plan 112).

## Git workflow

- Branch: `advisor/111-workflow-run-identity-gate`
- Commits por paso lógico, estilo del repo: `fix(security): <mensaje en español>`
  (ver `git log --oneline -10`, p. ej. `fix(ci): source-urls instala el extra pipeline`).
- NO hagas push ni PR salvo instrucción explícita del operador.

## Steps

### Step 0: Baseline verde

Corre la fila "Baseline tests (gate)". Si falla en el checkout sin cambios,
STOP: baseline roto (no lo "arregles").

### Step 1: Gate de identidad en el job `release`

En `pypi-release.yml`, cambia el `if:` del job `release` (`:34`) para exigir
repositorio y evento cuando el disparador es `workflow_run`:

```yaml
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event.workflow_run.conclusion == 'success' &&
       github.event.workflow_run.head_repository.full_name == github.repository &&
       github.event.workflow_run.head_branch == 'main' &&
       github.event.workflow_run.event != 'pull_request')
```

### Step 2: Guard de identidad por run descargado (defensa en profundidad)

Dentro del step `Download verified pipeline data assets`, antes del
`if [[ -z "$run_id" ]]` (`:138`), agrega una función y aplícala al `run_id`
resuelto (y a cada candidato del fallback):

```bash
          is_trusted_run() {
            local rid="$1"
            local repo
            repo="$(gh run view "$rid" --json headRepository --jq '.headRepository.full_name' 2>/dev/null || echo unknown)"
            [[ "$repo" == "$GITHUB_REPOSITORY" ]]
          }
```

- En la rama `workflow_run`, tras `run_id="${{ github.event.workflow_run.id }}"`,
  agrega `is_trusted_run "$run_id" || { echo "::error::Run $run_id no pertenece a $GITHUB_REPOSITORY"; exit 1; }`.
- En el loop de fallback (`:156-163`), agrega `is_trusted_run "$candidate" || continue`
  como primera línea del body.
- En `try_download` (`:111-130`), deja el `is_publication_grade` como está.

### Step 3: Endurecer el chequeo de SHA (ancestría, no igualdad)

Reemplaza el bloque de warning (`:181-186`) por un chequeo que acepte commits
ancestros de `main` y rechace historias ajenas:

```bash
          source_run="${found:-$run_id}"
          artifact_sha="$(gh run view "$source_run" --json headSha --jq .headSha 2>/dev/null || echo unknown)"
          main_sha="$(git rev-parse HEAD)"
          if [[ "$artifact_sha" != "unknown" && "$artifact_sha" != "$main_sha" ]]; then
            if git merge-base --is-ancestor "$artifact_sha" "$main_sha" 2>/dev/null; then
              echo "::notice::Artifact del run $source_run ($artifact_sha) es un commit ancestro de main; se acepta como fallback publication-grade."
            else
              echo "::error::Artifact del run $source_run proviene de $artifact_sha, que NO es ancestro de main ($main_sha). Abortando."
              exit 1
            fi
          fi
```

Nota: `artifact_sha` puede no existir localmente con `fetch-depth: 0`?
`actions/checkout` con `fetch-depth: 0` trae todo el historial de main, y el
artifact SHA viene de un run de main, así que debe estar. Si no lo está,
`merge-base --is-ancestor` falla el `if`, cae en el `else` y aborta — correcto.

### Step 4: Gate en `pages-deploy.yml`

Cambia el `if:` del job `deploy` (`:34`) por:

```yaml
    if: >-
      github.event_name != 'workflow_run' ||
      (github.event.workflow_run.conclusion == 'success' &&
       github.event.workflow_run.head_repository.full_name == github.repository &&
       github.event.workflow_run.head_branch == 'main' &&
       github.event.workflow_run.event != 'pull_request')
```

### Step 5: Guardrail test

En `tests/test_ci_config.py` agrega una clase (modelo:
`AutoridadesElectasScraplingGuardrailTests`) que lea
`PYPI_RELEASE_WORKFLOW` y el workflow de Pages (`ROOT_DIR / ".github" /
"workflows" / "pages-deploy.yml"`) y afirme:
1. `"head_repository.full_name == github.repository"` presente en ambos.
2. `"is_trusted_run"` y `"gh run view"` + `"headRepository"` presentes en
   `pypi-release.yml`.
3. `"git merge-base --is-ancestor"` presente en `pypi-release.yml`.
4. Docstring que documente este incidente/riesgo (patrón del archivo).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -k "WorkflowRunTrust" -v`
→ los 4 asserts pasan.

## Test plan

- Nuevos tests: `WorkflowRunTrustGuardrailTests` (4 asserts de texto, arriba).
- Patrón estructural: `tests/test_ci_config.py:118` y `:1399` (mismo estilo,
  sin parser YAML).
- No se agregan tests de comportamiento de GitHub Actions (no es posible en
  unit tests); el guardrail es la red contra re-drift.
- Verificación: `./.venv/bin/pytest tests/test_ci_config.py -v` → todo verde.

## Done criteria

- [ ] `grep -c "head_repository.full_name == github.repository" .github/workflows/pypi-release.yml .github/workflows/pages-deploy.yml` → 1 en cada uno
- [ ] `grep -c "git merge-base --is-ancestor" .github/workflows/pypi-release.yml` → 1
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -v` → todo verde, incluida la clase nueva
- [ ] `make lint` y `make format-check` → exit 0
- [ ] `git diff --name-only 1464109...HEAD` lista solo los 3 archivos in-scope
- [ ] Fila de `plans/README.md` actualizada

## STOP conditions

- Si tu versión de `gh` no soporta `gh run view --json headRepository`
  (verifícalo con `gh run view --help`), detente y reporta: cambia el guard a
  `headBranch`+`event` como mínimo y documenta la limitación.
- Si GitHub documenta que `head_repository` no está disponible en el contexto
  `workflow_run`, omite Step 1/4 y reporta; Step 2 sigue siendo válido.
- Si el diff en los workflows excede estos cambios (p. ej. hay que tocar
  permisos o secrets), STOP.
- Si el baseline del Step 0 falla.

## Maintenance notes

- Cualquier workflow nuevo que consuma `workflow_run` debe copiar el gate
  (la misma lección del guardrail de `pages-deploy` en Plan 064).
- Si se habilita un carril de release desde PRs (no previsto), este gate lo
  bloquea a propósito: la provenance auto-declarada no es autenticación.
- **Deferred:** firma/atestación de artifacts (sigstore/attestations de
  `actions/upload-artifact`) — no vale la complejidad hoy con un solo
  mantenedor; reabrir si entra un segundo publicador.
