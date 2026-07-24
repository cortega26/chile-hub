"""Construye el artefacto GeoParquet de `geometria_comunal` (Plan 053).

Script standalone -- **NO** forma parte de `make build`/`src/build_dev_db.py`.
`geometria_comunal` es un dataset carril `candidate` / cadencia `bajo_demanda`
(igual que `delincuencia_comunal` y `autoridades_locales`): su extractor no
corre en `make extract`, así que no participa del build diario ni del
`dataset_catalog.json` generado. Ver `docs/adr/ADR-012-geometria-comunal-y-reverse-geocoding.md`
para el razonamiento completo de esta separación.

Uso:
    python scripts/build_geometria_comunal.py              # extrae + valida + escribe
    python scripts/build_geometria_comunal.py --skip-fetch  # reusa staging existente
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import polars as pl  # noqa: E402

from src.builders.geo import write_geometria_comunal_parquet  # noqa: E402
from src.extractors.geometria_comunal_extractor import (  # noqa: E402
    STAGING_CSV_PATH,
    process_geometria_comunal,
)
from src.validation import validate_geometria_comunal  # noqa: E402

NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
OUTPUT_PATH = NORMALIZED_DIR / "geometria_comunal.parquet"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="No corre el extractor; reusa data/staging/geometria_comunal.csv existente.",
    )
    args = parser.parse_args()

    if not args.skip_fetch:
        result = process_geometria_comunal()
        if not result:
            raise SystemExit("geometria_comunal: extracción vacía, no se genera artefacto.")

    if not STAGING_CSV_PATH.exists():
        raise SystemExit(
            f"geometria_comunal: no existe {STAGING_CSV_PATH}. "
            "Corre sin --skip-fetch o ejecuta el extractor primero."
        )

    df = pl.read_csv(
        STAGING_CSV_PATH,
        schema_overrides={"codigo_region": pl.String, "codigo_comuna": pl.String},
    )

    validation = validate_geometria_comunal(df)
    for warning in validation["warnings"]:
        print(f"WARNING: geometria_comunal: {warning}")
    if validation["status"] == "error":
        raise SystemExit(
            "geometria_comunal: validación fallida -- " + "; ".join(validation["errors"])
        )

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    write_geometria_comunal_parquet(df, str(OUTPUT_PATH))
    print(f"geometria_comunal: artefacto escrito en {OUTPUT_PATH} ({df.height} comunas)")


if __name__ == "__main__":
    main()
