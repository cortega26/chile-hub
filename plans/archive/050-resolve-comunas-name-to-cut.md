# Plan 050: Exponer un resolutor público `resolve_comunas()` (nombres → códigos CUT)

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de avanzar. Si ocurre algo
> de la sección "STOP conditions", detente y reporta — no improvises. Al terminar,
> actualiza la fila de estado de este plan en `plans/README.md` (salvo que un
> revisor te haya despachado y te diga que él mantiene el índice).
>
> **Este es un plan de diseño/spike con entregable de código.** El objetivo no es
> sólo escribir un método: es **decidir su contrato** (determinista vs. fuzzy),
> implementarlo en su versión determinista, y dejar las preguntas abiertas
> registradas en un ADR. No amplíes el alcance a fuzzy/edit-distance sin aprobación
> explícita — ver STOP conditions.
>
> **Drift check (córrelo primero)**:
> `git diff --stat 7ebf94b..HEAD -- src/chile_hub/core.py src/extractors/subdere_extractor.py src/extractors/autoridades_locales_extractor.py`
> Si alguno de esos archivos cambió desde que se escribió este plan, compara los
> excerptos de "Estado actual" contra el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW-MED (decisión de alcance determinista vs. fuzzy es el único riesgo real)
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `7ebf94b`, 2026-07-14

## Why this matters

El trabajo #1 real de cualquiera que consuma datos chilenos es: *"tengo una columna
de nombres de comuna tipeados por humanos ('Ñuñoa', 'nunoa', 'Concón', 'CONCEPCION')
y necesito el `codigo_comuna` (CUT) para poder unir con datos oficiales"*. El
product-spec define el éxito del MVP (criterio #4, `docs/product-spec.md:175`) como
*"unirlo con sus propios datos sin trabajo de limpieza"* — y **ese es el único
criterio de éxito que ningún método público actual cubre**. `cross_view()` y `sql()`
ya asumen que el usuario tiene `codigo_comuna`; no hay forma de *obtenerlo* desde un
nombre.

La infraestructura para hacerlo ya existe pero está **enterrada e inaccesible**: la
invariante #4 del proyecto (`AGENTS.md:259-271`) construye la columna
`nombre_comuna_clean` precisamente *"clave de búsqueda para joins de texto
inexactos"*, pero (a) la normalización que la produce vive **inline, sin ser una
función reutilizable**, en `subdere_extractor.py:560-570`, así que un usuario no
puede reproducirla; y (b) el diccionario de lookup `{nombre_comuna_clean →
(codigo_comuna, codigo_region)}` ya está **hand-rolled internamente** en
`autoridades_locales_extractor.py:437` (`_load_comunas_lookup`) — evidencia directa
de una API pública que el código interno necesitó y tuvo que rodear a mano. Este plan
saca esa capacidad a la superficie pública.

## Current state

Archivos relevantes:

- `src/chile_hub/core.py` — clase `ChileHub` con toda la API pública. Aquí va el
  método nuevo. Sus métodos siguen un patrón consistente: docstring en español con
  Args/Returns/Raises, tipos `str | Dataset`, retorno `pl.DataFrame`. Modela el
  método nuevo sobre `search_datasets` (`core.py:670`) para la firma+docstring y
  sobre `cross_view` (`core.py:337`) para el manejo de DataFrames Polars.
- `src/extractors/subdere_extractor.py:558-570` — **única definición** de la cadena
  de normalización, inline y no reutilizable:

  ```python
  # src/extractors/subdere_extractor.py:558-570
  df = df.with_columns(
      pl.col("nombre_comuna")
      .str.to_lowercase()
      .str.replace_all("á", "a")
      .str.replace_all("é", "e")
      .str.replace_all("í", "i")
      .str.replace_all("ó", "o")
      .str.replace_all("ú", "u")
      .str.replace_all("ü", "u")
      .str.replace_all("ñ", "n")  # Ej: "Ñuñoa" → "nunoa"
      .alias("nombre_comuna_clean")
  )
  ```

- `src/extractors/autoridades_locales_extractor.py:437-452` — lookup ya hand-rolled
  internamente (prueba de la API faltante):

  ```python
  def _load_comunas_lookup() -> dict[str, tuple[str, str]]:
      """``nombre_comuna_clean -> (codigo_comuna, codigo_region)`` desde staging/comunas.csv."""
      comunas_path = Path(STAGING_DIR) / "comunas.csv"
      if not comunas_path.exists():
          return {}
      df = pl.read_csv(comunas_path, schema_overrides={"codigo_comuna": pl.String, "codigo_region": pl.String})
      return {
          row["nombre_comuna_clean"]: (row["codigo_comuna"], row["codigo_region"])
          for row in df.iter_rows(named=True)
      }
  ```

- El dataset `comunas` publicado tiene las columnas `codigo_comuna`, `nombre_comuna`,
  `nombre_comuna_clean`, `codigo_region`, `nombre_region` (ver el `.select(...)` en
  `subdere_extractor.py:573-587`). Se carga con `self.load_polars("comunas")`.

Convenciones que aplican aquí:

- **Invariante #1** (`AGENTS.md:209`): los códigos CUT son **strings de longitud
  fija** (`"05101"`). El resolutor debe devolverlos como `pl.String`, nunca int.
- **Invariante #5** (`AGENTS.md:520`): paths relativos a `__file__`. No aplica aquí
  porque lees vía `self.load_polars`, pero no introduzcas paths a CWD.
- Excepciones de dominio: `ChileHubDatasetError`, `ChileHubDataError` (ya definidas
  en `core.py`, usadas por los métodos existentes). Reúsalas.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Bootstrap (si `.venv` no existe) | `make bootstrap` | exit 0 |
| Build de datos (requerido antes de test_core) | `make build` | exit 0, `data/normalized/` poblado |
| Tests del método (requieren normalized) | `./.venv/bin/pytest tests/test_core.py -v` | todos pasan |
| Tests del helper de normalización (no requieren normalized) | `./.venv/bin/pytest tests/test_pipeline_logic.py -v` | todos pasan |
| Lint | `make lint` | exit 0 |
| Format check | `make format-check` | exit 0 |

## Scope

**In scope** (los únicos archivos que debes crear/modificar):

- `src/chile_hub/text.py` (crear) — helper de normalización reutilizable.
- `src/chile_hub/core.py` — método `resolve_comunas()` + subcomando CLI `resolve`.
- `tests/test_core.py` — tests del método público.
- `tests/test_pipeline_logic.py` — tests del helper `normalize_comuna_name`.
- `docs/adr/ADR-009-resolutor-nombres-comunales.md` (crear) — decisión + preguntas abiertas.
- `plans/README.md` — fila de estado.

**Out of scope** (NO tocar, aunque parezcan relacionados):

- `src/extractors/subdere_extractor.py` — **NO** refactorices la cadena inline para
  que importe el helper nuevo en este plan. Tocar `src/extractors/**` dispara el gate
  de co-cambio de `scripts/check_companion_paths.py` (exige tocar `test_extractors.py`)
  y agrega riesgo de regenerar el dataset base. El DRY del extractor es un follow-up
  explícito (ver Maintenance notes).
- `src/validation.py`, `src/build_dev_db.py` — sin relación.
- Cualquier lógica **fuzzy / edit-distance / typo-correction** — fuera de alcance
  duro (ver STOP conditions). Este plan entrega match **determinista**.

## Git workflow

- Branch: `advisor/050-resolve-comunas`
- Commits estilo conventional commits (el repo los usa; ej. reciente:
  `feat(landing): ...`, `docs(plans): ...`). Ej. para este plan:
  `feat(api): agrega resolve_comunas() para mapear nombres a códigos CUT`.
- No hagas push ni abras PR salvo instrucción explícita del operador.

## Steps

### Step 1: Extrae la normalización a un helper reutilizable

Crea `src/chile_hub/text.py` con una función pura que reproduzca **exactamente** la
cadena de `subdere_extractor.py:560-570` (mismo orden, mismos reemplazos), operando
sobre un `str` de Python (no una expresión Polars), para poder normalizar input de
usuario:

```python
"""Normalización de texto compartida para búsqueda de nombres sin acento.

La cadena de reemplazos debe mantenerse idéntica a la que produce
``nombre_comuna_clean`` en ``src/extractors/subdere_extractor.py`` (invariante #4,
AGENTS.md §4.5). Si esa cadena cambia, cambia también aquí (ver ADR-009).
"""

_ACCENT_MAP = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}


def normalize_comuna_name(name: str) -> str:
    """Normaliza un nombre de comuna a su forma ``nombre_comuna_clean``.

    Minúsculas, sin acentos, sin ``ñ``. Es la clave canónica de join de texto
    inexacto del proyecto. ``normalize_comuna_name("Ñuñoa") == "nunoa"``.
    """
    out = name.strip().lower()
    for src, dst in _ACCENT_MAP.items():
        out = out.replace(src, dst)
    return out
```

**Verify**: `./.venv/bin/python -c "from src.chile_hub.text import normalize_comuna_name as n; assert n('Ñuñoa')=='nunoa'; assert n('  CONCÓN ')=='concon'; print('ok')"` → imprime `ok`

### Step 2: Implementa `ChileHub.resolve_comunas()`

Agrega el método a la clase `ChileHub` en `core.py` (colócalo junto a `cross_view` /
`search_datasets`). Contrato **determinista**:

- Entrada: `names: list[str] | pl.Series | pl.DataFrame` con una columna, o simple
  `list[str]`. Para mantenerlo simple y verificable, acepta `list[str]` en esta
  versión (documenta que una columna de DataFrame se pasa como `df["col"].to_list()`).
- Normaliza cada nombre con `normalize_comuna_name` y hace **exact match** contra la
  columna `nombre_comuna_clean` del dataset `comunas`.
- Devuelve un `pl.DataFrame` con una fila por input (preservando orden y duplicados):
  columnas `input` (str original), `codigo_comuna` (str o null), `nombre_comuna`
  (str o null), `codigo_region` (str o null), `matched` (bool).
- Los no-encontrados devuelven `matched=False` y códigos null — **explícitamente, sin
  lanzar excepción** (el usuario decide qué hacer con los no-matcheados).

Forma objetivo:

```python
def resolve_comunas(self, names: list[str]) -> pl.DataFrame:
    """Resuelve nombres de comuna (tipeados por humanos) a códigos CUT.

    Match **determinista**: normaliza cada nombre a su forma ``nombre_comuna_clean``
    (minúsculas, sin acentos, sin ``ñ``) y hace coincidencia exacta contra el
    dataset ``comunas``. No corrige typos ni hace coincidencia difusa.

    Args:
        names: Lista de nombres de comuna. Para resolver una columna de un
            DataFrame, pásala como ``df["mi_columna"].to_list()``.

    Returns:
        DataFrame Polars con una fila por input (mismo orden, duplicados
        preservados) y columnas: ``input``, ``codigo_comuna``, ``nombre_comuna``,
        ``codigo_region``, ``matched`` (bool). Los no encontrados tienen
        ``matched=False`` y códigos nulos.

    Examples:
        >>> hub = ChileHub()
        >>> hub.resolve_comunas(["Ñuñoa", "concon", "No Existe"])
    """
    from src.chile_hub.text import normalize_comuna_name  # o import a nivel módulo

    comunas = self.load_polars("comunas")
    lookup = {
        row["nombre_comuna_clean"]: (row["codigo_comuna"], row["nombre_comuna"], row["codigo_region"])
        for row in comunas.iter_rows(named=True)
    }
    rows = []
    for original in names:
        key = normalize_comuna_name(str(original))
        hit = lookup.get(key)
        rows.append({
            "input": original,
            "codigo_comuna": hit[0] if hit else None,
            "nombre_comuna": hit[1] if hit else None,
            "codigo_region": hit[2] if hit else None,
            "matched": hit is not None,
        })
    return pl.DataFrame(rows, schema={
        "input": pl.String, "codigo_comuna": pl.String, "nombre_comuna": pl.String,
        "codigo_region": pl.String, "matched": pl.Boolean,
    })
```

Ajusta el `import` al estilo del archivo (los demás métodos importan a nivel de
módulo; si el resto de `core.py` importa así, mueve `from .text import
normalize_comuna_name` a la cabecera — verifica cómo importa `core.py` sus módulos
hermanos como `datasets`/`data_manager` y **replica ese estilo**, absoluto o
relativo).

**Verify**: `make build && ./.venv/bin/python -c "from src.chile_hub import ChileHub; h=ChileHub(); r=h.resolve_comunas(['Ñuñoa','No Existe']); print(r.to_dicts())"` →
la fila de `Ñuñoa` tiene `matched=True` y un `codigo_comuna` de 5 chars; la de
`No Existe` tiene `matched=False` y `codigo_comuna=None`.

### Step 3: Agrega el subcomando CLI `resolve`

En `core.py`, junto a los `add_parser(...)` existentes (`cross` está en `core.py:2105`,
`search` en `core.py:2121`), agrega un subparser `resolve` que tome uno o más nombres
posicionales y renderice el resultado como tabla (reusa el helper `render_table` ya
usado por `cross`/`search`). Modela el wiring exactamente sobre el subcomando `cross`:
busca `subparsers.add_parser("cross"` y su bloque `set_defaults`/handler, y replica la
estructura para `resolve`.

**Verify**: `./.venv/bin/python -m src.chile_hub resolve Ñuñoa Concón "No Existe"` →
imprime una tabla con 3 filas; `Ñuñoa` y `Concón` con código, `No Existe` sin código.

### Step 4: Escribe ADR-009 con las preguntas abiertas

Crea `docs/adr/ADR-009-resolutor-nombres-comunales.md` siguiendo el formato de los
ADR existentes (lee `docs/adr/ADR-007-sql-query-surface.md` como plantilla: secciones
**Fecha / Estado / Decisión / Contexto / Consecuencias / Alternativas consideradas**).
Registra:

- **Decisión**: resolutor **determinista** (normalize + exact match sobre
  `nombre_comuna_clean`); no-matches devueltos explícitamente, sin excepción.
- **Preguntas abiertas** (déjalas como sección explícita, no las resuelvas):
  1. ¿Se agrega un modo fuzzy opcional (`method="fuzzy"`) con edit-distance? Riesgo:
     se desborda hacia territorio de geocoder, fuera de la misión "acotada" del
     product-spec. Recomendación del plan: no, hasta que haya demanda.
  2. ¿Se agrega `resolve_regiones()` análogo? (16 regiones, trivial si se decide.)
  3. ¿Aceptar `pl.DataFrame`/`pl.Series` de entrada además de `list[str]`?
  4. ¿Colisiones? Verifica si algún `nombre_comuna_clean` no es único en las 346
     comunas (ej. comunas homónimas). Documenta el hallazgo en el ADR — si hay
     colisiones, el `dict` actual pierde una; decide si es aceptable o si el retorno
     debe permitir múltiples matches. **Corre**:
     `./.venv/bin/python -c "from src.chile_hub import ChileHub; c=ChileHub().load_polars('comunas'); print('duplicados:', c.filter(c['nombre_comuna_clean'].is_duplicated()).select('nombre_comuna_clean','codigo_comuna').to_dicts())"`
     y pega el resultado en el ADR.

**Verify**: el archivo existe y tiene la sección "Preguntas abiertas":
`grep -c "Preguntas abiertas" docs/adr/ADR-009-resolutor-nombres-comunales.md` → ≥ 1

## Test plan

- En `tests/test_pipeline_logic.py` (no requiere normalized), agrega una clase o
  casos para `normalize_comuna_name`: `"Ñuñoa"→"nunoa"`, `"CONCÓN"→"concon"`,
  espacios al borde recortados, string ya limpio sin cambios, string vacío.
- En `tests/test_core.py` (requiere `make build` previo), agrega tests de
  `resolve_comunas`: (a) happy path — una comuna conocida resuelve a su CUT de 5
  chars; (b) no-match — devuelve `matched=False` y códigos null sin lanzar; (c)
  preservación de orden y duplicados — input `["Ñuñoa","Ñuñoa"]` devuelve 2 filas
  idénticas matcheadas; (d) el `codigo_comuna` devuelto es `pl.String` (invariante
  CUT), verifica `r.schema["codigo_comuna"] == pl.String`.
- **Test de paridad anti-divergencia (obligatorio)** — en `tests/test_core.py`, verifica
  que `normalize_comuna_name` reproduce **exactamente** `nombre_comuna_clean` para las
  346 comunas publicadas. Este es el guardrail mecánico que convierte la advertencia en
  prosa de las Maintenance notes (dos copias de la cadena que pueden divergir en
  silencio) en un fallo de CI: si divergen, `resolve_comunas` normalizaría el input del
  usuario distinto a como se construyó `nombre_comuna_clean`, produciendo no-matches
  silenciosos contra datos publicados. Forma:

  ```python
  def test_normalize_matches_published_nombre_comuna_clean(self):
      from src.chile_hub.text import normalize_comuna_name
      comunas = ChileHub().load_polars("comunas")
      for row in comunas.iter_rows(named=True):
          assert normalize_comuna_name(row["nombre_comuna"]) == row["nombre_comuna_clean"], (
              f"divergencia en {row['codigo_comuna']}: "
              f"{normalize_comuna_name(row['nombre_comuna'])!r} != {row['nombre_comuna_clean']!r}"
          )
  ```

  Si este test falla, es señal de que la cadena de `text.py` y la inline de
  `subdere_extractor.py:560-570` divergieron — trátalo como STOP condition, no relajes
  el test.
- Modela la estructura de los tests nuevos sobre los tests existentes de
  `cross_view` en `tests/test_core.py` (búscalos con
  `grep -n "cross_view" tests/test_core.py`).
- **Nota de co-cambio**: modificar `src/chile_hub/core.py` NO está entre los
  disparadores de `check_companion_paths.py companions` (esos son `src/validation.py`,
  `src/extractors/**`, `src/build_dev_db.py`), así que no hay gate de test forzado —
  pero igual escribe los tests: es la política de §8 de `AGENTS.md`.

**Verify**: `make build && ./.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py -v` → todos pasan, incluidos los nuevos.

## Done criteria

Todas deben cumplirse:

- [ ] `src/chile_hub/text.py` existe con `normalize_comuna_name`.
- [ ] `ChileHub.resolve_comunas` existe y devuelve el DataFrame con las 5 columnas y `codigo_comuna` como `pl.String`.
- [ ] `./.venv/bin/python -m src.chile_hub resolve Ñuñoa` imprime una tabla con el código.
- [ ] `make build && ./.venv/bin/pytest tests/test_core.py tests/test_pipeline_logic.py` → exit 0, con los tests nuevos presentes y pasando.
- [ ] El test de paridad anti-divergencia (`normalize_comuna_name` == `nombre_comuna_clean` para las 346 comunas) existe en `tests/test_core.py` y pasa.
- [ ] `make lint` y `make format-check` → exit 0.
- [ ] `docs/adr/ADR-009-resolutor-nombres-comunales.md` existe con sección "Preguntas abiertas" y el resultado del chequeo de colisiones pegado.
- [ ] `git status` no muestra archivos modificados fuera de la lista "In scope".
- [ ] Fila de estado actualizada en `plans/README.md`.

## STOP conditions

Detente y reporta (no improvises) si:

- El código en `subdere_extractor.py:558-570` o `autoridades_locales_extractor.py:437`
  no coincide con los excerptos de "Estado actual" (el repo derivó desde `7ebf94b`).
- El dataset `comunas` no tiene la columna `nombre_comuna_clean` al cargarlo (indica
  que el build cambió el schema; no inventes la columna).
- El chequeo de colisiones del Step 4 revela `nombre_comuna_clean` duplicados **y** no
  está claro qué comportamiento es correcto — reporta el hallazgo y espera decisión en
  vez de elegir silenciosamente cuál gana.
- Te encuentras tentado a agregar lógica fuzzy / `rapidfuzz` / edit-distance para
  "mejorar los matches": **para**. Eso es explícitamente fuera de alcance y cambia la
  misión. Repórtalo como pregunta abierta en el ADR y no lo implementes.
- Cualquier verificación falla dos veces tras un intento razonable de arreglo.

## Maintenance notes

Para quien mantenga esto después:

- **Acople con la invariante #4**: `normalize_comuna_name` DEBE mantenerse idéntica a
  la cadena inline de `subdere_extractor.py:560-570`. Hoy están duplicadas a propósito
  (evitar el gate de co-cambio en este plan). **Follow-up deferido**: refactorizar
  `subdere_extractor.py` para que importe `normalize_comuna_name` (aplicándolo con
  `pl.col(...).map_elements` o reconstruyendo la cadena Polars desde `_ACCENT_MAP`),
  tocando también `tests/test_extractors.py` por el gate de `check_companion_paths.py`.
  Eso cierra el riesgo de que las dos copias diverjan.
- **Qué escrutar en el PR**: que `codigo_comuna` salga como `pl.String` de 5 chars (no
  int, no truncado) — es la invariante que este dataset entero existe para proteger.
- **Follow-ups en el ADR-009**: modo fuzzy, `resolve_regiones()`, aceptar Series/DF de
  entrada. No los implementes aquí; que una futura sesión decida con las preguntas
  abiertas ya planteadas.
