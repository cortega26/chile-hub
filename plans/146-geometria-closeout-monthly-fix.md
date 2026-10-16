# Plan 146: Close-out geometria decision (C) + monthly rebuild one-liner

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- data/source_registry.json data/dataset_specs/geometria_comunal.json .github/workflows/monthly-scrape.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Origin**: maintainer accepted option (C) from Plan 145 on 2026-10-15 — keep geometria candidate, no 139 merge. This plan executes the two resulting micro-changes. Plan 139 stays BLOCKED as the historical record.

## Status

- **Priority**: P1 (touches the monthly publish path)
- **Effort**: S
- **Risk**: LOW (2 small hunks; monthly job itself is the final gate and only runs on schedule)
- **Depends on**: 145 (decision (C))
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

Part 1 closes the decision loop: the registry still pressures with `review_by: 2026-10-21`, which will read overdue without an explicit condition. Part 2 fixes the probable cause of the 2026-10-01 monthly failure: the rebuild step runs bare `python` (setup-python interpreter, no project deps) while every other step in the same job uses `uv run` after `uv sync --extra pipeline --extra dev`. Both are one-hunk changes with maintainer approval already given.

## Current state

- `data/source_registry.json` geometria entry + `data/dataset_specs/geometria_comunal.json` `source.*`: `review_by: 2026-10-21`, `next_action: "Cobertura 345/346 (falta codigo_comuna=12202/Antártica, hueco conocido de la fuente BCN — ver ADR-012). Evaluar promoción a stable_publishable una vez confirmada cadencia de refresco y estabilidad del endpoint ArcGIS (region 12/Magallanes requiere fallback comuna-por-comuna por payload combinado grande)."` (Triple-copy rule from Plans 143/139: spec is render-effective; legacy kept identical; Phase-2 equivalence tests enforce it.)
- `.github/workflows/monthly-scrape.yml`: `:43` setup-python, `:48` setup-uv, `:55` `uv sync --extra pipeline --extra dev`, extract step uses `uv run python src/extractors/sinim_finanzas_live_extractor.py`, but "Rebuild normalized artifacts" runs bare `python src/build_dev_db.py`. No `requirements.txt`/venv activation anywhere in the job — bare `python` cannot import polars/duckdb → instant failure, matching the 2026-10-01 symptom (scrape OK, rebuild failed).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Focal tests | `./.venv/bin/pytest tests/test_phase2_datasetspec.py tests/test_ci_config.py -q` | declared | all pass |
| YAML parse | `./.venv/bin/python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/monthly-scrape.yml'))" 2>/dev/null \|\| python3 -c "import yaml; yaml.safe_load(open('.github/workflows/monthly-scrape.yml')); print('yaml ok')"` | declared | parses (use whichever interpreter has pyyaml; report which) |
| Doctor | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `data/dataset_specs/geometria_comunal.json` (`source.review_by`, `source.next_action`)
- `data/source_registry.json` (geometria `review_by`, `next_action` — identical to spec)
- `.github/workflows/monthly-scrape.yml` (one line: `uv run python src/build_dev_db.py`)
- `plans/README.md` (status row only — SKIP per dispatcher override; reviewer owns the index)

**Out of scope**: everything else — no extractor/builder/contract/doc change, no other workflow, no schedule change, no 139-branch touch.

## Git workflow

- Branch: `advisor/146-geometria-closeout`
- One commit per part; message style `tipo(scope): mensaje`.
- Do NOT push.

## Steps

### Step 0: Establish a green baseline

Drift check + focal tests + `make doctor` on the unmodified tree.

**Verify**: no drift; tests + doctor green.

### Step 1: (C) close-out — review_by + condition (triple-copy)

In BOTH `data/dataset_specs/geometria_comunal.json` (`source.*`) and `data/source_registry.json` (geometria entry), set identically:

- `review_by: "2026-12-31"`
- `next_action: "Capa candidata (decisión 2026-10-15, planes 139/145): 345/346 comunas (Antártica codigo_comuna=12202 ausente aguas arriba en la fuente BCN, ver ADR-012). Promover a stable_publishable solo con ingestión en build_dev_db.py + dueño de cadencia de refresco + contrato en partial_expected. Refresco actual: manual vía geometria-comunal.yml."`

Do NOT touch description, track, maturity, eligibility, outputs, or anything else.

**Verify**: `./.venv/bin/pytest tests/test_phase2_datasetspec.py -q` → all pass (equivalence holds); `make doctor` → exit 0.

### Step 2: Monthly rebuild one-liner

Change exactly one line in `.github/workflows/monthly-scrape.yml` ("Rebuild normalized artifacts" step): `python src/build_dev_db.py` → `uv run python src/build_dev_db.py`. Then: YAML parses; `grep -n "uv run\|^ *python " .github/workflows/monthly-scrape.yml` shows no remaining bare-`python` run step in this job (report any other bare occurrence found — do NOT fix beyond this one line; report it).

**Verify**: YAML parses; focal tests pass; `make doctor` → exit 0; `make lint && make format-check` → exit 0 (yaml is not linted by ruff — doctor + parse suffice).

## Test plan

No new tests (both hunks are covered by existing gates: phase2 equivalence for Part 1; the monthly job itself is the Part-2 gate and runs only on schedule — state this explicitly in the report). Focal suites + doctor + parse + lint.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] Spec + registry geometria `review_by == 2026-12-31`, identical `next_action` with the explicit promotion condition
- [ ] Nothing else in either JSON entry changed (track/maturity/eligibility/outputs/description untouched)
- [ ] Workflow rebuild step uses `uv run python`; YAML parses
- [ ] `tests/test_phase2_datasetspec.py` + `tests/test_ci_config.py` green; `make doctor`, `make lint`, `make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only the 3 in-scope files
- [ ] Report states clearly: Part-2 proof awaits the next scheduled monthly run (1 Nov 2026); the 2026-10-01 attribution is probable-cause, not proven

## STOP conditions

Stop and report back (do not improvise) if:

- The registry/spec geometria entries differ from Current state (drift).
- The workflow's Python setup differs from Current state (e.g. a venv activation exists that makes bare `python` correct after all — report, do not "fix" a working setup).
- Any verification fails twice after a reasonable fix attempt.

## Maintenance notes

- The 2026-12-31 review must not slip silently a second time: if (A) is still unfunded then, the condition text already says what is missing — just re-date or fund it.
- Reviewer should scrutinize: byte-identical next_action in both copies, and that the workflow diff is exactly one line.
- **Deferred:** (A) pipeline ingestion — specified in Plan 145 NOTES, unblocked only by maintainer funding + refresh ownership.
