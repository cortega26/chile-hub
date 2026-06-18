# Plan 009: Separate Stable Publishable and Candidate Dataset Tracks

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the next
> step. If anything in the "STOP conditions" section occurs, stop and report
> instead of improvising. When done, update the status row for this plan in
> `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat 91d3caa..HEAD -- data/source_registry.json scripts/verify_pipeline.py src/build_dev_db.py tests/test_pipeline_logic.py tests/test_chile_hub.py Makefile plans/README.md`
>
> If any in-scope implementation file changed since this plan was written,
> compare the "Current state" excerpts against the live code before proceeding.
> If the relevant APIs or file layout no longer match, treat it as a STOP
> condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: implemented parts of `plans/008-hardening-source-readiness-schema-contracts-quality.md` (`data/source_registry.json`, schema contracts, and registry verification already exist in commit `91d3caa`)
- **Category**: data-quality / architecture / dx
- **Planned at**: commit `91d3caa`, 2026-06-18

## Why this matters

`make verify-live` currently treats every dataset in the catalog as if it must be
production-ready. That is too blunt: it either blocks the whole project on known
candidate layers, or tempts maintainers to lower the publication gate. Do not
lower the gate.

The professional fix is to make dataset maturity explicit. Stable publishable
datasets must be live, fresh, and safe for publication. Candidate datasets may
exist in local/dev builds and documentation, but must be excluded from the public
ZIP and must not be represented as production-ready until their live extractors
are stable.

This plan implements that split first. It intentionally does not "forgive"
`indicadores` when it uses unsafe `raw_recovery`; a stable publishable indicator
dataset must still pass the strict existing rules: live delivery or an explicitly
allowed `published_backfill`, never raw recovery in a publication build.

## Current state

The current failure mode to address:

- `finanzas_municipales` is `source_mode=fallback`.
- `resultados_educacionales` is `source_mode=fallback`.
- `indicadores_urbanos_siedu` is `source_mode=fallback`.
- `perfil_territorial_comunal` is derived and inherits the worst upstream state,
  so it also becomes fallback while it depends on candidate fallback layers.
- `indicadores` can fail strict publication when `mindicador.cl` times out and
  UF or another code is filled via `raw_recovery`.

Important existing files:

- `data/source_registry.json` declares current source readiness. It already marks
  `finanzas_municipales`, `resultados_educacionales`,
  `indicadores_urbanos_siedu`, and `perfil_territorial_comunal` as
  `maturity_status="candidate"` and `live_ready=false`.
- `scripts/verify_pipeline.py` validates the source registry and implements
  `verify_publication_policy()`.
- `src/build_dev_db.py` builds the artifact manifest, public ZIP, hub bundle, and
  generated catalog/status artifacts.
- `tests/test_pipeline_logic.py` has focused unit tests for publication policy
  and source registry behavior.
- `tests/test_chile_hub.py` has integration assertions for manifest, ZIP, bundle,
  CLI, and Makefile behavior.

Current source registry excerpts:

```text
data/source_registry.json:163-176
{
  "source_id": "sinim_finanzas_municipales",
  "dataset": "finanzas_municipales",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Configure stable direct SINIM export and replace curated fallback rows."
}

data/source_registry.json:179-192
{
  "source_id": "mineduc_resultados_educacionales",
  "dataset": "resultados_educacionales",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Replace curated fallback with stable official aggregate export."
}

data/source_registry.json:195-208
{
  "source_id": "ine_siedu_indicadores",
  "dataset": "indicadores_urbanos_siedu",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Replace partial fallback with stable official SIEDU export."
}

data/source_registry.json:211-224
{
  "source_id": "chile_hub_perfil_territorial",
  "dataset": "perfil_territorial_comunal",
  "access_method": "derived",
  "live_extractor_status": "derived",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Track readiness inherited from upstream component datasets."
}
```

Current strict policy excerpt:

```text
scripts/verify_pipeline.py:266-309
def verify_publication_policy(metadata=None):
    if metadata is None:
        metadata = load_json(NORMALIZED_DIR / "pipeline_metadata.json")

    violations = []
    for dataset_name in sorted(REQUIRED_DATASETS):
        dataset = metadata.get("datasets", {}).get(dataset_name, {})
        freshness = dataset.get("freshness", {})
        if dataset.get("source_mode") != "live":
            violations.append(f"{dataset_name}: source_mode={dataset.get('source_mode')}")
        if freshness.get("status") != "fresh":
            violations.append(f"{dataset_name}: freshness={freshness.get('status')}")

    indicadores = metadata.get("datasets", {}).get("indicadores", {})
    allowed_indicator_source_details = {
        "public_api",
        "public_api_with_published_backfill",
    }
    if indicadores.get("source_detail") not in allowed_indicator_source_details:
        violations.append(f"indicadores: source_detail={indicadores.get('source_detail')}")
    failed_diagnostics = {
        field: indicadores.get(field, [])
        for field in (
            "fetch_failures",
            "raw_recoveries",
            "preserved_existing_pairs",
            "empty_live_pairs",
        )
        if indicadores.get(field)
    }
    if failed_diagnostics:
        violations.append(f"indicadores: recovery diagnostics={failed_diagnostics}")
```

Current bundle/manifest behavior:

```text
src/build_dev_db.py:887-1009
def build_publishable_artifact_index():
    artifact_index = {}
    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        outputs = config.get("outputs", {})
        for output_type, path in outputs.items():
            if isinstance(path, str) and path.startswith("data/normalized/"):
                artifact_index[path] = {
                    "dataset": dataset_name,
                    "output_type": output_type,
                }
...
def write_artifact_manifest():
    artifact_index = build_publishable_artifact_index()
    artifacts = []
    for filename in sorted(os.listdir(NORMALIZED_DIR)):
        if not filename.endswith(PUBLISHABLE_ARTIFACT_SUFFIXES):
            continue
...
        artifacts.append(
            {
                "path": relative_path,
                "dataset": artifact_metadata.get("dataset"),
                "output_type": artifact_metadata.get("output_type"),
                "shared_type": artifact_metadata.get("shared_type"),
                "format": artifact_metadata.get("format"),
                "size_bytes": os.path.getsize(path),
                "sha256": compute_sha256(path),
            }
        )
```

```text
src/build_dev_db.py:1430-1460
for dataset in dataset_catalog.get("datasets", []):
    dataset_name = dataset["dataset"]
    dataset_health = health_by_dataset.get(dataset_name, {})
    bundle["datasets"].append(
        {
            "dataset": dataset_name,
            ...
            "publishability_status": dataset_health.get("publishability_status"),
            "outputs": dataset.get("outputs", {}),
            "usage_examples": dataset.get("usage_examples", {}),
            "artifacts": artifacts_by_dataset.get(dataset_name, []),
        }
    )
```

This means the public artifact list and public bundle are currently driven by
generated files and catalog outputs, not by an explicit publication track.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Build artifacts | `make build` | exits 0; regenerates `data/normalized/*` |
| Dev verification | `make verify` | exits 0; allows declared candidate fallback layers |
| Focused tests | `make test` | all tests pass |
| Lint | `make lint` | exits 0 |
| Format check | `make format-check` | exits 0 |
| Strict publication gate | `make verify-live` | exits 0 only when all `stable_publishable` datasets are live/fresh and `indicadores` has no unsafe recovery diagnostics |
| Package checksum | `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256` | prints `OK` |

If `make verify-live` fails only because `indicadores` used `raw_recovery` after
a transient `mindicador.cl` timeout, that is a correct strict failure. Do not
relax it in this plan.

## Scope

**In scope**:

- `data/source_registry.json`
- `scripts/verify_pipeline.py`
- `src/build_dev_db.py`
- `tests/test_pipeline_logic.py`
- `tests/test_chile_hub.py`
- generated `data/normalized/*` artifacts produced by `make build`
- `plans/README.md` status update after execution

**Out of scope**:

- Replacing the SINIM, MINEDUC outcomes, or SIEDU fallback extractors with stable
  live extractors.
- Promoting any candidate dataset to public/stable without a real live extractor
  and fresh successful run.
- Allowing `raw_recovery`, `preserved_existing`, `empty_live`, or partial
  indicator delivery in strict publication.
- Renaming dataset IDs or removing candidate datasets from dev/local outputs.
- Changing public response schemas unrelated to publication readiness.
- Lowering `make verify-live` expectations to get a green build.

## Git workflow

- Branch: `advisor/009-split-stable-publishable-candidate-tracks`
- Commit style in recent history is conventional commits, for example
  `feat: improve hub usability and validation gates`. Use a single commit such
  as `feat: split publishable and candidate dataset tracks` unless the operator
  asks for smaller commits.
- Do not push or open a PR unless the operator explicitly instructs it.

## Steps

### Step 1: Add explicit publication track fields to `data/source_registry.json`

Add two fields to every registry entry:

```json
"publication_track": "stable_publishable",
"public_bundle_eligible": true
```

Allowed values:

- `publication_track`: `stable_publishable` or `candidate`
- `public_bundle_eligible`: boolean

Initial values:

| Dataset | publication_track | public_bundle_eligible | Reason |
|---|---|---:|---|
| `regiones` | `stable_publishable` | `true` | live stable BCN source |
| `provincias` | `stable_publishable` | `true` | live stable BCN source |
| `comunas` | `stable_publishable` | `true` | live stable BCN + INE reference source |
| `comunas_enriquecidas` | `stable_publishable` | `true` | derived from stable `comunas` |
| `indicadores` | `stable_publishable` | `true` | stable source, but strict policy must still reject unsafe recovery |
| `censo_comunal` | `stable_publishable` | `true` | stable direct official source |
| `censo_hogares_viviendas` | `stable_publishable` | `true` | stable direct official source |
| `establecimientos_salud` | `stable_publishable` | `true` | stable direct source; fallback blocked for publication |
| `distritos_electorales` | `stable_publishable` | `true` | stable legal reference source |
| `establecimientos_educacionales` | `stable_publishable` | `true` | stable official source; fallback blocked for publication |
| `empresas` | `stable_publishable` | `true` | stable official datos.gob.cl source |
| `finanzas_municipales` | `candidate` | `false` | fallback-only SINIM candidate |
| `resultados_educacionales` | `candidate` | `false` | fallback-only MINEDUC outcomes candidate |
| `indicadores_urbanos_siedu` | `candidate` | `false` | fallback-only/partial SIEDU candidate |
| `perfil_territorial_comunal` | `candidate` | `false` | derived layer inherits non-publicable upstreams |

For `perfil_territorial_comunal`, also add:

```json
"upstream_datasets": [
  "comunas",
  "censo_comunal",
  "censo_hogares_viviendas",
  "establecimientos_salud",
  "establecimientos_educacionales",
  "distritos_electorales",
  "finanzas_municipales",
  "resultados_educacionales",
  "indicadores_urbanos_siedu"
]
```

Do not use `maturity_status="stable"` for `perfil_territorial_comunal` until all
upstream candidate datasets it depends on are promotable.

**Verify**: `python -m json.tool data/source_registry.json >/tmp/source_registry.check` exits 0.

### Step 2: Strengthen registry verification

Update `verify_source_registry()` in `scripts/verify_pipeline.py` to validate the
new fields.

Rules:

- Every registry entry must have `publication_track` and
  `public_bundle_eligible`.
- `publication_track` must be either `stable_publishable` or `candidate`.
- `public_bundle_eligible` must be a boolean.
- `publication_track="stable_publishable"` requires:
  - `public_bundle_eligible is True`
  - `maturity_status == "stable"`
  - `live_ready is True`
  - `live_extractor_status != "fallback_only"`
- `publication_track="candidate"` requires:
  - `public_bundle_eligible is False`
  - `maturity_status == "candidate"` unless the dataset is explicitly
    `experimental` or `deprecated`
  - `fallback_policy == "allowed_for_dev_blocked_for_publication"` when
    `fallback_allowed is True`
- `live_extractor_status="fallback_only"` must always imply
  `publication_track="candidate"` and `public_bundle_eligible is False`.
- `access_method="derived"` entries with `upstream_datasets` must inherit
  non-publicable status: if any upstream registry entry is candidate or
  `public_bundle_eligible=false`, the derived dataset must also be candidate and
  ineligible.
- No source-backed candidate may be publishable just because its current build
  happened to be fresh.

Add tests in `tests/test_pipeline_logic.py`:

- Accept a minimal stable publishable registry entry.
- Accept a candidate fallback-only registry entry.
- Reject a `fallback_only` entry with `publication_track="stable_publishable"`.
- Reject a candidate entry with `public_bundle_eligible=true`.
- Reject a derived entry whose upstream is candidate but whose own track is
  `stable_publishable`.

Model these tests after existing source registry tests at
`tests/test_pipeline_logic.py:230-293`.

**Verify**: `make test` exits 0.

### Step 3: Make publication policy use the registry/readiness track

Change `verify_publication_policy()` so it evaluates only stable publishable
datasets for strict live/fresh requirements, while also enforcing that candidate
datasets are not present in the public package.

Recommended shape:

```python
def stable_publishable_dataset_names(registry):
    return {
        entry["dataset"]
        for entry in registry
        if entry.get("publication_track") == "stable_publishable"
        and entry.get("public_bundle_eligible") is True
    }
```

Then:

- Load `data/source_registry.json` when `verify_publication_policy()` is called
  without injected test data.
- Permit tests to inject a registry argument, e.g.
  `verify_publication_policy(metadata, registry=registry, manifest=manifest)`.
- For each stable publishable dataset, require:
  - metadata exists
  - `source_mode == "live"`
  - `freshness.status == "fresh"`
  - if registry `fallback_policy` is `allowed_for_dev_blocked_for_publication`,
    any current fallback metadata is still a violation
- For each candidate dataset, do not require live/fresh in `verify-live`, but
  require it to be absent from the public manifest/ZIP artifact list if a
  manifest is available.
- Keep the existing `indicadores` strict checks for:
  - `source_detail` in `{"public_api", "public_api_with_published_backfill"}`
  - empty `fetch_failures`
  - empty `raw_recoveries`
  - empty `preserved_existing_pairs`
  - empty `empty_live_pairs`
  - every `indicator_delivery` value in `{"live", "published_backfill"}`
- Only apply the `indicadores` strict checks while `indicadores` is on the
  `stable_publishable` track. It should remain on that track in this plan.

Update or replace current publication policy tests at
`tests/test_pipeline_logic.py:100-160`:

- Stable publishable live/fresh metadata passes.
- Candidate fallback metadata passes policy only when candidate artifacts are
  absent from the injected manifest.
- Candidate fallback metadata fails policy when its artifact appears in the
  injected manifest.
- A stable publishable dataset in fallback still fails.
- `indicadores` with `raw_recoveries` still fails even if all candidate datasets
  are excluded.

**Verify**: `make test` exits 0.

### Step 4: Exclude candidate dataset artifacts from the public manifest and ZIP

Update `src/build_dev_db.py` so `write_artifact_manifest()` includes dataset
artifacts only when their registry entry is `public_bundle_eligible=true`.

Implementation guidance:

- Add a small loader/helper in `src/build_dev_db.py`, or reuse an existing JSON
  loader if present, to read `data/source_registry.json`.
- Build a lookup by dataset:

```python
registry_by_dataset = {
    entry["dataset"]: entry
    for entry in load_source_registry()
}
```

- When building the artifact index, annotate dataset artifacts with:
  - `publication_track`
  - `public_bundle_eligible`
- When writing the manifest, skip candidate dataset artifacts. Do not skip shared
  reports such as `dataset_catalog.json`, `hub_health.json`, or
  `provenance_report.json`; those reports may mention candidates, but candidate
  data files must not be packaged as production artifacts.
- Avoid accidentally including unknown dataset files as shared artifacts. If a
  `data/normalized/*` file has a publishable suffix and looks like a dataset
  output but is not in the artifact index, fail loudly or exclude it with a
  warning. Do not silently package unclassified dataset files.

The generated public ZIP is created from `artifact_manifest.json` at
`src/build_dev_db.py:1468-1505`, so once the manifest excludes candidate data
artifacts, the ZIP should exclude them automatically.

Tests to add or update:

- In `tests/test_pipeline_logic.py`, add a unit test around the manifest helper
  if it can be isolated without running the full build.
- In `tests/test_chile_hub.py`, update manifest/ZIP assertions so candidate
  dataset artifact paths are absent from `artifact_manifest.json` and from
  `chile-hub-publishable-bundle.zip`.
- Keep assertions that shared reports remain present in the ZIP:
  `data/normalized/hub_bundle.json`,
  `data/normalized/artifact_manifest.json`, and other required reports.

**Verify**: `make build && make verify && make test` exits 0.

### Step 5: Make `hub_bundle.json` clearly separate public datasets from candidates

Update `write_hub_bundle_json()` in `src/build_dev_db.py`.

Required behavior:

- `bundle["datasets"]` contains only datasets with
  `publication_track="stable_publishable"` and `public_bundle_eligible=true`.
- Candidate datasets are not listed in `bundle["datasets"]` and have no
  candidate data artifacts attached.
- Add a separate top-level `bundle["candidate_datasets"]` list with compact
  metadata for transparency:
  - `dataset`
  - `maturity_status`
  - `publication_track`
  - `public_bundle_eligible`
  - `source_mode`
  - `source_detail`
  - `freshness`
  - `next_action` from registry
  - `upstream_datasets` when present
- Add `bundle["public_dataset_count"]` and `bundle["candidate_dataset_count"]`.
- Keep `dataset_catalog.json` as the full catalog. Candidate entries in the
  catalog must carry clear metadata:
  `maturity_status="candidate"`, `publication_track="candidate"`,
  `public_bundle_eligible=false`, and a warning/next action.

Tests to update:

- `tests/test_chile_hub.py` currently expects `bundle["dataset_count"]` and
  `len(bundle["datasets"])` to equal the full catalog count. Replace that with:
  - `bundle["dataset_count"]` can remain the full catalog count for backward
    context, or be renamed only if all downstream tests/CLI expectations are
    updated deliberately.
  - `bundle["public_dataset_count"] == len(bundle["datasets"])`.
  - every `bundle["datasets"]` entry is stable publishable.
  - every known candidate appears in `bundle["candidate_datasets"]`.
  - no candidate `outputs` or candidate `artifacts` appear under
    `bundle["datasets"]`.

If maintaining backward compatibility is important, prefer keeping
`dataset_count` as the full catalog count and adding the two new explicit counts
instead of changing the meaning of `dataset_count`.

**Verify**: `make build && make verify && make test` exits 0.

### Step 6: Preserve dev green while making publication green meaningful

Run:

```sh
make build
make verify
make test
make lint
make format-check
```

Expected result: all exit 0.

Then run:

```sh
make verify-live
```

Expected result after this plan:

- It must not fail because `finanzas_municipales`,
  `resultados_educacionales`, `indicadores_urbanos_siedu`, or
  `perfil_territorial_comunal` are fallback, as long as they are candidate and
  excluded from the public manifest/ZIP.
- It must still fail if any stable publishable dataset is fallback or stale.
- It must still fail if `indicadores` has `raw_recoveries`, `fetch_failures`,
  `preserved_existing_pairs`, `empty_live_pairs`, partial delivery, or any
  `indicator_delivery` value outside `live` / `published_backfill`.

If `make verify-live` fails due only to a live `mindicador.cl` timeout causing
`indicadores` raw recovery, do not edit the strict policy to pass. Record that
as the next operational issue: improve retry/backoff or rerun when the public
API is available.

**Verify**:

- `make verify` exits 0.
- `make verify-live` exits 0 only when strict stable publishable data is truly
  publication-safe.

### Step 7: Document the candidate backlog as follow-up work

Do not solve the three candidate extractors in this plan. Add a short maintenance
note in code comments only if needed, and ensure generated catalog/report
metadata exposes these next actions:

- `finanzas_municipales`: find a stable SINIM/SUBDERE endpoint or direct export;
  otherwise remain `candidate`, non-publicable.
- `resultados_educacionales`: replace curated fallback with a stable official
  MINEDUC aggregate dump/export.
- `indicadores_urbanos_siedu`: configure a stable official SIEDU download; if
  only partial coverage is available, keep it candidate and clearly mark partial
  coverage.
- `perfil_territorial_comunal`: promote only after its non-publicable upstreams
  become stable publishable, because it inherits the worst upstream state.
- `indicadores`: improve retry/backoff for `mindicador.cl`, but keep strict
  publication rules limited to live or `published_backfill`.

If the operator wants, these can become separate future plans 010-013.

**Verify**: `make build && make verify` exits 0 and `data/normalized/dataset_catalog.json`
contains the candidate next actions.

## Test plan

Add or update tests for:

- Registry accepts explicit `stable_publishable` and `candidate` tracks.
- Registry rejects impossible combinations such as `fallback_only` plus
  `stable_publishable`.
- Derived registry entries inherit the worst upstream publication track.
- Publication policy ignores candidate fallback status only when candidate
  artifacts are absent from the public manifest/ZIP.
- Publication policy still rejects stable publishable fallback/stale datasets.
- Publication policy still rejects `indicadores` raw recovery and partial
  delivery.
- Manifest excludes candidate dataset artifacts.
- ZIP excludes candidate dataset artifacts.
- `hub_bundle.json.datasets` contains only stable publishable datasets.
- `hub_bundle.json.candidate_datasets` transparently lists the candidate layers
  and their next actions.

Use existing tests as patterns:

- `tests/test_pipeline_logic.py:100-160` for publication policy tests.
- `tests/test_pipeline_logic.py:230-293` for source registry tests.
- `tests/test_chile_hub.py` manifest, bundle, ZIP, and CLI assertions.

## Done criteria

All must hold:

- [ ] `data/source_registry.json` has `publication_track` and
  `public_bundle_eligible` for every dataset.
- [ ] The four current candidates are:
  `finanzas_municipales`, `resultados_educacionales`,
  `indicadores_urbanos_siedu`, and `perfil_territorial_comunal`.
- [ ] Candidate dataset data artifacts are absent from
  `data/normalized/artifact_manifest.json`.
- [ ] Candidate dataset data artifacts are absent from
  `data/normalized/chile-hub-publishable-bundle.zip`.
- [ ] `data/normalized/hub_bundle.json.datasets` contains only stable publishable
  datasets.
- [ ] `data/normalized/hub_bundle.json.candidate_datasets` lists the candidate
  datasets with clear non-publicable metadata.
- [ ] `make verify` exits 0 for dev/local builds.
- [ ] `make verify-live` does not fail due to declared candidate fallback
  datasets excluded from the public bundle.
- [ ] `make verify-live` still fails for unsafe stable publishable states,
  especially `indicadores` raw recovery or partial delivery.
- [ ] `make test`, `make lint`, and `make format-check` exit 0.
- [ ] `plans/README.md` status row for plan 009 is updated.

## STOP conditions

Stop and report back if:

- `data/source_registry.json` no longer has one entry per dataset or has been
  replaced by a different readiness mechanism.
- The current candidate list differs from the four datasets named in this plan
  and there is no obvious registry reason for the change.
- Excluding candidate artifacts would require deleting candidate datasets from
  dev/local generation entirely.
- `make verify-live` can only be made green by allowing raw recovery, partial
  indicator delivery, stale stable datasets, or stable dataset fallback.
- `hub_bundle.json` is consumed by a documented external contract that requires
  every catalog dataset in `bundle["datasets"]`; in that case, stop and ask
  whether to introduce a new `public_datasets` field instead of changing
  `datasets`.
- A candidate dataset has a real live extractor by the time this plan is
  executed. In that case, verify the extractor and registry first; do not
  blindly keep it candidate.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

This plan creates the durable boundary between "exists in development" and
"safe to publish." Future promotion work should be one dataset at a time:

- Promote `finanzas_municipales` only after a stable SINIM/SUBDERE export is
  configured and freshness/schema tests prove it.
- Promote `resultados_educacionales` only after replacing curated fallback with
  an official MINEDUC aggregate source.
- Promote `indicadores_urbanos_siedu` only after a stable official SIEDU export
  exists, or keep it candidate with explicit partial coverage.
- Promote `perfil_territorial_comunal` last, because it inherits upstream
  readiness.
- Keep `indicadores` strict. Better retry/backoff is useful, but raw recovery is
  a development resilience mechanism, not a public release mechanism.

Reviewers should scrutinize the manifest and ZIP contents closely. The most
important invariant is that the public package cannot accidentally include
candidate fallback data while `make verify-live` reports success.
