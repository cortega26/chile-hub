# Autoridades locales — Wikipedia (CC-BY-SA)

> **Carril:** `candidate` — NO incluido en el bundle público.
> **Licencia:** **CC-BY-SA 4.0 (share-alike)** — dataset **segregado** de
> `autoridades_electas` (CC-BY) para no propagar share-alike. Ver `DATA_LICENSES.md`.
> **Fuente:** Wikipedia en español. **review_by:** 2026-10-05

## Descripción

Autoridades **locales/subnacionales** electas de Chile, compiladas desde Wikipedia. Se
separa de `autoridades_electas` porque su fuente es CC-BY-SA: mantener los cargos de
fuente oficial (diputados, senadores) en un dataset CC-BY y los de Wikipedia aquí evita
contaminar la licencia del resto.

**v1:** cargo **`gobernador_regional`** (16), con partido, coalición y `codigo_region`.

Cargo **pendiente:** `alcalde` (345). No existe fuente de tabla única redistribuible: el
"Anexo:Alcaldes de Chile" de Wikipedia son ~345 subpáginas y Wikidata da conteos
inconsistentes. Es un follow-up (agregación multi-página o curación).

Solo cargos públicos; **sin datos personales**.

## Fuente y método

- **Gobernadores (16):** página "Gobernador regional de Chile" de Wikipedia, tabla única,
  obtenida con [Scrapling](https://github.com/D4Vinci/Scrapling) (aislado en el extra
  `scraping` de `pyproject.toml`). La región se toma del *título* del enlace
  (`Gobernador(a) regional [Metropolitano] de|del <región>`) y se mapea a `codigo_region`.
- Import perezoso de Scrapling con degradación: si no está instalado, el cargo se omite.

## Schema

Mismo esquema que `autoridades_electas`: `id_autoridad`, `nombre`, `cargo`, `institucion`,
`partido`, `pacto`, `distrito_electoral`, `circunscripcion_senatorial`, `codigo_comuna`,
`codigo_region`, `periodo_inicio`, `periodo_fin`, `estado_mandato`, `fuente`, `url_fuente`,
`fecha_consulta`. Para gobernadores se pueblan `codigo_region`, `partido`, `pacto`.

## Cobertura

- **v1:** 16 gobernadores regionales (regiones 01–16).
- **Frecuencia:** bajo demanda (cambia por elección; ver `review_by`).

## Limitaciones

1. **v1 incompleto:** falta `alcalde` (345), sin fuente redistribuible de tabla única.
2. **CC-BY-SA:** la redistribución exige atribución + share-alike.
3. `periodo` de gobernadores aún nulo (parseo de fechas pendiente).

## Regla de salida

Se promueve solo si se asegura una fuente **no share-alike** para los cargos (o se acepta
el bundle CC-BY-SA para este dataset). Si la tabla de Wikipedia cambia de estructura y el
extractor se rompe sin arreglo para `review_by`, se degrada a `rejected`.

## Referencias

- Wikipedia — Gobernador regional de Chile: https://es.wikipedia.org/wiki/Gobernador_regional_de_Chile
- Licencias: `DATA_LICENSES.md`
- Plan 023 — Ola A: `plans/023-autoridades-electas-partidos-politicos.md`
