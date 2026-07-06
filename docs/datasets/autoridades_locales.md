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

**v1:** cargos **`gobernador_regional`** (16) y **`alcalde`** (224 comunas con página en
Wikipedia de las 345 existentes; 165 con alcalde identificado).

Solo cargos públicos; **sin datos personales**.

## Fuente y método

- **Gobernadores (16):** página "Gobernador regional de Chile" de Wikipedia, tabla única,
  obtenida con [Scrapling](https://github.com/D4Vinci/Scrapling) (aislado en el extra
  `scraping` de `pyproject.toml`). La región se toma del *título* del enlace
  (`Gobernador(a) regional [Metropolitano] de|del <región>`) y se mapea a `codigo_region`.
- **Alcaldes (345 comunas enlazadas → 224 con página):** la página índice
  "Anexo:Alcaldes de Chile" enlaza a una subpágina por comuna
  ("Anexo:Alcaldes de \<comuna\>"); no hay tabla única. Se listan los 345 títulos (1
  request) y se descarga su wikitext en lotes de 50 (~7 requests) vía la **API pública
  de MediaWiki** (`action=query`, sin Scrapling: es una API abierta de solo lectura que
  no bloquea, a diferencia de camara.cl/senado.cl). De los 345 enlaces, **~224 tienen
  página real**; el resto son enlaces rojos (páginas no creadas, típicamente comunas
  rurales pequeñas) — una limitación real de la fuente, no del extractor. El alcalde
  vigente se extrae del campo `titular=` del infobox `{{Ficha de cargo...}}` (~165/224);
  si no hay infobox, se intenta la última fila de la tabla histórica con marca explícita
  de vigencia ("en el cargo"/"en ejercicio"/"actualidad"); sin evidencia clara, el
  alcalde queda **nulo** (`estado_mandato: sin_identificar`) — no se inventa un nombre
  (algunas comunas están efectivamente vacantes, p. ej. Antofagasta a fines de 2024).
  El nombre de comuna se cruza con `comunas.csv` (`nombre_comuna_clean`) para poblar
  `codigo_comuna`/`codigo_region` (~221/224 matchean).
- Import perezoso de Scrapling con degradación: si no está instalado, el cargo
  `gobernador_regional` se omite (los alcaldes no dependen de Scrapling).

## Schema

Mismo esquema que `autoridades_electas`: `id_autoridad`, `nombre`, `cargo`, `institucion`,
`partido`, `pacto`, `distrito_electoral`, `circunscripcion_senatorial`, `codigo_comuna`,
`codigo_region`, `periodo_inicio`, `periodo_fin`, `estado_mandato`, `fuente`, `url_fuente`,
`fecha_consulta`. Para gobernadores se pueblan `codigo_region`, `partido`, `pacto`.

## Cobertura

- **v1:** 16 gobernadores regionales (regiones 01–16) + 224 comunas con página de
  alcalde (de 345 totales), de las cuales 165 tienen alcalde identificado.
- **Frecuencia:** bajo demanda (cambia por elección; ver `review_by`).

## Limitaciones

1. **Cobertura de alcaldes real, no completa:** 121 comunas no tienen página propia en
   Wikipedia (enlaces rojos) y quedan fuera del dataset (no como fila con nulo, sino
   ausentes); de las 224 con página, 59 no exponen un alcalde identificable con el
   método actual (infobox vacío/inconsistente y sin marca de vigencia en la tabla) y
   quedan con `nombre` nulo y `estado_mandato: sin_identificar`.
2. **CC-BY-SA:** la redistribución exige atribución + share-alike.
3. `periodo_inicio` de gobernadores aún nulo (parseo de fechas pendiente); en alcaldes
   solo se puebla cuando el infobox trae una plantilla `{{fecha|D|M|Y}}` reconocible.
4. **Wikipedia es una fuente editada, no oficial:** puede tener errores o desactualizarse
   respecto al SERVEL. Verificar contra fuente oficial ante discrepancia relevante.

## Regla de salida

Se promueve solo si se asegura una fuente **no share-alike** para los cargos (o se acepta
el bundle CC-BY-SA para este dataset) y se mejora la cobertura de alcaldes de forma
material. Si la cobertura de Wikipedia cae por debajo de `MIN_ALCALDES_CON_TITULAR`
(140) o el extractor se rompe sin arreglo para `review_by`, se degrada a `rejected`.

## Referencias

- Wikipedia — Gobernador regional de Chile: https://es.wikipedia.org/wiki/Gobernador_regional_de_Chile
- Wikipedia — Anexo:Alcaldes de Chile: https://es.wikipedia.org/wiki/Anexo:Alcaldes_de_Chile
- Licencias: `DATA_LICENSES.md`
- Plan 023 — Ola A: `plans/023-autoridades-electas-partidos-politicos.md`
