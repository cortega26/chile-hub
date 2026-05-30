import os
import datetime
import json
import requests
import polars as pl

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
METADATA_PATH = os.path.join(STAGING_DIR, "indicadores.metadata.json")

# API pública gratuita recomendada para desarrollo en Chile
MINDICADOR_API_URL = "https://mindicador.cl/api"

def ensure_directories():
    os.makedirs(STAGING_DIR, exist_ok=True)

def write_metadata(metadata):
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def fetch_live_indicators():
    print(f"Intentando descargar indicadores económicos diarios desde: {MINDICADOR_API_URL}")
    try:
        response = requests.get(MINDICADOR_API_URL, timeout=8)
        if response.status_code == 200:
            data = response.json()
            print("Datos de mindicador.cl descargados con éxito.")
            
            # Parsear la respuesta JSON al formato canónico
            parsed_data = []
            
            # Extraer fecha base de consulta
            # mindicador.cl entrega la UF, Dolar, Euro, UTM, etc.
            keys_to_extract = {
                "uf": "uf",
                "dolar": "dolar",
                "euro": "euro",
                "utm": "utm",
                "ipc": "ipc"
            }
            
            for api_key, canon_key in keys_to_extract.items():
                if api_key in data:
                    indicator_info = data[api_key]
                    # La fecha viene en formato ISO (ej: '2026-05-30T04:00:00.000Z')
                    # Extraemos solo la parte YYYY-MM-DD
                    raw_date = indicator_info["fecha"][:10]
                    value = float(indicator_info["valor"])
                    
                    parsed_data.append({
                        "fecha": raw_date,
                        "codigo_indicador": canon_key,
                        "valor": value
                    })
            return parsed_data
    except Exception as e:
        print(f"Error al conectar con la API de indicadores: {e}")
    return None

def generate_fallback_indicators():
    print("Generando dataset de indicadores de fallback (Simulación local offline)...")
    # Generamos registros para el día de hoy y los últimos 5 días
    today = datetime.date.today()
    fallback_data = []
    
    # Valores de referencia aproximados (Año 2026)
    base_values = {
        "uf": 39420.50,
        "dolar": 945.20,
        "euro": 1025.10,
        "utm": 65180.00,
        "ipc": 0.3
    }
    
    for i in range(6):
        target_date = today - datetime.timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Simulamos una pequeña variación diaria en divisas y UF
        # Para la UF sumamos o restamos un valor pequeño por día
        for key, base in base_values.items():
            if key == "uf":
                value = base - (i * 12.3)
            elif key == "dolar":
                value = base - (i * 2.5)
            elif key == "euro":
                value = base - (i * 1.8)
            else:
                value = base # UTM e IPC no varían a nivel diario
                
            fallback_data.append({
                "fecha": date_str,
                "codigo_indicador": key,
                "valor": round(value, 2)
            })
            
    return fallback_data

def process_indicators():
    ensure_directories()
    source_mode = "live"
    notes = []
    
    # Intentamos obtener datos en vivo
    records = fetch_live_indicators()
    
    # Si la API falla, usamos el simulador estático
    if not records:
        records = generate_fallback_indicators()
        source_mode = "fallback"
        notes.append("fallback_due_to_live_fetch_failure")
        
    df = pl.DataFrame(records)
    
    # Aseguramos tipos de datos y orden
    df = df.with_columns([
        pl.col("fecha").str.to_date("%Y-%m-%d"),
        pl.col("codigo_indicador").cast(pl.Utf8),
        pl.col("valor").cast(pl.Float64)
    ]).sort(["fecha", "codigo_indicador"])
    
    output_path = os.path.join(STAGING_DIR, "indicadores.csv")
    df.write_csv(output_path)
    metadata = {
        "dataset": "indicadores",
        "source_name": "mindicador.cl",
        "source_url": MINDICADOR_API_URL,
        "source_mode": source_mode,
        "source_detail": "public_api" if source_mode == "live" else "generated_fallback",
        "refreshed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "record_count": len(df),
        "fields": df.columns,
        "indicator_codes": sorted(df["codigo_indicador"].unique().to_list()),
        "notes": notes,
    }
    write_metadata(metadata)
    print(f"Guardados indicadores normalizados en: {output_path} (Total registros: {len(df)})")
    return output_path

if __name__ == "__main__":
    process_indicators()
