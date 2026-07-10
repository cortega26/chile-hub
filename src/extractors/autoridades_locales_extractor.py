"""Extractor de autoridades locales de Chile (Plan 042 · BCN SIIT alcaldes al 100%).

Dataset **`autoridades_locales`**, con fuente dual:

- **Alcaldes (345 comunas):** BCN SIIT (Biblioteca del Congreso Nacional) — fuente
  gubernamental oficial, cobertura 100%. Reemplaza a Wikipedia como fuente primaria
  de nombre de alcalde. Wikipedia se usa solo como enriquecimiento opcional de
  periodo_inicio para las ~224 comunas con página "Anexo:Alcaldes de X".

- **Gobernadores regionales (16):** Wikipedia, tabla vía Scrapling (CC-BY-SA).

v1 (carril `candidate`) usaba Wikipedia como fuente única para alcaldes (plan 023).
v2 (plan 042) migra a BCN SIIT como fuente primaria de nombre, resolviendo:
  - Cobertura 165/345 → 345/345 (100%)
  - Licencia share-alike → dato público gubernamental (sin restricción para datos
    factuales de autoridades).
  - Wikipedia se mantiene como fuente de periodo_inicio donde esté disponible.

Solo cargos públicos; **sin datos personales**."""

import concurrent.futures
import datetime
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
    from src.extractors.http_utils import fetch_with_retry
    from src.extractors.region_utils import REGION_A_CODIGO, norm_text
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata
    from http_utils import fetch_with_retry
    from region_utils import REGION_A_CODIGO, norm_text

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "autoridades_locales.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "autoridades_locales.metadata.json")

GOBERNADORES_URL = "https://es.wikipedia.org/wiki/Gobernador_regional_de_Chile"
ALCALDES_INDICE_TITULO = "Anexo:Alcaldes de Chile"
MEDIAWIKI_API = "https://es.wikipedia.org/w/api.php"
_HEADERS = {"User-Agent": "chile-hub/data-pipeline (+https://github.com/cortega26/chile-hub)"}

BCN_SIIT_URL = "https://www.bcn.cl/siit/reportescomunales/comunas_v.html"
BCN_SIIT_ANNO = "2024"
_BCN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

SCHEMA: dict[str, type[pl.DataType]] = {
    "id_autoridad": pl.String,
    "nombre": pl.String,
    "cargo": pl.String,
    "institucion": pl.String,
    "partido": pl.String,
    "pacto": pl.String,
    "distrito_electoral": pl.String,
    "circunscripcion_senatorial": pl.String,
    "codigo_comuna": pl.String,
    "codigo_region": pl.String,
    "periodo_inicio": pl.String,
    "periodo_fin": pl.String,
    "estado_mandato": pl.String,
    "fuente": pl.String,
    "url_fuente": pl.String,
    "fecha_consulta": pl.String,
}

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC-BY-SA",
    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    "attribution_required": True,
    "redistribution_ok": True,
    "share_alike": True,
    "summary": (
        "Autoridades locales (gobernadores regionales y alcaldes) compiladas desde "
        "Wikipedia (CC-BY-SA). Dataset segregado para no propagar share-alike al resto "
        "del bundle."
    ),
}

EXPECTED_GOBERNADORES = 16
EXPECTED_COMUNAS_ALCALDES = 346
# Cobertura mínima aceptable del campo "alcalde vigente". Con BCN SIIT como
# fuente primaria se esperan 346/346 comunas con nombre. 300 deja margen para
# vacancia temporal o errores de red transitorios, sin disparar falsas alarmas.
MIN_ALCALDES_CON_TITULAR = 300

# El título del enlace de región es "Gobernador(a) regional [Metropolitano] de|del <región>".
_REGION_TITLE_RE = re.compile(
    r"^gobernador[a]?\s+regional\s+(?:metropolitan[oa]\s+)?del?\s+(.+)$", re.I
)


def _region_from_title(title: str) -> str | None:
    match = _REGION_TITLE_RE.match(title.strip())
    return match.group(1).strip() if match else None


_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^/]*/>", re.S)
# Lookahead que delimita el valor de un campo de infobox hasta el siguiente campo
# (`|otro_campo=`), un salto de línea, o el cierre `}}` — NO hasta el primer "|" a
# secas, porque muchos infobox comprimen varios campos en una sola línea
# (`|titular=X|inicio=Y|...`) y un corte ingenuo capturaría el resto de esos campos. Un
# wikilink con pipe interno (`[[X|Y]]`) no se corta porque "Y]]" no calza con el patrón
# "campo=" del lookahead.
_FIN_DE_CAMPO = r"(?=\s*\|[a-zA-Záéíóúñ_ ]+\s*=|\n|\}\}|$)"
# El grupo usa "*" (no "+"): un campo vacío ("|titular = " seguido de "|otro_campo=")
# debe capturar cadena vacía y ser tratado como "sin valor", no saltar al campo
# siguiente y capturarlo por error (con "+" el motor de regex, al no poder matchear 0
# caracteres antes de "|", se ve forzado a expandirse hasta el próximo salto de línea,
# tragándose el contenido del campo siguiente completo).
_TITULAR_RE = re.compile(r"\|\s*titular\s*=\s*(.*?)" + _FIN_DE_CAMPO)
_INICIO_RE = re.compile(r"\|\s*inicio\s*=\s*(.*?)" + _FIN_DE_CAMPO)
_INICIO_FECHA_RE = re.compile(
    r"\{\{[Ff]echa(?:\s+de\s+inicio)?\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*(\d{4})"
)
_VIGENTE_MARKERS = ("en el cargo", "en ejercicio", "actualidad", "presente")
# Disambiguadores comunes en títulos de subpágina, p. ej. "Concepción (Chile)".
_DISAMBIG_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _clean_wikitext_value(raw: str) -> str:
    """Limpia un valor de infobox/celda: quita <ref>, corta en salto de línea/pipe extra,
    y resuelve un wikilink ``[[X|Y]]`` -> ``Y`` (o ``[[X]]`` -> ``X``)."""
    value = _REF_RE.sub("", raw).strip()
    value = value.split("\n")[0].strip()
    match = _WIKILINK_RE.search(value)
    if match:
        return (match.group(2) or match.group(1)).strip()
    # sin wikilink: quitar markup residual simple (negritas/cursivas)
    return value.strip("'").strip()


def _parse_inicio(raw: str) -> str | None:
    match = _INICIO_FECHA_RE.search(raw)
    if not match:
        return None
    day, month, year = match.groups()
    try:
        return datetime.date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _extract_alcalde_actual(wikitext: str) -> tuple[str | None, str | None]:
    """Devuelve ``(nombre, periodo_inicio)`` del alcalde vigente, o ``(None, None)``.

    Estrategia primaria: campo ``titular=`` del infobox (cubre la mayoría de comunas).
    Fallback: última fila de la última tabla que tenga una marca explícita de vigencia
    ("en el cargo"/"en ejercicio"/"actualidad"). Sin evidencia clara, retorna ``None``
    (no se inventa un titular — algunas comunas están efectivamente vacantes).
    """
    titular_match = _TITULAR_RE.search(wikitext)
    if titular_match:
        nombre = _clean_wikitext_value(titular_match.group(1))
        if nombre:
            inicio_match = _INICIO_RE.search(wikitext)
            inicio = _parse_inicio(inicio_match.group(1)) if inicio_match else None
            return nombre, inicio

    tables = re.findall(r"\{\|.*?\n\|\}", wikitext, re.S)
    if not tables:
        return None, None
    rows = tables[-1].split("|-")
    for row in reversed(rows):
        if not any(marker in row.lower() for marker in _VIGENTE_MARKERS):
            continue
        # Cada celda de MediaWiki empieza con "|" al inicio de línea (o "||" para varias
        # celdas en una misma línea). Dividir por CUALQUIER "|" rompería wikilinks con
        # texto alternativo como [[Sacha Razmilic|Sacha Razmilic Burgos]] a la mitad.
        cells = [
            c.strip(" \n")
            for line in re.split(r"\n\s*\|", row)
            for c in line.split("||")
            if c.strip(" \n")
        ]
        for cell in cells:
            # Celdas de imagen ([[Archivo:...]] / [[File:...]]) no son el nombre — si se
            # limpian igual, un wikilink con pipe ([[Archivo:x.svg|100x100px]]) devolvería
            # el tamaño ("100x100px") como si fuera texto válido. Se descartan antes de
            # limpiar, sobre la celda cruda.
            if re.match(r"^\[\[\s*(archivo|file|imagen)\s*:", cell, re.I):
                continue
            cleaned = _clean_wikitext_value(cell)
            if not cleaned:
                continue
            # descarta: numeraciones ordinales ("31°", con o sin comillas de negrita ya
            # resueltas por _clean_wikitext_value), fechas/números puros, y la columna de
            # período que contiene la palabra "cargo" (la propia marca de vigencia).
            if (
                not re.match(r"^\d+°?$", cleaned)
                and not re.match(r"^[\d\s\-/.]+$", cleaned)
                and "cargo" not in cleaned.lower()
            ):
                return cleaned, None
    return None, None


def _comuna_name_from_title(title: str) -> str:
    """``Anexo:Alcaldes de Concepción (Chile)`` -> ``Concepción``."""
    name = title.removeprefix("Anexo:Alcaldes de ").strip()
    return _DISAMBIG_RE.sub("", name).strip()


def fetch_alcalde_titles() -> list[str]:
    """Títulos de las ~345 subpáginas "Anexo:Alcaldes de <comuna>" (1 request)."""
    params = {
        "action": "parse",
        "page": ALCALDES_INDICE_TITULO,
        "prop": "links",
        "format": "json",
        "formatversion": "2",
        "pllimit": "500",
    }
    response = fetch_with_retry(MEDIAWIKI_API, params=params, headers=_HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    links = data.get("parse", {}).get("links", [])
    return [
        link["title"]
        for link in links
        if link["title"].startswith("Anexo:Alcaldes de ")
        and link["title"] != ALCALDES_INDICE_TITULO
    ]


def fetch_alcaldes_wikitext(titles: list[str]) -> dict[str, str]:
    """Wikitext de cada subpágina, en lotes de 50 títulos (API pública de MediaWiki)."""
    resultado: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        lote = titles[i : i + 50]
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(lote),
            "format": "json",
            "formatversion": "2",
        }
        response = fetch_with_retry(MEDIAWIKI_API, params=params, headers=_HEADERS, timeout=30)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
        for page in pages:
            if page.get("missing"):
                continue
            revisions = page.get("revisions") or []
            if revisions:
                resultado[page["title"]] = revisions[0]["slots"]["main"]["content"]
    return resultado


def fetch_alcaldes() -> list[dict[str, str | None]]:
    """Lista de ``{comuna, nombre, periodo_inicio}`` para las 345 comunas.

    Estrategia en dos niveles:
    1. **BCN SIIT (primaria)**: nombre del alcalde para las 345 comunas desde
       la Biblioteca del Congreso Nacional — fuente oficial, cobertura 100%.
    2. **Wikipedia (enriquecimiento)**: partido/coalición desde "Anexo:Alcaldes
       de X" donde exista (~224 comunas). Solo enriquece, no reemplaza.

    Si BCN SIIT falla por completo, degrada a solo-Wikipedia (comportamiento
    previo). Si ambas fallan, retorna ``[]``."""
    comunas = _load_comunas_lookup()
    if not comunas:
        print("Advertencia: comunas.csv no disponible. Sin lookup de códigos territoriales.")
        return []

    # --- Nivel 1: BCN SIIT (primaria, 345 comunas) ---
    filas_bcn: dict[str, dict[str, str | None]] = {}
    try:
        todas_bcn = fetch_alcaldes_bcn(comunas)
        for fila in todas_bcn:
            comuna = fila["comuna"] or ""
            filas_bcn[comuna] = {
                "comuna": comuna,
                "nombre": fila["nombre"],
                "periodo_inicio": None,
            }
        print(
            f"BCN SIIT: {sum(1 for f in filas_bcn.values() if f['nombre'])}/"
            f"{len(filas_bcn)} alcaldes con nombre."
        )
    except Exception as exc:  # noqa: BLE001 — degradación a Wikipedia sola
        print(f"Advertencia: BCN SIIT falló por completo ({exc}). Degradando a Wikipedia.")
        filas_bcn = {}

    # --- Nivel 2: Wikipedia (enriquecimiento de periodo_inicio) ---
    wikidata: dict[str, dict[str, str | None]] = {}
    wikitext_por_titulo: dict[str, str] = {}
    try:
        titles = fetch_alcalde_titles()
        wikitext_por_titulo = fetch_alcaldes_wikitext(titles) if titles else {}
        for title, wikitext in wikitext_por_titulo.items():
            comuna = _comuna_name_from_title(title)
            nombre_wp, inicio = _extract_alcalde_actual(wikitext)
            wikidata[comuna] = {
                "comuna": comuna,
                "nombre_wikipedia": nombre_wp,
                "periodo_inicio": inicio,
            }
    except Exception as exc:  # noqa: BLE001
        print(f"Advertencia: Wikipedia inaccesible ({exc}). Sin enriquecimiento de partido.")

    # --- Merge: BCN SIIT como base, Wikipedia como enriquecimiento ---
    filas: list[dict[str, str | None]] = []
    for comuna_bcn, datos_bcn in filas_bcn.items():
        wp = wikidata.get(comuna_bcn, {})
        nombre = datos_bcn["nombre"]  # BCN SIIT es la fuente autoritativa del nombre
        if not nombre:
            # Fallback: si BCN SIIT no tiene nombre, usar Wikipedia
            nombre = wp.get("nombre_wikipedia")
        filas.append(
            {
                "comuna": comuna_bcn,
                "nombre": nombre,
                "periodo_inicio": wp.get("periodo_inicio"),
            }
        )

    # Si BCN SIIT falló completamente, usar solo Wikipedia (modo degradado)
    if not filas_bcn:
        for title, wikitext in wikitext_por_titulo.items():
            nombre, inicio = _extract_alcalde_actual(wikitext)
            filas.append(
                {
                    "comuna": _comuna_name_from_title(title),
                    "nombre": nombre,
                    "periodo_inicio": inicio,
                }
            )

    return filas


def fetch_gobernadores() -> list[dict[str, str]]:
    """Extrae (region, nombre, partido, pacto) de la tabla de Wikipedia vía Scrapling.

    Cada fila de datos trae, como enlaces: región, titular, partido y coalición. Si la
    obtención falla, retorna ``[]`` (el extractor no rompe).
    """
    try:
        from scrapling.fetchers import Fetcher

        page = Fetcher.get(GOBERNADORES_URL, stealthy_headers=True)
        tables = page.css("table.wikitable")
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener gobernadores ({exc}). Se omiten.")
        return []
    if not tables:
        print("Advertencia: Wikipedia no expuso la tabla de gobernadores.")
        return []
    filas = []
    for row in tables[0].css("tr"):
        if not row.css("td"):
            continue
        links = [
            (a.attrib.get("title", "").strip(), a.text.strip())
            for a in row.css("a")
            if a.attrib.get("title")
        ]

        # links: región (título "Gobernador(a) regional|metropolitano de X"), luego
        # titular, partido y coalición. La región se toma del *título* (completo), no del
        # texto del enlace (que puede venir truncado).
        region = ""
        resto = []
        for title, text in links:
            reg = _region_from_title(title)
            if reg and not region:
                region = reg
            else:
                resto.append((title, text))
        if not region or not resto:
            continue
        nombre = resto[0][1]
        partido = resto[1][0] if len(resto) > 1 else ""
        pacto = resto[2][1] if len(resto) > 2 else ""
        filas.append({"region": region, "nombre": nombre, "partido": partido, "pacto": pacto})
    return filas


def _normalize_gobernadores(
    gobernadores: list[dict[str, str]], fecha_consulta: str
) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    for g in gobernadores:
        region = g["region"].strip()
        codigo_region = REGION_A_CODIGO.get(norm_text(region))
        rows.append(
            {
                "id_autoridad": f"gobernador_{codigo_region or norm_text(region).replace(' ', '_')}",
                "nombre": g["nombre"].strip(),
                "cargo": "gobernador_regional",
                "institucion": f"Gobierno Regional de {region}",
                "partido": g.get("partido") or None,
                "pacto": g.get("pacto") or None,
                "distrito_electoral": None,
                "circunscripcion_senatorial": None,
                "codigo_comuna": None,
                "codigo_region": codigo_region,
                "periodo_inicio": None,
                "periodo_fin": None,
                "estado_mandato": "vigente",
                "fuente": "Wikipedia (CC-BY-SA)",
                "url_fuente": GOBERNADORES_URL,
                "fecha_consulta": fecha_consulta,
            }
        )
    return rows


def _load_comunas_lookup() -> dict[str, tuple[str, str]]:
    """``nombre_comuna_clean -> (codigo_comuna, codigo_region)`` desde staging/comunas.csv.

    Retorna ``{}`` si el archivo no existe (permite ejecutar el extractor de forma
    aislada; el cruce a `codigo_comuna` queda nulo en ese caso, sin romper)."""
    comunas_path = Path(STAGING_DIR) / "comunas.csv"
    if not comunas_path.exists():
        return {}
    df = pl.read_csv(
        comunas_path, schema_overrides={"codigo_comuna": pl.String, "codigo_region": pl.String}
    )
    return {
        row["nombre_comuna_clean"]: (row["codigo_comuna"], row["codigo_region"])
        for row in df.iter_rows(named=True)
    }


def fetch_alcalde_bcn(codigo_comuna: str) -> str | None:
    """Obtiene el nombre del alcalde para una comuna desde BCN SIIT.

    Args:
        codigo_comuna: Código único territorial (CUT) de 5 dígitos.

    Returns:
        Nombre del alcalde en formato "Apellido1 Apellido2 Nombres", o None
        si la página no contiene el campo o hay error de red.
    """
    params = {"anno": BCN_SIIT_ANNO, "idcom": codigo_comuna}
    try:
        resp = fetch_with_retry(BCN_SIIT_URL, params=params, headers=_BCN_HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Advertencia: BCN SIIT inaccesible para comuna {codigo_comuna} ({exc}).")
        return None

    match = re.search(
        r"<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>",
        resp.text,
        re.I,
    )
    if not match:
        return None
    nombre = match.group(1).strip()
    # Limpiar entidades HTML y espacios múltiples
    nombre = nombre.replace("&nbsp;", " ").replace("\xa0", " ")
    nombre = re.sub(r"\s+", " ", nombre).strip()
    if not nombre or nombre.lower() in ("", "vacante", "no disponible"):
        return None
    return nombre


def fetch_alcaldes_bcn(
    comunas_lookup: dict[str, tuple[str, str]],
    max_workers: int = 6,
) -> list[dict[str, str | None]]:
    """Obtiene alcaldes desde BCN SIIT para todas las comunas del lookup.

    Args:
        comunas_lookup: ``{nombre_comuna_clean: (codigo_comuna, codigo_region)}``
        max_workers: Número máximo de requests concurrentes.

    Returns:
        Lista de ``{comuna, nombre, periodo_inicio}`` con todas las comunas
        para las que BCN SIIT devolvió un nombre. Las comunas sin alcalde
        identificable se incluyen con ``nombre=None``.
    """
    # Construir lista de (comuna_nombre, codigo_comuna) únicos
    # (comunas_lookup tiene 346 entradas; filtrar solo las 345 comunas reales)
    tareas: list[tuple[str, str, str]] = []
    for nombre_comuna, (codigo, region) in comunas_lookup.items():
        # Excluir entradas que no son comunas reales (ej. "chile")
        if codigo and len(codigo) == 5 and codigo != "00000":
            tareas.append((nombre_comuna, codigo, region))

    resultado: dict[str, str | None] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_a_codigo = {
            executor.submit(fetch_alcalde_bcn, codigo): (nombre, codigo, region)
            for nombre, codigo, region in tareas
        }
        for future in concurrent.futures.as_completed(future_a_codigo):
            nombre_comuna, codigo, region = future_a_codigo[future]
            try:
                alcalde = future.result()
            except Exception as exc:
                print(f"Advertencia: error obteniendo alcalde de {nombre_comuna} ({codigo}): {exc}")
                alcalde = None
            resultado[nombre_comuna] = alcalde

    return [
        {"comuna": comuna, "nombre": nombre, "periodo_inicio": None}
        for comuna, nombre in resultado.items()
    ]


def _normalize_alcaldes(
    alcaldes: list[dict[str, str | None]],
    comunas_lookup: dict[str, tuple[str, str]],
    fecha_consulta: str,
) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    for a in alcaldes:
        comuna = (a.get("comuna") or "").strip()
        if not comuna:
            continue
        codigo_comuna, codigo_region = comunas_lookup.get(norm_text(comuna), (None, None))
        nombre = a.get("nombre")
        rows.append(
            {
                "id_autoridad": f"alcalde_{codigo_comuna or norm_text(comuna).replace(' ', '_')}",
                "nombre": nombre,
                "cargo": "alcalde",
                "institucion": f"Municipalidad de {comuna}",
                "partido": None,
                "pacto": None,
                "distrito_electoral": None,
                "circunscripcion_senatorial": None,
                "codigo_comuna": codigo_comuna,
                "codigo_region": codigo_region,
                "periodo_inicio": a.get("periodo_inicio"),
                "periodo_fin": None,
                "estado_mandato": "vigente" if nombre else "sin_identificar",
                "fuente": "BCN SIIT",
                "url_fuente": f"https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno={BCN_SIIT_ANNO}&idcom={codigo_comuna or ''}",
                "fecha_consulta": fecha_consulta,
            }
        )
    return rows


def build_autoridades_locales_df(
    gobernadores: list[dict[str, str]],
    alcaldes: list[dict[str, str | None]] | None = None,
    comunas_lookup: dict[str, tuple[str, str]] | None = None,
) -> pl.DataFrame:
    """Construye el DataFrame canónico de autoridades locales (gobernadores + alcaldes)."""
    fecha = datetime.datetime.now(UTC).date().isoformat()
    rows = _normalize_gobernadores(gobernadores, fecha)
    rows += _normalize_alcaldes(alcaldes or [], comunas_lookup or {}, fecha)
    df = pl.DataFrame(rows, schema=SCHEMA)
    return df.unique(subset=["id_autoridad"], keep="first").sort(["cargo", "id_autoridad"])


class AutoridadesLocalesExtractor(BaseExtractor):
    """Extractor de autoridades locales (gobernadores + alcaldes, ambos CC-BY-SA)."""

    @property
    def dataset_name(self) -> str:
        return "autoridades_locales"

    def fetch(self, **kwargs) -> dict[str, object]:
        return {
            "gobernadores": fetch_gobernadores(),
            "alcaldes": fetch_alcaldes(),
            "comunas_lookup": _load_comunas_lookup(),
        }

    def normalize(self, raw_data: dict[str, object]) -> pl.DataFrame:
        gobernadores = raw_data.get("gobernadores") or []
        alcaldes = raw_data.get("alcaldes") or []
        comunas_lookup = raw_data.get("comunas_lookup") or {}
        assert isinstance(gobernadores, list)
        assert isinstance(alcaldes, list)
        assert isinstance(comunas_lookup, dict)
        return build_autoridades_locales_df(gobernadores, alcaldes, comunas_lookup)

    def validate(self, df: pl.DataFrame, metadata: dict) -> dict:
        errors = []
        n_gob = df.filter(pl.col("cargo") == "gobernador_regional").height
        if n_gob and n_gob != EXPECTED_GOBERNADORES:
            errors.append(f"Gobernadores esperados {EXPECTED_GOBERNADORES}, obtenidos {n_gob}.")
        n_comunas_alcalde = df.filter(pl.col("cargo") == "alcalde")["codigo_comuna"].n_unique()
        if n_comunas_alcalde and n_comunas_alcalde > EXPECTED_COMUNAS_ALCALDES:
            errors.append(
                f"Comunas con alcalde ({n_comunas_alcalde}) excede el total de comunas "
                f"({EXPECTED_COMUNAS_ALCALDES})."
            )
        if df["id_autoridad"].n_unique() != df.height:
            errors.append("id_autoridad no es único.")
        personales = {"rut", "run", "domicilio", "fecha_nacimiento"}
        if personales & {c.lower() for c in df.columns}:
            errors.append("El dataset contiene columnas de datos personales (línea roja).")
        return {"status": "error" if errors else "ok", "errors": errors, "record_count": df.height}

    def write_staging(self, df: pl.DataFrame, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


def process_autoridades_locales() -> str:
    """Ejecuta el extractor standalone."""
    ensure_staging_directories()
    extractor = AutoridadesLocalesExtractor()
    raw = extractor.fetch()
    df = extractor.normalize(raw)
    validation = extractor.validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validación fallida: {validation['errors']}")

    n_gob = df.filter(pl.col("cargo") == "gobernador_regional").height
    alcaldes_df = df.filter(pl.col("cargo") == "alcalde")
    n_comunas = alcaldes_df.height
    n_con_titular = alcaldes_df.filter(pl.col("nombre").is_not_null()).height
    if n_comunas and n_con_titular < MIN_ALCALDES_CON_TITULAR:
        print(
            f"Advertencia: solo {n_con_titular}/{n_comunas} comunas con alcalde identificado "
            f"(mínimo esperado {MIN_ALCALDES_CON_TITULAR}). Revisar BCN SIIT."
        )
    metadata = {
        "dataset": "autoridades_locales",
        "source_name": "BCN SIIT + Wikipedia (CC-BY-SA)",
        "source_url": BCN_SIIT_URL,
        "source_mode": "live",
        "source_detail": (
            "Alcaldes: BCN SIIT (reportescomunales, fuente oficial del Congreso, "
            "345 comunas). Gobernadores: Wikipedia 'Gobernador regional de Chile' "
            "(Scrapling, CC-BY-SA)."
        ),
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            f"gobernador_regional: {n_gob}/{EXPECTED_GOBERNADORES}.",
            f"alcalde: {n_comunas} comunas procesadas desde BCN SIIT, {n_con_titular} "
            "con alcalde identificado (fuente oficial del Congreso Nacional).",
            "BCN SIIT es dato público gubernamental chileno; sin restricción de "
            "licencia para datos factuales de autoridades.",
        ],
        "reuse_policy": REUSE_POLICY,
    }
    extractor.write_staging(df, metadata)
    print(
        f"Autoridades locales guardadas en: {STAGING_CSV_PATH} "
        f"({df.height} registros: {n_gob} gobernadores, {n_comunas} comunas con alcalde "
        f"procesadas, {n_con_titular} con titular identificado)"
    )
    return STAGING_CSV_PATH


if __name__ == "__main__":
    process_autoridades_locales()
