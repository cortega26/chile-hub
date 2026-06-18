# Criterios para incluir datasets

`chile-hub` crece por criterios, no por acumulacion. Una capa nueva debe aumentar
el valor del hub sin comprometer trazabilidad, legalidad, mantenibilidad ni la
confianza de quienes consumen los artefactos publicados.

## Criterios bloqueantes

Una propuesta no entra al roadmap si falla cualquiera de estos puntos:

| Criterio | Pregunta | Decision |
|:---|:---|:---|
| Reuso legal | Tiene licencia abierta, permisos claros o amparo publico sin restriccion explicita? | Si no, se rechaza o queda como referencia externa. |
| Fuente inspeccionable | Existe API, CSV, XLSX, ZIP, JSON o descarga estable? | Si solo requiere scraping HTML fragil, se rechaza. |
| Estabilidad | El schema y la URL son razonablemente estables? | Si cambia sin aviso, queda como investigacion. |
| Datos no personales | Evita padrones, datos sensibles o identificadores personales protegidos? | Si hay riesgo de Ley 19.628, se rechaza. |
| Validacion posible | Se puede validar cardinalidad, claves, tipos o rangos? | Si no se puede verificar, no se publica. |

## Criterios de prioridad

Los datasets que pasan los bloqueantes se ordenan por:

1. Dolor de usuario recurrente y documentado.
2. Valor de cruce con `codigo_comuna`, `codigo_region` u otro identificador estable.
3. Utilidad transversal para desarrolladores, analistas, periodistas o civic-tech.
4. Bajo costo operacional de refresco y monitoreo.
5. Claridad de schema, campos y frecuencia esperada.
6. Capacidad de publicarse en formatos ya soportados: Parquet, DuckDB, SQLite, JSON o Excel.
7. Diferenciacion: reduce limpieza repetida que cada usuario haria por su cuenta.

## Estados de decision

| Estado | Significado |
|:---|:---|
| `accepted` | Pasa criterios y tiene prioridad suficiente para plan de implementacion. |
| `needs-research` | Puede ser valioso, pero falta confirmar licencia, fuente, schema o costo. |
| `deferred` | Es valido, pero no desplaza mejoras de robustez o capas mas demandadas. |
| `rejected` | Falla un criterio bloqueante o no encaja con el proposito del hub. |

## Razones comunes de rechazo

- La fuente no permite redistribucion o tiene terminos ambiguos.
- El dato contiene informacion personal, sensible o electoral individual.
- La unica fuente disponible es HTML fragil sin descarga estructurada.
- El dataset no cruza con la DPA ni aporta un identificador estable.
- El costo de mantenimiento excede el beneficio para una capa publica curada.
- La propuesta duplica una capa existente sin mejorar cobertura, calidad o uso.

## Como proponer una capa

Abre un issue usando la plantilla `Dataset request` e incluye:

- URL oficial de la fuente.
- Estado de licencia o terminos de reuso.
- Caso de uso concreto que desbloquea.
- Claves de cruce esperadas.
- Frecuencia de actualizacion y riesgos de mantenimiento.
- Ejemplo minimo de columnas esperadas si ya las conoces.

Si la propuesta todavia es exploratoria, usa GitHub Discussions antes de pedir
integracion al catalogo mantenido.
