# Plan 009: Separar carriles de conjuntos de datos estables publicables y candidatos

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada
> comando de verificación y confirma el resultado esperado antes de pasar al siguiente
> paso. Si ocurre algo de lo indicado en la sección "Condiciones de detención", detente
> e informa en lugar de improvisar. Cuando termines, actualiza la fila de estado de este
> plan en `plans/README.md`.
>
> **Verificación de desvío (ejecutar primero)**:
> `git diff --stat 91d3caa..HEAD -- data/source_registry.json scripts/verify_pipeline.py src/build_dev_db.py tests/test_pipeline_logic.py tests/test_chile_hub.py Makefile plans/README.md`
>
> Si algún archivo de implementación dentro del alcance cambió desde que se escribió
> este plan, compara los extractos del "Estado actual" con el código en vivo antes de
> proceder. Si las APIs relevantes o la estructura de archivos ya no coinciden,
> considéralo una condición de detención.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: M
- **Riesgo**: MED
- **Depende de**: partes implementadas de `plans/008-hardening-source-readiness-schema-contracts-quality.md` (`data/source_registry.json`, contratos de esquema y verificación del registro ya existen en el commit `91d3caa`)
- **Categoría**: data-quality / architecture / dx
- **Planificado en**: commit `91d3caa`, 2026-06-18

## Por qué es importante

`make verify-live` actualmente trata cada conjunto de datos del catálogo como si debiera
estar listo para producción. Eso es demasiado rígido: o bloquea todo el proyecto por
capas candidatas conocidas, o tienta a los mantenedores a bajar el estándar de
publicación. No bajes el estándar.

La solución profesional es hacer explícita la madurez de los conjuntos de datos. Los
conjuntos de datos estables publicables deben estar en vivo, frescos y seguros para su
publicación. Los conjuntos de datos candidatos pueden existir en compilaciones
locales/de desarrollo y en la documentación, pero deben excluirse del ZIP público y no
deben representarse como listos para producción hasta que sus extractores en vivo sean
estables.

Este plan implementa esa separación primero. Intencionalmente no "perdona"
a `indicadores` cuando usa `raw_recovery` inseguro; un conjunto de datos de indicadores
estable publicable debe seguir cumpliendo las reglas estrictas existentes: entrega en
vivo o un `published_backfill` explícitamente permitido, nunca recuperación en crudo en
una compilación de publicación.

## Estado actual

El modo de fallo actual a abordar:

- `finanzas_municipales` está en `source_mode=fallback`.
- `resultados_educacionales` está en `source_mode=fallback`.
- `indicadores_urbanos_siedu` está en `source_mode=fallback`.
- `perfil_territorial_comunal` es derivado y hereda el peor estado upstream,
  por lo que también se vuelve fallback mientras dependa de capas candidatas en
  fallback.
- `indicadores` puede fallar la publicación estricta cuando `mindicador.cl` agota el
  tiempo de espera y UF u otro código se completa mediante `raw_recovery`.

Archivos importantes existentes:

- `data/source_registry.json` declara la preparación actual de las fuentes. Ya marca
  `finanzas_municipales`, `resultados_educacionales`,
  `indicadores_urbanos_siedu` y `perfil_territorial_comunal` como
  `maturity_status="candidate"` y `live_ready=false`.
- `scripts/verify_pipeline.py` valida el registro de fuentes e implementa
  `verify_publication_policy()`.
- `src/build_dev_db.py` construye el manifiesto de artefactos, el ZIP público, el
  paquete hub y los artefactos generados de catálogo/estado.
- `tests/test_pipeline_logic.py` tiene pruebas unitarias enfocadas en la política de
  publicación y el comportamiento del registro de fuentes.
- `tests/test_chile_hub.py` tiene aserciones de integración para el manifiesto, ZIP,
  paquete, CLI y comportamiento del Makefile.

Extractos actuales del registro de fuentes:

```text
data/source_registry.json:163-176
{
  "source_id": "sinim_finanzas_municipales",
  "dataset": "finanzas_municipales",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Configure stable direct SINIM export and replace curated fallback rows."
}

data/source_registry.json:179-192
{
  "source_id": "mineduc_resultados_educacionales",
  "dataset": "resultados_educacionales",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Replace curated fallback with stable official aggregate export."
}

data/source_registry.json:195-208
{
  "source_id": "ine_siedu_indicadores",
  "dataset": "indicadores_urbanos_siedu",
  "live_extractor_status": "fallback_only",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Replace partial fallback with stable official SIEDU export."
}

data/source_registry.json:211-224
{
  "source_id": "chile_hub_perfil_territorial",
  "dataset": "perfil_territorial_comunal",
  "access_method": "derived",
  "live_extractor_status": "derived",
  "fallback_policy": "allowed_for_dev_blocked_for_publication",
  "maturity_status": "candidate",
  "live_ready": false,
  "fallback_allowed": true,
  "publish_blocking": true,
  "next_action": "Track readiness inherited from upstream component datasets."
}
```

Extracto de la política estricta actual:

```text
scripts/verify_pipeline.py:266-309
def verify_publication_policy(metadata=None):
    if metadata is None:
        metadata = load_json(NORMALIZED_DIR / "pipeline_metadata.json")

    violations = []
    for dataset_name in sorted(REQUIRED_DATASETS):
        dataset = metadata.get("datasets", {}).get(dataset_name, {})
        freshness = dataset.get("freshness", {})
        if dataset.get("source_mode") != "live":
            violations.append(f"{dataset_name}: source_mode={dataset.get('source_mode')}")
        if freshness.get("status") != "fresh":
            violations.append(f"{dataset_name}: freshness={freshness.get('status')}")

    indicadores = metadata.get("datasets", {}).get("indicadores", {})
    allowed_indicator_source_details = {
        "public_api",
        "public_api_with_published_backfill",
    }
    if indicadores.get("source_detail") not in allowed_indicator_source_details:
        violations.append(f"indicadores: source_detail={indicadores.get('source_detail')}")
    failed_diagnostics = {
        field: indicadores.get(field, [])
        for field in (
            "fetch_failures",
            "raw_recoveries",
            "preserved_existing_pairs",
            "empty_live_pairs",
        )
        if indicadores.get(field)
    }
    if failed_diagnostics:
        violations.append(f"indicadores: recovery diagnostics={failed_diagnostics}")
```

Comportamiento actual del paquete/manifiesto:

```text
src/build_dev_db.py:887-1009
def build_publishable_artifact_index():
    artifact_index = {}
    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        outputs = config.get("outputs", {})
        for output_type, path in outputs.items():
            if isinstance(path, str) and path.startswith("data/normalized/"):
                artifact_index[path] = {
                    "dataset": dataset_name,
                    "output_type": output_type,
                }
...
def write_artifact_manifest():
    artifact_index = build_publishable_artifact_index()
    artifacts = []
    for filename in sorted(os.listdir(NORMALIZED_DIR)):
        if not filename.endswith(PUBLISHABLE_ARTIFACT_SUFFIXES):
            continue
...
        artifacts.append(
            {
                "path": relative_path,
                "dataset": artifact_metadata.get("dataset"),
                "output_type": artifact_metadata.get("output_type"),
                "shared_type": artifact_metadata.get("shared_type"),
                "format": artifact_metadata.get("format"),
                "size_bytes": os.path.getsize(path),
                "sha256": compute_sha256(path),
            }
        )
```

```text
src/build_dev_db.py:1430-1460
for dataset in dataset_catalog.get("datasets", []):
    dataset_name = dataset["dataset"]
    dataset_health = health_by_dataset.get(dataset_name, {})
    bundle["datasets"].append(
        {
            "dataset": dataset_name,
            ...
            "publishability_status": dataset_health.get("publishability_status"),
            "outputs": dataset.get("outputs", {}),
            "usage_examples": dataset.get("usage_examples", {}),
            "artifacts": artifacts_by_dataset.get(dataset_name, []),
        }
    )
```

Esto significa que la lista de artefactos públicos y el paquete público están
actualmente impulsados por archivos generados y salidas del catálogo, no por un carril
de publicación explícito.

## Comandos que necesitarás

| Propósito | Comando | Esperado en caso de éxito |
|---|---|---|
| Construir artefactos | `make build` | sale con 0; regenera `data/normalized/*` |
| Verificación de desarrollo | `make verify` | sale con 0; permite capas candidatas declaradas en fallback |
| Pruebas enfocadas | `make test` | todas las pruebas pasan |
| Lint | `make lint` | sale con 0 |
| Verificación de formato | `make format-check` | sale con 0 |
| Validación estricta de publicación | `make verify-live` | sale con 0 solo cuando todos los conjuntos de datos `stable_publishable` están en vivo/frescos y `indicadores` no tiene diagnósticos de recuperación inseguros |
| Suma de verificación del paquete | `shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256` | imprime `OK` |

Si `make verify-live` falla solo porque `indicadores` usó `raw_recovery` después
de un tiempo de espera transitorio de `mindicador.cl`, esa es una falla estricta
correcta. No la relajes en este plan.

## Alcance

**Dentro del alcance**:

- `data/source_registry.json`
- `scripts/verify_pipeline.py`
- `src/build_dev_db.py`
- `tests/test_pipeline_logic.py`
- `tests/test_chile_hub.py`
- artefactos generados en `data/normalized/*` producidos por `make build`
- actualización del estado en `plans/README.md` después de la ejecución

**Fuera del alcance**:

- Reemplazar los extractores en fallback de SINIM, resultados MINEDUC o SIEDU con
  extractores en vivo estables.
- Promover cualquier conjunto de datos candidato a público/estable sin un extractor en
  vivo real y una ejecución exitosa reciente.
- Permitir `raw_recovery`, `preserved_existing`, `empty_live` o entrega parcial de
  indicadores en la publicación estricta.
- Renombrar IDs de conjuntos de datos o eliminar conjuntos de datos candidatos de las
  salidas locales/de desarrollo.
- Cambiar esquemas de respuesta pública no relacionados con la preparación para la
  publicación.
- Reducir las expectativas de `make verify-live` para lograr una compilación verde.

## Flujo de trabajo en Git

- Rama: `advisor/009-split-stable-publishable-candidate-tracks`
- El estilo de commits en la historia reciente es conventional commits, por ejemplo
  `feat: improve hub usability and validation gates`. Usa un solo commit como
  `feat: split publishable and candidate dataset tracks` a menos que el operador
  solicite commits más pequeños.
- No hagas push ni abras un PR a menos que el operador lo indique explícitamente.

## Pasos

### Paso 1: Agregar campos explícitos de carril de publicación a `data/source_registry.json`

Agrega dos campos a cada entrada del registro:

```json
"publication_track": "stable_publishable",
"public_bundle_eligible": true
```

Valores permitidos:

- `publication_track`: `stable_publishable` o `candidate`
- `public_bundle_eligible`: booleano

Valores iniciales:

| Conjunto de datos | publication_track | public_bundle_eligible | Razón |
|---|---|---|---:|---|
| `regiones` | `stable_publishable` | `true` | fuente BCN en vivo estable |
| `provincias` | `stable_publishable` | `true` | fuente BCN en vivo estable |
| `comunas` | `stable_publishable` | `true` | fuente de referencia BCN + INE en vivo estable |
| `comunas_enriquecidas` | `stable_publishable` | `true` | derivado de `comunas` estable |
| `indicadores` | `stable_publishable` | `true` | fuente estable, pero la política estricta debe seguir rechazando recuperación insegura |
| `censo_comunal` | `stable_publishable` | `true` | fuente oficial directa estable |
| `censo_hogares_viviendas` | `stable_publishable` | `true` | fuente oficial directa estable |
| `establecimientos_salud` | `stable_publishable` | `true` | fuente directa estable; fallback bloqueado para publicación |
| `distritos_electorales` | `stable_publishable` | `true` | fuente de referencia legal estable |
| `establecimientos_educacionales` | `stable_publishable` | `true` | fuente oficial estable; fallback bloqueado para publicación |
| `empresas` | `stable_publishable` | `true` | fuente oficial estable de datos.gob.cl |
| `finanzas_municipales` | `candidate` | `false` | candidato SINIM solo con fallback |
| `resultados_educacionales` | `candidate` | `false` | candidato MINEDUC de resultados solo con fallback |
| `indicadores_urbanos_siedu` | `candidate` | `false` | candidato SIEDU solo con fallback/parcial |
| `perfil_territorial_comunal` | `candidate` | `false` | capa derivada que hereda upstreams no publicables |

Para `perfil_territorial_comunal`, agrega también:

```json
"upstream_datasets": [
  "comunas",
  "censo_comunal",
  "censo_hogares_viviendas",
  "establecimientos_salud",
  "establecimientos_educacionales",
  "distritos_electorales",
  "finanzas_municipales",
  "resultados_educacionales",
  "indicadores_urbanos_siedu"
]
```

No uses `maturity_status="stable"` para `perfil_territorial_comunal` hasta que todos
los conjuntos de datos candidatos upstream de los que depende sean promovibles.

**Verificar**: `python -m json.tool data/source_registry.json >/tmp/source_registry.check` sale con 0.

### Paso 2: Fortalecer la verificación del registro

Actualiza `verify_source_registry()` en `scripts/verify_pipeline.py` para validar los
nuevos campos.

Reglas:

- Cada entrada del registro debe tener `publication_track` y
  `public_bundle_eligible`.
- `publication_track` debe ser `stable_publishable` o `candidate`.
- `public_bundle_eligible` debe ser un booleano.
- `publication_track="stable_publishable"` requiere:
  - `public_bundle_eligible is True`
  - `maturity_status == "stable"`
  - `live_ready is True`
  - `live_extractor_status != "fallback_only"`
- `publication_track="candidate"` requiere:
  - `public_bundle_eligible is False`
  - `maturity_status == "candidate"` a menos que el conjunto de datos esté
    explícitamente marcado como `experimental` o `deprecated`
  - `fallback_policy == "allowed_for_dev_blocked_for_publication"` cuando
    `fallback_allowed is True`
- `live_extractor_status="fallback_only"` siempre debe implicar
  `publication_track="candidate"` y `public_bundle_eligible is False`.
- Las entradas con `access_method="derived"` que tengan `upstream_datasets` deben
  heredar el estado no publicable: si alguna entrada del registro upstream es
  candidata o tiene `public_bundle_eligible=false`, el conjunto de datos derivado
  también debe ser candidato y no elegible.
- Ningún candidato respaldado por una fuente puede ser publicable solo porque su
  compilación actual resultó estar fresca.

Agrega pruebas en `tests/test_pipeline_logic.py`:

- Aceptar una entrada mínima de registro estable publicable.
- Aceptar una entrada de registro candidata solo con fallback.
- Rechazar una entrada `fallback_only` con `publication_track="stable_publishable"`.
- Rechazar una entrada candidata con `public_bundle_eligible=true`.
- Rechazar una entrada derivada cuyo upstream es candidato pero cuyo propio carril es
  `stable_publishable`.

Modela estas pruebas siguiendo las pruebas existentes del registro de fuentes en
`tests/test_pipeline_logic.py:230-293`.

**Verificar**: `make test` sale con 0.

### Paso 3: Hacer que la política de publicación use el registro/carril de preparación

Cambia `verify_publication_policy()` para que evalúe solo los conjuntos de datos
estables publicables para los requisitos estrictos de vivo/fresco, al mismo tiempo
que exige que los conjuntos de datos candidatos no estén presentes en el paquete
público.

Forma recomendada:

```python
def stable_publishable_dataset_names(registry):
    return {
        entry["dataset"]
        for entry in registry
        if entry.get("publication_track") == "stable_publishable"
        and entry.get("public_bundle_eligible") is True
    }
```

Luego:

- Carga `data/source_registry.json` cuando se llame a `verify_publication_policy()`
  sin datos de prueba inyectados.
- Permite que las pruebas inyecten un argumento de registro, por ejemplo,
  `verify_publication_policy(metadata, registry=registry, manifest=manifest)`.
- Para cada conjunto de datos estable publicable, requiere:
  - que existan metadatos
  - `source_mode == "live"`
  - `freshness.status == "fresh"`
  - si el `fallback_policy` del registro es
    `allowed_for_dev_blocked_for_publication`, cualquier metadato de fallback actual
    sigue siendo una violación
- Para cada conjunto de datos candidato, no requieras vivo/fresco en `verify-live`,
  pero exige que esté ausente de la lista de artefactos del manifiesto/ZIP público si
  hay un manifiesto disponible.
- Mantén las verificaciones estrictas existentes de `indicadores` para:
  - `source_detail` en `{"public_api", "public_api_with_published_backfill"}`
  - `fetch_failures` vacío
  - `raw_recoveries` vacío
  - `preserved_existing_pairs` vacío
  - `empty_live_pairs` vacío
  - cada valor de `indicator_delivery` en `{"live", "published_backfill"}`
- Aplica las verificaciones estrictas de `indicadores` solo mientras `indicadores`
  esté en el carril `stable_publishable`. Debe permanecer en ese carril en este plan.

Actualiza o reemplaza las pruebas actuales de política de publicación en
`tests/test_pipeline_logic.py:100-160`:

- Los metadatos de vivo/fresco estables publicables pasan.
- Los metadatos de fallback candidatos pasan la política solo cuando los artefactos
  candidatos están ausentes del manifiesto inyectado.
- Los metadatos de fallback candidatos fallan la política cuando su artefacto aparece
  en el manifiesto inyectado.
- Un conjunto de datos estable publicable en fallback sigue fallando.
- `indicadores` con `raw_recoveries` sigue fallando incluso si todos los conjuntos de
  datos candidatos están excluidos.

**Verificar**: `make test` sale con 0.

### Paso 4: Excluir artefactos de conjuntos de datos candidatos del manifiesto público y del ZIP

Actualiza `src/build_dev_db.py` para que `write_artifact_manifest()` incluya
artefactos de conjuntos de datos solo cuando su entrada en el registro tenga
`public_bundle_eligible=true`.

Orientación para la implementación:

- Agrega un cargador/helper pequeño en `src/build_dev_db.py`, o reutiliza un cargador
  JSON existente si lo hay, para leer `data/source_registry.json`.
- Construye una búsqueda por conjunto de datos:

```python
registry_by_dataset = {
    entry["dataset"]: entry
    for entry in load_source_registry()
}
```

- Al construir el índice de artefactos, anota los artefactos de conjuntos de datos con:
  - `publication_track`
  - `public_bundle_eligible`
- Al escribir el manifiesto, omite los artefactos de conjuntos de datos candidatos. No
  omitas informes compartidos como `dataset_catalog.json`, `hub_health.json` o
  `provenance_report.json`; esos informes pueden mencionar candidatos, pero los
  archivos de datos de candidatos no deben empaquetarse como artefactos de producción.
- Evita incluir accidentalmente archivos de conjuntos de datos desconocidos como
  artefactos compartidos. Si un archivo `data/normalized/*` tiene un sufijo
  publicable y parece ser una salida de conjunto de datos pero no está en el índice
  de artefactos, falla de forma ruidosa o exclúyelo con una advertencia. No
  empaquetes silenciosamente archivos de conjuntos de datos no clasificados.

El ZIP público generado se crea a partir de `artifact_manifest.json` en
`src/build_dev_db.py:1468-1505`, por lo que una vez que el manifiesto excluya los
artefactos de datos candidatos, el ZIP debería excluirlos automáticamente.

Pruebas para agregar o actualizar:

- En `tests/test_pipeline_logic.py`, agrega una prueba unitaria para el helper del
  manifiesto si se puede aislar sin ejecutar la compilación completa.
- En `tests/test_chile_hub.py`, actualiza las aserciones del manifiesto/ZIP para que
  las rutas de artefactos de conjuntos de datos candidatos estén ausentes de
  `artifact_manifest.json` y de `chile-hub-publishable-bundle.zip`.
- Mantén las aserciones de que los informes compartidos permanecen presentes en el
  ZIP: `data/normalized/hub_bundle.json`,
  `data/normalized/artifact_manifest.json` y otros informes requeridos.

**Verificar**: `make build && make verify && make test` sale con 0.

### Paso 5: Hacer que `hub_bundle.json` separe claramente los conjuntos de datos públicos de los candidatos

Actualiza `write_hub_bundle_json()` en `src/build_dev_db.py`.

Comportamiento requerido:

- `bundle["datasets"]` contiene solo conjuntos de datos con
  `publication_track="stable_publishable"` y `public_bundle_eligible=true`.
- Los conjuntos de datos candidatos no se listan en `bundle["datasets"]` y no tienen
  artefactos de datos candidatos adjuntos.
- Agrega una lista separada de nivel superior `bundle["candidate_datasets"]` con
  metadatos compactos para transparencia:
  - `dataset`
  - `maturity_status`
  - `publication_track`
  - `public_bundle_eligible`
  - `source_mode`
  - `source_detail`
  - `freshness`
  - `next_action` del registro
  - `upstream_datasets` cuando esté presente
- Agrega `bundle["public_dataset_count"]` y `bundle["candidate_dataset_count"]`.
- Mantén `dataset_catalog.json` como el catálogo completo. Las entradas candidatas en
  el catálogo deben llevar metadatos claros:
  `maturity_status="candidate"`, `publication_track="candidate"`,
  `public_bundle_eligible=false` y una advertencia/next_action.

Pruebas para actualizar:

- `tests/test_chile_hub.py` actualmente espera que `bundle["dataset_count"]` y
  `len(bundle["datasets"])` sean iguales al conteo completo del catálogo. Reemplaza
  eso con:
  - `bundle["dataset_count"]` puede permanecer como el conteo completo del catálogo
    para contexto de retrocompatibilidad, o renombrarse solo si todas las pruebas
    descendentes y expectativas de la CLI se actualizan deliberadamente.
  - `bundle["public_dataset_count"] == len(bundle["datasets"])`.
  - cada entrada de `bundle["datasets"]` es estable publicable.
  - cada candidato conocido aparece en `bundle["candidate_datasets"]`.
  - ningún `outputs` candidato o `artifacts` candidato aparece bajo
    `bundle["datasets"]`.

Si mantener la retrocompatibilidad es importante, prefiere mantener
`dataset_count` como el conteo completo del catálogo y agregar los dos nuevos conteos
explícitos en lugar de cambiar el significado de `dataset_count`.

**Verificar**: `make build && make verify && make test` sale con 0.

### Paso 6: Preservar el estado verde de desarrollo mientras se hace significativo el estado verde de publicación

Ejecuta:

```sh
make build
make verify
make test
make lint
make format-check
```

Resultado esperado: todos salen con 0.

Luego ejecuta:

```sh
make verify-live
```

Resultado esperado después de este plan:

- No debe fallar porque `finanzas_municipales`,
  `resultados_educacionales`, `indicadores_urbanos_siedu` o
  `perfil_territorial_comunal` estén en fallback, siempre que sean candidatos y
  estén excluidos del manifiesto/ZIP público.
- Debe seguir fallando si algún conjunto de datos estable publicable está en fallback
  o desactualizado.
- Debe seguir fallando si `indicadores` tiene `raw_recoveries`, `fetch_failures`,
  `preserved_existing_pairs`, `empty_live_pairs`, entrega parcial o cualquier valor
  de `indicator_delivery` fuera de `live` / `published_backfill`.

Si `make verify-live` falla solo debido a un tiempo de espera en vivo de
`mindicador.cl` que causa recuperación en crudo de `indicadores`, no edites la
política estricta para que pase. Regístralo como el próximo problema operativo:
mejorar reintentos/backoff o re-ejecutar cuando la API pública esté disponible.

**Verificar**:

- `make verify` sale con 0.
- `make verify-live` sale con 0 solo cuando los datos estables publicables están
  verdaderamente seguros para publicación.

### Paso 7: Documentar el backlog de candidatos como trabajo de seguimiento

No resuelvas los tres extractores candidatos en este plan. Agrega una nota de
mantenimiento breve en comentarios de código solo si es necesario, y asegúrate de que
los metadatos generados del catálogo/informe expongan estas próximas acciones:

- `finanzas_municipales`: encontrar un endpoint SINIM/SUBDERE estable o exportación
  directa; de lo contrario, permanecer como `candidate`, no publicable.
- `resultados_educacionales`: reemplazar el fallback curado con un volcado/exportación
  oficial estable de MINEDUC.
- `indicadores_urbanos_siedu`: configurar una descarga oficial estable de SIEDU; si
  solo hay cobertura parcial disponible, mantenerlo como candidato y marcar
  claramente la cobertura parcial.
- `perfil_territorial_comunal`: promover solo después de que sus upstreams no
  publicables se vuelvan estables publicables, porque hereda el peor estado upstream.
- `indicadores`: mejorar reintentos/backoff para `mindicador.cl`, pero mantener las
  reglas estrictas de publicación limitadas a vivo o `published_backfill`.

Si el operador lo desea, estos pueden convertirse en futuros planes 010-013.

**Verificar**: `make build && make verify` sale con 0 y
`data/normalized/dataset_catalog.json` contiene las próximas acciones de los
candidatos.

## Plan de pruebas

Agrega o actualiza pruebas para:

- El registro acepta carriles explícitos `stable_publishable` y `candidate`.
- El registro rechaza combinaciones imposibles como `fallback_only` más
  `stable_publishable`.
- Las entradas derivadas del registro heredan el peor carril de publicación upstream.
- La política de publicación ignora el estado de fallback candidato solo cuando los
  artefactos candidatos están ausentes del manifiesto/ZIP público.
- La política de publicación sigue rechazando conjuntos de datos estables publicables
  en fallback/desactualizados.
- La política de publicación sigue rechazando recuperación en crudo y entrega parcial
  de `indicadores`.
- El manifiesto excluye artefactos de conjuntos de datos candidatos.
- El ZIP excluye artefactos de conjuntos de datos candidatos.
- `hub_bundle.json.datasets` contiene solo conjuntos de datos estables publicables.
- `hub_bundle.json.candidate_datasets` lista de forma transparente las capas
  candidatas y sus próximas acciones.

Usa las pruebas existentes como patrones:

- `tests/test_pipeline_logic.py:100-160` para pruebas de política de publicación.
- `tests/test_pipeline_logic.py:230-293` para pruebas del registro de fuentes.
- `tests/test_chile_hub.py` para aserciones de manifiesto, paquete, ZIP y CLI.

## Criterios de finalización

Todo debe cumplirse:

- [ ] `data/source_registry.json` tiene `publication_track` y
  `public_bundle_eligible` para cada conjunto de datos.
- [ ] Los cuatro candidatos actuales son:
  `finanzas_municipales`, `resultados_educacionales`,
  `indicadores_urbanos_siedu` y `perfil_territorial_comunal`.
- [ ] Los artefactos de datos de conjuntos de datos candidatos están ausentes de
  `data/normalized/artifact_manifest.json`.
- [ ] Los artefactos de datos de conjuntos de datos candidatos están ausentes de
  `data/normalized/chile-hub-publishable-bundle.zip`.
- [ ] `data/normalized/hub_bundle.json.datasets` contiene solo conjuntos de datos
  estables publicables.
- [ ] `data/normalized/hub_bundle.json.candidate_datasets` lista los conjuntos de
  datos candidatos con metadatos claros no publicables.
- [ ] `make verify` sale con 0 para compilaciones locales/de desarrollo.
- [ ] `make verify-live` no falla debido a conjuntos de datos candidatos declarados
  en fallback excluidos del paquete público.
- [ ] `make verify-live` sigue fallando por estados inseguros de estables publicables,
  especialmente recuperación en crudo o entrega parcial de `indicadores`.
- [ ] `make test`, `make lint` y `make format-check` salen con 0.
- [ ] La fila de estado en `plans/README.md` para el plan 009 está actualizada.

## Condiciones de detención

Detente e informa si:

- `data/source_registry.json` ya no tiene una entrada por conjunto de datos o ha sido
  reemplazado por un mecanismo de preparación diferente.
- La lista actual de candidatos difiere de los cuatro conjuntos de datos nombrados en
  este plan y no hay una razón obvia en el registro para el cambio.
- Excluir artefactos candidatos requeriría eliminar conjuntos de datos candidatos de
  la generación local/de desarrollo por completo.
- `make verify-live` solo puede volverse verde permitiendo recuperación en crudo,
  entrega parcial de indicadores, conjuntos de datos estables desactualizados o
  fallback de conjuntos de datos estables.
- `hub_bundle.json` es consumido por un contrato externo documentado que requiere
  que todos los conjuntos de datos del catálogo estén en `bundle["datasets"]`; en ese
  caso, detente y pregunta si se debe introducir un nuevo campo `public_datasets` en
  lugar de cambiar `datasets`.
- Un conjunto de datos candidato tiene un extractor en vivo real para cuando se
  ejecute este plan. En ese caso, verifica primero el extractor y el registro; no lo
  mantengas ciegamente como candidato.
- La verificación de un paso falla dos veces después de un intento de corrección
  razonable.

## Notas de mantenimiento

Este plan crea el límite duradero entre "existe en desarrollo" y
"seguro para publicar". El trabajo de promoción futuro debe ser un conjunto de datos
a la vez:

- Promover `finanzas_municipales` solo después de que se configure una exportación
  estable de SINIM/SUBDERE y las pruebas de frescura/esquema lo demuestren.
- Promover `resultados_educacionales` solo después de reemplazar el fallback curado
  con una fuente agregada oficial de MINEDUC.
- Promover `indicadores_urbanos_siedu` solo después de que exista una exportación
  oficial estable de SIEDU, o mantenerlo como candidato con cobertura parcial
  explícita.
- Promover `perfil_territorial_comunal` al final, porque hereda la preparación
  upstream.
- Mantener `indicadores` estricto. Un mejor reintento/backoff es útil, pero la
  recuperación en crudo es un mecanismo de resiliencia de desarrollo, no un mecanismo
  de lanzamiento público.

Los revisores deben escudriñar de cerca el contenido del manifiesto y del ZIP. El
invariante más importante es que el paquete público no pueda incluir accidentalmente
datos de fallback candidatos mientras `make verify-live` reporte éxito.
