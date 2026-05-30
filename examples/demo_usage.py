import os
import duckdb

# Rutas del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data/normalized/chile_data.duckdb")
PARQUET_PATH = os.path.join(BASE_DIR, "data/normalized/comunas.parquet")

def run_duckdb_queries():
    print(f"--- 1. Conectando a la base de datos DuckDB local: {DB_PATH} ---")
    if not os.path.exists(DB_PATH):
        print(f"Error: No existe el archivo {DB_PATH}. Debes correr primero 'src/build_dev_db.py'.")
        return
        
    con = duckdb.connect(DB_PATH)
    try:
        # Consulta A: Cantidad de comunas por región
        print("\n[A] Resumen: Cantidad de comunas mapeadas por Región:")
        res_regiones = con.execute("""
            SELECT 
                codigo_region, 
                nombre_region, 
                COUNT(*) as total_comunas,
                SUM(poblacion_estimada) as poblacion_total
            FROM comunas
            GROUP BY codigo_region, nombre_region
            ORDER BY codigo_region
        """).fetch_df()
        print(res_regiones)
        
        # Consulta B: Búsqueda flexible de comunas (sin acentos)
        print("\n[B] Búsqueda: Buscar comunas por nombre aproximado ('Santiago' o 'antartica'):")
        res_search = con.execute("""
            SELECT codigo_comuna, nombre_comuna, nombre_provincia, nombre_region
            FROM comunas
            WHERE nombre_comuna_clean LIKE '%santiago%' OR nombre_comuna_clean LIKE '%antartica%'
        """).fetch_df()
        print(res_search)
        
        # Consulta C: Obtener los indicadores macroeconómicos más recientes
        print("\n[C] Indicadores: Valores más recientes cargados en la base de datos:")
        res_indicadores = con.execute("""
            SELECT fecha, codigo_indicador, valor
            FROM indicadores
            ORDER BY fecha DESC, codigo_indicador
            LIMIT 10
        """).fetch_df()
        print(res_indicadores)
        
        # Consulta D: Cruzar datos simulados de UF con población
        # Simulamos calcular el "Costo de UF por Habitante" de una región
        print("\n[D] Análisis: Simulación de cruce (Población Metropolitana vs UF hoy):")
        res_cruce = con.execute("""
            SELECT 
                c.nombre_region,
                SUM(c.poblacion_estimada) as total_habitantes,
                (SELECT valor FROM indicadores WHERE codigo_indicador = 'uf' ORDER BY fecha DESC LIMIT 1) as valor_uf_hoy,
                SUM(c.poblacion_estimada) * (SELECT valor FROM indicadores WHERE codigo_indicador = 'uf' ORDER BY fecha DESC LIMIT 1) as costo_total_uf
            FROM comunas c
            WHERE c.codigo_region = '13'
            GROUP BY c.nombre_region
        """).fetch_df()
        print(res_cruce)
        
    finally:
        con.close()

def run_direct_parquet_query():
    print(f"\n--- 2. Consultando directamente el archivo Parquet local: {PARQUET_PATH} ---")
    if not os.path.exists(PARQUET_PATH):
        print("Error: No existe el archivo Parquet.")
        return
        
    # DuckDB puede consultar archivos Parquet directamente de forma nativa sin cargarlos a memoria previamente
    con = duckdb.connect() # Conexión en memoria efímera
    try:
        res = con.execute(f"""
            SELECT codigo_comuna, nombre_comuna, poblacion_estimada
            FROM read_parquet('{PARQUET_PATH}')
            WHERE poblacion_estimada > 300000
            ORDER BY poblacion_estimada DESC
        """).fetch_df()
        print("Comunas con más de 300.000 habitantes (Consultado directo desde Parquet):")
        print(res)
    finally:
        con.close()

if __name__ == "__main__":
    run_duckdb_queries()
    run_direct_parquet_query()
