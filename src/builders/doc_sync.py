"""Sincroniza hechos "variables" hardcodeados en README.md y AGENTS.md con su fuente de verdad.

Cada función lee un hecho derivado del estado real del proyecto (conteo de
tests, de ADRs, de contratos, de datasets, versión del paquete, salud y
calidad del hub) y reemplaza el bloque delimitado correspondiente vía
``replace_delimited_block``. Ver AGENTS.md §12 para la tabla completa de
propietarios canónicos y dónde corre la generación/verificación.
"""

import ast
import os

from src.builders._shared import DATASET_CATALOG_CONFIG, NORMALIZED_DIR, ROOT_DIR
from src.builders.io_utils import read_json_if_exists, read_project_version, replace_delimited_block

README_PATH = os.path.join(ROOT_DIR, "README.md")
AGENTS_PATH = os.path.join(ROOT_DIR, "AGENTS.md")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
ADR_DIR = os.path.join(ROOT_DIR, "docs", "adr")
CONTRACTS_DIR = os.path.join(ROOT_DIR, "contracts", "datasets")

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


def sync_agents_dataset_count(check_only=False):
    """Conteo de datasets en AGENTS.md desde el catálogo."""
    total = len(DATASET_CATALOG_CONFIG)
    return replace_delimited_block(
        AGENTS_PATH, "AGENTS_DATASET_COUNT", str(total), check_only=check_only, separator=""
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
]


def sync_all_docs(check_only=False):
    return [fn.__name__ for fn in SYNC_FUNCS if fn(check_only=check_only)]
