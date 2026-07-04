"""Extractor de partidos políticos desde el web service de datos abiertos de la Cámara.

Fuente: `WSComun.asmx/retornarPartidosPoliticos` (Cámara de Diputadas y Diputados).
Devuelve el roster de partidos conocidos por la Cámara (Id/Nombre/Alias), que incluye
partidos vigentes e históricos asociados a las militancias de los diputados/as. No es el
registro legal de SERVEL: `estado_legal`, `fecha_constitucion` y `ambito` no vienen en
esta fuente y quedan nullable en v1 (completar con SERVEL en un follow-up).

Plan 023 · Ola B. Solo datos institucionales públicos; sin datos personales.
"""

import datetime
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import polars as pl

UTC = datetime.timezone.utc

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from http_utils import fetch_with_retry

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "partidos_politicos.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "partidos_politicos.metadata.json")

SOURCE_URL = (
    "https://opendata.camara.cl/camaradiputados/WServices/WSComun.asmx/retornarPartidosPoliticos"
)
CAMARA_NS = {"v": "http://opendata.camara.cl/camaradiputados/v1"}

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Roster de partidos políticos publicado por la Cámara de Diputadas y Diputados "
        "en su portal de datos abiertos (datos institucionales públicos)."
    ),
}

# Sufijos/valores esperados para reconciliación (orden de magnitud, no rígido).
MIN_EXPECTED_PARTIES = 15


def _text(node: ET.Element, tag: str) -> str:
    child = node.find(f"v:{tag}", CAMARA_NS)
    return (child.text or "").strip() if child is not None and child.text else ""


def fetch_partidos_xml() -> bytes:
    """Descarga el XML de partidos desde el web service de la Cámara."""
    headers = {"User-Agent": "chile-hub/data-pipeline (+https://github.com/cortega26/chile-hub)"}
    response = fetch_with_retry(SOURCE_URL, timeout=30, headers=headers)
    response.raise_for_status()
    content: bytes = response.content
    return content


def parse_partidos(xml_bytes: bytes) -> pl.DataFrame:
    """Parsea el XML de la Cámara al esquema canónico de `partidos_politicos`."""
    root = ET.fromstring(xml_bytes)
    fecha_consulta = datetime.datetime.now(UTC).date().isoformat()
    rows = []
    for partido in root.findall(".//v:PartidoPolitico", CAMARA_NS):
        id_partido = _text(partido, "Id")
        nombre = _text(partido, "Nombre")
        sigla = _text(partido, "Alias") or id_partido
        if not id_partido or not nombre:
            continue
        rows.append(
            {
                "id_partido": id_partido,
                "nombre": nombre,
                "sigla": sigla,
                # No provistos por la Cámara → nullable en v1 (completar con SERVEL).
                "estado_legal": None,
                "fecha_constitucion": None,
                "ambito": None,
                "fuente": "Cámara de Diputadas y Diputados (datos abiertos)",
                "url_fuente": SOURCE_URL,
                "fecha_consulta": fecha_consulta,
            }
        )
    df = pl.DataFrame(
        rows,
        schema={
            "id_partido": pl.String,
            "nombre": pl.String,
            "sigla": pl.String,
            "estado_legal": pl.String,
            "fecha_constitucion": pl.String,
            "ambito": pl.String,
            "fuente": pl.String,
            "url_fuente": pl.String,
            "fecha_consulta": pl.String,
        },
    )
    return df.unique(subset=["id_partido"], keep="first").sort("id_partido")


class PartidosPoliticosExtractor(BaseExtractor):
    """Extractor del roster de partidos políticos de la Cámara."""

    @property
    def dataset_name(self) -> str:
        return "partidos_politicos"

    def fetch(self, **kwargs) -> bytes:
        return fetch_partidos_xml()

    def normalize(self, raw_data: bytes) -> pl.DataFrame:
        return parse_partidos(raw_data)

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        errors = []
        if df.height < MIN_EXPECTED_PARTIES:
            errors.append(
                f"Conteo de partidos ({df.height}) por debajo del mínimo esperado "
                f"({MIN_EXPECTED_PARTIES})."
            )
        if df.filter(pl.col("id_partido").is_null() | (pl.col("id_partido") == "")).height:
            errors.append("Hay partidos sin id_partido.")
        if df["id_partido"].n_unique() != df.height:
            errors.append("id_partido no es único.")
        # Línea roja: sin columnas de datos personales.
        personales = {"rut", "run", "domicilio"}
        if personales & {c.lower() for c in df.columns}:
            errors.append("El dataset contiene columnas de datos personales (línea roja).")
        return {"status": "error" if errors else "ok", "errors": errors, "record_count": df.height}

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


def process_partidos_politicos() -> str:
    """Ejecuta el extractor standalone (invocado desde el Makefile)."""
    ensure_staging_directories()
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = Path(RAW_DIR) / f"camara_partidos_{stamp}.xml"

    extractor = PartidosPoliticosExtractor()
    xml_bytes = extractor.fetch()
    with open(raw_path, "wb") as f:
        f.write(xml_bytes)

    df = extractor.normalize(xml_bytes)
    validation = extractor.validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    metadata = {
        "dataset": "partidos_politicos",
        "source_name": "Cámara de Diputadas y Diputados (datos abiertos)",
        "source_url": SOURCE_URL,
        "source_mode": "live",
        "source_detail": "WSComun.asmx/retornarPartidosPoliticos",
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            "Roster de partidos de la Cámara (incluye vigentes e históricos).",
            "estado_legal/fecha_constitucion/ambito no provistos por la fuente (nullable v1).",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(f"Partidos políticos guardados en: {STAGING_CSV_PATH} ({df.height} registros)")
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process_partidos_politicos()
