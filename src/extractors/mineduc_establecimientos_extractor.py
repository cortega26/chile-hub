"""Extrae el directorio oficial de establecimientos educacionales de MINEDUC."""

import datetime
import os
import subprocess
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
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "establecimientos_educacionales.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "establecimientos_educacionales.metadata.json")

# URL oficial del Directorio de Establecimientos Educacionales 2025
DOWNLOAD_URL = (
    "https://datosabiertos.mineduc.cl/wp-content/uploads/2025/11/Directorio-Oficial-EE-2025.rar"
)

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY-3.0",
    "license_url": "https://creativecommons.org/licenses/by/3.0/cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": "Directorio oficial MINEDUC publicado por el Centro de Estudios del Ministerio de Educación de Chile bajo licencia CC BY.",
}


def fetch_data() -> tuple[Path, str, str]:
    ensure_staging_directories()
    # Path del rar temporal
    rar_path = Path(RAW_DIR) / "mineduc_directorio_2025.rar"

    try:
        # Intentar fetch en vivo
        print(f"Intentando descargar {DOWNLOAD_URL}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        r = requests.get(DOWNLOAD_URL, headers=headers, timeout=60)
        r.raise_for_status()
        rar_path.write_bytes(r.content)
        print("Descarga completada.")

        # Intentar extraer usando unrar local
        unrar_bin = Path(ROOT_DIR) / ".venv" / "bin" / "unrar"
        if not unrar_bin.exists():
            # Buscar en el PATH por si acaso
            unrar_bin = "unrar"

        print(f"Extrayendo {rar_path} con {unrar_bin}...")
        cmd = [str(unrar_bin), "x", "-y", str(rar_path), RAW_DIR]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Eliminar archivo RAR temporal para no ensuciar data/raw
        if rar_path.exists():
            rar_path.unlink()

        if res.returncode != 0:
            print(f"Error en extracción (code {res.returncode}): {res.stderr}")
            raise RuntimeError(f"Error al extraer el archivo RAR: {res.stderr}")

        # Buscar el archivo CSV extraído
        csv_files = sorted(Path(RAW_DIR).glob("*Directorio_Oficial_EE*.csv"))
        if not csv_files:
            raise FileNotFoundError("No se encontró el archivo CSV extraído en data/raw/")

        # Retornamos el último encontrado
        return csv_files[-1], "live", DOWNLOAD_URL

    except Exception as e:
        print(f"Error en fetch live: {e}. Activando estrategia de fallback...")
        # Limpiar RAR temporal si quedó
        if rar_path.exists():
            rar_path.unlink()

        # Estrategia fallback: Buscar algún CSV existente en data/raw
        snapshots = sorted(Path(RAW_DIR).glob("*Directorio_Oficial_EE*.csv"))
        if not snapshots:
            raise FileNotFoundError(
                "No hay snapshots locales de MINEDUC en data/raw/ para fallback."
            ) from e
        return snapshots[-1], "fallback", DOWNLOAD_URL


def parse_csv(path: Path) -> pl.DataFrame:
    # Leer el CSV con separador ";" y codificación utf8-lossy para ignorar BOM y caracteres mal formados
    source = pl.read_csv(
        path,
        separator=";",
        encoding="utf8-lossy",
        infer_schema_length=20000,
        schema_overrides={
            "RBD": pl.String,
            "DGV_RBD": pl.String,
            "COD_REG_RBD": pl.String,
            "COD_COM_RBD": pl.String,
            "COD_DEPE2": pl.Int32,
            "ESTADO_ESTAB": pl.Int32,
        },
    )

    # Filtrar establecimientos cerrados (ESTADO_ESTAB == 3)
    # y realizar las transformaciones del schema canónico
    normalized = (
        source.filter(pl.col("ESTADO_ESTAB") != 3)
        .select(
            [
                pl.col("RBD").alias("rbd"),
                pl.col("DGV_RBD").alias("dv_rbd"),
                pl.col("NOM_RBD").alias("nombre_establecimiento"),
                pl.col("COD_REG_RBD").str.zfill(2).alias("codigo_region"),
                pl.col("COD_COM_RBD").str.zfill(5).alias("codigo_comuna"),
                pl.col("COD_DEPE2")
                .replace_strict(
                    {
                        1: "Municipal",
                        2: "Particular Subvencionado",
                        3: "Particular Pagado",
                        4: "Corporación de Administración Delegada",
                        5: "Servicio Local de Educación (SLEP)",
                    },
                    default="Otro",
                )
                .alias("dependencia_administrativa"),
                pl.col("LATITUD")
                .str.replace(",", ".")
                .cast(pl.Float64, strict=False)
                .alias("latitud"),
                pl.col("LONGITUD")
                .str.replace(",", ".")
                .cast(pl.Float64, strict=False)
                .alias("longitud"),
                pl.col("ESTADO_ESTAB")
                .replace_strict(
                    {1: "Vigente", 2: "Receso", 3: "Cerrado", 4: "Autorizado sin matrícula"},
                    default="Desconocido",
                )
                .alias("estado_funcionamiento"),
            ]
        )
        .filter(pl.col("rbd").is_not_null())
        .unique(subset=["rbd"], keep="last")
        .sort("rbd")
    )

    return normalized


def process_mineduc() -> str:
    path, source_mode, source_url = fetch_data()
    df = parse_csv(path)

    # Validar
    validation = MineducEstablecimientosExtractor().validate(df, {"source_mode": source_mode})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    metadata = {
        "dataset": "establecimientos_educacionales",
        "source_name": "Ministerio de Educación - Directorio Oficial de Establecimientos",
        "source_url": source_url,
        "source_mode": source_mode,
        "source_detail": "mineduc_datos_abiertos_rar"
        if source_mode == "live"
        else "raw_snapshot_recovery",
        "refreshed_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [],
        "reuse_policy": REUSE_POLICY,
    }

    MineducEstablecimientosExtractor().write_staging(df, metadata)
    print(
        f"Establecimientos educacionales guardados en: {STAGING_CSV_PATH} ({df.height} registros, {source_mode})"
    )
    return STAGING_CSV_PATH


class MineducEstablecimientosExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "establecimientos_educacionales"

    def fetch(self, **kwargs):
        return fetch_data()

    def normalize(self, raw_data):
        return parse_csv(raw_data[0])

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_establecimientos_educacionales

        return validate_establecimientos_educacionales(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


if __name__ == "__main__":
    process_mineduc()
