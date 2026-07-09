"""Extractor live de finanzas municipales desde SINIM vía Playwright + XML Spreadsheet.

Estrategia (Fase 3.2 del Plan 022):
1. Playwright → navegar a datos_municipales.php, configurar filtros vía JS directo
2. Extraer PHPSESSID de la sesión PHP
3. Descargar XML Spreadsheet 2003 con requests + cookie de sesión
4. Parsear XML para extraer 6 variables financieras × 345 municipios
5. Multiplicar valores × 1000 (el XML reporta "miles de pesos nominales")
6. Validar contra DPA y guardar en staging

Guardarraíles (§4.2 del plan):
- Legal primero: revisión completada en docs/legal/fase-3-legal-review.md
- Snapshot crudo append-only en data/raw/
- Preferir curl antes que renderizar: descarga con requests, no Playwright
- Workflow mensual aislado (3.3)
- Honestidad de cadencia: source_mode = "mensual/programada" (3.4)
"""

import datetime
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
STAGING_CSV_PATH = STAGING_DIR / "finanzas_municipales.csv"
METADATA_PATH = STAGING_DIR / "finanzas_municipales.metadata.json"

SINIM_DATOS_MUNICIPALES_URL = "https://datos.sinim.gov.cl/datos_municipales.php"
SINIM_EXCEL_PATH = "/datos_municipales/obtener_datos_municipales.php"

# Parámetros del Excel (verificados en exploración Fase 5)
# area[]=1 → ADMINISTRACION Y FINANZAS MUNICIPALES
# subarea[]=T → TODAS LAS SUBÁREAS
# variables[]=T → TODAS LAS VARIABLES (122)
# periodos[]=25 → Año 2024
# regiones[]=T → TODAS LAS REGIONES
# municipios[]=T → TODOS LOS MUNICIPIOS
# corrmon=false → sin corrección monetaria
EXCEL_PARAMS = (
    "area[]=1&subarea[]=T&variables[]=T&periodos[]=25&regiones[]=T&municipios[]=T&corrmon=false"
)

# Mapping de columnas del XML al esquema de finanzas_municipales.
# Índices 0-indexados en la fila de datos (Cell[0]=codigo_comuna, Cell[1]=nombre_comuna).
# Valores en "miles de pesos nominales (M$)" → se multiplican × 1000.
VARIABLE_COLUMN_MAP = {
    "ingresos_totales": 14,  # IADM01 — Ingresos Municipales (Ingreso Total Percibido)
    "gastos_totales": 39,  # IADM11 — Gastos Municipales (Gastos Total Devengado)
    "ingresos_propios_permanentes": 23,  # IADM41 — Ingresos Propios Permanentes (IPP)
    "fondo_comun_municipal": 16,  # IADM40 — Ingresos por Fondo Común Municipal
    "gasto_personal": 65,  # IADM61 — Gastos en Personal Municipal (Subtítulo 21)
    "gasto_inversion": 71,  # IADM22 — Inversión Municipal
}

REUSE_POLICY = {
    "status": "public-api-review-terms",
    "license": "CC BY 2.0 CL. El sitio SINIM declara 'sin fines comerciales'. "
    "Chile-hub es un proyecto no comercial (MIT, sin revenue). "
    "Atribución requerida a SINIM/SUBDERE/Ministerio del Interior.",
    "license_url": "https://datos.sinim.gov.cl/",
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Datos presupuestarios municipales (ingresos, gastos, inversión, personal, "
        "Fondo Común Municipal) desde SINIM/SUBDERE. Uso no comercial, citar fuente. "
        "Revisión legal: docs/legal/fase-3-legal-review.md"
    ),
}


def _setup_sinim_session() -> tuple[str, str]:
    """Configura la sesión SINIM con Playwright y retorna (phpsessid, user_agent).

    Interactúa con los dropdowns de Chosen.js vía JavaScript directo para
    configurar los filtros en cascada (área→subárea→variables, región→municipios).
    """
    from playwright.sync_api import sync_playwright

    phpsessid = None
    user_agent = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navegar a la página de datos municipales
            page.goto(SINIM_DATOS_MUNICIPALES_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)  # Esperar inicialización de Chosen.js

            # === Configurar filtros vía JS directo ===
            # El orden importa: las cascadas son área→subárea→variables y región→municipios

            # 1. Área: ADMINISTRACION Y FINANZAS MUNICIPALES (value=1)
            _set_select_js(page, "dato_area", ["1"])
            page.wait_for_timeout(2000)
            _wait_for_options(page, "dato_subarea", min_options=2)

            # 2. Subárea: TODAS (value=T)
            _set_select_js(page, "dato_subarea", ["T"])
            page.wait_for_timeout(2000)
            _wait_for_options(page, "variables", min_options=2)

            # 3. Variables: TODAS (value=T)
            _set_select_js(page, "variables", ["T"])
            page.wait_for_timeout(2000)

            # 4. Período: 2024 (value=25)
            _set_select_js(page, "periodos", ["25"])
            page.wait_for_timeout(2000)

            # 5. Región: TODAS (value=T)
            _set_select_js(page, "regiones", ["T"])
            page.wait_for_timeout(2000)
            _wait_for_options(page, "municipios", min_options=300)

            # 6. Municipios: TODOS (value=T)
            _set_select_js(page, "municipios", ["T"])
            page.wait_for_timeout(2000)

            # Hacer clic en "Ver" para cargar los datos (activa el enlace de Excel)
            ver_link = page.locator("a[href='#']").filter(has_text="Ver").first
            if ver_link.count() > 0:
                ver_link.click()
                page.wait_for_timeout(5000)

            # Extraer cookies de sesión
            cookies = context.cookies()
            for c in cookies:
                if c["name"] == "PHPSESSID":
                    phpsessid = c["value"]

            # Extraer User-Agent
            user_agent = page.evaluate("() => navigator.userAgent")

        finally:
            browser.close()

    if not phpsessid:
        raise RuntimeError("No se pudo obtener PHPSESSID de la sesión SINIM")

    return phpsessid, user_agent or "Mozilla/5.0"


def _set_select_js(page, select_id: str, values: list[str]) -> None:
    """Selecciona valores en un <select> oculto (Chosen.js) vía JS."""
    page.evaluate(
        """
        (args) => {
            const sel = document.getElementById(args.id);
            if (!sel) return;
            for (let i = 0; i < sel.options.length; i++) {
                sel.options[i].selected = false;
            }
            const valueSet = new Set(args.values);
            for (let i = 0; i < sel.options.length; i++) {
                if (valueSet.has(sel.options[i].value)) {
                    sel.options[i].selected = true;
                }
            }
            sel.dispatchEvent(new Event('change', {bubbles: true}));
            sel.dispatchEvent(new Event('chosen:updated', {bubbles: true}));
            if (typeof $ !== 'undefined' && $(sel).data('chosen')) {
                $(sel).trigger('chosen:updated');
            }
        }
    """,
        {"id": select_id, "values": values},
    )


def _wait_for_options(page, select_id: str, min_options: int = 2, timeout_ms: int = 10000) -> None:
    """Espera a que un <select> tenga al menos min_options opciones (carga AJAX)."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        count = page.evaluate(
            """(id) => {
            const sel = document.getElementById(id);
            return sel ? sel.options.length : 0;
        }""",
            select_id,
        )
        if count >= min_options:
            return
        time.sleep(0.5)
    # Último intento
    count = page.evaluate(
        """(id) => {
        const sel = document.getElementById(id);
        return sel ? sel.options.length : 0;
    }""",
        select_id,
    )
    if count < min_options:
        raise RuntimeError(
            f"Timeout esperando opciones para #{select_id}: {count} opciones (< {min_options})"
        )


def _download_excel_xml(phpsessid: str, user_agent: str, raw_path: Path) -> str:
    """Descarga el Excel XML desde SINIM usando requests con la cookie de sesión."""
    import requests

    full_url = f"https://datos.sinim.gov.cl{SINIM_EXCEL_PATH}?{EXCEL_PARAMS}"

    headers = {
        "User-Agent": user_agent,
        "Referer": SINIM_DATOS_MUNICIPALES_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = requests.get(
        full_url,
        headers=headers,
        cookies={"PHPSESSID": phpsessid},
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(f"SINIM respondió HTTP {response.status_code}: {response.text[:500]}")

    content_type = response.headers.get("content-type", "")
    if "html" in content_type.lower() and len(response.content) < 1000:
        raise RuntimeError(
            f"SINIM retornó HTML en vez de Excel. ¿Sesión expirada? "
            f"Respuesta: {response.text[:500]}"
        )

    # Guardar snapshot crudo (append-only, invariante #3)
    raw_path.write_bytes(response.content)

    return response.content.decode("latin-1")


def _parse_xml_spreadsheet(xml_content: str) -> list[dict[str, Any]]:
    """Parsea el XML Spreadsheet 2003 y extrae las filas de datos.

    Estructura del XML:
      Row 0: título/descripción
      Row 1: headers de variables (ej. "BPIGM (M$) Presupuesto Inicial...")
      Row 2: tipos de columna ("CODIGO", "MUNICIPIO", "2024", ...)
      Rows 3-347: datos (codigo_comuna, nombre_comuna, valor1, valor2, ...)

    Retorna lista de dicts con las columnas del esquema finanzas_municipales.
    """
    # Extraer todas las filas
    row_blocks = re.findall(r"<Row[^>]*>(.*?)</Row>", xml_content, re.DOTALL)

    if len(row_blocks) < 4:
        raise RuntimeError(f"XML de SINIM tiene solo {len(row_blocks)} filas, esperadas ≥ 4")

    data_rows = row_blocks[3:]  # Saltar filas 0-2 (título, headers, tipos)
    rows_out = []

    for row_xml in data_rows:
        cells = re.findall(r"<Cell[^>]*?>.*?</Cell>", row_xml, re.DOTALL)
        if len(cells) < max(VARIABLE_COLUMN_MAP.values()) + 1:
            continue  # Fila incompleta

        # Extraer código de comuna (Cell[0])
        codigo_match = re.search(r"<Data[^>]*>(.*?)</Data>", cells[0], re.DOTALL)
        if not codigo_match:
            continue
        codigo_comuna = codigo_match.group(1).strip()

        # Extraer nombre de comuna (Cell[1])
        # El XML viene en latin-1 (ISO-8859-1), convertir a UTF-8
        nombre_match = re.search(r"<Data[^>]*>(.*?)</Data>", cells[1], re.DOTALL)
        nombre_comuna = nombre_match.group(1).strip() if nombre_match else ""
        # Corregir encoding: SINIM entrega nombres en latin-1
        try:
            nombre_comuna = nombre_comuna.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass  # Mantener el nombre como está si la conversión falla

        # Extraer valores financieros
        def _extract_number(cell_index: int) -> float | None:
            if cell_index >= len(cells):
                return None
            data_match = re.search(r"<Data[^>]*>(.*?)</Data>", cells[cell_index], re.DOTALL)
            if not data_match:
                return None
            try:
                # Valor en miles de pesos → multiplicar × 1000
                return float(data_match.group(1).strip()) * 1000
            except (ValueError, TypeError):
                return None

        row = {
            "anio": 2024,
            "codigo_comuna": codigo_comuna,
            "nombre_comuna": nombre_comuna,
            "ingresos_totales": _extract_number(VARIABLE_COLUMN_MAP["ingresos_totales"]),
            "gastos_totales": _extract_number(VARIABLE_COLUMN_MAP["gastos_totales"]),
            "ingresos_propios_permanentes": _extract_number(
                VARIABLE_COLUMN_MAP["ingresos_propios_permanentes"]
            ),
            "fondo_comun_municipal": _extract_number(VARIABLE_COLUMN_MAP["fondo_comun_municipal"]),
            "gasto_personal": _extract_number(VARIABLE_COLUMN_MAP["gasto_personal"]),
            "gasto_inversion": _extract_number(VARIABLE_COLUMN_MAP["gasto_inversion"]),
        }
        rows_out.append(row)

    return rows_out


def fetch_data() -> tuple[list[dict[str, Any]], str, str, list[str]]:
    """Obtiene datos live desde SINIM con fallback a filas curadas.

    Returns:
        (rows, source_mode, source_url, notes)
    """
    ensure_staging_directories()
    notes: list[str] = []
    source_url = SINIM_DATOS_MUNICIPALES_URL
    timestamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DIR / f"sinim_finanzas_municipales_{timestamp}.xlsx"

    try:
        # 1. Configurar sesión con Playwright
        notes.append("live: Playwright configurando filtros SINIM")
        phpsessid, user_agent = _setup_sinim_session()

        # 2. Descargar Excel XML
        notes.append("live: descargando XML Spreadsheet")
        xml_content = _download_excel_xml(phpsessid, user_agent, raw_path)

        # 3. Parsear XML
        notes.append("live: parseando XML Spreadsheet")
        rows = _parse_xml_spreadsheet(xml_content)

        if len(rows) < 100:
            raise RuntimeError(
                f"SINIM retornó solo {len(rows)} municipios (esperados ≥ 100). "
                f"Posible cambio en la estructura del XML."
            )

        notes.append(f"live: {len(rows)} municipios extraídos (snapshot: {raw_path.name})")
        # Guardrail §4.2.5: scrape mensual NO se marca "live"
        source_mode = "monthly"

    except Exception as e:
        notes.append(f"live_failed: {e}")
        notes.append("fallback: usando filas curadas (3 comunas)")
        rows = _get_fallback_rows()
        source_mode = "fallback"
        source_url = SINIM_DATOS_MUNICIPALES_URL

    return rows, source_mode, source_url, notes


def _get_fallback_rows() -> list[dict[str, Any]]:
    """Filas curadas de respaldo (3 comunas con datos verificados)."""
    return [
        {
            "anio": 2024,
            "codigo_comuna": "13101",
            "nombre_comuna": "Santiago",
            "ingresos_totales": 245000000000.0,
            "gastos_totales": 231000000000.0,
            "ingresos_propios_permanentes": 162000000000.0,
            "fondo_comun_municipal": 39000000000.0,
            "gasto_personal": 70500000000.0,
            "gasto_inversion": 28500000000.0,
        },
        {
            "anio": 2024,
            "codigo_comuna": "05109",
            "nombre_comuna": "Viña del Mar",
            "ingresos_totales": 155000000000.0,
            "gastos_totales": 149000000000.0,
            "ingresos_propios_permanentes": 98000000000.0,
            "fondo_comun_municipal": 21000000000.0,
            "gasto_personal": 52300000000.0,
            "gasto_inversion": 17400000000.0,
        },
        {
            "anio": 2024,
            "codigo_comuna": "08101",
            "nombre_comuna": "Concepción",
            "ingresos_totales": 132000000000.0,
            "gastos_totales": 126000000000.0,
            "ingresos_propios_permanentes": 76500000000.0,
            "fondo_comun_municipal": 24500000000.0,
            "gasto_personal": 41800000000.0,
            "gasto_inversion": 15200000000.0,
        },
    ]


def normalize_rows(rows: list[dict[str, Any]]) -> pl.DataFrame:
    """Normaliza filas al esquema canónico de finanzas_municipales."""
    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("anio").cast(pl.Int32),
            pl.col("codigo_comuna").cast(pl.String).str.zfill(5),
            pl.col("nombre_comuna").cast(pl.String),
            pl.col("ingresos_totales").cast(pl.Float64),
            pl.col("gastos_totales").cast(pl.Float64),
            pl.col("ingresos_propios_permanentes").cast(pl.Float64),
            pl.col("fondo_comun_municipal").cast(pl.Float64),
            pl.col("gasto_personal").cast(pl.Float64),
            pl.col("gasto_inversion").cast(pl.Float64),
        )
        .sort(["anio", "codigo_comuna"])
    )


def build_metadata(df: pl.DataFrame, source_mode: str, source_url: str, notes: list[str]) -> dict:
    """Construye metadata.json para staging."""
    return build_standard_metadata(
        dataset="finanzas_municipales",
        source_name="SINIM - SUBDERE",
        source_url=source_url,
        source_mode=source_mode,
        source_detail=(
            "live_scraping_sinim_portal"
            if source_mode != "fallback"
            else "curated_fallback_pending_direct_export"
        ),
        df=df,
        notes=notes,
        reuse_policy=REUSE_POLICY,
    )


def process_sinim_finanzas() -> str:
    """Ejecuta el ciclo completo de extracción para finanzas_municipales."""
    raw_rows, source_mode, source_url, notes = fetch_data()
    df = normalize_rows(raw_rows)
    metadata = build_metadata(df, source_mode, source_url, notes)

    validation = SinimFinanzasLiveExtractor().validate(df, metadata)
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    SinimFinanzasLiveExtractor().write_staging(df, metadata)
    print(
        f"Finanzas municipales (SINIM live) guardadas en: {STAGING_CSV_PATH} "
        f"({df.height} registros, source_mode={source_mode})"
    )
    return str(STAGING_CSV_PATH)


class SinimFinanzasLiveExtractor(BaseExtractor):
    """Extractor live de finanzas municipales desde el portal SINIM.

    Usa Playwright para configuración de sesión + requests para descarga
    del Excel XML Spreadsheet 2003. Incluye fallback a 3 filas curadas
    si el scraping falla.
    """

    @property
    def dataset_name(self) -> str:
        return "finanzas_municipales"

    def fetch(self, **kwargs: Any) -> tuple:
        return fetch_data()

    def normalize(self, raw_data: tuple) -> pl.DataFrame:
        return normalize_rows(raw_data[0])

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        from src.validation import validate_finanzas_municipales

        return validate_finanzas_municipales(df, metadata)

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        df.write_csv(STAGING_CSV_PATH)
        write_staging_metadata(str(METADATA_PATH), metadata)
        return STAGING_CSV_PATH


if __name__ == "__main__":
    process_sinim_finanzas()
