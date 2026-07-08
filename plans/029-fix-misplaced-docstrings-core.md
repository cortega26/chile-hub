# Plan 029: Fix three misplaced docstrings in `core.py` that silently drop `__doc__`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/chile_hub/core.py`
> If the file changed since this plan was written, re‑run the detection script
> in Step 1 to find the current line numbers before editing.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

Three public `ChileHub` methods have a statement **before** their triple‑quoted string,
so the string is a no‑op expression, not the function's `__doc__`. This looks like a
mechanical refactor artifact: a `dataset_name = _resolve_dataset_name(dataset_name)` line
was inserted at the top of each method, pushing the docstring to second position. The
result is that `ChileHub.load_polars`, `ChileHub.validate_dataset`, and
`ChileHub.validate_user_data` all have `__doc__ is None`, so they **vanish from the
mkdocstrings API reference** (`docs/api.md` → the published docs site) and from
`help(ChileHub.load_polars)`. These are core public API methods; their reference docs
currently silently do not render.

## Current state

`src/chile_hub/core.py`, three methods with the same defect (statement then string):

- `load_polars` (def at line 300):
  ```python
  def load_polars(self, dataset_name: str | Dataset, validate: bool = False) -> pl.DataFrame:
      dataset_name = _resolve_dataset_name(dataset_name)
      """Carga un dataset como DataFrame de Polars.
      ...
      """
  ```
- `validate_dataset` (def at line 374):
  ```python
  def validate_dataset(self, dataset_name: str | Dataset) -> dict:
      dataset_name = _resolve_dataset_name(dataset_name)
      """Valida los datos publicados del hub contra su contrato JSON Schema.
      ...
      """
  ```
- `validate_user_data` (def at line 419):
  ```python
  def validate_user_data(self, df: pl.DataFrame, dataset_name: str | Dataset) -> dict:
      dataset_name = _resolve_dataset_name(dataset_name)
      """Valida un DataFrame de usuario contra el contrato de schema del dataset.
      ...
      """
  ```

A full AST scan of `src/chile_hub/` finds **exactly these three** occurrences and no others.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Detect misplaced docstrings | see Step 1 script | before: 3; after: 0 |
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Core tests | `.venv/bin/python -m pytest tests/test_core.py tests/test_chile_hub.py -q` | all pass |

## Scope

**In scope**:
- `src/chile_hub/core.py`

**Out of scope**:
- The bodies/behavior of the three methods — only the ordering of the first two lines changes.
- The `validate_user_data` root‑dir issue (it uses module `ROOT_DIR` while `validate_dataset` uses
  `self.root_dir`) — that is a separate behavioral change; leave it and see Maintenance notes.

## Git workflow

- Branch: `advisor/029-fix-misplaced-docstrings`
- Conventional commit, e.g. `fix(api): restaura docstrings de load_polars/validate_* (orden de sentencias)`.

## Steps

### Step 1: Confirm the three sites (and only three)

Run this detection script and confirm it prints exactly 3 sites (load_polars, validate_dataset,
validate_user_data):

```bash
.venv/bin/python - <<'PY'
import ast
src = open("src/chile_hub/core.py").read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for i, stmt in enumerate(node.body):
            if i > 0 and isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str):
                print(f"{node.name}  def@{node.lineno}  misplaced-string@{stmt.lineno}")
PY
```

**Verify**: prints 3 lines. If it prints a different set, use those line numbers instead and note it.

### Step 2: Move the docstring above the statement in each method

For each of the three methods, swap the order so the docstring is the **first** statement and
`dataset_name = _resolve_dataset_name(...)` runs after it. Target shape (load_polars shown):

```python
    def load_polars(self, dataset_name: str | Dataset, validate: bool = False) -> pl.DataFrame:
        """Carga un dataset como DataFrame de Polars.
        ...
        """
        dataset_name = _resolve_dataset_name(dataset_name)
        ...
```

Do the identical reordering for `validate_dataset` and `validate_user_data`. Do not change any other line.

**Verify**: re‑run the Step 1 script → prints nothing (0 sites).

### Step 3: Confirm `__doc__` is now populated

**Verify**:
```bash
.venv/bin/python -c "from src.chile_hub.core import ChileHub; assert ChileHub.load_polars.__doc__ and ChileHub.validate_dataset.__doc__ and ChileHub.validate_user_data.__doc__; print('docstrings ok')"
```
→ prints `docstrings ok`.

## Test plan

- Add one small test to `tests/test_core.py` (or `tests/test_chile_hub.py`, wherever `ChileHub` API
  tests live) asserting `ChileHub.load_polars.__doc__ is not None` (and the other two). This guards
  against the refactor artifact reappearing.
- Pattern: any existing method test in `tests/test_core.py`.
- Verification: `.venv/bin/python -m pytest tests/test_core.py tests/test_chile_hub.py -q` → all pass.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] The Step 1 detection script prints 0 sites
- [ ] The Step 3 `__doc__` assertion command prints `docstrings ok`
- [ ] `.venv/bin/python -m pytest tests/test_core.py tests/test_chile_hub.py -q` exits 0 (incl. the new `__doc__` test)
- [ ] `make lint` and `make format-check` exit 0
- [ ] Only `src/chile_hub/core.py` (+ the test file) modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The detection script finds more or fewer than 3 sites (the file drifted) — use the live results.
- Reordering changes behavior in any test (it should not; `_resolve_dataset_name` has no side effects
  relevant to the docstring position).

## Maintenance notes

- Related, deliberately deferred: `validate_user_data` resolves its contract path from module‑level
  `ROOT_DIR` (`Path(__file__).resolve().parents[2]`) while `validate_dataset` uses `self.root_dir`.
  In an installed/bundle context these differ, so `validate_user_data` may look for contracts in the
  wrong place. That is a behavioral fix (needs deciding where contracts live for installed users) and
  is tracked separately — do not fold it in here.
- Reviewer should rebuild the docs (`make docs-build`) and confirm the three methods now render in the
  API reference.
