# Plan 006: Tests para la lógica de fallback de indicadores

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- src/extractors/bcentral_extractor.py tests/test_pipeline_logic.py`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: M
- **Riesgo**: MED
- **Depende de**: ninguno
- **Categoría**: tests
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

`bcentral_extractor.py` contiene la lógica de fallback y recovery más compleja del proyecto: cuando un fetch falla, el extractor intenta recuperarse desde snapshots raw locales, luego desde staging existente. Si `fetch_all_history()` retorna `None`, se activa `generate_fallback_indicators()`. Ninguna de estas ramas tiene tests. Si el fallback tiene un bug, se descubre solo cuando la API real falla en producción — que es exactamente cuando más se necesita que funcione.

## Estado actual

### `process_indicators()` en `src/extractors/bcentral_extractor.py:279-359`

```python
def process_indicators() -> str:
    ...
    df, diagnostics = fetch_all_history()  # retorna (DataFrame, dict) o (None, dict)

    if df is None:
        df = generate_fallback_indicators()
        source_mode = "fallback"
        source_detail = "generated_fallback"
        notes.append("fallback_due_to_live_fetch_failure")
        ...

    if source_mode == "live" and diagnostics.get("raw_recoveries"):
        source_detail = "public_api_with_raw_recovery"
        ...
    if source_mode == "live" and diagnostics.get("preserved_existing_pairs"):
        source_detail = "public_api_partial"
        ...
    if source_mode == "live" and diagnostics.get("published_backfills"):
        source_detail = "public_api_with_published_backfill"
        ...
    ...
    df.write_csv(STAGING_CSV_PATH)
    write_metadata(metadata)
    return STAGING_CSV_PATH
```

### `fetch_all_history()` en `bcentral_extractor.py:155-243`

```python
def fetch_all_history():
    """Retorna (DataFrame, diagnostics) o (None, diagnostics) si falla."""
    ...
    for codigo in INDICATOR_CODES:
        for year in years_to_fetch:
            try:
                records = fetch_indicator_year(codigo, year)
                ...
            except Exception as e:
                diagnostics["fetch_failures"].append(...)
                raw_records = load_latest_raw_snapshot(codigo, year)
                if raw_records:
                    ...  # raw_recovery
                    diagnostics["raw_recoveries"].append(...)
                elif existing_df is not None:
                    diagnostics["preserved_existing_pairs"].append(...)
    if not new_records:
        return None, diagnostics  # dispara fallback en process_indicators()
```

### Tests existentes en `test_pipeline_logic.py`

Los tests actuales importan `bcentral_extractor` (línea 15) pero solo lo referencian en contexto de staging, no mockean `fetch_all_history`. El patrón a seguir para mocking es `unittest.mock.patch`.

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Correr tests existentes | `.venv/bin/python -m unittest tests.test_pipeline_logic -v` | todos pasan |
| Correr nuevos tests | `.venv/bin/python -m unittest tests.test_pipeline_logic.IndicatorFallbackTests -v` | todos pasan |
| Verificar imports | `python3 -c "from src.extractors.bcentral_extractor import process_indicators, generate_fallback_indicators, INDICATOR_CODES; print('OK')"` | `OK` |

## Alcance

**En scope**:
- `tests/test_pipeline_logic.py` — agregar la clase `IndicatorFallbackTests`

**Fuera de scope**:
- `src/extractors/bcentral_extractor.py` — no modificar (solo testear)
- No agregar dependencias nuevas (usar `unittest.mock` de stdlib)

## Git workflow

- Rama: `advisor/006-tests-fallback-indicadores`
- Estilo de commit: `test: agregar tests para logica de fallback de indicadores`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar imports de mocking

Al inicio de `test_pipeline_logic.py`, después de los imports existentes:

```python
import tempfile
from unittest.mock import patch, MagicMock
import polars as pl
from src.extractors import bcentral_extractor
from src.extractors.bcentral_extractor import (
    process_indicators,
    generate_fallback_indicators,
    INDICATOR_CODES,
    EXPECTED_INDICATOR_CODES,
)
```

**Verificar**: `python3 -c "from src.extractors.bcentral_extractor import generate_fallback_indicators, INDICATOR_CODES; print('OK')"` imprime `OK`.

### Paso 2: Agregar la clase `IndicatorFallbackTests`

```python
class IndicatorFallbackTests(unittest.TestCase):
    """Tests para la lógica de fallback y recovery de bcentral_extractor.py."""

    def _make_minimal_df(self):
        """DataFrame mínimo válido con todos los indicadores requeridos."""
        import datetime
        records = []
        today = datetime.date.today()
        for code in sorted(EXPECTED_INDICATOR_CODES):
            records.append({"fecha": today, "codigo_indicador": code, "valor": 1.0})
        return pl.DataFrame(records).with_columns(
            pl.col("fecha").cast(pl.Date),
            pl.col("codigo_indicador").cast(pl.String),
            pl.col("valor").cast(pl.Float64),
        )

    def test_generate_fallback_returns_valid_dataframe(self):
        """generate_fallback_indicators() retorna un DataFrame no vacío con todos los códigos."""
        df = generate_fallback_indicators()
        self.assertGreater(df.height, 0)
        codes_in_df = set(df["codigo_indicador"].unique().to_list())
        self.assertTrue(EXPECTED_INDICATOR_CODES.issubset(codes_in_df),
            f"Faltan códigos en fallback: {EXPECTED_INDICATOR_CODES - codes_in_df}")
        self.assertIn("fecha", df.columns)
        self.assertIn("valor", df.columns)

    def test_process_indicators_uses_fallback_when_fetch_returns_none(self):
        """Cuando fetch_all_history() retorna (None, diagnostics), process_indicators()
        activa generate_fallback_indicators() y escribe metadata con source_mode=fallback."""
        diagnostics = {
            "fetch_failures": ["uf/2026: timeout"],
            "raw_recoveries": [],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": [],
        }
        fallback_df = self._make_minimal_df()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patchear paths de archivos de salida para no contaminar data/staging
            staging_path = str(Path(tmpdir) / "indicadores.csv")
            metadata_path = str(Path(tmpdir) / "indicadores.metadata.json")

            with patch("src.extractors.bcentral_extractor.fetch_all_history",
                       return_value=(None, diagnostics)), \
                 patch("src.extractors.bcentral_extractor.STAGING_CSV_PATH", staging_path), \
                 patch("src.extractors.bcentral_extractor.METADATA_PATH", metadata_path):
                result_path = process_indicators()

        # Verificar que se escribió el CSV
        self.assertTrue(Path(staging_path).exists())
        written_df = pl.read_csv(staging_path)
        self.assertGreater(written_df.height, 0)

        # Verificar que el metadata refleja fallback
        import json
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        self.assertEqual(metadata["source_mode"], "fallback")
        self.assertIn("fallback_due_to_live_fetch_failure", metadata.get("notes", []))

    def test_process_indicators_records_raw_recovery_in_metadata(self):
        """Cuando un fetch falla pero hay raw snapshot, source_detail incluye raw_recovery."""
        minimal_df = self._make_minimal_df()
        diagnostics = {
            "fetch_failures": ["uf/2026: timeout"],
            "raw_recoveries": ["uf/2026"],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            staging_path = str(Path(tmpdir) / "indicadores.csv")
            metadata_path = str(Path(tmpdir) / "indicadores.metadata.json")

            with patch("src.extractors.bcentral_extractor.fetch_all_history",
                       return_value=(minimal_df, diagnostics)), \
                 patch("src.extractors.bcentral_extractor.STAGING_CSV_PATH", staging_path), \
                 patch("src.extractors.bcentral_extractor.METADATA_PATH", metadata_path):
                process_indicators()

        import json
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        self.assertEqual(metadata["source_mode"], "live")
        self.assertIn("public_api_with_raw_recovery", metadata["source_detail"])
        self.assertEqual(metadata["raw_recoveries"], ["uf/2026"])

    def test_process_indicators_records_published_backfill_in_metadata(self):
        """Cuando hay published_backfills, source_detail es public_api_with_published_backfill."""
        minimal_df = self._make_minimal_df()
        diagnostics = {
            "fetch_failures": [],
            "raw_recoveries": [],
            "preserved_existing_pairs": [],
            "empty_live_pairs": [],
            "published_backfills": ["ipc"],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            staging_path = str(Path(tmpdir) / "indicadores.csv")
            metadata_path = str(Path(tmpdir) / "indicadores.metadata.json")

            with patch("src.extractors.bcentral_extractor.fetch_all_history",
                       return_value=(minimal_df, diagnostics)), \
                 patch("src.extractors.bcentral_extractor.STAGING_CSV_PATH", staging_path), \
                 patch("src.extractors.bcentral_extractor.METADATA_PATH", metadata_path):
                process_indicators()

        import json
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        self.assertIn("public_api_with_published_backfill", metadata["source_detail"])
        self.assertEqual(metadata["published_backfills"], ["ipc"])
```

**Verificar**: `.venv/bin/python -m unittest tests.test_pipeline_logic.IndicatorFallbackTests -v` — todos pasan.

### Paso 3: Correr la suite completa

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, sin regresiones en los tests existentes.

## Criterios de done

- [ ] `grep -n "class IndicatorFallbackTests" tests/test_pipeline_logic.py` retorna la clase
- [ ] `.venv/bin/python -m unittest tests.test_pipeline_logic.IndicatorFallbackTests -v` — todos pasan
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan
- [ ] Solo `tests/test_pipeline_logic.py` modificado
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si `STAGING_CSV_PATH` o `METADATA_PATH` no son variables de módulo accesibles para el patch (son calculadas dentro de funciones) — usar `patch.object` o un enfoque de tempdir diferente; reportar en lugar de improvisar.
- Si la firma de `process_indicators()` cambió (acepta argumentos) — reportar.
- Si `EXPECTED_INDICATOR_CODES` no es exportable del módulo — verificar el nombre real y ajustar el import.

## Notas de mantenimiento

- Si se agrega un nuevo modo de recovery (ej. `s3_backfill`), agregar un test para ese modo en esta clase.
- Los tests usan `patch` sobre variables de módulo — si se refactorizan las rutas a constantes de clase, los patches deben actualizarse.
