# Idea: Resultados electorales, autoridades electas y partidos

## Estado

- **Decision actual**: needs-research
- **Prioridad tentativa**: P2
- **Esfuerzo estimado**: M para autoridades/parlamentarios; L para resultados
  historicos normalizados multi-eleccion
- **Riesgo**: MED
- **Categoria**: civic-data / electoral / legal / data-quality
- **Registrado**: 2026-06-18

## Propuesta

Evaluar una o mas capas electorales agregadas para Chile:

- Resultados electorales historicos por eleccion, territorio, pacto, partido,
  candidatura u opcion.
- Autoridades electas vigentes e historicas: presidencia, Congreso, gobiernos
  regionales, alcaldias, concejos municipales y CORES.
- Registro publico de partidos politicos: nombre, sigla, estado legal, fecha de
  constitucion, ambito territorial y enlaces oficiales.

Esta idea complementaria no reemplaza el dataset actual `distritos_electorales`,
que solo mapea comunas a distritos de diputadas/diputados y circunscripciones
senatoriales.

## Linea roja

No incluir datos personales electorales individuales:

- padron nominativo;
- RUN;
- domicilio electoral;
- local o mesa asociado a una persona;
- afiliacion individual a partido politico;
- datos de contacto de electores;
- cualquier dato que permita perfilar votantes individuales.

El alcance aceptable debe limitarse a resultados agregados, autoridades
publicas, candidaturas inscritas oficialmente y metadatos institucionales.

## Valor potencial

- Alta utilidad para periodismo de datos, investigacion, civic-tech, municipios,
  partidos, universidades y analisis territorial.
- Cruza naturalmente con `codigo_comuna`, `codigo_region`,
  `distrito_electoral` y `circunscripcion_senatorial`.
- Permite analizar participacion, votos validos/nulos/blancos, ganadores,
  pactos y evolucion historica.
- Existen fuentes oficiales con datos historicos o semiestructurados: SERVEL,
  TRICEL, BCN, Camara y Senado.
- Puede elevar mucho el valor del dataset actual `distritos_electorales`.

## Riesgos y costos

- Los formatos historicos son heterogeneos: XLS, XLSX, HTML, XML, PDFs o
  portales interactivos.
- La normalizacion multi-eleccion es dificil: cambian pactos, partidos, nombres
  de territorios, divisiones electorales y reglas.
- Los resultados preliminares y definitivos no deben mezclarse sin marcar
  claramente `estado_resultado`.
- La atribucion de autoridad electa requiere distinguir candidatura ganadora,
  proclamacion oficial, reemplazos, renuncias y periodos.
- El tema es sensible: errores en votos o ganadores danan confianza rapidamente.
- Algunas consultas personalizadas de SERVEL requieren RUN o ClaveUnica y deben
  quedar fuera del pipeline.

## Enfoque recomendado

1. Partir con autoridades legislativas vigentes usando datos abiertos del
   Congreso, porque hay XML y la superficie es acotada.
2. Evaluar una capa historica de resultados definitivos por comuna para
   elecciones presidenciales y plebiscitos, antes de abordar parlamentarias y
   municipales.
3. Mantener `resultados_preliminares` fuera del MVP; usar solo resultados
   definitivos o sancionados por TRICEL cuando sea posible.
4. Separar datasets por naturaleza:
   - `autoridades_electas`
   - `partidos_politicos`
   - `resultados_electorales`
5. Definir validaciones fuertes: totales, porcentajes, territorios, eleccion,
   unicidad de candidatura/opcion y consistencia con DPA.

## Esquema exploratorio

```text
dataset: resultados_electorales

id_resultado
tipo_eleccion           # presidencial | parlamentaria | municipal | gore | core | plebiscito | primaria
anio
vuelta
estado_resultado        # definitivo | preliminar | proclamado
codigo_region
codigo_comuna
distrito_electoral
circunscripcion_senatorial
territorio_nombre
cargo
candidato_nombre
opcion
partido
pacto
votos
porcentaje
electores_habilitados
votos_validamente_emitidos
votos_nulos
votos_blancos
fuente
url_fuente
fecha_fuente
```

```text
dataset: autoridades_electas

id_autoridad
nombre
cargo
institucion
partido
pacto
periodo_inicio
periodo_fin
codigo_region
codigo_comuna
distrito_electoral
circunscripcion_senatorial
estado_mandato          # vigente | finalizado | reemplazo | renuncia | desconocido
fuente
url_fuente
fecha_consulta
```

```text
dataset: partidos_politicos

id_partido
nombre
sigla
estado_legal
fecha_constitucion
ambito
url_fuente
fecha_consulta
```

## Criterios para avanzar

- Existe una fuente oficial estructurada o descargable para el primer alcance.
- La capa evita completamente datos personales de electores.
- Se puede distinguir resultados definitivos de preliminares.
- Se puede validar contra DPA y, cuando aplique, contra distritos electorales.
- Los totales publicados pueden reconciliarse con los documentos fuente.
- El dataset aporta algo complementario: normalizacion, versionado, cruces
  territoriales o acceso programatico.

## Criterios para rechazar o postergar

- La fuente principal exige consultas por RUN, ClaveUnica o datos personales.
- La unica fuente disponible para una capa es scraping HTML fragil o PDFs sin
  estructura confiable.
- No se puede separar con claridad resultados preliminares de definitivos.
- La normalizacion historica requiere decisiones politicas o interpretativas no
  trazables.
- El costo de mantencion supera el beneficio frente a datasets ya publicados.

## Referencias iniciales

- SERVEL, resultados electorales historicos: https://www.servel.cl/centro-de-datos/resultados-electorales-historicos-gw3/
- BCN, elecciones historicas: https://www.bcn.cl/siit/elecciones_historicas/
- TRICEL, resultados oficiales: https://tribunalcalificador.cl/resultados-de-elecciones-res/
- Datos abiertos legislativos del Congreso: https://opendata.camara.cl/
- Datos abiertos legislativos del Senado: https://www.senado.cl/transparencia/datos-abiertos-legislativos
- ChileAtiende, consulta de afiliacion individual a partido politico: https://www.chileatiende.gob.cl/fichas/2938-consultar-sobre-afiliacion-a-un-partido-politico
