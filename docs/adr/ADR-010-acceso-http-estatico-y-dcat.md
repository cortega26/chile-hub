# ADR-010: Capa de acceso HTTP estatica documentada + catalogo DCAT (`data.json`)

**Fecha:** 2026-07-24
**Estado:** accepted
**Decision:** Se documenta y cosecha la capa de acceso HTTP estatica que ya existe
(artefactos de `data/normalized/` servidos por GitHub Pages bajo
`https://tooltician.com/chile-hub/`), se agrega un generador prototipo de catalogo
DCAT (`data.json`, perfil DCAT-US) derivado de `datapackage.json`, y
`ChileHub.from_datapackage()` deja de lanzar `FileNotFoundError` para un
argumento URL: ahora **valida** el descriptor remoto vía frictionless y levanta un
error explicito con las alternativas reales (en vez de la promesa incumplida
anterior). Devolver un `ChileHub` plenamente funcional sobre datos remotos queda
como follow-up (ver Preguntas abiertas #5). **Ningun servidor, endpoint dinamico,
auth o billing** -- solo archivos estaticos y un descriptor cosechable, consistente
con la exclusion explicita del product-spec de "una API publica que deba
mantenerse en linea 24/7".

## Contexto

La capa de acceso HTTP estatica ya existe y ya se consume en produccion, solo que
no esta documentada como modo de acceso ni es cosechable por terceros:

- Los artefactos normalizados estan commiteados (`.gitignore:7-11` reabre
  `data/normalized/*.{json,md,parquet}`) y se sirven en GitHub Pages via
  `pages-deploy.yml` (`path: .`).
- El propio `README.md` ya consume esos artefactos por HTTP con URL estable: los
  badges de Coverage/Data apuntan a
  `https://tooltician.com/chile-hub/data/normalized/coverage_badge.json` y
  `.../freshness_badge.json`. Es decir,
  `https://tooltician.com/chile-hub/data/normalized/` ya es un base URL publico y
  estable que devuelve JSON/Parquet.
- `src/builders/data_package.py::write_data_package_json()` ya genera
  `data/normalized/datapackage.json`, un descriptor Frictionless -- la fuente
  natural para traducir a un catalogo DCAT.

Faltan dos cosas para convertir hosting ya pagado en superficie de producto real:
descubribilidad estandar (un catalogo cosechable estilo `data.json`/DCAT-AP, el
formato que usan los portales de datos abiertos gubernamentales) y que el propio
cliente Python pueda consumir su hosting (`from_datapackage()` prometia aceptar
URLs en su docstring pero solo manejaba rutas locales).

## Decision

### 1. Base URL y contrato de estabilidad

Confirmado: `https://tooltician.com/chile-hub/` (ver `README.md`, badges de
Coverage/Data ya en produccion). `data/normalized/` es el directorio de artefactos
publicados y se regenera en cada build/publish -- **es "latest" mutable**, no una
URL pinada por version. No se implementa pinning por release en este spike (ver
Preguntas abiertas / follow-ups); el catalogo DCAT documenta este comportamiento
explicitamente en su descripcion para que un consumidor externo sepa que
`downloadURL` apunta siempre a la ultima build, no a un snapshot inmutable.

### 2. Perfil de catalogo: DCAT-US (default), no DCAT-AP

Se investigo que perfil cosecha **datos.gob.cl** (el portal de datos abiertos del
gobierno de Chile). No se pudo confirmar con certeza cual formato de harvesting usa
especificamente ese portal -- los portales de datos abiertos gubernamentales
tipicamente corren sobre CKAN, que soporta tanto un harvester nativo de
`data.json` (perfil DCAT-US / `project-open-data.json`, el usado por data.gov) como
extensiones DCAT-AP/DCAT-AP-ES (RDF/TTL, mas comun en portales europeos e
hispanohablantes como datos.gob.es) -- pero no se encontro documentacion especifica
de datos.gob.cl que confirme cual de los dos cosecha. **Se registra como pregunta
abierta** (ver abajo) y se usa **DCAT-US** (`dataset[]` + `distribution[]`, JSON
plano, sin RDF/TTL) como default por ser el perfil mas simple, mejor documentado
publicamente, y el que exige menos dependencias nuevas (JSON puro, sin librerias
RDF).

### 3. Fuente de verdad y mapeo campo -> campo

`data.json` se **deriva** de `datapackage.json` (nunca se edita a mano, consistente
con AGENTS.md §10/§12). Mapeo implementado en `src/builders/dcat_catalog.py`:

| DCAT-US (`data.json`) | Origen (`datapackage.json`) |
|---|---|
| `dataset[].title` | `resources[].title` |
| `dataset[].description` | `resources[].description` |
| `dataset[].identifier` | `resources[].name` (nombre del dataset) |
| `dataset[].modified` | `datapackage.json.created` (fecha del ultimo build) |
| `dataset[].license` | `resources[].licenses[0].path` (si existe) |
| `dataset[].distribution[].downloadURL` | `{BASE_URL}/data/normalized/{resources[].path}` (URL absoluta) |
| `dataset[].distribution[].mediaType` | `resources[].mediatype` |
| `dataset[].distribution[].format` | `resources[].format` |
| Top-level `title`/`description` | `datapackage.json.title`/`description` |

### 4. Fix de `from_datapackage(url)`

`ChileHub.from_datapackage()` detecta si `path_or_url` es una URL (`http://` o
`https://`) y, en ese caso, delega en `frictionless.Package(str(path_or_url))`
(frictionless resuelve URLs remotas nativamente) en vez de `Path(...).exists()`
(que siempre es `False` para una URL, produciendo el `FileNotFoundError` que el
docstring nunca debio prometer). El path local existente **no cambia** -- mismo
comportamiento, mismos tests verdes.

**Limitacion documentada (verificada en el codigo, no asumida)**: se confirmo que
`ChileHub.__init__` asume que `data_dir`/`catalog_path` es un directorio local
(`self.catalog_path.open("r", ...)` sobre un `Path` real) -- no existe hoy en
`core.py` ningun mecanismo que lea `dataset_catalog.json`/Parquet directamente
desde una URL arbitraria pasada como `data_dir`. Forzar ese soporte es exactamente
el rediseño de `__init__` que este spike **no** debe hacer (ver STOP conditions
del plan). Por eso `from_datapackage(url)` **valida** el descriptor remoto
(confirma que existe y es un Frictionless Data Package conforme) pero luego
levanta `ChileHubDataError` con un mensaje explicito señalando las dos rutas que
si funcionan hoy: `ChileHub()` sin argumentos (bundle publicado, cache
automatica) o consumir la URL directamente vía `docs/http-access.md`
(Polars/DuckDB/arrow leen Parquet por HTTP nativamente, sin pasar por
`ChileHub`). Cerrar esta limitacion (que `from_datapackage(url)` devuelva un
`ChileHub` plenamente funcional sobre datos remotos) queda como follow-up
explicito que requiere decidir el modelo de `data_dir` remoto en `__init__` --
fuera de alcance de este spike.

## Consecuencias

- Positivas: convierte hosting ya pagado (GitHub Pages) en superficie de producto
  real y descubrible sin escribir ni mantener un servidor. Reemplaza el
  `FileNotFoundError` generico anterior (una promesa de docstring incumplida) por
  validacion real del descriptor remoto + un mensaje explicito con las
  alternativas que si funcionan. Un consumidor no-Python (R, JS/Observable, un
  cosechador gubernamental) puede descubrir y bajar datasets sin clonar el repo ni
  instalar la libreria.
- Negativas: `data.json` es un **prototipo**, no un artefacto verificado por
  `scripts/sync_docs.py` ni `verify_pipeline.py` todavia (ver follow-ups). Si
  `datos.gob.cl` efectivamente requiere DCAT-AP/RDF en vez de DCAT-US, el
  prototipo necesitaria un perfil adicional -- se prefirio no bloquear el spike
  por esa incertidumbre (ver Preguntas abiertas). `from_datapackage(url)` sigue
  sin devolver un `ChileHub` funcional para datos remotos -- solo valida y explica
  las alternativas (ver Preguntas abiertas #5).

## Preguntas abiertas

1. **¿`datos.gob.cl` cosecha DCAT-US (`data.json`) o requiere DCAT-AP (RDF/TTL)?**
   No se pudo confirmar. Si un futuro contacto con el equipo de datos.gob.cl
   confirma el perfil real, ajustar `dcat_catalog.py` o agregar un segundo
   generador para el perfil correcto.
2. **¿Se implementa pinning de URLs por version/release?** Hoy `downloadURL`
   siempre apunta a la build mas reciente (mutable). Un consumidor que necesite
   reproducibilidad exacta debe usar el bundle ZIP versionado de GitHub Releases,
   no `data.json`. Si hay demanda de un indice de versiones historicas, es un
   follow-up separado.
3. **¿Publicar `data.json` implica comprometerse a estabilidad de URLs de
   descarga?** Implicitamente si -- un cosechador externo que indexe estas URLs
   esperara que sigan resolviendo. Cualquier reestructuracion futura de
   `data/normalized/` deberia considerar este contrato implicito.
4. **¿Se promueve el prototipo a artefacto oficial?** Hoy `data.json` se genera en
   `build_dev_db.py::main()` junto a los demas artefactos pero no tiene gate de
   `check_companion_paths.py` ni verificacion en `verify_pipeline.py`. Promoverlo
   requeriria agregarlo a la tabla de propietarios canonicos de `AGENTS.md §12`.
5. **¿Se implementa soporte real de `data_dir` remoto en `ChileHub.__init__`?**
   Hoy `from_datapackage(url)` valida el descriptor pero levanta `ChileHubDataError`
   en vez de devolver un hub funcional, porque `__init__` asume un directorio
   local (`Path.open()`). Cerrarlo requiere decidir el modelo: ¿leer
   `dataset_catalog.json`/Parquet via `requests`/`fsspec` cuando `data_dir` es una
   URL? ¿Descargar a un cache temporal (reusando `ChileHubDataManager`)? Es un
   cambio de diseño mayor a `__init__`, fuera de alcance de este spike -- abrir un
   plan propio si hay demanda real de esta capacidad.

## Alternativas consideradas

- **DCAT-AP/RDF desde el inicio** -- Se descarto para este spike: requiere
  dependencias RDF (`rdflib` u similar) y un modelo de datos mas complejo (grafos,
  no JSON plano) para un beneficio no confirmado (no se pudo verificar que
  datos.gob.cl lo requiera especificamente). DCAT-US cubre el caso de uso de
  descubribilidad con muchisima menos superficie.
- **Servir un endpoint dinamico que genere el catalogo on-demand** -- Rechazado de
  plano: viola la linea roja del product-spec ("ninguna API que deba mantenerse en
  linea 24/7"). Todo se genera en build-time y se sirve como archivo estatico.
- **Reemplazar `datapackage.json` por `data.json` como unico descriptor** -- Se
  descarto: son formatos con audiencias distintas (Frictionless para
  reproducibilidad tecnica/schemas; DCAT para descubribilidad/harvesting
  gubernamental). Mantener ambos, derivando uno del otro, evita duplicar la fuente
  de verdad.
