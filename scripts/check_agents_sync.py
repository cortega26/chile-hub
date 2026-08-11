"""Verifica hechos contables de AGENTS.md contra su fuente de verdad.

Complementa a `scripts/sync_docs.py` (que regenera los bloques delimitados
`START_AGENTS_*`): este script cubre la prosa EDITORIAL de AGENTS.md que
§12 no automatiza (a propósito) y que por eso tiende a stale — conteos de
líneas usados como áncoras de lectura, listas de módulos en el árbol del
§2, la tabla de capas del §1 y el conteo de archivos de test del árbol.

Regla: solo verifica hechos contables (números y existencia de archivos),
nunca prosa. Si un hecho no es derivable mecánicamente, no se chequea aquí.

Corre en `make doctor` y en el job `quality` de CI. Stdlib-only (igual que
`check_landing_sync.py` y `sync_docs.py`).
"""

import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_PATH = os.path.join(ROOT_DIR, "AGENTS.md")
SRC_DIR = os.path.join(ROOT_DIR, "src")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
BUILDERS_DIR = os.path.join(SRC_DIR, "builders")
CHILEHUB_DIR = os.path.join(SRC_DIR, "chile_hub")
CATALOG_PATH = os.path.join(ROOT_DIR, "data", "dataset_catalog_config.json")

ERRORS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)


def wc_lines(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def load_catalog() -> dict:
    import json

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw.get("datasets", raw) if isinstance(raw, dict) else dict(raw)


# ---------------------------------------------------------------------------
# 1. Áncoras de líneas: `archivo (N líneas)` en el árbol §2 y en §2½.
#    El nombre puede ser un path relativo (`chile_hub/pipeline_status_utils.py`)
#    o un basename ambiguo (`core.py`); en ese caso pasa si ALGÚN archivo
#    de src/ con ese basename coincide con el conteo declarado.
# ---------------------------------------------------------------------------
LINE_COUNT_PATTERN = re.compile(r"([\w/]+\.py)[^\n]*?\((\d{1,3}(?: \d{3})*) líneas\)")


def _find_by_basename(basename: str) -> list[str]:
    found = []
    for dirpath, _dirs, filenames in os.walk(SRC_DIR):
        if "__pycache__" in dirpath:
            continue
        for fname in filenames:
            if fname == basename:
                found.append(os.path.join(dirpath, fname))
    return found


def check_line_count_anchors(content: str) -> None:
    for name, claimed in LINE_COUNT_PATTERN.findall(content):
        claimed_count = int(claimed.replace(" ", ""))
        if "/" in name:
            rel = name[len("src/") :] if name.startswith("src/") else name
            candidates = [os.path.join(SRC_DIR, rel)]
        else:
            candidates = _find_by_basename(name)
        if not candidates:
            fail(
                f"AGENTS.md cita '{name} (… líneas)' pero no existe ningún archivo "
                f"con ese nombre bajo src/. ¿Se renombró o eliminó el módulo?"
            )
            continue
        matching = [p for p in candidates if wc_lines(p) == claimed_count]
        if not matching:
            actual = "; ".join(f"{p}: {wc_lines(p)}" for p in sorted(candidates))
            fail(
                f"AGENTS.md dice '{name} ({claimed} líneas)' pero el conteo real es: "
                f"{actual}. Corre `make sync-docs` si es un bloque delimitado, o "
                f"actualiza el número a mano."
            )


# ---------------------------------------------------------------------------
# 2. Árbol del §2: las listas de módulos de builders/ y del paquete chile_hub/
#    deben existir. (La lista de extractores ya se regenera vía
#    START_AGENTS_EXTRACTOR_LIST en doc_sync.py.)
# ---------------------------------------------------------------------------
def check_builders_list(content: str) -> None:
    match = re.search(r"builders/\s+Módulos del pipeline[^(]*\(([^)]+)\)", content)
    if not match:
        fail("AGENTS.md: no se encontró la lista de módulos de builders/ en el árbol del §2.")
        return
    real = {f[:-3] for f in os.listdir(BUILDERS_DIR) if f.endswith(".py") and f != "__init__.py"}
    for module in match.group(1).split(", "):
        module = module.strip()
        if module not in real:
            fail(
                f"AGENTS.md lista '{module}' en builders/ pero no existe en src/builders/. "
                f"¿Se eliminó o renombró? Módulos reales: {', '.join(sorted(real))}."
            )


def check_chilehub_package_list(content: str) -> None:
    subtree = content[content.index("chile_hub/                 Paquete") :]
    subtree = subtree[: subtree.index("└── pipeline_status_utils.py")]
    named = re.findall(r"│   │   [├└]── ([\w]+\.py)", subtree)
    real = {f for f in os.listdir(CHILEHUB_DIR) if f.endswith(".py")}
    for module in named:
        if module not in real:
            fail(
                f"AGENTS.md lista '{module}' en el paquete chile_hub/ pero no existe "
                f"en src/chile_hub/. Módulos reales: {', '.join(sorted(real))}."
            )


# ---------------------------------------------------------------------------
# 3. Tabla de capas del §1: cada dataset del catálogo debe tener su fila.
#    Mapa curado: clave de catálogo -> fragmento distintivo de la fila.
#    Si agregas un dataset y su fila no matchea por nombre, agrega la entrada
#    aquí junto con la fila en AGENTS.md.
# ---------------------------------------------------------------------------
CATALOG_KEY_TO_ROW_FRAGMENT = {
    "regiones": "División Político-Administrativa",
    "provincias": "División Político-Administrativa",
    "comunas": "División Político-Administrativa",
    "comunas_enriquecidas": "Comunas Enriquecidas",
    "indicadores": "Indicadores Económicos",
    "censo_comunal": "Censo Comunal 2024",
    "censo_hogares_viviendas": "Censo Hogares y Viviendas 2024",
    "establecimientos_salud": "Establecimientos de Salud",
    "distritos_electorales": "Distritos Electorales",
    "establecimientos_educacionales": "Establecimientos Educacionales",
    "finanzas_municipales": "Finanzas Municipales",
    "resultados_educacionales": "Resultados Educacionales",
    "indicadores_urbanos_siedu": "Indicadores Urbanos SIEDU",
    "perfil_territorial_comunal": "Perfil Territorial Comunal",
    "empresas": "Empresas (RES)",
    "pobreza_comunal": "Pobreza Comunal (SAE)",
    "consumo_electrico_comunal": "Consumo Eléctrico Comunal",
    "partidos_politicos": "Partidos Políticos",
    "autoridades_electas": "Autoridades Electas",
    "delincuencia_comunal": "Delincuencia Comunal",
    "autoridades_locales": "Autoridades Locales",
    "geometria_comunal": "Geometría Comunal",
}


def check_layers_table(content: str) -> None:
    catalog = load_catalog()
    table_start = content.index("| Capa | Fuente | Descripción |")
    table_end = content.index("**El objetivo no es tener todos los datos de Chile.")
    table = content[table_start:table_end]
    for key in catalog:
        fragment = CATALOG_KEY_TO_ROW_FRAGMENT.get(key)
        if fragment is None:
            fail(
                f"Dataset '{key}' sin entrada en CATALOG_KEY_TO_ROW_FRAGMENT de "
                f"scripts/check_agents_sync.py. Agrega su fragmento de fila (y la fila "
                f"en la tabla del §1 de AGENTS.md)."
            )
            continue
        if fragment not in table:
            fail(
                f"AGENTS.md §1 no tiene fila para el dataset '{key}' (buscó '{fragment}'). "
                f"Agrega la fila a la tabla de capas (y la entrada en este script si el "
                f"nombre no matchea)."
            )


# ---------------------------------------------------------------------------
# 4. Árbol del §2: conteo de archivos de test y existencia de e2e/fixtures.
#    (El contenido de la tabla completa se regenera vía START_AGENTS_TEST_TABLE.)
# ---------------------------------------------------------------------------
def check_tests_tree(content: str) -> None:
    test_count_line = re.search(r"tests/\s+(\d+) archivos", content)
    real_count = len(
        [f for f in os.listdir(TESTS_DIR) if f.startswith("test_") and f.endswith(".py")]
    )
    if test_count_line and int(test_count_line.group(1)) != real_count:
        fail(
            f"AGENTS.md dice '{test_count_line.group(1)} archivos' para tests/ pero hay "
            f"{real_count} test_*.py. Actualiza el árbol del §2."
        )
    for subdir in ("e2e", "fixtures"):
        if f"tests/{subdir}/" not in content:
            continue
        if not os.path.isdir(os.path.join(TESTS_DIR, subdir)):
            fail(
                f"AGENTS.md referencia tests/{subdir}/ en el árbol del §2 pero el "
                f"directorio no existe."
            )


def main() -> None:
    with open(AGENTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    check_line_count_anchors(content)
    check_builders_list(content)
    check_chilehub_package_list(content)
    check_layers_table(content)
    check_tests_tree(content)

    if ERRORS:
        print("check_agents_sync: AGENTS.md desincronizado con el código:\n")
        for msg in ERRORS:
            print(f"  - {msg}")
        sys.exit(1)
    print("check_agents_sync: hechos contables de AGENTS.md OK")


if __name__ == "__main__":
    main()
