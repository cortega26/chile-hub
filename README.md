# 🇨🇱 chile-data-core

[![Status](https://img.shields.io/badge/status-alpha--validation-orange.svg)]()
[![License](https://img.shields.io/badge/license-CC--BY--4.0-blue.svg)]()
[![CI/CD Data Updates](https://img.shields.io/badge/data--pipeline-active-success.svg)]()

La capa base territorial (geo-administrativa) y económica de Chile, normalizada y empaquetada para su consumo inmediato en DuckDB, Python, R y Excel.

> **El problema:** datos.gob.cl es un catálogo de enlaces rotos y archivos Excel deformes. Cada vez que inicias un proyecto de BI, analítica o desarrollo de software en Chile, pierdes horas limpiando nombres de comunas, validando códigos SUBDERE/CUT y programando scrapers inestables para obtener el valor de la UF.
>
> **La solución:** `chile-data-core` te entrega un único set de datos limpio, curado y versionado, consumible localmente o vía CDN en una sola línea de código.

---

## 🚀 Modos de Consumo Rápido

### 💻 Para Desarrolladores y Analistas (Técnico)

Los datos se publican a diario en formatos de alto rendimiento. Puedes leerlos directamente desde nuestro CDN estático (GitHub Releases) sin descargar archivos de forma manual.

#### 1. Ingesta Directa con DuckDB (Recomendado)
DuckDB puede leer los archivos Parquet remotos de forma nativa a la velocidad del rayo:

```sql
-- Consultar la división político-administrativa completa
SELECT * 
FROM read_parquet('https://cdn.datos.cl/latest/comunas.parquet');

-- Cruzar tus datos locales con la población comunal oficial
SELECT 
    c.nombre_comuna, 
    c.poblacion_estimada, 
    v.ventas
FROM read_parquet('https://cdn.datos.cl/latest/comunas.parquet') c
JOIN my_local_sales v ON c.codigo_comuna = v.codigo_comuna;
```

#### 2. Carga en Python (Polars / Pandas)

```python
import polars as pl

# Cargar comunas normalizadas en un DataFrame de Polars
df_comunas = pl.read_parquet("https://cdn.datos.cl/latest/comunas.parquet")

# Obtener los indicadores económicos macro de hoy
df_indicadores = pl.read_json("https://cdn.datos.cl/latest/indicadores_hoy.json")
print(df_indicadores)
```

#### 3. Endpoint JSON para Frontend Web
Ideal para poblar dinámicamente selectores `<select>` de región y comuna en formularios de registro:

```javascript
// Obtener comunas ordenadas jerárquicamente
fetch("https://cdn.datos.cl/latest/dpa_jerarquica.json")
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 📊 Para Analistas de Negocio y Finanzas (No Técnico)

No necesitas escribir código para usar los datos actualizados de Chile.

1.  **Descarga Directa en Excel (.xlsx):**
    *   Descarga el archivo consolidado diario [chile_data_latest.xlsx](https://cdn.datos.cl/latest/chile_data_latest.xlsx). Contiene pestañas limpias con la lista oficial de comunas (con códigos CUT de texto que no pierden el cero inicial) e indicadores económicos actualizados.
2.  **Plantilla en Google Sheets Autocargable:**
    *   Crea una copia de nuestra [Plantilla de Google Sheets Oficial](https://docs.google.com/spreadsheets/d/1DemoTemplateChileData/copy).
    *   La plantilla utiliza fórmulas nativas como `=IMPORTDATA("https://cdn.datos.cl/latest/indicadores.csv")` para cargar de forma automática la UF, el Dólar y la UTM del día cada vez que abras la hoja de cálculo.

---

## 🗺️ Estructura del Modelo de Datos

El dataset consolidado incluye las siguientes tablas:

### 1. `comunas`
La división político-administrativa con códigos **CUT** oficiales de 5 dígitos (con formato de texto para evitar que Excel elimine los ceros iniciales como en el caso de comunas de la Región de Tarapacá).

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `codigo_comuna` | `VARCHAR` | Código CUT de la comuna (5 chars) | `"01101"` |
| `nombre_comuna` | `VARCHAR` | Nombre oficial normalizado con acentos | `"Iquique"` |
| `nombre_comuna_clean`| `VARCHAR` | Nombre en minúsculas y sin acentos | `"iquique"` |
| `codigo_provincia` | `VARCHAR` | Código CUT de la provincia (3 chars) | `"011"` |
| `nombre_provincia` | `VARCHAR` | Nombre oficial de la provincia | `"Iquique"` |
| `codigo_region` | `VARCHAR` | Código CUT de la región (2 chars) | `"01"` |
| `nombre_region` | `VARCHAR` | Nombre oficial de la región | `"Tarapacá"` |
| `latitud_cabecera` | `DOUBLE` | Latitud de la capital comunal | `-20.2138` |
| `longitud_cabecera`| `DOUBLE` | Longitud de la capital comunal | `-70.1508` |
| `poblacion_estimada`| `INTEGER`| Proyección de población del INE para el año actual | `223400` |

### 2. `indicadores`
Serie de tiempo con valores económicos diarios de referencia del Banco Central de Chile.

| Columna | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `fecha` | `DATE` | Fecha de aplicación (YYYY-MM-DD) | `2026-05-30` |
| `codigo_indicador` | `VARCHAR` | Identificador corto (`uf`, `dolar`, `utm`, `euro`) | `"uf"` |
| `valor` | `DOUBLE` | Valor en Pesos Chilenos (CLP) | `39420.50` |

---

## 🛠️ Licencias y Atribución Legal

Este proyecto recopila y normaliza información pública bajo la Ley de Transparencia de Chile (Nº 20.285).
*   **Códigos Territoriales:** Fuente SUBDERE / INE. Licencia Pública de Datos Abiertos.
*   **Población:** Estimaciones y Proyecciones de Población del Instituto Nacional de Estadísticas (INE).
*   **Indicadores Económicos:** API de Datos del Banco Central de Chile.
*   **Distribución:** El dataset consolidado y el código de los transformadores se distribuyen bajo la licencia [Creative Commons Atribución 4.0 Internacional (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/deed.es). Puedes usarlo con fines comerciales siempre que menciones a `chile-data-core` y a las fuentes gubernamentales de origen.

---

## 📢 Nota sobre la Fase de Validación

> [!NOTE]
> Este proyecto se encuentra actualmente en **Fase de Validación de Tracción**. Si encuentras útiles estos datos para tus flujos de trabajo diarios, por favor **danos una estrella ⭐ en GitHub** o abre un Issue sugiriendo nuevas variables (ej. patentes comerciales, presupuestos SINIM, datos SII). Esto nos ayudará a justificar el costo de mantener la API dinámica en tiempo real y agregar más sets de datos chilenos.
