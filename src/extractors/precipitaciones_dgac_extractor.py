"""Publica la serie DGAC validada como snapshot canónico de staging.

El parser y la proveniencia son exactamente los del laboratorio histórico; no
hay segunda implementación ni fallback con datos de muestra.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.research_dgac_precipitaciones import harvest

DEFAULT_OUTPUT = ROOT_DIR / "data" / "staging" / "precipitaciones_dgac.csv"
SOURCE_URL = "https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil"


def extract(output: Path = DEFAULT_OUTPUT) -> dict:
    """Descarga, verifica y publica un snapshot de origen real o aborta."""
    metadata = harvest(output)
    if metadata["months"] != 143 or metadata["record_count"] < 120_000:
        raise RuntimeError("DGAC: cobertura histórica insuficiente para publicación")
    canonical = {
        **metadata,
        "publication_track": "stable_publishable",
        "source_name": "DGAC — datos.gob.cl",
        "source_url": SOURCE_URL,
        "source_detail": "CKAN: 143 archivos-mes, 2013–2026, licencias CC BY/CC0",
        "source_mode": "live",
        "refreshed_at_utc": metadata["generated_at_utc"],
        "fields": list(metadata["fields"]),
        "reuse_policy": {
            "status": "open-attribution",
            "license": "CC BY + CC0 (por archivo)",
            "license_url": SOURCE_URL,
            "attribution_required": True,
            "redistribution_ok": True,
            "summary": "Solo fuentes cc-by y cc-zero; excluye CC-NC y error DGAC 2017-01.",
        },
    }
    # Metadata del harvest ya existe; reemplazo atómico del sidecar.
    metadata_path = output.with_suffix(".metadata.json")
    tmp_path = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp_path.replace(metadata_path)
    return canonical


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metadata = extract(args.output)
    print(
        json.dumps(
            {
                "dataset": metadata["dataset"],
                "record_count": metadata["record_count"],
                "station_count": metadata["station_count"],
                "months": metadata["months"],
                "sha256": metadata["sha256"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
