# ADR-012: Geometría comunal — fuente, licencia y decisión técnica

**Fecha:** 2026-07-23
**Estado:** accepted (compuerta de licencia del Plan 053 Step 1 — decisión técnica, no requiere ratificación de estrategia de producto; ver ADR-011 para esa compuerta separada)
**Decision:** Se confirma fuente y licencia redistribuible para la geometría de límites comunales de Chile. El Plan 053 **continúa** hacia el Step 2 (extracción), sujeto a que ADR-011 (estrategia) sea ratificado por el mantenedor antes de publicar el artefacto.

## Contexto

El Plan 053 Step 1 exige confirmar, de forma explícita y separada de los atributos DPA (ya
verdes en `AGENTS.md` §6), que **la geometría** (los polígonos, no solo la tabla de atributos)
tiene licencia redistribuible. Esta es una compuerta que puede matar el plan si no se confirma.

## Investigación

### Fuente candidata

Se exploró la familia de servicios ArcGIS de BCN (`arcgiswebad.bcn.cl/arcgis/rest/services/`,
la misma raíz que ya usa `subdere_extractor.py` para atributos DPA). Se enumeraron las carpetas
`Hosted`, `SIIT` y `tematico`. La capa `tematico/Comunas_Generalizadas` (MapServer, layer 0,
nombre interno `chilegeneralizado`, `geometryType: esriGeometryPolygon`) expone polígonos
comunales de todo Chile con los campos `cod_comuna` (entero, CUT sin padding), `nom_com`,
`nom_reg`, `nom_prov`, `codregion`, entre otros.

Verificación funcional (`returnGeometry=true`, filtro `cod_comuna=13101`):

```
curl -s ".../tematico/Comunas_Generalizadas/MapServer/0/query?where=cod_comuna=13101&outFields=cod_comuna,nom_com,nom_reg&returnGeometry=true&f=json"
```

devuelve `geometry.rings` no vacío para Santiago (Región Metropolitana) — la capa es funcional
y consultable por `cod_comuna`, que mapea 1:1 al `codigo_comuna` (CUT) del resto del hub (tras
zero-pad a 5 caracteres, invariante #1 — el campo llega como entero, ej. `13101`, y para
regiones como Tarapacá se debe verificar que no se pierda el cero inicial al castear a string).

El nombre `Comunas_Generalizadas` ("generalizada" = geometría simplificada para cartografía a
escala nacional) es una señal favorable para el plan: reduce de entrada el riesgo de tamaño de
artefacto que el Step 3 pide evaluar.

### Licencia

BCN publica sus mapas vectoriales (SIIT) también como descarga estática en
`https://www.bcn.cl/siit/mapas_vectoriales/index_html`, con una sección explícita de
condiciones de uso:

> "Los mapas vectoriales son puestos a disposición en virtud del principio de transparencia de
> la función pública. Las personas o instituciones pueden usar libremente esta información,
> señalando como fuente a la Biblioteca del Congreso Nacional de Chile."

Esa misma página lista explícitamente **"División comunal" (30.6 MB)** entre las capas
descargables — es decir, la geometría de límites comunales (no solo los atributos) está
cubierta por esta declaración de uso libre con atribución. Advertencia declarada en la misma
página: el material es de referencia y no debe usarse para trabajo que requiera precisión
geodésica — no es una restricción de redistribución, es un disclaimer de precisión (que además
refuerza que simplificar geometría para reducir tamaño del artefacto, per Step 3, no degrada
nada que la fuente ya garantice).

La capa ArcGIS `tematico/Comunas_Generalizadas` es la misma división comunal de BCN servida por
un canal técnico distinto (REST en vez de shapefile descargable) bajo el mismo dominio
institucional (`bcn.cl` / `arcgiswebad.bcn.cl`) — se trata de la misma fuente y la misma
declaración de condiciones de uso aplica.

**Clasificación bajo el semáforo de `AGENTS.md` §6**: 🟢 `open-attribution` — cumple el primer
criterio de "origen primario es redistribuible" (institución pública chilena, acceso público,
declaración explícita de uso libre con atribución) y además supera el criterio mínimo: no es
solo "sin restricción explícita", hay una declaración *afirmativa* de uso libre con atribución,
equivalente en efecto a CC-BY.

## Decision

- **Fuente confirmada**: capa ArcGIS `tematico/Comunas_Generalizadas` (MapServer, layer 0,
  `chilegeneralizado`) de `arcgiswebad.bcn.cl`, respaldada por la declaración de condiciones de
  uso de `bcn.cl/siit/mapas_vectoriales` que cubre explícitamente "División comunal".
- **Licencia confirmada**: uso libre con atribución obligatoria a "Biblioteca del Congreso
  Nacional de Chile" — clasificación 🟢 `open-attribution`. El dataset `geometria_comunal.md`
  (Step 5) debe incluir esta cita de atribución literal.
- **La compuerta del Step 1 PASA.** El plan continúa hacia el Step 2 (extracción a staging),
  Step 3 (artefacto GeoParquet) y Step 4 (`resolve_by_coords()`, opcional/desacoplado) — sujetos
  a la ratificación de ADR-011 (estrategia construir-por-delante-de-demanda), que sigue
  `proposed` y requiere revisión del mantenedor antes de que el artefacto se considere
  autorizado para publicación.
- **Decisión técnica preliminar para el Step 2** (a confirmar al ejecutarlo): crear un extractor
  nuevo `src/extractors/geometria_comunal_extractor.py` en vez de extender
  `subdere_extractor.py`, tal como recomienda el plan, para no arriesgar el dataset base
  `comunas`. Debe castear `cod_comuna` a string de 5 caracteres con zero-pad (invariante #1) y
  validar que las 346 comunas del DPA existen en la respuesta.

## Consecuencias

- Positivas: no hace falta un fallback de "solo enlazar la fuente" (§6, regla conservadora) —
  el hub puede redistribuir el artefacto GeoParquet completo, que es el entregable flagship del
  plan.
- Negativas / riesgo residual: la geometría es "generalizada" (simplificada), no de precisión
  geodésica — aceptable y hasta deseable para el caso de uso de reverse geocoding y para
  mantener el artefacto liviano, pero debe documentarse explícitamente en
  `docs/datasets/geometria_comunal.md` (Step 5) para que nadie la use para trabajo catastral o
  de precisión legal de límites.
- El campo fuente es `cod_comuna` entero (no string de 5 con padding) — el extractor del Step 2
  debe manejar el cast con cuidado para no repetir el bug de invariante #1 que el proyecto
  activamente previene (pérdida de cero inicial en códigos de Tarapacá y similares).

## Step 3 — decisión de arquitectura: fuera del build diario, no en `build_dev_db.py`

**Decisión revisada tras revisión de arquitectura**: la primera versión de este Step 3 wireó
`geometria_comunal` dentro de `_load_inputs`/`_compute_validations`/`_write_data_artifacts` de
`src/build_dev_db.py`, siguiendo el patrón de datasets opcionales como `pobreza_comunal` o
`consumo_electrico_comunal`. Esto era **incorrecto**: esos datasets SÍ corren en `make extract`
(están en el Makefile), mientras que `geometria_comunal` es explícitamente carril `candidate` /
cadencia `bajo_demanda` — **no** está en `make extract`. El precedente correcto son
`delincuencia_comunal` y `autoridades_locales`: ninguno de los dos tiene **ninguna** referencia
en `build_dev_db.py`; ambos tienen `"outputs"` **omitido** (no `null`, simplemente ausente) en
`data/dataset_catalog_config.json`; `delincuencia_comunal` publica su ciclo completo
(extract → validate ligero → commit del CSV de staging) desde su propio job en
`.github/workflows/monthly-scrape.yml`, totalmente desacoplado del build diario.

Wireear `geometria_comunal` en el build diario tenía dos consecuencias que rompían la
arquitectura CI:
1. **`EXPECTED_DATASET_COUNT` (test de contrato) se vuelve no determinista**: el conteo pasaría
   a depender de si alguien corrió el extractor de geometría manualmente antes del build, algo
   que `make extract` nunca hace.
2. **Peor**: declarar `"outputs": {"parquet": ...}` en el catálogo estático hace que
   `scripts/verify_pipeline.py` (`_derive_dataset_artifact_paths()`, que lee
   `DATASET_CATALOG_CONFIG` — el catálogo **estático**, no el generado) exija
   `data/normalized/geometria_comunal.parquet` en **todo** `make verify`, incluido el build
   diario de CI que nunca genera ese archivo. Habría dejado el pipeline diario rojo.

**Decisión final**: `geometria_comunal` sigue exactamente el patrón de `delincuencia_comunal`:
- **Sin ninguna referencia en `src/build_dev_db.py` ni `src/builders/metadata.py`.**
- **`"outputs"` omitido** en `data/dataset_catalog_config.json` (no participa de
  `REQUIRED_DATASETS`/`_derive_dataset_artifact_paths()` de `verify_pipeline.py`).
- `validate_geometria_comunal` (en `src/validation.py`) se registra como excepción explícita en
  `ALLOWED_UNREGISTERED_VALIDATORS` de `scripts/check_validation_registration.py` (mismo patrón
  que la excepción ya existente `puntos_interes`).
- Contrato (`contracts/datasets/geometria_comunal.schema.json`) y doc
  (`docs/datasets/geometria_comunal.md`) **sí** se mantienen — `check_companion_paths.py
  registry` los exige para toda entrada del catálogo estático, con o sin `outputs`
  (`delincuencia_comunal` también tiene ambos pese a `outputs` ausente).
- **Nuevo script standalone `scripts/build_geometria_comunal.py`**: ejecuta el ciclo completo
  extract → valida (`validate_geometria_comunal`, fail-loud vía `SystemExit` si hay error real,
  a diferencia del patrón "no abortar" de `delincuencia_comunal" — geometria SÍ tiene un
  artefacto público que debe ser correcto) → escribe el GeoParquet
  (`write_geometria_comunal_parquet`). Corre a demanda o desde un futuro workflow de CI
  dedicado (diferido, ver "Maintenance notes" del plan) — nunca desde `make build`.
- No consumible vía `hub.load_polars()` (que resuelve contra el catálogo **generado**,
  `data/normalized/dataset_catalog.json`, donde `geometria_comunal` no aparece) — el acceso es
  directo al archivo (`gpd.read_parquet(...)`), ya documentado así en
  `docs/datasets/geometria_comunal.md` incluso antes de esta corrección.

**Verificado**: `git grep -i geometria src/build_dev_db.py src/builders/metadata.py` no
devuelve nada (revert limpio); `make build` (sin `geometria_comunal.csv` participando) reproduce
el catálogo generado tal como era antes de este plan; `scripts/build_geometria_comunal.py
--skip-fetch` (reusando el staging ya extraído) escribe el artefacto correctamente por
separado; `check_companion_paths.py registry` y `check_validation_registration.py` pasan.

## Step 3 — decisión de mecánica del artefacto GeoParquet

**Librería**: `geopandas.GeoDataFrame.to_parquet(geometry_encoding="WKB", schema_version="1.0.0")`,
no `pyarrow` manual. Se evaluó escribir el footer `geo` (metadata GeoParquet) a mano con
`pyarrow` para evitar la dependencia de `geopandas` (más pesada: trae `pyogrio` + `pyproj`), pero
el spec de metadata GeoParquet 1.0 (bbox, CRS en PROJJSON, tipos de geometría) tiene superficie
suficiente para justificar delegarlo a una librería madura en vez de reimplementarlo — cero
beneficio de build-time en hacerlo a mano. `shapely` (ya usado por el extractor del Step 2) y
`geopandas` se agregaron al extra `pipeline` de `pyproject.toml` (build-time only, **no**
tocan `[project.dependencies]` ni el extra público `geo` de la Capa 2/Step 4).

Verificado: el artefacto escrito es GeoParquet 1.0 válido (footer `geo` con
`version: "1.0.0"`, `columns.geometry.encoding: "WKB"`), legible tanto por `geopandas.read_parquet`
(reconoce la geometría, CRS EPSG:4326) como por `pl.read_parquet` plano (la columna `geometry`
llega como `pl.Binary` — exactamente lo que necesita `verify_pipeline.py`, que usa
`pl.read_parquet` para validar contratos). `codigo_comuna`/`codigo_region` sobreviven el
round-trip completo (CSV → Polars con `schema_overrides` → GeoDataFrame → GeoParquet → Polars)
sin perder ceros iniciales (probado explícitamente con `01101`, Iquique).

Nota menor: `pl.read_parquet` emite un `UserWarning` benigno ("Extension type 'geoarrow.wkb' is
not registered") al leer el archivo — es `pyarrow` anotando metadata de extensión Arrow interna
sobre la columna binaria; no afecta la lectura (cae a `pl.Binary` igualmente) ni la validez del
archivo como GeoParquet 1.0/WKB. No requiere acción.

**Tolerancia de simplificación**: se evaluaron 6 tolerancias (`shapely.simplify`,
`preserve_topology=True`) sobre las 345 comunas reales extraídas:

| Tolerancia (grados) | Tamaño del artefacto |
|---|---|
| 0 (sin simplificar) | 27.8 MB |
| 0.001 (~100 m) | **4.98 MB** ← elegida |
| 0.005 (~550 m) | 2.45 MB |
| 0.01 (~1.1 km) | 2.15 MB |
| 0.02 (~2.2 km) | 1.99 MB |
| 0.05 (~5.5 km) | 1.90 MB |

Se eligió **0.001° (~100 m)**: reduce el artefacto en ~82% (27.8 MB → 4.98 MB) preservando forma
reconocible de cada comuna — más allá de 0.01 los retornos son marginales (2.15 MB → 1.90 MB
entre 0.01 y 0.05) mientras el riesgo de distorsionar comunas pequeñas o angostas crece. La
fuente ya es "generalizada" (no geodésica), así que esta simplificación adicional es coherente
con el disclaimer de precisión ya declarado, no una degradación nueva de la promesa de calidad.
Ningún polígono colapsó a vacío (`is_empty`) en ninguna tolerancia probada.

**Hallazgo operativo — el hook local `check-added-large-files` (`--maxkb=500`,
`.pre-commit-config.yaml:11`) bloquea un commit local de `geometria_comunal.parquet` incluso
simplificado** (4.98 MB ≫ 500 KB). Este límite es anterior a este plan y evidentemente calibrado
para código fuente, no para artefactos de datos: `data/normalized/empresas.parquet` (28.5 MB) ya
vive en el historial de git, lo que indica que los artefactos grandes del pipeline se commitean
vía el workflow de CI (`monthly-scrape.yml`/`pipeline-check.yml`, que no corre pre-commit local)
y no vía `git commit` interactivo. Por disciplina de "nunca saltar hooks sin instrucción
explícita", el ejecutor de este plan **no** commiteó el binario `geometria_comunal.parquet`
generado — el código (extractor, validador, writer, wiring de `build_dev_db.py`, contrato, docs)
sí quedó commiteado y verificado (`make build` produce el artefacto correcto localmente). Queda
como decisión del mantenedor: (a) subir `--maxkb` para permitir el commit local de este dataset
específico, o (b) dejar que el artefacto se genere y commitee solo vía el pipeline de CI, igual
que `empresas.parquet`.

## Alternativas consideradas

- **Usar la descarga estática del shapefile "División comunal" (30.6 MB) en vez del endpoint
  ArcGIS REST** — no descartada, sigue siendo una fuente válida bajo la misma licencia; se
  prefiere el endpoint REST en el Step 2 porque es consultable programáticamente (mismo patrón
  que ya usa `subdere_extractor.py` para atributos) y no requiere manejo de un ZIP/shapefile
  binario en el pipeline. Si el endpoint REST cambia o se degrada, el shapefile estático es el
  fallback documentado aquí.
- **Reconstruir polígonos desde OpenStreetMap** — descartada sin necesidad de evaluarla a fondo:
  la fuente BCN ya es oficial, ya está en uso por el hub, y tiene licencia confirmada; no hay
  motivo para introducir una fuente adicional (anti-patrón de dispersión que ADR-011 explícitamente excluye).
