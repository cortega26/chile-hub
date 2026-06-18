# Idea: Apoyos formales para emprendedores

## Estado

- **Decision actual**: needs-research
- **Prioridad tentativa**: P2
- **Esfuerzo estimado**: M si existe fuente estructurada; L si requiere integrar
  multiples portales
- **Riesgo**: MED-HIGH
- **Categoria**: product / public-services / data-quality / legal
- **Registrado**: 2026-06-18

## Propuesta

Evaluar un dataset que concentre informacion sobre apoyos formales disponibles
en Chile para emprendedores, microempresas, pymes y cooperativas: fondos,
convocatorias, capacitaciones, asesorias, redes, herramientas de formalizacion y
programas de crecimiento.

El objetivo no seria reemplazar los portales oficiales, sino publicar una capa
estructurada, trazable y facil de consultar para analistas, municipios,
incubadoras, periodistas, consultores y emprendedores.

## Contexto

Al 2026-06-18 ya existe Chile Emprende, plataforma del Ministerio de Economia que
centraliza fondos, convocatorias y capacitaciones para mipymes y cooperativas.
Tambien existen fuentes relacionadas como ChileAtiende, Sercotec, Corfo,
Start-Up Chile, FOSIS, SENCE, INDAP, SII, SERNAMEG y PRODEMU.

La primera pregunta de investigacion es si Chile Emprende u otra fuente oficial
expone una API, JSON embebido, CSV, XLSX o descarga estable. Si la unica forma
viable es scraping HTML fragil, la idea debe postergarse.

## Valor potencial

- Resuelve un dolor claro: la oferta publica cambia, esta distribuida en muchos
  sitios y cuesta saber que aplica a cada perfil.
- Tiene alta utilidad civica y practica para emprendedores, pymes, cooperativas,
  municipios, consultores, incubadoras y medios.
- Puede cruzarse con territorio, etapa del negocio, tipo de apoyo e institucion.
- Complementa el foco actual de `chile-hub` en datos publicos limpios y
  reproducibles.
- Puede partir como catalogo de programas estables antes de intentar seguir cada
  convocatoria dinamica.

## Riesgos y costos

- Alta volatilidad: convocatorias abren, cierran y cambian montos, requisitos,
  regiones y fechas.
- Riesgo de publicar informacion obsoleta que afecte decisiones reales de
  personas o empresas.
- Muchas fuentes pueden no ofrecer datos estructurados descargables.
- Puede duplicar Chile Emprende si no se define una propuesta complementaria.
- La validacion requiere revisar vigencia, enlaces, fechas, estado de
  postulacion y trazabilidad de fuente, no solo tipos y conteos.
- El mantenimiento podria parecerse mas a una agenda viva de beneficios que a un
  dataset estable.

## Enfoque recomendado

1. Evaluar primero si Chile Emprende tiene API, endpoints JSON, datos embebidos o
   exportaciones descargables.
2. Si existe fuente estructurada, construir un extractor candidato con cobertura
   inicial de programas y convocatorias.
3. Si no existe fuente estructurada, registrar enlaces y taxonomia como
   documentacion, pero no incorporar al pipeline.
4. Partir con programas relativamente estables y agregar convocatorias solo si se
   puede verificar fecha de apertura, fecha de cierre y estado.
5. Marcar esta capa como `candidate` hasta demostrar frescura y estabilidad por
   varios ciclos de actualizacion.

## Esquema exploratorio

```text
dataset: programas_apoyo_emprendimiento

id_programa
nombre_programa
institucion
tipo_apoyo              # financiamiento | capacitacion | asesoria | formalizacion | red | credito | otro
etapa_emprendimiento    # idea | inicio | mipyme | crecimiento | cooperativa | organizacion
beneficiario_objetivo
cobertura_geografica    # nacional | regional | comunal | sectorial
codigo_region
codigo_comuna
monto_minimo
monto_maximo
cofinanciamiento
requiere_formalizacion
fecha_apertura
fecha_cierre
estado_convocatoria     # abierta | cerrada | permanente | desconocida
url_postulacion
url_fuente
fecha_consulta
source_mode
```

## Criterios para avanzar

- Existe al menos una fuente oficial estructurada y estable.
- La licencia o politica de reutilizacion permite redistribuir metadatos del
  programa, o al menos publicar enlaces y campos descriptivos no restrictivos.
- El extractor puede distinguir programas permanentes de convocatorias
  temporales.
- Se puede validar estado temporal con `fecha_apertura`, `fecha_cierre` y
  `fecha_consulta`.
- El dataset aporta algo complementario a Chile Emprende: versionado,
  descargabilidad, cruces territoriales, historial o API de datos.

## Criterios para rechazar o postergar

- La unica fuente viable requiere scraping HTML fragil.
- No hay permisos claros para redistribuir la informacion.
- La frescura no puede monitorearse de forma confiable.
- El dataset se limita a duplicar un portal oficial sin mejorar acceso
  programatico, trazabilidad o analisis.
- La carga de mantencion desplaza mejoras de calidad de datasets ya publicados.

## Referencias iniciales

- Chile Emprende: https://www.chileemprende.gob.cl/
- Ministerio de Economia sobre Chile Emprende: https://www.economia.gob.cl/2026/06/03/conoce-chile-emprende-la-plataforma-que-reune-la-oferta-publica-de-apoyo-para-emprendedores.htm
- Portal de Emprendimiento: https://miportalemprendimiento.gob.cl/
- Sercotec: https://www.sercotec.cl/
- Corfo: https://www.corfo.cl/
- Start-Up Chile: https://startupchile.org/
