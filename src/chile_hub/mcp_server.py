"""Servidor MCP (stdio) de chile-hub — datos públicos de Chile para agentes.

Expone cuatro tools de sólo lectura sobre la capa HTTP estática
(`data/normalized/{capa}.parquet`): listar capas, leer filas, resolver nombres
de comuna a CUT y consultar indicadores económicos. No hay hosting, telemetría
ni escritura en disco: el servidor corre local en el cliente MCP.

El paquete `mcp` vive en el extra opcional `mcp`; este módulo lo importa de
forma perezosa para que `import chile_hub` siga funcionando sin él.

Uso:
  pip install "chile-hub[mcp]"
  chile-hub-mcp            # stdio, para configurar en Claude Desktop / VS Code
"""

from __future__ import annotations

from typing import Any

from . import __version__
from .mcp_tools import (
    DEFAULT_LIMIT,
    get_dataset,
    get_indicadores,
    list_datasets,
    resolve_comunas,
)

INSTALL_HINT = (
    "Falta el paquete 'mcp'. Instala con: pip install \"chile-hub[mcp]\" "
    '(o ejecuta: uvx --from "chile-hub[mcp]" chile-hub-mcp).'
)


def build_server() -> Any:
    """Construye el `MCPServer` con las cuatro tools registradas.

    Importa `mcp` aquí dentro: sin el extra, el error es explícito en vez de
    romper el import del paquete.
    """
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:  # pragma: no cover — depende del entorno
        raise SystemExit(INSTALL_HINT) from exc

    server = MCPServer(
        name="chile-hub",
        title="chile-hub — datos públicos de Chile",
        instructions=(
            "Capa de datos curada y validada sobre fuentes oficiales de Chile. "
            "Usa list_datasets para descubrir capas, resolve_comunas para "
            "traducir nombres a códigos CUT (clave de cruce), get_dataset para "
            "leer filas y get_indicadores para series económicas."
        ),
        version=__version__,
    )

    @server.tool(
        name="list_datasets",
        description="Lista las capas de datos disponibles con la URL de su Parquet público.",
    )
    def _list_datasets() -> list[dict[str, Any]]:
        return list_datasets()

    @server.tool(
        name="get_dataset",
        description=(
            "Devuelve las primeras filas de una capa (máximo 1000). "
            f"Default: {DEFAULT_LIMIT} filas."
        ),
    )
    def _get_dataset(nombre: str, limite: int = DEFAULT_LIMIT) -> dict[str, Any]:
        return get_dataset(nombre, limite=limite)

    @server.tool(
        name="resolve_comunas",
        description=(
            "Resuelve nombres de comuna (con tildes, ñ o mayúsculas) a su "
            "código CUT de 5 caracteres y nombre oficial."
        ),
    )
    def _resolve_comunas(nombres: list[str]) -> list[dict[str, Any]]:
        return resolve_comunas(nombres)

    @server.tool(
        name="get_indicadores",
        description=(
            "Serie de indicadores económicos (uf, dolar, euro, utm, ipc). "
            "Filtra por código y/o rango de fechas ISO (YYYY-MM-DD), inclusivo."
        ),
    )
    def _get_indicadores(
        codigo: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        limite: int = DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        return get_indicadores(
            codigo=codigo,
            desde=desde,
            hasta=hasta,
            limite=limite,
        )

    return server


def main() -> None:
    """Entry point del console script `chile-hub-mcp` (stdio)."""
    build_server().run()
