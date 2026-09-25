# Plan 103: Infraestructura de citación (`CITATION.cff`) + ruta DOI Zenodo

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` and the scoreboard/backlog in `ROADMAP.md`.
>
> **Drift check (run first)**: `git diff --stat 039fc03..HEAD -- CITATION.cff docs/citation.md README.md mkdocs.yml examples/notebooks/README.md tests/test_ci_config.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: distribution
- **Planned at**: commit `039fc03`, 2026-09-25

## Why this matters

La academia es el consumidor más denso de datos oficiales chilenos, y el repo
ya tiene quickstart R (`docs/r-quickstart.md`) — pero **no existe `CITATION.cff`
ni DOI**: nadie puede citar chile-hub de forma canónica. GitHub muestra el botón
"Cite this repository" en cuanto exista el archivo, y la integración
GitHub↔Zenodo emite un DOI gratis por release. Cada paper/tesis que cite el hub
es un backlink permanente y un usuario nuevo. El costo de habilitarlo es un
archivo de metadatos + instrucciones para el operador.

## Current state

- No existe `CITATION.cff` ni `docs/citation.md`; `grep -ri zenodo` en el repo
  no encuentra nada fuera de `.venv/`.
- `pyproject.toml:12-13` declara `authors = [{ name = "Carlos Ortega" }]`.
- `mkdocs.yml:51-61` tiene nav sin entrada de citación.
- `examples/notebooks/` tiene 4 notebooks sin README con enlaces "Open in Colab".
- `README.md` está protegido por bloques delimitados (`doc_sync.py`); agregar
  prosa nueva fuera de bloques es seguro, pero **no** hardcodear conteos.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Doctor | `make doctor` | declared | exit 0 |
| MkDocs | `make docs-build` | declared | exit 0 |
| Tests | `./.venv/bin/pytest tests/test_ci_config.py -q -k "Citation"` | declared | all pass |

## Scope

**In scope**:
- `CITATION.cff` (nuevo, raíz)
- `docs/citation.md` (nuevo) + entrada en el nav de `mkdocs.yml`
- `README.md` (sección "Cómo citar", prosa sin conteos)
- `examples/notebooks/README.md` (nuevo, badges "Open in Colab")
- `tests/test_ci_config.py` (guardrail)

**Out of scope**:
- Crear la cuenta Zenodo / activar la integración: acción manual del operador,
  documentada como checklist (no automatizable desde el repo).
- `version_variables` de PSR para `CITATION.cff`: AGENTS.md §7 fija la versión
  sólo en `pyproject.toml`; no agregar un segundo lugar que sincronizar.
- Traducciones de la página de citación.

## Git workflow

- Branch: `advisor/distribution-wave-1` (wave 101–105).
- Commit por step; conventional commits (ej. `docs(citation): ...`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: `CITATION.cff`

Crear el archivo con `cff-version: 1.2.0`, `message`, `title`, `abstract`,
`type: software`, `authors` (Carlos Ortega, desde `pyproject.toml`),
`repository-code`, `url`, `license: MIT`, `keywords`. **Omitir `version` y
`date-released`** (derivarían con cada release de PSR; la versión citada se
resuelve en `docs/citation.md`). Dejar un comentario YAML indicando dónde pegar
el `doi:` cuando Zenodo lo emita.

**Verify**: `./.venv/bin/python -c "import yaml; d=yaml.safe_load(open('CITATION.cff')); assert d['cff-version']=='1.2.0' and d['title']; print('ok')"` → `ok`.

### Step 2: `docs/citation.md` + nav

Documentar: cómo citar el software (BibTeX + APA 7), cómo citar una capa
específica (atribución por fuente según `DATA_LICENSES.md`), la ruta DOI Zenodo
(checklist de 4 pasos para el operador: login con GitHub → activar el repo →
`make release` / release de GitHub → pegar el DOI en `CITATION.cff` y esta
página), y la nota de que el paquete publica un release por tag automático.
Agregar `- Citar chile-hub: citation.md` al nav de `mkdocs.yml`.

**Verify**: `make docs-build && test -f reference/citation/index.html` → existe.

### Step 3: README + material de curso

Agregar en `README.md` una sección corta "Cómo citar" que enlace a
`docs/citation.md` (sin conteos ni versiones literales). Crear
`examples/notebooks/README.md` con los 4 notebooks y enlaces
`https://colab.research.google.com/github/cortega26/chile-hub/blob/main/examples/notebooks/<archivo>`,
más una línea de atribución a las fuentes.

**Verify**: `make doctor` exit 0 (bloques derivados del README intactos);
`grep -c "colab.research.google.com" examples/notebooks/README.md` == 4.

### Step 4: Guardrail

En `tests/test_ci_config.py`, clase `CitationFileGuardrailTests`: `CITATION.cff`
existe, parsea con YAML, tiene `cff-version: 1.2.0`, `type: software`,
`authors`, `repository-code`, `license`, y **no** contiene `version:` (evita el
drift con PSR). Verifica además que `docs/citation.md` está en el nav de
`mkdocs.yml`.

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -q -k Citation` → all pass.

## Test plan

- Nuevos: `CitationFileGuardrailTests` (2 tests de texto/metadata, sin red).
- No requiere `data/normalized/`.
- Regresión: `make doctor` + `make docs-build`.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `test -f CITATION.cff && grep -q "cff-version: 1.2.0" CITATION.cff`
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -q` exits 0
- [ ] `make doctor` exits 0 y `make docs-build` exits 0
- [ ] README enlaza `docs/citation.md` y `examples/notebooks/README.md` tiene 4 badges Colab
- [ ] `git diff --name-only 039fc03...HEAD` lista sólo archivos in-scope
- [ ] `plans/README.md` status row + `ROADMAP.md` scoreboard/backlog actualizados

## STOP conditions

Stop and report back (do not improvise) if:

- `CITATION.cff` requeriría un `version:` sincronizado (contradice AGENTS.md §7).
- `make doctor` falla por `sync_docs --check` tras editar README (indicaría que
  se tocó un bloque derivado; revertir a prosa plana).
- El nombre/afiliación de autoría de `pyproject.toml` no coincide con lo
  esperado y no hay una fuente canónica en el repo.
- Una verificación falla dos veces tras un intento razonable de fix.

## Maintenance notes

- Cuando el operador active Zenodo, el único cambio es agregar `doi:` +
  `identifiers` en `CITATION.cff` y la línea correspondiente en
  `docs/citation.md`; el guardrail permite campos nuevos, sólo prohíbe `version:`.
- Reviewer: la fecha de `date-released` no debe reaparecer como campo
  mantenido a mano.
