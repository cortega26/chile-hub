"""Carga, validación y enriquecimiento de metadatos de datasets.

Incluye la carga de metadatos de staging y contratos de esquema, además de los
builders derivados (freshness, degradación, cobertura, drift) que enriquecen los
metadatos antes de generar reportes.
"""

import json
import os
from datetime import date, datetime

import polars as pl

from src.builders._shared import (
    DATASET_CATALOG_CONFIG,
    NON_FALLBACK_SOURCE_MODES,
    NORMALIZED_DIR,
    ROOT_DIR,
    UTC,
)
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
        with open(contract_path, encoding="utf-8") as f:
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
        ) from e

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


def build_indicator_ages(df, today=None):
    """Fecha máxima y antigüedad en días de cada serie de `indicadores`.

    Se calcula en el **build**, sobre el DataFrame real, no en el extractor:
    así la señal está siempre fresca aunque el extractor no haya vuelto a correr,
    que es justamente el escenario donde una serie muerta se esconde (ADR-016).

    La edad se mide sobre el dato entregado, no sobre `refreshed_at_utc` — ese
    solo dice cuándo corrió el extractor, no cuán viejo es lo que trae. Las edades
    negativas son normales y esperadas: la UF y la UTM se publican por adelantado.
    """
    today = today or datetime.now(UTC).date()
    max_dates: dict[str, str] = {}
    ages: dict[str, int] = {}
    if df is None or df.height == 0:
        return max_dates, ages
    grouped = df.group_by("codigo_indicador").agg(pl.col("fecha").max().alias("max_fecha"))
    for row in grouped.iter_rows(named=True):
        fecha = row["max_fecha"]
        if fecha is None:
            continue
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        max_dates[row["codigo_indicador"]] = fecha.isoformat()
        ages[row["codigo_indicador"]] = (today - fecha).days
    return max_dates, ages


def build_indicator_delivery(metadata):
    indicator_codes = metadata.get("indicator_codes", [])
    delivery = metadata.get("indicator_delivery")
    if isinstance(delivery, dict) and delivery:
        return delivery

    delivery = dict.fromkeys(indicator_codes, "live")
    for pair in metadata.get("raw_recoveries", []):
        delivery[pair.split("/", 1)[0]] = "raw_recovery"
    for pair in metadata.get("preserved_existing_pairs", []):
        delivery[pair.split("/", 1)[0]] = "preserved_existing"
    for code in metadata.get("published_backfills", []):
        delivery[code] = "published_backfill"
    return delivery


def actionable_warnings(validation):
    """Warnings que exigen acción: todos menos los declarados como esperados.

    ``expected_warnings`` lo declara el validador que emite el mensaje
    (``src/validation/_helpers.py::_add_expected_warning``), nunca este consumidor.
    ``warnings`` conserva siempre la lista completa (ver ADR-014).
    """
    expected = set(validation.get("expected_warnings", []))
    return [warning for warning in validation.get("warnings", []) if warning not in expected]


def build_degradation(dataset_name, dataset_metadata, validation):
    source_mode = dataset_metadata.get("source_mode")
    record_count = dataset_metadata.get("record_count")
    warnings = actionable_warnings(validation)
    expected_warnings = list(validation.get("expected_warnings", []))

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

    anomalies = validation.get("anomalies", [])
    if anomalies:
        first = anomalies[0]
        return {
            "status": "warning",
            "impact": (
                f"Anomalía temporal detectada en {first['codigo_indicador']} "
                f"el {first['fecha']}: {first['motivo']}"
            ),
            "recommended_action": (
                f"Revisar valor atípico en {first['codigo_indicador']} del {first['fecha']}; "
                "confirmar con la fuente antes de publicar (ver ADR-013)."
            ),
            "anomaly_detected": True,
            "anomaly_indicator_codes": sorted({a["codigo_indicador"] for a in anomalies}),
        }

    if warnings:
        return {
            "status": "warning",
            "impact": "; ".join(warnings),
            "recommended_action": "Revisar warnings operativos del dataset antes de consumirlo en producción.",
        }

    if expected_warnings:
        # Sin accionables, pero los esperados se enumeran: no se esconden.
        return {
            "status": "none",
            "impact": (
                f"{len(expected_warnings)} observación(es) esperada(s): "
                + "; ".join(expected_warnings)
            ),
            "recommended_action": "Ninguna.",
        }

    return {
        "status": "none",
        "impact": "Sin degradación operativa detectada en este build.",
        "recommended_action": "Ninguna.",
    }


def build_coverage(dataset_name, dataset_metadata, contract=None):
    """Calcula la cobertura de un dataset y si su parcialidad es *esperada*.

    ``coverage_policy`` del contrato (``contracts/datasets/<dataset>.schema.json``)
    es la declaración de diseño: ``partial_expected`` significa que la fuente
    nunca cubre el universo completo (p. ej. SIEDU sólo mide comunas urbanas).
    El campo booleano ``expected`` está **siempre presente** para que sea
    inspeccionable, y ``status`` conserva su enum original — ``partial`` sigue
    describiendo correctamente la cobertura (ver ADR-014).
    """
    coverage_policy = (contract or {}).get("coverage_policy")

    def _finalize(coverage, expected_reason=None):
        is_expected = coverage["status"] == "partial" and (
            coverage_policy == "partial_expected" or expected_reason is not None
        )
        coverage["expected"] = is_expected
        if is_expected:
            coverage["expected_reason"] = expected_reason or (
                f"El contrato declara coverage_policy='{coverage_policy}': "
                "la fuente no cubre el universo completo por diseño."
            )
        return coverage

    declared_coverage = dataset_metadata.get("coverage", {})
    if declared_coverage.get("status") == "partial_expected":
        return _finalize(
            {
                "status": "partial",
                "expected_record_count": None,
                "actual_record_count": dataset_metadata.get("record_count"),
                "coverage_ratio": declared_coverage.get("coverage_ratio"),
                "summary": declared_coverage.get(
                    "expected_scope",
                    "Cobertura parcial esperada y declarada por la fuente.",
                ),
            },
            expected_reason=declared_coverage.get(
                "expected_scope",
                "El extractor declara la cobertura parcial como esperada.",
            ),
        )

    expected_record_count = DATASET_CATALOG_CONFIG.get(dataset_name, {}).get(
        "expected_record_count"
    )
    actual_record_count = dataset_metadata.get("record_count")

    if expected_record_count is None:
        return _finalize(
            {
                "status": "not_applicable",
                "expected_record_count": None,
                "actual_record_count": actual_record_count,
                "coverage_ratio": None,
                "summary": "Sin baseline de cobertura por cardinalidad para esta capa.",
            }
        )

    if actual_record_count is None or expected_record_count <= 0:
        return _finalize(
            {
                "status": "unknown",
                "expected_record_count": expected_record_count,
                "actual_record_count": actual_record_count,
                "coverage_ratio": None,
                "summary": "No fue posible calcular cobertura contra el baseline esperado.",
            }
        )

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

    return _finalize(
        {
            "status": status,
            "expected_record_count": expected_record_count,
            "actual_record_count": actual_record_count,
            "coverage_ratio": coverage_ratio,
            "summary": summary,
        }
    )


def build_drift(dataset_metadata):
    source_mode = dataset_metadata.get("source_mode")
    coverage = dataset_metadata.get("coverage", {})
    degradation = dataset_metadata.get("degradation", {})
    coverage_status = coverage.get("status", "unknown")
    degradation_status = degradation.get("status", "none")

    # Una cobertura parcial declarada como esperada en el contrato no es drift:
    # es el diseño de la fuente (ver ADR-014). El resto de las condiciones no cambia.
    coverage_expected = coverage.get("expected") is True

    triggers = []
    if source_mode == "fallback":
        triggers.append(f"mode={source_mode}")
    if coverage_status == "unknown" or (coverage_status == "partial" and not coverage_expected):
        triggers.append(f"coverage={coverage_status}")
    if degradation_status in {"warning", "degraded"}:
        triggers.append(f"degradation={degradation_status}")

    drift_status = "drifted" if triggers else "healthy"

    if drift_status == "healthy":
        summary = "Sin drift operativo detectado en este build."
        recommended_action = "Ninguna."
    else:
        summary = "Drift detectado: " + ", ".join(triggers) + "."
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
        # El contrato se carga una sola vez: alimenta tanto coverage_policy
        # (build_coverage) como los campos incrustados para el changelog.
        contract = load_schema_contract(dataset_name)
        degradation = build_degradation(dataset_name, metadata, validation)
        coverage = build_coverage(dataset_name, metadata, contract)
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


def _enriched_entry(
    dataset,
    catalog_key,
    base_metadata,
    df,
    *,
    include_dataset=True,
    alias_for=None,
    include_reuse=True,
    extra=None,
    trailing_extra=None,
):
    """Entrada enriquecida estándar (Plan 132c, auditoría 2026-10-13).

    Reproduce el orden de claves del dict original (el artefacto es publicado):
    base → [dataset] → [alias_for] → record_count → fields → [extra] →
    [reuse_policy] → freshness → [trailing_extra].
    """
    entry: dict = {**base_metadata}
    if include_dataset:
        entry["dataset"] = dataset
    if alias_for is not None:
        entry["alias_for"] = alias_for
    entry["record_count"] = df.height
    entry["fields"] = df.columns
    if extra:
        entry.update(extra)
    if include_reuse:
        entry["reuse_policy"] = DATASET_CATALOG_CONFIG[catalog_key]["reuse_policy"]
    entry["freshness"] = build_freshness(
        base_metadata.get("refreshed_at_utc"),
        DATASET_CATALOG_CONFIG[catalog_key]["freshness_policy"]["max_age_hours"],
    )
    if trailing_extra:
        entry.update(trailing_extra)
    return entry


def _optional_dataset_entry(
    name,
    df,
    base_metadata,
    *,
    source_detail_default="",
    require_metadata=True,
):
    """Entrada de un dataset opcional; `{}` si el insumo no está (Plan 091).

    Con `require_metadata=False` reproduce el caso `empresas`: el original solo
    exige el frame (la metadata se asume presente cuando el frame lo está).
    """
    if df is None or (require_metadata and base_metadata is None):
        return {}
    return {
        name: {
            "dataset": name,
            "source_name": base_metadata.get("source_name", ""),
            "source_url": base_metadata.get("source_url", ""),
            "source_mode": base_metadata.get("source_mode", "fallback"),
            "source_detail": base_metadata.get("source_detail", source_detail_default),
            "refreshed_at_utc": base_metadata.get("refreshed_at_utc", ""),
            "record_count": df.height,
            "fields": df.columns,
            "notes": base_metadata.get("notes", []),
            "reuse_policy": DATASET_CATALOG_CONFIG[name]["reuse_policy"],
            "freshness": build_freshness(
                base_metadata.get("refreshed_at_utc", ""),
                DATASET_CATALOG_CONFIG[name]["freshness_policy"]["max_age_hours"],
            ),
        }
    }


def _metadata_perfil_territorial(dfs, meta):
    """Perfil territorial: capa derivada.

    `source_mode` es "live" solo si TODOS los upstreams lo son de verdad:
    "monthly" es fuente genuina (ver NON_FALLBACK_SOURCE_MODES y ADR-014), no
    un respaldo hardcodeado.
    """
    upstreams = (
        meta["comunas"],
        meta["censo"],
        meta["censo_hogares"],
        meta["salud"],
        meta["electoral"],
        meta["educacionales"],
        meta["finanzas"],
        meta["resultados_educacionales"],
        meta["siedu"],
    )
    return {
        "dataset": "perfil_territorial_comunal",
        "source_name": "chile-hub",
        "source_url": "https://github.com/cortega26/chile-hub",
        "source_mode": "live"
        if all(metadata.get("source_mode") in NON_FALLBACK_SOURCE_MODES for metadata in upstreams)
        else "fallback",
        "source_detail": "derived_from_validated_chile_hub_layers",
        "refreshed_at_utc": datetime.now(UTC).isoformat(),
        "record_count": dfs["perfil_territorial"].height,
        "fields": dfs["perfil_territorial"].columns,
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
    }


def build_dataset_metadata(dfs, meta):
    """Construye el diccionario de metadatos enriquecidos por dataset.

    Plan 132c (auditoría 2026-10-13): el bloque original de 443 líneas se
    descompone en helpers por patrón (`_enriched_entry`,
    `_optional_dataset_entry`, `_metadata_perfil_territorial`); este
    orquestador conserva el ORDEN de las claves del dict original.
    """
    indicador_codes = sorted(dfs["indicadores"]["codigo_indicador"].unique().to_list())
    indicador_max_dates, indicador_ages = build_indicator_ages(dfs["indicadores"])

    return {
        "regiones": _enriched_entry("regiones", "regiones", meta["comunas"], dfs["regiones"]),
        "provincias": _enriched_entry(
            "provincias", "provincias", meta["comunas"], dfs["provincias"]
        ),
        "comunas": _enriched_entry("comunas", "comunas", meta["comunas"], dfs["comunas"]),
        "comunas_enriquecidas": _enriched_entry(
            "comunas_enriquecidas",
            "comunas",
            meta["comunas"],
            dfs["comunas"],
            alias_for="comunas",
        ),
        "indicadores": _enriched_entry(
            "indicadores",
            "indicadores",
            meta["indicadores"],
            dfs["indicadores"],
            extra={
                "indicator_codes": indicador_codes,
                "indicator_max_date": indicador_max_dates,
                "indicator_age_days": indicador_ages,
                "indicator_delivery": build_indicator_delivery(
                    {**meta["indicadores"], "indicator_codes": indicador_codes}
                ),
            },
        ),
        "censo_comunal": _enriched_entry(
            "censo_comunal", "censo_comunal", meta["censo"], dfs["censo"]
        ),
        "establecimientos_salud": _enriched_entry(
            "establecimientos_salud",
            "establecimientos_salud",
            meta["salud"],
            dfs["salud"],
        ),
        "establecimientos_educacionales": _enriched_entry(
            "establecimientos_educacionales",
            "establecimientos_educacionales",
            meta["educacionales"],
            dfs["educacionales"],
        ),
        "censo_hogares_viviendas": _enriched_entry(
            "censo_hogares_viviendas",
            "censo_hogares_viviendas",
            meta["censo_hogares"],
            dfs["censo_hogares"],
            include_dataset=False,
            include_reuse=False,
        ),
        "distritos_electorales": _enriched_entry(
            "distritos_electorales",
            "distritos_electorales",
            meta["electoral"],
            dfs["electoral"],
            include_dataset=False,
            include_reuse=False,
        ),
        "finanzas_municipales": _enriched_entry(
            "finanzas_municipales", "finanzas_municipales", meta["finanzas"], dfs["finanzas"]
        ),
        "resultados_educacionales": _enriched_entry(
            "resultados_educacionales",
            "resultados_educacionales",
            meta["resultados_educacionales"],
            dfs["resultados_educacionales"],
        ),
        "indicadores_urbanos_siedu": _enriched_entry(
            "indicadores_urbanos_siedu",
            "indicadores_urbanos_siedu",
            meta["siedu"],
            dfs["siedu"],
            trailing_extra={"coverage": meta["siedu"].get("coverage", {})},
        ),
        "perfil_territorial_comunal": _metadata_perfil_territorial(dfs, meta),
        **_optional_dataset_entry(
            "empresas",
            dfs["empresas"],
            meta["empresas"],
            source_detail_default="datos_gob_cl_ckan_api",
            require_metadata=False,
        ),
        **_optional_dataset_entry(
            "pobreza_comunal", dfs["pobreza_comunal"], meta["pobreza_comunal"]
        ),
        **_optional_dataset_entry(
            "consumo_electrico_comunal", dfs["consumo_electrico"], meta["consumo_electrico"]
        ),
        **_optional_dataset_entry(
            "partidos_politicos", dfs["partidos_politicos"], meta["partidos_politicos"]
        ),
        **_optional_dataset_entry(
            "autoridades_electas", dfs["autoridades_electas"], meta["autoridades_electas"]
        ),
        **_optional_dataset_entry(
            "estadisticas_vitales", dfs["estadisticas_vitales"], meta["estadisticas_vitales"]
        ),
        **_optional_dataset_entry(
            "permisos_edificacion", dfs["permisos_edificacion"], meta["permisos_edificacion"]
        ),
        **_optional_dataset_entry("calidad_aire", dfs["calidad_aire"], meta["calidad_aire"]),
        "precipitaciones_dgac": _enriched_entry(
            "precipitaciones_dgac",
            "precipitaciones_dgac",
            meta["precipitaciones_dgac"],
            dfs["precipitaciones_dgac"],
        ),
    }
