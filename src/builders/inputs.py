"""Tabla única de insumos de staging y loader del build.

Plan 132a (auditoría 2026-10-13): `_load_inputs` en `build_dev_db.py`
(364 líneas) repetía la lista de datasets cuatro veces (rutas, requeridos,
metadatos, frames). Acá vive **una** tabla (`STAGING_INPUTS`) y un loader
genérico; `build_dev_db._load_inputs` queda como fachada que pasa sus globales
para preservar los overrides de `tests/test_phase1_characterization`.

Semántica preservada (contrato de los tests de caracterización):
- Requeridos: primero se validan TODOS los CSV y después los metadatos
  (mismo orden y mensajes de error que antes).
- Opcionales: se cargan solo si existen CSV y metadata; si no, el frame queda
  en `None` y se loguea `dataset_skipped` (no bloquea el build — Plan 091).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import cast

import polars as pl

from ._logging import get_logger
from .datasets import build_perfil_territorial_comunal, derive_geography_layers
from .metadata import build_indicator_delivery, load_metadata
from .staging_schema import STAGING_SCHEMAS, apply_date_casts

log = get_logger("build_dev_db")


@dataclass(frozen=True)
class StagingInput:
    """Un dataset de entrada del build.

    `name` es la clave en los dicts de frames/metadata; `csv` y `metadata` son
    archivos dentro del directorio de staging; `read` selecciona la variante de
    lectura (`csv` | `date` | `datecast` | `no_schema`) y `schema` es la clave
    en `STAGING_SCHEMAS` cuando difiere de `name`.
    """

    name: str
    csv: str
    metadata: str
    extractor: str
    required: bool = True
    read: str = "csv"
    schema: str | None = None


# Orden = orden de los mensajes de error/metadata del loader original.
STAGING_INPUTS: tuple[StagingInput, ...] = (
    StagingInput("comunas", "comunas.csv", "comunas.metadata.json", "subdere_extractor.py"),
    StagingInput(
        "indicadores",
        "indicadores.csv",
        "indicadores.metadata.json",
        "bcentral_extractor.py",
        read="date",
    ),
    StagingInput(
        "censo",
        "censo_comunal.csv",
        "censo_comunal.metadata.json",
        "censo_extractor.py",
        schema="censo_comunal",
    ),
    StagingInput(
        "salud",
        "establecimientos_salud.csv",
        "establecimientos_salud.metadata.json",
        "salud_extractor.py",
        schema="establecimientos_salud",
    ),
    StagingInput(
        "censo_hogares",
        "censo_hogares_viviendas.csv",
        "censo_hogares_viviendas.metadata.json",
        "censo_hogares_viviendas_extractor.py",
        schema="censo_hogares_viviendas",
    ),
    StagingInput(
        "electoral",
        "distritos_electorales.csv",
        "distritos_electorales.metadata.json",
        "electoral_extractor.py",
        schema="distritos_electorales",
    ),
    StagingInput(
        "educacionales",
        "establecimientos_educacionales.csv",
        "establecimientos_educacionales.metadata.json",
        "mineduc_establecimientos_extractor.py",
        schema="establecimientos_educacionales",
    ),
    StagingInput(
        "finanzas",
        "finanzas_municipales.csv",
        "finanzas_municipales.metadata.json",
        "sinim_finanzas_extractor.py",
        schema="finanzas_municipales",
    ),
    StagingInput(
        "resultados_educacionales",
        "resultados_educacionales.csv",
        "resultados_educacionales.metadata.json",
        "mineduc_resultados_extractor.py",
        schema="resultados_educacionales",
    ),
    StagingInput(
        "siedu",
        "indicadores_urbanos_siedu.csv",
        "indicadores_urbanos_siedu.metadata.json",
        "siedu_extractor.py",
        schema="indicadores_urbanos_siedu",
    ),
    # Opcionales (no bloquean el build; Plan 091)
    StagingInput(
        "empresas",
        "empresas.csv",
        "empresas.metadata.json",
        "res_extractor.py",
        required=False,
        read="datecast",
    ),
    StagingInput(
        "pobreza_comunal",
        "pobreza_comunal.csv",
        "pobreza_comunal.metadata.json",
        "pobreza_extractor.py",
        required=False,
        schema="pobreza_comunal",
    ),
    StagingInput(
        "consumo_electrico",
        "consumo_electrico_comunal.csv",
        "consumo_electrico_comunal.metadata.json",
        "consumo_electrico_extractor.py",
        required=False,
        schema="consumo_electrico_comunal",
    ),
    StagingInput(
        "partidos_politicos",
        "partidos_politicos.csv",
        "partidos_politicos.metadata.json",
        "partidos_politicos_extractor.py",
        required=False,
        read="no_schema",
    ),
    StagingInput(
        "autoridades_electas",
        "autoridades_electas.csv",
        "autoridades_electas.metadata.json",
        "autoridades_electas_extractor.py",
        required=False,
        schema="autoridades_electas",
    ),
    StagingInput(
        "estadisticas_vitales",
        "estadisticas_vitales.csv",
        "estadisticas_vitales.metadata.json",
        "estadisticas_vitales_extractor.py",
        required=False,
        schema="estadisticas_vitales",
    ),
    StagingInput(
        "permisos_edificacion",
        "permisos_edificacion.csv",
        "permisos_edificacion.metadata.json",
        "permisos_edificacion_extractor.py",
        required=False,
        schema="permisos_edificacion",
    ),
    StagingInput(
        "calidad_aire",
        "calidad_aire.csv",
        "calidad_aire.metadata.json",
        "calidad_aire_extractor.py",
        required=False,
        schema="calidad_aire",
    ),
)


def _read_frame(spec: StagingInput, csv_path: str) -> pl.DataFrame:
    """Lee el CSV de un insumo según su variante (schemas + casts especiales)."""
    if spec.read == "date":
        schema_key = spec.schema or spec.name
        return pl.read_csv(csv_path, schema_overrides=STAGING_SCHEMAS[schema_key]).with_columns(
            pl.col("fecha").str.to_date("%Y-%m-%d")
        )
    if spec.read == "datecast":
        return apply_date_casts(
            pl.read_csv(csv_path, schema_overrides=STAGING_SCHEMAS[spec.schema or spec.name]),
            spec.name,
        )
    if spec.read == "no_schema":
        return pl.read_csv(csv_path, infer_schema_length=None)
    return pl.read_csv(csv_path, schema_overrides=STAGING_SCHEMAS[spec.schema or spec.name])


def _load_previous_pipeline_metadata(normalized_dir: str) -> dict | None:
    """Metadata del build anterior (para deltas); `None` si no existe o es inválida."""
    path = os.path.join(normalized_dir, "pipeline_metadata.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return cast("dict", json.load(f))
    except json.JSONDecodeError:
        return None


def load_staging_inputs(
    staging_dir: str, normalized_dir: str
) -> tuple[dict[str, pl.DataFrame | None], dict[str, dict | None], dict | None]:
    """Carga metadatos y frames de staging según `STAGING_INPUTS`.

    Devuelve `(frames, metadata, previous_pipeline_metadata)`; los opcionales
    ausentes quedan en `None` dentro de `frames`.
    """
    required = [
        (spec, os.path.join(staging_dir, spec.csv)) for spec in STAGING_INPUTS if spec.required
    ]
    if any(not os.path.exists(path) for _, path in required):
        raise SystemExit(
            "Error: No se encuentran los archivos CSV en staging. Corre los extractores primero."
        )
    for spec, _ in required:
        if not os.path.exists(os.path.join(staging_dir, spec.metadata)):
            raise SystemExit(
                f"Error: No se encuentra {spec.metadata} en data/staging/. "
                f"Corre el extractor primero: python src/extractors/{spec.extractor}"
            )

    required_frames: dict[str, pl.DataFrame] = {}
    optional_frames: dict[str, pl.DataFrame | None] = {}
    metadata: dict[str, dict | None] = {}
    for spec in STAGING_INPUTS:
        csv_path = os.path.join(staging_dir, spec.csv)
        metadata_path = os.path.join(staging_dir, spec.metadata)
        if spec.required:
            metadata[spec.name] = load_metadata(metadata_path)
            required_frames[spec.name] = _read_frame(spec, csv_path)
            continue
        meta = load_metadata(metadata_path) if os.path.exists(metadata_path) else None
        metadata[spec.name] = meta
        if os.path.exists(csv_path) and meta is not None:
            frame = _read_frame(spec, csv_path)
            optional_frames[spec.name] = frame
            log.info("dataset_loaded", dataset=spec.name, records=frame.height)
        else:
            optional_frames[spec.name] = None
            log.info("dataset_skipped", dataset=spec.name, reason="not_found_in_staging")

    indicadores_meta = cast("dict", metadata["indicadores"])
    indicadores_meta["indicator_codes"] = sorted(indicadores_meta.get("indicator_codes", []))
    indicadores_meta["indicator_delivery"] = build_indicator_delivery(indicadores_meta)

    required_frames["regiones"], required_frames["provincias"] = derive_geography_layers(
        required_frames["comunas"]
    )
    required_frames["perfil_territorial"] = build_perfil_territorial_comunal(
        required_frames["comunas"],
        required_frames["censo"],
        required_frames["censo_hogares"],
        required_frames["salud"],
        required_frames["educacionales"],
        required_frames["electoral"],
        required_frames["finanzas"],
        required_frames["resultados_educacionales"],
        required_frames["siedu"],
        df_vitales=optional_frames["estadisticas_vitales"],
        df_permisos=optional_frames["permisos_edificacion"],
        df_calidad=optional_frames["calidad_aire"],
    )

    frames: dict[str, pl.DataFrame | None] = {**required_frames, **optional_frames}
    return frames, metadata, _load_previous_pipeline_metadata(normalized_dir)
