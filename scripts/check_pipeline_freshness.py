"""SLO de frescura (Plan 109): avisa si `pipeline_metadata.json` está viejo.

`make doctor` lo invoca para detectar schedules rotos: si el artefacto
publicado lleva más de 48 h sin regenerarse, imprime un warning que apunta al
issue "Schedule diario roto" (job `notify-schedule-failure` de
`pipeline-check.yml`). No falla (exit 0): un clon sin build o una fuente caída
no deben romper el chequeo local — el gate duro por dataset vive en
`verify_pipeline.py --profile publication`.

Uso: python scripts/check_pipeline_freshness.py
"""

import datetime
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT_DIR / "data" / "normalized" / "pipeline_metadata.json"
MAX_AGE_HOURS = 48.0


def age_hours(generated_at_utc: str, now: datetime.datetime | None = None) -> float:
    """Horas transcurridas desde `generated_at_utc` (ISO 8601 con offset)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    generated = datetime.datetime.fromisoformat(generated_at_utc)
    return (now - generated).total_seconds() / 3600


def check(path: Path | None = None, now: datetime.datetime | None = None) -> int:
    """Imprime el estado de frescura y retorna 0 siempre (aviso, no gate)."""
    path = path or METADATA_PATH
    if not path.exists():
        print(f"Frescura: WARNING: {path} no existe; corre `make build` para regenerarlo.")
        return 0
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        hours = age_hours(metadata["generated_at_utc"], now=now)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"Frescura: WARNING: {path} ilegible ({exc}); corre `make build`.")
        return 0
    if hours > MAX_AGE_HOURS:
        print(
            f"Frescura: WARNING: pipeline_metadata.json tiene {hours:.1f} h "
            f"(> {MAX_AGE_HOURS:.0f} h) — el schedule diario pudo haber fallado; "
            "revisa el issue 'Schedule diario roto'."
        )
    else:
        print(f"Frescura: OK — pipeline_metadata.json de hace {hours:.1f} h.")
    return 0


def main() -> int:
    return check()


if __name__ == "__main__":
    sys.exit(main())
