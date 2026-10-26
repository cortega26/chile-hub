# Navegación MCP para agentes — CodeGraph + Serena

Esta política cubre **agentes de desarrollo dentro de chile-hub**. La fuente
canónica sigue siendo `SOURCE_OF_TRUTH.md` → `AGENTS.md`; las invariantes del
pipeline y los controles de publicación no se transfieren a ningún MCP.

## Decisión por operación: una herramienta primaria

| Necesidad | Primera opción | Recuperación |
| --- | --- | --- |
| Arquitectura, dependencias, rutas de llamadas, impacto transversal | CodeGraph `codegraph_explore` | `rg` y lectura limitada cuando el índice/MCP no funcione |
| Sitios exactos de referencia antes de un cambio, nombres sobrecargados, implementaciones | Serena (LSP) | `rg` con contexto y lectura acotada |
| Renombrado, borrado seguro, inserción o reemplazo de cuerpo de símbolo | Serena (LSP) | Edición nativa revisada más pruebas |
| Diagnósticos de tipos/compilador de un archivo | Serena `get_diagnostics_for_file` | `make typecheck` o el linter del área |
| Literal, archivo de datos, metadatos, YAML/JSON, documentación | Herramientas nativas | MCP solo ante necesidad estructural real |
| Refactorización que afecta varias capas | CodeGraph (mapa/impacto) → Serena (cambio) | Revisión dirigida y pruebas |

Regla por defecto: una herramienta primaria por pregunta. Consultar ambos MCP es
deliberado —no duplicación— en estos casos:

- **Nombre sobrecargado** (`main`, `run`, `validate`, `validate_*`, `build`): el
  match por nombre de CodeGraph mezcla definiciones homónimas y literales de test
  que parecen declaraciones; LSP resuelve import y scope. Contrasta el conteo de
  callers con un `grep -c` acotado antes de concluir impacto.
- **Antes de una mutación** (renombrar, borrar, reemplazo masivo): confirma los
  sitios con Serena y el mapa con CodeGraph. Un conteo de callers que no cuadra
  con `grep` se resuelve a favor de `grep`.
- **Índice stale o ausente:** el aviso de staleness de CodeGraph o la falta de
  `.codegraph/` (clon nuevo, worktree, CI) dejan a Serena y a las herramientas
  nativas como única fuente.

Nunca derives un `name_path` de Serena a partir de una coincidencia de CodeGraph:
la resolución por nombre puede apuntar a otra función del mismo archivo.
Resuélvelo primero con `find_symbol` y verifica la ruta real.

No uses Serena para repetir capacidades nativas de lectura de archivos,
ejecución de shell o regex: el contexto `ide` minimiza esas herramientas. La
memoria de Serena no debe crear una segunda fuente de verdad frente a
`AGENTS.md`, catálogo de datasets o contratos. No inicialices automáticamente
un CodeGraph nuevo sin revisar su configuración. Los resultados semánticos no
demuestran que el pipeline conserve sus invariantes: tras una mutación de
Serena, ejecuta `make doctor` y las pruebas del área.

**Límite compartido:** ningún MCP es autoridad sobre literales, esquemas,
contratos ni tablas de dispatch (`validations = {…}`,
`DATASET_CATALOG_CONFIG.extractor`, `COMPANION_RULES`). Esas preguntas se
responden con `rg`/lectura y se validan con `make doctor`, `sync_docs.py
--check`, `check_landing_sync.py` o `check_validation_registration.py`, no con
el grafo.

**Contención de herramientas:** Serena usa además `--agent-interface tools`
para evitar el REPL genérico y `--add-mode no-memories` para no exponer una
memoria paralela a la documentación canónica del repositorio.

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

**Superficie de herramientas:** esta política no deniega herramientas de Serena
ni de CodeGraph; el solapamiento real (`find_symbol`, `find_declaration`,
`get_symbols_overview`) es la vía de recuperación cuando no hay índice, y
`find_referencing_symbols`/`find_implementations` son el oráculo LSP frente a
los conteos por nombre de CodeGraph. Retirar capacidades exige el ensayo
comparativo del criterio 2 y conservar la paridad entre clientes (criterio 1).
