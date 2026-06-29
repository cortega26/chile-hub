"""Renderizado de tablas de la CLI con rich.

Devuelve texto plano (box-drawing Unicode, sin ANSI) para que la salida sea
estable en tests y en pipes. El color es un follow-up deferido.
"""

from __future__ import annotations

import io
from typing import Sequence

from rich.console import Console
from rich.table import Table


def render_table(
    title: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    width: int = 120,
) -> str:
    """Renderiza una tabla a texto plano, precedida por *title*.

    El título se emite tal cual en la primera linea (los tests lo verifican por
    subcadena). La tabla se renderiza sin color para mantener la salida estable.
    """
    table = Table(show_edge=True, expand=False)
    for header in headers:
        table.add_column(header, overflow="fold")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    buffer = io.StringIO()
    console = Console(
        file=buffer,
        width=width,
        force_terminal=False,  # sin ANSI
        no_color=True,
        highlight=False,
    )
    console.print(table)
    return f"{title}\n\n{buffer.getvalue()}"
