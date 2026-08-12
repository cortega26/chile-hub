# Plan 070: Filtrar HF por publication_track (nunca candidate/deprecated)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- scripts/publish_hf_dataset.py docs/hf/ AGENTS.md tests/test_pipeline_logic.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none (pero coordina con 071 — ambos tocan el catálogo)
- **Category**: bug / docs
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

`AGENTS.md:750-753` afirma que el mirror de Hugging Face "nunca incluye el
carril candidate". El script `publish_hf_dataset.py` selecciona por
`outputs` truthy + `redistribution_ok is True` del catálogo, sin mirar
`publication_track` del registry. **Confirmado en producción**: el mirror
`cortega26/chile-hub` ya tiene 19 parquets, incluyendo
`consumo_electrico_comunal.parquet` (fuente muerta, deprecated, 3 filas de
muestra en fallback) y `perfil_territorial_comunal.parquet` (candidate).
La política canónica se contradice sola: doc dice "nunca candidate", código
sube candidate.

## Current state

- `scripts/publish_hf_dataset.py:40-63` — selección:
  ```python
  def select_publishable_files():
      catalog = _read_catalog()
      for name, entry in sorted(catalog.items()):
          outputs = entry.get("outputs")
          if not outputs:
              continue
          if entry.get("reuse_policy", {}).get("redistribution_ok") is not True:
              continue
  ```
  El docstring (L44-45) asume "el carril candidate nunca declara outputs",
  pero el build hoy declara `outputs` para las 2 candidate (verificado en
  `data/normalized/dataset_catalog.json`).
- `data/source_registry.json` — `publication_track: candidate` para
  `perfil_territorial_comunal` (maturity: candidate) y
  `consumo_electrico_comunal` (maturity: deprecated).
- `AGENTS.md:750-753` — el claim "nunca incluye el carril candidate".

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Dry-run HF | `HF_TOKEN=x ./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` | lista sin candidate |
| Tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q` | all pass |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**:
- `scripts/publish_hf_dataset.py`
- `tests/test_pipeline_logic.py` (guardrail de selección)
- `AGENTS.md` (si el claim necesita matiz tras el fix)
- `docs/hf/dataset-card.md` (si menciona el conteo)

**Out of scope**:
- El builder de catálogo (`src/builders/catalog.py`) — se toca en 071.
- La landing (carril candidate visible) — DIR-01.
- Re-verificación del mirror publicado (operador).

## Git workflow

- Branch: `advisor/070-hf-publication-track`
- Conventional commits, uno por paso lógico.
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Lee el registry como fuente de carril

En `select_publishable_files()`, carga `data/source_registry.json` (ya hay
patrón de lectura en el repo, p. ej. `scripts/verify_pipeline.py`), construye
el set de datasets con `publication_track == "stable_publishable"` (y NO
`maturity_status == "deprecated"`), y filtra la selección por ese set **además**
de `outputs` + `redistribution_ok`.

**Verify**: `HF_TOKEN=x ./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` → la lista NO contiene `consumo_electrico_comunal` ni `perfil_territorial_comunal`; sigue teniendo 17 parquets.

### Step 2: Guardrail de selección

En `tests/test_pipeline_logic.py` (modelar sobre `AdoptionStatsTests` o el
patrón de `select_publishable_files` existente), test que `select_publishable_files()`
NO incluye candidate/deprecated del registry, y que falla ruidoso si una
`stable_publishable` carece de su Parquet.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "hf\|publishable"` → all pass.

### Step 3: Actualiza la doc

Confirma que `AGENTS.md:750-753` y `docs/hf/dataset-card.md` reflejen el
comportamiento real (17 capas, candidate excluido por `publication_track`).

**Verify**: `make sync-docs` sin cambios inesperados; `make doctor` exit 0.

## Test plan

- `test_hf_excludes_candidate_and_deprecated` (nuevo) — lee el registry real
  y verifica que la selección no contiene candidate/deprecated.
- Modelar sobre el test existente de `select_publishable_files` (si existe)
  o sobre `AdoptionStatsTests`.
- Verificación: suite focal + dry-run.

## Done criteria

- [ ] `--dry-run` lista 17 capas, sin candidate/deprecated
- [ ] Test de selección existe y pasa
- [ ] `make doctor` exit 0
- [ ] `AGENTS.md` y la doc de HF coherentes con el código
- [ ] `plans/README.md` status row updated

## STOP conditions

- El registry no tiene `publication_track` para algún dataset (drift de schema).
- El dry-run excluye más de lo esperado (un stable_publishable sin `outputs`).

## Maintenance notes

- El script HF y el builder de catálogo comparten la noción de "publicable";
  el fix de 071 (catálogo del ZIP) debe re-verificar este script para no
  romper la consistencia.
- El mirror publicado ya contiene las 2 candidate — re-verificar
  `cortega26/chile-hub` tras el fix es tarea del operador (subida real).
