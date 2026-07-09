# Plan 027: Label a successful SINIM scrape as live provenance, not curated fallback

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/extractors/sinim_finanzas_live_extractor.py`
> If the file changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

`sinim_finanzas_live_extractor.py` deliberately tags a successful monthly scrape with
`source_mode = "monthly"` (a guardrail so a monthly scrape isn't advertised as daily‑`"live"`).
But `build_metadata` computes `source_detail` from `source_mode == "live"` — a value the success
path **never** produces. So a real scrape of ~345 municipalities is written with
`source_detail = "curated_fallback_pending_direct_export"`, i.e. **identical** to the 3‑row curated
fallback. Every consumer of provenance — `provenance_report`, `drift_report`, and any downstream
audit or redistribution decision — is then unable to distinguish a genuine live scrape from the stub.
That defeats the entire point of provenance tracking for this dataset.

## Current state

`src/extractors/sinim_finanzas_live_extractor.py`:

- On scrape success (lines 357‑365), `source_mode` is set to `"monthly"`:
  ```python
      notes.append(f"live: {len(rows)} municipios extraídos (snapshot: {raw_path.name})")
      # Guardrail §4.2.5: scrape mensual NO se marca "live"
      source_mode = "monthly"
  ```
- On failure (lines 367‑372), `source_mode = "fallback"` and `rows = _get_fallback_rows()` (3 rows).
- `build_metadata` (lines 435‑449) mis‑keys `source_detail`:
  ```python
      source_detail=(
          "live_scraping_sinim_portal"
          if source_mode == "live"
          else "curated_fallback_pending_direct_export"
      ),
  ```
  Since `source_mode` is only ever `"monthly"` or `"fallback"`, the `"live"` branch is dead and the
  fallback string is always used.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Extractor tests | `.venv/bin/python -m pytest tests/test_extractors.py -q -k "sinim or Sinim or finanzas or Finanzas"` | all pass |

## Scope

**In scope**:
- `src/extractors/sinim_finanzas_live_extractor.py`
- `tests/test_extractors.py` (add a test)

**Out of scope**:
- `src/extractors/sinim_finanzas_extractor.py` (the static daily variant) — it always returns the
  curated fallback, so `curated_fallback_...` is correct there. (Its divergence from the live copy is
  Plan 038/TECHDEBT‑03, not this plan.)
- The `"monthly"` vs `"live"` `source_mode` guardrail — keep it; only `source_detail` derivation is wrong.

## Git workflow

- Branch: `advisor/027-sinim-provenance-label`
- Conventional commit, e.g. `fix(extractors): etiqueta provenance real en scrape SINIM exitoso`.

## Steps

### Step 1: Derive `source_detail` from actual scrape success

In `build_metadata`, change the condition so any non‑fallback mode is treated as a real scrape:

```python
      source_detail=(
          "live_scraping_sinim_portal"
          if source_mode != "fallback"
          else "curated_fallback_pending_direct_export"
      ),
```

(Equivalently `if source_mode in {"live", "monthly"}` — pick one and be consistent. `!= "fallback"`
is more robust to future mode names.)

**Verify**: `make lint` → exit 0.

### Step 2: Add a regression test

In `tests/test_extractors.py`, add a test (model after the existing SINIM/finanzas test class —
`grep -n "class .*Finanzas" tests/test_extractors.py`) that calls
`sinim_finanzas_live_extractor.build_metadata(df, "monthly", url, notes)` and asserts
`metadata["source_detail"] == "live_scraping_sinim_portal"`, plus a second case with
`source_mode="fallback"` asserting the curated string. Build a tiny 1‑row `df` with the canonical
finanzas schema (see `normalize_rows`), or reuse a fixture the existing test class already builds.

**Verify**: `.venv/bin/python -m pytest tests/test_extractors.py -q -k "sinim or Sinim or finanzas or Finanzas"` → all pass, including the new test.

## Test plan

- New test (Step 2): `build_metadata` labels a `"monthly"` scrape as `live_scraping_sinim_portal` and a
  `"fallback"` as `curated_fallback_pending_direct_export`.
- Pattern: the existing SINIM live extractor test class in `tests/test_extractors.py`.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n 'source_mode == "live"' src/extractors/sinim_finanzas_live_extractor.py` → no matches
- [ ] The new test asserts both the `"monthly"`→live and `"fallback"`→curated cases and passes
- [ ] `.venv/bin/python -m pytest tests/test_extractors.py -q -k "sinim or Sinim or finanzas or Finanzas"` exits 0
- [ ] `make lint` and `make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `build_metadata` no longer takes `source_mode` as a plain string (signature drifted).
- `fetch_data` can produce a `source_mode` value other than `"monthly"`/`"fallback"`/`"live"` — if so,
  reconsider the condition and report what values are possible.

## Maintenance notes

- If a future change introduces a true daily‑`"live"` mode for SINIM, the `!= "fallback"` condition
  already handles it; no further edit needed.
- Reviewer should confirm `provenance_report`/`drift_report` now show distinct provenance for a real
  monthly scrape vs the fallback (visible after a `monthly-scrape` run — see Plan 034, which fixes that
  workflow so the live path actually runs).
