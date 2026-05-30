import json
import argparse
from pathlib import Path

import polars as pl


ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DATASET_CATALOG_PATH = NORMALIZED_DIR / "dataset_catalog.json"
ARTIFACT_MANIFEST_PATH = NORMALIZED_DIR / "artifact_manifest.json"


class ChileHub:
    def __init__(self, catalog_path=DATASET_CATALOG_PATH):
        self.catalog_path = Path(catalog_path)
        self.root_dir = self.catalog_path.resolve().parents[2]
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_artifact_manifest(self):
        with ARTIFACT_MANIFEST_PATH.open("r", encoding="utf-8") as f:
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

    def example_usage(self, dataset_name, kind="python"):
        dataset = self.get_dataset(dataset_name)
        examples = dataset.get("usage_examples", {})
        if kind not in examples:
            available = ", ".join(sorted(examples.keys()))
            raise KeyError(
                f"Example '{kind}' no existe para '{dataset_name}'. Disponibles: {available}"
            )
        return examples[kind]

    def summary(self):
        return [
            {
                "dataset": entry["dataset"],
                "source_mode": entry["source_mode"],
                "record_count": entry["record_count"],
                "join_keys": entry.get("join_keys", []),
                "confidence_tier": entry.get("confidence_tier"),
                "freshness_status": entry.get("freshness", {}).get("status"),
                "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                "validation_status": entry.get("validation_status"),
            }
            for entry in self.catalog.get("datasets", [])
        ]

    def artifacts(self, dataset_name=None):
        manifest = self._load_artifact_manifest()
        artifacts = manifest.get("artifacts", [])
        if dataset_name is None:
            return artifacts

        self.get_dataset(dataset_name)
        return [entry for entry in artifacts if entry.get("dataset") == dataset_name]

    def inventory(self):
        inventory = []
        manifest_artifacts = self.artifacts()
        by_dataset = {}
        for artifact in manifest_artifacts:
            dataset = artifact.get("dataset")
            if not dataset:
                continue
            by_dataset.setdefault(dataset, []).append(artifact)

        for entry in self.catalog.get("datasets", []):
            dataset_name = entry["dataset"]
            artifacts = sorted(
                by_dataset.get(dataset_name, []),
                key=lambda item: (item.get("output_type") or "", item.get("path") or ""),
            )
            published_outputs = [artifact["output_type"] for artifact in artifacts if artifact.get("output_type")]
            inventory.append(
                {
                    "dataset": dataset_name,
                    "source_mode": entry.get("source_mode"),
                    "record_count": entry.get("record_count"),
                    "validation_status": entry.get("validation_status"),
                    "confidence_tier": entry.get("confidence_tier"),
                    "freshness_status": entry.get("freshness", {}).get("status"),
                    "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                    "published_outputs": published_outputs,
                    "artifact_count": len(artifacts),
                    "total_size_bytes": sum(artifact.get("size_bytes", 0) for artifact in artifacts),
                    "artifacts": [
                        {
                            "path": artifact.get("path"),
                            "output_type": artifact.get("output_type"),
                            "size_bytes": artifact.get("size_bytes"),
                        }
                        for artifact in artifacts
                    ],
                }
            )
        return inventory


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

    example_parser = subparsers.add_parser("example", help="Mostrar ejemplo de uso de un dataset")
    example_parser.add_argument("dataset", help="Nombre del dataset")
    example_parser.add_argument(
        "--kind",
        default="python",
        help="Tipo de ejemplo a mostrar, por ejemplo python, duckdb o cli",
    )

    artifacts_parser = subparsers.add_parser("artifacts", help="Mostrar artefactos publicables")
    artifacts_parser.add_argument(
        "dataset",
        nargs="?",
        help="Nombre opcional de dataset para filtrar artefactos",
    )

    subparsers.add_parser("inventory", help="Mostrar inventario compacto de datasets y artefactos")

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

    if args.command == "example":
        print(hub.example_usage(args.dataset, args.kind))
        return

    if args.command == "artifacts":
        print(json.dumps(hub.artifacts(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "inventory":
        print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))
        return

    if args.command == "summary":
        print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
