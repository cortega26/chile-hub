# Registro de cambios

Este proyecto usa Conventional Commits y `python-semantic-release` para versionar
las publicaciones en PyPI. Los commits de actualización de datos
(`chore(data): daily refresh [skip ci]`) no representan releases de software
y se excluyen intencionalmente de estas notas.

Los bloques `> 🎯 **Resumen:**` que acompañan a algunos releases minor/major son
**notas narrativas escritas por un humano**: cuentan *por qué* el release importa
y cómo se conecta con la dirección del proyecto. Las listas categorizadas debajo
son la bitácora automática generada desde los Conventional Commits.

<!-- version list -->

## 1.21.1 - 2026-07-10

### Corregido

- Amplía cobertura del hook sync-docs a builders, catalog y contratos
  ([`3959c79`](https://github.com/cortega26/chile-hub/commit/3959c79f697e2e8bbddccb4c1f03853402dc56b5))

- **metadata**: Actualiza fuente y licencia de autoridades_locales a BCN SIIT
  ([`0064191`](https://github.com/cortega26/chile-hub/commit/00641916d81c3b5497e04e8276d28443ce114b17))

### Documentación

- Actualiza referencias a autoridades_locales en AGENTS.md y docs/
  ([`425e943`](https://github.com/cortega26/chile-hub/commit/425e94338fa19994e62e22e5eb67031b993a23e3))

- Completa actualización de referencias a BCN SIIT en autoridades_locales
  ([`bd42251`](https://github.com/cortega26/chile-hub/commit/bd42251073dd9db0112de758c687e6537ed5db8d))


## 1.21.0 - 2026-07-10

### Corregido

- Agrega --skip-build a make release
  ([`ba96fa4`](https://github.com/cortega26/chile-hub/commit/ba96fa4c2ab9e5fdf6c0211affc5893ef3bda5da))

- Usa --no-verify en bump-version y release
  ([`ba01e5c`](https://github.com/cortega26/chile-hub/commit/ba01e5c20456e03183483ada70655e5b775121fd))

### Integración continua

- Añade cache-suffix por job para evitar colisiones de caché de setup-uv
  ([`055a780`](https://github.com/cortega26/chile-hub/commit/055a7808e212d72caabd42443420f91625e2eca8))

### Documentación

- Sincroniza README.md con versión actual (1.20.0)
  ([`65f349f`](https://github.com/cortega26/chile-hub/commit/65f349f5f5389231387787eff945dd5dceeebd81))

### Agregado

- Agrega make bump-version y hook pre-commit sync-docs auto-stage
  ([`5c9261c`](https://github.com/cortega26/chile-hub/commit/5c9261ccc263388fe898b6f534b87495239c44cc))

- Bump-version auto-commitea y agrega make release
  ([`4be3b86`](https://github.com/cortega26/chile-hub/commit/4be3b8695f6bcd71d8a4843340b01cee57790b06))


## 1.20.0 - 2026-07-10

### Corregido

- **core**: Reemplaza type: ignore por cast explícito para compatibilidad mypy
  ([`7b072a8`](https://github.com/cortega26/chile-hub/commit/7b072a83e814cba4ffdc64c2cabc17f1d70a3d94))

- **data**: Agrega headers de navegador para BCN SIIT (resuelve HTTP 403)
  ([`eea47a2`](https://github.com/cortega26/chile-hub/commit/eea47a2e135687fe7fbcb4d37db7dddc9d5ea24d))

### Agregado

- **core**: Add ChileHub.sql() query surface over Parquet via DuckDB views
  ([`b0ee156`](https://github.com/cortega26/chile-hub/commit/b0ee156b3e56f83ebd937fa1f32b840bbe0e9af3))

- **core**: Add from_datapackage() and frictionless_validate() via Frictionless
  ([`ce23ee5`](https://github.com/cortega26/chile-hub/commit/ce23ee54c962698f6bc8f696d4c9511c84960672))

- **data**: Reemplaza fuente de alcaldes con BCN SIIT (100% cobertura, 346/346)
  ([`27ba534`](https://github.com/cortega26/chile-hub/commit/27ba534a971528bcbf1af5597f2cc76befab1b37))


## 1.19.16 - 2026-07-10

### Mantenimiento

- **deps**: Mueve deps solo-pipeline fuera de runtime del paquete
  ([`8032069`](https://github.com/cortega26/chile-hub/commit/8032069786fc8bf85092f1f0800f302ebd9631d3))

- **deps**: Mueve deps solo-pipeline fuera de runtime del paquete
  ([`660cc9f`](https://github.com/cortega26/chile-hub/commit/660cc9f0527b862e3d8ac4325cf17517584f44b7))

- **plans**: Archiva planes 032 y 033 (DONE) — deps runtime e higiene CI
  ([`2fc121d`](https://github.com/cortega26/chile-hub/commit/2fc121d46fcd8673f4e9cced75dafc0d63f0e437))

- **plans**: Archiva planes 032 y 033 (DONE) — deps runtime e higiene CI
  ([`8cebcd8`](https://github.com/cortega26/chile-hub/commit/8cebcd849bf7fd244ba3f01614ce2bc4244236fe))

- **plans**: Elimina archivo original del Plan 039 (ya movido a archive/)
  ([`a8ff660`](https://github.com/cortega26/chile-hub/commit/a8ff6608d3676e388cb4d4c4701ac110e0da8000))

### Integración continua

- **quality**: Ejecuta mypy/bandit/pip-audit/interrogate en CI
  ([`06d78ba`](https://github.com/cortega26/chile-hub/commit/06d78bab295a43b2e7b0cfc52cd996aa56b1b2e7))

- **quality**: Ejecuta mypy/bandit/pip-audit/interrogate en CI
  ([`84cffe3`](https://github.com/cortega26/chile-hub/commit/84cffe3d43ca4dc1e358da6d679bfa2808401212))

### Documentación

- **adr**: Document comunal coverage decisions (ADR-006)
  ([`3d27596`](https://github.com/cortega26/chile-hub/commit/3d27596482782581291c294af4660dd057410c25))

### Mejorado

- **validation**: Vectoriza DV de RUT y elimina dependencia rutificador
  ([`6062f45`](https://github.com/cortega26/chile-hub/commit/6062f45db29a659a7ac3e66102f7f421682a67d2))

### Refactorizado

- Deduplica pipeline_status_utils via re-export shim
  ([`77931b2`](https://github.com/cortega26/chile-hub/commit/77931b2ee16b39f3d59d6e1220b8389362428480))

### Tests

- **builders**: Golden round-trip para writers de formatos y bundle
  ([`4310cf6`](https://github.com/cortega26/chile-hub/commit/4310cf6bc130d8fb3d6dae9c1d0789187f47fe65))

- **verify**: Caracteriza el gate de publicación y lo hace visible a coverage
  ([`8488302`](https://github.com/cortega26/chile-hub/commit/84883025d46f573aa0f808095b1a3133604a5a4e))


## 1.19.15 - 2026-07-09

### Corregido

- **api**: Restaura docstrings de load_polars/validate_* (orden de sentencias)
  ([`1d7a963`](https://github.com/cortega26/chile-hub/commit/1d7a9636800daf02ab86a965c97a47c42e057cd5))

### Mantenimiento

- **plans**: Actualiza índice — Ola 1 (027-031) completa
  ([`09869ee`](https://github.com/cortega26/chile-hub/commit/09869eedfdd3f56904356446cb7be82f08b82fec))

- **plans**: Archiva plan 028 (DONE) — elimina verificación unrar no-op
  ([`e33cd3b`](https://github.com/cortega26/chile-hub/commit/e33cd3bc4b843b84dad3df321f3d7158a0f688eb))

- **plans**: Archiva plan 029 (DONE) — docstrings restaurados en core.py
  ([`42bf34a`](https://github.com/cortega26/chile-hub/commit/42bf34aa1864d5d56627afbaffa5d8c133f6a632))

- **plans**: Archiva plan 030 (DONE) — guardia Excel + dedup SHA bundle
  ([`6949f65`](https://github.com/cortega26/chile-hub/commit/6949f6581e8cefff4d6ec3432934db4625eee406))

- **plans**: Archiva plan 031 (DONE) — cache de load_polars en ruta por defecto
  ([`4df4947`](https://github.com/cortega26/chile-hub/commit/4df494795d81fec4bc1f87a5241cb1fe039ee312))

### Documentación

- Update README release metadata
  ([`e5947da`](https://github.com/cortega26/chile-hub/commit/e5947da71f55c2f54685c04181d36484d12dd0f9))

### Mejorado

- **api**: Cachea Parquet en load_polars también en la ruta por defecto
  ([`7b1f065`](https://github.com/cortega26/chile-hub/commit/7b1f065f24ab78eed67e018e68f4d98812470cc9))

- **build**: Omite Excel para tablas masivas y evita doble hash del bundle
  ([`a6aa9ef`](https://github.com/cortega26/chile-hub/commit/a6aa9ef5247f206d9f758e1f0f19e3f0f387e274))


## 1.19.14 - 2026-07-09

### Corregido

- **extractors**: Etiqueta provenance real en scrape SINIM exitoso
  ([`a478f50`](https://github.com/cortega26/chile-hub/commit/a478f50c78f566d244b28c4d210851c3028b9aac))

- **extractors**: Etiqueta provenance real en scrape SINIM exitoso.
  ([`4690fec`](https://github.com/cortega26/chile-hub/commit/4690fec06e443f4828acabd8853dc8635ae54195))

### Mantenimiento

- **plans**: Archiva plan 027 (DONE) — provenance real en scrape SINIM
  ([`a478f50`](https://github.com/cortega26/chile-hub/commit/a478f50c78f566d244b28c4d210851c3028b9aac))

### Documentación

- Update pinned version example
  ([`f269868`](https://github.com/cortega26/chile-hub/commit/f269868be7e2f69c753c57d5ac3689693e9abb50))


## 1.19.13 - 2026-07-08

### Corregido

- **docs**: Avoid duplicate reference slug
  ([`7ef9df7`](https://github.com/cortega26/chile-hub/commit/7ef9df7f7da7feb3e632792ea3bd8127dbf2e376))

### Mantenimiento

- Centralize hardcoded README facts (DRY single-source sync)
  ([#28](https://github.com/cortega26/chile-hub/pull/28),
  [`378eba0`](https://github.com/cortega26/chile-hub/commit/378eba061a707f96f60bbba4952c8b9da6ec7df1))

- Centralize hardcoded README facts into a single-source sync mechanism
  ([#28](https://github.com/cortega26/chile-hub/pull/28),
  [`378eba0`](https://github.com/cortega26/chile-hub/commit/378eba061a707f96f60bbba4952c8b9da6ec7df1))

### Documentación

- Hide unnecessary mkdocs sidebar scrollbars
  ([`12e23b9`](https://github.com/cortega26/chile-hub/commit/12e23b97ab4a5c60a087156868031ab658a82c3f))

- Improve documentation discoverability
  ([`b9acaf7`](https://github.com/cortega26/chile-hub/commit/b9acaf70a4fd135c57361ef457d062fbd4bb5533))

- Normalize changelog language and refresh docs
  ([`db6c3af`](https://github.com/cortega26/chile-hub/commit/db6c3af183cb4179ed2d4f220755a177e72b48e5))

- Suppress mkdocs sidebar scrollbars broadly
  ([`0090fc3`](https://github.com/cortega26/chile-hub/commit/0090fc34c6629d5a7193af9a6b793acb382989db))

- Sync README test count
  ([`3bad640`](https://github.com/cortega26/chile-hub/commit/3bad640170a8a6fd45d5da91e2d941c648950acd))


## 1.19.12 - 2026-07-08

### Corregido

- Keep landing data version in sync
  ([`df0999e`](https://github.com/cortega26/chile-hub/commit/df0999e1a53c1e9d03ea9eb39bdc921a37e9dcab))

### Documentación

- Harden AGENTS.md with test policy + doc/test anti-drift gate
  ([#27](https://github.com/cortega26/chile-hub/pull/27),
  [`32d7e35`](https://github.com/cortega26/chile-hub/commit/32d7e35bfe8871ea343d9fbc08e5843129a21c8a))

### Tests

- Regression coverage for the Pipeline Check #270 fix chain + recent gaps
  ([`354ad6e`](https://github.com/cortega26/chile-hub/commit/354ad6e1ed3a1290c6281b8dfda327f4017f4f39))


## 1.19.11 - 2026-07-08

### Corregido

- **datos**: Corrige el mapeo de columnas XLSX de pobreza_comunal y sincroniza las pruebas con el registro
  ([`3f968ab`](https://github.com/cortega26/chile-hub/commit/3f968ab2a4765a7761d16d689199ccbce6aa9f5c))

- **despliegue**: Mantiene el enlace top_issue en el bundle público solo durante el build
  ([`9b85a23`](https://github.com/cortega26/chile-hub/commit/9b85a2309d55d54b044537fefbaa5fe6a11369a5))


## 1.19.10 - 2026-07-08

### Corregido

- **ci**: Evita que el job diario sobrescriba el snapshot mensual de SINIM
  ([`5ba983e`](https://github.com/cortega26/chile-hub/commit/5ba983e9b31ab7e32efa39348618f70ad052ba7f))


## 1.19.9 - 2026-07-08

### Corregido

- **ci**: Resincroniza el JSON-LD de index.html con source_registry (Pipeline Check #270)
  ([`fcc7f6f`](https://github.com/cortega26/chile-hub/commit/fcc7f6f11b809dfe299fd597a60afdb3d2f5c4ee))


## 1.19.8 - 2026-07-08

### Corregido

- **ci**: Fuerza la inclusión de salidas mensuales de scraping ignoradas por git y depreca consumo_electrico_comunal
  ([`57e6eaf`](https://github.com/cortega26/chile-hub/commit/57e6eafb5492878f08395419e4d624d0aaaea314))


## 1.19.7 - 2026-07-08

### Corregido

- **ci**: Hace tolerantes los commits del scraping mensual
  ([`974b502`](https://github.com/cortega26/chile-hub/commit/974b502cb4f6975e168f6ba6adbcfe312a085ea2))

- **ci**: Silencia la sonda heredada de Python en CodeQL
  ([`f056684`](https://github.com/cortega26/chile-hub/commit/f0566844d5f02a5153f5385f20306849eb1fd31f))

- **ci**: Configura el ejecutable de Python para CodeQL
  ([`0229cc3`](https://github.com/cortega26/chile-hub/commit/0229cc32d89662fed27ad1a0924d4ac122ff9f7a))

- **ci**: Prepara de forma segura las salidas del scraping mensual
  ([`f0f8096`](https://github.com/cortega26/chile-hub/commit/f0f80964b83f88fb0538bc4bb8faeb033b0c56ea))


## 1.19.6 - 2026-07-08

### Corregido

- **ci**: Fija la versión de extracción Python de CodeQL
  ([`e2f3710`](https://github.com/cortega26/chile-hub/commit/e2f3710676899ffe13ded10f335cf3d24a47b62b))

- **ci**: Redespliega Pages después de commits automatizados en main
  ([`fd23f12`](https://github.com/cortega26/chile-hub/commit/fd23f120ddbaa719771ff03612967aa25ec37780))


## 1.19.5 - 2026-07-08

### Corregido

- **ci**: Aclara la preparación y reduce el ruido de los logs de release
  ([`dc5a882`](https://github.com/cortega26/chile-hub/commit/dc5a88259eebcc433e09a8e957fa6369e3f6e884))


## 1.19.4 - 2026-07-08

### Corregido

- **ci**: Endurece las compuertas de artefactos de release
  ([`4ebca99`](https://github.com/cortega26/chile-hub/commit/4ebca99768d2f99415f221a41fda226fcebfbfa0))


## 1.19.3 - 2026-07-07

### Corregido

- **api**: Agrega datasets faltantes al enum Dataset
  ([`88187f0`](https://github.com/cortega26/chile-hub/commit/88187f031f0ef856c1260d0d282a93efbd066af0))

### Mantenimiento

- **dependencias**: Sincroniza uv.lock después del incremento de versión
  ([`0a95440`](https://github.com/cortega26/chile-hub/commit/0a95440635c552c960a9115ea9d72482169d441a))


## 1.19.2 - 2026-07-07

### Corregido

- **extractores**: Preserva ceros CUT y usa isoformat en consumo/pobreza
  ([`3ad6ab9`](https://github.com/cortega26/chile-hub/commit/3ad6ab9a378bb8e42eec89bae745f1c525d05b83))

### Mantenimiento

- **dependencias**: Regenera uv.lock y añade guardia --locked en CI
  ([`a6b22b8`](https://github.com/cortega26/chile-hub/commit/a6b22b82cc0e1702b9a1b33138054204ad1e03ca))


## 1.19.1 - 2026-07-06

### Corregido

- **ci**: Sincroniza versiones de inicio/análisis de codeql-action y agrupa incrementos futuros
  ([#25](https://github.com/cortega26/chile-hub/pull/25),
  [`b80e728`](https://github.com/cortega26/chile-hub/commit/b80e728de6af506d10e700223533c3a5ff854834))

### Documentación

- **readme**: Sincroniza tabla y menciones de capas tras promover 2 datasets
  ([#26](https://github.com/cortega26/chile-hub/pull/26),
  [`c1419e9`](https://github.com/cortega26/chile-hub/commit/c1419e94951b199cb4da23eb7ba562ce77ca7d2d))


## 1.19.0 - 2026-07-06

### Mantenimiento

- **dependencias**: Actualiza astral-sh/setup-uv de 8.2.0 a 8.3.0
  ([#23](https://github.com/cortega26/chile-hub/pull/23),
  [`5671b54`](https://github.com/cortega26/chile-hub/commit/5671b545a8014f6d15bed9134dc06843319eae05))

- **dependencias-dev**: Actualiza el grupo python-dev con 2 cambios
  ([#20](https://github.com/cortega26/chile-hub/pull/20),
  [`23ac012`](https://github.com/cortega26/chile-hub/commit/23ac0126273f56b0ac3723996bd34ee40e47c742))

### Documentación

- **sitio**: Publica referencia de API con MkDocs Material (Plan 021)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

### Agregado

- **datos**: Autoridades_electas v1 — diputados con distrito vía Scrapling (Plan 023 Ola A)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Autoridades_electas — cargo senadores + cableado candidate (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Autoridades_locales — alcaldes (345 comunas, con mejor esfuerzo) vía API MediaWiki
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Autoridades_locales — gobernadores (Wikipedia CC-BY-SA, segregado) (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Extractor partidos_politicos desde Cámara + Plan 023
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Promueve partidos_politicos y autoridades_electas a stable_publishable
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

- **datos**: Registra partidos_politicos en carril candidate (Plan 023)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))

### Pruebas

- **cobertura**: Mide todo el pipeline, no solo la librería (TC-02)
  ([#24](https://github.com/cortega26/chile-hub/pull/24),
  [`b3a8deb`](https://github.com/cortega26/chile-hub/commit/b3a8deb5df7cf7bfe4bfd263f550169de5ffc477))


## 1.18.1 - 2026-07-01

### Corregido

- **ci**: Elimina la bandera obsoleta que forzaba Node 24
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

- Preparación de CI — respaldo para pobreza_comunal y consumo_electrico_comunal + archivar Plan 022
  ([`b0ba125`](https://github.com/cortega26/chile-hub/commit/b0ba12579aef7c56980bdcd7b23dc12a85f72e24))

- Despliegue — añade pobreza_comunal y consumo_electrico_comunal a categorías CATEGORIES
  ([`63244a5`](https://github.com/cortega26/chile-hub/commit/63244a54ba8d2bce1e0287bb3a5327e7b86fa41b))

### Agregado

- Fase 1 — honestidad de datos y base de confianza (plan 022)
  ([`1d97b49`](https://github.com/cortega26/chile-hub/commit/1d97b49daf2d722ee901d7e1d643f5b55519d5a6))

- Fase 2 — narrativa técnica visible y Ola B1 — CASEN + CNE (plan 022)
  ([`7e7d63b`](https://github.com/cortega26/chile-hub/commit/7e7d63b7acdab646b55e6337d475a26499ba227e))

- Fase 3 — señales pasivas operativas y sanación de fuentes vía scraping (plan 022)
  ([`ca698ea`](https://github.com/cortega26/chile-hub/commit/ca698ea19001b117703d60b62afa669e37b9ccc9))

- Fase 4 — distribución sobre lo validado + Ola B2 — CEAD delincuencia + investigación electoral (plan
  022)
  ([`8e3e579`](https://github.com/cortega26/chile-hub/commit/8e3e579bdb26cc888c637b95f5f257dc352965d4))


## 1.17.1 - 2026-06-30

### Corregido

- **insignia**: Usa URL de shields.io y la mueve a la última posición
  ([`46604ca`](https://github.com/cortega26/chile-hub/commit/46604ca028991630d7d497d669d358247b049638))

### Mantenimiento

- **dependencias**: Actualiza actions/cache de 5.0.5 a 6.1.0
  ([#16](https://github.com/cortega26/chile-hub/pull/16),
  [`d61298b`](https://github.com/cortega26/chile-hub/commit/d61298becc001f500b329c0dec92967dd76545f2))

- **dependencias**: Actualiza actions/setup-python de 6.2.0 a 6.3.0
  ([#17](https://github.com/cortega26/chile-hub/pull/17),
  [`491847f`](https://github.com/cortega26/chile-hub/commit/491847fed3cb2a5f08340abb1d1ef4430ec1f425))

- **dependencias-dev**: Actualiza el grupo python-dev con 2 cambios
  ([#15](https://github.com/cortega26/chile-hub/pull/15),
  [`56a3843`](https://github.com/cortega26/chile-hub/commit/56a3843e4cce9480e8ae9c5d5df936419625d636))


## 1.17.0 - 2026-06-30

> 🎯 **Resumen:** Este release cierra los pendientes estratégicos de ingeniería y posiciona
> a chile-hub como parte del ecosistema Tooltician. Se completan tres frentes diferidos
> desde la auditoría inicial: contratos de tipos en tiempo de ejecución (`contracts.py`), el enum
> `Dataset` que unifica la referencia a capas, y el panel de salud programático
> (`hub_health.json`). La librería ahora valida tipos al importar y expone un panel de
> salud consultable sin abrir un Parquet. La identidad visual se alinea con Tooltician
> (insignia + lema en español), cerrando la brecha entre la ingeniería real y su cara
> pública. Este release es la base técnica sobre la que se construye la narrativa de
> confiabilidad del Plan 022.

### Documentación

- **insignia**: Insignia Tooltician -> Parte de Tooltician
  ([`74c0064`](https://github.com/cortega26/chile-hub/commit/74c00645f3e94e69e5f1802943d21e8c6582be33))

- **readme**: Añade insignia y lema del ecosistema Tooltician
  ([`39bda6a`](https://github.com/cortega26/chile-hub/commit/39bda6a395cbbbbde323bf32da9d716d0e21dff7))

- **readme**: Insignia y lema Tooltician en español
  ([`0d8c179`](https://github.com/cortega26/chile-hub/commit/0d8c179770231ac433870f2370564327f70d0cb0))

### Agregado

- **pendientes**: Completa #2 #3 #5 — contratos en tiempo de ejecución, enum Dataset y panel de salud
  ([`a3ef978`](https://github.com/cortega26/chile-hub/commit/a3ef9782fb3c4dbf557d63d7fda226c15c42ac2a))


## 1.16.0 - 2026-06-29

> 🎯 **Resumen:** Lanzamiento de madurez de UX y estándares. La CLI migra de relleno manual
> a tablas formateadas con `rich` (Plan 018): `chile-hub info`, `list datasets` y
> `show` ahora renderizan tablas con bordes, colores y columnas auto-ajustadas. El
> pipeline publica `datapackage.json` en formato Frictionless Data (Plan 019), derivado
> automáticamente de los contratos `contracts/datasets/*.json`, dando interoperabilidad
> estándar sin mantenimiento adicional. Se institucionaliza la disciplina de archivado de
> planes: los planes DONE se mueven a `archive/` de inmediato. La experiencia de uso
> y la apertura de datos dan un salto sin tocar la lógica de negocio.

### Mantenimiento

- **dependencias-dev**: Actualiza duckdb ([#10](https://github.com/cortega26/chile-hub/pull/10),
  [`140c8ea`](https://github.com/cortega26/chile-hub/commit/140c8ea034c9068aabb9b108760c45e1fda08543))

- **dependencias-dev**: Actualiza el grupo python-dev con 3 cambios
  ([#11](https://github.com/cortega26/chile-hub/pull/11),
  [`cd2e046`](https://github.com/cortega26/chile-hub/commit/cd2e0463af5e99dfcbc8eff0c70a188dcd0d1775))

- **planes**: Archiva planes DONE y añade instrucción de archivado automático
  ([`faf90c2`](https://github.com/cortega26/chile-hub/commit/faf90c2eb3859d5828d29125347babca9503df35))

### Agregado

- **pipeline**: Publica datapackage.json (Frictionless) derivado de contratos
  ([`0d1fcc8`](https://github.com/cortega26/chile-hub/commit/0d1fcc80959d3dff06135f7ae8c73a11b21ea21c))

### Refactorizado

- **cli**: Renderiza tablas con rich en vez de relleno manual
  ([`85ef69f`](https://github.com/cortega26/chile-hub/commit/85ef69f61c341974de3e4f3f43c4eded24080963))


## 1.15.1 - 2026-06-24

### Corregido

- **build**: Mueve ajuste de sys.path antes de importaciones de src.* en build_dev_db.py
  ([`643f89c`](https://github.com/cortega26/chile-hub/commit/643f89c8d289c87cff6f842be7f7fcfa3a8cffa0))

### Mantenimiento

- **dependencias**: Actualiza actions/checkout de 6.0.3 a 7.0.0
  ([#12](https://github.com/cortega26/chile-hub/pull/12),
  [`581748f`](https://github.com/cortega26/chile-hub/commit/581748f34b2c20c6bb4dfe209571f2f02748085b))

- **dependencias**: Actualiza astral-sh/setup-uv de 8.1.0 a 8.2.0
  ([#13](https://github.com/cortega26/chile-hub/pull/13),
  [`79edd13`](https://github.com/cortega26/chile-hub/commit/79edd1351a6208bf245cddb513d4b0b929342bca))

- **dependencias**: Actualiza codecov/codecov-action de 5 a 7
  ([#14](https://github.com/cortega26/chile-hub/pull/14),
  [`3494e86`](https://github.com/cortega26/chile-hub/commit/3494e865489a578892f58edae52848ce5b84a237))

### Documentación

- **changelog**: Actualizar registro de cambios y configurar generación automática en español
  ([`c0796f4`](https://github.com/cortega26/chile-hub/commit/c0796f48fe4c17e25395578a724f3451c5ab6991))

- **datasets**: Evalúa candidatos y agrega estado under-review
  ([`a0978a3`](https://github.com/cortega26/chile-hub/commit/a0978a38cf2889b19b65b88b610edf443d7ecfe4))


---

## 1.15.0 - 2026-06-21

> 🎯 **Resumen:** Lanzamiento de robustez de ingeniería. Todos los extractores HTTP ahora
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
  docstrings), `bandit` (escaneo de seguridad estático), `pytest-xdist` (pruebas en
  paralelo), `hypothesis` (pruebas basadas en propiedades) y `structlog` (registro
  estructurado del pipeline).
- Corregida compatibilidad de `pytest-xdist` en CI removiendo `-n auto` de
  `addopts`.
- Reparadas insignias de cobertura y frescura de datos en el README.

---

## 1.13.0 - 2026-06-20

### Cambiado

- Rediseño de la landing page con cajón lateral deslizante
  para mostrar detalles de cada dataset, reemplazando el panel anterior. La
  navegación es ahora más fluida y funciona correctamente en dispositivos móviles.

---

## 1.12.0 - 2026-06-20

### Agregado

- Extractor en vivo para **SIEDU** (Sistema de Indicadores y Estándares de Desarrollo
  Urbano del MINVU): descarga directa desde la API oficial, eliminando la
  dependencia de snapshots locales.
- Extractor en vivo para **MINEDUC Resultados Educacionales**: obtención en vivo desde
  la fuente oficial del Ministerio de Educación.
- Ambos datasets pasan de modo `fallback` a modo `live`, cerrando las incidencias #6 y #7.

---

## 1.11.1 - 2026-06-19

### Corregido

- Corregidos metadatos `source_mode` engañosos en varios extractores; URLs alineadas
  con los puntos de acceso reales de cada fuente.
- Dataset SINIM degradado a carril `candidate` al confirmarse que su fuente requiere
  revisión de redistribución.

---

## 1.11.0 - 2026-06-19

### Agregado

- `ChileHub.cross_view()`: cruza dos datasets por código CUT en una sola llamada.
- `ChileHub.validate_user_data()`: valida un DataFrame externo contra el esquema
  de un dataset del hub.
- `ChileHub.search_datasets()`: búsqueda de datasets por palabras clave.
- Bandera `--exit-code` en la CLI para integración programática con scripts de CI y
  orquestación.

### Cambiado

- Catálogo extraído como archivo externo `dataset_catalog_config.json`;
  `build_dev_db.py` ya no lo embebe como código fuente, simplificando el
  orquestador y corrigiendo `PYTHONPATH` en entornos de desarrollo.

### Corregido

- Eliminada ventana TOCTOU en la descarga del paquete: el hash SHA-256 se calcula
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

- Cierre correcto de respuestas HTTP mediante context managers en todos los extractores.
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
- Pendientes de mejoras estratégicas con hoja de ruta priorizada documentada en
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
  de las fuentes de origen en vivo.
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
- `codecov-action` anclado a la etiqueta estable `v5` en lugar de un SHA de confirmación.

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

- Corrección en la suite de pruebas eliminando la dependencia directa de snapshots `raw` locales.
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

- Migración del despliegue de GitHub Pages al flujo moderno basado en GitHub Actions.

### Corregido

- Control de clics en las pestañas de curl para evitar errores interactivos en datasets que no generan salida JSON.

## 1.2.0 - 2026-06-17

### Agregado

- Agregada nueva superficie de dataset público: `empresas` (Registro de Empresas y
  Sociedades del Ministerio de Economía, ~1.57M registros con RUT, razón
  social, tipo societario y comuna tributaria).
- Agregado `res_extractor.py` con obtención en vivo desde datos.gob.cl, snapshot
  cruda, staging CSV y generación de metadatos.
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

- `puntos_interes` (POI de OpenStreetMap) — extractor, configuración, pruebas, CI y
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
  redistribución, salud, paquete, CI y documentación para las nuevas capas.
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
