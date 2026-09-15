"""Extrae calidad del aire por estación desde el SINCA (MMA).

Fuente: Sistema de Información Nacional de Calidad del Aire — Ministerio del
Medio Ambiente
URL: https://sinca.mma.gob.cl/
Formato: 1 JSON diario (`listadomapa2k19`) con inventario de estaciones
  (código, nombre, comuna, región, lat/lon) + series horarias de las últimas
  24 h por contaminante. El extractor agrega a grano diario por estación.

Alcance MVP: promedios diarios por (fecha, estación, contaminante) para
MP2.5, MP10, SO2, NO2, CO y O3. La serie es incremental: cada corrida agrega
el último día sobre el historial. Como el JSON solo trae 24 h, el historial
se siembra desde el Parquet publicado (`data/normalized/calidad_aire.parquet`)
cuando staging está vacío (p. ej. tras un cache-miss de CI) —excepción
documentada al flujo staging→normalized, sin la cual la historia se
reiniciaría en silencio.

Cobertura parcial por diseño: ~65 de 346 comunas tienen estación de
monitoreo (verificado contra el inventario; documentado en NOTES).
"""

import datetime
import html as html_module
import os
import sys
from pathlib import Path
from typing import Any

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

try:
    from src.extractors.region_utils import norm_text
except ModuleNotFoundError:
    from region_utils import norm_text

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "calidad_aire.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "calidad_aire.metadata.json")
COMUNAS_CSV_PATH = os.path.join(STAGING_DIR, "comunas.csv")
HISTORY_PARQUET_PATH = os.path.join(NORMALIZED_DIR, "calidad_aire.parquet")

# ── Fuente ───────────────────────────────────────────────────────────────────
LISTADO_URL = "https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/"

SOURCE_NAME = "SINCA — Ministerio del Medio Ambiente"
LICENSE_URL = "https://sinca.mma.gob.cl/"

REUSE_POLICY = {
    "status": "public-api-review-terms",
    "license": "Datos públicos MMA; sin licencia explícita, citar fuente oficial",
    "license_url": LICENSE_URL,
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Mediciones de calidad del aire del SINCA (MMA), API JSON pública. "
        "Organismo público chileno sin restricción explícita de reúso; "
        "citar fuente oficial."
    ),
}

# Código SINCA (JSON realtime + CSV) -> (código canónico, nombre, unidad).
CONTAMINANTES = {
    "PM25": ("mp25", "MP 2,5", "ug/m3"),
    "PM10": ("mp10", "MP 10", "ug/m3"),
    "0001": ("so2", "SO2", "ug/m3N"),
    "0003": ("no2", "NO2", "ppbv"),
    "0004": ("co", "CO", "ppmv"),
    "0008": ("o3", "O3", "ppbv"),
}

# Grafías de comuna en SINCA → clean DPA (norm_text ya aplicado).
COMUNA_ALIAS: dict[str, str] = {}

REQUIRED_COLUMNS = [
    "fecha",
    "id_estacion",
    "nombre_estacion",
    "codigo_region",
    "codigo_comuna",
    "nombre_comuna",
    "latitud",
    "longitud",
    "codigo_contaminante",
    "nombre_contaminante",
    "unidad",
    "valor_promedio_diario",
    "valor_max_horario",
    "horas_validas",
    "estado_dato",
    "fuente",
    "url_fuente",
    "fecha_fuente",
]

# ── Fallback mínimo ─────────────────────────────────────────────────────────
# Estructural, no cobertura: evita que el build se rompa si el SINCA no
# responde. El job `publish` de CI rechaza datasets en fallback (§5).
FALLBACK_ROWS = [
    {
        "fecha": "2026-09-14",
        "id_estacion": "271",
        "nombre_estacion": "Quilicura",
        "codigo_region": "13",
        "codigo_comuna": "13144",
        "nombre_comuna": "Quilicura",
        "latitud": -33.36,
        "longitud": -70.73,
        "codigo_contaminante": "mp25",
        "nombre_contaminante": "MP 2,5",
        "unidad": "ug/m3",
        "valor_promedio_diario": 0.0,
        "valor_max_horario": 0.0,
        "horas_validas": 1,
        "estado_dato": "provisional",
        "fuente": f"{SOURCE_NAME} (fallback)",
        "url_fuente": LISTADO_URL,
        "fecha_fuente": "",
    }
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _snapshot_path() -> Path:
    """Ruta de snapshot crudo con timestamp."""
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(RAW_DIR) / f"sinca_listadomapa_{stamp}.json"


def _to_float(value: Any) -> float | None:
    """Celda numérica a float; None/'' → None (hora inválida)."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-"):
            return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _clean_comuna(nombre: Any) -> str:
    """Normaliza un nombre de comuna SINCA para el cruce a CUT."""
    clean = norm_text(str(nombre)) if nombre is not None else ""
    return COMUNA_ALIAS.get(clean, clean)


def _load_comunas_lookup() -> dict[str, tuple[str, str, str]]:
    """``nombre_comuna_clean -> (codigo_comuna, codigo_region, nombre_comuna)``."""
    if not os.path.exists(COMUNAS_CSV_PATH):
        raise FileNotFoundError(
            "No se encuentra data/staging/comunas.csv. "
            "Corre primero: python src/extractors/subdere_extractor.py"
        )
    df = pl.read_csv(
        COMUNAS_CSV_PATH,
        schema_overrides={"codigo_comuna": pl.String, "codigo_region": pl.String},
    )
    return {
        row["nombre_comuna_clean"]: (
            row["codigo_comuna"],
            row["codigo_region"],
            row["nombre_comuna"],
        )
        for row in df.iter_rows(named=True)
    }


def _parse_realtime_series(series: dict) -> tuple[str, list[tuple[str, float]]]:
    """Extrae (codigo_contaminante, [(hora_iso, valor), ...]) de una serie.

    Omite códigos desconocidos y horas sin valor. Retorna ("", []) si la
    serie no aporta nada parseable.
    """
    code = str(series.get("code", "")).strip()
    if code not in CONTAMINANTES:
        return "", []
    canon, _, _ = CONTAMINANTES[code]
    puntos = []
    for fila in (series.get("info", {}) or {}).get("rows", []):
        celdas = fila.get("c", []) if isinstance(fila, dict) else []
        if len(celdas) < 2:
            continue
        hora = (celdas[0] or {}).get("v")
        valor = _to_float((celdas[1] or {}).get("v"))
        if not hora or valor is None:
            continue
        puntos.append((str(hora)[:16], valor))
    if not puntos:
        return "", []
    return canon, puntos


def _parse_listado(
    payload: Any, lookup: dict, url_fuente: str, fecha_fuente: str, hoy: str
) -> tuple[list[dict], list[str], dict[str, int]]:
    """Convierte el JSON del listado a filas diarias por (estación, contaminante).

    Agrega las 24 h a promedio diario + máximo horario + horas válidas.
    Retorna (filas, notas, totales_por_contaminante).
    """
    estaciones = payload if isinstance(payload, list) else []
    notas: list[str] = []
    filas: list[dict] = []
    sin_comuna: list[str] = []
    n_estaciones = 0

    for est in estaciones:
        if not isinstance(est, dict):
            continue
        key = str(est.get("key", "")).strip()
        nombre = html_module.unescape(str(est.get("nombre", "")).strip())
        if not key:
            continue
        n_estaciones += 1
        clean = _clean_comuna(est.get("comuna", ""))
        hit = lookup.get(clean)
        if hit is None:
            sin_comuna.append(f"{nombre} (comuna SINCA: {est.get('comuna', '')})")
            continue
        codigo_comuna, codigo_region, nombre_comuna = hit
        latitud = _to_float(est.get("latitud"))
        longitud = _to_float(est.get("longitud"))

        for serie in est.get("realtime", []) or []:
            canon, puntos = _parse_realtime_series(serie)
            if not canon:
                continue
            _, nombre_cont, unidad = CONTAMINANTES[str(serie.get("code", "")).strip()]
            por_fecha: dict[str, list[float]] = {}
            for hora_iso, valor in puntos:
                fecha = hora_iso[:10]
                por_fecha.setdefault(fecha, []).append(valor)
            for fecha, valores in sorted(por_fecha.items()):
                filas.append(
                    {
                        "fecha": fecha,
                        "id_estacion": key,
                        "nombre_estacion": nombre,
                        "codigo_region": codigo_region,
                        "codigo_comuna": codigo_comuna,
                        "nombre_comuna": nombre_comuna,
                        "latitud": latitud,
                        "longitud": longitud,
                        "codigo_contaminante": canon,
                        "nombre_contaminante": html_module.unescape(nombre_cont),
                        "unidad": unidad,
                        "valor_promedio_diario": round(sum(valores) / len(valores), 2),
                        "valor_max_horario": max(valores),
                        "horas_validas": len(valores),
                        "estado_dato": "provisional" if fecha >= hoy else "definitivo",
                        "fuente": SOURCE_NAME,
                        "url_fuente": url_fuente,
                        "fecha_fuente": fecha_fuente,
                    }
                )

    if sin_comuna:
        notas.append(
            f"{len(sin_comuna)} estaciones sin match CUT (se omiten): "
            f"{sorted(set(sin_comuna))[:10]}"
        )
    notas.append(
        f"inventario: {n_estaciones} estaciones en el listado; "
        f"{len({r['id_estacion'] for r in filas})} con filas emitidas"
    )
    return filas, notas, {}


def fetch_data() -> tuple[list[dict], str, str, list[str]]:
    """Obtiene calidad del aire diaria desde el SINCA.

    Retorna (rows, source_mode, source_url, notes). Las filas cubren solo el
    último día disponible; el historial se siembra desde el Parquet publicado
    (ver _seed_history_from_parquet) para no reiniciar la serie.
    """
    ensure_staging_directories()
    notes: list[str] = []
    fecha_fuente = datetime.datetime.now(UTC).strftime("%Y-%m-%d")

    try:
        lookup = _load_comunas_lookup()
    except FileNotFoundError as exc:
        return FALLBACK_ROWS, "fallback", LISTADO_URL, [str(exc)]

    from_snapshot = False
    try:
        with fetch_with_retry(LISTADO_URL, timeout=120) as response:
            response.raise_for_status()
            payload = response.json()
        target = _snapshot_path()
        target.write_bytes(response.content)
    except (requests.RequestException, OSError, ValueError) as exc:
        snapshots = sorted(Path(RAW_DIR).glob("sinca_listadomapa_*.json"))
        if not snapshots:
            notes.append(f"listado SINCA inaccesible y sin snapshots ({exc})")
            return FALLBACK_ROWS, "fallback", LISTADO_URL, notes
        target = snapshots[-1]
        notes.append(f"listado SINCA inaccesible, usando snapshot {target.name} ({exc})")
        try:
            import json as _json

            payload = _json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc2:
            notes.append(f"snapshot ilegible ({exc2})")
            return FALLBACK_ROWS, "fallback", LISTADO_URL, notes
        # El payload viene de disco (potencialmente viejo): no es "live".
        # Se reporta "fallback" para que freshness/publication lo traten como
        # no-fresco (Plan 086). Ver VALID_SOURCE_MODES en _shared.py.
        from_snapshot = True

    hoy = datetime.datetime.now(UTC).strftime("%Y-%m-%d")
    rows, parse_notes, _ = _parse_listado(payload, lookup, LISTADO_URL, fecha_fuente, hoy)
    notes.extend(parse_notes)
    if not rows:
        notes.append("listado sin filas parseables")
        return FALLBACK_ROWS, "fallback", LISTADO_URL, notes
    if from_snapshot:
        notes.append(f"{len(rows)} filas diarias recuperadas desde snapshot '{target.name}'")
        return rows, "fallback", LISTADO_URL, notes
    notes.append(f"{len(rows)} filas diarias nuevas desde '{target.name}'")
    return rows, "live", LISTADO_URL, notes


def _seed_history_from_parquet() -> pl.DataFrame | None:
    """Lee el historial publicado para sembrarlo en staging.

    Excepción documentada al flujo staging→normalized: el JSON del SINCA
    solo trae 24 h, así que sin esta siembra cada cache-miss de CI
    reiniciaría la serie en silencio. Retorna None si no hay Parquet.
    """
    if not os.path.exists(HISTORY_PARQUET_PATH):
        return None
    try:
        return pl.read_parquet(HISTORY_PARQUET_PATH)
    except Exception:  # noqa: BLE001 — Parquet corrupto: partir de cero con nota
        return None


def normalize_rows(rows: list[dict]) -> pl.DataFrame:
    """Convierte filas a DataFrame canónico."""
    if not rows:
        return pl.DataFrame(
            schema={
                "fecha": pl.String,
                "id_estacion": pl.String,
                "nombre_estacion": pl.String,
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "latitud": pl.Float64,
                "longitud": pl.Float64,
                "codigo_contaminante": pl.String,
                "nombre_contaminante": pl.String,
                "unidad": pl.String,
                "valor_promedio_diario": pl.Float64,
                "valor_max_horario": pl.Float64,
                "horas_validas": pl.Int64,
                "estado_dato": pl.String,
                "fuente": pl.String,
                "url_fuente": pl.String,
                "fecha_fuente": pl.String,
            }
        )

    df = pl.DataFrame(rows, strict=False)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))

    return df.with_columns(
        pl.col("fecha").cast(pl.String),
        pl.col("id_estacion").cast(pl.String),
        pl.col("nombre_estacion").cast(pl.String),
        pl.col("codigo_region").cast(pl.String),
        pl.col("codigo_comuna").cast(pl.String),
        pl.col("nombre_comuna").cast(pl.String),
        pl.col("latitud").cast(pl.Float64),
        pl.col("longitud").cast(pl.Float64),
        pl.col("codigo_contaminante").cast(pl.String),
        pl.col("nombre_contaminante").cast(pl.String),
        pl.col("unidad").cast(pl.String),
        pl.col("valor_promedio_diario").cast(pl.Float64),
        pl.col("valor_max_horario").cast(pl.Float64),
        pl.col("horas_validas").cast(pl.Int64),
        pl.col("estado_dato").cast(pl.String),
        pl.col("fuente").cast(pl.String),
        pl.col("url_fuente").cast(pl.String),
        pl.col("fecha_fuente").cast(pl.String),
    ).select(REQUIRED_COLUMNS)


def build_metadata(df: pl.DataFrame, mode: str, source_url: str, notes: list[str]) -> dict:
    """Construye metadatos estándar para el dataset."""
    commune_count = df["codigo_comuna"].n_unique() if df.height else 0
    metadata = {
        "dataset": "calidad_aire",
        "source_name": SOURCE_NAME,
        "source_url": source_url,
        "source_mode": mode,
        "source_detail": (
            "Promedios diarios por estación y contaminante (MP2.5, MP10, SO2, "
            "NO2, CO, O3) desde el JSON del SINCA. Cobertura parcial por "
            "diseño (~65 comunas con estación). Serie incremental desde la "
            "primera cosecha."
        ),
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": REQUIRED_COLUMNS,
        "notes": notes,
        "reuse_policy": REUSE_POLICY,
    }
    metadata["coverage"] = {
        "status": "partial_expected",
        "coverage_ratio": round(commune_count / 346, 4),
        "expected_scope": "Comunas con estación de monitoreo SINCA, no las 346 comunas del país.",
    }
    return metadata


def process_calidad_aire() -> dict:
    """Ejecuta el flujo completo de extracción y staging."""
    rows, mode, source_url, notes = fetch_data()
    df_new = normalize_rows(rows)

    # Serie incremental: fusionar con el historial (staging actual o, si no
    # existe, el Parquet publicado) deduplicando por clave primaria. Lo
    # nuevo va al final y gana (keep="last"): una re-cosecha del mismo día
    # trae datos más frescos (p. ej. validación nivel 2 del operador).
    frames = []
    if os.path.exists(STAGING_CSV_PATH):
        try:
            frames.append(
                pl.read_csv(
                    STAGING_CSV_PATH,
                    schema_overrides={
                        "codigo_region": pl.String,
                        "codigo_comuna": pl.String,
                        "id_estacion": pl.String,
                        "horas_validas": pl.Int64,
                    },
                )
            )
            notes.append("historial: fusionado con staging existente")
        except Exception as exc:  # noqa: BLE001 — staging corrupto: partir de lo nuevo
            notes.append(f"historial: staging ilegible, se parte de lo nuevo ({exc})")
    else:
        seeded = _seed_history_from_parquet()
        if seeded is not None and seeded.height > 0:
            frames.append(seeded)
            notes.append(f"historial: sembrado desde Parquet publicado ({seeded.height} filas)")

    df = pl.concat([*frames, df_new], how="diagonal").unique(
        subset=["fecha", "id_estacion", "codigo_contaminante"], keep="last"
    )
    # Tipos tras el concat (el Parquet trae fecha como Date).
    df = df.with_columns(
        pl.col("fecha").cast(pl.String),
        pl.col("horas_validas").cast(pl.Int64),
        pl.col("valor_promedio_diario").cast(pl.Float64),
        pl.col("valor_max_horario").cast(pl.Float64),
        pl.col("latitud").cast(pl.Float64),
        pl.col("longitud").cast(pl.Float64),
    ).sort(["fecha", "id_estacion", "codigo_contaminante"])

    metadata = build_metadata(df, mode, source_url, notes)

    ensure_staging_directories()
    df.write_csv(STAGING_CSV_PATH)
    write_staging_metadata(METADATA_PATH, metadata)
    print(f"calidad_aire: {df.height} filas escritas en staging (mode={mode})")

    return metadata


# ── Extractor ────────────────────────────────────────────────────────────────


class CalidadAireExtractor(BaseExtractor):
    """Extractor de calidad del aire por estación (SINCA)."""

    @property
    def dataset_name(self) -> str:
        return "calidad_aire"

    def fetch(self, **kwargs):
        return fetch_data()

    def normalize(self, raw_data):
        rows, _mode, _url, _notes = raw_data
        return normalize_rows(rows)

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_calidad_aire

        return validate_calidad_aire(df, metadata)

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
    process_calidad_aire()
