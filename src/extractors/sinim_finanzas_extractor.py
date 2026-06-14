"""Extractor opt-in de finanzas SINIM; nunca se publica en el bundle."""

import argparse
import datetime
import json
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SOURCE_URL = "https://datos.sinim.gov.cl/datos_municipales.php"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-url",
        required=True,
        help="URL directa de una exportacion CSV/XLSX autorizada por SINIM",
    )
    args = parser.parse_args()
    if args.source_url == SOURCE_URL:
        raise SystemExit("Se requiere una URL directa de exportacion, no una pagina HTML.")
    response = requests.get(args.source_url, timeout=60)
    response.raise_for_status()
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = DATA_DIR / "raw" / f"sinim_finanzas_municipales_{stamp}"
    raw_path.write_bytes(response.content)
    metadata = {
        "dataset": "finanzas_municipales",
        "source_name": "SINIM - SUBDERE",
        "source_url": args.source_url,
        "source_mode": "live",
        "source_detail": "user_authorized_direct_export",
        "refreshed_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "record_count": None,
        "fields": [],
        "notes": ["opt_in_only", "excluded_from_public_bundle"],
        "reuse_policy": {
            "status": "restricted",
            "license": "Uso no comercial con atribucion",
            "license_url": "https://datos.sinim.gov.cl/",
            "attribution_required": True,
            "redistribution_ok": False,
            "summary": "No redistribuir en el bundle publico sin permiso expreso.",
        },
    }
    path = DATA_DIR / "staging" / "finanzas_municipales.metadata.json"
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot restringido guardado en {raw_path}; no se genero artefacto publicable.")


if __name__ == "__main__":
    main()
