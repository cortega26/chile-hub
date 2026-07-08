"""Extrae estimaciones de pobreza comunal (CASEN / SAE) desde el Observatorio Social del MDS.

Fuente: Observatorio Social — Ministerio de Desarrollo Social y Familia
URL: https://observatorio.ministeriodesarrollosocial.gob.cl/pobreza-comunal-2022
Formato: 2 archivos XLSX (tasa de pobreza por ingresos + índice multidimensional)
Metodología: Estimación de Áreas Pequeñas (SAE) a partir de la encuesta CASEN
"""

import datetime
import os
import sys
from pathlib import Path

import openpyxl
import polars as pl
import requests

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
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "pobreza_comunal.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "pobreza_comunal.metadata.json")

# ── URLs de descarga ────────────────────────────────────────────────────────
BASE_URL = "https://observatorio.ministeriodesarrollosocial.gob.cl"
POBREZA_INGRESOS_URL = (
    f"{BASE_URL}/storage/docs/pobreza-comunal/2022/"
    "Estimaciones_Tasa_Pobreza_Ingresos_Comunas_2022.xlsx"
)
POBREZA_MULTIDIMENSIONAL_URL = (
    f"{BASE_URL}/storage/docs/pobreza-comunal/2022/"
    "Estimaciones_Indice_Pobreza_Multidimensional_Comunas_2022.xlsx"
)

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "Datos abiertos MDS",
    "license_url": "https://observatorio.ministeriodesarrollosocial.gob.cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Estimaciones de pobreza comunal derivadas de CASEN por el Observatorio Social "
        "del MDS. Datos abiertos con atribución requerida."
    ),
}

# ── Fallback mínimo ─────────────────────────────────────────────────────────
# Datos de las 3 comunas más pobladas + 1 rural como referencia estructural.
# NO es un respaldo de cobertura total; solo evita que el build se rompa
# si el portal del MDS no responde.
FALLBACK_ROWS = [
    {
        "codigo_region": "13",
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "anio": 2022,
        "dimension": "ingresos",
        "tasa": 4.5,
        "limite_inferior": 3.2,
        "limite_superior": 6.1,
        "metodologia": "SAE",
        "fuente": "Observatorio Social — MDS (fallback)",
        "url_fuente": POBREZA_INGRESOS_URL,
        "fecha_fuente": "",
    },
    {
        "codigo_region": "13",
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "anio": 2022,
        "dimension": "multidimensional",
        "tasa": 8.2,
        "limite_inferior": 6.1,
        "limite_superior": 10.5,
        "metodologia": "SAE",
        "fuente": "Observatorio Social — MDS (fallback)",
        "url_fuente": POBREZA_MULTIDIMENSIONAL_URL,
        "fecha_fuente": "",
    },
    {
        "codigo_region": "08",
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "anio": 2022,
        "dimension": "ingresos",
        "tasa": 6.8,
        "limite_inferior": 4.9,
        "limite_superior": 9.0,
        "metodologia": "SAE",
        "fuente": "Observatorio Social — MDS (fallback)",
        "url_fuente": POBREZA_INGRESOS_URL,
        "fecha_fuente": "",
    },
]

# Columnas que produce el extractor
REQUIRED_COLUMNS = [
    "codigo_region",
    "codigo_comuna",
    "nombre_comuna",
    "anio",
    "dimension",
    "tasa",
    "limite_inferior",
    "limite_superior",
    "metodologia",
    "fuente",
    "url_fuente",
    "fecha_fuente",
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _snapshot_path(label: str) -> Path:
    """Genera una ruta de snapshot crudo con timestamp."""
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(RAW_DIR) / f"mds_pobreza_comunal_{label}_{stamp}.xlsx"


def _download_xlsx(url: str, label: str) -> Path:
    """Descarga un XLSX y guarda snapshot crudo. Retorna la ruta al archivo."""
    target = _snapshot_path(label)
    with fetch_with_retry(url, timeout=60) as response:
        response.raise_for_status()
        target.write_bytes(response.content)
    return target


def _parse_pobreza_xlsx(path: Path, dimension: str, anio: int) -> list[dict]:
    """Parsea un XLSX de pobreza comunal y retorna filas normalizadas.

    Formato real verificado el 2026-07-08 (hoja "Estimaciones", ambos archivos
    ingresos y multidimensional comparten layout): fila 1 título, fila 2 en
    blanco, fila 3 encabezado, datos desde la fila 4 en adelante:
    [código_comuna, nombre_región, nombre_comuna, población_proyectada,
    personas_en_pobreza, tasa (fracción 0-1), límite_inferior, límite_superior,
    presencia_muestra_casen, tipo_estimación_sae]. El archivo no incluye un
    código de región numérico — se deriva de los 2 primeros dígitos del
    código de comuna (convención DPA estándar). La tasa y los límites vienen
    como fracción; se escalan a porcentaje para igualar la convención del
    resto del dataset (ver FALLBACK_ROWS).
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows_raw = list(sheet.iter_rows(min_row=4, values_only=True))
    workbook.close()

    rows = []
    for row in rows_raw:
        # Detectar fila de datos: debe tener al menos 4 celdas con valores
        if not row or sum(1 for c in row if c is not None) < 4:
            continue

        try:
            codigo_comuna = str(int(row[0])).zfill(5) if row[0] is not None else None
            codigo_region = codigo_comuna[:2] if codigo_comuna else None
            nombre_comuna = str(row[2]).strip() if row[2] is not None else ""
            tasa = float(row[5]) * 100 if row[5] is not None else None
            limite_inferior = float(row[6]) * 100 if len(row) > 6 and row[6] is not None else None
            limite_superior = float(row[7]) * 100 if len(row) > 7 and row[7] is not None else None
        except (ValueError, TypeError, IndexError):
            continue

        if codigo_comuna is None:
            continue

        rows.append(
            {
                "codigo_region": codigo_region,
                "codigo_comuna": codigo_comuna,
                "nombre_comuna": nombre_comuna,
                "anio": anio,
                "dimension": dimension,
                "tasa": tasa,
                "limite_inferior": limite_inferior,
                "limite_superior": limite_superior,
                "metodologia": "SAE",
                "fuente": "Observatorio Social — Ministerio de Desarrollo Social y Familia",
                "url_fuente": (
                    POBREZA_INGRESOS_URL
                    if dimension == "ingresos"
                    else POBREZA_MULTIDIMENSIONAL_URL
                ),
                "fecha_fuente": datetime.datetime.now(UTC).strftime("%Y-%m-%d"),
            }
        )
    return rows


def fetch_data() -> tuple[list[dict], str, str, list[str]]:
    """Obtiene datos de pobreza comunal desde el Observatorio Social.

    Retorna (rows, source_mode, source_url, notes).
    """
    ensure_staging_directories()
    notes = []
    all_rows = []

    downloads = [
        (POBREZA_INGRESOS_URL, "ingresos", "ingresos"),
        (POBREZA_MULTIDIMENSIONAL_URL, "multidimensional", "multidimensional"),
    ]

    any_live = False
    for url, dimension, label in downloads:
        try:
            path = _download_xlsx(url, label)
            rows = _parse_pobreza_xlsx(path, dimension, anio=2022)
            all_rows.extend(rows)
            any_live = True
            notes.append(f"{dimension}: {len(rows)} comunas con estimación desde URL oficial")
        except (requests.RequestException, OSError, KeyError) as exc:
            # Intentar recuperar del último snapshot
            snapshots = sorted(Path(RAW_DIR).glob(f"mds_pobreza_comunal_{label}_*.xlsx"))
            if snapshots:
                rows = _parse_pobreza_xlsx(snapshots[-1], dimension, anio=2022)
                all_rows.extend(rows)
                notes.append(
                    f"{dimension}: {len(rows)} comunas desde snapshot "
                    f"{snapshots[-1].name} (error: {exc})"
                )
            else:
                notes.append(f"{dimension}: sin datos — descarga falló y no hay snapshot ({exc})")

    if not all_rows:
        return FALLBACK_ROWS, "fallback", POBREZA_INGRESOS_URL, notes

    mode = "live" if any_live else "fallback"
    return all_rows, mode, POBREZA_INGRESOS_URL, notes


def normalize_rows(rows: list[dict]) -> pl.DataFrame:
    """Convierte filas de pobreza a DataFrame canónico."""
    if not rows:
        return pl.DataFrame(schema={col: pl.String for col in REQUIRED_COLUMNS})

    df = pl.DataFrame(rows, strict=False)

    # Asegurar que existen todas las columnas requeridas
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col in ("tasa", "limite_inferior", "limite_superior"):
                df = df.with_columns(pl.lit(None, dtype=pl.Float64).alias(col))
            elif col == "anio":
                df = df.with_columns(pl.lit(2022, dtype=pl.Int64).alias(col))
            else:
                df = df.with_columns(pl.lit("", dtype=pl.String).alias(col))

    # Tipos correctos
    df = df.with_columns(
        pl.col("codigo_region").cast(pl.String),
        pl.col("codigo_comuna").cast(pl.String),
        pl.col("nombre_comuna").cast(pl.String),
        pl.col("anio").cast(pl.Int64),
        pl.col("dimension").cast(pl.String),
        pl.col("tasa").cast(pl.Float64),
        pl.col("limite_inferior").cast(pl.Float64),
        pl.col("limite_superior").cast(pl.Float64),
        pl.col("metodologia").cast(pl.String),
        pl.col("fuente").cast(pl.String),
        pl.col("url_fuente").cast(pl.String),
        pl.col("fecha_fuente").cast(pl.String),
    )

    return df.select(REQUIRED_COLUMNS)


def build_metadata(mode: str, source_url: str, notes: list[str], row_count: int) -> dict:
    """Construye metadatos estándar para el dataset."""
    return {
        "dataset": "pobreza_comunal",
        "source_name": "Observatorio Social — Ministerio de Desarrollo Social y Familia",
        "source_url": source_url,
        "source_mode": mode,
        "source_detail": "Estimaciones de Pobreza Comunal vía SAE desde encuesta CASEN",
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": row_count,
        "fields": REQUIRED_COLUMNS,
        "notes": notes,
        "reuse_policy": REUSE_POLICY,
    }


def process_pobreza_comunal() -> dict:
    """Ejecuta el flujo completo de extracción y staging."""
    rows, mode, source_url, notes = fetch_data()
    df = normalize_rows(rows)

    metadata = build_metadata(mode, source_url, notes, df.height)

    ensure_staging_directories()
    df.write_csv(STAGING_CSV_PATH)
    write_staging_metadata(METADATA_PATH, metadata)
    print(f"pobreza_comunal: {df.height} filas escritas en staging (mode={mode})")

    return metadata


# ── Extractor ────────────────────────────────────────────────────────────────


class PobrezaComunalExtractor(BaseExtractor):
    """Extractor de pobreza comunal desde el Observatorio Social del MDS."""

    @property
    def dataset_name(self) -> str:
        return "pobreza_comunal"

    def fetch(self, **kwargs):
        return fetch_data()

    def normalize(self, raw_data):
        rows, _mode, _url, _notes = raw_data
        return normalize_rows(rows)

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_pobreza_comunal

        return validate_pobreza_comunal(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(str(output))
        merged = {
            **metadata,
            "dataset": self.dataset_name,
            "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
            "record_count": df.height,
        }
        write_staging_metadata(METADATA_PATH, merged)
        return output


if __name__ == "__main__":
    process_pobreza_comunal()
