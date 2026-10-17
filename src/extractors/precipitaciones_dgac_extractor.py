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
    temp_output = output.with_name(output.stem + ".incomplete.csv")
    metadata = harvest(temp_output)
    if metadata["months"] != 143 or metadata["record_count"] < 120_000:
        temp_output.unlink(missing_ok=True)
        temp_output.with_suffix(".metadata.json").unlink(missing_ok=True)
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
    temp_meta = temp_output.with_suffix(".metadata.json")
    temp_meta.write_text(
        json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Sólo después de completar toda la cosecha y sus gates básicos:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output.replace(output)
    temp_meta.replace(output.with_suffix(".metadata.json"))
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
