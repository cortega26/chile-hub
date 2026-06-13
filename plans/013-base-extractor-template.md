# Plan 013: Crear clase base `BaseExtractor` para uniformizar extractores

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**:
> `git diff --stat e3951f0..HEAD -- src/extractors/subdere_extractor.py src/extractors/bcentral_extractor.py`
> Si alguno cambió, compara los excerpts de "Estado actual" antes de continuar.

## Estado

- **Prioridad**: P3
- **Esfuerzo**: M
- **Riesgo**: MEDIUM
- **Depende de**: 012 (opcional, facilita ver el patrón de un tercer extractor)
- **Categoría**: direction
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

Los dos extractores actuales (`subdere_extractor.py` y `bcentral_extractor.py`) siguen el mismo ciclo de vida — fetch, normalize, validate, write_staging, write_metadata — pero lo implementan de forma ad-hoc y diferente: las firmas de funciones no coinciden, el manejo de fallback no es uniforme, y agregar un tercer extractor requiere leer y copiar patrones de ambos. Una clase base abstracta `BaseExtractor` hace explícito el contrato de cada extractor, facilita testearlo de forma aislada (implementando una clase de prueba mínima), y reduce el costo de incorporar nuevas fuentes de datos — que es parte de la visión a largo plazo del hub.

Este plan es de baja urgencia (no hay bug que corregir) y de riesgo MEDIUM porque refactoriza código funcional. El criterio de done más importante es que el comportamiento externo (outputs de staging y metadata) no cambia.

## Estado actual

### Contrato implícito de `subdere_extractor.py`

```python
# subdere_extractor.py:18-60 — funciones de nivel módulo
def fetch_comunas_data(use_curl_cffi=False) -> dict:
    """Llama a ArcGIS y retorna el JSON crudo."""
    ...

def normalize_comunas(raw_data: dict) -> pl.DataFrame:
    """Normaliza el JSON de BCN a un DataFrame Polars limpio."""
    ...

def validate_comunas(df: pl.DataFrame, metadata: dict) -> dict:
    """Valida el DataFrame y retorna un reporte de validación."""
    ...

def run_subdere_extraction(dry_run=False, use_fallback=False) -> dict:
    """Orquesta fetch + normalize + validate + write_staging."""
    ...
```

### Contrato implícito de `bcentral_extractor.py`

```python
# bcentral_extractor.py:40-105 — instancia de clase existente
class BCentralExtractor:
    def fetch_indicator_year(self, series_id, year): ...
    def fetch_all_history(self, series_id): ...
    def process_indicators(self, dry_run=False): ...
```

`bcentral_extractor.py` ya usa una clase, pero el nombre y la interfaz no coinciden con `subdere_extractor.py` que usa funciones sueltas. `BaseExtractor` da un contrato común a ambos.

### Patrón de fallback

Ambos extractores siguen la misma secuencia de fallback:
1. Fetch en vivo
2. Si falla → recuperar snapshot raw anterior
3. Si no hay snapshot → usar staging existente
4. Si no hay staging → synthetic fallback (datos mínimos hardcodeados)

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Tests existentes | `.venv/bin/python -m unittest discover -s tests -v` | todos pasan (antes y después) |
| Verificar import de BaseExtractor | `python3 -c "from src.extractors.base import BaseExtractor; print('OK')"` | `OK` |
| Verificar subclases | `python3 -c "from src.extractors.subdere_extractor import SubdereExtractor; e = SubdereExtractor(); print(e.dataset_name)"` | `comunas` |
| Build completo | `make build` | exit 0 |

## Alcance

**En scope**:
- `src/extractors/base.py` — crear (clase abstracta `BaseExtractor`)
- `src/extractors/subdere_extractor.py` — refactorizar `run_subdere_extraction` como subclase de `BaseExtractor`; mantener las funciones de nivel módulo como aliases o como funciones wrapper para backwards compatibility
- `src/extractors/bcentral_extractor.py` — refactorizar `BCentralExtractor` como subclase de `BaseExtractor`
- `tests/test_extractors.py` — agregar test de la clase base con una implementación mínima de prueba

**Fuera de scope**:
- `src/build_dev_db.py` — no modificar; consume los outputs de staging, no invoca los extractores directamente
- Lógica interna de fetch, normalize, validate — no cambiar
- Firmas de las funciones de nivel módulo en `subdere_extractor.py` — mantener para no romper llamadas existentes

## Git workflow

- Rama: `advisor/013-base-extractor-template`
- Estilo de commit: `refactor: agregar BaseExtractor como clase base abstracta de los extractores`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Crear `src/extractors/base.py`

```python
"""Clase base abstracta para extractores de Chile-hub."""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    """Contrato común para todos los extractores del hub.

    Ciclo de vida: fetch → normalize → validate → write_staging → write_metadata.
    Cada subclase implementa los métodos abstractos; run() orquesta el ciclo.
    """

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nombre del dataset (ej. 'comunas', 'indicadores'). Debe coincidir con DATASET_CATALOG_CONFIG."""

    @abstractmethod
    def fetch(self, **kwargs) -> object:
        """Obtiene los datos crudos de la fuente. Retorna el objeto crudo (dict, str, bytes, etc.)
        Debe manejar internamente la lógica de fallback a snapshot o staging."""

    @abstractmethod
    def normalize(self, raw_data: object) -> object:
        """Transforma los datos crudos a un DataFrame Polars normalizado."""

    @abstractmethod
    def validate(self, df: object, metadata: dict) -> dict:
        """Valida el DataFrame normalizado. Retorna un reporte de validación con al menos:
        {'valid': bool, 'record_count': int, 'issues': list[str]}"""

    @abstractmethod
    def write_staging(self, df: object, metadata: dict) -> Path:
        """Escribe el DataFrame a data/staging/<dataset_name>.csv y el metadata a
        data/staging/<dataset_name>.metadata.json. Retorna el path del CSV."""

    def run(self, dry_run: bool = False, **kwargs) -> dict:
        """Orquesta el ciclo completo: fetch → normalize → validate → write_staging.
        Retorna el reporte de validación.
        """
        raw = self.fetch(**kwargs)
        df = self.normalize(raw)
        metadata = {"dataset": self.dataset_name, "dry_run": dry_run}
        validation = self.validate(df, metadata)
        if not dry_run:
            self.write_staging(df, metadata)
        return validation
```

**Verificar**: `python3 -c "from src.extractors.base import BaseExtractor; print('OK')"` imprime `OK`.

### Paso 2: Agregar `__init__.py` en `src/extractors/` si no existe

```bash
ls src/extractors/__init__.py 2>/dev/null || touch src/extractors/__init__.py
```

**Verificar**: el directorio es importable como paquete Python.

### Paso 3: Refactorizar `BCentralExtractor` como subclase

Al inicio de `src/extractors/bcentral_extractor.py`, agregar:

```python
from src.extractors.base import BaseExtractor
```

Modificar la definición de la clase:

```python
# ANTES:
class BCentralExtractor:

# DESPUÉS:
class BCentralExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "indicadores"
```

Agregar los métodos abstractos `fetch`, `normalize`, `validate`, `write_staging` como wrappers de la lógica existente:

```python
def fetch(self, **kwargs) -> object:
    # La lógica de fetch ya existe como fetch_all_history + process_indicators
    # Este método es el punto de entrada del ciclo base
    return self.fetch_all_history(
        kwargs.get("series_id", None)
    )

def normalize(self, raw_data: object) -> object:
    # La normalización ya ocurre dentro de process_indicators
    # En el refactor, exponer como método separado
    raise NotImplementedError("normalize debe ser implementado como parte del refactor de process_indicators")

def validate(self, df: object, metadata: dict) -> dict:
    # Delegar a la función validate_indicadores existente
    from src.build_dev_db import validate_indicadores
    return validate_indicadores(df, metadata)

def write_staging(self, df: object, metadata: dict) -> Path:
    raise NotImplementedError("write_staging debe ser implementado como parte del refactor de process_indicators")
```

**NOTA IMPORTANTE para el ejecutor**: El refactor completo de `BCentralExtractor` requiere separar la lógica de `process_indicators()` en `fetch()`, `normalize()`, y `write_staging()`. Esto es un refactor de M complejidad. Si la separación no es limpia (la función hace fetch + normalize + write en un solo bloque sin separación clara), implementar solo `dataset_name` y dejar los otros métodos con `raise NotImplementedError` con un comentario de que el refactor pendiente es `TECH-DEBT: separar process_indicators en métodos discretos`. El objetivo de este plan es establecer el contrato, no completar el refactor completo si las funciones internas están demasiado acopladas.

**Verificar**: `python3 -c "from src.extractors.bcentral_extractor import BCentralExtractor; e = BCentralExtractor(); print(e.dataset_name)"` imprime `indicadores`.

### Paso 4: Refactorizar `subdere_extractor.py` como subclase

En `src/extractors/subdere_extractor.py`, agregar al inicio:

```python
from src.extractors.base import BaseExtractor
```

Crear la clase `SubdereExtractor` que envuelva las funciones de nivel módulo existentes:

```python
class SubdereExtractor(BaseExtractor):
    """Extractor de datos territoriales BCN/SUBDERE."""

    @property
    def dataset_name(self) -> str:
        return "comunas"

    def fetch(self, use_curl_cffi=False, **kwargs) -> dict:
        return fetch_comunas_data(use_curl_cffi=use_curl_cffi)

    def normalize(self, raw_data: dict) -> object:
        return normalize_comunas(raw_data)

    def validate(self, df: object, metadata: dict) -> dict:
        return validate_comunas(df, metadata)

    def write_staging(self, df: object, metadata: dict) -> Path:
        # Delegar al código existente de write en run_subdere_extraction
        # Refactor: extraer la escritura de staging como función independiente
        raise NotImplementedError(
            "TECH-DEBT: extraer la escritura de staging de run_subdere_extraction"
        )
```

**Mantener las funciones de nivel módulo** (`fetch_comunas_data`, `normalize_comunas`, `validate_comunas`, `run_subdere_extraction`) sin modificar. `SubdereExtractor` las envuelve; si `run_subdere_extraction` ya existe, puede seguir usándose tal cual desde `build_dev_db.py`.

**Verificar**: `python3 -c "from src.extractors.subdere_extractor import SubdereExtractor; e = SubdereExtractor(); print(e.dataset_name)"` imprime `comunas`.

### Paso 5: Agregar test de la clase base

En `tests/test_extractors.py`, agregar (o crear el archivo si no existe):

```python
import unittest
from src.extractors.base import BaseExtractor


class _MinimalExtractor(BaseExtractor):
    """Implementación mínima de BaseExtractor para tests."""
    @property
    def dataset_name(self) -> str:
        return "test_dataset"

    def fetch(self, **kwargs) -> dict:
        return {"records": [{"id": 1}]}

    def normalize(self, raw_data: dict) -> list:
        return raw_data.get("records", [])

    def validate(self, df: list, metadata: dict) -> dict:
        return {"valid": True, "record_count": len(df), "issues": []}

    def write_staging(self, df: list, metadata: dict):
        pass  # no-op en tests


class BaseExtractorContractTests(unittest.TestCase):
    def setUp(self):
        self.extractor = _MinimalExtractor()

    def test_dataset_name(self):
        self.assertEqual(self.extractor.dataset_name, "test_dataset")

    def test_run_dry_run_does_not_call_write_staging(self):
        # Si dry_run=True, write_staging no debe llamarse
        called = []
        original = self.extractor.write_staging
        self.extractor.write_staging = lambda *a, **kw: called.append(1)
        result = self.extractor.run(dry_run=True)
        self.assertEqual(called, [], "write_staging no debe llamarse en dry_run")

    def test_run_returns_validation_report(self):
        result = self.extractor.run(dry_run=True)
        self.assertIn("valid", result)
        self.assertIn("record_count", result)

    def test_subclase_no_puede_instanciarse_sin_abstractos(self):
        with self.assertRaises(TypeError):
            BaseExtractor()  # No puede instanciarse directamente

    def test_subdere_extractor_tiene_dataset_name(self):
        from src.extractors.subdere_extractor import SubdereExtractor
        e = SubdereExtractor()
        self.assertEqual(e.dataset_name, "comunas")

    def test_bcentral_extractor_tiene_dataset_name(self):
        from src.extractors.bcentral_extractor import BCentralExtractor
        e = BCentralExtractor()
        self.assertEqual(e.dataset_name, "indicadores")
```

**Verificar**: `.venv/bin/python -m unittest tests.test_extractors.BaseExtractorContractTests -v` — todos pasan.

### Paso 6: Correr todos los tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Verificar**: todos pasan, sin regresiones. El comportamiento observable del pipeline no cambia.

### Paso 7: Correr el build completo

```bash
make build
```

**Verificar**: exit 0. Los artefactos en `data/staging/` y `data/normalized/` son idénticos a antes del refactor.

## Criterios de done

- [ ] `src/extractors/base.py` existe con `class BaseExtractor(ABC)`
- [ ] `python3 -c "from src.extractors.base import BaseExtractor; print('OK')"` imprime `OK`
- [ ] `python3 -c "from src.extractors.subdere_extractor import SubdereExtractor; print(SubdereExtractor().dataset_name)"` imprime `comunas`
- [ ] `python3 -c "from src.extractors.bcentral_extractor import BCentralExtractor; print(BCentralExtractor().dataset_name)"` imprime `indicadores`
- [ ] `.venv/bin/python -m unittest tests.test_extractors.BaseExtractorContractTests -v` — todos pasan
- [ ] `.venv/bin/python -m unittest discover -s tests` — todos pasan (sin regresiones)
- [ ] `make build` sale con exit 0
- [ ] Las funciones de nivel módulo en `subdere_extractor.py` siguen funcionando (no se eliminaron)
- [ ] `plans/README.md` fila actualizada a DONE

## Condiciones de STOP

- Si importar `base.py` desde `subdere_extractor.py` crea una importación circular (ej. `base.py` importa algo de `subdere_extractor.py`) — reportar antes de continuar. `base.py` no debe importar nada de los extractores específicos.
- Si `process_indicators()` en `bcentral_extractor.py` mezcla fetch + normalize + write en un solo bloque sin separación clara — implementar solo `dataset_name` en la subclase y documentar el `NotImplementedError` con un ticket de deuda técnica. No refactorizar `process_indicators` internamente en este plan.
- Si los tests de extractor existentes (`test_extractors.py` si ya existía) fallan después del refactor — reportar el traceback antes de continuar.

## Notas de mantenimiento

- Para agregar un nuevo extractor: subclasificar `BaseExtractor`, implementar los 4 métodos abstractos, registrar en `DATASET_CATALOG_CONFIG` (plan 009), y agregar a `REQUIRED_DATASETS`. El test de contrato en `test_extractors.py` sirve como guía de implementación.
- `BaseExtractor.run()` es el método de orquestación por defecto. Los extractores pueden sobreescribirlo si necesitan un ciclo de vida más complejo (ej. múltiples fetch en paralelo).
- Si en el futuro se quiere soporte async, `BaseExtractor` puede evolucionar a `AsyncBaseExtractor` con `async def run()` — mantener la versión sync intacta como base para extractores simples.
