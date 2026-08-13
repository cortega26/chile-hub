import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.builders.doc_sync import sync_all_docs, sync_readme_version_pin_example
from src.builders.reports import sync_readme_layers_table


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza hechos hardcodeados en README.md con su fuente de verdad."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="No escribe; falla si algún bloque quedaría desincronizado.",
    )
    parser.add_argument(
        "--version-only",
        action="store_true",
        help=(
            "Solo sincroniza el pin de versión (sync_readme_version_pin_example). "
            "Uso exclusivo del release: los bloques derivados de data/normalized "
            "(health, quality, layers) los escribe únicamente el publish diario — "
            "el release no debe regenerarlos desde un artifact potencialmente viejo "
            "(carrera release↔publish, ver fix/write-races)."
        ),
    )
    args = parser.parse_args()

    changed = []
    if args.version_only:
        if sync_readme_version_pin_example(check_only=args.check):
            changed.append("sync_readme_version_pin_example")
    else:
        if sync_readme_layers_table(check_only=args.check):
            changed.append("sync_readme_layers_table")
        changed += sync_all_docs(check_only=args.check)

    if args.check:
        if changed:
            raise SystemExit(
                "ERROR: bloques de README.md o AGENTS.md desincronizados: "
                + ", ".join(changed)
                + " — corre 'make sync-docs' y commitea el resultado."
            )
        print("sync_docs --check: README.md y AGENTS.md al día")
    else:
        if changed:
            print("sync_docs: bloques actualizados: " + ", ".join(changed))
        else:
            print("sync_docs: sin cambios")


if __name__ == "__main__":
    main()
