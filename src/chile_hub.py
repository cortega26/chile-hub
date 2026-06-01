import json
import argparse
from pathlib import Path

import polars as pl


ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DATASET_CATALOG_PATH = NORMALIZED_DIR / "dataset_catalog.json"
ARTIFACT_MANIFEST_PATH = NORMALIZED_DIR / "artifact_manifest.json"
HUB_HEALTH_PATH = NORMALIZED_DIR / "hub_health.json"
HUB_BUNDLE_PATH = NORMALIZED_DIR / "hub_bundle.json"
REDISTRIBUTION_REPORT_PATH = NORMALIZED_DIR / "redistribution_report.json"
PROVENANCE_REPORT_PATH = NORMALIZED_DIR / "provenance_report.json"
DRIFT_REPORT_PATH = NORMALIZED_DIR / "drift_report.json"


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

    def _load_hub_health(self):
        with HUB_HEALTH_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_hub_bundle(self):
        with HUB_BUNDLE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_redistribution_report(self):
        with REDISTRIBUTION_REPORT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_provenance_report(self):
        with PROVENANCE_REPORT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_drift_report(self):
        with DRIFT_REPORT_PATH.open("r", encoding="utf-8") as f:
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
                "reuse_status": entry.get("reuse_policy", {}).get("status"),
                "reuse_license": entry.get("reuse_policy", {}).get("license"),
                "attribution_required": entry.get("reuse_policy", {}).get("attribution_required"),
                "freshness_status": entry.get("freshness", {}).get("status"),
                "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                "coverage_status": entry.get("coverage", {}).get("status"),
                "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                "validation_status": entry.get("validation_status"),
                "warning_count": len(entry.get("warnings", [])),
                "drift_status": entry.get("drift", {}).get("status"),
                "drift_summary": entry.get("drift", {}).get("summary"),
                "degradation_status": entry.get("degradation", {}).get("status"),
                "degradation_impact": entry.get("degradation", {}).get("impact"),
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

    def shared_artifacts(self, shared_type=None, format=None):
        artifacts = [entry for entry in self.artifacts() if entry.get("shared_type")]
        if shared_type is not None:
            artifacts = [entry for entry in artifacts if entry.get("shared_type") == shared_type]
        if format is not None:
            artifacts = [entry for entry in artifacts if entry.get("format") == format]
        return artifacts

    def reports(self):
        return self.bundle().get("reports", {})

    def get_report(self, shared_type, format):
        for entry in self.reports().values():
            if entry.get("shared_type") == shared_type and entry.get("format") == format:
                return entry
        raise KeyError(
            f"Reporte '{shared_type}' con formato '{format}' no existe en el bundle."
        )

    def overview(self):
        health = self.health()
        bundle = self.bundle()
        packages = self.packages()
        shared_artifacts = self.shared_artifacts()
        return {
            "generated_at_utc": health.get("generated_at_utc"),
            "overall_status": health.get("overall_status"),
            "dataset_count": health.get("dataset_count"),
            "live_count": health.get("live_count"),
            "fallback_count": health.get("fallback_count"),
            "stale_count": health.get("stale_count"),
            "drifted_count": health.get("drifted_count"),
            "degraded_count": health.get("degraded_count"),
            "partial_coverage_count": health.get("partial_coverage_count"),
            "warning_count": health.get("warning_count"),
            "shared_artifact_count": len(shared_artifacts),
            "package_count": len(packages),
            "report_keys": sorted(bundle.get("reports", {}).keys()),
            "datasets": [
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "validation_status": entry.get("validation_status"),
                    "freshness_status": entry.get("freshness_status"),
                    "coverage_status": entry.get("coverage_status"),
                    "drift_status": entry.get("drift_status"),
                }
                for entry in health.get("datasets", [])
            ],
        }

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
                    "reuse_status": entry.get("reuse_policy", {}).get("status"),
                    "reuse_license": entry.get("reuse_policy", {}).get("license"),
                    "attribution_required": entry.get("reuse_policy", {}).get("attribution_required"),
                    "freshness_status": entry.get("freshness", {}).get("status"),
                    "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                    "coverage_status": entry.get("coverage", {}).get("status"),
                    "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                    "warning_count": len(entry.get("warnings", [])),
                    "drift_status": entry.get("drift", {}).get("status"),
                    "drift_summary": entry.get("drift", {}).get("summary"),
                    "degradation_status": entry.get("degradation", {}).get("status"),
                    "degradation_impact": entry.get("degradation", {}).get("impact"),
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

    def health(self):
        return self._load_hub_health()

    def bundle(self):
        return self._load_hub_bundle()

    def packages(self):
        manifest = self._load_artifact_manifest()
        return manifest.get("packages", [])

    def redistribution(self):
        return self._load_redistribution_report()

    def provenance(self):
        return self._load_provenance_report()

    def drift(self):
        return self._load_drift_report()


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

    shared_artifacts_parser = subparsers.add_parser("shared-artifacts", help="Mostrar artefactos compartidos del hub")
    shared_artifacts_parser.add_argument("--shared-type", help="Filtrar por shared_type")
    shared_artifacts_parser.add_argument("--format", help="Filtrar por formato, por ejemplo json o markdown")

    report_parser = subparsers.add_parser("report", help="Resolver metadata de un reporte compartido")
    report_parser.add_argument("shared_type", help="shared_type del reporte, por ejemplo hub_health")
    report_parser.add_argument("--format", default="json", help="Formato del reporte, por ejemplo json o markdown")

    subparsers.add_parser("inventory", help="Mostrar inventario compacto de datasets y artefactos")
    subparsers.add_parser("overview", help="Mostrar vista agregada compacta del hub")
    subparsers.add_parser("health", help="Mostrar salud agregada del hub")
    subparsers.add_parser("bundle", help="Mostrar bundle consolidado del hub")
    subparsers.add_parser("packages", help="Mostrar paquetes publicables del hub")
    subparsers.add_parser("redistribution", help="Mostrar inventario de redistribucion del hub")
    subparsers.add_parser("provenance", help="Mostrar inventario de procedencia del hub")
    subparsers.add_parser("drift", help="Mostrar inventario de drift operativo del hub")

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

    if args.command == "shared-artifacts":
        print(json.dumps(hub.shared_artifacts(args.shared_type, args.format), ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        print(json.dumps(hub.get_report(args.shared_type, args.format), ensure_ascii=False, indent=2))
        return

    if args.command == "inventory":
        print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))
        return

    if args.command == "overview":
        print(json.dumps(hub.overview(), ensure_ascii=False, indent=2))
        return

    if args.command == "health":
        print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
        return

    if args.command == "bundle":
        print(json.dumps(hub.bundle(), ensure_ascii=False, indent=2))
        return

    if args.command == "packages":
        print(json.dumps(hub.packages(), ensure_ascii=False, indent=2))
        return

    if args.command == "redistribution":
        print(json.dumps(hub.redistribution(), ensure_ascii=False, indent=2))
        return

    if args.command == "provenance":
        print(json.dumps(hub.provenance(), ensure_ascii=False, indent=2))
        return

    if args.command == "drift":
        print(json.dumps(hub.drift(), ensure_ascii=False, indent=2))
        return

    if args.command == "summary":
        print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
