# Plan 019: Publicar un `datapackage.json` (Frictionless Data Package) como artefacto adicional

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar, actualiza la fila de estado de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat 140c8ea..HEAD -- src/build_dev_db.py src/builders/ contracts/datasets/ scripts/verify_pipeline.py pyproject.toml`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `140c8ea`, 2026-06-29

## Why this matters

chile-hub publica datasets curados de Chile, pero su descriptor de esquema usa un
formato propio (`contracts/datasets/*.schema.json`) que solo entienden sus propias
herramientas. El estándar **Frictionless Data Package** (`datapackage.json`) es el
formato de facto del ecosistema open-data: lo consumen Datasette, CKAN, Open Data
Editor, `pandas`/`frictionless` y muchos validadores. Publicar un `datapackage.json`
junto a los Parquet ya servidos hace que cualquiera pueda descubrir, validar e
ingerir el hub completo con una línea (`frictionless.Package("https://tooltician.com/chile-hub/data/normalized/datapackage.json")`)
sin conocer el formato interno.

**Restricción de diseño (no negociable)**: este plan **NO reemplaza** los contratos
internos `contracts/datasets/*.schema.json`. El ADR-005
(`docs/adr/ADR-005-contratos-esquema-json-schema.md`) decidió deliberadamente
mantener el formato propio como fuente de verdad interna (más expresivo para ancho
fijo, cobertura y outputs; los tipos de Polars no mapean 1:1 a estándares). El
`datapackage.json` es una capa de **publicación derivada** de esos contratos, no su
sustituto. Si en algún punto parece que hay que editar los contratos para que encaje
Frictionless, eso es una STOP condition.

## Current state

Archivos relevantes:

- `src/build_dev_db.py` — orquestador; la fase `_generate_reports()` (líneas
  590–652) genera todos los reportes en `data/normalized/`. Aquí se engancha la
  generación del data package, justo después de `write_dataset_catalog`.
- `src/builders/catalog.py` — patrón a seguir para un builder nuevo (imports de
  `_shared`, escritura con `write_json_atomic`).
- `src/builders/metadata.py:16-29` — `load_schema_contract(dataset_name)` ya carga
  cada contrato; reúsalo para obtener `column_types`, `primary_key`,
  `required_columns`.
- `contracts/datasets/*.schema.json` — 15 contratos. Ejemplo
  (`contracts/datasets/comunas.schema.json`):
  ```json
  {
    "dataset": "comunas",
    "primary_key": ["codigo_comuna"],
    "required_columns": ["codigo_region", "codigo_provincia", "codigo_comuna", "nombre_comuna", "nombre_comuna_clean"],
    "column_types": { "codigo_region": "string", "codigo_provincia": "string", "codigo_comuna": "string", "nombre_comuna": "string" },
    "nullable_columns": [],
    "fixed_width_columns": { "codigo_region": 2, "codigo_provincia": 3, "codigo_comuna": 5 },
    "expected_record_count": 346,
    "coverage_policy": "full",
    "publish_outputs": ["parquet", "json"]
  }
  ```
- `data/normalized/dataset_catalog.json` — generado en build; cada entrada de
  `datasets[]` tiene `dataset`, `description`, `source_name`, `source_url`,
  `fields` (lista completa de columnas), `outputs` (rutas relativas por formato),
  y `reuse_policy` (`{status, license, license_url, attribution_required, ...}`).
- `.gitignore:8-13` — `data/normalized/*` está ignorado **excepto** `*.json`,
  `*.md`, `*.parquet`, `*.zip`, `*.sha256`. Por tanto `datapackage.json` quedará
  trackeado y se publicará automáticamente vía GitHub Pages (el workflow
  `pages-deploy.yml` sube `path: .`).
- `src/builders/artifacts.py:155-158` — `write_artifact_manifest()` hace
  `os.listdir(NORMALIZED_DIR)`, así que el nuevo `.json` se incluirá en el manifiesto
  automáticamente (verifícalo en el Step 4).

Cómo `_generate_reports` escribe el catálogo (`src/build_dev_db.py:602`):

```python
catalog_output, dataset_catalog = write_dataset_catalog(pipeline_metadata)
write_dataset_catalog_markdown_file(dataset_catalog)
```

Convención del repo: español neutral en docstrings/comentarios; builders en
`src/builders/`; escritura atómica con `write_json_atomic` (de
`src/builders/io_utils.py`); imports absolutos `from src.builders...` dentro del
paquete de build; mypy corre sobre `src/builders`.

Especificación de referencia (Frictionless Data Package v1):
https://specs.frictionlessdata.io/data-package/ y Table Schema:
https://specs.frictionlessdata.io/table-schema/

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Build pipeline | `make build` | exit 0; escribe `data/normalized/` |
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |
| Typecheck | `.venv/bin/python -m mypy` | sin errores nuevos |
| Tests (foco) | `.venv/bin/python -m pytest tests/test_data_package.py -q` | pasan |
| Suite completa | `make test` | todos pasan |
| Validar descriptor | `.venv/bin/python -c "import frictionless; p=frictionless.Package('data/normalized/datapackage.json'); print(p.metadata_valid)"` | `True` |

`make build` requiere datos de staging en `data/staging/`. Si no están, repórtalo
(STOP). El **unit test** del Step 3 NO requiere build (usa un catálogo y contrato
sintéticos).

## Scope

**In scope** (únicos archivos a modificar/crear):
- `src/builders/data_package.py` — **crear**: builder del data package.
- `src/build_dev_db.py` — enganchar la generación en `_generate_reports()`.
- `scripts/verify_pipeline.py` — añadir verificación del descriptor (metadata-only).
- `pyproject.toml` — añadir `frictionless` como dependencia **dev**.
- `tests/test_data_package.py` — **crear**: tests del builder.

**Out of scope** (NO tocar):
- `contracts/datasets/*.schema.json` — el formato interno NO cambia (ADR-005).
- Cualquier validación que cargue las filas de datos del Parquet — la verificación
  es **solo de metadata del descriptor** (`empresas` tiene ~1.57M filas; validar
  datos sería lento y está fuera de alcance).
- `src/validation.py` y los validadores de dominio — siguen como están.
- La librería `frictionless` NO se usa para **generar** el descriptor (la generación
  es emisión de JSON puro); solo se usa en dev para **validar** que el descriptor
  emitido es conforme.

## Git workflow

- Branch: `advisor/019-frictionless-datapackage`
- Commits estilo conventional commits: ej.
  `feat(pipeline): publicar datapackage.json (Frictionless) derivado de contratos`.
- No hagas push ni abras PR salvo indicación del operador.
- Nota: `make build` regenera muchos artefactos en `data/normalized/`. Al commitear,
  incluye solo `data/normalized/datapackage.json` y los archivos de código; NO
  commitees regeneraciones espurias de otros artefactos salvo que el operador lo pida.

## Steps

### Step 1: Crear el builder `src/builders/data_package.py`

Crea un módulo que construya el descriptor desde el `dataset_catalog` + los contratos.
Estructura objetivo:

```python
"""Generación del descriptor Frictionless Data Package (datapackage.json).

Capa de PUBLICACIÓN derivada de los contratos internos (contracts/datasets/*.schema.json)
y del dataset_catalog.json. NO reemplaza el formato interno (ver ADR-005); solo
expone el hub en un estándar interoperable del ecosistema open-data.
"""

import os
from datetime import datetime

from src.builders._shared import NORMALIZED_DIR, ROOT_DIR, UTC
from src.builders.io_utils import write_json_atomic
from src.builders.metadata import load_schema_contract

# chile-hub column_types -> Frictionless Table Schema types
_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "date": "date",
}


def _build_fields(dataset_name, catalog_fields):
    """Construye los fields de Table Schema a partir del contrato + fields del catálogo."""
    contract = load_schema_contract(dataset_name) or {}
    column_types = contract.get("column_types", {})
    required = set(contract.get("required_columns", []))
    fields = []
    for column in catalog_fields:
        ftype = _TYPE_MAP.get(column_types.get(column, "string"), "string")
        field = {"name": column, "type": ftype}
        if column in required:
            field["constraints"] = {"required": True}
        fields.append(field)
    return fields, contract.get("primary_key", [])


def build_data_package(dataset_catalog, version, homepage):
    """Construye el dict del Frictionless Data Package desde el catálogo."""
    resources = []
    for entry in dataset_catalog.get("datasets", []):
        name = entry["dataset"]
        outputs = entry.get("outputs", {})
        parquet_path = outputs.get("parquet")
        if not parquet_path:
            continue  # solo datasets con Parquet publicado
        fields, primary_key = _build_fields(name, entry.get("fields", []))
        reuse = entry.get("reuse_policy", {}) or {}
        schema = {"fields": fields, "missingValues": [""]}
        if primary_key:
            schema["primaryKey"] = primary_key
        resource = {
            "name": name,
            "path": os.path.basename(parquet_path),
            "format": "parquet",
            "mediatype": "application/vnd.apache.parquet",
            "title": name,
            "description": entry.get("description", ""),
            "schema": schema,
        }
        if entry.get("source_name") or entry.get("source_url"):
            resource["sources"] = [
                {"title": entry.get("source_name", ""), "path": entry.get("source_url", "")}
            ]
        if reuse.get("license") or reuse.get("license_url"):
            resource["licenses"] = [
                {"title": reuse.get("license", ""), "path": reuse.get("license_url", "")}
            ]
        resources.append(resource)

    return {
        "name": "chile-hub",
        "title": "chile-hub — Datos públicos de Chile curados",
        "description": (
            "Capa de datos reproducible y curada sobre datasets públicos oficiales "
            "de Chile: geografía, demografía, salud, educación, finanzas municipales "
            "e indicadores."
        ),
        "version": version,
        "homepage": homepage,
        "created": datetime.now(UTC).isoformat(),
        "resources": resources,
    }


def write_data_package_json(dataset_catalog, version, homepage):
    """Genera y escribe data/normalized/datapackage.json. Retorna la ruta."""
    package = build_data_package(dataset_catalog, version, homepage)
    output_path = os.path.join(NORMALIZED_DIR, "datapackage.json")
    write_json_atomic(package, output_path, ensure_ascii=False, indent=2)
    return output_path
```

**Verify**: `.venv/bin/python -c "from src.builders.data_package import build_data_package; print('ok')"` → imprime `ok`.

### Step 2: Enganchar la generación en `_generate_reports`

En `src/build_dev_db.py`, añade el import del builder junto a los demás imports de
`src.builders.*` (sigue el estilo con `# noqa: E402` que usan los otros bloques):

```python
from src.builders.data_package import write_data_package_json  # noqa: E402
```

Luego, en `_generate_reports()` (después de la línea 603,
`write_dataset_catalog_markdown_file(dataset_catalog)`), añade:

```python
data_package_output = write_data_package_json(
    dataset_catalog,
    pipeline_metadata["version"],
    pipeline_metadata["public_site_url"],
)
```

Incluye `data_package=data_package_output` en el `log.info("reports_written", ...)`
(líneas 634–652) para que quede registrado junto a los demás outputs.

**Verify**: `make build` → exit 0 y `test -f data/normalized/datapackage.json` → existe.

### Step 3: Tests del builder (sin build)

Crea `tests/test_data_package.py` modelado sobre el estilo de los tests existentes
(revisa `tests/test_pipeline_logic.py` para el patrón de builders sin datos). Usa un
catálogo sintético y mockea/parchea `load_schema_contract` para no depender de
archivos reales. Cubre:
- `build_data_package` produce `name == "chile-hub"`, `version` y `resources` no vacío.
- Un dataset con `column_types` mapea tipos correctamente (`integer`→`integer`, etc.)
  y columnas fuera de `column_types` caen a `"string"`.
- `primary_key` del contrato aparece en `schema.primaryKey`.
- `required_columns` produce `constraints.required == True` en esos fields.
- Un dataset sin `outputs.parquet` se omite de `resources`.

**Verify**: `.venv/bin/python -m pytest tests/test_data_package.py -q` → todos pasan.

### Step 4: Verificación del descriptor en el pipeline

Primero confirma que el manifiesto ya lo incluye:
`.venv/bin/python -c "import json; m=json.load(open('data/normalized/artifact_manifest.json')); print(any('datapackage.json' in str(a) for a in m.get('artifacts', [])))"`
→ `True`. Si es `False`, revisa `write_artifact_manifest()` en
`src/builders/artifacts.py` y asegúrate de que no excluye `datapackage.json` por
nombre; ajústalo mínimamente solo si lo excluye explícitamente.

Luego añade `frictionless` como dependencia dev en `pyproject.toml` (sección
`[project.optional-dependencies].dev`, líneas 57–73), pineado a una versión 5.x
(la familia v5 es la API `Package(...).metadata_valid`):

```toml
    "frictionless>=5.18,<6",
```

Añade a `scripts/verify_pipeline.py` una función que valide **solo la metadata** del
descriptor (no las filas de datos), e invócala desde el flujo de verificación junto a
`verify_schema_contracts()`. Patrón:

```python
def verify_data_package():
    """Valida que datapackage.json sea un descriptor Frictionless conforme (metadata-only)."""
    descriptor_path = NORMALIZED_DIR / "datapackage.json"
    if not descriptor_path.exists():
        fail("Missing datapackage.json — ejecuta el build")
    try:
        import frictionless
    except ImportError:
        # frictionless es dependencia dev; si no está, omitir sin fallar el build prod.
        return
    package = frictionless.Package(str(descriptor_path))
    if not package.metadata_valid:
        errors = "; ".join(str(e) for e in package.metadata_errors)
        fail(f"datapackage.json no es un Frictionless Data Package válido: {errors}")
```

Busca dónde `verify_schema_contracts()` es invocada dentro de `verify_pipeline.py` y
añade `verify_data_package()` en el mismo lugar (mismo perfil de verificación).

**Verify**:
- `.venv/bin/python -c "import frictionless; p=frictionless.Package('data/normalized/datapackage.json'); print(p.metadata_valid)"` → `True`
- `.venv/bin/python scripts/verify_pipeline.py --profile dev` → exit 0.

### Step 5: Verificación final

**Verify**:
- `make lint` → exit 0
- `make format-check` → exit 0
- `.venv/bin/python -m mypy` → sin errores nuevos
- `make test` → todos pasan (incluye `tests/test_data_package.py`)

## Test plan

- Nuevo `tests/test_data_package.py` (5 casos del Step 3), sin dependencia de datos
  reales (parchear `load_schema_contract`), modelado sobre `tests/test_pipeline_logic.py`.
- La validación de conformidad real (`frictionless`) corre en el Step 4 contra el
  descriptor generado por `make build`.
- Verificación: `make test` → todos pasan; `verify_pipeline.py --profile dev` exit 0.

## Done criteria

Todas deben cumplirse:

- [ ] `src/builders/data_package.py` existe con `build_data_package` y `write_data_package_json`.
- [ ] `make build` genera `data/normalized/datapackage.json`.
- [ ] `python -c "import frictionless; print(frictionless.Package('data/normalized/datapackage.json').metadata_valid)"` → `True`.
- [ ] `datapackage.json` aparece en `data/normalized/artifact_manifest.json`.
- [ ] `frictionless` está en `[project.optional-dependencies].dev` de `pyproject.toml`.
- [ ] `scripts/verify_pipeline.py` valida el descriptor y `--profile dev` exit 0.
- [ ] `make test`, `make lint`, `make format-check` exit 0; mypy sin errores nuevos.
- [ ] `tests/test_data_package.py` existe y pasa.
- [ ] `contracts/datasets/*.schema.json` SIN cambios (`git status` no los lista).
- [ ] Fila de `plans/README.md` actualizada.

## STOP conditions

Detente y reporta (no improvises) si:

- Para que Frictionless valide haría falta editar un `contracts/datasets/*.schema.json`
  (violaría ADR-005).
- `make build` falla por falta de datos de staging.
- La validación `frictionless` reporta errores que solo se resuelven cambiando el
  formato/tipos de los datos publicados (no solo el descriptor).
- `metadata_valid` es `True` pero `frictionless.Package(...).validate()` (si lo
  pruebas opcionalmente) intenta descargar/cargar las filas y tarda > 2 min —
  detente y deja la verificación en metadata-only.
- La versión de `frictionless` instalada no expone `Package(...).metadata_valid`
  (API distinta a v5) — repórtalo en vez de adivinar la API.

## Maintenance notes

- **Sincronización**: el descriptor se regenera en cada `make build` desde los
  contratos; no hay que mantenerlo a mano. Si se añade un dataset (ver `AGENTS.md §5`),
  su resource aparece automáticamente si tiene contrato + `outputs.parquet`.
- **Tipos**: el `_TYPE_MAP` cubre los 5 tipos de los contratos actuales. Si un
  contrato introduce un tipo nuevo, añádelo al mapa (cae a `"string"` por defecto, lo
  cual es seguro pero menos preciso).
- **Follow-up deferido**: enlazar el `datapackage.json` desde la landing (`index.html`,
  sección catálogo) y documentar el consumo con `frictionless`/Datasette. No incluido
  aquí para mantener el alcance en la generación + verificación.
- En revisión de PR: confirmar que ningún contrato interno cambió y que la verificación
  es metadata-only (no carga filas).
