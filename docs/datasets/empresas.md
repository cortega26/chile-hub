# Empresas — Registro de Empresas y Sociedades (RES)

Dataset de constituciones de empresas y sociedades bajo el Régimen Simplificado
establecido por la Ley 20.659, publicado por el Ministerio de Economía, Fomento
y Turismo en datos.gob.cl.

## Fuente

| Campo | Valor |
|:---|:---|
| **Nombre** | Registro de Empresas y Sociedades (RES) |
| **Publicador** | Ministerio de Economía, Fomento y Turismo |
| **URL** | https://datos.gob.cl/dataset/registro-de-empresas-y-sociedades |
| **Licencia** | CC-BY 3.0 CL |
| **Formato** | CSV anual (2013–2026), delimitado por `;` |
| **Actualización** | Mensual (aproximadamente) |
| **Cobertura** | ~1.5M constituciones desde mayo 2013 |

## Esquema

| Columna | Tipo | Descripción |
|:---|:---|:---|
| `rut` | `String` | RUT de la empresa con dígito verificador (ej: `76286049-K`) |
| `razon_social` | `String` | Nombre legal de la empresa |
| `codigo_sociedad` | `String` | Tipo societario: `SPA`, `EIRL`, `SRL`, `SA`, `SC`, `SCPA`, `SCA`, `COOP`, `EE`, `FNDC`, `AGR`, `COPROP` |
| `tipo_actuacion` | `String` | Tipo de actuación registrada (generalmente `CONSTITUCION`) |
| `capital` | `Int64` | Capital declarado en pesos chilenos |
| `fecha_actuacion` | `Date` | Fecha de la primera firma de constitución |
| `fecha_registro` | `Date` | Fecha de la última firma de registro |
| `fecha_aprobacion_sii` | `Date` | Fecha de aprobación por el SII |
| `anio` | `Int32` | Año de la constitución |
| `mes` | `String` | Mes de la constitución (en español) |
| `comuna_tributaria` | `String` | Comuna del domicilio tributario |
| `region_tributaria` | `String` | Código de región del domicilio tributario (formato SII: 1–15, no CUT) |
| `comuna_social` | `String` | Comuna del domicilio social |
| `region_social` | `String` | Código de región del domicilio social (formato SII) |

## Uso

### Python

```python
from chile_hub import ChileHub

hub = ChileHub()
df = hub.load_polars("empresas")

# Top 10 comunas con mas empresas constituidas
top_comunas = (
    df.group_by("comuna_tributaria")
    .len()
    .sort("len", descending=True)
    .head(10)
)
print(top_comunas)

# Empresas constituidas por año
por_anio = df.group_by("anio").len().sort("anio")
print(por_anio)

# Filtrar por tipo de sociedad
spa = df.filter(pl.col("codigo_sociedad") == "SPA")
print(f"SpA constituidas: {spa.height}")
```

### DuckDB / SQL

```sql
-- Empresas por comuna tributaria
SELECT comuna_tributaria, count(*) AS n
FROM 'data/normalized/empresas.parquet'
GROUP BY 1 ORDER BY n DESC LIMIT 10;

-- Constituciones por año y tipo de sociedad
SELECT anio, codigo_sociedad, count(*) AS n
FROM 'data/normalized/empresas.parquet'
GROUP BY 1, 2 ORDER BY 1, 3 DESC;

-- Buscar empresa por RUT
SELECT *
FROM 'data/normalized/empresas.parquet'
WHERE rut = '76286049-K';
```

### CLI

```bash
chile-hub show empresas
chile-hub path empresas --output parquet
```

## Limitaciones

1. **Sin dirección postal.** Solo incluye comuna y región, no calle ni número.
2. **Sin actividad económica.** El RES no registra el giro o rubro de la empresa.
3. **Solo régimen simplificado.** Cubre ~88.5% de las constituciones nuevas (desde
   mayo 2013). No incluye empresas del régimen tradicional vía Diario Oficial.
4. **Solo constituciones.** No refleja modificaciones, fusiones, escisiones ni
   cese de actividades posterior a la constitución.
5. **Códigos de región SII.** Usan el formato 1–15 del SII, distinto al formato
   CUT 01–16. Para cruzar con la DPA se requiere mapeo adicional.
6. **Mayúsculas/Minúsculas.** Los nombres de empresas se normalizan a *Title Case*.
   Algunos nombres pueden diferir de la inscripción original.
7. **Duplicados posibles.** Una misma empresa puede aparecer más de una vez si
   tuvo múltiples actuaciones registradas en el RES.

## Notas de integración con chile-hub

- **Tier:** B — dataset derivado de fuente oficial con atribución requerida.
- **Join keys:** `rut` (principal). No tiene `codigo_comuna` CUT; el cruce
  territorial debe hacerse por nombre de comuna o mapeando códigos de región SII.
- **Bundle:** Incluido en el ZIP público (licencia CC-BY).
- **Actualización:** El extractor descarga y consolida los 14 CSVs anuales del
  dataset en datos.gob.cl (~40 MB total). La primera ejecución puede demorar
  varios segundos.

## Registro de cambios

- **2026-06-17:** Dataset agregado a chile-hub (extractor, validación, tests,
  documentación).

<!-- START_DATASET_SCHEMA -->

## Schema (auto-generado desde `contracts/datasets/empresas.schema.json`)

| Columna | Tipo | Ejemplo | Requerida | Nota |
|:---|:---|:---|:---:|:---|
| `rut` | `VARCHAR` | `"76286049-K"` | Sí | PK |
| `razon_social` | `VARCHAR` | `"COMERCIALIZADORA EJEMPLO SPA"` | Sí | — |
| `codigo_sociedad` | `VARCHAR` | `"SPA"` | Sí | — |
| `capital` | `INTEGER` | `5000000` | Sí | — |
| `fecha_actuacion` | `DATE` | `"2020-06-15"` | No | — |
| `anio` | `INTEGER` | `2020` | Sí | — |
| `comuna_tributaria` | `VARCHAR` | `"SANTIAGO"` | No | — |
| `region_tributaria` | `VARCHAR` | `"13"` | No | — |

<!-- END_DATASET_SCHEMA -->
