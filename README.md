<div align="center">

<h1>🇨🇱 chile-hub</h1>

<p><strong>Datos públicos de Chile, curados y listos para análisis en una línea de código.</strong></p>

<p><strong>15 capas oficiales y derivadas · 346 comunas · CUT preservado como texto · Parquet, DuckDB, SQLite, JSON y Excel</strong></p>

[![CI/CD](https://github.com/cortega26/chile-hub/actions/workflows/pipeline-check.yml/badge.svg)](https://github.com/cortega26/chile-hub/actions)
[![PyPI version](https://img.shields.io/pypi/v/chile-hub.svg)](https://pypi.org/project/chile-hub/)
[![PyPI downloads](https://img.shields.io/pypi/dm/chile-hub.svg)](https://pypi.org/project/chile-hub/)
[![Coverage](https://img.shields.io/badge/coverage-pytest--cov-16a34a.svg)](#desarrollo-local)
[![License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-3776AB.svg?style=flat&logo=python&logoColor=white)]()
[![Formats](https://img.shields.io/badge/Formats-Parquet%20%7C%20DuckDB%20%7C%20SQLite%20%7C%20JSON%20%7C%20Excel-orange.svg)]()
[![Datasets](https://img.shields.io/badge/Datasets-15%20capas-16a34a.svg)]()
[![Comunas](https://img.shields.io/badge/Comunas-346-8b5cf6.svg)]()

<p>
  <a href="#-instalar-y-usar-en-segundos">Instalación</a> ·
  <a href="#las-15-capas-de-datos">Capas</a> ·
  <a href="#arquitectura-del-pipeline">Arquitectura</a> ·
  <a href="#cli-de-referencia">CLI</a> ·
  <a href="#fuentes-licencias-y-reúso">Licencias</a>
</p>

</div>

---

## ⚡ Instalar y usar en segundos

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()
comunas = hub.load_polars("comunas")          # 346 comunas como DataFrame
indicadores = hub.load_polars("indicadores")  # Serie histórica UF, Dólar, Euro, UTM, IPC

# Cruce territorial garantizado — códigos CUT siempre VARCHAR
censo = hub.load_polars("censo_comunal")
df = comunas.join(censo, on="codigo_comuna")
print(df.head())
```

La primera ejecución descarga automáticamente el bundle validado desde GitHub Releases, verifica su integridad SHA256 y lo deja en cache local. A partir de ahí, todo corre contra el cache. También puedes administrarlo explícitamente:

```bash
chile-hub cache update     # Forzar descarga del bundle más reciente
chile-hub cache status     # Ubicación y estado del cache local
chile-hub cache clear      # Liberar espacio
```

> **Variante para desarrolladores del pipeline:** `pip install chile-hub[pipeline]` agrega DuckDB, Pandas, XlsxWriter y curl_cffi para ejecutar el pipeline completo de extracción y build. La instalación mínima solo incluye Polars, PyArrow, requests y platformdirs — suficiente para consumir datos.

> [!NOTE]
> **chile-hub** no busca "tener todos los datos de Chile". Busca **reducir drásticamente el costo técnico** de encontrar, limpiar, validar, cruzar y consumir datasets geográficos, demográficos, electorales y económicos críticos de Chile.

---

## Por qué existe

Trabajar con datos públicos chilenos implica enfrentar los mismos obstáculos una y otra vez:

| ❌ Sin chile-hub | ✅ Con chile-hub |
|:---|:---|
| Enlaces rotos y APIs inconsistentes | Pipeline automatizado con fallbacks y verificación de integridad |
| Planillas Excel deformes con celdas combinadas | Parquet, DuckDB y JSON listos para producción |
| Códigos CUT que pierden ceros al leerse como `int` | CUT garantizados como `VARCHAR` de largo fijo (`"01101"`) |
| Nombres de comunas imposibles de cruzar (_Ñuñoa_ vs _Nunoa_) | Columna `nombre_comuna_clean` normalizada para cruces exactos |
| Cero trazabilidad sobre origen y vigencia del dato | Metadatos con fuente, fecha de extracción, licencia y modo |

chile-hub empaqueta esas decisiones en una capa reproducible: extrae desde fuentes oficiales, normaliza schemas, valida reglas territoriales y publica artefactos listos para consumo local o CI/CD.

---

## Qué entrega chile-hub

<table>
<tr><td>

**Curado y validado**
Cada capa pasa por validaciones automáticas de integridad referencial, cardinalidad exacta (346 comunas) y formato de códigos territoriales. El pipeline **falla ruidosamente** antes de publicar datos corruptos.

</td><td>

**Cruzable por diseño**
Todos los datasets se vinculan mediante códigos CUT (`codigo_comuna`, `codigo_provincia`, `codigo_region`). Una sola clave une demografía, salud, educación, finanzas municipales, indicadores urbanos y distritos electorales.

</td></tr>
<tr><td>

**Múltiples formatos**
Parquet para analítica de alto rendimiento, DuckDB para consultas SQL locales, SQLite para aplicaciones embebidas, JSON para pipelines y Excel para usuarios de planillas. Todos generados desde la misma fuente.

</td><td>

**Trazabilidad total**
Cada artefacto incluye: fuente original, fecha de extracción, modo (en vivo/respaldo), hash SHA256, licencia y estatus de redistribución. Sabes exactamente qué estás consumiendo.

</td></tr>
<tr><td>

**Una línea de código**
```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("comunas")
```

</td><td>

**CI/CD transparente**
Pipeline determinista en GitHub Actions: extracción → build → verificación → tests → pruebas de humo. Todo reproducible en local con `make refresh`.

</td></tr>
</table>

---

## Las 15 capas de datos

| # | Capa | Registros | Fuente | Licencia | Actualización |
|:--:|:---|:---|:---|:---|:--:|
| 1 | **Regiones** | 16 | BCN ArcGIS | CC BY | — |
| 2 | **Provincias** | 56 | BCN ArcGIS | CC BY | — |
| 3 | **Comunas** | 346 | BCN ArcGIS | CC BY | — |
| 4 | **Comunas Enriquecidas** | 346 | BCN + INE | CC BY | — |
| 5 | **Indicadores Económicos** | Serie histórica | BCCh / mindicador.cl | Libre c/cita | Diaria |
| 6 | **Censo Comunal 2024** | 346 | INE | CC BY 4.0 | Decenal |
| 7 | **Censo Hogares y Viviendas** | 346 | INE | CC BY 4.0 | Decenal |
| 8 | **Establecimientos de Salud** | ~5 600 | MINSAL / datos.gob.cl | CC0 | Mensual |
| 9 | **Distritos Electorales** | 346 | BCN / Ley 20.840 | CC0 | — |
| 10 | **Establecimientos Educacionales** | ~12 900 | MINEDUC | CC BY 3.0 CL | Anual |
| 11 | **Finanzas Municipales** | fallback curado | SINIM / SUBDERE | Revisión términos | Anual |
| 12 | **Resultados Educacionales** | fallback curado | MINEDUC | CC BY 3.0 CL | Anual |
| 13 | **Indicadores Urbanos SIEDU** | cobertura parcial | INE / SIEDU | Datos abiertos INE | Anual |
| 14 | **Perfil Territorial Comunal** | 346 | chile-hub derivado | Fuentes abiertas | Derivada |
| 15 | **Empresas (RES)** | ~1 570 000 | Min. Economía / datos.gob.cl | CC-BY 3.0 CL | Mensual |

> **Todas las capas se vinculan por `codigo_comuna`**, el Código Único Territorial de 5 caracteres definido por SUBDERE.

<details>
<summary><b>Ver schema completo de cada capa</b></summary>

<br>

**1. regiones** — 16 regiones político-administrativas
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` |
| `nombre_region` | `VARCHAR` | `"Tarapacá"` |

**2. provincias** — 56 provincias con referencia a su región
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` |
| `nombre_region` | `VARCHAR` | `"Tarapacá"` |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` |
| `nombre_provincia` | `VARCHAR` | `"Iquique"` |

**3. comunas** — 346 comunas con nombres oficiales y limpios, coordenadas y población
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` |
| `nombre_comuna_clean` | `VARCHAR` | `"iquique"` |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` |
| `codigo_region` | `VARCHAR(2)` | `"01"` |
| `nombre_region` | `VARCHAR` | `"Tarapacá"` |
| `latitud_cabecera` | `DOUBLE` | `-20.2138` |
| `longitud_cabecera` | `DOUBLE` | `-70.1508` |
| `poblacion_estimada` | `INTEGER` | `223400` |

**4. comunas_enriquecidas** — Comunas con coordenadas de cabecera y población estimada INE
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` |
| `nombre_comuna_clean` | `VARCHAR` | `"iquique"` |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` |
| `codigo_region` | `VARCHAR(2)` | `"01"` |
| `latitud_cabecera` | `DOUBLE` | `-20.2138` |
| `longitud_cabecera` | `DOUBLE` | `-70.1508` |
| `poblacion_estimada` | `INTEGER` | `223400` |

**5. indicadores** — Serie de indicadores económicos diarios (UF, Dólar, Euro, UTM, IPC)
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `fecha` | `DATE` | `2026-05-30` |
| `codigo_indicador` | `VARCHAR` | `"uf"` |
| `valor` | `DOUBLE` | `39420.50` |

**6. censo_comunal** — Población por sexo y 5 tramos de edad para las 346 comunas
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_region` | `VARCHAR(2)` | `"01"` |
| `codigo_provincia` | `VARCHAR(3)` | `"011"` |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` |
| `nombre_comuna` | `VARCHAR` | `"Iquique"` |
| `poblacion_censada` | `INTEGER` | `223400` |
| `hombres` / `mujeres` | `INTEGER` | `111200` / `112200` |
| `razon_hombre_mujer` | `DOUBLE` | `99.11` |
| `poblacion_0_14` … `poblacion_65_mas` | `INTEGER` | 5 tramos etarios |

**7. censo_hogares_viviendas** — Viviendas, hogares y promedio de personas por hogar
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` |
| `viviendas_censadas` | `INTEGER` | `85000` |
| `viviendas_particulares_ocupadas` | `INTEGER` | `75000` |
| `viviendas_colectivas` | `INTEGER` | `200` |
| `hogares_censados` | `INTEGER` | `73000` |
| `promedio_personas_hogar` | `DOUBLE` | `3.06` |

**8. establecimientos_salud** — Directorio nacional de recintos de salud (~5 600)
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_establecimiento` | `VARCHAR` | `"101101"` |
| `nombre_establecimiento` | `VARCHAR` | `"Hospital Dr. Ernesto Torres Galdames"` |
| `tipo_establecimiento` | `VARCHAR` | `"Hospital"` |
| `nivel_atencion` | `VARCHAR` | `"Alta Complejidad"` |
| `codigo_comuna` | `VARCHAR(5)` | `"01101"` |
| `tiene_servicio_urgencia` | `VARCHAR` | `"SI"` / `"NO"` |
| `latitud` / `longitud` | `DOUBLE` | Coordenadas geográficas |
| `estado_funcionamiento` | `VARCHAR` | `"Vigente"` |

**9. distritos_electorales** — Mapeo de comunas a distritos y circunscripciones
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"13114"` |
| `nombre_comuna` | `VARCHAR` | `"Las Condes"` |
| `distrito_electoral` | `VARCHAR` | `"11"` |
| `circunscripcion_senatorial` | `VARCHAR` | `"7"` |

**10. establecimientos_educacionales** — Directorio de colegios y liceos (~12 900)
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `rbd` | `VARCHAR` | `"1"` |
| `dv_rbd` | `VARCHAR` | `"4"` |
| `nombre_establecimiento` | `VARCHAR` | `"Liceo Abate Molina"` |
| `codigo_comuna` | `VARCHAR(5)` | `"07101"` |
| `dependencia_administrativa` | `VARCHAR` | `"Municipal"` |
| `latitud` / `longitud` | `DOUBLE` | Coordenadas geográficas |
| `estado_funcionamiento` | `VARCHAR` | `"Vigente"` |

**11. finanzas_municipales** — Indicadores financieros municipales anuales
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `anio` | `INTEGER` | `2024` |
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` |
| `ingresos_totales` / `gastos_totales` | `DOUBLE` | `245000000000.0` |
| `ingresos_propios_permanentes` | `DOUBLE` | `162000000000.0` |
| `fondo_comun_municipal` | `DOUBLE` | `39000000000.0` |

**12. resultados_educacionales** — Métricas educacionales agregadas por comuna/año
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `anio` | `INTEGER` | `2024` |
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` |
| `matricula_total` | `INTEGER` | `122000` |
| `asistencia_promedio` | `DOUBLE` | `86.2` |
| `tasa_aprobacion` / `tasa_retiro` | `DOUBLE` | `91.4` / `4.5` |

**13. indicadores_urbanos_siedu** — Indicadores urbanos en formato largo
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `anio` | `INTEGER` | `2024` |
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` |
| `codigo_indicador` | `VARCHAR` | `"siedu_acceso_areas_verdes"` |
| `categoria` | `VARCHAR` | `"Espacio publico"` |
| `valor` / `unidad` | `DOUBLE` / `VARCHAR` | `71.4` / `"porcentaje"` |

**14. perfil_territorial_comunal** — Perfil derivado con una fila por comuna
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `codigo_comuna` | `VARCHAR(5)` | `"13101"` |
| `poblacion_censada` | `INTEGER` | `223400` |
| `establecimientos_salud_total` | `INTEGER` | `140` |
| `establecimientos_educacionales_total` | `INTEGER` | `410` |
| `distrito_electoral` | `VARCHAR` | `"10"` |

**15. empresas** — Registro de Empresas y Sociedades (RES) con RUT, razón social, tipo societario y comuna
| Columna | Tipo | Ejemplo |
|:---|:---|:---|
| `rut` | `VARCHAR` | `"76286049-K"` |
| `razon_social` | `VARCHAR` | `"COMERCIALIZADORA EJEMPLO SPA"` |
| `codigo_sociedad` | `VARCHAR` | `"SPA"` |
| `capital` | `INTEGER` | `5000000` |
| `fecha_actuacion` | `DATE` | `2020-06-15` |
| `anio` | `INTEGER` | `2020` |
| `comuna_tributaria` | `VARCHAR` | `"SANTIAGO"` |
| `region_tributaria` | `VARCHAR` | `"13"` |

</details>

---

## Guía de uso

### Consumir datos (instalación desde PyPI)

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()

# Catálogo de capas disponibles
print(hub.list_datasets())

# Cargar cualquier capa como Polars DataFrame
comunas = hub.load_polars("comunas")
censo = hub.load_polars("censo_comunal")
salud = hub.load_polars("establecimientos_salud")

# Cruce garantizado: códigos CUT son VARCHAR, no int
df = comunas.join(censo, on="codigo_comuna")
print(df.head())

# Salud operativa del hub
print(hub.health())
```

La primera ejecución descarga el bundle validado desde GitHub Releases, verifica
su integridad SHA256 y lo deja en cache local. También puedes prepararlo explícitamente:

```bash
chile-hub cache update     # Descargar el bundle más reciente
chile-hub cache status     # Ver ubicación y estado del cache
chile-hub cache clear      # Liberar espacio en disco
```

### Consultas SQL con DuckDB

```sql
-- Top 10 comunas por población censada
SELECT nombre_comuna, poblacion_censada, hombres, mujeres
FROM 'data/normalized/censo_comunal.parquet'
ORDER BY poblacion_censada DESC
LIMIT 10;

-- Cruce territorial: comunas × distritos electorales
SELECT c.nombre_comuna, c.nombre_region,
       e.distrito_electoral, e.circunscripcion_senatorial
FROM 'data/normalized/comunas.parquet' c
JOIN 'data/normalized/distritos_electorales.parquet' e
  ON c.codigo_comuna = e.codigo_comuna
WHERE c.nombre_region = 'Valparaíso';
```

### Usar en scripts y producción

```python
import polars as pl

comunas = pl.read_parquet("data/normalized/comunas.parquet")
censo = pl.read_parquet("data/normalized/censo_comunal.parquet")

# Cruce garantizado: códigos CUT son VARCHAR, no int
df = comunas.join(censo, on="codigo_comuna")
print(df.head())
```

> **Versionado:** Para entornos productivos, fija la versión exacta en `requirements.txt`:
> ```
> chile-hub==1.2.0
> ```
> El bundle de datos se publica con cada release. La API del módulo `ChileHub` sigue
> versionado semántico: cambios de interfaz pública solo en _major releases_.

### Desarrollo local del pipeline

Si necesitas ejecutar el pipeline de extracción y build en tu máquina:

```bash
git clone https://github.com/cortega26/chile-hub.git
cd chile-hub
make bootstrap          # Crea .venv, instala dependencias + Playwright
make refresh            # extract → build → verify → test → pruebas de humo
```

> Usa `pip install chile-hub[pipeline]` si quieres las dependencias completas del pipeline
> (DuckDB, Pandas, XlsxWriter, curl_cffi) pero sin clonar el repositorio.

---

## Arquitectura del Pipeline

El pipeline es **lineal, determinista y estricto**: si una validación falla, el build se cancela antes de publicar datos corruptos.

```mermaid
flowchart LR
    classDef extract fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0f172a;
    classDef stage fill:#ecfeff,stroke:#0891b2,stroke-width:2px,color:#0f172a;
    classDef build fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#0f172a;
    classDef verify fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#0f172a;
    classDef test fill:#fae8ff,stroke:#c084fc,stroke-width:2px,color:#0f172a;
    classDef publish fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px,color:#0f172a;

    subgraph EXTRACT["1. EXTRACT - fuentes oficiales"]
        direction TB
        X1["Territorio<br/>BCN / SERVEL"]:::extract
        X2["Demografía 2024<br/>INE"]:::extract
        X3["Servicios públicos<br/>MINSAL / MINEDUC"]:::extract
        X4["Economía<br/>BCCh / SINIM / RES"]:::extract
        X5["Indicadores urbanos<br/>SIEDU"]:::extract
    end

    S["data/staging/<br/>CSV + metadata.json"]:::stage
    B["2. BUILD<br/>build_dev_db.py"]:::build
    N["data/normalized/<br/>artefactos publicables"]:::stage
    V["3. VERIFY<br/>verify_pipeline.py"]:::verify
    T["4. TEST<br/>pytest"]:::test
    L["5. SMOKE + PUBLISH<br/>landing + bundle"]:::publish

    X1 --> S
    X2 --> S
    X3 --> S
    X4 --> S
    X5 --> S
    S --> B --> N --> V --> T --> L
```

> [!IMPORTANT]
> **Invariante crítica:** El pipeline aborta si la cardinalidad de comunas ≠ 346, si los códigos CUT pierden el formato `VARCHAR`, o si alguna regla de negocio se rompe. **Nunca** se publican datos corruptos.

<details>
<summary><b>Extractores incluidos en el paso 1</b></summary>

| Dominio | Extractores |
|:---|:---|
| Territorio | `subdere_extractor.py`, `electoral_extractor.py` |
| Demografía | `censo_extractor.py`, `censo_hogares_viviendas_extractor.py` |
| Servicios públicos | `salud_extractor.py`, `mineduc_establecimientos_extractor.py`, `mineduc_resultados_extractor.py` |
| Economía | `bcentral_extractor.py`, `sinim_finanzas_extractor.py`, `res_extractor.py` |
| Indicadores urbanos | `siedu_extractor.py` |

</details>

---

## Modelo de Datos — Códigos CUT

El valor central de chile-hub es que **todas las capas se vinculan jerárquicamente** mediante los Códigos Únicos Territoriales (CUT) de SUBDERE/INE:

```mermaid
erDiagram
    REGIONES {
        VARCHAR codigo_region PK "Ej: '01' (Tarapacá)"
        VARCHAR nombre_region
    }
    PROVINCIAS {
        VARCHAR codigo_provincia PK "Ej: '011' (Iquique)"
        VARCHAR codigo_region FK
        VARCHAR nombre_provincia
    }
    COMUNAS {
        VARCHAR codigo_comuna PK "Ej: '01101' (Iquique)"
        VARCHAR codigo_provincia FK
        VARCHAR codigo_region FK
        VARCHAR nombre_comuna
        VARCHAR nombre_comuna_clean "Ej: 'iquique' (sin tildes)"
    }
    COMUNAS_ENRIQUECIDAS {
        VARCHAR codigo_comuna PK
        VARCHAR nombre_comuna
        DOUBLE latitud_cabecera
        DOUBLE longitud_cabecera
        INTEGER poblacion_estimada
    }
    CENSO_COMUNAL {
        VARCHAR codigo_comuna PK
        INTEGER poblacion_censada
        INTEGER hombres
        INTEGER mujeres
        INTEGER poblacion_0_14
    }
    CENSO_HOGARES_VIVIENDAS {
        VARCHAR codigo_comuna PK
        INTEGER viviendas_censadas
        INTEGER hogares_censados
        DOUBLE promedio_personas_hogar
    }
    ESTABLECIMIENTOS_SALUD {
        VARCHAR codigo_establecimiento PK
        VARCHAR codigo_comuna FK
        VARCHAR nombre_establecimiento
        VARCHAR tipo_establecimiento
    }
    DISTRITOS_ELECTORALES {
        VARCHAR codigo_comuna PK
        VARCHAR distrito_electoral
        VARCHAR circunscripcion_senatorial
    }
    ESTABLECIMIENTOS_EDUCACIONALES {
        VARCHAR rbd PK "Rol Base de Datos"
        VARCHAR codigo_comuna FK
        VARCHAR nombre_establecimiento
    }
    INDICADORES {
        DATE fecha PK
        VARCHAR codigo_indicador PK "Ej: 'uf', 'dolar'"
        DOUBLE valor
    }

    REGIONES ||--o{ PROVINCIAS : "contiene"
    PROVINCIAS ||--o{ COMUNAS : "contiene"
    COMUNAS ||--|| COMUNAS_ENRIQUECIDAS : "enriquece"
    COMUNAS ||--o| CENSO_COMUNAL : "demografía"
    COMUNAS ||--o| CENSO_HOGARES_VIVIENDAS : "hogares"
    COMUNAS ||--o{ ESTABLECIMIENTOS_SALUD : "salud"
    COMUNAS ||--o{ ESTABLECIMIENTOS_EDUCACIONALES : "educación"
    COMUNAS ||--o| DISTRITOS_ELECTORALES : "electoral"
```

---

## Formatos de salida

Cada ejecución del pipeline genera en `data/normalized/`:

| Tipo | Archivo | Uso |
|:---|:---|:---|
| **Base de datos** | `chile_data.duckdb` | Analítica local de alto rendimiento |
| **Base de datos** | `chile_data.db` | SQLite para aplicaciones embebidas |
| **Intercambio** | `chile_data_latest.xlsx` | Excel multipestaña (códigos CUT como texto) |
| **Intercambio** | `*.parquet` por capa | Polars / Pandas / DuckDB |
| **Intercambio** | `*.json` por capa | Pipelines y automatización |
| **Metadatos** | `artifact_manifest.json` | Catálogo físico con SHA256 y tamaños |
| **Metadatos** | `hub_health.json` / `.md` | Reporte de salud operativa |
| **Metadatos** | `dataset_status.json` | Estado machine-readable por dataset |
| **Metadatos** | `dataset_changelog.json` | Deltas de filas, campos, fuente y validación |
| **Metadatos** | `dataset_catalog.json` / `.md` | Catálogo con schemas y ejemplos |
| **Metadatos** | `redistribution_report.json` / `.md` | Estado legal de reúso por dataset |
| **Metadatos** | `provenance_report.json` / `.md` | Trazabilidad de origen y marcas de tiempo |
| **Bundle** | `chile-hub-publishable-bundle.zip` | Paquete público con verificación SHA256 |

---

## CLI de referencia

El paquete instala el comando `chile-hub` en el `PATH`. Todos los subcomandos
funcionan tanto desde PyPI como desde el entorno de desarrollo.

### Inspección y consulta

| Comando | Descripción |
|:---|:---|
| `chile-hub list` | Lista todos los datasets registrados |
| `chile-hub version` | Muestra la versión instalada del paquete |
| `chile-hub cache status` | Muestra ubicación y estado del cache local |
| `chile-hub cache update` | Descarga y verifica el bundle publicado |
| `chile-hub cache clear` | Elimina el cache local |
| `chile-hub show <capa>` | Schema y metadatos detallados de una capa |
| `chile-hub path <capa> --output parquet` | Ruta física al archivo de una capa |
| `chile-hub example <capa> --kind duckdb` | Receta de consumo lista para copiar y pegar |
| `chile-hub overview` | Resumen general del build y estado actual |
| `chile-hub inventory` | Archivos en `data/normalized/` con tamaños y hashes |

### Calidad, salud y auditoría

| Comando | Descripción |
|:---|:---|
| `chile-hub health` | Reporte consolidado de salud del hub |
| `chile-hub freshness-audit` | Auditoría de frescura contra el reloj actual |
| `chile-hub runtime-status` | Salud registrada + vigencia en vivo |
| `chile-hub top-issue` | Capa con mayor degradación operativa |
| `chile-hub drift` | Desvíos, fallbacks activos y regresiones |
| `chile-hub status` | JSON ultraliviano para CI/CD |
| `chile-hub dataset-status` | Estado detallado machine-readable por dataset |
| `chile-hub dataset-changelog` | Cambios entre el build actual y el metadata anterior |

### Distribución e integridad

| Comando | Descripción |
|:---|:---|
| `chile-hub bundle` | Metadata consolidada en un solo JSON |
| `chile-hub redistribution` | Reporte legal de reúso por capa |
| `chile-hub provenance` | URLs de origen y métodos de extracción |
| `chile-hub verify-package` | Instrucción de verificación de integridad del ZIP |

> En entorno de desarrollo, usa `python -m chile_hub` o `python -m src.chile_hub`
> como alternativa al comando `chile-hub` si el paquete no está instalado en modo editable.

---

## Desarrollo local

Esta sección es para contribuidores que necesitan ejecutar el pipeline completo
de extracción, build y verificación en su máquina. Si solo necesitas consumir
los datos, usa `pip install chile-hub` (ver [Guía de uso](#guía-de-uso)).

```bash
# Entorno
make bootstrap          # Crea .venv, instala dependencias + Playwright
make doctor             # Verifica versión de Python y dependencias críticas

# Pipeline completo
make refresh            # extract → build → verify → test → landing

# Pasos individuales
make extract            # Ejecuta los extractores → data/staging/
make build              # Compila artefactos → data/normalized/
make verify             # Verifica integridad (SHA256, conteos, schema)
make test               # pytest (lee data/normalized/, no corre el pipeline)
make coverage           # pytest + cobertura de src/ (term-missing + coverage.xml)
make verify-landing     # Pruebas de humo de landing page con Playwright

# Tests
./.venv/bin/pytest -v
./.venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=xml
./.venv/bin/pytest tests/test_chile_hub.py::ChileHubTests::test_load_polars -v
```

---

## Fuentes, licencias y reúso

### Semáforo de redistribución

| Color | Estado | Acción |
|:---:|:---|:---|
| 🟢 `open-attribution` | CC BY, CC0 o equivalente | Se incluye en el bundle público |
| 🟡 `public-api-review-terms` | API pública sin licencia explícita | Se distribuye tras verificar el origen primario |
| 🔴 `restricted` | Derechos de autor, Ley 19.628 | **Nunca** se integra al bundle público |

### Licencia del proyecto

El código Python se distribuye bajo **[MIT](LICENSE)**. Los datasets conservan
las licencias, permisos y requisitos de atribución de sus fuentes oficiales.
Consulta [DATA_LICENSES.md](DATA_LICENSES.md), `chile-hub redistribution` y
`chile-hub provenance` antes de redistribuir artefactos derivados.

---

## Próximos pasos

El roadmap actual prioriza **fortalecer la estabilidad operacional** de las 15 capas activas frente a caídas de APIs, especialmente las capas nuevas que aún corren en modo `fallback`. El criterio para incorporar nuevas capas exige justificar:

- Dolor de usuario recurrente y documentado
- Valor de cruce con la División Político-Administrativa (CUT)
- Bajo costo de mantenimiento continuo

> La especificación completa del producto está en [`docs/product-spec.md`](./docs/product-spec.md).
> El estado de la última corrida se documenta en `data/normalized/pipeline_status.md` tras cada build.

---

## ¿Quieres contribuir?

Revisa [`AGENTS.md`](./AGENTS.md) para entender la arquitectura, las reglas no negociables y el flujo de trabajo. El punto de partida rápido es [`SOURCE_OF_TRUTH.md`](./SOURCE_OF_TRUTH.md).

**¿Encontraste un error o tienes un caso de uso?** Abre un [issue](https://github.com/cortega26/chile-hub/issues) — ayuda a priorizar el roadmap.


<div align="center">

**🇨🇱 Hecho con datos públicos chilenos, para quienes construyen sobre Chile.**

</div>
