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

> El servidor vive en el extra opcional `mcp` (`mcp>=2.2`): el paquete base
> `chile-hub` no trae sus dependencias, así que instala/ejecuta **siempre** con
> el extra (`chile-hub[mcp]` / `--from "chile-hub[mcp]"`). Sin él, el comando
> `chile-hub-mcp` falla al importar `mcp`.

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

## Registry oficial MCP

El repositorio incluye `server.json` en la raíz para el
[registry oficial](https://registry.modelcontextprotocol.io) (preview), con:

- `name: io.github.cortega26/chile-hub` (namespace verificado vía GitHub),
- `packages[0]`: `registryType: "pypi"`, `identifier: "chile-hub"`,
  `transport: "stdio"`.

**Verificación de propiedad (PyPI)**: el registry comprueba el namespace contra
GitHub y exige el marcador `mcp-name: io.github.cortega26/chile-hub` en el
README del paquete publicado en PyPI. Ese marcador vive en `README.md` (que es
la descripción en PyPI), así que hay que publicar **después** del primer
release que lo incluya.

**Runtime**: el registry instala `chile-hub` sin el extra `[mcp]`; `server.json`
no expresa extras de PyPI. Para levantar el servidor hay que instalar o
ejecutar con el extra (ver [Instalación](#instalación)):

```bash
pip install "chile-hub[mcp]"                                  # o
uvx --from "chile-hub[mcp]" chile-hub-mcp
```

Un paquete-alias `chile-hub-mcp` que declare el extra queda como follow-up si
el registry llega a exigir un entrypoint ejecutable para publicar.

### Publicación (operador)

```bash
# 1. Instalar mcp-publisher (Homebrew o el binario del release oficial)
brew install mcp-publisher

# 2. Autenticarse con OAuth de GitHub (namespace io.github.cortega26/*)
mcp-publisher login github

# 3. Validar server.json sin publicar (también: POST público a /v0.1/validate)
mcp-publisher validate

# 4. Publicar
mcp-publisher publish
```

Verificación posterior:

```bash
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.cortega26/chile-hub"
```

> `server.json` fija `version` al release vigente: revalidar en cada release que
> no quede stale respecto de `pyproject.toml`.
