# Registro de cambios

Este proyecto usa Conventional Commits y `python-semantic-release` para generar
notas de lanzamiento para publicaciones en PyPI.

Los commits de actualización de datos, como `chore(data): daily refresh [skip ci]`, no
representan lanzamientos de software y se excluyen intencionalmente de las notas de lanzamiento.

## 1.4.0 - 2026-06-18

### Agregado

- Separación de carriles (`publication_track`) en el registro de fuentes: 11 datasets como `stable_publishable` y 4 como `candidate`.
- Restricción del empaquetado público: los datasets marcados como candidatas son excluidos del manifest oficial, del bundle ZIP público y del indexado general de descargas.
- Estructuración en `hub_bundle.json` para diferenciar claramente entre datasets públicos listos y datasets candidatos.

### Cambiado

- Refactorización de `verify_pipeline.py` para aplicar políticas de publicación inteligentes dependientes del carril asignado.

## 1.3.1 - 2026-06-18

### Agregado

- Creación de `source_adapter.py` para abstraer y unificar el comportamiento de los extractores de datasets candidatos.
- Enlaces de soporte y contacto del proyecto en la landing page y documentación.

### Corregido

- Corrección en la suite de pruebas eliminando la dependencia directa en snapshots `raw` locales.
- Aseguramiento de `pyarrow` como dependencia explícita requerida para la exportación y registro de Polars con DuckDB.

## 1.3.0 - 2026-06-18

### Agregado

- Registro unificado de fuentes (`data/source_registry.json`) con metadatos sobre madurez, políticas de fallback, cronograma de revisión y umbral de estancamiento.
- Contratos de esquema en formato JSON Schema (`contracts/datasets/*.schema.json`) para los 15 datasets activos.
- Generación de reportes automáticos de preparación (`source_readiness`) y calidad (`dataset_quality`) en formato JSON/Markdown con sus respectivas integraciones en API y CLI.
- Sistema de detección de estancamiento de datos (`verify_readiness`) según reglas diferenciadas por tipo de capa.
- Política de compatibilidad de datasets (`docs/dataset-compatibility-policy.md`) con cálculo automático de severidad de cambios de esquema (major/minor/patch/none).

### Cambiado

- Estandarización de toda la documentación y comentarios del código a español neutro.

## 1.2.2 - 2026-06-17

### Cambiado

- Sincronización dinámica de la insignia de versión en el navbar de la landing page, leyéndola directamente de `hub_bundle.json` en lugar de estar hardcodeada.

## 1.2.1 - 2026-06-17

### Cambiado

- Migración del despliegue de GitHub Pages al flujo moderno basado en GitHub Actions workflow.

### Corregido

- Control de clicks en las pestañas de curl para evitar errores interactivos en datasets que no generan salida JSON.

## 1.2.0 - 2026-06-17

### Agregado

- Agregada nueva superficie de dataset público: `empresas` (Registro de Empresas y
  Sociedades del Ministerio de Economía, ~1.57M registros con RUT, razón
  social, tipo societario y comuna tributaria).
- Agregado `res_extractor.py` con obtención en vivo desde datos.gob.cl, snapshot
  crudo, staging CSV y generación de metadatos.
- Agregada `validate_empresas()` en `src/validation.py` con verificaciones de
  integridad referencial contra el DPA.
- Agregada lógica de división automática en `build_excel()` para datasets que
  exceden el límite de 1,048,576 filas de Excel (`empresas` se divide en múltiples
  hojas numeradas automáticamente).
- Agregado `docs/datasets/empresas.md` con esquema, fuente, licencia y ejemplos
  de uso completos.

### Cambiado

- Catálogo activo expandido de 14 a 15 datasets.
- Gestión de versión centralizada: `pyproject.toml` es la fuente única de
  verdad; `__init__.py` la lee dinámicamente.
- Optimizado `build_dev_db.py`: conversión única `.to_pandas()` (antes 2×),
  inserciones SQLite multi-fila, omisión de JSON para tablas >100K filas,
  salida de progreso.
- Actualizados README, SOURCE_OF_TRUTH.md, AGENTS.md y CHANGELOG para reflejar
  el catálogo actual de 15 capas, la estructura del paquete y el conteo de líneas.

### Eliminado

- `puntos_interes` (POIs de OpenStreetMap) — extractor, configuración, tests, CI y
  documentación. La API de Overpass resultó demasiado inestable para CI; se
  reconsiderará cuando haya una fuente oficial chilena de POIs disponible.
  `validate_puntos_interes()` se conserva en `src/validation.py` para
  reutilización futura.

### Notas

- `empresas` se extrae en vivo desde datos.gob.cl (CC-BY 3.0 CL); la salida
  Excel se divide en múltiples hojas para mantenerse dentro del límite de filas de Excel.

## 1.1.0 - 2026-06-17

### Agregado

- Agregadas cuatro nuevas superficies de dataset público: `finanzas_municipales`,
  `resultados_educacionales`, `indicadores_urbanos_siedu` y el derivado
  `perfil_territorial_comunal`.
- Agregadas integración de extractor, metadatos de staging, validación centralizada,
  Parquet/JSON normalizado, DuckDB, SQLite, Excel, catálogo, procedencia,
  redistribución, health, bundle, CI y documentación para las nuevas capas.
- Agregados artefactos operativos legibles por máquina `dataset_status.json` y
  `dataset_changelog.json`.
- Agregados `ChileHub.dataset_status()`, `ChileHub.dataset_changelog()` y los
  comandos CLI correspondientes `chile-hub dataset-status` y `chile-hub dataset-changelog`.

### Cambiado

- Catálogo activo expandido de 10 a 14 datasets.
- Actualizadas las pruebas de humo del landing page y las expectativas de
  incidencias principales para que las capas de respaldo puedan convertirse en
  la prioridad operativa correctamente identificada.

### Notas

- `finanzas_municipales`, `resultados_educacionales` e
  `indicadores_urbanos_siedu` actualmente se construyen en modo `fallback` hasta
  que se configuren exportaciones directas estables. `make verify` pasa;
  se espera que `make verify-live` rechace esas capas hasta que se complete la
  extracción en vivo.

## 1.0.1 - 2026-06-17

### Agregado

- Agregado `pytest-cov` a la cadena de herramientas de desarrollo, con soporte
  local de `make coverage` y reportes de cobertura en CI para el paquete `src/`.
- Actualizadas las dependencias de desarrollo y publicación a sus últimas
  versiones estables compatibles, incluyendo `build`, `pre-commit`, `pytest-cov`
  y `python-semantic-release`.

### Corregido

- Restaurada la compatibilidad con Python 3.10 reemplazando el uso de
  `datetime.UTC` (solo Python 3.11) con `datetime.timezone.utc`.
- Corregido el flujo de publicación en PyPI para que `python-semantic-release`
  omita su paso de compilación interna y el entorno del job use la compilación
  del paquete.
