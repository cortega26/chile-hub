import os
import requests
import polars as pl

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")

# URL Oficial de la Codificación Territorial del INE (DPA 2020/2021)
# Esta URL oficial puede estar caída o cambiar sin previo aviso.
SUBDERE_DPA_URL = "https://www.subdere.gov.cl/sites/default/files/documentos/cut_2018_0.xls"

# Fallback local con una muestra representativa y real de comunas de Chile (con Ñuble y comunas con ceros iniciales)
DPA_FALLBACK_DATA = [
    # Región de Arica y Parinacota (Código 15)
    {"codigo_region": "15", "nombre_region": "Arica y Parinacota", "abreviatura": "AP", "codigo_provincia": "151", "nombre_provincia": "Arica", "codigo_comuna": "15101", "nombre_comuna": "Arica", "latitud_cabecera": -18.4783, "longitud_cabecera": -70.3126, "poblacion_estimada": 247500},
    {"codigo_region": "15", "nombre_region": "Arica y Parinacota", "abreviatura": "AP", "codigo_provincia": "151", "nombre_provincia": "Arica", "codigo_comuna": "15102", "nombre_comuna": "Camarones", "latitud_cabecera": -19.0167, "longitud_cabecera": -69.8667, "poblacion_estimada": 1200},
    # Región de Tarapacá (Código 01 - Ceros iniciales)
    {"codigo_region": "01", "nombre_region": "Tarapacá", "abreviatura": "TA", "codigo_provincia": "011", "nombre_provincia": "Iquique", "codigo_comuna": "01101", "nombre_comuna": "Iquique", "latitud_cabecera": -20.2138, "longitud_cabecera": -70.1508, "poblacion_estimada": 223400},
    {"codigo_region": "01", "nombre_region": "Tarapacá", "abreviatura": "TA", "codigo_provincia": "011", "nombre_provincia": "Iquique", "codigo_comuna": "01107", "nombre_comuna": "Alto Hospicio", "latitud_cabecera": -20.2692, "longitud_cabecera": -70.1008, "poblacion_estimada": 129000},
    # Región de Antofagasta (Código 02)
    {"codigo_region": "02", "nombre_region": "Antofagasta", "abreviatura": "AN", "codigo_provincia": "021", "nombre_provincia": "Antofagasta", "codigo_comuna": "02101", "nombre_comuna": "Antofagasta", "latitud_cabecera": -23.6500, "longitud_cabecera": -70.4000, "poblacion_estimada": 425000},
    # Región Metropolitana (Código 13)
    {"codigo_region": "13", "nombre_region": "Metropolitana de Santiago", "abreviatura": "RM", "codigo_provincia": "131", "nombre_provincia": "Santiago", "codigo_comuna": "13101", "nombre_comuna": "Santiago", "latitud_cabecera": -33.4372, "longitud_cabecera": -70.6506, "poblacion_estimada": 503000},
    {"codigo_region": "13", "nombre_region": "Metropolitana de Santiago", "abreviatura": "RM", "codigo_provincia": "131", "nombre_provincia": "Santiago", "codigo_comuna": "13114", "nombre_comuna": "Las Condes", "latitud_cabecera": -33.4121, "longitud_cabecera": -70.5666, "poblacion_estimada": 330000},
    {"codigo_region": "13", "nombre_region": "Metropolitana de Santiago", "abreviatura": "RM", "codigo_provincia": "131", "nombre_provincia": "Santiago", "codigo_comuna": "13123", "nombre_comuna": "Providencia", "latitud_cabecera": -33.4312, "longitud_cabecera": -70.6122, "poblacion_estimada": 157000},
    {"codigo_region": "13", "nombre_region": "Metropolitana de Santiago", "abreviatura": "RM", "codigo_provincia": "131", "nombre_provincia": "Santiago", "codigo_comuna": "13124", "nombre_comuna": "Pudahuel", "latitud_cabecera": -33.4411, "longitud_cabecera": -70.7516, "poblacion_estimada": 253000},
    {"codigo_region": "13", "nombre_region": "Metropolitana de Santiago", "abreviatura": "RM", "codigo_provincia": "131", "nombre_provincia": "Santiago", "codigo_comuna": "13125", "nombre_comuna": "Quilicura", "latitud_cabecera": -33.3611, "longitud_cabecera": -70.7306, "poblacion_estimada": 254000},
    # Región de Valparaíso (Código 05)
    {"codigo_region": "05", "nombre_region": "Valparaíso", "abreviatura": "VS", "codigo_provincia": "051", "nombre_provincia": "Valparaíso", "codigo_comuna": "05101", "nombre_comuna": "Valparaíso", "latitud_cabecera": -33.0472, "longitud_cabecera": -71.6127, "poblacion_estimada": 315000},
    {"codigo_region": "05", "nombre_region": "Valparaíso", "abreviatura": "VS", "codigo_provincia": "051", "nombre_provincia": "Valparaíso", "codigo_comuna": "05109", "nombre_comuna": "Viña del Mar", "latitud_cabecera": -33.0245, "longitud_cabecera": -71.5518, "poblacion_estimada": 361000},
    # Región del Biobío (Código 08)
    {"codigo_region": "08", "nombre_region": "Biobío", "abreviatura": "BI", "codigo_provincia": "081", "nombre_provincia": "Concepción", "codigo_comuna": "08101", "nombre_comuna": "Concepción", "latitud_cabecera": -36.8201, "longitud_cabecera": -73.0444, "poblacion_estimada": 235000},
    # Región de La Araucanía (Código 09)
    {"codigo_region": "09", "nombre_region": "La Araucanía", "abreviatura": "AR", "codigo_provincia": "091", "nombre_provincia": "Cautín", "codigo_comuna": "09101", "nombre_comuna": "Temuco", "latitud_cabecera": -38.7359, "longitud_cabecera": -72.5904, "poblacion_estimada": 302000},
    # Región de Los Ríos (Código 14)
    {"codigo_region": "14", "nombre_region": "Los Ríos", "abreviatura": "LR", "codigo_provincia": "141", "nombre_provincia": "Valdivia", "codigo_comuna": "14101", "nombre_comuna": "Valdivia", "latitud_cabecera": -39.8142, "longitud_cabecera": -73.2459, "poblacion_estimada": 176000},
    # Región de Los Lagos (Código 10)
    {"codigo_region": "10", "nombre_region": "Los Lagos", "abreviatura": "LL", "codigo_provincia": "101", "nombre_provincia": "Llanquihue", "codigo_comuna": "10101", "nombre_comuna": "Puerto Montt", "latitud_cabecera": -41.4689, "longitud_cabecera": -72.9411, "poblacion_estimada": 269000},
    # Región de Ñuble (Nueva Región, Código 16)
    {"codigo_region": "16", "nombre_region": "Ñuble", "abreviatura": "NU", "codigo_provincia": "161", "nombre_provincia": "Diguillín", "codigo_comuna": "16101", "nombre_comuna": "Chillán", "latitud_cabecera": -36.6066, "longitud_cabecera": -72.1034, "poblacion_estimada": 204000},
    # Región de Magallanes (Código 12)
    {"codigo_region": "12", "nombre_region": "Magallanes y de la Antártica Chilena", "abreviatura": "MG", "codigo_provincia": "121", "nombre_provincia": "Magallanes", "codigo_comuna": "12101", "nombre_comuna": "Punta Arenas", "latitud_cabecera": -53.1627, "longitud_cabecera": -70.9081, "poblacion_estimada": 141000}
]

def ensure_directories():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(STAGING_DIR, exist_ok=True)

def download_subdere_file():
    target_path = os.path.join(RAW_DIR, "cut_2018.xls")
    print(f"Intentando descargar base territorial de SUBDERE: {SUBDERE_DPA_URL}")
    try:
        response = requests.get(SUBDERE_DPA_URL, timeout=10)
        if response.status_code == 200:
            with open(target_path, "wb") as f:
                f.write(response.content)
            print("Descarga completada y almacenada en raw/cut_2018.xls")
            return target_path
        else:
            print(f"Error de descarga HTTP: Código {response.status_code}. Se utilizará el fallback local.")
    except Exception as e:
        print(f"Error al descargar la base territorial: {e}. Se utilizará el fallback local.")
    return None

def normalize_dpa(file_path=None):
    print("Normalizando la División Político-Administrativa (DPA)...")
    if file_path and os.path.exists(file_path):
        try:
            # Si logramos descargar la base de SUBDERE, la procesamos
            # Nota: cut_2018.xls suele requerir xlrd para leer con pandas o polars
            # En la Fase 0 usaremos el motor openpyxl o pandas para leer el excel si está instalado
            import pandas as pd
            df_pandas = pd.read_excel(file_path, dtype=str)
            df = pl.from_pandas(df_pandas)
            print("Procesando datos desde el archivo descargado de SUBDERE...")
            
            # Aquí vendría la lógica de renombre de columnas de SUBDERE a nuestro canon
            # Como ejemplo simplificado y robusto de normalización:
            # (SUBDERE tiene columnas Código Región, Nombre Región, Código Provincia, etc.)
            # Normalizamos el formato del Código Comuna a 5 dígitos
            df = df.rename({
                "Código Región": "codigo_region",
                "Nombre Región": "nombre_region",
                "Código Provincia": "codigo_provincia",
                "Nombre Provincia": "nombre_provincia",
                "Código Comuna": "codigo_comuna",
                "Nombre Comuna": "nombre_comuna"
            })
            
            # Aseguramos ceros a la izquierda
            df = df.with_columns([
                pl.col("codigo_region").str.rjust(2, "0"),
                pl.col("codigo_provincia").str.rjust(3, "0"),
                pl.col("codigo_comuna").str.rjust(5, "0"),
            ])
            
            # Agregar abreviaturas y centroides por defecto si no existen
            # (En un pipeline de producción completo esto cruza con datos de IDE Chile)
            df = df.with_columns([
                pl.lit("").alias("abreviatura"),
                pl.lit(0.0).cast(pl.Float64).alias("latitud_cabecera"),
                pl.lit(0.0).cast(pl.Float64).alias("longitud_cabecera"),
                pl.lit(0).cast(pl.Int32).alias("poblacion_estimada")
            ])
        except Exception as e:
            print(f"Error procesando el Excel de SUBDERE: {e}. Usando fallback de datos estático.")
            df = pl.DataFrame(DPA_FALLBACK_DATA)
    else:
        # Fallback local con los datos predefinidos
        print("Usando set de datos DPA embebido (Fase 0 Fallback)...")
        df = pl.DataFrame(DPA_FALLBACK_DATA)
    
    # Normalización adicional (nombre clean para búsquedas sin acento)
    # Reemplazo de caracteres con acento común en Chile
    df = df.with_columns(
        pl.col("nombre_comuna")
        .str.to_lowercase()
        .str.replace_all("á", "a")
        .str.replace_all("é", "e")
        .str.replace_all("í", "i")
        .str.replace_all("ó", "o")
        .str.replace_all("ú", "u")
        .str.replace_all("ü", "u")
        .alias("nombre_comuna_clean")
    )
    
    # Reordenar y seleccionar columnas finales
    df_clean = df.select([
        "codigo_region",
        "nombre_region",
        "abreviatura",
        "codigo_provincia",
        "nombre_provincia",
        "codigo_comuna",
        "nombre_comuna",
        "nombre_comuna_clean",
        "latitud_cabecera",
        "longitud_cabecera",
        "poblacion_estimada"
    ])
    
    output_path = os.path.join(STAGING_DIR, "comunas.csv")
    df_clean.write_csv(output_path)
    print(f"Guardada DPA normalizada en: {output_path} (Total registros: {len(df_clean)})")
    return output_path

if __name__ == "__main__":
    ensure_directories()
    # Intentamos la descarga, pero el script es inmune a fallos de red por el fallback
    raw_file = download_subdere_file()
    normalize_dpa(raw_file)
