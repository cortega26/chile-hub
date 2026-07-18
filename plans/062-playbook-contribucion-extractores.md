# Plan 062: Playbook de contribución de extractores (carril comunitario)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- CONTRIBUTING.md .github/ISSUE_TEMPLATE/ docs/dataset-inclusion-criteria.md AGENTS.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction / docs
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

`docs/backlog/NEXT_STEPS.md` lista como dirección de largo plazo abierta:
**"Modelo de contribución — definir cómo aceptar extractores de la comunidad."**
El repo ya tiene toda la maquinaria que hace *seguro* aceptar extractores
externos (contrato ABC de `BaseExtractor`, gate de registro de `validate_*`,
contratos de esquema, `check_companion_paths` en CI, carril `candidate` con
`review_by`), y ya tiene el template de issue `dataset_request.yml` que hace
las preguntas bloqueantes. Lo que falta es el **camino documentado** desde
"issue aprobado" hasta "PR mergeado": hoy un contribuyente externo tendría que
reconstruir el flujo leyendo `AGENTS.md §5` (escrito para agentes/mantenedor,
no como guía de PR). Sin ese camino, la maquinaria de gobernanza no se
convierte en embudo de contribuciones.

**Re-scope verificado durante la auditoría**: el issue template
`.github/ISSUE_TEMPLATE/dataset_request.yml` **ya existe** y cubre licencia,
formato, join keys, caso de uso y checklist de criterios — por eso este plan es
solo el playbook del lado código, no el intake.

## Current state

- `CONTRIBUTING.md` — estructura actual (verificada): frontmatter YAML
  (title/description/category/audience/priority/related_docs/last_updated),
  secciones `## Verificaciones locales` (make lint/format-check/test/doctor),
  `## Cambios de datos` (remite a `AGENTS.md §5` en un párrafo), `## Pull
  requests` (prefijos conventional commits). **No existe** una guía paso a paso
  para contribuir un extractor.
- `.github/ISSUE_TEMPLATE/dataset_request.yml` — ya implementa el intake
  (source URL, licensing dropdown, format dropdown, use case, join keys,
  expected schema, maintenance notes, checklist de criterios). Se **referencia**,
  no se modifica.
- `docs/dataset-inclusion-criteria.md` — criterios de aceptación/deprecación
  (fuente de verdad de carriles; se referencia).
- `AGENTS.md §5` — los 7 pasos de "¿Cómo agregar un nuevo dataset?" (evaluar
  fuente → extractor → registrar catálogo → validaciones → tests → CI → docs).
  El playbook **condensa y enlaza** estos pasos para audiencia contribuyente;
  no los duplica en detalle (AGENTS.md sigue siendo la fuente canónica).
- Piezas del flujo con nombre propio para enlazar desde el playbook:
  `src/extractors/base.py` (BaseExtractor ABC), `src/validation.py`,
  `scripts/check_validation_registration.py`,
  `scripts/check_companion_paths.py`, `data/dataset_catalog_config.json`,
  `data/source_registry.json` (carril `candidate`, `review_by`),
  `docs/dataset-ideas/` (ejemplos de evaluación de fuentes),
  `tests/test_extractors.py` (clase de test por extractor).
- Verificación relevante: `make doctor` corre
  `check_companion_paths.py registry`; `CONTRIBUTING.md` no dispara reglas de
  co-cambio (verificado en `COMPANION_RULES` — no aparece como trigger ni como
  compañero obligatorio).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Doctor | `make doctor` | exit 0 |
| Lint | `make lint && make format-check` | exit 0 |
| Enlaces internos sanos | `grep -n "](AGENTS.md" CONTRIBUTING.md` | encuentra los enlaces nuevos |

## Scope

**In scope** (the only files you should modify):
- `CONTRIBUTING.md` (nueva sección + actualizar `last_updated` del frontmatter)

**Out of scope** (do NOT touch, even though they look related):
- `AGENTS.md` — §5 sigue siendo la fuente canónica; el playbook enlaza, no
  reescribe. (El plan 058 edita AGENTS.md §12; no pisar ese archivo aquí.)
- `.github/ISSUE_TEMPLATE/dataset_request.yml` — ya existe y está completo.
- `docs/dataset-inclusion-criteria.md`, `docs/dataset-ideas/*`.
- Cualquier archivo de código o CI.

## Git workflow

- Branch: `advisor/062-extractor-contribution-playbook`
- Commit: `docs(contributing): playbook de contribucion de extractores via carril candidate`
- No pushear ni abrir PR salvo instrucción del operador.

## Steps

### Step 1: Escribir la sección playbook en `CONTRIBUTING.md`

Inserta una sección `## Contribuir un extractor (dataset nuevo)` entre
`## Cambios de datos` y `## Pull requests`. Contenido (español, tono del
archivo — directo, sin marketing):

1. **Párrafo de encuadre** (2–3 líneas): los datasets nuevos entran por el
   carril `candidate`; se evalúan contra
   `docs/dataset-inclusion-criteria.md`; el mantenedor decide la promoción a
   `stable_publishable`. Antes de escribir código, abrir un issue con el
   template "Dataset request" (enlazar
   `.github/ISSUE_TEMPLATE/dataset_request.yml`) — un PR de extractor sin
   issue previo aprobado probablemente se cierre.
2. **Checklist del PR de extractor** (lista numerada, cada ítem 1–2 líneas con
   enlace al recurso canónico):
   1. Issue "Dataset request" con respuesta positiva del mantenedor a las 3
      preguntas bloqueantes (licencia, formato, estabilidad — enlazar
      `AGENTS.md §5` Paso 1).
   2. Extractor en `src/extractors/{nombre}_extractor.py` siguiendo el
      contrato de `src/extractors/base.py` (ver un extractor simple como
      modelo, p. ej. `pobreza_extractor.py`).
   3. `data/staging/{nombre}.csv` + `{nombre}.metadata.json` con todos los
      campos obligatorios (enlazar `AGENTS.md §5` Paso 2, que los lista).
   4. Entrada en `data/dataset_catalog_config.json` (+ `source_registry.json`
      con carril/`review_by` — enlazar `docs/dataset-inclusion-criteria.md`).
   5. `validate_{nombre}()` en `src/validation.py` + registro en el bloque
      `validations = {…}` de `build_dev_db.py`; verificar con
      `python scripts/check_validation_registration.py`.
   6. Tests: clase en `tests/test_extractors.py` + casos de borde en
      `tests/test_pipeline_logic.py` (enlazar `AGENTS.md §5` Paso 5).
   7. Doc `docs/datasets/{nombre}.md` + contrato
      `contracts/datasets/{nombre}.schema.json` (ambos los exige
      `make doctor` vía `check_companion_paths.py registry`).
   8. CI: agregar el extractor al paso de extracción del workflow
      correspondiente (`pipeline-check.yml` diario o `monthly-scrape.yml`
      mensual — criterio de cadencia en `AGENTS.md §3`).
3. **Lo que el mantenedor revisa** (3–4 bullets): licencia/redistribución
   (semáforo de `AGENTS.md §6`), que el fallback no llegue al bundle público,
   que `make doctor` + `make refresh` pasen, y que el dataset aporte valor de
   cruce (join keys con DPA).
4. **Nota final**: expectativa honesta — mantenedor único, revisión en días no
   horas; un extractor aceptado en `candidate` puede tardar ciclos en promover
   (ver `review_by`).

**Verify**: `grep -c "Contribuir un extractor" CONTRIBUTING.md` → `1` · y
`grep -c "check_validation_registration.py" CONTRIBUTING.md` → ≥1

### Step 2: Actualizar el frontmatter

Cambia `last_updated: 2026-07-14` por la fecha real del cambio (formato
`YYYY-MM-DD`). No toques ningún otro campo del frontmatter.

**Verify**: `head -20 CONTRIBUTING.md | grep "last_updated"` → fecha nueva

### Step 3: Verificación de enlaces y gates

Recorre los enlaces internos agregados y confirma que cada archivo referenciado
existe (`AGENTS.md`, `.github/ISSUE_TEMPLATE/dataset_request.yml`,
`docs/dataset-inclusion-criteria.md`, `src/extractors/base.py`,
`src/validation.py`, `scripts/check_validation_registration.py`,
`tests/test_extractors.py`, `contracts/datasets/`).

**Verify**: `for f in AGENTS.md .github/ISSUE_TEMPLATE/dataset_request.yml docs/dataset-inclusion-criteria.md src/extractors/base.py src/validation.py scripts/check_validation_registration.py tests/test_extractors.py; do test -e "$f" || echo "FALTA: $f"; done; echo ok` → `ok`
· y `make doctor` → exit 0

## Test plan

- Sin tests de código (doc-only). Verificación = `make doctor` exit 0 +
  chequeo de enlaces de Step 3 + `make lint && make format-check` (no-regresión
  general, aunque no toca Python).
- No se requiere test de texto en `test_ci_config.py` (la política del repo lo
  reserva para regresiones de CI/Makefile ya ocurridas — no aplica a una doc).

## Done criteria

- [ ] `CONTRIBUTING.md` tiene la sección `## Contribuir un extractor (dataset nuevo)` con los 4 bloques de contenido
- [ ] La sección referencia el issue template existente (no propone crear uno)
- [ ] Todos los enlaces internos verificados (Step 3 imprime `ok`)
- [ ] `make doctor` exit 0
- [ ] `last_updated` del frontmatter actualizado
- [ ] Solo `CONTRIBUTING.md` modificado (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) si:

- `CONTRIBUTING.md` cambió de estructura (frontmatter distinto, secciones
  renombradas) — reconciliar antes de insertar.
- El flujo canónico de `AGENTS.md §5` ya no tiene 7 pasos o renombró piezas
  (el checklist debe reflejar el flujo real, no el de este plan — si difieren,
  el plan está stale).
- Descubres que el issue template `dataset_request.yml` fue eliminado o
  reemplazado (la premisa del re-scope queda inválida).
- Te tientas a agregar el playbook también a `AGENTS.md` — fuera de scope
  deliberado (AGENTS.md es para agentes; CONTRIBUTING para humanos); si crees
  que hace falta una línea puente en AGENTS.md, proponla en el PR, no la
  escribas.

## Maintenance notes

- **Co-evolución con `AGENTS.md §5`**: si §5 cambia (p. ej. se agrega un paso
  obligatorio como el campo `extractor` del plan 058), el checklist de
  CONTRIBUTING queda potencialmente stale. Es prosa curada (no hay verificación
  mecánica) — la defensa es la revisión humana en PRs que toquen §5; mencionarlo
  en la descripción de esos PRs.
- Si el proyecto adopta CODEOWNERS o review de segundo par, actualizar el
  bloque "Lo que el mantenedor revisa".
- En review, escrutar: que el playbook no prometa SLA de revisión ni
  promoción automática candidate→stable (decisión del mantenedor), y que el
  tono disuada PRs de fuentes frágiles (scraping HTML) — el anti-patrón #10 y
  el matiz de ADR-011 (profundidad sobre fuentes existentes sí, amplitud con
  fuentes frágiles no) deben quedar implícitos en el encuadre.
