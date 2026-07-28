# ADR-014: Separar drift esperado de drift real en el dashboard de salud

**Fecha:** 2026-07-28
**Estado:** accepted
**Decision:** La clasificación de salud distingue la parcialidad y los warnings
que son **diseño confirmado** de los que exigen **acción**, mediante dos campos
nuevos — `coverage.expected` (declarado en el contrato vía `coverage_policy`) y
`expected_warnings` (declarado por el validador que emite el mensaje) — sin
agregar ningún valor a los enums `drift_status`, `coverage_status` o
`source_mode`, y sin relajar ningún gate de `scripts/verify_pipeline.py`.

## Contexto

`hub_health.json` reportaba `drifted_count: 8` y `warn_count: 7` sobre 19
datasets. La auditoría dataset por dataset mostró que **4 de los 8 "drifted" eran
un bug de clasificación, no un problema de datos**:

| Dataset | Realidad | Por qué se marcaba drifted |
|---|---|---|
| `perfil_territorial_comunal` | derivado de capas validadas, 346/346, 0 warnings | su `source_mode` se calculaba `"live" if all(upstream == "live")`; `finanzas_municipales` es `monthly` → caía a `fallback` |
| `finanzas_municipales` | 345/346, 0 warnings; el contrato **ya declaraba** `coverage_policy: "partial_expected"` | `build_coverage` nunca leía `coverage_policy` |
| `indicadores_urbanos_siedu` | cobertura urbana intencional; contrato **ya declaraba** `partial_expected` | ídem, más un warning informativo |
| `pobreza_comunal` / `partidos_politicos` | parcialidad SAE por diseño; `estado_legal` poblado en 15/36 según SERVEL | cualquier warning ⇒ `degradation: warning` ⇒ drifted |

El costo de no arreglarlo era que el dashboard público entrenaba a sus lectores a
ignorar `drifted_count`: si la mitad de las alarmas es ruido estructural, la
señal de las reales se pierde.

## Decision

### 1. `monthly` no es un fallback (fuente única de verdad)

`VALID_SOURCE_MODES` y `NON_FALLBACK_SOURCE_MODES` viven ahora en
`src/builders/_shared.py` y los consumen tanto el build (`src/builders/metadata.py`)
como el gate de publicación (`scripts/verify_pipeline.py`). El predicado de la
capa derivada usa pertenencia a `NON_FALLBACK_SOURCE_MODES` en vez de `== "live"`.

**Por qué no un `source_mode: "derived"`**: la derivación ya está expresada en
`source_detail` y en `notes`; un valor nuevo cuesta seis gates y no agrega
información.

### 2. `coverage.expected`, no un `coverage_status` nuevo

`build_coverage` lee `coverage_policy` del contrato y emite un booleano
`expected` **siempre presente** (más `expected_reason` cuando es verdadero).
`status` conserva su enum: `partial` sigue describiendo correctamente la
cobertura — lo que cambia es si esa parcialidad era esperada.

**Por qué no un tercer valor de enum**: `coverage_status` está gateado en cinco
puntos de `verify_pipeline.py` y consumido por la landing, el catálogo y el
bundle. Un campo ortogonal es aditivo y no rompe consumidores existentes.

### 3. `expected_warnings` se declara en el emisor, nunca en el consumidor

`src/validation.py::_add_expected_warning()` agrega el mensaje a `warnings`
**y** a `expected_warnings`. `warnings` sigue conteniendo todos los mensajes en
todos los artefactos: es el registro transparente y hay gates y tests que lo
asumen. `build_degradation` calcula los accionables como la diferencia; si no
queda ninguno, devuelve `status: "none"` con un `impact` que **enumera** los
esperados ("N observación(es) esperada(s): …"), no que los esconde.

**Por qué no clasificar por regex sobre el texto en el consumidor**: se rompe la
primera vez que alguien reformula el mensaje, y deja la política lejos de la
regla que la origina.

### 4. Quién puede declarar un warning como esperado

Sólo dos lugares, ambos revisables en el diff:

1. El **contrato** del dataset (`coverage_policy: "partial_expected"`), para
   parcialidad estructural de la fuente.
2. La **regla de validación** que emite el mensaje, vía `_add_expected_warning()`,
   con una justificación en el comentario o docstring adyacente.

Nunca en `build_degradation`, `build_drift`, `build_hub_health` ni en la landing.
Un dataset que cambia de `drifted` a `healthy` **sin** una de esas dos
declaraciones es un silenciador, no una reclasificación.

### 5. `warning_count` no cambia de significado

`build_hub_health` gana `actionable_warning_count` junto al `warning_count`
existente; la severidad se deriva del accionable. Ningún artefacto reinterpreta
`warning_count`, así que los consumidores viejos siguen leyendo lo mismo.

## Consecuencias

- `drifted_count` baja de **8 a 3**; `warn_count` de **7 a 3**;
  `overall_status` sigue siendo `warn`. Los 3 restantes son problemas reales:
  `empresas` (1 RUT inválido), `indicadores` (`ipc` reusado del artefacto
  publicado) y `consumo_electrico_comunal` (fuente decomisionada por CNE).
- Gates nuevos en `verify_pipeline.py`: `coverage.expected` booleano y presente
  siempre, `expected` sólo sobre `status == "partial"`, y
  `actionable_warning_count` entero `<= warning_count`. Ninguno existente se relajó.
- La landing distingue `partial` de `partial esperada` y calcula el badge de
  atención con los accionables.

## Preguntas abiertas

1. **`pobreza_comunal`**: su contrato declara `coverage_policy: "partial"`, pero
   su propio warning dice "parcial por diseño". Hoy su `coverage_status` es
   `not_applicable` (no tiene `expected_record_count`), así que el flag sería
   inerte; su reclasificación viene por la vía de `expected_warnings`. Si alguna
   vez gana un baseline de cardinalidad, habrá que decidir entre
   `partial_expected` en el contrato o dejarlo driftar.
2. **`geometria_comunal`**: mismo caso (`coverage_policy: "partial"`), pendiente
   de que el carril candidate se estabilice (Planes 064/065).
3. **`resultados_educacionales` y `delincuencia_comunal`** declaran
   `partial_expected` pero hoy no alcanzan `coverage_status: partial`, así que el
   flag queda inerte. Están cubiertos por tests para que un cambio futuro de
   cobertura no los haga driftar sin que nadie lo haya ejercitado.

## Alternativas descartadas

- **Un tercer `drift_status` (`expected_drift`)**: seis gates a tocar, y obliga a
  cada consumidor a aprender un estado nuevo para expresar algo que un booleano
  ortogonal ya expresa.
- **Bajar los contadores tocando datos o quitando warnings**: sería esconder el
  problema; el plan lo declara explícitamente como STOP condition.
- **Filtrar los mensajes de `warnings`**: destruiría el registro transparente que
  el resto del pipeline y varios tests asumen.
