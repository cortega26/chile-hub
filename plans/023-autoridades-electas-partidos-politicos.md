# Plan 023: Datasets `autoridades_electas` y `partidos_politicos`

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar cada ola, actualiza la fila de estado de este plan en `plans/README.md`
> y sigue la "Rutina obligatoria tras cada iteración" de ese archivo (índice,
> backlog/scorecard si aplica, archivado).
>
> **Drift check (ejecutar primero)**:
> `git diff --stat 2c39890..HEAD -- data/source_registry.json src/builders/catalog.py src/extractors/ contracts/datasets/ Makefile docs/legal/b2-2-electoral-research.md`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: **M-L** (revisado tras Step 0: diputados es S; senadores/gobernadores/
  alcaldes requieren scraping/agregación, no "snapshot" trivial como asumía la research)
- **Risk**: **MED** (revisado: 3 de 4 cargos dependen de scraping frágil — SPA senado,
  Wikipedia multi-página para alcaldes; sin datos personales, research legal cerrada)
- **Depends on**: none — deriva del Plan 022, Ola B2.2 (research completada)
- **Category**: data / catálogo (Track B — expansión por valor de cruce)
- **Planned at**: commit `2c39890`, 2026-07-03
- **Step 0 ejecutado**: 2026-07-03 — fuentes verificadas con datos reales (ver
  "Hallazgos confirmados"). Diputados listo para codificar; resto necesita scraping.

## Progreso de implementación

**2026-07-04:**

- ✅ **`partidos_politicos` (Ola B) — extractor + contrato + tests construidos y verificados.**
  - `src/extractors/partidos_politicos_extractor.py` (`BaseExtractor`, patrón del repo,
    sin dependencias nuevas — `xml.etree` + `fetch_with_retry`). Ejecutado contra la
    fuente viva: **36 partidos reales** (Frente Amplio, DC, Evolución Política, …).
  - `contracts/datasets/partidos_politicos.schema.json`.
  - 3 tests en `tests/test_extractors.py` (`PartidosPoliticosExtractorTests`): mapeo de
    esquema + dedupe, ausencia de columnas personales, validación de conteo mínimo.
  - Suite completa: **514 pruebas verdes, 0 regresiones**. Lint/format limpios.
  - ⏳ **Falta cablearlo al bundle** (`DATASET_CATALOG_CONFIG` en `_shared.py`,
    `_load_inputs` en `build_dev_db.py`, `source_registry`, `Makefile extract`, ficha,
    formatos). Confirmado que esa integración es cirugía intricada del god-module con
    lógica por-dataset; se hace en un paso dedicado. Carril sugerido: `candidate` primero.
  - Nota de honestidad: la fuente Cámara es un roster (incluye históricos) sin
    `estado_legal`/`fecha_constitucion`/`ambito` → nullable en v1; completar con SERVEL.

- ⏳ **`autoridades_electas` (Ola A) — pendiente.** El núcleo de diputados (roster+partido)
  es limpio, pero el **distrito no está en el API** (confirmado; ver hallazgos) → requiere
  scrape del perfil HTML. Senadores (Playwright), gobernadores (curado) y alcaldes
  (Wikipedia CC-BY-SA multi-página) siguen pendientes. Es el grueso restante del plan.

## Why this matters

El Plan 022 (Ola B2.2) cerró la **research legal y de fuentes** del dominio electoral
—`docs/legal/b2-2-electoral-research.md`— y explícitamente derivó la *implementación*
de `autoridades_electas` y `partidos_politicos` a este plan de follow-up. Hoy el índice
`plans/README.md` los lista como el siguiente paso recomendado (#1), pero el fichero de
plan no existía: este documento cierra esa brecha y ejecuta el trabajo.

El valor es de **cruce**, no de acumulación (principio rector del Track B): la audiencia
real del proyecto son investigadores que cruzan capas territoriales. Añadir quién
representa a cada comuna/distrito/región (autoridades) y el registro de partidos abre el
dominio institucional-electoral **sin tocar datos personales** (línea roja Ley 19.628,
validada en la research §1). Ambos datasets son agregados institucionales de cargos
públicos, redistribuibles (CC0/CC-BY).

`resultados_electorales` **queda fuera de alcance** y diferido (research §4.3): no existe
fuente estructurada estable por comuna. Se agenda revisión trimestral; no se construye.

## Current state

Puntos de integración de un dataset nuevo (confirmados en el repo, 2026-07-03):

- **Extractor**: `src/extractors/<name>_extractor.py`. Contrato común en
  `src/extractors/base.py` (`BaseExtractor` ABC: `dataset_name`, `fetch`, `normalize`,
  `validate`, `write_staging`, más `run()` como entry point programático). Los
  extractores existentes también exponen funciones `process_*()` standalone invocadas
  desde `if __name__ == "__main__"` (así los ejecuta el Makefile). Helpers:
  `ensure_staging_directories()`, `write_staging_metadata()`. Salida a
  `data/staging/<name>.csv` + `data/staging/<name>.metadata.json`.
  - Patrón de referencia más cercano: `src/extractors/electoral_extractor.py`
    (`distritos_electorales`) — mismo dominio, ya cruza región→circunscripción y
    escribe staging + `REUSE_POLICY`. **Reutiliza su estructura**, no la modifiques.
- **Makefile**: el target `extract` (líneas ~86–99) invoca cada extractor con
  `PYTHONPATH=src $(PYTHON) src/extractors/<name>_extractor.py`. Aquí se añaden las
  dos líneas nuevas.
- **Registro de fuentes**: `data/source_registry.json` es una **lista** de objetos, uno
  por fuente. Campos usados (copia la forma de una entrada `stable_publishable`
  existente, p. ej. `bcn_regiones`): `source_id`, `dataset`, `source_name`,
  `official_url`, `access_method`, `license_status`, `live_extractor_status`,
  `fallback_policy`, `maturity_status`, `live_ready`, `fallback_allowed`,
  `publish_blocking`, `review_by`, `stalled_after_days`, `owner`, `next_action`,
  `publication_track`, `public_bundle_eligible`, `cadencia`.
- **Catálogo**: `src/builders/catalog.py` contiene `DATASET_CATALOG_CONFIG` (config por
  dataset que alimenta la landing y los artefactos). Añade una entrada nueva copiando la
  forma de una existente; confírmala con `grep -n "DATASET_CATALOG_CONFIG" -n
  src/builders/catalog.py` y revisa una entrada análoga.
- **Contratos**: `contracts/datasets/<name>.schema.json` (formato propio del repo, ver
  ADR-005). Copia la forma de `contracts/datasets/distritos_electorales.schema.json`.
- **Fichas**: `docs/datasets/<name>.md`. Copia la estructura de
  `docs/datasets/distritos_electorales.md`. Registra el cambio en
  `docs/datasets/status_changelog.md` si el patrón lo requiere.
- **Tests**: `tests/` (8 ficheros `test_*.py`, ~490 tests). Añade tests del extractor y
  del contrato siguiendo `tests/` existentes.

**Sin dependencias nuevas**: XML de la Cámara con `xml.etree.ElementTree` (stdlib);
Wikidata SPARQL con `requests` (ya presente) vía GET a `query.wikidata.org/sparql` con
`format=json`. No añadas `SPARQLWrapper` ni parsers XML de terceros.

Convención del repo: español neutral; sin voseo; dependencias pineadas; conventional
commits; `uv` como gestor; "fallar con estridencia" ante fuente inaccesible.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Ejecutar el extractor nuevo | `PYTHONPATH=src .venv/bin/python src/extractors/autoridades_electas_extractor.py` | exit 0; genera staging CSV + metadata |
| Ejecutar todos los extractores | `make extract` | exit 0 |
| Build del pipeline | `make build` | exit 0; artefactos regenerados |
| Verificar contratos/readiness | `make verify` | exit 0 |
| Tests | `make test` | exit 0; sin regresiones |
| Lint + formato | `make lint && make format-check` | exit 0 |
| Readiness de fuentes | `make verify-readiness` | exit 0 |

## Scope

**In scope** (Ola A — `autoridades_electas`):
- `src/extractors/autoridades_electas_extractor.py` — **crear**.
- `contracts/datasets/autoridades_electas.schema.json` — **crear**.
- `data/source_registry.json` — añadir entrada(s) de fuente (Cámara XML, Wikidata).
- `src/builders/catalog.py` — añadir entrada en `DATASET_CATALOG_CONFIG`.
- `docs/datasets/autoridades_electas.md` — **crear** ficha.
- `Makefile` — añadir la línea del extractor en el target `extract`.
- `tests/` — tests del extractor y del contrato.
- `data/staging/autoridades_electas.csv` (+ metadata) y un **snapshot de fallback**
  versionado (según política del repo para fuentes live).

**In scope** (Ola B — `partidos_politicos`): los mismos artefactos con `partidos_politicos`.

**Out of scope** (NO tocar):
- `resultados_electorales` — diferido (research §4.3). No crear extractor ni contrato.
- Cualquier dato personal electoral (padrón, RUN, domicilio, mesa, afiliación
  individual) — **línea roja no negociable** (research §1).
- `index.html`/`app.js` de la landing salvo lo que el build regenere automáticamente
  desde el catálogo (no edición manual).
- Datos de resultados por mesa/persona o dashboards Power BI de SERVEL (research §2.2).

## Git workflow

- Branch: `advisor/023-autoridades-electas-partidos-politicos`.
- Commits estilo conventional commits, p. ej.
  `feat(data): añade dataset autoridades_electas (Cámara XML + Wikidata)` y
  `feat(data): añade dataset partidos_politicos`.
- Un commit (o PR) por ola es preferible; las olas son independientes.
- No hagas push ni abras PR salvo indicación del operador.

## Steps

### Step 0: Confirmar fuentes (research spike, obligatorio antes de codificar)

La research dejó URLs y QIDs "a confirmar". Resuélvelos y **documéntalos** antes de
escribir el extractor; si una fuente no responde como espera la research, es STOP.

1. **Cámara XML**: confirma la URL viva del endpoint de diputados/as vigentes (la
   research apunta a `https://opendata.camara.cl/pages/diputados_vigentes.aspx`, marcada
   "URL exacta a confirmar"). `GET` con `requests`, verifica `200` y que el cuerpo sea
   XML parseable con `xml.etree.ElementTree`. Inspecciona los tags reales (nombre,
   partido, distrito, período) — pueden diferir del ejemplo de la research §5.
2. **Wikidata SPARQL**: resuelve los QIDs/propiedades reales (la research dejó
   `wd:Q....`). Necesitas los ítems de cargo para senador de Chile, alcalde y gobernador
   regional, y las propiedades `P39` (cargo ocupado), inicio/fin de mandato, y el cruce a
   comuna/región. Prueba cada query en `https://query.wikidata.org/sparql?format=json`.
3. Registra los hallazgos (URLs, QIDs, tags XML, conteos observados) en el commit o en
   una nota breve `docs/legal/` o en el propio metadata del extractor.

**Verify**:
- La URL de Cámara devuelve XML `200` y parsea.
- Cada query SPARQL devuelve filas con los conteos esperables del orden de: ~155
  diputados/as, ~50 senadores/as, ~345 alcaldes/as, 16 gobernadores/as.

**STOP** si: la URL de Cámara no responde o no es XML; Wikidata no expone senadores/
alcaldes vigentes con cargo estructurado; o los conteos difieren de forma drástica del
orden esperado (indica QID equivocado). Repórtalo — no rellenes con datos inventados.

#### Hallazgos confirmados (Step 0 ejecutado — 2026-07-03)

Ejecutado desde el entorno de desarrollo. **Corrige drift de la research** y cambia la
estrategia de fuentes:

- ✅ **Diputados/as — Cámara XML (fuente autoritativa).** El endpoint de la research
  (`pages/diputados_vigentes.aspx`) devuelve HTML, no datos. El endpoint **real y vivo**
  es el web service SOAP/REST:
  `https://opendata.camara.cl/camaradiputados/WServices/WSDiputado.asmx/retornarDiputadosPeriodoActual`
  → HTTP 200, ~179 KB XML, namespace `http://opendata.camara.cl/camaradiputados/v1`.
  Conteo exacto: **155 diputados/as** (coincide con lo esperado). Estructura por registro:
  `Id`, `Nombre`, `Nombre2`, `ApellidoPaterno`, `ApellidoMaterno`, `Sexo`, y
  `Militancias/Militancia` (historial de partido con `FechaInicio`/`FechaTermino` y
  `Partido{Id,Nombre,Alias}`). El partido vigente = la `Militancia` con `FechaTermino`
  abierta/más reciente. **⚠️ El XML incluye `RUT`/`RUTDV`: NO extraerlos** (línea roja).
  **Cabo suelto del distrito:** ni `retornarDiputadosPeriodoActual` ni
  `retornarDiputado?prmDiputadoId=` exponen el distrito (verificado 2026-07-03). Vías a
  probar en implementación: (a) `retornarDiputadosXPeriodo?prmPeriodoID=<actual>` —
  requiere primero el método correcto de listado de periodos en `WSComun.asmx`
  (`retornarPeriodosLegislativos` NO es válido ahí); (b) el perfil HTML del diputado en
  `camara.cl` muestra "Distrito N". Sin el distrito, el cargo diputado pierde su principal
  valor de cruce, así que resolverlo es parte del alcance mínimo del cargo.
- ❌ **Wikidata SPARQL — NO fiable para autoridades vigentes.** QIDs reales resueltos:
  senador `Q18882653`, diputado `Q18067639`, gobernador regional `Q85870414` (alcalde
  solo tiene el genérico `Q30185`). Pero el filtro "sin `P582`" NO equivale a "vigente":
  senadores → **426** (esperado ~50), diputados → **1508** (esperado 155) por históricos
  mal modelados; gobernadores → **1** (esperado 16) por cobertura casi nula. **Conclusión:
  Wikidata no sirve como fuente primaria ni de fallback para senadores/alcaldes/
  gobernadores.** Requieren **snapshot curado versionado** (senadores 50, gobernadores 16,
  alcaldes 345) desde fuentes oficiales, con `source_mode` honesto y `review_by`.

**Implicación de alcance:** solo `diputados` tiene fuente live limpia. La decisión de
alcance de la Ola A (qué cargos entran en v1 y con qué carril) queda registrada arriba en
"Decisión de carril" y se confirma con el operador antes de codificar los cargos curados.

#### Fuentes de los cargos curados — probadas (2026-07-03)

Se buscó una fuente oficial estructurada y **redistribuible** para senadores/gobernadores/
alcaldes. Resultado:

- **`datos.gob.cl` (CKAN):** sin listas consolidadas de autoridades (solo "Alcalde y
  Concejo" de un municipio aislado). Descartado como fuente nacional.
- **Datos municipales ya extraídos (`finanzas_municipales`, SINIM):** no incluyen el
  nombre del alcalde/alcaldesa (solo variables financieras). No hay atajo desde el
  catálogo actual.
- **Senadores/as (50):** `senado.cl` es una SPA (Next.js) sin endpoint XML/CSV limpio;
  requiere localizar su API interna o scraping. Esfuerzo/fragilidad **MED**.
- **Gobernadores/as (16):** sin fuente estructurada única encontrada; 16 registros →
  snapshot curado desde sitios oficiales de gobiernos regionales es defendible y
  verificable.
- **Alcaldes/as (345):** ❌ **sin fuente oficial estructurada y redistribuible.** SERVEL
  publica en Power BI no scrapeable (research §2.2). La única lista consolidada y
  mantenida es el "Anexo:Alcaldes de Chile" de Wikipedia, con licencia **CC-BY-SA
  (share-alike)** — **incompatible con la promesa de apertura CC-BY/CC0 del bundle**. La
  alternativa (curación manual de 345) se desactualiza en cada elección municipal
  (mantenimiento MED-ALTO). **`alcaldes` queda en la misma categoría "needs-source" que
  `resultados_electorales` hasta asegurar fuente redistribuible.**

**Decisión de alcance (operador, 2026-07-03):** v1 completo con los 4 cargos. Alcaldes
vía Wikipedia CC-BY-SA, aislado y marcado (no contamina el resto del bundle CC-BY/CC0).

#### Verificación final de fuentes (Step 0 completo — 2026-07-03)

Mapa de fuentes tras probar todas las vías:

| Cargo | N | Fuente | Estado | Método |
|-------|---|--------|--------|--------|
| Diputados/as (roster+partido) | 155 | Cámara WS `retornarDiputadosPeriodoActual` | ✅ **live, limpia, verificada** | XML stdlib |
| Diputados/as (distrito) | — | ❌ **no está en el API de la Cámara** | verificado en 3 endpoints + lista completa (644 KB, 0 hits) | scraping del perfil HTML `camara.cl` (fragilidad) |
| Senadores/as | 50 | `senado.cl` (SPA Next.js) | ⚠️ sin endpoint limpio | Playwright (patrón SINIM) o API interna a localizar |
| Gobernadores/as | 16 | gobiernos regionales / oficial | ⚠️ sin fuente estructurada única | snapshot curado (16, verificable) |
| Alcaldes/as | 345 | Wikipedia `Anexo:Alcaldes de Chile` (CC-BY-SA) | ⚠️ **no es tabla única** | la página raíz enlaza ~345 subpáginas por comuna; agregar vía API MediaWiki, o SERVEL Playwright |
| **Partidos (Ola B)** | 36 | Cámara WS `WSComun.asmx/retornarPartidosPoliticos` | ✅ **institucional, limpia, verificada** | XML stdlib; roster Id/Nombre/Alias (sin estado legal/fecha → completar con SERVEL) |

**Consecuencia realista:** solo `diputados` es de bajo esfuerzo. Los otros tres cargos
requieren **infraestructura de scraping** (Playwright para senado/SERVEL; agregación
multi-página para alcaldes en Wikipedia) — factible (el repo ya usa Playwright para
SINIM), pero es trabajo real por fuente, no un "snapshot" trivial. Se construye de forma
incremental y verificada, cargo por cargo, empezando por diputados. `alcaldes` lleva nota
de licencia CC-BY-SA en `DATA_LICENSES.md` y columna `licencia` por fila.

---

### Ola A — `autoridades_electas`

### Step A1: Contrato del dataset

Crea `contracts/datasets/autoridades_electas.schema.json` copiando la forma de
`contracts/datasets/distritos_electorales.schema.json`. Columnas (research §4.1):

```text
id_autoridad, nombre, cargo, institucion, partido, pacto,
distrito_electoral, circunscripcion_senatorial, codigo_comuna, codigo_region,
periodo_inicio, periodo_fin, estado_mandato, fuente, url_fuente, fecha_consulta
```

Reglas de dominio en el contrato: `cargo ∈ {diputado, senador, alcalde,
gobernador_regional, presidente}`; `estado_mandato ∈ {vigente, finalizado, reemplazo}`;
`codigo_comuna` con formato CUT (5 dígitos, solo alcaldes); `codigo_region` 2 dígitos
(gobernadores y senadores); fechas `YYYY-MM-DD` (`periodo_fin` nullable).

**Verify**: `test -f contracts/datasets/autoridades_electas.schema.json` y el JSON es
válido (`python -c "import json;json.load(open('contracts/datasets/autoridades_electas.schema.json'))"`).

### Step A2: Extractor

Crea `src/extractors/autoridades_electas_extractor.py` siguiendo el patrón de
`electoral_extractor.py`. Requisitos:

- **Diputados/as**: `GET` al endpoint XML de la Cámara; parseo **defensivo** con
  `ElementTree.find()`/`findall()` y valores por defecto claros ante tags ausentes.
  Mapear distrito → `distrito_electoral` cruzando con `distritos_electorales` existente.
- **Senadores/as, alcaldes/as, gobernadores/as**: Wikidata SPARQL (GET JSON). Alcaldes
  cruzan por `codigo_comuna` (CUT); senadores por `codigo_region`/circunscripción;
  gobernadores por `codigo_region`.
- **Fallback**: si una fuente falla, degradar con estridencia y usar el snapshot
  versionado (`fallback_policy: allowed_for_dev`), registrando `source_mode` honesto en
  el metadata (no marcar `live` si vino del fallback).
- Escribe `data/staging/autoridades_electas.csv` + `.metadata.json` con
  `write_staging_metadata()`. Incluye un `REUSE_POLICY` como en `electoral_extractor.py`.

**Verify**:
`PYTHONPATH=src .venv/bin/python src/extractors/autoridades_electas_extractor.py`
→ exit 0; el CSV existe y tiene ~566 filas (≈155+50+345+16), sin columnas de datos
personales.

### Step A3: Validadores de dominio (reconciliación)

Añade validación (en el `validate()` del extractor y/o en la capa de validación del
pipeline) que **reconcilie conteos** contra expectativas configurables con tolerancia:
diputados/as, senadores/as, alcaldes/as (≈ número de municipios), gobernadores/as (16).
Cruza `codigo_comuna` contra el DPA (comunas válidas) y `distrito_electoral` contra
`distritos_electorales`. Los conteos cambian con el calendario electoral: trátalos como
esperados con rango, no como constantes rígidas, y documenta el `review_by`.

**Verify**: `make verify` exit 0; un test unitario falla si el conteo cae fuera del rango.

### Step A4: Registro, catálogo y Makefile

- `data/source_registry.json`: añade entrada(s) para la(s) fuente(s) copiando la forma de
  una entrada `stable_publishable` (`bcn_regiones`). **Decisión de carril** (ver
  "Decisión de carril" abajo): si Step 0 confirmó fuentes estables y el snapshot de
  fallback está versionado, usa `publication_track: stable_publishable`,
  `public_bundle_eligible: true`; si hubo fragilidad, usa `candidate` con `review_by`
  a 90 días.
- `src/builders/catalog.py`: añade la entrada de `autoridades_electas` en
  `DATASET_CATALOG_CONFIG` (copia la forma de una existente; categoría "Institucional/
  Electoral").
- `Makefile`: añade en el target `extract`
  `PYTHONPATH=src $(PYTHON) src/extractors/autoridades_electas_extractor.py`.

**Verify**: `make extract` exit 0; `make build` exit 0; el dataset aparece en el
catálogo (`make catalog` o `make hub-list` lo lista).

### Step A5: Ficha de documentación

Crea `docs/datasets/autoridades_electas.md` copiando la estructura de
`docs/datasets/distritos_electorales.md`: descripción, fuentes, columnas, cobertura,
**declaración explícita de límite** (solo cargos públicos vigentes; sin datos personales;
sin resultados de votación), licencia, cadencia y `review_by`.

**Verify**: `test -f docs/datasets/autoridades_electas.md`.

### Step A6: Tests

Añade tests en `tests/` (extractor con HTTP mockeado — sigue el patrón de mocking del
repo; contrato; reconciliación de conteos; ausencia de columnas personales).

**Verify**: `make test` exit 0; los tests nuevos cubren el extractor y el contrato.

---

### Ola B — `partidos_politicos`

### Step B1–B6: repetir el patrón

Mismos artefactos con `partidos_politicos` (research §4.2). Diferencias:

- **Fuente**: **`WSComun.asmx/retornarPartidosPoliticos` de la Cámara** (verificada
  2026-07-03: 36 partidos con `Id`/`Nombre`/`Alias`, institucional, sin problema de
  licencia). Es el roster autoritativo; `estado_legal`/`fecha_constitucion`/`ambito` no
  vienen ahí → completar con SERVEL (registro de partidos) si se requieren esos campos, o
  dejarlos nullable en v1. Sustituye la vía Wikidata/SERVEL que sugería la research.
- **Contrato/columnas**: `id_partido, nombre, sigla, estado_legal, fecha_constitucion,
  ambito, url_fuente, fecha_consulta`; `estado_legal ∈ {constituido, en_formacion,
  disuelto}`; `ambito ∈ {nacional, regional}`.
- **Carril**: `stable_publishable` (institucional, lista pequeña y verificable).
- Extractor, entrada de registry, entrada de catálogo, ficha, línea en `Makefile extract`
  y tests, como en la Ola A.

**Verify** (por ola): `make extract && make build && make verify && make test` exit 0.

---

### Step Z: Verificación final e índice

1. `make refresh` (o `make extract build verify test verify-landing lint format-check`)
   → exit 0, sin regresiones.
2. Confirma que la landing regenerada muestra los datasets nuevos con su categoría y que
   `hub_health.json` los cuenta correctamente (`make hub-health`).
3. Actualiza `plans/README.md`: fila 023 → `DONE` (o el estado granular de la ola
   completada), muévelo a "archivados" solo cuando **ambas** olas estén `DONE`, y ajusta
   "Orden de ejecución recomendado".
4. Registra en `CHANGELOG` vía conventional commit (semantic-release genera las notas).

**Verify**: `git status` limpio salvo archivos en alcance; `make check` exit 0.

## Decisión de carril (robustez)

La research recomienda `stable_publishable` (bundle público) para ambos datasets, por ser
institucionales y redistribuibles. Antes de marcarlos `public_bundle_eligible: true`,
deben cumplirse **las tres** condiciones; si alguna falla, entra como `candidate` con
`review_by` a 90 días y se promueve tras una ventana de estabilidad:

1. Step 0 confirmó URLs/QIDs vivos y parseables.
2. Hay un **snapshot de fallback versionado** (el build no depende de la red).
3. Los validadores de reconciliación (Step A3) pasan con datos reales.

Esto honra el principio del gate B1/B2 del Plan 022: "ninguna capa frágil en el bundle
público".

## Test plan

- Extractor con HTTP mockeado (Cámara XML fixture + respuesta SPARQL fixture): parseo,
  normalización al esquema del contrato, y camino de fallback.
- Contrato: el dataset validado cumple `autoridades_electas.schema.json` /
  `partidos_politicos.schema.json`.
- Reconciliación: conteos por cargo dentro del rango esperado; `codigo_comuna` ⊂ DPA;
  `distrito_electoral` ⊂ `distritos_electorales`.
- Negativo: el dataset **no** contiene columnas de datos personales (RUN, domicilio,
  mesa, afiliación individual) — test explícito que falla si aparecen.
- `make test` completo sin regresiones (~490 tests baseline).

## Done criteria

**Ola A** (todas):
- [ ] `contracts/datasets/autoridades_electas.schema.json` existe y valida el dataset.
- [ ] `src/extractors/autoridades_electas_extractor.py` genera staging CSV + metadata.
- [ ] Entrada(s) en `data/source_registry.json` con carril decidido y justificado.
- [ ] Entrada en `DATASET_CATALOG_CONFIG` (`src/builders/catalog.py`).
- [ ] `docs/datasets/autoridades_electas.md` con declaración de límite de datos.
- [ ] Línea en `Makefile` target `extract`; snapshot de fallback versionado.
- [ ] Tests del extractor + contrato + reconciliación + negativo de datos personales.
- [ ] `make refresh` exit 0; sin regresiones; landing y `hub_health` reflejan el dataset.

**Ola B**: los mismos criterios con `partidos_politicos`.

**Cierre**:
- [ ] `plans/README.md` actualizado (estado/orden); archivado cuando ambas olas `DONE`.
- [ ] `make check` exit 0.

## STOP conditions

Detente y reporta (no improvises) si:

- La fuente de Cámara no responde, no es XML, o cambió de esquema de forma que el parseo
  defensivo no cubre (drift respecto a la research §5).
- Wikidata no expone senadores/alcaldes/gobernadores vigentes como cargos estructurados,
  o los conteos no reconcilian con el orden esperado (posible QID equivocado).
- Cualquier fuente exigiría extraer datos personales (RUN, domicilio, mesa, afiliación
  individual) para completar el dataset — es **línea roja dura**, se descarta la fuente.
- Un dataset no puede construirse sin red y sin snapshot de fallback (rompería builds
  offline/CI).
- Aparece presión para incluir `resultados_electorales` — está fuera de alcance y
  diferido; no lo construyas en este plan.

## Maintenance notes

- **Cadencia y `review_by`**: los conteos de autoridades cambian con el calendario
  electoral (elecciones parlamentarias/municipales/presidenciales). Fija `review_by`
  cerca del próximo hito electoral y ajusta los rangos de reconciliación entonces.
- **Wikidata es caché, no fuente primaria** (research §7): puede estar desactualizada;
  verifica contra fuente oficial cuando haya discrepancia. No la trates como autoritativa
  para fechas de mandato.
- **`resultados_electorales`**: revisión trimestral (research §4.3). Activar solo si
  aparece fuente estructurada estable por comuna (export CSV/Excel oficial de SERVEL,
  mirror en datos.gob.cl, o agregados por comuna en TRICEL). Sería un Plan 024.
- **Enriquecimiento cruzado**: una vez publicado, `autoridades_electas` habilita cruces
  con `distritos_electorales`, `comunas` y `perfil_territorial_comunal` — candidato a
  columna derivada en el perfil territorial (follow-up, no en este plan).
</content>
</invoke>
