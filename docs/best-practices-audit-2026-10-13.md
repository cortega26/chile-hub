# Auditoría de mejores prácticas de software — chile-hub (2026-10-13)

**Alcance:** `src/`, `scripts/`, `tests/` y la configuración de gates
(`pyproject.toml`, `.pre-commit-config.yaml`, CI). Fuera de alcance: la landing
(`index.html`/`app.js`, cubierta por Lighthouse/Playwright) y los datos publicados.
**Commit de referencia:** `886a062` (v1.49.0). **Naturaleza:** auditoría read-only;
las remediaciones viven en los planes [`131`–`138`](../plans/README.md).
**Herramientas:** ruff 0.17.0 y mypy 2.4.0 (pins del lock), `radon@6.0.1`,
`vulture@2.14`, `pylint@3.3.8`, `interrogate` 1.7.0, métricas AST propias.
Comandos de reproducción en el Anexo A.

## Resumen ejecutivo

chile-hub es **operativamente ejemplar y estructuralmente divergente**: la capa
de proceso (1 370 tests, guardrails con incidente documentado, CI autosanable
ADR-024, pins de dependencias) es de primer nivel; la capa de código muestra el
patrón clásico de un repo que creció rápido y cuyos gates nunca se apretaron:
**cinco módulos concentran casi toda la complejidad**, hay duplicaciones de
hechos concretas y una decena de olores de correctitud, y los gates de
lint/tipos no tienen trinquete.

| Riesgo (ordenado) | Evidencia principal |
|---|---|
| 1. Correctitud: bugs latentes y silencios | B023 ×2 (closure sobre variable de loop), `except Exception: pass` en registro SQL, `lru_cache` sobre métodos (fuga), `date.today()` ×3, `subprocess.run` sin `check` ×2 |
| 2. Cinco módulos dios | `core.py` 2 078 L / 77 métodos (MI C), `validation.py` 1 960 L (MI C), `verify_pipeline.py` 1 961 L (MI C), `pipeline_status_utils.py` 1 022 L (MI B), `verify_landing.py` 913 L + **función de 739 líneas** |
| 3. Fuentes de verdad duplicadas | mapa de regiones copiado como fallback, muestra SINIM ×2, `SCHEMA` de extractores ×2, mapeo artefacto→formato ×2, unpacking `dfs[...]` ×3 |
| 4. Gates sin trinquete | ruff solo `E,W,F,I`; `mypy --strict` = **767 errores**; `interrogate` no bloqueante (44 %); sin gate de complejidad ni de duplicación |

## Lo que ya está sano (no tocar)

- **Cultura de guardrails:** cada incidente de CI deja test + docstring con
  PR/run; política de autosanación (ADR-024) vigente.
- **Cero código muerto** (`vulture` ≥80 % conf: 0 hallazgos) y **cero `assert`
  en `src/`** (el estilo unittest en tests, PT009 ×2 862, es convención
  consistente, no deuda).
- **Distribución sana de funciones**: 2 420 funciones, mediana 10 líneas, p90
  37; la cola de funciones >100 líneas (41) está concentrada en los módulos
  listados — el problema es de concentración, no sistémico.
- **Tests**: 1 370 passing, cobertura real 73.3 % (badge), `hypothesis` en uso,
  characterization harness offline (Phase 1).
- **Dependencias y CI**: pins exactos + `uv.lock`, smoke MCP, profiles de
  verificación de publicación.

## Hallazgos

Severidad: 🔴 alta · 🟠 media · 🟡 baja. Esfuerzo: S/M/L.

### 1. Correctitud y robustez (Zen: los errores nunca deben pasar en silencio)

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| C1 | Closure sobre variable de loop en `_extract_number`/`cells`: seguro solo si se invoca antes de la siguiente iteración | `src/extractors/sinim_finanzas_live_extractor.py:301,303` (B023) | 🔴 | 131 |
| C2 | `except Exception: pass` al registrar vistas SQL: datasets sin Parquet se omiten en silencio | `src/chile_hub/core.py:589` | 🟠 | 131 |
| C3 | `lru_cache(maxsize=1)` en 11 métodos de instancia: el caché retiene `self` → instancias no liberables (fuga real para consumidores de librería) | `core.py:148-190` (B019 ×11) | 🟠 | 134 |
| C4 | Estado global mutable `_LAST_FETCH_MODE` / `_LAST_SENTINEL_DROP_COUNT` en extractores; `ExtractionResult` (Phase 4) existe para portar esto | `estadisticas_vitales_extractor.py:603`; `res_extractor.py:188,323` | 🟠 | 133 |
| C5 | 49 `except` amplios/desnudos (34 en `src`+`scripts`); faltan 11 `raise … from` (trazabilidad) | BLE001/B904 | 🟡 | 131 |
| C6 | `date.today()` ×3 (política UTC del repo) y `subprocess.run` sin `check` ×2 | `bcentral_extractor.py:505,510`; `res_extractor.py:190`; `mineduc_*_extractor.py` (PLW1510) | 🟡 | 131 |
| C7 | ISC004 ×14: muestras revisadas son concatenciones intencionales (falsos positivos), pero conviene parentizar para desambiguar | `core.py:716`; `doc_sync.py:433` | 🟡 | 131 |

### 2. SOLID / arquitectura

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| A1 | `ChileHub` es una clase dios: 77 métodos que mezclan *artifact store* (13 loaders cacheados), motor de consulta (`sql`/`cross_view`/`resolve_*`), contratos (`validate*`/`frictionless*`) y **presentación** (`summary_table`, `snapshot_text/table`, tablas). Partir por responsabilidad manteniendo la API pública como fachada | `core.py` 2 078 L, MI C (0.00), 23 % docstrings | 🔴 | 134 |
| A2 | `validation.py`: 33 funciones / 25+ validadores en un archivo, MI C. El registro ya existe conceptualmente (`check_validation_registration.py`, DatasetSpec); convertir a paquete con fachada de re-export | 1 960 L, sin docstring de módulo | 🟠 | 135 |
| A3 | Los dos verificadores de publicación divergieron: `verify_pipeline.py` (MI C, 1 961 L) y `verify_landing.py` (MI C 3.88, `verify_landing()` de **739 líneas**, 7 % docs) sin utilidades compartidas. Es la última línea de defensa antes de publicar: lo más mantenible debe vivir ahí | radon + AST | 🟠 | 136 |
| A4 | `pipeline_status_utils.py` (MI B 16.6, 17 % docs) es un cajón de reportes; extraer junto a A2 | 1 022 L / 35 funciones | 🟠 | 132 |

### 3. KISS / complejidad

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| K1 | God functions: `cli._main` **F(79)**, `_parse_comuna_sheet` F(61), `build_hub_health` F(53), `_load_inputs` E(34)/**364 L**, `parse_dataset_spec` E(39), `verify_landing()` 739 L, `build_dataset_metadata` **443 L** | radon cc + AST | 🔴 | 132, 133, 134, 136 |
| K2 | 44 `C901` + 32 `too-many-branches` + 27 `too-many-statements`: **sin gate de complejidad**; decomponer sin trinquete regresa | ruff ALL | 🟠 | 132 (enable C901) |
| K3 | `build_parser` 344 L y `_main` 308 L (`pragma: no cover`): registry de handlers por comando | `cli.py:72,418` | 🟠 | 132 |

### 4. DRY (adjudicado: solo duplicaciones reales)

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| D1 | **Mapa de alias de regiones duplicado** como copia de fallback (`except ModuleNotFoundError`) en extractores → dos fuentes que pueden divergir en silencio (normalización de joins) | `chile_hub/regions.py` vs `extractors/region_utils.py` (pylint R0801) | 🟠 | 133 |
| D2 | Unpacking `dfs["…"]` → 18 variables repetido en `_load_inputs`, `_compute_validations` y `build_dataset_metadata` | build_dev_db `527:569`/`710:730` ≈ metadata `404:442` | 🟠 | 132 |
| D3 | Muestra fallback SINIM embebida duplicada entre stub y live (la normalización ya comparte `_sinim_shared`) | `sinim_finanzas_extractor.py:52:90` ≈ `sinim_finanzas_live_extractor.py:377:413` | 🟠 | 133 |
| D4 | `SCHEMA` de extractores duplicado (`autoridades_electas` / `autoridades_locales`) | pylint R0801 | 🟡 | 133 |
| D5 | Mapeo artefacto→(nombre, formato) duplicado entre builder y verificador | `builders/artifacts.py:219:237` ≈ `verify_pipeline.py:1516:1534` | 🟡 | 133 |

*Aceptado, no deuda:* idioma `sys.path` + imports perezosos (E402/PLC0415 se
ignoran a propósito, con guardrail), `print()` en CLI/scripts (T201), PT009.

### 5. PEP-8 / PEP-257 / idiomas modernos

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| P1 | Docstrings: 44 % en `src`+`scripts`; **12 módulos sin docstring** (incluye `core.py`, `validation.py`, `build_dev_db.py`, `verify_pipeline.py`, `verify_landing.py`); 483 infracciones D | interrogate +D | 🟠 | 138 |
| P2 | Líneas largas: solo ~104 >100 caracteres (E501 ignorado) — deuda menor; decidir "fijar o ignorar" de una vez | AST | 🟡 | 131 |
| P3 | Migración idiomática: PTH `os.path`→`pathlib` ≈600, UP017 ×40, RUF100 (noqa obsoletos) ×40, UP015 ×31, SIM117 ×25, C420 ×14 — mayormente `--fix` | ruff | 🟡 | 131, 138 |
| P4 | `COM812` (1 033) debe **ignorarse explícitamente** (incompatible con el formatter) | ruff | 🟡 | 131 |

### 6. Tipado

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| T1 | `mypy --strict`: **767 errores / 46 archivos** — 355 `no-untyped-call`, 279 `no-untyped-def`, 120 `type-arg`. Peores: `core.py` 91, `pipeline_status_utils` 77, `build_dev_db` 77, `reports` 60, `cli`/`metadata`/`doc_sync` 49; en `src` solo: ANN001 386, ANN201 259 | mypy strict | 🟠 | 137 |
| T2 | El config actual (subset, no strict, `ignore_missing_imports=true`) es un piso razonable, pero sin trinquete | pyproject | 🟡 | 137 |

### 7. Gates y tests

| # | Hallazgo | Evidencia | Sev | Plan |
|---|---|---|---|---|
| G1 | Suite sana; el hueco es cobertura **por módulo** (validadores y extractores son la lógica de mayor riesgo) | badge 73.3 % | 🟡 | 138 |
| G2 | Gate sin trinquete: ruff `E,W,F,I`; interrogate `\|\| true`; sin complejidad/duplicación. Causa sistémica del drift — misma medicina que ADR-024: batches escalonados con guardrails | config | 🟠 | 131–138 |

## Roadmap de remediación

| Wave | Plan | Contenido | Prioridad | Esfuerzo | Riesgo |
|---|---|---|---|---|---|
| 1 | [131](../plans/131-audit-p0-correctitud-quick-wins.md) | Correctitud (C1, C2, C5–C7) + batch de modernización ruff + gates ruff con trinquete | P1 | S-M | LOW-MED |
| 2 | [132](../plans/132-audit-decomposicion-pipeline-build.md) | `DatasetFrames` + descomposición de `_load_inputs`/`build_dataset_metadata`/`_compute_validations`/`build_hub_health`/CLI + C901 | P1 | M | MED |
| 2 | [133](../plans/133-audit-single-source-dry.md) | Extractores: regiones/SINIM/SCHEMA single-source, globales → `ExtractionResult`, god functions | P2 | M-L | LOW-MED |
| 3 | [134](../plans/134-audit-chilehub-facade-split.md) | Split de `ChileHub` (store/query/contratos/presentación) + C3 (B019) | P2 | L | MED |
| 3 | [135](../plans/135-audit-validation-package.md) | `src/validation/` paquete con fachada + checker actualizado | P2 | M | MED |
| 3 | [136](../plans/136-audit-verificadores.md) | `verify_landing` split + utilidades compartidas de verificación | P2 | M | MED |
| 4 | [137](../plans/137-audit-mypy-strict-ratchet.md) | Trinquete `mypy --strict` por módulo | P3 | M | LOW |
| 4 | [138](../plans/138-audit-docs-coverage-pathlib.md) | PEP-257 + interrogate/d-rules con trinquete + coverage floor + pathlib | P3 | M | LOW |

Secuencia recomendada: **131 → (132 ∥ 133) → 134 → 135 → 136 → (137 ∥ 138)**.
Solapes: 132 ∩ 133 no comparten archivos; 134/135/138 tocan los mismos módulos
(138 al final); 136 solo `scripts/`.

## Anexo A — reproducibilidad

```bash
# Escaneos (todos read-only; salidas efímeras en /tmp/opencode/audit/)
.venv/bin/ruff check --no-cache --exit-zero --statistics --select ALL src scripts tests
.venv/bin/interrogate src scripts
uvx radon@6.0.1 cc -s --min C src scripts
uvx radon@6.0.1 mi -s src scripts
uvx vulture@2.14 src scripts --min-confidence 80
.venv/bin/mypy --strict --no-incremental src/chile_hub src/validation.py \
  src/build_dev_db.py src/builders src/extractors src/registry
uvx pylint@3.3.8 --disable=all --enable=duplicate-code --min-similarity-lines=14 src scripts
```
