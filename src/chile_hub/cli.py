"""Punto de entrada de consola para chile-hub.

TECHDEBT-02: el CLI (build_parser/_main/main/_print_result) se movió de
``core.py`` (god module de ~2.6K líneas) a este módulo. ``core.py`` queda
solo con la API pública; este módulo orquesta la API.
"""

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

from .core import ChileHub, ChileHubDataManager
from .exceptions import ChileHubError

__all__ = ["main"]


def _print_result(result, fmt="json", output=None):
    """Imprime un resultado dict/list en el formato solicitado."""
    if output:
        import polars as pl

        if isinstance(result, pl.DataFrame):
            if output == "csv":
                result.write_csv(sys.stdout)
            elif output == "parquet":
                result.write_parquet(sys.stdout.buffer)
            elif output == "json":
                result.write_json(sys.stdout)  # type: ignore[arg-type]  # TextIO es IOBase; falso positivo en stubs de Polars
            return
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # table: convertir dict a string formateado
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"{k}: {v}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    print(json.dumps(item, ensure_ascii=False, indent=2))
                else:
                    print(item)
        else:
            print(result)


def _output_dataframe(df, output, fmt):
    """Escribe un DataFrame a stdout o archivo según output y fmt."""
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if output.endswith(".csv"):
            df.write_csv(out_path)
        elif output.endswith(".parquet"):
            df.write_parquet(out_path)
        elif output.endswith(".json"):
            df.write_json(out_path)
        else:
            raise ValueError(
                f"Formato de archivo no soportado: {output}. Use .csv, .parquet o .json"
            )
        print(f"Escrito en {output}")
    elif fmt == "json":
        df.write_json(sys.stdout)
    else:
        print(df)


def build_parser():  # pragma: no cover — entry point de CLI, testeado vía integración
    parser = argparse.ArgumentParser(description="CLI minima para inspeccionar chile-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Mostrar version instalada de chile-hub")

    cache_parser = subparsers.add_parser("cache", help="Administrar cache local de datos")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)
    cache_subparsers.add_parser("status", help="Mostrar estado del cache local")
    cache_update_parser = cache_subparsers.add_parser(
        "update", help="Descargar o actualizar artefactos normalizados"
    )
    cache_update_parser.add_argument(
        "--data-version",
        default="latest",
        help="Version de datos o tag de GitHub Release a descargar",
    )
    cache_subparsers.add_parser("clear", help="Eliminar cache local de chile-hub")

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

    shared_artifacts_parser = subparsers.add_parser(
        "shared-artifacts", help="Mostrar artefactos compartidos del hub"
    )
    shared_artifacts_parser.add_argument("--shared-type", help="Filtrar por shared_type")
    shared_artifacts_parser.add_argument(
        "--artifact-format",
        help="Filtrar por formato de artifact, por ejemplo json o markdown",
    )
    shared_artifacts_parser.add_argument(
        "--output",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de shared-artifacts",
    )

    reports_parser = subparsers.add_parser("reports", help="Listar reportes compartidos del hub")
    reports_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del indice de reportes",
    )

    report_parser = subparsers.add_parser(
        "report", help="Resolver metadata de un reporte compartido"
    )
    report_parser.add_argument(
        "shared_type", help="shared_type del reporte, por ejemplo hub_health"
    )
    report_parser.add_argument(
        "--format",
        default="json",
        help="Formato del reporte, por ejemplo json o markdown",
    )

    inventory_parser = subparsers.add_parser(
        "inventory", help="Mostrar inventario compacto de datasets y artefactos"
    )
    inventory_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del inventario",
    )
    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Mostrar snapshot humano y compacto del hub"
    )
    snapshot_parser.add_argument(
        "--format",
        choices=["text", "table"],
        default="text",
        help="Formato de salida del snapshot",
    )
    overview_parser = subparsers.add_parser(
        "overview", help="Mostrar vista agregada compacta del hub"
    )
    overview_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de overview",
    )
    status_parser = subparsers.add_parser(
        "status", help="Mostrar status operativo compacto del hub"
    )
    status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de status",
    )
    status_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si overall_status no es 'ok'.",
    )
    subparsers.add_parser("dataset-status", help="Mostrar status detallado por dataset")
    subparsers.add_parser("dataset-changelog", help="Mostrar changelog de datasets")
    subparsers.add_parser("source-readiness", help="Mostrar madurez de fuente por dataset")
    subparsers.add_parser("dataset-quality", help="Mostrar puntuacion de calidad por dataset")
    health_parser = subparsers.add_parser("health", help="Mostrar salud agregada del hub")
    health_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de health",
    )
    health_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si overall_status no es 'ok'.",
    )
    subparsers.add_parser("bundle", help="Mostrar bundle consolidado del hub")
    freshness_audit_parser = subparsers.add_parser(
        "freshness-audit",
        help="Recalcular frescura contra el reloj actual sin reconstruir el hub",
    )
    freshness_audit_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de freshness-audit",
    )
    runtime_status_parser = subparsers.add_parser(
        "runtime-status",
        help="Combinar estado build y estado actual recalculado del hub",
    )
    runtime_status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de runtime-status",
    )
    top_issue_parser = subparsers.add_parser(
        "top-issue",
        help="Mostrar la capa prioritaria que requiere atención operativa",
    )
    top_issue_parser.add_argument(
        "--format",
        choices=["json", "text", "table"],
        default="json",
        help="Formato de salida de top-issue",
    )
    packages_parser = subparsers.add_parser("packages", help="Mostrar paquetes publicables del hub")
    packages_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de packages",
    )
    package_parser = subparsers.add_parser("package", help="Mostrar package principal del hub")
    package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    verify_package_parser = subparsers.add_parser(
        "verify-package",
        help="Mostrar metadata de verificación del package principal",
    )
    verify_package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    redistribution_parser = subparsers.add_parser(
        "redistribution", help="Mostrar inventario de redistribucion del hub"
    )
    redistribution_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de redistribution",
    )
    provenance_parser = subparsers.add_parser(
        "provenance", help="Mostrar inventario de procedencia del hub"
    )
    provenance_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de provenance",
    )
    drift_parser = subparsers.add_parser(
        "drift", help="Mostrar inventario de drift operativo del hub"
    )
    drift_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de drift",
    )

    summary_parser = subparsers.add_parser("summary", help="Mostrar resumen breve de datasets")
    summary_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del summary",
    )

    export_parser = subparsers.add_parser(
        "export", help="Exportar un dataset a un archivo (CSV, JSON o Parquet)"
    )
    export_parser.add_argument("dataset", help="Nombre del dataset a exportar")
    export_parser.add_argument(
        "--format",
        choices=["csv", "json", "parquet"],
        required=True,
        help="Formato del archivo de salida",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Ruta de destino del archivo exportado",
    )

    check_sources_parser = subparsers.add_parser(
        "check-sources",
        help="Verificar el estado de conexión de las fuentes externas oficiales",
    )
    check_sources_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida de check-sources",
    )
    check_sources_parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout en segundos para la conexión HTTP",
    )
    check_sources_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si alguna fuente está offline.",
    )

    # Subcomando: cross
    cross_parser = subparsers.add_parser("cross", help="Cruza datasets por clave territorial comun")
    cross_parser.add_argument("datasets", nargs="+", help="Datasets a cruzar (min 2)")
    cross_parser.add_argument(
        "--on", default="codigo_comuna", help="Clave de join (default: codigo_comuna)"
    )
    cross_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida (default: table)",
    )
    cross_parser.add_argument(
        "--output", default=None, help="Archivo de salida (.csv, .parquet, o .json)"
    )

    # Subcomando: resolve
    resolve_parser = subparsers.add_parser(
        "resolve", help="Resuelve nombres de comuna a codigos CUT (match determinista)"
    )
    resolve_parser.add_argument("names", nargs="+", help="Nombres de comuna a resolver")
    resolve_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida (default: table)",
    )
    resolve_parser.add_argument(
        "--output", default=None, help="Archivo de salida (.csv, .parquet, o .json)"
    )

    # Subcomando: search
    search_parser = subparsers.add_parser(
        "search", help="Busca datasets por keyword, fuente o madurez"
    )
    search_parser.add_argument(
        "query", nargs="?", default="", help="Texto de búsqueda en nombre y descripción"
    )
    search_parser.add_argument(
        "--source", default="", help="Filtrar por fuente (ej. 'INE', 'MINSAL')"
    )
    search_parser.add_argument(
        "--maturity", default="", help="Filtrar por madurez ('stable' o 'candidate')"
    )
    search_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida (default: json)",
    )

    # Subcomando: validate
    validate_parser = subparsers.add_parser(
        "validate", help="Valida un dataset del hub o un archivo CSV/Parquet contra su schema"
    )
    validate_parser.add_argument(
        "target",
        nargs="?",
        help="Nombre del dataset del hub, o ruta a un archivo .csv/.parquet",
    )
    validate_parser.add_argument(
        "--dataset",
        help="Nombre del dataset de referencia (ej. 'comunas'). Obligatorio si se valida "
        "un archivo externo; opcional si target es un dataset del hub.",
    )

    return parser


def _main(argv=None):  # pragma: no cover — dispatch de CLI, testeado vía smoke tests
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        try:
            version = importlib.metadata.version("chile-hub")
        except importlib.metadata.PackageNotFoundError:
            version = "1.0.1"
        print(version)
        return

    if args.command == "cache":
        manager = ChileHubDataManager(
            data_version=getattr(args, "data_version", "latest"),
        )
        if args.cache_command == "status":
            print(json.dumps(manager.status(), ensure_ascii=False, indent=2))
            return
        if args.cache_command == "update":
            data_dir = manager.update()
            print(data_dir)
            return
        if args.cache_command == "clear":
            manager.clear()
            print(manager.cache_root)
            return

    hub = ChileHub()

    if args.command == "export":
        df = hub.load_polars(args.dataset)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "csv":
            df.write_csv(out_path)
        elif args.format == "json":
            df.write_json(out_path)
        elif args.format == "parquet":
            df.write_parquet(out_path)
        print(
            f"Dataset '{args.dataset}' exportado exitosamente a '{args.output}' ({args.format.upper()})"
        )
        return

    if args.command == "check-sources":
        timeout = getattr(args, "timeout", 5)
        results = hub.check_sources(timeout=timeout)
        if args.format == "table":
            print(hub.check_sources_table(results), end="")
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            offline = [s for s in results if s.get("status") == "offline"]
            if offline:
                raise SystemExit(1)
        return

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
        if args.output == "table":
            print(
                hub.shared_artifacts_table(args.shared_type, args.artifact_format),
                end="",
            )
        else:
            print(
                json.dumps(
                    hub.shared_artifacts(args.shared_type, args.artifact_format),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    if args.command == "reports":
        if args.format == "table":
            print(hub.report_index_table(), end="")
        else:
            print(json.dumps(hub.report_index(), ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        print(
            json.dumps(
                hub.get_report(args.shared_type, args.format),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "inventory":
        if args.format == "table":
            print(hub.inventory_table(), end="")
        else:
            print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))
        return

    if args.command == "snapshot":
        if args.format == "table":
            print(hub.snapshot_table(), end="")
        else:
            print(hub.snapshot_text(), end="")
        return

    if args.command == "overview":
        if args.format == "table":
            print(hub.overview_table(), end="")
        else:
            print(json.dumps(hub.overview(), ensure_ascii=False, indent=2))
        return

    if args.command == "status":
        if args.format == "table":
            print(hub.status_table(), end="")
        else:
            print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            status_data = hub.status()
            if status_data.get("overall_status") != "ok":
                raise SystemExit(1)
        return

    if args.command == "dataset-status":
        print(json.dumps(hub.dataset_status(), ensure_ascii=False, indent=2))
        return

    if args.command == "dataset-changelog":
        print(json.dumps(hub.dataset_changelog(), ensure_ascii=False, indent=2))
        return

    if args.command == "source-readiness":
        print(json.dumps(hub.source_readiness(), ensure_ascii=False, indent=2))
        return

    if args.command == "dataset-quality":
        print(json.dumps(hub.dataset_quality(), ensure_ascii=False, indent=2))
        return

    if args.command == "health":
        if args.format == "table":
            print(hub.health_table(), end="")
        else:
            print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            health_data = hub.health()
            if health_data.get("overall_status") != "ok":
                raise SystemExit(1)
        return

    if args.command == "bundle":
        print(json.dumps(hub.bundle(), ensure_ascii=False, indent=2))
        return

    if args.command == "freshness-audit":
        if args.format == "table":
            print(hub.freshness_audit_table(), end="")
        else:
            print(json.dumps(hub.freshness_audit(), ensure_ascii=False, indent=2))
        return

    if args.command == "runtime-status":
        if args.format == "table":
            print(hub.runtime_status_table(), end="")
        else:
            print(json.dumps(hub.runtime_status(), ensure_ascii=False, indent=2))
        return

    if args.command == "top-issue":
        top_issue = hub.top_issue()
        if args.format == "table":
            print(hub.top_issue_table(), end="")
        elif args.format == "text":
            if not top_issue:
                print("chile-hub top issue\n\nSin top issue activo.\n", end="")
            else:
                print(
                    "chile-hub top issue\n\n"
                    f"dataset={top_issue.get('dataset')} | "
                    f"build={top_issue.get('build_freshness_status', 'unknown')} | "
                    f"current={top_issue.get('current_freshness_status', 'unknown')} | "
                    f"drift={top_issue.get('drift_status', 'unknown')} | "
                    f"warnings={top_issue.get('warning_count', 0)} | "
                    f"source_detail={top_issue.get('source_detail', 'unknown')} | "
                    f"reason={top_issue.get('diagnostic_summary', 'unknown')} | "
                    f"action={top_issue.get('recommended_action', 'unknown')}\n",
                    end="",
                )
        else:
            print(json.dumps(top_issue, ensure_ascii=False, indent=2))
        return

    if args.command == "packages":
        if args.format == "table":
            print(hub.packages_table(), end="")
        else:
            print(json.dumps(hub.packages(), ensure_ascii=False, indent=2))
        return

    if args.command == "package":
        print(json.dumps(hub.primary_package(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "verify-package":
        print(json.dumps(hub.package_verification(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "redistribution":
        if args.format == "table":
            print(hub.redistribution_table(), end="")
        else:
            print(json.dumps(hub.redistribution(), ensure_ascii=False, indent=2))
        return

    if args.command == "provenance":
        if args.format == "table":
            print(hub.provenance_table(), end="")
        else:
            print(json.dumps(hub.provenance(), ensure_ascii=False, indent=2))
        return

    if args.command == "drift":
        if args.format == "table":
            print(hub.drift_table(), end="")
        else:
            print(json.dumps(hub.drift(), ensure_ascii=False, indent=2))
        return

    if args.command == "cross":
        df = hub.cross_view(args.datasets, on=args.on)
        _output_dataframe(df, args.output, args.format)
        return

    if args.command == "resolve":
        df = hub.resolve_comunas(args.names)
        _output_dataframe(df, args.output, args.format)
        return

    if args.command == "search":
        results = hub.search_datasets(
            query=args.query,
            source_name=args.source,
            maturity=args.maturity,
        )
        _print_result(results, args.format)
        return

    if args.command == "validate":
        if args.target is None:
            # Sin argumento: mostrar ayuda del subcomando
            parser.parse_args(["validate", "--help"])
            return

        target_path = Path(args.target)

        # Si target existe como archivo, validar archivo externo
        if target_path.exists() and target_path.suffix in (".csv", ".parquet"):
            if not args.dataset:
                raise ChileHubError("Debes especificar --dataset al validar un archivo externo.")
            import polars as pl

            if target_path.suffix == ".csv":
                df = pl.read_csv(target_path, infer_schema_length=0)
            else:
                df = pl.read_parquet(target_path)
            result = hub.validate_user_data(df, args.dataset)
        else:
            # Si no es archivo, validar dataset del hub
            dataset_name = args.dataset if args.dataset else args.target
            result = hub.validate_dataset(dataset_name)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["status"] == "error":
            raise SystemExit(1)
        return

    if args.command == "summary":
        if args.format == "table":
            print(hub.summary_table(), end="")
        else:
            print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


def main(argv=None):  # pragma: no cover — entry point de consola
    try:
        return _main(argv)
    except ChileHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
