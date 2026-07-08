import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_CATALOG_PATH = ROOT_DIR / "data" / "dataset_catalog_config.json"
CONTRACTS_DIR = ROOT_DIR / "contracts" / "datasets"
DOCS_DIR = ROOT_DIR / "docs" / "datasets"

# Excepciones documentadas: datasets sin contrato o doc dedicado todavía.
# Vacío hoy — agregar aquí solo con una razón explícita si aparece un caso legítimo.
ALLOWED_MISSING_CONTRACT: set[str] = set()
ALLOWED_MISSING_DOC: set[str] = set()

# Rutas que disparan una regla de co-cambio -> al menos una de sus rutas
# compañeras debe aparecer también en el diff. Si agregas una ruta nueva con
# esta misma relación (ej. un módulo más en src/), suma la regla aquí.
COMPANION_RULES: dict[str, list[str]] = {
    "data/dataset_catalog_config.json": [
        "AGENTS.md",
        "SOURCE_OF_TRUTH.md",
        "docs/datasets/",
    ],
    "data/source_registry.json": [
        "AGENTS.md",
        "docs/datasets/",
        "docs/dataset-inclusion-criteria.md",
    ],
    "contracts/datasets/": ["docs/datasets/"],
    "src/validation.py": ["tests/test_validation.py", "tests/test_pipeline_logic.py"],
    "src/extractors/": ["tests/test_extractors.py"],
    "src/build_dev_db.py": ["tests/test_pipeline_logic.py", "tests/test_chile_hub.py"],
    ".github/workflows/pipeline-check.yml": ["AGENTS.md"],
    ".github/workflows/monthly-scrape.yml": ["AGENTS.md"],
    "Makefile": ["AGENTS.md", "README.md"],
}

# Módulos compartidos de src/extractors/ que no representan un dataset propio;
# no deben disparar la regla "src/extractors/" -> "tests/test_extractors.py".
EXTRACTOR_RULE_EXCLUDED_PATHS = {
    "src/extractors/base.py",
    "src/extractors/http_utils.py",
    "src/extractors/region_utils.py",
    "src/extractors/source_adapter.py",
    "src/extractors/__init__.py",
}


def dataset_keys() -> set[str]:
    with open(DATASET_CATALOG_PATH, "r", encoding="utf-8") as f:
        return set(json.load(f).keys())


def check_registry() -> list[str]:
    errors = []
    for key in sorted(dataset_keys()):
        if key not in ALLOWED_MISSING_CONTRACT:
            contract_path = CONTRACTS_DIR / f"{key}.schema.json"
            if not contract_path.is_file():
                errors.append(f"falta contrato de esquema para '{key}': {contract_path}")
        if key not in ALLOWED_MISSING_DOC:
            doc_path = DOCS_DIR / f"{key}.md"
            if not doc_path.is_file():
                errors.append(f"falta documentación de dataset para '{key}': {doc_path}")
    return errors


def matches_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix)


def check_companions(changed_files: list[str]) -> list[str]:
    errors = []
    for trigger_prefix, companion_prefixes in COMPANION_RULES.items():
        triggered = [
            path
            for path in changed_files
            if matches_prefix(path, trigger_prefix) and path not in EXTRACTOR_RULE_EXCLUDED_PATHS
        ]
        if not triggered:
            continue
        has_companion = any(
            matches_prefix(path, companion_prefix)
            for path in changed_files
            for companion_prefix in companion_prefixes
        )
        if not has_companion:
            errors.append(
                f"'{trigger_prefix}' cambió ({', '.join(sorted(triggered))}) pero ninguna "
                f"ruta compañera cambió en el mismo diff (se esperaba alguna de: "
                f"{', '.join(companion_prefixes)})"
            )
    return errors


def read_changed_files_from(source: str) -> list[str]:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def diff_changed_files(base: str) -> list[str]:
    try:
        # Diff de dos puntos (no de tres): compara los árboles de `base` y HEAD
        # directamente, sin requerir un merge-base — funciona con clones parciales
        # (fetch-depth acotado) como los que usa CI.
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"ERROR: no se pudo calcular el diff contra '{base}': {exc.stderr.strip()}"
        ) from exc
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica que la documentación/tests estén cableados al código.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser(
        "registry",
        help="Verifica que cada dataset de data/dataset_catalog_config.json tenga "
        "su contrato de esquema y su doc en docs/datasets/.",
    )

    companions_parser = subparsers.add_parser(
        "companions",
        help="Verifica reglas de co-cambio (COMPANION_RULES) sobre un conjunto de "
        "rutas modificadas.",
    )
    source_group = companions_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--base", help="Ref de git contra el cual calcular el diff.")
    source_group.add_argument(
        "--changed-files-from",
        help="Archivo con una ruta por línea, o '-' para leer desde stdin.",
    )

    args = parser.parse_args()

    if args.mode == "registry":
        errors = check_registry()
    else:
        changed_files = (
            read_changed_files_from(args.changed_files_from)
            if args.changed_files_from
            else diff_changed_files(args.base)
        )
        errors = check_companions(changed_files)

    if errors:
        raise SystemExit("ERROR: " + "; ".join(errors))

    print(f"check_companion_paths ok (modo: {args.mode})")


if __name__ == "__main__":
    main()
