"""Extractor para la asociacion de comunas a distritos y circunscripciones electorales."""

import datetime
import json
import os
import sys
from pathlib import Path

import polars as pl

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from src.extractors.base import (
        BaseExtractor,
        ensure_staging_directories,
        write_staging_metadata,
    )
except ModuleNotFoundError:
    from base import BaseExtractor, ensure_staging_directories, write_staging_metadata

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
STAGING_CSV_PATH = os.path.join(STAGING_DIR, "distritos_electorales.csv")
METADATA_PATH = os.path.join(STAGING_DIR, "distritos_electorales.metadata.json")

REUSE_POLICY = {
    "status": "open-attribution",
    "license": "CC0",
    "license_url": "http://www.opendefinition.org/licenses/cc-zero",
    "attribution_required": False,
    "redistribution_ok": True,
    "summary": "Asociación comunal a distritos y circunscripciones electorales basada en Ley N° 20.840.",
}

REGION_TO_CIRCUNSCRIPCION = {
    "15": "1",
    "01": "2",
    "02": "3",
    "03": "4",
    "04": "5",
    "05": "6",
    "13": "7",
    "06": "8",
    "07": "9",
    "08": "10",
    "09": "11",
    "14": "12",
    "10": "13",
    "11": "14",
    "12": "15",
    "16": "16",
}

# Subdivisions clean names for multi-district regions
dist_7_names = {
    "algarrobo",
    "cartagena",
    "casablanca",
    "concon",
    "el quisco",
    "el tabo",
    "isla de pascua",
    "juan fernandez",
    "san antonio",
    "santo domingo",
    "valparaiso",
    "vina del mar",
}

dist_16_names = {
    "la estrella",
    "litueche",
    "marchigue",
    "navidad",
    "paredones",
    "pichilemu",
    "chepica",
    "chimbarongo",
    "lolol",
    "nancagua",
    "palmilla",
    "peralillo",
    "placilla",
    "pumanque",
    "san fernando",
    "santa cruz",
    "las cabras",
    "peumo",
    "pichidegua",
    "san vicente",
}

dist_18_names = {
    "linares",
    "colbun",
    "longavi",
    "parral",
    "retiro",
    "san javier",
    "villa alegre",
    "yerbas buenas",
    "cauquenes",
    "chanco",
    "pelluhue",
}

dist_21_names = {
    "arauco",
    "canete",
    "contulmo",
    "curanilahue",
    "lebu",
    "los alamos",
    "tirua",
    "alto biobio",
    "antuco",
    "cabrero",
    "laja",
    "los angeles",
    "mulchen",
    "nacimiento",
    "negrete",
    "quilaco",
    "quilleco",
    "san rosendo",
    "santa barbara",
    "tucapel",
    "yumbel",
    "santa juana",
}

dist_22_names = {
    "angol",
    "collipulli",
    "curacautin",
    "ercilla",
    "lonquimay",
    "los sauces",
    "lumaco",
    "puren",
    "renaico",
    "traiguen",
    "victoria",
    "galvarino",
    "lautaro",
    "melipeuco",
    "perquenco",
    "vilcun",
}

dist_25_names = {
    "fresia",
    "frutillar",
    "llanquihue",
    "los muermos",
    "osorno",
    "puerto octay",
    "puerto varas",
    "purranque",
    "puyehue",
    "rio negro",
    "san juan de la costa",
    "san pablo",
}

rm_districts = {
    "8": {
        "cerrillos",
        "estacion central",
        "lampa",
        "maipu",
        "pudahuel",
        "quilicura",
        "colina",
        "tiltil",
    },
    "9": {
        "cerro navia",
        "conchali",
        "huechuraba",
        "independencia",
        "lo prado",
        "quinta normal",
        "recoleta",
        "renca",
    },
    "10": {"la granja", "macul", "nunoa", "providencia", "san joaquin", "santiago"},
    "11": {"la reina", "las condes", "lo barnechea", "penalolen", "vitacura"},
    "12": {"la pintana", "puente alto", "pirque", "san jose de maipo", "la florida"},
    "13": {
        "el bosque",
        "la cisterna",
        "lo espejo",
        "pedro aguirre cerda",
        "san miguel",
        "san ramon",
    },
    "14": {
        "alhue",
        "buin",
        "calera de tango",
        "curacaví",
        "el monte",
        "isla de maipo",
        "maria pinto",
        "melipilla",
        "padre hurtado",
        "paine",
        "penaflor",
        "san bernardo",
        "san pedro",
        "talagante",
        "curacavi",
    },
}


def build_electoral_df() -> pl.DataFrame:
    comunas_path = Path(STAGING_DIR) / "comunas.csv"
    if not comunas_path.exists():
        raise FileNotFoundError(
            f"No se encuentra {comunas_path}. Corre el subdere_extractor primero."
        )

    comunas = pl.read_csv(
        comunas_path, schema_overrides={"codigo_region": pl.String, "codigo_comuna": pl.String}
    )

    rows = []
    for r in comunas.iter_rows(named=True):
        cod_reg = r["codigo_region"]
        clean_name = r["nombre_comuna_clean"]

        # Circunscripcion
        circ = REGION_TO_CIRCUNSCRIPCION.get(cod_reg, "unknown")

        # District
        dist = "unknown"
        if cod_reg == "15":
            dist = "1"
        elif cod_reg == "01":
            dist = "2"
        elif cod_reg == "02":
            dist = "3"
        elif cod_reg == "03":
            dist = "4"
        elif cod_reg == "04":
            dist = "5"
        elif cod_reg == "16":
            dist = "19"
        elif cod_reg == "14":
            dist = "24"
        elif cod_reg == "11":
            dist = "27"
        elif cod_reg == "12":
            dist = "28"
        elif cod_reg == "05":
            dist = "7" if clean_name in dist_7_names else "6"
        elif cod_reg == "06":
            dist = "16" if clean_name in dist_16_names else "15"
        elif cod_reg == "07":
            dist = "18" if clean_name in dist_18_names else "17"
        elif cod_reg == "08":
            dist = "21" if clean_name in dist_21_names else "20"
        elif cod_reg == "09":
            dist = "22" if clean_name in dist_22_names else "23"
        elif cod_reg == "10":
            dist = "25" if clean_name in dist_25_names else "26"
        elif cod_reg == "13":
            for d, names in rm_districts.items():
                if clean_name in names:
                    dist = d
                    break

        rows.append(
            {
                "codigo_comuna": r["codigo_comuna"],
                "nombre_comuna": r["nombre_comuna"],
                "distrito_electoral": dist,
                "circunscripcion_senatorial": circ,
            }
        )

    df = pl.DataFrame(rows)

    unknown_dists = df.filter(pl.col("distrito_electoral") == "unknown")
    if not unknown_dists.is_empty():
        raise ValueError(f"Comunas sin distrito electoral asignado: {unknown_dists}")

    unknown_circs = df.filter(pl.col("circunscripcion_senatorial") == "unknown")
    if not unknown_circs.is_empty():
        raise ValueError(f"Comunas sin circunscripcion senatorial asignada: {unknown_circs}")

    return df.sort("codigo_comuna")


def process_electoral() -> str:
    ensure_staging_directories()

    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = Path(RAW_DIR) / f"bcn_electoral_mapping_{stamp}.json"

    df = build_electoral_df()

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(df.to_dicts(), f, ensure_ascii=False, indent=2)

    validation = ElectoralExtractor().validate(df, {"source_mode": "live"})
    if validation["status"] == "error":
        raise SystemExit(f"Validacion fallida: {validation['errors']}")

    metadata = {
        "dataset": "distritos_electorales",
        "source_name": "BCN / Biblioteca del Congreso Nacional de Chile",
        "source_url": "https://www.bcn.cl/siit/observatorio/ley20840",
        "source_mode": "live",
        "source_detail": "bcn_electoral_mapping_generated",
        "refreshed_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "record_count": df.height,
        "fields": df.columns,
        "notes": [],
        "reuse_policy": REUSE_POLICY,
    }

    ElectoralExtractor().write_staging(df, metadata)
    print(f"Mapeo electoral guardado en: {STAGING_CSV_PATH} ({df.height} registros)")
    return STAGING_CSV_PATH


class ElectoralExtractor(BaseExtractor):
    @property
    def dataset_name(self) -> str:
        return "distritos_electorales"

    def fetch(self, **kwargs):
        return build_electoral_df()

    def normalize(self, raw_data):
        return raw_data

    def validate(self, df, metadata: dict) -> dict:
        from src.validation import validate_distritos_electorales

        return validate_distritos_electorales(df, metadata)

    def write_staging(self, df, metadata: dict) -> Path:
        ensure_staging_directories()
        output = Path(STAGING_CSV_PATH)
        df.write_csv(output)
        write_staging_metadata(METADATA_PATH, metadata)
        return output


if __name__ == "__main__":
    process_electoral()
