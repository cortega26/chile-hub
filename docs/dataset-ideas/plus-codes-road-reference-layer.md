# Idea: Plus Codes y puntos de referencia vial

## Estado

- **Decision actual**: needs-research
- **Prioridad tentativa**: P3
- **Esfuerzo estimado**: M-L, dependiendo de la fuente vial
- **Riesgo**: MED-HIGH
- **Categoria**: product / geospatial / legal / data-quality
- **Registrado**: 2026-06-18

## Propuesta

Evaluar un dataset bajo el nivel comuna que permita ubicar lugares mediante Plus
Codes, especialmente en zonas rurales o donde las direcciones tradicionales son
ambiguas. La idea original sugiere generar codigos para cruces de calles y/o
para puntos cada cierta distancia sobre calles, avenidas, pasajes y caminos.

Plus Codes no son una fuente de datos independiente: son una codificacion de
coordenadas basada en Open Location Code. El valor del dataset estaria en la
seleccion, validacion y publicacion de puntos geograficos utiles, no en el
algoritmo de codificacion.

## Valor potencial

- Facilita catastros, logistica, trabajo en terreno, emergencias y analisis rural.
- Puede enriquecer datasets existentes con coordenadas, como salud, educacion y
  cabeceras comunales.
- Funciona offline y evita depender de APIs propietarias para codificar puntos.
- Agrega una capa territorial mas fina que comuna sin publicar datos personales.

## Riesgos y costos

- La dificultad principal es conseguir una red vial nacional confiable,
  actualizada y redistribuible.
- Si se usa OpenStreetMap, la capa derivada debe cumplir ODbL, incluyendo
  atribucion y potenciales obligaciones share-alike sobre bases derivadas.
- No se deben usar datos extraidos de Google Maps como fuente vial.
- Muestrear cada 50 metros puede producir un dataset grande y costoso de
  validar, versionar y distribuir.
- Un punto cada 50 metros no equivale a una direccion exacta; puede crear una
  falsa sensacion de precision si no se documentan limites y supuestos.
- Los cruces de calles no resuelven bien sectores rurales, caminos sin nombre o
  tramos largos sin intersecciones.

## Enfoque recomendado

1. Agregar primero Plus Codes como columnas derivadas en datasets existentes que
   ya tienen `latitud` y `longitud`.
2. Hacer un spike con una comuna piloto para medir cobertura, tamano, calidad de
   nombres de vias, precision geometrica y obligaciones de licencia.
3. Comparar fuentes candidatas:
   - Red Vial Nacional MOP / IDE Chile / datos.gob.cl.
   - Mapas vectoriales BCN, si la licencia y cobertura aplican.
   - OpenStreetMap, solo si se acepta explicitamente la politica ODbL.
4. Disenar una capa experimental separada del bundle publico hasta resolver
   licencia, tamano y utilidad.

## Esquema exploratorio

```text
dataset: puntos_referencia_vial_plus_codes

id_punto
codigo_region
codigo_comuna
tipo_punto              # interseccion | tramo_50m | hito_vial
nombre_via_1
nombre_via_2
distancia_desde_inicio_m
latitud
longitud
plus_code
precision_plus_code     # 10 | 11
fuente_geometria
licencia_fuente
fecha_fuente
```

## Criterios para avanzar

- Existe una fuente estructurada y redistribuible para geometrias viales.
- La fuente tiene cobertura suficiente para al menos un caso rural y uno urbano.
- El dataset piloto puede validarse contra DPA por `codigo_comuna`.
- El tamano final nacional es razonable para los formatos publicados por
  `chile-hub`, o se define como descarga opcional separada.
- La documentacion explica que Plus Code codifica un area derivada de
  coordenadas y no reemplaza una direccion oficial.

## Criterios para rechazar o postergar

- La unica fuente viable tiene licencia ambigua o restrictiva.
- La capa depende de scraping HTML o APIs propietarias no redistribuibles.
- El volumen nacional degrada demasiado el build, los tests o el bundle publico.
- No se identifica un caso de uso recurrente mas alla de una necesidad puntual.

## Referencias

- Open Location Code / Plus Codes: https://github.com/google/open-location-code
- Plus Codes: https://maps.google.com/pluscodes/
- Open Database License: https://opendatacommons.org/licenses/odbl/
- OSMF Legal FAQ: https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ
