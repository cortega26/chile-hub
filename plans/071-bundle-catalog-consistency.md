# Plan 071: El catálogo del bundle ZIP solo declara capas realmente incluidas

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- src/builders/artifacts.py src/builders/catalog.py scripts/verify_pipeline.py tests/test_pipeline_logic.py tests/test_builders_artifacts.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: coordina con 070 (ambos tocan "qué es publicable")
- **Category**: bug
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

El ZIP publicable contiene 16 parquet pero su `dataset_catalog.json` interno
declara 19 capas con `outputs` — 3 sin archivo (`comunas_enriquecidas` alias
de `comunas`, `perfil_territorial_comunal` y `consumo_electrico_comunal`,
ambas candidate). Un consumidor que itere el catálogo del bundle (o use
`from_datapackage`/data manager) encuentra capas que no existen. El drift
viaja en cada release publicado. Confirmado leyendo el ZIP real
(`data/normalized/chile-hub-publishable-bundle.zip`).

## Current state

- `src/builders/artifacts.py:28-55` — el índice del bundle filtra por
  `public_bundle_eligible`:
  ```python
  eligible = {entry["dataset"] for entry in registry if entry.get("public_bundle_eligible")}
  ```
- `src/builders/artifacts.py:86+` — el `dataset_catalog.json` entra como
  shared artifact completo, sin filtrar.
- `src/builders/catalog.py` — produce `dataset_catalog.json` con todas las
  capas con `outputs` (incluidas candidate).
- Verificación del ZIP (existe un test de conteo de entradas,
  `artifacts.py:400-403` / `test_builders_artifacts.py`), pero no compara
  catálogo vs contenido.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build | `make build` | exit 0 |
| Verificar ZIP | `./.venv/bin/python -c "..."` (ver Step 2) | catálogo == contenido |
| Tests | `./.venv/bin/pytest tests/test_builders_artifacts.py tests/test_pipeline_logic.py -q` | all pass |
| Doctor | `make doctor` | exit 0 |

## Scope

**In scope**:
- `src/builders/artifacts.py` (o `src/builders/catalog.py` — decide en Step 1)
- `tests/test_builders_artifacts.py`
- `tests/test_chile_hub.py` (contrato del bundle si aplica)

**Out of scope**:
- El mirror HF (070).
- La landing (DIR-01).
- Cambiar `public_bundle_eligible` del registry.

## Git workflow

- Branch: `advisor/071-bundle-catalog-consistency`
- Conventional commits, uno por paso lógico.
- No push ni PR salvo instrucción del operador.

## Steps

### Step 1: Decide el punto de filtrado

Analiza si el filtro debe ir en `catalog.py` (el catálogo construido no
declara `outputs` para candidate — más limpio, pero toca la landing que
también lee el catálogo) o en `artifacts.py` (generar una variante del
catálogo para el ZIP, filtrada por `public_bundle_eligible` — menor impacto).
Recomendación: variante en `artifacts.py` (el catálogo principal queda
intacto para landing/API).

**Verify**: decisión documentada en el commit; `make build` exit 0.

### Step 2: Implementa el filtrado + test de consistencia

Genera el `dataset_catalog.json` del ZIP filtrado por `public_bundle_eligible`
(excepto el alias `comunas_enriquecidas` → `comunas`, que debe quedar con su
`outputs` apuntando al parquet real). Agrega en `tests/test_builders_artifacts.py`
un test que compare, tras `make build`, cada entrada con `outputs` del
catálogo interno del ZIP contra `zipfile.namelist()` — no debe haber entradas
sin su parquet.

**Verify**: `./.venv/bin/pytest tests/test_builders_artifacts.py -q` → all pass.

### Step 3: Verifica el bundle resultante

```bash
./.venv/bin/python - <<'PY'
import zipfile, json
z = zipfile.ZipFile("data/normalized/chile-hub-publishable-bundle.zip")
names = set(z.namelist())
cat = json.loads(z.read("data/normalized/dataset_catalog.json"))
missing = [d["dataset"] for d in cat["datasets"] if d.get("outputs")
           and f"data/normalized/{d['dataset']}.parquet" not in names
           and d["dataset"] != "comunas_enriquecidas"]
assert not missing, missing
print("catálogo del ZIP consistente:", len(cat["datasets"]), "entradas")
PY
```
**Verify**: sin missing; el ZIP sigue teniendo 16 parquet (17 con el alias).

## Test plan

- `test_bundle_catalog_matches_zip_contents` (nuevo) — el assert del Step 3
  como test parametrizado sobre el bundle real.
- Modelar sobre los tests existentes de `test_builders_artifacts.py`.
- Verificación: suite focal + `make build`.

## Done criteria

- [ ] El catálogo interno del ZIP no declara capas sin su parquet
- [ ] El alias `comunas_enriquecidas` sigue funcionando (apunta al parquet real)
- [ ] Test de consistencia existe y pasa
- [ ] `make doctor` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

- La landing o `hub_bundle.json` dependen del catálogo sin filtrar de forma
  que el filtro las rompa (verificar `app.js`).
- El test de consistencia falla por una capa legítima que debería estar
  (drift en `public_bundle_eligible`).

## Maintenance notes

- Al agregar un dataset nuevo, el contrato "catálogo del ZIP == contenido"
  queda protegido por el test — no relajar el test para acomodar drift.
- Coordinar con 070: el script HF lee el mismo catálogo; si 070 filtra por
  registry y 071 filtra el ZIP, ambos deben producir el mismo conjunto.
