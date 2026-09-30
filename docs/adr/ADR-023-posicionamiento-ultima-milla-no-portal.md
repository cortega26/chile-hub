# ADR-023: chile-hub es la última milla de los datos oficiales, no un portal

**Fecha:** 2026-09-29
**Estado:** accepted (ratificado por el mantenedor al aprobar el plan, 2026-09-29)
**Decisión:**
- chile-hub se posiciona como una capa de reutilización que trabaja aguas abajo de las fuentes oficiales y de datos.gob.cl. No es un portal ni una fuente oficial.
- La misión, la visión y los principios tienen un solo dueño: la sección "Misión, visión y relación con el ecosistema oficial" de `docs/product-spec.md`.
- Ninguna superficie pública describe a chile-hub como "oficial".
- El criterio de prioridad #7 de `docs/dataset-inclusion-criteria.md` pasa a ser "valor agregado sobre la fuente oficial".
- chile-hub no buscará que datos.gob.cl lo coseche como publicador. Esto cierra la pregunta abierta #1 de ADR-010.

## Contexto

Varias superficies públicas describían a chile-hub con palabras que corresponden al Estado:

- el README lo presentaba como "el hub de datos abiertos de Chile";
- la landing y su JSON-LD lo llamaban "capa de datos oficial";
- las fichas comunales hablaban de "indicadores oficiales", aunque `perfil_territorial_comunal` es una capa derivada por chile-hub.

Ese rol ya tiene dueño. La resolución de la Subsecretaría de Hacienda del 4 de octubre de 2024, que aprueba los términos y condiciones del Portal de Datos Abiertos, establece tres cosas:

1. La Secretaría de Gobierno Digital, creada por la Ley 21.658, opera datos.gob.cl como "el repositorio de datos abiertos centralizado del Estado".
2. Publican en él las entidades del Estado integradas al portal mediante un trámite.
3. Dato abierto es el que puede ser "usado, reutilizado y redistribuido libremente por cualquier persona". Esa definición legitima el rol de reutilizador de chile-hub.

La misma resolución indica que la norma técnica de datos abiertos seguía en desarrollo.

Según la API CKAN del portal, consultada el 2026-09-29, datos.gob.cl cataloga 3.218 datasets de 273 organizaciones. Muchos exigen trabajo antes de poder cruzarse: 831 datasets tienen recursos XLSX, 354 XLS, 124 PDF y 60 RAR. Ese trabajo es justamente lo que hace chile-hub.

El producto ya operaba aguas abajo del portal: `establecimientos_salud` y `empresas` se extraen de su API. Lo que competía con el portal era el discurso, no el producto. Competir en amplitud, además, no es viable para un proyecto que mantiene una sola persona.

## Decisión

1. **Posicionamiento.** Eslogan: "La última milla de los datos oficiales de Chile". La misión, la visión, los cuatro principios (la fuente oficial manda, profundidad antes que amplitud, buen vecino del ecosistema, lo abierto sigue abierto) y la tabla de roles viven en `docs/product-spec.md`. Las demás superficies llevan una línea y un puntero.
2. **Textos públicos.**
   - "Oficial" describe a las fuentes, nunca a chile-hub.
   - El README, la landing y las fichas comunales declaran que chile-hub es un proyecto independiente, sin afiliación con el Estado, datos.gob.cl ni las instituciones fuente.
   - Las fichas comunales enlazan a la `official_url` de sus fuentes y la declaran en `isBasedOn`. Las fuentes salen de una lista explícita de organismos, no del registro completo: algunas `official_url` apuntan a descargas directas o al propio repositorio.
3. **Alcance.** El criterio de prioridad #7 pasa a ser "valor agregado sobre la fuente oficial". Si la fuente ya entrega el dato limpio y cruzable, se referencia en vez de replicarlo. Es un criterio de prioridad, no bloqueante: no depreca capas actuales.
4. **Relación con datos.gob.cl.** chile-hub es un reutilizador, no un publicador.
   - `status_show` lista `dcat_rdf_harvester` y `ckan_harvester`, pero ningún cosechador DCAT-JSON.
   - En el portal publican entidades del Estado. Meter datos derivados en el catálogo oficial enturbiaría la procedencia.
   - `data.json` se mantiene por su valor de descubribilidad para buscadores y agentes (ADR-010).
5. **Canales aguas arriba.** Registrar el proyecto en "Reutilización", pedir datos faltantes por "Sugerencias" o por la Ley 20.285, y reportar errores con "Notifica un error". Son acciones del mantenedor y se siguen en `ROADMAP.md`.
6. **Nombre.** Se mantiene. "Hub" nombra el punto donde las capas se cruzan por CUT.

## Alternativas consideradas

- **Renombrar el proyecto.** Descartada: el paquete de PyPI, el DOI de Zenodo, el espejo en Hugging Face y los enlaces existentes dependen del nombre, y el problema estaba en el discurso, no en el nombre.
- **Competir en amplitud y convertirse en un catálogo general.** Descartada: el portal tiene mandato legal y una escala que un proyecto de una persona no puede igualar. Intentarlo multiplica extractores frágiles y el riesgo de agotamiento.
- **Federarse como publicador en datos.gob.cl.** Descartada por las razones del punto 4 de la decisión.
- **Dejar todo como está.** Descartada: el discurso contradecía al producto, y describirse como "oficial" erosiona el activo principal del proyecto, que es la procedencia verificable.

## Consecuencias

- **Positivas:**
  - El discurso público queda alineado con lo que el producto hace desde el principio (ver `docs/case-study-construccion-chile-hub.md` §1, "la última milla").
  - Se reduce el riesgo de que alguien confunda a chile-hub con una fuente oficial.
  - El criterio #7 protege el foco frente a la tentación de sumar capas fáciles de replicar.
- **Negativas:**
  - Las fichas comunales pierden "datos oficiales" en el título. Search Console aún no está registrado, así que el efecto en búsqueda no se puede medir contra una línea base.
  - Los canales aguas arriba dependen de terceros que chile-hub no controla.
- **Relación con ADR-011:** ADR-011 decide *cuándo* construir por delante de la demanda; esta ADR decide *en qué carril*: profundidad sobre fuentes oficiales, no amplitud de catálogo.

## Señales de revisión

- Se publica la norma técnica de datos abiertos y estandariza formatos, metadatos o códigos territoriales.
- Una fuente oficial pasa a entregar, lista para cruzar, una capa que chile-hub replica. En ese caso, la capa pasa a ser una referencia (enlace más receta de cruce), con el protocolo para deprecar datasets de `AGENTS.md` §5.
- datos.gob.cl u otra institución propone una colaboración formal.
