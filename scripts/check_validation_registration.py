import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATION_PATH = ROOT_DIR / "src" / "validation.py"
BUILD_PATH = ROOT_DIR / "src" / "build_dev_db.py"

ALLOWED_UNREGISTERED_VALIDATORS = {
    # Removed from the active catalog, retained for a future official POI source.
    "puntos_interes",
}

ALLOWED_WITHOUT_DEDICATED_VALIDATOR = {
    # Semantic alias that reuses validate_comunas() by design.
    "comunas_enriquecidas",
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


def main() -> None:
    functions = validation_functions()
    registered = registered_validation_keys()

    unregistered = sorted(functions - registered - ALLOWED_UNREGISTERED_VALIDATORS)
    missing_dedicated = sorted(registered - functions - ALLOWED_WITHOUT_DEDICATED_VALIDATOR)

    if unregistered or missing_dedicated:
        messages = []
        if unregistered:
            messages.append(
                "validators not registered in build_dev_db.py: " + ", ".join(unregistered)
            )
        if missing_dedicated:
            messages.append(
                "validation keys without validate_* functions: " + ", ".join(missing_dedicated)
            )
        raise SystemExit("ERROR: " + "; ".join(messages))

    print(
        "validation registration ok: "
        f"{len(registered)} validation keys, {len(functions)} validate_* functions"
    )


if __name__ == "__main__":
    main()
