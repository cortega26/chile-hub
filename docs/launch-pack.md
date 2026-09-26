# Launch pack — chile-hub (2026-09)

> **Uso:** material listo para publicar y checklist de siembra. No es marketing:
> es narrativa técnica con links verificables. El operador decide qué, cuándo y
> dónde. **Regla de oro:** responder todos los comentarios y no pedir upvotes.

## Assets y links canónicos

| Qué | URL |
|:---|:---|
| Repositorio | https://github.com/cortega26/chile-hub |
| PyPI | https://pypi.org/project/chile-hub/ |
| Landing / catálogo | https://tooltician.com/chile-hub/ |
| DOI (concept) | https://doi.org/10.5281/zenodo.22968698 |
| Hugging Face (21 subsets) | https://huggingface.co/datasets/cortega26/chile-hub |
| Docs MCP | https://tooltician.com/chile-hub/reference/mcp/ |
| Cómo citar | https://tooltician.com/chile-hub/reference/citation/ |
| Caso de estudio | https://github.com/cortega26/chile-hub/blob/main/docs/case-study-construccion-chile-hub.md |

Números actuales (2026-09-26): 22 capas construibles / 21 publicables · 1.106
tests · 94.0/100 de calidad · ~2.200 instalaciones PyPI/mes · 90 stars · 10 forks.
Post de seguimiento: **148 reacciones, 17 comentarios**; issues de leads:
[#107](https://github.com/cortega26/chile-hub/issues/107),
[#108](https://github.com/cortega26/chile-hub/issues/108),
[#109](https://github.com/cortega26/chile-hub/issues/109).

---

## 1. Show HN (inglés, ~120 palabras)

**Título:** `Show HN: Chile-hub – Chilean public data as clean Parquet, DuckDB and MCP`

**Cuerpo:**

> Hi HN — I built chile-hub, an open-source data layer for Chilean public data
> (census, health, education, poverty, municipal finance, geometry, building
> permits…). The problem: the data exists, but getting from "it's somewhere on a
> government portal" to "I can analyze it" takes days of cleaning Excel files,
> fixing broken joins and re-checking licenses.
>
> 21 publishable layers, validated by executable JSON Schema contracts; the
> pipeline aborts instead of publishing bad data. Cuts are always fixed-width
> strings (the classic lost-leading-zero problem). Consumption is one line:
> `pip install chile-hub`, plus Parquet over HTTP, DuckDB `hf://`, or an MCP
> server for coding agents.
>
> Everything is in Spanish (it's Chilean data) but code/docs examples are
> copy-paste. Happy to answer anything about the pipeline, the publication
> lanes, or the CI gates.

**Reglas HN:** publicar como autor (no astroturfing), enlazar el repo, responder
todo el día; no pedir upvotes ni pedir votos a nadie.

---

## 2. Post para dev.to / Hashnode (inglés, ~500 palabras)

Título sugerido: **"Executable data contracts: how I ship government data that
refuses to lie"**.

Estructura (reusar `docs/case-study-construccion-chile-hub.md` traducido
libremente):

1. **El problema:** la última milla de los datos abiertos (no es "conseguir
   datos", es que sean usables).
2. **La regla:** fail-loud; el pipeline aborta antes de publicar.
3. **Las 3 decisiones que importan:** CUT como `VARCHAR(5)`; contratos JSON
   Schema verificados en cada build; carriles `stable_publishable`/`candidate`.
4. **Un caso real:** `permisos_edificacion` bloqueado por IP desde CI → snapshot
   versionado con modo `monthly` declarado (honestidad > frescura fingida).
5. **Distribución automatizada:** HF mirror, DOI por release, JSON-LD + sitemap,
   MCP para agentes.
6. **Cierre:** cómo consumir en una línea + DOI para citar.

---

## 3. Versión LinkedIn (español)

Reusar `docs/linkedin-post-caso-de-estudio.md` (post técnico de fondo). El post
de seguimiento ya se publicó el 2026-09-26; este es el deep-dive. Añadir al
primer comentario: PyPI, GitHub, landing, DOI.

---

## 4. Checklist de siembra (comunidades)

> Ordenadas por retorno esperado/esfuerzo. Respetar las reglas de cada
> comunidad; presentarse como autor; responder todo.

- [ ] **LinkedIn** — responder los 16 comentarios del post del 26-sep (ver §5);
      publicar el post técnico en 1–2 semanas.
- [ ] **Hacker News** — Show HN en día de semana (martes/miércoles, 8–10 ET).
- [ ] **dev.to** — post en inglés; enlazar DOI y repo.
- [ ] **Reddit** — `r/chile` (tag de proyecto/OC, sin spam), `r/opensource`,
      `r/datos`, `r/Python` (respetar la regla de self-promotion: participar
      antes de postear).
- [ ] **Python Chile / PyData / R Users** — grupos de Meetup/Telegram/Discord;
      ofrecer un lightning talk de 10 min ("contratos ejecutables + fail-loud").
- [ ] **Universidades** — cursos de ingeniería, sociología, geografía,
      periodismo de datos y economía: ofrecer "dataset listo para tu curso" con
      los notebooks Colab y `docs/citation.md`.
- [ ] **Periodismo de datos** — medios y ONGs (CIPER, LaBot, El Mostrador,
      Fundación Datos Protegidos): pitch corto "datos comunales listos, con DOI
      y fuente por capa".
- [ ] **Hugging Face** — pedir likes/feedback en el dataset card (0 likes hoy) y
      publicar un Space mínimo que consuma el mirror.
- [ ] **datos.gob.cl / comunidad open data** — compartir el catálogo DCAT y el
      DOI; explorar federación.

---

## 5. Leads accionables del post del 2026-09-26 (17 comentarios)

> **Estado 2026-09-26:** el autor ya respondió a Reynaldo (guía de fuentes/licencias).
> La vista pública de LinkedIn no muestra todas las respuestas anidadas: confirmar
> en la UI las de Cristian, Tushar y Luis. Los 3 pedidos ya tienen issue.

| Persona | Señal | Issue | Acción |
|:---|:---|:---|:---|
| Cristian Orrego (CEAZAmet) | **DGA (meteo/caudales) + DMC** históricos y actuales en un solo lugar | [#107](https://github.com/cortega26/chile-hub/issues/107) | Confirmar respuesta en LinkedIn; validar API/dump + licencia contra `docs/dataset-inclusion-criteria.md` |
| Tushar Punjabi | Aportar datos de **energía/renovables y consumo** | [#108](https://github.com/cortega26/chile-hub/issues/108) | Confirmar respuesta; compartir `CONTRIBUTING.md` + playbook; ojo: `consumo_electrico_comunal` está `deprecated` |
| Luis Oliveros (PhD Data Science) | **Datos de desastres 2024–2026** scrapeados, sin curar | [#109](https://github.com/cortega26/chile-hub/issues/109) | Confirmar respuesta; pedir fuente primaria y licencia (sin eso queda `under-review`) |
| Reynaldo Fulguera (Bolivia) | Replicar el framework en su ciudad | — | **Respondida** (guía de fuentes/licencias); compartir `AGENTS.md` + caso de estudio |
| Gabriela Marín / Valentina Huepe (Perú) | Iniciativa similar en Perú | — | Conectar y comparar arquitecturas |
| Ninotschka, José Astorga, Hugo, Marcelo, Daniel Olivares | Apoyo/gracias | — | Responder y agradecer; no convertir en venta |

**Guardrails:** no prometer fechas ni features; toda sugerencia entra por
`dataset_request` y pasa los criterios de inclusión. La conversación pública es
el activo; el issue es el compromiso.

---

## 6. Qué NO hacer

- No pedir upvotes ni "voten por mí" (baneo en HN/Reddit).
- No publicar en 5 lugares el mismo día con el mismo texto (spam).
- No prometer capas nuevas sin evaluación de licencia/mantenimiento.
- No usar el DOI/paper como gancho comercial; es infraestructura de citación.
