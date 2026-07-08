# Registro de cambios

Este proyecto usa Conventional Commits y `python-semantic-release` para versionar
las publicaciones en PyPI. Los commits de actualización de datos
(`chore(data): daily refresh [skip ci]`) no representan lanzamientos de software
y se excluyen intencionalmente de estas notas.

Los bloques `> 🎯 **Resumen:**` que acompañan a algunos releases minor/major son
**notas narrativas escritas por un humano**: cuentan *por qué* el release importa
y cómo se conecta con la dirección del proyecto. Las listas categorizadas debajo
son la bitácora automática generada desde los Conventional Commits.

<!-- version list -->

## 1.19.8 - 2026-07-08

### Corregido

- **ci**: Force-add gitignored monthly scrape outputs; deprecate consumo_electrico_comunal
  ([`57e6eaf`](https://github.com/cortega26/chile-hub/commit/57e6eafb5492878f08395419e4d624d0aaaea314))


## 1.19.7 - 2026-07-08

### Corregido

- **ci**: Make monthly scrape commits tolerant
  ([`974b502`](https://github.com/cortega26/chile-hub/commit/974b502cb4f6975e168f6ba6adbcfe312a085ea2))

- **ci**: Quiet CodeQL Python legacy probe
  ([`f056684`](https://github.com/cortega26/chile-hub/commit/f0566844d5f02a5153f5385f20306849eb1fd31f))

- **ci**: Set CodeQL Python executable
  ([`0229cc3`](https://github.com/cortega26/chile-hub/commit/0229cc32d89662fed27ad1a0924d4ac122ff9f7a))

- **ci**: Stage monthly scrape outputs safely
  ([`f0f8096`](https://github.com/cortega26/chile-hub/commit/f0f80964b83f88fb0538bc4bb8faeb033b0c56ea))


## 1.19.6 - 2026-07-08

### Corregido

- **ci**: Pin CodeQL Python extraction version
  ([`e2f3710`](https://github.com/cortega26/chile-hub/commit/e2f3710676899ffe13ded10f335cf3d24a47b62b))

- **ci**: Redeploy Pages after bot-authored commits to main
  ([`fd23f12`](https://github.com/cortega26/chile-hub/commit/fd23f120ddbaa719771ff03612967aa25ec37780))


## 1.19.5 - 2026-07-08

### Corregido

- **ci**: Clarify readiness and quiet release logs
  ([`dc5a882`](https://github.com/cortega26/chile-hub/commit/dc5a88259eebcc433e09a8e957fa6369e3f6e884))


## 1.19.4 - 2026-07-08

### Corregido

- **ci**: Harden release artifact gates
  ([`4ebca99`](https://github.com/cortega26/chile-hub/commit/4ebca99768d2f99415f221a41fda226fcebfbfa0))


## 1.19.3 - 2026-07-07

### Corregido

- **api**: Agrega datasets faltantes al enum Dataset
  ([`88187f0`](https://github.com/cortega26/chile-hub/commit/88187f031f0ef856c1260d0d282a93efbd066af0))

### Mantenimiento

- **deps**: Sync uv lock after release bump
  ([`0a95440`](https://github.com/cortega26/chile-hub/commit/0a95440635c552c960a9115ea9d72482169d441a))


## 1.19.2 - 2026-07-07

### Corregido

- **extractors**: Preserva ceros CUT y usa isoformat en consumo/pobreza
  ([`3ad6ab9`](https://github.com/cortega26/chile-hub/commit/3ad6ab9a378bb8e42eec89bae745f1c525d05b83))

### Mantenimiento

- **deps**: Regenera uv.lock y añade guardia --locked en CI
  ([`a6b22b8`](https://github.com/cortega26/chile-hub/commit/a6b22b82cc0e1702b9a1b33138054204ad1e03ca))


## 1.19.1 - 2026-07-06

### Corregido

- **ci**: Sync codeql-action init/analyze versions and group future bumps
  ([#25](https://github.com/cortega26/chile-hub/pull/25),
  [`b80e728`](https://github.com/cortega26/chile-hub/commit/b80e728de6af506d10e700223533c3a5ff854834))

### Documentación

- **readme**: Sincroniza tabla y menciones de capas tras promover 2 datasets
  ([#26](https://github.com/cortega26/chile-hub/pull/26),
  [`c1419e9`](https://github.com/cortega26/chile-hub/commit/c1419e94951b199cb4da23eb7ba562ce77ca7d2d))


## 1.19.0 - 2026-07-06

### Mantenimiento

- **deps**: Bump astral-sh/setup-uv from 8.2.0 to 8.3.0
  ([#23](https://github.com/cortega26/chile-hub/pull/23),
  [`5671b54`](https://github.com/cortega26/chile-hub/commit/5671b545a8014f6d15bed9134dc06843319eae05))

- **deps-dev**: Bump the python-dev group with 2 updates
  ([#20](https://github.com/cortega26/chile-hub/pull/20),
  [`23ac012`](https://github.com/cortega26/chile-hub/commit/23ac0126273f56b0ac3723996bd34ee40e47c742))

### Documentación

- **site**: Publica referencia de API con MkDocs Material (Plan 021)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

### Agregado

- **data**: Autoridades_electas v1 — diputados con distrito vía Scrapling (Plan 023 Ola A)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Autoridades_electas — cargo senadores + cableado candidate (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Autoridades_locales — alcaldes (345 comunas, best-effort) vía API MediaWiki
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Autoridades_locales — gobernadores (Wikipedia CC-BY-SA, segregado) (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Extractor partidos_politicos desde Cámara + Plan 023
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Promueve partidos_politicos y autoridades_electas a stable_publishable
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **data**: Registra partidos_politicos en carril candidate (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

### Tests

- **coverage**: Mide todo el pipeline, no solo la librería (TC-02)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))


## 1.18.1 - 2026-07-01

### Corregido

- **ci**: Remove obsolete Node 24 forcing flag
  ([#19](https://github.com/cortega26/chile-hub/pull/19),
  [`4ae8957`](https://github.com/cortega26/chile-hub/commit/4ae8957f85ffbb8bddffabe065cdb20f967b3ff7))

### Mantenimiento

- Elimina plan 014 de plans/ (ya archivado)
  ([`2c39890`](https://github.com/cortega26/chile-hub/commit/2c39890d60648499c986f45a0173f6fc7952e56f))

### Documentación

- Actualiza docstring de source_adapter — estándar recomendado
  ([`ef118bc`](https://github.com/cortega26/chile-hub/commit/ef118bc6eb691cbf5d6f230f82db2105d72ac044))

- Actualiza README para 17 capas — badges, métricas, schemas y extractores
  ([`77e58ea`](https://github.com/cortega26/chile-hub/commit/77e58eaa2a3ccf4074be3d2b32de68d73c275bf0))

- Archiva Plan 014 como DONE
  ([`f51ac1d`](https://github.com/cortega26/chile-hub/commit/f51ac1d6137d608aa68fe7deec6c8021b13ebd23))

- Documenta BaseExtractor.run() como entry point programático
  ([`c7f3392`](https://github.com/cortega26/chile-hub/commit/c7f3392b4fb4a8cd3a64ad13e36e2a28d0d4326c))

- Tabla README — delincuencia_comunal como «próximamente» + leyenda
  ([`0aea153`](https://github.com/cortega26/chile-hub/commit/0aea153524b40d0bf9063c1a11ec6f72c96a1c7f))

### Refactorizado

- Remueve bloques try/except ModuleNotFoundError de subdere_extractor
  ([`97dec70`](https://github.com/cortega26/chile-hub/commit/97dec7098bf945e6e6986cd09deacc6dfe4371bf))

- Simplifica entrada comunas_enriquecidas en metadata.py como alias
  ([`c48ff0e`](https://github.com/cortega26/chile-hub/commit/c48ff0e91f321155b2069e2cc78c1086efe56e65))


## 1.18.0 - 2026-06-30

### Corregido

- CI readiness — fallback para pobreza_comunal y consumo_electrico_comunal + archivar Plan 022
  ([`b0ba125`](https://github.com/cortega26/chile-hub/commit/b0ba12579aef7c56980bdcd7b23dc12a85f72e24))

- Landing — añade pobreza_comunal y consumo_electrico_comunal a categorías CATEGORIES
  ([`63244a5`](https://github.com/cortega26/chile-hub/commit/63244a54ba8d2bce1e0287bb3a5327e7b86fa41b))

### Agregado

- Fase 1 — honestidad de datos y base de confianza (plan 022)
  ([`1d97b49`](https://github.com/cortega26/chile-hub/commit/1d97b49daf2d722ee901d7e1d643f5b55519d5a6))

- Fase 2 — narrativa técnica visible y Ola B1 — CASEN + CNE (plan 022)
  ([`7e7d63b`](https://github.com/cortega26/chile-hub/commit/7e7d63b7acdab646b55e6337d475a26499ba227e))

- Fase 3 — señales pasivas operativas y sanación de fuentes vía scraping (plan 022)
  ([`ca698ea`](https://github.com/cortega26/chile-hub/commit/ca698ea19001b117703d60b62afa669e37b9ccc9))

- Fase 4 — distribución sobre lo validado + Ola B2 — CEAD delincuencia + electoral research (plan
  022)
  ([`8e3e579`](https://github.com/cortega26/chile-hub/commit/8e3e579bdb26cc888c637b95f5f257dc352965d4))


## 1.17.1 - 2026-06-30

### Corregido

- **badge**: Use shields.io URL and move to last position
  ([`46604ca`](https://github.com/cortega26/chile-hub/commit/46604ca028991630d7d497d669d358247b049638))

### Mantenimiento

- **deps**: Bump actions/cache from 5.0.5 to 6.1.0
  ([#16](https://github.com/cortega26/chile-hub/pull/16),
  [`d61298b`](https://github.com/cortega26/chile-hub/commit/d61298becc001f500b329c0dec92967dd76545f2))

- **deps**: Bump actions/setup-python from 6.2.0 to 6.3.0
  ([#17](https://github.com/cortega26/chile-hub/pull/17),
  [`491847f`](https://github.com/cortega26/chile-hub/commit/491847fed3cb2a5f08340abb1d1ef4430ec1f425))

- **deps-dev**: Bump the python-dev group with 2 updates
  ([#15](https://github.com/cortega26/chile-hub/pull/15),
  [`56a3843`](https://github.com/cortega26/chile-hub/commit/56a3843e4cce9480e8ae9c5d5df936419625d636))


## 1.17.0 - 2026-06-30

> 🎯 **Resumen:** Este release cierra el backlog estratégico de ingeniería y posiciona
> a chile-hub como parte del ecosistema Tooltician. Se completan tres frentes diferidos
> desde la auditoría inicial: contratos de tipos en runtime (`contracts.py`), el enum
> `Dataset` que unifica la referencia a capas, y el dashboard de salud programático
> (`hub_health.json`). La librería ahora valida tipos al importar y expone un panel de
> salud consultable sin abrir un Parquet. La identidad visual se alinea con Tooltician
> (badge + tagline en español), cerrando la brecha entre la ingeniería real y su cara
> pública. Este release es la base técnica sobre la que se construye la narrativa de
> confiabilidad del Plan 022.

### Documentación

- **badge**: Badge Tooltician -> Parte de Tooltician
  ([`74c0064`](https://github.com/cortega26/chile-hub/commit/74c00645f3e94e69e5f1802943d21e8c6582be33))

- **readme**: Añadir badge y tagline de Tooltician ecosystem
  ([`39bda6a`](https://github.com/cortega26/chile-hub/commit/39bda6a395cbbbbde323bf32da9d716d0e21dff7))

- **readme**: Badge y tagline Tooltician en español
  ([`0d8c179`](https://github.com/cortega26/chile-hub/commit/0d8c179770231ac433870f2370564327f70d0cb0))

### Agregado

- **backlog**: Completar #2 #3 #5 — contratos runtime, enum Dataset, dashboard salud
  ([`a3ef978`](https://github.com/cortega26/chile-hub/commit/a3ef9782fb3c4dbf557d63d7fda226c15c42ac2a))


## 1.16.0 - 2026-06-29

> 🎯 **Resumen:** Release de madurez de UX y estándares. La CLI migra de padding manual
> a tablas formateadas con `rich` (Plan 018): `chile-hub info`, `list datasets` y
> `show` ahora renderizan tablas con bordes, colores y columnas auto-ajustadas. El
> pipeline publica `datapackage.json` en formato Frictionless Data (Plan 019), derivado
> automáticamente de los contratos `contracts/datasets/*.json`, dando interoperabilidad
> estándar sin mantenimiento adicional. Se institucionaliza la disciplina de archivado de
> planes: los planes DONE se mueven a `archive/` de inmediato. La experiencia de uso
> y la apertura de datos dan un salto sin tocar la lógica de negocio.

### Mantenimiento

- **deps-dev**: Bump duckdb ([#10](https://github.com/cortega26/chile-hub/pull/10),
  [`140c8ea`](https://github.com/cortega26/chile-hub/commit/140c8ea034c9068aabb9b108760c45e1fda08543))

- **deps-dev**: Bump the python-dev group with 3 updates
  ([#11](https://github.com/cortega26/chile-hub/pull/11),
  [`cd2e046`](https://github.com/cortega26/chile-hub/commit/cd2e0463af5e99dfcbc8eff0c70a188dcd0d1775))

- **plans**: Archivar planes DONE y añadir instrucción de archivado automático
  ([`faf90c2`](https://github.com/cortega26/chile-hub/commit/faf90c2eb3859d5828d29125347babca9503df35))

### Agregado

- **pipeline**: Publicar datapackage.json (Frictionless) derivado de contratos
  ([`0d1fcc8`](https://github.com/cortega26/chile-hub/commit/0d1fcc80959d3dff06135f7ae8c73a11b21ea21c))

### Refactorizado

- **cli**: Renderizar tablas con rich en vez de padding manual
  ([`85ef69f`](https://github.com/cortega26/chile-hub/commit/85ef69f61c341974de3e4f3f43c4eded24080963))


## 1.15.1 - 2026-06-24

### Corregido

- **build**: Mover ajuste de sys.path antes de importaciones de src.* en build_dev_db.py
  ([`643f89c`](https://github.com/cortega26/chile-hub/commit/643f89c8d289c87cff6f842be7f7fcfa3a8cffa0))

### Mantenimiento

- **deps**: Bump actions/checkout from 6.0.3 to 7.0.0
  ([#12](https://github.com/cortega26/chile-hub/pull/12),
  [`581748f`](https://github.com/cortega26/chile-hub/commit/581748f34b2c20c6bb4dfe209571f2f02748085b))

- **deps**: Bump astral-sh/setup-uv from 8.1.0 to 8.2.0
  ([#13](https://github.com/cortega26/chile-hub/pull/13),
  [`79edd13`](https://github.com/cortega26/chile-hub/commit/79edd1351a6208bf245cddb513d4b0b929342bca))

- **deps**: Bump codecov/codecov-action from 5 to 7
  ([#14](https://github.com/cortega26/chile-hub/pull/14),
  [`3494e86`](https://github.com/cortega26/chile-hub/commit/3494e865489a578892f58edae52848ce5b84a237))

### Documentación

- **changelog**: Actualizar registro de cambios y configurar generación automática en español
  ([`c0796f4`](https://github.com/cortega26/chile-hub/commit/c0796f48fe4c17e25395578a724f3451c5ab6991))

- **datasets**: Evaluar candidatos y agregar estado under-review
  ([`a0978a3`](https://github.com/cortega26/chile-hub/commit/a0978a38cf2889b19b65b88b610edf443d7ecfe4))


---

## 1.15.0 - 2026-06-21

> 🎯 **Resumen:** Release de robustez de ingeniería. Todos los extractores HTTP ahora
> reintentan automáticamente con backoff exponencial (vía `tenacity`): los fallos
> transitorios de red —frecuentes en CI y en portales gubernamentales— ya no rompen
> el build. La gestión de dependencias migra a `uv` en todos los flujos de CI,
> dando resolución determinista y reduciendo el tiempo de instalación significativamente.
> Estas dos mejoras eliminan las dos fuentes más comunes de falsos negativos en el
> pipeline diario, haciendo que "CI roja = problema real" por primera vez.

### Agregado

- Reintentos HTTP con backoff exponencial (vía `tenacity`) en todos los extractores:
  los fallos transitorios de red se reintentan automáticamente hasta 3 veces con espera
  creciente entre intentos, eliminando errores espúreos de CI por cortes momentáneos.

### Cambiado

- Gestión de dependencias migrada a `uv` en todos los flujos de CI, reduciendo
  significativamente el tiempo de instalación y garantizando resolución determinista
  de versiones.

---

## 1.14.1 - 2026-06-21

### Corregido

- Uso de `shutil.which()` para resolver la ruta del binario `unrar` desde el `PATH`
  del sistema en la verificación de integridad, evitando fallos cuando el binario
  existe pero no está en la ubicación por defecto.

---

## 1.14.0 - 2026-06-20

### Agregado

- Integración de `rutificador` en `validate_empresas()` para verificar matemáticamente
  el dígito verificador de cada RUT en el dataset de empresas, detectando valores
  corruptos o generados incorrectamente.

### Interno

- Cobertura de pruebas incrementada de 88.1 % a 90.4 % sobre el código de librería.

---

## 1.13.1 - 2026-06-20

### Cambiado

- `build_dev_db.py` descompuesto en el paquete `src/builders/` con módulos
  especializados (`_shared`, `io_utils`, `formats`, `metadata`, `reports`,
  `artifacts`, `datasets`, `catalog`, `landing`). El orquestador delega en estos
  módulos, reduciendo su tamaño y complejidad de forma significativa.

### Interno

- Incorporadas herramientas de calidad al entorno de desarrollo: `mypy` (tipado
  estático), `pip-audit` (auditoría de dependencias), `interrogate` (cobertura de
  docstrings), `bandit` (escaneo de seguridad estático), `pytest-xdist` (tests en
  paralelo), `hypothesis` (property-based testing) y `structlog` (logging
  estructurado del pipeline).
- Corregida compatibilidad de `pytest-xdist` en CI removiendo `-n auto` de
  `addopts`.
- Reparadas insignias de Coverage y Data Freshness en el README.

---

## 1.13.0 - 2026-06-20

### Cambiado

- Rediseño de la landing page con cajón lateral deslizante (_slide-over drawer_)
  para mostrar detalles de cada dataset, reemplazando el panel anterior. La
  navegación es ahora más fluida y funciona correctamente en dispositivos móviles.

---

## 1.12.0 - 2026-06-20

### Agregado

- Extractor live para **SIEDU** (Sistema de Indicadores y Estándares de Desarrollo
  Urbano del MINVU): descarga directa desde la API oficial, eliminando la
  dependencia de snapshots locales.
- Extractor live para **MINEDUC Resultados Educacionales**: obtención en vivo desde
  la fuente oficial del Ministerio de Educación.
- Ambos datasets pasan de modo `fallback` a modo `live`, cerrando los Issues #6 y #7.

---

## 1.11.1 - 2026-06-19

### Corregido

- Corregida metadata `source_mode` engañosa en varios extractores; URLs alineadas
  con los endpoints reales de cada fuente.
- Dataset SINIM degradado a carril `candidate` al confirmarse que su fuente requiere
  revisión de redistribución.

---

## 1.11.0 - 2026-06-19

### Agregado

- `ChileHub.cross_view()`: cruza dos datasets por código CUT en una sola llamada.
- `ChileHub.validate_user_data()`: valida un DataFrame externo contra el esquema
  de un dataset del hub.
- `ChileHub.search_datasets()`: búsqueda de datasets por palabras clave.
- Flag `--exit-code` en la CLI para integración programática con scripts de CI y
  orquestación.

### Cambiado

- Catálogo extraído como archivo externo `dataset_catalog_config.json`;
  `build_dev_db.py` ya no lo embebe como código fuente, simplificando el
  orquestador y corrigiendo `PYTHONPATH` en entornos de desarrollo.

### Corregido

- Eliminada ventana TOCTOU en la descarga del bundle: el hash SHA-256 se calcula
  en tránsito, no sobre el archivo ya escrito en disco.
- Verificación de integridad del binario `unrar` antes de invocarlo, evitando la
  ejecución de binarios no confiables.
- Mensajes de error en `build_dev_db.py` usan rutas relativas para no filtrar
  rutas absolutas del sistema de archivos del servidor.
- `_load_catalog` envuelve la carga con `try/except` para propagar
  `ChileHubDataError` en lugar de excepciones genéricas.
- `DataManager.clear()` valida la ruta antes de borrar para prevenir eliminaciones
  fuera del directorio de caché.
- Los datasets alias ya no sobrescriben los artefactos del dataset canónico en
  `artifact_manifest`.
- `dataset_catalog_config.json` rastreado en git para evitar `FileNotFoundError`
  en CI.

---

## 1.10.0 - 2026-06-19

### Mejorado

- Caché en memoria para cargas de artefactos en la API pública: llamadas repetidas a
  `load_polars()`, `load_duckdb()` y métodos relacionados retornan desde caché sin
  releer disco.
- Caché de datos de staging en los flujos diarios de CI para reducir tiempos de
  ejecución en corridas sin cambios de código.

### Corregido

- Cierre correcto de respuestas HTTP mediante context manager en todos los extractores.
- Tipado estricto de excepciones: `except Exception` reemplazado por tipos
  específicos en extractores para evitar captura silenciosa de errores inesperados.
- Añadida llamada `drop_nulls()` en `validate_censo_hogares_viviendas()` para
  evitar errores al procesar filas con celdas vacías.
- Corregido `TypeError` por celdas `None` en el extractor de `censo_hogares_viviendas`.
- Libros Excel abiertos con context manager en `openpyxl` para garantizar cierre
  del recurso.

---

## 1.9.0 - 2026-06-19

### Agregado

- Insignia dinámica de frescura de datos en el README que refleja la antigüedad del
  último pipeline de extracción exitoso.

---

## 1.8.0 - 2026-06-19

### Interno

- Cobertura de pruebas alcanza el 89 % sobre el código de librería central
  (`src/chile_hub`), con nuevas suites que cubren casos límite de `core.py`,
  tablas de reportes y funciones puras de utilidades.

---

## 1.7.0 - 2026-06-19

### Agregado

- Implementación de mejoras prioritarias de la auditoría de calidad: context managers
  en todos los recursos externos, tipado estricto de excepciones y eliminación de
  condiciones de carrera en operaciones de archivo.
- Backlog de mejoras estratégicas con roadmap priorizado documentado en
  `docs/backlog/`.

### Interno

- Token Codecov configurado en CI y umbrales de cobertura ajustados al nivel real
  alcanzado por la suite de pruebas.

---

## 1.6.0 - 2026-06-19

### Agregado

- Nuevo comando CLI `chile-hub export`: exporta un dataset a un archivo en el
  formato especificado (CSV, JSON, Parquet, Excel).
- Nuevo comando CLI `chile-hub check-sources`: verifica el estado de accesibilidad
  de las fuentes upstream en vivo.
- Rangos de versiones de dependencias flexibilizados en `pyproject.toml` para
  mejorar la compatibilidad de instalación en distintos entornos.

---

## 1.5.0 - 2026-06-18

### Agregado

- Suite de pruebas de integración ampliada: cobertura de `pipeline_status_utils`,
  valores límite de `core.py`, ocho extractores parcialmente cubiertos, todos los
  validadores restantes, puntos de entrada de la CLI y `source_adapter.py`.
- Carga del diagrama del pipeline en orientación vertical en la documentación.

### Cambiado

- Integración formal del Plan 009: la separación de pistas publicables y candidatas
  ahora opera como política explícita en el motor del pipeline (no solo en el
  registro de fuentes).

### Interno

- Corregida instalación del paquete `chile_hub` en el job de CI.
- `codecov-action` anclado al tag estable `v5` en lugar de un SHA de commit.

---

## 1.4.0 - 2026-06-18

### Agregado

- Separación de carriles (`publication_track`) en el registro de fuentes: 11 datasets como `stable_publishable` y 4 como `candidate`.
- Restricción del empaquetado público: los datasets marcados como candidatas son excluidos del manifest oficial, del bundle ZIP público y del indexado general de descargas.
- Estructuración en `hub_bundle.json` para diferenciar claramente entre datasets públicos listos y datasets candidatos.

### Cambiado

- Refactorización de `verify_pipeline.py` para aplicar políticas de publicación inteligentes dependientes del carril asignado.

## 1.3.1 - 2026-06-18

### Agregado

- Creación de `source_adapter.py` para abstraer y unificar el comportamiento de los extractores de datasets candidatos.
- Enlaces de soporte y contacto del proyecto en la landing page y documentación.

### Corregido

- Corrección en la suite de pruebas eliminando la dependencia directa en snapshots `raw` locales.
- Aseguramiento de `pyarrow` como dependencia explícita requerida para la exportación y registro de Polars con DuckDB.

## 1.3.0 - 2026-06-18

### Agregado

- Registro unificado de fuentes (`data/source_registry.json`) con metadatos sobre madurez, políticas de fallback, cronograma de revisión y umbral de estancamiento.
- Contratos de esquema en formato JSON Schema (`contracts/datasets/*.schema.json`) para los 15 datasets activos.
- Generación de reportes automáticos de preparación (`source_readiness`) y calidad (`dataset_quality`) en formato JSON/Markdown con sus respectivas integraciones en API y CLI.
- Sistema de detección de estancamiento de datos (`verify_readiness`) según reglas diferenciadas por tipo de capa.
- Política de compatibilidad de datasets (`docs/dataset-compatibility-policy.md`) con cálculo automático de severidad de cambios de esquema (major/minor/patch/none).

### Cambiado

- Estandarización de toda la documentación y comentarios del código a español neutro.

## 1.2.2 - 2026-06-17

### Cambiado

- Sincronización dinámica de la insignia de versión en el navbar de la landing page, leyéndola directamente de `hub_bundle.json` en lugar de estar hardcodeada.

## 1.2.1 - 2026-06-17

### Cambiado

- Migración del despliegue de GitHub Pages al flujo moderno basado en GitHub Actions workflow.

### Corregido

- Control de clicks en las pestañas de curl para evitar errores interactivos en datasets que no generan salida JSON.

## 1.2.0 - 2026-06-17

### Agregado

- Agregada nueva superficie de dataset público: `empresas` (Registro de Empresas y
  Sociedades del Ministerio de Economía, ~1.57M registros con RUT, razón
  social, tipo societario y comuna tributaria).
- Agregado `res_extractor.py` con obtención en vivo desde datos.gob.cl, snapshot
  crudo, staging CSV y generación de metadatos.
- Agregada `validate_empresas()` en `src/validation.py` con verificaciones de
  integridad referencial contra el DPA.
- Agregada lógica de división automática en `build_excel()` para datasets que
  exceden el límite de 1,048,576 filas de Excel (`empresas` se divide en múltiples
  hojas numeradas automáticamente).
- Agregado `docs/datasets/empresas.md` con esquema, fuente, licencia y ejemplos
  de uso completos.

### Cambiado

- Catálogo activo expandido de 14 a 15 datasets.
- Gestión de versión centralizada: `pyproject.toml` es la fuente única de
  verdad; `__init__.py` la lee dinámicamente.
- Optimizado `build_dev_db.py`: conversión única `.to_pandas()` (antes 2×),
  inserciones SQLite multi-fila, omisión de JSON para tablas >100K filas,
  salida de progreso.
- Actualizados README, SOURCE_OF_TRUTH.md, AGENTS.md y CHANGELOG para reflejar
  el catálogo actual de 15 capas, la estructura del paquete y el conteo de líneas.

### Eliminado

- `puntos_interes` (POIs de OpenStreetMap) — extractor, configuración, tests, CI y
  documentación. La API de Overpass resultó demasiado inestable para CI; se
  reconsiderará cuando haya una fuente oficial chilena de POIs disponible.
  `validate_puntos_interes()` se conserva en `src/validation.py` para
  reutilización futura.

### Notas

- `empresas` se extrae en vivo desde datos.gob.cl (CC-BY 3.0 CL); la salida
  Excel se divide en múltiples hojas para mantenerse dentro del límite de filas de Excel.

## 1.1.0 - 2026-06-17

### Agregado

- Agregadas cuatro nuevas superficies de dataset público: `finanzas_municipales`,
  `resultados_educacionales`, `indicadores_urbanos_siedu` y el derivado
  `perfil_territorial_comunal`.
- Agregadas integración de extractor, metadatos de staging, validación centralizada,
  Parquet/JSON normalizado, DuckDB, SQLite, Excel, catálogo, procedencia,
  redistribución, health, bundle, CI y documentación para las nuevas capas.
- Agregados artefactos operativos legibles por máquina `dataset_status.json` y
  `dataset_changelog.json`.
- Agregados `ChileHub.dataset_status()`, `ChileHub.dataset_changelog()` y los
  comandos CLI correspondientes `chile-hub dataset-status` y `chile-hub dataset-changelog`.

### Cambiado

- Catálogo activo expandido de 10 a 14 datasets.
- Actualizadas las pruebas de humo del landing page y las expectativas de
  incidencias principales para que las capas de respaldo puedan convertirse en
  la prioridad operativa correctamente identificada.

### Notas

- `finanzas_municipales`, `resultados_educacionales` e
  `indicadores_urbanos_siedu` actualmente se construyen en modo `fallback` hasta
  que se configuren exportaciones directas estables. `make verify` pasa;
  se espera que `make verify-live` rechace esas capas hasta que se complete la
  extracción en vivo.

## 1.0.1 - 2026-06-17

### Agregado

- Agregado `pytest-cov` a la cadena de herramientas de desarrollo, con soporte
  local de `make coverage` y reportes de cobertura en CI para el paquete `src/`.
- Actualizadas las dependencias de desarrollo y publicación a sus últimas
  versiones estables compatibles, incluyendo `build`, `pre-commit`, `pytest-cov`
  y `python-semantic-release`.

### Corregido

- Restaurada la compatibilidad con Python 3.10 reemplazando el uso de
  `datetime.UTC` (solo Python 3.11) con `datetime.timezone.utc`.
- Corregido el flujo de publicación en PyPI para que `python-semantic-release`
  omita su paso de compilación interna y el entorno del job use la compilación
  del paquete.
