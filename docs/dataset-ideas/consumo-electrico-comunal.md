# Idea: Consumo eléctrico comunal (CNE / Energía Abierta)

## Estado

- **Decisión actual**: accepted
- **Prioridad tentativa**: P1
- **Esfuerzo estimado**: S-M — descarga directa de Excel o API JSON; esquema
  simple
- **Riesgo**: LOW
- **Categoría**: energía / económico / medio-ambiente / civic-data
- **Registrado**: 2026-06-21
- **Fuente verificada**: sí — dataset oficial con descarga Excel y API REST JSON
  (2026-06-21); ver Referencias.

## Propuesta

Publicar una capa de consumo eléctrico anual por comuna y tipo de cliente, a
partir del dataset oficial "Consumo Eléctrico Anual por Comuna y Tipo de
Cliente" de la Comisión Nacional de Energía (CNE), publicado en el portal
Energía Abierta. Los datos se procesan desde la información que las empresas
distribuidoras entregan a la CNE.

Esta capa abre el dominio energía / medio-ambiente, hoy ausente del hub, con una
de las fuentes más limpias y de menor costo operacional disponibles.

## Valor potencial

- Fuente limpia y de bajo costo: la más alineada con el principio "menos
  datasets, más limpios y confiables".
- Cruza por `codigo_comuna`; el desglose por tipo de cliente
  (residencial/comercial/industrial u otros) habilita análisis de actividad
  económica y de consumo residencial.
- Útil para análisis territorial, eficiencia energética, periodismo y políticas
  públicas.
- Doble vía de acceso (Excel + API), lo que reduce el riesgo de quiebre de un
  único mecanismo.

## Riesgos y costos

- La **API requiere una API key gratuita** de la plataforma Junar; hay que
  tratarla como secreto y permitir fallback a la descarga Excel.
- El portal Energía Abierta ha cambiado de dominio en el tiempo
  (`energiaabierta.cl`, `energiaabierta.cne.cl`, `datos.energiaabierta.cl`); hay
  que fijar y monitorear la URL o el endpoint.
- Verificar la unidad de medida (kWh) y normalizar nombres de comuna a CUT.
- Confirmar el último año disponible y el rezago de publicación.

## Enfoque recomendado

1. Usar la **descarga Excel** del dataset como fuente primaria (sin key) y la
   **API JSON** como alternativa y vía de validación cruzada.
2. Normalizar nombres de comuna a `codigo_comuna` y validar contra la DPA.
3. Conservar el desglose por tipo de cliente en formato long.
4. Validar rangos (consumo no negativo), cardinalidad por
   `(anio, codigo_comuna, tipo_cliente)` y totales por región.
5. Publicar como `stable_publishable` tras validar cardinalidad y unidades.

## Esquema exploratorio

```text
dataset: consumo_electrico_comunal

codigo_region
codigo_comuna
nombre_comuna
anio
tipo_cliente               # residencial | comercial | industrial | otro (según fuente)
consumo_kwh
numero_clientes            # si la fuente lo provee
fuente
url_fuente
fecha_fuente
```

## Criterios para avanzar

- Confirmar las columnas exactas, la unidad (kWh) y el último año disponible al
  implementar el extractor.
- Decidir entre Excel directo (preferido) y API con key, con fallback entre
  ambos.
- Validar cardinalidad y normalización de comuna a CUT contra la DPA.

## Criterios para rechazar o postergar

- La CNE deja de publicar el dataset por comuna en formato estructurado.
- El acceso queda restringido únicamente a una API con key sin descarga abierta
  equivalente.
- El esquema cambia sin aviso de forma que rompe la validación de cardinalidad o
  unidades.

## Referencias iniciales

- Dataset "Consumo Eléctrico Anual por Comuna y Tipo de Cliente":
  http://energiaabierta.cl/datasets-estadistica/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/
- Vista de datos / descarga:
  http://datos.energiaabierta.cl/dataviews/241686/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/
- Documentación de API (Junar): http://datos.energiaabierta.cl/developers/
- Portal Energía Abierta (CNE): http://energiaabierta.cl/
