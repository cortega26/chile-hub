# Plan 008: Fortalecer la madurez de fuente, los contratos de esquema y las compuertas de calidad

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada
> comando de verificación y confirma el resultado esperado antes de pasar al
> siguiente paso. Si ocurre alguna condición de detención, detente y reporta en
> lugar de improvisar.
>
> **Verificación de desvío (ejecutar primero)**:
> `git diff --stat 4eb79ce..HEAD -- src/build_dev_db.py src/chile_hub/core.py scripts/verify_pipeline.py .github/workflows/pipeline-check.yml Makefile tests/test_chile_hub.py tests/test_pipeline_logic.py`
>
> Si algún archivo dentro del alcance cambió desde que se escribió este plan,
> compara el código actual con este plan antes de proceder. Si las APIs
> relevantes o la estructura de archivos ya no coinciden, trata eso como una
> condición de detención.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: L
- **Riesgo**: MED
- **Depende de**: ninguno
- **Categoría**: direction / architecture / data-quality / dx
- **Planificado en**: commit `4eb79ce`, 2026-06-17
- **Actualización de estado**: 2026-06-18 — dividido en piezas más pequeñas implementadas: `contracts/datasets/*.schema.json`, `data/source_registry.json` y `scripts/verify_pipeline.py` con compuertas de contrato/registry. Los artefactos generados `source_readiness.*` y la propagación más profunda de madurez quedan como trabajo futuro.

## Por qué es importante

`chile-hub` ahora tiene 14 capas activas, incluyendo tres datasets candidatos
respaldados por fuentes que actualmente operan en modo `fallback` honesto. Los
artefactos existentes de salud, desvío, estado y changelog hacen visible esto,
pero el proyecto aún carece de contratos explícitos de madurez de fuente,
estados de madurez del dataset, contratos de esquema, detección de
estancamiento y una separación entre "verde para desarrollo" y "verde para
publicación".

Este plan hace que esos estados sean verificables por máquina. El resultado
deseado es que un PR normal pueda mantenerse en verde con fallbacks declarados,
mientras que las compuertas de publicación y madurez fallen ruidosamente cuando
una fuente está estancada, es solo fallback, tiene desvío de esquema o no está
legal/públicamente lista.

## Estado actual

Implementación actual relevante:

- `src/build_dev_db.py` posee `DATASET_CATALOG_CONFIG`, frescura, cobertura,
  degradación, desvío, `dataset_status.json`, `dataset_changelog.json`,
  catálogo, bundle, manifest e informes generados.
- `scripts/verify_pipeline.py` posee la verificación de artefactos y la
  política de publicación. `--require-live` actualmente requiere que todos los
  datasets tengan `source_mode == "live"` y metadatos frescos.
- `.github/workflows/pipeline-check.yml` tiene una ruta de build-and-test y
  pasa `--require-live` solo para builds programados o de publicación.
- `src/chile_hub/core.py` ya expone `dataset_status()` y `dataset_changelog()`.
- Las capas candidatas actuales con fallback son `finanzas_municipales`,
  `resultados_educacionales` e `indicadores_urbanos_siedu`.

Comportamiento actual clave a preservar:

- `make verify` debe seguir siendo la compuerta normal para desarrolladores y
  permitir datasets con fallback declarados y validados.
- `make verify-live` debe seguir siendo estricto y orientado a publicación.
- `data/normalized/` debe ser regenerado por `make build`; nunca editar
  manualmente los artefactos generados.
- Las funciones `validate_*()` existentes en `src/validation.py` siguen siendo
  validadores semánticos; los contratos de esquema agregados por este plan son
  contratos estructurales.

## Alcance

Dentro del alcance:

- `src/build_dev_db.py`
- `src/chile_hub/core.py`
- `scripts/verify_pipeline.py`
- `.github/workflows/pipeline-check.yml`
- `Makefile`
- `tests/test_chile_hub.py`
- `tests/test_pipeline_logic.py`
- nuevo `data/source_registry.yml`
- nuevos `contracts/datasets/*.schema.json`
- nuevo `docs/dataset-compatibility-policy.md`
- salidas generadas `data/normalized/*` de `make build`

Fuera del alcance:

- Reemplazar las implementaciones fallback de SINIM, resultados MINEDUC o SIEDU
  con extractores live verdaderos. Este plan debe hacer visible y exigible esa
  deuda, no resolver el descubrimiento upstream.
- Eliminar o renombrar columnas públicas de datasets.
- Reescribir todos los extractores en torno a un nuevo adaptador en un solo
  paso.
- Cambiar la versión del paquete a menos que el mantenedor solicite
  explícitamente un bump de versión después de la implementación.

## Comandos que necesitarás

| Propósito | Comando | Esperado en caso de éxito |
|---|---|---|
| Extracción | `make extract` | sale con 0 |
| Build | `make build` | sale con 0 y regenera artefactos normalizados |
| Verify de desarrollo | `make verify` | sale con 0 |
| Tests | `make test` | todos los tests pasan |
| Landing | `make verify-landing` | sale con 0 |
| Lint | `make lint` | sale con 0 |
| Formato | `make format-check` | sale con 0 |
| Verify de publicación | `make verify-live` | falla hasta que las capas candidatas con fallback estén en live; la falla debe ser precisa |

## Pasos de implementación

### Paso 1: Agregar madurez del dataset y madurez de fuente al catálogo

Extiende cada entrada de dataset en `DATASET_CATALOG_CONFIG` con:

```python
"maturity": {
    "status": "stable | candidate | experimental | deprecated",
    "since_version": "1.1.0",
    "owner": "core",
    "notes": "...",
},
"source_readiness": {
    "live_ready": True | False,
    "fallback_allowed": True | False,
    "publish_blocking": True | False,
    "source_contract_url": "...",
    "last_live_success_required": True | False,
    "stalled_after_days": 30,
    "review_by": "YYYY-MM-DD",
    "next_action": "...",
},
```

Valores iniciales:

- `stable`: regiones, provincias, comunas, comunas_enriquecidas, indicadores,
  censo_comunal, censo_hogares_viviendas, establecimientos_salud,
  distritos_electorales, establecimientos_educacionales.
- `candidate`: finanzas_municipales, resultados_educacionales,
  indicadores_urbanos_siedu.
- `stable`: perfil_territorial_comunal, con notas de que la madurez se hereda
  de datasets upstream.
- Los datasets candidatos respaldados por fuente con fallback deben tener
  `live_ready=False`, `fallback_allowed=True`, `publish_blocking=True` y un
  `next_action` concreto.
- Los datasets estables en live deben tener `live_ready=True`,
  `fallback_allowed=True` solo si el extractor actual ya soporta fallback,
  y `publish_blocking=True` cuando el fallback sería inseguro para publicación.

Propaga estos campos en los metadatos/salidas del catálogo:

- `pipeline_metadata.json`
- `dataset_catalog.json`
- `dataset_status.json`
- `hub_bundle.json`

**Verificar**: `make build && make verify` sale con 0.

### Paso 2: Agregar un registry de fuentes verificado

Crea `data/source_registry.yml` con una entrada por dataset:

```yaml
- source_id: sinim_finanzas_municipales
  dataset: finanzas_municipales
  source_name: SINIM - SUBDERE
  official_url: https://datos.sinim.gov.cl/datos_municipales.php
  access_method: landing_snapshot
  license_status: public-api-review-terms
  live_extractor_status: fallback_only
  fallback_policy: allowed_for_dev_blocked_for_publication
  owner: core
  next_action: Configurar exportación estable directa de SINIM y reemplazar filas fallback curadas.
  review_by: "2026-07-17"
```

Valores enum permitidos:

- `access_method`: `api`, `direct_file`, `landing_snapshot`, `derived`
- `license_status`: `open-attribution`, `public-api-review-terms`, `restricted`
- `live_extractor_status`: `implemented`, `fallback_only`, `derived`
- `fallback_policy`: `none`, `allowed_for_dev`, `allowed_for_dev_blocked_for_publication`

Agrega un cargador de registry a `scripts/verify_pipeline.py`. Usa un
analizador YAML mínimo solo si ya existe una dependencia; de lo contrario,
usa sintaxis YAML compatible con JSON y analiza con un pequeño analizador
local o cambia a `data/source_registry.json`. Prefiere no agregar una nueva
dependencia en tiempo de ejecución a menos que el repositorio ya tenga
soporte YAML.

Reglas de validación:

- cada dataset del catálogo aparece exactamente una vez
- cada dataset del registry existe en `DATASET_CATALOG_CONFIG`
- `license_status` es igual a `reuse_policy.status` del catálogo
- `live_extractor_status=fallback_only` requiere `source_readiness.live_ready=False`
- los datasets respaldados por fuente con `fallback_only` requieren `source_readiness.publish_blocking=True`
- los datasets `derived` requieren `access_method=derived`

**Verificar**: agrega tests en `tests/test_pipeline_logic.py` para éxito,
dataset faltante, dataset duplicado y fallo de enum.

### Paso 3: Agregar contratos de esquema

Crea:

```text
contracts/datasets/<dataset>.schema.json
```

Un contrato por dataset. Cada contrato debe incluir:

```json
{
  "dataset": "comunas",
  "primary_key": ["codigo_comuna"],
  "required_columns": ["codigo_comuna", "nombre_comuna"],
  "column_types": {
    "codigo_comuna": "string",
    "nombre_comuna": "string"
  },
  "nullable_columns": [],
  "fixed_width_columns": {
    "codigo_comuna": 5,
    "codigo_region": 2,
    "codigo_provincia": 3
  },
  "expected_record_count": 346,
  "coverage_policy": "full | partial_expected | not_applicable",
  "publish_outputs": ["parquet", "json"]
}
```

La verificación de contratos en `scripts/verify_pipeline.py` debe:

- cargar cada salida Parquet del dataset
- confirmar que las columnas requeridas existen
- confirmar que la clave primaria declarada es única
- confirmar que las columnas CUT de ancho fijo son strings y tienen el largo esperado
- confirmar `expected_record_count` solo cuando `coverage_policy=full`
- permitir cobertura parcial de SIEDU solo cuando `coverage_policy=partial_expected`
- confirmar que las salidas de publicación esperadas existen en el catálogo y el sistema de archivos

Mantén Polars como lector porque el proyecto ya depende de él.

**Verificar**: agrega tests para columna requerida faltante, clave primaria
duplicada, ancho CUT inválido y cobertura parcial permitida solo para SIEDU.

### Paso 4: Generar artefactos de madurez de fuente

Genera a partir del catálogo + registry + metadatos actuales:

```text
data/normalized/source_readiness.json
data/normalized/source_readiness.md
```

Cada entrada de dataset debe incluir:

- dataset
- estado de madurez
- source id
- source mode
- preparación para live
- fallback permitido
- bloqueo de publicación
- estado del extractor live
- URL del contrato de fuente
- estado de estancamiento
- review_by
- next_action
- recommended_action

Registra ambos artefactos en:

- manifest de artefactos compartidos
- índice de informes del hub bundle
- archivos requeridos del verificador

Agrega API/CLI pública:

```python
hub.source_readiness()
```

```bash
chile-hub source-readiness
```

**Verificar**: `chile-hub source-readiness` devuelve los 14 datasets.

### Paso 5: Generar tarjeta de puntuación de calidad del dataset

Genera:

```text
data/normalized/dataset_quality.json
data/normalized/dataset_quality.md
```

Dimensiones de puntuación:

- `validation`: 0 o 100
- `schema_contract`: 0 o 100
- `source_readiness`: 0, 50 o 100
- `freshness`: 0, 50 o 100
- `coverage`: 0, 70 o 100
- `reuse_policy`: 0, 50 o 100

Ponderaciones:

- validation: 25
- schema_contract: 20
- source_readiness: 20
- freshness: 15
- coverage: 10
- reuse_policy: 10

Cada entrada de dataset debe incluir:

- puntuaciones por dimensión
- `overall_score`
- `grade`: `A`, `B`, `C`, `D` o `F`
- `blocking_reasons`
- `recommended_action`

Resultado inicial esperado:

- los datasets estables en live obtienen puntuación más alta que los datasets candidatos con fallback
- los datasets candidatos con fallback tienen bloqueadores explícitos de madurez de fuente
- perfil_territorial_comunal incluye advertencias de madurez upstream cuando los upstreams son fallback

Registra los artefactos JSON/Markdown en manifest, bundle, informes y verificador.

Agrega API/CLI pública:

```python
hub.dataset_quality()
```

```bash
chile-hub dataset-quality
```

**Verificar**: los tests afirman que aparecen los 14 datasets y que los
datasets candidatos con fallback obtienen puntuación menor que los datasets
estables en live.

### Paso 6: Separar perfiles de verificación

Actualiza la CLI de `scripts/verify_pipeline.py`:

```bash
python scripts/verify_pipeline.py --profile dev
python scripts/verify_pipeline.py --profile readiness
python scripts/verify_pipeline.py --profile publication
```

Reglas:

- `dev`: comportamiento actual de `make verify`; se permite fallback cuando está declarado y es válido.
- `readiness`: valida registry de fuentes, madurez, preparación, contratos de esquema, política de estancamiento y artefactos de calidad.
- `publication`: equivalente al estricto `--require-live` actual, más madurez de fuente y contratos de esquema. Rechaza datasets respaldados por fuente con fallback a menos que se excluyan explícitamente del bundle publicable.

Preserva la compatibilidad hacia atrás:

- `--require-live` sigue siendo compatible y se asigna a `--profile publication`.
- ningún perfil por defecto es `dev`.

Actualiza el Makefile:

```make
verify-dev:
	$(PYTHON) scripts/verify_pipeline.py --profile dev

verify-readiness:
	$(PYTHON) scripts/verify_pipeline.py --profile readiness

verify-publication:
	$(PYTHON) scripts/verify_pipeline.py --profile publication

verify:
	$(PYTHON) scripts/verify_pipeline.py --profile dev

verify-live:
	$(PYTHON) scripts/verify_pipeline.py --profile publication
```

Actualiza CI:

- el build de PR usa dev + readiness.
- el build programado/de publicación usa publication.
- el resumen del job incluye la madurez de fuente y la tarjeta de calidad en Markdown.

**Verificar**:

- `make verify` pasa.
- `make verify-readiness` pasa con valores iniciales de `review_by` futuros.
- `make verify-live` falla mientras las capas candidatas son fallback, con mensajes de bloqueo precisos.

### Paso 7: Agregar detección de estancamiento

Usa `review_by` y `stalled_after_days` de `source_readiness` / registry.

Reglas:

- `experimental`: el estancamiento emite una advertencia.
- `candidate`: el estancamiento hace fallar `verify-readiness`.
- `stable`: una regresión en madurez de fuente hace fallar `verify-readiness`.
- los datasets derivados pueden marcarse como estancados solo por bloqueadores upstream.

Usa la fecha actual en tiempo de ejecución. Los tests deben inyectar o
ajustar la fecha para evitar fallos dependientes del tiempo.

**Verificar**: los tests cubren candidato no estancado, candidato estancado,
advertencia de estancamiento experimental y fallo por regresión estable.

### Paso 8: Agregar política de compatibilidad de datasets y severidad de changelog

Crea:

```text
docs/dataset-compatibility-policy.md
```

Política:

- agregar un dataset: versión minor
- agregar columnas anulables: versión minor
- eliminar columnas: versión major
- renombrar columnas: versión major
- cambiar claves primarias: versión major
- cambiar el tipo de columna de forma incompatible: versión major
- cambiar metadatos o campos solo de informe: patch o minor según visibilidad
- deprecar un dataset requiere al menos un aviso en una versión minor

Extiende `dataset_changelog.json` con:

- `change_severity`: `none | patch | minor | major`
- `breaking_changes`
- `new_columns`
- `removed_columns`
- `primary_key_changed`
- `contract_changed`

Usa los contratos de esquema para clasificar los cambios. Si no existe un
contrato previo, clasifica como `minor` para dataset nuevo.

**Verificar**: los tests cubren columna anulable agregada, columna eliminada,
cambio de clave primaria y severidad de dataset nuevo.

### Paso 9: Fundación opcional de adaptador de fuente

Agrega:

```text
src/extractors/source_adapter.py
```

Incluye solo helpers reutilizables:

- `fetch_url_snapshot(url, raw_prefix, timeout)`
- `build_standard_metadata(...)`
- `fallback_metadata_note(...)`
- `source_mode_from_live_success(...)`

Úsalo solo en los tres extractores candidatos por ahora:

- `sinim_finanzas_extractor.py`
- `mineduc_resultados_extractor.py`
- `siedu_extractor.py`

No reescribas extractores estables en este plan.

**Verificar**: los tests de extractores continúan pasando; agrega tests
enfocados para la salida de los helpers.

## Interfaces públicas y artefactos

Nuevos archivos controlados por versión:

- `data/source_registry.yml` o `data/source_registry.json`
- `contracts/datasets/*.schema.json`
- `docs/dataset-compatibility-policy.md`

Nuevos artefactos generados:

- `data/normalized/source_readiness.json`
- `data/normalized/source_readiness.md`
- `data/normalized/dataset_quality.json`
- `data/normalized/dataset_quality.md`

Nuevos métodos de API:

- `ChileHub.source_readiness()`
- `ChileHub.dataset_quality()`

Nuevos comandos CLI:

- `chile-hub source-readiness`
- `chile-hub dataset-quality`

Nuevas claves de informe del hub bundle:

- `source_readiness_json`
- `source_readiness_markdown`
- `dataset_quality_json`
- `dataset_quality_markdown`

## Plan de pruebas

Agrega o actualiza tests en `tests/test_pipeline_logic.py`:

- las entradas del catálogo requieren `maturity` y `source_readiness`
- el registry de fuentes valida todos los datasets exactamente una vez
- un enum inválido del registry falla
- un dataset solo con fallback sin bloqueador de publicación falla readiness
- el contrato de esquema detecta columna requerida faltante
- el contrato de esquema detecta clave primaria duplicada
- el contrato de esquema detecta ancho CUT inválido
- la cobertura parcial de SIEDU pasa solo con `partial_expected`
- las calificaciones de calidad colocan a los candidatos con fallback por debajo de los datasets estables en live
- el perfil dev permite datasets con fallback declarados
- el perfil readiness detecta candidatos estancados
- el perfil publication rechaza datasets respaldados por fuente con fallback

Agrega o actualiza tests en `tests/test_chile_hub.py`:

- `hub.dataset_quality()` devuelve los 14 datasets
- `hub.source_readiness()` devuelve los 14 datasets
- el índice de informes incluye artefactos de calidad/madurez
- el manifest de artefactos incluye los nuevos artefactos compartidos JSON/Markdown
- tests smoke de CLI para `dataset-quality` y `source-readiness`

Agrega o actualiza `scripts/verify_landing.py` solo si la página de landing
muestra los nuevos informes de calidad/madurez. Si no se muestran, no se
requiere cambio en la UI de landing.

Verificación final:

```bash
make extract
make build
make verify
make verify-readiness
make test
make verify-landing
make lint
make format-check
make verify-live
```

Esperado:

- todos los comandos pasan excepto `make verify-live`
- `make verify-live` falla hasta que las capas candidatas con fallback sean fuentes live verdaderas
- la falla de `make verify-live` nombra los datasets exactos y los bloqueadores de madurez de fuente

## Criterios de finalización

- [ ] Cada dataset tiene `maturity` y `source_readiness` en el catálogo/config.
- [ ] Cada dataset tiene una entrada en el registry de fuentes.
- [ ] Cada dataset tiene un contrato de esquema.
- [ ] `dataset_quality` y `source_readiness` se generan y exponen en API,
      CLI, bundle, manifest y verificador.
- [ ] La verificación de desarrollo sigue en verde con fallbacks declarados.
- [ ] La verificación de madurez evita que el trabajo de fuentes candidatas
      estancadas quede en el olvido.
- [ ] La verificación de publicación falla ruidosa y precisamente mientras
      las capas candidatas sean fallback.
- [ ] Los tests cubren registry, madurez, contratos, puntuación, CLI/API y
      perfiles.
- [ ] Ningún artefacto normalizado generado se edita manualmente.

## Condiciones de detención

Detente y reporta si:

- Agregar el registry de fuentes requiere una dependencia no fijada.
- La validación de contratos requiere cambiar esquemas públicos de datasets.
- `make verify` no puede mantenerse en verde mientras los datasets con
  fallback declarados son válidos.
- `make verify-live` comienza a pasar mientras los datasets candidatos
  respaldados por fuente aún tienen `source_mode=fallback`.
- Alguna implementación requiere eliminar o renombrar un dataset público o
  una columna pública existente.

## Notas de mantenimiento

- Trata la madurez de fuente y los contratos de esquema como parte del
  contrato operativo público. Los revisores deben rechazar nuevos datasets
  que no incluyan entradas de registry, madurez, preparación y contrato de
  esquema.
- Mantén los perfiles `dev`, `readiness` y `publication` conceptualmente
  distintos. Difuminarlos recreará el problema original de "verde pero no
  publicable".
- Una vez que SINIM, resultados MINEDUC y SIEDU tengan extractores live
  verdaderos, actualiza sus entradas de registry y bloqueos de madurez de
  fuente en el mismo PR que el cambio del extractor.
