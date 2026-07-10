# Plan 042: Ampliar cobertura de alcaldes al 100% vía BCN SIIT

> **Executor instructions**: Sigue este plan paso a paso. Ejecuta cada comando de
> verificación y confirma el resultado esperado antes de pasar al siguiente paso.
> Si ocurre algo de la sección "STOP conditions", detente y reporta — no improvises.
> Al terminar, actualiza la fila de estado de este plan en `plans/README.md`.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat ce23ee5..HEAD -- src/extractors/autoridades_locales_extractor.py tests/test_extractors.py contracts/datasets/autoridades_locales.schema.json docs/datasets/autoridades_locales.md data/staging/comunas.csv`
> Si algún archivo en alcance cambió desde que se escribió este plan, compara los
> extractos de "Current state" con el código vivo antes de continuar; ante una
> discrepancia, trátalo como STOP condition.

## Status

- **Priority**: P2
- **Effort**: S-M
- **Risk**: LOW
- **Depends on**: Plan 023 (`autoridades_locales` ya existe como `candidate`; `comunas.csv` en staging)
- **Category**: data / catálogo (Track B)
- **Planned at**: commit `ce23ee5`, 2026-07-10

## Why this matters

El dataset `autoridades_locales` (Plan 023) tiene hoy **165/345** alcaldes identificados
(47.8%). La fuente actual es Wikipedia ("Anexo:Alcaldes de X"), que sufre de dos
problemas: 121 comunas no tienen página (enlaces rojos) y la licencia es **CC-BY-SA**
(share-alike), lo que fuerza segregar este dataset del bundle principal CC-BY.

La **Biblioteca del Congreso Nacional (BCN)** publica el Sistema Integrado de Información
Territorial (SIIT) con un reporte por comuna que incluye el nombre del alcalde en una
tabla HTML limpia. Una verificación con 23 comunas diversas — desde Arica hasta
Antártica, desde Santiago hasta Juan Fernández — dio **23/23 (100%)** de éxito.

Usar BCN SIIT como fuente primaria de alcaldes:
- Eleva la cobertura de **165 → 345 (100%)**
- Resuelve el problema de licencia: datos gubernamentales chilenos, sin share-alike
- Abre el camino para promover `autoridades_locales` (o los alcaldes individualmente)
  de `candidate` a `stable_publishable`
- La extracción son 345 requests HTTP (uno por comuna), ~30-60s con paralelismo (5-10
  workers). Como los alcaldes cambian cada 4 años, esta carga es aceptable.

## Current state

### Archivo principal a modificar

`src/extractors/autoridades_locales_extractor.py` (538 líneas).

El flujo actual de alcaldes:

1. `fetch_alcalde_titles()` (línea 225): obtiene ~345 títulos "Anexo:Alcaldes de X"
   desde la página índice de Wikipedia (1 request a MediaWiki API).
2. `fetch_alcaldes_wikitext(titles)` (línea 247): descarga wikitext en lotes de 50
   (API `action=query`). Las páginas que no existen (`"missing": true`) se ignoran.
3. `fetch_alcaldes()` (línea 273): itera sobre el wikitext obtenido y extrae con
   `_extract_alcalde_actual()` (que busca `titular=` en `{{Ficha de cargo}}` o fallback
   de tabla histórica). Retorna `{comuna, nombre, periodo_inicio}`.
4. `_normalize_alcaldes()` (línea 389): cruza con `comunas.csv` para poblar
   `codigo_comuna`/`codigo_region`, y construye las filas del DataFrame.

**Problema**: solo las ~224 comunas con página "Anexo:Alcaldes de X" generan filas;
las 121 restantes simplemente no aparecen. Y de esas 224, solo ~165 tienen alcalde
identificable.

### BCN SIIT — formato del HTML

URL: `https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno=2024&idcom={codigo_comuna}`

El HTML contiene una tabla `<table class="table table-striped table-bordered table-sm mb-4">`:

```html
<tr>
  <td class="text-right font-weight-bold">Alcalde</td>
  <td>Olavarría Baeza Lorena Catalina</td>
</tr>
<tr>
  <td class="text-right font-weight-bold">Nº de concejales</td>
  <td>8</td>
</tr>
<tr>
  <td class="text-right font-weight-bold">Pertenece a</td>
  <td>Región Metropolitana de Santiago<br>
  Provincia de Melipilla<br>
  Distrito 14 - 7° Circunscripción</td>
</tr>
```

La fila "Pertenece a" contiene **distrito electoral** y **circunscripción senatorial**
(ya disponibles en `distritos_electorales`, pero es una verificación adicional).

Patrón de extracción (regex):
```python
re.search(
    r'<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>',
    html, re.I
)
```

### El lookup de comunas ya existe

`_load_comunas_lookup()` (línea 372) lee `data/staging/comunas.csv` y construye un
diccionario `nombre_comuna_clean → (codigo_comuna, codigo_region)`. Contiene las 346
comunas (345 + 1 para Chile/nacional). Es la clave para iterar sobre BCN SIIT.

### Convenciones del repo

- **Idioma**: español neutral, sin voseo.
- **HTTP**: `requests` + `tenacity` vía `fetch_with_retry()` en `src/extractors/http_utils.py`.
- **Paralelismo**: no hay patrón establecido en extractores (todos son secuenciales).
  Usar `concurrent.futures.ThreadPoolExecutor` con 5-8 workers, que es conservador para
  un servidor público como BCN.
- **Extractores**: `BaseExtractor` ABC. Los nuevos helpers se añaden como funciones
  standalone en el mismo módulo, no como métodos de la clase.
- **Tests**: `unittest` en `tests/test_extractors.py`. Sin HTTP mocking para integración;
  los tests unitarios usan fixtures de HTML/wikitext.

## Commands you will need

| Propósito | Comando | Esperado |
|-----------|---------|----------|
| Ejecutar extractor standalone | `PYTHONPATH=src .venv/bin/python src/extractors/autoridades_locales_extractor.py` | exit 0; ~360 filas (16 gob + ~345 alc) |
| Solo tests del extractor | `.venv/bin/python -m pytest tests/test_extractors.py -k "AutoridadesLocales" -v` | todos pass |
| Suite completa | `make test` | exit 0; sin regresiones |
| Lint + formato | `make lint && make format-check` | exit 0 |

## Scope

**In scope** (archivos a modificar):
- `src/extractors/autoridades_locales_extractor.py` — añadir `fetch_alcaldes_bcn()` y
  modificar `fetch_alcaldes()` para usarla como fuente primaria
- `tests/test_extractors.py` — nuevos tests para BCN SIIT
- `docs/datasets/autoridades_locales.md` — actualizar fuente, cobertura y licencia
- `contracts/datasets/autoridades_locales.schema.json` — ajustar `expected_record_count`

**Out of scope** (NO tocar):
- `src/extractors/autoridades_electas_extractor.py` — no relacionado
- `src/extractors/partidos_politicos_extractor.py` — no relacionado
- Gobernadores regionales — siguen con Wikipedia/Scrapling (16/16, sin cambio)
- Promoción a `stable_publishable` — decisión del operador tras verificar los datos
- `Makefile`, `data/source_registry.json`, `src/builders/` — el cableado del dataset
  ya existe; este plan solo mejora el extractor
- SERVEL / TRICEL / otras fuentes — esta ola solo usa BCN SIIT + Wikipedia residual

## Git workflow

- Branch: `advisor/042-bcn-siit-alcaldes`
- Commits estilo conventional commits, ej.
  `feat(data): reemplaza fuente de alcaldes con BCN SIIT (100% cobertura, 345/345)`
- No hagas push ni abras PR salvo indicación del operador.

## Steps

### Step 1: Añadir `fetch_alcaldes_bcn()` — extracción desde BCN SIIT

En `src/extractors/autoridades_locales_extractor.py`, añade las siguientes funciones
nuevas **después** de `_load_comunas_lookup()` (línea 386) y **antes** de
`_normalize_alcaldes()` (línea 389):

#### 1a: Constante de URL base (añadir cerca de las demás constantes, ~línea 60)

```python
BCN_SIIT_URL = "https://www.bcn.cl/siit/reportescomunales/comunas_v.html"
BCN_SIIT_ANNO = "2024"
```

#### 1b: Función `fetch_alcalde_bcn(codigo_comuna: str) -> str | None`

```python
def fetch_alcalde_bcn(codigo_comuna: str) -> str | None:
    """Obtiene el nombre del alcalde para una comuna desde BCN SIIT.

    Args:
        codigo_comuna: Código único territorial (CUT) de 5 dígitos.

    Returns:
        Nombre del alcalde en formato "Apellido1 Apellido2 Nombres", o None
        si la página no contiene el campo o hay error de red.
    """
    params = {"anno": BCN_SIIT_ANNO, "idcom": codigo_comuna}
    try:
        resp = fetch_with_retry(BCN_SIIT_URL, params=params, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Advertencia: BCN SIIT inaccesible para comuna {codigo_comuna} ({exc}).")
        return None

    match = re.search(
        r'<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>',
        resp.text, re.I,
    )
    if not match:
        return None
    nombre = match.group(1).strip()
    # Limpiar entidades HTML y espacios múltiples
    nombre = nombre.replace("&nbsp;", " ").replace("\xa0", " ")
    nombre = re.sub(r"\s+", " ", nombre).strip()
    if not nombre or nombre.lower() in ("", "vacante", "no disponible"):
        return None
    return nombre
```

#### 1c: Función `fetch_alcaldes_bcn(comunas_lookup: dict) -> list[dict]`

Usa `ThreadPoolExecutor` para paralelizar las 345 requests.

```python
import concurrent.futures

def fetch_alcaldes_bcn(
    comunas_lookup: dict[str, tuple[str, str]],
    max_workers: int = 6,
) -> list[dict[str, str | None]]:
    """Obtiene alcaldes desde BCN SIIT para todas las comunas del lookup.

    Args:
        comunas_lookup: ``{nombre_comuna_clean: (codigo_comuna, codigo_region)}``
        max_workers: Número máximo de requests concurrentes.

    Returns:
        Lista de ``{comuna, nombre, periodo_inicio}`` con todas las comunas
        para las que BCN SIIT devolvió un nombre. Las comunas sin alcalde
        identificable se incluyen con ``nombre=None``.
    """
    # Construir lista de (comuna_nombre, codigo_comuna) únicos
    # (comunas_lookup tiene 346 entradas; filtrar solo las 345 comunas reales)
    tareas: list[tuple[str, str, str]] = []
    for nombre_comuna, (codigo, region) in comunas_lookup.items():
        # Excluir entradas que no son comunas reales (ej. "chile")
        if codigo and len(codigo) == 5 and codigo != "00000":
            tareas.append((nombre_comuna, codigo, region))

    resultado: dict[str, str | None] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_a_codigo = {
            executor.submit(fetch_alcalde_bcn, codigo): (nombre, codigo, region)
            for nombre, codigo, region in tareas
        }
        for future in concurrent.futures.as_completed(future_a_codigo):
            nombre_comuna, codigo, region = future_a_codigo[future]
            try:
                alcalde = future.result()
            except Exception as exc:
                print(f"Advertencia: error obteniendo alcalde de {nombre_comuna} ({codigo}): {exc}")
                alcalde = None
            resultado[nombre_comuna] = alcalde

    return [
        {"comuna": comuna, "nombre": nombre, "periodo_inicio": None}
        for comuna, nombre in resultado.items()
    ]
```

#### 1d: Import de `concurrent.futures` (al inicio del archivo)

Añade después de `import datetime` (~línea 27):

```python
import concurrent.futures
```

**Verify**: El archivo es Python válido:
`.venv/bin/python -c "from src.extractors.autoridades_locales_extractor import fetch_alcalde_bcn, fetch_alcaldes_bcn; print('OK')"` → exit 0.

### Step 2: Integrar BCN SIIT como fuente primaria en `fetch_alcaldes()`

Modifica `fetch_alcaldes()` (línea 273) para usar BCN SIIT como fuente primaria y
Wikipedia como enriquecimiento opcional de partido/coalición.

#### 2a: Modificar `fetch_alcaldes()`

Reemplaza la función actual (líneas 273–292) con:

```python
def fetch_alcaldes() -> list[dict[str, str | None]]:
    """Lista de ``{comuna, nombre, periodo_inicio, partido}`` para las 345 comunas.

    Estrategia en dos niveles:
    1. **BCN SIIT (primaria)**: nombre del alcalde para las 345 comunas desde
       la Biblioteca del Congreso Nacional — fuente oficial, cobertura 100%.
    2. **Wikipedia (enriquecimiento)**: partido/coalición desde "Anexo:Alcaldes
       de X" donde exista (~224 comunas). Solo enriquece, no reemplaza.

    Si BCN SIIT falla por completo, degrada a solo-Wikipedia (comportamiento
    previo). Si ambas fallan, retorna ``[]``."""
    comunas = _load_comunas_lookup()
    if not comunas:
        print("Advertencia: comunas.csv no disponible. Sin lookup de códigos territoriales.")
        return []

    # --- Nivel 1: BCN SIIT (primaria, 345 comunas) ---
    filas_bcn: dict[str, dict[str, str | None]] = {}
    try:
        todas_bcn = fetch_alcaldes_bcn(comunas)
        for fila in todas_bcn:
            comuna = fila["comuna"]
            filas_bcn[comuna] = {
                "comuna": comuna,
                "nombre": fila["nombre"],
                "periodo_inicio": None,
                "partido_raw": None,
            }
        print(
            f"BCN SIIT: {sum(1 for f in filas_bcn.values() if f['nombre'])}/"
            f"{len(filas_bcn)} alcaldes con nombre."
        )
    except Exception as exc:  # noqa: BLE001 — degradación a Wikipedia sola
        print(f"Advertencia: BCN SIIT falló por completo ({exc}). Degradando a Wikipedia.")
        filas_bcn = {}

    # --- Nivel 2: Wikipedia (enriquecimiento de partido) ---
    wikidata: dict[str, dict[str, str | None]] = {}
    try:
        titles = fetch_alcalde_titles()
        wikitext_por_titulo = fetch_alcaldes_wikitext(titles) if titles else {}
        for title, wikitext in wikitext_por_titulo.items():
            comuna = _comuna_name_from_title(title)
            nombre_wp, inicio = _extract_alcalde_actual(wikitext)
            wikidata[comuna] = {
                "comuna": comuna,
                "nombre_wikipedia": nombre_wp,
                "periodo_inicio": inicio,
                # Extraer partido del infobox (valor bruto, se limpia abajo)
                "partido_raw": _extract_partido_from_infobox(wikitext),
            }
    except Exception as exc:  # noqa: BLE001
        print(f"Advertencia: Wikipedia inaccesible ({exc}). Sin enriquecimiento de partido.")

    # --- Merge: BCN SIIT como base, Wikipedia como enriquecimiento ---
    filas: list[dict[str, str | None]] = []
    for comuna_bcn, datos_bcn in filas_bcn.items():
        wp = wikidata.get(comuna_bcn, {})
        nombre = datos_bcn["nombre"]  # BCN SIIT es la fuente autoritativa del nombre
        if not nombre:
            # Fallback: si BCN SIIT no tiene nombre, usar Wikipedia
            nombre = wp.get("nombre_wikipedia")
        filas.append({
            "comuna": comuna_bcn,
            "nombre": nombre,
            "periodo_inicio": wp.get("periodo_inicio"),
        })

    # Si BCN SIIT falló completamente, usar solo Wikipedia (modo degradado)
    if not filas_bcn:
        for title, wikitext in wikitext_por_titulo.items() if 'wikitext_por_titulo' in dir() else {}:
            nombre, inicio = _extract_alcalde_actual(wikitext)
            filas.append({
                "comuna": _comuna_name_from_title(title),
                "nombre": nombre,
                "periodo_inicio": inicio,
            })

    return filas
```

**Nota sobre `partido_raw`**: esta versión **no incluye** partido/coalición en el
dataset final. El enriquecimiento de partido desde Wikipedia requiere un plan separado
(extraer el partido del infobox de "Anexo:Alcaldes de X" y normalizarlo a un nombre
canónico). Se deja como follow-up explícito. Este plan se enfoca en **cobertura de
nombre**, que es el bloqueante para promover el dataset.

#### 2b: Limpiar `_extract_partido_from_infobox` (deferido)

La función se menciona como placeholder; no es necesario implementarla en esta ola.
Si el executor quiere intentarlo como bonus, el patrón es:

```python
def _extract_partido_from_infobox(wikitext: str) -> str | None:
    """Extrae el partido del valor de ``titular=`` en ``{{Ficha de cargo}}``.

    Ej: ``| titular = [[Nombre]] ([[Partido|Sigla]])`` → ``Partido``
    """
    match = _TITULAR_RE.search(wikitext)
    if not match:
        return None
    raw = match.group(1)
    # Buscar texto entre paréntesis al final
    paren_match = re.search(r"\(([^)]+(?:\[\[[^\]]+\]\][^)]*)?)\)\s*$", raw)
    if paren_match:
        partido_raw = paren_match.group(1)
        # Resolver wikilink
        partido_raw = _WIKILINK_RE.sub(
            lambda m: (m.group(2) or m.group(1)).strip(), partido_raw
        )
        return partido_raw.strip()
    return None
```

**Verify**: el extractor sigue funcionando:
`.venv/bin/python -c "from src.extractors.autoridades_locales_extractor import fetch_alcaldes; r = fetch_alcaldes(); print(f'{len(r)} filas'); assert len(r) >= 340"` → imprime ≥ 340 filas.

### Step 3: Actualizar `_normalize_alcaldes()` para tolerar 345 filas

La función `_normalize_alcaldes()` (línea 389) no necesita cambios estructurales —
ya itera sobre todas las filas de `alcaldes`. Pero el `url_fuente` debe reflejar
BCN SIIT en lugar de Wikipedia. Cambia la línea ~417:

```python
# Antes:
"fuente": "Wikipedia (CC-BY-SA)",
"url_fuente": f"https://es.wikipedia.org/wiki/Anexo:Alcaldes_de_{comuna.replace(' ', '_')}",
# Después:
"fuente": "BCN SIIT",
"url_fuente": f"https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno={BCN_SIIT_ANNO}&idcom={codigo_comuna or ''}",
```

**Verify**: `grep '"fuente": "BCN SIIT"' src/extractors/autoridades_locales_extractor.py` encuentra la línea.

### Step 4: Actualizar umbrales, metadata y mensajes

#### 4a: `MIN_ALCALDES_CON_TITULAR`

En la línea 105, cambia el umbral para reflejar la nueva fuente:

```python
# Antes:
MIN_ALCALDES_CON_TITULAR = 140
# Después:
MIN_ALCALDES_CON_TITULAR = 300
```

345 es el máximo teórico; 300 deja margen para comunas con vacancia temporal o
errores de red transitorios, sin disparar falsas alarmas.

#### 4b: Metadata en `process_autoridades_locales()`

En `process_autoridades_locales()` (línea 486), actualiza los mensajes de metadata
para reflejar BCN SIIT (~líneas 502–525):

```python
metadata = {
    "dataset": "autoridades_locales",
    "source_name": "BCN SIIT + Wikipedia (CC-BY-SA)",
    "source_url": BCN_SIIT_URL,
    "source_mode": "live",
    "source_detail": (
        "Alcaldes: BCN SIIT (reportescomunales, fuente oficial del Congreso, "
        "345 comunas). Gobernadores: Wikipedia 'Gobernador regional de Chile' "
        "(Scrapling, CC-BY-SA)."
    ),
    # ... resto igual
    "notes": [
        f"gobernador_regional: {n_gob}/16 (Wikipedia, CC-BY-SA).",
        f"alcalde: {n_comunas} comunas procesadas desde BCN SIIT, {n_con_titular} "
        "con alcalde identificado (fuente oficial del Congreso Nacional).",
        "BCN SIIT es dato público gubernamental chileno; sin restricción de "
        "licencia para datos factuales de autoridades.",
    ],
    # ...
}
```

#### 4c: Mensaje de advertencia

En `process_autoridades_locales()`, actualiza la advertencia (~línea 500):

```python
if n_comunas and n_con_titular < MIN_ALCALDES_CON_TITULAR:
    print(
        f"Advertencia: solo {n_con_titular}/{n_comunas} comunas con alcalde identificado "
        f"(mínimo esperado {MIN_ALCALDES_CON_TITULAR}). Revisar BCN SIIT."
    )
```

**Verify**: `grep "MIN_ALCALDES_CON_TITULAR = 300" src/extractors/autoridades_locales_extractor.py` y
`grep "BCN SIIT" src/extractors/autoridades_locales_extractor.py` encuentran las líneas.

### Step 5: Añadir tests

En `tests/test_extractors.py`, dentro de `AutoridadesLocalesExtractorTests`, añade
**después** de `test_sin_columnas_personales_alcaldes` (línea 1963):

```python
def test_fetch_alcalde_bcn_extrae_nombre(self):
    """Prueba unitaria con HTML real de BCN SIIT (Melipilla)."""
    f = autoridades_locales_extractor.fetch_alcalde_bcn
    # Esto requiere red; si no hay, es un test de integración, no unitario.
    # Para CI sin red, usar mock:
    try:
        nombre = f("13501")
    except Exception:
        self.skipTest("Sin acceso a BCN SIIT en este entorno")
    self.assertIsNotNone(nombre)
    self.assertIn("Olavarría", nombre)
    self.assertNotIn("&nbsp;", nombre)
    self.assertNotIn("<td>", nombre)

def test_fetch_alcalde_bcn_html_sintetico(self):
    """Prueba unitaria del parseo de HTML (sin HTTP)."""
    import re as _re_module
    # Simular el HTML de BCN SIIT
    html = (
        '<table class="table table-striped">'
        "<tr><td>Superficie</td><td>1345.0 km2</td></tr>"
        "<tr><td>Alcalde</td><td>Apellido1 Apellido2 Nombres</td></tr>"
        "<tr><td>Nº de concejales</td><td>8</td></tr>"
        "</table>"
    )
    match = _re_module.search(
        r'<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>',
        html, re.I,
    )
    self.assertIsNotNone(match)
    nombre = match.group(1).strip()
    self.assertEqual(nombre, "Apellido1 Apellido2 Nombres")

def test_fetch_alcalde_bcn_html_sin_alcalde(self):
    """HTML sin campo Alcalde devuelve None."""
    import re as _re_module
    html = "<table><tr><td>Superficie</td><td>1345.0 km2</td></tr></table>"
    match = _re_module.search(
        r'<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>',
        html, re.I,
    )
    self.assertIsNone(match)

def test_fetch_alcalde_bcn_limpia_nbsp(self):
    """Los &nbsp; en el nombre se limpian a espacios normales."""
    import re as _re_module
    html = "<td>Alcalde</td><td>Nombre&nbsp;Con&nbsp;Espacios</td>"
    match = _re_module.search(
        r'<td[^>]*>\s*Alcalde\s*</td>\s*<td[^>]*>\s*(.+?)\s*</td>',
        html, re.I,
    )
    nombre = match.group(1).strip()
    nombre = nombre.replace("&nbsp;", " ").replace("\xa0", " ")
    nombre = _re_module.sub(r"\s+", " ", nombre).strip()
    self.assertEqual(nombre, "Nombre Con Espacios")

def test_fetch_alcaldes_bcn_cobertura_total(self):
    """BCN SIIT debe cubrir al menos 340 de las 345 comunas."""
    lookup = autoridades_locales_extractor._load_comunas_lookup()
    if not lookup:
        self.skipTest("comunas.csv no disponible")
    try:
        filas = autoridades_locales_extractor.fetch_alcaldes_bcn(lookup, max_workers=5)
    except Exception:
        self.skipTest("Sin acceso a BCN SIIT en este entorno")
    self.assertGreaterEqual(len(filas), 340)
    con_nombre = sum(1 for f in filas if f["nombre"])
    self.assertGreaterEqual(con_nombre, 300, f"Solo {con_nombre} alcaldes con nombre")

def test_normalize_alcaldes_fuente_bcn(self):
    """Las filas de alcalde usan BCN SIIT como fuente (no Wikipedia)."""
    alcaldes = [{"comuna": "Melipilla", "nombre": "Olavarría Baeza Lorena Catalina", "periodo_inicio": None}]
    lookup = {"melipilla": ("13501", "13")}
    df = autoridades_locales_extractor.build_autoridades_locales_df([], alcaldes, lookup)
    row = df.filter(pl.col("cargo") == "alcalde").row(0, named=True)
    self.assertEqual(row["fuente"], "BCN SIIT")
    self.assertIn("idcom=13501", row["url_fuente"])
```

**Nota**: los tests `test_fetch_alcalde_bcn_extrae_nombre` y
`test_fetch_alcaldes_bcn_cobertura_total` requieren acceso a internet. El executor
debe verificar que pasan en su entorno; en CI sin red, se saltan con `skipTest`.

**Verify**: `.venv/bin/python -m pytest tests/test_extractors.py -k "AutoridadesLocales" -v` → todos los tests pasan (13 existentes + 6 nuevos = 19).

### Step 6: Actualizar esquema y documentación

#### 6a: Contrato

En `contracts/datasets/autoridades_locales.schema.json`, actualiza:

```json
"expected_record_count": 361,
```

(16 gobernadores + 345 alcaldes = 361; tolera ligeras variaciones por vacancias.)

#### 6b: Ficha

Reescribe las secciones relevantes de `docs/datasets/autoridades_locales.md`:

1. **Descripción**: cambia la cobertura documentada de "224 comunas con página en
   Wikipedia" a "345 comunas (cobertura nacional completa)".

2. **Fuente y método**: reemplaza la sección de alcaldes con:
   ```markdown
   - **Alcaldes (345 comunas):** [BCN SIIT](https://www.bcn.cl/siit/reportescomunales/comunas_v.html?anno=2024)
     (Sistema Integrado de Información Territorial de la Biblioteca del Congreso
     Nacional). Una request HTTP por comuna (`idcom={codigo_comuna}`), parseo HTML
     de la tabla de datos comunales. Fuente oficial del Congreso chileno; datos
     factuales de autoridades públicas, sin restricción de licencia.
   ```

3. **Licencia**: la sección actual dice "CC-BY-SA 4.0 (share-alike)". Actualiza:
   ```markdown
   > **Licencia de los datos de alcaldes:** datos factuales de autoridades públicas
   > obtenidos de BCN SIIT (fuente gubernamental chilena). Sin restricción conocida
   > de copyright para datos factuales de cargos públicos.
   > **Licencia de gobernadores regionales:** CC-BY-SA 4.0 (Wikipedia). Los 16
   > registros de gobernador mantienen atribución share-alike.
   ```

4. **Limitaciones**: actualiza "121 comunas no tienen página propia" →
   "Cobertura nacional completa (345 comunas). Puede haber brechas puntuales por
   vacancia temporal del cargo."

**Verify**:
- `python -c "import json; c = json.load(open('contracts/datasets/autoridades_locales.schema.json')); assert c['expected_record_count'] == 361"`
- `grep "BCN SIIT" docs/datasets/autoridades_locales.md` encuentra la línea.

### Step 7: Verificación final

1. Ejecuta el extractor standalone:
   `PYTHONPATH=src .venv/bin/python src/extractors/autoridades_locales_extractor.py`
   → exit 0; el output debe mostrar ≥ 300 alcaldes con nombre y entre 350 y 365
   filas totales.

2. Suite completa:
   `make test` → exit 0; sin regresiones.

3. Lint y formato:
   `make lint && make format-check` → exit 0.

**Verify**: los tres comandos pasan.

## Test plan

- **`fetch_alcalde_bcn` con HTML sintético**: extrae nombre, maneja campo ausente,
  limpia `&nbsp;`, no inyecta tags HTML en el resultado.
- **`fetch_alcalde_bcn` con BCN real**: integración contra Melipilla (13501),
  verifica que el nombre contiene "Olavarría".
- **`fetch_alcaldes_bcn` cobertura**: con `comunas.csv` real, ≥ 340 filas y ≥ 300
  con nombre.
- **`_normalize_alcaldes` fuente**: verifica que `fuente = "BCN SIIT"` y la URL
  contiene `idcom=`.
- **Regresión**: los 13 tests existentes de `AutoridadesLocalesExtractorTests`
  siguen pasando.
- **Sin regresiones en la suite completa**: `make test` exit 0.

## Done criteria

- [ ] `fetch_alcalde_bcn()` y `fetch_alcaldes_bcn()` existen y son importables.
- [ ] `fetch_alcaldes()` usa BCN SIIT como fuente primaria; Wikipedia como fallback.
- [ ] `MIN_ALCALDES_CON_TITULAR = 300`.
- [ ] 6 tests nuevos en `AutoridadesLocalesExtractorTests`; todos pasan.
- [ ] `make test` exit 0; sin regresiones (549+ tests).
- [ ] `expected_record_count = 361` en el contrato.
- [ ] Ficha `docs/datasets/autoridades_locales.md` actualizada con BCN SIIT.
- [ ] `make lint && make format-check` exit 0.
- [ ] Ejecución real del extractor reporta ≥ 300 alcaldes con nombre, ~361 filas.
- [ ] `plans/README.md` actualizado (fila 042 → DONE).

## STOP conditions

Detente y reporta (no improvises) si:

- El código en `autoridades_locales_extractor.py` no coincide con los extractos de
  "Current state" (drift desde `ce23ee5`).
- BCN SIIT cambia su estructura HTML (el regex no matchea en ≥ 20% de las comunas).
- BCN SIIT bloquea las requests (HTTP 403/429 consistente). En ese caso, reducir
  `max_workers` a 2-3 y reintentar; si persiste, reportar.
- Menos de 300 comunas tienen alcalde identificable desde BCN SIIT (indicaría un
  cambio estructural en el sitio o un problema de red sistémico).
- `make test` muestra regresiones en tests no relacionados con este extractor.
- Aparece la tentación de tocar `autoridades_electas_extractor.py` o
  `partidos_politicos_extractor.py` — están fuera de alcance.

## Maintenance notes

- **Cadencia**: BCN SIIT se actualiza anualmente (parámetro `anno=`). Tras cada
  elección municipal (próxima: 2028), actualizar `BCN_SIIT_ANNO` al año
  correspondiente. El extractor tomará los nuevos alcaldes automáticamente.
- **Paralelismo**: `max_workers=6` es conservador. Si BCN SIIT empieza a rate-limitar,
  reducir a 2-3. Si el extractor es muy lento, subir a 8-10. Monitorear en CI.
- **Partido/coalición**: este plan difiere el enriquecimiento de partido desde
  Wikipedia. Un follow-up (Plan 043+) puede añadir `_extract_partido_from_infobox()`
  e integrarlo en el merge sin cambiar la fuente primaria.
- **Promoción**: con cobertura 345/345 desde fuente gubernamental, el dataset es
  candidato fuerte a `stable_publishable`. La decisión requiere revisión del operador
  y posible movimiento de los alcaldes a `autoridades_electas` (licencia limpia) o
  mantenerlos en `autoridades_locales` con nota de licencia mixta.
- **Plan 023**: este plan cierra el follow-up de cobertura de alcaldes. Si se completa
  con éxito, 023 puede archivarse.
