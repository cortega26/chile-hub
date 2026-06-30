# B2.2 — Research: Resultados electorales, autoridades electas y partidos políticos

> **Plan 022 · Ola B2.2 · Fecha: 2026-06-30**
> **Clasificación general:** 🟢 `open-attribution` para agregados, 🔴 `restricted`
> para datos personales (Ley 19.628).
> **Decisión de diseño:** separar en 3 datasets distintos por naturaleza de datos.

## 1. Línea roja (no negociable)

Los siguientes datos NO se extraen, procesan, almacenan ni publican bajo ninguna
circunstancia:

- Padrón electoral nominativo
- RUN / RUT de electores
- Domicilio electoral
- Local o mesa de votación asociada a una persona
- Afiliación individual a partido político
- Cualquier dato que permita perfilar, identificar o rastrear votantes individuales

**Solo se trabajan:**
- Resultados electorales **agregados** (por comuna/mesa/distrito/circunscripción)
- **Institucionales:** autoridades electas, cargos públicos, partidos políticos
- **Metadatos:** fechas de elección, tipo, vuelta, estado del resultado

Esta línea roja fue validada en la revisión legal de Fase 3
(`docs/legal/fase-3-legal-review.md` §3) y es **compuerta dura del plan**: si una
fuente solo ofrece datos con RUN o requiere Clave Única para consultas, se descarta.

## 2. Fuentes evaluadas

### 2.1 TRICEL — Resultados oficiales definitivos

| Dimensión | Hallazgo |
|-----------|----------|
| **URL** | `https://tribunalcalificador.cl/resultados-de-elecciones-res/` |
| **Cobertura** | Presidencial, Senadores, Diputados, Plebiscitos, Primarias, Gobernadores Regionales, Convencionales Constituyentes |
| **Años** | 1988–2024 |
| **Formatos** | Excel (.xlsx para ≥2013, .xls para años anteriores), PDFs (solo sentencias) |
| **Nivel geográfico** | Nacional (presidencial), Circunscripción Senatorial (senadores), Distrito (diputados), Regional (gobernadores). **No directamente por comuna.** |
| **Descarga directa** | ✅ Links directos tipo `tribunalcalificador.cl/wp-content/uploads/...` |
| **API** | ❌ No tiene |
| **Licencia** | Datos públicos oficiales. Resultados sancionados por TRICEL como información pública. |
| **Fragilidad** | **MEDIA** — Las URLs de archivos pueden cambiar. El portal WordPress es estable pero los archivos se reorganizan ocasionalmente. Los links en la página pueden no reflejar los archivos más recientes (verificado: link de diputados 2021 retornó 404 en 2026-06-30). |
| **Carga de datos personales** | ✅ **NINGUNA.** Solo resultados agregados por territorio. |

**Conclusión:** 🟢 **Viable como fuente primaria para resultados electorales.**
Requiere verificación de URLs antes de codificar. No tiene datos por comuna
directamente — mapear distritos/circunscripciones a comunas requiere cruzar con
el dataset `distritos_electorales` existente.

### 2.2 SERVEL — Resultados históricos y datos abiertos

| Dimensión | Hallazgo |
|-----------|----------|
| **Portal principal** | `https://www.servel.cl/centro-de-datos/resultados-electorales-historicos-gw3/` |
| **Datos abiertos** | `https://www.servel.cl/centro-de-datos-gk7l/estadisticas-de-datos-abiertos-4zg/` |
| **Archivo histórico** | `https://archivo.servel.cl/` |
| **Cobertura** | Presidencial, parlamentarias, municipales, CORE, GORE, plebiscitos, primarias, convencionales (1989–2025) |
| **Formatos** | **Modernos (2013–2025):** Power BI dashboards interactivos **sin descarga directa**. **Legado (1989–2009):** HTML estático en `historial.servel.cl/SitioHistorico/`. **Participación:** subpáginas por año con posible descarga Excel (no confirmada). |
| **Nivel geográfico** | Comuna (en dashboards e informes de participación); los dashboards permiten drill-down hasta comuna |
| **Descarga directa** | ⚠️ **No verificada.** Las páginas de "Datos Abiertos" enlazan a subpáginas, no a archivos. Los dashboards Power BI no exponen exportación programática. |
| **API** | ❌ No tiene |
| **Licencia** | Datos públicos electorales. Sin restricciones de redistribución visibles. |
| **Fragilidad** | **ALTA** — Los dashboards Power BI no son scrapeables de forma confiable. Las páginas HTML legacy pueden cambiar. La estructura de subpáginas de participación es profunda y heterogénea. |
| **Carga de datos personales** | ✅ **NINGUNA** en resultados/participación. ⚠️ Las secciones de "Padrón electoral" y "Afiliados a partidos" contienen datos agregados pero deben verificarse. |

**Conclusión:** 🟡 **No viable como fuente primaria para extracción automática.**
Los dashboards Power BI no son descargables; el HTML legacy es frágil. Útil
como referencia y para verificación cruzada, pero no como fuente de pipeline.

### 2.3 Cámara de Diputadas y Diputados — Datos abiertos legislativos

| Dimensión | Hallazgo |
|-----------|----------|
| **URL** | `https://opendata.camara.cl/` (base); endpoints en `pages/` |
| **Endpoints** | `diputados_vigentes.aspx`, `diputados_periodo.aspx`, `periodo_actual.aspx`, `periodos.aspx`, `legislaturas.aspx`, `comisiones_vigentes.aspx`, `sesiones.aspx`, `votacion_boletin.aspx`, `votacion_detalle.aspx` |
| **Formato** | **XML** (sin JSON/CSV) |
| **Cobertura** | Diputadas y diputados vigentes e históricos por período legislativo, comisiones, sesiones, votaciones |
| **Nivel de detalle** | Nombre, partido, distrito, período legislativo (por diputado/a). Las votaciones incluyen detalle por boletín. |
| **Licencia** | "Libre de trabas o restricciones" según el portal. |
| **Fragilidad** | **BAJA** — Endpoints estables, formato XML estructurado, mantenido por el Congreso. |
| **Carga de datos personales** | ✅ **NINGUNA.** Datos de cargos públicos (diputados/as en ejercicio). |

**Conclusión:** 🟢 **Viable como fuente primaria para `autoridades_electas`**
(diputados/as). El endpoint más valioso es `diputados_vigentes.aspx`: devuelve
XML con nombre, partido, distrito, y período de cada diputado/a en ejercicio.

### 2.4 Senado — Datos abiertos legislativos

| Dimensión | Hallazgo |
|-----------|----------|
| **URL** | `https://www.senado.cl/transparencia/datos-abiertos-legislativos` |
| **Formato** | **XML** (proyectos de ley tramitados) |
| **Cobertura** | Proyectos legislativos desde 2012. **No incluye** senadores, partidos ni períodos en la sección de datos abiertos visible. |
| **Utilidad para este plan** | **BAJA** — El portal visible solo ofrece datos de proyectos (tramitación), no de autoridades. |
| **Fragilidad** | **BAJA** |
| **Carga de datos personales** | ✅ **NINGUNA** |

**Conclusión:** 🟡 **No viable para autoridades electas** con la información
disponible. La lista de senadores vigentes probablemente existe en otra sección
del sitio pero no en la sección de "datos abiertos" documentada. Se necesita más
investigación o usar fuentes alternativas (BCN, Wikipedia, Wikidata).

### 2.5 BCN — SIIT Elecciones históricas

| Dimensión | Hallazgo |
|-----------|----------|
| **URL** | `https://www.bcn.cl/siit/elecciones_historicas/` |
| **Cobertura** | Presidenciales, Senatoriales, Diputados, Municipales, Alcaldes, Concejales, CORES, Plebiscitos desde 1989 |
| **Formato** | Páginas HTML interactivas con parámetros `?tipo=`. Sin descargas directas visibles. |
| **Origen de datos** | TRICEL (resultados definitivos sancionados) |
| **Fragilidad** | **MEDIA** — Los datos vienen de TRICEL, así que BCN es una capa intermedia. Si TRICEL es accesible directamente, BCN no agrega valor. |

**Conclusión:** 🟡 **Redundante con TRICEL.** Si TRICEL ofrece descargas
directas, no hay ventaja en scrapear BCN. Si TRICEL deja de estar accesible,
BCN puede ser un plan B.

### 2.6 Wikidata — Autoridades y partidos (fuente complementaria)

| Dimensión | Hallazgo |
|-----------|----------|
| **URL** | `https://www.wikidata.org/` (SPARQL endpoint: `query.wikidata.org`) |
| **Cobertura** | Autoridades electas, partidos políticos, períodos, cargos |
| **Formato** | JSON vía SPARQL, CC0 |
| **Utilidad** | Complementaria para `autoridades_electas` y `partidos_politicos`. |
| **Fragilidad** | **BAJA** |

**Conclusión:** 🟢 **Complemento útil.** Wikidata tiene entradas estructuradas
para senadores, diputados, alcaldes y partidos chilenos con referencias a BCN.
Puede usarse para enriquecer datos desde fuentes oficiales.

## 3. Decisión de arquitectura

### ¿Por qué no hacer `resultados_electorales` primero?

Los resultados electorales por comuna son el dataset de mayor valor, pero
tienen dos bloqueantes:

1. **TRICEL no publica por comuna para parlamentarias.** Los Excel de diputados
   y senadores están por distrito/circunscripción. Mapear a comuna requiere
   cruzar con `distritos_electorales`, y el mapeo distrito→comunas no es 1:1
   (varias comunas comparten distrito).
2. **Los dashboards Power BI de SERVEL no son scrapeables de forma confiable.**
   La alternativa sería scrapear las páginas HTML legacy de historial.servel.cl
   (1989–2009), que es frágil y solo cubre hasta 2009.

**Decisión:** diferir `resultados_electorales` hasta que aparezca una fuente
estructurada estable con datos por comuna (ej. un mirror en datos.gob.cl, un
export CSV oficial de SERVEL, o una API estable).

### ¿Qué construir ahora?

En orden de dificultad creciente:

```
autoridades_electas  (S-M) → partidos_politicos  (S) → resultados_electorales  (L, diferido)
```

## 4. Plan de implementación recomendado

### 4.1 `autoridades_electas` — MVP (esfuerzo S-M, riesgo LOW)

**Fuentes:**
- Cámara XML: `diputados_vigentes.aspx` → XML con diputados/as vigentes
- BCN o Wikidata: senadores vigentes (SPARQL o scraping de página)
- SERVEL o BCN: alcaldes vigentes (lista acotada, 345 municipios)
- Gobernadores regionales: lista acotada (16 regiones)

**Método de extracción:**
1. **Diputados/as:** GET al endpoint XML de la Cámara, parsear con
   `xml.etree.ElementTree`. Extraer: nombre, partido, distrito, período.
2. **Senadores/as:** Wikidata SPARQL query para senadores chilenos vigentes
   (CC0, sin restricciones de licencia). Alternativa: scraping ligero de la
   página de BCN o Wikipedia.
3. **Alcaldes/alcaldesas:** Wikidata SPARQL o scraping ligero de BCN.
4. **Gobernadores/as regionales:** Wikidata SPARQL (16 registros, trivial).

**Schema propuesto:**

```text
dataset: autoridades_electas

id_autoridad (clave interna)
nombre
cargo           # diputado | senador | alcalde | gobernador_regional | presidente
institucion     # Camara de Diputados | Senado | Municipalidad de X | Gobierno Regional de X
partido
pacto
distrito_electoral
circunscripcion_senatorial
codigo_comuna   # solo para alcaldes
codigo_region   # solo para gobernadores y senadores
periodo_inicio  # YYYY-MM-DD
periodo_fin     # YYYY-MM-DD (o NULL si vigente)
estado_mandato  # vigente | finalizado | reemplazo
fuente
url_fuente
fecha_consulta
```

**Carril:** `stable_publishable` — datos públicos institucionales, CC0/CC-BY.

### 4.2 `partidos_politicos` — (esfuerzo S, riesgo LOW)

**Fuente:** SERVEL (`servel.cl/centro-de-datos/estadisticas-de-partidos-politicos/`)
o Wikidata. El registro de partidos es pequeño (~20–30 partidos) y estable.

**Método:** Wikidata SPARQL o extracción desde página estática de SERVEL. Son
pocos registros, así que incluso una compilación manual curada es viable.

**Schema propuesto:**

```text
dataset: partidos_politicos

id_partido
nombre
sigla
estado_legal    # constituido | en_formacion | disuelto
fecha_constitucion
ambito          # nacional | regional
url_fuente
fecha_consulta
```

**Carril:** `stable_publishable` — datos institucionales públicos.

### 4.3 `resultados_electorales` — Diferido (esfuerzo L, riesgo MED-HIGH)

**Condición de activación:** aparece una fuente estructurada estable con
resultados por comuna (no por distrito/circunscripción) en formato descargable
(Excel, CSV, o API). Candidatos a monitorear:
- SERVEL publica exportación CSV/Excel además de Power BI
- Un mirror en datos.gob.cl
- TRICEL agrega resultados por comuna en futuras publicaciones

**Mientras tanto:** monitorear trimestralmente. No construir.

## 5. Plan de extracción para `autoridades_electas`

### Paso 1: Diputados/as desde Cámara XML

El endpoint `https://opendata.camara.cl/pages/diputados_vigentes.aspx` (URL
exacta a confirmar) devuelve XML. La estructura esperada es:

```xml
<Diputados>
  <Diputado>
    <Nombre>...</Nombre>
    <Partido>...</Partido>
    <Distrito>...</Distrito>
    <PeriodoLegislativo>...</PeriodoLegislativo>
  </Diputado>
  ...
</Diputados>
```

Implementar con `xml.etree.ElementTree` (stdlib, sin dependencias nuevas).
Mapear distrito a código de distrito electoral desde `distritos_electorales`
existente.

### Paso 2: Senadores/as desde Wikidata SPARQL

```sparql
SELECT ?senador ?senadorLabel ?partidoLabel ?circunscripcionLabel ?inicio ?fin
WHERE {
  ?senador wdt:P39 wd:Q....  # cargo: senador de Chile
  ...
}
```

Alternativa si Wikidata no es aceptable: scrapear BCN o usar una lista curada
(son 50 senadores, estable por 8 años).

### Paso 3: Alcaldes desde Wikidata SPARQL + cruza con DPA

~345 alcaldes. Wikidata tiene la propiedad `alcalde` (P131) para municipios
chilenos. Se puede extraer con SPARQL y cruzar por `codigo_comuna`.

### Paso 4: Gobernadores desde Wikidata

16 registros, trivial.

## 6. Evaluación de criterios de inclusión

### `autoridades_electas`

| Criterio | ¿Cumple? | Evidencia |
|----------|----------|-----------|
| Fuente oficial estructurada | ✅ | Cámara XML + Wikidata SPARQL |
| Evita datos personales | ✅ | Solo cargos públicos |
| Distingue resultados definitivos | ✅ | Son autoridades en ejercicio, no resultados |
| Validable contra DPA | ✅ | Cruza por distrito, región y comuna (alcaldes) |
| Total reconciliable con fuente | ✅ | Conteo conocido: 155 diputados, 50 senadores, 345 alcaldes, 16 gores |

### `partidos_politicos`

| Criterio | ¿Cumple? | Evidencia |
|----------|----------|-----------|
| Fuente oficial estructurada | ✅ | SERVEL o Wikidata |
| Evita datos personales | ✅ | Datos institucionales, no personas |
| Validable | ✅ | Lista pequeña y verificable |

## 7. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| XML de Cámara cambia esquema | MED | Parseo defensivo con `find()` + fallback claro |
| Wikidata tiene datos desactualizados | LOW | Verificar contra fuente oficial; Wikidata es cache, no fuente primaria |
| TRICEL reorganiza archivos Excel | N/A (diferido) | Monitorear trimestral; no construir hasta tener fuente estable |
| SERVEL Power BI no scrapeable | N/A (aceptado) | No intentar scrapear Power BI; buscar fuentes alternativas |

## 8. Conclusión

**Siguiente paso inmediato: construir `autoridades_electas`.**

Es el dataset de mayor certeza técnica (XML de Cámara + Wikidata SPARQL), menor
esfuerzo (S-M), menor riesgo (LOW), y cumple todos los criterios de inclusión.
Es `stable_publishable` y entra al bundle público. Abre el dominio electoral sin
tocar datos personales.

**`partidos_politicos`** se construye en segundo lugar (S, LOW, `stable_publishable`).

**`resultados_electorales`** permanece en `needs-research` hasta que aparezca
una fuente estructurada por comuna. Se agenda una revisión trimestral.

---

*Research cerrado según Plan 022 — Ola B2.2. Revisión legal en
`docs/legal/fase-3-legal-review.md` §3. Listo para avanzar a implementación.*
