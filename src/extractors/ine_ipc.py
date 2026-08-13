"""Override de IPC desde la fuente autoritativa (INE).

mindicador.cl dejó de publicar la serie IPC en diciembre de 2025 (issue #43);
el INE es la fuente original del índice y publica la variación mensual en su
página pública. Este módulo replica el patrón validado del proyecto Monedario
(`workers/economic-snapshot-refresh/src/sources/ineIpc.ts`, observado estable
desde 2026-05-16): ancla el match al encabezado <h1> del IPC para no tomar la
tarjeta de un índice hermano (ICT/IPP) si el INE reordena el layout.

Política anti-scraping del repo (AGENTS.md §5/§10): esto es un override de
último recurso, no la fuente principal. La fuente principal sigue siendo
mindicador.cl; solo cuando una serie mensual esperada llega vacía o falla se
consulta al INE. El HTML no se república: se extrae el dato y su fecha.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

INE_IPC_URL = (
    "https://www.ine.gob.cl/estadisticas-por-tema/precios-e-inflacion/"
    "indice-de-precios-al-consumidor"
)

SPANISH_MONTHS = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

_MONTH_PATTERN = "|".join(SPANISH_MONTHS)

# Acotación del par cifra/periodo (Plan 075): el span entre el h1 del IPC,
# su cifra y su período no puede cruzar el cierre de un contenedor
# (`</div>`), de modo que el valor de una tarjeta nunca se case con el
# período de otra si el INE reordena el layout. Permite tags internos
# (`<p>`, `<br>` — el fixture real tiene `</p><p>` entre cifra y período,
# así que `[^<]` rompería el parseo) y admite hasta 500 chars de holgura:
# la tarjeta real ocupa ~57. Si el INE separa cifra y período en bloques
# distintos, este patrón deja de matchear y el override degrada — es la
# primera alerta del rediseño, no un valor erróneo silencioso.
_ACOTADO = r"(?:(?!</div>)[\s\S]){0,500}"

# Anclado al <h1> del IPC; el par cifraV3/periodoCifraV3 siguiente es el del
# propio IPC (mismo contenedor, span acotado), no el de una tarjeta hermana.
# Tolerante a tildes y a clases adicionales (p. ej. `class="cifraV3 highlight"`).
_PATTERN = re.compile(
    rf"<h1[^>]*>[^<]*[ÍI]ndice\s+de\s+Precios\s+al\s+Consumidor[^<]*</h1>"
    rf"{_ACOTADO}<p[^>]*class=\"[^\"]*\bcifraV3\b[^\"]*\"[^>]*>\s*(-?\d+(?:[,.]\d+)?)\s*%\s*</p>"
    rf"{_ACOTADO}<p[^>]*class=\"[^\"]*\bperiodoCifraV3\b[^\"]*\"[^>]*>\s*Variaci[oó]n\s+mensual\s+"
    rf"({_MONTH_PATTERN})\s+(\d{{4}})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IneIpcReading:
    """Variación mensual del IPC publicada por el INE."""

    value: float
    date_iso: str


def parse_ine_ipc(html: str) -> IneIpcReading | None:
    """Extrae (valor %, fecha YYYY-MM-01) del HTML de la página del IPC.

    Retorna ``None`` si el patrón no matchea (página rediseñada, tarjeta
    ausente, valor no numérico).
    """
    match = _PATTERN.search(html)
    if not match:
        return None
    raw_value = match.group(1).replace(",", ".")
    try:
        value = float(raw_value)
    except ValueError:
        return None
    month_name = match.group(2).lower()
    month_number = SPANISH_MONTHS.get(month_name)
    if month_number is None:
        return None
    return IneIpcReading(value=value, date_iso=f"{match.group(3)}-{month_number}-01")


def fetch_ine_ipc(
    *,
    timeout: int = 30,
    url: str = INE_IPC_URL,
    get_html=None,
) -> IneIpcReading | None:
    """Descarga la página del IPC del INE y extrae la variación mensual.

    Args:
        timeout: Timeout HTTP (el sitio gov responde lento, ver issue #43).
        url: URL de la página (override para tests).
        get_html: Callable(url) -> str | None para inyectar el fetch en tests.
            Por defecto usa requests con headers browser-like (el INE responde
            403 a UAs por defecto de algunas librerías).

    Returns:
        IneIpcReading o None si el fetch o el parseo fallan (degradación
        silenciosa: el llamador decide qué hacer).
    """
    if get_html is None:
        import requests

        def _default_get(target_url: str) -> str | None:
            try:
                resp = requests.get(
                    target_url,
                    timeout=timeout,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                        ),
                        "Accept": "text/html,application/xhtml+xml",
                        "Referer": "https://www.ine.gob.cl/",
                    },
                )
                resp.raise_for_status()
                return resp.text
            except Exception:
                return None

        get_html = _default_get

    html = get_html(url)
    if not html:
        return None
    return parse_ine_ipc(html)
