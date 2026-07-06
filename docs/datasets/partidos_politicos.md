# Partidos políticos — Cámara de Diputadas y Diputados + SERVEL

> **Carril:** `stable_publishable` — incluido en el bundle público.
> **Fuentes:** Cámara de Diputadas y Diputados de Chile, portal de datos abiertos
> (`WSComun.asmx/retornarPartidosPoliticos`) + SERVEL (`partidos-constituidos`/
> `partidos-en-formacion`).
> **review_by:** 2026-10-05 · **stalled_after_days:** 90

## Descripción

Roster de partidos políticos conocidos por la Cámara de Diputadas y Diputados,
obtenido de su web service de datos abiertos. Incluye partidos **vigentes e
históricos** (los asociados a las militancias registradas de los diputados/as).
`estado_legal` y `fecha_constitucion` se completan uniendo por nombre normalizado
contra las dos páginas públicas de SERVEL que listan partidos constituidos y en
formación.

Datos institucionales públicos; **sin datos personales** (línea roja Ley 19.628,
ver `docs/legal/b2-2-electoral-research.md`).

## Schema

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_partido` | string | Identificador/ sigla del partido en la Cámara (clave) |
| `nombre` | string | Nombre oficial del partido |
| `sigla` | string | Sigla/alias del partido |
| `estado_legal` | string \| null | `constituido` \| `en_formacion` — vía SERVEL, por join de nombre; nulo si el partido no aparece en ninguna de las dos páginas |
| `fecha_constitucion` | string \| null | Fecha de constitución (YYYY-MM-DD), parseada desde el texto en español de SERVEL |
| `ambito` | string \| null | Ámbito (nacional/regional) — **no provisto por ninguna fuente encontrada**; siempre nulo |
| `fuente` | string | Organismo emisor |
| `url_fuente` | string | URL del web service |
| `fecha_consulta` | string | Fecha (YYYY-MM-DD) de la consulta |

## Cobertura

- **Registros:** ~36 partidos (varía según altas/bajas; el roster de la Cámara incluye históricos).
- **`estado_legal`/`fecha_constitucion`:** ~15/36 matcheados por nombre contra SERVEL
  (observado 2026-07-06). El resto son partidos históricos que ya no aparecen en las
  páginas vigentes de SERVEL — coherente con que el roster de la Cámara incluye
  militancias pasadas, no solo partidos legalmente activos hoy.
- **Frecuencia de actualización:** bajo demanda (fuentes estables, sin cadencia fija).

## Limitaciones

1. **Roster de la Cámara, no el registro legal completo de SERVEL:** incluye
   partidos históricos sin match en SERVEL, que quedan con `estado_legal`/
   `fecha_constitucion` nulos (no se inventa un valor).
2. **`ambito` (nacional/regional) siempre nulo:** se buscó esa señal en el sitio de
   SERVEL (incluida la página de partidos en formación) y no se encontró en ninguna
   fuente institucional disponible.
3. **Join por nombre, no por identificador compartido:** la Cámara y SERVEL no
   comparten un ID de partido; el join normaliza texto (minúsculas, sin acentos, sin
   sufijo "de Chile") pero puede fallar ante variaciones de nombre no previstas.

## Referencias

- Portal de datos abiertos de la Cámara: https://opendata.camara.cl/
- Endpoint: `WSComun.asmx/retornarPartidosPoliticos`
- SERVEL — partidos constituidos: https://www.servel.cl/partidos-politicos/partidos-constituidos/
- SERVEL — partidos en formación: https://www.servel.cl/partidos-politicos/partidos-en-formacion/
- Research electoral: `docs/legal/b2-2-electoral-research.md`
- Plan 023 — Ola B: `plans/023-autoridades-electas-partidos-politicos.md`
