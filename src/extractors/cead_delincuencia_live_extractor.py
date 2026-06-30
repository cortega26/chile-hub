"""Extractor de delincuencia comunal desde CEAD vía POST + parseo HTML.

Estrategia (Ola B2.1 del Plan 022):
1. POST al endpoint PHP de CEAD con filtros (medida, año, meses, comuna, familias)
2. Parsear la tabla HTML de respuesta
3. Extraer casos por familia de delito × mes × comuna
4. Guardar snapshot crudo en data/raw/
5. Validar contra DPA y guardar en staging

Guardarraíles:
- Carril CANDIDATE — NO entra al bundle público (legal review: derive-only)
- review_by: 2026-09-21, stalled_after_days: 90
- Workflow mensual aislado, desacoplado del build diario
- Fallback a último snapshot si el scraping falla
- Honestidad de cadencia: source_mode = "monthly"
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
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

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
STAGING_CSV_PATH = STAGING_DIR / "delincuencia_comunal.csv"
METADATA_PATH = STAGING_DIR / "delincuencia_comunal.metadata.json"

# ── Endpoint CEAD ────────────────────────────────────────────────────────
CEAD_STATS_URL = (
    "https://cead.minsegpublica.gob.cl/wp-content/themes/"
    "gobcl-wp-master/data/get_estadisticas_delictuales.php"
)
# Alternativa histórica (por si el dominio principal cambia)
CEAD_STATS_URL_ALT = (
    "https://cead.spd.gov.cl/wp-content/themes/"
    "gobcl-wp-master/data/get_estadisticas_delictuales.php"
)

# ── Familias de delito (8 familias + "Otros") ─────────────────────────
# Mapeo familia_id → nombre canónico
FAMILIAS_DELITO: dict[str, str] = {
    "1": "delitos_contra_la_vida",
    "2": "robos_violentos",
    "3": "violencia_intrafamiliar",
    "4": "delitos_asociados_a_drogas",
    "5": "delitos_asociados_a_armas",
    "6": "delitos_contra_propiedad_no_violentos",
    "7": "incivilidades",
    "99": "otros_delitos_o_faltas",
}

# Nombres URL-encoded para el POST
FAMILIAS_NOMBRES: dict[str, str] = {
    "1": "Delitos+contra+la+vida+o+integridad+de+las+personas",
    "2": "Robos+violentos",
    "3": "Violencia+intrafamiliar",
    "4": "Delitos+asociados+a+drogas",
    "5": "Delitos+asociados+a+armas",
    "6": "Delitos+contra+la+propiedad+no+violentos",
    "7": "Incivilidades",
    "99": "Otros+delitos+o+faltas",
}

# ── Meses ────────────────────────────────────────────────────────────────
MESES = [
    (1, "Enero"),
    (2, "Febrero"),
    (3, "Marzo"),
    (4, "Abril"),
    (5, "Mayo"),
    (6, "Junio"),
    (7, "Julio"),
    (8, "Agosto"),
    (9, "Septiembre"),
    (10, "Octubre"),
    (11, "Noviembre"),
    (12, "Diciembre"),
]

REUSE_POLICY = {
    "status": "public-api-review-terms",
    "license": "Sin licencia explícita en el portal CEAD. Datos públicos agregados "
    "de la Subsecretaría de Prevención del Delito (Ministerio del Interior).",
    "license_url": "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/",
    "attribution_required": True,
    "redistribution_ok": False,
    "summary": (
        "Casos policiales de Delitos de Mayor Connotación Social (DMCS) y otras "
        "categorías por comuna, desde el Centro de Estudios y Análisis del Delito "
        "(CEAD). Carril CANDIDATE — NO redistribuible en el bundle público. "
        "Revisión legal: docs/legal/fase-3-legal-review.md. "
        "review_by: 2026-09-21."
    ),
}


def _load_comuna_codes() -> list[tuple[str, str]]:
    """Carga los códigos de comuna desde el DPA (comunas.parquet).

    Returns:
        Lista de tuplas (codigo_comuna, nombre_comuna).
    """
    comunas_path = DATA_DIR / "normalized" / "comunas.parquet"
    if not comunas_path.exists():
        # Fallback: usar el CSV de staging si no hay parquet
        comunas_path = STAGING_DIR / "comunas.csv"
    if not comunas_path.exists():
        raise FileNotFoundError(
            "No se encontró el archivo de comunas (comunas.parquet o comunas.csv). "
            "Ejecuta el build primero para generar el DPA."
        )

    if comunas_path.suffix == ".parquet":
        df = pl.read_parquet(comunas_path)
    else:
        df = pl.read_csv(comunas_path)

    # Seleccionar columnas de código y nombre
    codigo_col = "codigo_comuna" if "codigo_comuna" in df.columns else "codigo_comuna_clean"
    nombre_col = "nombre_comuna" if "nombre_comuna" in df.columns else "nombre_comuna_clean"

    return [
        (row[codigo_col], row[nombre_col])
        for row in df.select([codigo_col, nombre_col]).iter_rows(named=True)
    ]


def _build_post_body(
    year: int,
    codigo_comuna: str,
    medida: int = 1,
) -> str:
    """Construye el body POST para una consulta al endpoint CEAD.

    Args:
        year: Año a consultar.
        codigo_comuna: Código CUT de 5 dígitos.
        medida: 1 = frecuencia (casos), 2 = tasa por 100k hab.

    Returns:
        Body URL-encoded listo para POST.
    """
    params: list[str] = []

    # Medida y tipo de valor
    params.append(f"medida={medida}")
    params.append("tipoVal=1%2C2")  # Casos policiales + Denuncias

    # Año
    params.append(f"anio%5B%5D={year}")

    # Trimestres
    for t in (4, 3, 2, 1):
        params.append(f"trimestre%5B%5D={t}")

    # Meses
    for mes_num, _ in MESES:
        params.append(f"mes%5B%5D={mes_num}")

    # Nombres de meses
    for _, mes_nombre in MESES:
        params.append(f"mes_nombres%5B%5D={mes_nombre}")

    # Comuna
    params.append(f"comuna%5B%5D={codigo_comuna}")

    # Familias de delito (todas)
    for fid in FAMILIAS_DELITO:
        params.append(f"familia%5B%5D={fid}")
    for fname in FAMILIAS_NOMBRES.values():
        params.append(f"familia_nombres%5B%5D={fname}")

    # Parámetros fijos
    params.append("seleccion=2")
    params.append("descarga=false")

    return "&".join(params)


def _fetch_comuna_data(
    year: int,
    codigo_comuna: str,
    nombre_comuna: str,
    session: Any,
) -> tuple[list[dict[str, Any]], float]:
    """Obtiene y parsea los datos de una comuna desde CEAD.

    Args:
        year: Año a consultar.
        codigo_comuna: Código CUT de 5 dígitos.
        nombre_comuna: Nombre de la comuna (para el registro).
        session: requests.Session configurada.

    Returns:
        Tupla con (lista de dicts con los datos, tiempo_de_respuesta_segundos).
    """
    import requests as req

    body = _build_post_body(year, codigo_comuna)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Connection": "close",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        ),
        "Referer": "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/",
    }

    t0 = time.time()
    response = session.post(
        CEAD_STATS_URL,
        data=body.encode("utf-8"),
        headers=headers,
        timeout=120,
    )
    elapsed = time.time() - t0

    if response.status_code != 200:
        raise req.HTTPError(
            f"CEAD respondió HTTP {response.status_code} para comuna {codigo_comuna}"
        )

    html = response.text

    # Detectar respuesta vacía o error
    if "<tr" not in html or "DELITOS O FALTAS" not in html:
        raise ValueError(
            f"CEAD retornó HTML sin tabla para comuna {codigo_comuna}. "
            f"Primeros 200 chars: {html[:200]}"
        )

    # Parsear la tabla HTML
    rows = _parse_html_table(html, year, codigo_comuna, nombre_comuna)
    return rows, elapsed


def _parse_html_table(
    html: str,
    year: int,
    codigo_comuna: str,
    nombre_comuna: str,
) -> list[dict[str, Any]]:
    """Parsea la tabla HTML de respuesta de CEAD.

    Estructura esperada:
      Thead: 3 filas de encabezado (año, trimestres, meses 1-12)
      Tbody: 8 filas de datos (una por familia de delito)
        Col 0: nombre de la familia
        Cols 1-12: valores mensuales

    Args:
        html: HTML crudo de la respuesta.
        year: Año consultado.
        codigo_comuna: Código CUT.
        nombre_comuna: Nombre de la comuna.

    Returns:
        Lista de dicts con schema delincuencia_comunal.
    """
    # Extraer todas las filas de la tabla
    all_rows = re.findall(r"<tr[^>]*?>(.*?)</tr>", html, re.DOTALL)

    if len(all_rows) < 4:
        return []

    # Las filas de datos están en el tbody (índices 3+)
    data_rows_html = all_rows[3:]  # Las primeras 3 son headers

    rows_out: list[dict[str, Any]] = []
    for row_html in data_rows_html:
        # Extraer celdas TD
        cells = re.findall(r"<td[^>]*?>(.*?)</td>", row_html, re.DOTALL)
        if len(cells) < 13:
            continue  # Fila incompleta (debe tener nombre + 12 meses)

        # Limpiar nombre de la familia (celda 0)
        familia_nombre = re.sub(r"<[^>]+>", "", cells[0]).strip()
        if not familia_nombre:
            continue

        # Mapear nombre a ID canónico
        familia_id = None
        for fid, fname in FAMILIAS_NOMBRES.items():
            # Decodificar URL-encoding para comparar
            fname_decoded = fname.replace("+", " ")
            if familia_nombre.lower() == fname_decoded.lower():
                familia_id = fid
                break
        if familia_id is None:
            continue  # Familia no reconocida

        familia_key = FAMILIAS_DELITO.get(familia_id, familia_nombre)

        # Extraer valores mensuales (celdas 1-12)
        for mes_idx in range(12):
            if mes_idx + 1 >= len(cells):
                break
            raw_value = re.sub(r"<[^>]+>", "", cells[mes_idx + 1]).strip()
            # El formato puede incluir separadores de miles ("1.044") o ser " - "
            raw_value = raw_value.replace(".", "")  # Quitar separadores de miles
            raw_value = raw_value.replace(",", ".")  # Convertir coma decimal a punto
            try:
                casos = int(raw_value) if raw_value and raw_value != "-" else 0
            except (ValueError, TypeError):
                casos = 0

            mes_num, mes_nombre = MESES[mes_idx]

            rows_out.append(
                {
                    "anio": year,
                    "mes": mes_num,
                    "nombre_mes": mes_nombre,
                    "codigo_comuna": codigo_comuna,
                    "nombre_comuna": nombre_comuna,
                    "familia_delito": familia_key,
                    "nombre_familia": familia_nombre,
                    "casos": casos,
                    "fuente": "CEAD — Subsecretaría de Prevención del Delito",
                    "url_fuente": "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/",
                }
            )

    return rows_out


def fetch_data(year: int | None = None) -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Obtiene datos de delincuencia desde CEAD para todas las comunas.

    Args:
        year: Año a consultar (default: año anterior al actual).

    Returns:
        (rows, source_mode, source_url, notes)
    """
    import requests as req

    ensure_staging_directories()
    notes: list[str] = []
    source_url = CEAD_STATS_URL

    if year is None:
        year = datetime.datetime.now(UTC).year - 1  # Default: año anterior

    timestamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    # Cargar códigos de comuna desde el DPA
    try:
        comunas = _load_comuna_codes()
        notes.append(f"DPA: {len(comunas)} comunas cargadas")
    except FileNotFoundError as e:
        notes.append(f"DPA no disponible: {e}")
        return [], "fallback", source_url, notes

    all_rows: list[dict[str, Any]] = []
    session = req.Session()
    success_count = 0
    fail_count = 0

    notes.append(f"live: iniciando scraping CEAD para {year} ({len(comunas)} comunas)")

    for i, (codigo_comuna, nombre_comuna) in enumerate(comunas):
        try:
            rows, elapsed = _fetch_comuna_data(year, codigo_comuna, nombre_comuna, session)
            all_rows.extend(rows)
            success_count += 1

            # Rate limiting: esperar al menos 2× el tiempo de respuesta
            delay = max(elapsed * 2, 0.5)
            time.sleep(delay)

        except Exception as e:
            fail_count += 1
            notes.append(f"fallo comuna {codigo_comuna} ({nombre_comuna}): {e}")

            # Continuar con la siguiente comuna (no abortar todo el scrape)
            # Esperar un poco más tras un fallo
            time.sleep(1.0)

        # Progreso cada 50 comunas
        if (i + 1) % 50 == 0:
            notes.append(
                f"progreso: {i + 1}/{len(comunas)} comunas, "
                f"{success_count} ok, {fail_count} fallos, "
                f"{len(all_rows)} filas acumuladas"
            )

    notes.append(
        f"live: {success_count}/{len(comunas)} comunas exitosas, "
        f"{fail_count} fallos, {len(all_rows)} filas totales"
    )

    # Determinar source_mode según cobertura
    if success_count >= 300:  # ≥87% de comunas
        source_mode = "monthly"
    elif success_count >= 100:  # ≥29% de comunas
        source_mode = "fallback"
        notes.append("fallback: cobertura parcial (<87% comunas)")
    else:
        source_mode = "fallback"
        notes.append("fallback: cobertura insuficiente (<29% comunas)")

    # Si no se obtuvo nada, fallback total
    if not all_rows:
        notes.append("fallback: sin datos — se mantiene el último snapshot bueno")
        source_mode = "fallback"

    # Guardar snapshot crudo (HTML de la última respuesta como muestra)
    if success_count > 0:
        raw_path = RAW_DIR / f"cead_delincuencia_{year}_{timestamp}.json"
        raw_path.write_text(
            json.dumps(
                {
                    "year": year,
                    "fetched_at_utc": timestamp,
                    "comunas_ok": success_count,
                    "comunas_fail": fail_count,
                    "total_rows": len(all_rows),
                    "sample_first_10": all_rows[:10],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        notes.append(f"snapshot crudo: {raw_path.name}")

    return all_rows, source_mode, source_url, notes


def normalize_rows(rows: list[dict[str, Any]]) -> pl.DataFrame:
    """Normaliza filas al esquema canónico de delincuencia_comunal."""
    if not rows:
        return pl.DataFrame(
            schema={
                "anio": pl.Int32,
                "mes": pl.Int32,
                "nombre_mes": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "familia_delito": pl.String,
                "nombre_familia": pl.String,
                "casos": pl.Int64,
                "fuente": pl.String,
                "url_fuente": pl.String,
            }
        )

    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("anio").cast(pl.Int32),
            pl.col("mes").cast(pl.Int32),
            pl.col("nombre_mes").cast(pl.String),
            pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
            pl.col("nombre_comuna").cast(pl.String),
            pl.col("familia_delito").cast(pl.String),
            pl.col("nombre_familia").cast(pl.String),
            pl.col("casos").cast(pl.Int64),
            pl.col("fuente").cast(pl.String),
            pl.col("url_fuente").cast(pl.String),
        )
        .sort(["anio", "mes", "codigo_comuna", "familia_delito"])
    )


def build_metadata(
    df: pl.DataFrame,
    source_mode: str,
    source_url: str,
    notes: list[str],
) -> dict[str, Any]:
    """Construye metadata.json para staging."""
    return build_standard_metadata(
        dataset="delincuencia_comunal",
        source_name="CEAD — Subsecretaría de Prevención del Delito",
        source_url=source_url,
        source_mode=source_mode,
        source_detail=(
            "live_scraping_cead_php_endpoint"
            if source_mode == "monthly"
            else "scraping_failed_fallback_to_last_snapshot"
        ),
        df=df,
        notes=notes
        + [
            "Carril CANDIDATE — NO incluido en el bundle público.",
            "review_by: 2026-09-21. stalled_after_days: 90.",
            "Datos: casos policiales (Carabineros + PDI) por familia de delito.",
        ],
        reuse_policy=REUSE_POLICY,
    )


def process_cead_delincuencia(year: int | None = None) -> str:
    """Ejecuta el ciclo completo de extracción para delincuencia_comunal."""
    raw_rows, source_mode, source_url, notes = fetch_data(year)

    if source_mode == "fallback" and not raw_rows:
        print(
            "⚠️  CEAD: scraping falló sin datos. Se mantiene el último snapshot bueno. "
            "El build diario no se ve afectado."
        )
        return ""

    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)

    # Validación ligera (el dataset es candidate, no tiene contrato fail-loud)
    validation = CeaddelincuenciaLiveExtractor().validate(df, metadata)
    if validation["status"] == "error":
        print(
            f"⚠️  Validación CEAD fallida (no bloqueante — carril candidate): {validation['errors']}"
        )
        # No abortar — candidate no es fail-loud

    CeaddelincuenciaLiveExtractor().write_staging(df, metadata)
    print(
        f"Delincuencia comunal (CEAD) guardada en: {STAGING_CSV_PATH} "
        f"({df.height} registros, {df['codigo_comuna'].n_unique()} comunas, "
        f"source_mode={source_mode})"
    )
    return str(STAGING_CSV_PATH)


class CeaddelincuenciaLiveExtractor(BaseExtractor):
    """Extractor de delincuencia comunal desde el portal CEAD.

    Usa POST directo al endpoint PHP de CEAD (sin JavaScript/Playwright)
    y parsea la tabla HTML de respuesta. Itera por comuna con rate limiting.

    Carril: CANDIDATE — NO incluido en el bundle público.
    """

    @property
    def dataset_name(self) -> str:
        return "delincuencia_comunal"

    def fetch(self, **kwargs: Any) -> tuple:
        year = kwargs.get("year")
        return fetch_data(year)

    def normalize(self, raw_data: tuple) -> pl.DataFrame:
        return normalize_rows(raw_data[0])

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        """Validación ligera para dataset candidate.

        Los datasets en carril candidate no tienen contrato fail-loud:
        la validación es informativa, no bloqueante.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if df.height == 0:
            warnings.append("dataset vacío — scraping posiblemente fallido")
        else:
            comunas_presentes = df["codigo_comuna"].n_unique()
            if comunas_presentes < 300:
                warnings.append(
                    f"solo {comunas_presentes}/346 comunas presentes — cobertura parcial"
                )

            # Verificar columnas requeridas
            required = {"anio", "mes", "codigo_comuna", "familia_delito", "casos"}
            missing = required - set(df.columns)
            if missing:
                errors.append(f"faltan columnas requeridas: {missing}")

            # Verificar que no haya valores negativos en casos
            if "casos" in df.columns:
                negativos = df.filter(pl.col("casos") < 0).height
                if negativos > 0:
                    errors.append(f"{negativos} filas con casos negativos")

        return {
            "status": "error" if errors else "ok",
            "errors": errors,
            "warnings": warnings,
        }

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extraer delincuencia comunal desde CEAD")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Año a extraer (default: año anterior al actual)",
    )
    args = parser.parse_args()
    process_cead_delincuencia(year=args.year)
