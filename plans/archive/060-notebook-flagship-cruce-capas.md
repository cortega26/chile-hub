# Plan 060: Notebook flagship — cruce multi-capa por `codigo_comuna`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- examples/ data/dataset_catalog_config.json docs/datasets/perfil_territorial_comunal.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction / docs
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

El criterio de éxito #4 del product-spec es que un usuario pueda **"unirlo con
sus propios datos sin trabajo de limpieza"** — el valor central del hub son los
joins por `codigo_comuna`. Pero los 3 notebooks de `examples/notebooks/` son
mono-temáticos (`01_comunas_censo`, `02_indicadores`, `03_salud_educacion`):
ninguno demuestra el cruce de 4+ capas que es la tesis del producto. Un
notebook flagship que atraviese `perfil_territorial_comunal` × `pobreza_comunal`
× `resultados_educacionales` demuestra esa tesis de punta a punta y además es
el artefacto más citable/compartible (insumo directo para la dataset card del
plan 059 y para la landing).

## Current state

- `examples/notebooks/01_comunas_censo.ipynb` — **patrón a imitar** (verificado
  celda por celda): kernelspec `Python 3`, **3 celdas**, **outputs vacíos** (los
  notebooks se commitean sin ejecutar), ASCII-only en código y markdown:

  ```
  [0] markdown: # Comunas + Censo 2024 | Cruce territorial basico usando `codigo_comuna` como llave estable.
  [1] code: from chile_hub import ChileHub | hub = ChileHub() | comunas = hub.load_polars("comunas") | censo = hub.load_polars("censo_comunal")
  [2] code: ranking = (comunas.join(censo, on="codigo_comuna") .select("codigo_comuna", "nombre_comuna", "nombre_region", "poblacion_censada") .sort(...
  ```

- `docs/datasets/perfil_territorial_comunal.md` — tabla derivada con **una fila
  por comuna** que consolida DPA, Censo 2024, hogares/viviendas, salud,
  educación, distritos electorales, finanzas y SIEDU. Es la puerta de entrada
  natural del notebook (ya trae los joins DPA hechos).
- Claves de join disponibles (catálogo `data/dataset_catalog_config.json`):
  `pobreza_comunal` (join `codigo_comuna`), `resultados_educacionales`
  (comuna + año), `establecimientos_salud` (directorio por comuna),
  `censo_comunal` (comuna). `perfil_territorial_comunal` ya incluye conteos de
  establecimientos y métricas headline.
- La API pública estable: `hub.load_polars("<dataset>")` (ver
  `docs/installation.md`). Polars en español para nombres de columnas de salida.
- No hay ejecución de notebooks en CI — la verificación es local con
  `jupyter nbconvert --execute` (ver Step 3).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Build local | `make build` | exit 0 (artefactos frescos) |
| Ejecutar notebook | `./.venv/bin/python -m jupyter nbconvert --to notebook --execute --stdout examples/notebooks/04_perfil_territorial_pobreza.ipynb > /dev/null` ¹ | exit 0, sin `Traceback` |
| Lint (repo) | `make lint && make format-check` | exit 0 (no toca .py, sanity general) |

¹ Si `jupyter` no está en el venv: usar
`./.venv/bin/python -m ipykernel` no aplica — la vía simple es
`./.venv/bin/pip install --quiet jupyter nbconvert ipykernel` **en un venv
descartable** (`python3 -m venv /tmp/nbenv && /tmp/nbenv/bin/pip install jupyter chile-hub polars`)
para no ensuciar el venv del proyecto, o `uvx --from nbconvert jupyter-nbconvert`.
NO agregar jupyter a `pyproject.toml`.

## Scope

**In scope** (the only files you should modify/create):
- `examples/notebooks/04_perfil_territorial_pobreza.ipynb` (crear)
- `examples/demo_usage.py` o `examples/README`-style pointer **solo si existe
  ya un índice de ejemplos** — si no existe, no crearlo (ver STOP conditions).

**Out of scope** (do NOT touch, even though they look related):
- Los notebooks 01–03 existentes.
- `src/`, `data/`, `docs/datasets/*` (los schemas se citan, no se modifican).
- `pyproject.toml` (sin dependencias nuevas).
- Cualquier salida tipo PNG/HTML exportada del notebook — no se commitean
  artefactos generados por el análisis.

## Git workflow

- Branch: `advisor/060-flagship-notebook`
- Commit: `docs(examples): notebook flagship cruce perfil territorial x pobreza x educacion`
- No pushear ni abrir PR salvo instrucción del operador.

## Steps

### Step 1: Diseñar el análisis (papel primero)

Narrativa en 6–10 celdas, español, ASCII-only (sin tildes en el notebook, igual
que 01):

1. **Markdown**: título `# Perfil territorial x pobreza x educacion` + una
   línea: "Cruce multi-capa por `codigo_comuna`: la tesis de chile-hub en un
   solo notebook."
2. **Code**: imports + cargar `perfil_territorial_comunal`, `pobreza_comunal`,
   `resultados_educacionales` vía `hub.load_polars`. Mostrar `.shape` de cada
   uno en un comentario impreso.
3. **Markdown**: qué columna de cada capa se usa y por qué
   (`codigo_comuna` como llave estable de 5 chars — citar que es string con
   cero inicial, invariante del hub).
4. **Code**: join perfil × pobreza por `codigo_comuna`; seleccionar
   `codigo_comuna, nombre_comuna, nombre_region, poblacion_censada`,
   la tasa de pobreza por ingresos y las métricas de salud/educación headline
   del perfil. **Antes de escribir el select definitivo, inspeccionar las
   columnas reales** (`df.columns` en una ejecución interactiva o
   `./.venv/bin/python -c "from src.chile_hub import ChileHub; print(ChileHub().load_polars('pobreza_comunal').columns)"`)
   y usar solo columnas que existen.
5. **Code**: agregar `resultados_educacionales` (filtrar al año más reciente
   disponible con `filter(pl.col("anio") == pl.col("anio").max())` — verificar
   el nombre real de la columna de año primero).
6. **Code**: ranking top 20 comunas por pobreza con sus métricas, ordenado;
   una correlación simple (`.corr()` de polars o Pearson vía
   `select(pl.corr(...))`) entre pobreza y una métrica educacional.
7. **Markdown**: 3–5 bullets de lectura de resultados + sección "Como
   extender": reemplazar `pobreza_comunal` por `delincuencia_comunal`
   (candidate), cruzar con `consumo_electrico_comunal`, o usar
   `nombre_comuna_clean` para unir datos propios.
8. **Markdown final**: links a `docs/datasets/perfil_territorial_comunal.md`,
   `docs/datasets/pobreza_comunal.md` y README.

**Verify**: el diseño lista las columnas reales verificadas contra el build
local (no columnas supuestas).

### Step 2: Escribir el notebook

Crea el `.ipynb` (JSON válido, `nbformat: 4`, kernelspec `Python 3` igual que
01). Ejecuta las celdas localmente para confirmar que corren, y **luego limpia
los outputs** (convención del repo: outputs vacíos — verificado en 01:
`outputs per cell: [0, 0, 0]`). Limpiar con
`jupyter nbconvert --clear-output --inplace` o editando el JSON.

**Verify**: `python3 -c "import json; nb=json.load(open('examples/notebooks/04_perfil_territorial_pobreza.ipynb')); assert all(len(c.get('outputs',[]))==0 for c in nb['cells']); assert nb['metadata']['kernelspec']['display_name']=='Python 3'; print('formato ok', len(nb['cells']), 'celdas')"` → `formato ok … celdas`

### Step 3: Ejecutar de punta a punta (verificación funcional)

Con `make build` ya corrido (artefactos frescos en `data/normalized/`):

```bash
./.venv/bin/python -m jupyter nbconvert --to notebook --execute --stdout \
  examples/notebooks/04_perfil_territorial_pobreza.ipynb > /dev/null
```

(o la variante con venv descartable de la tabla de comandos).

**Verify**: exit 0 y sin `Traceback` en stderr. Tras la ejecución, limpiar
outputs de nuevo (Step 2 verify) porque nbconvert --execute los escribe si se
hace `--inplace` — usando `--stdout > /dev/null` no se modifica el archivo.

### Step 4: Enlazar desde el índice de ejemplos (solo si existe)

Si existe un índice/README de `examples/` que liste los notebooks, agrega la
entrada 04 con una línea descriptiva. Si NO existe, no lo crees (STOP: ver
condiciones — el repo puede preferir descubrimiento por nombre de archivo).

**Verify**: `ls examples/` y decidir; si hubo edición, `git diff --stat` muestra
solo ese archivo + el notebook.

## Test plan

- Sin tests unitarios nuevos (los notebooks no están bajo pytest — convención
  verificada: ningún test referencia `examples/`).
- Verificación funcional = Step 3 (nbconvert ejecuta limpio).
- Verificación de formato = Step 2 (JSON válido, outputs vacíos, kernelspec).
- `./.venv/bin/pytest -v` → suite completa sigue pasando (no debiera tocarse
  nada que la afecte; es un chequeo de no-regresión barato).

## Done criteria

- [ ] `examples/notebooks/04_perfil_territorial_pobreza.ipynb` existe, JSON válido, 6–10 celdas, outputs vacíos
- [ ] `jupyter nbconvert --execute` corre exit 0 contra el build local
- [ ] El notebook cruza ≥3 capas por `codigo_comuna` y solo usa columnas verificadas
- [ ] `python3 -c` del Step 2 imprime `formato ok`
- [ ] `./.venv/bin/pytest` exit 0 (no-regresión)
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) si:

- Las columnas reales de `pobreza_comunal` / `resultados_educacionales` /
  `perfil_territorial_comunal` no permiten la narrativa diseñada (p. ej.
  pobreza sin tasa por ingresos a nivel comunal, o educacionales sin
  `codigo_comuna`) — rediseñar el análisis es una decisión editorial, no del
  executor.
- `examples/` tiene un índice cuyo formato no es obvio para agregar la entrada
  04 (no improvisar un formato nuevo).
- La ejecución requiere datos que el build local no produce (p. ej. una capa
  candidate que el paquete instalado no descarga) — el notebook flagship debe
  correr solo con el bundle público.
- Los notebooks existentes cambiaron de convención (outputs commiteados,
  tildes, otro kernelspec) — reconciliar antes de escribir.
- Un step falla dos veces tras un intento razonable de fix.

## Maintenance notes

- **Drift de datos**: el notebook lee del bundle/cache en runtime, no de
  valores hardcodeados — los rankings cambiarán con cada refresh y eso es
  correcto. Lo que NO debe cambiar son los nombres de columnas; si un schema
  evoluciona, este notebook es el canario visible (follow-up barato si se
  quiere: un test que valide que las columnas usadas existen en los contratos
  `contracts/datasets/*.schema.json` — fuera de scope aquí).
- Reutilización: este notebook es el contenido candidato para la dataset card
  HF (plan 059) y para un futuro embed en la landing — mantenerlo legible como
  narrativa, no como volcado de tablas.
- En review, escrutar: que los filtros de año usen el máximo disponible (no un
  año hardcodeado), y que el texto explique la cobertura parcial donde aplique
  (SIEDU/educacionales no cubren las 346 comunas — ver `docs/datasets/`).
