"""Ejecuta los notebooks de `examples/notebooks/` contra el bundle publicado.

Los notebooks se commitean con outputs para que GitHub y Colab muestren
resultados sin ejecutar nada. Este script los refresca con `nbconvert
--execute` en un entorno efímero de uv (sin tocar `pyproject.toml`/`uv.lock`):
usa `chile-hub` de PyPI, que descarga el bundle validado desde GitHub Releases.

Uso:
  python scripts/refresh_notebooks.py                 # todos
  python scripts/refresh_notebooks.py examples/notebooks/01_comunas_censo.ipynb

Requiere `uv` y acceso a PyPI/GitHub Releases. No corre en CI: los outputs
dependen de datos live y se regeneran a mano tras cambios en los notebooks.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT_DIR / "examples" / "notebooks"

EPHEMERAL_PACKAGES = [
    "nbconvert>=7,<8",
    "ipykernel>=6,<7",
    "matplotlib>=3.8,<4",
    "pip",
    "chile-hub",
]


def refresh_notebook(path: Path) -> None:
    cmd = [
        "uv",
        "run",
        "--no-project",
        *[f"--with={package}" for package in EPHEMERAL_PACKAGES],
        "python",
        "-m",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        str(path),
    ]
    print(f"[refresh] ejecutando {path.relative_to(ROOT_DIR)}")
    subprocess.run(cmd, check=True, cwd=ROOT_DIR)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebooks",
        nargs="*",
        help="Rutas de notebooks a refrescar (default: todos los de examples/notebooks/)",
    )
    args = parser.parse_args(argv)

    if args.notebooks:
        paths = [Path(p) for p in args.notebooks]
    else:
        paths = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))

    if not paths:
        print("refresh_notebooks: no se encontraron notebooks", file=sys.stderr)
        return 1

    for path in paths:
        if not path.is_file():
            print(f"refresh_notebooks: no existe {path}", file=sys.stderr)
            return 1
        refresh_notebook(path)

    print(f"refresh_notebooks: {len(paths)} notebooks actualizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
