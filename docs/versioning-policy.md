# Política de Versionamiento para chile-hub

Este documento establece la política oficial de versionamiento para el proyecto `chile-hub`. Define el uso de **Semantic Versioning (SemVer 2.0.0)** y aclara la distinción entre actualizaciones de software/esquema y actualizaciones de datos en bruto.

---

## 1. Reglas de Semantic Versioning (SemVer 2.0.0)

La versión del proyecto se define en la clave `version` del archivo `pyproject.toml` en el formato `MAJOR.MINOR.PATCH` (por ejemplo, `0.1.0`).

### 1.1 MAJOR (Mayor): Cambios Disruptivos (Breaking Changes)
Se incrementa la versión **MAJOR** (ej. `0.1.2` $\rightarrow$ `1.0.0`) cuando se realizan cambios incompatibles con versiones anteriores en la API pública de Python, el CLI o en los esquemas de datos finales expuestos en `data/normalized/`.

**Ejemplos:**
- Eliminación de un dataset existente del catálogo público.
- Eliminación o renombrado de columnas canónicas (ej. renombrar `codigo_comuna` a `comuna_id`).
- Cambios en los tipos de datos de columnas canónicas (ej. cambiar códigos CUT de `VARCHAR/String` a `INTEGER/Int`).
- Eliminación o cambios no retrocompatibles en firmas de métodos públicos en la clase `ChileHub` o subcomandos del CLI.

### 1.2 MINOR (Menor): Adición de Características y Datos (Additive Changes)
Se incrementa la versión **MINOR** (ej. `0.1.0` $\rightarrow$ `0.2.0`) cuando se agrega funcionalidad de manera compatible con las versiones anteriores, o cuando se añaden nuevos datasets y columnas.

**Ejemplos:**
- Adición de un nuevo dataset al hub (ej. agregar `sinim_finanzas` o `establecimientos_educacionales`).
- Adición de nuevas columnas a un dataset existente.
- Implementación de nuevas funcionalidades en la API de Python o en el CLI (ej. un nuevo subcomando o método de exportación).
- Cambios de arquitectura interna del pipeline que no rompen el formato final de salida de los datos.

### 1.3 PATCH (Parche): Corrección de Errores e Integridad (Bug Fixes)
Se incrementa la versión **PATCH** (ej. `0.1.0` $\rightarrow$ `0.1.1`) cuando se realizan correcciones de errores compatibles con versiones anteriores, mejoras de rendimiento o ajustes de documentación.

**Ejemplos:**
- Correcciones en la lógica de un extractor (ej. adaptar un extractor a cambios menores en el endpoint HTTP de origen sin cambiar el esquema resultante).
- Ajustes finos en las funciones de validación de `src/validation.py`.
- Corrección de erratas de tipografía en nombres de columnas o texto en la landing page.
- Actualización de dependencias del proyecto o documentación en general.

---

## 2. Versión de Software/Esquema vs. Actualización de Datos

Es fundamental separar la versión de la base de código y estructura (SemVer) del ciclo de actualización del contenido de los datos.

### 2.1 Versión del Software/Esquema (Código)
- Representa el **código fuente**, los **esquemas de las tablas** y los **contratos del pipeline**.
- Se gestiona en `pyproject.toml` y requiere un commit de código y un tag de release de Git.
- Mantiene sincronizada la versión en la landing page (`index.html`) a través de la compilación automatizada del pipeline.

### 2.2 Actualización del Contenido de los Datos (Freshness)
- Representa la **frescura y valores reales** del contenido (ej. la cotización del dólar de hoy, la población del censo actual).
- Ocurre de forma continua mediante ejecuciones programadas del pipeline de extracción y compilación (vía GitHub Actions).
- **No cambia la versión SemVer del software**, pero actualiza el timestamp `refreshed_at_utc` en el archivo `metadata.json` correspondiente de cada dataset en `data/staging/` y en `dataset_catalog.json`.
- La frescura operativa se monitoriza mediante el CLI (`chile-hub health`) y los metadatos dinámicos generados en `pipeline_metadata.json`, los cuales reflejan en vivo el estado y alertas de frescura sin necesidad de lanzar una nueva versión de código.

---

## 3. Automatización y Flujo de Publicación

1. **Definir la versión**: Al introducir cambios de esquema o código, el desarrollador/agente actualiza la versión en `pyproject.toml`.
2. **Sincronización automática**: Al correr `make build` (que ejecuta `src/build_dev_db.py`), el pipeline lee `pyproject.toml` usando `tomllib`, inyecta la versión en los metadatos normalizados (`pipeline_metadata.json` y `hub_bundle.json`) y actualiza el badge HTML en la landing page `index.html`.
3. **CI/CD**: El pipeline de integración verifica la consistencia de los archivos autogenerados y asegura que no ocurran discrepancias de versión antes de publicar los artefactos.
