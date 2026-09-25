# Servidor MCP (para agentes)

chile-hub incluye un servidor **MCP** (Model Context Protocol) de sólo lectura
para que agentes de código —Claude Desktop/Code, Cursor, VS Code— consulten los
datasets sin escribir Python. Corre local por stdio: sin hosting, sin API
propia, sin telemetría y sin descargar el bundle (lee los Parquet de la capa
HTTP estática).

## Instalación

```bash
pip install "chile-hub[mcp]"
chile-hub-mcp
```

O sin instalar nada permanente, vía `uvx`:

```bash
uvx --from "chile-hub[mcp]" chile-hub-mcp
```

## Configuración

Claude Desktop (`claude_desktop_config.json`) y clientes compatibles:

```json
{
  "mcpServers": {
    "chile-hub": {
      "command": "uvx",
      "args": ["--from", "chile-hub[mcp]", "chile-hub-mcp"]
    }
  }
}
```

## Tools

| Tool | Qué hace | Parámetros |
|:---|:---|:---|
| `list_datasets` | Lista las capas disponibles y la URL de su Parquet | — |
| `get_dataset` | Primeras filas de una capa (máximo 1000) | `nombre`, `limite` |
| `resolve_comunas` | Nombres de comuna → código CUT de 5 caracteres | `nombres` (lista) |
| `get_indicadores` | Serie UF/dólar/euro/UTM/IPC | `codigo`, `desde`, `hasta`, `limite` |

Ejemplos de uso por el agente:

- `resolve_comunas(["Ñuñoa", "valparaiso"])` → `13120`, `05101`
- `get_indicadores(codigo="uf", desde="2026-01-01")`
- `get_dataset(nombre="censo_comunal", limite=5)`

> El servidor es de sólo lectura por diseño. Para SQL arbitrario usa la API
> Python (`ChileHub.sql()`) o DuckDB sobre los Parquet (ver
> [Acceso HTTP estático](http-access.md)).
