"""Extractor de autoridades locales de Chile (Plan 023 · Ola A, dataset separado).

Dataset **`autoridades_locales`**, aislado de `autoridades_electas` porque su fuente es
**Wikipedia (CC-BY-SA)** — no debe contaminar la licencia CC-BY de los cargos oficiales.

v1 (carril `candidate`): cargos **gobernador_regional** (16, tabla vía Scrapling) y
**alcalde** (345 comunas, vía la API pública de MediaWiki — sin Scrapling: es una API
abierta de solo lectura, no bloquea como camara.cl/senado.cl).

Método para alcaldes: la página índice "Anexo:Alcaldes de Chile" enlaza a 345
subpáginas ("Anexo:Alcaldes de <comuna>"), una por comuna — no hay tabla única. Se
listan sus títulos (1 request) y se descarga su wikitext en lotes de 50 (~7 requests).
De las 345 comunas enlazadas, ~224 tienen página propia (el resto son enlaces rojos:
páginas no creadas, típicamente comunas rurales pequeñas — una limitación real de la
fuente, no un bug de este extractor). El alcalde vigente se extrae del campo
``titular=`` del infobox `{{Ficha de cargo...}}` (cubre ~165/224 páginas existentes; el
nombre de la plantilla varía: "Ficha de cargo", "Ficha de cargo politico/político"). Si
no hay infobox, se intenta un fallback: la última fila de la tabla histórica marcada
explícitamente como vigente ("en el cargo", "en ejercicio", "actualidad"); si tampoco
hay marca explícita, el alcalde queda **nulo** para esa comuna — no se inventa un
titular sin evidencia (algunas comunas están efectivamente acéfalas/vacantes, ver
Antofagasta 2024). La cobertura real se documenta en el metadata (``notes``).

Solo cargos públicos; **sin datos personales**. Mismo esquema que `autoridades_electas`.
"""

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
EXPECTED_COMUNAS_ALCALDES = 345
# Cobertura mínima aceptable del campo "alcalde vigente" (best-effort; ver notas del
# módulo). Observado en la práctica (2026-07-06): de las 345 comunas enlazadas desde el
# índice, ~224 tienen página propia en Wikipedia (el resto son enlaces rojos — páginas
# no creadas, típicamente comunas rurales pequeñas), y de esas ~165 exponen un alcalde
# identificable. El umbral deja margen bajo ese piso real; una caída por debajo indica
# un cambio estructural en Wikipedia, no la ausencia esperable de páginas.
MIN_ALCALDES_CON_TITULAR = 140

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
    """Lista de ``{comuna, nombre, periodo_inicio}`` para las comunas con alcalde
    identificado. Si la obtención falla por completo, retorna ``[]`` (degradación)."""
    try:
        titles = fetch_alcalde_titles()
        wikitext_por_titulo = fetch_alcaldes_wikitext(titles)
    except Exception as exc:  # noqa: BLE001 — degradación intencional
        print(f"Advertencia: no se pudo obtener alcaldes ({exc}). Se omiten.")
        return []
    filas: list[dict[str, str | None]] = []
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
                "fuente": "Wikipedia (CC-BY-SA)",
                "url_fuente": f"https://es.wikipedia.org/wiki/Anexo:Alcaldes_de_{comuna.replace(' ', '_')}",
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
            f"(mínimo esperado {MIN_ALCALDES_CON_TITULAR}). Revisar cambios de estructura en Wikipedia."
        )
    metadata = {
        "dataset": "autoridades_locales",
        "source_name": "Wikipedia (CC-BY-SA)",
        "source_url": GOBERNADORES_URL,
        "source_mode": "live",
        "source_detail": (
            "Wikipedia 'Gobernador regional de Chile' (Scrapling) + "
            "'Anexo:Alcaldes de Chile' (API MediaWiki, 345 subpáginas)"
        ),
        "refreshed_at_utc": datetime.datetime.now(UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [
            f"gobernador_regional: {n_gob}/{EXPECTED_GOBERNADORES}.",
            f"alcalde: {n_comunas} comunas procesadas, {n_con_titular} con alcalde "
            "identificado (best-effort: infobox 'titular=' o última fila de tabla "
            "marcada explícitamente como vigente; sin marca clara queda nulo — no se "
            "inventa un titular, ver docs/datasets/autoridades_locales.md).",
            "Fuente Wikipedia CC-BY-SA: dataset segregado para no propagar share-alike.",
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
