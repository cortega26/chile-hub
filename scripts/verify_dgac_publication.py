"""Verifica una cosecha DGAC y prepara CSV/Parquet para su distribución.

No depende de los otros 21 datasets. Rechaza licencias incompatibles, cobertura
truncada, claves duplicadas y discrepancias con el SHA de la cosecha.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chile_hub.contracts import verify_dataset_contract
from src.validation import validate_precipitaciones_dgac

SCHEMA = {
    "id_estacion": pl.String,
    "fecha": pl.String,
    "latitud_dms": pl.String,
    "altitud_m": pl.Float64,
    "precipitacion_mm": pl.Float64,
}


def verify_and_write(csv_path: Path, metadata_path: Path, out_dir: Path) -> dict:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    source_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if metadata.get("sha256") != source_sha:
        raise ValueError("SHA-256 de CSV no coincide con metadata DGAC")
    frame = pl.read_csv(csv_path, schema_overrides=SCHEMA)
    validated = validate_precipitaciones_dgac(frame, metadata)
    if validated["status"] != "ok":
        raise ValueError(f"Validador DGAC: {validated['errors']}")
    contract = json.loads(
        (ROOT / "contracts" / "datasets" / "precipitaciones_dgac.schema.json").read_text(
            encoding="utf-8"
        )
    )
    result = verify_dataset_contract("precipitaciones_dgac", contract, frame)
    if result["status"] != "ok":
        raise ValueError(f"Contrato DGAC: {result['errors']}")
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "precipitaciones_dgac.parquet"
    temp = parquet_path.with_suffix(".parquet.tmp")
    frame.write_parquet(temp, compression="zstd")
    temp.replace(parquet_path)
    shutil.copy2(csv_path, out_dir / "precipitaciones_dgac.csv")
    shutil.copy2(metadata_path, out_dir / "precipitaciones_dgac.metadata.json")
    return {
        "dataset": "precipitaciones_dgac",
        "rows": frame.height,
        "stations": frame["id_estacion"].n_unique(),
        "months": metadata["months"],
        "csv_sha256": source_sha,
        "parquet_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "data/staging/precipitaciones_dgac.csv")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=ROOT / "data/staging/precipitaciones_dgac.metadata.json",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/normalized")
    args = parser.parse_args()
    print(json.dumps(verify_and_write(args.csv, args.metadata, args.out_dir)))


if __name__ == "__main__":
    main()
