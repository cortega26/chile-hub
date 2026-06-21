# Idea: Pobreza comunal (CASEN / estimaciones SAE)

## Estado

- **Decisión actual**: accepted
- **Prioridad tentativa**: P1
- **Esfuerzo estimado**: M — un extractor sobre dos XLSX comunales (ingresos y
  multidimensional)
- **Riesgo**: LOW-MED
- **Categoría**: socioeconómico / civic-data / product
- **Registrado**: 2026-06-21
- **Fuente verificada**: sí — XLSX por comuna en el Observatorio Social
  (2026-06-21); ver Referencias.

## Propuesta

Publicar una capa comunal de pobreza basada en las Estimaciones de Pobreza
Comunal del Ministerio de Desarrollo Social y Familia (MDS), derivadas de la
Encuesta CASEN mediante metodología de Estimación de Áreas Pequeñas (SAE).
Cubre la tasa de pobreza por ingresos (serie comunal desde 2011) y el índice de
pobreza multidimensional (serie comunal desde 2015).

Esta capa llena la brecha socioeconómica señalada como faltante de mayor valor
en `docs/backlog/08-evaluacion-producto-comercial.md` y aporta la dimensión
socioeconómica que hoy le falta al `perfil_territorial_comunal`.

## Valor potencial

- Resuelve un dolor recurrente y documentado: la pobreza comunal es uno de los
  indicadores socioeconómicos más demandados por periodismo de datos,
  municipios, investigación y civic-tech.
- Cruza naturalmente por `codigo_comuna`; complementa el Censo (stock
  demográfico) con una medida de bienestar.
- Fuente oficial, abierta y agregada (no personal): estimaciones por comuna, sin
  microdatos.
- Doble valor: es prerrequisito del producto "Perfil Territorial / Ficha de
  Mercado por Comuna" descrito en ME8.
- Diferenciación: evita que cada usuario reconstruya el cruce CASEN–comuna y
  normalice nombres/CUT por su cuenta.

## Riesgos y costos

- **Cobertura parcial**: la SAE no estima todas las comunas (comunas pequeñas o
  sin muestra suficiente quedan sin estimación). Hay que declarar las comunas
  sin dato y nunca imputarlas en silencio.
- Las estimaciones traen **intervalos de confianza** (límite inferior/superior);
  deben publicarse junto al valor puntual, no descartarse.
- **Frecuencia baja**: CASEN es bienal/trienal y las estimaciones comunales se
  publican con rezago. Es una ventaja de mantenimiento (refresco infrecuente),
  pero exige documentar el año de referencia.
- Los cambios metodológicos entre rondas (líneas de pobreza, factores de
  expansión con proyecciones de población) pueden romper la comparabilidad
  histórica; conviene marcar `metodologia` y `anio`.

## Enfoque recomendado

1. Construir un extractor que descargue los dos XLSX comunales del Observatorio
   Social (tasa de pobreza por ingresos e índice multidimensional) y los una por
   `codigo_comuna`.
2. Normalizar a formato long con una dimensión (`ingresos` | `multidimensional`)
   y conservar el valor puntual más su intervalo de confianza.
3. Validar cardinalidad contra la DPA, marcando explícitamente las comunas sin
   estimación.
4. Documentar año de referencia, metodología SAE y la advertencia de
   comparabilidad histórica.
5. Publicar como `stable_publishable` una vez que pase la validación de
   cardinalidad y rangos.

## Esquema exploratorio

```text
dataset: pobreza_comunal

codigo_region
codigo_comuna
nombre_comuna
anio                       # año de la ronda CASEN (p. ej. 2022)
dimension                  # ingresos | multidimensional
tasa                       # estimación puntual (%)
limite_inferior            # intervalo de confianza inferior (%)
limite_superior            # intervalo de confianza superior (%)
metodologia                # SAE
fuente
url_fuente
fecha_fuente
```

## Criterios para avanzar

- Definir en el esquema publicado el manejo de comunas sin estimación y de los
  intervalos de confianza.
- Validar cardinalidad contra la DPA y rangos 0–100 % de la tasa.
- Confirmar el último año comunal disponible y dejar el extractor preparado para
  el siguiente.

## Criterios para rechazar o postergar

- El MDS deja de publicar las estimaciones comunales en formato estructurado.
- Un cambio metodológico impide validar o comparar sin decisiones
  interpretativas no trazables.
- El costo de mantención supera el beneficio frente a datasets ya publicados.

## Referencias iniciales

- Estimaciones de Pobreza Comunal 2022:
  https://observatorio.ministeriodesarrollosocial.gob.cl/pobreza-comunal-2022
- Archivos verificados (XLSX por comuna):
  `Estimaciones_Tasa_Pobreza_Ingresos_Comunas_2022.xlsx`,
  `Estimaciones_Indice_Pobreza_Multidimensional_Comunas_2022.xlsx`
- Informe metodológico SAE 2022:
  https://observatorio.ministeriodesarrollosocial.gob.cl/storage/docs/pobreza-comunal/2022/Resultados_Estimaciones_SAE_2022.pdf
- Encuesta CASEN 2022:
  https://observatorio.ministeriodesarrollosocial.gob.cl/encuesta-casen-2022
