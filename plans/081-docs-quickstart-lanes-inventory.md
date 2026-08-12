# Plan 081: Docs — quickstart R, marcas de carril, inventario de extractores

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 53781e2..HEAD -- docs/r-quickstart.md AGENTS.md docs/extraction-lanes.md src/builders/doc_sync.py scripts/check_agents_sync.py docs/datasets/perfil_territorial_comunal.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `53781e2`, 2026-08-12

## Why this matters

Tres inconsistencias de documentación con impacto real:
1. **`docs/r-quickstart.md` roto**: la Opción A (recomendada) hace
   `read_parquet("chile-hub-data/comunas.parquet")` pero los arcnames del ZIP
   llevan prefijo `data/normalized/`; la Opción C abre
   `chile-hub-data/chile_data.duckdb` que **no existe en el bundle** (no viaja
   .duckdb/.db/.xlsx). Un usuario R siguiendo la doc no puede consumir el
   producto.
2. **AGENTS.md §1 no marca 2 candidate**: `perfil_territorial_comunal` y
   `consumo_electrico_comunal` (este último deprecated) no llevan la marca
   `carril candidate` que sí tienen geometría/delincuencia/autoridades
   locales; la tabla canónica contradice al registry que cita.
3. **`ine_ipc.py` invisible**: AGENTS.md dice "19 extractores" (hay 20) y
   `extraction-lanes.md` omite el override INE del carril diario; el gate
   anti-drift (`doc_sync.py:305` cuenta solo `*_extractor.py`) no lo detecta.

## Current state

- `docs/r-quickstart.md:15-16,47` — rutas inexistentes (verificado contra el
  ZIP real: arcnames `data/normalized/...`, sin .duckdb).
- `AGENTS.md:57,68,69` — marcas candidate presentes; `:62,65` ausentes.
- `src/builders/doc_sync.py:305` — cuenta `*_extractor.py`;
  `EXTRACTOR_DESCRIPTIONS` (`:249-292`) sin `ine_ipc`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Sync check | `make sync-docs` | exit 0 |
| Doctor | `make doctor` | exit 0 |
| Verificar ZIP | `unzip -l data/normalized/chile-hub-publishable-bundle.zip` | ver rutas |

## Scope

**In scope**: los archivos del drift check.
**Out of scope**: decidir si el .duckdb debe viajar en el bundle (decisión de
producto — si se decide que sí, es otro plan; este plan documenta el estado
real).

## Steps

### Step 1: Corrige r-quickstart.md

Actualiza la Opción A a `chile-hub-data/data/normalized/comunas.parquet`.
Para la Opción C, reemplaza el ejemplo de `.duckdb` por consulta duckdb sobre
los parquet individuales (como ya hace el resto de la doc), o documenta
explícitamente que el .duckdb no viaja en el bundle (según la decisión de
producto).

**Verify**: `grep -n "data/normalized" docs/r-quickstart.md` → rutas reales;
`unzip -l` confirma que existen.

### Step 2: Marcas de carril en AGENTS.md

Añade "(carril `candidate`)" a las filas de perfil y consumo (y "deprecated"
a consumo), coherente con el registry. Añade el header "Carril:" al doc
`docs/datasets/perfil_territorial_comunal.md` (sus hermanas candidate lo
tienen).

**Verify**: `make doctor` exit 0 (check_agents_sync no rompe — si lo hace,
ampliar `check_layers_table` para verificar marcas contra el registry).

### Step 3: Inventario de extractores

En `doc_sync.py`, incluye `ine_ipc.py` en el conteo/inventario (o deriva el
conteo de `src/extractors/*.py` menos los 4 compartidos). Agrega una línea en
`docs/extraction-lanes.md` sobre el override INE en el carril diario.

**Verify**: `make sync-docs` regenera el árbol con 20 extractores; `make doctor` exit 0.

## Done criteria

- [ ] r-quickstart.md usa rutas reales del ZIP
- [ ] AGENTS.md marca las 5 candidate (incluida consumo como deprecated)
- [ ] El inventario de extractores cuenta `ine_ipc.py` (20)
- [ ] `make doctor` exit 0
- [ ] `plans/README.md` status row updated

## STOP conditions

- El `check_agents_sync` no puede verificar las marcas sin romper otros
  hechos — documentar y ajustar el check con cuidado.
- La decisión de producto sobre el .duckdb en el bundle no está tomada —
  documentar el estado real y dejar la decisión anotada.

## Maintenance notes

- El punto ciego del gate (módulos que no siguen la convención de nombre)
  queda cubierto al incluir `ine_ipc` explícitamente — si se agregan más
  módulos sin sufijo `_extractor`, ampliar la derivación.
