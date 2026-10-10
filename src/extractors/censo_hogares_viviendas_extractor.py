"""Extrae viviendas y hogares censados por comuna desde Censo 2024."""

import datetime
import sys
from pathlib import Path
from zipfile import BadZipFile

import openpyxl
import polars as pl
import requests

UTC = datetime.timezone.utc

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_csv_atomic,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_csv_atomic

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

from src.validation import validate_censo_hogares_viviendas

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
STAGING_CSV_PATH = STAGING_DIR / "censo_hogares_viviendas.csv"
METADATA_PATH = STAGING_DIR / "censo_hogares_viviendas.metadata.json"
SOURCE_URL = (
    "https://censo2024.ine.gob.cl/wp-content/uploads/2025/03/V1_Viviendas-y-hogares-censados.xlsx"
)
# Anti-bot: censo2024.ine.gob.cl responde 404 al UA por defecto de requests
# (bloqueo introducido ~2026-08-04; mismo patrón que mineduc_establecimientos).
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}
REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC BY 4.0",
    "license_url": "https://www.ine.gob.cl/terminos-de-uso",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": "Resultados oficiales del Censo 2024; atribucion requerida.",
}


class CensoHogaresViviendasExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "censo_hogares_viviendas"

    def fetch(self, **kwargs):
        return fetch_workbook()

    def normalize(self, raw_data):
        path, _ = raw_data
        return parse_workbook(path)

    def validate(self, df, metadata: dict) -> dict:
        return validate_censo_hogares_viviendas(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        merged = {**metadata, "dataset": self.dataset_name, "reuse_policy": REUSE_POLICY}
        return write_staging_csv_atomic(df, STAGING_CSV_PATH, METADATA_PATH, merged)


def fetch_workbook():
    ensure_staging_directories()
    target = (
        RAW_DIR
        / f"ine_censo2024_hogares_viviendas_{datetime.datetime.now(UTC):%Y%m%dT%H%M%SZ}.xlsx"
    )
    recoverable = (
        requests.RequestException,
        OSError,
        BadZipFile,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        pl.exceptions.PolarsError,
    )
    try:
        with fetch_with_retry(SOURCE_URL, timeout=60, headers=REQUEST_HEADERS) as response:
            response.raise_for_status()
            target.write_bytes(response.content)
        _assert_usable_workbook(target)
        return target, "live"
    except recoverable:
        snapshots = sorted(RAW_DIR.glob("ine_censo2024_hogares_viviendas_*.xlsx"), reverse=True)
        for snapshot in snapshots:
            try:
                _assert_usable_workbook(snapshot)
            except recoverable:
                continue
            return snapshot, "fallback"
        raise


def _assert_usable_workbook(path: Path) -> None:
    """Rechaza XLSX corruptos, vacíos o sin una tabla de hogares reconocible."""
    df = parse_workbook(path)
    if df.is_empty() or "hogares_censados" not in df.columns:
        raise ValueError(f"Censo viviendas/hogares sin registros utilizables: {path.name}")


def parse_workbook(path):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    records = {}
    for row in workbook["2"].iter_rows(min_row=5, values_only=True):
        if not row[4] or int(row[4]) == 0:
            continue
        code = str(int(row[4])).zfill(5)
        records[code] = {
            "codigo_region": str(int(row[0])).zfill(2),
            "nombre_region": row[1],
            "codigo_provincia": str(int(row[2])).zfill(3),
            "nombre_provincia": row[3],
            "codigo_comuna": code,
            "nombre_comuna": row[5],
            "viviendas_censadas": int(row[6]),
            "viviendas_particulares_ocupadas": int(row[7]),
            "viviendas_particulares_desocupadas": int(row[8]),
            "viviendas_colectivas": int(row[9]),
        }
    for row in workbook["6"].iter_rows(min_row=5, values_only=True):
        if len(row) < 8:
            continue
        if not row[4] or int(row[4]) == 0:
            continue
        code = str(int(row[4])).zfill(5)
        records[code].update(
            {
                "hogares_censados": int(row[6]),
                "promedio_personas_hogar": None if row[7] in ("-", None) else float(row[7]),
            }
        )
    workbook.close()
    return pl.DataFrame(list(records.values())).sort("codigo_comuna")


def process():
    path, source_mode = fetch_workbook()
    df = parse_workbook(path)
    extractor = CensoHogaresViviendasExtractor()
    validation = extractor.validate(df, {"source_mode": source_mode})
    if validation["status"] == "error":
        raise SystemExit(f"Validacion fallida: {validation['errors']}")

    metadata = {
        "dataset": "censo_hogares_viviendas",
        "source_name": "Instituto Nacional de Estadisticas - Censo 2024",
        "source_url": SOURCE_URL,
        "source_mode": source_mode,
        "source_detail": "official_xlsx" if source_mode == "live" else "raw_snapshot_recovery",
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(f"Censo hogares y viviendas guardado: {df.height} registros ({source_mode})")


if __name__ == "__main__":
    process()
