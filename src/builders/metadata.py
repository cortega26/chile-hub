"""Carga, validación y enriquecimiento de metadatos de datasets.

Incluye la carga de metadatos de staging y contratos de esquema, además de los
builders derivados (freshness, degradación, cobertura, drift) que enriquecen los
metadatos antes de generar reportes.
"""

import json
import os
from datetime import datetime

from src.builders._shared import DATASET_CATALOG_CONFIG, NORMALIZED_DIR, ROOT_DIR, UTC
from src.pipeline_status_utils import compute_freshness


def load_schema_contract(dataset_name):
    """Carga el contrato de esquema para un dataset.

    Retorna un dict con los campos del contrato, o None si el archivo
    no existe o no se puede interpretar.
    """
    contract_path = os.path.join(ROOT_DIR, "contracts", "datasets", f"{dataset_name}.schema.json")
    if not os.path.exists(contract_path):
        return None
    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def ensure_directories():
    os.makedirs(NORMALIZED_DIR, exist_ok=True)


def validate_metadata_schema(path, content):
    """
    Valida que el archivo JSON de metadatos de staging no sea nulo, sea un JSON válido
    y contenga todos los campos obligatorios del contrato de datos.
    """
    required_fields = {
        "dataset",
        "source_name",
        "source_url",
        "source_mode",
        "refreshed_at_utc",
        "record_count",
        "fields",
        "reuse_policy",
    }
    if not isinstance(content, dict):
        raise SystemExit(
            f"Error: Metadatos en {os.path.relpath(path, ROOT_DIR)} no es un objeto JSON (dict)."
        )

    missing_fields = required_fields - set(content.keys())
    if missing_fields:
        raise SystemExit(
            f"Error: Metadatos en {path} no cumple con el esquema obligatorio.\n"
            f"Campos faltantes: {', '.join(sorted(missing_fields))}"
        )


def load_metadata(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"Error: Archivo de metadatos {os.path.relpath(path, ROOT_DIR)} "
            f"contiene un JSON malformado: {e}"
        )

    validate_metadata_schema(path, content)
    return content


def build_freshness(refreshed_at_utc, max_age_hours):
    return compute_freshness(refreshed_at_utc, max_age_hours)


def build_freshness_warnings(dataset_name, freshness):
    status = freshness.get("status")
    age_hours = freshness.get("age_hours")
    max_age_hours = freshness.get("max_age_hours")

    if status == "stale":
        return [
            (
                f"{dataset_name} freshness is stale: "
                f"{age_hours}h since refresh, policy max is {max_age_hours}h"
            )
        ]
    if status == "unknown":
        return [f"{dataset_name} freshness is unknown: missing or invalid refreshed_at_utc"]
    return []


def build_indicator_delivery(metadata):
    indicator_codes = metadata.get("indicator_codes", [])
    delivery = metadata.get("indicator_delivery")
    if isinstance(delivery, dict) and delivery:
        return delivery

    delivery = {code: "live" for code in indicator_codes}
    for pair in metadata.get("raw_recoveries", []):
        delivery[pair.split("/", 1)[0]] = "raw_recovery"
    for pair in metadata.get("preserved_existing_pairs", []):
        delivery[pair.split("/", 1)[0]] = "preserved_existing"
    for code in metadata.get("published_backfills", []):
        delivery[code] = "published_backfill"
    return delivery


def build_degradation(dataset_name, dataset_metadata, validation):
    source_mode = dataset_metadata.get("source_mode")
    record_count = dataset_metadata.get("record_count")
    warnings = validation.get("warnings", [])

    if source_mode == "fallback":
        if dataset_name == "comunas":
            return {
                "status": "degraded",
                "impact": (
                    f"Cobertura territorial parcial: {record_count} comunas disponibles "
                    "desde fallback embebido."
                ),
                "recommended_action": "Reintentar extractores o restaurar la fuente territorial primaria.",
            }
        if dataset_name in {"regiones", "provincias"}:
            return {
                "status": "degraded",
                "impact": (
                    f"Capa derivada desde comunas en fallback; cardinalidad reducida a {record_count} filas."
                ),
                "recommended_action": "Recuperar comunas live para restaurar cobertura derivada completa.",
            }
        if dataset_name == "indicadores":
            return {
                "status": "degraded",
                "impact": "Valores provenientes de fallback local; no representan el último snapshot live.",
                "recommended_action": "Reintentar la API pública antes de redistribuir o usar en reporting.",
            }

    if warnings:
        return {
            "status": "warning",
            "impact": "; ".join(warnings),
            "recommended_action": "Revisar warnings operativos del dataset antes de consumirlo en producción.",
        }

    return {
        "status": "none",
        "impact": "Sin degradación operativa detectada en este build.",
        "recommended_action": "Ninguna.",
    }


def build_coverage(dataset_name, dataset_metadata):
    declared_coverage = dataset_metadata.get("coverage", {})
    if declared_coverage.get("status") == "partial_expected":
        return {
            "status": "partial",
            "expected_record_count": None,
            "actual_record_count": dataset_metadata.get("record_count"),
            "coverage_ratio": declared_coverage.get("coverage_ratio"),
            "summary": declared_coverage.get(
                "expected_scope",
                "Cobertura parcial esperada y declarada por la fuente.",
            ),
        }

    expected_record_count = DATASET_CATALOG_CONFIG.get(dataset_name, {}).get(
        "expected_record_count"
    )
    actual_record_count = dataset_metadata.get("record_count")

    if expected_record_count is None:
        return {
            "status": "not_applicable",
            "expected_record_count": None,
            "actual_record_count": actual_record_count,
            "coverage_ratio": None,
            "summary": "Sin baseline de cobertura por cardinalidad para esta capa.",
        }

    if actual_record_count is None or expected_record_count <= 0:
        return {
            "status": "unknown",
            "expected_record_count": expected_record_count,
            "actual_record_count": actual_record_count,
            "coverage_ratio": None,
            "summary": "No fue posible calcular cobertura contra el baseline esperado.",
        }

    coverage_ratio = round(actual_record_count / expected_record_count, 4)
    if actual_record_count >= expected_record_count:
        status = "full"
        summary = (
            f"Cobertura completa: {actual_record_count}/{expected_record_count} filas "
            "respecto del baseline esperado."
        )
    else:
        status = "partial"
        summary = (
            f"Cobertura parcial: {actual_record_count}/{expected_record_count} filas "
            "respecto del baseline esperado."
        )

    return {
        "status": status,
        "expected_record_count": expected_record_count,
        "actual_record_count": actual_record_count,
        "coverage_ratio": coverage_ratio,
        "summary": summary,
    }


def build_drift(dataset_metadata):
    source_mode = dataset_metadata.get("source_mode")
    coverage = dataset_metadata.get("coverage", {})
    degradation = dataset_metadata.get("degradation", {})
    coverage_status = coverage.get("status", "unknown")
    degradation_status = degradation.get("status", "none")

    drift_status = "healthy"
    if (
        source_mode == "fallback"
        or coverage_status in {"partial", "unknown"}
        or degradation_status in {"warning", "degraded"}
    ):
        drift_status = "drifted"

    if drift_status == "healthy":
        summary = "Sin drift operativo detectado en este build."
        recommended_action = "Ninguna."
    else:
        summary = (
            f"Drift detectado: mode={source_mode}, coverage={coverage_status}, "
            f"degradation={degradation_status}."
        )
        recommended_action = degradation.get(
            "recommended_action",
            "Revisar fuente, cobertura y warnings antes de consumir esta capa.",
        )

    return {
        "status": drift_status,
        "summary": summary,
        "recommended_action": recommended_action,
    }


def enrich_dataset_metadata(dataset_metadata, validations):
    enriched = {}
    for dataset_name, metadata in dataset_metadata.items():
        validation = validations.get(dataset_name, {})
        degradation = build_degradation(dataset_name, metadata, validation)
        coverage = build_coverage(dataset_name, metadata)
        # Incrustar campos del contrato de esquema para comparación de changelog
        contract = load_schema_contract(dataset_name)
        contract_fields = {}
        if contract:
            contract_fields = {
                "contract_primary_key": contract.get("primary_key", []),
                "contract_required_columns": contract.get("required_columns", []),
                "contract_column_types": contract.get("column_types", {}),
                "contract_nullable_columns": contract.get("nullable_columns", []),
                "contract_exists": True,
            }
        enriched[dataset_name] = {
            **metadata,
            "degradation": degradation,
            "coverage": coverage,
            **contract_fields,
        }
        enriched[dataset_name]["drift"] = build_drift(enriched[dataset_name])
    return enriched


def build_dataset_metadata(dfs, meta):
    """Construye el diccionario de metadatos enriquecidos por dataset."""
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

    dataset_metadata = {
        "regiones": {
            **comunas_metadata,
            "dataset": "regiones",
            "record_count": df_regiones.height,
            "fields": df_regiones.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["regiones"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["regiones"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "provincias": {
            **comunas_metadata,
            "dataset": "provincias",
            "record_count": df_provincias.height,
            "fields": df_provincias.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["provincias"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["provincias"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "comunas": {
            **comunas_metadata,
            "dataset": "comunas",
            "record_count": df_comunas.height,
            "fields": df_comunas.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["comunas"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["comunas"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "comunas_enriquecidas": {
            **comunas_metadata,
            "dataset": "comunas_enriquecidas",
            "alias_for": "comunas",
            "record_count": df_comunas.height,
            "fields": df_comunas.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["comunas"]["reuse_policy"],
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["comunas"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "indicadores": {
            **indicadores_metadata,
            "dataset": "indicadores",
            "record_count": df_indicadores.height,
            "fields": df_indicadores.columns,
            "indicator_codes": sorted(df_indicadores["codigo_indicador"].unique().to_list()),
            "indicator_delivery": build_indicator_delivery(
                {
                    **indicadores_metadata,
                    "indicator_codes": sorted(
                        df_indicadores["codigo_indicador"].unique().to_list()
                    ),
                }
            ),
            "reuse_policy": DATASET_CATALOG_CONFIG["indicadores"]["reuse_policy"],
            "freshness": build_freshness(
                indicadores_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["indicadores"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "censo_comunal": {
            **censo_metadata,
            "dataset": "censo_comunal",
            "record_count": df_censo.height,
            "fields": df_censo.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["censo_comunal"]["reuse_policy"],
            "freshness": build_freshness(
                censo_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["censo_comunal"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "establecimientos_salud": {
            **salud_metadata,
            "dataset": "establecimientos_salud",
            "record_count": df_salud.height,
            "fields": df_salud.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["establecimientos_salud"]["reuse_policy"],
            "freshness": build_freshness(
                salud_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["establecimientos_salud"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "establecimientos_educacionales": {
            **educacionales_metadata,
            "dataset": "establecimientos_educacionales",
            "record_count": df_educacionales.height,
            "fields": df_educacionales.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["establecimientos_educacionales"][
                "reuse_policy"
            ],
            "freshness": build_freshness(
                educacionales_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["establecimientos_educacionales"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "censo_hogares_viviendas": {
            **censo_hogares_metadata,
            "record_count": df_censo_hogares.height,
            "fields": df_censo_hogares.columns,
            "freshness": build_freshness(
                censo_hogares_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["censo_hogares_viviendas"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "distritos_electorales": {
            **electoral_metadata,
            "record_count": df_electoral.height,
            "fields": df_electoral.columns,
            "freshness": build_freshness(
                electoral_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["distritos_electorales"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "finanzas_municipales": {
            **finanzas_metadata,
            "dataset": "finanzas_municipales",
            "record_count": df_finanzas.height,
            "fields": df_finanzas.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["finanzas_municipales"]["reuse_policy"],
            "freshness": build_freshness(
                finanzas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["finanzas_municipales"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "resultados_educacionales": {
            **resultados_educacionales_metadata,
            "dataset": "resultados_educacionales",
            "record_count": df_resultados_educacionales.height,
            "fields": df_resultados_educacionales.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["resultados_educacionales"]["reuse_policy"],
            "freshness": build_freshness(
                resultados_educacionales_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["resultados_educacionales"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        "indicadores_urbanos_siedu": {
            **siedu_metadata,
            "dataset": "indicadores_urbanos_siedu",
            "record_count": df_siedu.height,
            "fields": df_siedu.columns,
            "reuse_policy": DATASET_CATALOG_CONFIG["indicadores_urbanos_siedu"]["reuse_policy"],
            "freshness": build_freshness(
                siedu_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["indicadores_urbanos_siedu"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
            "coverage": siedu_metadata.get("coverage", {}),
        },
        "perfil_territorial_comunal": {
            "dataset": "perfil_territorial_comunal",
            "source_name": "chile-hub",
            "source_url": "https://github.com/cortega26/chile-hub",
            "source_mode": "live"
            if all(
                metadata.get("source_mode") == "live"
                for metadata in (
                    comunas_metadata,
                    censo_metadata,
                    censo_hogares_metadata,
                    salud_metadata,
                    electoral_metadata,
                    educacionales_metadata,
                    finanzas_metadata,
                    resultados_educacionales_metadata,
                    siedu_metadata,
                )
            )
            else "fallback",
            "source_detail": "derived_from_validated_chile_hub_layers",
            "refreshed_at_utc": datetime.now(UTC).isoformat(),
            "record_count": df_perfil_territorial.height,
            "fields": df_perfil_territorial.columns,
            "notes": [
                "derived_dataset",
                "upstreams: comunas,censo_comunal,censo_hogares_viviendas,establecimientos_salud,establecimientos_educacionales,distritos_electorales,finanzas_municipales,resultados_educacionales,indicadores_urbanos_siedu",
            ],
            "reuse_policy": DATASET_CATALOG_CONFIG["perfil_territorial_comunal"]["reuse_policy"],
            "freshness": build_freshness(
                datetime.now(UTC).isoformat(),
                DATASET_CATALOG_CONFIG["perfil_territorial_comunal"]["freshness_policy"][
                    "max_age_hours"
                ],
            ),
        },
        **(
            {
                "empresas": {
                    "dataset": "empresas",
                    "source_name": empresas_metadata.get("source_name", ""),
                    "source_url": empresas_metadata.get("source_url", ""),
                    "source_mode": empresas_metadata.get("source_mode", "fallback"),
                    "source_detail": empresas_metadata.get(
                        "source_detail", "datos_gob_cl_ckan_api"
                    ),
                    "refreshed_at_utc": empresas_metadata.get("refreshed_at_utc", ""),
                    "record_count": df_empresas.height,
                    "fields": df_empresas.columns,
                    "notes": empresas_metadata.get("notes", []),
                    "reuse_policy": DATASET_CATALOG_CONFIG["empresas"]["reuse_policy"],
                    "freshness": build_freshness(
                        empresas_metadata.get("refreshed_at_utc", ""),
                        DATASET_CATALOG_CONFIG["empresas"]["freshness_policy"]["max_age_hours"],
                    ),
                }
            }
            if df_empresas is not None
            else {}
        ),
        **(
            {
                "pobreza_comunal": {
                    "dataset": "pobreza_comunal",
                    "source_name": pobreza_comunal_metadata.get("source_name", ""),
                    "source_url": pobreza_comunal_metadata.get("source_url", ""),
                    "source_mode": pobreza_comunal_metadata.get("source_mode", "fallback"),
                    "source_detail": pobreza_comunal_metadata.get("source_detail", ""),
                    "refreshed_at_utc": pobreza_comunal_metadata.get("refreshed_at_utc", ""),
                    "record_count": df_pobreza_comunal.height,
                    "fields": df_pobreza_comunal.columns,
                    "notes": pobreza_comunal_metadata.get("notes", []),
                    "reuse_policy": DATASET_CATALOG_CONFIG["pobreza_comunal"]["reuse_policy"],
                    "freshness": build_freshness(
                        pobreza_comunal_metadata.get("refreshed_at_utc", ""),
                        DATASET_CATALOG_CONFIG["pobreza_comunal"]["freshness_policy"][
                            "max_age_hours"
                        ],
                    ),
                }
            }
            if df_pobreza_comunal is not None and pobreza_comunal_metadata is not None
            else {}
        ),
        **(
            {
                "consumo_electrico_comunal": {
                    "dataset": "consumo_electrico_comunal",
                    "source_name": consumo_electrico_metadata.get("source_name", ""),
                    "source_url": consumo_electrico_metadata.get("source_url", ""),
                    "source_mode": consumo_electrico_metadata.get("source_mode", "fallback"),
                    "source_detail": consumo_electrico_metadata.get("source_detail", ""),
                    "refreshed_at_utc": consumo_electrico_metadata.get("refreshed_at_utc", ""),
                    "record_count": df_consumo_electrico.height,
                    "fields": df_consumo_electrico.columns,
                    "notes": consumo_electrico_metadata.get("notes", []),
                    "reuse_policy": DATASET_CATALOG_CONFIG["consumo_electrico_comunal"][
                        "reuse_policy"
                    ],
                    "freshness": build_freshness(
                        consumo_electrico_metadata.get("refreshed_at_utc", ""),
                        DATASET_CATALOG_CONFIG["consumo_electrico_comunal"]["freshness_policy"][
                            "max_age_hours"
                        ],
                    ),
                }
            }
            if df_consumo_electrico is not None and consumo_electrico_metadata is not None
            else {}
        ),
        **(
            {
                "partidos_politicos": {
                    "dataset": "partidos_politicos",
                    "source_name": partidos_politicos_metadata.get("source_name", ""),
                    "source_url": partidos_politicos_metadata.get("source_url", ""),
                    "source_mode": partidos_politicos_metadata.get("source_mode", "fallback"),
                    "source_detail": partidos_politicos_metadata.get("source_detail", ""),
                    "refreshed_at_utc": partidos_politicos_metadata.get("refreshed_at_utc", ""),
                    "record_count": df_partidos_politicos.height,
                    "fields": df_partidos_politicos.columns,
                    "notes": partidos_politicos_metadata.get("notes", []),
                    "reuse_policy": DATASET_CATALOG_CONFIG["partidos_politicos"]["reuse_policy"],
                    "freshness": build_freshness(
                        partidos_politicos_metadata.get("refreshed_at_utc", ""),
                        DATASET_CATALOG_CONFIG["partidos_politicos"]["freshness_policy"][
                            "max_age_hours"
                        ],
                    ),
                }
            }
            if df_partidos_politicos is not None and partidos_politicos_metadata is not None
            else {}
        ),
        **(
            {
                "autoridades_electas": {
                    "dataset": "autoridades_electas",
                    "source_name": autoridades_electas_metadata.get("source_name", ""),
                    "source_url": autoridades_electas_metadata.get("source_url", ""),
                    "source_mode": autoridades_electas_metadata.get("source_mode", "fallback"),
                    "source_detail": autoridades_electas_metadata.get("source_detail", ""),
                    "refreshed_at_utc": autoridades_electas_metadata.get("refreshed_at_utc", ""),
                    "record_count": df_autoridades_electas.height,
                    "fields": df_autoridades_electas.columns,
                    "notes": autoridades_electas_metadata.get("notes", []),
                    "reuse_policy": DATASET_CATALOG_CONFIG["autoridades_electas"]["reuse_policy"],
                    "freshness": build_freshness(
                        autoridades_electas_metadata.get("refreshed_at_utc", ""),
                        DATASET_CATALOG_CONFIG["autoridades_electas"]["freshness_policy"][
                            "max_age_hours"
                        ],
                    ),
                }
            }
            if df_autoridades_electas is not None and autoridades_electas_metadata is not None
            else {}
        ),
    }
    return dataset_metadata
