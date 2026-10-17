# Candidato de investigación — precipitaciones diarias DGAC 2024–2025

**Estado:** `under-review` / prototipo reproducible. **NO es una capa publicable,
ni está incluida en el ZIP, la API `ChileHub` o el catálogo estable.** No
incrementar el contador de datasets hasta completar los gates de ingreso.

**Fuente primaria:** Dirección General de Aeronáutica Civil (DGAC), recursos
mensuales CSV publicados en [datos.gob.cl](https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil).
Inspección del catálogo CKAN: 16 de octubre de 2026.

## Por qué vale la pena

Permite estudiar precipitación diaria, intensidad/extremos observados,
estacionalidad e irregularidad territorial por estación meteorológica. Cruce
posterior posible con series climatológicas, hidrológicas o territoriales
**solo** mediante un catálogo de estaciones con coordenadas/códigos verificados.

**Valor específico de chile-hub:** reconstruir dos años completos a partir
de 24 archivos mensuales dispersos, establecer esquema único, preservar
faltantes, validar fechas/estaciones/duplicados y registrar SHA-256 por archivo
original y por resultado.

## Fuentes exactas y permisos

| Período | Paquete CKAN | Licencia declarada |
|---|---|---|
| 2024-I | `precipitaciones-2024` | CC BY |
| 2024-II | `precipitaciones-2do-semestre-del-ano-2024` | CC0 |
| 2025-I | `precipitacion-1er-semestre-2025` | CC0 |
| 2025-II | `precipitaciones-2do-semestre-2025` | CC0 |

Consultar paquetes y URLs de archivos mediante
`https://datos.gob.cl/api/3/action/package_show?id=precipitaciones-2024`
(análogamente para los demás slugs). La licencia es por paquete y se conserva
por observación; **no** atribuir la licencia de chile-hub (MIT para el código)
a los datos de la DGAC.

**Ejemplo observado en CKAN:** recurso
`Precipitacion_072025.csv`, ID `a954e2ca-44aa-443b-8a4e-b9c5fcfd1fb7`;
estación `180005` (`Chacalluta, Arica Ap.`), fecha 2025-07-01,
precipitación 0.0. El Datastore usa valores de la **primera observación**
como nombres de columna (`180005`, `2025`, `7`, `1`, `0.0`);
consumirlo sin corregir ese problema **pierde la primera observación de cada
archivo**. El extractor prefiere el CSV original sin cabeceras.

## Ejecutar

Desde la raíz del repositorio, con Python 3.11+:

```bash
python scripts/research_dgac_precipitaciones.py \
  --output /tmp/precipitaciones_dgac_2024_2025.csv
python -m unittest tests.test_research_dgac_precipitaciones -v
```

Emite un CSV de grano `(fecha, id_estacion)` y metadatos
`precipitaciones_dgac_2024_2025.metadata.json` en la misma carpeta.

| Columna | Significado |
|---|---|
| `fecha` | ISO 8601, fecha de medición |
| `id_estacion` | Identificador DGAC como texto, seis dígitos |
| `nombre_estacion` | Etiqueta original DGAC |
| `latitud_dms` | Latitud en grados/minutos/segundos sin conversión |
| `altitud_m` | Altitud numérica de estación, metros |
| `precipitacion_mm` | Precipitación diaria, mm; campo vacío = faltante |
| `url_fuente` | CSV mensual oficial |
| `licencia_fuente` | CC BY o CC0 del paquete correspondiente |

El script exige **los 24 meses**, mínimo 100 registros por CSV, identificación
de estación, fechas dentro del mes, precipitación no negativa, unicidad de
`(fecha, id_estacion)` y licencia esperada. No genera output si falla un mes.
Los metadatos contienen trazabilidad y hashes SHA-256. Sin interpolaciones,
valores inventados, ni imputación de faltantes.

## Limitaciones y gates para promoción

1. **Descarga no certificada de extremo a extremo:** se verificó acceso al
   catálogo CKAN y a registros de su API Datastore; la descarga directa del
   CSV no pudo certificarse desde este entorno. Un CI ejecutando los 24 CSV
   es condición de aceptación, no una suposición.
2. La cobertura es por **estaciones observacionales**, no por las 346 comunas
   ni por una malla nacional; no extrapolar estaciones a comunas por el nombre.
3. Comparación longitudinal requiere comprobar cambios de estaciones,
   instrumentos, cobertura y definición de precipitación para los 24 archivos.
4. Un archivo sin cabecera se parsea por posición de 8 columnas. Cualquier
   cambio de formato falla de forma explícita para revisión.
5. Los datos anteriores a 2024 y posteriores a 2025 **no están incluidos**
   en este prototipo. La fuente publica otros períodos, pero no declarar
   cobertura sin haberlos validado.

**Salida del estado `under-review`:** verificación end-to-end en un runner con
acceso a datos.gob.cl, inspección manual de estaciones y faltantes, test de
conteos contrastado con los CSV originales, documentación de calidad y
contrato de esquema; recién entonces registrar en
`data/dataset_catalog_config.json`, `data/source_registry.json`,
`contracts/datasets/`, validadores y pipeline estándar. Revisar antes del
**2026-11-30**; si la fuente no es reproducible, archivar el candidato.

**Mini-scorecard:** valor alto · legal abierto con atribución por paquete ·
tamaño moderado (~1,8 MB de CSV crudos estimados) · cadencia semestral ·
fragilidad de descarga/formato pendiente → `under-review`.

**No afirmar:** que el dataset completo ya está publicado, que la API principal
lo expone, que el período se extrajo exitosamente o que se comprobó reducción
de tiempos frente a otros proveedores.

**Citación recomendada:** DGAC, *Precipitaciones por estación* (2024–2025),
datos.gob.cl, y Carlos Ortega, *chile-hub* como software de curación
([DOI](https://doi.org/10.5281/zenodo.22968698)).
