# Plan 028: Remove the misleading unrar "integrity check" (a per‑process no‑op that always passes)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat c486e7c..HEAD -- src/extractors/mineduc_resultados_extractor.py src/extractors/mineduc_establecimientos_extractor.py`
> If either file changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `c486e7c`, 2026-07-07

## Why this matters

Both MINEDUC extractors call `_verify_unrar_integrity(...)` before shelling out to
`unrar`, and the function is documented as verifying the binary against a "known hash".
It does not. `_UNRAR_EXPECTED_SHA256` is a module global initialized to `None`; on the
first (and, because each extractor runs as its own `python …_extractor.py` process, only)
call it records the **observed** hash and returns `True`. It also returns `True` for any
non‑regular file. So the control **always passes** and would never catch a tampered
`unrar`. This is worse than no check: it gives maintainers false assurance of a security
guarantee that does not exist. The honest fix is to delete the theater and rely on the OS
package manager's signed `unrar` (CI installs it via `apt-get install unrar`), keeping only
a plain availability check with a helpful error.

## Current state

Both files define an identical no‑op and call it as a "security gate":

- `src/extractors/mineduc_resultados_extractor.py`:
  - `import hashlib` (line 10) — used **only** by this function (line 128).
  - `_UNRAR_EXPECTED_SHA256 = None` global; `_verify_unrar_integrity` (lines 102‑134) with the
    always‑true logic:
    ```python
    if not unrar_path.is_file():
        return True
    actual = hashlib.sha256(unrar_path.read_bytes()).hexdigest()
    if _UNRAR_EXPECTED_SHA256 is None:
        _UNRAR_EXPECTED_SHA256 = actual
        return True
    return actual == _UNRAR_EXPECTED_SHA256
    ```
  - Call site (lines 212‑218):
    ```python
    unrar_bin = _find_unrar()
    unrar_path_obj = Path(unrar_bin) if isinstance(unrar_bin, str) else unrar_bin
    if not _verify_unrar_integrity(unrar_path_obj):
        raise SystemExit(
            f"Verificación de integridad fallida para {unrar_bin}. "
            "Reinstala con 'apt-get install unrar'."
        )
    ```
- `src/extractors/mineduc_establecimientos_extractor.py`:
  - `import hashlib` (line 4) — used **only** at line 68.
  - `_UNRAR_EXPECTED_SHA256 = None` global; `_verify_unrar_integrity` (lines 42‑74) — same logic.
  - Call site (lines 110‑122):
    ```python
    unrar_bin: Path | str = Path(ROOT_DIR) / ".venv" / "bin" / "unrar"
    if isinstance(unrar_bin, Path) and not unrar_bin.exists():
        unrar_bin = "unrar"
    unrar_path = Path(unrar_bin) if isinstance(unrar_bin, str) else unrar_bin
    if not _verify_unrar_integrity(unrar_path):
        raise SystemExit(
            f"Verificación de integridad fallida para {unrar_bin}. "
            f"El binario puede haber sido modificado. Reinstala con 'apt-get install unrar'."
        )
    ```
- No tests reference `_verify_unrar_integrity` or `unrar` (grep across `tests/` is empty), so no
  test needs deleting.
- `shutil` is already imported in both files (used by `_find_unrar` / resolution).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Lint (also flags unused imports) | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Import smoke | `.venv/bin/python -c "import src.extractors.mineduc_resultados_extractor, src.extractors.mineduc_establecimientos_extractor"` | exit 0 |
| Extractor tests | `.venv/bin/python -m pytest tests/test_extractors.py -q` | all pass |

## Scope

**In scope**:
- `src/extractors/mineduc_resultados_extractor.py`
- `src/extractors/mineduc_establecimientos_extractor.py`

**Out of scope**:
- `_find_unrar()` resolution logic — keep it.
- The actual `subprocess.run([...unrar...])` extraction calls — keep them.
- `data_manager.py` SHA256 verification of the downloaded bundle — that one is real and correct; do not touch.

## Git workflow

- Branch: `advisor/028-remove-unrar-noop`
- Conventional commit, e.g. `security(extractors): elimina verificación unrar no‑op y engañosa`.

## Steps

### Step 1: Delete the no‑op function and its global in both files

In each file remove: the `_UNRAR_EXPECTED_SHA256 = None` global, the entire
`_verify_unrar_integrity(...)` function, and the now‑unused `import hashlib`.

### Step 2: Replace each call site with an honest availability check

`mineduc_resultados_extractor.py` (was lines 212‑218) →

```python
        unrar_bin = _find_unrar()
        if shutil.which(str(unrar_bin)) is None and not Path(unrar_bin).exists():
            raise SystemExit(
                f"unrar no está disponible ({unrar_bin}). Instala con 'apt-get install unrar'."
            )
```

`mineduc_establecimientos_extractor.py` (was lines 110‑122) → keep the resolution, replace only the
integrity guard:

```python
        unrar_bin: Path | str = Path(ROOT_DIR) / ".venv" / "bin" / "unrar"
        if isinstance(unrar_bin, Path) and not unrar_bin.exists():
            unrar_bin = "unrar"
        if shutil.which(str(unrar_bin)) is None and not Path(unrar_bin).exists():
            raise SystemExit(
                f"unrar no está disponible ({unrar_bin}). Instala con 'apt-get install unrar'."
            )
```

**Verify**: `grep -rn "_verify_unrar_integrity\|_UNRAR_EXPECTED_SHA256\|import hashlib" src/extractors/mineduc_*.py` → no matches.

### Step 3: Confirm imports are clean

Run `make lint` — ruff (`F401`) will flag any now‑unused import (`hashlib`). Remove whatever it reports.
Confirm `shutil` is still used (it is, by the new availability check and `_find_unrar`).

**Verify**: `make lint` → exit 0; the import smoke command → exit 0.

## Test plan

- No new behavioral test is strictly required (the removed code had no test). Optionally add a small test
  that monkeypatches `shutil.which` to return `None` and asserts the extractor's download/extract entry
  raises `SystemExit` with an "unrar no está disponible" message — only if the existing test class makes
  that easy to reach without network. Do not add a networked test.
- Verification: `.venv/bin/python -m pytest tests/test_extractors.py -q` → all pass.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -rn "_verify_unrar_integrity" src/` → no matches
- [ ] `grep -rn "_UNRAR_EXPECTED_SHA256" src/` → no matches
- [ ] `grep -n "import hashlib" src/extractors/mineduc_resultados_extractor.py src/extractors/mineduc_establecimientos_extractor.py` → no matches
- [ ] Import smoke command exits 0
- [ ] `.venv/bin/python -m pytest tests/test_extractors.py -q` exits 0
- [ ] `make lint` and `make format-check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `hashlib` turns out to be used elsewhere in either file (grep before deleting the import).
- A test does reference the removed function (it shouldn't, per the current grep) — adjust it and note it.
- The call‑site context has drifted so the replacement snippet doesn't fit cleanly.

## Maintenance notes

- If real supply‑chain assurance for `unrar` is ever wanted, do it properly: pin a per‑platform expected
  digest as a hardcoded constant and compare against it (and drop the `return True` on non‑regular files).
  A per‑process TOFU is never a security control.
- Reviewer should confirm CI's `apt-get install unrar` step (only runs on `schedule`/`workflow_dispatch`)
  still provides the binary the extractors need.
