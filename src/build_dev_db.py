import os
import sqlite3
import polars as pl
import duckdb

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")

def ensure_directories():
    os.makedirs(NORMALIZED_DIR, exist_ok=True)

def build_duckdb(df_comunas, df_indicadores, output_path):
    print(f"Compilando base de datos DuckDB en: {output_path}")
    # Si la base de datos ya existe, la eliminamos para reconstruirla limpia
    if os.path.exists(output_path):
        os.remove(output_path)
        
    con = duckdb.connect(output_path)
    try:
        # Registrar los DataFrames de Polars como vistas temporales en DuckDB
        con.register("df_comunas_view", df_comunas)
        con.register("df_indicadores_view", df_indicadores)
        
        # Crear tablas físicas en DuckDB
        con.execute("CREATE TABLE comunas AS SELECT * FROM df_comunas_view")
        con.execute("CREATE TABLE indicadores AS SELECT * FROM df_indicadores_view")
        
        # Agregar índices básicos para mejorar rendimiento en queries
        con.execute("CREATE UNIQUE INDEX idx_comuna_code ON comunas (codigo_comuna)")
        con.execute("CREATE INDEX idx_indicador_date ON indicadores (fecha, codigo_indicador)")
        
        print("Tablas e índices creados con éxito en DuckDB.")
    finally:
        con.close()

def build_sqlite(df_comunas, df_indicadores, output_path):
    print(f"Compilando base de datos SQLite en: {output_path}")
    if os.path.exists(output_path):
        os.remove(output_path)
        
    # Convertimos a Pandas para inserción rápida con to_sql de pandas
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    
    # SQLite no maneja Date de forma nativa como tipo fecha real (los guarda como string ISO)
    # Por lo tanto, convertimos las fechas a string ISO antes de guardar
    df_indicadores_pd["fecha"] = df_indicadores_pd["fecha"].astype(str)
    
    conn = sqlite3.connect(output_path)
    try:
        df_comunas_pd.to_sql("comunas", conn, index=False, if_exists="replace")
        df_indicadores_pd.to_sql("indicadores", conn, index=False, if_exists="replace")
        
        # Crear índices en SQLite
        cursor = conn.cursor()
        cursor.execute("CREATE UNIQUE INDEX idx_lite_comuna ON comunas (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_indicador ON indicadores (fecha, codigo_indicador)")
        conn.commit()
        print("Tablas e índices creados con éxito en SQLite.")
    finally:
        conn.close()

def build_excel(df_comunas, df_indicadores, output_path):
    print(f"Generando archivo Excel consolidado para no técnicos en: {output_path}")
    # Convertir a Pandas para exportar de forma robusta con XlsxWriter
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    
    # Limpieza visual y formateo para Excel
    # En Excel, queremos que el Código Comuna siga siendo un string para que no se pierdan los ceros iniciales
    # XlsxWriter nos permite definir formatos específicos por columna
    with pd_excel_writer(output_path) as writer:
        df_comunas_pd.to_excel(writer, sheet_name="Comunas y Regiones", index=False)
        df_indicadores_pd.to_excel(writer, sheet_name="Indicadores Diarios", index=False)
        
        # Acceder a los objetos workbook y worksheet para aplicar formato estético
        workbook  = writer.book
        worksheet_comunas = writer.sheets["Comunas y Regiones"]
        worksheet_indicadores = writer.sheets["Indicadores Diarios"]
        
        # Formato de texto para el código comunal para prevenir pérdida de ceros
        text_format = workbook.add_format({'num_format': '@'})
        worksheet_comunas.set_column('A:A', 12, text_format) # Código Comuna
        worksheet_comunas.set_column('D:D', 15, text_format) # Código Provincia
        worksheet_comunas.set_column('F:F', 12, text_format) # Código Región
        
        # Ajustar anchos de columnas comunes para que sea estético
        worksheet_comunas.set_column('B:B', 22) # Nombre Comuna
        worksheet_comunas.set_column('G:G', 25) # Nombre Región
        worksheet_indicadores.set_column('A:A', 15) # Fecha
        worksheet_indicadores.set_column('B:B', 18) # Código Indicador
        worksheet_indicadores.set_column('C:C', 15) # Valor
        
    print("Archivo Excel multi-pestaña generado con éxito.")

def pd_excel_writer(path):
    import pandas as pd
    return pd.ExcelWriter(path, engine="xlsxwriter")

def build_flat_files(df_comunas, df_indicadores):
    import json
    
    # Generamos archivos Parquet
    comunas_parquet = os.path.join(NORMALIZED_DIR, "comunas.parquet")
    indicadores_parquet = os.path.join(NORMALIZED_DIR, "indicadores.parquet")
    
    df_comunas.write_parquet(comunas_parquet)
    df_indicadores.write_parquet(indicadores_parquet)
    print(f"Archivos Parquet exportados a: {NORMALIZED_DIR}")
    
    # Generamos los endpoints JSON simulados
    comunas_json = os.path.join(NORMALIZED_DIR, "comunas.json")
    indicadores_json = os.path.join(NORMALIZED_DIR, "indicadores_hoy.json")
    
    # Para JSON estáticos orientados a frontend, exportamos como lista de diccionarios
    # SQLite/DuckDB maneja fechas como objetos datetime.date, por lo que convertimos a str para serialización JSON
    df_indicadores_serializable = df_indicadores.with_columns(
        pl.col("fecha").cast(pl.String)
    )
    
    with open(comunas_json, "w", encoding="utf-8") as f:
        json.dump(df_comunas.to_dicts(), f, ensure_ascii=False, indent=2)
        
    with open(indicadores_json, "w", encoding="utf-8") as f:
        json.dump(df_indicadores_serializable.to_dicts(), f, ensure_ascii=False, indent=2)
        
    print(f"Endpoints JSON de prueba exportados a: {NORMALIZED_DIR}")

def main():
    ensure_directories()
    
    # Rutas de origen (Staging)
    comunas_csv = os.path.join(STAGING_DIR, "comunas.csv")
    indicadores_csv = os.path.join(STAGING_DIR, "indicadores.csv")
    
    if not os.path.exists(comunas_csv) or not os.path.exists(indicadores_csv):
        print("Error: No se encuentran los archivos CSV en staging. Corre los extractores primero.")
        return
        
    # Cargar datos desde staging
    # Especificamos explícitamente el tipo de dato de los códigos a String para no perder ceros
    df_comunas = pl.read_csv(comunas_csv, schema_overrides={
        "codigo_region": pl.String,
        "codigo_provincia": pl.String,
        "codigo_comuna": pl.String
    })
    
    df_indicadores = pl.read_csv(indicadores_csv, schema_overrides={
        "codigo_indicador": pl.String,
        "valor": pl.Float64
    }).with_columns(
        pl.col("fecha").str.to_date("%Y-%m-%d")
    )
    
    # Compilar entregables
    build_duckdb(df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data.duckdb"))
    build_sqlite(df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data.db"))
    build_excel(df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data_latest.xlsx"))
    build_flat_files(df_comunas, df_indicadores)
    
    print("\n--- Compilación del Sprint 0 completada con éxito ---")

if __name__ == "__main__":
    main()
