# Autoridades locales — BCN SIIT + Wikipedia (CC-BY-SA)

> **Carril:** `candidate` — NO incluido en el bundle público.
> **Fuente:** BCN SIIT (alcaldes) + Wikipedia (gobernadores).
> **review_by:** 2026-10-05

## Descripcion

Autoridades **locales/subnacionales** electas de Chile. Se separa de
`autoridades_electas` porque los gobernadores usan Wikipedia (CC-BY-SA); los alcaldes
usaban Wikipedia en v1 pero desde v2 usan **BCN SIIT** (fuente gubernamental oficial).

**v2 (Plan 042):** cargos **`gobernador_regional`** (16) y **`alcalde`** (345 comunas,
cobertura nacional completa). Los alcaldes se obtienen desde BCN SIIT (Biblioteca del
Congreso Nacional) — cobertura 100%, fuente oficial, sin restriccion de licencia para
datos factuales de autoridades publicas.

Solo cargos publicos; **sin datos personales**.

## Fuente y metodo

- **Gobernadores (16):** pagina "Gobernador regional de Chile" de Wikipedia, tabla unica,
  obtenida con [Scrapling](https://github.com/D4Vinci/Scrapling) (aislado en el extra
  `scraping` de `pyproject.toml`). La region se toma del *titulo* del enlace
  (`Gobernador(a) regional [Metropolitano] de|del <region>`) y se mapea a `codigo_region`.
- **Alcaldes (345 comunas):** [BCN SIIT](https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno=2024)
  (Sistema Integrado de Informacion Territorial de la Biblioteca del Congreso Nacional).
  Una request HTTP por comuna (`idcom={codigo_comuna}`), parseo HTML de la tabla de datos
  comunales. Fuente oficial del Congreso chileno; datos factuales de autoridades publicas,
  sin restriccion de licencia.
- **Enriquecimiento:** Wikipedia ("Anexo:Alcaldes de X") se usa como fuente secundaria
  para `periodo_inicio` donde este disponible (~224 comunas con pagina existente). El
  nombre del alcalde siempre proviene de BCN SIIT (fuente primaria).
- Import perezoso de Scrapling con degradacion: si no esta instalado, el cargo
  `gobernador_regional` se omite (los alcaldes no dependen de Scrapling).

## Schema

Mismo esquema que `autoridades_electas`: `id_autoridad`, `nombre`, `cargo`, `institucion`,
`partido`, `pacto`, `distrito_electoral`, `circunscripcion_senatorial`, `codigo_comuna`,
`codigo_region`, `periodo_inicio`, `periodo_fin`, `estado_mandato`, `fuente`, `url_fuente`,
`fecha_consulta`. Para gobernadores se pueblan `codigo_region`, `partido`, `pacto`.

## Cobertura

- **v2:** 16 gobernadores regionales (regiones 01–16) + 345 alcaldes (cobertura nacional
  completa). BCN SIIT identifica al alcalde vigente en ~340+ comunas; las vacancias
  temporales quedan con `nombre` nulo.
- **Frecuencia:** bajo demanda (cambia por eleccion; ver `review_by`).

## Licencia

> **Licencia de los datos de alcaldes:** datos factuales de autoridades publicas
> obtenidos de BCN SIIT (fuente gubernamental chilena). Sin restriccion conocida
> de copyright para datos factuales de cargos publicos.
> **Licencia de gobernadores regionales:** CC-BY-SA 4.0 (Wikipedia). Los 16
> registros de gobernador mantienen atribucion share-alike.

## Limitaciones

1. **Cobertura nacional completa (345 comunas).** Puede haber brechas puntuales por
   vacancia temporal del cargo.
2. **Licencia mixta:** los gobernadores mantienen CC-BY-SA (Wikipedia); los alcaldes son
   dato publico gubernamental sin restriccion conocida.
3. `periodo_inicio` solo se puebla desde Wikipedia cuando la subpagina "Anexo:Alcaldes
   de X" existe (~224 comunas) y el infobox trae una plantilla `{{fecha|D|M|Y}}`
   reconocible; en el resto queda nulo.

## Regla de salida

Se promueve si la cobertura de BCN SIIT se mantiene sobre `MIN_ALCALDES_CON_TITULAR`
(300) y no hay regresiones en la validacion. Si BCN SIIT cambia su estructura HTML o
bloquea las requests, se degrada a `rejected`.

## Referencias

- BCN SIIT — Reportes Comunales: https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno=2024
- Wikipedia — Gobernador regional de Chile: https://es.wikipedia.org/wiki/Gobernador_regional_de_Chile
- Licencias: `DATA_LICENSES.md`
- Plan 042 — BCN SIIT alcaldes: `plans/042-ampliar-cobertura-alcaldes-main-article.md`
