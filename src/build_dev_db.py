import json
import os
import sys
from datetime import timezone

import polars as pl

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

UTC = timezone.utc

# Rutas, constantes y configuración de catálogo compartidas (re-exportadas para
# mantener compatibilidad con scripts externos y tests que las importan desde aquí;
# DATASET_CATALOG_CONFIG se consume vía build_dev_db en verify_pipeline.py y tests).
from src.builders._shared import (  # noqa: E402, F401
    AUTORIDADES_ELECTAS_METADATA_PATH,
    CENSO_HOGARES_METADATA_PATH,
    CENSO_METADATA_PATH,
    COMUNAS_METADATA_PATH,
    CONSUMO_ELECTRICO_COMUNAL_METADATA_PATH,
    DATASET_CATALOG_CONFIG,
    ELECTORAL_METADATA_PATH,
    EMPRESAS_METADATA_PATH,
    FINANZAS_METADATA_PATH,
    INDICADORES_METADATA_PATH,
    NORMALIZED_DIR,
    PARTIDOS_POLITICOS_METADATA_PATH,
    POBREZA_COMUNAL_METADATA_PATH,
    RESULTADOS_EDUCACIONALES_METADATA_PATH,
    SALUD_METADATA_PATH,
    SIEDU_METADATA_PATH,
    STAGING_DIR,
)
from src.builders.artifacts import (  # noqa: E402
    attach_publishable_package_to_manifest,
    write_artifact_manifest,
    write_hub_bundle_json,
    write_publishable_bundle_sha256,
    write_publishable_bundle_zip,
)
from src.builders.catalog import (  # noqa: E402
    write_dataset_catalog,
    write_pipeline_metadata,
)
from src.builders.data_package import write_data_package_json  # noqa: E402
from src.builders.datasets import (  # noqa: E402
    build_perfil_territorial_comunal,
    derive_geography_layers,
)
from src.builders.doc_sync import sync_all_docs  # noqa: E402
from src.builders.formats import (  # noqa: E402
    build_duckdb,
    build_excel,
    build_flat_files,
    build_sqlite,
)
from src.builders.io_utils import (  # noqa: E402
    write_json_atomic,
    write_parquet_atomic,
)

# build_coverage, build_degradation y build_drift se re-exportan para los tests
# (no se usan directamente aquí, solo a través de enrich_dataset_metadata).
from src.builders.metadata import (  # noqa: E402, F401
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
from src.builders.reports import (  # noqa: E402
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
    validate_censo_comunal,
    validate_censo_hogares_viviendas,
    validate_comunas,
    validate_consumo_electrico_comunal,
    validate_distritos_electorales,
    validate_empresas,
    validate_establecimientos_educacionales,
    validate_establecimientos_salud,
    validate_finanzas_municipales,
    validate_indicadores,
    validate_indicadores_urbanos_siedu,
    validate_partidos_politicos,
    validate_perfil_territorial_comunal,
    validate_pobreza_comunal,
    validate_provincias,
    validate_regiones,
    validate_resultados_educacionales,
)


def _load_inputs():
    """Carga metadatos de staging y lee todos los DataFrames de origen."""
    previous_pipeline_metadata = None
    previous_metadata_path = os.path.join(NORMALIZED_DIR, "pipeline_metadata.json")
    if os.path.exists(previous_metadata_path):
        try:
            with open(previous_metadata_path, encoding="utf-8") as f:
                previous_pipeline_metadata = json.load(f)
        except json.JSONDecodeError:
            previous_pipeline_metadata = None

    # Rutas de origen (Staging)
    comunas_csv = os.path.join(STAGING_DIR, "comunas.csv")
    indicadores_csv = os.path.join(STAGING_DIR, "indicadores.csv")
    censo_csv = os.path.join(STAGING_DIR, "censo_comunal.csv")
    salud_csv = os.path.join(STAGING_DIR, "establecimientos_salud.csv")
    censo_hogares_csv = os.path.join(STAGING_DIR, "censo_hogares_viviendas.csv")
    electoral_csv = os.path.join(STAGING_DIR, "distritos_electorales.csv")
    educacionales_csv = os.path.join(STAGING_DIR, "establecimientos_educacionales.csv")
    finanzas_csv = os.path.join(STAGING_DIR, "finanzas_municipales.csv")
    resultados_educacionales_csv = os.path.join(STAGING_DIR, "resultados_educacionales.csv")
    siedu_csv = os.path.join(STAGING_DIR, "indicadores_urbanos_siedu.csv")
    empresas_csv = os.path.join(STAGING_DIR, "empresas.csv")
    pobreza_comunal_csv = os.path.join(STAGING_DIR, "pobreza_comunal.csv")
    consumo_electrico_csv = os.path.join(STAGING_DIR, "consumo_electrico_comunal.csv")
    partidos_politicos_csv = os.path.join(STAGING_DIR, "partidos_politicos.csv")
    autoridades_electas_csv = os.path.join(STAGING_DIR, "autoridades_electas.csv")

    required_staging = (
        comunas_csv,
        indicadores_csv,
        censo_csv,
        salud_csv,
        censo_hogares_csv,
        electoral_csv,
        educacionales_csv,
        finanzas_csv,
        resultados_educacionales_csv,
        siedu_csv,
    )
    if any(not os.path.exists(path) for path in required_staging):
        raise SystemExit(
            "Error: No se encuentran los archivos CSV en staging. Corre los extractores primero."
        )

    metadata_checks = [
        ("comunas.metadata.json", COMUNAS_METADATA_PATH, "subdere_extractor.py"),
        ("indicadores.metadata.json", INDICADORES_METADATA_PATH, "bcentral_extractor.py"),
        ("censo_comunal.metadata.json", CENSO_METADATA_PATH, "censo_extractor.py"),
        ("establecimientos_salud.metadata.json", SALUD_METADATA_PATH, "salud_extractor.py"),
        (
            "censo_hogares_viviendas.metadata.json",
            CENSO_HOGARES_METADATA_PATH,
            "censo_hogares_viviendas_extractor.py",
        ),
        ("distritos_electorales.metadata.json", ELECTORAL_METADATA_PATH, "electoral_extractor.py"),
        (
            "establecimientos_educacionales.metadata.json",
            os.path.join(STAGING_DIR, "establecimientos_educacionales.metadata.json"),
            "mineduc_establecimientos_extractor.py",
        ),
        (
            "finanzas_municipales.metadata.json",
            FINANZAS_METADATA_PATH,
            "sinim_finanzas_extractor.py",
        ),
        (
            "resultados_educacionales.metadata.json",
            RESULTADOS_EDUCACIONALES_METADATA_PATH,
            "mineduc_resultados_extractor.py",
        ),
        ("indicadores_urbanos_siedu.metadata.json", SIEDU_METADATA_PATH, "siedu_extractor.py"),
    ]
    for filename, path, extractor in metadata_checks:
        if not os.path.exists(path):
            raise SystemExit(
                f"Error: No se encuentra {filename} en data/staging/. "
                f"Corre el extractor primero: python src/extractors/{extractor}"
            )

    comunas_metadata = load_metadata(COMUNAS_METADATA_PATH)
    indicadores_metadata = load_metadata(INDICADORES_METADATA_PATH)
    censo_metadata = load_metadata(CENSO_METADATA_PATH)
    salud_metadata = load_metadata(SALUD_METADATA_PATH)
    censo_hogares_metadata = load_metadata(CENSO_HOGARES_METADATA_PATH)
    electoral_metadata = load_metadata(ELECTORAL_METADATA_PATH)
    educacionales_metadata = load_metadata(
        os.path.join(STAGING_DIR, "establecimientos_educacionales.metadata.json")
    )
    finanzas_metadata = load_metadata(FINANZAS_METADATA_PATH)
    resultados_educacionales_metadata = load_metadata(RESULTADOS_EDUCACIONALES_METADATA_PATH)
    siedu_metadata = load_metadata(SIEDU_METADATA_PATH)
    empresas_metadata = (
        load_metadata(EMPRESAS_METADATA_PATH) if os.path.exists(EMPRESAS_METADATA_PATH) else None
    )
    pobreza_comunal_metadata = (
        load_metadata(POBREZA_COMUNAL_METADATA_PATH)
        if os.path.exists(POBREZA_COMUNAL_METADATA_PATH)
        else None
    )
    consumo_electrico_metadata = (
        load_metadata(CONSUMO_ELECTRICO_COMUNAL_METADATA_PATH)
        if os.path.exists(CONSUMO_ELECTRICO_COMUNAL_METADATA_PATH)
        else None
    )
    partidos_politicos_metadata = (
        load_metadata(PARTIDOS_POLITICOS_METADATA_PATH)
        if os.path.exists(PARTIDOS_POLITICOS_METADATA_PATH)
        else None
    )
    autoridades_electas_metadata = (
        load_metadata(AUTORIDADES_ELECTAS_METADATA_PATH)
        if os.path.exists(AUTORIDADES_ELECTAS_METADATA_PATH)
        else None
    )

    metadata_files = [
        ("comunas", comunas_metadata, "subdere_extractor.py"),
        ("indicadores", indicadores_metadata, "bcentral_extractor.py"),
        ("censo_comunal", censo_metadata, "censo_extractor.py"),
        ("establecimientos_salud", salud_metadata, "salud_extractor.py"),
        ("censo_hogares_viviendas", censo_hogares_metadata, "censo_hogares_viviendas_extractor.py"),
        ("distritos_electorales", electoral_metadata, "electoral_extractor.py"),
        (
            "establecimientos_educacionales",
            educacionales_metadata,
            "mineduc_establecimientos_extractor.py",
        ),
        ("finanzas_municipales", finanzas_metadata, "sinim_finanzas_extractor.py"),
        (
            "resultados_educacionales",
            resultados_educacionales_metadata,
            "mineduc_resultados_extractor.py",
        ),
        ("indicadores_urbanos_siedu", siedu_metadata, "siedu_extractor.py"),
    ]
    for name, meta, extractor in metadata_files:
        if meta is None:
            raise SystemExit(
                f"Error: No se encuentran los metadatos para {name} en data/staging/. "
                f"Corre el extractor primero: python src/extractors/{extractor}"
            )
    indicadores_metadata["indicator_codes"] = sorted(
        df_code for df_code in indicadores_metadata.get("indicator_codes", [])
    )
    indicadores_metadata["indicator_delivery"] = build_indicator_delivery(indicadores_metadata)

    # Cargar datos desde staging
    # Especificamos explícitamente el tipo de dato de los códigos a String para no perder ceros
    df_comunas = pl.read_csv(
        comunas_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )

    df_indicadores = pl.read_csv(
        indicadores_csv,
        schema_overrides={"codigo_indicador": pl.String, "valor": pl.Float64},
    ).with_columns(pl.col("fecha").str.to_date("%Y-%m-%d"))
    df_censo = pl.read_csv(
        censo_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_salud = pl.read_csv(
        salud_csv,
        schema_overrides={
            "codigo_establecimiento": pl.String,
            "codigo_region": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_censo_hogares = pl.read_csv(
        censo_hogares_csv,
        schema_overrides={
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_electoral = pl.read_csv(
        electoral_csv,
        schema_overrides={
            "codigo_comuna": pl.String,
            "distrito_electoral": pl.String,
            "circunscripcion_senatorial": pl.String,
        },
    )
    df_educacionales = pl.read_csv(
        educacionales_csv,
        schema_overrides={
            "rbd": pl.String,
            "dv_rbd": pl.String,
            "codigo_region": pl.String,
            "codigo_comuna": pl.String,
        },
    )
    df_finanzas = pl.read_csv(
        finanzas_csv,
        schema_overrides={"anio": pl.Int32, "codigo_comuna": pl.String},
    )
    df_resultados_educacionales = pl.read_csv(
        resultados_educacionales_csv,
        schema_overrides={"anio": pl.Int32, "codigo_comuna": pl.String},
    )
    df_siedu = pl.read_csv(
        siedu_csv,
        schema_overrides={
            "anio": pl.Int32,
            "codigo_comuna": pl.String,
            "codigo_indicador": pl.String,
            "valor": pl.Float64,
        },
    )

    # Empresas: dataset opcional (nuevo, puede no existir en builds anteriores)
    df_empresas = None
    if os.path.exists(empresas_csv) and empresas_metadata is not None:
        df_empresas = pl.read_csv(
            empresas_csv,
            schema_overrides={
                "rut": pl.String,
                "razon_social": pl.String,
                "codigo_sociedad": pl.String,
                "capital": pl.Int64,
                "anio": pl.Int32,
                "comuna_tributaria": pl.String,
                "region_tributaria": pl.String,
                "comuna_social": pl.String,
                "region_social": pl.String,
            },
        )
        log.info("dataset_loaded", dataset="empresas", records=df_empresas.height)
    else:
        log.info("dataset_skipped", dataset="empresas", reason="not_found_in_staging")

    # Pobreza comunal: dataset opcional (nuevo, puede no existir en builds anteriores)
    df_pobreza_comunal = None
    if os.path.exists(pobreza_comunal_csv) and pobreza_comunal_metadata is not None:
        df_pobreza_comunal = pl.read_csv(
            pobreza_comunal_csv,
            schema_overrides={
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "anio": pl.Int64,
                "tasa": pl.Float64,
                "limite_inferior": pl.Float64,
                "limite_superior": pl.Float64,
            },
        )
        log.info("dataset_loaded", dataset="pobreza_comunal", records=df_pobreza_comunal.height)
    else:
        log.info("dataset_skipped", dataset="pobreza_comunal", reason="not_found_in_staging")

    # Consumo eléctrico: dataset opcional (nuevo)
    df_consumo_electrico = None
    if os.path.exists(consumo_electrico_csv) and consumo_electrico_metadata is not None:
        df_consumo_electrico = pl.read_csv(
            consumo_electrico_csv,
            schema_overrides={
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "anio": pl.Int64,
                "consumo_kwh": pl.Float64,
                "numero_clientes": pl.Int64,
            },
        )
        log.info(
            "dataset_loaded",
            dataset="consumo_electrico_comunal",
            records=df_consumo_electrico.height,
        )
    else:
        log.info(
            "dataset_skipped",
            dataset="consumo_electrico_comunal",
            reason="not_found_in_staging",
        )

    # Partidos políticos: dataset opcional (nuevo)
    df_partidos_politicos = None
    if os.path.exists(partidos_politicos_csv) and partidos_politicos_metadata is not None:
        df_partidos_politicos = pl.read_csv(partidos_politicos_csv, infer_schema_length=None)
        log.info(
            "dataset_loaded",
            dataset="partidos_politicos",
            records=df_partidos_politicos.height,
        )
    else:
        log.info("dataset_skipped", dataset="partidos_politicos", reason="not_found_in_staging")

    # Autoridades electas: dataset opcional (nuevo)
    df_autoridades_electas = None
    if os.path.exists(autoridades_electas_csv) and autoridades_electas_metadata is not None:
        df_autoridades_electas = pl.read_csv(
            autoridades_electas_csv,
            schema_overrides={
                "distrito_electoral": pl.String,
                "circunscripcion_senatorial": pl.String,
                "codigo_comuna": pl.String,
                "codigo_region": pl.String,
            },
        )
        log.info(
            "dataset_loaded",
            dataset="autoridades_electas",
            records=df_autoridades_electas.height,
        )
    else:
        log.info("dataset_skipped", dataset="autoridades_electas", reason="not_found_in_staging")

    df_regiones, df_provincias = derive_geography_layers(df_comunas)
    df_perfil_territorial = build_perfil_territorial_comunal(
        df_comunas,
        df_censo,
        df_censo_hogares,
        df_salud,
        df_educacionales,
        df_electoral,
        df_finanzas,
        df_resultados_educacionales,
        df_siedu,
    )

    dfs = {
        "comunas": df_comunas,
        "indicadores": df_indicadores,
        "censo": df_censo,
        "salud": df_salud,
        "censo_hogares": df_censo_hogares,
        "electoral": df_electoral,
        "educacionales": df_educacionales,
        "finanzas": df_finanzas,
        "resultados_educacionales": df_resultados_educacionales,
        "siedu": df_siedu,
        "empresas": df_empresas,
        "pobreza_comunal": df_pobreza_comunal,
        "consumo_electrico": df_consumo_electrico,
        "partidos_politicos": df_partidos_politicos,
        "autoridades_electas": df_autoridades_electas,
        "regiones": df_regiones,
        "provincias": df_provincias,
        "perfil_territorial": df_perfil_territorial,
    }
    meta = {
        "comunas": comunas_metadata,
        "indicadores": indicadores_metadata,
        "censo": censo_metadata,
        "salud": salud_metadata,
        "censo_hogares": censo_hogares_metadata,
        "electoral": electoral_metadata,
        "educacionales": educacionales_metadata,
        "finanzas": finanzas_metadata,
        "resultados_educacionales": resultados_educacionales_metadata,
        "siedu": siedu_metadata,
        "empresas": empresas_metadata,
        "pobreza_comunal": pobreza_comunal_metadata,
        "consumo_electrico": consumo_electrico_metadata,
        "partidos_politicos": partidos_politicos_metadata,
        "autoridades_electas": autoridades_electas_metadata,
    }
    return dfs, meta, previous_pipeline_metadata


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
            df_salud, salud_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "censo_hogares_viviendas": validate_censo_hogares_viviendas(
            df_censo_hogares, censo_hogares_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "distritos_electorales": validate_distritos_electorales(
            df_electoral, electoral_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "establecimientos_educacionales": validate_establecimientos_educacionales(
            df_educacionales, educacionales_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "finanzas_municipales": validate_finanzas_municipales(
            df_finanzas, finanzas_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        "resultados_educacionales": validate_resultados_educacionales(
            df_resultados_educacionales,
            resultados_educacionales_metadata,
            df_comunas["codigo_comuna"].to_list(),
        ),
        "indicadores_urbanos_siedu": validate_indicadores_urbanos_siedu(
            df_siedu, siedu_metadata, df_comunas["codigo_comuna"].to_list()
        ),
        **(
            {
                "empresas": validate_empresas(
                    df_empresas, empresas_metadata, df_comunas["codigo_comuna"].to_list()
                )
            }
            if df_empresas is not None
            else {}
        ),
        **(
            {
                "pobreza_comunal": validate_pobreza_comunal(
                    df_pobreza_comunal,
                    pobreza_comunal_metadata,
                    df_comunas["codigo_comuna"].to_list(),
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
                    df_comunas["codigo_comuna"].to_list(),
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
                    df_comunas["codigo_comuna"].to_list(),
                )
            }
            if df_autoridades_electas is not None
            else {}
        ),
        "perfil_territorial_comunal": validate_perfil_territorial_comunal(
            df_perfil_territorial,
            {
                "dataset": "perfil_territorial_comunal",
                "notes": [],
            },
            df_comunas["codigo_comuna"].to_list(),
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

    # Convertir tablas extra a pandas UNA sola vez para SQLite y Excel.
    # Empresas tiene ~1.57M filas: la conversión es costosa y no debe duplicarse.
    extra_tables_pd = {name: df.to_pandas() for name, df in extra_tables.items()}

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
        extra_tables_pd,
        os.path.join(NORMALIZED_DIR, "chile_data.db"),
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
        extra_tables_pd,
        os.path.join(NORMALIZED_DIR, "chile_data_latest.xlsx"),
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
    write_json_atomic(
        df_censo_hogares.to_dicts(),
        os.path.join(NORMALIZED_DIR, "censo_hogares_viviendas.json"),
        ensure_ascii=False,
        indent=2,
    )

    write_parquet_atomic(
        df_electoral, os.path.join(NORMALIZED_DIR, "distritos_electorales.parquet")
    )
    write_json_atomic(
        df_electoral.to_dicts(),
        os.path.join(NORMALIZED_DIR, "distritos_electorales.json"),
        ensure_ascii=False,
        indent=2,
    )


def _generate_reports(pipeline_metadata, previous_pipeline_metadata, metadata_output):
    """Genera reportes, estados, bundle y manifiesto, e imprime el resumen."""
    hub_health = build_hub_health(pipeline_metadata)
    write_status_markdown_file(pipeline_metadata, health=hub_health)
    hub_health_output = write_hub_health_json(hub_health)
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
    sha256_output = write_publishable_bundle_sha256(zip_output)
    artifact_manifest_output, artifact_manifest = attach_publishable_package_to_manifest(
        zip_output, sha256_output, artifact_manifest
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
