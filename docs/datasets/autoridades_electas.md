# Autoridades electas — Cámara + Senado

> **Carril:** `candidate` — NO incluido en el bundle público.
> **Fuentes:** Cámara de Diputadas y Diputados (datos abiertos + listado web) y
> Senado de Chile (`senado.cl`).
> **review_by:** 2026-10-05 · **stalled_after_days:** 90

## Descripción

Autoridades electas **en ejercicio** de Chile (cargos públicos), como agregado
institucional. **v1** cubre dos cargos:

- **Diputados/as (155)** del período legislativo vigente, con partido y **distrito
  electoral**.
- **Senadores/as (50)** en ejercicio, con partido y **circunscripción senatorial**.

Cargos **pendientes** (follow-up): `gobernador_regional` (16) y `alcalde` (345).

Solo datos institucionales públicos de cargos en ejercicio; **sin datos personales**
(línea roja Ley 19.628, ver `docs/legal/b2-2-electoral-research.md`). Los campos
personales que exponen las fuentes (RUT en la Cámara; email/teléfono en el Senado) se
**descartan** en la extracción.

## Fuentes y método

| Cargo | Fuente | Método |
|-------|--------|--------|
| Diputado — roster + partido | `WSDiputado.asmx/retornarDiputadosPeriodoActual` (Cámara) | XML (stdlib) |
| Diputado — distrito | `camara.cl/diputados/diputados.aspx` | **Scrapling** (bypassa 403); une por `prmID` == Id del WS |
| Senador — roster + partido + circunscripción | `senado.cl` (Next.js) | **Scrapling**; lee `__NEXT_DATA__` |

`camara.cl` responde 403 a un GET normal y `senado.cl` es una SPA: ambos se obtienen con
[Scrapling](https://github.com/D4Vinci/Scrapling) (fetch con headers stealth), aislado en
el extra `scraping` de `pyproject.toml`. El extractor importa Scrapling de forma perezosa
y **degrada** si no está instalado (diputados sin distrito; senadores omitidos).

## Schema

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_autoridad` | string | Clave interna (`diputado_<id>` / `senador_<id>`) |
| `nombre` | string | Nombre completo |
| `cargo` | string | `diputado` \| `senador` (v1) |
| `institucion` | string | Cámara de Diputadas y Diputados \| Senado |
| `partido` | string \| null | Partido vigente |
| `pacto` | string \| null | Pacto/coalición (no provisto por la fuente) |
| `distrito_electoral` | string \| null | Distrito (solo diputados) |
| `circunscripcion_senatorial` | string \| null | Circunscripción (solo senadores) |
| `codigo_comuna` | string \| null | CUT (solo alcaldes — pendiente) |
| `codigo_region` | string \| null | Código de región (pendiente de poblar) |
| `periodo_inicio` / `periodo_fin` | string \| null | Período del mandato (YYYY-MM-DD) |
| `estado_mandato` | string | `vigente` |
| `fuente` / `url_fuente` / `fecha_consulta` | string | Procedencia |

## Cobertura

- **v1:** 205 registros (155 diputados + 50 senadores).
- **Con Scrapling instalado** (extra `scraping`): distrito de diputados y senadores
  completos. **Sin Scrapling:** solo 155 diputados sin distrito (degradación).
- **Frecuencia:** bajo demanda (los cargos cambian por elección; ver `review_by`).

## Limitaciones

1. **v1 incompleto:** faltan `gobernador_regional` (16) y `alcalde` (345). Los alcaldes
   requieren una fuente redistribuible (Wikipedia es CC-BY-SA; decisión de licencia
   pendiente).
2. **Período de diputados fijado en código** (2026-03-11 → 2030-03-10): actualizar cada
   4 años.
3. **`codigo_region` / `periodo` de senadores** aún nulos (la fuente los trae con otro
   esquema; se poblarán en un follow-up).

## Regla de salida (promoción)

Se promueve a `stable_publishable` cuando: (a) se cubran los 4 cargos, (b) se resuelva la
licencia de alcaldes, y (c) el extractor se mantenga estable hasta `review_by`.

## Referencias

- Datos abiertos Cámara: https://opendata.camara.cl/
- Senado: https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores
- Research electoral: `docs/legal/b2-2-electoral-research.md`
- Plan 023 — Ola A: `plans/023-autoridades-electas-partidos-politicos.md`
