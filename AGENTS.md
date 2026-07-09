# AGENTS.md — Guía de Trabajo para Agentes de IA

Este documento define cómo trabajar correctamente en el repositorio `chile-hub`.
Es la fuente de verdad para cualquier agente de IA o colaborador nuevo que necesite
entender la arquitectura, las reglas no negociables y las convenciones del proyecto.

> **Leer completo antes de modificar cualquier archivo.**
> Las reglas de esta guía evitan errores que se propagan silenciosamente a los datos publicados.

---

## 1. Propósito del proyecto

`chile-hub` es una capa de datos pública, curada y reproducible sobre **datos oficiales de Chile**.
Actualmente publica diecinueve (19) capas:

| Capa | Fuente | Descripción |
|:---|:---|:---|
| **División Político-Administrativa** (regiones, provincias, comunas) | BCN ArcGIS | 16 regiones, 56 provincias, 346 comunas con códigos CUT, coordenadas y abreviaturas |
| **Comunas Enriquecidas** | BCN ArcGIS + INE | Comunas con coordenadas de cabecera y población estimada INE, listas para análisis territorial |
| **Indicadores Económicos** | mindicador.cl (datos BCCh / INE) | UF, Dólar, Euro, UTM, IPC — histórico desde 2010, actualización diaria |
| **Censo Comunal 2024** | INE | Población por sexo y cinco grandes grupos de edad para las 346 comunas |
| **Censo Hogares y Viviendas 2024** | INE | Viviendas y hogares por comuna, incluyendo promedios de personas por hogar |
| **Establecimientos de Salud** | MINSAL / datos.gob.cl | Directorio vigente con tipo, dependencia, urgencia, estado y coordenadas |
| **Distritos Electorales** | BCN / SERVEL | Asociación de comunas a distritos electorales de diputados y circunscripciones senatoriales |
| **Establecimientos Educacionales** | MINEDUC | Directorio oficial con RBD, dependencia, ubicación y estado de funcionamiento |
| **Finanzas Municipales** | SINIM / SUBDERE | Indicadores financieros municipales anuales por comuna |
| **Resultados Educacionales** | MINEDUC | Métricas educacionales agregadas por comuna y año, sin registros personales |
| **Indicadores Urbanos SIEDU** | INE / SIEDU | Indicadores urbanos en formato largo con cobertura parcial esperada |
| **Perfil Territorial Comunal** | chile-hub derivado | Una fila por comuna con métricas territoriales consolidadas |
| **Empresas (RES)** | Ministerio de Economía / datos.gob.cl | Registro de constituciones de empresas bajo Ley 20.659 con RUT, razón social, tipo societario y comuna |
| **Pobreza Comunal (SAE)** | MDS / Observatorio Social | Estimaciones de pobreza por ingresos y multidimensional por comuna |
| **Consumo Eléctrico Comunal** | CNE / Energía Abierta | Consumo eléctrico anual por comuna y tipo de cliente |
| **Partidos Políticos** | Cámara de Diputados / SERVEL | Roster de partidos políticos vigentes e históricos con estado legal |
| **Autoridades Electas** | Cámara de Diputados + Senado | Diputados y senadores en ejercicio, con partido y distrito o circunscripción |
| **Delincuencia Comunal** | CEAD / Subsecretaría de Prevención del Delito | Casos policiales DMCS y otras categorías por comuna y mes (carril `candidate`, ver nota abajo) |
| **Autoridades Locales** | Wikipedia (CC-BY-SA) | Gobernadores regionales y alcaldes, segregado de Autoridades Electas por licencia share-alike (carril `candidate`) |

**El objetivo no es tener todos los datos de Chile. Es entregar un número pequeño de datasets
limpios, versionados, validados y consumibles en una línea de código.**

> **Carriles de publicación:** no todos los datasets listados arriba están en el bundle
> público. Algunos viven en el carril `candidate` (evaluados, implementados, pero fuera
> del ZIP publicable por fragilidad de fuente o licencia) con una fecha `review_by` de
> reevaluación. La fuente de verdad de qué dataset está en qué carril, su
> `maturity_status` y `confidence_tier` es **`data/dataset_catalog_config.json`** (y
> `data/source_registry.json`); los criterios de aceptación completos viven en
> **`docs/dataset-inclusion-criteria.md`**. No dupliques ese sistema aquí — referencia
> esos documentos.

---

## 2. Estructura del repositorio

```
chile-hub/
├── .github/workflows/
│   └── pipeline-check.yml      CI/CD: extrae, construye, valida, publica
│
├── src/
│   ├── extractors/                 18 extractores por dataset + 4 módulos compartidos (ver nota abajo)
│   │   ├── base.py                              BaseExtractor ABC (contrato para todos los extractores)
│   │   ├── http_utils.py                        Reintentos/backoff HTTP compartidos
│   │   ├── region_utils.py                      Normalización de nombres de región compartida
│   │   ├── source_adapter.py                    Adaptador de fuente compartido
│   │   ├── subdere_extractor.py                 DPA: regiones/provincias/comunas/comunas_enriquecidas (BCN ArcGIS) → data/staging/
│   │   ├── bcentral_extractor.py                Indicadores desde mindicador.cl → data/staging/
│   │   ├── censo_extractor.py                   Censo 2024 — población comunal (INE) → data/staging/
│   │   ├── censo_hogares_viviendas_extractor.py Censo 2024 — hogares y viviendas (INE) → data/staging/
│   │   ├── salud_extractor.py                   Establecimientos de salud (MINSAL) → data/staging/
│   │   ├── electoral_extractor.py               Distritos electorales (BCN/SERVEL) → data/staging/
│   │   ├── mineduc_establecimientos_extractor.py Establecimientos educacionales (MINEDUC) → data/staging/
│   │   ├── mineduc_resultados_extractor.py      Resultados educacionales agregados (MINEDUC) → data/staging/
│   │   ├── siedu_extractor.py                   Indicadores urbanos SIEDU (INE) → data/staging/
│   │   ├── res_extractor.py                     Empresas — Registro de Empresas y Sociedades (datos.gob.cl) → data/staging/
│   │   ├── pobreza_extractor.py                 Pobreza comunal SAE (MDS) → data/staging/
│   │   ├── consumo_electrico_extractor.py       Consumo eléctrico comunal (CNE) → data/staging/
│   │   ├── partidos_politicos_extractor.py      Partidos políticos vigentes (SERVEL) → data/staging/
│   │   ├── autoridades_electas_extractor.py     Diputados y senadores en ejercicio → data/staging/
│   │   ├── sinim_finanzas_extractor.py          Finanzas municipales — stub de fallback; NO corre en `make extract`
│   │   ├── sinim_finanzas_live_extractor.py     Finanzas municipales — scraper real; corre en `monthly-scrape.yml`
│   │   ├── cead_delincuencia_live_extractor.py  Delincuencia comunal (CEAD); corre en `monthly-scrape.yml`
│   │   └── autoridades_locales_extractor.py     Autoridades locales (Wikipedia); carril `candidate`, sin cadencia automática
│   ├── validation.py              Todas las funciones validate_*() — módulo independiente (1 194 líneas)
│   ├── build_dev_db.py            Orquestador (867 líneas): main() + fases (_load_inputs, _compute_validations, _write_data_artifacts, _generate_reports)
│   ├── builders/                  Módulos del pipeline extraídos de build_dev_db.py (formats, metadata, reports, artifacts, datasets, catalog, landing, io_utils, _shared)
│   ├── chile_hub.py               Compatibility shim (21 líneas) — delega al paquete
│   ├── chile_hub/                 Paquete Python instalable (ChileHub API + CLI + data manager)
│   │   ├── core.py                ChileHub class + API pública (2 302 líneas)
│   │   ├── cli.py                 CLI entry points
│   │   ├── data_manager.py        Descarga de bundle, cache, verificación SHA256
│   │   └── pipeline_status_utils.py  Reportes Markdown de salud, catálogo y redistribución (888 líneas)
│   └── pipeline_status_utils.py   Copia para imports de build_dev_db.py (888 líneas)
│
├── data/
│   ├── dataset_catalog_config.json  Fuente de verdad de qué datasets existen (cargado por _shared.py)
│   ├── source_registry.json         Registro de fuentes: maturity_status, confidence_tier, review_by
│   ├── raw/          Snapshots crudos de cada respuesta de API (JSON). Solo lectura una vez guardados.
│   ├── staging/      Datos parseados y cercanos a la fuente (CSV + metadata.json por dataset).
│   └── normalized/   Artefactos finales publicables (Parquet, JSON, DuckDB, Excel, ZIP, reportes).
│
├── tests/                        9 archivos — ver tabla completa en §8, no la dupliques aquí
│   ├── test_chile_hub.py         API/CLI de ChileHub, contratos de artefactos, workflow, Makefile
│   ├── test_extractors.py        Un test class por extractor + contrato de BaseExtractor
│   ├── test_pipeline_logic.py    Lógica interna de build_dev_db.py, invariantes CUT, changelog
│   ├── test_validation.py        Funciones validate_*() de src/validation.py
│   ├── test_core.py              Métodos públicos de ChileHub (core.py)
│   ├── test_data_package.py      Builder de Frictionless Data Package
│   ├── test_packaging_runtime.py Empaquetado del bundle publicable en runtime
│   ├── test_render.py            Helper de renderizado de tablas (_render.py)
│   └── test_ci_config.py         Guardrails de regresiones reales de CI/Makefile
│
├── scripts/
│   ├── verify_pipeline.py             Verifica integridad de artefactos post-build
│   ├── verify_landing.py              Smoke tests de la landing page con Playwright
│   ├── pipeline_status.py             Genera pipeline_status.md
│   ├── check_validation_registration.py  Valida que cada validate_*() esté registrada en build_dev_db.py
│   └── check_companion_paths.py       Anti-drift: dataset registry↔docs/contratos + co-cambio de rutas (§12)
│
├── docs/datasets/          Documentación por dataset (fuente, schema, licencia, recetas)
└── examples/               Notebooks y scripts de demostración para usuarios
```

No todos los datasets tienen un extractor 1:1: `subdere_extractor.py` alimenta cuatro
claves (`regiones`, `provincias`, `comunas`, `comunas_enriquecidas`) y
`perfil_territorial_comunal` es derivado en `build_dev_db.py` a partir de otros
datasets, sin extractor propio. El mapeo autoritativo dataset↔extractor es
**`data/dataset_catalog_config.json`**, no esta lista — si la lista de arriba y el
JSON no coinciden, confía en el JSON y actualiza esta lista.

---

## Navegar el código — CodeGraph y lecturas acotadas

CodeGraph está instalado (`.codegraph/codegraph.db`). Úsalo antes de abrir archivos grandes.

```bash
codegraph search "<query>"                         # Buscar símbolo, función o concepto
codegraph refs src/build_dev_db.py::validate_comunas  # Callers y callees de una función
codegraph graph src/chile_hub.py                   # Grafo de imports del módulo
codegraph find <symbol_name>                       # En qué archivo está definido
```

**Reglas para acotar lecturas y ahorrar tokens:**
- Usar `view_file` con `StartLine`/`EndLine` — nunca leer archivos grandes enteros de golpe.
- `base.py` (73 líneas) es seguro de leer completo. `validation.py` (1 194 líneas) — leer por validador individual.
- `build_dev_db.py` (867 líneas) y `src/chile_hub/core.py` (2 302 líneas) — usar estas áncoras:

| Archivo | Líneas de interés |
|---|---|
| `src/build_dev_db.py` | imports de validators (cabecera) · función `_compute_validations()` (bloque `validations = {…}`) · `build_dataset_metadata` se importa de `src/builders/metadata.py` |
| `src/chile_hub/core.py` | L24 (clase ChileHub) · L24-200 (superficie pública de la API) |
| `tests/test_chile_hub.py` | Requiere `data/normalized/` — correr `make build` antes |

---

## 3. Flujo del pipeline (orden obligatorio)

```
1. EXTRACT   src/extractors/subdere_extractor.py
             src/extractors/bcentral_extractor.py
             src/extractors/censo_extractor.py
             src/extractors/censo_hogares_viviendas_extractor.py
             src/extractors/salud_extractor.py
             src/extractors/electoral_extractor.py
             src/extractors/mineduc_establecimientos_extractor.py
             src/extractors/mineduc_resultados_extractor.py
             src/extractors/siedu_extractor.py
             src/extractors/res_extractor.py
             src/extractors/pobreza_extractor.py
             src/extractors/consumo_electrico_extractor.py
             src/extractors/partidos_politicos_extractor.py
             src/extractors/autoridades_electas_extractor.py
             (los 14 que corre `make extract` / el job diario de CI — ver §11)
             → Produce: data/staging/{dataset}.csv + data/staging/{dataset}.metadata.json
             → Produce: data/raw/{source}_{timestamp}.json  (snapshot crudo)

             Cadencia distinta / carril `candidate` (NO corren en `make extract`):
             sinim_finanzas_live_extractor.py y cead_delincuencia_live_extractor.py
             (vía `monthly-scrape.yml`); autoridades_locales_extractor.py (ad hoc).
             sinim_finanzas_extractor.py es un stub de fallback, no un paso del
             pipeline diario — nunca invocarlo desde un job programado (ver
             `tests/test_ci_config.py::SinimDailyJobGuardrailTests`).

2. BUILD     src/build_dev_db.py
             Lee: data/staging/
             → Produce: data/normalized/ (todos los artefactos)

3. VERIFY    scripts/verify_pipeline.py
             Lee: data/normalized/
             → Valida integridad de artefactos y contratos de datos

4. TEST      pytest
             → Suite completa de tests unitarios y de contrato

5. LANDING   scripts/verify_landing.py
             → Smoke tests de la landing page
```

**Regla de ejecución:** los pasos deben correr en este orden. Nunca modificar `data/normalized/`
directamente; siempre regenerar corriendo el pipeline desde el paso 2.

---

## 4. Invariantes críticas — reglas que nunca deben romperse

### 4.1 Códigos CUT siempre como string de longitud fija

```python
# ✅ Correcto
codigo_comuna   = "01101"   # str, siempre 5 caracteres
codigo_provincia = "011"    # str, siempre 3 caracteres
codigo_region   = "01"      # str, siempre 2 caracteres

# ❌ Incorrecto — Excel y algunas bases de datos silenciosamente pierden el cero
codigo_comuna = 1101    # int: pierde el cero inicial de Tarapacá
```

Los códigos deben preservarse como `VARCHAR` en DuckDB/SQLite, como `str` en Python
y con formato de texto `@` en Excel. El pipeline ya hace esto; no romper ese comportamiento.

### 4.2 El pipeline falla ruidosamente antes de publicar datos malos

Si una validación falla, el pipeline **debe abortar**. No sobreescribir artefactos en
`data/normalized/` con datos inválidos. Los usuarios dependen de la última versión
publicada; un dataset corrupto es peor que un dataset desactualizado.

```python
# Patrón obligatorio en validaciones
if errors:
    raise SystemExit(f"Validación fallida: {errors}")
# No usar warnings silenciosos para errores de datos críticos
```

### 4.3 Los artefactos en data/raw/ son de solo escritura

Una vez guardado un snapshot en `data/raw/`, no modificarlo. Es el registro de auditoría
de lo que entregó la fuente en ese momento. Si el procesamiento falla, se puede volver
al raw para depurar sin necesidad de volver a contactar la fuente.

### 4.4 Cada dataset tiene su metadata.json en staging

El archivo `data/staging/{dataset}.metadata.json` debe existir antes de que `build_dev_db.py`
procese ese dataset. Contiene `source_name`, `source_url`, `source_mode`, `refreshed_at_utc`,
`reuse_policy` y `record_count`. El pipeline lee este archivo; sin él, falla.

**Diagnóstico si falta un `metadata.json`:**
1. Ejecutar `ls data/staging/*.metadata.json` para ver cuáles existen.
2. Si falta el metadata de un dataset, ejecutar su extractor individualmente:
   `python src/extractors/{nombre}_extractor.py`. El extractor regenera tanto el CSV
   como el `metadata.json` en staging.
3. Si el extractor también falla, verificar conectividad con la fuente upstream y
   revisar `data/raw/` por si hay un snapshot previo que permita regeneración offline.
4. El comando `make doctor` verifica la presencia de todos los `metadata.json` esperados
   y reporta los faltantes.

### 4.5 nombre_comuna_clean siempre presente y sin caracteres especiales

La columna `nombre_comuna_clean` debe existir en el dataset de comunas, estar en minúsculas
y no tener tildes ni `ñ`. Es la clave de búsqueda para joins de texto inexactos.

```python
# Normalización obligatoria (orden importa para legibilidad)
.str.to_lowercase()
.str.replace_all("á", "a").str.replace_all("é", "e")
.str.replace_all("í", "i").str.replace_all("ó", "o")
.str.replace_all("ú", "u").str.replace_all("ü", "u")
.str.replace_all("ñ", "n")   # Crítico: Ñuñoa → nunoa
```

---

## 5. ¿Cómo agregar un nuevo dataset?

Sigue estos pasos en orden. No saltear ninguno.

### Paso 1 — Evaluar la fuente

Antes de escribir código, responder:

**Preguntas bloqueantes** (una respuesta negativa descarta el dataset para el MVP):

- [ ] **1. Licencia:** ¿Tiene licencia explícita o amparo claro en la Ley 20.285?
- [ ] **2. Formato:** ¿Está disponible como API JSON o dump estático descargable? (no scraping HTML frágil)
- [ ] **3. Estabilidad:** ¿El formato de origen es estable? ¿Ha cambiado en los últimos 12 meses?

**Preguntas orientativas** (una respuesta negativa no descarta, pero reduce prioridad):

- [ ] **4. Cruce DPA:** ¿El dataset cruza con la DPA por `codigo_comuna` o `codigo_region`?
- [ ] **5. Costo-beneficio:** ¿El dolor que resuelve justifica el costo de mantenimiento?

Si la respuesta a cualquiera de las preguntas bloqueantes (1–3) es negativa,
**no agregar al MVP**. Las preguntas orientativas (4–5) informan la prioridad
relativa frente a otros candidatos, pero no son excluyentes.

### Paso 2 — Crear el extractor

```
src/extractors/{nombre}_extractor.py
```

El extractor debe:
1. Intentar fetch en vivo; si falla, usar fallback (datos embebidos o generados).
2. Guardar snapshot crudo en `data/raw/{source}_{timestamp}.json`.
3. Normalizar al formato canónico y guardar en `data/staging/{nombre}.csv`.
4. Generar `data/staging/{nombre}.metadata.json` con todos los campos requeridos.

> **Importante sobre fallback:** el fallback permite desarrollo y prueba sin conexión,
> pero el job `publish` de CI (§9) **rechaza datasets en modo fallback**. Si un
> extractor entra en fallback durante un `schedule` diario, la publicación se aborta
> para ese dataset y se registra en el reporte de salud. El mantenedor debe
> investigar la causa del fallo de fetch y restaurar la conectividad con la fuente.

Campos obligatorios en `metadata.json`:
```json
{
  "dataset": "nombre",
  "source_name": "...",
  "source_url": "...",
  "source_mode": "live | fallback",
  "source_detail": "...",
  "refreshed_at_utc": "2026-01-01T00:00:00+00:00",
  "record_count": 0,
  "fields": [],
  "notes": [],
  "reuse_policy": {
    "status": "open-attribution | public-api-review-terms | restricted",
    "license": "...",
    "license_url": "...",
    "attribution_required": true,
    "redistribution_ok": true,
    "summary": "..."
  }
}
```

### Paso 3 — Registrar en data/dataset_catalog_config.json

`DATASET_CATALOG_CONFIG` ya **no** es un dict literal en `build_dev_db.py`: se carga
en tiempo de ejecución desde **`data/dataset_catalog_config.json`** vía
`src/builders/_shared.py::_load_catalog_config()`. Agregar la entrada correspondiente
en ese JSON siguiendo el patrón de los datasets existentes (`regiones`, `provincias`,
`comunas`, `indicadores`). Si el dataset tiene carril (`candidate` /
`stable_publishable`), `maturity_status` o `confidence_tier`, esos campos viven en
**`data/source_registry.json`** (ver §1 y `docs/dataset-inclusion-criteria.md`).

### Paso 4 — Agregar validaciones

Agregar una función `validate_{nombre}(df, metadata)` en **`src/validation.py`** (no en
`build_dev_db.py`) con al menos:
- Verificar que el DataFrame no está vacío.
- Verificar unicidad de la clave primaria.
- Verificar integridad referencial con la DPA si el dataset tiene `codigo_comuna` o `codigo_region`.

Luego importarla en `build_dev_db.py` y llamarla dentro del bloque `validations = {…}` de la función `_compute_validations()`.

> **Verificación obligatoria:** después de registrar la validación, ejecutar
> `python scripts/check_validation_registration.py` o `make doctor`.
> La verificación compara las funciones `validate_*()` de `src/validation.py`
> contra las claves del bloque `validations = {…}` de `build_dev_db.py`, con
> excepciones explícitas para alias semánticos y validadores archivados. Una
> validación definida pero no registrada se salta silenciosamente: los datos se
> publican sin pasar por esa verificación.

### Paso 5 — Agregar tests

En `tests/test_chile_hub.py`, agregar tests para:
- `hub.load_polars('{nombre}')` retorna filas.
- `hub.summary()` incluye el nuevo dataset con `validation_status: "ok"`.
- Los contratos de artefactos en `ArtifactContractTests`.

En `tests/test_extractors.py`, agregar una clase `{Nombre}ExtractorTests` con al menos:
- Smoke test del método `run()` en modo dry-run.
- Verificación de que el CSV y `metadata.json` de staging tienen el schema esperado.

En `tests/test_pipeline_logic.py`, agregar casos en `ValidatorTests` que cubran
borde vacío y clave primaria duplicada para `validate_{nombre}()`.

### Paso 6 — Actualizar el workflow de CI

Agregar el extractor al paso de extracción en `.github/workflows/pipeline-check.yml`.

### Paso 7 — Documentar

Crear `docs/datasets/{nombre}.md` con: descripción, fuente, licencia, schema completo,
ejemplos de uso en Python/DuckDB/SQL, notas sobre limitaciones y changelog.

> **CHANGELOG:** `CHANGELOG.md` se actualiza automáticamente en cada release mediante
> `python-semantic-release` (configurado con `mode = "update"`). No es necesario
> editarlo manualmente; PSR lo hace en el commit de release. Ver `docs/release.md`
> para los detalles del proceso y los filtros activos.

### Modificar, renombrar o deprecar un dataset existente

**Modificar un extractor (actualizar endpoint, ajustar columnas):** seguir el mismo flujo
que para agregar uno nuevo (Pasos 2–6). Si el schema cambia (columnas agregadas, renombradas
o eliminadas), actualizar también `docs/datasets/{nombre}.md` y verificar que los tests de
contrato en `ArtifactContractTests` reflejen el nuevo schema.

**Renombrar un dataset:** el nombre del dataset es parte de la API pública
(`hub.load_polars("{nombre}")`). Para renombrar:
1. Agregar el extractor y validación con el nuevo nombre.
2. Mantener una entrada de compatibilidad en `DATASET_CATALOG_CONFIG` que apunte al nombre
   antiguo como alias durante un período de transición (mínimo 2 versiones).
3. Anunciar la depreciación en `docs/datasets/{nombre_antiguo}.md` con fecha de eliminación.
4. Eliminar el alias en una versión futura, una vez que los consumidores hayan migrado.

**Deprecar un dataset:** si un dataset dejó de ser mantenible o su fuente desapareció:
1. Marcar `status: "deprecated"` en su entrada de `DATASET_CATALOG_CONFIG`.
2. Mover su documentación a `docs/datasets/archived/{nombre}.md`.
3. Dejar de incluirlo en el bundle público ZIP.
4. Mantener el extractor como no operativo (levanta `NotImplementedError` con mensaje
   explicativo) durante 2 versiones para no romper CI.
5. Eliminar el extractor y validación en una versión futura.
6. Anunciar en el changelog del release.

---

## 6. Fuentes y política legal

### Semáforo de reutilización

| Color | Estado | Acción |
|:---|:---|:---|
| 🟢 `open-attribution` | Redistribución libre con citación (CC-BY o equivalente) | Publicar en bundle |
| 🟡 `public-api-review-terms` | API pública sin licencia explícita; datos origen son públicos | Publicar solo si el origen primario es redistribuible (ver criterios abajo) |
| 🔴 `restricted` | Términos prohíben redistribución comercial o masiva | **Excluir del bundle público** |

### Criterios para "origen primario es redistribuible"

Para que un origen califique como redistribuible bajo `public-api-review-terms`, debe cumplir
**al menos una** de estas condiciones:

- El organismo emisor es una institución pública chilena y los datos son de acceso público
  sin restricción explícita en los términos del portal (ej. datos.gob.cl, INE, BCN).
- La Ley 20.285 (Transparencia) ampara el acceso y no hay restricción de propiedad intelectual
  o secreto estadístico aplicable.
- El sitio de origen declara explícitamente que permite uso comercial y redistribución.

Si ninguna aplica, el dataset se clasifica como `restricted` y se excluye del bundle público.

| Fuente | Dataset | Estado | Nota |
|:---|:---|:---|:---|
| BCN ArcGIS | DPA (regiones, provincias, comunas) | 🟢 CC BY | Atribución requerida |
| Banco Central de Chile | Indicadores (vía mindicador.cl) | 🟢 Libre con citación | BCCh permite reproducción con cita |
| INE | IPC, proyecciones | 🟢 CC BY | Atribución requerida |
| SII | Estadísticas de empresas | 🔴 Restringido | **Nunca incluir** sin análisis legal |
| Ministerio de Economía | RES (Registro de Empresas y Sociedades) | 🟢 CC-BY | datos.gob.cl; solo régimen simplificado (Ley 20.659) |
| OpenStreetMap | Puntos de Interés (POI) | 🟢 ODbL | Atribución requerida: "© OpenStreetMap contributors" |
| SERVEL | Padrón electoral, datos de votantes | 🔴 Restringido | Ley 19.628, datos personales — **nunca incluir** |
| SERVEL / BCN | Distritos electorales (geográficos) | 🟢 CC BY | Asociación comuna-distrito; son datos geográficos, no personales |

### Regla conservadora

Ante cualquier duda sobre la licencia de una fuente, **no redistribuir el dato**.
Publicar los metadatos y el enlace a la fuente original en su lugar.

### Protocolo ante fuente permanentemente caída

Si una fuente upstream deja de existir (API apagada, portal descontinuado, organización
disuelta), aplicar este protocolo:

1. **Verificar** que la caída es permanente y no una interrupción temporal (esperar al
   menos 3 ciclos de `schedule`, ~3 días).
2. **Congelar** el dataset en su última versión publicada. El snapshot en `data/raw/`
   y los artefactos en `data/normalized/` sirven como respaldo histórico.
3. **Marcar** el metadata con `source_mode: "archived"` y `notes: ["Fuente original
   dejó de existir el YYYY-MM-DD. Dataset congelado en su última actualización."]`.
4. **Evaluar** si el dataset sigue siendo útil sin actualizaciones. Si la respuesta es sí,
   mantenerlo como dataset histórico (solo lectura, sin fetch). Si es no, aplicar el
   procedimiento de depreciación de §5.
5. **Notificar** en el reporte de salud (`make hub-health-table`) que la fuente está
   caída, para que los consumidores sepan que el dataset no recibirá actualizaciones.

---

## 7. Convenciones de código

### Nombres de columnas

Siempre usar `snake_case` en español para columnas canónicas:
```
codigo_region, nombre_region, abreviatura
codigo_provincia, nombre_provincia
codigo_comuna, nombre_comuna, nombre_comuna_clean
latitud_cabecera, longitud_cabecera, poblacion_estimada
fecha, codigo_indicador, valor
```

No usar nombres en inglés para columnas de dominio (sí se puede en variables internas).

### Tipos de datos

| Campo | Tipo en Polars | Tipo en DuckDB | Nota |
|:---|:---|:---|:---|
| Códigos CUT | `pl.String` | `VARCHAR` | Longitud fija: 2/3/5 |
| Nombres | `pl.String` | `VARCHAR` | Con tildes correctas |
| Coordenadas | `pl.Float64` | `DOUBLE` | 6 decimales |
| Fechas | `pl.Date` | `DATE` | ISO 8601 YYYY-MM-DD |
| Valores económicos | `pl.Float64` | `DOUBLE` | Sin redondeo |
| Población | `pl.Int32` | `INTEGER` | 0 si no disponible |

### Orden de imports

```python
# 1. stdlib
import os, json, datetime, time

# 2. third-party (orden alfabético)
import polars as pl
import duckdb
import requests

# 3. locales
from pipeline_status_utils import build_hub_health
```

### Paths siempre calculados relativos a `__file__`

```python
# ✅ Correcto — funciona desde cualquier directorio de trabajo
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

# ❌ Incorrecto — path relativo al cwd, falla desde CI
DATA_DIR = "data"
```

### Versión: fuente única en `pyproject.toml`

La versión del paquete se define **exclusivamente** en `[project] version` dentro de
`pyproject.toml`. `src/chile_hub/__init__.py` la lee dinámicamente en tiempo de
ejecución: parsea `pyproject.toml` en desarrollo y usa `importlib.metadata` cuando
se instala desde PyPI.

```python
# ✅ Correcto — leer desde pyproject.toml (automático en __init__.py)
from chile_hub import __version__

# ❌ Incorrecto — NO duplicar la versión en __init__.py como string estático
__version__ = "1.2.0"
```

`python-semantic-release` solo actualiza `pyproject.toml` (`version_toml` en
`[tool.semantic_release]`). No hay `version_variables` que mantener sincronizados.

---

## 8. Testing

### Correr los tests

```bash
# Prerequisito: el pipeline debe haber corrido al menos una vez
make build

# Suite completa
pytest -v

# Test individual
pytest tests/test_chile_hub.py::ChileHubTests::test_load_polars -v
```

### ¿Qué cubren los tests?

9 archivos en `tests/`. Esta tabla es de **navegación por archivo**, no un
inventario de clases — las clases cambian con frecuencia y una lista exhaustiva
aquí quedaría stale de inmediato. Para el inventario vivo de clases:
```bash
grep -n "^class " tests/*.py
```

| Archivo | Requiere `data/normalized/` | Qué cubre |
|:---|:---:|:---|
| `test_chile_hub.py` | Sí (`make build` antes) | API Python de `ChileHub`, CLI, contratos de artefactos (SHA256, catálogo, ZIP), contratos de workflow/Makefile, `Dataset(StrEnum)` |
| `test_extractors.py` | No | Un test class por extractor (fetch, normalización, staging) + contrato ABC de `BaseExtractor` + reintentos HTTP |
| `test_pipeline_logic.py` | No | Lógica interna de `build_dev_db.py`, invariantes CUT, fallback de indicadores, severidad de `dataset_changelog.json`, builders (`reports`, `pipeline_status_utils`) |
| `test_validation.py` | No | Funciones `validate_*()` de `src/validation.py`: bordes vacíos, claves duplicadas, casos límite |
| `test_core.py` | Sí | Métodos públicos de `ChileHub` (`core.py`): metadatos, reportes operativos, inspección — no cubre CLI |
| `test_data_package.py` | No | Builder de Frictionless Data Package |
| `test_packaging_runtime.py` | No | Empaquetado del bundle publicable (ZIP, SHA256) en runtime |
| `test_render.py` | No | Helper de renderizado de tablas (`_render.py`) |
| `test_ci_config.py` | No | Guardrails de texto simple para regresiones **reales** ya ocurridas de CI/Makefile (ver política abajo) |

### Reglas al agregar tests

- Los tests que leen `data/normalized/` (`test_chile_hub.py`, `test_core.py`)
  **no deben correr extractores ni el pipeline** — un fallo por datos
  desactualizados indica que el pipeline no ha corrido (`make build`), no que
  el código está roto.
- Todos los valores esperados en assertions deben estar justificados en
  comentarios si no son obvios.

### Política de revisión y actualización de tests

**Cuándo agregar un test:**
- Dataset nuevo → §5 Paso 5 (ya cubierto).
- Fix de un bug → agregar un test de regresión que falle sin el fix y pase con él.
  Sin este test, el bug puede reaparecer sin que nadie lo note.
- Cambio de contrato/esquema/CI/Makefile con impacto real (rompió un pipeline,
  un dato mal validado llegó a publicarse, etc.) → seguir el patrón de
  `tests/test_ci_config.py`: un test de texto simple, con un docstring que
  documente el incidente concreto que lo motivó (qué pasó, qué commit lo arregló).
  No hace falta un parser completo (YAML, AST) si una comprobación de texto
  acotada ya previene la regresión — ver el propio `test_ci_config.py` para el
  criterio de cuándo alcanza con texto y cuándo no.

**Cuándo actualizar un test existente sin debilitarlo:**
- Solo si el comportamiento esperado cambió **a propósito**. El commit que
  actualiza el test debe explicar el porqué (referenciar el ADR, plan o issue
  que motivó el cambio de contrato), no solo "arreglar test roto".
- Nunca relajar una aserción, aumentar una tolerancia o quitar una validación
  de un test únicamente para que el pipeline pase sin haber entendido la causa
  raíz del fallo. Si no está claro si el test o el código están equivocados,
  investigar antes de tocar cualquiera de los dos.
- `skip`/`xfail` temporal solo con razón explícita y fecha de revisión en el
  mismo commit; nunca como forma silenciosa de esquivar un fallo.

**Cobertura:** `.codecov.yml` define `patch.target: 75%` (diffs) y
`project.target: auto` con `threshold: 2%` como piso de referencia — aunque
el upload a Codecov esté deshabilitado hoy (se usa el badge autogenerado), el
criterio sigue vigente: código nuevo del pipeline debe venir acompañado de
tests que ejerciten sus ramas nuevas, no solo el camino feliz.

**Co-cambio automático:** `scripts/check_companion_paths.py` (modo `companions`,
§12) bloquea en CI un PR que modifique `src/validation.py`, `src/extractors/**`
o `src/build_dev_db.py` sin tocar también su archivo de test compañero. Esto no
reemplaza el criterio humano de arriba — solo evita el caso más simple de
"cambié código y me olvidé de tocar el test".

---

## 9. CI/CD

El workflow `.github/workflows/pipeline-check.yml` corre en `push` a `main`,
`pull_request`, `schedule` diario y `workflow_dispatch` manual.

### Jobs del workflow

1. `quality` — Ruff lint y format check, más los gates anti-drift de §12
   (`check_companion_paths.py registry` siempre; `companions` solo en `pull_request`).
2. `build-and-test` — extractores, build, verificación, tests y status.
3. `landing` — smoke test Playwright usando exactamente los outputs del job anterior.
4. `publish` — solo en `schedule` o dispatch con `publish=true`; exige
   `verify_pipeline.py --require-live` y publica `data/normalized/` en `main`.

El cron corre a las `10:00 UTC`: `06:00 CLT` o `07:00 CLST`. La publicación rechaza
fallbacks, datos stale, fallas de fetch, recuperación raw y preservación de staging. Solo permite
backfill del último valor publicado cuando la consulta live fue exitosa y la fuente aún no
publicó un valor nuevo para el período esperado. La frecuencia esperada depende del dataset:
series diarias (indicadores económicos) toleran 1 día hábil sin valor nuevo; series mensuales
(censo, IPC) toleran 1 mes; series anuales (finanzas municipales, resultados educacionales)
toleran 1 año. Si la consulta live falla, no se aplica backfill: el dataset queda en su
última versión publicada hasta que el fetch se restaure. Los commits automáticos usan
`[skip ci]` para evitar loops. Los artefactos de CI se suben como un directorio generado único,
sin mantener una segunda lista manual de archivos.

### ¿Qué hacer cuando el publish rechaza un dataset?

Si el job `publish` rechaza un dataset (por fallback, fetch fallido, o dato stale):

1. Revisar el log de CI para identificar qué extractor falló y por qué.
2. Si la fuente está temporalmente caída: esperar al siguiente `schedule` (24 h). El dataset
   queda en su última versión publicada; los usuarios no ven datos corruptos.
3. Si la fuente cambió de API o formato: actualizar el extractor siguiendo §5 (se permite
   modificar extractores existentes con el mismo flujo que agregar uno nuevo).
4. Si la fuente desapareció permanentemente: aplicar el protocolo de §6 (marcar como
   `stale` y evaluar exclusión del bundle).

---

## 10. Antipatrones — nunca hacer esto

### ❌ Modificar data/normalized/ manualmente

Los archivos en `data/normalized/` son artefactos generados. Editarlos a mano rompe
la reproducibilidad y los hashes del manifest. Siempre regenerar desde el pipeline.

### ❌ Modificar la versión en index.html manualmente

La versión en el navbar de `index.html` (etiqueta `<span class="badge-alpha">v...</span>`) se sincroniza automáticamente con la versión declarada en `pyproject.toml` durante el proceso de compilación (`make build`). No la edites a mano.


### ❌ Usar `pd.read_excel()` con columnas de código numérico sin dtype override

```python
# ❌ — pd.read_excel convierte "01101" a int 1101
df = pd.read_excel("cut.xlsx")

# ✅ — forzar dtype string en columnas de código
df = pd.read_excel("cut.xlsx", dtype={"Código Comuna": str})
```

### ❌ Agregar fuentes con licencia ambigua sin documentarlo

Si una fuente tiene `redistribution_ok: False` o `status: "public-api-review-terms"`,
no puede entrar en el bundle público ZIP. Debe estar explícitamente excluida o
resuelta legalmente antes del lanzamiento.

### ❌ Usar scraping HTML frágil como fuente principal

El HTML de un sitio web cambia en cada rediseño. Las fuentes MVP deben ser:
- APIs JSON documentadas, o
- Dumps estáticos con URL estable (CSV/Excel/JSON directo).

### ❌ Inflar el MVP con más datasets antes de validar adopción

No agregar nuevos datasets hasta que los existentes tengan señales de adopción
documentadas (descargas, issues con casos de uso, menciones externas).

### ❌ Usar versiones no fijadas en pyproject.toml (dependencias pipeline/dev)

```toml
# ✅ Runtime (rango compatible para que consumidores publicados resuelvan)
"polars>=1.41.2,<2"

# ✅ Pipeline / dev (pin exacto reproducido vía uv.lock)
"duckdb==1.5.4"
```

Las dependencias **runtime** de la librería usan rangos compatibles (e.g. `polars>=1.41.2,<2`)
porque los consumidores publicados necesitan flexibilidad de resolución. Las dependencias
**pipeline y dev** (extractores, builders, validación, tooling) usan pins exactos (`==`)
porque un cambio silencioso allí rompe la generación de artefactos. En ambos casos el
_lockfile_ (`uv.lock`) es el único contrato reproducible — `uv sync` lo reproduce exactamente.

### ❌ Publicar datos sin pasar por validate_*()

Las funciones `validate_comunas()`, `validate_indicadores()`, etc. viven en `src/validation.py`
y son importadas por `build_dev_db.py`. Son la última línea de defensa antes de publicar.
No bypassear estas validaciones ni mover su lógica a otro módulo.

---

## 11. Referencia rápida de comandos

```bash
# Entorno
make bootstrap          # Crea .venv, instala deps + Playwright/Chromium
make doctor             # Python efectivo, dependencias clave y gates anti-drift (§12)

# Pipeline completo (lo más común)
make refresh            # extract → build → verify → test → verify-landing → lint + format-check

# Pasos individuales
make extract            # Corre los 14 extractores de cadencia diaria → data/staging/
make build              # Compila todos los artefactos → data/normalized/
make verify             # Integridad de artefactos (SHA-256, conteos, schema)
make test               # pytest — lee data/normalized/, NO corre el pipeline
make verify-landing     # Playwright smoke tests de index.html

# Diagnóstico del hub
make hub-health-table
make hub-top-issue-table
make hub-runtime-status-table

# Bundle publicable
make package-bundle     # ZIP desde artifact_manifest.json

# API Python
from src.chile_hub import ChileHub
hub = ChileHub()
hub.health()                     # Estado general del hub
hub.load_polars("comunas")       # DataFrame Polars con 346 comunas
hub.load_polars("indicadores")   # Serie histórica de indicadores
hub.redistribution()             # Reporte legal por dataset

# CLI
python -m src.chile_hub list
python -m src.chile_hub health --format table
python -m src.chile_hub show comunas
python -m src.chile_hub path comunas --output parquet
python -m src.chile_hub redistribution
python -m src.chile_hub provenance
python -m src.chile_hub bundle

# Tests individuales
./.venv/bin/pytest tests/test_chile_hub.py::ChileHubTests::test_load_polars -v
./.venv/bin/pytest tests/test_extractors.py -v      # No requiere data/normalized/
./.venv/bin/pytest tests/test_pipeline_logic.py -v  # No requiere data/normalized/
```

---

## 12. Documentación cableada al código — política anti-drift

Este mismo documento estuvo desactualizado (conteo de datasets, lista de
extractores, ubicación de `DATASET_CATALOG_CONFIG`, archivos de test) hasta que
esta sección se escribió. La lección: una regla de "recuerda actualizar la doc"
sin verificación mecánica no escala — nadie se acuerda. La política de aquí en
adelante es que **todo hecho documentado que sea derivable del código declare su
fuente de verdad canónica** y, cuando sea mecánicamente verificable, esté
protegido por un chequeo automatizado en vez de depender solo de buena voluntad.

### Propietarios canónicos

| Hecho | Fuente de verdad | Verificado por |
|:---|:---|:---|
| Qué datasets existen, su metadata | `data/dataset_catalog_config.json` | `check_companion_paths.py registry` |
| Carril (`candidate`/`stable_publishable`), `maturity_status`, `confidence_tier`, `review_by` | `data/source_registry.json` | — (criterios en `docs/dataset-inclusion-criteria.md`) |
| Contrato de esquema por dataset | `contracts/datasets/{nombre}.schema.json` | `check_companion_paths.py registry` |
| Documentación de usuario por dataset | `docs/datasets/{nombre}.md` | `check_companion_paths.py registry` |
| Criterios de inclusión/deprecación de datasets | `docs/dataset-inclusion-criteria.md` | — (revisión humana) |
| Registro de funciones `validate_*()` | bloque `validations = {…}` en `build_dev_db.py` | `check_validation_registration.py` |
| Versión del paquete | `pyproject.toml` (`[project] version`) | `python-semantic-release` (§7), `scripts/sync_docs.py` propaga a README.md |
| Inventario de clases de test | `tests/*.py` (no una tabla en prosa) | `grep '^class ' tests/*.py` (§8) |
| Conteo de tests en README | `tests/test_*.py` (AST, no pytest — ver caveat parametrize en `doc_sync.py`) | `scripts/sync_docs.py --check` |
| Conteo de ADRs en README | `docs/adr/*.md` | `scripts/sync_docs.py --check` |
| Conteo de contratos en README | `contracts/datasets/*.schema.json` | `scripts/sync_docs.py --check` |
| Badge "N capas" y resumen de auditoría legal en README | `data/dataset_catalog_config.json` / `data/normalized/redistribution_report.json` | `scripts/sync_docs.py --check` |
| Resumen de salud (`ok`/`warn`/`error`) en README | `data/normalized/hub_health.json` | `scripts/sync_docs.py --check` |
| Score de calidad (A-F) en README | `data/normalized/dataset_quality.json` | `scripts/sync_docs.py --check` |
| Ejemplo de pin de versión en README | `pyproject.toml` vía `read_project_version()` | `scripts/sync_docs.py --check` |

### Mecanismo: `scripts/check_companion_paths.py`

Dos modos, ambos corren en `make doctor` y/o en el job `quality` de CI
(`.github/workflows/pipeline-check.yml`):

1. **`registry`** (siempre, sin diff): verifica que cada clave de
   `data/dataset_catalog_config.json` tenga su contrato en `contracts/datasets/`
   y su doc en `docs/datasets/`. Bloqueante — `SystemExit` si falta alguno.
2. **`companions`** (solo en `pull_request`, vía diff contra el commit base):
   aplica la tabla `COMPANION_RULES` — si cambia una ruta disparadora (p. ej.
   `data/dataset_catalog_config.json`, `src/validation.py`,
   `src/extractors/**`) y ninguna de sus rutas compañeras (docs, tests,
   `AGENTS.md`) aparece en el mismo diff, el PR falla con un mensaje explícito
   de qué se esperaba.

**Regla de mantenimiento:** si agregas una ruta nueva con una relación de
co-cambio real (un módulo más en `src/`, un nuevo doc que depende de un JSON),
agrega la regla correspondiente a `COMPANION_RULES` en el mismo PR que la
introduce — no dejes que el próximo drift se descubra a mano, como este.

### Mecanismo: bloques delimitados + `scripts/sync_docs.py`

`check_companion_paths.py` fuerza que se *toque* un archivo compañero, pero no
verifica que su *contenido* siga siendo correcto. Para hechos de README.md que
son derivables mecánicamente de un artefacto o del código (no prosa curada),
`src/builders/doc_sync.py` + `src/builders/reports.py::sync_readme_layers_table()`
regeneran el texto exacto dentro de un bloque delimitado por comentarios HTML
(`<!-- START_X --> ... <!-- END_X -->`), usando el helper compartido
`src/builders/io_utils.py::replace_delimited_block()`.

- **Generación:** `make sync-docs`, o automáticamente al final de
  `make build` (`build_dev_db.py::main()` llama a `sync_readme_layers_table()`
  y `sync_all_docs()`).
- **Verificación:** `python scripts/sync_docs.py --check` (no escribe, falla
  con `SystemExit` si algún bloque quedaría desincronizado) corre en
  `make doctor` y en el job `quality` de CI en cada push/PR/schedule — sin
  dependencias nuevas, `doc_sync.py` es 100% stdlib.
- **Caso especial — drift por datos *live*:** el chequeo de `quality` solo
  detecta drift introducido por el propio PR (código, tests, ADRs, contratos,
  `pyproject.toml`). Si los datos cambian sin que ningún PR toque código (p. ej.
  `hub_health.json` se regenera con nuevos valores en el `schedule` diario), el
  paso "Check build-synced files" del job `build-and-test` (solo
  `schedule`/`workflow_dispatch`, después de un build real) compara
  `index.html`, `app.js` **y `README.md`** contra el build recién generado.

**Qué NO usa este mecanismo:** las tablas de prosa de `AGENTS.md` (§1 capas,
§2/§3 extractores, §8 archivos de test) no se regeneran — son descripciones
curadas editorialmente, no datos de una sola celda; automatizarlas exigiría
mantener esa prosa duplicada dentro de un generador, sin eliminar el
mantenimiento manual. Su protección es otra: los *conteos* que citan ("19
capas", "9 archivos de test", "14 extractores en `make extract`") se detectan
a ojo en revisión de PR, y su *completitud estructural* (¿falta una fila?) ya
la cubre el gate de co-cambio de `check_companion_paths.py` de arriba.

**Seguimiento recomendado, no implementado todavía** (mayor alcance):
automatizar la tabla "CLI de referencia" de README.md introspeccionando
`build_parser()` (requiere agregar `uv sync` al job `quality`, hoy sin
dependencias); y automatizar la tabla de extractores de README.md, lo que
requiere agregar primero un campo `"extractor"` a las 21 entradas de
`data/dataset_catalog_config.json` (beneficio adicional: permitiría extender
`check_companion_paths.py registry` para validar que ese archivo existe).

---

*Este documento se actualiza junto con los cambios que describe (ver §12), no
en una fecha fija. Para la fecha real de la última modificación:
`git log -1 --format=%ad -- AGENTS.md`.*
