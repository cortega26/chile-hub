"""Sincroniza hechos "variables" hardcodeados en README.md y AGENTS.md con su fuente de verdad.

Cada función lee un hecho derivado del estado real del proyecto (conteo de
tests, de ADRs, de contratos, de datasets, versión del paquete, salud y
calidad del hub) y reemplaza el bloque delimitado correspondiente vía
``replace_delimited_block``. Ver AGENTS.md §12 para la tabla completa de
propietarios canónicos y dónde corre la generación/verificación.
"""

import ast
import json
import os

from src.builders._shared import DATASET_CATALOG_CONFIG, NORMALIZED_DIR, ROOT_DIR
from src.builders.io_utils import read_json_if_exists, read_project_version, replace_delimited_block

README_PATH = os.path.join(ROOT_DIR, "README.md")
AGENTS_PATH = os.path.join(ROOT_DIR, "AGENTS.md")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
ADR_DIR = os.path.join(ROOT_DIR, "docs", "adr")
CONTRACTS_DIR = os.path.join(ROOT_DIR, "contracts", "datasets")
DATASET_DOCS_DIR = os.path.join(ROOT_DIR, "docs", "datasets")

GRADE_ORDER = ["A", "B", "C", "D", "F"]


def _count_test_functions():
    """Cuenta funciones `test_*` en tests/test_*.py vía AST (sin correr pytest).

    Coincide con `pytest --collect-only` mientras la suite no use
    `@pytest.mark.parametrize` (verificado: 0 usos hoy). Si se introduce
    parametrize, este conteo subestimará el real — en ese caso migrar a
    invocar `pytest --collect-only -q` (requiere pytest instalado).
    """
    total = 0
    for name in sorted(os.listdir(TESTS_DIR)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        path = os.path.join(TESTS_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                total += 1
    return total


def sync_readme_test_count(check_only=False):
    count = _count_test_functions()
    body = (
        f"- **{count} tests** (`pytest --collect-only`) que validan extracción, "
        "contratos e integridad de datos."
    )
    return replace_delimited_block(
        README_PATH, "TEST_COUNT", body, check_only=check_only, separator="\n"
    )


def sync_readme_adr_count(check_only=False):
    count = len([n for n in os.listdir(ADR_DIR) if n.startswith("ADR-") and n.endswith(".md")])
    body = (
        f"- **{count} ADRs** ([`docs/adr/`](docs/adr/)) que documentan cada decisión "
        'de arquitectura con su contexto, consecuencias y tradeoffs — no solo el "qué", '
        'sino el "por qué".'
    )
    return replace_delimited_block(
        README_PATH, "ADR_COUNT", body, check_only=check_only, separator="\n"
    )


def sync_readme_contract_count(check_only=False):
    count = len([n for n in os.listdir(CONTRACTS_DIR) if n.endswith(".schema.json")])
    body = (
        f"{count} contratos JSON Schema ([`contracts/datasets/`](contracts/datasets/)) "
        "definen columnas esperadas, tipos, claves primarias y cobertura. Se validan "
        "**en cada build** automáticamente."
    )
    return replace_delimited_block(
        README_PATH, "CONTRACT_COUNT", body, check_only=check_only, separator=""
    )


def sync_readme_dataset_badge(check_only=False):
    built_count = len([d for d in DATASET_CATALOG_CONFIG.values() if d.get("outputs")])
    body = (
        f"[![Datasets](https://img.shields.io/badge/Datasets-{built_count}%20capas-16a34a.svg)]()"
    )
    return replace_delimited_block(
        README_PATH, "DATASET_BADGE", body, check_only=check_only, separator="\n"
    )


def sync_readme_version_pin_example(check_only=False):
    version = read_project_version(ROOT_DIR)
    body = (
        "> **Versionado:** Para entornos productivos, fija la versión exacta en `requirements.txt`\n"
        "> (revisa el badge de PyPI al inicio de este README para la versión más reciente):\n"
        "> ```\n"
        f"> chile-hub=={version}\n"
        "> ```\n"
        "> El bundle de datos se publica con cada release. La API del módulo `ChileHub` sigue\n"
        "> versionado semántico: cambios de interfaz pública solo en _major releases_."
    )
    return replace_delimited_block(
        README_PATH, "VERSION_PIN_EXAMPLE", body, check_only=check_only, separator="\n"
    )


def sync_readme_redistribution_summary(check_only=False):
    report = read_json_if_exists(os.path.join(NORMALIZED_DIR, "redistribution_report.json"))
    if report is None:
        return False
    ready = report.get("ready_count", 0)
    total = report.get("dataset_count", 0)
    body = (
        "Licencia, atribución requerida y permiso de redistribución verificados dataset por "
        f"dataset. **{ready} de {total} capas** pasan la auditoría (`ready`)."
    )
    return replace_delimited_block(
        README_PATH, "REDISTRIBUTION_SUMMARY", body, check_only=check_only, separator=""
    )


def sync_readme_health_summary(check_only=False):
    health = read_json_if_exists(os.path.join(NORMALIZED_DIR, "hub_health.json"))
    if health is None:
        return False
    ok = health.get("ok_count", 0)
    warn = health.get("warn_count", 0)
    error = health.get("error_count", 0)
    body = (
        "Dashboard público con severidad, frescura, cobertura, drift y degradación por dataset. "
        f"{ok} capas `ok`, {warn} `warn`, {error} `error`."
    )
    return replace_delimited_block(
        README_PATH, "HEALTH_SUMMARY", body, check_only=check_only, separator=""
    )


def sync_readme_quality_summary(check_only=False):
    quality = read_json_if_exists(os.path.join(NORMALIZED_DIR, "dataset_quality.json"))
    if quality is None:
        return False
    average = quality.get("average_score", 0)
    distribution = quality.get("grade_distribution", {})
    grades = ", ".join(f"{distribution[g]} {g}" for g in GRADE_ORDER if distribution.get(g, 0) > 0)
    body = (
        f"Puntuación compuesta A-F por dataset: **promedio {average}/100** ({grades}). "
        "Dimensiones: validación, contrato, madurez de fuente, frescura, cobertura, política de reúso."
    )
    return replace_delimited_block(
        README_PATH, "QUALITY_SUMMARY", body, check_only=check_only, separator=""
    )


_AGENTS_TEST_DESCRIPTIONS = {
    "test_chile_hub.py": (
        "API Python de `ChileHub`, CLI, contratos de artefactos "
        "(SHA256, catálogo, ZIP), contratos de workflow/Makefile, "
        "`Dataset(StrEnum)`"
    ),
    "test_extractors.py": (
        "Un test class por extractor (fetch, normalización, staging) "
        "+ contrato ABC de `BaseExtractor` + reintentos HTTP"
    ),
    "test_pipeline_logic.py": (
        "Lógica interna de `build_dev_db.py`, invariantes CUT, "
        "fallback de indicadores, severidad de `dataset_changelog.json`, "
        "builders (`reports`, `pipeline_status_utils`)"
    ),
    "test_validation.py": (
        "Funciones `validate_*()` de `src/validation.py`: bordes vacíos, "
        "claves duplicadas, casos límite"
    ),
    "test_core.py": (
        "Métodos públicos de `ChileHub` (`core.py`): metadatos, "
        "reportes operativos, inspección — no cubre CLI"
    ),
    "test_data_package.py": "Builder de Frictionless Data Package",
    "test_packaging_runtime.py": ("Empaquetado del bundle publicable (ZIP, SHA256) en runtime"),
    "test_render.py": "Helper de renderizado de tablas (`_render.py`)",
    "test_ci_config.py": (
        "Guardrails de texto simple para regresiones **reales** ya ocurridas de CI/Makefile"
    ),
    "test_builders_artifacts.py": (
        "Builders de artefactos publicables (bundle ZIP, SHA-256, consistencia manifiesto↔ZIP)"
    ),
    "test_builders_formats.py": (
        "Golden round-trip para writers de formatos (Parquet, JSON, Excel, DuckDB, SQLite)"
    ),
    "test_verify_pipeline.py": (
        "Verificación de pipeline (`verify_pipeline.py`) — guardia pre-publicación de artefactos"
    ),
    "test_data_manager.py": (
        "Unit tests de `ChileHubDataManager` y contrato de caché de geometría — sin "
        "`data/normalized/` (TC-07: extraídos de `test_chile_hub.py`)"
    ),
}


def _test_file_requires_normalized(filepath):
    """Heurística: ¿el archivo de test lee de data/normalized/?"""
    with open(filepath, "r", encoding="utf-8") as f:
        return "data/normalized" in f.read(4096)


def sync_agents_test_table(check_only=False):
    """Tabla de archivos de test en AGENTS.md desde tests/test_*.py."""
    test_files = sorted(
        f for f in os.listdir(TESTS_DIR) if f.startswith("test_") and f.endswith(".py")
    )
    count = len(test_files)

    rows = []
    for fname in test_files:
        fpath = os.path.join(TESTS_DIR, fname)
        requires = "Sí (`make build` antes)" if _test_file_requires_normalized(fpath) else "No"
        desc = _AGENTS_TEST_DESCRIPTIONS.get(fname)
        if desc is None:
            raise SystemExit(
                f"ERROR: test '{fname}' sin descripción en "
                "_AGENTS_TEST_DESCRIPTIONS. Agrega una entrada en "
                "src/builders/doc_sync.py."
            )
        rows.append(f"| `{fname}` | {requires} | {desc} |")

    header = "| Archivo | Requiere `data/normalized/` | Qué cubre |\n|:---|:---:|:---|"

    intro = (
        f"**{count} archivos** en `tests/`. Esta tabla es de "
        "**navegación por archivo**, no un\n"
        "inventario de clases — las clases cambian con frecuencia y una "
        "lista exhaustiva\n"
        "aquí quedaría stale de inmediato. Para el inventario vivo de "
        "clases:\n"
        "```bash\n"
        'grep -n "^class " tests/*.py\n'
        "```"
    )

    body = intro + "\n\n" + "\n".join([header] + rows)

    return replace_delimited_block(
        AGENTS_PATH, "AGENTS_TEST_TABLE", body, check_only=check_only, separator="\n\n"
    )


_AGENTS_EXTRACTOR_DESCRIPTIONS = {
    "base.py": "BaseExtractor ABC (contrato para todos los extractores)",
    "http_utils.py": "Reintentos/backoff HTTP compartidos",
    "region_utils.py": "Normalización de nombres de región compartida",
    "source_adapter.py": "Adaptador de fuente compartido",
    "subdere_extractor.py": (
        "DPA: regiones/provincias/comunas/comunas_enriquecidas (BCN ArcGIS) → data/staging/"
    ),
    "bcentral_extractor.py": "Indicadores desde mindicador.cl → data/staging/",
    "censo_extractor.py": "Censo 2024 — población comunal (INE) → data/staging/",
    "censo_hogares_viviendas_extractor.py": (
        "Censo 2024 — hogares y viviendas (INE) → data/staging/"
    ),
    "salud_extractor.py": "Establecimientos de salud (MINSAL) → data/staging/",
    "electoral_extractor.py": "Distritos electorales (BCN/SERVEL) → data/staging/",
    "mineduc_establecimientos_extractor.py": (
        "Establecimientos educacionales (MINEDUC) → data/staging/"
    ),
    "mineduc_resultados_extractor.py": (
        "Resultados educacionales agregados (MINEDUC) → data/staging/"
    ),
    "siedu_extractor.py": "Indicadores urbanos SIEDU (INE) → data/staging/",
    "res_extractor.py": (
        "Empresas — Registro de Empresas y Sociedades (datos.gob.cl) → data/staging/"
    ),
    "pobreza_extractor.py": "Pobreza comunal SAE (MDS) → data/staging/",
    "consumo_electrico_extractor.py": ("Consumo eléctrico comunal (CNE) → data/staging/"),
    "partidos_politicos_extractor.py": ("Partidos políticos vigentes (SERVEL) → data/staging/"),
    "autoridades_electas_extractor.py": ("Diputados y senadores en ejercicio → data/staging/"),
    "sinim_finanzas_extractor.py": (
        "Finanzas municipales — stub de fallback; NO corre en `make extract`"
    ),
    "sinim_finanzas_live_extractor.py": (
        "Finanzas municipales — scraper real; corre en `monthly-scrape.yml`"
    ),
    "cead_delincuencia_live_extractor.py": (
        "Delincuencia comunal (CEAD); corre en `monthly-scrape.yml`"
    ),
    "autoridades_locales_extractor.py": (
        "Autoridades locales (BCN SIIT + Wikipedia); carril `candidate`, sin cadencia automática"
    ),
    "geometria_comunal_extractor.py": (
        "Geometría comunal — límites poligonales (BCN ArcGIS); carril `candidate` → data/staging/"
    ),
}

EXTRACTORS_DIR = os.path.join(ROOT_DIR, "src", "extractors")

_SHARED_MODULES = {"base.py", "http_utils.py", "region_utils.py", "source_adapter.py"}


def sync_agents_extractor_list(check_only=False):
    """Árbol de extractores en AGENTS.md desde src/extractors/."""
    all_files = sorted(
        f for f in os.listdir(EXTRACTORS_DIR) if f.endswith(".py") and f != "__init__.py"
    )
    shared = [f for f in all_files if f in _SHARED_MODULES]
    extractors_list = [f for f in all_files if f.endswith("_extractor.py")]
    extractor_count = len(extractors_list)
    shared_count = len(shared)

    lines = [
        "│   ├── extractors/                 "
        f"{extractor_count} extractores por dataset + {shared_count}"
        " módulos compartidos (ver nota abajo)"
    ]

    # Shared modules first
    for fname in shared:
        prefix = "│   │   ├──"
        desc = _AGENTS_EXTRACTOR_DESCRIPTIONS.get(fname)
        if desc is None:
            raise SystemExit(
                f"ERROR: extractor '{fname}' sin descripción en "
                "_AGENTS_EXTRACTOR_DESCRIPTIONS. Agrega una entrada en "
                "src/builders/doc_sync.py."
            )
        lines.append(f"{prefix} {fname:45s} {desc}")

    # Extractors
    for i, fname in enumerate(extractors_list):
        is_last = i == len(extractors_list) - 1
        prefix = "│   │   └──" if is_last else "│   │   ├──"
        desc = _AGENTS_EXTRACTOR_DESCRIPTIONS.get(fname)
        if desc is None:
            raise SystemExit(
                f"ERROR: extractor '{fname}' sin descripción en "
                "_AGENTS_EXTRACTOR_DESCRIPTIONS. Agrega una entrada en "
                "src/builders/doc_sync.py."
            )
        lines.append(f"{prefix} {fname:45s} {desc}")

    body = "\n".join(lines)
    return replace_delimited_block(
        AGENTS_PATH, "AGENTS_EXTRACTOR_LIST", body, check_only=check_only, separator="\n"
    )


def sync_agents_dataset_count(check_only=False):
    """Conteo de datasets en AGENTS.md desde el catálogo."""
    total = len(DATASET_CATALOG_CONFIG)
    return replace_delimited_block(
        AGENTS_PATH, "AGENTS_DATASET_COUNT", str(total), check_only=check_only, separator=""
    )


def _contract_type_to_sql(col_type, width=None):
    """Convierte tipo de contrato a formato SQL para el README."""
    mapping = {
        "string": "VARCHAR",
        "integer": "INTEGER",
        "float": "DOUBLE",
        "date": "DATE",
        "boolean": "BOOLEAN",
    }
    base = mapping.get(col_type, col_type.upper())
    if width and col_type == "string":
        return f"{base}({width})"
    return base


_README_DATASET_DOMAINS = {
    "regiones": "Territorio",
    "provincias": "Territorio",
    "comunas": "Territorio",
    "comunas_enriquecidas": "Territorio",
    "distritos_electorales": "Territorio",
    "geometria_comunal": "Territorio",
    "censo_comunal": "Demografía",
    "censo_hogares_viviendas": "Demografía",
    "pobreza_comunal": "Demografía",
    "establecimientos_salud": "Servicios públicos",
    "establecimientos_educacionales": "Servicios públicos",
    "resultados_educacionales": "Servicios públicos",
    "indicadores": "Economía",
    "finanzas_municipales": "Economía",
    "empresas": "Economía",
    "consumo_electrico_comunal": "Economía",
    "indicadores_urbanos_siedu": "Indicadores urbanos",
    "partidos_politicos": "Política",
    "autoridades_electas": "Política",
    "autoridades_locales": "Política",
    "delincuencia_comunal": "Seguridad (carril `candidate`)",
    "perfil_territorial_comunal": None,
}

_README_DOMAIN_ORDER = [
    "Territorio",
    "Demografía",
    "Servicios públicos",
    "Economía",
    "Indicadores urbanos",
    "Política",
    "Seguridad (carril `candidate`)",
]


def sync_readme_extractor_table(check_only=False):
    """Tabla de extractores por dominio en README.md desde el catálogo."""
    catalog = DATASET_CATALOG_CONFIG
    by_domain: dict[str, list[str]] = {domain: [] for domain in _README_DOMAIN_ORDER}

    for key, cfg in catalog.items():
        if key not in _README_DATASET_DOMAINS:
            raise SystemExit(
                f"ERROR: dataset '{key}' sin dominio en _README_DATASET_DOMAINS. "
                "Agrega una entrada en src/builders/doc_sync.py."
            )
        domain = _README_DATASET_DOMAINS[key]
        if domain is None:
            continue
        value = cfg.get("extractor")
        paths = [] if value is None else ([value] if isinstance(value, str) else list(value))
        for rel in paths:
            basename = os.path.basename(rel)
            if basename not in by_domain[domain]:
                by_domain[domain].append(basename)

    rows = []
    for domain in _README_DOMAIN_ORDER:
        extractors = ", ".join(f"`{name}`" for name in by_domain[domain])
        rows.append(f"| {domain} | {extractors} |")
    rows.append("| Derivado en `build_dev_db.py` (sin extractor) | `perfil_territorial_comunal` |")

    header = "| Dominio | Extractores |\n|:---|:---|"
    body = "\n".join([header] + rows)

    return replace_delimited_block(
        README_PATH, "EXTRACTOR_TABLE", body, check_only=check_only, separator="\n\n"
    )


def sync_docs_schema_blocks(check_only=False):
    """Bloque Schema en cada docs/datasets/{dataset}.md desde su contrato.

    El contrato (`contracts/datasets/{dataset}.schema.json`) es la fuente de
    verdad del esquema; la sección "Schema (auto-generado)" de cada doc es un
    artefacto derivado. Sin esto, la tabla de columnas del doc stale se
    desincronizaba del contrato sin que nada lo detectara (el gate de
    `check_companion_paths.py` solo fuerza que el doc se TOQUE, no que su
    contenido siga correcto).
    """
    catalog = DATASET_CATALOG_CONFIG
    for ds_name in sorted(catalog):
        contract_path = os.path.join(CONTRACTS_DIR, f"{ds_name}.schema.json")
        doc_path = os.path.join(DATASET_DOCS_DIR, f"{ds_name}.md")
        if not os.path.exists(contract_path) or not os.path.exists(doc_path):
            continue

        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        columns_list = contract.get("columns", [])
        if not columns_list:
            continue

        required = set(contract.get("required_columns", []))
        primary_key = set(contract.get("primary_key", []))

        header = f"## Schema (auto-generado desde `contracts/datasets/{ds_name}.schema.json`)"
        table_header = (
            "| Columna | Tipo | Ejemplo | Requerida | Nota |\n|:---|:---|:---|:---:|:---|"
        )
        rows = []
        for col in columns_list:
            col_name = col["name"]
            col_type = _contract_type_to_sql(col.get("type", "string"), col.get("width"))
            example = col.get("example")
            if example is None:
                example_str = "—"
            elif isinstance(example, bool):
                example_str = "`true`" if example else "`false`"
            elif isinstance(example, (int, float)):
                example_str = f"`{example}`"
            else:
                example_str = f'`"{example}"`'
            required_str = "Sí" if col_name in required else "No"
            note = "PK" if col_name in primary_key else "—"
            rows.append(
                f"| `{col_name}` | `{col_type}` | {example_str} | {required_str} | {note} |"
            )

        body = header + "\n\n" + "\n".join([table_header] + rows)
        replace_delimited_block(
            doc_path, "DATASET_SCHEMA", body, check_only=check_only, separator="\n\n"
        )


def sync_readme_schema_details(check_only=False):
    """Tablas de schema en README.md desde contratos enriquecidos."""
    catalog = DATASET_CATALOG_CONFIG
    built_names = [n for n in catalog if catalog[n].get("outputs")]
    upcoming_names = [n for n in catalog if not catalog[n].get("outputs")]
    ordered_names = built_names + upcoming_names

    sections = []
    for i, ds_name in enumerate(ordered_names, 1):
        contract_path = os.path.join(CONTRACTS_DIR, f"{ds_name}.schema.json")
        if not os.path.exists(contract_path):
            continue

        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        columns_list = contract.get("columns", [])
        if not columns_list:
            continue

        cfg = catalog.get(ds_name, {})
        description = cfg.get("description", "")
        primary_key = contract.get("primary_key", [])
        has_outputs = bool(cfg.get("outputs"))

        notes = []
        if not has_outputs:
            notes.append("en carril candidate — datos no incluidos en el bundle público")
        pk_hint = f"PK: {', '.join(primary_key)}" if primary_key else ""

        header = f"**{i}. {ds_name}**"
        if description:
            header += f" — {description}"
        if notes:
            header += f" ({'; '.join(notes)})"
        if pk_hint:
            header += f" ({pk_hint})"

        table_header = "| Columna | Tipo | Ejemplo |\n|:---|:---|:---|"
        table_rows = []
        for col in columns_list:
            col_name = col["name"]
            col_type = _contract_type_to_sql(col.get("type", "string"), col.get("width"))
            example = col.get("example")
            if example is None:
                example_str = "—"
            elif isinstance(example, bool):
                example_str = "`true`" if example else "`false`"
            elif isinstance(example, (int, float)):
                example_str = f"`{example}`"
            else:
                example_str = f'`"{example}"`'
            table_rows.append(f"| `{col_name}` | `{col_type}` | {example_str} |")

        sections.append("\n".join([header, table_header] + table_rows))

    body = "\n\n".join(sections)

    return replace_delimited_block(
        README_PATH, "SCHEMA_DETAILS", body, check_only=check_only, separator="\n\n"
    )


SYNC_FUNCS = [
    sync_readme_test_count,
    sync_readme_adr_count,
    sync_readme_contract_count,
    sync_readme_dataset_badge,
    sync_readme_version_pin_example,
    sync_readme_redistribution_summary,
    sync_readme_health_summary,
    sync_readme_quality_summary,
    sync_agents_dataset_count,
    sync_agents_test_table,
    sync_agents_extractor_list,
    sync_readme_schema_details,
    sync_readme_extractor_table,
    sync_docs_schema_blocks,
]


def sync_all_docs(check_only=False):
    return [fn.__name__ for fn in SYNC_FUNCS if fn(check_only=check_only)]
