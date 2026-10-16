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


def _add_format_parser(
    subparsers,
    name,
    help_text,
    format_help,
    *,
    choices=("json", "table"),
    default="json",
    exit_code=False,
):
    """Subparser con `--format` (y `--exit-code` opcional). Plan 132d."""
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("--format", choices=list(choices), default=default, help=format_help)
    if exit_code:
        parser.add_argument(
            "--exit-code",
            action="store_true",
            help="Retorna exit code 1 si overall_status no es 'ok'.",
        )
    return parser


def _add_cache_parser(subparsers):
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


def _add_show_parser(subparsers):
    show_parser = subparsers.add_parser("show", help="Mostrar metadata de un dataset")
    show_parser.add_argument("dataset", help="Nombre del dataset")


def _add_path_parser(subparsers):
    path_parser = subparsers.add_parser("path", help="Resolver path de salida de un dataset")
    path_parser.add_argument("dataset", help="Nombre del dataset")
    path_parser.add_argument(
        "--output",
        default="parquet",
        help="Tipo de output a resolver, por ejemplo parquet, json o sqlite_table",
    )


def _add_example_parser(subparsers):
    example_parser = subparsers.add_parser("example", help="Mostrar ejemplo de uso de un dataset")
    example_parser.add_argument("dataset", help="Nombre del dataset")
    example_parser.add_argument(
        "--kind",
        default="python",
        help="Tipo de ejemplo a mostrar, por ejemplo python, duckdb o cli",
    )


def _add_artifacts_parser(subparsers):
    artifacts_parser = subparsers.add_parser("artifacts", help="Mostrar artefactos publicables")
    artifacts_parser.add_argument(
        "dataset",
        nargs="?",
        help="Nombre opcional de dataset para filtrar artefactos",
    )


def _add_shared_artifacts_parser(subparsers):
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


def _add_report_parser(subparsers):
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


def _add_package_parsers(subparsers):
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


def _add_export_parser(subparsers):
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


def _add_check_sources_parser(subparsers):
    parser = _add_format_parser(
        subparsers,
        "check-sources",
        "Verificar el estado de conexión de las fuentes externas oficiales",
        "Formato de salida de check-sources",
        default="table",
        exit_code=True,
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout en segundos para la conexión HTTP",
    )


def _add_cross_parser(subparsers):
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


def _add_resolve_parser(subparsers, name, help_text, argument_help):
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("names", nargs="+", help=argument_help)
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida (default: table)",
    )
    parser.add_argument(
        "--output", default=None, help="Archivo de salida (.csv, .parquet, o .json)"
    )


def _add_search_parser(subparsers):
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


def _add_validate_parser(subparsers):
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


def build_parser():
    parser = argparse.ArgumentParser(description="CLI minima para inspeccionar chile-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Mostrar version instalada de chile-hub")

    _add_cache_parser(subparsers)

    subparsers.add_parser("list", help="Listar datasets disponibles")

    _add_show_parser(subparsers)
    _add_path_parser(subparsers)
    _add_example_parser(subparsers)
    _add_artifacts_parser(subparsers)
    _add_shared_artifacts_parser(subparsers)

    _add_format_parser(
        subparsers,
        "reports",
        "Listar reportes compartidos del hub",
        "Formato de salida del indice de reportes",
    )
    _add_report_parser(subparsers)
    _add_format_parser(
        subparsers,
        "inventory",
        "Mostrar inventario compacto de datasets y artefactos",
        "Formato de salida del inventario",
    )
    _add_format_parser(
        subparsers,
        "snapshot",
        "Mostrar snapshot humano y compacto del hub",
        "Formato de salida del snapshot",
        choices=("text", "table"),
        default="text",
    )
    _add_format_parser(
        subparsers,
        "overview",
        "Mostrar vista agregada compacta del hub",
        "Formato de salida de overview",
    )
    _add_format_parser(
        subparsers,
        "status",
        "Mostrar status operativo compacto del hub",
        "Formato de salida de status",
        exit_code=True,
    )
    subparsers.add_parser("dataset-status", help="Mostrar status detallado por dataset")
    subparsers.add_parser("dataset-changelog", help="Mostrar changelog de datasets")
    subparsers.add_parser("source-readiness", help="Mostrar madurez de fuente por dataset")
    subparsers.add_parser("dataset-quality", help="Mostrar puntuacion de calidad por dataset")
    _add_format_parser(
        subparsers,
        "health",
        "Mostrar salud agregada del hub",
        "Formato de salida de health",
        exit_code=True,
    )
    subparsers.add_parser("bundle", help="Mostrar bundle consolidado del hub")
    _add_format_parser(
        subparsers,
        "freshness-audit",
        "Recalcular frescura contra el reloj actual sin reconstruir el hub",
        "Formato de salida de freshness-audit",
    )
    _add_format_parser(
        subparsers,
        "runtime-status",
        "Combinar estado build y estado actual recalculado del hub",
        "Formato de salida de runtime-status",
    )
    _add_format_parser(
        subparsers,
        "top-issue",
        "Mostrar la capa prioritaria que requiere atención operativa",
        "Formato de salida de top-issue",
        choices=("json", "text", "table"),
    )
    _add_format_parser(
        subparsers,
        "packages",
        "Mostrar paquetes publicables del hub",
        "Formato de salida de packages",
    )
    _add_package_parsers(subparsers)
    _add_format_parser(
        subparsers,
        "redistribution",
        "Mostrar inventario de redistribucion del hub",
        "Formato de salida de redistribution",
    )
    _add_format_parser(
        subparsers,
        "provenance",
        "Mostrar inventario de procedencia del hub",
        "Formato de salida de provenance",
    )
    _add_format_parser(
        subparsers,
        "drift",
        "Mostrar inventario de drift operativo del hub",
        "Formato de salida de drift",
    )

    _add_format_parser(
        subparsers, "summary", "Mostrar resumen breve de datasets", "Formato de salida del summary"
    )

    _add_export_parser(subparsers)
    _add_check_sources_parser(subparsers)

    # Subcomando: cross
    _add_cross_parser(subparsers)

    # Subcomando: resolve
    _add_resolve_parser(
        subparsers,
        "resolve",
        "Resuelve nombres de comuna a codigos CUT (match determinista)",
        "Nombres de comuna a resolver",
    )

    # Subcomando: resolve-regiones
    _add_resolve_parser(
        subparsers,
        "resolve-regiones",
        "Resuelve nombres de región a códigos CUT (match determinista)",
        "Nombres de región a resolver",
    )

    # Subcomando: resolve-coords (reusa el parser de resolve: pares LAT,LON)
    # Nota: las coordenadas chilenas empiezan con `-`, así que argparse exige
    # el separador `--` antes del primer par (ej. `resolve-coords -- -33.4,-70.6`).
    _add_resolve_parser(
        subparsers,
        "resolve-coords",
        "Resuelve coordenadas LAT,LON a códigos CUT de comuna (match determinista)",
        "Pares LAT,LON a resolver (ej. -- -33.4489,-70.6693)",
    )

    _add_search_parser(subparsers)

    # Subcomando: validate
    _add_validate_parser(subparsers)

    return parser


def _cmd_version(args):
    try:
        version = importlib.metadata.version("chile-hub")
    except importlib.metadata.PackageNotFoundError:
        version = "1.0.1"
    print(version)


def _cmd_cache(args):
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


def _cmd_export(args):
    hub = ChileHub()
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


def _cmd_check_sources(args):
    hub = ChileHub()
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


def _cmd_list(args):
    hub = ChileHub()
    for dataset in hub.list_datasets():
        print(dataset)


def _cmd_show(args):
    hub = ChileHub()
    print(json.dumps(hub.get_dataset(args.dataset), ensure_ascii=False, indent=2))


def _cmd_path(args):
    hub = ChileHub()
    print(hub.get_output_path(args.dataset, args.output))


def _cmd_example(args):
    hub = ChileHub()
    print(hub.example_usage(args.dataset, args.kind))


def _cmd_artifacts(args):
    hub = ChileHub()
    print(json.dumps(hub.artifacts(args.dataset), ensure_ascii=False, indent=2))


def _cmd_shared_artifacts(args):
    hub = ChileHub()
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


def _cmd_reports(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.report_index_table(), end="")
    else:
        print(json.dumps(hub.report_index(), ensure_ascii=False, indent=2))


def _cmd_report(args):
    hub = ChileHub()
    print(
        json.dumps(
            hub.get_report(args.shared_type, args.format),
            ensure_ascii=False,
            indent=2,
        )
    )


def _cmd_inventory(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.inventory_table(), end="")
    else:
        print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))


def _cmd_snapshot(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.snapshot_table(), end="")
    else:
        print(hub.snapshot_text(), end="")


def _cmd_overview(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.overview_table(), end="")
    else:
        print(json.dumps(hub.overview(), ensure_ascii=False, indent=2))


def _cmd_status(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.status_table(), end="")
    else:
        print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
    if getattr(args, "exit_code", False):
        status_data = hub.status()
        if status_data.get("overall_status") != "ok":
            raise SystemExit(1)


def _cmd_dataset_status(args):
    hub = ChileHub()
    print(json.dumps(hub.dataset_status(), ensure_ascii=False, indent=2))


def _cmd_dataset_changelog(args):
    hub = ChileHub()
    print(json.dumps(hub.dataset_changelog(), ensure_ascii=False, indent=2))


def _cmd_source_readiness(args):
    hub = ChileHub()
    print(json.dumps(hub.source_readiness(), ensure_ascii=False, indent=2))


def _cmd_dataset_quality(args):
    hub = ChileHub()
    print(json.dumps(hub.dataset_quality(), ensure_ascii=False, indent=2))


def _cmd_health(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.health_table(), end="")
    else:
        print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
    if getattr(args, "exit_code", False):
        health_data = hub.health()
        if health_data.get("overall_status") != "ok":
            raise SystemExit(1)


def _cmd_bundle(args):
    hub = ChileHub()
    print(json.dumps(hub.bundle(), ensure_ascii=False, indent=2))


def _cmd_freshness_audit(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.freshness_audit_table(), end="")
    else:
        print(json.dumps(hub.freshness_audit(), ensure_ascii=False, indent=2))


def _cmd_runtime_status(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.runtime_status_table(), end="")
    else:
        print(json.dumps(hub.runtime_status(), ensure_ascii=False, indent=2))


def _cmd_top_issue(args):
    hub = ChileHub()
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


def _cmd_packages(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.packages_table(), end="")
    else:
        print(json.dumps(hub.packages(), ensure_ascii=False, indent=2))


def _cmd_package(args):
    hub = ChileHub()
    print(json.dumps(hub.primary_package(args.type), ensure_ascii=False, indent=2))


def _cmd_verify_package(args):
    hub = ChileHub()
    print(json.dumps(hub.package_verification(args.type), ensure_ascii=False, indent=2))


def _cmd_redistribution(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.redistribution_table(), end="")
    else:
        print(json.dumps(hub.redistribution(), ensure_ascii=False, indent=2))


def _cmd_provenance(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.provenance_table(), end="")
    else:
        print(json.dumps(hub.provenance(), ensure_ascii=False, indent=2))


def _cmd_drift(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.drift_table(), end="")
    else:
        print(json.dumps(hub.drift(), ensure_ascii=False, indent=2))


def _cmd_cross(args):
    hub = ChileHub()
    df = hub.cross_view(args.datasets, on=args.on)
    _output_dataframe(df, args.output, args.format)


def _cmd_resolve(args):
    hub = ChileHub()
    df = hub.resolve_comunas(args.names)
    _output_dataframe(df, args.output, args.format)


def _cmd_resolve_regiones(args):
    hub = ChileHub()
    df = hub.resolve_regiones(args.names)
    _output_dataframe(df, args.output, args.format)


def _parse_coords_pairs(names):
    """Parsea pares "LAT,LON" del CLI a tuplas de float (resolve-coords)."""
    points = []
    for raw in names:
        try:
            lat_str, lon_str = raw.split(",")
            points.append((float(lat_str), float(lon_str)))
        except ValueError:
            raise ChileHubError(
                f"Coordenada inválida {raw!r}: se espera el formato LAT,LON "
                "(ej. -33.4489,-70.6693)."
            ) from None
    return points


def _cmd_resolve_coords(args):
    hub = ChileHub()
    points = _parse_coords_pairs(args.names)
    try:
        df = hub.resolve_by_coords(points)
    except ValueError as exc:
        raise ChileHubError(str(exc)) from None
    _output_dataframe(df, args.output, args.format)


def _cmd_search(args):
    hub = ChileHub()
    results = hub.search_datasets(
        query=args.query,
        source_name=args.source,
        maturity=args.maturity,
    )
    _print_result(results, args.format)


def _cmd_validate(args):
    hub = ChileHub()
    if args.target is None:
        # Sin argumento: mostrar ayuda del subcomando
        build_parser().parse_args(["validate", "--help"])
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


def _cmd_summary(args):
    hub = ChileHub()
    if args.format == "table":
        print(hub.summary_table(), end="")
    else:
        print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))


HANDLERS = {
    "version": _cmd_version,
    "cache": _cmd_cache,
    "export": _cmd_export,
    "check-sources": _cmd_check_sources,
    "list": _cmd_list,
    "show": _cmd_show,
    "path": _cmd_path,
    "example": _cmd_example,
    "artifacts": _cmd_artifacts,
    "shared-artifacts": _cmd_shared_artifacts,
    "reports": _cmd_reports,
    "report": _cmd_report,
    "inventory": _cmd_inventory,
    "snapshot": _cmd_snapshot,
    "overview": _cmd_overview,
    "status": _cmd_status,
    "dataset-status": _cmd_dataset_status,
    "dataset-changelog": _cmd_dataset_changelog,
    "source-readiness": _cmd_source_readiness,
    "dataset-quality": _cmd_dataset_quality,
    "health": _cmd_health,
    "bundle": _cmd_bundle,
    "freshness-audit": _cmd_freshness_audit,
    "runtime-status": _cmd_runtime_status,
    "top-issue": _cmd_top_issue,
    "packages": _cmd_packages,
    "package": _cmd_package,
    "verify-package": _cmd_verify_package,
    "redistribution": _cmd_redistribution,
    "provenance": _cmd_provenance,
    "drift": _cmd_drift,
    "cross": _cmd_cross,
    "resolve": _cmd_resolve,
    "resolve-regiones": _cmd_resolve_regiones,
    "resolve-coords": _cmd_resolve_coords,
    "search": _cmd_search,
    "validate": _cmd_validate,
    "summary": _cmd_summary,
}


def _main(argv=None):
    """Parseo de argumentos y dispatch al handler del subcomando (plan 132d)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = HANDLERS.get(args.command)
    if handler is None:  # argparse restringe `command`; rama defensiva
        parser.error(f"comando no soportado: {args.command}")
        return None  # inalcanzable: parser.error termina en SystemExit(2)
    return handler(args)


def main(argv=None):  # pragma: no cover — entry point de consola
    try:
        return _main(argv)
    except ChileHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
