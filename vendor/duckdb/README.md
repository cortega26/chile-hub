# DuckDB-Wasm vendorizado

Bundle auto-hospedado del explorador SQL del sitio (`playground.js`). El motor
se carga desde estos archivos locales para respetar la CSP (`script-src 'self'
'wasm-unsafe-eval'`, `worker-src 'self' blob:`) sin depender de un CDN.

| Campo | Valor |
|:---|:---|
| Paquete | `@duckdb/duckdb-wasm` `1.32.0` (último estable en npm) |
| Motor DuckDB embebido | `1.4.3` — verificado con `SELECT version()` en el navegador; el pipeline escribe con `duckdb==1.5.5` y el smoke lee esos Parquet sin degradación |
| `apache-arrow` esperado | `^17.0.0` — servido desde `vendor/apache-arrow/` vía el import map de `index.html` (no vive en este directorio) |
| Origen | `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.32.0/dist/` |
| Fecha de vendorizado | 2026-09-29 (Plan 128) |

Archivos versionados (nombres exactos que importa `playground.js`; no renombrar):

| Archivo | Rol |
|:---|:---|
| `duckdb-browser.mjs` | Loader ESM (`AsyncDuckDB`, `ConsoleLogger`) |
| `duckdb-browser-mvp.worker.js` | Worker del target MVP (sin SharedArrayBuffer) |
| `duckdb-mvp.wasm` | Binario del motor, target MVP |
| `duckdb-browser-eh.worker.js` | Worker del target EH; se mantiene alineado al mismo release aunque el playground use solo MVP |

Notas de mantenimiento:

- `duckdb-eh.wasm` no se versiona (ADR-021: snapshot liviano); el playground usa
  solo el target MVP. No re-agregarlo sin cambiar también `playground.js` y el
  guardrail `tests/test_ci_config.py::ReleaseSnapshotWeightGuardrailTests`.
- Para actualizar: descargar los cuatro archivos del release elegido desde la
  misma URL base, conservar los nombres, actualizar esta tabla y correr
  `make verify-landing` (el smoke ejecuta una consulta real contra
  `data/normalized/comunas.parquet`).
- Si un release futuro de `duckdb-wasm` sube su rango de `apache-arrow`,
  actualizar `vendor/apache-arrow/` y el import map de `index.html` en el mismo
  cambio.
- El pipeline Python está pineado en `duckdb==1.5.5`. No hay release estable de
  `duckdb-wasm` con motor 1.5.x (1.30 → 1.3.2, 1.31 → 1.4.0, 1.32 → 1.4.3); el
  criterio del Plan 128 es elegir el bundle con DuckDB ≤1.6 y validar que lea
  los Parquet publicados. `make verify-landing` ejecuta `SELECT count(*)` sobre
  `comunas.parquet` en cada corrida para detectar incompatibilidades.
