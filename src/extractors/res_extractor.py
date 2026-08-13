"""Extrae el Registro de Empresas y Sociedades (RES) desde datos.gob.cl.

Fuente: https://datos.gob.cl/dataset/registro-de-empresas-y-sociedades
Licencia: CC-BY (open-attribution)
Formato: CSV anual (2013-2026), delimitado por ;
Columnas originales:
  ID;RUT;Razon Social;Fecha de actuacion;Fecha de registro;
  Fecha de aprobacion x SII;Anio;Mes;Comuna Tributaria;Region Tributaria;
  Codigo de sociedad;Tipo de actuacion;Capital;Comuna Social;Region Social

El dataset se consolida en una sola tabla con columnas normalizadas a snake_case.
No contiene dirección postal (solo comuna y región), ni actividad económica.
"""

import datetime
import io
import os
import re
import sys
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
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "empresas.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "empresas.metadata.json")

# API de CKAN para obtener los recursos del dataset RES
PACKAGE_API_URL = (
    "https://datos.gob.cl/api/3/action/package_show?id=registro-de-empresas-y-sociedades"
)

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY",
    "license_url": "https://creativecommons.org/licenses/by/3.0/cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Registro de Empresas y Sociedades (RES) del Ministerio de Economia, "
        "publicado en datos.gob.cl bajo CC-BY. "
        "Contiene constituciones de empresas bajo la Ley 20.659."
    ),
}

# Columnas del CSV original -> nombres canónicos en snake_case
COLUMN_RENAME = {
    "ID": "id_res",
    "RUT": "rut",
    "Razon Social": "razon_social",
    "Fecha de actuacion (1era firma)": "fecha_actuacion",
    "Fecha de registro (ultima firma)": "fecha_registro",
    "Fecha de aprobacion x SII": "fecha_aprobacion_sii",
    "Anio": "anio",
    "Mes": "mes",
    "Comuna Tributaria": "comuna_tributaria",
    "Region Tributaria": "region_tributaria",
    "Codigo de sociedad": "codigo_sociedad",
    "Tipo de actuacion": "tipo_actuacion",
    "Capital": "capital",
    "Comuna Social": "comuna_social",
    "Region Social": "region_social",
}

# Valores de RUT que la fuente usa como marcador de "sin dato" en vez de como
# identificador. Se descartan en la normalización (ver normalize_rows) y el
# conteo queda en los metadatos de staging para que un alza sea visible.
RUT_SENTINELS = ["0"]

# Filas descartadas por centinela en la última corrida de parse_resources().
# Se expone como estado de módulo (el pipeline es secuencial y de un solo hilo)
# para que process() pueda registrarlo en los metadatos de staging sin cambiar
# la firma de parse_resources(), que es parte del contrato del extractor.
_LAST_SENTINEL_DROP_COUNT = 0

# Modo del último fetch (Plan 076): "incremental" (solo el año en curso porque
# el staging ya tiene el histórico) o "full" (primera carga o staging ilegible).
# Mismo patrón de estado de módulo que _LAST_SENTINEL_DROP_COUNT.
_LAST_FETCH_MODE = "full"

# Tipos de sociedad que mapean a abreviaturas canónicas
SOCIEDAD_MAP = {
    "SRL": "SRL",
    "SPA": "SpA",
    "EIRL": "EIRL",
    "SA": "SA",
    "SC": "SC",
    "SCPA": "SCpA",
    "SCA": "SCA",
    "COOP": "COOP",
    "EE": "EE",
    "FNDC": "FNDC",
    "AGR": "AGR",
    "COPROP": "COPROP",
}


def _staging_years_present() -> set[int] | None:
    """Años presentes en el staging consolidado (columna `anio`).

    Retorna ``None`` si no hay staging o no se puede leer (primera carga o
    staging de una generación distinta) — en ese caso el fetch es completo.
    Solo lee la columna ``anio`` (lazy scan): el consolidado tiene ~1.57M
    filas, pero proyectar una sola columna es barato.
    """
    if not os.path.exists(STAGING_CSV_PATH):
        return None
    try:
        years = (
            pl.scan_csv(STAGING_CSV_PATH, infer_schema_length=0)
            .select("anio")
            .unique()
            .collect()["anio"]
            .cast(pl.Int32, strict=False)
            .to_list()
        )
    except Exception:
        return None
    return {y for y in years if y is not None}


_RESOURCE_YEAR_RE = re.compile(r"[Aa]ño\s+(\d{4})")


def _resource_year(resource: dict) -> int | None:
    """Año del archivo anual, extraído del nombre del recurso.

    Los recursos siguen el patrón "Constituciones del año 2026, con fecha de
    corte al 30 de junio del 2026" — el año en curso cambia de nombre en cada
    republicación (corte), los históricos son estables.
    """
    name = resource.get("name", "")
    match = _RESOURCE_YEAR_RE.search(name)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def fetch_resources() -> tuple[list[bytes], str, str]:
    """Obtiene los CSVs del dataset RES desde datos.gob.cl.

    Incremental (Plan 076): si el staging consolidado ya existe, solo se
    descargan los archivos del año en curso (+ el año anterior si falta —
    la fuente puede publicarlo con retraso). Sin staging, se descarga el
    histórico completo. El merge con el staging previo lo hace process().

    Retorna:
        Tupla con (lista_de_contenidos_csv_bytes, source_mode, source_detail).
    """
    ensure_staging_directories()

    with fetch_with_retry(PACKAGE_API_URL, timeout=30) as package:
        package.raise_for_status()
        payload = package.json()["result"]

    csv_resources = [r for r in payload["resources"] if r.get("format", "").lower() == "csv"]

    if not csv_resources:
        raise SystemExit("No se encontraron recursos CSV en el dataset RES.")

    global _LAST_FETCH_MODE
    present_years = _staging_years_present()
    current_year = datetime.date.today().year

    if present_years is None:
        selected_resources = csv_resources
        _LAST_FETCH_MODE = "full"
    else:
        years_to_fetch = {current_year}
        if current_year - 1 not in present_years:
            years_to_fetch.add(current_year - 1)
        selected_resources = [r for r in csv_resources if _resource_year(r) in years_to_fetch]
        # Si la fuente cambió el naming y ningún recurso matchea los años
        # buscados, degradar a fetch completo en vez de quedarse sin datos.
        if not selected_resources:
            selected_resources = csv_resources
            _LAST_FETCH_MODE = "full"
        else:
            _LAST_FETCH_MODE = "incremental"

    contents = []
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    for resource in selected_resources:
        resource_name = resource.get("name", "unknown").replace(" ", "_")
        raw_path = Path(RAW_DIR) / f"res_{resource_name}_{stamp}.csv"

        try:
            with fetch_with_retry(resource["url"], timeout=120) as response:
                response.raise_for_status()
                raw_path.write_bytes(response.content)
                contents.append(response.content)
        except Exception as exc:
            # Si falla la descarga live, intentar recuperar snapshots raw previos
            snapshots = sorted(Path(RAW_DIR).glob(f"res_{resource_name}_*.csv"))
            if snapshots:
                contents.append(snapshots[-1].read_bytes())
            else:
                raise SystemExit(
                    f"Error descargando {resource['url']}: {exc}. No hay snapshot raw de respaldo."
                )

    return contents, "live", "datos_gob_cl_ckan_api"


def parse_resources(contents: list[bytes]) -> pl.DataFrame:
    """Parsea y consolida todos los CSVs anuales del RES en un solo DataFrame.

    Args:
        contents: Lista de contenidos CSV en bytes (uno por año).

    Retorna:
        DataFrame de Polars con todas las constituciones normalizadas.
    """
    frames = []

    for content in contents:
        # El CSV usa ; como delimitador y puede tener BOM
        text = content.decode("utf-8-sig")
        df_year = pl.read_csv(
            io.StringIO(text),
            separator=";",
            infer_schema_length=0,  # todo como string para controlar la normalización
        )

        # Renombrar columnas al canon snake_case
        existing_cols = {c: COLUMN_RENAME[c] for c in df_year.columns if c in COLUMN_RENAME}
        df_year = df_year.rename(existing_cols)

        frames.append(df_year)

    if not frames:
        raise SystemExit("No se pudieron parsear los archivos CSV del RES.")

    df = pl.concat(frames, how="diagonal_relaxed")

    # ── Normalización ─────────────────────────────────────────────────────

    # RUT: limpiar espacios, conservar guion y digito verificador
    df = df.with_columns(pl.col("rut").str.strip_chars().str.replace_all(r"\.", "").alias("rut"))

    # razon_social: titulo (primera letra mayuscula de cada palabra)
    df = df.with_columns(
        pl.col("razon_social")
        .str.strip_chars()
        .str.to_lowercase()
        .str.to_titlecase()
        .alias("razon_social")
    )

    # anio: entero
    df = df.with_columns(pl.col("anio").cast(pl.Int32, strict=False).alias("anio"))

    # codigo_sociedad: mapear a abreviatura canonica
    df = df.with_columns(
        pl.col("codigo_sociedad")
        .str.strip_chars()
        .str.to_uppercase()
        .replace_strict(SOCIEDAD_MAP, default=None)
        .alias("codigo_sociedad")
    )

    # capital: limpiar y convertir a entero
    df = df.with_columns(pl.col("capital").cast(pl.Int64, strict=False).alias("capital"))

    # comunas: titulo, sin espacios extra
    for col in ("comuna_tributaria", "comuna_social"):
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).str.strip_chars().str.to_lowercase().str.to_titlecase().alias(col)
            )

    # regiones: código numérico a string con padding (2 dígitos)
    for col in ("region_tributaria", "region_social"):
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).cast(pl.String, strict=False).str.strip_chars().str.zfill(2).alias(col)
            )

    # Fechas: convertir a Date (formato DD-MM-YYYY)
    for col in ("fecha_actuacion", "fecha_registro", "fecha_aprobacion_sii"):
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).str.strip_chars().str.to_date("%d-%m-%Y", strict=False).alias(col)
            )

    # Eliminar filas sin RUT (encabezados repetidos u otros artefactos)
    df = df.filter(pl.col("rut").is_not_null() & (pl.col("rut").str.len_chars() > 0))

    # Centinelas de la fuente: filas donde el RUT es un marcador de "sin dato"
    # ("0") en vez de un identificador. No es un RUT mal tipeado, así que
    # corregir el dígito verificador no aplica; y dejarlo en null tampoco sirve,
    # porque validate_empresas() trata los RUT nulos como error duro. Se
    # descartan y se cuentan: un alza en este contador es señal de que la
    # fuente cambió de comportamiento (issue #42).
    global _LAST_SENTINEL_DROP_COUNT
    _LAST_SENTINEL_DROP_COUNT = df.filter(pl.col("rut").is_in(RUT_SENTINELS)).height
    if _LAST_SENTINEL_DROP_COUNT:
        df = df.filter(~pl.col("rut").is_in(RUT_SENTINELS))

    # Eliminar duplicados exactos (puede haber overlap entre archivos anuales)
    df = df.unique()

    # Ordenar por fecha de registro descendente, luego RUT
    df = df.sort(["fecha_registro", "rut"], descending=[True, False])

    # ── Columnas finales ───────────────────────────────────────────────────
    final_cols = [
        "rut",
        "razon_social",
        "codigo_sociedad",
        "tipo_actuacion",
        "capital",
        "fecha_actuacion",
        "fecha_registro",
        "fecha_aprobacion_sii",
        "anio",
        "mes",
        "comuna_tributaria",
        "region_tributaria",
        "comuna_social",
        "region_social",
    ]
    # Solo incluir columnas que existen
    available = [c for c in final_cols if c in df.columns]

    return df.select(available)


class ResExtractor(BaseExtractor):
    """Extractor para el Registro de Empresas y Sociedades (RES)."""

    @property
    def dataset_name(self) -> str:
        return "empresas"

    def fetch(self, **kwargs):
        return fetch_resources()

    def normalize(self, raw_data):
        contents, _, _ = raw_data
        return parse_resources(contents)

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_empresas

        return validate_empresas(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        full_metadata = {
            **metadata,
            "dataset": self.dataset_name,
            "record_count": df.height,
            "fields": df.columns,
            "reuse_policy": REUSE_POLICY,
        }
        write_staging_metadata(METADATA_PATH, full_metadata)
        return output


def _merge_incremental(df_new: pl.DataFrame) -> pl.DataFrame:
    """Concatena el staging consolidado previo con el año recién parseado.

    Plan 076: el fetch incremental solo trae el año en curso; el histórico
    vive en `data/staging/empresas.csv`. Detalles de contrato:

    - `infer_schema_length=0` al leer el staging: las columnas de región son
      numéricas con padding ("01") y el inferir como int les quita el cero —
      validate_empresas las exige en formato de 2 dígitos (P1 de la review
      del PR #74).
    - Dedup por clave natural `(rut, razon_social, fecha_registro)` con
      `keep="last"`: la fuente republica el año en curso con correcciones;
      un `unique()` de fila completa conservaría el registro stale y el
      corregido como dos filas (P2 de la review del PR #74). Con
      `concat([existing, new])`, keep="last" hace ganar la versión nueva.
      Conserva el sort final del contrato.
    """
    existing = pl.read_csv(STAGING_CSV_PATH, infer_schema_length=0)
    merged = pl.concat([existing, df_new], how="diagonal_relaxed")
    merged = merged.unique(subset=["rut", "razon_social", "fecha_registro"], keep="last")
    merged = merged.sort(["fecha_registro", "rut"], descending=[True, False])
    return merged


def process() -> str:
    """Ejecuta el pipeline completo del extractor RES."""
    contents, source_mode, source_detail = fetch_resources()
    df = parse_resources(contents)
    if _LAST_FETCH_MODE == "incremental":
        df = _merge_incremental(df)

    extractor = ResExtractor()
    validation = extractor.validate(df, {"source_mode": source_mode})
    if validation["status"] == "error":
        raise SystemExit(f"Validacion fallida: {validation['errors']}")

    metadata = {
        "dataset": "empresas",
        "source_name": (
            "Ministerio de Economia, Fomento y Turismo - Registro de Empresas y Sociedades (RES)"
        ),
        "source_url": ("https://datos.gob.cl/dataset/registro-de-empresas-y-sociedades"),
        "source_mode": source_mode,
        "source_detail": source_detail,
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            f"filas descartadas por RUT centinela {RUT_SENTINELS}: {_LAST_SENTINEL_DROP_COUNT}",
            "Solo incluye empresas constituidas bajo el Regimen Simplificado "
            "(Ley 20.659) desde mayo 2013.",
            "No contiene dirección postal (solo comuna y región).",
            "No contiene actividad económica (giro).",
            "No refleja cese de actividades ni modificaciones posteriores.",
            "Los codigos de region usan el formato numerico del SII (1-15), "
            "distinto del codigo CUT (01-16). Verificar antes de cruzar con DPA.",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(f"Empresas RES guardadas en: {STAGING_CSV_PATH} ({df.height} registros, {source_mode})")
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process()
