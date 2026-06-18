# Política de Compatibilidad de Datasets para chile-hub

Este documento define las reglas de compatibilidad de esquema para los datasets
del hub y la clasificación de severidad de cambios en el tiempo. Complementa la
[política de versionamiento de software](versioning-policy.md), que rige el
versionado del paquete Python y del CLI.

---

## 1. Separación de responsabilidades

| Mecanismo | Alcance | Dónde se registra |
|---|---|---|
| SemVer (`pyproject.toml`) | API pública, CLI, esquemas de salida | `pyproject.toml` → tags Git → PyPI |
| Severidad de changelog | Cambios estructurales por dataset | `dataset_changelog.json` (por build) |

La severidad de changelog permite que consumidores y CI distingan
automáticamente entre un cambio compatible (nueva columna anulable) y uno
rompedor (eliminación de columna requerida), sin necesidad de leer el diff
completo entre builds.

---

## 2. Taxonomía de severidad

| Severidad | Significado | Impacto en consumidores |
|---|---|---|
| `none` | Sin cambios detectados | Ninguno |
| `patch` | Cambios solo de datos (registros, campos sin tocar el contrato de esquema) | Mínimo; posible variación en cardinalidad |
| `minor` | Dataset nuevo, o columnas anulables agregadas al contrato | Compatible hacia atrás; los consumidores existentes no se rompen |
| `major` | Cambio rompedor en el contrato de esquema | Consumidores existentes deben adaptarse |

---

## 3. Reglas de clasificación por tipo de cambio

### 3.1 Cambios MAJOR (rompedores)

| Cambio | Ejemplo |
|---|---|
| Eliminar una columna requerida del contrato | Quitar `nombre_comuna` de `required_columns` |
| Cambiar la clave primaria | Pasar de `["codigo_comuna"]` a `["codigo_region", "codigo_comuna"]` |
| Cambio incompatible de tipo de columna | `string` → `integer`, `float` → `string`, `date` → `string` |
| Agregar una columna no-anulable al contrato | Nueva columna `codigo_pais` requerida, sin aparecer en `nullable_columns` |
| Renombrar una columna | `nombre_comuna` → `nombre_comuna_oficial` |
| Eliminar columnas del contrato | Cualquier columna presente en el contrato anterior que desaparece |

### 3.2 Cambios MINOR (compatibles)

| Cambio | Ejemplo |
|---|---|
| Agregar un dataset nuevo | Primera aparición en `dataset_changelog.json` |
| Agregar una columna anulable al contrato | Nueva columna `telefono_contacto` declarada en `nullable_columns` |
| Agregar columnas requeridas que ya existían en los datos | Formalizar en contrato una columna que los datos ya tenían |

### 3.3 Cambios PATCH (solo datos)

| Cambio | Ejemplo |
|---|---|
| Delta de registros sin cambios de contrato | 345 → 346 comunas |
| Campos agregados o eliminados en los datos pero no en el contrato | Columna derivada interna aparece/desaparece |
| Cambio de `source_mode` o `freshness_status` | `live` → `fallback`, `fresh` → `stale` |

### 3.4 Sin cambios (`none`)

El dataset es idéntico al build anterior en todos los aspectos monitoreados:
registros, campos, modo de fuente, frescura, validación y contrato.

---

## 4. Compatibilidad de tipos de columna

| Tipo anterior | Tipo nuevo | Compatible | Severidad |
|---|---|---|---|
| `string` | `string` | Sí | — |
| `integer` | `integer` | Sí | — |
| `float` | `float` | Sí | — |
| `integer` | `float` | Sí (widening) | `minor` |
| `float` | `integer` | No (narrowing) | `major` |
| `string` | `integer` | No | `major` |
| `integer` | `string` | No | `major` |
| `string` | `date` | No | `major` |
| `date` | `string` | No | `major` |
| `boolean` | `string` | No | `major` |
| Cualquiera | `boolean` | No | `major` |

El único widening reconocido es `integer` → `float`, porque todos los enteros
son representables como flotantes sin pérdida de información en el rango de
trabajo del hub.

---

## 5. Campos del changelog por dataset

Cada entrada en `dataset_changelog.json` incluye, además de los campos
existentes de comparación de datos, los siguientes campos de severidad:

| Campo | Tipo | Descripción |
|---|---|---|
| `change_severity` | `string` | `none`, `patch`, `minor` o `major` |
| `breaking_changes` | `list[string]` | Descripciones legibles de cambios rompedores |
| `new_columns` | `list[string]` | Nombres de columnas nuevas agregadas al contrato |
| `removed_columns` | `list[string]` | Nombres de columnas eliminadas del contrato |
| `primary_key_changed` | `bool` | `true` si la clave primaria del contrato cambió |
| `contract_changed` | `bool` | `true` si cualquier campo estructural del contrato cambió |

Estos campos se calculan comparando los contratos de esquema
(`contracts/datasets/<dataset>.schema.json`) entre el build actual y el
anterior. Los campos relevantes del contrato se almacenan en
`pipeline_metadata.json` durante el build para permitir la comparación.

---

## 6. Deprecación de datasets

Deprecar un dataset requiere:

1. Cambiar su `maturity_status` a `deprecated` en `source_registry.json`.
2. Mantener el dataset en el build y el contrato durante al menos una versión
   minor completa.
3. Anunciar la deprecación en `dataset_changelog.json` (el cambio de madurez
   aparece como cambio de metadatos, severidad `minor`).
4. Solo después de una versión minor con el aviso, el dataset puede eliminarse
   (lo que constituye un cambio `major`).

---

## 7. Referencias

- [Política de Versionamiento](versioning-policy.md)
- [Plan 008: Madurez de fuente y contratos](../plans/008-hardening-source-readiness-schema-contracts-quality.md)
- [Source Registry](../data/source_registry.json)
- [Contratos de esquema](../contracts/datasets/)
