# Plan 006: Consolidar lógica duplicada y corregir violación de capas

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.

> **Drift check (run first)**:
> `git diff --stat ba2f434..HEAD -- src/pipeline_status_utils.py src/chile_hub.py src/build_dev_db.py src/extractors/subdere_extractor.py src/extractors/bcentral_extractor.py`
> If any of these files changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (pero 005 toca build_dev_db.py — coordinar orden)
- **Category**: tech-debt
- **Planned at**: commit `ba2f434`, 2026-06-13

## Why this matters

Tres formas de duplicación y una violación arquitectónica crean riesgo de
divergencia y mantenimiento frágil:

1. **Top-issue duplicado**: `pipeline_status_utils.py:83` y
   `chile_hub.py:72` implementan la misma lógica de priorización con
   pequeñas diferencias (una usa `freshness_status` del build, la otra
   `current_freshness_status` de runtime). Si se agrega un nuevo tier
   de prioridad, hay que actualizar dos lugares.

2. **Freshness duplicado**: `build_dev_db.py:208` y `chile_hub.py:792`
   computan `age_hours` y `fresh/stale/unknown` con la misma fórmula pero
   en implementaciones separadas.

3. **Violación de capas**: los extractores (`subdere_extractor.py:669` y
   `bcentral_extractor.py:403`) importan `validate_comunas` y
   `validate_indicadores` desde `src.build_dev_db`, creando una dependencia
   inversa (extracción depende de build). Las funciones de validación deben
   vivir en un módulo neutral.

## Current state

### Duplicación de top_issue

- `src/pipeline_status_utils.py:83-115`:

```python
def compute_top_issue(entries):
    if not entries:
        return None

    def attention_priority(entry):
        warning_count = entry.get("warning_count", 0) or 0
        freshness_status = entry.get("freshness_status")
        drift_status = entry.get("drift_status")
        degradation_status = entry.get("degradation_status")
        if warning_count > 0 or freshness_status in {"stale", "unknown"}:
            return 0
        if drift_status == "drifted" or degradation_status in {"warning", "degraded"}:
            return 1
        return 2

    ordered = sorted(
        entries, key=lambda entry: (attention_priority(entry), entry.get("dataset", ""))
    )
    top_entry = ordered[0]
    priority = attention_priority(top_entry)
    if priority >= 2:
        return None
    return { ... }
```

- `src/chile_hub.py:72-122`:

```python
def top_issue(self):
    ...
    candidates = []
    for entry in self.summary():
        ...
        priority = self._attention_priority_for_dataset(entry, current_status)
        candidates.append({...})

    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda item: (item["attention_priority"], item["dataset"]))
    if ordered[0]["attention_priority"] >= 2:
        return None
    return ordered[0]
```

Con `_attention_priority_for_dataset()` en `chile_hub.py:72-80` usando
`current_freshness_status` en vez de `freshness_status`.

### Duplicación de freshness

- `src/build_dev_db.py:208-225`:

```python
def build_freshness(refreshed_at_utc, max_age_hours):
    refreshed_at = parse_iso_datetime(refreshed_at_utc)
    if refreshed_at is None or max_age_hours is None:
        return {"status": "unknown", ...}
    checked_at = datetime.now(UTC)
    age_hours = max((checked_at - refreshed_at).total_seconds() / 3600, 0)
    return {"status": "fresh" if age_hours <= max_age_hours else "stale", ...}
```

- `src/chile_hub.py:799-806` (dentro de `freshness_audit()`):

```python
age_hours = round(max((checked_at - refreshed_at).total_seconds() / 3600, 0), 2)
current_status = "fresh" if age_hours <= max_age_hours else "stale"
```

### Violación de capas

- `src/extractors/subdere_extractor.py:669`:

```python
def validate(self, df, metadata: dict) -> dict:
    from src.build_dev_db import validate_comunas
    return validate_comunas(df, metadata)
```

- `src/extractors/bcentral_extractor.py:403`:

```python
def validate(self, df, metadata: dict) -> dict:
    from src.build_dev_db import validate_indicadores
    return validate_indicadores(df, metadata)
```

Las funciones `validate_comunas` (línea 413), `validate_regiones` (447),
`validate_provincias` (463) y `validate_indicadores` (479) están definidas
en `src/build_dev_db.py`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Run extractors | `make extract` | exit 0 |
| Run build | `make build` | exit 0 |
| Verify artifacts | `make verify` | exit 0 |
| Run tests | `make test` | exit 0 |
| Run lint | `make lint` | exit 0 |

## Scope

**In scope** (files to modify):
- `src/build_dev_db.py` — extraer funciones de validación a un nuevo módulo;
  actualizar imports
- `src/validation.py` — **CREAR**: contiene `validate_comunas`,
  `validate_regiones`, `validate_provincias`, `validate_indicadores`
- `src/pipeline_status_utils.py` — actualizar `compute_top_issue` para ser
  reutilizada desde `chile_hub.py`; extraer `build_freshness` compartido
- `src/chile_hub.py` — eliminar `_attention_priority_for_dataset()` y
  `top_issue()` duplicados; usar la versión compartida
- `src/extractors/subdere_extractor.py` — cambiar import de
  `src.build_dev_db` a `src.validation`
- `src/extractors/bcentral_extractor.py` — mismo cambio de import
- `tests/test_pipeline_logic.py` — actualizar imports de validación
- `tests/test_chile_hub.py` — actualizar import de `validate_indicadores`

**Out of scope** (do NOT touch):
- Cambios en el comportamiento de las validaciones — solo se mueven de lugar.
- `src/extractors/base.py` — no se modifica en este plan.
- Cambios en la API pública de `ChileHub` — `top_issue()` debe mantener
  exactamente el mismo contrato (mismos campos de retorno).

## Steps

### Step 1: Crear `src/validation.py` con las funciones de validación

Mover estas funciones desde `src/build_dev_db.py` al nuevo archivo
`src/validation.py`:

- `validate_comunas(df, metadata)` (líneas 413-444)
- `validate_regiones(df_regiones)` (líneas 447-460)
- `validate_provincias(df_provincias)` (líneas 463-476)
- `validate_indicadores(df_indicadores, metadata)` (líneas 479-524)

El nuevo archivo debe importar:
- `os` (no lo necesita realmente, pero por si acaso)
- `polars as pl` (para type hints implícitos)
- Las constantes `EXPECTED_LIVE_COMUNAS_COUNT`, `FALLBACK_COMUNAS_COUNT`,
  `EXPECTED_INDICATOR_CODES` desde `src.build_dev_db` (o moverlas también).

**Alternativa más limpia**: mover también las constantes a `src/validation.py`:

```python
EXPECTED_INDICATOR_CODES = {"uf", "dolar", "euro", "utm", "ipc"}
FALLBACK_COMUNAS_COUNT = 18
EXPECTED_LIVE_COMUNAS_COUNT = 346
```

Y en `build_dev_db.py`, re-importarlas desde `src.validation`.

**Verify**: `make lint` → exit 0. Los imports deben resolverse correctamente.

### Step 2: Actualizar imports en todos los callers

Actualizar los imports en:

- `src/build_dev_db.py`: `from src.validation import (validate_comunas,
  validate_regiones, validate_provincias, validate_indicadores,
  EXPECTED_INDICATOR_CODES, FALLBACK_COMUNAS_COUNT, EXPECTED_LIVE_COMUNAS_COUNT)`
- `src/extractors/subdere_extractor.py:669`: cambiar a
  `from src.validation import validate_comunas`
- `src/extractors/bcentral_extractor.py:403`: cambiar a
  `from src.validation import validate_indicadores`
- `tests/test_chile_hub.py:19`: cambiar a
  `from src.validation import validate_indicadores`
- `tests/test_pipeline_logic.py`: actualizar todos los imports de funciones
  de validación y constantes.

**Verify**: `make build && make test` → exit 0. Todos los tests pasan.

### Step 3: Extraer `compute_freshness()` compartido

En `src/pipeline_status_utils.py`, crear una función `compute_freshness()`:

```python
def compute_freshness(refreshed_at_utc, max_age_hours, checked_at=None):
    """Retorna dict con status (fresh/stale/unknown), age_hours, max_age_hours, checked_at_utc."""
    if checked_at is None:
        checked_at = datetime.now(UTC)
    refreshed_at = parse_iso_datetime(refreshed_at_utc)
    if refreshed_at is None or max_age_hours is None:
        return {
            "status": "unknown",
            "age_hours": None,
            "max_age_hours": max_age_hours,
            "checked_at_utc": checked_at.isoformat(),
        }
    age_hours = max((checked_at - refreshed_at).total_seconds() / 3600, 0)
    return {
        "status": "fresh" if age_hours <= max_age_hours else "stale",
        "age_hours": round(age_hours, 2),
        "max_age_hours": max_age_hours,
        "checked_at_utc": checked_at.isoformat(),
    }
```

Actualizar `build_freshness()` en `build_dev_db.py` para delegar en
`compute_freshness()`.

Actualizar `ChileHub.freshness_audit()` en `chile_hub.py` para usar
`compute_freshness()` en vez de la fórmula inline.

**Verify**: `make build && make test` → exit 0. El freshness audit y el
build deben producir los mismos resultados.

### Step 4: Unificar top_issue en pipeline_status_utils

Hacer que `ChileHub.top_issue()` y `ChileHub._attention_priority_for_dataset()`
deleguen en `compute_top_issue()` de `pipeline_status_utils`.

El desafío: el `top_issue()` de `ChileHub` usa `current_freshness_status` del
runtime freshness audit, mientras que `compute_top_issue()` usa
`freshness_status` del build.

Solución: parametrizar el campo de freshness. Agregar un parámetro
`freshness_field="freshness_status"` a `compute_top_issue()`:

```python
def compute_top_issue(entries, freshness_field="freshness_status"):
    def attention_priority(entry):
        warning_count = entry.get("warning_count", 0) or 0
        freshness_status = entry.get(freshness_field)
        ...
```

En `build_hub_health()`, llamar con el default (`"freshness_status"`).
En `ChileHub.top_issue()`, construir entries con el campo
`freshness_status` poblado desde `current_freshness_status` y llamar a
`compute_top_issue(entries)`.

**Verify**: `make test` → exit 0. Los tests `test_top_issue`,
`test_top_issue_table`, `test_overview`, `test_bundle_summary` deben
seguir pasando con los mismos valores.

### Step 5: Ejecutar el pipeline completo

**Verify**: `make refresh` → exit 0. Todos los artifacts se generan
correctamente. `make lint` → exit 0.

## Test plan

- Los tests existentes son la red de seguridad: `make test` debe pasar
  exactamente igual que antes.
- `tests/test_pipeline_logic.py::ValidatorTests` — cubre todas las funciones
  de validación; después del movimiento deben seguir pasando.
- `tests/test_chile_hub.py::ChileHubTests` — cubre `top_issue()`,
  `freshness_audit()`, `summary()`; deben producir los mismos resultados.
- Si algún test falla, verificar que los imports se actualizaron
  correctamente y que las funciones movidas no cambiaron de comportamiento.

## Done criteria

- [ ] `src/validation.py` existe con las 4 funciones de validación y las 3
      constantes
- [ ] `src/build_dev_db.py` importa validaciones desde `src.validation`
- [ ] Los extractores importan desde `src.validation`, no desde
      `src.build_dev_db`
- [ ] `compute_freshness()` existe en `src/pipeline_status_utils.py` y es
      usada por `build_dev_db.build_freshness()` y
      `chile_hub.ChileHub.freshness_audit()`
- [ ] `compute_top_issue()` acepta `freshness_field` como parámetro y es
      usada por `build_hub_health()` y `ChileHub.top_issue()`
- [ ] `ChileHub._attention_priority_for_dataset()` es eliminada (su lógica
      está en `compute_top_issue()`)
- [ ] `make refresh` sale con exit 0
- [ ] `make test` sale con exit 0
- [ ] `make lint` sale con exit 0

## STOP conditions

Stop and report back (do not improvise) if:

- Los excerpts de "Current state" no coinciden con el código actual.
- Mover las funciones de validación rompe tests (verificar imports primero).
- La unificación de `compute_freshness()` produce resultados diferentes a
  los originales (posible si hay diferencias sutiles en el manejo de
  timezone o redondeo).
- La unificación de `compute_top_issue()` cambia el resultado de
  `top_issue()` en los tests (indicaría que la parametrización del campo
  de freshness no es suficiente).
- `make refresh` falla en cualquier paso.

## Maintenance notes

- Si se agrega un nuevo dataset con su propia validación, la función
  `validate_{nombre}()` debe ir en `src/validation.py`.
- Si se modifica la política de priorización de top_issue (nuevos tiers),
  solo hay que modificar `compute_top_issue()` en `pipeline_status_utils.py`.
- `compute_freshness()` acepta un parámetro `checked_at` para testing; si no
  se provee, usa `datetime.now(UTC)`. Esto facilita tests deterministas.
- Los extractores ya no dependen del módulo build — esto permite en el
  futuro mover `build_dev_db.py` a un paquete separado sin romper los
  extractores.
