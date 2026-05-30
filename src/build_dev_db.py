import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
import polars as pl
import duckdb
from pipeline_status_utils import write_status_markdown_file, write_dataset_catalog_markdown_file

# Configuración de rutas
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
STAGING_DIR = os.path.join(DATA_DIR, "staging")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
COMUNAS_METADATA_PATH = os.path.join(STAGING_DIR, "comunas.metadata.json")
INDICADORES_METADATA_PATH = os.path.join(STAGING_DIR, "indicadores.metadata.json")

EXPECTED_INDICATOR_CODES = {"uf", "dolar", "euro", "utm", "ipc"}
FALLBACK_COMUNAS_COUNT = 18
EXPECTED_LIVE_COMUNAS_COUNT = 346
PUBLISHABLE_ARTIFACT_SUFFIXES = (".json", ".md", ".parquet")

DATASET_CATALOG_CONFIG = {
    "regiones": {
        "description": "Capa derivada de regiones para filtros, joins y referencias administrativas de alto nivel.",
        "join_keys": ["codigo_region"],
        "confidence_tier": "Tier B",
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('regiones')",
            "duckdb": "SELECT *\nFROM 'data/normalized/regiones.parquet'\nORDER BY codigo_region;",
            "cli": "python -m src.chile_hub show regiones",
        },
        "outputs": {
            "parquet": "data/normalized/regiones.parquet",
            "json": "data/normalized/regiones.json",
            "duckdb_table": "regiones",
            "sqlite_table": "regiones",
            "excel_sheet": "Regiones",
        },
        "documentation": "docs/datasets/regiones.md",
    },
    "provincias": {
        "description": "Capa derivada de provincias para cruces intermedios entre region y comuna.",
        "join_keys": ["codigo_provincia", "codigo_region"],
        "confidence_tier": "Tier B",
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('provincias')",
            "duckdb": "SELECT *\nFROM 'data/normalized/provincias.parquet'\nWHERE codigo_region = '13';",
            "cli": "python -m src.chile_hub show provincias",
        },
        "outputs": {
            "parquet": "data/normalized/provincias.parquet",
            "json": "data/normalized/provincias.json",
            "duckdb_table": "provincias",
            "sqlite_table": "provincias",
            "excel_sheet": "Provincias",
        },
        "documentation": "docs/datasets/provincias.md",
    },
    "comunas": {
        "description": "Base territorial normalizada para cruces por region, provincia y comuna.",
        "join_keys": ["codigo_comuna", "codigo_region"],
        "confidence_tier": "Tier B",
        "freshness_policy": {
            "max_age_hours": 24 * 90,
            "label": "estable",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('comunas')",
            "duckdb": "SELECT codigo_comuna, nombre_comuna, nombre_region\nFROM 'data/normalized/comunas.parquet'\nLIMIT 10;",
            "cli": "python -m src.chile_hub path comunas --output parquet",
        },
        "outputs": {
            "parquet": "data/normalized/comunas.parquet",
            "json": "data/normalized/comunas.json",
            "duckdb_table": "comunas",
            "sqlite_table": "comunas",
            "excel_sheet": "Comunas y Regiones",
        },
        "documentation": "docs/datasets/comunas.md",
    },
    "indicadores": {
        "description": "Serie de indicadores economicos diarios de referencia para analisis y software.",
        "join_keys": ["fecha", "codigo_indicador"],
        "confidence_tier": "Tier A/B",
        "freshness_policy": {
            "max_age_hours": 72,
            "label": "diaria",
        },
        "usage_examples": {
            "python": "from src.chile_hub import ChileHub\n\nhub = ChileHub()\ndf = hub.load_polars('indicadores')",
            "duckdb": "SELECT *\nFROM 'data/normalized/indicadores.parquet'\nORDER BY fecha DESC, codigo_indicador;",
            "cli": "python -m src.chile_hub show indicadores",
        },
        "outputs": {
            "parquet": "data/normalized/indicadores.parquet",
            "json": "data/normalized/indicadores_hoy.json",
            "duckdb_table": "indicadores",
            "sqlite_table": "indicadores",
            "excel_sheet": "Indicadores Diarios",
        },
        "documentation": "docs/datasets/indicadores.md",
    },
}


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_freshness(refreshed_at_utc, max_age_hours):
    refreshed_at = parse_iso_datetime(refreshed_at_utc)
    if refreshed_at is None or max_age_hours is None:
        return {
            "status": "unknown",
            "age_hours": None,
            "max_age_hours": max_age_hours,
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    checked_at = datetime.now(timezone.utc)
    age_hours = max((checked_at - refreshed_at).total_seconds() / 3600, 0)
    return {
        "status": "fresh" if age_hours <= max_age_hours else "stale",
        "age_hours": round(age_hours, 2),
        "max_age_hours": max_age_hours,
        "checked_at_utc": checked_at.isoformat(),
    }

def ensure_directories():
    os.makedirs(NORMALIZED_DIR, exist_ok=True)

def load_metadata(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_comunas(df_comunas, metadata):
    errors = []
    warnings = []
    row_count = df_comunas.height
    duplicate_count = row_count - df_comunas["codigo_comuna"].n_unique()

    if duplicate_count > 0:
        errors.append(f"codigo_comuna must be unique, found {duplicate_count} duplicate rows")

    if metadata and metadata.get("source_mode") == "live" and row_count < EXPECTED_LIVE_COMUNAS_COUNT:
        errors.append(
            f"live comunas dataset looks incomplete: {row_count} rows, expected at least {EXPECTED_LIVE_COMUNAS_COUNT}"
        )

    if metadata and metadata.get("source_mode") == "fallback":
        if row_count != FALLBACK_COMUNAS_COUNT:
            warnings.append(
                f"fallback comunas expected about {FALLBACK_COMUNAS_COUNT} rows, found {row_count}"
            )
        warnings.append("comunas source_mode is fallback; coverage is limited by design")

    return {
        "dataset": "comunas",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
    }

def validate_regiones(df_regiones):
    errors = []
    if df_regiones.height == 0:
        errors.append("regiones dataset is empty")
    duplicate_count = df_regiones.height - df_regiones["codigo_region"].n_unique()
    if duplicate_count > 0:
        errors.append(f"codigo_region must be unique, found {duplicate_count} duplicate rows")
    return {
        "dataset": "regiones",
        "status": "error" if errors else "ok",
        "record_count": df_regiones.height,
        "errors": errors,
        "warnings": [],
    }

def validate_provincias(df_provincias):
    errors = []
    if df_provincias.height == 0:
        errors.append("provincias dataset is empty")
    keys = (
        df_provincias["codigo_region"] + "-" + df_provincias["codigo_provincia"]
    ).n_unique()
    if keys != df_provincias.height:
        errors.append("codigo_region + codigo_provincia must be unique")
    return {
        "dataset": "provincias",
        "status": "error" if errors else "ok",
        "record_count": df_provincias.height,
        "errors": errors,
        "warnings": [],
    }

def validate_indicadores(df_indicadores, metadata):
    errors = []
    warnings = []
    row_count = df_indicadores.height
    codes = set(df_indicadores["codigo_indicador"].unique().to_list())
    missing_codes = sorted(EXPECTED_INDICATOR_CODES - codes)

    if row_count == 0:
        errors.append("indicadores dataset is empty")

    if missing_codes:
        errors.append(f"missing expected indicator codes: {', '.join(missing_codes)}")

    if metadata and metadata.get("source_mode") == "fallback":
        warnings.append("indicadores source_mode is fallback; values are synthetic development data")

    return {
        "dataset": "indicadores",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "indicator_codes": sorted(codes),
    }

def write_pipeline_metadata(dataset_metadata, validations):
    pipeline_metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": dataset_metadata,
        "validations": validations,
    }
    output_path = os.path.join(NORMALIZED_DIR, "pipeline_metadata.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_metadata, f, ensure_ascii=False, indent=2)
    return output_path

def write_dataset_catalog(pipeline_metadata):
    datasets = []
    for dataset_name, dataset_metadata in pipeline_metadata["datasets"].items():
        validation = pipeline_metadata["validations"].get(dataset_name, {})
        config = DATASET_CATALOG_CONFIG.get(dataset_name, {})
        freshness_policy = config.get("freshness_policy", {})
        datasets.append(
            {
                "dataset": dataset_name,
                "description": config.get("description", ""),
                "source_name": dataset_metadata.get("source_name"),
                "source_url": dataset_metadata.get("source_url"),
                "source_mode": dataset_metadata.get("source_mode"),
                "source_detail": dataset_metadata.get("source_detail"),
                "refreshed_at_utc": dataset_metadata.get("refreshed_at_utc"),
                "record_count": dataset_metadata.get("record_count"),
                "fields": dataset_metadata.get("fields", []),
                "join_keys": config.get("join_keys", []),
                "confidence_tier": config.get("confidence_tier"),
                "freshness": dataset_metadata.get("freshness", {}),
                "freshness_policy": freshness_policy,
                "usage_examples": config.get("usage_examples", {}),
                "outputs": config.get("outputs", {}),
                "documentation": config.get("documentation"),
                "validation_status": validation.get("status"),
                "warnings": validation.get("warnings", []),
                "notes": dataset_metadata.get("notes", []),
            }
        )

    catalog = {
        "generated_at_utc": pipeline_metadata["generated_at_utc"],
        "dataset_count": len(datasets),
        "datasets": datasets,
    }
    output_path = os.path.join(NORMALIZED_DIR, "dataset_catalog.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    return output_path

def compute_sha256(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def build_publishable_artifact_index():
    artifact_index = {}
    for dataset_name, config in DATASET_CATALOG_CONFIG.items():
        outputs = config.get("outputs", {})
        for output_type, path in outputs.items():
            if isinstance(path, str) and path.startswith("data/normalized/"):
                artifact_index[path] = {
                    "dataset": dataset_name,
                    "output_type": output_type,
                }
    return artifact_index

def write_artifact_manifest():
    artifact_index = build_publishable_artifact_index()
    artifacts = []
    for filename in sorted(os.listdir(NORMALIZED_DIR)):
        if not filename.endswith(PUBLISHABLE_ARTIFACT_SUFFIXES):
            continue
        path = os.path.join(NORMALIZED_DIR, filename)
        if not os.path.isfile(path):
            continue
        relative_path = f"data/normalized/{filename}"
        artifact_metadata = artifact_index.get(relative_path, {})
        artifacts.append(
            {
                "path": relative_path,
                "dataset": artifact_metadata.get("dataset"),
                "output_type": artifact_metadata.get("output_type"),
                "size_bytes": os.path.getsize(path),
                "sha256": compute_sha256(path),
            }
        )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    output_path = os.path.join(NORMALIZED_DIR, "artifact_manifest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return output_path

def derive_geography_layers(df_comunas):
    df_regiones = (
        df_comunas
        .select(["codigo_region", "nombre_region"])
        .unique()
        .sort("codigo_region")
    )
    df_provincias = (
        df_comunas
        .select(["codigo_region", "nombre_region", "codigo_provincia", "nombre_provincia"])
        .unique()
        .sort(["codigo_region", "codigo_provincia"])
    )
    return df_regiones, df_provincias

def build_duckdb(df_regiones, df_provincias, df_comunas, df_indicadores, output_path):
    print(f"Compilando base de datos DuckDB en: {output_path}")
    # Si la base de datos ya existe, la eliminamos para reconstruirla limpia
    if os.path.exists(output_path):
        os.remove(output_path)
        
    con = duckdb.connect(output_path)
    try:
        # Registrar los DataFrames de Polars como vistas temporales en DuckDB
        con.register("df_regiones_view", df_regiones)
        con.register("df_provincias_view", df_provincias)
        con.register("df_comunas_view", df_comunas)
        con.register("df_indicadores_view", df_indicadores)
        
        # Crear tablas físicas en DuckDB
        con.execute("CREATE TABLE regiones AS SELECT * FROM df_regiones_view")
        con.execute("CREATE TABLE provincias AS SELECT * FROM df_provincias_view")
        con.execute("CREATE TABLE comunas AS SELECT * FROM df_comunas_view")
        con.execute("CREATE TABLE indicadores AS SELECT * FROM df_indicadores_view")
        
        # Agregar índices básicos para mejorar rendimiento en queries
        con.execute("CREATE UNIQUE INDEX idx_region_code ON regiones (codigo_region)")
        con.execute("CREATE UNIQUE INDEX idx_provincia_code ON provincias (codigo_provincia)")
        con.execute("CREATE UNIQUE INDEX idx_comuna_code ON comunas (codigo_comuna)")
        con.execute("CREATE INDEX idx_indicador_date ON indicadores (fecha, codigo_indicador)")
        
        print("Tablas e índices creados con éxito en DuckDB.")
    finally:
        con.close()

def build_sqlite(df_regiones, df_provincias, df_comunas, df_indicadores, output_path):
    print(f"Compilando base de datos SQLite en: {output_path}")
    if os.path.exists(output_path):
        os.remove(output_path)
        
    # Convertimos a Pandas para inserción rápida con to_sql de pandas
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    
    # SQLite no maneja Date de forma nativa como tipo fecha real (los guarda como string ISO)
    # Por lo tanto, convertimos las fechas a string ISO antes de guardar
    df_indicadores_pd["fecha"] = df_indicadores_pd["fecha"].astype(str)
    
    conn = sqlite3.connect(output_path)
    try:
        df_regiones_pd.to_sql("regiones", conn, index=False, if_exists="replace")
        df_provincias_pd.to_sql("provincias", conn, index=False, if_exists="replace")
        df_comunas_pd.to_sql("comunas", conn, index=False, if_exists="replace")
        df_indicadores_pd.to_sql("indicadores", conn, index=False, if_exists="replace")
        
        # Crear índices en SQLite
        cursor = conn.cursor()
        cursor.execute("CREATE UNIQUE INDEX idx_lite_region ON regiones (codigo_region)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_provincia ON provincias (codigo_provincia)")
        cursor.execute("CREATE UNIQUE INDEX idx_lite_comuna ON comunas (codigo_comuna)")
        cursor.execute("CREATE INDEX idx_lite_indicador ON indicadores (fecha, codigo_indicador)")
        conn.commit()
        print("Tablas e índices creados con éxito en SQLite.")
    finally:
        conn.close()

def build_excel(df_regiones, df_provincias, df_comunas, df_indicadores, output_path):
    print(f"Generando archivo Excel consolidado para no técnicos en: {output_path}")
    # Convertir a Pandas para exportar de forma robusta con XlsxWriter
    df_regiones_pd = df_regiones.to_pandas()
    df_provincias_pd = df_provincias.to_pandas()
    df_comunas_pd = df_comunas.to_pandas()
    df_indicadores_pd = df_indicadores.to_pandas()
    
    # Limpieza visual y formateo para Excel
    # En Excel, queremos que el Código Comuna siga siendo un string para que no se pierdan los ceros iniciales
    # XlsxWriter nos permite definir formatos específicos por columna
    with pd_excel_writer(output_path) as writer:
        df_regiones_pd.to_excel(writer, sheet_name="Regiones", index=False)
        df_provincias_pd.to_excel(writer, sheet_name="Provincias", index=False)
        df_comunas_pd.to_excel(writer, sheet_name="Comunas y Regiones", index=False)
        df_indicadores_pd.to_excel(writer, sheet_name="Indicadores Diarios", index=False)
        
        # Acceder a los objetos workbook y worksheet para aplicar formato estético
        worksheet_regiones = writer.sheets["Regiones"]
        worksheet_provincias = writer.sheets["Provincias"]
        workbook  = writer.book
        worksheet_comunas = writer.sheets["Comunas y Regiones"]
        worksheet_indicadores = writer.sheets["Indicadores Diarios"]
        
        # Formato de texto para el código comunal para prevenir pérdida de ceros
        text_format = workbook.add_format({'num_format': '@'})
        worksheet_regiones.set_column('A:A', 12, text_format)
        worksheet_provincias.set_column('A:A', 12, text_format)
        worksheet_provincias.set_column('C:C', 15, text_format)
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

def build_flat_files(df_regiones, df_provincias, df_comunas, df_indicadores):
    import json
    
    # Generamos archivos Parquet
    regiones_parquet = os.path.join(NORMALIZED_DIR, "regiones.parquet")
    provincias_parquet = os.path.join(NORMALIZED_DIR, "provincias.parquet")
    comunas_parquet = os.path.join(NORMALIZED_DIR, "comunas.parquet")
    indicadores_parquet = os.path.join(NORMALIZED_DIR, "indicadores.parquet")
    
    df_regiones.write_parquet(regiones_parquet)
    df_provincias.write_parquet(provincias_parquet)
    df_comunas.write_parquet(comunas_parquet)
    df_indicadores.write_parquet(indicadores_parquet)
    print(f"Archivos Parquet exportados a: {NORMALIZED_DIR}")
    
    # Generamos los endpoints JSON simulados
    regiones_json = os.path.join(NORMALIZED_DIR, "regiones.json")
    provincias_json = os.path.join(NORMALIZED_DIR, "provincias.json")
    comunas_json = os.path.join(NORMALIZED_DIR, "comunas.json")
    indicadores_json = os.path.join(NORMALIZED_DIR, "indicadores_hoy.json")
    
    # Para JSON estáticos orientados a frontend, exportamos como lista de diccionarios
    # SQLite/DuckDB maneja fechas como objetos datetime.date, por lo que convertimos a str para serialización JSON
    df_indicadores_serializable = df_indicadores.with_columns(
        pl.col("fecha").cast(pl.String)
    )
    
    with open(regiones_json, "w", encoding="utf-8") as f:
        json.dump(df_regiones.to_dicts(), f, ensure_ascii=False, indent=2)

    with open(provincias_json, "w", encoding="utf-8") as f:
        json.dump(df_provincias.to_dicts(), f, ensure_ascii=False, indent=2)

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

    comunas_metadata = load_metadata(COMUNAS_METADATA_PATH)
    indicadores_metadata = load_metadata(INDICADORES_METADATA_PATH)
        
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
    df_regiones, df_provincias = derive_geography_layers(df_comunas)

    validations = {
        "regiones": validate_regiones(df_regiones),
        "provincias": validate_provincias(df_provincias),
        "comunas": validate_comunas(df_comunas, comunas_metadata),
        "indicadores": validate_indicadores(df_indicadores, indicadores_metadata),
    }

    failed_validations = [
        result["dataset"] for result in validations.values() if result["status"] == "error"
    ]
    if failed_validations:
        print(f"Error: Validaciones fallidas para {', '.join(failed_validations)}.")
        for result in validations.values():
            for error in result["errors"]:
                print(f" - {result['dataset']}: {error}")
        return
    
    # Compilar entregables
    build_duckdb(df_regiones, df_provincias, df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data.duckdb"))
    build_sqlite(df_regiones, df_provincias, df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data.db"))
    build_excel(df_regiones, df_provincias, df_comunas, df_indicadores, os.path.join(NORMALIZED_DIR, "chile_data_latest.xlsx"))
    build_flat_files(df_regiones, df_provincias, df_comunas, df_indicadores)
    dataset_metadata = {
        "regiones": {
            **comunas_metadata,
            "dataset": "regiones",
            "record_count": df_regiones.height,
            "fields": df_regiones.columns,
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["regiones"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "provincias": {
            **comunas_metadata,
            "dataset": "provincias",
            "record_count": df_provincias.height,
            "fields": df_provincias.columns,
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["provincias"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "comunas": {
            **comunas_metadata,
            "freshness": build_freshness(
                comunas_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["comunas"]["freshness_policy"]["max_age_hours"],
            ),
        },
        "indicadores": {
            **indicadores_metadata,
            "freshness": build_freshness(
                indicadores_metadata.get("refreshed_at_utc"),
                DATASET_CATALOG_CONFIG["indicadores"]["freshness_policy"]["max_age_hours"],
            ),
        },
    }
    validations_with_freshness = {
        dataset_name: {
            **validation,
            "freshness_status": dataset_metadata[dataset_name]["freshness"]["status"],
            "freshness_age_hours": dataset_metadata[dataset_name]["freshness"]["age_hours"],
        }
        for dataset_name, validation in validations.items()
    }
    metadata_output = write_pipeline_metadata(
        dataset_metadata,
        validations_with_freshness,
    )
    with open(metadata_output, "r", encoding="utf-8") as f:
        pipeline_metadata = json.load(f)
    write_status_markdown_file(pipeline_metadata)
    catalog_output = write_dataset_catalog(pipeline_metadata)
    with open(catalog_output, "r", encoding="utf-8") as f:
        dataset_catalog = json.load(f)
    write_dataset_catalog_markdown_file(dataset_catalog)
    artifact_manifest_output = write_artifact_manifest()
    print(f"Metadata y validaciones exportadas a: {metadata_output}")
    print(f"Catalogo de datasets exportado a: {catalog_output}")
    print(f"Manifest de artefactos exportado a: {artifact_manifest_output}")
    
    print("\n--- Compilación del Sprint 0 completada con éxito ---")

if __name__ == "__main__":
    main()
