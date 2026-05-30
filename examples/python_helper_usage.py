import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chile_hub import ChileHub


hub = ChileHub()

print("--- Datasets disponibles ---")
for dataset in hub.summary():
    print(dataset)

print("\n--- Path de comunas (Parquet) ---")
print(hub.get_output_path("comunas", "parquet"))

print("\n--- Cargando indicadores con Polars ---")
df_indicadores = hub.load_polars("indicadores")
print(df_indicadores.sort(["fecha", "codigo_indicador"], descending=[True, False]).head(5))
