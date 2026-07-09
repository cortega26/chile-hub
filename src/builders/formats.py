"""Builders de formato de salida: DuckDB, SQLite, Excel y archivos planos.

Cada función recibe los DataFrames ya normalizados y escribe un artefacto en
disco de forma atómica.
"""

import os
import sqlite3

import duckdb
import polars as pl

from src.builders._shared import DATASET_CATALOG_CONFIG, EXCEL_MAX_ROWS, NORMALIZED_DIR
from src.builders.io_utils import pd_excel_writer, write_json_atomic, write_parquet_atomic


def build_duckdb(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    extra_tables,
    output_path,
):
    print(f"Compilando base de datos DuckDB en: {output_path}")
    tmp_path = output_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    con = duckdb.connect(tmp_path)
    try:
        # Registrar los DataFrames de Polars como vistas temporales en DuckDB
        con.register("df_regiones_view", df_regiones)
        con.register("df_provincias_view", df_provincias)
        con.register("df_comunas_view", df_comunas)
        con.register("df_indicadores_view", df_indicadores)
        con.register("df_censo_view", df_censo)
        con.register("df_salud_view", df_salud)
        con.register("df_educacionales_view", df_educacionales)
        for table_name, df_extra in extra_tables.items():
            con.register(f"df_{table_name}_view", df_extra)

        # Crear tablas físicas en DuckDB
        con.execute("CREATE TABLE regiones AS SELECT * FROM df_regiones_view")
        con.execute("CREATE TABLE provincias AS SELECT * FROM df_provincias_view")
        con.execute("CREATE TABLE comunas AS SELECT * FROM df_comunas_view")
        con.execute("CREATE VIEW comunas_enriquecidas AS SELECT * FROM comunas")
        con.execute("CREATE TABLE indicadores AS SELECT * FROM df_indicadores_view")
        con.execute("CREATE TABLE censo_comunal AS SELECT * FROM df_censo_view")
        con.execute("CREATE TABLE establecimientos_salud AS SELECT * FROM df_salud_view")
        con.execute(
            "CREATE TABLE establecimientos_educacionales AS SELECT * FROM df_educacionales_view"
        )
        for table_name in extra_tables:
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_{table_name}_view")  # nosec B608  # table_name from internal catalog dict, not user input

        # Agregar índices básicos para mejorar rendimiento en queries
        con.execute("CREATE UNIQUE INDEX idx_region_code ON regiones (codigo_region)")
        con.execute("CREATE UNIQUE INDEX idx_provincia_code ON provincias (codigo_provincia)")
        con.execute("CREATE UNIQUE INDEX idx_comuna_code ON comunas (codigo_comuna)")
        con.execute("CREATE INDEX idx_indicador_date ON indicadores (fecha, codigo_indicador)")
        con.execute("CREATE UNIQUE INDEX idx_censo_comuna ON censo_comunal (codigo_comuna)")
        con.execute("CREATE INDEX idx_salud_comuna ON establecimientos_salud (codigo_comuna)")
        con.execute("CREATE UNIQUE INDEX idx_educ_rbd ON establecimientos_educacionales (rbd)")
        con.execute(
            "CREATE INDEX idx_educ_comuna ON establecimientos_educacionales (codigo_comuna)"
        )
        for table_name in extra_tables:
            if "codigo_comuna" in extra_tables[table_name].columns:
                con.execute(f"CREATE INDEX idx_{table_name}_comuna ON {table_name} (codigo_comuna)")

        print("Tablas e índices creados con éxito en DuckDB.")
    finally:
        con.close()

    os.replace(tmp_path, output_path)


def build_sqlite(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    extra_tables,
    extra_tables_pd=None,
    output_path=None,
):
    print(f"Compilando base de datos SQLite en: {output_path}")
    tmp_path = output_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    # Convertimos a Pandas para inserción con to_sql de pandas
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    df_censo_pd = df_censo.to_pandas()
    df_salud_pd = df_salud.to_pandas()
    df_educacionales_pd = df_educacionales.to_pandas()
    if extra_tables_pd is None:
        extra_tables_pd = {name: df.to_pandas() for name, df in extra_tables.items()}

    # SQLite no maneja Date de forma nativa como tipo fecha real (los guarda como string ISO)
    # Por lo tanto, convertimos las fechas a string ISO antes de guardar
    df_indicadores_pd["fecha"] = df_indicadores_pd["fecha"].astype(str)

    conn = sqlite3.connect(tmp_path)
    try:
        df_regiones_pd.to_sql("regiones", conn, index=False, if_exists="replace")
        df_provincias_pd.to_sql("provincias", conn, index=False, if_exists="replace")
        df_comunas_pd.to_sql("comunas", conn, index=False, if_exists="replace")
        conn.execute("CREATE VIEW comunas_enriquecidas AS SELECT * FROM comunas")
        df_indicadores_pd.to_sql("indicadores", conn, index=False, if_exists="replace")
        df_censo_pd.to_sql("censo_comunal", conn, index=False, if_exists="replace")
        df_salud_pd.to_sql("establecimientos_salud", conn, index=False, if_exists="replace")
        df_educacionales_pd.to_sql(
            "establecimientos_educacionales", conn, index=False, if_exists="replace"
        )
        # SQLite no es eficiente para tablas masivas.  Omitimos las que
        # superen el umbral; DuckDB y Parquet cubren ese caso de uso.
        _SQLITE_MAX_ROWS = 500_000
        _SQLITE_MAX_VARS = 999
        for table_name, df_extra in extra_tables_pd.items():
            num_rows = len(df_extra)
            if num_rows > _SQLITE_MAX_ROWS:
                print(
                    f"  Omite SQLite para {table_name} ({num_rows:,} filas > "
                    f"{_SQLITE_MAX_ROWS:,}) — usa DuckDB o Parquet.",
                    flush=True,
                )
                continue
            num_cols = len(df_extra.columns)
            if num_rows > 10_000 and num_cols > 0:
                chunksize = _SQLITE_MAX_VARS // num_cols
                df_extra.to_sql(
                    table_name,
                    conn,
                    index=False,
                    if_exists="replace",
                    method="multi",
                    chunksize=chunksize,
                )
            else:
                df_extra.to_sql(table_name, conn, index=False, if_exists="replace")

        # Crear índices en SQLite
        cursor = conn.cursor()
        cursor.execute("CREATE UNIQUE INDEX idx_lite_region ON regiones (codigo_region)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_provincia ON provincias (codigo_provincia)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_comuna ON comunas (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_indicador ON indicadores (fecha, codigo_indicador)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_censo ON censo_comunal (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_salud ON establecimientos_salud (codigo_comuna)")
        cursor.execute(
            "CREATE UNIQUE INDEX idx_lite_educ_rbd ON establecimientos_educacionales (rbd)"
        )
        cursor.execute(
            "CREATE INDEX idx_lite_educ_comuna ON establecimientos_educacionales (codigo_comuna)"
        )
        for table_name, df_extra in extra_tables.items():
            if "codigo_comuna" in df_extra.columns:
                cursor.execute(
                    f"CREATE INDEX idx_lite_{table_name}_comuna ON {table_name} (codigo_comuna)"
                )
        conn.commit()
        print("Tablas e índices creados con éxito en SQLite.")
    finally:
        conn.close()

    os.replace(tmp_path, output_path)


def build_excel(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    extra_tables,
    extra_tables_pd=None,
    output_path=None,
):
    print(f"Generando archivo Excel consolidado para no técnicos en: {output_path}")
    # Convertir a Pandas para exportar de forma robusta con XlsxWriter
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    df_censo_pd = df_censo.to_pandas()
    df_salud_pd = df_salud.to_pandas()
    df_educacionales_pd = df_educacionales.to_pandas()
    if extra_tables_pd is None:
        extra_tables_pd = {name: df.to_pandas() for name, df in extra_tables.items()}

    # Limpieza visual y formateo para Excel
    # En Excel, queremos que el Código Comuna siga siendo un string para que no se pierdan los ceros iniciales
    # XlsxWriter nos permite definir formatos específicos por columna
    tmp_path = output_path + ".tmp.xlsx"
    with pd_excel_writer(tmp_path) as writer:
        df_regiones_pd.to_excel(writer, sheet_name="Regiones", index=False)
        df_provincias_pd.to_excel(writer, sheet_name="Provincias", index=False)
        df_comunas_pd.to_excel(writer, sheet_name="Comunas y Regiones", index=False)
        df_indicadores_pd.to_excel(writer, sheet_name="Indicadores Diarios", index=False)
        df_censo_pd.to_excel(writer, sheet_name="Censo Comunal", index=False)
        df_salud_pd.to_excel(writer, sheet_name="Establecimientos Salud", index=False)
        df_educacionales_pd.to_excel(
            writer, sheet_name="Establecimientos Educacionales", index=False
        )
        # Escribir tablas extra, dividiendo las que excedan el límite de filas de Excel
        _EXCEL_MAX_ROWS_SKIP = 500_000
        extra_sheet_names = {}  # table_name -> [sheet_names]
        for table_name, df_extra in extra_tables_pd.items():
            num_rows = len(df_extra)
            if num_rows > _EXCEL_MAX_ROWS_SKIP:
                print(
                    f"  Omite Excel para {table_name} ({num_rows:,} filas > "
                    f"{_EXCEL_MAX_ROWS_SKIP:,}) — usa DuckDB o Parquet.",
                    flush=True,
                )
                continue
            base_sheet = DATASET_CATALOG_CONFIG[table_name]["outputs"].get(
                "excel_sheet", table_name[:31]
            )[:31]
            if num_rows <= EXCEL_MAX_ROWS:
                df_extra.to_excel(writer, sheet_name=base_sheet, index=False)
                extra_sheet_names[table_name] = [base_sheet]
            else:
                num_parts = (num_rows + EXCEL_MAX_ROWS - 1) // EXCEL_MAX_ROWS
                print(
                    f"  ⚠ {base_sheet}: {num_rows:,} filas exceden el límite de Excel "
                    f"({EXCEL_MAX_ROWS:,}) — dividiendo en {num_parts} hojas."
                )
                part_names = []
                for i in range(num_parts):
                    start = i * EXCEL_MAX_ROWS
                    end = min(start + EXCEL_MAX_ROWS, num_rows)
                    # "HojaBase" → "HojaBase parte 1", …
                    suffix = f" parte {i + 1}"
                    max_base = 31 - len(suffix)
                    part_name = base_sheet[:max_base] + suffix
                    df_extra.iloc[start:end].to_excel(writer, sheet_name=part_name, index=False)
                    part_names.append(part_name)
                extra_sheet_names[table_name] = part_names

        # Acceder a los objetos workbook y worksheet para aplicar formato estético
        worksheet_regiones = writer.sheets["Regiones"]
        worksheet_provincias = writer.sheets["Provincias"]
        workbook = writer.book
        worksheet_comunas = writer.sheets["Comunas y Regiones"]
        worksheet_indicadores = writer.sheets["Indicadores Diarios"]
        worksheet_censo = writer.sheets["Censo Comunal"]
        worksheet_salud = writer.sheets["Establecimientos Salud"]
        worksheet_educacionales = writer.sheets["Establecimientos Educacionales"]

        # Formato de texto para el código comunal para prevenir pérdida de ceros
        text_format = workbook.add_format({"num_format": "@"})
        worksheet_regiones.set_column("A:A", 12, text_format)
        worksheet_provincias.set_column("A:A", 12, text_format)
        worksheet_provincias.set_column("C:C", 15, text_format)
        worksheet_comunas.set_column("A:A", 12, text_format)  # Código Comuna
        worksheet_comunas.set_column("D:D", 15, text_format)  # Código Provincia
        worksheet_comunas.set_column("F:F", 12, text_format)  # Código Región

        # Ajustar anchos de columnas comunes para que sea estético
        worksheet_comunas.set_column("B:B", 22)  # Nombre Comuna
        worksheet_comunas.set_column("G:G", 25)  # Nombre Región
        worksheet_indicadores.set_column("A:A", 15)  # Fecha
        worksheet_indicadores.set_column("B:B", 18)  # Código Indicador
        worksheet_indicadores.set_column("C:C", 15)  # Valor
        worksheet_censo.set_column("A:A", 12, text_format)
        worksheet_censo.set_column("C:C", 15, text_format)
        worksheet_censo.set_column("E:E", 15, text_format)
        worksheet_salud.set_column("A:A", 20, text_format)
        worksheet_salud.set_column("F:F", 12, text_format)
        worksheet_salud.set_column("H:H", 15, text_format)
        worksheet_educacionales.set_column("A:A", 12, text_format)  # rbd
        worksheet_educacionales.set_column("B:B", 10, text_format)  # dv_rbd
        worksheet_educacionales.set_column("D:D", 12, text_format)  # codigo_region
        worksheet_educacionales.set_column("E:E", 12, text_format)  # codigo_comuna
        for table_name, sheet_names in extra_sheet_names.items():
            df_extra = extra_tables[table_name]
            has_codigo_comuna = "codigo_comuna" in df_extra.columns
            codigo_comuna_idx = (
                df_extra.columns.index("codigo_comuna") if has_codigo_comuna else None
            )
            for sheet_name in sheet_names:
                worksheet = writer.sheets[sheet_name]
                if has_codigo_comuna:
                    worksheet.set_column(codigo_comuna_idx, codigo_comuna_idx, 12, text_format)

    os.replace(tmp_path, output_path)
    print("Archivo Excel multi-pestaña generado con éxito.")


def build_flat_files(
    df_regiones,
    df_provincias,
    df_comunas,
    df_indicadores,
    df_censo,
    df_salud,
    df_educacionales,
    extra_tables=None,
):
    if extra_tables is None:
        extra_tables = {}
    # Generamos archivos Parquet
    regiones_parquet = os.path.join(NORMALIZED_DIR, "regiones.parquet")
    provincias_parquet = os.path.join(NORMALIZED_DIR, "provincias.parquet")
    comunas_parquet = os.path.join(NORMALIZED_DIR, "comunas.parquet")
    indicadores_parquet = os.path.join(NORMALIZED_DIR, "indicadores.parquet")

    write_parquet_atomic(df_regiones, regiones_parquet)
    write_parquet_atomic(df_provincias, provincias_parquet)
    write_parquet_atomic(df_comunas, comunas_parquet)
    write_parquet_atomic(df_indicadores, indicadores_parquet)
    write_parquet_atomic(df_censo, os.path.join(NORMALIZED_DIR, "censo_comunal.parquet"))
    write_parquet_atomic(df_salud, os.path.join(NORMALIZED_DIR, "establecimientos_salud.parquet"))
    write_parquet_atomic(
        df_educacionales, os.path.join(NORMALIZED_DIR, "establecimientos_educacionales.parquet")
    )
    for table_name, df_extra in extra_tables.items():
        write_parquet_atomic(df_extra, os.path.join(NORMALIZED_DIR, f"{table_name}.parquet"))
    print(f"  Archivos Parquet exportados a: {NORMALIZED_DIR}")

    # Generamos los endpoints JSON simulados
    regiones_json = os.path.join(NORMALIZED_DIR, "regiones.json")
    provincias_json = os.path.join(NORMALIZED_DIR, "provincias.json")
    comunas_json = os.path.join(NORMALIZED_DIR, "comunas.json")
    indicadores_json = os.path.join(NORMALIZED_DIR, "indicadores_hoy.json")

    # Para JSON estáticos orientados a frontend, exportamos como lista de diccionarios
    # SQLite/DuckDB maneja fechas como objetos datetime.date, por lo que convertimos a str para serialización JSON
    df_indicadores_serializable = df_indicadores.with_columns(pl.col("fecha").cast(pl.String))

    write_json_atomic(df_regiones.to_dicts(), regiones_json, ensure_ascii=False, indent=2)
    write_json_atomic(df_provincias.to_dicts(), provincias_json, ensure_ascii=False, indent=2)
    write_json_atomic(df_comunas.to_dicts(), comunas_json, ensure_ascii=False, indent=2)
    write_json_atomic(
        df_indicadores_serializable.to_dicts(), indicadores_json, ensure_ascii=False, indent=2
    )
    write_json_atomic(
        df_censo.to_dicts(),
        os.path.join(NORMALIZED_DIR, "censo_comunal.json"),
        ensure_ascii=False,
        indent=2,
    )
    write_json_atomic(
        df_salud.to_dicts(),
        os.path.join(NORMALIZED_DIR, "establecimientos_salud.json"),
        ensure_ascii=False,
        indent=2,
    )
    write_json_atomic(
        df_educacionales.to_dicts(),
        os.path.join(NORMALIZED_DIR, "establecimientos_educacionales.json"),
        ensure_ascii=False,
        indent=2,
    )
    # JSON para tablas extra: omitir las masivas (> 100k filas).
    # Parquet y DuckDB son los formatos recomendados para grandes volúmenes.
    _JSON_MAX_ROWS = 100_000
    for table_name, df_extra in extra_tables.items():
        num_rows = df_extra.height
        if num_rows > _JSON_MAX_ROWS:
            print(
                f"  Omite JSON para {table_name} ({num_rows:,} filas > {_JSON_MAX_ROWS:,}) — "
                f"usa Parquet en su lugar."
            )
            continue
        write_json_atomic(
            df_extra.to_dicts(),
            os.path.join(NORMALIZED_DIR, f"{table_name}.json"),
            ensure_ascii=False,
            indent=2,
        )

    print(f"  Endpoints JSON exportados a: {NORMALIZED_DIR}")
