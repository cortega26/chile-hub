# Roadmap — chile-hub

> **Qué es este archivo**: el tracking vivo del trabajo de mejora. Contiene
> **instrucciones de ejecución**, el **orden en waves**, el **scoreboard** y el
> **goto por síntoma**. **No duplica contenido de planes** — el detalle
> ejecutable (pasos, verifies, STOP conditions) vive en `plans/1NN-*.md`; el
> índice ejecutor y las filas de estado por plan viven en `plans/README.md`; la
> métrica semanal en `docs/backlog/scorecard.md` y `NEXT_STEPS.md`.
>
> **Fuente de verdad del qué está en cada carril**: `data/dataset_catalog_config.json`
> y `data/source_registry.json`. **Fuente de verdad de las reglas de ingeniería**:
> `AGENTS.md`. Ante cualquier discrepancia con este roadmap, mandan esos archivos.
>
> Última reescritura: **2026-09-29** (auditoría `/improve deep`, planes 111–130).

---

## Estado actual (2026-09-29)

- **Batch activo**: auditoría `/improve deep` 2026-09-29 (commit `1464109`) →
  **20 planes (111–130)** organizados en **4 waves**. Todos `TODO`; la wave 1
  está lista para arrancar.
- **Planes previos aún abiertos** (no de este batch): 107 `READY` (handoff de
  operador) y 110 `HOLD` (patrocinios; veredicto D de la Auditoría 3, ver
  `docs/sostenibilidad/README.md`). **091 cerrada** como
  cubierta por el gate `publication` (2026-09-30); **108 y 109 DONE**.
- **Tracción de referencia**: ~2.2k **descargas**/mes PyPI (2026-09-25). Las
  domina la cadencia de releases: no son instalaciones ni usuarios (ver
  `docs/sostenibilidad/README.md`). espejo
  HF con 274 descargas (2026-09-29, registrado a mano hasta que aterrice el
  Plan 129); 21 capas publicables; DOI Zenodo aplicado
  (`10.5281/zenodo.22968698`); ~100 estrellas GitHub.
- **Posicionamiento**: chile-hub como última milla de los datos oficiales
  (ADR-023; canon en `docs/product-spec.md`). Las acciones hacia afuera están
  en "Acciones de operador" más abajo.

---

## 1. Instrucciones — cómo se ejecuta esto

### Rutina obligatoria por plan

1. **Elegir**: el primer `[ ]` de la wave activa (o el que indique el goto por
   síntoma), respetando la lista de solapes de archivos de §4.
2. **Leer el plan completo** antes de tocar nada. Correr su **drift check**
   (`git diff --stat 1464109..HEAD -- <in-scope>`): si algún archivo in-scope
   cambió y el código no coincide con los extractos de "Current state", es
   **STOP** (no improvisar).
3. **Branch**: `advisor/NNN-slug` (un plan = un branch). Commits por paso
   lógico, estilo del repo (`tipo(scope): mensaje`). **No push ni PR** salvo
   instrucción explícita del operador.
4. **Verificar**: los comandos del plan + los gates estándar de §3. Cada paso
   del plan tiene su propio verify; no se avanza con un verify en rojo.
5. **Cerrar con la rutina de `plans/README.md:77-99`**:
   1) actualizar la fila del plan en `plans/README.md`
   (`TODO → IN PROGRESS → DONE`),
   2) actualizar este ROADMAP (scoreboard + casilla del backlog) y, si aplica,
   `docs/backlog/scorecard.md` / `NEXT_STEPS.md`,
   3) **archivar** el `.md` en `plans/archive/` y sacar su fila de activos,
   4) revalidar dependencias y orden de la wave siguiente.

### Rutina por wave (para batchear y no perder el hilo)

- Una wave se abre cuando la anterior está **cerrada**: todos sus planes `DONE`
  o cerrados con razón escrita (BLOCKED/SKIP + motivo).
- **Cierre de wave**: `make doctor` + suite completa verdes, scoreboard en
  `X/X`, filas archivadas, y la lista de solapes de la wave siguiente
  revalidada (los planes pueden haber movido archivos).
- **Sesión típica**: 3–4 planes de la wave en worktrees paralelos (solo los
  disjuntos), revisar diffs, mergear cuando el operador lo confirme, actualizar
  el board, y recién entonces abrir la wave siguiente.

### Eficiencia — por qué waves y no una cola lineal

- Los planes están agrupados por **archivos disjuntos dentro de cada wave**, que
  es lo único que permite paralelizar sin conflictos de merge.
- Los planes de una wave comparten el mismo tipo de riesgo (P1 correctness,
  luego P2 seguridad/datos/deuda, luego P3), así que una revisión enfocada
  alcanza para todo el lote.
- Un plan de una wave posterior que dependa de otro (p. ej. 125 necesita la red
  de tests de 123) nunca se adelanta: la dependencia está escrita en §4.

---

## 2. Auditoría `/improve deep` 2026-09-29 — planes 111–130

> **Qué es**: re-auditoría profunda (9 subagentes read-only, una categoría del
> playbook cada uno) + vet del advisor contra el código en vivo. El mantenedor
> pidió planes para **todos los hallazgos net-positivos** → 20 planes.
> **Qué no es**: no agrega datasets (ADR-011/anti-patrón #10), no toca
> carriles, no re-litiga los rechazos listados en §8.
>
> Los hallazgos ya rechazados en auditorías previas no se repitieron; el único
> dato corregido del reporte de subagentes fue MkDocs Material (EOL extendido a
> may-2027; watch item, §8).

### Scoreboard — única tabla viva (actualizar en cada cierre)

| Wave | Planes | Contenido | Done | Estado |
|------|--------|-----------|------|--------|
| **W1** | 111, 115, 116, 118, 122, 127 | P1: seguridad de release, superficie pública, CI/tests, docs | 6/6 | **DONE (2026-09-29, mergeada a `main`; suite 1167 + gates verdes)** |
| **W2** | 112, 113, 114, 119, 124, 126, 128 | P2: pins/hardening, fuente/MCP, DatasetSpec, tooling, deps | 6/7 + 128 parcial | **DONE (2026-09-29)**; 128 Step 2 DONE, Step 1 BLOCKED al 2026-10-01 |
| **W3** | 117, 120, 121, 123, 125, 129 | P2/P3: decisión archived, perf, tests de gates, dirección | 6/6 | **DONE (2026-09-29, mergeada a `main`; suite 1239 + gates verdes)** |
| **W4** | 130 | P3: dejar de versionar el ZIP (requiere decisión) | 1/1 | **DONE (2026-09-29, decisión del operador = asset de Release; mergeada)** |
| **Total** | 111–130 | | **19/20 + 128 parcial** | W1–W4 cerradas; solo resta 128 Step 1 (Python 3.15) al 2026-10-01 |

### Backlog por wave (orden de ejecución)

**Wave 1 — P1, planes disjuntos (paralelizable en worktrees):**

- [x] **111** [Gate de identidad `workflow_run` + ancestría de artifacts](plans/archive/111-workflow-run-identity-gate.md) — P1/S-M/MED — un artifact de PR de fork no puede entrar al Release/HF. — ✅ mergeado en `main` (661d77c+3a6f49d+4a40723; merge `ae1e12c`).
- [x] **115** [Superficie generada: año "2.024", playground, URL base](plans/archive/115-generated-surface-fixes.md) — P1/S/LOW — fix visible en 346 fichas + SQL Explorer. — ✅ mergeado en `main` (832bd6f+96a24f8; merge `b007cac`).
- [x] **116** [Commitear `mapa_comunal.geojson` en el refresh de geometría](plans/archive/116-mapa-comunal-geojson-commit.md) — P1/S/LOW — el mapa deja de divergir del parquet. — ✅ mergeado en `main` (4afef66; fast-forward).
- [x] **118** [Vitales: fetch incremental](plans/archive/118-vitales-incremental-fetch.md) — P1/S-M/MED — ~89 s/día y ~28 MB/día menos. — ✅ mergeado en `main` (14ec4ff+3526884; merge `18adc2d`).
- [x] **122** [Cobertura `scripts/`, smoke MCP, xdist en CI](plans/archive/122-ci-test-integrity.md) — P1/S-M/LOW-MED — la señal de tests deja de mentir. — ✅ mergeado en `main` (023c437+8ace7fc; merge `70453c9`).
- [x] **127** [Correcciones de docs canónicos (7)](plans/archive/127-docs-corrections-batch.md) — P1/S/LOW — AGENTS/installation/NEXT_STEPS/links. — ✅ mergeado en `main` (b1df764+7d172a3; merge `5f6a855`).

**Wave 2 — P2 (114 → 113 secuencial; el resto paralelo; 126 después de 122):**

- [x] **112** [Pinnea entornos efímeros de CI](plans/archive/112-pin-ephemeral-ci-installs.md) — P1/S/LOW — ✅ mergeado en `main` (`f0e8746`; FF).
- [x] **114** [Fuentes self-hosted + privacidad](plans/archive/114-self-host-fonts-privacy.md) — P2/S-M/LOW — ✅ mergeado en `main` (`d51f721`; FF).
- [x] **113** [Hardening batch: unrar, vaciado HF, JSON-LD, quoting](plans/archive/113-security-hardening-batch.md) — P2/S/LOW — ✅ mergeado en `main` (`ba85f3c`+`6ddb705`+`223dfe1`+`d614467`; merge `4f78d0a`).
- [x] **119** [Caché Parquet en el servidor MCP](plans/archive/119-mcp-parquet-cache.md) — P2/S/LOW — ✅ mergeado en `main` (`3e766b3`; merge `11aa716`).
- [x] **124** [DatasetSpec: 3 specs + gate catálogo↔spec](plans/archive/124-datasetspec-gate.md) — P2/M/LOW — ✅ mergeado en `main` (`1121cdc`; merge `3fc0381`).
- [x] **126** [Higiene tooling/onboarding](plans/archive/126-tooling-onboarding-hygiene.md) — P1-P2/S-M/LOW — ✅ mergeado en `main` (`5ec16bb`…`8b2a634`; FF).
- [~] **128** [Python 3.15 + DuckDB-Wasm](plans/128-deps-forward-compat.md) — P1/P3/S/M/LOW-MED — ◐ Step 2 (DuckDB-Wasm 1.32.0) mergeado (`915ee8c`; merge `d8f7d7a`); Step 1 (3.15) BLOCKED hasta 2026-10-01.

**Wave 3 — P2/P3:**

- [x] **117** [Alinear `source_mode: archived`](plans/archive/117-archived-source-mode-alignment.md) — P2/S-M/LOW-MED — ✅ mergeado en `main` (`7fc72b0`; FF, Rama A).
- [x] **120** [`check_sources` paralelo + caché de geometría](plans/archive/120-core-perf-diagnostics-cache.md) — P3/S/LOW — ✅ mergeado en `main` (`da4be85`; FF).
- [x] **121** [Lighthouse: performance + artefacto](plans/archive/121-lighthouse-performance-baseline.md) — P3/S/LOW — ✅ mergeado en `main` (`9c26728`; merge `2942668`).
- [x] **123** [Backfill de tests de gates](plans/archive/123-gate-test-backfill.md) — P2/M/LOW-MED — ✅ mergeado en `main` (`81701a6`; merge `057ebf4`).
- [x] **125** [Consolidar `write_staging`](plans/archive/125-consolidate-write-staging.md) — P2/M/LOW-MED — ✅ mergeado en `main` (`9ff7255`; merge `19d7af0`).
- [x] **129** [Cierres de distribución: HF metric, registry MCP, `resolve_regiones`](plans/archive/129-direction-distribution-closes.md) — P2/S-M/LOW — ✅ mergeado en `main` (`e2ef696`+`d64def0`+`5203d3a`+`62b1ff1`; FF, con 1 revisión de mypy).

**Wave 4 — decisión:**

- [x] **130** [Dejar de versionar el ZIP publicable](plans/archive/130-stop-committing-bundle-zip.md) — P3/S-M/MED — ✅ mergeado en `main` (`2fb7d15`; FF), decisión del operador = asset de Release; extra: sync de `server.json` en el release (`54c1691`).

### Decisiones pendientes (operador)

| # | Decisión | Default del advisor | Efecto si no llega |
|---|----------|---------------------|--------------------|
| 130 | ¿La descarga del ZIP en la landing apunta al asset de Release/HF? | Sí (el ZIP de repo deja de actualizarse; Release sí) | El plan se cierra sin cambios |
| 117 | Rama A (alinear docs con ADR-015) vs Rama B (implementar `archived`) | Rama A (refleja el código) | Se ejecuta Rama A y se deja constancia |
| 128 | Step 1 (3.15) después del 2026-10-01 | Sí | Step 1 queda BLOCKED; Step 2 corre igual |
| 111 | Edita workflows privilegiados (release/HF) | Requiere revisión del mantenedor antes del merge | El plan queda implementado en branch |
| 091 | Opcionales estrictos — decisión | **Cerrada (2026-09-30): cubierta por el gate `publication`** | — |
| — | MkDocs Material → Zensical | Watch item; decidir antes de may-2027 | Ninguno hoy |

---

## 3. Gates estándar (obligatorios antes de cerrar cualquier plan)

```bash
make lint && make format-check     # estilo
make doctor                        # dependencias + gates anti-drift
./.venv/bin/pytest <tests del plan> -v   # verificación focal
```

Para planes que tocan pipeline/datos (`build_dev_db.py`, validaciones,
extractores, catálogo) agregar además `make build` y `make verify` cuando el
plan lo pida. Para la landing: `make verify-landing`. Nunca commitear con un
gate en rojo: el plan que falla se marca `BLOCKED` con el error exacto y se
sigue con el próximo de la wave.

---

## 4. Dependencias y solapes de archivos (no correr en worktrees simultáneos)

**Dependencias duras (orden obligatorio):**

- `122 → 126`: ambos editan `.github/workflows/pipeline-check.yml`.
- `122 → 123`: la cobertura de `scripts/` (122) es la señal que hace visible el
  backfill (123).
- `123 → 125`: los tests del merge de `calidad_aire` son la red antes de tocar
  los overrides de `write_staging`.
- `128 Step 1` requiere Python 3.15 final (2026-10-01). Step 2 es independiente.
- `130` requiere la decisión de Step 0 (y va después de 114: ambas tocan
  `index.html`).

**Solapes de archivos (secuenciar, aunque estén en la misma wave):**

| Archivo | Planes | Regla |
|---------|--------|-------|
| `pipeline-check.yml` | 122, 126 | 122 primero |
| `index.html` / `landing.py` / `inject_dataset_json_ld.py` | 114, 115, 113, 130 | 114 → 115 → 113 → 130 |
| `AGENTS.md` | 124, 127 | 124 primero |
| `src/chile_hub/core.py` | 120, 129 | 120 primero (ambos son aditivos, pero secuenciar evita conflictos) |

El resto de cada wave es disjunto y puede correr en paralelo (un worktree por
plan, branch `advisor/NNN-slug`).

### Grafo resumido

```
W1:  111  115  116  118  122  127          (6 planes disjuntos)
                       │
                       ▼
W2:  122→126 ; 114→113 ; 112  119  124  128
                              │
                              ▼
W3:  117  120  121  123→125  129
                              │
                              ▼
W4:  130 (decisión)
```

---

## 5. Planes previos activos (no pertenecen a esta auditoría)

| # | Plan | Estado | Nota |
|---|------|--------|------|
| 107 | Handoff de activación de lanzamiento | READY | Issues de leads #107/#108/#109 creados; ejecución por agente externo |
| 108 | Gate "Check build-synced files" bloquea el publish diario | DONE | Mergeado en PR #110 (`7652568`, merge `4528872`); ADR-022 |
| 109 | README sin datos volátiles + alerta de schedule roto | DONE | `efad585`+`cbeb572` (revisión), merge `509a123`; Parte C descartada sin caso concreto |
| 110 | Programa de patrocinios | HOLD | Decisión del mantenedor (2026-09-30): sin búsqueda activa por 0 evidencia de adopción; **revisión 2026-11-01**; índice en `docs/sostenibilidad/README.md` |
| 091 | Opcionales estrictos + fallback sintético strict | REJECTED | Cerrada 2026-09-30: cubierta por el gate `publication` |

Detalle execrable de estos en `plans/README.md` y sus `.md`.

---

## 6. Goto por síntoma

| Quiero… | Ir a |
|---------|------|
| ejecutar lo siguiente | primer `[ ]` del backlog de la wave activa (§2) + su `plans/1NN-*.md` |
| saber el estado | Scoreboard (§2) |
| entender cómo batchear / cerrar | Instrucciones (§1) |
| detalle ejecutor de un plan | `plans/1NN-*.md` (self-contained) + `plans/README.md` |
| ver filas de estado por plan | `plans/README.md` ("Planes activos") |
| métrica semanal / avance | `docs/backlog/scorecard.md` + `NEXT_STEPS.md` |
| contexto rápido del repo | `SOURCE_OF_TRUTH.md` → `AGENTS.md` |
| agregar un dataset | `AGENTS.md §5` + `docs/dataset-inclusion-criteria.md` (normativo) |
| entender carriles/estados | `docs/dataset-inclusion-criteria.md` + `data/source_registry.json` |
| seguridad/release CI | Planes 111, 112, 113 |
| canales de distribución previos (HF/SEO/MCP/DOI) | Historial cerrado (§7) |
| por qué NO se hace algo | Rechazados (§8) |

---

## 7. Acciones de operador (hacia afuera, sin código)

Del posicionamiento 2026-09-29 (ADR-023); requieren la cuenta del mantenedor:

- [ ] **2026-11-01** — Revisar el tema de sostenibilidad/sponsors (decisión 2026-09-30: sin búsqueda activa por 0 evidencia de adopción; ver `docs/sostenibilidad/README.md`).

- [ ] Registrar chile-hub en "Reutilización" de datos.gob.cl (ingreso con ClaveÚnica).
- [ ] Pedir la delincuencia comunal estructurada del CEAD por "Sugerencias" de
  datos.gob.cl o por la Ley 20.285, en vez de scrapearla.
- [ ] Reportar con "Notifica un error" el bulk 2015 de delincuencia en datos.gob.cl
  (tiene enlaces muertos).
- [ ] Opcional: presentar el proyecto a la mesa de ayuda de la Secretaría de
  Gobierno Digital y preguntar por el estado de la norma técnica de datos abiertos.
- [x] Zenodo: concept DOI `10.5281/zenodo.22968698` aplicado en `CITATION.cff`,
  `docs/citation.md` y badge del README (2026-09-26).

---

## 8. Historial cerrado (no re-ejecutar)

> Las waves cerradas quedan acá como registro; sus planes viven en
> `plans/archive/`. No se actualizan.

- **Distribución 2026-09-25 (101–105)** — DONE: subsets HF + `hf://` (`5c3fd32`),
  JSON-LD/sitemap/`llms.txt` (`528220f`), citación + DOI (`edd41a3`), servidor
  MCP (`25b00ed`), páginas por comuna (`330786e`). Branch
  `advisor/distribution-wave-1`.
- **Infra 2026-09-25 (106–107)** — 106 DONE (snapshot de release 412→140 MB,
  ADR-021); 107 READY (ver §5).
- **Auditoría 2026-09-15 (086–100)** — DONE salvo 091 (REVERTED, §5): Wave 1
  086–090, Wave 2 092/093, Wave 3 094–096, Wave 4 097/098, Wave 5 099/100,
  Wave 6 077–079. Bandit 0 issues; suite ~1037 tests verdes.
- **Auditorías 2026-06 a 2026-08 (024–085)** — DONE/archivadas en su totalidad;
  ver secciones "Planes archivados" en `plans/README.md`.
- **CI**: el deadlock del gate "Check build-synced files" quedó resuelto (ADR-022,
  plan 108 DONE) y el plan 109 (README estable + alerta de schedule roto) quedó
  DONE el 2026-09-30.
- **Migración de arquitectura — Phase 4** (`ExtractionResult` tipado): rama
  `feat/phase4-extraction-result` mergeada el 2026-09-30 (`a5669b6`).

---

## 9. Rechazados (no re-auditar)

| Hallazgo | Motivo |
|----------|--------|
| **MkDocs Material → Zensical (migración)** | El EOL se extendió a **2027-05-05** (anuncio 2026-09-29); mantención crítica vigente. Watch item: reabrir solo si se acerca la fecha sin decisión. |
| Conflicto `click` dev-vs-scraping | By-design (`pyproject.toml` + `conflicts` + entorno efímero en CI). El Plan 112 pinea ese entorno, no lo elimina. |
| Duplicado `shapely`/`geopandas` (pipeline+geo) | Intencional: expone `resolve_by_coords()` al consumidor. |
| Lock drift | Limpio (`uv lock --locked` + gate en CI). |
| `validate_puntos_interes` huérfana | Exención documentada en `check_validation_registration.py`. |
| Deps abandonadas / APIs deprecadas | Sin evidencia (auditorías 2026-09-15 y 2026-09-29). |
| `build_freshness` duplicado | Ya delega en `compute_freshness`. |
| Kaggle / conda-forge | Diferidos: el Plan 129 habilita medir HF ("≥270/mes sostenido"); sin esa señal no se reabre. |
| Telemetría en el paquete | Rechazado por ética de apertura; la adopción se mide solo por APIs públicas. |
| API premium / paywall | Rechazado (el dato es CC-BY y pequeño). |
| README/docs en inglés | Rechazado: producto y audiencia primaria chilenos. |
| Datasets nuevos sobre fuentes frágiles | Gated por ADR-011/anti-patrón #10; los leads viven como issues `dataset_request`. |
| Builds incrementales / build paralelo (PERF-01/04) | Diferidos: sin telemetría de duración y timeout de CI <45 min. Reconsiderar con medición. |
| PERF-05/06/07/08, SEC-02/03 antiguos | Micro-optimizaciones o riesgo acotado; documentados en auditorías previas. El ZIP (PERF-16) sí quedó en el Plan 130. |
| Firma/atestación de artifacts (sigstore) | Deferred en el Plan 111; reabrir si entra un segundo publicador. |

---

*Este archivo se actualiza en cada cierre de plan/wave (ver §1), no en una
fecha fija. Para la fecha real de la última modificación:
`git log -1 --format=%ad -- ROADMAP.md`.*
