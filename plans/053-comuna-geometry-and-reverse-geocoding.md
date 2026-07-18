# Plan 053: Geometría comunal (GeoParquet) + reverse geocoding `resolve_by_coords()`

> **Executor instructions**: Este es un **feasibility-spike con entregable de datos**.
> Sigue los pasos en orden y respeta las compuertas (gates). El Step 1 es una
> **compuerta de licencia que puede matar el plan** — si no se confirma, detente y
> reporta (no improvises un scraping de geometría de dudosa licencia). Ejecuta cada
> verificación antes de avanzar. Al terminar, actualiza la fila de estado en
> `plans/README.md`.
>
> **Decisión de producto que habilita este plan**: el mantenedor autorizó
> explícitamente **construir capacidad por delante de la demanda** ("a veces hay que
> crear la oferta para generar la demanda"). Este plan es el primer fruto de esa
> decisión. La disciplina que se **mantiene** pese a esa luz verde: nada de dispersión
> hacia fuentes frágiles — este plan profundiza sobre una fuente **ya usada y de alta
> calidad** (BCN ArcGIS), no agrega scraping nuevo. Ver Step 0 (ADR-011).
>
> **Drift check (córrelo primero)**:
> `git diff --stat 7ebf94b..HEAD -- src/extractors/subdere_extractor.py data/dataset_catalog_config.json data/source_registry.json pyproject.toml src/chile_hub/core.py`
> Ante cualquier discrepancia con los excerptos de "Estado actual", trátalo como STOP.

## Status

- **Priority**: P1 (flagship de la estrategia construir-por-delante-de-demanda)
- **Effort**: L (spike de factibilidad + artefacto de datos + método opcional)
- **Risk**: MED (la licencia de la geometría es un riesgo real de kill; ver Step 1)
- **Depends on**: none. **Complementa** al Plan 050 (`resolve_comunas` por nombre) pero
  NO lo bloquea ni depende de él — son superficies hermanas de resolución de entidades.
- **Category**: direction
- **Planned at**: commit `7ebf94b`, 2026-07-14

## Why this matters

La fricción #1 de cualquiera que trabaje con datos geográficos chilenos es
**reverse geocoding**: "tengo lat/lon (de un GPS, una dirección geocodificada, un
sensor) y necesito saber en qué comuna cae". Hoy no hay forma barata de hacerlo con
datos oficiales abiertos. `chile-hub` está a un artefacto de distancia de resolverlo, y
la evidencia raya en lo irónico:

- El extractor ya trae lógica para calcular centroides desde polígonos
  ([subdere_extractor.py:358-370](../src/extractors/subdere_extractor.py#L358-L370),
  `_extract_coords` soporta `Point` y `Polygon`)...
- ...pero el endpoint que consultas es una **tabla de atributos** con
  [`returnGeometry: "false"`](../src/extractors/subdere_extractor.py#L394), y luego
  enriqueces coordenadas desde un CSV estático. Es decir: **descartas la geometría a
  propósito y la rodeas a mano**.

BCN publica los polígonos de límites comunales a través de su plataforma ArcGIS (la
misma familia de fuente que ya usas). Exponerlos como **GeoParquet** entrega dos cosas:

1. **Un artefacto que la gente comparte** (el generador de demanda): un
   `limites_comunales.geoparquet` usable directo en QGIS, geopandas, deck.gl,
   Observable, sin instalar `chile-hub`. Ese es el activo viral.
2. **`resolve_by_coords()`**: el hermano geoespacial de `resolve_comunas()` del Plan
   050 — juntos forman la capa de **resolución de entidades territoriales** de Chile
   (por nombre y por coordenada).

## Current state

- `src/extractors/subdere_extractor.py:68` — servicio BCN actual (atributos, sin geom):
  ```python
  "https://arcgiswebad.bcn.cl/arcgis/rest/services/Hosted/Capa_Factores/FeatureServer/0/query"
  ```
  y `:393-394`: `"returnGeometry": "false",  # Capa_Factores es tabla de atributos, sin geometría`.
- `src/extractors/subdere_extractor.py:357-370` — `_extract_coords`, ya sabe leer
  `geometry` de un feature ArcGIS (Point y Polygon, `outSR=4326`).
- `data/dataset_catalog_config.json` — dict keyed por dataset; cada entrada tiene
  `outputs` (formatos publicados). Las claves actuales incluyen `regiones`,
  `provincias`, `comunas`, `comunas_enriquecidas`, `indicadores`, …
- `pyproject.toml` — runtime slim (Plan 032): `dependencies = ["polars>=1.41.2,<2", …]`
  (4 entradas). Extras opcionales existentes: `pipeline`, `query`, `validation`, `dev`,
  `scraping`. **Toda dependencia geoespacial pesada va en un extra nuevo `geo`, nunca
  en `dependencies`.**
- `tests/test_chile_hub.py:969` — `ArtifactContractTests`: verifica el schema de los
  artefactos publicados. Si agregas una columna al dataset `comunas`, este test se
  rompe (y con razón — ver Boundary).

Convenciones que aplican:

- **§6 política legal** (`AGENTS.md:455`): *"Ante cualquier duda sobre la licencia de
  una fuente, no redistribuir el dato. Publicar los metadatos y el enlace a la fuente
  original en su lugar."* Esto gobierna el Step 1.
- **Invariante #1**: `codigo_comuna` es string de longitud fija de 5 (la FK para unir la
  geometría de vuelta con el resto del hub).
- **§5 agregar dataset** (`AGENTS.md:275`): flujo de 7 pasos (extractor → catalog config
  → validación → tests → CI → docs). La geometría entra como **dataset nuevo**, no como
  columna de uno existente.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Probar el endpoint ArcGIS candidato (Step 1) | `curl -s "<URL>/query?where=1=1&outFields=*&returnGeometry=true&resultRecordCount=1&f=json" \| head -c 2000` | JSON con un `geometry.rings` no vacío |
| Build (genera artefactos) | `make build` | exit 0 |
| Instalar extra geo (Step 4) | `uv sync --extra geo` | exit 0 |
| Tests (no requieren normalized) | `./.venv/bin/pytest tests/test_extractors.py tests/test_validation.py -v` | pasan |
| Tests de contrato (requieren build) | `make build && ./.venv/bin/pytest tests/test_chile_hub.py -v -k Contract` | pasan |
| Lint / format | `make lint && make format-check` | exit 0 |

## Scope

Se entrega por capas; la **Capa 1 (artefacto de datos) es el entregable primario** y
aterriza el valor flagship aunque la Capa 2 (método) se difiera.

**In scope**:

- `docs/adr/ADR-011-estrategia-construir-por-delante-de-demanda.md` — lo escribe el
  executor como Step 0 (yo, el advisor, no puedo escribir bajo `docs/`).
- `docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md` — decisión técnica, tras
  confirmar factibilidad (Step 1).
- `src/extractors/subdere_extractor.py` **o** un extractor nuevo
  `src/extractors/geometria_comunal_extractor.py` (el Step 2 decide cuál) — trae la
  geometría.
- `data/dataset_catalog_config.json` + `data/source_registry.json` — registra el
  dataset nuevo `geometria_comunal` (carril `candidate` inicialmente).
- `src/validation.py` + `tests/test_validation.py` — `validate_geometria_comunal`.
- `src/builders/` — writer GeoParquet del artefacto (mecánica es salida del spike).
- `contracts/datasets/geometria_comunal.schema.json` + `docs/datasets/geometria_comunal.md`
  (requeridos por `check_companion_paths.py registry`).
- `tests/test_extractors.py` — clase del extractor (gate de co-cambio).
- `pyproject.toml` — extra `geo` (Capa 2).
- `src/chile_hub/core.py` + `tests/test_core.py` — `resolve_by_coords()` (Capa 2).
- `.github/workflows/pipeline-check.yml` — paso de extracción (si aplica).
- `plans/README.md` — fila de estado.

**Out of scope / Boundary (NO tocar)**:

- **La geometría es un artefacto SEPARADO. NUNCA una columna en el dataset `comunas`.**
  Agregarla a `comunas` infla el dataset que todos cargan por defecto y rompe
  `ArtifactContractTests` (`tests/test_chile_hub.py:969`). Se une de vuelta por
  `codigo_comuna` (string fijo de 5).
- **El artefacto DEBE usar extensión `.parquet`, NUNCA `.geoparquet`.** El `.gitignore`
  re-incluye en `data/normalized/` sólo `*.json`, `*.md` y `*.parquet` (`.gitignore:8-11`;
  la línea 8 `data/normalized/*` re-excluye todo lo demás). Un `.geoparquet` quedaría
  **silenciosamente gitignoreado** — no commiteado, no servido en Pages, e invisible para
  la distribución HTTP/DCAT del Plan 051 que debe transportarlo. Y de todos modos
  GeoParquet **es** Parquet con metadata geo en el footer, no una extensión distinta: el
  nombre idiomático es `geometria_comunal.parquet`.
- **Ninguna dependencia geoespacial en `[project.dependencies]`.** Va en el extra `geo`.
  `resolve_by_coords()` debe importar la lib geo de forma lazy y lanzar un `ImportError`
  con "pip install chile-hub[geo]" si falta (mismo patrón que `sql()` /
  `from_datapackage()` en `core.py`).
- **No hagas scraping HTML de geometría** ni la tomes de una fuente de licencia dudosa
  (anti-patrón `AGENTS.md:708` + §6). Si BCN ArcGIS no confirma, el fallback es
  **enlazar la fuente**, no republicar (Step 1).

## Git workflow

- Branch: `advisor/053-comuna-geometry`
- Conventional commits, uno por capa/paso lógico (ej.
  `feat(data): publica límites comunales como GeoParquet`,
  `feat(geo): resolve_by_coords() reverse geocoding tras extra [geo]`).
- No push ni PR salvo instrucción del operador.

## Steps

### Step 0: Escribe ADR-011 (la decisión de estrategia)

Antes que nada, materializa la decisión de producto en el registro canónico del repo.
Crea `docs/adr/ADR-011-estrategia-construir-por-delante-de-demanda.md` (formato de los
ADR existentes; usa `docs/adr/ADR-004-carriles-de-publicacion.md` como plantilla).
Contenido:

- **Decisión**: se autoriza construir **capacidad de producto por delante de la
  demanda** ("crear la oferta para generar la demanda"), matizando el anti-patrón #10
  (`AGENTS.md:714`).
- **Alcance de la excepción** (el matiz que evita que esto sea barra libre): aplica a
  **profundidad de capacidad y distribución sobre fuentes existentes de alta calidad**
  (geometría, capa HTTP/DCAT, resolución de entidades). **NO** aplica a amplitud de
  datasets sobre fuentes frágiles (scraping HTML), que sigue gated por adopción.
- **Consecuencias**: los Planes 053 (este) y 051 se ejecutan sin esperar señal de
  adopción; el Plan 052 (señal de adopción) sigue siendo valioso para *medir* la demanda
  que se genere.
- **Estado**: `proposed` — marca claramente que requiere ratificación del mantenedor si
  este plan lo ejecuta un agente.

**Verify**: `test -f docs/adr/ADR-011-estrategia-construir-por-delante-de-demanda.md && grep -c "anti-patrón\|anti-patron\|#10" docs/adr/ADR-011-estrategia-construir-por-delante-de-demanda.md` → ≥ 1

### Step 1: GATE DE LICENCIA — confirma fuente y derechos de la geometría (puede matar el plan)

**Esta es la compuerta que decide si el plan procede.** No escribas nada de ingeniería
de GeoParquet hasta cerrarla.

1. **Fuente**: encuentra el servicio ArcGIS de BCN (u otra fuente oficial redistribuible)
   que expone la geometría de límites comunales con `codigo_comuna` (CUT). Punto de
   partida: la familia `arcgiswebad.bcn.cl/arcgis/rest/services/` (la que ya usas para
   atributos). Prueba capas hermanas con `returnGeometry=true`:
   ```
   curl -s "https://arcgiswebad.bcn.cl/arcgis/rest/services/?f=json" | head -c 3000
   ```
   y localiza una capa con geometría poligonal comunal.
2. **Licencia**: confirma explícitamente que **la geometría** (no sólo los atributos DPA,
   que ya sabes son CC-BY) es redistribuible. Esta es una pregunta **distinta**: los
   atributos pueden ser CC-BY y la capa vectorial tener otros términos. Busca la
   declaración de licencia del servicio/portal.

**Decisión**:
- Si confirmas fuente **y** licencia redistribuible → documenta ambas en
  `ADR-012-geometria-comunal-y-reverse-geocoding.md` (crear) y **continúa**.
- Si **no** puedes confirmar la licencia de la geometría → **STOP**. No republiques.
  Registra el hallazgo en ADR-012, y como fallback documenta en
  `docs/datasets/geometria_comunal.md` el enlace a la fuente oficial (patrón §6: publicar
  metadatos + enlace, no el dato). Reporta al operador y termina el plan aquí.

**Verify**: `test -f docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md && grep -iE "licencia|license" docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md` → muestra la línea con la licencia confirmada (o la razón del STOP).

### Step 2: Extrae la geometría → staging (GeoJSON/WKT)

Con la fuente confirmada, trae los polígonos. Decide (y documenta en ADR-012) si
extiendes `subdere_extractor.py` (activando `returnGeometry=true` en una capa que la
tenga) o creas `geometria_comunal_extractor.py` nuevo. Recomendación: **extractor
nuevo**, para no arriesgar el dataset base `comunas` que ya funciona. El extractor debe
seguir el contrato de `BaseExtractor` (`src/extractors/base.py`), guardar snapshot en
`data/raw/`, y escribir la geometría a staging en un formato que el writer del Step 3
consuma (GeoJSON por comuna, o WKT en una columna). Carga `codigo_comuna` como string
fijo de 5 (invariante #1).

**Verify**: `python src/extractors/geometria_comunal_extractor.py && ls data/staging/geometria_comunal* && python -c "import polars as pl; df=pl.read_csv('data/staging/geometria_comunal.csv', schema_overrides={'codigo_comuna': pl.String}); assert df.height >= 340; assert df['codigo_comuna'].str.len_chars().max()==5; print('comunas con geom:', df.height)"` → ≥ 340 comunas con geometría, `codigo_comuna` de 5 chars.

### Step 3: Publica el artefacto GeoParquet (ENTREGABLE PRIMARIO)

Registra `geometria_comunal` en `data/dataset_catalog_config.json` (carril `candidate`
vía `data/source_registry.json`, siguiendo el patrón de un dataset candidate existente
como `delincuencia_comunal`), agrega `validate_geometria_comunal` en `src/validation.py`
(no vacío; unicidad de `codigo_comuna`; integridad referencial DPA — los 346 CUT deben
existir en `comunas`), regístrala en el bloque `validations = {…}` de `build_dev_db.py`,
y escribe el writer GeoParquet en `src/builders/`. **GeoParquet = Parquet con metadata
geo estándar** (usa `geopandas.to_parquet` o `pyarrow` con el schema geo); la mecánica
exacta es salida de este spike — documenta en ADR-012 qué lib se usó y por qué. El
artefacto es **separado** y **debe llamarse `geometria_comunal.parquet`** (extensión
`.parquet` obligatoria — ver Boundary; `.geoparquet` quedaría gitignoreado), NO una
columna de `comunas`. **Tamaño**: los polígonos de 346 comunas pueden pesar decenas de
MB y este repo commitea los artefactos a git + los sirve en Pages (cada clon lo paga);
evalúa en el spike una tolerancia de simplificación de geometría (en el espíritu del
guard de tamaño de Excel del Plan 030) y documenta la decisión en ADR-012.

**Verify**: `make build && ./.venv/bin/python -c "import polars as pl; df=pl.read_parquet('data/normalized/geometria_comunal.parquet'); assert df['codigo_comuna'].dtype==pl.String; print('filas:', df.height, 'cols:', df.columns)"` → artefacto existe, `codigo_comuna` string; y `./.venv/bin/pytest tests/test_chile_hub.py -v -k Contract` → los contratos de los datasets **existentes** siguen verdes (no rompiste `comunas`).

### Step 4 (Capa 2 — opcional, desacoplada): `resolve_by_coords()` tras extra `[geo]`

Agrega el extra `geo` en `pyproject.toml` (`[project.optional-dependencies]`, junto a
`query`/`validation`) con la lib de point-in-polygon (p. ej. `shapely` y/o `geopandas`).
Agrega `ChileHub.resolve_by_coords(points)` en `core.py`: importa la lib geo de forma
**lazy** (patrón de `sql()`/`from_datapackage()`), carga el GeoParquet, y para cada
`(lat, lon)` devuelve el `codigo_comuna`/`nombre_comuna` que lo contiene (o null +
`matched=False` si cae fuera de Chile). Devuelve `pl.DataFrame` con `input_lat`,
`input_lon`, `codigo_comuna`, `nombre_comuna`, `matched`. **Este paso no debe bloquear el
Step 3**: si point-in-polygon resulta más caro de lo esperado, entrega el artefacto y
difiere el método (regístralo como follow-up en ADR-012).

**Verify**: `uv sync --extra geo && ./.venv/bin/python -c "from src.chile_hub import ChileHub; h=ChileHub(); r=h.resolve_by_coords([(-33.45,-70.66)]); print(r.to_dicts())"` → la fila de Santiago centro resuelve a un `codigo_comuna` de la RM con `matched=True`.

### Step 5: Docs + contrato + CI

Crea `docs/datasets/geometria_comunal.md` (fuente, licencia confirmada en Step 1, schema,
ejemplos en geopandas/QGIS/`resolve_by_coords`) y
`contracts/datasets/geometria_comunal.schema.json` (requeridos por
`check_companion_paths.py registry`, `AGENTS.md §12`). Agrega el extractor al workflow si
corre en cadencia. Documenta que el artefacto GeoParquet se sirve por la capa HTTP
estática del Plan 051.

**Verify**: `./.venv/bin/python scripts/check_companion_paths.py registry` → exit 0 (contrato y doc presentes para `geometria_comunal`).

## Test plan

- `tests/test_extractors.py`: clase `GeometriaComunalExtractorTests` — smoke del `run()`,
  schema de staging, `codigo_comuna` string de 5. Modela sobre una clase existente.
- `tests/test_validation.py`: casos de `validate_geometria_comunal` — vacío, CUT
  duplicado, CUT que no existe en DPA. Modela sobre los tests de `validate_comunas`.
- `tests/test_core.py` (Capa 2): `resolve_by_coords` — punto conocido dentro de una
  comuna (RM), punto en el mar/fuera de Chile → `matched=False`, `codigo_comuna` es
  `pl.String`. Marca `@skipUnless` si `shapely`/`geopandas` no está instalado, para no
  romper la suite base.
- **Regresión clave**: `tests/test_chile_hub.py::ArtifactContractTests` debe seguir
  verde — prueba de que NO tocaste el schema de `comunas`.

**Verify**: `make build && ./.venv/bin/pytest tests/test_extractors.py tests/test_validation.py tests/test_chile_hub.py -v` → todos pasan, incluidos los nuevos.

## Done criteria

- [ ] ADR-011 (estrategia) y ADR-012 (geometría, con licencia confirmada o razón de STOP) existen.
- [ ] `data/normalized/geometria_comunal.parquet` (GeoParquet) existe, ≥ 340 comunas, `codigo_comuna` string de 5, integridad referencial con DPA verde.
- [ ] El schema del dataset `comunas` **no cambió**: `ArtifactContractTests` verde.
- [ ] Ninguna dependencia geo en `[project.dependencies]`: `grep -A6 "^dependencies = \[" pyproject.toml` no menciona shapely/geopandas; el extra `geo` sí.
- [ ] (Si Capa 2 se entregó) `resolve_by_coords([(-33.45,-70.66)])` resuelve a la RM con `matched=True`; falla con `ImportError` claro si `[geo]` no está instalado.
- [ ] `check_companion_paths.py registry` verde; doc y contrato de `geometria_comunal` presentes.
- [ ] `make lint && make format-check` exit 0.
- [ ] `git status` sin archivos fuera de "In scope".
- [ ] Fila de estado en `plans/README.md` actualizada.

## STOP conditions

Detente y reporta (no improvises) si:

- **La licencia de la geometría no se confirma** (Step 1) — es el kill-switch. No
  republiques bajo ninguna interpretación optimista; cae al fallback de enlazar la
  fuente y termina.
- No encuentras un servicio oficial con geometría comunal + `codigo_comuna` — reporta;
  no reconstruyas polígonos desde otra fuente de licencia distinta.
- El artefacto de geometría tiende a agregarse como columna de `comunas` para "ahorrar
  un dataset" — para; rompe la frontera dura de este plan.
- Point-in-polygon (Capa 2) exige meter una dep geo pesada al runtime base para que
  funcione — no lo hagas; el método vive tras el extra `geo` o se difiere.
- El código en `subdere_extractor.py` o el catalog config no coincide con "Estado
  actual" (drift desde `7ebf94b`).
- Cualquier verificación falla dos veces tras un intento razonable.

## Maintenance notes

- **ADR-011 requiere ratificación humana**: si un agente ejecuta este plan, el
  mantenedor debe revisar y aprobar ADR-011 (`proposed` → `accepted`) — es un cambio de
  estrategia de producto, no una decisión técnica delegable.
- **Qué escrutar en el PR**: (1) que `comunas` no ganó columnas (regresión de contrato);
  (2) que el runtime slim del Plan 032 se preservó (nada geo en `dependencies`); (3) que
  la licencia citada en ADR-012 y en la doc es real y verificable, no asumida.
- **Sinergia deferida**: el artefacto GeoParquet habilita un demo de mapa en la landing
  (junto al playground del Plan 020) y se distribuye por la capa HTTP/DCAT del Plan 051
  — ambos follow-ups de generación de demanda, fuera del alcance de este plan.
- **Complemento con 050**: `resolve_comunas` (nombre) + `resolve_by_coords` (coordenada)
  deberían documentarse juntos como "resolución de entidades territoriales" una vez que
  ambos existan.
