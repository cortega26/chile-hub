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

## 1.31.0 - 2026-08-24

### Agregado

- **registry**: Phase 3C alias and derived cohort (2 datasets)
  ([`936494b`](https://github.com/cortega26/chile-hub/commit/936494b3910449861b825e85a46fddfaa79f9549))

- **registry**: Phase 3D exceptional cohort (7 datasets) — complete 22-spec migration
  ([`5c4c1a9`](https://github.com/cortega26/chile-hub/commit/5c4c1a9f6e10e73ab86bc50df98f388254983773))


## 1.30.0 - 2026-08-24

### Agregado

- **registry**: Phase 3A direct stable cohort (9 datasets)
  ([`b2b4a96`](https://github.com/cortega26/chile-hub/commit/b2b4a9673d64efe59656c052f124cbccda18b133))

- **registry**: Phase 3B shared-source cohort (regiones, provincias, comunas)
  ([`3f024e3`](https://github.com/cortega26/chile-hub/commit/3f024e3a238082ae0533d9240021643761fcb12e))


## 1.29.0 - 2026-08-24

### Corregido

- **landing**: Show current package version
  ([`6658c30`](https://github.com/cortega26/chile-hub/commit/6658c300961456a480a12381ef89b6e1c137b0c1))

### Documentación

- Auto-sync tras carrera con release [skip ci]
  ([`52aa686`](https://github.com/cortega26/chile-hub/commit/52aa6867c2830bb31fb30175f4a683f4a72e80f6))

### Agregado

- **registry**: Phase 2 DatasetSpec pilot for partidos_politicos
  ([`10ebf71`](https://github.com/cortega26/chile-hub/commit/10ebf711ef8ecf55c9b1c51d6b7d3feed0e8a950))


## 1.28.8 - 2026-08-22

### Corregido

- **landing**: Polish mobile layout
  ([`e00caa9`](https://github.com/cortega26/chile-hub/commit/e00caa9933bff72ccf852e729e046f8a4278c67c))


## 1.28.7 - 2026-08-22

### Corregido

- **release**: Verify landing metadata before commit
  ([`11ad400`](https://github.com/cortega26/chile-hub/commit/11ad4003f904c0fd1f66b8e82b0ede7ac873feca))

### Mantenimiento

- **deps**: Bump astral-sh/setup-uv from 9.0.0 to 10.0.1
  ([#81](https://github.com/cortega26/chile-hub/pull/81),
  [`bd01786`](https://github.com/cortega26/chile-hub/commit/bd01786b48264515a9a2c1142d04f5b84ab09d17))

- **deps**: Bump the codeql-action group with 2 updates
  ([#80](https://github.com/cortega26/chile-hub/pull/80),
  [`efb3d10`](https://github.com/cortega26/chile-hub/commit/efb3d1068003988b0d7828fc010cbf17ff3fe05d))

- **deps-dev**: Bump the python-dev group across 1 directory with 4 updates
  ([#82](https://github.com/cortega26/chile-hub/pull/82),
  [`3bb923c`](https://github.com/cortega26/chile-hub/commit/3bb923ca1bd9017088c74ef17cdb221749d4d7a8))


## 1.28.6 - 2026-08-22

### Corregido

- **deps**: Upgrade pip to resolve audit finding
  ([`57b06f9`](https://github.com/cortega26/chile-hub/commit/57b06f942cd90c2c0c8f35ec3064e3fae1516e33))

- **landing**: Sync app cache version
  ([`0cabffc`](https://github.com/cortega26/chile-hub/commit/0cabffc45a81452d89d58f88be41723168233a9a))

- **res**: Tipos Date en fecha_* de empresas; codigo_comuna en fallback de cead
  ([`2de14af`](https://github.com/cortega26/chile-hub/commit/2de14af67898db6612d8be069e2f5a1701ede75b))

### Mantenimiento

- **codegraph**: Ignora todo .codegraph/ salvo .gitignore
  ([`80da68f`](https://github.com/cortega26/chile-hub/commit/80da68f8951ac969e788972bcf7e45767abce38e))

### Documentación

- Auto-sync tras carrera con release [skip ci]
  ([`273abbe`](https://github.com/cortega26/chile-hub/commit/273abbe3c269afa88930ddfdd44354ad7ec279b6))

### Refactorizado

- **build**: Registro central de tipos de staging (schema_overrides)
  ([`5e60466`](https://github.com/cortega26/chile-hub/commit/5e6046695a6d79bd97691ea02ca3f39b84c48f7a))


## 1.28.5 - 2026-08-13

### Corregido

- **landing**: Tolerancia direccional de version en el badge (misma ventana release->publish)
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))

- **res**: Tipos canonicos en el merge incremental — anio/capital/fechas
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))

- **res**: Tipos canónicos en el merge incremental (bug del dispatch)
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))

- **verify**: Tolerancia direccional de version en hub_bundle (mismo patron que pipeline_metadata)
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))

- **verify**: Tolerancia direccional de version en pipeline_metadata
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))

### Tests

- Version futura con +5 (robusto a la ventana release->publish)
  ([#78](https://github.com/cortega26/chile-hub/pull/78),
  [`8a246b6`](https://github.com/cortega26/chile-hub/commit/8a246b6fff8ffc701ede86178b25b14d37ab1686))


## 1.28.4 - 2026-08-13

### Corregido

- **ci**: Eliminar carreras de escritura sobre main (release no escribe datos)
  ([#77](https://github.com/cortega26/chile-hub/pull/77),
  [`c2d1455`](https://github.com/cortega26/chile-hub/commit/c2d145529d878973da8b0476903265b2528c1fb3))

- **ci**: Eliminar carreras de escritura sobre main — release no escribe datos (write-races)
  ([#77](https://github.com/cortega26/chile-hub/pull/77),
  [`c2d1455`](https://github.com/cortega26/chile-hub/commit/c2d145529d878973da8b0476903265b2528c1fb3))

- **ci**: P1x2 + P2 de la review del PR #77 — artifact lleva derivados, release commitea index/app
  ([#77](https://github.com/cortega26/chile-hub/pull/77),
  [`c2d1455`](https://github.com/cortega26/chile-hub/commit/c2d145529d878973da8b0476903265b2528c1fb3))


## 1.28.3 - 2026-08-13

### Corregido

- **test**: INDICADORES_NON_SYNTHETIC_DELIVERY incluye ine_override
  ([#76](https://github.com/cortega26/chile-hub/pull/76),
  [`1f37e2d`](https://github.com/cortega26/chile-hub/commit/1f37e2d9bbb2376da3672bf9733905f616b4f47d))

### Documentación

- Auto-sync tras carrera con release [skip ci]
  ([`ff8dd74`](https://github.com/cortega26/chile-hub/commit/ff8dd740780971d63f162192853bbcb668291e26))

- Auto-sync tras carrera con release [skip ci]
  ([`aa8274e`](https://github.com/cortega26/chile-hub/commit/aa8274ec64aefecab25fadcd8c4874f953ada2ec))

- Quality summary 95.2 — destraba Check build-synced files del publish
  ([`89276e4`](https://github.com/cortega26/chile-hub/commit/89276e43002e3af5dabdcd31a4878cf1f3b41ed9))

- README quality summary 94.2 -> 95.2 (Plan 084)
  ([`3cfb158`](https://github.com/cortega26/chile-hub/commit/3cfb158ce0e54e1475d224c756fe3dae63777791))

- **e2e**: Quita el ejemplo de script individual archivado
  ([#75](https://github.com/cortega26/chile-hub/pull/75),
  [`d18088e`](https://github.com/cortega26/chile-hub/commit/d18088e9abcf039512cd017050172d2e21a285e7))

### Tests

- Higiene — sin red real, sleeps inyectados, guards, e2e congelados (Plan 080)
  ([#75](https://github.com/cortega26/chile-hub/pull/75),
  [`d18088e`](https://github.com/cortega26/chile-hub/commit/d18088e9abcf039512cd017050172d2e21a285e7))

- Higiene — sin red real, sleeps, guards, e2e congelados (Plan 080)
  ([#75](https://github.com/cortega26/chile-hub/pull/75),
  [`d18088e`](https://github.com/cortega26/chile-hub/commit/d18088e9abcf039512cd017050172d2e21a285e7))


## 1.28.2 - 2026-08-13

### Corregido

- **res**: Contrato del merge incremental — padding de regiones y dedup por clave
  ([#74](https://github.com/cortega26/chile-hub/pull/74),
  [`7988f98`](https://github.com/cortega26/chile-hub/commit/7988f985fa3208901765aeab4e5e388fffae6866))

### Mejorado

- **res**: Fetch incremental — solo el anio en curso (Plan 076)
  ([#74](https://github.com/cortega26/chile-hub/pull/74),
  [`7988f98`](https://github.com/cortega26/chile-hub/commit/7988f985fa3208901765aeab4e5e388fffae6866))

- **res**: Fetch incremental — solo el año en curso (Plan 076)
  ([#74](https://github.com/cortega26/chile-hub/pull/74),
  [`7988f98`](https://github.com/cortega26/chile-hub/commit/7988f985fa3208901765aeab4e5e388fffae6866))


## 1.28.1 - 2026-08-13

### Corregido

- **ine**: Acoplar valor y periodo en el regex del override (Plan 075)
  ([#73](https://github.com/cortega26/chile-hub/pull/73),
  [`3181254`](https://github.com/cortega26/chile-hub/commit/318125410ce60b7952f1689aea166ab9971fed40))

- **ine**: Acoplar valor y período en el regex del override (Plan 075)
  ([#73](https://github.com/cortega26/chile-hub/pull/73),
  [`3181254`](https://github.com/cortega26/chile-hub/commit/318125410ce60b7952f1689aea166ab9971fed40))

- **ine**: Rechazar apertura de contenedor anidado en el span (Plan 075)
  ([#73](https://github.com/cortega26/chile-hub/pull/73),
  [`3181254`](https://github.com/cortega26/chile-hub/commit/318125410ce60b7952f1689aea166ab9971fed40))

### Documentación

- **adr**: ADR-017 — cadena multi-fuente para el override de IPC (Plan 085)
  ([#72](https://github.com/cortega26/chile-hub/pull/72),
  [`37a9b4d`](https://github.com/cortega26/chile-hub/commit/37a9b4dc5f988710b6f47ba64f2ccffdd3accdfc))

- **adr**: Alcance exacto del escape hatch del ADR-017
  ([#72](https://github.com/cortega26/chile-hub/pull/72),
  [`37a9b4d`](https://github.com/cortega26/chile-hub/commit/37a9b4dc5f988710b6f47ba64f2ccffdd3accdfc))


## 1.28.0 - 2026-08-13

### Agregado

- **registry**: 4 fixes de la review del PR #71 (Plan 084)
  ([#71](https://github.com/cortega26/chile-hub/pull/71),
  [`384376d`](https://github.com/cortega26/chile-hub/commit/384376dd65ca3194e0fdbbaf46f258e3d8bb2ab5))

- **registry**: Promover perfil_territorial_comunal al bundle estable (Plan 084)
  ([#71](https://github.com/cortega26/chile-hub/pull/71),
  [`384376d`](https://github.com/cortega26/chile-hub/commit/384376dd65ca3194e0fdbbaf46f258e3d8bb2ab5))

### Tests

- **chile_hub**: Bundle_summary agnostico a la generacion de datos
  ([#71](https://github.com/cortega26/chile-hub/pull/71),
  [`384376d`](https://github.com/cortega26/chile-hub/commit/384376dd65ca3194e0fdbbaf46f258e3d8bb2ab5))


## 1.27.0 - 2026-08-13

### Corregido

- **verify**: Gate de review counts tolerante a datos del ultimo publish
  ([#70](https://github.com/cortega26/chile-hub/pull/70),
  [`b723048`](https://github.com/cortega26/chile-hub/commit/b723048924eb9f3edcfdbca79b810ffadc58a05b))

### Agregado

- **health**: Senal proactiva de review_by upcoming/due (Plan 083)
  ([#70](https://github.com/cortega26/chile-hub/pull/70),
  [`b723048`](https://github.com/cortega26/chile-hub/commit/b723048924eb9f3edcfdbca79b810ffadc58a05b))

- **health**: Señal proactiva de review_by upcoming/due (Plan 083)
  ([#70](https://github.com/cortega26/chile-hub/pull/70),
  [`b723048`](https://github.com/cortega26/chile-hub/commit/b723048924eb9f3edcfdbca79b810ffadc58a05b))


## 1.26.0 - 2026-08-12

### Documentación

- Quickstart R, marcas de carril, inventario de extractores (Plan 081)
  ([#68](https://github.com/cortega26/chile-hub/pull/68),
  [`a20ceeb`](https://github.com/cortega26/chile-hub/commit/a20ceeb3a32e819d2c9d3ef3cb3aeeb5e5cccda4))

- **r-quickstart**: Opcion C sin INSTALL httpfs (rutas locales, offline-safe)
  ([#68](https://github.com/cortega26/chile-hub/pull/68),
  [`a20ceeb`](https://github.com/cortega26/chile-hub/commit/a20ceeb3a32e819d2c9d3ef3cb3aeeb5e5cccda4))

### Agregado

- **landing**: Carril candidate visible en la landing (Plan 082)
  ([#69](https://github.com/cortega26/chile-hub/pull/69),
  [`afaa96b`](https://github.com/cortega26/chile-hub/commit/afaa96bd88663bff04b38d8dbf4581a24aedb3cb))

- **landing**: Seccion candidate visible + fix grid estables (Plan 082)
  ([#69](https://github.com/cortega26/chile-hub/pull/69),
  [`afaa96b`](https://github.com/cortega26/chile-hub/commit/afaa96bd88663bff04b38d8dbf4581a24aedb3cb))

### Tests

- **landing**: Deriva el nombre candidate del bundle en el smoke test
  ([#69](https://github.com/cortega26/chile-hub/pull/69),
  [`afaa96b`](https://github.com/cortega26/chile-hub/commit/afaa96bd88663bff04b38d8dbf4581a24aedb3cb))


## 1.25.1 - 2026-08-12

### Corregido

- **validation**: El punto más reciente ≤0 se evalúa con detector de nivel (Plan 074)
  ([`efa42a2`](https://github.com/cortega26/chile-hub/commit/efa42a2ddbcbccd057ff425269fb7dc161a8b614))

- **validation**: Ruptura de serie constante con MAD=0 se reporta (P2 del 074)
  ([`aef3e3f`](https://github.com/cortega26/chile-hub/commit/aef3e3fd077406c3c2ffa667ed0bfe556d32c271))

### Mantenimiento

- Ignora codegraph.lock (artefacto local del indexador)
  ([`b12bf72`](https://github.com/cortega26/chile-hub/commit/b12bf72acbbd51dbf22c27edb58b97bd999357c2))

### Documentación

- Sincroniza conteo de validation.py (1505)
  ([`631443e`](https://github.com/cortega26/chile-hub/commit/631443eac5977691b79fb8d43061b68b1ff3469e))


## 1.25.0 - 2026-08-12

### Corregido

- **artifacts**: El catálogo del bundle ZIP solo declara capas incluidas
  ([`e9d6041`](https://github.com/cortega26/chile-hub/commit/e9d6041f5ed9cd704f594be259cbd0271c6fd023))

- **artifacts**: El manifest embebido describe el catálogo filtrado del ZIP
  ([`ee99e7a`](https://github.com/cortega26/chile-hub/commit/ee99e7a6ea9cc3a35b2a57ad795a7e7c93e66f27))

- **artifacts**: Tipo del catálogo filtrado (mypy) y round-trip con catálogo
  ([`76e123a`](https://github.com/cortega26/chile-hub/commit/76e123abbaaaabdb509ed582917083819630027f))

- **ci**: CodeQL tambien escucha merge_group (check requerido de la cola)
  ([`f41143f`](https://github.com/cortega26/chile-hub/commit/f41143f9518b32a963adac7b420807eef4c67938))

- **data_manager**: Validar el ZIP antes de borrar la caché verificada
  ([`19d1608`](https://github.com/cortega26/chile-hub/commit/19d1608582526f95022e29522ea5b150e0496414))

- **data_manager**: Zip-slip guard en _extract_bundle (Plan 072)
  ([`a1e50d3`](https://github.com/cortega26/chile-hub/commit/a1e50d3aef6a3cdd5abf446fd52d33ff22fea37c))

- **extractors**: El override INE es delivery visible, no backfill enmascarado
  ([`6ef22fd`](https://github.com/cortega26/chile-hub/commit/6ef22fdd2ff96368261f94e773336fa725bdb08b))

- **hf**: Delete_patterns en el mirror, e2e 059 a 17, AGENTS.md 17 capas
  ([`cc4cc8e`](https://github.com/cortega26/chile-hub/commit/cc4cc8ebea7ad4fa450e1d82d53bbcdb60ad67c3))

- **hf**: El mirror filtra por publication_track del registry (nunca candidate)
  ([`d34462f`](https://github.com/cortega26/chile-hub/commit/d34462fdfa43945fe47dea2627db97107c59c626))

- **package**: El contrato del wheel sobrevive a as_file() efímero (P2)
  ([`84f84e3`](https://github.com/cortega26/chile-hub/commit/84f84e310a57dc6cde815e0089be6d80852c0132))

- **package**: Incluir contracts en el sdist (build sdist→wheel en CI)
  ([`df91b93`](https://github.com/cortega26/chile-hub/commit/df91b93d2eb74db9e01f654711526c830c369230))

- **release**: El override INE es age-gated (no puede publicar stale indefinidamente)
  ([`17ff5de`](https://github.com/cortega26/chile-hub/commit/17ff5debb2d6d417b5dc9801a793a54848d6fa7c))

### Mantenimiento

- Trigger CI en merge-queue-ready (fix CodeQL + sync docs)
  ([`9e9e253`](https://github.com/cortega26/chile-hub/commit/9e9e2533df264c8e3040200f520e5e38eb959919))

- Trigger CI on docs-gate-auto-heal branch
  ([`8c72956`](https://github.com/cortega26/chile-hub/commit/8c72956c04967fcf8511bfeba639d6c3edd982b8))

- Trigger CI tras fix P1 (job docs-autosync separado)
  ([`fd672e7`](https://github.com/cortega26/chile-hub/commit/fd672e711615f71e78bb469ac46b394233428435))

### Integración continua

- **docs**: Auto-heal del gate de sync en push a main (carrera con releases)
  ([`5e81f86`](https://github.com/cortega26/chile-hub/commit/5e81f86e29ce0709fd647b644c6c5bb04e25bc63))

- **docs**: Auto-heal del gate de sync en push a main (carrera con releases)
  ([`c067db0`](https://github.com/cortega26/chile-hub/commit/c067db010f0939bcf0f22f3468c0b9feee7ec650))

### Documentación

- Sincroniza conteo de tests tras guardrail de merge group [skip ci]
  ([`b6a47b4`](https://github.com/cortega26/chile-hub/commit/b6a47b4ad326c1539862652495107101255018cb))

### Agregado

- **ci**: Prepara el workflow para la merge queue de GitHub (evento merge_group)
  ([`53781e2`](https://github.com/cortega26/chile-hub/commit/53781e2c8224633d73b3021a46ce53e7e049f427))

- **package**: Contratos disponibles para consumidores instalados (Plan 073)
  ([`6691476`](https://github.com/cortega26/chile-hub/commit/66914763e2a8ed3c56a04a69110ede3ae26078eb))


## 1.24.1 - 2026-08-12

### Corregido

- **release**: Sincroniza README (pin de version) en el commit de release
  ([`e6848d8`](https://github.com/cortega26/chile-hub/commit/e6848d879aa68d86a210c96452767fb90d3c3a0a))

### Mantenimiento

- Trigger pipeline tras sync del pin 1.24.0
  ([`b030e13`](https://github.com/cortega26/chile-hub/commit/b030e13fadd9c9d53d3b10efaa5e50dd33490634))

### Documentación

- Sincroniza pin de README con 1.24.0 tras release intermedio [skip ci]
  ([`22896c0`](https://github.com/cortega26/chile-hub/commit/22896c0c6c8b78501e94a1ff9ba208f63cdabee4))


## 1.24.0 - 2026-08-12

### Corregido

- **landing**: Copy factual preciso tras review (17 capas, match exacto, 345 geometrías)
  ([`eabb9d2`](https://github.com/cortega26/chile-hub/commit/eabb9d209915e33374d4efe747f266280a35ace6))

### Mantenimiento

- Trigger pipeline tras sync de README (1.23.1)
  ([`b416ea3`](https://github.com/cortega26/chile-hub/commit/b416ea36d434aa12de43cbbb8dae7c795456ec87))

### Documentación

- Sincroniza README con 1.23.1 tras release intermedio [skip ci]
  ([`7dd1d83`](https://github.com/cortega26/chile-hub/commit/7dd1d839ff101529783bf2298ceb30a6a015a97b))

### Agregado

- **landing**: Hero rediseñado, sección Capacidades y footer estructurado
  ([`75f7010`](https://github.com/cortega26/chile-hub/commit/75f7010a4e2c6ded2f121d8ea7fcea14e6a974a7))

- **landing**: Reveal al scroll y scrollspy del nav
  ([`9ef56c9`](https://github.com/cortega26/chile-hub/commit/9ef56c9ebc357c94f1f269bb1aea5b94738073f8))


## 1.23.1 - 2026-08-11

### Corregido

- **release**: Degrada a ready=false cuando la re-verificacion del artefacto falla
  ([`e72c176`](https://github.com/cortega26/chile-hub/commit/e72c176b83c36332e4612457442a292176b54c95))

- **release**: Usa 'if' para capturar el fallo de re-verificacion bajo set -e
  ([`d119bb1`](https://github.com/cortega26/chile-hub/commit/d119bb1d90e2acc88d578eec7de335ed08207fba))

### Documentación

- Sincroniza README tras merge de main (856 tests, pin 1.23.0)
  ([`4f9969f`](https://github.com/cortega26/chile-hub/commit/4f9969fcf42529be502bdbb9119decbf0b42c2ac))


## 1.23.0 - 2026-08-11

### Corregido

- **extractors**: Censo 2024 responde 404 al UA de requests (anti-bot INE)
  ([`dd4a711`](https://github.com/cortega26/chile-hub/commit/dd4a7117841d991a4190cc99e0d3053f69ba1f30))

- **extractors**: Sube el timeout de mindicador.cl y registra latencia por llamada
  ([`531a16e`](https://github.com/cortega26/chile-hub/commit/531a16e2528ef8f1e6ec44c8234aecd25fa51ecb))

- **hardening**: SEC-02 is_relative_to, SEC-03 escapeHtml en salud
  ([`82717ca`](https://github.com/cortega26/chile-hub/commit/82717ca412182737bd1cf8ebec784f021482b93a))

- **release**: Adjunta datos verificados al release y explica el bache de 1.22.0
  ([`dc9f532`](https://github.com/cortega26/chile-hub/commit/dc9f532f245f8de45bdf5a2aa00394b67c966657))

- **release**: Perfil 'release' en verify_pipeline — sin exigir staging en el release job
  ([`a824a9c`](https://github.com/cortega26/chile-hub/commit/a824a9c9f717788d8c80793ab679cefdbc5a2501))

- **release**: Repara la cadena de publicacion (staging, extra pipeline, replay de overrides)
  ([`c39cce5`](https://github.com/cortega26/chile-hub/commit/c39cce51d6f8cf86bd3426420e1eb2d803c8c36d))

- **review**: P1 preserve IPC months en override INE + P2 sentinel pyproject ajeno
  ([`a2fa8c3`](https://github.com/cortega26/chile-hub/commit/a2fa8c34da34d9343fadcb12348909ae901c250f))

### Mantenimiento

- Trigger CI on batch branch (HEAD tenia [skip ci])
  ([`991c4ab`](https://github.com/cortega26/chile-hub/commit/991c4ab47cddc5e8fa18508356baa78b9057c361))

- **deps**: Bump actions/setup-python from 6.3.0 to 7.0.0
  ([#49](https://github.com/cortega26/chile-hub/pull/49),
  [`e29b6df`](https://github.com/cortega26/chile-hub/commit/e29b6df41e6a46048a3ed672ee99d37a429bc399))

- **deps**: Bump astral-sh/setup-uv from 8.3.0 to 9.0.0
  ([#48](https://github.com/cortega26/chile-hub/pull/48),
  [`b953c6a`](https://github.com/cortega26/chile-hub/commit/b953c6a18e3f9bfd997e0396ec370b8f518a4256))

- **deps**: Bump pypa/gh-action-pypi-publish from 1.14.1 to 1.14.2
  ([#50](https://github.com/cortega26/chile-hub/pull/50),
  [`a17761a`](https://github.com/cortega26/chile-hub/commit/a17761a429680d8d7c2f2fe2c9cf39ee6705f4c9))

- **deps**: Bump the codeql-action group with 2 updates
  ([`adbe259`](https://github.com/cortega26/chile-hub/commit/adbe2598762d9cd93eaae1415480103ff038eabc))

- **deps**: Bump the codeql-action group with 2 updates
  ([#47](https://github.com/cortega26/chile-hub/pull/47),
  [`cbf1bde`](https://github.com/cortega26/chile-hub/commit/cbf1bded458e3cc5c96009015886bfa61562a34a))

- **deps**: Sincroniza uv.lock con pyproject.toml [skip ci]
  ([`8446b85`](https://github.com/cortega26/chile-hub/commit/8446b857c9ac8ca02babb1af0c3ebefa37180818))

- **deps**: Trigger CI re-run on updated branch
  ([`348a7e8`](https://github.com/cortega26/chile-hub/commit/348a7e846f0d46f7fbdc041a182ff0f34615a68e))

- **deps-dev**: Bump the python-dev group with 3 updates
  ([`84eda0b`](https://github.com/cortega26/chile-hub/commit/84eda0b47825b77144065ea2fab5de9e9a7416aa))

- **deps-dev**: Bump the python-dev group with 3 updates
  ([#46](https://github.com/cortega26/chile-hub/pull/46),
  [`d649230`](https://github.com/cortega26/chile-hub/commit/d649230218f916bbcccd61e52dfb263aa4c58ab2))

- **docs**: Sincroniza conteo de tests (804)
  ([`0c5b002`](https://github.com/cortega26/chile-hub/commit/0c5b002405f6993fc13da0bb75fd6d032d01a977))

- **docs**: Sincroniza conteo de tests en README (833 tras guardrails nuevos)
  ([`bfd5123`](https://github.com/cortega26/chile-hub/commit/bfd5123afbaf2726544abbf40c82206fb75ba63b))

- **plans**: Archiva el plan 053 (geometria comunal, completado)
  ([`e6bfa6a`](https://github.com/cortega26/chile-hub/commit/e6bfa6a852de97e388a45ec4ed6668ff639c4af1))

### Documentación

- Sincroniza AGENTS.md y README con el refactor (lineas core/cli, 13 archivos de tests, carriles)
  [skip ci]
  ([`36990df`](https://github.com/cortega26/chile-hub/commit/36990df86dc90615df37e9f439e5285122203b7c))

### Agregado

- Notify users about data updates ([#45](https://github.com/cortega26/chile-hub/pull/45),
  [`e62d9e7`](https://github.com/cortega26/chile-hub/commit/e62d9e7f20c03405476d0d298700aaec690e1e80))

- **ci**: Expone override allow_stale_backfills en workflow_dispatch
  ([`7126b0d`](https://github.com/cortega26/chile-hub/commit/7126b0d0aa69dc476f8f88da152d64ffb4f26758))

- **extractors**: IPC desde la fuente autoritativa INE cuando mindicador no lo entrega
  ([`61ec8e4`](https://github.com/cortega26/chile-hub/commit/61ec8e4276343391e56652bd46cf2e1b2e39322e))

- **geo**: Agrega resolve_by_coords para comunas
  ([`d9d5deb`](https://github.com/cortega26/chile-hub/commit/d9d5debcbc3745e5c029ef5b7862d045eecc7b23))

- **quality**: Guardrails anti-drift de documentación y fuentes
  ([`36f794d`](https://github.com/cortega26/chile-hub/commit/36f794d60dfbe194cffd43f632020b176e8403b2))

### Refactorizado

- **cli**: TECHDEBT-02 — mueve build_parser/_main/main/_print_result de core.py a cli.py
  ([`fddcf7e`](https://github.com/cortega26/chile-hub/commit/fddcf7edcd3e12e36f63889a5bee7468e5af0ae3))

- **paths**: TECHDEBT-05/06 — raiz unica _paths.find_root() y docs de carriles de extraccion
  ([`1c6e6d4`](https://github.com/cortega26/chile-hub/commit/1c6e6d4e52d75762ec30ff811dee2e06fb41863d))

- **tests**: TC-07 — extrae ChileHubDataManager y GeoCache a test_data_manager.py
  ([`085768f`](https://github.com/cortega26/chile-hub/commit/085768f96c08ed8ea22633cc0d1263ce0b480448))


## 1.22.0 - 2026-07-29

> 🎯 **Resumen:** El release más grande de la historia del proyecto, y no por
> diseño: **la publicación estuvo bloqueada 19 días sin que nada lo señalara.**
> El 2026-07-10 un `git push` no atómico dejó el tag `v1.22.0` publicado mientras
> el commit de bump era rechazado por una carrera con otro bot. Desde entonces
> `python-semantic-release` calculaba esa misma versión, veía su propio tag y
> respondía *"already released"* — en verde, porque los pasos de build y publish
> quedaban `skipped`. Resultado: 59 commits `feat`/`fix` acumulados en una sola
> versión, en vez de las ~6 minor que habrían salido con cadencia normal. El tag
> huérfano se eliminó y el push ahora usa `--atomic`, con un guardrail en
> `tests/test_ci_config.py` porque este fallo no produce ninguna señal roja.
>
> **Nada se perdió**: estas notas cubren el rango completo desde `v1.21.1`, así
> que los cambios que habrían aparecido en las versiones intermedias están todos
> listados abajo. Lo que se perdió fue la *granularidad* — no el registro.
>
> Qué trae, agrupado por hilo de trabajo:
>
> - **Confianza en el dato.** Detección de anomalías temporales en series
>   numéricas con rechazo de publicación override-able (ADR-013); backfill
>   consciente de la edad, que impide que una serie muerta se esconda tras un
>   reuso del último artefacto publicado (ADR-016 — descubierto porque `ipc`
>   llevaba 240 días congelado y nadie lo veía); y separación de *drift esperado*
>   vs *drift real* (ADR-014), que bajó `drifted_count` de 8 a 3 sin relajar un
>   solo gate ni tocar un dato.
> - **Salud legible.** Estado `retired` para fuentes muertas, derivado del
>   registry (ADR-015); historial append-only `hub_health_history.jsonl` con
>   sparkline en la landing; y contadores que por fin distinguen ruido
>   estructural de trabajo pendiente.
> - **Distribución.** Catálogo DCAT `data.json`, publicación del bundle en
>   Hugging Face Hub, GeoParquet comunal publicado por CI y servido desde Pages
>   (carril `candidate`, fuera del bundle estable), y señal de adopción
>   PyPI + GitHub Releases.
> - **API.** `resolve_comunas()` para mapear nombres a códigos CUT (ADR-009) y
>   `from_datapackage()` aceptando URLs (ADR-010).
> - **Landing.** Explorador SQL con DuckDB-Wasm, overhaul tipográfico, ritmo
>   visual, skeletons de carga y unificación de idioma y tokens de color.
> - **Anti-drift.** Campo `extractor` en las 22 entradas del catálogo, tabla de
>   extractores auto-generada, y cuatro fases de `doc-sync` que eliminan bloques
>   de documentación mantenidos a mano.


### Corregido

- **api**: From_datapackage acepta URLs
  ([`1ae710d`](https://github.com/cortega26/chile-hub/commit/1ae710d8dd03bd6ef17d60eadd9bb9c28de5edd9))

- **ci**: Ejecuta autoridades_electas con scrapling en entorno efimero
  ([`a04fe3f`](https://github.com/cortega26/chile-hub/commit/a04fe3fe1314adc6aa3d9b44bb798a24c81cd295))

- **ci**: Elimina condicion de carrera en la resolucion de run_id de hf-publish
  ([`bb5cfe6`](https://github.com/cortega26/chile-hub/commit/bb5cfe6ec76b95537728632caaf159b6898c4d8c))

- **ci**: Excluye el carril candidate del guardian de frescura
  ([`a30d56b`](https://github.com/cortega26/chile-hub/commit/a30d56bf39944609aa1d6d544fb7ca81c5915f72))

- **ci**: Redespliega Pages tras el refresh de geometria comunal
  ([`510da34`](https://github.com/cortega26/chile-hub/commit/510da348638bf2f6b3e9b91ba350efcf6ef8f5e6))

- **ci**: Remove outputs from autoridades_locales catalog entry
  ([`00e917d`](https://github.com/cortega26/chile-hub/commit/00e917dd5e26605ea9a8299b00a4b764784ada50))

- **ci**: Unblock dependency updates and publish adoption badge
  ([`bacd872`](https://github.com/cortega26/chile-hub/commit/bacd872f51a6d7cf8945be20714dbdfd0a08aba1))

- **landing**: Agrega color al badge .dataset-badge.monthly
  ([`4006f12`](https://github.com/cortega26/chile-hub/commit/4006f12c4cdd331ed28922fade26c631c546e215))

- **landing**: Agrega estilo de pill a .dataset-tag en tarjetas del catálogo
  ([`a965e8e`](https://github.com/cortega26/chile-hub/commit/a965e8ea92535d666dce19785ce3224f66e4115f))

- **landing**: Alinea privacy.html con el sistema de diseño del sitio
  ([`00ef134`](https://github.com/cortega26/chile-hub/commit/00ef134e2753f4f723aa93d681b03cf0e55b1c16))

- **landing**: Consolida CSS duplicado de .dataset-card y quita !important de .catalog-grid (plan
  048)
  ([`5417a12`](https://github.com/cortega26/chile-hub/commit/5417a12696f9442e6c7ad9f147ef039bc5cdba35))

- **landing**: Correct parquet base URL computation in playground.js
  ([`2ebed21`](https://github.com/cortega26/chile-hub/commit/2ebed216c59b8fa5854e3d4ef9e7c29ed4b2c3cb))

- **landing**: Correct variable name — wasmResp not resp
  ([`901f5b9`](https://github.com/cortega26/chile-hub/commit/901f5b91ef9af44f7eab11326682891e8193deb1))

- **landing**: Corrige var(--space-lg) no definida y fuente Fira Code no cargada (plan 047)
  ([`d338675`](https://github.com/cortega26/chile-hub/commit/d338675a363d462d197c503baa7926d18dda8204))

- **landing**: Envuelve resultados del Explorador SQL en contenedor con scroll
  ([`3b05681`](https://github.com/cortega26/chile-hub/commit/3b05681cab1b13822a9b06df88b95cce418fa2e6))

- **landing**: Force DuckDB-Wasm MVP variant to avoid EH signature mismatch
  ([`af870b7`](https://github.com/cortega26/chile-hub/commit/af870b734b212a64029564b61473d63e065e6535))

- **landing**: Pre-fetch WASM + Blob URL approach (worker fetch corrupted via CDN)
  ([`9843cfa`](https://github.com/cortega26/chile-hub/commit/9843cfa3e65fbac13a6acb3f459e6fe0d354656b))

- **landing**: Pre-fetch WASM in main thread via Blob URL to bypass CDN corruption
  ([`c630afb`](https://github.com/cortega26/chile-hub/commit/c630afb5c6329b8a77bf15ffd376c9d81b6b69fc))

- **landing**: Register parquet files via DuckDB-Wasm registerFileURL
  ([`5635cf6`](https://github.com/cortega26/chile-hub/commit/5635cf639574625de43329424ddecc85c78910eb))

- **landing**: Remove meta CSP — single HTTP header CSP avoids dual-policy intersection
  ([`d238038`](https://github.com/cortega26/chile-hub/commit/d23803807b097f182c65091245ed30b2c1e133b4))

- **landing**: Set explicit Blob MIME type for WASM to satisfy nosniff
  ([`9025aa5`](https://github.com/cortega26/chile-hub/commit/9025aa55a2bb4d37f3d519ee782c86615d3ec54c))

- **landing**: Simplify WASM loading — XCTO removed server-side fixes the issue
  ([`8a2686d`](https://github.com/cortega26/chile-hub/commit/8a2686d0e0134ba4826de40f6ff8180f32eda20b))

- **landing**: Use fetch+registerFileBuffer for parquet; add CSP hashes
  ([`c6f2453`](https://github.com/cortega26/chile-hub/commit/c6f245370bbdd324cef55fd450516a2dd8dd08c3))

- **landing**: Use page-relative path for WASM fetch
  ([`f2668e0`](https://github.com/cortega26/chile-hub/commit/f2668e03daa9c5a3d6b8ae3a22799968e2bcae58))

- **metadata**: Separa drift esperado de drift real en la taxonomia de salud
  ([`ddfc128`](https://github.com/cortega26/chile-hub/commit/ddfc1284264fa88c7bc60bb8fd6ef62edded70d3))

- **quality**: Repara umbral local de interrogate para que coincida con su propio comentario
  ([`17cb961`](https://github.com/cortega26/chile-hub/commit/17cb96105617f8c71f98aad14fa762e4898bcaf9))

- **release**: Usa --atomic al publicar el commit de release y su tag
  ([`667ed3f`](https://github.com/cortega26/chile-hub/commit/667ed3fbe53a87ce47d1c2bb00f6a2b59ac3cab0))

- **tooling**: Deja pre-commit run --all-files en verde
  ([`976417b`](https://github.com/cortega26/chile-hub/commit/976417bb93cf0ce72143dc71051398fa452c8349))

- **validation**: Elimina ruido de validacion en empresas
  ([#42](https://github.com/cortega26/chile-hub/pull/42),
  [`29d198d`](https://github.com/cortega26/chile-hub/commit/29d198d86d44091901a4dd18a8d04de7459edaf5))

### Mantenimiento

- **deps**: Bump actions/checkout from 7.0.0 to 7.0.1
  ([#40](https://github.com/cortega26/chile-hub/pull/40),
  [`9986287`](https://github.com/cortega26/chile-hub/commit/9986287be8b69e3137ca1050a2891cd4ac7ae175))

- **deps**: Bump actions/setup-python from 6.3.0 to 7.0.0
  ([#35](https://github.com/cortega26/chile-hub/pull/35),
  [`bd7fbcc`](https://github.com/cortega26/chile-hub/commit/bd7fbcc5dc54bafb3eb9555e3ffd07b1ee7592cb))

- **deps**: Bump astral-sh/setup-uv from 8.2.0 to 9.0.0
  ([#31](https://github.com/cortega26/chile-hub/pull/31),
  [`91997fe`](https://github.com/cortega26/chile-hub/commit/91997fe9ec1db5b51ba65df463b8cb0dac6fab8c))

- **deps**: Bump pypa/gh-action-pypi-publish from 1.14.0 to 1.14.1
  ([#34](https://github.com/cortega26/chile-hub/pull/34),
  [`1034aa9`](https://github.com/cortega26/chile-hub/commit/1034aa97fb3986baf36148745cf6fc141d71f863))

- **deps**: Bump the codeql-action group with 2 updates
  ([#39](https://github.com/cortega26/chile-hub/pull/39),
  [`d662e28`](https://github.com/cortega26/chile-hub/commit/d662e28bb2a6c9dcd7e04e5cb3fcb97b41191e64))

- **deps**: Bump the codeql-action group with 2 updates
  ([#33](https://github.com/cortega26/chile-hub/pull/33),
  [`8d2bd45`](https://github.com/cortega26/chile-hub/commit/8d2bd45a5766588745dad11575882df39b52b689))

- **deps**: Bump the codeql-action group with 2 updates
  ([#30](https://github.com/cortega26/chile-hub/pull/30),
  [`b8d9bef`](https://github.com/cortega26/chile-hub/commit/b8d9bef662458615d1b91eb93aec8b4d0cc7adde))

- **deps**: Regenera uv.lock (drift acumulado de bumps de dependabot)
  ([`5f3068e`](https://github.com/cortega26/chile-hub/commit/5f3068e9cb18aa496e2829ce3f05ae53811d4e2d))

- **deps**: Sincroniza uv.lock con pyproject.toml
  ([`ec15c25`](https://github.com/cortega26/chile-hub/commit/ec15c2579ef44d6a3c9b7198b7be285f0a15d8d8))

- **deps-dev**: Bump duckdb in the python-pipeline group
  ([#37](https://github.com/cortega26/chile-hub/pull/37),
  [`b3314bc`](https://github.com/cortega26/chile-hub/commit/b3314bcde3f018eb70a02de49c4af128eb5022bd))

- **deps-dev**: Bump the python-dev group across 1 directory with 5 updates
  ([#32](https://github.com/cortega26/chile-hub/pull/32),
  [`d1a23e7`](https://github.com/cortega26/chile-hub/commit/d1a23e721d55f4d4725232c27842b75a0e647148))

- **deps-dev**: Bump the python-dev group with 3 updates
  ([#38](https://github.com/cortega26/chile-hub/pull/38),
  [`0530cf6`](https://github.com/cortega26/chile-hub/commit/0530cf6369951b27e40bb8fb8f68ae23f5faad14))

- **docs**: Sincroniza conteo de tests (801)
  ([`2964b07`](https://github.com/cortega26/chile-hub/commit/2964b07cae828630ac0ca4590ea7689ac5ac3887))

- **landing**: Sincroniza JSON-LD con geometria_comunal (sync_landing_metadata)
  ([`2bae7f2`](https://github.com/cortega26/chile-hub/commit/2bae7f2e11f266c78d49cf1d01139c9e217f1631))

- **landing**: Sincroniza JSON-LD con geometria_comunal (sync_landing_metadata)
  ([`63cc106`](https://github.com/cortega26/chile-hub/commit/63cc1067cd068baa2ce090322fdf2151663020cf))

- **todo**: Newline final (end-of-file-fixer)
  ([`1e0b5fe`](https://github.com/cortega26/chile-hub/commit/1e0b5fe9bfb7f6926c9d63324c6e30f6b4fc56ef))

### Documentación

- Agrega spec/todo de orquestacion de la cola de planes activos
  ([`f172cdf`](https://github.com/cortega26/chile-hub/commit/f172cdf4515aaf1ea175184b4ba48699119e7621))

- Amplia nota de conflictos esperados en spec.md (checkpoint 2)
  ([`fc08573`](https://github.com/cortega26/chile-hub/commit/fc085738d3a72aa906137ce634bb736fb198dc3c))

- Incorpora hallazgos del checkpoint 1 (revision de gaps post 058+057)
  ([`0bd5eca`](https://github.com/cortega26/chile-hub/commit/0bd5eca258bb7355e90b0958a4bfbfdb1a29fa97))

- Marca Plan 050 completo en todo.md
  ([`6e2b13c`](https://github.com/cortega26/chile-hub/commit/6e2b13c8cb0ad622f876eb77cf9c2971103ae631))

- Marca Plan 051 completo en todo.md
  ([`a626ca7`](https://github.com/cortega26/chile-hub/commit/a626ca700596e4af71f99a1d574cde5399c6766b))

- Marca Plan 054 completo en todo.md
  ([`bde19e2`](https://github.com/cortega26/chile-hub/commit/bde19e26663a314747b44471a75e945653ca813d))

- Marca Plan 057 completo en todo.md
  ([`4b9dfc7`](https://github.com/cortega26/chile-hub/commit/4b9dfc794d7358ce2b4ca2c00b23d939d1ffdbdb))

- Marca Plan 058 completo en todo.md
  ([`07db232`](https://github.com/cortega26/chile-hub/commit/07db23294a9ecefb4ed130717386ef7694b8a0a2))

- Marca Plan 059 completo en todo.md
  ([`726d752`](https://github.com/cortega26/chile-hub/commit/726d7522689944e27a5bb90d03992d256a9bfa9f))

- Marca Plan 063 completo en todo.md
  ([`ac5f264`](https://github.com/cortega26/chile-hub/commit/ac5f2644241c1ba111235f374a516f99ffc668e3))

- Optimize documentation for AI assistants with YAML frontmatter and professional structure
  ([`577ceb1`](https://github.com/cortega26/chile-hub/commit/577ceb1278cbee453c96a7eedfc8b3a4f1c3cedc))

- Registra Checkpoint 4 (final) y confirma bloqueo de Plan 053 en todo.md
  ([`8c42815`](https://github.com/cortega26/chile-hub/commit/8c428155e808a2c77d3f00f5a8f370dab2469a13))

- Registra checkpoints 1-3 completos en todo.md
  ([`1b5779f`](https://github.com/cortega26/chile-hub/commit/1b5779f1ae512a2e5ba094bf150783454de5a469))

- Remove README metadata front matter
  ([`4c249b7`](https://github.com/cortega26/chile-hub/commit/4c249b7ba07c7204466a1191d9deb5bf92bcf54e))

- Remove redundant downloads badge
  ([`bd81e1c`](https://github.com/cortega26/chile-hub/commit/bd81e1c52b34f46bd9ab20de702c9a249fea568e))

- Update Documentation URL in pyproject.toml
  ([`5c47439`](https://github.com/cortega26/chile-hub/commit/5c474398c585bf6ff8ab71a8c350b6739332ecb0))

- **adr**: ADR-011 (estrategia construir-por-delante-de-demanda, proposed) y ADR-012 (licencia
  geometria comunal, accepted)
  ([`fcb5f03`](https://github.com/cortega26/chile-hub/commit/fcb5f0321ad621e73ecec1ecb63b165f13128d77))

- **adr**: Agrega ADR-010 (acceso HTTP estatico + catalogo DCAT)
  ([`dea3621`](https://github.com/cortega26/chile-hub/commit/dea36211c35d9a82a102e90116fcdbb1c38ba7dd))

- **adr**: Agrega ADR-013 (validacion de anomalias temporales)
  ([`4eaf581`](https://github.com/cortega26/chile-hub/commit/4eaf581e09858b9bbf23705855644ee49882a1b0))

- **adr**: Ratifica ADR-011 (proposed -> accepted)
  ([`f23e3c2`](https://github.com/cortega26/chile-hub/commit/f23e3c215e71c95f94e506f6ff39bbcbe2a68329))

- **agents**: Documenta hub_health_history.jsonl en propietarios canonicos
  ([`8400a7c`](https://github.com/cortega26/chile-hub/commit/8400a7cee2bd73366256cac96d2baa9f11f5e020))

- **agents**: Registra check_landing_sync en la politica anti-drift (§12)
  ([`b79461f`](https://github.com/cortega26/chile-hub/commit/b79461fb1faded29e92673796f41a0a9a408abf0))

- **api**: Documenta y verifica la unica divergencia intencional en normalize_comuna_name
  ([`864ee3f`](https://github.com/cortega26/chile-hub/commit/864ee3f49eedce5abb201d4a6db359e4bcc2e671))

- **ci**: Documenta el job hf-publish en AGENTS.md + badge HF en README
  ([`76f217f`](https://github.com/cortega26/chile-hub/commit/76f217f5a0796e3e56d1363c10a33a304efab840))

- **contributing**: Playbook de contribucion de extractores via carril candidate
  ([`928cec1`](https://github.com/cortega26/chile-hub/commit/928cec1bcfd053356273f8f88a63ce1ade81e922))

- **dist**: Documenta el modo de acceso HTTP estatico
  ([`e8157cb`](https://github.com/cortega26/chile-hub/commit/e8157cb36c549063ca36742c29e1063eab6cbb33))

- **examples**: Add flagship notebook (formatted)
  ([`8cd298c`](https://github.com/cortega26/chile-hub/commit/8cd298c987f4d3416f83faf35143e5a05a2b1b54))

- **landing**: Clarify dual position:sticky usage, scope Plan 056 criterion
  ([`b24d8ac`](https://github.com/cortega26/chile-hub/commit/b24d8ac7ae4b817acbfef9e8a57658771787969d))

- **r**: Quickstart de consumo desde R con arrow y duckdb
  ([`26e8409`](https://github.com/cortega26/chile-hub/commit/26e8409d8d84c4349601599c7f7427f3a95d49ea))

- **readme**: Resincroniza TEST_COUNT (690 -> 697)
  ([`a759e2a`](https://github.com/cortega26/chile-hub/commit/a759e2ad96f9feeb731455fbcb46f0638cd90658))

- **todo**: Registra el cierre de los issues #42, #43 y #44
  ([`020491f`](https://github.com/cortega26/chile-hub/commit/020491fbf9d9603495676a6758d686eb36682e12))

- **validation**: Documenta y verifica la precedencia fallback-vs-anomalia
  ([`62eb17d`](https://github.com/cortega26/chile-hub/commit/62eb17dc9338f7191e349f89d2e2aa99170e8609))

### Agregado

- **api**: Agrega resolve_comunas() para mapear nombres a codigos CUT
  ([`3189cc7`](https://github.com/cortega26/chile-hub/commit/3189cc7f1d144049e023153d121d7ad418a543d2))

- **catalog**: Agrega campo extractor a las 22 entradas del catalogo
  ([`5d4446f`](https://github.com/cortega26/chile-hub/commit/5d4446fdabb4f982b4c86a891c214c6474feed1a))

- **ci**: Adelanta la deteccion de deriva de la landing a cada push/PR
  ([`71e4da3`](https://github.com/cortega26/chile-hub/commit/71e4da3babeeee4b8f9eb89878226b139cfbf919))

- **ci**: Agrega job hf-publish tras release
  ([`13acb16`](https://github.com/cortega26/chile-hub/commit/13acb160569c03e4398d08325ff0cd016a48cd41))

- **ci**: Publica GeoParquet comunal bajo demanda
  ([`b3d7335`](https://github.com/cortega26/chile-hub/commit/b3d7335376d4eb94a53545b34cac163e88ff15eb))

- **ci**: Publica señal de adopción PyPI + GitHub Releases
  ([`91a8b09`](https://github.com/cortega26/chile-hub/commit/91a8b0965a46e6e24f005c8eff5435666c9e28c3))

- **ci**: Rechaza publicacion ante anomalia temporal no revisada
  ([`6bc0415`](https://github.com/cortega26/chile-hub/commit/6bc0415ce2d2b81995c8e9587a2cd1d4b214595c))

- **ci**: Valida extractores en check_companion_paths registry
  ([`603ca1f`](https://github.com/cortega26/chile-hub/commit/603ca1f04a44141baf7f9400579c44f3dba62c70))

- **data**: Promueve autoridades_locales a stable_publishable
  ([`39fc13a`](https://github.com/cortega26/chile-hub/commit/39fc13a581959135ae651100e55e3a8e8a3a093c))

- **dist**: Genera catalogo DCAT data.json
  ([`5e79c3b`](https://github.com/cortega26/chile-hub/commit/5e79c3b43e1892a363c36a92cf4f1092940d118d))

- **dist**: Publica bundle en Hugging Face Hub tras release
  ([`a264b06`](https://github.com/cortega26/chile-hub/commit/a264b06a88692a62abcd1834920293bf5db1032d))

- **doc-sync**: Fase 1 — conteo de datasets en AGENTS.md auto-generado
  ([`4a20a26`](https://github.com/cortega26/chile-hub/commit/4a20a265c765099e43c4dbe71e89c242a9e792bf))

- **doc-sync**: Fase 2 — tabla de tests en AGENTS.md auto-generada
  ([`6a211af`](https://github.com/cortega26/chile-hub/commit/6a211af62ce3bdf2c69f58b10255ac04301253de))

- **doc-sync**: Fase 3 — schema details del README desde contratos
  ([`7a237dd`](https://github.com/cortega26/chile-hub/commit/7a237ddebbc47d43be389dc7ae3442b405e0bbdc))

- **doc-sync**: Fase 4 — lista de extractores en AGENTS.md auto-generada
  ([`f6b643b`](https://github.com/cortega26/chile-hub/commit/f6b643b044cec38e40de33808eb76d3f1b98103d))

- **docs**: Auto-genera tabla de extractores de README
  ([`bbd73cd`](https://github.com/cortega26/chile-hub/commit/bbd73cd294ddda4ea9ff924746263c0eee9d1e75))

- **extractors**: Geometria_comunal_extractor.py — Plan 053 Step 2
  ([`c9009c7`](https://github.com/cortega26/chile-hub/commit/c9009c7b8eaf3d71d633a0fb893fedbee1e230ac))

- **geo**: Validador, writer GeoParquet y registro candidate de geometria_comunal
  ([`56cd9d5`](https://github.com/cortega26/chile-hub/commit/56cd9d58d6ede215348cfaefdf0e7da83bec1871))

- **health**: Excluye fuentes retiradas de la contabilidad de salud
  ([#44](https://github.com/cortega26/chile-hub/pull/44),
  [`7df3ff0`](https://github.com/cortega26/chile-hub/commit/7df3ff00d77766ed516a788e4255cb2f215c88e5))

- **health**: Sincroniza landing, docs y ADR-014 de la taxonomia de drift
  ([`0bdbb04`](https://github.com/cortega26/chile-hub/commit/0bdbb04d6ca45707eac260589422931753be8338))

- **indicadores**: Hace el backfill consciente de la edad
  ([#43](https://github.com/cortega26/chile-hub/pull/43),
  [`9508368`](https://github.com/cortega26/chile-hub/commit/9508368c53416b867d37213d71a87ea2fae644b5))

- **landing**: Add skeleton loading states for catalog and KPIs
  ([`1056d51`](https://github.com/cortega26/chile-hub/commit/1056d51871d99a6b9c8839a6b179a244d8b12575))

- **landing**: Add sticky header with backdrop blur
  ([`660fed8`](https://github.com/cortega26/chile-hub/commit/660fed8aa2f7e187243f3bdc60a60d1bf05df796))

- **landing**: Differentiate section spacing and add visual separators
  ([`794cace`](https://github.com/cortega26/chile-hub/commit/794cace797996d6be7034aa5c12a518c32eaf745))

- **landing**: Explorador SQL DuckDB-Wasm. Closes plan 020. Co-Authored-By: Claude
  <noreply@anthropic.com>
  ([`24145e8`](https://github.com/cortega26/chile-hub/commit/24145e8cd67192de2ed85c68757aabf3b57c4176))

- **landing**: Sparkline de salud historica en dashboard
  ([`f2cca74`](https://github.com/cortega26/chile-hub/commit/f2cca74be4635a7a13db422795e6ea2537fc3831))

- **landing**: Typography overhaul to Inter, JetBrains Mono, and Source Serif 4
  ([`8aa59c9`](https://github.com/cortega26/chile-hub/commit/8aa59c973ef860f58d5761673cae15daad3e493b))

- **pipeline**: Historial append-only de salud del hub (hub_health_history.jsonl)
  ([`be2cc71`](https://github.com/cortega26/chile-hub/commit/be2cc71a5fe4cafc5626d3256efbb0ac7d545483))

- **pipeline**: Propaga anomalias temporales a drift_status
  ([`e823cce`](https://github.com/cortega26/chile-hub/commit/e823cce6a98a3d5a0ce874ae2a6a73258b5d6412))

- **validation**: Detecta anomalias temporales en indicadores
  ([`c3b1723`](https://github.com/cortega26/chile-hub/commit/c3b1723dd3645a66deaea09b613bcb81f01730e7))

### Refactorizado

- **indicadores**: Elimina la copia duplicada del calculo de edades
  ([`215e5be`](https://github.com/cortega26/chile-hub/commit/215e5be39146c7cb345de133f2932bb8c6eedb21))

### Tests

- Agrega tests de registro de extractores y tabla README
  ([`2e26186`](https://github.com/cortega26/chile-hub/commit/2e26186e9572aa22d6c92181d5b5b4687506c805))

- **ci**: Guardrails del job hf-publish
  ([`3c41c9b`](https://github.com/cortega26/chile-hub/commit/3c41c9b1ba23c77c9557dd2a04d945c5f3783746))

- **health**: Cubre la taxonomia de drift esperado vs real
  ([`1d79924`](https://github.com/cortega26/chile-hub/commit/1d79924284731088a63e0427a903ab0b9263e1ad))

- **pipeline**: Tests de append_hub_health_history
  ([`930ac60`](https://github.com/cortega26/chile-hub/commit/930ac60be53fc3ee191f636a8115cd2d604aada4))


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
