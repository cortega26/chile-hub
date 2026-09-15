"""
Extractor de Indicadores Económicos de Referencia.

Fuente operativa : mindicador.cl (API pública de la comunidad)
Fuente original  : Banco Central de Chile (BCCh) e Instituto Nacional de
                   Estadísticas (INE). El BCCh permite libre reproducción
                   con citación de la fuente.

Estrategia de actualización:
  - Primera ejecución  : descarga el historial completo desde HISTORY_START_YEAR.
  - Ejecuciones sucesivas: actualización incremental del año en curso únicamente,
    preservando el historial ya descargado en staging.
"""

import concurrent.futures
import datetime
import json
import os
import sys
import time
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
        write_raw_snapshot_atomic,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import (
        BaseExtractor,
        ensure_staging_directories,
        write_raw_snapshot_atomic,
        write_staging_metadata,
    )

try:
    from src.extractors.http_utils import fetch_with_retry
except ModuleNotFoundError:
    from http_utils import fetch_with_retry

try:
    from src.extractors.ine_ipc import fetch_ine_ipc
except ModuleNotFoundError:
    from ine_ipc import fetch_ine_ipc

# ── Rutas ─────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
METADATA_PATH = os.path.join(STAGING_DIR, "indicadores.metadata.json")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "indicadores.csv")
PUBLISHED_INDICATORS_PATH = os.path.join(NORMALIZED_DIR, "indicadores.parquet")

# ── Configuración ─────────────────────────────────────────────────────────────
MINDICADOR_BASE = "https://mindicador.cl/api"
HISTORY_START_YEAR = 2010  # Año de inicio del historial
REQUEST_DELAY_SECONDS = 0.3  # Pausa entre llamadas para no saturar la API

# Concurrencia acotada (Plan 010, throttle Plan 089): pool pequeño + submits
# espaciados REQUEST_DELAY_SECONDS. La espera vive ENTRE submits, no dentro del
# worker: N hilos durmiendo en paralelo no espaciaban nada contra la API.
# El plegado en orden de pares preserva diagnósticos y registros idénticos.
MINDICADOR_MAX_WORKERS = 3

# Indicadores a extraer en orden de prioridad
INDICATOR_CODES = ["uf", "dolar", "euro", "utm", "ipc"]

# Indicadores de publicación mensual (vs diaria). Pueden devolver vacío para el
# año en curso si el dato del mes aún no fue publicado — eso es esperado, no un error.
MONTHLY_INDICATORS = {"utm", "ipc"}

# Timeout por llamada HTTP a mindicador.cl. El endpoint de `ipc` es errático:
# respuestas observadas de 13.7s y TimeoutError a los 40s, contra ~1.2s del resto
# de las series (diagnóstico del issue #43, 2026-07-29). Un timeout de 15s estaba
# por debajo de esa latencia y confundía "la fuente no respondió" con "serie
# vacía". 30s da margen a las respuestas lentas sin dejar la puerta abierta a
# cuelgues indefinidos; la latencia se registra en el log para que el diagnóstico
# futuro distinga ambos casos.
MINDICADOR_TIMEOUT_SECONDS = 30

# Antigüedad máxima tolerada del ÚLTIMO dato de una serie entregada por
# `published_backfill` antes de que el gate de publicación la rechace (ADR-016).
# El umbral depende de la cadencia: 40 días de atraso en el dólar son una
# emergencia y en el IPC son normales.
#   - mensual: 70 días ≈ dos publicaciones perdidas (el INE publica el IPC
#     alrededor del día 8 del mes siguiente, así que ~40 días es lo normal).
#   - diaria: 10 días, holgura para feriados largos y ventanas de reintento.
MAX_BACKFILL_AGE_DAYS_MONTHLY = 70
MAX_BACKFILL_AGE_DAYS_DAILY = 10


# El cálculo de la EDAD vive en src/builders/metadata.py::build_indicator_ages()
# (se computa en cada build, sobre el DataFrame real). Aquí vive solo la cadencia
# y su umbral: una sola representación de cada cosa, sin copias que diverjan.
def max_backfill_age_days(codigo: str) -> int:
    """Umbral de antigüedad aplicable a una serie, según su cadencia."""
    return (
        MAX_BACKFILL_AGE_DAYS_MONTHLY
        if codigo in MONTHLY_INDICATORS
        else MAX_BACKFILL_AGE_DAYS_DAILY
    )


# Política de reutilización: los datos provienen del BCCh/INE (libre reproducción
# con citación). mindicador.cl es el agregador/punto de acceso, no la fuente original.
REUSE_POLICY = {
    "status": "open-attribution",
    "license": "Reproducción libre con citación (BCCh / INE)",
    "license_url": "https://www.bcentral.cl/web/banco-central/terminos-y-condiciones",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Datos del Banco Central de Chile (BCCh) e INE. "
        "El BCCh permite libre reproducción con citación de la fuente. "
        "Acceso consolidado vía mindicador.cl (API pública de la comunidad)."
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def ensure_directories() -> None:
    ensure_staging_directories()


def write_metadata(metadata: dict) -> None:
    write_staging_metadata(METADATA_PATH, metadata)


def save_raw_snapshot(payload: dict, codigo: str, year: int) -> None:
    """Persiste la respuesta cruda de la API para trazabilidad y auditoría."""
    timestamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"mindicador_{codigo}_{year}_{timestamp}.json"
    path = os.path.join(RAW_DIR, filename)
    write_raw_snapshot_atomic(path, payload)


def parse_indicator_payload(payload: dict, codigo: str) -> list:
    records = []
    for item in payload.get("serie", []):
        raw_date = item.get("fecha", "")[:10]  # YYYY-MM-DD
        valor = item.get("valor")
        if raw_date and valor is not None:
            records.append(
                {
                    "fecha": raw_date,
                    "codigo_indicador": codigo,
                    "valor": float(valor),
                }
            )
    return records


def load_latest_raw_snapshot(codigo: str, year: int) -> list:
    pattern = f"mindicador_{codigo}_{year}_*.json"
    candidates = sorted(Path(RAW_DIR).glob(pattern))
    if not candidates:
        return []
    latest_snapshot = candidates[-1]
    with latest_snapshot.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return parse_indicator_payload(payload, codigo)


# ── Fetch ─────────────────────────────────────────────────────────────────────


def fetch_indicator_year(codigo: str, year: int) -> list:
    """
    Descarga todos los valores de un indicador para un año calendario.

    La API de mindicador.cl entrega datos diarios para UF, dólar y euro,
    y datos mensuales para UTM e IPC.

    Retorna una lista de dicts con claves: fecha, codigo_indicador, valor.
    """
    url = f"{MINDICADOR_BASE}/{codigo}/{year}"
    started = time.monotonic()
    with fetch_with_retry(url, timeout=MINDICADOR_TIMEOUT_SECONDS) as response:
        response.raise_for_status()
        payload = response.json()
    elapsed = time.monotonic() - started
    print(f"  {codigo}/{year}: {len(payload.get('serie', []))} puntos en {elapsed:.1f}s")
    save_raw_snapshot(payload, codigo, year)
    return parse_indicator_payload(payload, codigo)


def load_existing_staging():
    """
    Lee el CSV de staging existente para la estrategia incremental.
    Retorna `(DataFrame, año_a_refrescar, published_backfills)` o
    `(None, None, [])` si no existe o no puede leerse.
    """
    try:
        if os.path.exists(STAGING_CSV_PATH):
            df = pl.read_csv(
                STAGING_CSV_PATH,
                schema_overrides={"fecha": pl.String},
            ).with_columns(pl.col("fecha").str.to_date("%Y-%m-%d"))
        elif os.path.exists(PUBLISHED_INDICATORS_PATH):
            df = pl.read_parquet(PUBLISHED_INDICATORS_PATH)
        else:
            return None, None, []
        missing_codes = sorted(
            set(INDICATOR_CODES) - set(df["codigo_indicador"].unique().to_list())
        )
        published_backfills = []
        if missing_codes and os.path.exists(PUBLISHED_INDICATORS_PATH):
            published_df = pl.read_parquet(PUBLISHED_INDICATORS_PATH).filter(
                pl.col("codigo_indicador").is_in(missing_codes)
            )
            if published_df.height > 0:
                df = (
                    pl.concat([df, published_df], how="vertical")
                    .unique(subset=["fecha", "codigo_indicador"], keep="last")
                    .sort(["fecha", "codigo_indicador"])
                )
                published_backfills = sorted(published_df["codigo_indicador"].unique().to_list())
        return df, datetime.datetime.now(UTC).date().year, published_backfills
    except Exception as e:
        print(f"Advertencia: no se pudo leer el staging existente: {e}. Se hará fetch completo.")
        return None, None, []


def fetch_all_history():
    """
    Descarga el historial completo o incremental de indicadores.

    - Si no existe staging: descarga desde HISTORY_START_YEAR hasta hoy.
    - Si existe staging  : re-fetcha solo el año en curso para incluir valores recientes.

    Retorna `(DataFrame, diagnostics)` ordenado y deduplicado, o `(None, diagnostics)`
    si no fue posible construir un dataset usable.
    """
    existing_df, _, published_backfills = load_existing_staging()
    current_year = datetime.datetime.now(UTC).date().year
    diagnostics = {
        "fetch_failures": [],
        "raw_recoveries": [],
        "preserved_existing_pairs": [],
        "empty_live_pairs": [],
        "published_backfills": published_backfills,
        "ine_override_pairs": [],
    }

    if existing_df is not None:
        years_to_fetch = [current_year]
        print(f"Staging encontrado — actualizando solo el año {current_year} (incremental).")
    else:
        years_to_fetch = list(range(HISTORY_START_YEAR, current_year + 1))
        print(f"Sin staging previo — descargando historial completo desde {HISTORY_START_YEAR}.")

    total_calls = len(INDICATOR_CODES) * len(years_to_fetch)
    new_records = []
    refreshed_pairs = set()

    # Pares en el mismo orden del loop serial anidado (codigo × año).
    pairs = [(codigo, year) for codigo in INDICATOR_CODES for year in years_to_fetch]

    def _fetch_pair(pair: tuple[str, int]) -> dict:
        """Fetch + recuperación de UN par (hilo). Sin diagnósticos aquí.

        Retorna el resultado crudo; el plegado en orden (abajo) replica la
        contabilidad del serial para diagnósticos byte-idénticos.
        """
        codigo, year = pair
        outcome = {
            "codigo": codigo,
            "year": year,
            "records": [],
            "error": None,
            "raw_records": [],
            "ine_reading": None,
            "ine_attempted": False,
        }
        try:
            outcome["records"] = fetch_indicator_year(codigo, year)
        except Exception as e:
            outcome["error"] = e
            # Recuperación desde snapshot raw local (como el serial). Si esto
            # levanta, propaga igual que el serial (aborta el fetch).
            outcome["raw_records"] = load_latest_raw_snapshot(codigo, year)

        # Override de último recurso para `ipc` en el año en curso (mismas
        # condiciones que el serial: sin registros y par no refrescado; como
        # los pares son únicos, equivale al chequeo local de abajo).
        if (
            codigo == "ipc"
            and year == current_year
            and not outcome["records"]
            and not outcome["raw_records"]
        ):
            outcome["ine_attempted"] = True
            outcome["ine_reading"] = fetch_ine_ipc()

        return outcome

    with concurrent.futures.ThreadPoolExecutor(max_workers=MINDICADOR_MAX_WORKERS) as pool:
        # Submits espaciados (Plan 089): el orden de `futures` replica el de
        # `pairs`, así que el plegado replica el serial; el sleep entre
        # submits sí impone la cortesía contra la API.
        futures = []
        for next_pair in pairs:
            futures.append(pool.submit(_fetch_pair, next_pair))
            time.sleep(REQUEST_DELAY_SECONDS)
        outcomes = [future.result() for future in futures]

    for call_n, outcome in enumerate(outcomes, 1):
        codigo = outcome["codigo"]
        year = outcome["year"]
        pair = f"{codigo}/{year}"
        records = outcome["records"]
        print(f"  [{call_n}/{total_calls}] Descargando {codigo}/{year}…")
        if outcome["error"] is None:
            if records:
                new_records.extend(records)
                refreshed_pairs.add((codigo, year))
            else:
                # Serie vacía para un indicador mensual en el año en curso:
                # el dato aún no fue publicado ese mes — comportamiento esperado.
                expected_monthly_gap = codigo in MONTHLY_INDICATORS and year == current_year
                if not expected_monthly_gap:
                    diagnostics["empty_live_pairs"].append(pair)
                if existing_df is not None:
                    has_published_history = (
                        existing_df.filter(pl.col("codigo_indicador") == codigo).height > 0
                    )
                    if has_published_history:
                        diagnostics["published_backfills"].append(codigo)
        else:
            e = outcome["error"]
            diagnostics["fetch_failures"].append(f"{codigo}/{year}: {e}")
            print(f"  Advertencia: no se pudo obtener {codigo}/{year}: {e}")
            raw_records = outcome["raw_records"]
            if raw_records:
                print(f"  Recuperando {codigo}/{year} desde snapshot raw local…")
                new_records.extend(raw_records)
                refreshed_pairs.add((codigo, year))
                diagnostics["raw_recoveries"].append(f"{codigo}/{year}")
            elif existing_df is not None:
                diagnostics["preserved_existing_pairs"].append(f"{codigo}/{year}")

        # Override de último recurso para `ipc` en el año en curso: si
        # mindicador.cl no lo entrega (serie muerta upstream desde
        # 2025-12, issue #43), la fuente autoritativa INE publica la
        # variación mensual en su página pública. Solo aplica cuando el
        # dato no llegó por la vía normal, y solo para el año en curso
        # (el INE publica el último mes, no historial).
        if outcome["ine_attempted"]:
            ine_reading = outcome["ine_reading"]
            if ine_reading is not None:
                print(
                    f"  IPC desde INE (fuente autoritativa): "
                    f"{ine_reading.date_iso} = {ine_reading.value}%"
                )
                new_records.append(
                    {
                        "fecha": ine_reading.date_iso,
                        "codigo_indicador": "ipc",
                        "valor": ine_reading.value,
                    }
                )
                # NO marcar (ipc, year) en refreshed_pairs: eso haria que el
                # merge eliminara TODO el slice ipc del año en curso del
                # staging existente y lo reemplazara solo por el registro
                # INE (un mes), truncando los meses que mindicador si habia
                # entregado. El concat + unique(keep="last") final fusiona
                # el registro INE con el historial existente por fecha.
                diagnostics.setdefault("ine_override_pairs", []).append(f"{codigo}/{year}")
            else:
                print("  Advertencia: no se pudo obtener IPC desde INE.")

    if not new_records and existing_df is not None:
        published_codes = sorted(existing_df["codigo_indicador"].unique().to_list())
        diagnostics["published_backfills"] = sorted(
            set(diagnostics["published_backfills"]) | set(published_codes)
        )
        return existing_df.sort(["fecha", "codigo_indicador"]), diagnostics

    if not new_records:
        print("Error: no se obtuvieron datos de mindicador.cl.")
        return None, diagnostics

    diagnostics["published_backfills"] = sorted(set(diagnostics["published_backfills"]))

    new_df = pl.DataFrame(new_records).with_columns(
        pl.col("fecha").str.to_date("%Y-%m-%d"),
        pl.col("codigo_indicador").cast(pl.String),
        pl.col("valor").cast(pl.Float64),
    )

    if existing_df is not None:
        # Reemplazar solo los pares codigo/año que fueron refrescados o recuperados.
        if refreshed_pairs:
            refreshed_codes = sorted({codigo for codigo, _ in refreshed_pairs})
            refreshed_years = sorted({year for _, year in refreshed_pairs})
            existing_trimmed = existing_df.filter(
                ~(
                    pl.col("codigo_indicador").is_in(refreshed_codes)
                    & pl.col("fecha").dt.year().is_in(refreshed_years)
                )
            )
        else:
            existing_trimmed = existing_df
        combined_df = pl.concat([existing_trimmed, new_df], how="vertical")
    else:
        combined_df = new_df

    return (
        combined_df.unique(subset=["fecha", "codigo_indicador"], keep="last").sort(
            ["fecha", "codigo_indicador"]
        ),
        diagnostics,
    )


# ── Fallback ──────────────────────────────────────────────────────────────────


def generate_fallback_indicators() -> pl.DataFrame:
    """
    Dataset sintético usado cuando la API en vivo no está disponible.
    Cubre los últimos 7 días con valores aproximados del año 2026.
    Marcado explícitamente como fallback en los metadatos.
    """
    print("Generando dataset de indicadores de fallback (simulación offline)…")
    today = datetime.datetime.now(UTC).date()
    base_values = {
        "uf": 40500.00,
        "dolar": 900.00,
        "euro": 1040.00,
        "utm": 70000.00,
        "ipc": 0.2,
    }
    records = []
    for i in range(7):
        fecha = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for codigo, base in base_values.items():
            valor = round(base - i * 5.0, 2) if codigo in ("uf", "dolar", "euro") else base
            records.append({"fecha": fecha, "codigo_indicador": codigo, "valor": valor})

    return (
        pl.DataFrame(records)
        .with_columns(pl.col("fecha").str.to_date("%Y-%m-%d"))
        .sort(["fecha", "codigo_indicador"])
    )


# ── Main ──────────────────────────────────────────────────────────────────────


def process_indicators() -> str:
    ensure_directories()
    source_mode = "live"
    notes: list = []
    source_detail = "public_api"

    df, diagnostics = fetch_all_history()

    if df is None:
        df = generate_fallback_indicators()
        source_mode = "fallback"
        source_detail = "generated_fallback"
        notes.append("fallback_due_to_live_fetch_failure")
        diagnostics = diagnostics or {
            "fetch_failures": [],
            "raw_recoveries": [],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
        }

    if (
        source_mode == "live"
        and diagnostics.get("raw_recoveries")
        and diagnostics.get("preserved_existing_pairs")
    ):
        source_detail = "public_api_with_raw_recovery_partial"
    elif source_mode == "live" and diagnostics.get("raw_recoveries"):
        source_detail = "public_api_with_raw_recovery"
    if source_mode == "live" and diagnostics.get("raw_recoveries"):
        notes.append("raw_recovery_used_for_pairs: " + ", ".join(diagnostics["raw_recoveries"]))
    if (
        source_mode == "live"
        and diagnostics.get("preserved_existing_pairs")
        and not diagnostics.get("raw_recoveries")
    ):
        source_detail = "public_api_partial"
    if source_mode == "live" and diagnostics.get("preserved_existing_pairs"):
        notes.append(
            "preserved_existing_pairs_due_to_fetch_failure: "
            + ", ".join(diagnostics["preserved_existing_pairs"])
        )
    if source_mode == "live" and diagnostics.get("empty_live_pairs"):
        notes.append("empty_live_pairs: " + ", ".join(diagnostics["empty_live_pairs"]))
    if source_mode == "live" and diagnostics.get("published_backfills"):
        source_detail = "public_api_with_published_backfill"
        notes.append(
            "published_backfills_used_for_codes: " + ", ".join(diagnostics["published_backfills"])
        )
    if source_mode == "live" and diagnostics.get("ine_override_pairs"):
        notes.append("ine_override_used_for_pairs: " + ", ".join(diagnostics["ine_override_pairs"]))

    indicator_codes = sorted(df["codigo_indicador"].unique().to_list())
    indicator_delivery = {code: "live" for code in indicator_codes}
    for pair in diagnostics.get("raw_recoveries", []):
        indicator_delivery[pair.split("/", 1)[0]] = "raw_recovery"
    for pair in diagnostics.get("preserved_existing_pairs", []):
        indicator_delivery[pair.split("/", 1)[0]] = "preserved_existing"
    for code in diagnostics.get("published_backfills", []):
        indicator_delivery[code] = "published_backfill"
    # El override (último recurso, fuente autoritativa) gana sobre el backfill:
    # el bucle anterior etiqueta la serie como "reutilización del artefacto
    # publicado" (falso cuando el valor viene del INE). El delivery debe ser
    # visible para que el gate de publicación evalúe el dato real. Plan 069.
    for pair in diagnostics.get("ine_override_pairs", []):
        indicator_delivery[pair.split("/", 1)[0]] = "ine_override"

    df.write_csv(STAGING_CSV_PATH)

    metadata = {
        "dataset": "indicadores",
        "source_name": "Banco Central de Chile (via mindicador.cl)",
        "source_url": MINDICADOR_BASE,
        "source_origin_url": "https://www.bcentral.cl/web/banco-central/estadisticas",
        "source_mode": source_mode,
        "source_detail": source_detail,
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "indicator_codes": indicator_codes,
        "indicator_delivery": indicator_delivery,
        "history_start_year": HISTORY_START_YEAR,
        "notes": notes,
        "fetch_failures": diagnostics.get("fetch_failures", []),
        "raw_recoveries": diagnostics.get("raw_recoveries", []),
        "preserved_existing_pairs": diagnostics.get("preserved_existing_pairs", []),
        "empty_live_pairs": diagnostics.get("empty_live_pairs", []),
        "published_backfills": diagnostics.get("published_backfills", []),
        "ine_override_pairs": diagnostics.get("ine_override_pairs", []),
        "reuse_policy": REUSE_POLICY,
    }
    write_metadata(metadata)

    print(f"Indicadores guardados en: {STAGING_CSV_PATH} ({df.height} registros, {source_mode})")
    return STAGING_CSV_PATH


class BCentralExtractor(BaseExtractor):
    """Adaptador orientado a objetos para el extractor de indicadores existente."""

    @property
    def dataset_name(self) -> str:
        return "indicadores"

    def fetch(self, **kwargs):
        return fetch_all_history()

    def normalize(self, raw_data):
        df, _diagnostics = raw_data
        return df if df is not None else generate_fallback_indicators()

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_indicadores

        return validate_indicadores(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_directories()
        output_path = Path(STAGING_CSV_PATH)
        df.write_csv(output_path)
        write_metadata(
            {
                **metadata,
                "dataset": self.dataset_name,
                "record_count": df.height,
                "fields": df.columns,
                "reuse_policy": REUSE_POLICY,
            }
        )
        return output_path


if __name__ == "__main__":
    process_indicators()
