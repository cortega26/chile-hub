# ADR-009: Resolutor de nombres de comuna a codigos CUT

**Fecha:** 2026-07-24
**Estado:** accepted
**Decision:** Se agrega `ChileHub.resolve_comunas(names)`, un resolutor
**determinista** (normalizacion + coincidencia exacta) de nombres de comuna a
codigos CUT, junto con el helper reutilizable `normalize_comuna_name()` y el
subcomando CLI `resolve`.

## Contexto

El trabajo #1 real de cualquiera que consuma datos chilenos es: *"tengo una
columna de nombres de comuna tipeados por humanos ('Ñuñoa', 'nunoa', 'Concón',
'CONCEPCION') y necesito el `codigo_comuna` (CUT) para poder unir con datos
oficiales"*. El product-spec define el exito del MVP (criterio #4) como *"unirlo
con sus propios datos sin trabajo de limpieza"* — y ese era el unico criterio de
exito que ningun metodo publico cubria: `cross_view()` y `sql()` ya asumen que
el usuario tiene `codigo_comuna`; no habia forma de *obtenerlo* desde un nombre.

La infraestructura para hacerlo ya existia pero enterrada e inaccesible:

- La invariante #4 del proyecto construye `nombre_comuna_clean` precisamente
  como "clave de busqueda para joins de texto inexactos", pero la cadena de
  normalizacion que la produce vivia inline, sin ser una funcion reutilizable,
  en `subdere_extractor.py:560-570`.
- Un lookup `{nombre_comuna_clean -> (codigo_comuna, codigo_region)}` ya estaba
  hand-rolled internamente en `autoridades_locales_extractor.py:437`
  (`_load_comunas_lookup`) — evidencia directa de una API publica que el
  codigo interno necesito y tuvo que rodear a mano.

## Decision

1. **Helper reutilizable**: `src/chile_hub/text.py::normalize_comuna_name(name)`
   reproduce exactamente la cadena de reemplazos de
   `subdere_extractor.py:560-570` (minusculas, sin acentos, sin `ñ`), operando
   sobre `str` de Python en vez de una expresion Polars, para poder normalizar
   input de usuario arbitrario.

2. **API shape**: `ChileHub.resolve_comunas(names: list[str]) -> pl.DataFrame`.
   Normaliza cada nombre con `normalize_comuna_name` y hace **coincidencia
   exacta** contra la columna `nombre_comuna_clean` del dataset `comunas`.
   Devuelve una fila por input (mismo orden, duplicados preservados) con
   columnas `input`, `codigo_comuna`, `nombre_comuna`, `codigo_region`,
   `matched` (bool). Los no-encontrados devuelven `matched=False` y codigos
   `null` — **explicitamente, sin lanzar excepcion**: el usuario decide que
   hacer con los no-matcheados (es una operacion de resolucion masiva sobre
   una columna, no una busqueda puntual donde un miss es excepcional).

3. **Alcance determinista, no fuzzy**: el match es exacto sobre el nombre
   normalizado. No se implementa correccion de typos ni edit-distance en esta
   version (ver Preguntas abiertas).

4. **CLI**: subcomando `chile-hub resolve <nombres...>` modelado exactamente
   sobre `cross` (mismo helper `_output_dataframe`, mismas opciones
   `--format`/`--output`).

5. **`codigo_comuna` siempre `pl.String`**: la invariante CUT del proyecto se
   preserva en el schema explicito de retorno (`schema={"codigo_comuna":
   pl.String, ...}`), nunca `int`.

### Chequeo de colisiones (Step 4)

Se verifico si algun `nombre_comuna_clean` no es unico entre las 346 comunas
publicadas:

```
duplicados: []
```

No hay colisiones hoy — cada `nombre_comuna_clean` mapea a exactamente una
comuna, por lo que el `dict` de lookup interno no pierde matches. Si una
comuna futura introdujera un nombre normalizado duplicado, el lookup actual
(un `dict` simple) se quedaria con el ultimo match en orden de iteracion —
ver Preguntas abiertas #4 para el seguimiento.

## Consecuencias

- Positivas: cierra el unico criterio de exito del MVP que ningun metodo
  publico cubria. Reutiliza infraestructura ya validada (`nombre_comuna_clean`)
  en vez de introducir una segunda fuente de verdad para normalizacion.
  Comportamiento explicito ante no-matches (columna `matched`, no excepcion)
  hace que sea seguro usar sobre columnas grandes con datos sucios.

- Negativas: dos copias de la misma cadena de normalizacion
  (`subdere_extractor.py` inline y `text.py`) que pueden divergir en silencio
  si alguien edita una sin la otra — mitigado por el test de paridad
  anti-divergencia obligatorio en `tests/test_core.py`, que falla la suite si
  divergen. El acople real (DRY) queda como follow-up (ver Maintenance notes
  del plan 050).

  **Una divergencia intencional ya existe y es segura**: `normalize_comuna_name`
  recorta espacios al borde (`.strip()`) antes de normalizar; la cadena Polars
  del extractor no lo hace (no lo necesita: `nombre_comuna` ya llega limpio de
  BCN). El recorte no puede producir un match falso (ninguna comuna publicada
  tiene espacios al borde en su forma limpia hoy) y existe para tolerar input de
  usuario tipeado a mano, el caso de uso real de `resolve_comunas`. Documentado
  en el docstring de `text.py`; cubierto por un test dedicado en
  `tests/test_pipeline_logic.py` (separado del test de paridad, que sólo
  verifica el resto de la cadena contra datos reales sin espacios al borde).

## Preguntas abiertas

1. **¿Se agrega un modo fuzzy opcional (`method="fuzzy"`) con edit-distance?**
   Riesgo: se desborda hacia territorio de geocoder, fuera de la mision
   "acotada" del product-spec. Recomendacion de este ADR: no, hasta que haya
   demanda concreta de usuarios con datos sucios que el match exacto no cubra.

2. **¿Se agrega `resolve_regiones()` analogo?** 16 regiones, trivial de
   implementar si se decide — mismo patron, dataset mas chico.

3. **¿Aceptar `pl.DataFrame`/`pl.Series` de entrada ademas de `list[str]`?**
   Hoy el usuario pasa `df["columna"].to_list()`. Aceptar la Series/columna
   directamente ahorra esa conversion pero agrega ramificacion de tipos al
   contrato. Diferido hasta ver si el `.to_list()` explicito genera friccion
   real reportada.

4. **¿Que pasa si aparecen colisiones de `nombre_comuna_clean` en el futuro?**
   Hoy no hay ninguna (ver chequeo arriba), pero si una comuna nueva colisiona
   con una existente, el lookup actual (dict) silenciosamente se queda con un
   solo match. Si eso ocurre, decidir si el contrato de retorno debe permitir
   multiples matches por input, o si se resuelve por prioridad de
   `codigo_region`/orden alfabetico. No resolver preventivamente sin un caso
   real.

## Alternativas consideradas

- **Refactorizar `subdere_extractor.py` para importar `normalize_comuna_name`
  desde ya** — Se descarto para este plan: tocar `src/extractors/**` dispara
  el gate de co-cambio de `check_companion_paths.py` (exige tocar
  `test_extractors.py`) y agrega riesgo de regenerar el dataset base sin
  necesidad. Queda como follow-up explicito (ver Maintenance notes del plan
  050) una vez que el guardrail de paridad anti-divergencia demuestre que las
  dos copias se mantienen sincronizadas en la practica.

- **Lanzar excepcion en no-matches** — Se descarto: `resolve_comunas` esta
  pensado para resolver una columna completa de datos potencialmente sucios;
  abortar en el primer miss forzaria al usuario a limpiar antes de poder ver
  cuantos matches tiene, en vez de dejarle decidir con la columna `matched`.

- **Modo fuzzy desde el inicio** — Se descarto explicitamente (ver Preguntas
  abiertas #1): cambia la mision del proyecto de "datos curados y
  deterministas" a "geocoder con heuristicas", con superficie de mantenimiento
  mucho mayor (umbral de similitud, falsos positivos) para un beneficio no
  demostrado todavia.
