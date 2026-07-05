# Partidos políticos — Cámara de Diputadas y Diputados

> **Carril:** `candidate` — NO incluido en el bundle público.
> **Fuente:** Cámara de Diputadas y Diputados de Chile, portal de datos abiertos
> (`WSComun.asmx/retornarPartidosPoliticos`).
> **review_by:** 2026-10-05 · **stalled_after_days:** 90

## Descripción

Roster de partidos políticos conocidos por la Cámara de Diputadas y Diputados,
obtenido de su web service de datos abiertos. Incluye partidos **vigentes e
históricos** (los asociados a las militancias registradas de los diputados/as).
Se publica en carril `candidate` mientras se completan sus campos legales desde
SERVEL y se valida una ventana de estabilidad antes de promoverlo a
`stable_publishable`.

Datos institucionales públicos; **sin datos personales** (línea roja Ley 19.628,
ver `docs/legal/b2-2-electoral-research.md`).

## Schema

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_partido` | string | Identificador/ sigla del partido en la Cámara (clave) |
| `nombre` | string | Nombre oficial del partido |
| `sigla` | string | Sigla/alias del partido |
| `estado_legal` | string \| null | Estado legal (constituido/en_formacion/disuelto) — no provisto por la Cámara; completar con SERVEL |
| `fecha_constitucion` | string \| null | Fecha de constitución — no provista por la Cámara |
| `ambito` | string \| null | Ámbito (nacional/regional) — no provisto por la Cámara |
| `fuente` | string | Organismo emisor |
| `url_fuente` | string | URL del web service |
| `fecha_consulta` | string | Fecha (YYYY-MM-DD) de la consulta |

## Cobertura

- **Registros:** ~36 partidos (varía según altas/bajas; el roster incluye históricos).
- **Frecuencia de actualización:** bajo demanda (fuente estable, sin cadencia fija).

## Limitaciones

1. **Roster de la Cámara, no el registro legal de SERVEL:** incluye partidos
   históricos y no distingue por sí mismo cuáles están legalmente vigentes. Los
   campos `estado_legal`, `fecha_constitucion` y `ambito` **no vienen en esta
   fuente** y quedan nulos en v1.
2. **Carril `candidate`:** por lo anterior, no entra al bundle público hasta
   completar los campos legales (SERVEL) y validar estabilidad.

## Regla de salida (promoción)

Se promueve a `stable_publishable` cuando: (a) se completen los campos legales
desde el registro de SERVEL, y (b) el extractor se mantenga estable hasta
`review_by` (2026-10-05). Si la fuente deja de estar disponible y no se asegura
un reemplazo, se degrada a `rejected`.

## Referencias

- Portal de datos abiertos de la Cámara: https://opendata.camara.cl/
- Endpoint: `WSComun.asmx/retornarPartidosPoliticos`
- Research electoral: `docs/legal/b2-2-electoral-research.md`
- Plan 023 — Ola B: `plans/023-autoridades-electas-partidos-politicos.md`
