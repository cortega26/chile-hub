"""Extrae nacimientos y defunciones por comuna desde los Anuarios de
Estadísticas Vitales del INE.

Fuente: Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales
URL: https://www.ine.gob.cl/estadisticas-por-tema/demografia-y-poblacion/estadisticas-vitales
Formato: 1 XLSX por año (anuario definitivo, 2010 en adelante), tabla 1.2.2-04
  "Nacidos vivos y defunciones por sexo, según región, provincia y comuna
  de residencia" (el nombre de hoja varía por año; se detecta por contenido).

Descubrimiento de archivos: el sitio del INE expone sus carpetas de documentos
vía endpoints JSON propios (`hijosCarpeta`/`getArchivos`, los mismos que usa
su JS) — no es scraping HTML sino una API JSON estable con GUIDs fijos.

Alcance MVP: solo anuarios DEFINITIVOS (grano comunal). Los boletines
provisionales/coyunturales del INE solo publican agregados nacional/región,
sin desglose comunal — por eso `estado_dato` es siempre "definitivo" y la
columna existe para futuros definitivos, no para provisionales.
"""

import datetime
import os
import re
import sys
from pathlib import Path
from typing import Any, cast

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

try:
    from src.extractors.region_utils import norm_text, region_nombre_a_codigo
except ModuleNotFoundError:
    from region_utils import norm_text, region_nombre_a_codigo

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "estadisticas_vitales.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "estadisticas_vitales.metadata.json")
COMUNAS_CSV_PATH = os.path.join(STAGING_DIR, "comunas.csv")

# ── Descubrimiento de archivos (endpoints JSON propios del sitio INE) ────────
INE_BASE = "https://www.ine.gob.cl/estadisticas-por-tema/demografia-y-poblacion"
EEVV_PAGE = f"{INE_BASE}/estadisticas-vitales"
FOLDERS_URL = f"{EEVV_PAGE}/hijosCarpeta/"
FILES_URL = f"{EEVV_PAGE}/getArchivos/"
# Carpeta "CUADROS ESTADÍSTICOS" (GUID estable del document library de INE).
CUADROS_FOLDER_ID = "a1cee0c4-70a2-40a4-989b-086533b97c4d"

SOURCE_NAME = "Instituto Nacional de Estadísticas (INE) — Estadísticas Vitales"
LICENSE_URL = "https://www.ine.gob.cl/terminos-de-uso"

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC BY 4.0",
    "license_url": LICENSE_URL,
    "attribution_required": True,
    "redistribution_ok": True,
    "summary": (
        "Anuarios de Estadísticas Vitales del INE (nacimientos y defunciones "
        "por comuna de residencia). Datos abiertos con atribución requerida."
    ),
}

# Eventos del MVP y su etiqueta de grupo en la fila de encabezado del XLSX.
# El layout varía por año (2015: totales sin sexo; 2023: split por sexo) pero
# los nombres de grupo son estables.
EVENTO_GRUPOS = {
    "nacimiento": ("nacidos vivos",),
    "defuncion": ("defunciones generales",),
}
SEXOS = ("hombre", "mujer", "indeterminado")

# Alias de grafías históricas de comunas en tabulados antiguos → clean actual.
# (Se completa si el parseo de algún año deja comunas sin match.)
COMUNA_ALIAS = {
    "paiguano": "paihuano",
    "marchihue": "marchigue",
    # El anuario 2023 escribe la comuna 11201 con grafía arcaica "Aisén".
    "aisen": "aysen",
    # Grafías de Coyhaique en tabulados 2010-2012.
    "coihaique": "coyhaique",
    "coihayque": "coyhaique",
}

# Variantes de nombre de provincia en los tabulados INE vs DPA vigente:
# "Biobío" (DPA: "Bío-Bío"), "San Felipe de Aconcagua" (DPA: "San Felipe")
# y "Diguillín" (ausente en la DPA de BCN, que lista "Ñuble" en su lugar).
PROVINCIAS_EXTRA = {"biobio", "san felipe de aconcagua", "diguillin"}

# Prefijos de numeración regional en tabulados antiguos ("XV Región de...",
# "14  Región de..."). Se retiran antes del lookup en REGION_A_CODIGO.
_ROMANOS_RE = re.compile(
    r"^(xvi|xv|xiv|xiii|xii|xi|ix|x|viii|vii|vi|v|iv|iii|ii|i)\s+", re.IGNORECASE
)
_DIGITOS_RE = re.compile(r"^\d+\s+")


def _codigo_region_etiqueta(label: str) -> str | None:
    """Mapea una etiqueta de región (cualquier época) a código CUT."""
    texto = _DIGITOS_RE.sub("", _ROMANOS_RE.sub("", label.strip()))
    return region_nombre_a_codigo(texto)


# ── Fallback mínimo ─────────────────────────────────────────────────────────
# Estructural, no cobertura: evita que el build se rompa si el INE no responde.
# El job `publish` de CI rechaza datasets en fallback (ver AGENTS.md §5).
FALLBACK_ROWS = [
    {
        "anio": 2023,
        "codigo_region": "13",
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "evento": "nacimiento",
        "sexo": "total",
        "cantidad": 0,
        "estado_dato": "definitivo",
        "fuente": f"{SOURCE_NAME} (fallback)",
        "url_fuente": EEVV_PAGE,
        "fecha_fuente": "",
    },
    {
        "anio": 2023,
        "codigo_region": "13",
        "codigo_comuna": "13101",
        "nombre_comuna": "Santiago",
        "evento": "defuncion",
        "sexo": "total",
        "cantidad": 0,
        "estado_dato": "definitivo",
        "fuente": f"{SOURCE_NAME} (fallback)",
        "url_fuente": EEVV_PAGE,
        "fecha_fuente": "",
    },
    {
        "anio": 2023,
        "codigo_region": "08",
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "evento": "nacimiento",
        "sexo": "total",
        "cantidad": 0,
        "estado_dato": "definitivo",
        "fuente": f"{SOURCE_NAME} (fallback)",
        "url_fuente": EEVV_PAGE,
        "fecha_fuente": "",
    },
    {
        "anio": 2023,
        "codigo_region": "08",
        "codigo_comuna": "08101",
        "nombre_comuna": "Concepción",
        "evento": "defuncion",
        "sexo": "total",
        "cantidad": 0,
        "estado_dato": "definitivo",
        "fuente": f"{SOURCE_NAME} (fallback)",
        "url_fuente": EEVV_PAGE,
        "fecha_fuente": "",
    },
]

REQUIRED_COLUMNS = [
    "anio",
    "codigo_region",
    "codigo_comuna",
    "nombre_comuna",
    "evento",
    "sexo",
    "cantidad",
    "estado_dato",
    "fuente",
    "url_fuente",
    "fecha_fuente",
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _snapshot_path(year: int) -> Path:
    """Ruta de snapshot crudo con timestamp."""
    stamp = datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(RAW_DIR) / f"ine_estadisticas_vitales_{year}_{stamp}.xlsx"


def _post_json(url: str, payload: dict) -> dict:
    """POST a los endpoints JSON del sitio INE con reintentos."""
    with fetch_with_retry(url, timeout=60, get_fn=requests.post, data=payload) as response:
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())


def _discover_anuario_docs() -> list[tuple[int, str, str]]:
    """Descubre (anio, titulo, url) de cada archivo de anuario a parsear.

    Recorre las subcarpetas anuales de CUADROS ESTADÍSTICOS. Algunos años
    publican un único combinado ("... nacimientos y defunciones") y otros
    archivos separados por hecho vital (2016: nacimientos + defunciones +
    matrimonios + fetales). Se seleccionan los que aportan nacimientos o
    defunciones; matrimonios/AUC/fetales quedan fuera del MVP. Años con solo
    provisionales (sin anuario) se omiten: los provisionales no traen
    grano comunal.
    """
    data = _post_json(FOLDERS_URL, {"idFolder": CUADROS_FOLDER_ID})
    year_folders = []
    for folder in data.get("folder", []):
        title = (folder.get("Titulo") or "").strip()
        if re.fullmatch(r"(19|20)\d{2}", title):
            year_folders.append((int(title), folder.get("Id")))
    year_folders.sort()

    found = []
    for year, folder_id in year_folders:
        docs = _post_json(FILES_URL, {"idFolder": folder_id}).get("documento", [])
        for doc in docs:
            title = (doc.get("Titulo") or "").strip()
            t = norm_text(title)
            if not t.startswith("anuario de estadisticas vitales") or str(year) not in t:
                continue
            if any(k in t for k in ("matrim", "auc", "union civil", "fetal")) and not any(
                k in t for k in ("nacim", "defunc")
            ):
                continue
            url = (doc.get("Url") or "").replace("http:", "https:")
            found.append((year, title, url))
    return found


def _download_xlsx(url: str, year: int) -> Path:
    """Descarga un XLSX y guarda snapshot crudo. Retorna la ruta."""
    target = _snapshot_path(year)
    with fetch_with_retry(url, timeout=120) as response:
        response.raise_for_status()
        target.write_bytes(response.content)
    return target


def _load_comunas_lookup() -> tuple[dict[str, tuple[str, str, str]], set[str]]:
    """``nombre_comuna_clean -> (codigo_comuna, codigo_region, nombre_comuna)``
    más el conjunto de nombres de provincia (para distinguir filas de
    provincia de filas de comuna en los tabulados).

    Usa data/staging/comunas.csv (lo genera subdere_extractor.py, que corre
    antes en `make extract`). Sin ese archivo no hay cruce a CUT posible.
    """
    if not os.path.exists(COMUNAS_CSV_PATH):
        raise FileNotFoundError(
            "No se encuentra data/staging/comunas.csv. "
            "Corre primero: python src/extractors/subdere_extractor.py"
        )
    df = pl.read_csv(
        COMUNAS_CSV_PATH,
        schema_overrides={"codigo_comuna": pl.String, "codigo_region": pl.String},
    )
    lookup = {}
    provinces = set()
    for row in df.iter_rows(named=True):
        lookup[row["nombre_comuna_clean"]] = (
            row["codigo_comuna"],
            row["codigo_region"],
            row["nombre_comuna"],
        )
        provinces.add(norm_text(str(row["nombre_provincia"])))
    return lookup, provinces


def _to_int(value) -> int:
    """Celda numérica a int; None/'-'/' ' → 0."""
    if value is None:
        return 0
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-"):
            return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def _find_comuna_sheet(wb) -> tuple[str, list[list]]:
    """Localiza la hoja 1.2.2-04 por contenido y retorna (nombre, filas).

    El nombre de hoja cambia por año ("122-04" en 2023, "1.2.2-04" en 2015,
    "COMUNAS DE RESIDENCIA" en 2019); lo estable es la celda
    "COMUNA(S) DE RESIDENCIA" en la columna A.
    """
    patron = re.compile(r"COMUNAS?\s+DE\s+RESIDENCIA")
    for name in wb.sheetnames:
        ws = wb[name]
        head = [row[0].value for row in ws.iter_rows(min_row=1, max_row=12, max_col=1)]
        if any(isinstance(c, str) and patron.search(c.upper()) for c in head):
            return name, list(ws.iter_rows(values_only=True))
    raise KeyError("ninguna hoja contiene la tabla comunal (COMUNA DE RESIDENCIA)")


def _detect_indent_convention(
    rows: list[list], header_end: int, provinces: set[str], lookup: dict
) -> bool:
    """Detecta si las filas indentadas son provincias (True, estilo 2023) o
    comunas (False, estilo 2018-2020). Decide con la primera fila indentada
    no ambigua (nombre solo de provincia o solo de comuna).
    """
    for r in rows[header_end:]:
        raw = r[0] if r else None
        if not isinstance(raw, str) or raw == raw.lstrip() or not raw.strip():
            continue
        s = COMUNA_ALIAS.get(norm_text(raw.strip()), norm_text(raw.strip()))
        in_prov = s in provinces
        in_com = s in lookup
        if in_prov and not in_com:
            return True
        if in_com and not in_prov:
            return False
    return True


def _parse_comuna_sheet(
    rows: list[list],
    year: int,
    lookup: dict,
    provinces: set[str],
    url_fuente: str,
    fecha_fuente: str,
) -> tuple[list[dict], dict[str, int], list[str]]:
    """Parsea la tabla comunal a filas (anio, comuna, evento, sexo, cantidad).

    Tolera los layouts 2010-2023: grupos con o sin split de sexo, etiqueta
    de defunciones repartida en dos filas ("DEFUNCIONES" + "Generales") y
    convención de indentado invertida (provincia indentada vs comuna
    indentada). Retorna (filas, totales_nacionales, notas).
    """
    norm = lambda v: norm_text(str(v)) if v is not None else ""  # noqa: E731
    provinces = set(provinces) | PROVINCIAS_EXTRA

    # Fila de grupos: primera con "nacidos vivos".
    try:
        group_idx = next(
            i for i, r in enumerate(rows[:20]) if any(norm(c) == "nacidos vivos" for c in r)
        )
    except StopIteration:
        raise KeyError("no se encontró la fila de grupos (Nacidos Vivos)")
    group_row = [norm(c) for c in rows[group_idx]]
    prev_row = [norm(c) for c in rows[group_idx - 1]] if group_idx > 0 else []
    # Fila de sexo: la siguiente, solo si trae Hombre/Mujer.
    next_row = [norm(c) for c in rows[group_idx + 1]]
    has_sexo = "hombre" in next_row
    sexo_row = next_row if has_sexo else []

    # Mapeo columna -> (evento, sexo). Las celdas combinadas solo tienen
    # valor en la primera columna: forward-fill por fila. La etiqueta de
    # grupo puede repartirse en dos filas ("DEFUNCIONES" + "Generales"):
    # se combinan prev+curr salvo que prev sea un fragmento de título.
    def _ffill(cells: list[str], j: int) -> str:
        while j > 0 and not cells[j]:
            j -= 1
        return cells[j] if j < len(cells) else ""

    colmap: dict[int, tuple[str, str]] = {}
    width = max(len(group_row), len(prev_row), len(sexo_row))
    for j in range(1, width):
        c = group_row[j] if j < len(group_row) else ""
        # Etiqueta de la fila superior SOLO si está en la misma columna (sin
        # forward-fill: un grupo vecino fusionado como "POBLACION" en 2016
        # contaminaría la columna actual).
        p = prev_row[j] if prev_row and j < len(prev_row) else ""
        combo = f"{p} {c}".strip() if (p and len(p) <= 15) else c
        if not combo:
            combo = _ffill(group_row, j)
        if combo == "nacidos vivos":
            evento = "nacimiento"
        elif combo == "defunciones generales":
            evento = "defuncion"
        elif combo == "defunciones":
            # Sub-etiqueta "Generales" en la fila siguiente (2015/2019).
            sub = next_row[j] if j < len(next_row) else ""
            if sub != "generales":
                continue
            evento = "defuncion"
        else:
            continue
        sexo = sexo_row[j] if has_sexo and j < len(sexo_row) and sexo_row[j] in SEXOS else "total"
        colmap[j] = (evento, sexo)

    if not colmap:
        raise KeyError("no se encontraron columnas de nacimientos/defunciones")

    header_end = group_idx + 2
    indented_is_province = _detect_indent_convention(rows, header_end, provinces, lookup)

    def _canon(raw: str) -> str:
        return COMUNA_ALIAS.get(norm_text(raw.strip()), norm_text(raw.strip()))

    def _es_total(upper: str) -> bool:
        return upper in ("TOTAL", "TOTAL PAIS", "TOTAL PAÍS")

    def _es_pie(upper: str) -> bool:
        return upper.startswith(("FUENTE", "NOTA", "P:"))

    def _es_region(label: str, clean: str) -> bool:
        upper = label.upper()
        # Mayúsculas ("ARICA Y PARINACOTA") o cualquier grafía mapeable
        # ("XV Región de...", "Región Metropolitana"). La guarda
        # `clean not in lookup` evita confundir la comuna Aysén con la
        # región homónima.
        return (upper == label and len(label) > 3) or (
            _codigo_region_etiqueta(label) is not None and clean not in lookup
        )

    body = [
        (i, r)
        for i, r in enumerate(rows[header_end:])
        if r and isinstance(r[0], str) and r[0].strip()
    ]
    # Tres layouts de jerarquía según el año:
    # - "prefix" (2010-2015): provincias marcadas "Provincia X", sin indentado.
    # - "indent" (2018-2023): provincias vs comunas por indentación
    #   (el sentido se invierte en 2018-2020; lo detecta _detect_indent_convention).
    # - "bare" (2017): sin indentado ni prefijo; solo queda la estructura.
    tiene_prefijo = any(_canon(r[0]).startswith(("provincia ", "prov.")) for _, r in body)
    tiene_indent = any(r[0] != r[0].lstrip() for _, r in body)
    modo = "prefix" if tiene_prefijo else ("indent" if tiene_indent else "bare")
    # Entre filas de contenido (no región/total/pie), conservar solo la
    # ÚLTIMA ocurrencia de cada etiqueta: la provincia homónima siempre
    # precede a su comuna ("Arica"/"Arica", "Coyhaique"/"Coihayque").
    contenidos = [
        (i, r)
        for i, r in body
        if not _es_total(r[0].strip().upper())
        and not _es_pie(r[0].strip().upper())
        and not _es_region(r[0].strip(), _canon(r[0]))
    ]
    ultima_pos = {}
    for i, r in contenidos:
        ultima_pos[_canon(r[0])] = i

    out: list[dict] = []
    totals: dict[str, int] = {}
    unmatched: list[str] = []

    for i, r in body:
        label_raw = r[0]
        label = label_raw.strip()
        upper = label.upper()
        clean = _canon(label)

        if _es_total(upper):
            for j, (evento, sexo) in colmap.items():
                totals[f"{evento}_{sexo}"] = totals.get(f"{evento}_{sexo}", 0) + _to_int(
                    r[j] if j < len(r) else None
                )
            continue
        if _es_pie(upper):
            # Pie de tabla (fuente, notas metodológicas).
            continue
        if _es_region(label, clean):
            continue
        if ultima_pos.get(clean, i) != i:
            continue  # ocurrencia temprana: fila estructural (provincia)
        if clean.startswith(("provincia ", "prov.")):
            continue
        if clean in provinces and clean not in lookup:
            # Provincia sin comuna homónima (vale en los tres layouts: en
            # "bare" es la única señal; en "indent"/"prefix" silencia filas
            # de provincia indentadas por quirk del archivo).
            continue
        if modo == "indent" and indented_is_province:
            if label_raw != label_raw.lstrip():
                continue  # provincia indentada (estilo 2021-2023)
        elif modo == "indent" and label_raw == label_raw.lstrip() and clean in provinces:
            continue  # provincia sin indentar (estilo 2018-2020)

        # Fila de comuna.
        hit = lookup.get(clean)
        if hit is None:
            unmatched.append(label)
            continue
        codigo_comuna, codigo_region, nombre_comuna = hit
        for j, (evento, sexo) in colmap.items():
            out.append(
                {
                    "anio": year,
                    "codigo_region": codigo_region,
                    "codigo_comuna": codigo_comuna,
                    "nombre_comuna": nombre_comuna,
                    "evento": evento,
                    "sexo": sexo,
                    "cantidad": _to_int(r[j] if j < len(r) else None),
                    "estado_dato": "definitivo",
                    "fuente": SOURCE_NAME,
                    "url_fuente": url_fuente,
                    "fecha_fuente": fecha_fuente,
                }
            )

    notas = []
    if unmatched:
        notas.append(
            f"{year}: {len(unmatched)} etiquetas sin match CUT: {sorted(set(unmatched))[:10]}"
        )
    if not indented_is_province:
        notas.append(f"{year}: convención de indentado invertida (comuna indentada)")
    return out, totals, notas


def fetch_data() -> tuple[list[dict], str, str, list[str]]:
    """Obtiene estadísticas vitales comunales desde el INE.

    Retorna (rows, source_mode, source_url, notes).
    """
    ensure_staging_directories()
    notes: list[str] = []
    all_rows: list[dict] = []
    fecha_fuente = datetime.datetime.now(UTC).strftime("%Y-%m-%d")

    try:
        lookup, provinces = _load_comunas_lookup()
    except FileNotFoundError as exc:
        return FALLBACK_ROWS, "fallback", EEVV_PAGE, [str(exc)]

    try:
        anuarios = _discover_anuario_docs()
    except (requests.RequestException, ValueError, KeyError) as exc:
        notes.append(f"descubrimiento de anuarios falló ({exc}); sin snapshots previos, fallback")
        anuarios = []

    if not anuarios:
        notes.append("sin anuarios definitivos disponibles")
        return FALLBACK_ROWS, "fallback", EEVV_PAGE, notes

    any_live = False
    errores: dict[int, list[str]] = {}
    for year, title, url in anuarios:
        try:
            try:
                path = _download_xlsx(url, year)
            except (requests.RequestException, OSError) as exc:
                snapshots = sorted(Path(RAW_DIR).glob(f"ine_estadisticas_vitales_{year}_*.xlsx"))
                if not snapshots:
                    raise
                path = snapshots[-1]
                notes.append(f"{year}: descarga falló, usando snapshot {path.name} ({exc})")
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            try:
                sheet_name, sheet_rows = _find_comuna_sheet(wb)
            finally:
                wb.close()
            rows, totals, sheet_notes = _parse_comuna_sheet(
                sheet_rows, year, lookup, provinces, url, fecha_fuente
            )
            notes.extend(sheet_notes)
            if not rows:
                errores.setdefault(year, []).append(f"'{title}': tabla comunal sin filas")
                continue
            all_rows.extend(rows)
            any_live = True
            tot_nac = sum(v for k, v in totals.items() if k.startswith("nacimiento_"))
            tot_def = sum(v for k, v in totals.items() if k.startswith("defuncion_"))
            notes.append(
                f"{year}: {len(rows)} filas desde '{title}' (hoja {sheet_name}; "
                f"TOTAL país: {tot_nac} nacimientos, {tot_def} defunciones)"
            )
        except Exception as exc:  # noqa: BLE001 — un archivo no tumba al resto; queda en notes
            errores.setdefault(year, []).append(f"'{title}': {exc}")
            continue
    # Solo reportar años omitidos si NINGÚN archivo del año aportó filas
    # (p. ej. el suplemento neonatal 2016 no trae tabla comunal general, pero
    # el archivo de nacimientos del mismo año sí).
    anios_con_filas = {r["anio"] for r in all_rows}
    for year in sorted(errores):
        if year not in anios_con_filas:
            notes.append(f"{year}: año omitido ({'; '.join(errores[year])})")

    if not all_rows:
        return FALLBACK_ROWS, "fallback", EEVV_PAGE, notes

    mode = "live" if any_live else "fallback"
    return all_rows, mode, EEVV_PAGE, notes


def normalize_rows(rows: list[dict]) -> pl.DataFrame:
    """Convierte filas a DataFrame canónico."""
    if not rows:
        return pl.DataFrame(
            schema={
                "anio": pl.Int64,
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "evento": pl.String,
                "sexo": pl.String,
                "cantidad": pl.Int64,
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
        pl.col("anio").cast(pl.Int64),
        pl.col("codigo_region").cast(pl.String),
        pl.col("codigo_comuna").cast(pl.String),
        pl.col("nombre_comuna").cast(pl.String),
        pl.col("evento").cast(pl.String),
        pl.col("sexo").cast(pl.String),
        pl.col("cantidad").cast(pl.Int64),
        pl.col("estado_dato").cast(pl.String),
        pl.col("fuente").cast(pl.String),
        pl.col("url_fuente").cast(pl.String),
        pl.col("fecha_fuente").cast(pl.String),
    ).select(REQUIRED_COLUMNS)


def build_metadata(mode: str, source_url: str, notes: list[str], row_count: int) -> dict:
    """Construye metadatos estándar para el dataset."""
    return {
        "dataset": "estadisticas_vitales",
        "source_name": SOURCE_NAME,
        "source_url": source_url,
        "source_mode": mode,
        "source_detail": (
            "Anuarios de Estadísticas Vitales (tabulados XLSX, tabla 1.2.2-04 "
            "por comuna de residencia). Solo definitivos: los boletines "
            "provisionales del INE no publican desglose comunal."
        ),
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": row_count,
        "fields": REQUIRED_COLUMNS,
        "notes": notes,
        "reuse_policy": REUSE_POLICY,
    }


def process_estadisticas_vitales() -> dict:
    """Ejecuta el flujo completo de extracción y staging."""
    rows, mode, source_url, notes = fetch_data()
    df = normalize_rows(rows)

    metadata = build_metadata(mode, source_url, notes, df.height)

    ensure_staging_directories()
    df.write_csv(STAGING_CSV_PATH)
    write_staging_metadata(METADATA_PATH, metadata)
    print(f"estadisticas_vitales: {df.height} filas escritas en staging (mode={mode})")

    return metadata


# ── Extractor ────────────────────────────────────────────────────────────────


class EstadisticasVitalesExtractor(BaseExtractor):
    """Extractor de estadísticas vitales comunales (INE)."""

    @property
    def dataset_name(self) -> str:
        return "estadisticas_vitales"

    def fetch(self, **kwargs):
        return fetch_data()

    def normalize(self, raw_data):
        rows, _mode, _url, _notes = raw_data
        return normalize_rows(rows)

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_estadisticas_vitales

        return validate_estadisticas_vitales(df, metadata)

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
    process_estadisticas_vitales()
