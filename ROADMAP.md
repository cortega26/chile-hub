# Roadmap — auditoría 2026-09-15 (commit `3315eb6`)

> **Qué es este archivo:** goto de tracking de la auditoría 2026-09-15.
> Waves → scoreboard → backlog → dependencias. El detalle ejecutable vive en
> `plans/086-*.md…100-*.md` (self-contained, estilo `plans/080-*` + template
> improve); el índice ejecutor sigue siendo `plans/README.md`; la métrica
> semanal sigue en `docs/backlog/scorecard.md` + `NEXT_STEPS.md`.
> **No duplicar contenido de planes aquí** — solo estado y links.
>
> **Rutina tras cada cierre** (misma que `plans/README.md:77-99`): 1) marcar la
> casilla del backlog y la fila del scoreboard; 2) actualizar `plans/README.md`
> + `docs/backlog/scorecard.md` + `NEXT_STEPS.md`; 3) mover el `.md` a
> `archive/` y sacar su fila de activos; 4) revalidar el grafo de dependencias.
>
> **Decisiones del mantenedor (2026-09-15):** alcance todos los net-positive;
> dropear Python 3.10; spike Polars 2.0 RC solo en rama; consolidación agresiva
> de docs de agentes.

## Scoreboard (única tabla viva — actualizar en cada cierre)

| Wave | Planes | Done | Estado |
|------|--------|------|--------|
| 0 Baseline | — | 1/1 | DONE (2026-09-15) |
| 1 Correctness S | 086–090 | 5/5 | DONE (2026-09-15, branch advisor/wave-1; suite 1027 passed) |
| 2 Correctness/Perf M | 091–093 | 2/3 | 092, 093 DONE; 091 REVERTED (ver backlog) |
| 3 Deps/Tooling/Sec | 094–096 | 3/3 | DONE (2026-09-15, branch advisor/wave-3; bandit 0 issues, suite 1032 passed) |
| 4 Docs agentes | 097–098 | 2/2 | DONE (2026-09-15, branch advisor/wave-4; doctor+lint+format verdes) |
| 5 Deuda+spikes | 099–100 | 2/2 | DONE (2026-09-15, branch advisor/wave-5; suite 1037 passed) |
| 6 L diferido (pre-existente) | 077–079 + split gods | 0/3 | TODO (ver `plans/README.md`) |

## Backlog (orden de ejecución)

- [x] Wave 0: SHA + `make doctor` en lectura + confirmar 077/078/079 TODO
- [x] 086 Snapshot SINCA viejo → `fallback` + nota con snapshot (P1/S, 2522d7d)
- [x] 087 `sync_landing_metadata` con raise tras print (P1/S, b751717)
- [x] 088 Cobertura catálogo→validación + 3 exenciones explícitas (P1/S, 48a60be)
- [x] 089 bcentral UTC×3 + submits espaciados (P1/S, fbddeaa)
- [x] 090 Frames pandas compartidos + skip pre-conversión (P1/S, 62143ac)
- [ ] 091 Opcionales ausentes ruidosos + fallback sintético strict (P1/M) — REVERTED 2026-09-15 (79b41fa): el abort en build rompe la garantía Phase-1 de core-build sin opcionales (7+1 tests); el gate publication ya rechaza missing/non-live/stale. Devuelto al backlog para decisión del mantenedor (alternativa: cerrar como cubierto por el gate).
- [x] 092 Payload hoy por código + no-paralelizar con números (P2/M, c9d8c2a)
- [x] 093 partition_by + allowlist única + cache LRU (P2/M, 3a155bd)
- [x] 094 Toolchain única + targets locales (P1/S, 972ffbb + 238bc10 isort)
- [x] 095 Floor py311 + despineo pandas (P1/M, 79fde6a)
- [x] 096 duckdb acotado + pip-audit expiry + bandit extractors + fix B314 (P1/S-M, 7beda93)
- [x] 097 Docs quirúrgicos + convención de conteos (P1/S, de12198)
- [x] 098 Docs arquitectura + gate ×3 + regex fix (P2/M, 4fdc4ce) + fix regex `check_agents_sync.py:54` (aceptar `\d{4}` sin espacio; hoy `1034` pelado no matchea y atribuye el número vecino — hallado en Wave 2, workaround: formato `1 034`)
- [x] 099 Deuda media: `_sinim_shared` + salud documentada-sin-churn + sys.path congelado (P2/M)
- [x] 100 Spike Polars `2.0rc1`: 22/22 parquet idénticos, suite verde, cero cambios a prod (P2/M; re-correr en GA; follow-ups: geoarrow-extension en `resolve_by_coords`, bump 1.44.1 dentro de `<2`, mismo trato a DuckDB 2.0 en su RC)
- [ ] Wave 6: terminar 077→079 y luego split god objects por dominio (L, tras Wave 2)

## Goto por síntoma

| Quiero… | Ir a |
|---|---|
| ejecutar lo siguiente | primer `[ ]` del Backlog + su `plans/0NN-*.md` |
| saber el estado | Scoreboard ↑ |
| contexto rápido del repo | `SOURCE_OF_TRUTH.md` → `AGENTS.md` |
| detalle ejecutor (pasos, verifies, STOP) | `plans/README.md` + `plans/0NN-*.md` |
| métrica semanal | `docs/backlog/scorecard.md` |
| agregar un dataset | `AGENTS.md §5` + `docs/dataset-inclusion-criteria.md` (normativo) |
| entender carriles/estados | `docs/dataset-inclusion-criteria.md` + `data/source_registry.json` |

## Dependencias

- `092` tras `090` (mismo `src/builders/formats.py` + `build_dev_db.py:744-796`).
- `098` tras `097` (misma prosa; evita conflictos).
- `099` tras `091` (la parte de salud canónica toca `hub_health.json`).
- `100` tras `092` (necesita el baseline de perf/payloads estable).
- Wave 6 tras Wave 2 (caracterización 077 antes de cualquier refactor).
- `079` tras `077` (pre-existente, ver `plans/README.md`).

## Follow-ups detectados durante waves (no re-auditar, sí trackear)

- [ ] Ficha `delincuencia_comunal` en `source_registry.json` con campos estructurados stales tras la degradación del 2026-09-15: `maturity_status: candidate` + `live_extractor_status: implemented` + `review_by: 2027-09-15` contradicen `next_action` ("degradado a rejected", extractor neutralizado). Requiere decisión del mantenedor sobre los valores enum + interplay con gates antes de tocar (hallado en Wave 4, fuera de scope docs).

## Rechazados en esta auditoría (no re-auditar)

- Conflicto `click` dev-vs-scraping: by-design (`pyproject.toml:94-107` + `conflicts` + entorno efímero en CI).
- Duplicado `shapely`/`geopandas` en extras `pipeline`+`geo`: intencional (expone `resolve_by_coords()` al consumidor).
- Lock drift: limpio (`uv lock --check` pasa + gate `--locked` en CI).
- `validate_puntos_interes` "huérfana": by-design — fuera del catálogo, exención documentada en `scripts/check_validation_registration.py:8-10`.
- Deps abandonadas / APIs deprecadas de polars/pandas en uso: sin evidencia (grep sin hits fuera de `def fetch`).
- `build_freshness` duplicado: ya delega en `compute_freshness` (`src/builders/metadata.py:88-89`); el resto va en 099.
