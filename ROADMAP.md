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
| 1 Correctness S | 086–090 | 0/5 | TODO |
| 2 Correctness/Perf M | 091–093 | 0/3 | TODO |
| 3 Deps/Tooling/Sec | 094–096 | 0/3 | TODO |
| 4 Docs agentes | 097–098 | 0/2 | TODO |
| 5 Deuda+spikes | 099–100 | 0/2 | TODO |
| 6 L diferido (pre-existente) | 077–079 + split gods | 0/3 | TODO (ver `plans/README.md`) |

## Backlog (orden de ejecución)

- [x] Wave 0: SHA + `make doctor` en lectura + confirmar 077/078/079 TODO
- [ ] 086 Snapshot SINCA viejo etiquetado `live` → `stale_snapshot` (P1/S, —)
- [ ] 087 `sync_landing_metadata` falla ruidoso en vez de `print` (P1/S, —)
- [ ] 088 Cobertura catálogo→validación: gate + exenciones explícitas (P1/S, —)
- [ ] 089 bcentral: TZ a UTC + throttle real (P1/S, —)
- [ ] 090 Una sola conversión `to_pandas()` + descarte pre-conversión (P1/S, —)
- [ ] 091 Opcionales ausentes ruidosos + fallback sintético strict (P1/M, —)
- [ ] 092 Paralelizar formatos + `indicadores_hoy` = última fecha (P2/M, tras 090)
- [ ] 093 Scans O(K·N)→`partition_by` + allowlist única + cache acotado (P2/M, —)
- [ ] 094 Toolchain única: ruff/mypy una versión + `make typecheck/audit/sec` (P1/S, —)
- [ ] 095 Floor Python `>=3.11` + despineo pandas + matriz CI (P1/M, —)
- [ ] 096 `duckdb` query acotado + pip-audit expiry + bandit a extractors (P1/S-M, —)
- [ ] 097 Docs quirúrgicos: CLAUDE counts, badge capas, §5 como puntero (P1/S, —)
- [ ] 098 Docs arquitectura: SOURCE índice, CLAUDE→30 líneas, anti-drift extendido (P2/M, tras 097)
- [ ] 099 Deuda media: sinim-shared + salud canónica + `sys.path`→`_paths` (P2/M, tras 091)
- [ ] 100 Spike Polars `2.0rc1` en rama + golden-diff (P2/M, tras 092; sin prod)
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

## Rechazados en esta auditoría (no re-auditar)

- Conflicto `click` dev-vs-scraping: by-design (`pyproject.toml:94-107` + `conflicts` + entorno efímero en CI).
- Duplicado `shapely`/`geopandas` en extras `pipeline`+`geo`: intencional (expone `resolve_by_coords()` al consumidor).
- Lock drift: limpio (`uv lock --check` pasa + gate `--locked` en CI).
- `validate_puntos_interes` "huérfana": by-design — fuera del catálogo, exención documentada en `scripts/check_validation_registration.py:8-10`.
- Deps abandonadas / APIs deprecadas de polars/pandas en uso: sin evidencia (grep sin hits fuera de `def fetch`).
- `build_freshness` duplicado: ya delega en `compute_freshness` (`src/builders/metadata.py:88-89`); el resto va en 099.
