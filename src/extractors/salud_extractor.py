"""Extrae el directorio vigente de establecimientos de salud de MINSAL."""

import datetime
import os
import sys
from pathlib import Path

import polars as pl
import requests

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "establecimientos_salud.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "establecimientos_salud.metadata.json")
PACKAGE_API_URL = (
    "https://datos.gob.cl/api/3/action/package_show?id=3bf4cf7c-f638-4735-9a01-f65faae4beca"
)
REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC0",
    "license_url": "http://www.opendefinition.org/licenses/cc-zero",
    "attribution_required": False,
    "redistribution_ok": True,
    "summary": "Directorio oficial MINSAL publicado en datos.gob.cl bajo CC0.",
}


def fetch_csv() -> tuple[Path, str, str]:
    ensure_staging_directories()
    try:
        package = requests.get(PACKAGE_API_URL, timeout=30)
        package.raise_for_status()
        payload = package.json()["result"]
        resource = next(item for item in payload["resources"] if item["format"].lower() == "csv")
        response = requests.get(resource["url"], timeout=60)
        response.raise_for_status()
        stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        target = Path(RAW_DIR) / f"minsal_establecimientos_salud_{stamp}.csv"
        target.write_bytes(response.content)
        return target, "live", resource["url"]
    except Exception:
        snapshots = sorted(Path(RAW_DIR).glob("minsal_establecimientos_salud_*.csv"))
        if not snapshots:
            raise
        return snapshots[-1], "fallback", PACKAGE_API_URL


def parse_csv(path: Path) -> pl.DataFrame:
    source = pl.read_csv(
        path,
        separator=";",
        encoding="utf8-lossy",
        infer_schema_length=10000,
        schema_overrides={"RegionCodigo": pl.String, "ComunaCodigo": pl.String},
    )
    return (
        source.select(
            pl.col("EstablecimientoCodigo").cast(pl.String).alias("codigo_establecimiento"),
            pl.col("EstablecimientoGlosa").alias("nombre_establecimiento"),
            pl.col("TipoEstablecimientoGlosa").alias("tipo_establecimiento"),
            pl.col("DependenciaAdministrativa").alias("dependencia_administrativa"),
            pl.col("NivelAtencionEstabglosa").alias("nivel_atencion"),
            pl.col("RegionCodigo").str.zfill(2).alias("codigo_region"),
            pl.col("RegionGlosa").alias("nombre_region"),
            pl.col("ComunaCodigo").str.zfill(5).alias("codigo_comuna"),
            pl.col("ComunaGlosa").alias("nombre_comuna"),
            pl.col("TieneServicioUrgencia").alias("tiene_servicio_urgencia"),
            pl.col("TipoUrgencia").alias("tipo_urgencia"),
            pl.col("Latitud").cast(pl.Float64, strict=False).alias("latitud"),
            pl.col("Longitud").cast(pl.Float64, strict=False).alias("longitud"),
            pl.col("EstadoFuncionamiento").alias("estado_funcionamiento"),
        )
        .filter(pl.col("codigo_establecimiento").is_not_null())
        .unique(subset=["codigo_establecimiento"], keep="last")
        .sort("codigo_establecimiento")
    )


def process_salud() -> str:
    path, source_mode, source_url = fetch_csv()
    df = parse_csv(path)
    validation = SaludExtractor().validate(df, {"source_mode": source_mode})
    if validation["status"] == "error":
        raise SystemExit(f"Validacion fallida: {validation['errors']}")
    metadata = {
        "dataset": "establecimientos_salud",
        "source_name": "Ministerio de Salud - Establecimientos de Salud",
        "source_url": source_url,
        "source_mode": source_mode,
        "source_detail": "datos_gob_csv" if source_mode == "live" else "raw_snapshot_recovery",
        "refreshed_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [],
        "reuse_policy": REUSE_POLICY,
    }
    SaludExtractor().write_staging(df, metadata)
    print(
        f"Establecimientos de salud guardados en: {STAGING_CSV_PATH} ({df.height} registros, {source_mode})"
    )
    return STAGING_CSV_PATH


class SaludExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "establecimientos_salud"

    def fetch(self, **kwargs):
        return fetch_csv()

    def normalize(self, raw_data):
        return parse_csv(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_establecimientos_salud

        return validate_establecimientos_salud(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


if __name__ == "__main__":
    process_salud()
