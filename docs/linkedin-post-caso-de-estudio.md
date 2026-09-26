# Borrador de post técnico — LinkedIn

> **Estado:** Borrador listo para publicar (actualizado 2026-09-26 con el estado
> real del proyecto: DOI, mirror HF, MCP, páginas por comuna, pipeline reparado).
> **Contexto:** el 2026-09-26 ya se publicó un post de seguimiento (141
> reacciones, 16 comentarios). Este es el post **técnico de fondo** — el que
> explica cómo está construido y por qué. El operador decide el momento.
> **Basado en** `docs/case-study-construccion-chile-hub.md`.

---

## Cómo construí un pipeline de datos abiertos que prefiere abortar a mentir

Durante el último año mantuve **chile-hub**, un proyecto open-source que toma 22
capas de datos públicos chilenos (censo, salud, educación, pobreza, energía,
finanzas municipales, geometría, permisos de edificación…), las valida con
contratos de esquema ejecutables y las publica en formatos listos para análisis.
Corre sobre GitHub Actions, se refresca a diario y se consume en una línea de
Python. Hoy lo usan ~2.200 instalaciones al mes y el bundle también se replica
en Hugging Face Hub y se expone a agentes de código vía MCP.

No es un producto. Es un **activo técnico** construido bajo una regla no
negociable: **si una validación falla, el pipeline aborta**. No se publican datos
parcialmente válidos. Prefiero una ausencia declarada a un error silencioso.

Escribí un caso de estudio detallado (enlace abajo). Aquí van las 5 decisiones de
arquitectura que definieron el proyecto y lo que aprendí:

**1. Pipeline determinista con trazabilidad completa**

4 etapas lineales: Extracción → Construcción → Validación → Publicación. Cada
etapa requiere el éxito de la anterior. Si el extractor del INE devuelve 345
comunas en lugar de 346, todo se detiene con un mensaje descriptivo. Cero modo
"best-effort". Cuando una fuente no se puede alcanzar desde CI (un portal del
MINVU bloquea por IP a los runners), el dataset degrada a un **modo declarado**
—snapshot versionado, `monthly`— en vez de fingir frescura.

**2. Contratos de esquema como código**

Cada dataset tiene un contrato JSON Schema en `contracts/datasets/` que define
columnas, tipos, nulabilidad, clave primaria, anchos fijos para códigos
territoriales y conteo esperado de registros. El pipeline valida **cada contrato
en cada build** (25 contratos hoy). Si un extractor cambia el esquema sin
actualizar el contrato, el build falla. Esto convierte una promesa de
documentación en verificación ejecutable.

**3. CUT como VARCHAR(5), nunca como entero**

El Código Único Territorial es el identificador que cruza todas las capas. En
casi todos los portales chilenos, el CUT se representa como entero — y `01101`
(Iquique) se convierte en `1101`, rompiendo joins silenciosamente. Todo CUT es
`VARCHAR` de ancho fijo desde la extracción. Esta es una de las 5 invariantes no
negociables del proyecto.

**4. Carriles de publicación separados**

No todo lo que se extrae se publica. `stable_publishable` para fuentes estables
con licencia clara (van al bundle público: 21 capas). `candidate` para fuentes
frágiles o scraping (se extraen, se validan, pero **no** entran al bundle hasta
madurar, con fecha de revisión y regla de salida). Esto permite experimentar sin
degradar la calidad del bundle.

**5. Honestidad sobre lo que falta**

`finanzas_municipales` tuvo 3 de 346 comunas durante meses porque el portal SINIM
requiere scraping JavaScript/POST. En vez de ocultarlo, lo etiqueté como `🔶
parcial` y documenté por qué. Hoy tiene 345/346 y sigue marcada parcial porque
no es total. La integridad de la narrativa vale más que el conteo de capas.

**Resultados a septiembre 2026:**

- 22 capas construibles (21 publicables), 1.106 tests, 21 ADRs, 25 contratos
- Calidad promedio: 94.0/100 · salud del hub: 20 `ok`, 1 `warn`, 0 `error`
- **0 datos corruptos publicados.** El pipeline falló varias veces — fuentes
  caídas, cambios de esquema no anunciados, Excels renombrados, un portal que
  bloquea por IP — y en cada caso **abortó antes de publicar** o degradó a un
  modo declarado. El fail-loud funcionó exactamente como fue diseñado.
- El bundle se replica en **Hugging Face Hub** (21 subsets, publicado por CI),
  hay un **servidor MCP** para agentes (`chile-hub[mcp]`), **347 páginas
  estáticas por comuna** con indicadores oficiales, y cada release recibe un
  **DOI de Zenodo** (concept DOI: 10.5281/zenodo.22968698).

**Lo que aprendí:**

- Los contratos de esquema automatizados fueron la decisión de mayor retorno.
- Fail-loud desde el día uno es más barato que migrar un sistema permisivo.
- Mantener 22 extractores como única persona es difícil; el scraping
  gubernamental es frágil por definición. Cada capa nueva es un compromiso de
  mantenimiento permanente.
- La distribución también se automatiza: HF, DOI, sitemap, JSON-LD y MCP se
  publican solos desde el mismo pipeline que valida los datos.

Si trabajas con datos abiertos, datos públicos, ETL o pipelines de datos
territoriales, el caso de estudio completo está aquí:
🔗 https://github.com/cortega26/chile-hub/blob/main/docs/case-study-construccion-chile-hub.md

La landing con todos los datasets descargables:
🔗 https://tooltician.com/chile-hub/

---

*Este post es parte del Plan 022 — Fase 4: Distribución sobre lo validado. Es
narrativa técnica, no marketing. Sin CTAs comerciales.*
