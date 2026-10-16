# Plan 147: Stealth-fetch for SINCA calidad_aire (anti-403, permisos precedent)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat ac2aee6..HEAD -- src/extractors/calidad_aire_extractor.py src/extractors/http_utils.py src/extractors/permisos_edificacion_extractor.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Origin**: CI red 2026-10-16 (2 consecutive Pipeline Check runs): SINCA `listadomapa2k19` returns 403 Forbidden to the GitHub-runner IP → calidad_aire falls back to snapshot (fallback + drifted + 2 warnings) → `top_issue` flips from `indicadores` to `calidad_aire` → 7 ranking tests fail. The merged 139–146 work is proven green (perfil goldens pass on fresh builds). Maintainer chose stealth-fetch over test de-brittling.

## Status

- **Priority**: P1 (CI red on main; daily publish signal)
- **Effort**: S
- **Risk**: LOW-MED (network-dependent; established shared helper, two in-repo precedents)
- **Depends on**: none
- **Category**: correctness
- **Planned at**: commit `ac2aee6`, 2026-10-16 (main post-#181; drift base is bd77d34-era code, unchanged since — re-check in Step 0)

## Why this matters

Same species as the 2026-09-25 permisos_edificacion incident (MINVU/CEDOC blocking the runner, fixed with `stealth_get`, recorded in `todo.md`): a bare-`requests` User-Agent gets 403 from an upstream WAF while the data itself is public. The extractor already degrades gracefully (snapshot fallback, validation ok), so the pipeline is healthy — but the suite stays red and the daily incremental series stops growing while fallback persists. Applying the proven shared helper restores live data with a 1–3 line change.

## Current state

- `src/extractors/calidad_aire_extractor.py:321`: `with fetch_with_retry(LISTADO_URL, timeout=120) as response:` — default `get_fn=requests.get` (bare User-Agent). `LISTADO_URL = "https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/"` (`:73`). Fallback chain `:326-359` (snapshot glob → FALLBACK_ROWS); audit EVERY other `requests.`/`fetch_with_retry` call site in this file in Step 1 (24h series fetches per station/contaminant may need the same treatment).
- `src/extractors/http_utils.py:38-50`: `stealth_get(url, **kwargs)` — curl_cffi Chrome impersonation when available, else `requests` + browser headers; degrades gracefully without the extra. `fetch_with_retry` (`:71+`) retries only ConnectionError/Timeout/5xx — 4xx propagate, so retries alone never fix a 403; stealth is the fix.
- Precedent (copy it): `permisos_edificacion_extractor.py:67-69` dual import (`src.extractors.http_utils` → fallback `http_utils`) then `_stealth_get(REPOSITORIO_URL, timeout=60)` (`:227`) and `_stealth_get(url, timeout=120)` (`:247`); same dual-import in `subdere_extractor.py:20-29`, used at `:371,437`.
- Evidence: dispatch runs 38837784648 + 38838204422 (2026-10-16) both show `403 Client Error: Forbidden for url: .../listadomapa2k19/` with snapshot `sinca_listadomapa_20261015T143926Z.json` reused (that listing succeeded 2026-10-15 → block started between runs, WAF/rate-limit pattern).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---|---|---|---|
| Focal tests | `./.venv/bin/pytest tests/test_extractors.py -q -k "Calidad or Aire or Sinca or Stealth or Http" tests/test_ci_config.py -q` | declared | all pass |
| Doctor | `make doctor` | declared | exit 0 |
| Lint/format | `make lint && make format-check` | declared | exit 0 |

## Scope

**In scope** (the only files you should modify):

- `src/extractors/calidad_aire_extractor.py` (route LISTADO + any series fetch sites through `stealth_get`, permisos-style)
- `tests/test_extractors.py` (1–3 tests: stealth path used, graceful-degrade without curl_cffi, fallback chain intact)
- `plans/README.md` (status row only — SKIP per dispatcher override; reviewer owns the index)

**Out of scope**: `http_utils.py` (helper already correct), the 7 ranking tests (chosen path restores live data so they pass unmodified — do NOT touch them), any other extractor, any workflow/schedule change, any retry-policy change (4xx must keep propagating).

## Git workflow

- Branch: `advisor/147-sinca-stealth-fetch`
- One commit per step; message style `tipo(scope): mensaje` (e.g. `fix(calidad-aire): stealth fetch for SINCA listing (anti-403)`).
- Do NOT push.

## Steps

### Step 0: Establish a green baseline

Drift check + focal tests + `make doctor` on the unmodified tree. Attempt a live `GET` of LISTADO_URL from the worktree (informational only — local IP may or may not reproduce the 403; record the status code either way, it does not gate anything).

**Verify**: no drift; tests + doctor green; recorded local status code.

### Step 1: Route all SINCA fetch sites through stealth_get

1. List every HTTP call site in `calidad_aire_extractor.py` (`grep -n "requests\.\|fetch_with_retry\|urlopen"`).
2. Apply the permisos dual-import + `_stealth_get(...)` pattern to LISTADO and every series-fetch site that uses a bare UA. Keep timeouts/params identical; change transport only.
3. Do NOT add retries for 4xx, do NOT change the fallback chain, do NOT touch parse/validate logic.

**Verify**: `grep -n "requests.get\|fetch_with_retry(LISTADO" src/extractors/calidad_aire_extractor.py` shows no remaining bare-UA call site; focal tests pass.

### Step 2: Tests

Add 1–3 tests in `tests/test_extractors.py` (model on the permisos stealth tests — locate them first with `grep -n "stealth" tests/test_extractors.py`): stealth helper is invoked for the listing URL; behavior without curl_cffi degrades to headered requests (mock); fallback-on-403 chain still returns snapshot/FALLBACK_ROWS. No live network in tests, ever.

**Verify**: `./.venv/bin/pytest tests/test_extractors.py -q -k "Calidad or Sinca or Stealth"` → pass including new tests.

### Step 3: Full verification (no build, no extract)

`make test` + `make doctor` + `make lint && make format-check`. Do NOT run extractors live (network) or `make build` (data churn). State explicitly in the report: CI proof of the 403 fix awaits the next scheduled/dispatch run (only GitHub-runner IP reproduces it).

**Verify**: suite green except possibly the 7 known SINCA-ranking tests IF the local tree still resolves them against stale committed artifacts — record exactly which fail and why; zero NEW failures vs the pre-change baseline measured in Step 0.

## Test plan

- New tests as in Step 2, modeled on existing stealth tests for permisos.
- Regression proof: full-suite failure set after the change must be a subset of the Step-0 baseline set (no new reds).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] No bare-UA HTTP call site remains in `calidad_aire_extractor.py`
- [ ] New stealth tests exist and pass; no live network in tests
- [ ] Post-change full-suite failures ⊆ Step-0 baseline failures (no new reds)
- [ ] `make doctor`, `make lint`, `make format-check` exit 0
- [ ] `git diff --name-only <merge-base>...HEAD` lists only in-scope files
- [ ] Report states CI proof pending (runner-IP-only reproduction)

## STOP conditions

Stop and report back (do not improvise) if:

- The extractor's fetch code differs from Current state (drift).
- `stealth_get` cannot be imported/used in this extractor's import style (report the import error, do not vendor a new helper).
- A series-fetch site requires different kwargs that `stealth_get` does not accept (report, do not extend `http_utils.py` here).
- Any verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If SINCA starts blocking impersonated Chrome UAs too, the next step is request throttling/caching, not header rotation games — record 403-rate in the extractor notes if observed.
- Reviewer should scrutinize: transport-only diff (timeouts/params/parse untouched), no test-network, and that the 7 ranking tests were NOT modified.
- **Deferred:** de-brittling the 7 `top_issue` tests per ADR-024 (assert computed-top, not fixed name) — unblocked by nothing; do it if SINCA stays hostile after stealth, so any future upstream wobble doesn't red the suite.
- **Deferred:** SINCA staleness alerting while on snapshot fallback (daily incremental series freezes) — currently visible only as warnings/top_issue.
