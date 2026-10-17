"""Verifica artefactos *versionados* sin confundirlos con un build nuevo.

Este gate se ejecuta en pull_request, merge_group y push. El manifest puede
representar la versión publicada previa: su ausencia de datasets recién
registrados no certifica ni bloquea la nueva publicación. En cambio comprueba
integridad física de todos sus archivos, y de la nueva fuente DGAC.
Los runs de schedule/dispatch son los únicos que emiten evidencia publication.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("data/normalized/artifact_manifest.json")
DGAC_CSV = Path("data/staging/precipitaciones_dgac.csv")
DGAC_META = Path("data/staging/precipitaciones_dgac.metadata.json")


def sha256_file(path: Path) -> str:
    """Calcula SHA-256 en streaming, sin cargar el CSV histórico en memoria."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_snapshot(root: Path = ROOT) -> dict:
    """Rechaza manifest o fuente alterados; distingue novedades sin publicar."""
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list) or manifest.get("artifact_count") != len(artifacts):
        raise ValueError("artifact_manifest.json tiene artifact_count inconsistente")

    names = set()
    verified_hashes = 0
    # Hub_bundle contiene copias de hashes del propio manifest, que a su vez
    # indexa hub_bundle. Es un grafo cíclico y el SHA embebido no puede
    # coincidir con el contenido final sin rediseñar el formato del bundle.
    # Ambos se comprueban estructuralmente, nunca se anuncian como SHA verificado.
    cyclic_paths = {MANIFEST.as_posix(), "data/normalized/hub_bundle.json"}
    for artifact in artifacts:
        path = artifact.get("path")
        if (
            not isinstance(path, str)
            or (not PurePosixPath(path).is_relative_to(PurePosixPath("data/normalized")))
            or ".." in PurePosixPath(path).parts
        ):
            raise ValueError(f"Ruta fuera de normalized en manifest: {path!r}")
        if path in names:
            raise ValueError(f"Artefacto duplicado en manifest: {path}")
        names.add(path)
        file = root / path
        if not file.is_file() or file.stat().st_size == 0:
            raise ValueError(f"Falta archivo publicado: {path}")
        if path in cyclic_paths:
            continue
        if artifact.get("size_bytes") != file.stat().st_size:
            raise ValueError(f"Tamaño de artefacto desfasado: {path}")
        if artifact.get("sha256") != sha256_file(file):
            raise ValueError(f"SHA-256 de artefacto desfasado: {path}")
        verified_hashes += 1

    metadata = json.loads((root / DGAC_META).read_text(encoding="utf-8"))
    if metadata.get("sha256") != sha256_file(root / DGAC_CSV):
        raise ValueError("Snapshot DGAC no coincide con SHA-256 de origen")
    if (
        metadata.get("months") != 143
        or metadata.get("record_count", 0) < 120_000
        or metadata.get("station_count", 0) < 20
    ):
        raise ValueError("Cobertura histórica DGAC incompleta")
    if metadata.get("source_mode") != "live":
        raise ValueError("Snapshot DGAC no corresponde a fuente oficial verificada")

    registry = json.loads((root / "data/source_registry.json").read_text(encoding="utf-8"))
    stable = {
        entry["dataset"] for entry in registry if entry["publication_track"] == "stable_publishable"
    }
    published = {entry["dataset"] for entry in artifacts if entry.get("dataset")}
    pending = sorted(stable - published)
    return {
        "manifest_artifacts_verified": verified_hashes,
        "cyclic_json_excluded_from_hash_check": sorted(names & cyclic_paths),
        "dgac_rows": metadata["record_count"],
        "dgac_months": metadata["months"],
        "stable_layers_awaiting_canonical_publication": pending,
        "publication_certified": False,
    }


def main() -> None:
    result = verify_snapshot()
    print(json.dumps(result, ensure_ascii=False))
    if result["stable_layers_awaiting_canonical_publication"]:
        print(
            "NOTICE: datasets añadidos al registro requieren un nuevo build "
            "publication-grade. Este gate verifica integridad de la versión "
            "previa, NO certifica el próximo release."
        )


if __name__ == "__main__":
    main()
