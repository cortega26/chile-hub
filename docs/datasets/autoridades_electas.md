# Autoridades electas — Cámara + Senado

> **Carril:** `stable_publishable` — incluido en el bundle público.
> **Fuentes:** Cámara de Diputadas y Diputados (datos abiertos + listado web) y
> Senado de Chile (`senado.cl`).
> **review_by:** 2026-10-05 · **stalled_after_days:** 90

## Descripción

Autoridades electas **en ejercicio** de Chile (cargos públicos), como agregado
institucional. **v1** cubre dos cargos:

- **Diputados/as (155)** del período legislativo vigente, con partido y **distrito
  electoral**.
- **Senadores/as (50)** en ejercicio, con partido, **circunscripción senatorial**,
  **región** y **período de mandato**.

Los cargos subnacionales `gobernador_regional` (16) y `alcalde` (345) **no viven
aquí**: se compilan desde Wikipedia (CC-BY-SA) y se publican por separado en el
dataset segregado `autoridades_locales`, para no propagar la licencia share-alike a
los cargos oficiales CC-BY de este dataset.

Solo datos institucionales públicos de cargos en ejercicio; **sin datos personales**
(línea roja Ley 19.628, ver `docs/legal/b2-2-electoral-research.md`). Los campos
personales que exponen las fuentes (RUT en la Cámara; email/teléfono en el Senado) se
**descartan** en la extracción.

## Fuentes y método

| Cargo | Fuente | Método |
|-------|--------|--------|
| Diputado — roster + partido | `WSDiputado.asmx/retornarDiputadosPeriodoActual` (Cámara) | XML (stdlib) |
| Diputado — distrito | `camara.cl/diputados/diputados.aspx` | **Scrapling** (bypassa 403); une por `prmID` == Id del WS |
| Senador — roster + partido + circunscripción + región + período | `senado.cl` (Next.js) | **Scrapling**; lee `__NEXT_DATA__` (campos `REGION`/`PERIODOS`) |

`camara.cl` responde 403 a un GET normal y `senado.cl` es una SPA: ambos se obtienen con
[Scrapling](https://github.com/D4Vinci/Scrapling) (fetch con headers stealth), aislado en
el extra `scraping` de `pyproject.toml`. El extractor importa Scrapling de forma perezosa
y **degrada** si no está instalado (diputados sin distrito; senadores omitidos).

`codigo_region` se mapea desde el campo de texto `REGION` de `senado.cl` (p. ej. "Región
de Antofagasta") vía el mapa compartido `src/extractors/region_utils.py` (mismo usado por
`autoridades_locales_extractor.py` para gobernadores). `periodo_inicio`/`periodo_fin` se
toman de `PERIODOS`, el mandato marcado `VIGENTE=1`, con la misma convención de
instalación del Congreso (11 de marzo → 10 de marzo) que ya se usaba para diputados.

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
| `codigo_comuna` | string \| null | CUT — no aplica en v1 (alcaldes viven en `autoridades_locales`) |
| `codigo_region` | string \| null | Código de región (solo senadores) |
| `periodo_inicio` / `periodo_fin` | string \| null | Período del mandato (YYYY-MM-DD) |
| `estado_mandato` | string | `vigente` |
| `fuente` / `url_fuente` / `fecha_consulta` | string | Procedencia |

## Cobertura

- **v1:** 205 registros (155 diputados + 50 senadores).
- **Con Scrapling instalado** (extra `scraping`): distrito de diputados y
  `codigo_region`/`periodo` de senadores completos (50/50, observado 2026-07-06).
  **Sin Scrapling:** solo 155 diputados sin distrito (degradación).
- **Frecuencia:** bajo demanda (los cargos cambian por elección; ver `review_by`).

## Limitaciones

1. **Solo diputados y senadores:** `gobernador_regional` y `alcalde` están en el
   dataset segregado `autoridades_locales` (Wikipedia, CC-BY-SA) por decisión de
   licencia — no son un follow-up de este dataset, sino un dataset distinto por diseño.
2. **Período de diputados fijado en código** (2026-03-11 → 2030-03-10): actualizar cada
   4 años. El de senadores se deriva dinámicamente de `PERIODOS` (`senado.cl`).
3. **`pacto` (coalición) no disponible:** ninguna de las dos fuentes lo expone.

## Referencias

- Datos abiertos Cámara: https://opendata.camara.cl/
- Senado: https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores
- Dataset relacionado (cargos subnacionales, CC-BY-SA): `docs/datasets/autoridades_locales.md`
- Research electoral: `docs/legal/b2-2-electoral-research.md`
- Plan 023 — Ola A: `plans/023-autoridades-electas-partidos-politicos.md`
