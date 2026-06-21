# Criterios para incluir datasets

`chile-hub` crece por criterios, no por acumulación. Una capa nueva debe aumentar
el valor del hub sin comprometer trazabilidad, legalidad, mantenibilidad ni la
confianza de quienes consumen los artefactos publicados.

## Criterios bloqueantes

Una propuesta no entra al roadmap si falla cualquiera de estos puntos (excepción:
la *fragilidad de fuente* puede degradarse a `under-review` en vez de rechazarse
— ver más abajo):

| Criterio | Pregunta | Decisión |
|:---|:---|:---|
| Reúso legal | Tiene licencia abierta, permisos claros o amparo público sin restricción explícita? | Sin permiso de reúso, se rechaza. Si permite el reúso pero no la redistribución, queda fuera del bundle como referencia externa o `candidate`. |
| Fuente inspeccionable | Existe API, CSV, XLSX, ZIP, JSON o descarga estable? | Si solo requiere scraping HTML frágil, se rechaza para el carril publicable; puede entrar como `under-review` (carril `candidate`) si el tradeoff es neto positivo. |
| Estabilidad | El esquema y la URL son razonablemente estables? | Si cambia sin aviso, pasa a `needs-research`. |
| Datos no personales | Evita padrones, datos sensibles o identificadores personales protegidos? | Si hay riesgo de Ley 19.628, se rechaza. |
| Validación posible | Se puede validar cardinalidad, claves, tipos o rangos? | Si no se puede verificar, no se publica. |

## Criterios de prioridad

Los datasets que pasan los bloqueantes se ordenan por:

1. Dolor de usuario recurrente y documentado.
2. Valor de cruce con `codigo_comuna`, `codigo_region` u otro identificador estable.
3. Utilidad transversal para desarrolladores, analistas, periodistas o civic-tech.
4. Bajo costo operacional de refresco y monitoreo.
5. Claridad de esquema, campos y frecuencia esperada.
6. Capacidad de publicarse en formatos ya soportados: Parquet, DuckDB, SQLite, JSON o Excel.
7. Diferenciación: reduce limpieza repetida que cada usuario haría por su cuenta.

## Estados de decisión

| Estado | Significado |
|:---|:---|
| `accepted` | Pasa criterios y tiene prioridad suficiente para plan de implementación. Destino: carril `stable_publishable`. |
| `under-review` | "Para revisión": evaluado con tradeoff neto positivo pese a ser imperfecto en una dimensión blanda (sobre todo fragilidad de fuente). Destino: carril `candidate`, fuera del bundle público, con `review_by` y regla de salida. No admite fallas en compuertas duras. Ver detalle abajo. |
| `needs-research` | Puede ser valioso, pero falta confirmar licencia, fuente, esquema o costo. |
| `deferred` | Es válido, pero no desplaza mejoras de robustez o capas más demandadas. |
| `rejected` | Falla un criterio bloqueante o no encaja con el propósito del hub. |

## Estado `under-review` (para revisión)

Algunos datasets tienen un tradeoff neto positivo aunque fallen un criterio
**blando**. Para no perderlos por un rechazo binario, entran como `under-review`:
quedan registrados, se implementan en el carril `candidate` (nunca en el bundle
público) y se reevalúan en una fecha fija.

**Qué admite y qué no.** `under-review` solo tolera debilidad en dimensiones
blandas —sobre todo **fragilidad de fuente** (scraping en vez de descarga
estable), además de tamaño, cadencia de refresco y costo de mantención—. No
admite fallas en las compuertas duras:

- Datos personales o sensibles (Ley 19.628): rechazo, sin excepción.
- Validación imposible: no se publica.
- Sin derechos de redistribución: no entra al bundle público, aunque puede quedar
  como referencia externa o dataset dev-only, igual que cualquier `candidate`.

**Mini-scorecard (una línea, obligatoria).** Cada ficha `under-review` registra el
balance que justifica el estado:

`valor · legal · tamaño · cadencia · fragilidad → decisión`

donde `legal` solo refleja dimensiones blandas (atribución, términos de uso); los
datos personales nunca son un deslizador.

**Regla de salida (no es terminal).** `under-review` exige una fecha `review_by` y
reutiliza `stalled_after_days` del registro de fuentes: si en ese plazo el dataset
no madura a un extractor estable ni demuestra mantención, se degrada a `rejected`
o se archiva. Sin esta regla, el estado se pudre en un `candidate` permanente sin
mantenimiento —el patrón que ya vivió `finanzas_municipales` (SINIM)—.

## Razones comunes de rechazo

- La fuente prohíbe reutilizar los datos, no solo redistribuirlos (la sola falta de redistribución no rechaza: define carril `candidate` o referencia; los términos ambiguos pasan a `needs-research`).
- El dato contiene información personal, sensible o electoral individual.
- La única fuente es HTML frágil y el valor no justifica mantenerla como `under-review`.
- El dataset no cruza con la DPA ni aporta un identificador estable.
- El costo de mantenimiento excede el beneficio para una capa pública curada.
- La propuesta duplica una capa existente sin mejorar cobertura, calidad o uso.

## Cómo proponer una capa

Abre un issue usando la plantilla `Dataset request` e incluye:

- URL oficial de la fuente.
- Estado de licencia o términos de reúso.
- Caso de uso concreto que desbloquea.
- Claves de cruce esperadas.
- Frecuencia de actualización y riesgos de mantenimiento.
- Ejemplo mínimo de columnas esperadas si ya las conoces.

Si la propuesta todavía es exploratoria, usa GitHub Discussions antes de pedir
integración al catálogo mantenido.
