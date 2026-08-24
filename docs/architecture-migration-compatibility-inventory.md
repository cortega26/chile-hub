# Compatibility inventory for the architecture migration

> **Status:** Phase 0 complete — reviewed 2026-08-23. This is the compatibility
> baseline for Phase 1 characterization and later promotion gates. It records
> supported behavior, not a promise to preserve every implementation detail.

## Classification rule and evidence

An item is a **public/behavioral compatibility guarantee** when it is part of a
published interface, documented policy, generated public artifact, existing ADR,
or an explicit contract/test that represents a consumer-facing promise. It is an
**implementation detail** when callers cannot rely on it and neither public
documentation nor accepted policy makes it observable or stable. When evidence
is mixed, this inventory chooses the narrower supported promise and records the
reason rather than freezing accidental behavior.

Primary evidence: `README.md`, `docs/installation.md`, `docs/http-access.md`,
`docs/versioning-policy.md`, `CONTRIBUTING.md`, `AGENTS.md`, ADR-001 through
ADR-017, `pyproject.toml`, public `chile_hub` modules, workflows, contracts, and
the corresponding API/packaging/pipeline tests.

## Public/behavioral compatibility guarantees

| Area | Guarantee during migration | Evidence / reasoning |
| --- | --- | --- |
| Python entry points | `from chile_hub import ChileHub`; documented public modules and exception classes remain importable; public method signatures remain compatible unless the SemVer/deprecation policy permits otherwise. | README API section, `docs/api.md`, `src/chile_hub/__init__.py`, `docs/versioning-policy.md` §1.1. |
| Constructor forms | `ChileHub()`, `ChileHub(data_dir=...)`, and `ChileHub(catalog_path=...)` preserve their documented mutual-exclusion/error behavior; `data_version` and `auto_update` retain their current supported meaning. | `core.py::ChileHub.__init__`, README, `docs/installation.md`, API tests. |
| Dataset access | Documented `ChileHub` methods, `Dataset` enum values, `load_polars`, SQL/query helpers, validation methods, and documented exceptions/error categories retain accepted behavior for supported inputs. | README/API docs and SemVer policy. Exact private helper arrangement is not contractual. |
| CLI | Installed `chile-hub` command, documented subcommands/options, success/error exit behavior, and machine-readable/table output modes where documented remain compatible. | `pyproject.toml [project.scripts]`, README, `cli.py`, CLI tests. Human prose/column spacing is only guaranteed where a test or documentation makes it parseable. |
| Dataset identifiers and aliases | Canonical IDs remain valid; `comunas_enriquecidas` continues to resolve as an alias of `comunas` without creating a distinct physical artifact. Current public enum policy remains unchanged until explicitly revised. | `datasets.py`, `metadata.py`, `artifacts.py`, catalog and tests. |
| Schemas and CUT | Contract files/paths, required structural rules, canonical column names/types, and fixed-width CUT strings remain compatible. `codigo_region`, `codigo_provincia`, and `codigo_comuna` remain strings of width 2/3/5. | ADR-002, ADR-005, contracts, versioning policy. |
| Public artifacts | Existing public artifact names, relative paths, schemas, expected bundle membership, companion checksums, and documented static `latest` URLs remain valid compatibility views. Candidate datasets remain excluded from the public bundle. | README, ADR-004, ADR-010, artifact/packaging tests. |
| Publication policy | Build/verify/publish remains fail-closed; stable/candidate behavior, public eligibility, candidate exclusion, and derived-dataset track inheritance retain current outcomes. | ADR-001, ADR-004, source registry, verifier tests. |
| Provenance/source policy | The current meaning of source mode, fallback/reuse policy, freshness/publication gates, source attribution, and extraction-lane ownership remains intact while internals migrate. | `source_registry.json`, `docs/extraction-lanes.md`, ADR-016/017, verifier/CI tests. |
| Required and optional inputs | Required staging data/metadata fail closed; currently optional or candidate paths retain their accepted inclusion/exclusion and error behavior. | AGENTS.md §3–4, build/verifier tests, registry policy. |
| Release/cache integrity | `chile-hub-publishable-bundle.zip`, its SHA-256 sidecar validation, release/tag selection, verified-cache replacement behavior, cache commands, and offline use retain current semantics. | `docs/installation.md`, `data_manager.py`, packaging/runtime tests. |
| Daily-data independence | Data refresh cadence and freshness can change without requiring a Python package SemVer release. | ADR-003, `docs/versioning-policy.md` §2. |
| Interoperability | Existing Parquet/JSON/DuckDB/SQLite/Excel outputs and generated Frictionless/DCAT projections remain available where the current catalog declares them. | Catalog, ADR-005, ADR-008, ADR-010. New output policy is out of scope. |

## Explicit implementation details

| Area | Not preserved merely because it exists | Reasoning |
| --- | --- | --- |
| Internal orchestration | Order and names of internal helper calls, manual dictionaries, builder boundaries, and whether a compatibility adapter or graph resolves a dataset. | Not public API; the roadmap exists to replace these while retaining outcomes. |
| Internal representations | In-memory catalog/registry objects, `DatasetSpec` serialization, module layout, private names, and cache implementation internals. | No published contract; future phases own these boundaries. |
| Volatile metadata | Build timestamps, temporary paths, file mtimes, logging order, network retry timing, and incidental dictionary ordering. | They do not describe data content or public policy. Equivalence tests must allowlist each volatile field narrowly. |
| Formatting without a contract | Whitespace, ordering, and prose of human-readable reports/tables absent a documented parser or explicit snapshot contract. | Preserve semantic fields and documented output modes, not incidental rendering. |
| Intermediate files | Temporary staging copies, cache files, raw filename timestamps, and unadvertised normalized intermediates. | Only documented/stable artifacts and audit immutability are guaranteed; later durable snapshot policy owns archival layout. |
| Test-only seams | Monkeypatch targets, fixture layout, private exception text, and line/branch coverage percentages. | They are implementation tools. Coverage informs missing scenarios but never defines completion. |

## Non-obvious classifications

- **Static `latest` URLs are guarantees, despite being mutable.** ADR-010 calls
  them a public static access contract. A future immutable release view must
  retain `latest` as a compatibility projection rather than silently remove it.
- **The exact contents of a configured public bundle are guarantees.** ADR-004
  makes publication tracks product policy; candidates can be transparently
  listed but cannot leak into the ZIP merely because internal representation
  changes.
- **`refreshed_at_utc` remains compatible, but its current storage mechanics do
  not.** It is documented freshness metadata. The Phase 4/6 model may project it
  from richer provenance without preserving extractor-local implementation.
- **Raw snapshots are audit evidence, not a public filesystem API.** Their
  append-only character is protected by AGENTS.md, but timestamp filename shape
  and local location are not a consumer contract; Phase 7 may add durable
  resolution without breaking that audit rule.
- **The `Dataset` enum is a public compatibility surface but not proof that every
  catalog entry must be added to it today.** Current omissions/candidate policy
  must remain unchanged until Phase 2 documents and proves an explicit enum
  policy.

## Future Phase 2 pilot selection

### Selected: `partidos_politicos`

`partidos_politicos` is the safest informative pilot: it is
`stable_publishable` and public; direct; has its own conventional daily extractor
(`partidos_politicos_extractor.py`); has no `alias_for` or derived dependency;
is not a special scraper lane; and has a compact, ordinary Parquet/JSON output
pair with a separately authored contract and dataset document. It exercises the
normal catalog/source-policy/contract/documentation path without the shared
`subdere_extractor.py` fan-out, multi-source recovery chain of `indicadores`, or
candidate/fallback edge conditions.

### Ranked alternatives

1. **`partidos_politicos` — chosen.** Simple direct stable path, dedicated
   extractor, normal outputs, no CUT dependency required for its contract.
2. **`censo_hogares_viviendas`.** Also direct, stable, public, dedicated, and
   ordinary Parquet/JSON; ranked second because its CUT referential validation
   depends on the territorial build inputs, adding cross-dataset sensitivity to
   the first registry proof.
3. **`pobreza_comunal`.** Direct and stable with compact outputs, but it has a
   long-cycle source and development fallback policy; that adds recovery policy
   which the pilot criteria deliberately avoid.

`regiones`, `provincias`, `comunas`, and `comunas_enriquecidas` are not suitable
first pilots because they share a fan-out extractor and the last is an alias.
`indicadores` is multi-source/recovery-sensitive; derived, candidate, monthly,
ad-hoc, geometry, and scraper datasets belong to later Phase 3 batches.

## Phase 0 closure

P0-D1 through P0-D4 are accepted and ratified in ADR-018 and ADR-019. The final
`ExtractionResult` model (Phase 4), durable provider/retention/legal/credential
and exception policy (Phase 7), release mechanics (Phases 8–9), and client/cache
decomposition (Phase 10) remain deliberately unresolved.
