import polars as pl

EXPECTED_INDICATOR_CODES = {"uf", "dolar", "euro", "utm", "ipc"}
FALLBACK_COMUNAS_COUNT = 18
EXPECTED_LIVE_COMUNAS_COUNT = 346


def validate_comunas(df_comunas, metadata):
    errors = []
    warnings = []
    row_count = df_comunas.height
    duplicate_count = row_count - df_comunas["codigo_comuna"].n_unique()

    if duplicate_count > 0:
        errors.append(f"codigo_comuna must be unique, found {duplicate_count} duplicate rows")

    if (
        metadata
        and metadata.get("source_mode") == "live"
        and row_count < EXPECTED_LIVE_COMUNAS_COUNT
    ):
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
    keys = (df_provincias["codigo_region"] + "-" + df_provincias["codigo_provincia"]).n_unique()
    if keys != df_provincias.height:
        errors.append("codigo_region + codigo_provincia must be unique")
    return {
        "dataset": "provincias",
        "status": "error" if errors else "ok",
        "record_count": df_provincias.height,
        "errors": errors,
        "warnings": [],
    }


def validate_censo_comunal(df_censo, metadata):
    errors = []
    row_count = df_censo.height
    if row_count == 0:
        errors.append("censo_comunal dataset is empty")
    if row_count != 346:
        errors.append(f"censo_comunal expected 346 communes, found {row_count}")
    if row_count - df_censo["codigo_comuna"].n_unique() > 0:
        errors.append("codigo_comuna must be unique in censo_comunal")
    age_total = sum(
        df_censo[column]
        for column in (
            "poblacion_0_14",
            "poblacion_15_29",
            "poblacion_30_44",
            "poblacion_45_64",
            "poblacion_65_mas",
        )
    )
    if df_censo.filter(age_total != df_censo["poblacion_censada"]).height > 0:
        errors.append("age bands must sum to poblacion_censada")
    return {
        "dataset": "censo_comunal",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": [],
    }


def validate_establecimientos_salud(df_salud, metadata, valid_commune_codes=None):
    errors = []
    row_count = df_salud.height
    if row_count == 0:
        errors.append("establecimientos_salud dataset is empty")
    if row_count - df_salud["codigo_establecimiento"].n_unique() > 0:
        errors.append("codigo_establecimiento must be unique")
    invalid_codes = df_salud.filter(pl.col("codigo_comuna").str.len_chars() != 5).height
    if invalid_codes:
        errors.append(f"found {invalid_codes} invalid codigo_comuna values")
    if valid_commune_codes is not None:
        unknown = set(df_salud["codigo_comuna"].drop_nulls().to_list()) - set(valid_commune_codes)
        if unknown:
            errors.append(
                f"health facilities reference unknown communes: {', '.join(sorted(unknown))}"
            )
    return {
        "dataset": "establecimientos_salud",
        "status": "error" if errors else "ok",
        "record_count": row_count,
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
        warnings.append(
            "indicadores source_mode is fallback; values are synthetic development data"
        )
    if metadata and metadata.get("raw_recoveries"):
        warnings.append(
            "indicadores live refresh reused raw snapshots for: "
            + ", ".join(metadata["raw_recoveries"])
        )
    if metadata and metadata.get("preserved_existing_pairs"):
        warnings.append(
            "indicadores live refresh preserved previous staging rows for: "
            + ", ".join(metadata["preserved_existing_pairs"])
        )
    if metadata and metadata.get("empty_live_pairs"):
        warnings.append(
            "indicadores live refresh returned empty series for: "
            + ", ".join(metadata["empty_live_pairs"])
        )
    if metadata and metadata.get("published_backfills"):
        warnings.append(
            "indicadores live refresh reused last published artifact for missing codes: "
            + ", ".join(metadata["published_backfills"])
        )

    return {
        "dataset": "indicadores",
        "status": "error" if errors else "ok",
        "record_count": row_count,
        "errors": errors,
        "warnings": warnings,
        "indicator_codes": sorted(codes),
    }
