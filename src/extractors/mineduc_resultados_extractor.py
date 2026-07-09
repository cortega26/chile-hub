"""Extrae resultados educacionales agregados desde fuentes MINEDUC.

Fuente: Rendimiento_2024.rar (MINEDUC Datos Abiertos).
  - CSV student-level de ~3.5M filas (separador ';', encoding UTF-8 BOM).
  - Se agrega a nivel (anio, codigo_comuna) para producir los 8 campos del contrato.
  - SIT_FIN_R codes: P=Promovido, R=Reprobado, T=Trasladado, Y=Retirado (true dropout).
"""

import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

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
    from src.extractors.source_adapter import build_standard_metadata
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from source_adapter import build_standard_metadata

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
STAGING_CSV_PATH = STAGING_DIR / "resultados_educacionales.csv"
METADATA_PATH = STAGING_DIR / "resultados_educacionales.metadata.json"

DOWNLOAD_URL = "https://datosabiertos.mineduc.cl/wp-content/uploads/2025/04/Rendimiento_2024.rar"
SOURCE_URL = DOWNLOAD_URL
RAR_FILENAME = "mineduc_rendimiento_2024.rar"

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY-3.0",
    "license_url": "https://creativecommons.org/licenses/by/3.0/cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Datos agregados desde Rendimiento 2024 del Centro de Estudios MINEDUC; "
        "citar fuente oficial."
    ),
}

FALLBACK_ROWS = [
    {
        "anio": 2024,
        "codigo_comuna": "13101",
        "matricula_total": 122000,
        "asistencia_promedio": 86.2,
        "tasa_aprobacion": 91.4,
        "tasa_reprobacion": 4.1,
        "tasa_retiro": 4.5,
        "establecimientos_reportados": 410,
    },
    {
        "anio": 2024,
        "codigo_comuna": "05109",
        "matricula_total": 52500,
        "asistencia_promedio": 85.9,
        "tasa_aprobacion": 92.1,
        "tasa_reprobacion": 3.6,
        "tasa_retiro": 4.3,
        "establecimientos_reportados": 175,
    },
    {
        "anio": 2024,
        "codigo_comuna": "08101",
        "matricula_total": 48700,
        "asistencia_promedio": 84.7,
        "tasa_aprobacion": 90.8,
        "tasa_reprobacion": 4.8,
        "tasa_retiro": 4.4,
        "establecimientos_reportados": 151,
    },
]


def _find_unrar() -> Path | str:
    unrar_bin = Path(ROOT_DIR) / ".venv" / "bin" / "unrar"
    if not unrar_bin.exists():
        return "unrar"
    return unrar_bin


def _aggregate_rendimiento(csv_path: Path) -> list[dict[str, Any]]:
    """Lee el CSV de rendimiento (student-level) y agrega a nivel de comuna."""
    df = (
        pl.scan_csv(
            csv_path,
            separator=";",
            encoding="utf8-lossy",
            infer_schema_length=5000,
            schema_overrides={
                "AGNO": pl.Int32,
                "COD_COM_RBD": pl.String,
                "RBD": pl.Int64,
                "ASISTENCIA": pl.Int32,
                "SIT_FIN_R": pl.String,
            },
        )
        .select(["AGNO", "COD_COM_RBD", "RBD", "ASISTENCIA", "SIT_FIN_R"])
        .filter(pl.col("AGNO").is_not_null())
        .with_columns(pl.col("COD_COM_RBD").str.zfill(5).alias("codigo_comuna"))
        .group_by(["AGNO", "codigo_comuna"])
        .agg(
            [
                pl.len().alias("matricula_total"),
                # Asistencia: solo estudiantes activos (P o R) con asistencia registrada
                pl.col("ASISTENCIA")
                .filter(pl.col("SIT_FIN_R").is_in(["P", "R"]) & (pl.col("ASISTENCIA") > 0))
                .mean()
                .fill_null(0.0)
                .alias("asistencia_promedio"),
                # Rates: cada código sobre el total de matrícula
                (pl.col("SIT_FIN_R").eq("P").sum() * 100.0 / pl.len()).alias("tasa_aprobacion"),
                (pl.col("SIT_FIN_R").eq("R").sum() * 100.0 / pl.len()).alias("tasa_reprobacion"),
                # SIT_FIN_R == 'Y' = Retirado (dropout; excluye Trasladado 'T')
                (pl.col("SIT_FIN_R").eq("Y").sum() * 100.0 / pl.len()).alias("tasa_retiro"),
                pl.col("RBD").n_unique().alias("establecimientos_reportados"),
            ]
        )
        .rename({"AGNO": "anio"})
        .sort(["anio", "codigo_comuna"])
        .collect()
    )
    return df.to_dicts()


def fetch_data(source_url: str = DOWNLOAD_URL) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Descarga Rendimiento_2024.rar y agrega a nivel comuna, con fallback a filas curadas."""
    ensure_staging_directories()
    notes: list[str] = [
        "privacy_safe_comuna_year_aggregation",
        "sit_fin_r_Y=retirado T=trasladado asistencia_only_for_P_R_students",
    ]

    rar_path = RAW_DIR / RAR_FILENAME

    try:
        print(f"Descargando {source_url} ...")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )
        }
        with fetch_with_retry(source_url, headers=headers, timeout=180) as r:
            r.raise_for_status()
            rar_path.write_bytes(r.content)
        size_mb = rar_path.stat().st_size // 1024 // 1024
        print(f"Descarga completada ({size_mb} MB).")

        unrar_bin = _find_unrar()
        if shutil.which(str(unrar_bin)) is None and not Path(unrar_bin).exists():
            raise SystemExit(
                f"unrar no está disponible ({unrar_bin}). Instala con 'apt-get install unrar'."
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            print(f"Extrayendo CSV a {tmp_dir} ...")
            cmd = [str(unrar_bin), "e", "-y", str(rar_path), tmp_dir + "/"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode != 0:
                raise RuntimeError(f"Error al extraer RAR (code {res.returncode}): {res.stderr}")

            csv_files = sorted(Path(tmp_dir).glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No se encontró ningún CSV en {tmp_dir}")

            csv_path = csv_files[-1]
            csv_mb = csv_path.stat().st_size // 1024 // 1024
            print(f"Procesando {csv_path.name} ({csv_mb} MB) ...")

            rows = _aggregate_rendimiento(csv_path)
        # TemporaryDirectory se elimina aquí automáticamente

        if not rows:
            raise ValueError("La agregación produjo 0 registros")

        notes.append(f"source_file: {rar_path.name}, comunas_agregadas: {len(rows)}")
        print(f"Extracción completada: {len(rows)} registros por (anio, comuna).")
        return rows, "live", source_url, notes

    except Exception as exc:
        print(f"Error en extracción live: {exc}. Usando fallback ...")
        notes.append(f"fallback_curated_rows_used: {type(exc).__name__}: {exc}")
        return FALLBACK_ROWS, "fallback", source_url, notes


def normalize_rows(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("anio").cast(pl.Int32),
            pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
            pl.col("matricula_total").cast(pl.Int64),
            pl.col("asistencia_promedio").cast(pl.Float64),
            pl.col("tasa_aprobacion").cast(pl.Float64),
            pl.col("tasa_reprobacion").cast(pl.Float64),
            pl.col("tasa_retiro").cast(pl.Float64),
            pl.col("establecimientos_reportados").cast(pl.Int64),
        )
        .sort(["anio", "codigo_comuna"])
    )


def build_metadata(df: pl.DataFrame, source_mode: str, source_url: str, notes: list[str]) -> dict:
    source_detail = (
        "mineduc_rendimiento_2024_rar_agregado_por_comuna"
        if source_mode == "live"
        else "curated_fallback_comuna_year_aggregation"
    )
    return build_standard_metadata(
        dataset="resultados_educacionales",
        source_name="Centro de Estudios MINEDUC - Rendimiento 2024",
        source_url=source_url,
        source_mode=source_mode,
        source_detail=source_detail,
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )


def process_mineduc_resultados() -> str:
    raw_rows, source_mode, source_url, notes = fetch_data()
    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)
    validation = MineducResultadosExtractor().validate(df, metadata)
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")
    MineducResultadosExtractor().write_staging(df, metadata)
    print(
        f"Resultados educacionales guardados en: {STAGING_CSV_PATH} "
        f"({df.height} registros, {source_mode})"
    )
    return str(STAGING_CSV_PATH)


class MineducResultadosExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "resultados_educacionales"

    def fetch(self, **kwargs):
        return fetch_data(**kwargs)

    def normalize(self, raw_data):
        return normalize_rows(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_resultados_educacionales

        return validate_resultados_educacionales(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_mineduc_resultados()
