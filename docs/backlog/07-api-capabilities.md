# [07] Nuevas capacidades de API

**Estado:** Completado ✅ (2026-06-29)
**Impacto:** Medio
**Esfuerzo:** Medio

---

## Resumen

Cuatro adiciones a la API pública, todas implementadas y en producción:

### 1. `ChileHub.cross_view()` — vista pre-join por CUT
**Archivo:** `src/chile_hub/core.py` ~linea 321
**Uso:**
```python
hub.cross_view(["comunas", "censo_comunal"], on="codigo_comuna", how="left")
```
Retorna un DataFrame de Polars con columnas prefijadas por dataset.
Acepta ``list[str | Dataset]`` para los nombres.

### 2. `ChileHub.validate_user_data()` — validación contra contratos
**Archivo:** `src/chile_hub/core.py` ~linea 398
**Uso:**
```python
hub.validate_user_data(df, "comunas")
# → {"status": "ok", "errors": [], "warnings": [...]}
```
Valida columnas requeridas, tipos, clave primaria y conteo contra
``contracts/datasets/{dataset}.schema.json``.

### 3. `--exit-code` en CLI
**Archivo:** `src/chile_hub/core.py` ~lineas 1798, 1814, 1936
**Comandos que lo soportan:**
- ``chile-hub health --exit-code`` — exit 1 si ``overall_status != "ok"``
- ``chile-hub status --exit-code`` — exit 1 si ``overall_status != "ok"``
- ``chile-hub check-sources --exit-code`` — exit 1 si alguna fuente offline

### 4. `ChileHub.search_datasets()` — búsqueda programática
**Archivo:** `src/chile_hub/core.py` ~linea 485
**Uso:**
```python
hub.search_datasets(query="salud")
hub.search_datasets(source_name="INE")
hub.search_datasets(maturity="stable")
```

## Dependencias
- ✅ ME6 completado (tipos de error `ChileHubDatasetError`, `ChileHubOutputError`)

## Notas
- Todas las capacidades están cubiertas por tests en ``tests/test_chile_hub.py``
- `cross_view()` y `search_datasets()` están expuestos vía CLI como subcomandos
- ``chile-hub validate <dataset>`` también soportado (desde ME2)
