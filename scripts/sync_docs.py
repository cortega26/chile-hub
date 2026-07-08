import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.builders.doc_sync import sync_all_docs
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
    args = parser.parse_args()

    changed = []
    if sync_readme_layers_table(check_only=args.check):
        changed.append("sync_readme_layers_table")
    changed += sync_all_docs(check_only=args.check)

    if args.check:
        if changed:
            raise SystemExit(
                "ERROR: bloques de README.md desincronizados: "
                + ", ".join(changed)
                + " — corre 'make sync-docs' y commitea el resultado."
            )
        print("sync_docs --check: README.md al día")
    else:
        if changed:
            print("sync_docs: bloques actualizados: " + ", ".join(changed))
        else:
            print("sync_docs: sin cambios")


if __name__ == "__main__":
    main()
