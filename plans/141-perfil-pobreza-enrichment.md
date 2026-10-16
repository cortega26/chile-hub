# Plan 141: Enrich perfil_territorial_comunal with pobreza (spike empresas)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat bd77d34..HEAD -- src/builders/datasets.py src/builders/inputs.py src/builders/metadata.py src/validation/_territorio.py data/dataset_catalog_config.json data/dataset_specs/perfil_territorial_comunal.json docs/datasets/perfil_territorial_comunal.md contracts/datasets/perfil_territorial_comunal.schema.json`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Amendment 2026-10-15 (lesson from Plans 143/139)**: `data/dataset_specs/perfil_territorial_comunal.json` exists and SHADOWS the legacy catalog/registry entries at render time (`catalog_config_with_spec_overlay`, `source_registry_with_spec_overlay`). It carries `source.upstream_datasets` (12 today) and `documentation.description`. Any Step-2 change must be applied to the spec AND the legacy JSONs together, keeping Phase-2 equivalence tests green. The pobreza lane's own spec/contract need no change (only perfil's).

## Status

- **Priority**: P2
- **Effort**: S (pobreza join) + spike (empresas density, no build)
- **Risk**: LOW
- **Depends on**: none (coordinate with 139/140 only on docs wording; no shared files)
- **Category**: direction
- **Planned at**: commit `bd77d34`, 2026-10-15

## Why this matters

`perfil_territorial_comunal` is the flagship one-row-per-comuna API feeding the flagship notebook (archived plan 060), the 347 comuna pages (plan 105), and the landing map. It already consolidates 12 upstreams (censo, salud, educación, finanzas, SIEDU, vitales, permisos, calidad) but omits `pobreza_comunal` — a 690-row, CUT-keyed, stable lane that joins trivially. Adding the latest poverty rate per comuna makes the profile answer the most-asked territorial question ("where is poverty concentrated?") without any new extraction. `empresas` density is the natural follow-up but its join key is free-text `comuna_tributaria`, so it stays a spike with a methodology note, not a silent join.

## Current state

Relevant files and roles:

- `src/builders/datasets.py:91-104` — `build_perfil_territorial_comunal(df_comunas, df_censo, df_censo_hogares, df_salud, df_educacionales, df_electoral, df_finanzas, df_resultados, df_siedu, df_vitales=None, df_permisos=None, df_calidad=None)` — no `df_pobreza` parameter today.
- `src/builders/datasets.py:145-155` — `siedu_summary` + `_latest_vitales_summary/_latest_permisos_summary/_latest_calidad_summary` pattern: each upstream is reduced to latest-year-per-comuna then left-joined. `pobreza` should follow this exact pattern.
- `src/builders/datasets.py:157-195` — left-join chain from `df_comunas` outward; missing-value policy is nullable columns (see `:196-210` vitales/permisos/calidad `None` branches that add `pl.lit(None)` columns).
- `src/builders/inputs.py:26,264` — `build_perfil_territorial_comunal` wired in `_load_inputs`/`required_frames["perfil_territorial"]`; adding an upstream means threading it here.
- `src/validation/_territorio.py:89-113` — `validate_perfil_territorial_comunal`: expects 346 communes, unique `codigo_comuna`, no unknown communes, no duplicate columns. New columns must not violate these.
- Verified counts (2026-10-15): `perfil_territorial_comunal.parquet` has 49 columns (list ends with `mp25_promedio_ultimo_anio, anio_calidad_aire`) and **no poverty column**; `pobreza_comunal.parquet` has **690 rows** (= 345 comunas × 2 dimensions for the latest year, SAE methodology with `tasa, limite_inferior, limite_superior`).
- `data/dataset_catalog_config.json:521-552` — pobreza entry: `join_keys: [codigo_comuna, codigo_region]`, PK `(codigo_comuna, anio, dimension)`, dimensions `ingresos` / `multidimensional`. `data/dataset_catalog_config.json:488-519` — empresas entry: join key is `rut`, location is free-text `comuna_tributaria` (e.g. `"SANTIAGO"`), explicitly documented as Parquet-first (`>1.5M registros, no JSON/SQLite`).
- Registry `perfil_territorial_comunal` upstream list (`data/source_registry.json:303-316`) names 12 upstreams and does not include `pobreza_comunal` or `empresas`.

Conventions that apply:

- Builder pattern exemplar: `_latest_vitales_summary` / `_latest_permisos_summary` in `src/builders/datasets.py` — reduce to `(codigo_comuna, value, anio)` then left-join; nullable when upstream missing. Match it exactly for pobreza.
- Column naming: Spanish `snake_case` (`AGENTS.md §7`): e.g. `tasa_pobreza_ingresos_ultimo_anio`, `anio_pobreza`, following `crecimiento_natural_ultimo_anio / anio_estadisticas_vitales` precedent.
- CUT types: `codigo_comuna` stays `pl.String` length 5 throughout.
- Contract + doc companion rule (`check_companion_paths.py registry` + `AGENTS.md §12`): schema `contracts/datasets/perfil_territorial_comunal.schema.json` and `docs/datasets/perfil_territorial_comunal.md` schema block (auto-synced via `doc_sync.py`) must be updated together with the builder.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Perfil columns | `./.venv/bin/python -c "import polars as pl; print(pl.read_parquet('data/normalized/perfil_territorial_comunal.parquet').columns)"` | executed | 49 columns, no `pobreza`/`tasa_pobreza` entry (pre-change) |
| Pobreza shape | `./.venv/bin/python -c "import polars as pl; df=pl.read_parquet('data/normalized/pobreza_comunal.parquet'); print(df.height, df.select('anio').unique().sort('anio').to_series().to_list(), df.select('dimension').unique().to_series().to_list())"` | executed | `690`, latest year list, `['ingresos','multidimensional']` |
| Focal tests | `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "erfil or obreza"` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `src/builders/datasets.py` (add pobreza summary + join + null-branch)
- `src/builders/inputs.py` (thread `df_pobreza` through)
- `src/builders/metadata.py` (`_metadata_perfil_territorial` fields, if it enumerates columns)
- `src/validation/_territorio.py` (extend perfil validator only for new-column sanity — no hardening beyond nullability + range 0–100)
- `data/dataset_specs/perfil_territorial_comunal.json` (render-effective copy: `source.upstream_datasets` 12→13 + `source.next_action` note; `documentation.description` only if it enumerates upstream columns)
- `data/source_registry.json` (perfil `upstream_datasets`/`next_action` — same rule as the spec: legacy edited together with spec, Phase-2 equivalence enforces it)
- `contracts/datasets/perfil_territorial_comunal.schema.json` + `docs/datasets/perfil_territorial_comunal.md` (companion updates, kept identical to the spec projection)
- `tests/test_pipeline_logic.py` and/or `tests/test_validation.py` (new join + validator tests)
- `plans/README.md` (status row only)

**Out of scope** (do NOT touch, even though they look related):

- `empresas` join implementation — spike only (methodology note + match-rate measurement, no builder change).
- Any change to the pobreza extractor, poverty methodology, or SAE intervals.
- `perfil` consumers (notebook 060, comuna pages, landing map) — they inherit new columns automatically; no consumer rewrite here.
- `finanzas_municipales`, `geometria_comunal`, or any other upstream.

## Git workflow

- Branch: `advisor/141-perfil-pobreza`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `feat(perfil): add latest SAE poverty rates to perfil_territorial_comunal`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Run the perfil-columns and pobreza-shape commands; record outputs. Run focal tests + `make doctor`.

**Verify**: perfil has no poverty column; pobreza is 690 rows with the two dimensions; tests + doctor green.

### Step 1: Add pobreza latest-year summary + left join

1. Add a `_latest_pobreza_summary(df_pobreza)` helper in `src/builders/datasets.py` next to the vitales/permisos/calidad helpers: for the max `anio` present, pivot/select one row per `codigo_comuna` with `tasa_pobreza_ingresos`, `tasa_pobreza_multidimensional` (plus `limite_inferior/superior` for each dimension if the schema review approves — default to rates + `anio_pobreza` only to keep the profile narrow), and `metodologia` constant `"SAE"`.
2. Thread `df_pobreza=None` parameter through `build_perfil_territorial_comunal()` and its caller in `src/builders/inputs.py:264` (mirror how `df_vitales/df_permisos/df_calidad` are optional-threaded).
3. Left-join on `codigo_comuna`; add the `None`-branch (`pl.lit(None)` columns) mirroring `:196-210` so a missing pobreza frame never breaks the build.
4. Column names must follow the `*_ultimo_anio` + `anio_*` precedent.

**Verify**: `./.venv/bin/pytest tests/test_pipeline_logic.py -q -k "erfil"` → pass; manual `python -c` join check shows 346 perfil rows still (no fan-out) and new columns nullable.

### Step 2: Metadata + contract + docs companions

1. Update `_metadata_perfil_territorial` if it lists fields explicitly; otherwise confirm it derives from `dfs["perfil_territorial"].columns` (read `src/builders/metadata.py:473-509` first).
2. Update the perfil schema contract + doc schema block together AND the spec (`source.upstream_datasets` 12→13 with `pobreza_comunal`, `source.next_action` noting the addition; `documentation.description` only if it names upstream columns). Then run `make doctor` (includes `sync_docs --check` AND the Phase-2 legacy≡spec equivalence tests via `pytest tests/test_phase2_datasetspec.py -q`, which must stay green — the 143/139 lesson: spec and legacy edited together or not at all).
3. Extend `validate_perfil_territorial_comunal` minimally: new columns nullable; when present, `0 <= tasa <= 100`. No new hard-fail beyond the existing 346-row/uniqueness gates.

**Verify**: `make doctor` → exit 0; focal validation tests pass.

### Step 3: Empresas density spike (no build change)

Measure, don't implement: (1) match rate of `empresas.comuna_tributaria` free-text against `comunas.nombre_comuna_clean` via the existing `normalize_comuna_name()` helper (`src/chile_hub/text.py`) — report matched/unmatched counts + top-20 unmatched values; (2) state the methodology caveat (tributary commune ≠ physical location; RES is Ley 20.659 simplified-regime only since 2013); (3) recommend include vs defer with one paragraph. Write the spike note into the perfil doc appendix or the plan report — no builder change.

**Verify**: spike note with numbers exists; `git diff --name-only` shows no `datasets.py` change from this step.

### Step 4: Full verification

Run `make test` + `make doctor` + `make lint && make format-check`. Do NOT run `make build` unless the plan's own test demands it (the builder change is covered by unit tests with synthetic frames per `test_phase1_characterization.py` pattern).

**Verify**: all green; `git diff --name-only bd77d34...HEAD` lists only in-scope files.

## Test plan

- New unit tests (model after `test_phase1_characterization.py` synthetic-staging pattern): pobreza summary picks max year; perfil join preserves 346 rows with nulls when pobreza missing; validator accepts null poverty but rejects `tasa > 100`.
- Spike evidence: empresas match-rate numbers quoted in the test/docstring or spike note (not asserted as a gate).
- Verification: focal pytest → pass including new tests; `make test` → verde.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] Perfil parquet schema (post-build, when eventually rebuilt) includes `tasa_pobreza_ingresos_ultimo_anio` (or approved equivalent) + `anio_pobreza`, nullable
- [ ] Builder + inputs thread `df_pobreza` with a `None`-safe branch (no build break when upstream missing)
- [ ] Validator extended only for nullability + 0–100 range; existing 346/uniqueness gates intact
- [ ] Contract + doc companions updated; `make doctor` exits 0
- [ ] Empresas spike note with match-rate + recommendation exists; no empresas builder change
- [ ] `make test` verde; `make lint && make format-check` exit 0
- [ ] `git diff --name-only bd77d34...HEAD` lists only in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Pobreza latest year has <340 comunas covered (coverage assumption void — the profile would inherit a hole; report instead of filling with backfill).
- The pobreza `(codigo_comuna, anio, dimension)` grain differs from Current state (e.g. new dimension values appear).
- Joining pobreza fans out perfil beyond 346 rows (grain error — do not deduplicate by guessing; report).
- `empresas` match rate is so low the density column would mislead (>10% unmatched) — record as defer, do not implement.

## Maintenance notes

- When the next CASEN round publishes (registry `review_by: 2027-06-30`, `next_action: monitorear próxima ronda`), the summary automatically picks the new max year; the `anio_pobreza` column makes the rollover visible. Reviewer should check the year bump in the first build after a CASEN release.
- Reviewer should scrutinize: column-name consistency with the `*_ultimo_anio` family, null-branch parity, and that the validator was not hardened into a hard-fail on poverty absence.
- **Deferred:** `empresas` density column — unblocked by a methodology decision on tributary-vs-physical commune + free-text match quality.
- **Deferred:** poverty confidence-interval columns — include only if a consumer (notebook/pages) actually renders uncertainty; otherwise rates + year suffice.
