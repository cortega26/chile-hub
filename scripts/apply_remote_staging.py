"""Aplica el staging extraído desde la VM remota (plan 153).

Cuatro fuentes oficiales bloquean el egress de GitHub Actions pero responden
desde la VM de OCI (Santiago). Esa VM escribe un espejo de staging
(`chile-hub-remote-staging`) y el pipeline lo copia aquí antes del build.

Defensas, porque el espejo es un artefacto externo:

- **Allowlist fija.** Solo se copian los datasets que se delegan; un nombre
  nuevo en el espejo no puede inyectar archivos en `data/staging/`.
- **Solo `live`/`monthly`.** Un fallback nunca reemplaza el último dato bueno
  que ya tenga el checkout.
- **Conteo consistente.** `record_count` del metadata debe coincidir con las
  filas reales del CSV; una pareja desincronizada se descarta.

Si algo no cuadra, se omite y el build sigue con la extracción local: el gate de
publicación decide después (retención), como hasta ahora.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

# Datasets delegados a la VM. Ampliar esta lista exige evidencia de que la
# fuente también falla desde GitHub (o que su calidad mejora allí).
REMOTE_STAGING_DATASETS = frozenset(
    {
        "autoridades_electas",
        "establecimientos_educacionales",
        "pobreza_comunal",
        "resultados_educacionales",
    }
)

ACCEPTED_MODES = frozenset({"live", "monthly"})


def _row_count(path: Path) -> int:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)  # cabecera
        return sum(1 for _ in reader)


def apply_remote_staging(remote_dir: Path, staging_dir: Path) -> tuple[list[str], list[str]]:
    """Copia lo aplicable y devuelve `(aplicados, omitidos_con_motivo)`."""
    applied: list[str] = []
    skipped: list[str] = []
    source = remote_dir / "data" / "staging"

    for name in sorted(REMOTE_STAGING_DATASETS):
        meta_path = source / f"{name}.metadata.json"
        csv_path = source / f"{name}.csv"
        if not meta_path.is_file() or not csv_path.is_file():
            skipped.append(f"{name}: falta metadata o csv en el espejo")
            continue
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            skipped.append(f"{name}: metadata ilegible")
            continue
        mode = metadata.get("source_mode")
        if mode not in ACCEPTED_MODES:
            skipped.append(f"{name}: source_mode={mode}")
            continue
        expected = metadata.get("record_count")
        if not isinstance(expected, int) or expected <= 0:
            skipped.append(f"{name}: record_count inválido ({expected!r})")
            continue
        actual = _row_count(csv_path)
        if actual != expected:
            skipped.append(f"{name}: filas {actual} != record_count {expected}")
            continue
        shutil.copy2(csv_path, staging_dir / csv_path.name)
        shutil.copy2(meta_path, staging_dir / meta_path.name)
        applied.append(name)

    return applied, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("remote_dir", help="Checkout del espejo remoto")
    parser.add_argument("--staging-dir", default="data/staging")
    parser.add_argument(
        "--fail-if-empty",
        action="store_true",
        help="Sale 1 si no se aplicó ningún dataset (para diagnóstico explícito)",
    )
    args = parser.parse_args(argv)

    applied, skipped = apply_remote_staging(Path(args.remote_dir), Path(args.staging_dir))

    for item in skipped:
        print(f"SKIP {item}")
    print(f"Aplicados desde el espejo remoto ({len(applied)}): {', '.join(applied) or 'ninguno'}")
    if not applied:
        print("AVISO: el espejo no aportó datasets; se usa la extracción local.")
        if args.fail_if_empty:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
