# AGENTS.md — Guía de Trabajo para Agentes de IA

Este documento define cómo trabajar correctamente en el repositorio `chile-hub`.
Es la fuente de verdad para cualquier agente de IA o colaborador nuevo que necesite
entender la arquitectura, las reglas no negociables y las convenciones del proyecto.

> **Leer completo antes de modificar cualquier archivo.**
> Las reglas de esta guía evitan errores que se propagan silenciosamente a los datos publicados.

---

## 1. Propósito del proyecto

`chile-hub` es una capa de datos pública, curada y reproducible sobre **datos oficiales de Chile**.
Actualmente publica diez capas:

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

**El objetivo no es tener todos los datos de Chile. Es entregar un número pequeño de datasets
limpios, versionados, validados y consumibles en una línea de código.**

---

## 2. Estructura del repositorio

```
chile-hub/
├── .github/workflows/
│   └── pipeline-check.yml      CI/CD: extrae, construye, valida, publica
│
├── src/
│   ├── extractors/
│   │   ├── subdere_extractor.py   Extrae DPA desde BCN ArcGIS → data/staging/
│   │   ├── bcentral_extractor.py  Extrae indicadores desde mindicador.cl → data/staging/
│   │   ├── censo_extractor.py     Extrae perfil comunal Censo 2024 desde INE → data/staging/
│   │   ├── censo_hogares_viviendas_extractor.py Extrae hogares y viviendas INE → data/staging/
│   │   ├── salud_extractor.py     Extrae establecimientos desde MINSAL → data/staging/
│   │   ├── electoral_extractor.py Extrae distritos electorales desde BCN → data/staging/
│   │   └── mineduc_establecimientos_extractor.py Extrae establecimientos educacionales desde MINEDUC → data/staging/
│   ├── build_dev_db.py            Construye todos los artefactos desde staging/
│   ├── pipeline_status_utils.py   Genera reportes Markdown de salud, catálogo y redistribución
│   └── chile_hub.py               API Python (ChileHub) + CLI
│
├── data/
│   ├── raw/          Snapshots crudos de cada respuesta de API (JSON). Solo lectura una vez guardados.
│   ├── staging/      Datos parseados y cercanos a la fuente (CSV + metadata.json por dataset).
│   └── normalized/   Artefactos finales publicables (Parquet, JSON, DuckDB, Excel, ZIP, reportes).
│
├── tests/
│   └── test_chile_hub.py   Suite completa: ChileHubTests, ArtifactContractTests, ChileHubCliTests
│
├── scripts/
│   ├── verify_pipeline.py  Verifica integridad de artefactos post-build
│   ├── verify_landing.py   Smoke tests de la landing page con Playwright
│   └── pipeline_status.py  Genera pipeline_status.md
│
├── docs/datasets/          Documentación por dataset (fuente, schema, licencia, recetas)
└── examples/               Notebooks y scripts de demostración para usuarios
```

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
             → Produce: data/staging/{dataset}.csv + data/staging/{dataset}.metadata.json
             → Produce: data/raw/{source}_{timestamp}.json  (snapshot crudo)

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

## 5. Cómo agregar un nuevo dataset

Sigue estos pasos en orden. No saltear ninguno.

### Paso 1 — Evaluar la fuente

Antes de escribir código, responder:

- [ ] ¿Tiene licencia explícita o amparo claro en la Ley 20.285?
- [ ] ¿Está disponible como API JSON o dump estático descargable? (no scraping HTML frágil)
- [ ] ¿El formato de origen es estable? ¿Ha cambiado en los últimos 12 meses?
- [ ] ¿El dataset cruza con la DPA por `codigo_comuna` o `codigo_region`?
- [ ] ¿El dolor que resuelve justifica el costo de mantenimiento?

Si la respuesta a cualquiera de las tres primeras preguntas es negativa, **no agregar al MVP**.

### Paso 2 — Crear el extractor

```
src/extractors/{nombre}_extractor.py
```

El extractor debe:
1. Intentar fetch en vivo; si falla, usar fallback (datos embebidos o generados).
2. Guardar snapshot crudo en `data/raw/{source}_{timestamp}.json`.
3. Normalizar al formato canónico y guardar en `data/staging/{nombre}.csv`.
4. Generar `data/staging/{nombre}.metadata.json` con todos los campos requeridos.

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

### Paso 3 — Registrar en build_dev_db.py

Agregar la entrada correspondiente en `DATASET_CATALOG_CONFIG` siguiendo el patrón
de los datasets existentes (`regiones`, `provincias`, `comunas`, `indicadores`).

### Paso 4 — Agregar validaciones

Agregar una función `validate_{nombre}(df, metadata)` en `build_dev_db.py` con al menos:
- Verificar que el DataFrame no está vacío.
- Verificar unicidad de la clave primaria.
- Verificar integridad referencial con la DPA si el dataset tiene `codigo_comuna` o `codigo_region`.

### Paso 5 — Agregar tests

En `tests/test_chile_hub.py`, agregar tests para:
- `hub.load_polars('{nombre}')` retorna filas.
- `hub.summary()` incluye el nuevo dataset con `validation_status: "ok"`.
- Los contratos de artefactos en `ArtifactContractTests`.

### Paso 6 — Actualizar el workflow de CI

Agregar el extractor al paso de extracción en `.github/workflows/pipeline-check.yml`.

### Paso 7 — Documentar

Crear `docs/datasets/{nombre}.md` con: descripción, fuente, licencia, schema completo,
ejemplos de uso en Python/DuckDB/SQL, notas sobre limitaciones y changelog.

---

## 6. Fuentes y política legal

### Semáforo de reutilización

| Color | Estado | Acción |
|:---|:---|:---|
| 🟢 `open-attribution` | Redistribución libre con citación (CC-BY o equivalente) | Publicar en bundle |
| 🟡 `public-api-review-terms` | API pública sin licencia explícita; datos origen son públicos | Publicar solo si el origen primario es redistribuible |
| 🔴 `restricted` | Términos prohíben redistribución comercial o masiva | **Excluir del bundle público** |

### Fuentes actuales y su estado

| Fuente | Dataset | Estado | Nota |
|:---|:---|:---|:---|
| BCN ArcGIS | DPA (regiones, provincias, comunas) | 🟢 CC BY | Atribución requerida |
| Banco Central de Chile | Indicadores (vía mindicador.cl) | 🟢 Libre con citación | BCCh permite reproducción con cita |
| INE | IPC, proyecciones | 🟢 CC BY | Atribución requerida |
| SII | Estadísticas de empresas | 🔴 Restringido | **Nunca incluir** sin análisis legal |
| SERVEL | Datos electorales | 🔴 Restringido | Ley 19.628, datos personales |

### Regla conservadora

Ante cualquier duda sobre la licencia de una fuente, **no redistribuir el dato**.
Publicar los metadatos y el enlace a la fuente original en su lugar.

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

---

## 8. Testing

### Correr los tests

```bash
# Prerequisito: el pipeline debe haber corrido al menos una vez
python src/extractors/subdere_extractor.py
python src/extractors/bcentral_extractor.py
python src/extractors/censo_extractor.py
python src/extractors/censo_hogares_viviendas_extractor.py
python src/extractors/salud_extractor.py
python src/extractors/electoral_extractor.py
python src/extractors/mineduc_establecimientos_extractor.py
python src/build_dev_db.py

# Suite completa
pytest -v

# Test individual
pytest tests/test_chile_hub.py::ChileHubTests::test_load_polars -v
```

### Qué cubren los tests

| Clase | Qué verifica |
|:---|:---|
| `ChileHubTests` | API Python: `load_polars`, `health`, `bundle`, `redistribution`, `provenance` |
| `ArtifactContractTests` | Contratos de artefactos: SHA256, catálogo, ZIP, metadatos de redistribución |
| `ChileHubCliTests` | CLI: todos los subcomandos (`list`, `path`, `show`, `health`, `bundle`, etc.) |

### Reglas al agregar tests

- Los tests **no deben correr extractores ni el pipeline**. Leen de `data/normalized/`.
- Un test que falla por datos desactualizados indica que el pipeline no ha corrido, no que el código está roto.
- Todos los valores esperados en assertions deben estar justificados en comentarios si no son obvios.

---

## 9. CI/CD

El workflow `.github/workflows/pipeline-check.yml` corre en `push` a `main`,
`pull_request`, `schedule` diario y `workflow_dispatch` manual.

### Jobs del workflow

1. `quality` — Ruff lint y format check.
2. `build-and-test` — extractores, build, verificación, tests y status.
3. `landing` — smoke test Playwright usando exactamente los outputs del job anterior.
4. `publish` — solo en `schedule` o dispatch con `publish=true`; exige
   `verify_pipeline.py --require-live` y publica `data/normalized/` en `main`.

El cron corre a las `10:00 UTC`: `06:00 CLT` o `07:00 CLST`. La publicación rechaza
fallbacks, datos stale, fallas de fetch, recuperación raw y preservación de staging. Solo permite
backfill del último valor publicado cuando la consulta live fue exitosa y una serie mensual aún no
publicó un valor nuevo. Los commits automáticos usan
`[skip ci]` para evitar loops. Los artefactos de CI se suben como un directorio generado único,
sin mantener una segunda lista manual de archivos.

---

## 10. Antipatrones — nunca hacer esto

### ❌ Modificar data/normalized/ manualmente

Los archivos en `data/normalized/` son artefactos generados. Editarlos a mano rompe
la reproducibilidad y los hashes del manifest. Siempre regenerar desde el pipeline.

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

### ❌ Usar versiones no fijadas en requirements.txt

```
# ❌
polars>=0.20.0

# ✅
polars==0.20.31
```

Las versiones flotantes pueden romper el pipeline silenciosamente en CI.

### ❌ Publicar datos sin pasar por validate_*()

Las funciones `validate_comunas()`, `validate_indicadores()`, etc. en `build_dev_db.py`
son la última línea de defensa antes de publicar. No bypassear estas validaciones.

---

## 11. Referencia rápida de comandos

```bash
# Correr el pipeline completo
python src/extractors/subdere_extractor.py
python src/extractors/bcentral_extractor.py
python src/extractors/censo_extractor.py
python src/extractors/censo_hogares_viviendas_extractor.py
python src/extractors/salud_extractor.py
python src/extractors/electoral_extractor.py
python src/extractors/mineduc_establecimientos_extractor.py
python src/build_dev_db.py

# Verificar artefactos
python scripts/verify_pipeline.py

# Correr tests
pytest -v

# Usar la API Python
from src.chile_hub import ChileHub
hub = ChileHub()
hub.health()                        # Estado general del hub
hub.load_polars("comunas")          # DataFrame Polars con 346 comunas
hub.load_polars("indicadores")      # Serie histórica de indicadores
hub.redistribution()                # Reporte legal por dataset

# CLI
python -m src.chile_hub list
python -m src.chile_hub health
python -m src.chile_hub show comunas
python -m src.chile_hub path comunas --output parquet
python -m src.chile_hub redistribution
python -m src.chile_hub provenance
python -m src.chile_hub bundle
```

---

*Última actualización: Junio 2026. Actualizar este documento cuando cambie la arquitectura,
se agreguen datasets o se modifiquen invariantes críticas.*
