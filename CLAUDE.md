# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito

`chile-hub` es un hub de capas de datos públicos de Chile — demográficos, económicos, políticos, socioeconómicos y de cualquier área que pueda ser de interés para analistas de datos, siempre que la fuente sea pública, legal y sistemáticamente consumible. El MVP arrancó con la DPA territorial e indicadores económicos para validar el enfoque; el alcance temático a largo plazo es amplio por diseño.

El valor del proyecto no es "tener todos los datos de Chile", sino reducir el costo de encontrar, limpiar, entender, cruzar y consumir datasets confiables. Técnicamente, el proyecto implementa un pipeline de extracción, normalización y empaquetado que produce artefactos reproducibles (Parquet, DuckDB, JSON, ZIP) consumibles en una línea de código, junto con una landing page estática y una CLI/API Python (`ChileHub`).

## Comandos esenciales

```bash
# Entorno
make bootstrap          # Crea .venv, instala dependencias y Chromium para Playwright
make doctor             # Verifica Python efectivo y dependencias clave

# Pipeline completo
make refresh            # extract → build → verify → test → verify-landing

# Pasos individuales
make extract            # Corre los dos extractores (subdere + bcentral)
make build              # Compila todos los artefactos desde data/staging/
make verify             # Verifica integridad de artefactos en data/normalized/
make test               # Suite completa de tests
make verify-landing     # Smoke tests de la landing con Playwright
make status             # Genera pipeline_status.md e imprime resumen humano

# Paquete publicable
make package-bundle     # Genera el ZIP publicable desde el manifest

# CLI del hub
python -m src.chile_hub list
python -m src.chile_hub health --format table
python -m src.chile_hub overview --format table
python -m src.chile_hub runtime-status --format table
python -m src.chile_hub top-issue --format table
```

### Tests

```bash
# Tests completos (requieren que el pipeline haya corrido al menos una vez)
./.venv/bin/python -m unittest discover -s tests -v

# Test individual
./.venv/bin/python -m unittest tests.test_chile_hub.ChileHubTests.test_load_polars -v
```

Los tests leen de `data/normalized/` — **no ejecutan el pipeline**. Si fallan por datos ausentes, correr `make build` antes de los tests.

## Arquitectura del pipeline

El flujo es estrictamente secuencial en cuatro etapas:

```
EXTRACT → staging → BUILD → normalized → VERIFY + TEST + LANDING
```

| Archivo | Rol |
|---|---|
| `src/extractors/subdere_extractor.py` | Extrae DPA desde BCN ArcGIS → `data/staging/comunas.{csv,metadata.json}` + `data/raw/` |
| `src/extractors/bcentral_extractor.py` | Extrae indicadores desde mindicador.cl → `data/staging/indicadores.{csv,metadata.json}` + `data/raw/` |
| `src/build_dev_db.py` | Lee `data/staging/`, valida, construye **todos** los artefactos en `data/normalized/` (Parquet, DuckDB, SQLite, Excel, JSON, ZIP, manifests, reportes) |
| `src/pipeline_status_utils.py` | Funciones para generar reportes Markdown (health, catálogo, redistribución, drift, overview) |
| `src/chile_hub.py` | API Python (`ChileHub`) y CLI (`python -m src.chile_hub`) |
| `scripts/verify_pipeline.py` | Verifica integridad post-build |
| `scripts/verify_landing.py` | Smoke tests Playwright de `index.html` |
| `scripts/pipeline_status.py` | Genera `pipeline_status.md` |
| `scripts/package_publishable_bundle.py` | Genera el ZIP publicable desde `artifact_manifest.json` |

### Artefactos clave en `data/normalized/`

- `dataset_catalog.json` — catálogo machine-readable por dataset (schema, freshness, outputs, ejemplos)
- `hub_bundle.json` — entrypoint único consolidado para consumo automatizado
- `hub_status.json` — polling liviano: `overall_status`, contadores clave, `top_issue`
- `hub_health.json` — salud agregada del hub con breakdown por capa
- `artifact_manifest.json` — hashes y tamaños de artefactos publicables
- `pipeline_metadata.json` — metadata detallada del último build

**Nunca editar `data/normalized/` manualmente.** Siempre regenerar con el pipeline.

## Invariantes críticas

### Códigos CUT siempre como string de longitud fija

```python
codigo_region    = "01"     # VARCHAR, 2 chars
codigo_provincia = "011"    # VARCHAR, 3 chars
codigo_comuna    = "01101"  # VARCHAR, 5 chars
```

Excel y pandas pueden silenciosamente convertir a int y perder el cero inicial. El pipeline usa Polars (`pl.String`) y DuckDB (`VARCHAR`) para evitarlo.

### El pipeline falla ruidosamente antes de publicar datos malos

```python
if errors:
    raise SystemExit(f"Validación fallida: {errors}")
```

Un dataset corrupto es peor que un dataset desactualizado. No usar warnings silenciosos para errores de datos críticos.

### `data/raw/` es de solo lectura una vez escrito

Los snapshots en `data/raw/` son el registro de auditoría. No modificarlos.

### `nombre_comuna_clean` siempre presente, minúsculas, sin tildes ni ñ

Es la clave para joins de texto inexactos. La normalización usa Polars `.str` en orden específico (ver `AGENTS.md` §4.5).

### Paths siempre relativos a `__file__`

```python
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
```

Nunca usar paths relativos al CWD (`"data"`); fallan en CI.

## Agregar un nuevo dataset

Ver `AGENTS.md` §5 para la guía completa. Resumen:

1. Evaluar fuente (licencia, estabilidad de API, cruce con DPA)
2. Crear `src/extractors/{nombre}_extractor.py` con fallback, snapshot en `data/raw/`, CSV en `data/staging/` y `metadata.json`
3. Registrar en `DATASET_CATALOG_CONFIG` dentro de `build_dev_db.py`
4. Agregar `validate_{nombre}()` en `build_dev_db.py`
5. Agregar tests en `tests/test_chile_hub.py`
6. Agregar extractor al workflow de CI en `.github/workflows/pipeline-check.yml`
7. Crear `docs/datasets/{nombre}.md`

### Campos obligatorios en `metadata.json` del extractor

```json
{
  "dataset": "...",
  "source_name": "...",
  "source_url": "...",
  "source_mode": "live | fallback",
  "source_detail": "...",
  "refreshed_at_utc": "...",
  "record_count": 0,
  "fields": [],
  "notes": [],
  "reuse_policy": {
    "status": "open-attribution | public-api-review-terms | restricted",
    "license": "...",
    "license_url": "...",
    "attribution_required": true,
    "redistribution_ok": true,
    "summary": "..."
  }
}
```

## Convenciones

- **Columnas**: `snake_case` en español (`codigo_region`, `nombre_comuna`, `fecha`, `valor`)
- **Tipos**: códigos CUT → `pl.String`/`VARCHAR`; fechas → `pl.Date`/`DATE` (ISO 8601); coordenadas → `pl.Float64`/`DOUBLE`
- **Versiones en `requirements.txt`**: fijar exactas (no rangos `>=`) para reproducibilidad en CI
- **Imports**: stdlib → third-party alfabético → locales
- **Redistribución**: fuentes `restricted` o `public-api-review-terms` no entran al bundle ZIP público sin resolución legal documentada
