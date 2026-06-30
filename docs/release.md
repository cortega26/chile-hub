# Proceso de publicación

`chile-hub` publica lanzamientos de software en PyPI y actualizaciones de datos
como artefactos normalizados verificados. Estos son flujos relacionados pero
intencionalmente separados.

## CHANGELOG

`CHANGELOG.md` se actualiza automáticamente en cada release mediante
`python-semantic-release`. La configuración `[tool.semantic_release.changelog]`
en `pyproject.toml` usa `mode = "update"`: PSR antepone la nueva sección al
archivo en el mismo commit de release (`chore(release): X.Y.Z`).

**Entradas auto-generadas:** los encabezados de sección siguen la convención de
Conventional Commits (en inglés), pero el cuerpo de cada entrada reproduce el
mensaje de commit tal como fue escrito. Las entradas manuales curadas que
anteceden a la versión 1.15.0 se conservan sin cambios.

**Filtros activos** (commits excluidos del changelog):
- `chore(data):` — actualizaciones diarias de datos
- `chore(release):` — commits del propio PSR
- `docs(backlog):` y `docs(plans):` — documentación interna de backlog

## Versionado

Usa Conventional Commits:

- `fix:` incrementa PATCH.
- `feat:` incrementa MINOR.
- `feat!:` o `BREAKING CHANGE:` incrementa MAJOR.
- `docs:`, `test:`, `style:` y los commits de actualización de datos no
  publican por defecto.

La versión canónica del software es `project.version` en `pyproject.toml`.
`python-semantic-release` la actualiza, crea un Git tag, crea un GitHub
Release, compila el wheel y la source distribution, y publica a través de
PyPI Trusted Publishing.

## TestPyPI

Usa el flujo manual `TestPyPI Package Smoke` antes de habilitar un lanzamiento
de producción para un cambio importante en el empaquetado. Compila el paquete,
lo publica en TestPyPI, instala el wheel en un entorno limpio, importa
`chile_hub` y ejecuta `chile-hub --help`.

## Cobertura

Las verificaciones locales de cobertura usan `make coverage`, que ejecuta
`pytest-cov` sobre `src/` y escribe tanto un reporte de terminal
`term-missing` como `coverage.xml`. El flujo principal del pipeline ejecuta el
mismo comando de cobertura durante las pruebas unitarias y de contrato, por lo
que los release candidates incluyen la señal de cobertura usada localmente.

## Producción PyPI

El flujo `PyPI Release` se ejecuta al hacer push a `main`. Omite los commits
con `[skip ci]`, calcula la siguiente versión a partir de Conventional Commits,
publica a través de OIDC Trusted Publishing y adjunta el paquete de datos
verificado más reciente junto con los metadatos al GitHub Release.

## Actualizaciones solo de datos

Las actualizaciones programadas de datos continúan usando el flujo del
pipeline. Validan los datos en vivo, actualizan `data/normalized/` y realizan
un commit con:

```text
chore(data): daily refresh [skip ci]
```

Estos commits no crean una nueva versión en PyPI.

## Notas de release legibles para humanos

Además del changelog automático, cada release **minor** y **major** lleva un bloque
narrativo escrito por un humano en `CHANGELOG.md`. El bloque usa el formato:

```
> 🎯 **Resumen:** uno a tres párrafos que cuentan *por qué* el release importa,
> cómo se conecta con la dirección del proyecto, y qué significa para quien lo lee.
```

**Cuándo se escribe:**
- Releases **minor** (`feat:`) y **major** (`feat!:` / `BREAKING CHANGE:`): **siempre**.
- Releases **patch** (`fix:`): **no llevan** resumen narrativo. El diff auto-generado
  es suficiente.

**Dónde se coloca:**
- Justo después de la línea `## X.Y.Z - FECHA`, antes de los encabezados categorizados
  (`### Agregado`, `### Corregido`, etc.).
- La lista categorizada que sigue es la bitácora automática de `python-semantic-release`;
  el resumen es la capa humana.

**Qué cubre el resumen:**
- El arco narrativo: qué problema resuelve este release en el contexto del proyecto.
- Conexión con planes activos (p. ej. "Este release completa el Plan 018…").
- Cambios de dirección o decisiones visibles para quien sigue el proyecto.
- NO es un duplicado de la lista de commits; es el *por qué*, no el *qué*.

**Quién lo escribe:**
- El mantenedor, al momento de hacer el release o justo después. El bloque se añade
  manualmente a `CHANGELOG.md` tras la publicación automática. Como PSR usa `mode = "update"`
  (antepone contenido), las notas de releases anteriores no se tocan.

**Convención de idioma:**
- Los resúmenes narrativos van en **español neutral**, como el resto de la documentación
  del proyecto. Las categorías auto-generadas por PSR heredan el idioma de los mensajes
  de commit (inglés o español, según como se escribieron).
