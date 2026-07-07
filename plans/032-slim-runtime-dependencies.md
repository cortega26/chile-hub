# Plan 032: Move pipeline‑only dependencies out of the installed library's runtime deps

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- pyproject.toml uv.lock AGENTS.md`
> If `pyproject.toml` changed since this plan was written, re‑confirm the import
> scan in Step 1 before removing anything.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED
- **Depends on**: 026 (regenerate lock first so the lock is clean before/after this change)
- **Category**: dependencies
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

The wheel ships only `src/chile_hub` (`[tool.hatch.build.targets.wheel] packages = ["src/chile_hub"]`).
An import scan of `src/chile_hub/**` shows the shipped library imports only `polars`, `requests`,
`rich`, `platformdirs` (plus stdlib and its own submodules). Yet the runtime `[project.dependencies]`
also lists **five pipeline‑only** packages the installed library never imports: `pyarrow`, `duckdb`,
`openpyxl`, `rutificador`, `tenacity`. So every `pip install chile-hub` pulls ~50–70 MB of unused
native wheels (pyarrow + duckdb dominate) onto end‑user machines that only ever receive Polars
DataFrames + JSON — larger install, larger CVE surface, more resolution friction, for code that never runs.

Four of the five (`duckdb`, `openpyxl`, `rutificador`, `tenacity`) are **already** declared in the
`pipeline` extra, so this is mostly a *removal* from runtime; only `pyarrow` needs adding to `pipeline`.
This also reconciles the repo's own policy contradiction: AGENTS.md §10 forbids unpinned runtime deps,
yet the runtime deps float with `>=` — the honest resolution is "ranges for the library's few real
runtime deps, `==` pins for pipeline/dev tooling."

## Current state

`pyproject.toml`:

- `[project.dependencies]` (lines 37‑48):
  ```toml
  dependencies = [
      "polars>=1.41.2",
      "pyarrow>=24.0.0",          # only needed by .to_pandas() during builds (pipeline)
      "requests>=2.34.2",
      "platformdirs>=4.10.0",
      "rich>=14.0",
      "rutificador>=1.5.8",       # only used by src/validation.py (pipeline)
      "openpyxl>=3.1.5",          # only used by extractors/builders (pipeline)
      "duckdb>=1.5.4",            # only used by src/builders/formats.py (pipeline)
      "tenacity>=9.1.4",          # only used by src/extractors/http_utils.py (pipeline)
  ]
  ```
- `[project.optional-dependencies].pipeline` (lines 52‑61) already contains
  `duckdb==1.5.4`, `openpyxl==3.1.5`, `rutificador>=1.5.8`, `tenacity==9.1.4` (plus `pandas`,
  `xlsxwriter`, `curl_cffi`, `structlog`). It does **not** contain `pyarrow`.
- The library's own imports (verified by both the tech‑debt and dependency audits): `polars`, `requests`,
  `rich`, `platformdirs`. `duckdb` appears in `core.py` only as CLI help text, not an import.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Confirm library imports | see Step 1 | only polars/requests/rich/platformdirs (+ stdlib/self) |
| Regenerate lock | `uv lock` | exit 0 |
| Lock in sync | `uv lock --locked` | exit 0 |
| Install‑smoke (runtime only) | see Step 3 | `ChileHub().load_polars(...)` works without the 5 deps |
| Package smoke | `make package-smoke` | wheel builds, imports, CLI `--help` works |

## Scope

**In scope**:
- `pyproject.toml` (`[project.dependencies]` and the `pipeline` extra)
- `uv.lock` (regenerated)
- `AGENTS.md §10` (reconcile the pinning‑policy wording)

**Out of scope**:
- Removing `rutificador` entirely — that's Plan 037 (which inlines the RUT check‑digit). Here you only
  move it from runtime to the `pipeline` extra; 037 later removes it from `pipeline` too.
- Changing `pipeline`/`dev` pins — leave the `==` pins as they are.
- Any source code — this is a manifest change only.

## Git workflow

- Branch: `advisor/032-slim-runtime-deps`
- Conventional commit, e.g. `chore(deps): mueve deps solo‑pipeline fuera de runtime del paquete`.

## Steps

### Step 1: Re‑confirm the library import graph before removing anything

```bash
grep -rnoE "^(import|from) [a-zA-Z0-9_]+" src/chile_hub | grep -vE "chile_hub|__future__" | sort -u
```
Confirm the only third‑party top‑level imports are `polars`, `requests`, `rich`, `platformdirs`.
If any of the five (`pyarrow`, `duckdb`, `openpyxl`, `rutificador`, `tenacity`) appears, STOP and report —
that one must stay in runtime.

### Step 2: Edit `pyproject.toml`

- Reduce `[project.dependencies]` to the four the library actually imports:
  ```toml
  dependencies = [
      "polars>=1.41.2,<2",
      "requests>=2.34.2",
      "platformdirs>=4.10.0",
      "rich>=14.0",
  ]
  ```
  (The `<2` upper bound on `polars` guards published consumers against an untested major; add
  `pyarrow` back here **only** if Step 3's install‑smoke fails without it.)
- Add `pyarrow` to the `pipeline` extra (the other four are already present):
  ```toml
  pipeline = [
      "duckdb==1.5.4",
      "pyarrow>=24.0.0",
      "pandas==3.0.3; python_version >= '3.11'",
      ...
  ]
  ```

### Step 3: Install‑smoke — prove the library works with runtime deps only

In a throwaway environment (do NOT touch the repo `.venv`), install just the runtime deps and confirm
the public read path works:

```bash
uv venv /tmp/chile-smoke
uv pip install --python /tmp/chile-smoke polars requests platformdirs rich
# point at this repo's built artifacts:
/tmp/chile-smoke/bin/python -c "
import sys; sys.path.insert(0, 'src')
from chile_hub import ChileHub
h = ChileHub()
df = h.load_polars('comunas')
print('rows:', df.height)
"
```

This must succeed **without** pyarrow/duckdb/openpyxl/rutificador/tenacity installed. If it raises
`ModuleNotFoundError` for one of them, that dep is genuinely a runtime dep — put it back in
`[project.dependencies]` and note which and why.

**Verify**: the command prints a positive row count.

### Step 4: Regenerate the lock and reconcile the policy doc

- `uv lock` → `uv lock --locked` (exit 0).
- In `AGENTS.md §10`, update the "versiones no fijadas" antipattern to state the intended policy:
  library **runtime** deps use compatible ranges (e.g. `polars>=1.41.2,<2`) so published consumers can
  resolve; **pipeline/dev** tooling uses `==` pins reproduced via `uv.lock`. Keep the example accurate.

**Verify**: `make package-smoke` → wheel builds, `from chile_hub import ChileHub` works, `chile-hub --help` works.

## Test plan

- No unit test changes; the gates are the install‑smoke (Step 3) and `make package-smoke` (Step 4).
- Optional: if `tests/test_packaging_runtime.py` asserts on declared dependencies, update it to expect the
  slimmed set.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -nE '"(pyarrow|duckdb|openpyxl|rutificador|tenacity)' pyproject.toml` shows them **only** under the `pipeline` extra, not `[project.dependencies]`
- [ ] Step 3 install‑smoke prints a positive row count with only the 4 runtime deps installed
- [ ] `make package-smoke` succeeds
- [ ] `uv lock --locked` exits 0
- [ ] `grep -n "quince\|no fijadas" AGENTS.md` policy text updated (no contradiction remains)
- [ ] No source files modified (`git status` shows only pyproject.toml, uv.lock, AGENTS.md)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The Step‑1 import scan shows the library importing any of the five deps (keep that one in runtime).
- The Step‑3 install‑smoke fails for a specific dep — report which; that dep stays in runtime.
- Removing `pyarrow` breaks a documented user workflow that relies on `chile-hub` transitively providing
  it (README's DuckDB/Excel pitch refers to the pre‑built *bundle artifacts*, not library imports — verify).

## Maintenance notes

- After Plan 037 lands (inline RUT check digit), remove `rutificador` from the `pipeline` extra too.
- Reviewer should confirm the wheel's `Requires-Dist` (`twine check` / inspect the built METADATA) lists
  only the four runtime deps.
