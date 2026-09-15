import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATION_PATH = ROOT_DIR / "src" / "validation.py"
BUILD_PATH = ROOT_DIR / "src" / "build_dev_db.py"

ALLOWED_UNREGISTERED_VALIDATORS = {
    # Removed from the active catalog, retained for a future official POI source.
    "puntos_interes",
    # geometria_comunal es candidate/bajo_demanda (como delincuencia_comunal y
    # autoridades_locales): su extractor NO corre en `make extract`, por lo que
    # no participa del build diario de build_dev_db.py. Se valida y publica vía
    # su propio script (scripts/build_geometria_comunal.py), no en el pipeline
    # diario -- ver ADR-012.
    "geometria_comunal",
}

ALLOWED_WITHOUT_DEDICATED_VALIDATOR = {
    # Semantic alias that reuses validate_comunas() by design.
    "comunas_enriquecidas",
}

# Claves del catálogo sin entrada en el bloque `validations = {...}` de
# build_dev_db.py. Cada una necesita carril + razón explícitos: un dataset
# declarado en el catálogo pero nunca validado publica (o desaparece) en
# silencio (Plan 088, AGENTS.md §10). Al ganar un build path, la entrada se
# mueve a un registro real — el gate fuerza esa edición.
ALLOWED_UNVALIDATED_DATASETS = {
    # candidate/bajo_demanda (ADR-012): su extractor NO corre en `make
    # extract`; se valida y publica vía scripts/build_geometria_comunal.py.
    "geometria_comunal": "candidate lane, separate build script (ADR-012)",
    # rejected/deprecated 2026-09-15: extractor neutralizado, fuera del bundle.
    "delincuencia_comunal": "rejected lane, deprecated 2026-09-15",
    # candidate/bajo_demanda: extractor + doc existen pero no hay build path
    # en build_dev_db.py (sin staging/normalized). Requiere plan de dataset
    # propio (validate_autoridades_locales + wiring) para salir de aquí.
    "autoridades_locales": "candidate lane bajo_demanda, no build path yet",
}


def load_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validation_functions() -> set[str]:
    tree = load_tree(VALIDATION_PATH)
    return {
        node.name.removeprefix("validate_")
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("validate_")
    }


def collect_validation_keys_from_dict(node: ast.Dict) -> set[str]:
    keys = set()
    for key, value in zip(node.keys, node.values, strict=False):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            keys.add(key.value)
        elif key is None and isinstance(value, ast.IfExp) and isinstance(value.body, ast.Dict):
            keys.update(collect_validation_keys_from_dict(value.body))
    return keys


def registered_validation_keys() -> set[str]:
    tree = load_tree(BUILD_PATH)
    keys = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "validations" for target in node.targets
        ):
            continue
        # `validations` se asigna en dos lugares: el literal dict en
        # `_compute_validations()` y la llamada `validations = _compute_validations(...)`
        # en `main()`. Solo interesa el dict; las demás asignaciones se ignoran.
        if not isinstance(node.value, ast.Dict):
            continue
        keys.update(collect_validation_keys_from_dict(node.value))
    if not keys:
        raise SystemExit("ERROR: could not find validations = {...} in build_dev_db.py")
    return keys


def catalog_keys() -> set[str]:
    import json as _json

    catalog_path = ROOT_DIR / "data" / "dataset_catalog_config.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        return set(_json.load(f).keys())


def main() -> None:
    functions = validation_functions()
    registered = registered_validation_keys()
    catalog = catalog_keys()

    unregistered = sorted(functions - registered - ALLOWED_UNREGISTERED_VALIDATORS)
    missing_dedicated = sorted(registered - functions - ALLOWED_WITHOUT_DEDICATED_VALIDATOR)
    unvalidated = sorted(catalog - registered - set(ALLOWED_UNVALIDATED_DATASETS))

    if unregistered or missing_dedicated or unvalidated:
        messages = []
        if unregistered:
            messages.append(
                "validators not registered in build_dev_db.py: " + ", ".join(unregistered)
            )
        if missing_dedicated:
            messages.append(
                "validation keys without validate_* functions: " + ", ".join(missing_dedicated)
            )
        if unvalidated:
            messages.append(
                "catalog datasets without validation entry in build_dev_db.py "
                "(add a validator or an explicit ALLOWED_UNVALIDATED_DATASETS reason): "
                + ", ".join(unvalidated)
            )
        raise SystemExit("ERROR: " + "; ".join(messages))

    print(
        "validation registration ok: "
        f"{len(registered)} validation keys, {len(functions)} validate_* functions, "
        f"{len(catalog)} catalog keys "
        f"({len(ALLOWED_UNVALIDATED_DATASETS)} with explicit unvalidated exemption)"
    )


if __name__ == "__main__":
    main()
