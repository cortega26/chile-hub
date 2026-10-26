# Navegación MCP para agentes — CodeGraph + Serena

Esta política cubre **agentes de desarrollo dentro de chile-hub**. La fuente
canónica sigue siendo `SOURCE_OF_TRUTH.md` → `AGENTS.md`; las invariantes del
pipeline y los controles de publicación no se transfieren a ningún MCP.

## Decisión por operación: una herramienta primaria

| Necesidad | Primera opción | Recuperación |
| --- | --- | --- |
| Arquitectura, dependencias, rutas de llamadas, impacto transversal | CodeGraph `codegraph_explore` | `rg` y lectura limitada cuando el índice/MCP no funcione |
| Definición/referencias de símbolo, cambios de función y renombrado semántico | Serena (LSP) | Edición nativa limitada más comprobación explícita |
| Literal, archivo de datos, metadatos, YAML/JSON, documentación | Herramientas nativas | MCP solo ante necesidad estructural real |
| Refactorización que afecta varias capas | CodeGraph (mapa/impacto) → Serena (cambio) | Revisión dirigida y pruebas |

Evita buscar lo mismo con ambos sistemas sin evidencia contradictoria o contexto
insuficiente. No uses Serena para repetir capacidades nativas de lectura de
archivos, ejecución de shell o regex: el contexto `ide` minimiza esas
herramientas. La memoria de Serena no debe crear una segunda fuente de verdad
frente a `AGENTS.md`, catálogo de datasets o contratos. No inicialices
automáticamente un CodeGraph nuevo sin revisar su configuración. Los resultados
semánticos no demuestran que el pipeline conserve sus invariantes.

## Activación local

- **OpenCode 1.x:** `opencode.json` registra CodeGraph y Serena por proyecto
  con el esquema `mcp.<nombre>`. OpenCode v2 usa `mcp.servers.<nombre>`:
  comprobar la versión instalada antes de migrar, sin mantener ambos esquemas.
- **VS Code:** `.vscode/mcp.json` contiene los mismos dos MCP en formato
  workspace, con `cwd` limitado a la carpeta abierta.
- Ambos ejecutan `codegraph serve --mcp` y
  `serena start-mcp-server --context ide --project-from-cwd` en stdio.
  Serena no abre el dashboard automáticamente.
- **Instalar prerrequisitos fuera del repositorio:** disponer de `codegraph`
  e inicializar/sincronizar su índice cuando corresponda; instalar Serena con
  `uv tool install -p 3.13 serena-agent` y `serena init`.
- `.serena/` es caché/memoria local no canónica: no debe versionarse.
- Evita entradas MCP duplicadas en configuraciones globales del mismo cliente.
  Mantén el daemon compartido habitual de CodeGraph para que varios clientes
  no compitan por escribir su índice; no dupliques procesos directos por proyecto.

Comprueba que ambos aparecen en `opencode mcp list` (OpenCode 1.x) o en
**MCP: List Servers** de VS Code. Prueba, sin editar nada, que CodeGraph
resuelve una dependencia del pipeline y Serena encuentra un símbolo conocido
de `src/extractors/`. Si falla una herramienta, vuelve a las herramientas
nativas e informa del problema: nunca declares una instalación funcional
basándote solo en la configuración versionada.

## Criterios de aceptación

1. Paridad de servidores y aislamiento por proyecto entre ambos clientes
   (cubierto por `tests/test_agent_mcp_configuration.py`).
2. Ensayo comparativo controlado sobre el mismo SHA con tareas de búsqueda
   de llamadas, impacto, edición simbólica y refactorización; comparar tokens,
   invocaciones, latencia, exactitud y regresiones. No atribuir mejoras sin
   medirlas.
3. Toda modificación de código sigue `AGENTS.md` y los comandos relevantes
   (`make doctor`, `make verify`, `make test`), sin descargar o publicar
   datos reales solo para demostrar la conexión MCP.
