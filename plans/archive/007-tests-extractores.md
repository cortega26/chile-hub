# Plan 007: Tests para los extractores con HTTP mocking

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar. Este es el plan de mayor esfuerzo de la suite — leerlo completo antes de empezar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- src/extractors/subdere_extractor.py src/extractors/bcentral_extractor.py tests/`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P2
- **Esfuerzo**: L
- **Riesgo**: MED
- **Depende de**: 006 (infraestructura de mocking ya establecida)
- **Categoría**: tests
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

Los extractores son el código más volátil del proyecto: dependen de APIs externas (BCN ArcGIS, mindicador.cl), hacen parsing de formatos externos, y tienen lógica de fallback crítica. Actualmente tienen cobertura cero. Un cambio en el formato de respuesta de BCN o en el esquema de mindicador.cl rompería el pipeline silenciosamente si no hay tests que lo detecten. Este plan crea `tests/test_extractors.py` con mocking de HTTP para cubrir los happy paths, error paths y fallbacks de ambos extractores.

## Estado actual

### Archivos en scope

- `src/extractors/subdere_extractor.py` (418 líneas): hace un GET a BCN ArcGIS, parsea GeoJSON con features, normaliza a comunas CSV, enriquece con coords y población desde CSVs estáticos.
- `src/extractors/bcentral_extractor.py` (363 líneas): hace GETs a mindicador.cl para cada indicador/año, guarda snapshots raw, construye DataFrame de indicadores.

### Función central de subdere_extractor

```python
# src/extractors/subdere_extractor.py (aprox. línea 135-175)
def fetch_bcn_comunas():
    """Fetch de BCN ArcGIS → lista de dicts con campos de comunas."""
    url = BCN_ARCGIS_URL
    response = requests.get(url, timeout=30)  # o curl_cffi si está disponible
    response.raise_for_status()
    data = response.json()
    features = data.get("features", [])
    ...
    return records
```

### Función central de bcentral_extractor

```python
# src/extractors/bcentral_extractor.py:106-118
def fetch_indicator_year(codigo, year):
    url = f"{MINDICADOR_BASE}/{codigo}/{year}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    payload = response.json()
    save_raw_snapshot(payload, codigo, year)
    return parse_indicator_payload(payload, codigo)
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr nuevos tests | `.venv/bin/python -m unittest tests.test_extractors -v` | todos pasan |
| Correr suite completa | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan |
| Verificar imports | `python3 -c "from src.extractors import subdere_extractor, bcentral_extractor; print('OK')"` | `OK` |

## Alcance

**En scope**:
- `tests/test_extractors.py` — crear este archivo desde cero

**Fuera de scope**:
- `src/extractors/subdere_extractor.py` y `bcentral_extractor.py` — no modificar
- `tests/test_chile_hub.py` y `tests/test_pipeline_logic.py` — no modificar

## Git workflow

- Rama: `advisor/007-tests-extractores`
- Estilo de commit: `test: agregar tests de extractores con HTTP mocking`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Crear `tests/test_extractors.py`

Crear el archivo con el siguiente contenido base:

```python
"""
Tests para src/extractors/subdere_extractor.py y bcentral_extractor.py.

Estos tests usan unittest.mock para evitar llamadas HTTP reales.
Prerequisito: el código fuente no debe haber cambiado su estructura pública
desde el commit e3951f0. Correr el drift check antes de ejecutar.
"""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import polars as pl
```

**Verificar**: `python3 tests/test_extractors.py` no lanza ImportError.

### Paso 2: Construir fixture de BCN ArcGIS

Antes de escribir los tests de subdere, entender qué formato retorna BCN ArcGIS. Leer `src/extractors/subdere_extractor.py` en la función que parsea `features` para construir un fixture JSON mínimo válido. El fixture debe tener al menos 2 features con los campos esperados (ej. `CUT`, `REGION`, `PROVINCIA`, `NOMBRE`, `SHAPE_X`, `SHAPE_Y`).

```python
# Fixture mínimo para BCN ArcGIS (adaptar según campos reales del extractor)
BCN_FIXTURE = {
    "features": [
        {
            "attributes": {
                "CUT": "01101",
                "REGION": "01",
                "PROVINCIA": "011",
                "NOMBRE": "Iquique",
                "SHAPE_X": -70.1508,
                "SHAPE_Y": -20.2138,
            }
        },
        {
            "attributes": {
                "CUT": "01107",
                "REGION": "01",
                "PROVINCIA": "011",
                "NOMBRE": "Alto Hospicio",
                "SHAPE_X": -70.0995,
                "SHAPE_Y": -20.2649,
            }
        },
    ]
}
```

**STOP**: Si al leer `subdere_extractor.py` los nombres de campo son distintos a `CUT`, `REGION`, `PROVINCIA`, `NOMBRE`, `SHAPE_X`, `SHAPE_Y`, usar los nombres reales. No asumir — leer el código.

### Paso 3: Agregar tests para subdere_extractor

```python
class SubdereExtractorTests(unittest.TestCase):
    """Tests para src/extractors/subdere_extractor.py."""

    def _make_mock_response(self, payload, status_code=200):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = payload
        if status_code >= 400:
            from requests import HTTPError
            mock.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
        else:
            mock.raise_for_status.return_value = None
        return mock

    def test_fetch_bcn_comunas_returns_records_on_success(self):
        """Happy path: BCN retorna features válidos → lista de dicts."""
        from src.extractors.subdere_extractor import fetch_bcn_comunas
        mock_resp = self._make_mock_response(BCN_FIXTURE)
        with patch("requests.get", return_value=mock_resp):
            records = fetch_bcn_comunas()
        self.assertIsNotNone(records)
        self.assertGreater(len(records), 0)
        # Verificar campos CUT en el output
        first = records[0]
        self.assertIn("codigo_comuna", first)

    def test_fetch_bcn_comunas_returns_none_on_http_error(self):
        """Si BCN retorna 5xx, fetch_bcn_comunas debe retornar None o lanzar excepción manejada."""
        from src.extractors.subdere_extractor import fetch_bcn_comunas
        mock_resp = self._make_mock_response({}, status_code=503)
        with patch("requests.get", return_value=mock_resp):
            try:
                result = fetch_bcn_comunas()
                # Si no lanza excepción, debe retornar None (indicando fallo)
                self.assertIsNone(result)
            except Exception:
                pass  # Lanzar excepción también es aceptable

    def test_normalize_dpa_produces_required_columns(self):
        """normalize_dpa() produce un DataFrame con las columnas canónicas esperadas."""
        from src.extractors.subdere_extractor import normalize_dpa
        mock_resp = self._make_mock_response(BCN_FIXTURE)
        with patch("requests.get", return_value=mock_resp):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("src.extractors.subdere_extractor.STAGING_DIR", tmpdir), \
                     patch("src.extractors.subdere_extractor.RAW_DIR", tmpdir):
                    # Llamar normalize_dpa directamente si es función pública
                    # Si no es pública, testear a través de la función de entrada principal
                    pass
        # Verificar columnas requeridas en el CSV de salida
        required_cols = {
            "codigo_comuna", "nombre_comuna", "nombre_comuna_clean",
            "codigo_provincia", "nombre_provincia",
            "codigo_region", "nombre_region",
            "latitud_cabecera", "longitud_cabecera", "poblacion_estimada",
        }
        # (adaptar según lo que expose normalize_dpa)
        # Este test es un placeholder — el ejecutor debe leer normalize_dpa y adaptar
        pass


class BCentralExtractorTests(unittest.TestCase):
    """Tests para src/extractors/bcentral_extractor.py."""

    def _make_mindicador_response(self, codigo, year, n_records=5):
        """Fixture de respuesta de mindicador.cl."""
        import datetime
        series = []
        for i in range(n_records):
            d = datetime.date(year, 1, i + 1)
            series.append({"fecha": d.isoformat() + "T00:00:00.000Z", "valor": 39000.0 + i})
        return {"codigo": codigo, "serie": series}

    def test_fetch_indicator_year_returns_records_on_success(self):
        """Happy path: mindicador.cl retorna serie válida → lista de dicts."""
        from src.extractors.bcentral_extractor import fetch_indicator_year
        payload = self._make_mindicador_response("uf", 2026, n_records=3)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = payload

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.get", return_value=mock_resp), \
                 patch("src.extractors.bcentral_extractor.RAW_DIR", tmpdir):
                records = fetch_indicator_year("uf", 2026)

        self.assertIsNotNone(records)
        self.assertGreater(len(records), 0)
        first = records[0]
        self.assertIn("fecha", first)
        self.assertIn("codigo_indicador", first)
        self.assertIn("valor", first)
        self.assertEqual(first["codigo_indicador"], "uf")

    def test_fetch_indicator_year_raises_on_http_error(self):
        """Si mindicador.cl retorna error HTTP, fetch_indicator_year lanza excepción."""
        from src.extractors.bcentral_extractor import fetch_indicator_year
        from requests import HTTPError
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("503")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.get", return_value=mock_resp), \
                 patch("src.extractors.bcentral_extractor.RAW_DIR", tmpdir):
                with self.assertRaises(Exception):
                    fetch_indicator_year("uf", 2026)

    def test_fetch_all_history_handles_single_fetch_failure(self):
        """Si un código/año falla, otros deben seguir procesándose."""
        from src.extractors.bcentral_extractor import fetch_all_history, INDICATOR_CODES
        from requests import HTTPError

        call_count = {"n": 0}
        def mock_fetch(codigo, year):
            call_count["n"] += 1
            if codigo == "uf":
                raise HTTPError("503")
            return [{"fecha": "2026-01-01", "codigo_indicador": codigo, "valor": 1.0}]

        with patch("src.extractors.bcentral_extractor.fetch_indicator_year", side_effect=mock_fetch), \
             patch("src.extractors.bcentral_extractor.load_latest_raw_snapshot", return_value=[]), \
             patch("src.extractors.bcentral_extractor.load_existing_staging", return_value=(None, None, [])), \
             patch("src.extractors.bcentral_extractor.time.sleep"):
            df, diagnostics = fetch_all_history()

        # uf falló pero los demás indicadores deben haber producido datos
        self.assertIn("uf", [f.split("/")[0] for f in diagnostics["fetch_failures"]])
        if df is not None:
            codes_in_df = set(df["codigo_indicador"].unique().to_list())
            self.assertFalse("uf" in codes_in_df or df.height == 0,
                "Si uf falló y no hay recovery, el df puede tener otros códigos")
```

**Verificar**: `.venv/bin/python -m unittest tests.test_extractors.BCentralExtractorTests.test_fetch_indicator_year_returns_records_on_success -v` — pasa.

### Paso 4: Refinar y completar tests placeholder

El test `test_normalize_dpa_produces_required_columns` es un placeholder. El ejecutor debe:
1. Leer `src/extractors/subdere_extractor.py` para entender la función de entrada principal (`normalize_dpa` o equivalente)
2. Adaptar el test para que llame esa función con el fixture, mockeando las llamadas HTTP y los paths de salida
3. Verificar que el CSV de salida tiene las columnas canónicas (lista en el test)

### Paso 5: Correr la suite completa

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, incluyendo los nuevos tests en `test_extractors.py`.

## Criterios de done

- [ ] `tests/test_extractors.py` existe
- [ ] `grep -n "class SubdereExtractorTests\|class BCentralExtractorTests" tests/test_extractors.py` retorna ambas clases
- [ ] `.venv/bin/python -m unittest tests.test_extractors -v` — todos pasan (no solo skipean)
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] Solo `tests/test_extractors.py` creado; ningún archivo fuente modificado
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si los nombres de funciones públicas de los extractores difieren de `fetch_bcn_comunas`, `normalize_dpa`, `fetch_indicator_year`, `fetch_all_history` — leer el código real y adaptar; si la estructura es fundamentalmente diferente, reportar antes de continuar.
- Si el fixture BCN no coincide con el formato real (campos distintos) — leer el extractor, construir el fixture correcto.
- Si algún test requiere tocar `data/staging/` o `data/raw/` del repo real — usar `tempfile.TemporaryDirectory()` y patchear las rutas.

## Notas de mantenimiento

- Estos tests deben actualizarse si BCN o mindicador.cl cambian el formato de respuesta.
- El fixture `BCN_FIXTURE` debe estar sincronizado con el schema real que parsea el extractor.
- Si se agrega un nuevo extractor (ej. para datos educativos), agregar una clase `NuevoExtractorTests` en este mismo archivo.
