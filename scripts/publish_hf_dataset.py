"""Publica el bundle publicable de chile-hub como dataset en Hugging Face Hub.

Canal de *descubrimiento* (complementa el Plan 051 = capa de acceso HTTP
estática). Copia los Parquet de las capas publicables (carril
`stable_publishable` en `data/source_registry.json`, `outputs` presente y
`reuse_policy.redistribution_ok`) más los JSON de catálogo a un directorio
de staging, genera un README desde la plantilla de `docs/hf/dataset-card.md`,
y sube ese directorio a `huggingface_hub`. El carril `candidate` queda
excluido por `publication_track` del registry (Plan 070: antes se infería de
`outputs`, asunción que el build violaba — candidate con outputs como perfil
y consumo llegaron al mirror).

`huggingface_hub` se importa de forma perezosa: el script corre en modo
`--dry-run` sin la dependencia instalada; sólo la necesita el modo de subida
real (instalado ad-hoc en el job de CI, nunca en pyproject.toml).
"""

import argparse
import shutil
import sys
from pathlib import Path

import tomllib

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CATALOG_PATH = ROOT_DIR / "data" / "dataset_catalog_config.json"
SOURCE_REGISTRY_PATH = ROOT_DIR / "data" / "source_registry.json"
CARD_TEMPLATE_PATH = ROOT_DIR / "docs" / "hf" / "dataset-card.md"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"

# JSON de catálogo que acompañan a los Parquet (mismo set que adjunta el
# job `release` a GitHub Releases hoy, ver Current state del plan).
CATALOG_JSON_FILES = ["datapackage.json", "dataset_catalog.json", "artifact_manifest.json"]


def _read_json(path: Path) -> dict:
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_catalog() -> dict:
    return _read_json(CATALOG_PATH)


def _read_source_registry() -> dict:
    """Carril por dataset: fuente única en `data/source_registry.json`.

    El catálogo construido (`dataset_catalog_config.json`) declara `outputs`
    también para candidate (perfil_territorial_comunal, consumo_electrico —
    Plan 070): inferir el carril de `outputs` era falso y dejó que el mirror
    de HF publicara 2 capas candidate como publicables. El registry es la
    fuente de verdad del carril (AGENTS.md §1).
    """
    data = _read_json(SOURCE_REGISTRY_PATH)
    entries = data if isinstance(data, list) else list(data.values())
    return {
        entry["dataset"]: entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("dataset")
    }


def select_publishable_files() -> tuple[list[tuple[str, Path]], list[Path]]:
    """Selecciona los archivos publicables desde el catálogo y el registry.

    Sólo capas con ``publication_track == "stable_publishable"`` en
    `source_registry.json` (carril candidate/deprecated excluido por
    construcción — Plan 070), ``outputs`` truthy **y**
    ``reuse_policy.redistribution_ok is True``. Falla ruidoso si alguna capa
    publicable carece de su Parquet en disco (drift entre catálogo y build).

    Retorna ``(parquet_entries, catalog_json_files)``, donde
    ``parquet_entries`` son pares ``(nombre_dataset, ruta_parquet)`` — se
    nombran por clave de catálogo, no por el basename del archivo fuente,
    porque ``comunas_enriquecidas`` es un alias intencional que apunta al
    mismo Parquet que ``comunas`` (ver Plan 014/PERF-08): sin este renombre,
    ambas claves colapsarían al mismo archivo de destino y el mirror de HF
    tendría 18 archivos en vez de las 17 capas publicables reales.
    """
    catalog = _read_catalog()
    registry = _read_source_registry()
    parquet_entries: list[tuple[str, Path]] = []
    for name, entry in sorted(catalog.items()):
        outputs = entry.get("outputs")
        if not outputs:
            continue
        registry_entry = registry.get(name, {})
        track = registry_entry.get("publication_track")
        if track != "stable_publishable":
            # Candidate/deprecated: documentado, no es un error — el carril
            # candidate puede declarar outputs en el catálogo (Plan 070).
            print(f"  [skip] {name}: publication_track={track!r} — fuera del mirror HF.")
            continue
        if entry.get("reuse_policy", {}).get("redistribution_ok") is not True:
            raise SystemExit(
                f"ERROR: '{name}' tiene outputs pero redistribution_ok != True; "
                "no se puede publicar en Hugging Face Hub sin redistribución "
                "confirmada. Revisa data/dataset_catalog_config.json."
            )
        parquet_rel_path = outputs.get("parquet")
        if not parquet_rel_path:
            raise SystemExit(
                f"ERROR: '{name}' tiene outputs pero sin clave 'parquet'; "
                "revisa data/dataset_catalog_config.json (drift de esquema)."
            )
        parquet_path = ROOT_DIR / parquet_rel_path
        if not parquet_path.is_file():
            raise SystemExit(
                f"ERROR: '{name}' es publicable pero falta su Parquet en "
                f"{parquet_path}. Corre 'make build' primero."
            )
        parquet_entries.append((name, parquet_path))

    catalog_json_files: list[Path] = []
    for filename in CATALOG_JSON_FILES:
        path = NORMALIZED_DIR / filename
        if not path.is_file():
            raise SystemExit(f"ERROR: falta {path}. Corre 'make build' primero.")
        catalog_json_files.append(path)

    return parquet_entries, catalog_json_files


def _build_dataset_table(catalog: dict, selected_names: set[str]) -> str:
    """Tabla de la card con SOLO las capas seleccionadas para publicar."""
    rows = ["| Dataset | Filas aprox. | Licencia |", "|:---|---:|:---|"]
    for name, entry in sorted(catalog.items()):
        if name not in selected_names:
            continue
        record_count = entry.get("expected_record_count", "N/D")
        license_name = entry.get("reuse_policy", {}).get("license", "N/D")
        rows.append(f"| `{name}` | {record_count} | {license_name} |")
    return "\n".join(rows)


def _read_project_version() -> str:
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)["project"]["version"]


def build_staging_dir(
    dest: Path, parquet_entries: list[tuple[str, Path]], catalog_json_files: list[Path]
) -> None:
    """Copia los parquet bajo dest/data/ y los JSON de catálogo en dest/;
    genera dest/README.md desde la plantilla con la tabla de datasets."""
    data_dir = dest / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, path in parquet_entries:
        shutil.copy2(path, data_dir / f"{name}.parquet")
    for path in catalog_json_files:
        shutil.copy2(path, dest / path.name)

    catalog = _read_catalog()
    template = CARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    # La card se genera con el conteo y la tabla REALES de lo publicado
    # (Plan 070: antes decía 19 capas fijas y listaba candidate).
    table = _build_dataset_table(catalog, {name for name, _ in parquet_entries})
    card = template.replace("{{DATASET_TABLE}}", table)
    card = card.replace("{{DATASET_COUNT}}", str(len(parquet_entries)))
    (dest / "README.md").write_text(card, encoding="utf-8")


def _print_staging_tree(dest: Path) -> None:
    for path in sorted(dest.rglob("*")):
        if path.is_file():
            print(path.relative_to(dest))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Arma el staging y lo imprime, sin subir nada."
    )
    parser.add_argument(
        "--repo-id",
        default=None,
        help="Repo de Hugging Face Hub destino (ej. cortega26/chile-hub). "
        "Requerido si no se usa --dry-run.",
    )
    args = parser.parse_args(argv)

    parquet_entries, catalog_json_files = select_publishable_files()

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir) / "chile-hub-hf"
        build_staging_dir(staging, parquet_entries, catalog_json_files)

        if args.dry_run:
            _print_staging_tree(staging)
            return

        if not args.repo_id:
            raise SystemExit("ERROR: --repo-id es requerido fuera de --dry-run.")

        try:
            from huggingface_hub import HfApi
        except ImportError:
            raise SystemExit("ERROR: instala con: pip install huggingface_hub")

        version = _read_project_version()
        api = HfApi()
        api.create_repo(args.repo_id, repo_type="dataset", exist_ok=True)
        api.upload_folder(
            folder_path=str(staging),
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message=f"chore(data): publish chile-hub {version}",
        )
        print(f"Publicado {args.repo_id} (chile-hub {version}).")


if __name__ == "__main__":
    sys.exit(main())
