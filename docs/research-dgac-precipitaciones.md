# Candidato de investigación — precipitaciones diarias históricas DGAC (2013–2026)

**Carril:** `under-review` / `candidate`. **No está todavía en el
bundle estable, la API pública `ChileHub` ni el catálogo de capas
publicables.** El CSV y su metadata se generan como artefactos de un
workflow de investigación independiente.

**Fuente primaria:** Dirección General de Aeronáutica Civil (DGAC),
[datos.gob.cl](https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil),
API CKAN y archivos mensuales CSV; revisión del catálogo: 16–17 de
octubre de 2026.

## Valor científico y alcance

El extractor produce observaciones diarias de lluvia en milímetros por estación
meteorológica, sin interpolación ni agregación comunal ficticia. Usos:
estacionalidad, tendencias interanuales, frecuencia de días lluviosos,
precipitaciones extremas y comparaciones entre estaciones con cobertura
temporal suficiente. Los cambios de estación, la falta de datos y la
calidad histórica son límites fundamentales para inferir tendencias
climáticas.

El valor agregado de chile-hub es consolidar **143 archivos-mes validados
de 144 recursos mensuales declarados bajo paquetes abiertos**, normalizar los CSV sin encabezados, preservar
valores faltantes, detectar duplicados y guardar procedencia, licencia
y hashes SHA-256 de cada archivo.

### Períodos y restricciones

| Año | Paquetes aprovechables | Meses esperados | Licencia CKAN |
|---|---:|---:|---|
| 2013 | 2 semestres | 12 | CC BY |
| 2014 | Ninguno redistribuible confirmado | 0 | Paquete legado CC-NC, excluido |
| 2015 | Segundo semestre | 6 | CC BY |
| 2016–2023 | 2 semestres por año | 96 | CC BY |
| 2024 | 2 semestres | 12 | CC BY (I), CC0 (II) |
| 2025 | 2 semestres | 12 | CC0 |
| 2026 | Primer semestre | 6 | CC0 |

**Total: 144 meses de paquetes abiertos identificados, 143 meses incorporados
tras cuarentena de enero 2017.** Los huecos de 2014 y 2015-I
**no significan que no lloviera ni que la DGAC no midiera**: datos
históricos aparecen en el paquete
[2719](https://datos.gob.cl/dataset/2719), que declara **CC-NC**.
Como `chile-hub` permite usos comerciales, no se mezclan en el archivo
redistribuible sin resolver las restricciones de uso. El segundo
semestre de 2026 no está publicado en el catálogo inspeccionado.
**No llamar la serie «continua 2013–2026».**

**Integridad:** enero de 2017 figura como `Precipitacion_012017.csv` pero
su contenido tiene columnas `T.Maxima` y `T.Minima` (temperaturas).
Por tanto, ese mes queda en cuarentena con motivo explícito en
`quarantined_source_months`, sin imputación ni interpretación como lluvia.

Las publicaciones antiguas presentan diferencias reales que el
extractor debe gestionar: nombres inconsistentes de recursos (2015,
2021 y julio 2023), dos cargas de septiembre 2022, duplicado de julio
2015 y un paquete separado de XLSX de 2025 con errores de clasificación
(que no se utiliza). Los duplicados se aceptan solo si el SHA-256 de
ambas descargas coincide; discrepancias **bloquean** la publicación.

## Reproducibilidad

```bash
# Histórico completo, por defecto:
python scripts/research_dgac_precipitaciones.py \
  --output /tmp/precipitaciones_dgac_historico_2013_2026.csv

# Subconjunto para regresión o diagnóstico, sin cambiar el catálogo:
python scripts/research_dgac_precipitaciones.py \
  --start-year 2024 --end-year 2025 \
  --output /tmp/precipitaciones_dgac_2024_2025.csv

python -m unittest discover -s tests \
  -p 'test_research_dgac_precipitaciones.py' -v
```

La ejecución crea un CSV **ordenado por fecha y estación** con
granularidad `(fecha, id_estacion)`, más un JSON `*.metadata.json`
con fechas, total de meses, observaciones, estaciones, faltantes,
conteo por año, hashes originales, licencias, duplicados y períodos
deliberadamente excluidos.

| Campo | Tipo / significado |
|---|---|
| `fecha` | ISO 8601 |
| `id_estacion` | Código DGAC como texto (6 dígitos) |
| `nombre_estacion` | Nombre observado |
| `latitud_dms` | Latitud tal como está en fuente, grados/minutos/segundos |
| `altitud_m` | Altitud |
| `precipitacion_mm` | Precipitación diaria en mm, vacío = sin dato |
| `url_fuente` | URL específica del recurso oficial |
| `licencia_fuente` | `cc-by` o `cc-zero` del paquete CKAN |

No se convierten valores faltantes en cero, no se asignan códigos
CUT sin verificación, ni se calculan promedios comunales a partir de
estaciones aisladas.

**Control de calidad:** años/meses dentro del recurso, mínimo de 100
filas por archivo, estaciones identificadas, lluvia no negativa,
claves estación-fecha únicas, todos los meses de cada paquete
declarado, licencias aceptadas y controles SHA-256 de duplicados.
**Falla cerrado:** si un paquete abierto no puede ser recuperado o
normalizado, el comando termina sin producir un CSV parcial y CI falla.

**Compatibilidad histórica demostrada:** 2013 contiene archivos
separados por punto y coma; 2016 tiene una cabecera convencional;
2026 tiene una cabecera con nombres diferentes y tildes. El extractor
reconoce específicamente esas variantes, preserva observaciones
sin cabecera y rechaza los formatos desconocidos. Hay tests para
estos casos y para no confundir temperaturas con precipitaciones.

## Evidencias, madurez y gates

- **Baseline 2024–2025 (certificado):** [GitHub Actions
  #38987688576](https://github.com/cortega26/chile-hub/actions/runs/38987688576),
  24 CSV, **24.123 registros**, **33 estaciones**, **7/7 tests**.
  SHA-256:
  `ce3da5259d9b316bebb6aa027da8a77cb8210601bf4c2925af7c14354f0495b5`.
- **Histórico ampliado (certificado 2026-10-17):**
  [workflow #38991196698](https://github.com/cortega26/chile-hub/actions/runs/38991196698)
  **PASS** con los CSV oficiales. El extractor consolidó **141.436
  observaciones, 33 estaciones, 143 meses** en `2013-01-01/2026-06-30`.
  SHA-256 del CSV:
  `0e0605843518a4f597d9e3cbed8b3840de092ef76b1fdc6472c7a294e89914a5`.
  [Descargar CSV + metadata](https://github.com/cortega26/chile-hub/actions/runs/38991196698/artifacts/12084869269)
  (artefacto temporal, expira el 16 de noviembre de 2026).
  La extracción es reproducible en esta corrida; la disponibilidad futura
  de archivos depende del portal oficial.

**Antes de promoción a la API principal:** validar cobertura mensual
y densidad por estación, anomalías y cambios instrumentales, revisar
las limitaciones históricas, crear `DatasetSpec`, contrato, registro,
validadores, CI canónica y snapshots estables sin datos falsos.
El chequeo heredado de `perfil_territorial_comunal` se gestiona
en [issue #185](https://github.com/cortega26/chile-hub/issues/185),
independiente de esta investigación.

**Citación:** DGAC, *Precipitaciones diarias por estación*, datos.gob.cl
(fuente primaria, licencia por paquete); Carlos Ortega,
*chile-hub* (software), https://doi.org/10.5281/zenodo.22968698.
