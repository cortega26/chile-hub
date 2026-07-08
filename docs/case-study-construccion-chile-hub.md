# Caso de estudio: cómo está construido chile-hub

> Un proyecto de datos abiertos mantenido por una persona, diseñado para que no
> tengas que confiar ciegamente en los datos. Este documento explica las decisiones
> de arquitectura, los tradeoffs y lo que aprendí en el camino.

---

## 1. El problema

Los datos públicos chilenos existen, pero **consumirlos es una tarea de
ingeniería en sí misma**. Están dispersos en portales gubernamentales con
formatos inconsistentes: archivos Excel con celdas fusionadas, shapefiles sin
documentar, APIs que requieren tokens, sitios que solo responden con
JavaScript. Cada investigador o analista pasa horas — a veces días — limpiando,
uniendo y validando antes de poder hacer su trabajo real.

El ecosistema open-data chileno tiene portales excelentes (datos.gob.cl, el
visor territorial del INE, los shapefiles de BCN), pero **ninguno resuelve la
última milla**: entregar datos limpios, documentados, cruzables y listos para
una línea de código.

**La pregunta que motivó chile-hub no fue "¿cómo consigo más datasets?", sino
"¿cómo hago que los datasets que ya existen sean realmente usables?".**

---

## 2. La apuesta técnica

En lugar de acumular capas, el proyecto apuesta por un **pipeline determinista
con trazabilidad completa** y una regla no negociable: **si una validación
falla, el pipeline aborta**. No se publican datos parcialmente válidos.

La arquitectura sigue un modelo lineal de 4 etapas:

```
Extracción → Construcción → Validación → Publicación
```

Cada etapa depende del éxito completo de la anterior. No hay atajos, no hay
modo "best-effort". Si el extractor del INE devuelve 345 comunas en lugar de
346, todo el pipeline se detiene con un mensaje descriptivo.

**¿Por qué tan estricto?** Porque los datos se usan en contextos donde un error
silencioso es peor que una ausencia declarada. Un investigador que cruza
resultados educacionales con pobreza comunal necesita saber que los joins por
`codigo_comuna` son íntegros. Si publicáramos datos con integridad referencial
rota, estaríamos creando el problema que prometimos resolver.

Esta decisión está documentada en
[ADR-001](adr/ADR-001-pipeline-lineal-determinista.md) y cruza todo el
proyecto: los extractores heredan de `BaseExtractor`, los validadores viven en
`src/validation.py`, y el script `scripts/verify_pipeline.py` ejecuta la
verificación post-build en CI.

---

## 3. Decisiones de arquitectura que definieron el proyecto

### 3.1 CUT como VARCHAR(5), nunca como entero

El Código Único Territorial es el identificador que une todas las capas:
región (2 dígitos), provincia (3) y comuna (5). En casi todos los portales
chilenos, el CUT se representa como entero — y eso rompe los joins.

`01101` (Iquique) como entero es `1101`. Pierdes el cero inicial que identifica
la región de Tarapacá. Multiplica eso por 346 comunas, 15 datasets y miles de
joins, y tienes una fuente inagotable de bugs silenciosos.

**Decisión:** todo CUT es `VARCHAR` de ancho fijo desde el momento de la
extracción. Esta regla es una de las 5 invariantes no negociables del proyecto
([ADR-002](adr/ADR-002-codigos-cut-varchar-fijo.md)).

### 3.2 Contratos de esquema como código

Cada dataset tiene un contrato JSON Schema en `contracts/datasets/` que define:

- Columnas requeridas, sus tipos y nulabilidad
- Clave primaria
- Anchos fijos para columnas CUT
- Registro esperado (cuando aplica)
- Política de cobertura (`full` / `partial` / `not_applicable`)
- Formatos de salida autorizados

El pipeline valida **cada contrato en cada build** vía
`scripts/verify_pipeline.py`. Si un extractor cambia el esquema sin actualizar
el contrato, el build falla. Si el contrato espera 346 registros y llegan 345,
el build falla.

Esto convierte una promesa de documentación en una **verificación ejecutable**
([ADR-005](adr/ADR-005-contratos-esquema-json-schema.md)). Los contratos son
la fuente de verdad del esquema; el README y la landing se generan desde ellos,
no al revés.

### 3.3 Carriles de publicación: no todo lo que se extrae se publica

No todos los datasets tienen la misma madurez. El sistema de carriles
([ADR-004](adr/ADR-004-carriles-de-publicacion.md)) separa:

- **`stable_publishable`** — fuente estable, licencia clara, validación
  completa. Entra al bundle público.
- **`candidate`** — fuente frágil, scraping, o licencia en revisión. Se
  extrae, se valida, pero **no** se incluye en el bundle. Tiene fecha de
  revisión (`review_by`) y regla de salida si no madura.

Esta separación permite experimentar con fuentes inestables sin degradar la
calidad del bundle. Actualmente 13 capas son `live` y 2 son `fallback`; 0
términos en revisión.

### 3.4 Versionado dual: software y datos

El paquete Python sigue SemVer: `fix` para correcciones, `feat` para nuevas
capacidades, `BREAKING` para cambios de API. Pero los datos tienen su propio
ritmo: algunos se actualizan a diario (indicadores económicos), otros son
decenales (censo).

Separar el versionado de software del versionado de datos
([ADR-003](adr/ADR-003-versionado-semantico-dual.md)) permite liberar
correcciones sin disparar una nueva versión de datos, y actualizar datos sin
inflar el changelog. La frescura de cada dataset se monitorea por separado en
`hub_health.json`.

---

## 4. Resultados

A junio de 2026, el proyecto produjo:

| Métrica | Valor |
|:---|---:|
| Capas de datos | 15 |
| Modo `live` (extracción directa) | 13 de 15 |
| Modo `fallback` (respaldo curado) | 2 de 15 |
| Calidad promedio | **93.5 / 100** |
| Nota A | 14 de 15 capas |
| Auditoría legal (redistribuible) | 15 de 15 (`ready`) |
| Tests | 490+ (372 pytest + verificaciones de pipeline) |
| ADRs | 5 |
| Contratos JSON Schema | 15 |
| Refresh automatizado | Diario vía CI/CD |

El pipeline corre íntegro en GitHub Actions, produce artefactos Parquet,
DuckDB, SQLite, JSON y Excel, y publica el bundle en cada release. La landing
en `tooltician.com/chile-hub/` se regenera con cada build.

**Lo que no se ve en la tabla:** 0 datos corruptos publicados. El pipeline
falló varias veces — por fuentes caídas, cambios de esquema no anunciados,
archivos Excel renombrados en el portal del MINEDUC — y en cada caso **abortó
antes de publicar**. El fail-loud funcionó exactamente como fue diseñado.

---

## 5. Aprendizajes

### Lo que funcionó

- **Contratos de esquema verificados automáticamente.** Es la decisión de mayor
  retorno. Los contratos son la fuente de verdad, el README se genera desde
  ellos, y el drift de esquema se detecta sin intervención humana.
- **Fail-loud desde el día uno.** Cada vez que una fuente cambió sin avisar, el
  pipeline lo detectó. Si hubiéramos empezado con warnings, probablemente
  habríamos publicado datos inconsistentes sin darnos cuenta.
- **Fuentes oficiales directas, no portales agregadores.** Extraer desde la URL
  del organismo emisor (BCN, INE, MINEDUC, BCCh) elimina intermediarios y da
  claridad legal. La auditoría de redistribución (`redistribution_report.md`)
  es exhaustiva por dataset, no una afirmación genérica sobre "datos abiertos".

### Lo que fue difícil

- **Mantener 15 extractores como única persona.** Cada fuente tiene su
  idiosincrasia: una API JSON, un Excel con celdas fusionadas, un archivo RAR
  con contraseña, un portal que requiere POST con JavaScript. El costo de
  mantenimiento no es escribir el extractor, es **monitorear que no se rompa**
  cuando la fuente cambia.
- **El scraping gubernamental es frágil por definición.** `finanzas_municipales`
  tiene 3 de 346 comunas porque el portal SINIM requiere scraping
  JavaScript/POST y no se ha estabilizado. Está honestamente etiquetado como
  `🔶 parcial` mientras se trabaja en una solución.
- **El balance entre "más datasets" y "más confiabilidad".** La tentación de
  agregar capas existe, pero cada capa nueva es un compromiso de mantenimiento
  permanente. La regla: solo entra lo que tiene valor de cruce por
  `codigo_comuna` y pasa los 7 criterios de inclusión documentados en
  `docs/dataset-inclusion-criteria.md`.

### Lo que haría distinto

- **Tests de integración desde el primer extractor**, no después. Los
  extractores que se escribieron sin tests tempranos requirieron más refactors.
- **Un language server para JSON Schema.** Escribir contratos a mano es
  propenso a errores de tipeo; una herramienta que valide en el editor habría
  ahorrado ciclos de build.
- **Migrar el build_dev_db monolítico antes.** La refactorización a
  `src/builders/` ocurrió tarde y fue más costosa de lo necesario.

---

## 6. Cómo usar chile-hub

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()

# Cargar cualquier capa como DataFrame de Polars
comunas = hub.load_polars("comunas")
censo = hub.load_polars("censo_comunal")

# Cruzar por código de comuna
cruce = comunas.join(censo, on="codigo_comuna", how="left")
```

También puedes consumir los archivos directamente desde la [landing
page](https://tooltician.com/chile-hub/) o desde el [bundle
ZIP](https://github.com/cortega26/chile-hub/releases) sin instalar nada.

---

## Referencias

- [README del proyecto](https://github.com/cortega26/chile-hub/blob/main/README.md)
- [Pipeline y validación](https://github.com/cortega26/chile-hub/blob/main/AGENTS.md)
- [Reporte de procedencia](https://github.com/cortega26/chile-hub/blob/main/data/normalized/provenance_report.md)
- [Auditoría legal de redistribución](https://github.com/cortega26/chile-hub/blob/main/data/normalized/redistribution_report.md)
- [Calidad de datos por capa](https://github.com/cortega26/chile-hub/blob/main/data/normalized/dataset_quality.md)
- [Salud del hub](https://github.com/cortega26/chile-hub/blob/main/data/normalized/hub_health.md)
- [Decisiones de arquitectura (ADRs)](https://github.com/cortega26/chile-hub/tree/main/docs/adr)

---

*Este caso de estudio es parte del [Plan 022](https://github.com/cortega26/chile-hub/blob/main/plans/022-plan-avance-narrativa-confiabilidad.md) — Fase 2: Narrativa técnica visible.*
