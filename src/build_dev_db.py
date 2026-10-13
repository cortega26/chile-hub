import os
import sys

# ── Ajuste de sys.path ────────────────────────────────────────────────────────
# `python src/build_dev_db.py` no incluye el directorio raíz en sys.path, por lo
# que las importaciones absolutas del paquete `src.*` fallarían.  Se agrega la
# raíz del proyecto al inicio del path ANTES de cualquier import del paquete.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# ──────────────────────────────────────────────────────────────────────────────

from src.builders._logging import get_logger

log = get_logger("build_dev_db")


# Rutas, constantes y configuración de catálogo compartidas (re-exportadas para
# mantener compatibilidad con scripts externos y tests que las importan desde aquí;
# DATASET_CATALOG_CONFIG se consume vía build_dev_db en verify_pipeline.py y tests).
from src.builders._shared import (  # noqa: F401
    AUTORIDADES_ELECTAS_METADATA_PATH,
    CALIDAD_AIRE_METADATA_PATH,
    CENSO_HOGARES_METADATA_PATH,
    CENSO_METADATA_PATH,
    COMUNAS_METADATA_PATH,
    CONSUMO_ELECTRICO_COMUNAL_METADATA_PATH,
    DATASET_CATALOG_CONFIG,
    ELECTORAL_METADATA_PATH,
    EMPRESAS_METADATA_PATH,
    ESTADISTICAS_VITALES_METADATA_PATH,
    FINANZAS_METADATA_PATH,
    INDICADORES_METADATA_PATH,
    NORMALIZED_DIR,
    PARTIDOS_POLITICOS_METADATA_PATH,
    PERMISOS_EDIFICACION_METADATA_PATH,
    POBREZA_COMUNAL_METADATA_PATH,
    RESULTADOS_EDUCACIONALES_METADATA_PATH,
    SALUD_METADATA_PATH,
    SIEDU_METADATA_PATH,
    STAGING_DIR,
)
from src.builders.artifacts import (
    attach_publishable_package_to_manifest,
    write_artifact_manifest,
    write_hub_bundle_json,
    write_publishable_bundle_sha256,
    write_publishable_bundle_zip,
)
from src.builders.catalog import (
    write_dataset_catalog,
    write_pipeline_metadata,
)
from src.builders.data_package import build_data_package, write_data_package_json
from src.builders.dcat_catalog import write_dcat_catalog_json
from src.builders.doc_sync import sync_all_docs
from src.builders.formats import (
    EXCEL_MAX_ROWS_SKIP,
    SQLITE_MAX_ROWS,
    build_duckdb,
    build_excel,
    build_flat_files,
    build_sqlite,
)
from src.builders.inputs import load_staging_inputs
from src.builders.io_utils import (
    compute_sha256,
    write_json_atomic,
    write_parquet_atomic,
)

# build_coverage, build_degradation y build_drift se re-exportan para los tests
# (no se usan directamente aquí, solo a través de enrich_dataset_metadata).
from src.builders.metadata import (  # noqa: F401
    build_coverage,
    build_dataset_metadata,
    build_degradation,
    build_drift,
    build_freshness,
    build_freshness_warnings,
    build_indicator_delivery,
    enrich_dataset_metadata,
    ensure_directories,
    load_metadata,
    load_schema_contract,
)
from src.builders.reports import (
    MAPA_METRICAS_FILENAME,
    append_hub_health_history,
    build_dataset_changelog,
    build_dataset_quality,
    build_dataset_status,
    build_drift_report,
    build_hub_status,
    build_overview,
    build_provenance_report,
    build_redistribution_report,
    build_source_readiness,
    sync_readme_layers_table,
    write_dataset_changelog_json,
    write_dataset_quality_json,
    write_dataset_status_json,
    write_drift_report_json,
    write_hub_health_json,
    write_hub_status_json,
    write_mapa_metricas_json,
    write_overview_json,
    write_provenance_report_json,
    write_redistribution_report_json,
    write_source_readiness_json,
)
from src.pipeline_status_utils import (
    build_hub_health,
    write_dataset_catalog_markdown_file,
    write_dataset_quality_markdown_file,
    write_drift_report_markdown_file,
    write_hub_health_markdown_file,
    write_overview_markdown_file,
    write_provenance_report_markdown_file,
    write_redistribution_report_markdown_file,
    write_source_readiness_markdown_file,
    write_status_markdown_file,
)
from src.validation import (
    validate_autoridades_electas,
    validate_calidad_aire,
    validate_censo_comunal,
    validate_censo_hogares_viviendas,
    validate_comunas,
    validate_consumo_electrico_comunal,
    validate_distritos_electorales,
    validate_empresas,
    validate_establecimientos_educacionales,
    validate_establecimientos_salud,
    validate_estadisticas_vitales,
    validate_finanzas_municipales,
    validate_indicadores,
    validate_indicadores_urbanos_siedu,
    validate_partidos_politicos,
    validate_perfil_territorial_comunal,
    validate_permisos_edificacion,
    validate_pobreza_comunal,
    validate_provincias,
    validate_regiones,
    validate_resultados_educacionales,
)


def _load_inputs():
    """Carga metadatos de staging y lee todos los DataFrames de origen.

    Fachada de `src.builders.inputs.load_staging_inputs` (plan 132a): pasa los
    globales del módulo para preservar los overrides de los tests de
    caracterización (`patch.multiple` sobre STAGING_DIR/NORMALIZED_DIR).
    """
    return load_staging_inputs(STAGING_DIR, NORMALIZED_DIR)


def _compute_validations(dfs, meta):
    """Ejecuta las validaciones de todos los datasets; aborta si alguna falla."""
    df_comunas = dfs["comunas"]
    df_indicadores = dfs["indicadores"]
    df_censo = dfs["censo"]
    df_salud = dfs["salud"]
    df_censo_hogares = dfs["censo_hogares"]
    df_electoral = dfs["electoral"]
    df_educacionales = dfs["educacionales"]
    df_finanzas = dfs["finanzas"]
    df_resultados_educacionales = dfs["resultados_educacionales"]
    df_siedu = dfs["siedu"]
    df_empresas = dfs["empresas"]
    df_pobreza_comunal = dfs["pobreza_comunal"]
    df_consumo_electrico = dfs["consumo_electrico"]
    df_partidos_politicos = dfs["partidos_politicos"]
    df_autoridades_electas = dfs["autoridades_electas"]
    df_estadisticas_vitales = dfs["estadisticas_vitales"]
    df_permisos_edificacion = dfs["permisos_edificacion"]
    df_calidad_aire = dfs["calidad_aire"]
    df_regiones = dfs["regiones"]
    df_provincias = dfs["provincias"]
    df_perfil_territorial = dfs["perfil_territorial"]
    comunas_metadata = meta["comunas"]
    indicadores_metadata = meta["indicadores"]
    censo_metadata = meta["censo"]
    salud_metadata = meta["salud"]
    censo_hogares_metadata = meta["censo_hogares"]
    electoral_metadata = meta["electoral"]
    educacionales_metadata = meta["educacionales"]
    finanzas_metadata = meta["finanzas"]
    resultados_educacionales_metadata = meta["resultados_educacionales"]
    siedu_metadata = meta["siedu"]
    empresas_metadata = meta["empresas"]
    pobreza_comunal_metadata = meta["pobreza_comunal"]
    consumo_electrico_metadata = meta["consumo_electrico"]
    partidos_politicos_metadata = meta["partidos_politicos"]
    autoridades_electas_metadata = meta["autoridades_electas"]
    estadisticas_vitales_metadata = meta["estadisticas_vitales"]
    permisos_edificacion_metadata = meta["permisos_edificacion"]
    calidad_aire_metadata = meta["calidad_aire"]

    # Una sola copia de la allowlist DPA (Plan 093): antes se copiaba la
    # columna codigo_comuna (~15 veces, una por validador). Los validadores
    # solo hacen set()/len() sobre ella, así que compartir el objeto es
    # seguro — futuros validadores deben recibir este mismo objeto.
    valid_comunas = df_comunas["codigo_comuna"].to_list()

    validations = {
        "regiones": validate_regiones(df_regiones),
        "provincias": validate_provincias(df_provincias),
        "comunas": validate_comunas(df_comunas, comunas_metadata),
        "comunas_enriquecidas": {
            **validate_comunas(df_comunas, comunas_metadata),
            "dataset": "comunas_enriquecidas",
        },
        "indicadores": validate_indicadores(df_indicadores, indicadores_metadata),
        "censo_comunal": validate_censo_comunal(df_censo, censo_metadata),
        "establecimientos_salud": validate_establecimientos_salud(
            df_salud, salud_metadata, valid_comunas
        ),
        "censo_hogares_viviendas": validate_censo_hogares_viviendas(
            df_censo_hogares, censo_hogares_metadata, valid_comunas
        ),
        "distritos_electorales": validate_distritos_electorales(
            df_electoral, electoral_metadata, valid_comunas
        ),
        "establecimientos_educacionales": validate_establecimientos_educacionales(
            df_educacionales, educacionales_metadata, valid_comunas
        ),
        "finanzas_municipales": validate_finanzas_municipales(
            df_finanzas, finanzas_metadata, valid_comunas
        ),
        "resultados_educacionales": validate_resultados_educacionales(
            df_resultados_educacionales,
            resultados_educacionales_metadata,
            valid_comunas,
        ),
        "indicadores_urbanos_siedu": validate_indicadores_urbanos_siedu(
            df_siedu, siedu_metadata, valid_comunas
        ),
        **(
            {"empresas": validate_empresas(df_empresas, empresas_metadata, valid_comunas)}
            if df_empresas is not None
            else {}
        ),
        **(
            {
                "pobreza_comunal": validate_pobreza_comunal(
                    df_pobreza_comunal,
                    pobreza_comunal_metadata,
                    valid_comunas,
                )
            }
            if df_pobreza_comunal is not None
            else {}
        ),
        **(
            {
                "consumo_electrico_comunal": validate_consumo_electrico_comunal(
                    df_consumo_electrico,
                    consumo_electrico_metadata,
                    valid_comunas,
                )
            }
            if df_consumo_electrico is not None
            else {}
        ),
        **(
            {
                "partidos_politicos": validate_partidos_politicos(
                    df_partidos_politicos, partidos_politicos_metadata
                )
            }
            if df_partidos_politicos is not None
            else {}
        ),
        **(
            {
                "autoridades_electas": validate_autoridades_electas(
                    df_autoridades_electas,
                    autoridades_electas_metadata,
                    valid_comunas,
                )
            }
            if df_autoridades_electas is not None
            else {}
        ),
        **(
            {
                "estadisticas_vitales": validate_estadisticas_vitales(
                    df_estadisticas_vitales,
                    estadisticas_vitales_metadata,
                    valid_comunas,
                )
            }
            if df_estadisticas_vitales is not None
            else {}
        ),
        **(
            {
                "permisos_edificacion": validate_permisos_edificacion(
                    df_permisos_edificacion,
                    permisos_edificacion_metadata,
                    valid_comunas,
                )
            }
            if df_permisos_edificacion is not None
            else {}
        ),
        **(
            {
                "calidad_aire": validate_calidad_aire(
                    df_calidad_aire,
                    calidad_aire_metadata,
                    valid_comunas,
                )
            }
            if df_calidad_aire is not None
            else {}
        ),
        "perfil_territorial_comunal": validate_perfil_territorial_comunal(
            df_perfil_territorial,
            {
                "dataset": "perfil_territorial_comunal",
                "notes": [],
            },
            valid_comunas,
        ),
    }

    failed_validations = [
        result["dataset"] for result in validations.values() if result["status"] == "error"
    ]
    if failed_validations:
        messages = [f"Validaciones fallidas para {', '.join(failed_validations)}."]
        for result in validations.values():
            for error in result["errors"]:
                messages.append(f" - {result['dataset']}: {error}")
        raise SystemExit("\n".join(messages))
    return validations


def _write_data_artifacts(dfs):
    """Compila DuckDB/SQLite/Excel/archivos planos y parquet/JSON auxiliares."""
    df_comunas = dfs["comunas"]
    df_indicadores = dfs["indicadores"]
    df_censo = dfs["censo"]
    df_salud = dfs["salud"]
    df_censo_hogares = dfs["censo_hogares"]
    df_electoral = dfs["electoral"]
    df_educacionales = dfs["educacionales"]
    df_finanzas = dfs["finanzas"]
    df_resultados_educacionales = dfs["resultados_educacionales"]
    df_siedu = dfs["siedu"]
    df_empresas = dfs["empresas"]
    df_pobreza_comunal = dfs["pobreza_comunal"]
    df_consumo_electrico = dfs["consumo_electrico"]
    df_partidos_politicos = dfs["partidos_politicos"]
    df_autoridades_electas = dfs["autoridades_electas"]
    df_estadisticas_vitales = dfs["estadisticas_vitales"]
    df_permisos_edificacion = dfs["permisos_edificacion"]
    df_calidad_aire = dfs["calidad_aire"]
    df_regiones = dfs["regiones"]
    df_provincias = dfs["provincias"]
    df_perfil_territorial = dfs["perfil_territorial"]

    extra_tables = {
        "finanzas_municipales": df_finanzas,
        "resultados_educacionales": df_resultados_educacionales,
        "indicadores_urbanos_siedu": df_siedu,
        "perfil_territorial_comunal": df_perfil_territorial,
    }
    if df_empresas is not None:
        extra_tables["empresas"] = df_empresas
    if df_pobreza_comunal is not None:
        extra_tables["pobreza_comunal"] = df_pobreza_comunal
    if df_consumo_electrico is not None:
        extra_tables["consumo_electrico_comunal"] = df_consumo_electrico
    if df_partidos_politicos is not None:
        extra_tables["partidos_politicos"] = df_partidos_politicos
    if df_autoridades_electas is not None:
        extra_tables["autoridades_electas"] = df_autoridades_electas
    if df_estadisticas_vitales is not None:
        extra_tables["estadisticas_vitales"] = df_estadisticas_vitales
    if df_permisos_edificacion is not None:
        extra_tables["permisos_edificacion"] = df_permisos_edificacion
    if df_calidad_aire is not None:
        extra_tables["calidad_aire"] = df_calidad_aire

    # Convertir a pandas UNA sola vez para SQLite y Excel (Plan 090).
    # Empresas tiene ~1.57M filas: la conversión es costosa y no debe
    # duplicarse — y las tablas que ambos formatos descartan por masivas ni
    # siquiera se convierten (skip decidido por height Polars, sin convertir).
    _pd_max_rows = max(SQLITE_MAX_ROWS, EXCEL_MAX_ROWS_SKIP)
    extra_tables_pd = {
        name: df.to_pandas() for name, df in extra_tables.items() if df.height <= _pd_max_rows
    }
    base_tables_pd = {
        "regiones": df_regiones.to_pandas(),
        "provincias": df_provincias.to_pandas(),
        "comunas": df_comunas.to_pandas(),
        "indicadores": df_indicadores.to_pandas(),
        "censo_comunal": df_censo.to_pandas(),
        "establecimientos_salud": df_salud.to_pandas(),
        "establecimientos_educacionales": df_educacionales.to_pandas(),
    }

    # Compilar entregables
    log.info("artifacts_build_start", total_formats=4)
    build_duckdb(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        extra_tables,
        os.path.join(NORMALIZED_DIR, "chile_data.duckdb"),
    )
    log.info("artifact_format_done", format="duckdb", progress="1/4")
    build_sqlite(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        extra_tables,
        extra_tables_pd=extra_tables_pd,
        base_tables_pd=base_tables_pd,
        output_path=os.path.join(NORMALIZED_DIR, "chile_data.db"),
    )
    log.info("artifact_format_done", format="sqlite", progress="2/4")
    build_excel(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        extra_tables,
        extra_tables_pd=extra_tables_pd,
        base_tables_pd=base_tables_pd,
        output_path=os.path.join(NORMALIZED_DIR, "chile_data_latest.xlsx"),
    )
    log.info("artifact_format_done", format="excel", progress="3/4")
    build_flat_files(
        df_regiones,
        df_provincias,
        df_comunas,
        df_indicadores,
        df_censo,
        df_salud,
        df_educacionales,
        extra_tables,
    )
    log.info("artifact_format_done", format="flat_files", progress="4/4")
    write_parquet_atomic(
        df_censo_hogares, os.path.join(NORMALIZED_DIR, "censo_hogares_viviendas.parquet")
    )
    # JSON compacto (sin indent): tablas completas; Parquet/DuckDB son la
    # vía para grandes volúmenes (mismo criterio que formats.build_flat_files).
    write_json_atomic(
        df_censo_hogares.to_dicts(),
        os.path.join(NORMALIZED_DIR, "censo_hogares_viviendas.json"),
        ensure_ascii=False,
    )

    write_parquet_atomic(
        df_electoral, os.path.join(NORMALIZED_DIR, "distritos_electorales.parquet")
    )
    write_json_atomic(
        df_electoral.to_dicts(),
        os.path.join(NORMALIZED_DIR, "distritos_electorales.json"),
        ensure_ascii=False,
    )

    # Asset del mapa del sitio: métricas ya resueltas por comuna (el año de
    # permisos en curso se descarta a favor del último completo).
    write_mapa_metricas_json(
        df_perfil_territorial,
        df_permisos_edificacion,
        df_pobreza_comunal,
        os.path.join(NORMALIZED_DIR, MAPA_METRICAS_FILENAME),
    )


def _generate_reports(pipeline_metadata, previous_pipeline_metadata, metadata_output):
    """Genera reportes, estados, bundle y manifiesto, e imprime el resumen."""
    hub_health = build_hub_health(pipeline_metadata)
    write_status_markdown_file(pipeline_metadata, health=hub_health)
    hub_health_output = write_hub_health_json(hub_health)
    hub_health_history_output = append_hub_health_history(hub_health)
    hub_status = build_hub_status(hub_health)
    hub_status_output = write_hub_status_json(hub_status)
    dataset_status_output = write_dataset_status_json(build_dataset_status(pipeline_metadata))
    dataset_changelog_output = write_dataset_changelog_json(
        build_dataset_changelog(pipeline_metadata, previous_pipeline_metadata)
    )
    write_hub_health_markdown_file(hub_health)
    catalog_output, dataset_catalog = write_dataset_catalog(pipeline_metadata)
    write_dataset_catalog_markdown_file(dataset_catalog)
    data_package_output = write_data_package_json(
        dataset_catalog,
        pipeline_metadata["version"],
        pipeline_metadata["public_site_url"],
    )
    dcat_catalog_output = write_dcat_catalog_json(
        build_data_package(
            dataset_catalog,
            pipeline_metadata["version"],
            pipeline_metadata["public_site_url"],
        )
    )
    redistribution_report = build_redistribution_report(dataset_catalog)
    redistribution_report_output = write_redistribution_report_json(redistribution_report)
    write_redistribution_report_markdown_file(redistribution_report)
    provenance_report = build_provenance_report(dataset_catalog)
    provenance_report_output = write_provenance_report_json(provenance_report)
    write_provenance_report_markdown_file(provenance_report)
    drift_report = build_drift_report(dataset_catalog)
    drift_report_output = write_drift_report_json(drift_report)
    write_drift_report_markdown_file(drift_report)
    source_readiness = build_source_readiness(pipeline_metadata)
    source_readiness_json_output, _ = write_source_readiness_json(source_readiness)
    write_source_readiness_markdown_file(source_readiness)
    dataset_quality = build_dataset_quality(pipeline_metadata, hub_health, source_readiness)
    dataset_quality_json_output, _ = write_dataset_quality_json(dataset_quality)
    write_dataset_quality_markdown_file(dataset_quality)
    artifact_manifest_output, artifact_manifest = write_artifact_manifest()
    zip_output = write_publishable_bundle_zip()
    bundle_sha256 = compute_sha256(zip_output)
    sha256_output = write_publishable_bundle_sha256(zip_output, sha256=bundle_sha256)
    artifact_manifest_output, artifact_manifest = attach_publishable_package_to_manifest(
        zip_output, sha256_output, artifact_manifest, sha256=bundle_sha256
    )
    hub_bundle_output, hub_bundle = write_hub_bundle_json(
        pipeline_metadata,
        hub_health,
        dataset_catalog,
        artifact_manifest,
    )
    overview = build_overview(hub_health, hub_bundle, artifact_manifest)
    overview_output, overview = write_overview_json(overview)
    write_overview_markdown_file(overview)
    log.info(
        "reports_written",
        metadata=metadata_output,
        hub_health=hub_health_output,
        hub_health_history=hub_health_history_output,
        hub_status=hub_status_output,
        dataset_status=dataset_status_output,
        dataset_changelog=dataset_changelog_output,
        catalog=catalog_output,
        redistribution=redistribution_report_output,
        provenance=provenance_report_output,
        drift=drift_report_output,
        source_readiness=source_readiness_json_output,
        dataset_quality=dataset_quality_json_output,
        overview=overview_output,
        artifact_manifest=artifact_manifest_output,
        hub_bundle=hub_bundle_output,
        data_package=data_package_output,
        dcat_catalog=dcat_catalog_output,
        zip=zip_output,
        sha256=sha256_output,
    )


def main():
    ensure_directories()
    dfs, meta, previous_pipeline_metadata = _load_inputs()
    validations = _compute_validations(dfs, meta)
    _write_data_artifacts(dfs)
    dataset_metadata = build_dataset_metadata(dfs, meta)
    validations_with_freshness = {
        dataset_name: {
            **validation,
            "warnings": validation.get("warnings", [])
            + build_freshness_warnings(dataset_name, dataset_metadata[dataset_name]["freshness"]),
            "freshness_status": dataset_metadata[dataset_name]["freshness"]["status"],
            "freshness_age_hours": dataset_metadata[dataset_name]["freshness"]["age_hours"],
        }
        for dataset_name, validation in validations.items()
    }
    dataset_metadata = enrich_dataset_metadata(dataset_metadata, validations_with_freshness)
    metadata_output, pipeline_metadata = write_pipeline_metadata(
        dataset_metadata,
        validations_with_freshness,
    )
    _generate_reports(pipeline_metadata, previous_pipeline_metadata, metadata_output)
    sync_readme_layers_table()
    sync_all_docs()
    log.info("build_complete")


if __name__ == "__main__":
    main()
