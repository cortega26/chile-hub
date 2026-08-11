"""Resolución de la raíz del proyecto y rutas canónicas del paquete.

TECHDEBT-05: antes cada módulo resolvía la raíz con su propio idioma
(``parents[2]`` en core/contracts/__init__, ``_find_root()`` en
pipeline_status_utils). Este módulo es la fuente única para el paquete
``chile_hub``: busca ``pyproject.toml`` como sentinel, con fallback a
``parents[2]`` para la wheel instalada (donde solo se usan rutas de reportes
que no dependen de disco).

Nota: ``ChileHub.root_dir`` (instancia) es OTRASEMANTICA — es la raíz del
directorio de datos del consumidor (donde vive el bundle descargado), no la
raíz del proyecto. No reemplazar una por la otra.
"""

from __future__ import annotations

from pathlib import Path


def _is_chile_hub_pyproject(path: Path) -> bool:
    """True si el pyproject.toml declara el paquete chile-hub.

    El sentinel no puede ser solo la presencia de ``pyproject.toml``: en un
    entorno instalado (wheel dentro del .venv del consumidor), el ascenso
    desde site-packages alcanza el pyproject.toml del proyecto CONSUMIDOR y
    lo aceptaría como raíz, reportando su versión como ``chile_hub.__version__``
    y resolviendo ROOT_DIR/NORMALIZED_DIR contra su árbol. Se exige que el
    archivo declare ``name = "chile-hub"``.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return 'name = "chile-hub"' in text


def find_root() -> Path:
    """Localiza la raíz del proyecto buscando el pyproject.toml de chile-hub.

    Funciona desde ``src/chile_hub/`` (wheel empaquetado o checkout) y desde
    ``src/`` (importaciones de build_dev_db.py). En un entorno instalado sin
    el pyproject del proyecto (p. ej. el .venv de un consumidor), devuelve un
    fallback razonable.
    """
    current = Path(__file__).resolve().parent
    for _ in range(6):
        candidate = current / "pyproject.toml"
        if candidate.exists() and _is_chile_hub_pyproject(candidate):
            return current
        current = current.parent
    # Fallback para rueda instalada: parents[2] desde src/chile_hub/ da
    # site-packages/, que no es la raíz real pero es inocuo porque en
    # ese contexto solo se usan rutas de reportes (ninguna depende de
    # paths en disco).
    return Path(__file__).resolve().parents[2]


ROOT_DIR = find_root()
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
