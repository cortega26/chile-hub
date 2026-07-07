# Plan 025: Sync the public `Dataset` enum (and the drifted docs) with the 19‑dataset catalog

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/chile_hub/datasets.py tests/test_chile_hub.py data/normalized/dataset_catalog.json AGENTS.md SOURCE_OF_TRUTH.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`Dataset` (`src/chile_hub/datasets.py`) is the **public, shipped** enum the README
tells users to prefer over "strings mágicos" for typo‑safety and IDE autocomplete.
It currently lists **15** members, but the pipeline publishes **19** datasets
(`data/normalized/dataset_catalog.json` has `dataset_count: 19`). The four datasets
`pobreza_comunal`, `consumo_electrico_comunal`, `partidos_politicos`, and
`autoridades_electas` were added to the catalog but never to the enum, so
`Dataset.from_string("autoridades_electas")` **raises `ValueError`** on a valid,
published dataset, and `Dataset.EMPRESAS`‑style access is impossible for those four.

The reason this drifted silently is that `tests/test_chile_hub.py` asserts
`len(vals) == 15` — the test actively **freezes** the enum at the wrong count. This
plan re‑syncs the enum, corrects the test into a self‑maintaining guard against future
drift, and fixes the stale count/table in the agent‑facing docs.

## Current state

- `src/chile_hub/datasets.py` lists exactly 15 members (lines 26‑40), ending at
  `PERFIL_TERRITORIAL_COMUNAL = "perfil_territorial_comunal"`. Missing:
  `pobreza_comunal`, `consumo_electrico_comunal`, `partidos_politicos`, `autoridades_electas`.
- The canonical list of 19 dataset ids is the set of keys in
  `data/normalized/dataset_catalog.json`: the file is a top-level object with
  `dataset_count`, `generated_at_utc`, and a `datasets` list; each dataset entry carries
  its id in the `dataset` field. Confirmed ids:
  `autoridades_electas, censo_comunal, censo_hogares_viviendas, comunas, comunas_enriquecidas,
  consumo_electrico_comunal, distritos_electorales, empresas, establecimientos_educacionales,
  establecimientos_salud, finanzas_municipales, indicadores, indicadores_urbanos_siedu,
  partidos_politicos, perfil_territorial_comunal, pobreza_comunal, provincias, regiones,
  resultados_educacionales`.
- `tests/test_chile_hub.py:1764-1768`:
  ```python
  vals = Dataset.values()
  self.assertEqual(len(vals), 15)
  self.assertIn("comunas", vals)
  self.assertIn("regiones", vals)
  self.assertIn("empresas", vals)
  ```
  There is also `test_all_datasets_have_corresponding_contract` immediately below it.
- `AGENTS.md:15` says "Actualmente publica **quince** capas" with a 13‑row table (lines 17‑31).
- `SOURCE_OF_TRUTH.md` and `AGENTS.md` also carry stale `core.py`/`validation.py`/`build_dev_db.py`
  line counts (see Step 4) — folded here because they share the same root cause (catalog grew,
  surfaces not updated).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Datasets test | `.venv/bin/python -m pytest tests/test_chile_hub.py -q -k "Dataset or dataset"` | all pass |
| Enum vs catalog cross‑check | (built into the new test, Step 3) | pass |

## Scope

**In scope**:
- `src/chile_hub/datasets.py`
- `tests/test_chile_hub.py`
- `AGENTS.md`, `SOURCE_OF_TRUTH.md` (Step 4 only)

**Out of scope**:
- `README.md` — already correctly says "19 capas"; do not touch.
- `data/normalized/*` — generated artifacts; never hand‑edit.
- Adding the missing datasets to any pipeline config — they are already fully wired; this is
  only about the public enum surface and docs.

## Git workflow

- Branch: `advisor/025-sync-dataset-enum`
- Conventional commit, e.g. `fix(api): agrega 4 datasets faltantes al enum Dataset y guarda contra drift`.

## Steps

### Step 1: Add the four missing members to `Dataset`

In `src/chile_hub/datasets.py`, add the four missing members. Place them next to their
thematic siblings for readability (order is not load‑bearing since `values()` derives from
declaration order, but keep it sensible):

```python
    PARTIDOS_POLITICOS = "partidos_politicos"
    AUTORIDADES_ELECTAS = "autoridades_electas"
    POBREZA_COMUNAL = "pobreza_comunal"
    CONSUMO_ELECTRICO_COMUNAL = "consumo_electrico_comunal"
```

**Verify**: `.venv/bin/python -c "from src.chile_hub.datasets import Dataset; print(len(Dataset.values()))"` → `19`.

### Step 2: Confirm `from_string` now resolves the new ids

**Verify**:
`.venv/bin/python -c "from src.chile_hub.datasets import Dataset; print(Dataset.from_string('autoridades_electas'))"`
→ prints `Dataset.AUTORIDADES_ELECTAS` (no `ValueError`).

### Step 3: Turn the frozen test into a drift guard

Replace the hardcoded `self.assertEqual(len(vals), 15)` in `tests/test_chile_hub.py` with a
check that the enum matches the **catalog** exactly, so the two can never silently diverge again:

```python
def test_values_match_catalog(self):
    import json
    from pathlib import Path

    from src.chile_hub.datasets import Dataset

    catalog_path = Path("data/normalized/dataset_catalog.json")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_ids = {entry["dataset"] for entry in catalog["datasets"]}
    self.assertEqual(set(Dataset.values()), catalog_ids)
```

Keep the existing `assertIn("comunas"/"regiones"/"empresas", ...)` sanity assertions (rename the
method if you prefer, but do not delete the coverage). If the catalog JSON no longer has a
top-level `datasets` list with `dataset` fields in this repo checkout, treat that as a STOP
condition and report the real shape rather than guessing.

**Verify**: `.venv/bin/python -m pytest tests/test_chile_hub.py -q -k "Dataset or dataset or catalog"` → all pass.

### Step 4: Fix the stale counts in the agent‑facing docs

- `AGENTS.md:15`: change "quince capas" to "diecinueve capas" and add the four missing rows to the
  §1 table (`Pobreza Comunal`, `Consumo Eléctrico Comunal`, `Partidos Políticos`, `Autoridades Electas`)
  with their source and one‑line description. Use `README.md`'s current table as the reference for wording.
- `AGENTS.md` / `SOURCE_OF_TRUTH.md` line‑count claims — correct these to the actual `wc -l` values
  (run `wc -l src/chile_hub/core.py src/validation.py src/build_dev_db.py src/pipeline_status_utils.py src/extractors/base.py`):
  - `core.py` (SOURCE_OF_TRUTH says "~1 600", AGENTS says "~2 130"; actual differs) → use the real number or replace with "see file".
  - `validation.py` ("~760"), `build_dev_db.py` ("~670"), `pipeline_status_utils.py` ("~770"), `base.py` ("59 lineas").

**Verify**: `grep -n "quince" AGENTS.md` → no matches; `grep -n "19" AGENTS.md | head` shows the updated count.

## Test plan

- New/updated test: `test_values_match_catalog` (Step 3) — the enum's value set equals the catalog id set.
- Pattern: the existing `DatasetTests`/`test_values_returns_all` block in `tests/test_chile_hub.py`.
- Verification: pytest command above → all pass.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `.venv/bin/python -c "from src.chile_hub.datasets import Dataset; print(len(Dataset.values()))"` prints `19`
- [ ] `.venv/bin/python -c "from src.chile_hub.datasets import Dataset; Dataset.from_string('partidos_politicos'); Dataset.from_string('consumo_electrico_comunal')"` exits 0
- [ ] `grep -n "assertEqual(len(vals), 15)" tests/test_chile_hub.py` → no matches
- [ ] `.venv/bin/python -m pytest tests/test_chile_hub.py -q -k "Dataset or dataset or catalog"` exits 0
- [ ] `grep -n "quince" AGENTS.md` → no matches
- [ ] `make lint` and `make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `data/normalized/dataset_catalog.json` no longer has a top-level `datasets` list whose entries
  include a `dataset` id field — report the real shape so the guard test can be written correctly
  rather than guessing.
- The catalog id set is not exactly the 19 ids listed in "Current state" (a dataset was added/removed
  since `c486e7c`) — sync the enum to the live catalog and note the difference.
- `test_all_datasets_have_corresponding_contract` fails after adding the four members (a contract file
  is missing under `contracts/datasets/`) — that is a real gap; report it rather than deleting the assertion.

## Maintenance notes

- The Step‑3 guard means adding a dataset now forces an enum update (test fails otherwise) — this is
  the intended safety net. Document it in `AGENTS.md §5` "add a dataset" checklist as a follow‑up.
- Reviewer should confirm no contract test regressed (the four new datasets need
  `contracts/datasets/{id}.schema.json` to exist).
