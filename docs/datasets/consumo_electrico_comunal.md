# Consumo Eléctrico Comunal

Consumo eléctrico anual por comuna y tipo de cliente, publicado por la Comisión Nacional de Energía (CNE) en el portal Energía Abierta. Los datos provienen de la información que las empresas distribuidoras entregan a la CNE.

## Fuente y licencia

- **Fuente:** CNE — Energía Abierta
- **Formato de origen:** Excel (descarga directa, sin API key)
- **Reutilización:** CC BY con atribución requerida
- **URL:** http://energiaabierta.cl/datasets-estadistica/consumo-electrico-anual-por-comuna-y-tipo-de-cliente/

## Esquema

`codigo_region`, `codigo_comuna`, `nombre_comuna`, `anio`, `tipo_cliente` (Residencial, Comercial, Industrial, Agrícola, Alumbrado Público, Otros), `consumo_kwh`, `numero_clientes`, `fuente`, `url_fuente`, `fecha_fuente`

## Uso

```python
from chile_hub import ChileHub
import polars as pl

hub = ChileHub()
df = hub.load_polars("consumo_electrico_comunal")

# Consumo residencial 2023, top 10 comunas
top_residencial = (
    df.filter(pl.col("tipo_cliente") == "Residencial")
    .sort("consumo_kwh", descending=True)
    .head(10)
)
print(top_residencial)
```

```sql
SELECT codigo_comuna, nombre_comuna, tipo_cliente,
       consumo_kwh / 1e6 AS consumo_gwh
FROM 'data/normalized/consumo_electrico_comunal.parquet'
WHERE tipo_cliente = 'Industrial'
ORDER BY consumo_kwh DESC;
```

## Limitaciones

- **Nombres de comuna sin CUT en la fuente original:** el Excel de Energía Abierta usa nombres de comuna, no códigos CUT. El extractor cruza contra la DPA de chile-hub para asignar `codigo_comuna`; comunas sin match son excluidas.
- **Rezago de publicación:** los datos anuales se publican con 1-2 años de rezago respecto al año de consumo.
- **Cambios de dominio:** el portal Energía Abierta ha cambiado de dominio históricamente (`energiaabierta.cl`, `energiaabierta.cne.cl`, `datos.energiaabierta.cl`). Se monitorea la URL.
- **Cobertura de tipo de cliente:** la clasificación por tipo de cliente sigue la nomenclatura de la CNE, que puede variar entre años.

## Registro de cambios

- v1 (2026-06-30): Primera versión. Datos de consumo eléctrico anual por comuna desde Energía Abierta (CNE).
