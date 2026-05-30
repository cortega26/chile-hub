import json
import argparse
from pathlib import Path

import polars as pl


ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DATASET_CATALOG_PATH = NORMALIZED_DIR / "dataset_catalog.json"


class ChileHub:
    def __init__(self, catalog_path=DATASET_CATALOG_PATH):
        self.catalog_path = Path(catalog_path)
        self.root_dir = self.catalog_path.resolve().parents[2]
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def list_datasets(self):
        return [entry["dataset"] for entry in self.catalog.get("datasets", [])]

    def get_dataset(self, dataset_name):
        for entry in self.catalog.get("datasets", []):
            if entry["dataset"] == dataset_name:
                return entry
        available = ", ".join(self.list_datasets())
        raise KeyError(f"Dataset '{dataset_name}' no existe. Disponibles: {available}")

    def get_output_path(self, dataset_name, output_type="parquet"):
        dataset = self.get_dataset(dataset_name)
        outputs = dataset.get("outputs", {})
        if output_type not in outputs:
            available = ", ".join(sorted(outputs.keys()))
            raise KeyError(
                f"Output '{output_type}' no existe para '{dataset_name}'. Disponibles: {available}"
            )
        return self.root_dir / outputs[output_type]

    def load_polars(self, dataset_name):
        path = self.get_output_path(dataset_name, "parquet")
        return pl.read_parquet(path)

    def summary(self):
        return [
            {
                "dataset": entry["dataset"],
                "source_mode": entry["source_mode"],
                "record_count": entry["record_count"],
                "join_keys": entry.get("join_keys", []),
                "confidence_tier": entry.get("confidence_tier"),
                "validation_status": entry.get("validation_status"),
            }
            for entry in self.catalog.get("datasets", [])
        ]


def build_parser():
    parser = argparse.ArgumentParser(description="CLI minima para inspeccionar chile-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Listar datasets disponibles")

    show_parser = subparsers.add_parser("show", help="Mostrar metadata de un dataset")
    show_parser.add_argument("dataset", help="Nombre del dataset")

    path_parser = subparsers.add_parser("path", help="Resolver path de salida de un dataset")
    path_parser.add_argument("dataset", help="Nombre del dataset")
    path_parser.add_argument(
        "--output",
        default="parquet",
        help="Tipo de output a resolver, por ejemplo parquet, json o sqlite_table",
    )

    subparsers.add_parser("summary", help="Mostrar resumen breve de datasets")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    hub = ChileHub()

    if args.command == "list":
        for dataset in hub.list_datasets():
            print(dataset)
        return

    if args.command == "show":
        print(json.dumps(hub.get_dataset(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "path":
        print(hub.get_output_path(args.dataset, args.output))
        return

    if args.command == "summary":
        print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
